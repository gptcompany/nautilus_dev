#!/usr/bin/env python3
"""T045: Validate OFI prediction accuracy >55% on test dataset.

Methodology:
1. Load Binance aggTrades data (tick-level trade data)
2. Process trades sequentially, calculating Hawkes OFI
3. For each bar/window: predict price direction from OFI sign
   - OFI > 0 -> predict price UP
   - OFI < 0 -> predict price DOWN
4. Compare prediction vs actual next-bar price movement
5. Calculate hit rate (accuracy)

Pass criterion: accuracy > 55%
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from typing import NamedTuple


class PredictionResult(NamedTuple):
    """Result of a single OFI prediction."""

    timestamp_ns: int
    ofi: float
    predicted_direction: int  # 1 for UP, -1 for DOWN, 0 for neutral
    actual_direction: int  # 1 for UP, -1 for DOWN, 0 for unchanged
    price_at_signal: float
    price_after: float
    correct: bool


def load_aggtrades(file_path: str) -> pd.DataFrame:
    """Load Binance aggTrades CSV file.

    Columns: agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker
    """
    df = pd.read_csv(file_path)

    # Handle both header and no-header formats
    if "agg_trade_id" in df.columns:
        # Has header
        df = df.rename(
            columns={
                "agg_trade_id": "trade_id",
                "transact_time": "timestamp_ms",
                "is_buyer_maker": "is_buyer_maker",
            }
        )
    else:
        # No header (old format)
        df.columns = [
            "trade_id",
            "price",
            "quantity",
            "first_trade_id",
            "last_trade_id",
            "timestamp_ms",
            "is_buyer_maker",
        ]

    # Convert timestamp to nanoseconds
    df["timestamp_ns"] = df["timestamp_ms"] * 1_000_000

    return df


def validate_ofi_accuracy(
    data_path: str,
    aggregation_window_ms: int = 1000,  # 1 second bars for prediction
    warmup_windows: int = 100,  # Windows to skip for warmup
    hawkes_decay_rate: float = 1.0,
    hawkes_lookback: int = 5000,
    max_trades: int = 500_000,  # Limit for testing speed
) -> dict:
    """
    Validate OFI prediction accuracy on aggTrades data.

    Args:
        data_path: Path to aggTrades CSV file
        aggregation_window_ms: Time window to aggregate predictions (milliseconds)
        warmup_windows: Number of windows to skip for warmup
        hawkes_decay_rate: Decay rate for Hawkes process
        hawkes_lookback: Number of ticks for Hawkes lookback
        max_trades: Maximum trades to process (for speed)

    Returns:
        Dictionary with accuracy metrics
    """
    from strategies.common.orderflow.hawkes_ofi import HawkesOFI
    from strategies.common.orderflow.config import HawkesConfig
    from strategies.common.orderflow.trade_classifier import TradeClassification, TradeSide

    print(f"Loading data from: {data_path}")
    df = load_aggtrades(data_path)

    if len(df) > max_trades:
        print(f"Limiting to {max_trades:,} trades (original: {len(df):,})")
        df = df.head(max_trades)

    print(f"Loaded {len(df):,} trades")
    print(
        f"Date range: {pd.to_datetime(df['timestamp_ms'].min(), unit='ms')} to {pd.to_datetime(df['timestamp_ms'].max(), unit='ms')}"
    )

    # Initialize Hawkes OFI
    config = HawkesConfig(
        decay_rate=hawkes_decay_rate,
        lookback_ticks=hawkes_lookback,
        refit_interval=500,
        use_fixed_params=True,  # Required since tick library not available
        fixed_baseline=0.1,
        fixed_excitation=0.5,
    )
    hawkes = HawkesOFI(config)

    # Process trades and aggregate into time windows
    # We'll use time-based windows for prediction validation

    results = []
    current_window_start = df["timestamp_ms"].iloc[0]
    window_trades = []
    last_window_ofi = 0.0
    last_window_price = df["price"].iloc[0]
    window_count = 0

    # Track OFI values per window for prediction
    print("\nProcessing trades...")

    for idx, row in df.iterrows():
        timestamp_ms = row["timestamp_ms"]
        price = float(row["price"])
        quantity = float(row["quantity"])
        is_buyer_maker = row["is_buyer_maker"]
        timestamp_ns = int(row["timestamp_ns"])

        # Determine trade side from is_buyer_maker
        # is_buyer_maker=True means the market taker was SELLING
        # is_buyer_maker=False means the market taker was BUYING
        if isinstance(is_buyer_maker, str):
            is_buyer_maker = is_buyer_maker.lower() == "true"

        side = TradeSide.SELL if is_buyer_maker else TradeSide.BUY

        # Create classification for this trade
        classification = TradeClassification(
            side=side,
            volume=quantity,
            price=price,
            timestamp_ns=timestamp_ns,
            method="direct",  # We have direct buyer/seller info
            confidence=1.0,
        )

        # Update Hawkes model
        hawkes.update(classification)

        # Check if we've completed a window
        if timestamp_ms >= current_window_start + aggregation_window_ms:
            window_count += 1

            # Get current OFI and price
            current_ofi = hawkes.ofi if hawkes.is_fitted else 0.0
            current_price = price

            # Skip warmup period
            if window_count > warmup_windows:
                # Record prediction from PREVIOUS window
                # We predicted at the end of last window, now we see the result

                if abs(last_window_ofi) > 0.001:  # Only predict when OFI is non-trivial
                    predicted = 1 if last_window_ofi > 0 else -1

                    # Actual direction: current price vs last window price
                    if current_price > last_window_price:
                        actual = 1
                    elif current_price < last_window_price:
                        actual = -1
                    else:
                        actual = 0

                    correct = (predicted == actual) if actual != 0 else False

                    results.append(
                        PredictionResult(
                            timestamp_ns=timestamp_ns,
                            ofi=last_window_ofi,
                            predicted_direction=predicted,
                            actual_direction=actual,
                            price_at_signal=last_window_price,
                            price_after=current_price,
                            correct=correct,
                        )
                    )

            # Update for next window
            last_window_ofi = current_ofi
            last_window_price = current_price
            current_window_start = timestamp_ms

            # Progress
            if window_count % 1000 == 0:
                print(f"  Processed {window_count:,} windows, {len(results):,} predictions...")

    print(f"\nTotal windows: {window_count:,}")
    print(f"Total predictions: {len(results):,}")

    if not results:
        print("ERROR: No predictions made!")
        return {"error": "No predictions", "accuracy": 0.0}

    # Calculate accuracy metrics
    df_results = pd.DataFrame(results)

    # Filter out unchanged prices (can't evaluate direction)
    evaluable = df_results[df_results["actual_direction"] != 0]

    total_predictions = len(evaluable)
    correct_predictions = evaluable["correct"].sum()
    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0

    # Breakdown by direction
    up_preds = evaluable[evaluable["predicted_direction"] == 1]
    down_preds = evaluable[evaluable["predicted_direction"] == -1]

    up_accuracy = up_preds["correct"].mean() if len(up_preds) > 0 else 0.0
    down_accuracy = down_preds["correct"].mean() if len(down_preds) > 0 else 0.0

    # OFI magnitude analysis
    # Stronger OFI signals might have better accuracy
    evaluable_with_ofi = evaluable.copy()
    evaluable_with_ofi["ofi_abs"] = evaluable_with_ofi["ofi"].abs()

    # Split by OFI strength quartiles
    q1, q2, q3 = evaluable_with_ofi["ofi_abs"].quantile([0.25, 0.5, 0.75])

    weak_ofi = evaluable_with_ofi[evaluable_with_ofi["ofi_abs"] <= q1]
    medium_ofi = evaluable_with_ofi[
        (evaluable_with_ofi["ofi_abs"] > q1) & (evaluable_with_ofi["ofi_abs"] <= q2)
    ]
    strong_ofi = evaluable_with_ofi[
        (evaluable_with_ofi["ofi_abs"] > q2) & (evaluable_with_ofi["ofi_abs"] <= q3)
    ]
    very_strong_ofi = evaluable_with_ofi[evaluable_with_ofi["ofi_abs"] > q3]

    results_dict = {
        "total_trades": len(df),
        "total_windows": window_count,
        "total_predictions": total_predictions,
        "correct_predictions": int(correct_predictions),
        "accuracy": accuracy,
        "accuracy_pct": accuracy * 100,
        "up_predictions": len(up_preds),
        "up_accuracy": up_accuracy,
        "down_predictions": len(down_preds),
        "down_accuracy": down_accuracy,
        "ofi_quartile_accuracy": {
            "weak (Q1)": weak_ofi["correct"].mean() if len(weak_ofi) > 0 else 0.0,
            "medium (Q2)": medium_ofi["correct"].mean() if len(medium_ofi) > 0 else 0.0,
            "strong (Q3)": strong_ofi["correct"].mean() if len(strong_ofi) > 0 else 0.0,
            "very_strong (Q4)": very_strong_ofi["correct"].mean()
            if len(very_strong_ofi) > 0
            else 0.0,
        },
        "pass_threshold": 0.55,
        "passed": accuracy > 0.55,
    }

    return results_dict


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate OFI prediction accuracy")
    parser.add_argument(
        "--data-path",
        type=str,
        default="/media/sam/3TB-WDC/binance-history-data-downloader/data/BTCUSDT/aggTrades/BTCUSDT-aggTrades-2024-12-01.csv",
        help="Path to aggTrades CSV file",
    )
    parser.add_argument(
        "--window-ms",
        type=int,
        default=1000,
        help="Aggregation window in milliseconds (default: 1000ms = 1s)",
    )
    parser.add_argument("--max-trades", type=int, default=500_000, help="Maximum trades to process")
    parser.add_argument("--decay-rate", type=float, default=1.0, help="Hawkes decay rate")

    args = parser.parse_args()

    print("=" * 70)
    print("T045: Validate OFI Prediction Accuracy")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Data path: {args.data_path}")
    print(f"  Window size: {args.window_ms}ms")
    print(f"  Max trades: {args.max_trades:,}")
    print(f"  Hawkes decay rate: {args.decay_rate}")
    print()

    results = validate_ofi_accuracy(
        data_path=args.data_path,
        aggregation_window_ms=args.window_ms,
        max_trades=args.max_trades,
        hawkes_decay_rate=args.decay_rate,
    )

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    if "error" in results:
        print(f"ERROR: {results['error']}")
        return 1

    print(f"\nData Summary:")
    print(f"  Total trades processed: {results['total_trades']:,}")
    print(f"  Total windows: {results['total_windows']:,}")
    print(f"  Total predictions: {results['total_predictions']:,}")

    print(f"\nAccuracy Metrics:")
    print(f"  Overall accuracy: {results['accuracy_pct']:.2f}%")
    print(
        f"  Correct predictions: {results['correct_predictions']:,} / {results['total_predictions']:,}"
    )

    print(f"\nDirection Breakdown:")
    print(
        f"  UP predictions: {results['up_predictions']:,} (accuracy: {results['up_accuracy'] * 100:.2f}%)"
    )
    print(
        f"  DOWN predictions: {results['down_predictions']:,} (accuracy: {results['down_accuracy'] * 100:.2f}%)"
    )

    print(f"\nOFI Strength Analysis:")
    for quartile, acc in results["ofi_quartile_accuracy"].items():
        print(f"  {quartile}: {acc * 100:.2f}%")

    print(f"\n" + "=" * 70)
    print(f"PASS THRESHOLD: {results['pass_threshold'] * 100:.0f}%")
    print(f"ACTUAL ACCURACY: {results['accuracy_pct']:.2f}%")

    if results["passed"]:
        print(f"\n>>> PASSED: Accuracy {results['accuracy_pct']:.2f}% > 55% threshold <<<")
        return 0
    else:
        print(f"\n>>> FAILED: Accuracy {results['accuracy_pct']:.2f}% <= 55% threshold <<<")
        return 1


if __name__ == "__main__":
    sys.exit(main())
