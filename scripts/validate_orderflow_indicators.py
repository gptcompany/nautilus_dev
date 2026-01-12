#!/usr/bin/env python3
"""T044/T045 Validation: VPIN and OFI on Hyperliquid L2 Data.

Validates:
- T044: VPIN-volatility correlation > 0.7 on high-volatility periods
- T045: OFI prediction accuracy > 55% on test dataset

Data source: Hyperliquid L2 orderbook (Aug 2024 - Yen carry unwind period)
"""

from __future__ import annotations

import json

# Import our orderflow indicators
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import lz4.frame
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.common.orderflow.config import HawkesConfig, VPINConfig
from strategies.common.orderflow.hawkes_ofi import HawkesOFI
from strategies.common.orderflow.vpin import VPINIndicator


@dataclass
class L2Snapshot:
    """Single L2 orderbook snapshot."""

    timestamp: datetime
    best_bid: float
    best_ask: float
    bid_volume: float
    ask_volume: float
    mid_price: float


def parse_l2_file(path: Path) -> Iterator[L2Snapshot]:
    """Parse LZ4 compressed L2 orderbook file."""
    with lz4.frame.open(path, "rb") as f:
        for line in f:
            try:
                data = json.loads(line)
                levels = data["raw"]["data"]["levels"]
                bids = levels[0]  # [[{"px": "58167.0", "sz": "0.0172", "n": 1}, ...]]
                asks = levels[1]

                if not bids or not asks:
                    continue

                best_bid = float(bids[0]["px"])
                best_ask = float(asks[0]["px"])
                bid_volume = sum(float(b["sz"]) for b in bids[:5])  # Top 5 levels
                ask_volume = sum(float(a["sz"]) for a in asks[:5])
                mid_price = (best_bid + best_ask) / 2

                yield L2Snapshot(
                    timestamp=datetime.fromisoformat(data["time"].replace("Z", "+00:00")),
                    best_bid=best_bid,
                    best_ask=best_ask,
                    bid_volume=bid_volume,
                    ask_volume=ask_volume,
                    mid_price=mid_price,
                )
            except (KeyError, ValueError, json.JSONDecodeError):
                continue


def aggregate_to_bars(snapshots: list[L2Snapshot], bar_seconds: int = 60) -> pd.DataFrame:
    """Aggregate L2 snapshots to OHLCV bars with OFI delta."""
    if not snapshots:
        return pd.DataFrame()

    # Group by time bucket
    records = []
    for snap in snapshots:
        bucket = snap.timestamp.replace(second=0, microsecond=0)
        records.append(
            {
                "timestamp": bucket,
                "mid_price": snap.mid_price,
                "bid_volume": snap.bid_volume,
                "ask_volume": snap.ask_volume,
                "ofi_delta": snap.bid_volume - snap.ask_volume,  # Buy pressure - Sell pressure
            }
        )

    df = pd.DataFrame(records)

    # Aggregate
    bars = (
        df.groupby("timestamp")
        .agg(
            {
                "mid_price": ["first", "max", "min", "last"],
                "bid_volume": "sum",
                "ask_volume": "sum",
                "ofi_delta": "sum",
            }
        )
        .reset_index()
    )

    # Flatten columns
    bars.columns = ["timestamp", "open", "high", "low", "close", "bid_vol", "ask_vol", "ofi_delta"]
    bars["volume"] = bars["bid_vol"] + bars["ask_vol"]

    # Calculate returns for volatility
    bars["returns"] = bars["close"].pct_change()

    # Rolling volatility (20-period)
    bars["volatility"] = bars["returns"].rolling(20).std() * np.sqrt(252 * 24 * 60)  # Annualized

    return bars


def calculate_vpin_series(bars: pd.DataFrame, config: VPINConfig) -> pd.Series:
    """Calculate VPIN for each bar using TradeClassification."""
    from strategies.common.orderflow.trade_classifier import TradeClassification, TradeSide

    vpin_indicator = VPINIndicator(config)
    vpin_values = []

    for idx, row in bars.iterrows():
        timestamp_ns = int(row["timestamp"].timestamp() * 1e9)

        # Create buy classification
        if row["bid_vol"] > 0:
            buy_classification = TradeClassification(
                side=TradeSide.BUY,
                volume=row["bid_vol"],
                price=row["close"],
                timestamp_ns=timestamp_ns,
                method="l2_volume",
                confidence=0.8,  # L2 volume-based classification
            )
            vpin_indicator.update(buy_classification)

        # Create sell classification
        if row["ask_vol"] > 0:
            sell_classification = TradeClassification(
                side=TradeSide.SELL,
                volume=row["ask_vol"],
                price=row["close"],
                timestamp_ns=timestamp_ns,
                method="l2_volume",
                confidence=0.8,
            )
            vpin_indicator.update(sell_classification)

        vpin_values.append(vpin_indicator.value)

    return pd.Series(vpin_values, index=bars.index, name="vpin")


def calculate_ofi_series(bars: pd.DataFrame, config: HawkesConfig) -> pd.Series:
    """Calculate Hawkes OFI for each bar using TradeClassification."""
    from strategies.common.orderflow.trade_classifier import TradeClassification, TradeSide

    hawkes = HawkesOFI(config)
    ofi_values = []

    for idx, row in bars.iterrows():
        timestamp_ns = int(row["timestamp"].timestamp() * 1e9)

        # Create buy classification from bid volume
        if row["bid_vol"] > 0:
            buy_classification = TradeClassification(
                side=TradeSide.BUY,
                volume=row["bid_vol"],
                price=row["close"],
                timestamp_ns=timestamp_ns,
                method="l2_volume",
                confidence=0.8,
            )
            hawkes.update(buy_classification)

        # Create sell classification from ask volume
        if row["ask_vol"] > 0:
            sell_classification = TradeClassification(
                side=TradeSide.SELL,
                volume=row["ask_vol"],
                price=row["close"],
                timestamp_ns=timestamp_ns + 1,  # Slight offset to avoid collision
                method="l2_volume",
                confidence=0.8,
            )
            hawkes.update(sell_classification)

        ofi_values.append(hawkes.ofi)

    return pd.Series(ofi_values, index=bars.index, name="ofi")


def validate_t044_vpin_volatility_correlation(
    bars: pd.DataFrame,
    vpin_series: pd.Series,
    min_correlation: float = 0.7,
) -> tuple[bool, float, str]:
    """T044: Validate VPIN-volatility correlation > 0.7.

    During high-volatility periods, VPIN should correlate with realized volatility.
    """
    # Filter to high-volatility periods (top 25%)
    vol_threshold = bars["volatility"].quantile(0.75)
    high_vol_mask = bars["volatility"] > vol_threshold

    if high_vol_mask.sum() < 20:
        return False, 0.0, f"Insufficient high-vol samples: {high_vol_mask.sum()}"

    # Get aligned series
    vol_high = bars.loc[high_vol_mask, "volatility"].dropna()
    vpin_high = vpin_series.loc[high_vol_mask].dropna()

    # Align indices
    common_idx = vol_high.index.intersection(vpin_high.index)
    if len(common_idx) < 20:
        return False, 0.0, f"Insufficient aligned samples: {len(common_idx)}"

    vol_aligned = vol_high.loc[common_idx]
    vpin_aligned = vpin_high.loc[common_idx]

    # Calculate correlation
    correlation, p_value = pearsonr(vpin_aligned, vol_aligned)

    passed = correlation >= min_correlation
    message = (
        f"VPIN-Vol correlation: {correlation:.3f} (p={p_value:.4f}) | "
        f"Threshold: {min_correlation} | "
        f"{'PASS' if passed else 'FAIL'}"
    )

    return passed, correlation, message


def validate_t045_ofi_prediction_accuracy(
    bars: pd.DataFrame,
    ofi_series: pd.Series,
    min_accuracy: float = 0.55,
    horizon_bars: int = 1,
) -> tuple[bool, float, str]:
    """T045: Validate OFI prediction accuracy > 55%.

    OFI should predict price direction over next N bars better than random.
    """
    # Calculate future returns
    future_returns = bars["close"].pct_change(horizon_bars).shift(-horizon_bars)

    # Align series
    valid_mask = ofi_series.notna() & future_returns.notna() & (ofi_series != 0)

    if valid_mask.sum() < 50:
        return False, 0.0, f"Insufficient samples: {valid_mask.sum()}"

    ofi_valid = ofi_series[valid_mask]
    returns_valid = future_returns[valid_mask]

    # Prediction: OFI > 0 predicts positive return, OFI < 0 predicts negative
    predicted_direction = np.sign(ofi_valid)
    actual_direction = np.sign(returns_valid)

    # Calculate accuracy
    correct = (predicted_direction == actual_direction).sum()
    total = len(predicted_direction)
    accuracy = correct / total

    passed = accuracy >= min_accuracy
    message = (
        f"OFI prediction accuracy: {accuracy:.3f} ({correct}/{total}) | "
        f"Threshold: {min_accuracy} | "
        f"{'PASS' if passed else 'FAIL'}"
    )

    return passed, accuracy, message


def main():
    """Run T044/T045 validation on Hyperliquid L2 data."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate VPIN and OFI indicators")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("/media/sam/3TB-WDC/hyperliquid_data/BTC/2024"),
        help="Path to Hyperliquid L2 data directory",
    )
    parser.add_argument(
        "--date-range",
        type=str,
        default="20240801-20240815",
        help="Date range (YYYYMMDD-YYYYMMDD)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="Maximum number of files to process (for testing)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("T044/T045 VPIN/OFI Validation")
    print("=" * 60)
    print(f"Data source: {args.data_dir}")
    print(f"Date range: {args.date_range}")
    print()

    # Parse date range
    start_date, end_date = args.date_range.split("-")

    # Find matching files
    all_files = sorted(args.data_dir.glob("*.lz4"))
    matching_files = [f for f in all_files if start_date <= f.stem.split("-")[0] <= end_date][
        : args.max_files
    ]

    if not matching_files:
        print(f"ERROR: No files found for date range {args.date_range}")
        return 1

    print(f"Processing {len(matching_files)} files...")

    # Parse L2 data
    all_snapshots = []
    for file_path in matching_files:
        print(f"  Parsing {file_path.name}...", end=" ")
        snapshots = list(parse_l2_file(file_path))
        all_snapshots.extend(snapshots)
        print(f"{len(snapshots)} snapshots")

    print(f"\nTotal snapshots: {len(all_snapshots)}")

    if len(all_snapshots) < 100:
        print("ERROR: Insufficient data for validation")
        return 1

    # Aggregate to bars
    print("\nAggregating to 1-min bars...")
    bars = aggregate_to_bars(all_snapshots)
    print(f"Generated {len(bars)} bars")

    # Calculate VPIN
    print("\nCalculating VPIN...")
    vpin_config = VPINConfig(
        bucket_size=50,  # Volume per bucket
        num_buckets=50,
    )
    vpin_series = calculate_vpin_series(bars, vpin_config)
    print(f"VPIN range: [{vpin_series.min():.3f}, {vpin_series.max():.3f}]")

    # Calculate OFI
    print("\nCalculating Hawkes OFI...")
    hawkes_config = HawkesConfig(
        window_minutes=60,
        refit_interval=100,
    )
    ofi_series = calculate_ofi_series(bars, hawkes_config)
    print(f"OFI range: [{ofi_series.min():.3f}, {ofi_series.max():.3f}]")

    # Run validations
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    # T044: VPIN-Volatility correlation
    print("\n[T044] VPIN-Volatility Correlation (high-vol periods):")
    t044_passed, t044_corr, t044_msg = validate_t044_vpin_volatility_correlation(
        bars, vpin_series, min_correlation=0.7
    )
    print(f"  {t044_msg}")

    # T045: OFI prediction accuracy
    print("\n[T045] OFI Prediction Accuracy (1-bar horizon):")
    t045_passed, t045_acc, t045_msg = validate_t045_ofi_prediction_accuracy(
        bars, ofi_series, min_accuracy=0.55
    )
    print(f"  {t045_msg}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"T044 VPIN-Vol Correlation: {'✓ PASS' if t044_passed else '✗ FAIL'} ({t044_corr:.3f})")
    print(f"T045 OFI Prediction:       {'✓ PASS' if t045_passed else '✗ FAIL'} ({t045_acc:.3f})")

    overall = t044_passed and t045_passed
    print(f"\nOverall: {'✓ ALL PASSED' if overall else '✗ SOME FAILED'}")

    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
