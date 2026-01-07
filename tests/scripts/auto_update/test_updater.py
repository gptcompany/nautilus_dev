# Unit tests for NautilusTrader Auto-Update Updater

"""Test updater module for auto_update."""

from pathlib import Path

import pytest

from scripts.auto_update.updater import (
    run_uv_sync,
    update_pyproject_version,
)

# =============================================================================
# T031: Test update_pyproject_version
# =============================================================================


class TestUpdatePyprojectVersion:
    """Test update_pyproject_version function."""

    def test_update_version_basic(self, tmp_pyproject_file: Path):
        """Test updating nautilus_trader version in pyproject.toml."""
        result = update_pyproject_version(
            pyproject_path=tmp_pyproject_file,
            new_version="1.222.0",
            dry_run=False,
        )
        assert result["success"] is True
        assert result["old_version"] == "1.221.0"
        assert result["new_version"] == "1.222.0"

        # Verify file was updated
        content = tmp_pyproject_file.read_text()
        assert "1.222.0" in content
        assert "1.221.0" not in content

    def test_update_version_dry_run(self, tmp_pyproject_file: Path):
        """Test dry-run doesn't modify file."""
        result = update_pyproject_version(
            pyproject_path=tmp_pyproject_file,
            new_version="1.222.0",
            dry_run=True,
        )
        assert result["success"] is True
        assert result["old_version"] == "1.221.0"
        assert result["dry_run"] is True

        # Verify file was NOT updated
        content = tmp_pyproject_file.read_text()
        assert "1.221.0" in content
        assert "1.222.0" not in content

    def test_update_version_with_extras(self, tmp_path: Path):
        """Test updating version with extras like [all]."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
dependencies = ["nautilus_trader[all]>=1.221.0"]
""")
        result = update_pyproject_version(
            pyproject_path=pyproject,
            new_version="1.222.0",
            dry_run=False,
        )
        assert result["success"] is True
        content = pyproject.read_text()
        assert "nautilus_trader[all]>=1.222.0" in content

    def test_update_version_not_found(self, tmp_path: Path):
        """Test when nautilus_trader is not in dependencies."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
dependencies = ["requests>=2.0"]
""")
        result = update_pyproject_version(
            pyproject_path=pyproject,
            new_version="1.222.0",
            dry_run=False,
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_update_version_missing_file(self, tmp_path: Path):
        """Test updating non-existent file."""
        with pytest.raises(FileNotFoundError):
            update_pyproject_version(
                pyproject_path=tmp_path / "missing.toml",
                new_version="1.222.0",
                dry_run=False,
            )


# =============================================================================
# T032: Test run_uv_sync
# =============================================================================


class TestRunUvSync:
    """Test run_uv_sync function."""

    def test_uv_sync_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't run uv sync."""
        result = run_uv_sync(working_dir=tmp_path, dry_run=True)
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["command"] is None

    def test_uv_sync_missing_pyproject(self, tmp_path: Path):
        """Test uv sync fails without pyproject.toml."""
        result = run_uv_sync(working_dir=tmp_path, dry_run=False)
        # Should still attempt but fail gracefully
        assert result["success"] is False or result.get("dry_run")
