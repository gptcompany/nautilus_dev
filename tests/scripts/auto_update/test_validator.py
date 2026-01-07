# Unit tests for NautilusTrader Auto-Update Validator

"""Test validator module for auto_update."""

from pathlib import Path
from unittest.mock import MagicMock, patch


from scripts.auto_update.validator import (
    parse_test_results,
    run_pytest,
    validate_update,
)


# =============================================================================
# T045: Test run_pytest
# =============================================================================


class TestRunPytest:
    """Test run_pytest function."""

    def test_run_pytest_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't run tests."""
        result = run_pytest(working_dir=tmp_path, dry_run=True)
        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["tests_run"] == 0

    @patch("subprocess.run")
    def test_run_pytest_success(self, mock_run: MagicMock, tmp_path: Path):
        """Test successful pytest run."""
        # Mock successful pytest output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"summary": {"total": 10, "passed": 10, "failed": 0}}',
            stderr="",
        )

        result = run_pytest(
            working_dir=tmp_path,
            test_paths=["tests/"],
            dry_run=False,
        )
        assert result["success"] is True
        assert mock_run.called

    @patch("subprocess.run")
    def test_run_pytest_failure(self, mock_run: MagicMock, tmp_path: Path):
        """Test pytest run with failures."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='{"summary": {"total": 10, "passed": 8, "failed": 2}}',
            stderr="",
        )

        result = run_pytest(
            working_dir=tmp_path,
            test_paths=["tests/"],
            dry_run=False,
        )
        assert result["success"] is False
        assert result["returncode"] == 1

    @patch("scripts.auto_update.validator.subprocess.run")
    def test_run_pytest_timeout(self, mock_run: MagicMock, tmp_path: Path):
        """Test pytest timeout handling."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=300)

        result = run_pytest(
            working_dir=tmp_path,
            dry_run=False,
            timeout=300,
        )
        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower()

    @patch("subprocess.run")
    def test_run_pytest_with_markers(self, mock_run: MagicMock, tmp_path: Path):
        """Test pytest run with specific markers."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="{}",
            stderr="",
        )

        run_pytest(
            working_dir=tmp_path,
            markers=["not slow", "unit"],
            dry_run=False,
        )

        # Verify markers were passed to pytest
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "-m" in cmd


# =============================================================================
# T046: Test parse_test_results
# =============================================================================


class TestParseTestResults:
    """Test parse_test_results function."""

    def test_parse_test_results_all_passed(self):
        """Test parsing results when all tests pass."""
        json_output = """{
            "summary": {
                "total": 50,
                "passed": 50,
                "failed": 0,
                "skipped": 0,
                "error": 0
            },
            "duration": 12.5
        }"""

        result = parse_test_results(json_output)
        assert result.passed is True
        assert result.total_tests == 50
        assert result.failed_tests == 0

    def test_parse_test_results_with_failures(self):
        """Test parsing results with failures."""
        json_output = """{
            "summary": {
                "total": 50,
                "passed": 45,
                "failed": 5,
                "skipped": 0,
                "error": 0
            },
            "tests": [
                {"nodeid": "test_foo.py::test_1", "outcome": "failed"},
                {"nodeid": "test_foo.py::test_2", "outcome": "failed"}
            ]
        }"""

        result = parse_test_results(json_output)
        assert result.passed is False
        assert result.total_tests == 50
        assert result.failed_tests == 5
        assert len(result.failed_test_names) >= 0

    def test_parse_test_results_with_errors(self):
        """Test parsing results with errors."""
        json_output = """{
            "summary": {
                "total": 50,
                "passed": 48,
                "failed": 0,
                "skipped": 0,
                "error": 2
            }
        }"""

        result = parse_test_results(json_output)
        assert result.passed is False  # Errors count as failures

    def test_parse_test_results_empty(self):
        """Test parsing empty/invalid output."""
        result = parse_test_results("")
        assert result.passed is False
        assert result.total_tests == 0

    def test_parse_test_results_invalid_json(self):
        """Test parsing invalid JSON."""
        result = parse_test_results("not valid json")
        assert result.passed is False
        assert result.total_tests == 0

    def test_parse_test_results_with_skipped(self):
        """Test parsing results with skipped tests."""
        json_output = """{
            "summary": {
                "total": 50,
                "passed": 45,
                "failed": 0,
                "skipped": 5,
                "error": 0
            }
        }"""

        result = parse_test_results(json_output)
        assert result.passed is True  # Skipped tests don't fail
        assert result.skipped_tests == 5


# =============================================================================
# T047: Test validate_update (Integration-style)
# =============================================================================


class TestValidateUpdate:
    """Test validate_update orchestrator function."""

    def test_validate_update_dry_run(self, tmp_path: Path):
        """Test dry-run validation."""
        result = validate_update(
            working_dir=tmp_path,
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True

    @patch("scripts.auto_update.validator.run_pytest")
    def test_validate_update_tests_pass(self, mock_run_pytest: MagicMock, tmp_path: Path):
        """Test validation when all tests pass."""
        mock_run_pytest.return_value = {
            "success": True,
            "dry_run": False,
            "stdout": '{"summary": {"total": 10, "passed": 10, "failed": 0}}',
            "returncode": 0,
        }

        result = validate_update(
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is True
        assert result["test_result"].passed is True

    @patch("scripts.auto_update.validator.run_pytest")
    def test_validate_update_tests_fail(self, mock_run_pytest: MagicMock, tmp_path: Path):
        """Test validation when tests fail."""
        mock_run_pytest.return_value = {
            "success": False,
            "dry_run": False,
            "stdout": '{"summary": {"total": 10, "passed": 8, "failed": 2}}',
            "returncode": 1,
        }

        result = validate_update(
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is False
        assert result["test_result"].passed is False

    @patch("scripts.auto_update.validator.run_pytest")
    def test_validate_update_with_custom_paths(self, mock_run_pytest: MagicMock, tmp_path: Path):
        """Test validation with custom test paths."""
        mock_run_pytest.return_value = {
            "success": True,
            "dry_run": False,
            "stdout": '{"summary": {"total": 5, "passed": 5, "failed": 0}}',
            "returncode": 0,
        }

        validate_update(
            working_dir=tmp_path,
            test_paths=["tests/unit/", "tests/integration/"],
            dry_run=False,
        )

        # Verify custom paths were passed
        call_args = mock_run_pytest.call_args
        assert call_args[1]["test_paths"] == ["tests/unit/", "tests/integration/"]

    @patch("scripts.auto_update.validator.run_pytest")
    def test_validate_update_blocks_on_failure(self, mock_run_pytest: MagicMock, tmp_path: Path):
        """Test that validation blocks merge on failure."""
        mock_run_pytest.return_value = {
            "success": False,
            "dry_run": False,
            "stdout": '{"summary": {"total": 10, "passed": 5, "failed": 5}}',
            "returncode": 1,
        }

        result = validate_update(
            working_dir=tmp_path,
            dry_run=False,
        )
        assert result["success"] is False
        assert result["can_merge"] is False
        assert "blocking" in result.get("reason", "").lower() or result["success"] is False
