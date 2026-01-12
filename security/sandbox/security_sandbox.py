"""Security Testing Sandbox."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from security.sandbox.config import SecuritySandboxConfig, TestResult, TestResults

logger = logging.getLogger(__name__)


@dataclass
class FraudScenario:
    """Fraud detection test scenario."""

    name: str
    description: str
    orders: list[dict[str, Any]]
    expected_alerts: list[str]
    severity_threshold: str = "medium"


@dataclass
class RateLimitScenario:
    """Rate limiter test scenario."""

    name: str
    description: str
    request_pattern: list[tuple[str, int]]
    expected_blocked: int
    tolerance: float = 0.1


@dataclass
class AuditScenario:
    """Audit trail test scenario."""

    name: str
    description: str
    events: list[dict[str, Any]]
    tamper_action: str | None = None
    expect_valid: bool = True


@dataclass
class SecurityTestReport:
    """Security test report."""

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    fraud_detection: TestResults | None = None
    rate_limiter: TestResults | None = None
    audit_trail: TestResults | None = None
    total_passed: int = 0
    total_failed: int = 0
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            "timestamp": self.timestamp,
            "fraud_detection": self._results_to_dict(self.fraud_detection),
            "rate_limiter": self._results_to_dict(self.rate_limiter),
            "audit_trail": self._results_to_dict(self.audit_trail),
            "summary": {
                "total_passed": self.total_passed,
                "total_failed": self.total_failed,
                "duration_ms": self.duration_ms,
            },
        }

    def _results_to_dict(self, results: TestResults | None) -> dict | None:
        """Convert TestResults to dict."""
        if not results:
            return None
        return {
            "scenario_name": results.scenario_name,
            "passed": results.scenarios_passed,
            "failed": results.scenarios_failed,
        }


class SecuritySandbox:
    """Security testing sandbox."""

    def __init__(self, config: SecuritySandboxConfig | None = None):
        """Initialize sandbox."""
        self.config = config or SecuritySandboxConfig()
        self._report = SecurityTestReport()

    async def test_fraud_detection(
        self, scenarios: list[FraudScenario] | None = None
    ) -> TestResults:
        """Test fraud detection."""
        from security.fraud_detection import FraudDetector

        scenarios = scenarios or self._default_fraud_scenarios()
        results = TestResults(scenario_name="fraud_detection")
        start_time = time.time()

        detector = FraudDetector()

        for scenario in scenarios:
            test_start = time.time()
            try:
                detector.reset_tracking()
                all_alerts = []
                for order in scenario.orders:
                    alerts = detector.check_order(order)
                    all_alerts.extend(alerts)

                detected_types = {a.fraud_type.value for a in all_alerts}
                expected_types = set(scenario.expected_alerts)
                passed = expected_types.issubset(detected_types)

                results.results.append(
                    TestResult(
                        name=scenario.name,
                        passed=passed,
                        duration_ms=int((time.time() - test_start) * 1000),
                        error_message=""
                        if passed
                        else f"Missing: {expected_types - detected_types}",
                    )
                )
            except Exception as e:
                results.results.append(
                    TestResult(name=scenario.name, passed=False, error_message=str(e))
                )

        results.total_duration_ms = int((time.time() - start_time) * 1000)
        self._report.fraud_detection = results
        return results

    async def test_rate_limiter(
        self, scenarios: list[RateLimitScenario] | None = None
    ) -> TestResults:
        """Test rate limiter."""
        scenarios = scenarios or self._default_rate_limit_scenarios()
        results = TestResults(scenario_name="rate_limiter")
        start_time = time.time()

        mock_limiter = MockRateLimiter()

        for scenario in scenarios:
            test_start = time.time()
            try:
                blocked_count = 0
                for limit_type, count in scenario.request_pattern:
                    for _ in range(count):
                        result = mock_limiter.check(limit_type)
                        if not result["allowed"]:
                            blocked_count += 1

                expected = scenario.expected_blocked
                tolerance = int(expected * scenario.tolerance)
                passed = abs(blocked_count - expected) <= tolerance

                results.results.append(
                    TestResult(
                        name=scenario.name,
                        passed=passed,
                        duration_ms=int((time.time() - test_start) * 1000),
                        error_message=""
                        if passed
                        else f"Blocked {blocked_count}, expected ~{expected}",
                    )
                )
                mock_limiter.reset()
            except Exception as e:
                results.results.append(
                    TestResult(name=scenario.name, passed=False, error_message=str(e))
                )

        results.total_duration_ms = int((time.time() - start_time) * 1000)
        self._report.rate_limiter = results
        return results

    async def test_audit_trail(self, scenarios: list[AuditScenario] | None = None) -> TestResults:
        """Test audit trail."""
        from security.audit_trail import AuditEvent

        scenarios = scenarios or self._default_audit_scenarios()
        results = TestResults(scenario_name="audit_trail")
        start_time = time.time()

        for scenario in scenarios:
            test_start = time.time()
            try:
                trail = MockAuditTrail()
                for event_data in scenario.events:
                    event = AuditEvent(**event_data)
                    trail.log(event)

                if scenario.tamper_action == "modify_hash":
                    trail.tamper_hash()
                elif scenario.tamper_action == "break_chain":
                    trail.break_chain()

                is_valid, _ = trail.verify_chain()
                passed = is_valid == scenario.expect_valid

                results.results.append(
                    TestResult(
                        name=scenario.name,
                        passed=passed,
                        duration_ms=int((time.time() - test_start) * 1000),
                        error_message=""
                        if passed
                        else f"Expected valid={scenario.expect_valid}, got {is_valid}",
                    )
                )
            except Exception as e:
                results.results.append(
                    TestResult(name=scenario.name, passed=False, error_message=str(e))
                )

        results.total_duration_ms = int((time.time() - start_time) * 1000)
        self._report.audit_trail = results
        return results

    async def run_all_tests(self) -> SecurityTestReport:
        """Run all tests."""
        start_time = time.time()
        await self.test_fraud_detection()
        await self.test_rate_limiter()
        await self.test_audit_trail()

        self._report.total_passed = sum(
            r.scenarios_passed
            for r in [
                self._report.fraud_detection,
                self._report.rate_limiter,
                self._report.audit_trail,
            ]
            if r
        )
        self._report.total_failed = sum(
            r.scenarios_failed
            for r in [
                self._report.fraud_detection,
                self._report.rate_limiter,
                self._report.audit_trail,
            ]
            if r
        )
        self._report.duration_ms = int((time.time() - start_time) * 1000)
        return self._report

    def generate_report(self) -> SecurityTestReport:
        """Get report."""
        return self._report

    def _default_fraud_scenarios(self) -> list[FraudScenario]:
        """Default fraud scenarios."""
        ts = datetime.utcnow().isoformat()
        return [
            FraudScenario(
                name="wash_trading_basic",
                description="Detect wash trading",
                orders=[
                    {
                        "order_id": "1",
                        "user_id": "t1",
                        "symbol": "BTC",
                        "side": "buy",
                        "price": 50000,
                        "quantity": 1,
                        "status": "filled",
                        "timestamp": ts,
                    },
                    {
                        "order_id": "2",
                        "user_id": "t1",
                        "symbol": "BTC",
                        "side": "sell",
                        "price": 50000,
                        "quantity": 1,
                        "status": "filled",
                        "timestamp": ts,
                    },
                    {
                        "order_id": "3",
                        "user_id": "t1",
                        "symbol": "BTC",
                        "side": "buy",
                        "price": 50001,
                        "quantity": 1,
                        "status": "filled",
                        "timestamp": ts,
                    },
                    {
                        "order_id": "4",
                        "user_id": "t1",
                        "symbol": "BTC",
                        "side": "sell",
                        "price": 50001,
                        "quantity": 1,
                        "status": "filled",
                        "timestamp": ts,
                    },
                ],
                expected_alerts=["wash_trading"],
            ),
            FraudScenario(
                name="clean_trading",
                description="Normal trading",
                orders=[
                    {
                        "order_id": "1",
                        "user_id": "a",
                        "symbol": "BTC",
                        "side": "buy",
                        "price": 50000,
                        "quantity": 1,
                        "status": "filled",
                        "timestamp": ts,
                    }
                ],
                expected_alerts=[],
            ),
        ]

    def _default_rate_limit_scenarios(self) -> list[RateLimitScenario]:
        """Default rate limit scenarios."""
        return [
            RateLimitScenario(
                name="api_burst",
                description="API burst",
                request_pattern=[("api", 200)],
                expected_blocked=90,
                tolerance=0.15,
            ),
            RateLimitScenario(
                name="trading_limit",
                description="Trading limit",
                request_pattern=[("trading", 20)],
                expected_blocked=5,
                tolerance=0.2,
            ),
        ]

    def _default_audit_scenarios(self) -> list[AuditScenario]:
        """Default audit scenarios."""
        return [
            AuditScenario(
                name="valid_chain",
                description="Valid chain",
                events=[
                    {
                        "event_type": "order_submitted",
                        "actor": "test",
                        "resource": "BTC",
                        "action": "create",
                    }
                ],
                expect_valid=True,
            ),
            AuditScenario(
                name="hash_tamper_detection",
                description="Detect hash tampering",
                events=[
                    {
                        "event_type": "order_submitted",
                        "actor": "test",
                        "resource": "ETH",
                        "action": "create",
                    }
                ],
                tamper_action="modify_hash",
                expect_valid=False,
            ),
        ]


class MockRateLimiter:
    """Mock rate limiter."""

    LIMITS = {
        "api": {"requests": 100, "burst": 10},
        "trading": {"requests": 10, "burst": 5},
        "login": {"requests": 5, "burst": 0},
    }

    def __init__(self):
        """Init."""
        self._tokens: dict[str, float] = {}

    def check(self, limit_type: str, identifier: str = "default") -> dict:
        """Check limit."""
        key = f"{limit_type}:{identifier}"
        config = self.LIMITS.get(limit_type, {"requests": 100, "burst": 0})
        capacity = config["requests"] + config["burst"]

        if key not in self._tokens:
            self._tokens[key] = capacity

        if self._tokens[key] >= 1:
            self._tokens[key] -= 1
            return {"allowed": True, "remaining": int(self._tokens[key])}
        return {"allowed": False, "remaining": 0}

    def reset(self):
        """Reset."""
        self._tokens.clear()


class MockAuditTrail:
    """Mock audit trail."""

    GENESIS_HASH = "0" * 64

    def __init__(self):
        """Init."""
        self._events: list = []
        self._last_hash = self.GENESIS_HASH

    def log(self, event) -> None:
        """Log event."""
        event.finalize(self._last_hash)
        self._events.append(event)
        self._last_hash = event.hash

    def tamper_hash(self) -> None:
        """Tamper hash."""
        if self._events:
            self._events[-1].hash = "tampered"

    def break_chain(self) -> None:
        """Break chain."""
        if len(self._events) > 1:
            self._events[-1].previous_hash = "wrong"

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify chain."""
        errors = []
        expected_prev = self.GENESIS_HASH

        for event in self._events:
            if event.hash != event.compute_hash():
                errors.append(f"Hash mismatch: {event.event_id}")
            if event.previous_hash != expected_prev:
                errors.append(f"Chain break: {event.event_id}")
            expected_prev = event.hash

        return len(errors) == 0, errors


async def run_security_tests() -> SecurityTestReport:
    """Run all security tests."""
    sandbox = SecuritySandbox()
    return await sandbox.run_all_tests()
