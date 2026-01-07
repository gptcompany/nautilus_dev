# Unit tests for NautilusTrader Auto-Update Analyzer

"""Test analyzer module for auto_update."""

from pathlib import Path

from scripts.auto_update.analyzer import (
    calculate_confidence,
    classify_severity,
    generate_impact_report,
    grep_codebase,
)
from scripts.auto_update.models import (
    AffectedFile,
    BreakingChange,
    ConfidenceLevel,
    ImpactReport,
    Recommendation,
    Severity,
)

# =============================================================================
# T021: Test grep_codebase
# =============================================================================


class TestGrepCodebase:
    """Test grep_codebase function."""

    def test_grep_finds_pattern(self, tmp_strategy_file: Path):
        """Test grep finds matching pattern in file."""
        pattern = r"def on_tick\("
        results = grep_codebase(
            pattern=pattern,
            source_dirs=[tmp_strategy_file.parent.parent],
        )
        assert len(results) > 0
        assert any("on_tick" in str(r) for r in results)

    def test_grep_returns_line_numbers(self, tmp_strategy_file: Path):
        """Test grep returns correct line numbers."""
        pattern = r"def on_tick\("
        results = grep_codebase(
            pattern=pattern,
            source_dirs=[tmp_strategy_file.parent.parent],
        )
        # Should find the on_tick definition
        assert len(results) > 0
        match = results[0]
        assert "line" in match
        assert match["line"] > 0

    def test_grep_no_matches(self, tmp_path: Path):
        """Test grep returns empty when no matches."""
        results = grep_codebase(
            pattern=r"nonexistent_function_xyz",
            source_dirs=[tmp_path],
        )
        assert results == []

    def test_grep_multiple_files(self, tmp_path: Path):
        """Test grep searches multiple files."""
        # Create two strategy files
        strategies_dir = tmp_path / "strategies"
        strategies_dir.mkdir()

        file1 = strategies_dir / "strat1.py"
        file1.write_text("def on_tick(self): pass")

        file2 = strategies_dir / "strat2.py"
        file2.write_text("def on_tick(self): pass")

        results = grep_codebase(
            pattern=r"def on_tick\(",
            source_dirs=[strategies_dir],
        )
        assert len(results) == 2

    def test_grep_respects_source_dirs(self, tmp_path: Path):
        """Test grep only searches specified directories."""
        # Create file in included dir
        included = tmp_path / "included"
        included.mkdir()
        (included / "file.py").write_text("def on_tick(): pass")

        # Create file in excluded dir
        excluded = tmp_path / "excluded"
        excluded.mkdir()
        (excluded / "file.py").write_text("def on_tick(): pass")

        results = grep_codebase(
            pattern=r"def on_tick\(",
            source_dirs=[included],  # Only include 'included'
        )
        assert len(results) == 1
        assert "included" in str(results[0]["path"])


# =============================================================================
# T022: Test classify_severity
# =============================================================================


class TestClassifySeverity:
    """Test classify_severity function."""

    def test_classify_critical_import_removal(self):
        """Test CRITICAL severity for import removal."""
        severity = classify_severity("Removed module nautilus_trader.legacy")
        assert severity == Severity.CRITICAL

    def test_classify_high_method_removal(self):
        """Test HIGH severity for method removal."""
        severity = classify_severity("Removed deprecated method on_tick")
        assert severity == Severity.HIGH

    def test_classify_medium_deprecation(self):
        """Test MEDIUM severity for deprecation."""
        severity = classify_severity("Deprecated parameter use_legacy_mode")
        assert severity == Severity.MEDIUM

    def test_classify_default_medium(self):
        """Test default severity is MEDIUM."""
        severity = classify_severity("Some unknown change")
        assert severity == Severity.MEDIUM


# =============================================================================
# T023: Test calculate_confidence
# =============================================================================


class TestCalculateConfidence:
    """Test calculate_confidence function."""

    def test_confidence_no_breaking_changes(self):
        """Test high confidence when no breaking changes."""
        score = calculate_confidence(
            breaking_changes=[],
            affected_files=[],
            days_since_release=3,
        )
        assert score >= 85  # VERY_HIGH

    def test_confidence_with_critical_change(self, sample_breaking_change_critical: BreakingChange):
        """Test low confidence with CRITICAL breaking change."""
        score = calculate_confidence(
            breaking_changes=[sample_breaking_change_critical],
            affected_files=[],
            days_since_release=3,
        )
        assert score < 40  # LOW

    def test_confidence_with_many_affected_files(self, sample_breaking_change_high: BreakingChange):
        """Test lower confidence with many affected files."""
        affected = [
            AffectedFile(
                path=Path(f"file{i}.py"),
                line_numbers=[1],
                breaking_change=sample_breaking_change_high,
            )
            for i in range(10)
        ]
        score = calculate_confidence(
            breaking_changes=[sample_breaking_change_high],
            affected_files=affected,
            days_since_release=3,
        )
        # Many files affected should lower confidence
        assert score < 70

    def test_confidence_fresh_release(self, sample_breaking_change_medium: BreakingChange):
        """Test lower confidence for very fresh releases."""
        score = calculate_confidence(
            breaking_changes=[sample_breaking_change_medium],
            affected_files=[],
            days_since_release=0,  # Just released
        )
        # Fresh release should lower confidence
        assert score < 85


# =============================================================================
# T024: Test generate_impact_report
# =============================================================================


class TestGenerateImpactReport:
    """Test generate_impact_report function."""

    def test_generate_report_basic(
        self,
        sample_breaking_change_medium: BreakingChange,
    ):
        """Test generating basic impact report."""
        report = generate_impact_report(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[sample_breaking_change_medium],
            affected_files=[],
        )
        assert isinstance(report, ImpactReport)
        assert report.version == "1.222.0"
        assert report.previous_version == "1.221.0"

    def test_generate_report_with_affected_files(
        self,
        sample_breaking_change_high: BreakingChange,
        sample_affected_file: AffectedFile,
    ):
        """Test report includes affected files."""
        report = generate_impact_report(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[sample_breaking_change_high],
            affected_files=[sample_affected_file],
        )
        assert len(report.affected_files) == 1
        assert report.total_affected_lines > 0

    def test_generate_report_confidence_level(
        self,
        sample_breaking_change_medium: BreakingChange,
    ):
        """Test report has correct confidence level."""
        report = generate_impact_report(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[sample_breaking_change_medium],
            affected_files=[],
        )
        # Medium change, no affected files -> should be HIGH or VERY_HIGH
        assert report.confidence_level in [
            ConfidenceLevel.VERY_HIGH,
            ConfidenceLevel.HIGH,
        ]

    def test_generate_report_blocked_on_critical(
        self,
        sample_breaking_change_critical: BreakingChange,
    ):
        """Test report is BLOCKED with CRITICAL change."""
        report = generate_impact_report(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[sample_breaking_change_critical],
            affected_files=[],
        )
        assert report.recommendation == Recommendation.BLOCKED
        assert report.can_auto_update is False

    def test_generate_report_auto_on_safe(self):
        """Test report is AUTO with no breaking changes."""
        report = generate_impact_report(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[],
            affected_files=[],
        )
        assert report.recommendation == Recommendation.AUTO
        assert report.can_auto_update is True
