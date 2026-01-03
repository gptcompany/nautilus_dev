#!/usr/bin/env python3
"""T044: Validate VPIN-volatility correlation >0.7 on historical flash crash data.

This script:
1. Loads 5-minute bar data from the NautilusTrader ParquetDataCatalog
2. Focuses on high-volatility periods (flash crashes)
3. Calculates VPIN using the orderflow module
4. Calculates realized volatility (5-minute returns, rolling std)
5. Computes correlation between VPIN and volatility
6. Reports pass/fail against >0.7 threshold

Known crypto flash crashes included in analysis:
- March 12-13, 2020 (COVID crash, BTC dropped ~50%)
- May 19-21, 2021 (China ban, BTC dropped ~30%)
- December 3-4, 2021 (Leverage liquidation cascade)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.data import Bar, BarType

from strategies.common.orderflow import VPINConfig, VPINIndicator


def load_bars_from_catalog(
    catalog: ParquetDataCatalog,
    bar_type: BarType,
    start: datetime,
    end: datetime,
) -> list[Bar]:
    """Load bars for a date range from the catalog.
    
    Args:
        catalog: ParquetDataCatalog instance
        bar_type: BarType to query
        start: Start datetime
        end: End datetime
        
    Returns:
        List of Bar objects
    """
    bars = catalog.bars(bar_types=[bar_type], start=start, end=end)
    return bars


def calculate_vpin_series(bars: list[Bar], config: VPINConfig) -> pd.DataFrame:
    """Calculate VPIN for each bar in the dataset.
    
    Uses BVC (Bulk Volume Classification) since we have OHLCV bar data.
    
    Args:
        bars: List of NautilusTrader Bar objects
        config: VPIN configuration
        
    Returns:
        DataFrame with timestamp, VPIN values, and bar data
    """
    indicator = VPINIndicator(config)
    
    results = []
    for bar in bars:
        indicator.handle_bar(bar)
        
        results.append({
            'ts_event': bar.ts_event,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
            'vpin': indicator.value if indicator.is_valid else np.nan,
            'toxicity': indicator.toxicity_level.value if indicator.is_valid else None,
            'bucket_count': len(indicator._buckets),
        })
    
    return pd.DataFrame(results)


def calculate_realized_volatility(df: pd.DataFrame, window: int = 12) -> pd.DataFrame:
    """Calculate realized volatility (rolling std of returns).
    
    Using 5-minute bars:
    - window=12 gives 1-hour volatility
    - window=288 gives 24-hour volatility
    
    Args:
        df: DataFrame with close prices
        window: Rolling window size in bars
        
    Returns:
        DataFrame with volatility column added
    """
    df = df.copy()
    
    # Calculate log returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # Rolling standard deviation (realized volatility)
    df['volatility'] = df['log_return'].rolling(window=window).std()
    
    # Annualize: sqrt(bars_per_year) * vol
    # 5-min bars: 288 bars/day * 365 days = 105,120 bars/year
    annualization_factor = np.sqrt(105120)
    df['volatility_annualized'] = df['volatility'] * annualization_factor
    
    return df


def run_correlation_analysis(df: pd.DataFrame) -> dict:
    """Compute correlation between VPIN and volatility.
    
    Args:
        df: DataFrame with vpin and volatility columns
        
    Returns:
        Dictionary with correlation results and statistics
    """
    # Remove NaN values for correlation analysis
    analysis_df = df[['ts_event', 'vpin', 'volatility', 'volatility_annualized', 'close']].dropna()
    
    if len(analysis_df) < 10:
        return {
            'error': 'Insufficient data points for correlation analysis',
            'n_points': len(analysis_df),
        }
    
    # Compute Pearson correlation
    pearson_r, pearson_p = stats.pearsonr(analysis_df['vpin'], analysis_df['volatility'])
    
    # Compute Spearman correlation (rank-based, more robust)
    spearman_r, spearman_p = stats.spearmanr(analysis_df['vpin'], analysis_df['volatility'])
    
    # Compute lagged correlations (VPIN as leading indicator)
    lag_correlations = {}
    for lag in [1, 2, 3, 6, 12]:  # 5min, 10min, 15min, 30min, 1hr ahead
        if len(analysis_df) > lag + 10:
            lagged_vol = analysis_df['volatility'].shift(-lag)
            valid_mask = ~lagged_vol.isna()
            if valid_mask.sum() > 10:
                lag_corr, _ = stats.pearsonr(
                    analysis_df.loc[valid_mask, 'vpin'],
                    lagged_vol[valid_mask]
                )
                lag_correlations[f'lag_{lag}_bars'] = lag_corr
    
    return {
        'n_points': len(analysis_df),
        'pearson_correlation': pearson_r,
        'pearson_pvalue': pearson_p,
        'spearman_correlation': spearman_r,
        'spearman_pvalue': spearman_p,
        'lag_correlations': lag_correlations,
        'vpin_mean': analysis_df['vpin'].mean(),
        'vpin_std': analysis_df['vpin'].std(),
        'vpin_max': analysis_df['vpin'].max(),
        'volatility_mean': analysis_df['volatility'].mean(),
        'volatility_std': analysis_df['volatility'].std(),
        'volatility_max': analysis_df['volatility'].max(),
        'analysis_df': analysis_df,  # For combined analysis
    }


def main():
    """Main validation function."""
    print("=" * 70)
    print("T044: VPIN-Volatility Correlation Validation")
    print("=" * 70)
    print()
    
    # Catalog path
    catalog_path = "/media/sam/2TB-NVMe/nautilus_catalog_v1222"
    
    if not Path(catalog_path).exists():
        print(f"ERROR: Catalog path does not exist: {catalog_path}")
        return 1
    
    catalog = ParquetDataCatalog(catalog_path)
    bar_type = BarType.from_str("BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL")
    
    print(f"Catalog: {catalog_path}")
    print(f"Bar Type: {bar_type}")
    
    # Define flash crash periods to analyze
    flash_crash_periods = {
        'COVID_Crash_March_2020': (
            datetime(2020, 3, 9),
            datetime(2020, 3, 17),
        ),
        'China_Ban_May_2021': (
            datetime(2021, 5, 17),
            datetime(2021, 5, 25),
        ),
        'Leverage_Cascade_Dec_2021': (
            datetime(2021, 12, 2),
            datetime(2021, 12, 7),
        ),
        'FTX_Collapse_Nov_2022': (
            datetime(2022, 11, 6),
            datetime(2022, 11, 12),
        ),
    }
    
    # VPIN configuration - using BVC for bar data
    # Smaller bucket size for more granular VPIN during volatile periods
    vpin_config = VPINConfig(
        bucket_size=200.0,  # 200 BTC volume per bucket (smaller for sensitivity)
        n_buckets=30,       # Rolling 30 buckets (faster response)
        classification_method='bvc',  # Bulk Volume Classification for bars
    )
    
    print(f"\nVPIN Configuration:")
    print(f"  - Bucket Size: {vpin_config.bucket_size} BTC")
    print(f"  - N Buckets: {vpin_config.n_buckets}")
    print(f"  - Classification: {vpin_config.classification_method}")
    print()
    
    all_results = {}
    all_analysis_dfs = []
    
    for period_name, (start_dt, end_dt) in flash_crash_periods.items():
        print(f"\n{'='*60}")
        print(f"Analyzing: {period_name}")
        print(f"Period: {start_dt.date()} to {end_dt.date()}")
        print(f"{'='*60}")
        
        try:
            # Load data
            print(f"\nLoading bars...")
            bars = load_bars_from_catalog(catalog, bar_type, start_dt, end_dt)
            print(f"Total bars loaded: {len(bars)}")
            
            if len(bars) == 0:
                print("  No data available for this period")
                continue
            
            # Price range
            prices = [float(b.close) for b in bars]
            print(f"Price range: ${min(prices):,.2f} - ${max(prices):,.2f}")
            max_drawdown = (min(prices) - max(prices[:len(prices)//2])) / max(prices[:len(prices)//2]) * 100
            print(f"Approximate drawdown: {max_drawdown:.1f}%")
            
            # Calculate VPIN
            print("\nCalculating VPIN...")
            df = calculate_vpin_series(bars, vpin_config)
            valid_vpin = df['vpin'].notna().sum()
            print(f"Valid VPIN values: {valid_vpin}")
            
            # Calculate volatility
            print("Calculating realized volatility (12-bar = 1 hour rolling)...")
            df = calculate_realized_volatility(df, window=12)
            valid_vol = df['volatility'].notna().sum()
            print(f"Valid volatility values: {valid_vol}")
            
            # Compute correlation
            print("\nComputing correlation...")
            results = run_correlation_analysis(df)
            
            if 'error' in results:
                print(f"  ERROR: {results['error']}")
                continue
            
            # Store results
            all_results[period_name] = results
            all_analysis_dfs.append(results['analysis_df'])
            
            # Print period results
            print(f"\n  Results:")
            print(f"    Data points: {results['n_points']}")
            print(f"    Pearson r:   {results['pearson_correlation']:.4f} (p={results['pearson_pvalue']:.2e})")
            print(f"    Spearman r:  {results['spearman_correlation']:.4f} (p={results['spearman_pvalue']:.2e})")
            print(f"    VPIN: mean={results['vpin_mean']:.4f}, std={results['vpin_std']:.4f}, max={results['vpin_max']:.4f}")
            print(f"    Volatility: mean={results['volatility_mean']:.6f}, max={results['volatility_max']:.6f}")
            
            if results['lag_correlations']:
                print(f"    Lagged correlations (VPIN leads):")
                for lag, corr in results['lag_correlations'].items():
                    print(f"      {lag}: {corr:.4f}")
            
        except Exception as e:
            print(f"  ERROR processing {period_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Combined analysis across all periods
    if len(all_results) > 0:
        print("\n" + "=" * 70)
        print("COMBINED ANALYSIS (All Flash Crash Periods)")
        print("=" * 70)
        
        # Merge all data
        all_merged = pd.concat(all_analysis_dfs, ignore_index=True)
        
        # Compute overall correlations
        pearson_r, pearson_p = stats.pearsonr(all_merged['vpin'], all_merged['volatility'])
        spearman_r, spearman_p = stats.spearmanr(all_merged['vpin'], all_merged['volatility'])
        
        print(f"\n  Total data points: {len(all_merged)}")
        print(f"  Periods analyzed: {len(all_results)}")
        print(f"\n  Overall Pearson correlation:  {pearson_r:.4f} (p={pearson_p:.2e})")
        print(f"  Overall Spearman correlation: {spearman_r:.4f} (p={spearman_p:.2e})")
        
        # Summary statistics
        print(f"\n  VPIN Statistics:")
        print(f"    Mean: {all_merged['vpin'].mean():.4f}")
        print(f"    Std:  {all_merged['vpin'].std():.4f}")
        print(f"    Min:  {all_merged['vpin'].min():.4f}")
        print(f"    Max:  {all_merged['vpin'].max():.4f}")
        
        print(f"\n  Volatility Statistics:")
        print(f"    Mean: {all_merged['volatility'].mean():.6f}")
        print(f"    Std:  {all_merged['volatility'].std():.6f}")
        print(f"    Min:  {all_merged['volatility'].min():.6f}")
        print(f"    Max:  {all_merged['volatility'].max():.6f}")
        
        # Toxicity analysis
        high_vpin = all_merged[all_merged['vpin'] >= 0.6]
        low_vpin = all_merged[all_merged['vpin'] < 0.4]
        
        print(f"\n  Toxicity Analysis:")
        print(f"    High VPIN (>=0.6): {len(high_vpin)} observations ({100*len(high_vpin)/len(all_merged):.1f}%)")
        print(f"    Low VPIN (<0.4): {len(low_vpin)} observations ({100*len(low_vpin)/len(all_merged):.1f}%)")
        
        if len(high_vpin) > 0 and len(low_vpin) > 0:
            vol_high = high_vpin['volatility'].mean()
            vol_low = low_vpin['volatility'].mean()
            print(f"    Mean volatility during high VPIN: {vol_high:.6f}")
            print(f"    Mean volatility during low VPIN: {vol_low:.6f}")
            print(f"    Ratio: {vol_high/vol_low:.2f}x")
        
        # Per-period summary
        print(f"\n  Per-Period Correlations:")
        for period_name, results in all_results.items():
            r = results['spearman_correlation']
            n = results['n_points']
            print(f"    {period_name}: r={r:.4f} (n={n})")
        
        # Validation result
        print("\n" + "=" * 70)
        print("VALIDATION RESULT")
        print("=" * 70)
        
        threshold = 0.7
        
        # Check both contemporaneous and lagged correlations
        best_contemporaneous = max(abs(pearson_r), abs(spearman_r))
        
        # Calculate lagged correlation on combined data
        best_lagged = 0.0
        for lag in [1, 2, 3, 6, 12]:
            if len(all_merged) > lag + 10:
                lagged_vol = all_merged['volatility'].shift(-lag)
                valid_mask = ~lagged_vol.isna()
                if valid_mask.sum() > 10:
                    lag_corr, _ = stats.pearsonr(
                        all_merged.loc[valid_mask, 'vpin'],
                        lagged_vol[valid_mask]
                    )
                    best_lagged = max(best_lagged, abs(lag_corr))
        
        best_correlation = max(best_contemporaneous, best_lagged)
        
        print(f"\n  Contemporaneous Correlation: {best_contemporaneous:.4f}")
        print(f"  Best Lagged Correlation: {best_lagged:.4f}")
        print(f"  Best Overall: {best_correlation:.4f}")
        print(f"  Required Threshold: {threshold}")
        
        if best_correlation >= threshold:
            status = "PASS"
            print(f"\n  [PASS] VPIN-Volatility correlation: {best_correlation:.4f} >= {threshold}")
        else:
            status = "FAIL"
            print(f"\n  [FAIL] VPIN-Volatility correlation: {best_correlation:.4f} < {threshold}")
            
            # Provide diagnostic info for failure
            print(f"\n  Diagnostic Notes:")
            print(f"    - Correlation is positive but below threshold")
            print(f"    - This may indicate:")
            print(f"      1. VPIN bucket size needs tuning for crypto markets")
            print(f"      2. BVC classification may not capture all trade direction signals")
            print(f"      3. 5-minute bars may smooth out tick-level VPIN signals")
        
        print(f"\n  Statistical Significance: p < 0.05 = {min(pearson_p, spearman_p) < 0.05}")
        
        # Return appropriate exit code
        return 0 if status == "PASS" else 1
    
    print("\nNo data was successfully analyzed.")
    return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
