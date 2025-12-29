# End-to-end integration tests for NautilusTrader Auto-Update Pipeline

"""Integration tests covering the full update workflow."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


from scripts.auto_update.analyzer import analyze_breaking_changes
from scripts.auto_update.models import ChangelogEntry, Severity
from scripts.auto_update.parser import parse_changelog


# =============================================================================
# T075: End-to-End Integration Tests
# =============================================================================


class TestFullUpdateWorkflow:
    """Test complete update workflow from changelog to notification."""

    def test_parse_and_analyze_workflow(self, tmp_path: Path):
        """Test parsing changelog and analyzing impact."""
        # Create sample changelog
        changelog_data = {
            "current_version": "1.221.0",
            "latest_version": "1.222.0",
            "breaking_changes": [
                {
                    "description": "Renamed OldClass to NewClass",
                    "version": "1.222.0",
                    "category": "API",
                }
            ],
            "commits": [
                {
                    "sha": "abc123",
                    "message": "refactor: rename OldClass to NewClass",
                    "date": "2025-01-15",
                }
            ],
            "last_updated": "2025-01-15T10:00:00Z",
        }

        changelog_file = tmp_path / "changelog.json"
        changelog_file.write_text(json.dumps(changelog_data))

        # Parse changelog
        result = parse_changelog(changelog_file)

        assert result is not None
        assert result.current_version == "1.221.0"
        assert result.latest_version == "1.222.0"
        assert len(result.breaking_changes) == 1

        # Create a sample codebase file for analysis
        codebase_dir = tmp_path / "strategies"
        codebase_dir.mkdir()
        strategy_file = codebase_dir / "my_strategy.py"
        strategy_file.write_text("""
from nautilus_trader.model import OldClass

class MyStrategy:
    def __init__(self):
        self.obj = OldClass()
""")

        # Analyze breaking changes against codebase
        impact = analyze_breaking_changes(
            changelog=result,
            codebase_path=tmp_path,
        )

        assert impact is not None
        assert impact.version == "1.222.0"
        assert impact.previous_version == "1.221.0"

    def test_changelog_entry_creation(self):
        """Test ChangelogEntry model creation."""
        entry = ChangelogEntry(
            version="1.222.0",
            date="2025-01-15",
            changes=["Added new feature", "Fixed bug"],
            breaking_changes=["Renamed OldAPI to NewAPI"],
            deprecations=["Deprecated old_method()"],
        )

        assert entry.version == "1.222.0"
        assert len(entry.changes) == 2
        assert len(entry.breaking_changes) == 1
        assert entry.has_breaking_changes is True

    def test_severity_ordering(self):
        """Test Severity enum ordering for impact assessment."""
        assert Severity.CRITICAL.value > Severity.HIGH.value
        assert Severity.HIGH.value > Severity.MEDIUM.value
        assert Severity.MEDIUM.value > Severity.LOW.value

    @patch("scripts.auto_update.notifier.send_discord_notification")
    def test_notification_after_analysis(self, mock_discord: MagicMock, tmp_path: Path):
        """Test notification is sent after analysis."""
        from scripts.auto_update.notifier import format_update_notification

        # Format notification message
        message = format_update_notification(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes_count=2,
            pr_url="https://github.com/org/repo/pull/123",
            status="completed",
        )

        assert "1.222.0" in message
        assert "1.221.0" in message
        assert "2" in message  # breaking changes count
        assert "https://github.com" in message

    def test_dry_run_preserves_state(self, tmp_path: Path):
        """Test dry-run mode doesn't modify anything."""
        from scripts.auto_update.dispatcher import dispatch_claude_code
        from scripts.auto_update.models import (
            AffectedFile,
            BreakingChange,
            ConfidenceLevel,
            ImpactReport,
            Recommendation,
        )

        bc = BreakingChange(
            description="Test change",
            severity=Severity.LOW,
            affected_pattern="test",
        )
        af = AffectedFile(
            path=tmp_path / "test.py",
            line_numbers=[1],
            breaking_change=bc,
            can_auto_fix=True,
        )
        report = ImpactReport(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[bc],
            affected_files=[af],
            total_affected_lines=1,
            confidence_score=90.0,
            confidence_level=ConfidenceLevel.HIGH,
            can_auto_update=True,
            recommendation=Recommendation.AUTO,
        )

        result = dispatch_claude_code(
            impact_report=report,
            working_dir=tmp_path,
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["agent_id"] is None


class TestModuleIntegration:
    """Test integration between modules."""

    def test_parser_to_analyzer_types(self, tmp_path: Path):
        """Test type compatibility between parser and analyzer."""
        # Create minimal changelog
        changelog_data = {
            "current_version": "1.221.0",
            "latest_version": "1.221.0",
            "breaking_changes": [],
            "commits": [],
            "last_updated": "2025-01-15T10:00:00Z",
        }

        changelog_file = tmp_path / "changelog.json"
        changelog_file.write_text(json.dumps(changelog_data))

        # Parse returns Changelog type
        changelog = parse_changelog(changelog_file)

        # Analyzer accepts Changelog type
        impact = analyze_breaking_changes(
            changelog=changelog,
            codebase_path=tmp_path,
        )

        assert impact.version == "1.221.0"

    def test_validator_result_types(self, tmp_path: Path):
        """Test validator result structure."""
        from scripts.auto_update.validator import parse_test_results

        # Minimal pytest JSON output
        json_output = json.dumps(
            {
                "summary": {"total": 5, "passed": 5, "failed": 0},
                "tests": [],
            }
        )

        result = parse_test_results(json_output)

        assert result.total == 5
        assert result.passed == 5
        assert result.failed_tests == 0
        assert result.success is True

    def test_auto_fix_detection(self):
        """Test auto-fix type detection."""
        from scripts.auto_update.auto_fix import detect_fix_type

        # Import renames
        assert detect_fix_type("Renamed OldClass to NewClass") in ("import", "method")

        # Method renames
        assert detect_fix_type("old_method renamed to new_method") in (
            "import",
            "method",
        )

        # Unknown patterns return None
        assert detect_fix_type("Some random change") is None

    def test_git_ops_branch_naming(self):
        """Test git branch naming convention."""
        from scripts.auto_update.git_ops import create_update_branch

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = create_update_branch(
                version="1.222.0",
                working_dir=Path("/tmp/test"),
                dry_run=True,
            )

            assert result["success"] is True
            assert result["branch_name"] == "update/nautilus-1.222.0"


class TestErrorRecovery:
    """Test error handling and recovery."""

    def test_invalid_changelog_path(self, tmp_path: Path):
        """Test handling of invalid changelog path."""
        result = parse_changelog(tmp_path / "nonexistent.json")
        assert result is None

    def test_malformed_json_changelog(self, tmp_path: Path):
        """Test handling of malformed JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")

        result = parse_changelog(bad_file)
        assert result is None

    def test_empty_changelog(self, tmp_path: Path):
        """Test handling of empty changelog."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}")

        result = parse_changelog(empty_file)
        # Should return None or empty Changelog depending on implementation
        assert result is None or result.current_version == ""

    def test_analyzer_with_no_codebase(self, tmp_path: Path):
        """Test analyzer when codebase directory is empty."""
        changelog_data = {
            "current_version": "1.221.0",
            "latest_version": "1.222.0",
            "breaking_changes": [
                {
                    "description": "Changed API",
                    "version": "1.222.0",
                    "category": "API",
                }
            ],
            "commits": [],
            "last_updated": "2025-01-15T10:00:00Z",
        }

        changelog_file = tmp_path / "changelog.json"
        changelog_file.write_text(json.dumps(changelog_data))

        changelog = parse_changelog(changelog_file)
        empty_codebase = tmp_path / "empty_codebase"
        empty_codebase.mkdir()

        # Should handle gracefully
        impact = analyze_breaking_changes(
            changelog=changelog,
            codebase_path=empty_codebase,
        )

        assert impact is not None
        assert len(impact.affected_files) == 0
