"""Predefined Test Scenarios."""

from datetime import datetime

from security.sandbox.security_sandbox import AuditScenario, FraudScenario, RateLimitScenario

_BASE_TS = datetime.utcnow().isoformat()

# Fraud Detection Scenarios
WASH_TRADING_BASIC = FraudScenario(
    name="wash_trading_basic",
    description="Basic wash trading",
    orders=[
        {
            "order_id": "w1",
            "user_id": "washer1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 50000,
            "quantity": 1,
            "status": "filled",
            "timestamp": _BASE_TS,
        },
        {
            "order_id": "w2",
            "user_id": "washer1",
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 50000,
            "quantity": 1,
            "status": "filled",
            "timestamp": _BASE_TS,
        },
        {
            "order_id": "w3",
            "user_id": "washer1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 50001,
            "quantity": 1,
            "status": "filled",
            "timestamp": _BASE_TS,
        },
        {
            "order_id": "w4",
            "user_id": "washer1",
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 50001,
            "quantity": 1,
            "status": "filled",
            "timestamp": _BASE_TS,
        },
    ],
    expected_alerts=["wash_trading"],
)

SPOOFING_HIGH_CANCEL = FraudScenario(
    name="spoofing_high_cancel",
    description="Spoofing via high cancel ratio",
    orders=[
        {
            "order_id": f"s{i}",
            "user_id": "spoofer1",
            "symbol": "ETHUSDT",
            "side": "buy",
            "price": 3000 + i,
            "quantity": 10,
            "status": "cancelled" if i < 95 else "filled",
            "timestamp": _BASE_TS,
        }
        for i in range(100)
    ],
    expected_alerts=["spoofing"],
)

LAYERING_MULTI_PRICE = FraudScenario(
    name="layering_multi_price",
    description="Layering at multiple price levels",
    orders=[
        {
            "order_id": f"l{i}",
            "user_id": "layer1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 49000 + (i * 100),
            "quantity": 5,
            "status": "submitted",
            "timestamp": _BASE_TS,
        }
        for i in range(15)
    ],
    expected_alerts=["layering"],
)

ORDER_STUFFING = FraudScenario(
    name="order_stuffing",
    description="Order stuffing",
    orders=[
        {
            "order_id": f"os{i}",
            "user_id": "stuffer1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 50000,
            "quantity": 0.01,
            "status": "submitted",
            "timestamp": _BASE_TS,
        }
        for i in range(50)
    ],
    expected_alerts=["order_stuffing"],
)

CLEAN_TRADING = FraudScenario(
    name="clean_trading",
    description="Normal trading",
    orders=[
        {
            "order_id": "c1",
            "user_id": "trader1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "price": 50000,
            "quantity": 1,
            "status": "filled",
            "timestamp": _BASE_TS,
        },
        {
            "order_id": "c2",
            "user_id": "trader2",
            "symbol": "BTCUSDT",
            "side": "sell",
            "price": 50100,
            "quantity": 1,
            "status": "filled",
            "timestamp": _BASE_TS,
        },
    ],
    expected_alerts=[],
)

FRAUD_SCENARIOS = [
    WASH_TRADING_BASIC,
    SPOOFING_HIGH_CANCEL,
    LAYERING_MULTI_PRICE,
    ORDER_STUFFING,
    CLEAN_TRADING,
]

# Rate Limit Scenarios
API_BURST = RateLimitScenario(
    name="api_burst",
    description="API burst",
    request_pattern=[("api", 200)],
    expected_blocked=90,
    tolerance=0.15,
)
TRADING_LIMIT = RateLimitScenario(
    name="trading_limit",
    description="Trading limit",
    request_pattern=[("trading", 20)],
    expected_blocked=5,
    tolerance=0.2,
)
LOGIN_BRUTE_FORCE = RateLimitScenario(
    name="login_brute_force",
    description="Login brute force",
    request_pattern=[("login", 10)],
    expected_blocked=5,
    tolerance=0.1,
)
WEBSOCKET_FLOOD = RateLimitScenario(
    name="websocket_flood",
    description="WebSocket flood",
    request_pattern=[("websocket", 100)],
    expected_blocked=30,
    tolerance=0.2,
)

RATE_LIMIT_SCENARIOS = [API_BURST, TRADING_LIMIT, LOGIN_BRUTE_FORCE, WEBSOCKET_FLOOD]

# Audit Scenarios
VALID_CHAIN = AuditScenario(
    name="valid_chain",
    description="Valid chain",
    events=[
        {"event_type": "order_submitted", "actor": "test", "resource": "BTC", "action": "create"},
        {"event_type": "order_filled", "actor": "test", "resource": "BTC", "action": "update"},
    ],
    expect_valid=True,
)

HASH_TAMPER = AuditScenario(
    name="hash_tamper_detection",
    description="Hash tamper detection",
    events=[
        {
            "event_type": "withdrawal_requested",
            "actor": "attacker",
            "resource": "USDT",
            "action": "create",
        }
    ],
    tamper_action="modify_hash",
    expect_valid=False,
)

CHAIN_BREAK = AuditScenario(
    name="chain_break_detection",
    description="Chain break detection",
    events=[
        {
            "event_type": "login_success",
            "actor": "user1",
            "resource": "session",
            "action": "create",
        },
        {"event_type": "api_key_created", "actor": "user1", "resource": "api", "action": "create"},
    ],
    tamper_action="break_chain",
    expect_valid=False,
)

AUDIT_SCENARIOS = [VALID_CHAIN, HASH_TAMPER, CHAIN_BREAK]

__all__ = [
    "WASH_TRADING_BASIC",
    "SPOOFING_HIGH_CANCEL",
    "LAYERING_MULTI_PRICE",
    "ORDER_STUFFING",
    "CLEAN_TRADING",
    "FRAUD_SCENARIOS",
    "API_BURST",
    "TRADING_LIMIT",
    "LOGIN_BRUTE_FORCE",
    "WEBSOCKET_FLOOD",
    "RATE_LIMIT_SCENARIOS",
    "VALID_CHAIN",
    "HASH_TAMPER",
    "CHAIN_BREAK",
    "AUDIT_SCENARIOS",
]
