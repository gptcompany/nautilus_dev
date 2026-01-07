# Unit tests for NautilusTrader Auto-Update Git Operations

"""Test git_ops module for auto_update."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.auto_update.git_ops import (
    create_pr,
    git_commit_changes,
    git_create_branch,
    git_push_branch,
)

# =============================================================================
# T033: Test git_create_branch
# =============================================================================


class TestGitCreateBranch:
    """Test git_create_branch function."""

    def test_create_branch_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't create branch."""
        result = git_create_branch(
            branch_name="update/v1.222.0",
            base_branch="master",
            working_dir=tmp_path,
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["branch_name"] == "update/v1.222.0"

    @patch("subprocess.run")
    def test_create_branch_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful branch creation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_create_branch(
            branch_name="update/v1.222.0",
            base_branch="master",
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is True
        assert mock_run.called


# =============================================================================
# T034: Test git_commit_changes
# =============================================================================


class TestGitCommitChanges:
    """Test git_commit_changes function."""

    def test_commit_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't commit."""
        result = git_commit_changes(
            message="Update nautilus_trader to v1.222.0",
            working_dir=tmp_path,
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True

    @patch("subprocess.run")
    def test_commit_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful commit."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_commit_changes(
            message="Update nautilus_trader to v1.222.0",
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is True


# =============================================================================
# T035: Test git_push_branch
# =============================================================================


class TestGitPushBranch:
    """Test git_push_branch function."""

    def test_push_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't push."""
        result = git_push_branch(
            branch_name="update/v1.222.0",
            remote="origin",
            working_dir=tmp_path,
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True

    @patch("subprocess.run")
    def test_push_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful push."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = git_push_branch(
            branch_name="update/v1.222.0",
            remote="origin",
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is True


# =============================================================================
# T036: Test create_pr
# =============================================================================


class TestCreatePr:
    """Test create_pr function."""

    def test_create_pr_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't create PR."""
        result = create_pr(
            title="Update nautilus_trader to v1.222.0",
            body="Auto-generated PR",
            base_branch="master",
            head_branch="update/v1.222.0",
            working_dir=tmp_path,
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["pr_url"] is None

    @patch("subprocess.run")
    def test_create_pr_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful PR creation."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/user/repo/pull/123",
            stderr="",
        )

        result = create_pr(
            title="Update nautilus_trader to v1.222.0",
            body="Auto-generated PR",
            base_branch="master",
            head_branch="update/v1.222.0",
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is True
        assert "github.com" in result["pr_url"]

    @patch("subprocess.run")
    def test_create_pr_failure(self, mock_run: MagicMock, tmp_path: Path):
        """Test PR creation failure."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="gh: not logged in",
        )

        result = create_pr(
            title="Update",
            body="Body",
            base_branch="master",
            head_branch="update/v1.222.0",
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is False
        assert "error" in result
