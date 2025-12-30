# Test fixtures for NautilusTrader Auto-Update Pipeline

"""Pytest fixtures for auto_update tests."""

from datetime import datetime
from pathlib import Path

import pytest

from scripts.auto_update.models import (
    AffectedFile,
    AutoUpdateConfig,
    BreakingChange,
    ChangelogData,
    DispatchResult,
    ImpactReport,
    OpenIssue,
    Severity,
    TestResult,
    UpdateResult,
)


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_timestamp() -> datetime:
    """Fixed timestamp for reproducible tests."""
    return datetime(2025, 12, 29, 5, 0, 0)


@pytest.fixture
def sample_open_issue() -> OpenIssue:
    """Sample GitHub issue from changelog."""
    return OpenIssue(
        number=12345,
        title="Fix ADL order handling for Binance",
        state="open",
        labels=["bug", "exchange:binance"],
        created_at=datetime(2025, 12, 28, 10, 0, 0),
        updated_at=datetime(2025, 12, 29, 8, 0, 0),
        author="nautechsystems",
        url="https://github.com/nautechsystems/nautilus_trader/issues/12345",
        comments=5,
    )


@pytest.fixture
def sample_changelog_data(sample_timestamp: datetime) -> ChangelogData:
    """Sample changelog data from N8N-generated JSON."""
    return ChangelogData(
        timestamp=sample_timestamp,
        stable_version="v1.221.0",
        nightly_commits=50,
        breaking_changes=[
            "Removed deprecated `Strategy.on_tick` method, use `on_quote_tick` instead",
            "Changed `BarType.from_str` signature to require venue parameter",
        ],
        open_issues={
            "total": 15500,
            "bugs": 500,
            "features": 15250,
            "bug_list": [
                {"number": 12345, "title": "Fix ADL order handling"},
            ],
            "feature_list": [
                {"number": 12346, "title": "Add new indicator support"},
            ],
        },
    )


@pytest.fixture
def sample_changelog_no_breaking(sample_timestamp: datetime) -> ChangelogData:
    """Changelog data with no breaking changes."""
    return ChangelogData(
        timestamp=sample_timestamp,
        stable_version="v1.221.0",
        nightly_commits=10,
        breaking_changes=[],
        open_issues={},
    )


@pytest.fixture
def sample_breaking_change_high() -> BreakingChange:
    """High severity breaking change."""
    return BreakingChange(
        description="Removed deprecated `Strategy.on_tick` method",
        affected_pattern=r"def on_tick\(",
        severity=Severity.HIGH,
        migration_guide="Replace on_tick with on_quote_tick",
    )


@pytest.fixture
def sample_breaking_change_medium() -> BreakingChange:
    """Medium severity breaking change."""
    return BreakingChange(
        description="Changed `BarType.from_str` signature",
        affected_pattern=r"BarType\.from_str\(",
        severity=Severity.MEDIUM,
        migration_guide="Add venue parameter to BarType.from_str calls",
    )


@pytest.fixture
def sample_breaking_change_critical() -> BreakingChange:
    """Critical severity breaking change (blocks all updates)."""
    return BreakingChange(
        description="Removed Strategy base class entirely",
        affected_pattern=r"from nautilus_trader\.trading\.strategy import Strategy",
        severity=Severity.CRITICAL,
        migration_guide=None,
    )


@pytest.fixture
def sample_affected_file(sample_breaking_change_high: BreakingChange) -> AffectedFile:
    """Sample affected file from grep."""
    return AffectedFile(
        path=Path("strategies/production/btc_momentum.py"),
        line_numbers=[45, 78],
        breaking_change=sample_breaking_change_high,
        can_auto_fix=True,
        fix_type="method_rename",
    )


@pytest.fixture
def sample_impact_report_safe(
    sample_breaking_change_medium: BreakingChange,
    sample_timestamp: datetime,
) -> ImpactReport:
    """Safe impact report (high confidence, can auto-update)."""
    return ImpactReport(
        version="1.222.0",
        previous_version="1.221.0",
        breaking_changes=[sample_breaking_change_medium],
        affected_files=[],
        total_affected_lines=0,
        confidence_score=90.0,
        generated_at=sample_timestamp,
    )


@pytest.fixture
def sample_impact_report_risky(
    sample_breaking_change_high: BreakingChange,
    sample_affected_file: AffectedFile,
    sample_timestamp: datetime,
) -> ImpactReport:
    """Risky impact report (medium confidence, needs review)."""
    return ImpactReport(
        version="1.222.0",
        previous_version="1.221.0",
        breaking_changes=[sample_breaking_change_high],
        affected_files=[sample_affected_file],
        total_affected_lines=12,
        confidence_score=55.0,
        generated_at=sample_timestamp,
    )


@pytest.fixture
def sample_impact_report_blocked(
    sample_breaking_change_critical: BreakingChange,
    sample_timestamp: datetime,
) -> ImpactReport:
    """Blocked impact report (critical breaking change)."""
    return ImpactReport(
        version="1.222.0",
        previous_version="1.221.0",
        breaking_changes=[sample_breaking_change_critical],
        affected_files=[],
        total_affected_lines=0,
        confidence_score=20.0,
        generated_at=sample_timestamp,
    )


@pytest.fixture
def sample_test_result_passed() -> TestResult:
    """Passing test result."""
    return TestResult(
        passed=True,
        total_tests=150,
        failed_tests=0,
        skipped_tests=5,
        failed_test_names=[],
        duration_seconds=45.2,
        coverage_percent=85.5,
    )


@pytest.fixture
def sample_test_result_failed() -> TestResult:
    """Failed test result."""
    return TestResult(
        passed=False,
        total_tests=150,
        failed_tests=3,
        skipped_tests=5,
        failed_test_names=[
            "test_on_tick_handler",
            "test_bar_type_parsing",
            "test_strategy_init",
        ],
        duration_seconds=42.8,
        coverage_percent=82.1,
    )


@pytest.fixture
def sample_update_result_success(
    sample_test_result_passed: TestResult,
    sample_timestamp: datetime,
) -> UpdateResult:
    """Successful update result."""
    return UpdateResult(
        success=True,
        version="1.222.0",
        branch_name="update/v1.222.0",
        pr_url="https://github.com/user/repo/pull/123",
        test_result=sample_test_result_passed,
        error_message=None,
        created_at=sample_timestamp,
    )


@pytest.fixture
def sample_update_result_failure(
    sample_test_result_failed: TestResult,
    sample_timestamp: datetime,
) -> UpdateResult:
    """Failed update result (tests failed)."""
    return UpdateResult(
        success=False,
        version="1.222.0",
        branch_name="update/v1.222.0",
        pr_url=None,
        test_result=sample_test_result_failed,
        error_message="3 tests failed",
        created_at=sample_timestamp,
    )


@pytest.fixture
def sample_dispatch_result_success() -> DispatchResult:
    """Successful dispatch result."""
    return DispatchResult(
        dispatched=True,
        task_prompt="Fix NautilusTrader 1.222.0 breaking changes...",
        agent_id="agent-abc123",
        pr_url="https://github.com/user/repo/pull/456",
        error_message=None,
        timeout_reached=False,
    )


@pytest.fixture
def sample_dispatch_result_timeout() -> DispatchResult:
    """Dispatch result with timeout."""
    return DispatchResult(
        dispatched=True,
        task_prompt="Fix NautilusTrader 1.222.0 breaking changes...",
        agent_id="agent-abc123",
        pr_url=None,
        error_message="Timeout after 1800 seconds",
        timeout_reached=True,
    )


@pytest.fixture
def sample_config() -> AutoUpdateConfig:
    """Sample auto-update configuration."""
    return AutoUpdateConfig(
        changelog_path=Path("docs/nautilus/nautilus-trader-changelog.json"),
        source_dirs=[Path("strategies"), Path("scripts")],
        pyproject_path=Path("pyproject.toml"),
        branch_prefix="update/v",
        remote="origin",
        base_branch="master",
        auto_merge_threshold=85,
        delayed_merge_threshold=65,
        test_timeout_seconds=600,
        claude_timeout_seconds=1800,
        dry_run=False,
        skip_tests=False,
        discord_webhook_url=None,
        email_recipient=None,
    )


@pytest.fixture
def sample_config_dry_run() -> AutoUpdateConfig:
    """Configuration with dry-run enabled."""
    return AutoUpdateConfig(
        changelog_path=Path("docs/nautilus/nautilus-trader-changelog.json"),
        source_dirs=[Path("strategies")],
        pyproject_path=Path("pyproject.toml"),
        dry_run=True,
        skip_tests=True,
    )


# =============================================================================
# Mock Data Fixtures
# =============================================================================


@pytest.fixture
def mock_changelog_json() -> dict:
    """Raw JSON structure from changelog file."""
    return {
        "timestamp": "2025-12-29T00:00:29.251Z",
        "stable_version": "v1.221.0",
        "nightly_commits": 50,
        "breaking_changes": [
            "Removed deprecated `Strategy.on_tick` method, use `on_quote_tick` instead",
            "Changed `BarType.from_str` signature to require venue parameter",
        ],
        "open_issues": {
            "total": 15500,
            "bugs": 500,
            "features": 15250,
            "bug_list": [
                {
                    "number": 12345,
                    "title": "Fix ADL order handling",
                    "state": "open",
                    "labels": ["bug"],
                    "created_at": "2025-12-28T10:00:00Z",
                    "updated_at": "2025-12-29T08:00:00Z",
                    "author": "nautechsystems",
                    "url": "https://github.com/nautechsystems/nautilus_trader/issues/12345",
                    "comments": 5,
                }
            ],
            "feature_list": [],
        },
    }


@pytest.fixture
def tmp_changelog_file(tmp_path: Path, mock_changelog_json: dict) -> Path:
    """Create a temporary changelog.json file."""
    import json

    changelog_file = tmp_path / "nautilus-trader-changelog.json"
    changelog_file.write_text(json.dumps(mock_changelog_json, indent=2))
    return changelog_file


@pytest.fixture
def tmp_pyproject_file(tmp_path: Path) -> Path:
    """Create a temporary pyproject.toml file."""
    pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"
dependencies = [
    "nautilus_trader>=1.221.0",
]
"""
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(pyproject_content)
    return pyproject_file


@pytest.fixture
def tmp_strategy_file(tmp_path: Path) -> Path:
    """Create a temporary strategy file with on_tick method."""
    strategies_dir = tmp_path / "strategies" / "production"
    strategies_dir.mkdir(parents=True)

    strategy_content = '''
from nautilus_trader.trading.strategy import Strategy

class TestStrategy(Strategy):
    """Test strategy with deprecated on_tick."""

    def on_tick(self, tick):
        """Deprecated method."""
        self.process(tick)

    def on_start(self):
        """Start handler."""
        pass
'''
    strategy_file = strategies_dir / "test_strategy.py"
    strategy_file.write_text(strategy_content)
    return strategy_file
