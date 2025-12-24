"""Catalog writer for NautilusTrader ParquetDataCatalog.

Handles writing instruments and data to the catalog with proper ordering:
1. Write instrument FIRST
2. Then write data (bars, ticks, etc.)
"""

from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from nautilus_trader.model.data import Bar, TradeTick
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.persistence.catalog import ParquetDataCatalog

if TYPE_CHECKING:
    pass


class CatalogWriter:
    """Writer for NautilusTrader ParquetDataCatalog."""

    def __init__(self, catalog_path: Path | str) -> None:
        """Initialize the catalog writer.

        Args:
            catalog_path: Path to the catalog directory
        """
        self.catalog_path = Path(catalog_path)
        self._catalog: ParquetDataCatalog | None = None

    @property
    def catalog(self) -> ParquetDataCatalog:
        """Get or create the catalog."""
        if self._catalog is None:
            self._catalog = ParquetDataCatalog(str(self.catalog_path))
        return self._catalog

    def write_instrument(self, instrument: Instrument) -> None:
        """Write an instrument to the catalog.

        Args:
            instrument: The instrument to write

        Note:
            Instrument MUST be written before any data for that instrument.
        """
        self.catalog.write_data([instrument])

    def write_instruments(self, instruments: Sequence[Instrument]) -> None:
        """Write multiple instruments to the catalog.

        Args:
            instruments: The instruments to write
        """
        self.catalog.write_data(list(instruments))

    def write_bars(self, bars: Sequence[Bar]) -> None:
        """Write bars to the catalog.

        Args:
            bars: The bars to write
        """
        if bars:
            self.catalog.write_data(list(bars))

    def write_ticks(self, ticks: Sequence[TradeTick]) -> None:
        """Write trade ticks to the catalog.

        Args:
            ticks: The trade ticks to write
        """
        if ticks:
            self.catalog.write_data(list(ticks))

    def write_data(self, data: Sequence) -> None:
        """Write generic data to the catalog.

        Args:
            data: The data to write (any NautilusTrader data type)
        """
        if data:
            self.catalog.write_data(list(data))

    def write_funding_rates(self, funding_rates: "Sequence[FundingRate]") -> None:
        """Write funding rate data to the catalog.

        Stores funding rates as custom data type in the catalog.
        Path: data/custom/funding_rate/{INSTRUMENT_ID}/

        Args:
            funding_rates: The funding rate records to write
        """
        if funding_rates:
            self.catalog.write_data(list(funding_rates))

    def get_instruments(self) -> list[Instrument]:
        """Get all instruments from the catalog."""
        return self.catalog.instruments()

    def get_bars(self, instrument_id: str | None = None) -> list[Bar]:
        """Get bars from the catalog.

        Args:
            instrument_id: Optional filter by instrument ID

        Returns:
            List of bars
        """
        if instrument_id:
            return self.catalog.bars(instrument_ids=[instrument_id])
        return self.catalog.bars()

    def get_ticks(self, instrument_id: str | None = None) -> list[TradeTick]:
        """Get trade ticks from the catalog.

        Args:
            instrument_id: Optional filter by instrument ID

        Returns:
            List of trade ticks
        """
        if instrument_id:
            return self.catalog.trade_ticks(instrument_ids=[instrument_id])
        return self.catalog.trade_ticks()


def create_catalog(catalog_path: Path | str) -> CatalogWriter:
    """Create a new catalog writer.

    Args:
        catalog_path: Path to the catalog directory

    Returns:
        CatalogWriter instance
    """
    return CatalogWriter(catalog_path)
