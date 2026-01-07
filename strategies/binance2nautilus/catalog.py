"""Catalog writer for NautilusTrader ParquetDataCatalog.

Handles writing instruments and data to the catalog with proper ordering:
1. Write instrument FIRST
2. Then write data (bars, ticks, etc.)

Note: FundingRateUpdate requires Arrow serialization registration.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pyarrow as pa
from nautilus_trader.model.data import Bar, FundingRateUpdate, TradeTick
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.serialization.arrow.serializer import register_arrow


def _make_funding_rate_encoder(schema: pa.Schema):
    """Create an encoder for FundingRateUpdate objects."""

    def encoder(data):
        if not isinstance(data, list):
            data = [data]
        # Convert to dicts - FundingRateUpdate.to_dict requires passing self
        dicts = []
        for item in data:
            d = {
                "ts_event": item.ts_event,
                "ts_init": item.ts_init,
                "rate": str(item.rate),  # Decimal to string
                "next_funding_ns": item.next_funding_ns if item.next_funding_ns else 0,
            }
            dicts.append(d)
        return pa.RecordBatch.from_pylist(dicts, schema=schema)

    return encoder


def _make_funding_rate_decoder():
    """Create a decoder for FundingRateUpdate objects."""
    from decimal import Decimal

    from nautilus_trader.model.identifiers import InstrumentId

    def decoder(table: pa.Table):
        results = []
        for row in table.to_pylist():
            fr = FundingRateUpdate(
                instrument_id=InstrumentId.from_str(row.get("instrument_id", "UNKNOWN")),
                rate=Decimal(str(row["rate"])),
                ts_event=row["ts_event"],
                ts_init=row["ts_init"],
                next_funding_ns=row.get("next_funding_ns"),
            )
            results.append(fr)
        return results

    return decoder


def _register_funding_rate_arrow() -> None:
    """Register FundingRateUpdate for Arrow serialization.

    NautilusTrader v1.222.0 does not include FundingRateUpdate in the
    default Arrow schema, so we register it manually with encoder/decoder.
    """
    from nautilus_trader.serialization.arrow.serializer import _ARROW_ENCODERS

    # Skip if already registered
    if FundingRateUpdate in _ARROW_ENCODERS:
        return

    # Build schema matching NautilusTrader's field definitions
    # Fields from nautilus_pyo3.FundingRateUpdate.get_fields():
    # {'ts_event': 'UInt64', 'next_funding_ns': 'UInt64', 'rate': 'Decimal128', 'ts_init': 'UInt64'}
    schema = pa.schema(
        [
            ("ts_event", pa.uint64()),
            ("ts_init", pa.uint64()),
            ("rate", pa.string()),  # Store as string for Decimal precision
            ("next_funding_ns", pa.uint64()),
        ]
    )

    # Register with encoder and decoder
    register_arrow(
        FundingRateUpdate,
        schema,
        encoder=_make_funding_rate_encoder(schema),
        decoder=_make_funding_rate_decoder(),
    )


# Register FundingRateUpdate on module import
_register_funding_rate_arrow()


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

    def write_funding_rates(self, funding_rates: Sequence) -> None:
        """Write funding rate data to the catalog.

        Stores FundingRateUpdate records in the catalog.
        Uses NautilusTrader's native FundingRateUpdate type.

        Args:
            funding_rates: The FundingRateUpdate records to write
        """
        if funding_rates:
            self.catalog.write_data(list(funding_rates))

    def get_instruments(self) -> list[Instrument]:
        """Get all instruments from the catalog."""
        return cast(list[Instrument], self.catalog.instruments())

    def get_bars(self, instrument_id: str | None = None) -> list[Bar]:
        """Get bars from the catalog.

        Args:
            instrument_id: Optional filter by instrument ID

        Returns:
            List of bars
        """
        if instrument_id:
            return cast(list[Bar], self.catalog.bars(instrument_ids=[instrument_id]))
        return cast(list[Bar], self.catalog.bars())

    def get_ticks(self, instrument_id: str | None = None) -> list[TradeTick]:
        """Get trade ticks from the catalog.

        Args:
            instrument_id: Optional filter by instrument ID

        Returns:
            List of trade ticks
        """
        if instrument_id:
            return cast(list[TradeTick], self.catalog.trade_ticks(instrument_ids=[instrument_id]))
        return cast(list[TradeTick], self.catalog.trade_ticks())


def create_catalog(catalog_path: Path | str) -> CatalogWriter:
    """Create a new catalog writer.

    Args:
        catalog_path: Path to the catalog directory

    Returns:
        CatalogWriter instance
    """
    return CatalogWriter(catalog_path)
