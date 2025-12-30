"""
StreamingConfig builder (T043).

Builds NautilusTrader StreamingConfig.
"""

from __future__ import annotations

from nautilus_trader.config import StreamingConfig
from nautilus_trader.persistence.config import RotationMode

from config.models import StreamingSettings

# Rotation mode mapping
_ROTATION_MODES = {
    "NONE": RotationMode.NO_ROTATION,
    "SIZE": RotationMode.SIZE,
    "TIME": RotationMode.INTERVAL,
}


def build_streaming_config(
    settings: StreamingSettings,
) -> StreamingConfig:
    """
    Build StreamingConfig from settings.

    Parameters
    ----------
    settings : StreamingSettings
        Streaming configuration settings.

    Returns
    -------
    StreamingConfig
        NautilusTrader streaming configuration.

    Notes
    -----
    Production settings:
    - SIZE rotation (128MB) prevents large files
    - 2-second flush balances latency vs I/O
    - fs_protocol="file" for local storage
    """
    rotation_mode = _ROTATION_MODES[settings.rotation_mode]

    return StreamingConfig(
        catalog_path=settings.catalog_path,
        fs_protocol="file",
        flush_interval_ms=settings.flush_interval_ms,
        rotation_mode=rotation_mode,
        max_file_size=settings.max_file_size_mb * 1024 * 1024,
    )
