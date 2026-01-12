"""Tests for sandbox module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from security.sandbox.config import (
    AnalysisResult,
    DockerSandboxConfig,
    ExecutionResult,
    MalwareSandboxConfig,
    NetworkMode,
    SandboxConfig,
    SecuritySandboxConfig,
    TestResult,
    TestResults,
    Threat,
)
from security.sandbox.docker_sandbox import DockerSandbox
from security.sandbox.malware_sandbox import MalwareSandbox
from security.sandbox.security_sandbox import (
    AuditScenario,
    FraudScenario,
    MockAuditTrail,
    MockRateLimiter,
    RateLimitScenario,
    SecuritySandbox,
    SecurityTestReport,
)


class TestSandboxConfig:
    """Test sandbox config classes."""

    def test_base_config_defaults(self):
        """Test base config defaults."""
        config = SandboxConfig()
        assert config.timeout_seconds == 300
        assert config.memory_limit == "512m"
        assert config.cpu_limit == 2.0
        assert config.network_mode == NetworkMode.NONE
        assert config.read_only is True

    def test_malware_config_defaults(self):
        """Test malware config defaults."""
        config = MalwareSandboxConfig()
        assert config.timeout_seconds == 60
        assert config.memory_limit == "256m"
        assert config.max_file_size_mb == 10
        assert config.enable_bandit is True

    def test_security_config_defaults(self):
        """Test security config defaults."""
        config = SecuritySandboxConfig()
        assert config.timeout_seconds == 600
        assert config.network_mode == NetworkMode.INTERNAL
        assert config.redis_host == "security-sandbox-redis"

    def test_docker_config_defaults(self):
        """Test docker config defaults."""
        config = DockerSandboxConfig()
        assert config.image == "python:3.12-slim"
        assert config.environment == {}
        assert config.volumes == []


class TestThreat:
    """Test Threat class."""

    def test_threat_to_dict(self):
        """Test threat serialization."""
        threat = Threat(
            type="malware",
            severity="high",
            description="Detected malware",
            location="/path/to/file",
            confidence=0.95,
        )
        result = threat.to_dict()
        assert result["type"] == "malware"
        assert result["severity"] == "high"
        assert result["confidence"] == 0.95


class TestAnalysisResult:
    """Test AnalysisResult class."""

    def test_analysis_result_to_dict(self):
        """Test analysis result serialization."""
        result = AnalysisResult(
            is_clean=False,
            threats=[Threat(type="test", severity="low", description="test threat")],
            scan_duration_ms=100,
            file_hash="abc123",
        )
        data = result.to_dict()
        assert data["is_clean"] is False
        assert len(data["threats"]) == 1
        assert data["scan_duration_ms"] == 100


class TestExecutionResult:
    """Test ExecutionResult class."""

    def test_success_property(self):
        """Test success property."""
        result = ExecutionResult(exit_code=0, stdout="ok", stderr="")
        assert result.success is True

        result = ExecutionResult(exit_code=1, stdout="", stderr="error")
        assert result.success is False

        result = ExecutionResult(exit_code=0, stdout="", stderr="", timed_out=True)
        assert result.success is False


class TestTestResults:
    """Test TestResults class."""

    def test_scenarios_passed(self):
        """Test scenarios passed count."""
        results = TestResults(
            scenario_name="test",
            results=[
                TestResult(name="t1", passed=True),
                TestResult(name="t2", passed=True),
                TestResult(name="t3", passed=False),
            ],
        )
        assert results.scenarios_passed == 2
        assert results.scenarios_failed == 1
        assert results.all_passed is False


class TestMalwareSandbox:
    """Test MalwareSandbox class."""

    @patch("subprocess.run")
    def test_ensure_image_exists(self, mock_run):
        """Test image existence check."""
        mock_run.return_value = MagicMock(returncode=0)
        sandbox = MalwareSandbox()
        assert sandbox._ensure_image_exists() is True

    def test_analyze_file_not_found(self):
        """Test file not found error."""
        sandbox = MalwareSandbox()
        result = sandbox.analyze_file(Path("/nonexistent/file.py"))
        assert result.is_clean is False
        assert result.threats[0].type == "file_not_found"

    def test_analyze_file_too_large(self, tmp_path):
        """Test file too large error."""
        config = MalwareSandboxConfig(max_file_size_mb=0)
        sandbox = MalwareSandbox(config=config)
        test_file = tmp_path / "large.py"
        test_file.write_text("x" * 1000)
        result = sandbox.analyze_file(test_file)
        assert result.is_clean is False
        assert result.threats[0].type == "file_too_large"


class TestDockerSandbox:
    """Test DockerSandbox class."""

    def test_build_docker_command_basic(self):
        """Test basic docker command building."""
        sandbox = DockerSandbox()
        cmd = sandbox._build_docker_command("echo hello")
        assert "docker" in cmd
        assert "run" in cmd
        assert "--rm" in cmd

    def test_build_docker_command_with_network_none(self):
        """Test docker command with network none."""
        config = DockerSandboxConfig(network_mode=NetworkMode.NONE)
        sandbox = DockerSandbox(config=config)
        cmd = sandbox._build_docker_command("test")
        assert "--network" in cmd
        assert "none" in cmd

    def test_build_docker_command_with_environment(self):
        """Test docker command with environment."""
        config = DockerSandboxConfig(environment={"FOO": "bar"})
        sandbox = DockerSandbox(config=config)
        cmd = sandbox._build_docker_command("test")
        assert "-e" in cmd
        assert "FOO=bar" in cmd


class TestMockRateLimiter:
    """Test MockRateLimiter."""

    def test_allows_initial_requests(self):
        """Test initial requests allowed."""
        limiter = MockRateLimiter()
        result = limiter.check("api")
        assert result["allowed"] is True

    def test_blocks_after_limit(self):
        """Test blocking after limit."""
        limiter = MockRateLimiter()
        for _ in range(110):
            limiter.check("api")
        result = limiter.check("api")
        assert result["allowed"] is False

    def test_reset(self):
        """Test reset."""
        limiter = MockRateLimiter()
        for _ in range(110):
            limiter.check("api")
        limiter.reset()
        result = limiter.check("api")
        assert result["allowed"] is True


class TestMockAuditTrail:
    """Test MockAuditTrail."""

    def test_valid_chain(self):
        """Test valid chain verification."""
        trail = MockAuditTrail()
        event = MagicMock()
        event.hash = "hash1"
        event.previous_hash = trail.GENESIS_HASH
        event.compute_hash.return_value = "hash1"

        trail.log(event)
        is_valid, errors = trail.verify_chain()
        assert is_valid is True
        assert len(errors) == 0

    def test_tamper_hash_detection(self):
        """Test hash tampering detection."""
        trail = MockAuditTrail()
        event = MagicMock()
        event.hash = "original_hash"
        event.previous_hash = trail.GENESIS_HASH
        event.compute_hash.return_value = "original_hash"

        trail.log(event)
        trail.tamper_hash()

        is_valid, errors = trail.verify_chain()
        assert is_valid is False
        assert len(errors) > 0


class TestSecuritySandbox:
    """Test SecuritySandbox class."""

    def test_init(self):
        """Test initialization."""
        sandbox = SecuritySandbox()
        assert sandbox.config is not None
        assert sandbox._report is not None

    def test_generate_report(self):
        """Test report generation."""
        sandbox = SecuritySandbox()
        report = sandbox.generate_report()
        assert isinstance(report, SecurityTestReport)


class TestScenarios:
    """Test scenario classes."""

    def test_fraud_scenario(self):
        """Test FraudScenario."""
        scenario = FraudScenario(
            name="test",
            description="test scenario",
            orders=[{"order_id": "1"}],
            expected_alerts=["wash_trading"],
        )
        assert scenario.name == "test"
        assert len(scenario.orders) == 1

    def test_rate_limit_scenario(self):
        """Test RateLimitScenario."""
        scenario = RateLimitScenario(
            name="test",
            description="test scenario",
            request_pattern=[("api", 100)],
            expected_blocked=10,
        )
        assert scenario.tolerance == 0.1

    def test_audit_scenario(self):
        """Test AuditScenario."""
        scenario = AuditScenario(
            name="test", description="test scenario", events=[{"event_type": "test"}]
        )
        assert scenario.expect_valid is True
        assert scenario.tamper_action is None
