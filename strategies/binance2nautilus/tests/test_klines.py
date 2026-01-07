"""Unit tests for klines converter.

Tests CSV parsing, DataFrame transformation, and wrangler output.
"""

from pathlib import Path

import pandas as pd
import pytest

from strategies.binance2nautilus import ConverterConfig
from strategies.binance2nautilus.converters.klines import TIMEFRAME_MAP, KlinesConverter


@pytest.fixture
def sample_klines_csv(tmp_path: Path) -> Path:
    """Create a sample klines CSV file."""
    csv_content = """open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore
1704067200000,90320.50,90396.90,90254.00,90376.80,393.365,1704067259999,35522468.40870,8771,173.579,15676612.26210,0
1704067260000,90376.80,90450.00,90350.00,90425.50,250.123,1704067319999,22612345.67890,5432,120.456,10891234.56780,0
1704067320000,90425.50,90500.00,90400.00,90480.00,300.789,1704067379999,27234567.89012,6543,150.123,13567890.12340,0
"""
    csv_file = tmp_path / "BTCUSDT-1m-2024-01-01.csv"
    csv_file.write_text(csv_content)
    return csv_file


@pytest.fixture
def config_with_temp_dir(tmp_path: Path) -> ConverterConfig:
    """Create config with temporary directories."""
    return ConverterConfig(
        source_dir=tmp_path,
        output_dir=tmp_path / "catalog",
    )


class TestKlinesConverter:
    """Tests for KlinesConverter."""

    def test_timeframe_map_contains_expected_values(self):
        """Timeframe map should contain 1m, 5m, 15m."""
        assert "1m" in TIMEFRAME_MAP
        assert "5m" in TIMEFRAME_MAP
        assert "15m" in TIMEFRAME_MAP
        assert TIMEFRAME_MAP["1m"] == "1-MINUTE"
        assert TIMEFRAME_MAP["5m"] == "5-MINUTE"
        assert TIMEFRAME_MAP["15m"] == "15-MINUTE"

    def test_converter_initialization(self):
        """Converter should initialize with correct settings."""
        converter = KlinesConverter(symbol="BTCUSDT", timeframe="1m")

        assert converter.symbol == "BTCUSDT"
        assert converter.timeframe == "1m"
        assert converter.data_type == "klines_1m"
        assert str(converter.bar_type) == "BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"

    def test_converter_unsupported_timeframe_raises(self):
        """Unsupported timeframe should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            KlinesConverter(symbol="BTCUSDT", timeframe="invalid")

    def test_parse_csv(self, sample_klines_csv: Path, config_with_temp_dir: ConverterConfig):
        """CSV parsing should return DataFrame with correct columns."""
        converter = KlinesConverter(
            symbol="BTCUSDT",
            timeframe="1m",
            config=config_with_temp_dir,
        )

        df = converter.parse_csv(sample_klines_csv)

        assert len(df) == 3
        assert "open_time" in df.columns
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_transform_creates_correct_dataframe(
        self, sample_klines_csv: Path, config_with_temp_dir: ConverterConfig
    ):
        """Transform should create DataFrame with DatetimeIndex and OHLCV columns."""
        converter = KlinesConverter(
            symbol="BTCUSDT",
            timeframe="1m",
            config=config_with_temp_dir,
        )

        raw_df = converter.parse_csv(sample_klines_csv)
        transformed = converter.transform(raw_df)

        # Check index is DatetimeIndex with UTC
        assert isinstance(transformed.index, pd.DatetimeIndex)
        assert transformed.index.tz is not None
        assert str(transformed.index.tz) == "UTC"

        # Check columns
        expected_columns = ["open", "high", "low", "close", "volume"]
        assert list(transformed.columns) == expected_columns

        # Check dtypes are float64
        for col in expected_columns:
            assert transformed[col].dtype == "float64"

        # Check values
        assert transformed.iloc[0]["open"] == 90320.50
        assert transformed.iloc[0]["high"] == 90396.90
        assert transformed.iloc[0]["close"] == 90376.80

    def test_wrangle_produces_bar_objects(
        self, sample_klines_csv: Path, config_with_temp_dir: ConverterConfig
    ):
        """Wrangler should produce Bar objects with correct properties."""
        converter = KlinesConverter(
            symbol="BTCUSDT",
            timeframe="1m",
            config=config_with_temp_dir,
        )

        raw_df = converter.parse_csv(sample_klines_csv)
        transformed = converter.transform(raw_df)
        bars = converter.wrangle(transformed)

        assert len(bars) == 3

        # Check first bar
        bar = bars[0]
        assert bar.bar_type == converter.bar_type
        assert float(bar.open) == pytest.approx(90320.50, rel=1e-6)
        assert float(bar.high) == pytest.approx(90396.90, rel=1e-6)
        assert float(bar.low) == pytest.approx(90254.00, rel=1e-6)
        assert float(bar.close) == pytest.approx(90376.80, rel=1e-6)

        # Check timestamp is in nanoseconds
        assert bar.ts_event > 1_700_000_000_000_000_000

    def test_process_file_end_to_end(
        self, sample_klines_csv: Path, config_with_temp_dir: ConverterConfig
    ):
        """Process file should produce correct Bar objects end-to-end."""
        converter = KlinesConverter(
            symbol="BTCUSDT",
            timeframe="1m",
            config=config_with_temp_dir,
        )

        bars = converter.process_file(sample_klines_csv)

        assert len(bars) == 3
        assert all(bar.bar_type == converter.bar_type for bar in bars)


class TestTimeframeSupport:
    """Tests for different timeframe support."""

    @pytest.mark.parametrize(
        "timeframe,expected_spec",
        [
            ("1m", "1-MINUTE"),
            ("5m", "5-MINUTE"),
            ("15m", "15-MINUTE"),
        ],
    )
    def test_supported_timeframes(self, timeframe: str, expected_spec: str):
        """Each supported timeframe should create correct bar type."""
        converter = KlinesConverter(symbol="BTCUSDT", timeframe=timeframe)

        assert expected_spec in str(converter.bar_type)
        assert converter.data_type == f"klines_{timeframe}"
