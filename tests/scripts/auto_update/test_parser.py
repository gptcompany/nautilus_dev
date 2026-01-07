# Unit tests for NautilusTrader Auto-Update Parser

"""Test parser module for auto_update."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts.auto_update.models import BreakingChange, ChangelogData, Severity
from scripts.auto_update.parser import (
    detect_update_available,
    extract_breaking_changes,
    get_current_version,
    load_changelog_json,
    parse_changelog,
)

# =============================================================================
# T013: Test parse_changelog
# =============================================================================


class TestParseChangelog:
    """Test parse_changelog function."""

    def test_parse_changelog_from_file(self, tmp_changelog_file: Path):
        """Test parsing changelog from file path."""
        result = parse_changelog(tmp_changelog_file)
        assert isinstance(result, ChangelogData)
        assert result.stable_version == "v1.221.0"
        assert result.nightly_commits == 50

    def test_parse_changelog_with_breaking_changes(self, tmp_changelog_file: Path):
        """Test parsing changelog extracts breaking changes."""
        result = parse_changelog(tmp_changelog_file)
        assert len(result.breaking_changes) == 2
        assert "on_tick" in result.breaking_changes[0]

    def test_parse_changelog_from_dict(self, mock_changelog_json: dict):
        """Test parsing changelog from dict."""
        result = parse_changelog(mock_changelog_json)
        assert result.stable_version == "v1.221.0"

    def test_parse_changelog_missing_file(self, tmp_path: Path):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            parse_changelog(tmp_path / "missing.json")

    def test_parse_changelog_invalid_json(self, tmp_path: Path):
        """Test parsing invalid JSON raises error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ not valid json }")
        with pytest.raises(json.JSONDecodeError):
            parse_changelog(bad_file)


# =============================================================================
# T014: Test extract_breaking_changes
# =============================================================================


class TestExtractBreakingChanges:
    """Test extract_breaking_changes function."""

    def test_extract_breaking_changes_basic(self, sample_changelog_data: ChangelogData):
        """Test extracting breaking changes from changelog."""
        changes = extract_breaking_changes(sample_changelog_data)
        assert len(changes) == 2
        assert all(isinstance(c, BreakingChange) for c in changes)

    def test_extract_breaking_changes_severity(self, sample_changelog_data: ChangelogData):
        """Test breaking changes have severity assigned."""
        changes = extract_breaking_changes(sample_changelog_data)
        # on_tick removal is HIGH severity (method removal)
        on_tick_change = next(c for c in changes if "on_tick" in c.description)
        assert on_tick_change.severity in [Severity.HIGH, Severity.MEDIUM]

    def test_extract_breaking_changes_patterns(self, sample_changelog_data: ChangelogData):
        """Test breaking changes have grep patterns."""
        changes = extract_breaking_changes(sample_changelog_data)
        for change in changes:
            assert change.affected_pattern != "" or change.severity == Severity.LOW

    def test_extract_breaking_changes_empty(self, sample_changelog_no_breaking: ChangelogData):
        """Test extracting from changelog with no breaking changes."""
        changes = extract_breaking_changes(sample_changelog_no_breaking)
        assert changes == []

    def test_extract_breaking_changes_with_migration_guide(self):
        """Test that migration hints are extracted when present."""
        changelog = ChangelogData(
            timestamp=datetime.now(),
            stable_version="v1.221.0",
            breaking_changes=[
                "Removed `Strategy.on_tick` method, use `on_quote_tick` instead",
            ],
        )
        changes = extract_breaking_changes(changelog)
        assert len(changes) == 1
        # Migration hint extracted from "use X instead"
        assert changes[0].migration_guide is not None


# =============================================================================
# T015: Test detect_update_available
# =============================================================================


class TestDetectUpdateAvailable:
    """Test detect_update_available function."""

    def test_update_available_newer_version(self):
        """Test detecting update when newer version exists."""
        result = detect_update_available(
            current_version="1.220.0",
            changelog_version="v1.221.0",
        )
        assert result["update_available"] is True
        assert result["latest_version"] == "1.221.0"

    def test_update_not_available_same_version(self):
        """Test no update when versions match."""
        result = detect_update_available(
            current_version="1.221.0",
            changelog_version="v1.221.0",
        )
        assert result["update_available"] is False

    def test_update_not_available_newer_current(self):
        """Test no update when current is newer."""
        result = detect_update_available(
            current_version="1.222.0",
            changelog_version="v1.221.0",
        )
        assert result["update_available"] is False

    def test_version_parsing_strips_prefix(self):
        """Test version parsing handles v prefix."""
        result = detect_update_available(
            current_version="v1.220.0",
            changelog_version="v1.221.0",
        )
        assert result["update_available"] is True

    def test_version_comparison_semver(self):
        """Test semver-like version comparison."""
        # Patch version bump
        assert detect_update_available("1.221.0", "v1.221.1")["update_available"] is True
        # Minor version bump
        assert detect_update_available("1.221.5", "v1.222.0")["update_available"] is True
        # Major version bump
        assert detect_update_available("1.999.999", "v2.0.0")["update_available"] is True


# =============================================================================
# Additional Tests: load_changelog_json
# =============================================================================


class TestLoadChangelogJson:
    """Test load_changelog_json function."""

    def test_load_valid_json(self, tmp_changelog_file: Path):
        """Test loading valid changelog JSON."""
        data = load_changelog_json(tmp_changelog_file)
        assert "stable_version" in data
        assert "timestamp" in data

    def test_load_missing_file_raises(self, tmp_path: Path):
        """Test loading missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_changelog_json(tmp_path / "not_exists.json")


# =============================================================================
# Additional Tests: get_current_version
# =============================================================================


class TestGetCurrentVersion:
    """Test get_current_version function."""

    def test_get_version_from_pyproject(self, tmp_pyproject_file: Path):
        """Test extracting nautilus_trader version from pyproject.toml."""
        version = get_current_version(tmp_pyproject_file)
        assert version == "1.221.0"

    def test_get_version_not_found(self, tmp_path: Path):
        """Test when nautilus_trader is not in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "test"
dependencies = ["requests"]
""")
        version = get_current_version(pyproject)
        assert version is None

    def test_get_version_with_extras(self, tmp_path: Path):
        """Test version extraction with extras."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
dependencies = ["nautilus_trader[all]>=1.222.0"]
""")
        version = get_current_version(pyproject)
        assert version == "1.222.0"
