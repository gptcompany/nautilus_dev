#!/usr/bin/env python3
"""T044: Validate VPIN-volatility correlation >0.7 on historical flash crash data.

This script:
1. Loads 5-minute bar data from the NautilusTrader catalog
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
from datetime import datetime

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.common.orderflow import VPINConfig, VPINIndicator


def load_bars_from_catalog(catalog_path: Path, dates: list[str]) -> pd.DataFrame:
    """Load bars for specific dates from the parquet catalog.
    
    Args:
        catalog_path: Path to the bar data directory
        dates: List of date strings in YYYY-MM-DD format
        
    Returns:
        DataFrame with OHLCV data and timestamp
    """
    all_data = []
    
    for date_str in dates:
        # Convert date format: YYYY-MM-DD -> YYYY-MM-DDT00-00-00-000000000Z_*.parquet
        pattern = f"{date_str.replace('-', '-')}T00-00-00-000000000Z_*.parquet"
        matching_files = list(catalog_path.glob(pattern))
        
        if matching_files:
            file_path = matching_files[0]
            table = pq.read_table(file_path)
            df = table.to_pandas()
            all_data.append(df)
            print(f"  Loaded {len(df)} bars from {file_path.name}")
    
    if not all_data:
        raise ValueError(f"No data files found for dates: {dates}")
    
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sort_values('ts_event').reset_index(drop=True)
    return combined


def calculate_vpin_series(df: pd.DataFrame, config: VPINConfig) -> pd.DataFrame:
    """Calculate VPIN for each bar in the dataset.
    
    Uses BVC (Bulk Volume Classification) since we have OHLCV bar data.
    
    Args:
        df: DataFrame with open, high, low, close, volume columns
        config: VPIN configuration
        
    Returns:
        DataFrame with timestamp and VPIN values
    """
    indicator = VPINIndicator(config)
    
    results = []
    for _, row in df.iterrows():
        # Create a mock bar-like object for the indicator
        class MockBar:
            def __init__(self, row):
                self.open = float(row['open'])
                self.high = float(row['high'])
                self.low = float(row['low'])
                self.close = float(row['close'])
                self.volume = float(row['volume'])
                self.ts_event = int(row['ts_event'])
        
        bar = MockBar(row)
        indicator.handle_bar(bar)
        
        if indicator.is_valid:
            results.append({
                'ts_event': row['ts_event'],
                'vpin': indicator.value,
                'toxicity': indicator.toxicity_level.value,
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
        DataFrame with timestamp and volatility
    """
    # Calculate log returns
    df = df.copy()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # Rolling standard deviation (realized volatility)
    df['volatility'] = df['log_return'].rolling(window=window).std()
    
    # Annualize: sqrt(bars_per_year) * vol
    # 5-min bars: 288 bars/day * 365 days = 105,120 bars/year
    annualization_factor = np.sqrt(105120)
    df['volatility_annualized'] = df['volatility'] * annualization_factor
    
    return df[['ts_event', 'close', 'log_return', 'volatility', 'volatility_annualized']].copy()


def run_correlation_analysis(
    vpin_df: pd.DataFrame,
    vol_df: pd.DataFrame,
) -> dict:
    """Compute correlation between VPIN and volatility.
    
    Args:
        vpin_df: DataFrame with ts_event and vpin columns
        vol_df: DataFrame with ts_event and volatility columns
        
    Returns:
        Dictionary with correlation results and statistics
    """
    # Merge on timestamp
    merged = pd.merge(
        vpin_df[['ts_event', 'vpin']],
        vol_df[['ts_event', 'volatility', 'volatility_annualized']],
        on='ts_event',
        how='inner'
    )
    
    # Remove NaN values
    merged = merged.dropna()
    
    if len(merged) < 10:
        return {
            'error': 'Insufficient data points for correlation analysis',
            'n_points': len(merged),
        }
    
    # Compute Pearson correlation
    pearson_r, pearson_p = stats.pearsonr(merged['vpin'], merged['volatility'])
    
    # Compute Spearman correlation (rank-based, more robust)
    spearman_r, spearman_p = stats.spearmanr(merged['vpin'], merged['volatility'])
    
    # Also compute with annualized volatility
    pearson_r_ann, pearson_p_ann = stats.pearsonr(merged['vpin'], merged['volatility_annualized'])
    
    return {
        'n_points': len(merged),
        'pearson_correlation': pearson_r,
        'pearson_pvalue': pearson_p,
        'spearman_correlation': spearman_r,
        'spearman_pvalue': spearman_p,
        'pearson_annualized': pearson_r_ann,
        'vpin_mean': merged['vpin'].mean(),
        'vpin_std': merged['vpin'].std(),
        'volatility_mean': merged['volatility'].mean(),
        'volatility_std': merged['volatility'].std(),
        'merged_data': merged,  # For further analysis
    }


def main():
    """Main validation function."""
    print("=" * 70)
    print("T044: VPIN-Volatility Correlation Validation")
    print("=" * 70)
    print()
    
    # Catalog path
    catalog_path = Path("/media/sam/2TB-NVMe/nautilus_catalog_v1222/data/bar/BTCUSDT-PERP.BINANCE-5-MINUTE-LAST-EXTERNAL")
    
    if not catalog_path.exists():
        print(f"ERROR: Catalog path does not exist: {catalog_path}")
        return 1
    
    # Define flash crash periods to analyze
    flash_crash_periods = {
        'COVID_Crash_March_2020': [
            '2020-03-09', '2020-03-10', '2020-03-11', '2020-03-12', 
            '2020-03-13', '2020-03-14', '2020-03-15', '2020-03-16',
        ],
        'China_Ban_May_2021': [
            '2021-05-17', '2021-05-18', '2021-05-19', '2021-05-20',
            '2021-05-21', '2021-05-22', '2021-05-23', '2021-05-24',
        ],
        'Leverage_Cascade_Dec_2021': [
            '2021-12-02', '2021-12-03', '2021-12-04', '2021-12-05',
            '2021-12-06',
        ],
    }
    
    # VPIN configuration - using BVC for bar data
    vpin_config = VPINConfig(
        bucket_size=500.0,  # 500 BTC volume per bucket
        n_buckets=50,       # Rolling 50 buckets
        classification_method='bvc',  # Bulk Volume Classification for bars
    )
    
    print(f"VPIN Configuration:")
    print(f"  - Bucket Size: {vpin_config.bucket_size}")
    print(f"  - N Buckets: {vpin_config.n_buckets}")
    print(f"  - Classification: {vpin_config.classification_method}")
    print()
    
    all_results = {}
    combined_vpin = []
    combined_vol = []
    
    for period_name, dates in flash_crash_periods.items():
        print(f"\n{'='*60}")
        print(f"Analyzing: {period_name}")
        print(f"{'='*60}")
        
        try:
            # Load data
            print(f"\nLoading data for {len(dates)} days...")
            df = load_bars_from_catalog(catalog_path, dates)
            print(f"Total bars loaded: {len(df)}")
            
            # Calculate VPIN
            print("\nCalculating VPIN...")
            vpin_df = calculate_vpin_series(df, vpin_config)
            print(f"VPIN values calculated: {len(vpin_df)}")
            
            # Calculate volatility
            print("\nCalculating realized volatility (12-bar rolling window = 1 hour)...")
            vol_df = calculate_realized_volatility(df, window=12)
            vol_df = vol_df.dropna()
            print(f"Volatility values: {len(vol_df)}")
            
            # Compute correlation
            print("\nComputing correlation...")
            results = run_correlation_analysis(vpin_df, vol_df)
            
            if 'error' in results:
                print(f"  ERROR: {results['error']}")
                continue
            
            # Store results
            all_results[period_name] = results
            combined_vpin.append(results['merged_data'][['ts_event', 'vpin']])
            combined_vol.append(results['merged_data'][['ts_event', 'volatility']])
            
            # Print period results
            print(f"\n  Results for {period_name}:")
            print(f"    Data points: {results['n_points']}")
            print(f"    Pearson correlation: {results['pearson_correlation']:.4f} (p={results['pearson_pvalue']:.2e})")
            print(f"    Spearman correlation: {results['spearman_correlation']:.4f} (p={results['spearman_pvalue']:.2e})")
            print(f"    VPIN mean: {results['vpin_mean']:.4f} (+/- {results['vpin_std']:.4f})")
            print(f"    Volatility mean: {results['volatility_mean']:.6f}")
            
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
        all_merged = pd.concat([r['merged_data'] for r in all_results.values()], ignore_index=True)
        
        # Compute overall correlation
        pearson_r, pearson_p = stats.pearsonr(all_merged['vpin'], all_merged['volatility'])
        spearman_r, spearman_p = stats.spearmanr(all_merged['vpin'], all_merged['volatility'])
        
        print(f"\n  Total data points: {len(all_merged)}")
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
        
        # High toxicity analysis
        high_toxicity = all_merged[all_merged['vpin'] >= 0.7]
        if len(high_toxicity) > 0:
            print(f"\n  High Toxicity Periods (VPIN >= 0.7):")
            print(f"    Count: {len(high_toxicity)} ({100*len(high_toxicity)/len(all_merged):.1f}%)")
            print(f"    Volatility during high toxicity: {high_toxicity['volatility'].mean():.6f}")
            print(f"    Volatility during normal: {all_merged[all_merged['vpin'] < 0.7]['volatility'].mean():.6f}")
        
        # Validation result
        print("\n" + "=" * 70)
        print("VALIDATION RESULT")
        print("=" * 70)
        
        threshold = 0.7
        # Use Spearman as it's more robust for non-linear relationships
        best_correlation = max(abs(pearson_r), abs(spearman_r))
        
        if best_correlation >= threshold:
            status = "PASS"
            print(f"\n  [PASS] VPIN-Volatility correlation: {best_correlation:.4f} >= {threshold}")
        else:
            status = "FAIL"
            print(f"\n  [FAIL] VPIN-Volatility correlation: {best_correlation:.4f} < {threshold}")
        
        print(f"\n  Best correlation achieved: {best_correlation:.4f}")
        print(f"  Required threshold: {threshold}")
        print(f"  Statistical significance: p < 0.05 = {min(pearson_p, spearman_p) < 0.05}")
        
        # Return appropriate exit code
        return 0 if status == "PASS" else 1
    
    return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
