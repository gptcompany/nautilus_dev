"""
TradingNode Configuration Factory (T014-T016).

Factory class for creating NautilusTrader TradingNodeConfig instances
from validated settings.
"""

from __future__ import annotations

from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.config import (
    BinanceDataClientConfig,
    BinanceExecClientConfig,
)
from nautilus_trader.adapters.bybit.config import (
    BybitDataClientConfig,
    BybitExecClientConfig,
    BybitProductType,
)
from nautilus_trader.config import (
    CacheConfig,
    DatabaseConfig,
    InstrumentProviderConfig,
    LiveDataEngineConfig,
    LiveExecEngineConfig,
    LiveRiskEngineConfig,
    LoggingConfig,
    StreamingConfig,
    TradingNodeConfig,
)
from nautilus_trader.persistence.config import RotationMode

from config.models import TradingNodeSettings


class TradingNodeConfigFactory:
    """Factory for creating TradingNodeConfig instances (T014)."""

    # Account type mappings
    _BINANCE_ACCOUNT_TYPES = {
        "SPOT": BinanceAccountType.SPOT,
        "USDT_FUTURES": BinanceAccountType.USDT_FUTURES,
        "COIN_FUTURES": BinanceAccountType.COIN_FUTURES,
    }

    _BYBIT_PRODUCT_TYPES = {
        "LINEAR": BybitProductType.LINEAR,
        "INVERSE": BybitProductType.INVERSE,
        "SPOT": BybitProductType.SPOT,
        "OPTION": BybitProductType.OPTION,
    }

    @classmethod
    def from_settings(
        cls,
        settings: TradingNodeSettings,
        strategies: list | None = None,
    ) -> TradingNodeConfig:
        """
        Create TradingNodeConfig from validated settings (T015).

        Parameters
        ----------
        settings : TradingNodeSettings
            Validated configuration settings.
        strategies : list, optional
            Strategy configurations to include.

        Returns
        -------
        TradingNodeConfig
            NautilusTrader configuration instance.
        """
        return TradingNodeConfig(
            trader_id=settings.environment.trader_id,
            # Timeouts
            timeout_connection=30.0,
            timeout_reconciliation=settings.reconciliation_startup_delay_secs + 5.0,
            timeout_portfolio=10.0,
            timeout_disconnection=10.0,
            timeout_post_stop=5.0,
            # Cache
            cache=cls._build_cache_config(settings),
            # Engines
            exec_engine=cls._build_exec_engine_config(settings),
            data_engine=cls._build_data_engine_config(),
            risk_engine=cls._build_risk_engine_config(settings),
            # Logging
            logging=cls._build_logging_config(settings),
            # Streaming
            streaming=cls._build_streaming_config(settings),
            # Clients
            data_clients=cls._build_data_clients(settings),
            exec_clients=cls._build_exec_clients(settings),
            # Strategies
            strategies=strategies or [],
        )

    @classmethod
    def create_production(
        cls,
        strategies: list | None = None,
    ) -> TradingNodeConfig:
        """
        Create production TradingNodeConfig from environment variables.

        Parameters
        ----------
        strategies : list, optional
            Strategy configurations to include.

        Returns
        -------
        TradingNodeConfig
            Production configuration instance.
        """
        settings = TradingNodeSettings.from_env()
        return cls.from_settings(settings, strategies=strategies)

    @classmethod
    def create_testnet(
        cls,
        strategies: list | None = None,
    ) -> TradingNodeConfig:
        """
        Create testnet TradingNodeConfig from environment variables.

        Forces testnet=True for all exchange clients.

        Parameters
        ----------
        strategies : list, optional
            Strategy configurations to include.

        Returns
        -------
        TradingNodeConfig
            Testnet configuration instance.
        """
        settings = TradingNodeSettings.from_env()

        # Force testnet mode
        if settings.binance:
            settings.binance.testnet = True
        if settings.bybit:
            settings.bybit.testnet = True

        return cls.from_settings(settings, strategies=strategies)

    @classmethod
    def _build_cache_config(cls, settings: TradingNodeSettings) -> CacheConfig:
        """Build CacheConfig with Redis backend."""
        return CacheConfig(
            database=DatabaseConfig(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                timeout=settings.redis.timeout,
            ),
            encoding="msgpack",
            timestamps_as_iso8601=True,
            buffer_interval_ms=100,
            flush_on_start=False,
            tick_capacity=10000,
            bar_capacity=10000,
        )

    @classmethod
    def _build_exec_engine_config(cls, settings: TradingNodeSettings) -> LiveExecEngineConfig:
        """Build LiveExecEngineConfig with reconciliation settings."""
        return LiveExecEngineConfig(
            # Reconciliation
            reconciliation=True,
            reconciliation_lookback_mins=settings.reconciliation_lookback_mins,
            reconciliation_startup_delay_secs=settings.reconciliation_startup_delay_secs,
            # In-flight order monitoring
            inflight_check_interval_ms=2000,
            inflight_check_threshold_ms=5000,
            inflight_check_retries=5,
            # Continuous open order checks
            open_check_interval_secs=5,
            open_check_lookback_mins=60,
            open_check_threshold_ms=5000,
            open_check_missing_retries=5,
            # Position snapshots
            snapshot_positions=True,
            snapshot_positions_interval_secs=60,
            # Memory management
            purge_closed_orders_interval_mins=15,
            purge_closed_orders_buffer_mins=60,
            purge_closed_positions_interval_mins=15,
            purge_closed_positions_buffer_mins=60,
            # Safety
            graceful_shutdown_on_exception=True,
            qsize=100000,
        )

    @classmethod
    def _build_data_engine_config(cls) -> LiveDataEngineConfig:
        """Build LiveDataEngineConfig."""
        return LiveDataEngineConfig(
            qsize=100000,
            time_bars_build_with_no_updates=True,
            time_bars_timestamp_on_close=True,
            validate_data_sequence=True,
        )

    @classmethod
    def _build_risk_engine_config(cls, settings: TradingNodeSettings) -> LiveRiskEngineConfig:
        """Build LiveRiskEngineConfig with rate limits."""
        return LiveRiskEngineConfig(
            bypass=False,
            max_order_submit_rate=settings.max_order_submit_rate,
            max_order_modify_rate=settings.max_order_modify_rate,
        )

    @classmethod
    def _build_logging_config(cls, settings: TradingNodeSettings) -> LoggingConfig:
        """Build LoggingConfig."""
        return LoggingConfig(
            log_level=settings.logging.log_level,
            log_level_file=settings.logging.log_level_file,
            log_directory=settings.logging.log_directory,
            log_file_format=(
                settings.logging.log_format if settings.logging.log_format != "text" else None
            ),
            log_file_max_size=settings.logging.max_size_mb * 1024 * 1024,
            log_file_max_backup_count=settings.logging.max_backup_count,
            log_colors=True,
        )

    @classmethod
    def _build_streaming_config(cls, settings: TradingNodeSettings) -> StreamingConfig:
        """Build StreamingConfig."""
        rotation_mode = {
            "NONE": RotationMode.NO_ROTATION,
            "SIZE": RotationMode.SIZE,
            "TIME": RotationMode.INTERVAL,
        }[settings.streaming.rotation_mode]

        return StreamingConfig(
            catalog_path=settings.streaming.catalog_path,
            fs_protocol="file",
            flush_interval_ms=settings.streaming.flush_interval_ms,
            rotation_mode=rotation_mode,
            max_file_size=settings.streaming.max_file_size_mb * 1024 * 1024,
        )

    @classmethod
    def _build_data_clients(cls, settings: TradingNodeSettings) -> dict:
        """Build data client configurations."""
        clients = {}

        if settings.binance:
            account_type = cls._BINANCE_ACCOUNT_TYPES[settings.binance.account_type]
            clients["BINANCE"] = BinanceDataClientConfig(
                account_type=account_type,
                testnet=settings.binance.testnet,
                us=settings.binance.us,
                update_instruments_interval_mins=60,
                instrument_provider=InstrumentProviderConfig(load_all=False),
            )

        if settings.bybit:
            product_types = [cls._BYBIT_PRODUCT_TYPES[pt] for pt in settings.bybit.product_types]
            clients["BYBIT"] = BybitDataClientConfig(
                product_types=product_types,
                testnet=settings.bybit.testnet,
                demo=settings.bybit.demo,
                update_instruments_interval_mins=60,
                instrument_provider=InstrumentProviderConfig(load_all=False),
            )

        return clients

    @classmethod
    def _build_exec_clients(cls, settings: TradingNodeSettings) -> dict:
        """Build execution client configurations."""
        clients = {}

        if settings.binance:
            account_type = cls._BINANCE_ACCOUNT_TYPES[settings.binance.account_type]
            clients["BINANCE"] = BinanceExecClientConfig(
                account_type=account_type,
                testnet=settings.binance.testnet,
                us=settings.binance.us,
                use_reduce_only=True,
                use_position_ids=True,
                recv_window_ms=5000,
                max_retries=3,
                listen_key_ping_max_failures=3,
                instrument_provider=InstrumentProviderConfig(load_all=False),
            )

        if settings.bybit:
            product_types = [cls._BYBIT_PRODUCT_TYPES[pt] for pt in settings.bybit.product_types]
            clients["BYBIT"] = BybitExecClientConfig(
                product_types=product_types,
                testnet=settings.bybit.testnet,
                demo=settings.bybit.demo,
                recv_window_ms=5000,
                max_retries=3,
                retry_delay_initial_ms=1000,
                retry_delay_max_ms=10000,
                instrument_provider=InstrumentProviderConfig(load_all=False),
            )

        return clients
