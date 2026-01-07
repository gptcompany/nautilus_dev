# Unit tests for NautilusTrader Auto-Update Models

"""Test Pydantic models for auto_update module."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from scripts.auto_update.models import (
    AffectedFile,
    AutoUpdateConfig,
    BreakingChange,
    ChangelogData,
    ConfidenceLevel,
    DispatchResult,
    ImpactReport,
    OpenIssue,
    Recommendation,
    Severity,
    TestResult,
    UpdateResult,
)


# =============================================================================
# Enum Tests (T004)
# =============================================================================


class TestSeverityEnum:
    """Test Severity enum."""

    def test_severity_values(self):
        """Verify all severity values exist."""
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"

    def test_severity_ordering(self):
        """Verify severity can be compared by name."""
        # String comparison for ordering
        severities = sorted([Severity.LOW, Severity.CRITICAL], key=lambda x: x.value)
        assert severities[0] == Severity.CRITICAL


class TestRecommendationEnum:
    """Test Recommendation enum."""

    def test_recommendation_values(self):
        """Verify all recommendation values exist."""
        assert Recommendation.AUTO == "auto"
        assert Recommendation.DELAYED == "delayed"
        assert Recommendation.MANUAL == "manual"
        assert Recommendation.BLOCKED == "blocked"


class TestConfidenceLevelEnum:
    """Test ConfidenceLevel enum."""

    def test_confidence_level_values(self):
        """Verify all confidence level values exist."""
        assert ConfidenceLevel.VERY_HIGH == "very_high"
        assert ConfidenceLevel.HIGH == "high"
        assert ConfidenceLevel.NEUTRAL == "neutral"
        assert ConfidenceLevel.LOW == "low"


# =============================================================================
# OpenIssue Tests (T005)
# =============================================================================


class TestOpenIssue:
    """Test OpenIssue model."""

    def test_create_open_issue(self, sample_open_issue: OpenIssue):
        """Test creating an OpenIssue from fixture."""
        assert sample_open_issue.number == 12345
        assert sample_open_issue.title == "Fix ADL order handling for Binance"
        assert sample_open_issue.state == "open"
        assert "bug" in sample_open_issue.labels

    def test_open_issue_defaults(self):
        """Test OpenIssue with minimal fields."""
        issue = OpenIssue(number=1, title="Test")
        assert issue.state == "open"
        assert issue.labels == []
        assert issue.comments == 0


# =============================================================================
# ChangelogData Tests (T005)
# =============================================================================


class TestChangelogData:
    """Test ChangelogData model."""

    def test_create_changelog_data(self, sample_changelog_data: ChangelogData):
        """Test creating ChangelogData from fixture."""
        assert sample_changelog_data.stable_version == "v1.221.0"
        assert sample_changelog_data.nightly_commits == 50
        assert len(sample_changelog_data.breaking_changes) == 2

    def test_has_breaking_changes(
        self,
        sample_changelog_data: ChangelogData,
        sample_changelog_no_breaking: ChangelogData,
    ):
        """Test has_breaking_changes property."""
        assert sample_changelog_data.has_breaking_changes is True
        assert sample_changelog_no_breaking.has_breaking_changes is False

    def test_bug_list_property(self, sample_changelog_data: ChangelogData):
        """Test bug_list extraction from open_issues."""
        bugs = sample_changelog_data.bug_list
        assert len(bugs) == 1
        assert bugs[0]["number"] == 12345

    def test_feature_list_property(self, sample_changelog_data: ChangelogData):
        """Test feature_list extraction from open_issues."""
        features = sample_changelog_data.feature_list
        assert len(features) == 1
        assert features[0]["number"] == 12346

    def test_parse_from_json(self, mock_changelog_json: dict):
        """Test parsing ChangelogData from raw JSON."""
        data = ChangelogData.model_validate(mock_changelog_json)
        assert data.stable_version == "v1.221.0"
        assert data.nightly_commits == 50


# =============================================================================
# BreakingChange Tests (T006)
# =============================================================================


class TestBreakingChange:
    """Test BreakingChange model."""

    def test_create_breaking_change(self, sample_breaking_change_high: BreakingChange):
        """Test creating BreakingChange from fixture."""
        assert "on_tick" in sample_breaking_change_high.description
        assert sample_breaking_change_high.severity == Severity.HIGH
        assert sample_breaking_change_high.migration_guide is not None

    def test_breaking_change_minimal(self):
        """Test BreakingChange with minimal fields."""
        bc = BreakingChange(description="Some change")
        assert bc.severity == Severity.MEDIUM  # Default
        assert bc.affected_pattern == ""
        assert bc.migration_guide is None

    def test_breaking_change_critical(self, sample_breaking_change_critical: BreakingChange):
        """Test critical breaking change."""
        assert sample_breaking_change_critical.severity == Severity.CRITICAL
        assert sample_breaking_change_critical.migration_guide is None


# =============================================================================
# AffectedFile Tests (T006)
# =============================================================================


class TestAffectedFile:
    """Test AffectedFile model."""

    def test_create_affected_file(self, sample_affected_file: AffectedFile):
        """Test creating AffectedFile from fixture."""
        assert sample_affected_file.path == Path("strategies/production/btc_momentum.py")
        assert sample_affected_file.line_numbers == [45, 78]
        assert sample_affected_file.can_auto_fix is True
        assert sample_affected_file.fix_type == "method_rename"

    def test_affected_file_not_fixable(self, sample_breaking_change_critical: BreakingChange):
        """Test AffectedFile that cannot be auto-fixed."""
        af = AffectedFile(
            path=Path("strategies/core.py"),
            line_numbers=[1],
            breaking_change=sample_breaking_change_critical,
            can_auto_fix=False,
        )
        assert af.can_auto_fix is False
        assert af.fix_type is None


# =============================================================================
# ImpactReport Tests (T007)
# =============================================================================


class TestImpactReport:
    """Test ImpactReport model with validation logic."""

    def test_safe_impact_report(self, sample_impact_report_safe: ImpactReport):
        """Test safe impact report (high confidence)."""
        assert sample_impact_report_safe.confidence_score == 90.0
        assert sample_impact_report_safe.confidence_level == ConfidenceLevel.VERY_HIGH
        assert sample_impact_report_safe.can_auto_update is True
        assert sample_impact_report_safe.recommendation == Recommendation.AUTO

    def test_risky_impact_report(self, sample_impact_report_risky: ImpactReport):
        """Test risky impact report (needs review)."""
        assert sample_impact_report_risky.confidence_score == 55.0
        assert sample_impact_report_risky.confidence_level == ConfidenceLevel.NEUTRAL
        assert sample_impact_report_risky.can_auto_update is False
        assert sample_impact_report_risky.recommendation == Recommendation.MANUAL

    def test_blocked_impact_report(self, sample_impact_report_blocked: ImpactReport):
        """Test blocked impact report (critical change)."""
        assert sample_impact_report_blocked.recommendation == Recommendation.BLOCKED
        assert sample_impact_report_blocked.can_auto_update is False

    def test_confidence_level_auto_correction(self):
        """Test that confidence_level is auto-corrected from score."""
        # Create with mismatched level
        report = ImpactReport(
            version="1.0.0",
            confidence_score=90.0,
            confidence_level=ConfidenceLevel.LOW,  # Will be corrected
        )
        # After validation, level should match score
        assert report.confidence_level == ConfidenceLevel.VERY_HIGH

    def test_should_dispatch_claude(
        self,
        sample_impact_report_risky: ImpactReport,
        sample_impact_report_blocked: ImpactReport,
    ):
        """Test should_dispatch_claude logic."""
        # Risky (MANUAL) -> should dispatch
        assert sample_impact_report_risky.should_dispatch_claude() is True

        # Blocked (CRITICAL) -> should NOT dispatch
        assert sample_impact_report_blocked.should_dispatch_claude() is False

    def test_confidence_thresholds(self):
        """Test all confidence threshold boundaries."""
        # VERY_HIGH: >= 85
        report_85 = ImpactReport(version="1.0.0", confidence_score=85.0)
        assert report_85.confidence_level == ConfidenceLevel.VERY_HIGH

        # HIGH: 65-84
        report_65 = ImpactReport(version="1.0.0", confidence_score=65.0)
        assert report_65.confidence_level == ConfidenceLevel.HIGH
        report_84 = ImpactReport(version="1.0.0", confidence_score=84.9)
        assert report_84.confidence_level == ConfidenceLevel.HIGH

        # NEUTRAL: 40-64
        report_40 = ImpactReport(version="1.0.0", confidence_score=40.0)
        assert report_40.confidence_level == ConfidenceLevel.NEUTRAL
        report_64 = ImpactReport(version="1.0.0", confidence_score=64.9)
        assert report_64.confidence_level == ConfidenceLevel.NEUTRAL

        # LOW: < 40
        report_39 = ImpactReport(version="1.0.0", confidence_score=39.9)
        assert report_39.confidence_level == ConfidenceLevel.LOW

    def test_confidence_score_bounds(self):
        """Test confidence score validation bounds."""
        # Valid bounds
        ImpactReport(version="1.0.0", confidence_score=0.0)
        ImpactReport(version="1.0.0", confidence_score=100.0)

        # Invalid bounds
        with pytest.raises(ValidationError):
            ImpactReport(version="1.0.0", confidence_score=-1.0)
        with pytest.raises(ValidationError):
            ImpactReport(version="1.0.0", confidence_score=101.0)


# =============================================================================
# TestResult Tests (T008)
# =============================================================================


class TestTestResult:
    """Test TestResult model."""

    def test_passed_test_result(self, sample_test_result_passed: TestResult):
        """Test passing test result."""
        assert sample_test_result_passed.passed is True
        assert sample_test_result_passed.total_tests == 150
        assert sample_test_result_passed.failed_tests == 0
        assert sample_test_result_passed.passed_tests == 145  # 150 - 0 - 5

    def test_failed_test_result(self, sample_test_result_failed: TestResult):
        """Test failed test result."""
        assert sample_test_result_failed.passed is False
        assert sample_test_result_failed.failed_tests == 3
        assert len(sample_test_result_failed.failed_test_names) == 3

    def test_passed_tests_calculation(self):
        """Test passed_tests property calculation."""
        result = TestResult(total_tests=100, failed_tests=10, skipped_tests=5)
        assert result.passed_tests == 85


# =============================================================================
# UpdateResult Tests (T008)
# =============================================================================


class TestUpdateResult:
    """Test UpdateResult model."""

    def test_successful_update(self, sample_update_result_success: UpdateResult):
        """Test successful update result."""
        assert sample_update_result_success.success is True
        assert sample_update_result_success.branch_name == "update/v1.222.0"
        assert sample_update_result_success.pr_url is not None

    def test_failed_update(self, sample_update_result_failure: UpdateResult):
        """Test failed update result."""
        assert sample_update_result_failure.success is False
        assert sample_update_result_failure.error_message == "3 tests failed"

    def test_success_requires_branch_name(self):
        """Test that success=True requires branch_name."""
        with pytest.raises(ValidationError):
            UpdateResult(success=True, version="1.0.0", branch_name="")


# =============================================================================
# DispatchResult Tests (T009)
# =============================================================================


class TestDispatchResult:
    """Test DispatchResult model."""

    def test_successful_dispatch(self, sample_dispatch_result_success: DispatchResult):
        """Test successful dispatch result."""
        assert sample_dispatch_result_success.dispatched is True
        assert sample_dispatch_result_success.agent_id is not None
        assert sample_dispatch_result_success.pr_url is not None

    def test_timeout_dispatch(self, sample_dispatch_result_timeout: DispatchResult):
        """Test dispatch result with timeout."""
        assert sample_dispatch_result_timeout.dispatched is True
        assert sample_dispatch_result_timeout.timeout_reached is True
        assert sample_dispatch_result_timeout.pr_url is None


# =============================================================================
# AutoUpdateConfig Tests (T010)
# =============================================================================


class TestAutoUpdateConfig:
    """Test AutoUpdateConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AutoUpdateConfig()
        assert config.changelog_path == Path("docs/nautilus/nautilus-trader-changelog.json")
        assert len(config.source_dirs) == 3
        assert config.auto_merge_threshold == 85
        assert config.delayed_merge_threshold == 65

    def test_custom_config(self, sample_config: AutoUpdateConfig):
        """Test custom configuration from fixture."""
        assert sample_config.dry_run is False
        assert sample_config.skip_tests is False

    def test_dry_run_config(self, sample_config_dry_run: AutoUpdateConfig):
        """Test dry-run configuration."""
        assert sample_config_dry_run.dry_run is True
        assert sample_config_dry_run.skip_tests is True

    def test_threshold_validation(self):
        """Test threshold bounds validation."""
        # Valid thresholds
        AutoUpdateConfig(auto_merge_threshold=0)
        AutoUpdateConfig(auto_merge_threshold=100)

        # Invalid thresholds
        with pytest.raises(ValidationError):
            AutoUpdateConfig(auto_merge_threshold=-1)
        with pytest.raises(ValidationError):
            AutoUpdateConfig(auto_merge_threshold=101)

    def test_timeout_validation(self):
        """Test timeout bounds validation."""
        # Valid timeouts
        AutoUpdateConfig(test_timeout_seconds=60)
        AutoUpdateConfig(claude_timeout_seconds=300)

        # Invalid timeouts
        with pytest.raises(ValidationError):
            AutoUpdateConfig(test_timeout_seconds=30)  # Below min
        with pytest.raises(ValidationError):
            AutoUpdateConfig(claude_timeout_seconds=100)  # Below min
