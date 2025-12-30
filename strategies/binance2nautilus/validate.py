"""Validation module for NautilusTrader ParquetDataCatalog.

Verifies catalog integrity, schema compatibility, and BacktestEngine support.
"""

from dataclasses import dataclass
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.model.data import Bar
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.persistence.catalog import ParquetDataCatalog


@dataclass
class ValidationResult:
    """Result of catalog validation."""

    is_valid: bool
    catalog_path: str
    instruments: list[str]
    bar_counts: dict[str, int]
    tick_counts: dict[str, int]
    schema_version: str
    backtest_compatible: bool | None
    errors: list[str]
    warnings: list[str]


def validate_catalog(
    catalog_path: Path | str,
    run_backtest_test: bool = False,
    test_bar_count: int = 1000,
) -> ValidationResult:
    """Validate a NautilusTrader ParquetDataCatalog.

    Args:
        catalog_path: Path to the catalog directory
        run_backtest_test: Whether to run BacktestEngine compatibility test
        test_bar_count: Number of bars to use for backtest test

    Returns:
        ValidationResult with details
    """
    catalog_path = Path(catalog_path)
    errors: list[str] = []
    warnings: list[str] = []

    # Check catalog exists
    if not catalog_path.exists():
        return ValidationResult(
            is_valid=False,
            catalog_path=str(catalog_path),
            instruments=[],
            bar_counts={},
            tick_counts={},
            schema_version="unknown",
            backtest_compatible=None,
            errors=[f"Catalog path does not exist: {catalog_path}"],
            warnings=[],
        )

    # Load catalog
    try:
        catalog = ParquetDataCatalog(str(catalog_path))
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            catalog_path=str(catalog_path),
            instruments=[],
            bar_counts={},
            tick_counts={},
            schema_version="unknown",
            backtest_compatible=None,
            errors=[f"Failed to load catalog: {e}"],
            warnings=[],
        )

    # Get instruments
    try:
        instruments = catalog.instruments()
        instrument_ids = [str(i.id) for i in instruments]
    except Exception as e:
        errors.append(f"Failed to load instruments: {e}")
        instrument_ids = []
        instruments = []

    # Get bar counts
    bar_counts: dict[str, int] = {}
    try:
        all_bars = catalog.bars()
        # Group by bar_type
        for bar in all_bars:
            bar_type = str(bar.bar_type)
            bar_counts[bar_type] = bar_counts.get(bar_type, 0) + 1
    except Exception as e:
        errors.append(f"Failed to load bars: {e}")

    # Get tick counts
    tick_counts: dict[str, int] = {}
    try:
        all_ticks = catalog.trade_ticks()
        for tick in all_ticks:
            inst_id = str(tick.instrument_id)
            tick_counts[inst_id] = tick_counts.get(inst_id, 0) + 1
    except Exception as e:
        warnings.append(f"Failed to load trade ticks: {e}")

    # Verify timestamps (FR-009: nanosecond precision)
    if all_bars:
        sample_bar = all_bars[0]
        if sample_bar.ts_event <= 0:
            errors.append("Invalid ts_event: must be positive nanoseconds")
        if sample_bar.ts_init <= 0:
            errors.append("Invalid ts_init: must be positive nanoseconds")
        # Check nanosecond range (should be > 1e18 for year 2019+)
        if sample_bar.ts_event < 1_500_000_000_000_000_000:
            warnings.append("ts_event may not be in nanoseconds (too small)")

    # Schema version detection (128-bit = v1.222.0 nightly)
    schema_version = "128-bit (v1.222.0)"  # Assumed based on nightly

    # BacktestEngine compatibility test
    backtest_compatible: bool | None = None
    if run_backtest_test and instruments and all_bars:
        backtest_compatible = _test_backtest_compatibility(
            instruments[0],
            all_bars[:test_bar_count],
            errors,
        )

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        catalog_path=str(catalog_path),
        instruments=instrument_ids,
        bar_counts=bar_counts,
        tick_counts=tick_counts,
        schema_version=schema_version,
        backtest_compatible=backtest_compatible,
        errors=errors,
        warnings=warnings,
    )


def _test_backtest_compatibility(
    instrument: Instrument,
    bars: list[Bar],
    errors: list[str],
) -> bool:
    """Test BacktestEngine compatibility with catalog data.

    Args:
        instrument: The instrument to test
        bars: Sample bars to add
        errors: Error list to append to

    Returns:
        True if compatible, False otherwise
    """
    try:
        # Import here to avoid circular imports and unused import warnings
        from nautilus_trader.backtest.models import FillModel
        from nautilus_trader.model.currencies import USDT
        from nautilus_trader.model.enums import AccountType, OmsType
        from nautilus_trader.model.objects import Money

        config = BacktestEngineConfig(trader_id="VALIDATOR-001")
        engine = BacktestEngine(config=config)

        # v1.222.0 requires venue to be added before instruments
        engine.add_venue(
            venue=instrument.id.venue,
            oms_type=OmsType.HEDGING,
            account_type=AccountType.MARGIN,
            base_currency=None,
            starting_balances=[Money(1_000_000, USDT)],
            fill_model=FillModel(),
        )

        engine.add_instrument(instrument)
        engine.add_data(bars)
        return True
    except TypeError as e:
        if "pyo3" in str(e).lower():
            errors.append(
                "BacktestEngine incompatible: PyO3 objects detected. "
                "Use V1 wranglers (BarDataWrangler, TradeTickDataWrangler)."
            )
        else:
            errors.append(f"BacktestEngine type error: {e}")
        return False
    except Exception as e:
        errors.append(f"BacktestEngine test failed: {e}")
        return False


def verify_record_count(
    catalog_path: Path | str,
    expected_counts: dict[str, int],
) -> tuple[bool, dict[str, tuple[int, int]]]:
    """Verify record counts match expected values (SC-004).

    Args:
        catalog_path: Path to the catalog
        expected_counts: Dict of {bar_type: expected_count}

    Returns:
        Tuple of (all_match, {bar_type: (actual, expected)})
    """
    result = validate_catalog(catalog_path)
    comparison: dict[str, tuple[int, int]] = {}
    all_match = True

    for bar_type, expected in expected_counts.items():
        actual = result.bar_counts.get(bar_type, 0)
        comparison[bar_type] = (actual, expected)
        if actual != expected:
            all_match = False

    return all_match, comparison
