"""
Integration test fixtures for reconciliation testing.

T033: Create integration test fixtures with mock venue.
"""

from __future__ import annotations

import pytest

from config.reconciliation.config import ReconciliationConfig
from config.reconciliation.external_claims import ExternalOrderClaimConfig
from config.reconciliation.presets import ReconciliationPreset
from config.trading_node.live_config import LiveTradingNodeConfig


@pytest.fixture
def standard_reconciliation_config() -> ReconciliationConfig:
    """Provide standard reconciliation configuration for integration tests."""
    return ReconciliationPreset.STANDARD.to_config()


@pytest.fixture
def conservative_reconciliation_config() -> ReconciliationConfig:
    """Provide conservative reconciliation configuration for integration tests."""
    return ReconciliationPreset.CONSERVATIVE.to_config()


@pytest.fixture
def aggressive_reconciliation_config() -> ReconciliationConfig:
    """Provide aggressive reconciliation configuration for integration tests."""
    return ReconciliationPreset.AGGRESSIVE.to_config()


@pytest.fixture
def disabled_reconciliation_config() -> ReconciliationConfig:
    """Provide disabled reconciliation configuration for integration tests."""
    return ReconciliationPreset.DISABLED.to_config()


@pytest.fixture
def trading_node_config() -> LiveTradingNodeConfig:
    """Provide standard TradingNode configuration for integration tests."""
    return LiveTradingNodeConfig(
        trader_id="TEST-TRADER-001",
        reconciliation=ReconciliationPreset.STANDARD,
        redis_host="localhost",
        redis_port=6379,
    )


@pytest.fixture
def trading_node_config_with_custom_recon() -> LiveTradingNodeConfig:
    """Provide TradingNode config with custom reconciliation settings."""
    custom_config = ReconciliationConfig(
        enabled=True,
        startup_delay_secs=12.0,
        lookback_mins=90,
        inflight_check_interval_ms=1500,
        inflight_check_threshold_ms=4000,
        inflight_check_retries=3,
        open_check_interval_secs=3.0,
        open_check_lookback_mins=90,
        open_check_threshold_ms=3000,
        purge_closed_orders_interval_mins=5,
        purge_closed_orders_buffer_mins=45,
    )
    return LiveTradingNodeConfig(
        trader_id="TEST-TRADER-002",
        reconciliation=custom_config,
    )


@pytest.fixture
def external_claims_config() -> ExternalOrderClaimConfig:
    """Provide external claims configuration for integration tests."""
    return ExternalOrderClaimConfig(
        instrument_ids=[
            "BTCUSDT-PERP.BINANCE",
            "ETHUSDT-PERP.BINANCE",
        ],
    )


@pytest.fixture
def external_claims_all() -> ExternalOrderClaimConfig:
    """Provide claim-all external claims configuration."""
    return ExternalOrderClaimConfig(claim_all=True)


# Mock venue data for testing
@pytest.fixture
def mock_open_orders() -> list[dict]:
    """Mock open orders from venue."""
    return [
        {
            "order_id": "ORD-001",
            "instrument_id": "BTCUSDT-PERP.BINANCE",
            "side": "BUY",
            "quantity": 0.1,
            "price": 50000.0,
            "status": "OPEN",
        },
        {
            "order_id": "ORD-002",
            "instrument_id": "ETHUSDT-PERP.BINANCE",
            "side": "SELL",
            "quantity": 1.0,
            "price": 3000.0,
            "status": "OPEN",
        },
    ]


@pytest.fixture
def mock_positions() -> list[dict]:
    """Mock positions from venue."""
    return [
        {
            "instrument_id": "BTCUSDT-PERP.BINANCE",
            "side": "LONG",
            "quantity": 0.5,
            "avg_entry_price": 48000.0,
            "unrealized_pnl": 1000.0,
        },
    ]


@pytest.fixture
def mock_fills() -> list[dict]:
    """Mock recent fills from venue."""
    return [
        {
            "fill_id": "FILL-001",
            "order_id": "ORD-001",
            "instrument_id": "BTCUSDT-PERP.BINANCE",
            "side": "BUY",
            "quantity": 0.1,
            "price": 50000.0,
            "commission": 5.0,
        },
    ]
