"""Conversion state tracking for incremental updates.

Tracks processed files and timestamps to support resumable and incremental operations.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class FileState:
    """State for a single processed file."""

    filename: str
    record_count: int
    first_timestamp_ns: int
    last_timestamp_ns: int
    processed_at: str  # ISO format


@dataclass
class SymbolState:
    """State for a symbol/data_type combination."""

    symbol: str
    data_type: str  # e.g., "klines_1m", "trades", "funding"
    files: dict[str, FileState] = field(default_factory=dict)
    total_records: int = 0
    last_updated: str = ""

    def add_file(self, file_state: FileState) -> None:
        """Add or update a processed file."""
        self.files[file_state.filename] = file_state
        self.total_records = sum(f.record_count for f in self.files.values())
        self.last_updated = datetime.utcnow().isoformat()


@dataclass
class ConversionState:
    """Complete conversion state for all symbols and data types."""

    catalog_path: str
    symbols: dict[str, dict[str, SymbolState]] = field(default_factory=dict)
    version: str = "1.0.0"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def get_symbol_state(self, symbol: str, data_type: str) -> SymbolState:
        """Get or create state for a symbol/data_type."""
        if symbol not in self.symbols:
            self.symbols[symbol] = {}
        if data_type not in self.symbols[symbol]:
            self.symbols[symbol][data_type] = SymbolState(
                symbol=symbol,
                data_type=data_type,
            )
        return self.symbols[symbol][data_type]

    def is_file_processed(self, symbol: str, data_type: str, filename: str) -> bool:
        """Check if a file has already been processed."""
        if symbol not in self.symbols:
            return False
        if data_type not in self.symbols[symbol]:
            return False
        return filename in self.symbols[symbol][data_type].files

    def mark_file_processed(
        self,
        symbol: str,
        data_type: str,
        filename: str,
        record_count: int,
        first_timestamp_ns: int,
        last_timestamp_ns: int,
    ) -> None:
        """Mark a file as processed."""
        state = self.get_symbol_state(symbol, data_type)
        state.add_file(
            FileState(
                filename=filename,
                record_count=record_count,
                first_timestamp_ns=first_timestamp_ns,
                last_timestamp_ns=last_timestamp_ns,
                processed_at=datetime.utcnow().isoformat(),
            )
        )
        self.updated_at = datetime.utcnow().isoformat()

    def get_pending_files(
        self,
        symbol: str,
        data_type: str,
        available_files: list[str],
    ) -> list[str]:
        """Get list of files that haven't been processed yet."""
        return [
            f
            for f in available_files
            if not self.is_file_processed(symbol, data_type, f)
        ]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "catalog_path": self.catalog_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "symbols": {
                symbol: {
                    data_type: {
                        "symbol": state.symbol,
                        "data_type": state.data_type,
                        "total_records": state.total_records,
                        "last_updated": state.last_updated,
                        "files": {
                            fname: {
                                "filename": fstate.filename,
                                "record_count": fstate.record_count,
                                "first_timestamp_ns": fstate.first_timestamp_ns,
                                "last_timestamp_ns": fstate.last_timestamp_ns,
                                "processed_at": fstate.processed_at,
                            }
                            for fname, fstate in state.files.items()
                        },
                    }
                    for data_type, state in data_types.items()
                }
                for symbol, data_types in self.symbols.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversionState":
        """Create from dictionary."""
        state = cls(
            catalog_path=data.get("catalog_path", ""),
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

        for symbol, data_types in data.get("symbols", {}).items():
            for data_type, sdata in data_types.items():
                sym_state = state.get_symbol_state(symbol, data_type)
                sym_state.total_records = sdata.get("total_records", 0)
                sym_state.last_updated = sdata.get("last_updated", "")
                for fname, fdata in sdata.get("files", {}).items():
                    sym_state.files[fname] = FileState(
                        filename=fdata["filename"],
                        record_count=fdata["record_count"],
                        first_timestamp_ns=fdata["first_timestamp_ns"],
                        last_timestamp_ns=fdata["last_timestamp_ns"],
                        processed_at=fdata["processed_at"],
                    )

        return state


def get_state_path(catalog_path: Path) -> Path:
    """Get the path to the state file for a catalog."""
    return catalog_path / "conversion_state.json"


def load_state(catalog_path: Path) -> ConversionState:
    """Load conversion state from disk.

    Args:
        catalog_path: Path to the catalog directory

    Returns:
        ConversionState (new if file doesn't exist)
    """
    state_path = get_state_path(catalog_path)
    if state_path.exists():
        with open(state_path) as f:
            data = json.load(f)
        return ConversionState.from_dict(data)
    return ConversionState(catalog_path=str(catalog_path))


def save_state(state: ConversionState, catalog_path: Path) -> None:
    """Save conversion state to disk.

    Args:
        state: The state to save
        catalog_path: Path to the catalog directory
    """
    state_path = get_state_path(catalog_path)
    catalog_path.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state.to_dict(), f, indent=2)
