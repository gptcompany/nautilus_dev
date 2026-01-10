#!/usr/bin/env python3
"""
Comprehensive test suite for auto-alpha-debug.py hook.

Run with: pytest test_auto_alpha_debug.py -v
Or:       python test_auto_alpha_debug.py (standalone mode)

Tests cover:
- Dual-source detection (uncommitted + last commit fallback)
- Commit tracking (prevent re-triggering)
- File filtering (code vs config)
- Complexity-based round calculation
- Edge cases and error handling
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test (file has hyphen, use importlib)
import importlib.util

_module_path = Path(__file__).parent / "auto-alpha-debug.py"
_spec = importlib.util.spec_from_file_location("auto_alpha_debug", _module_path)
aad = importlib.util.module_from_spec(_spec)
sys.modules["auto_alpha_debug"] = aad
_spec.loader.exec_module(aad)


# =============================================================================
# UNIT TESTS: Helper Functions
# =============================================================================


class TestEmptyChanges:
    """Test _empty_changes() helper."""

    def test_returns_dict_with_all_keys(self):
        result = aad._empty_changes("test_source")
        assert "files_changed" in result
        assert "lines_added" in result
        assert "lines_deleted" in result
        assert "total_lines" in result
        assert "code_files" in result
        assert "source" in result

    def test_source_is_set_correctly(self):
        assert aad._empty_changes("uncommitted")["source"] == "uncommitted"
        assert aad._empty_changes("last_commit")["source"] == "last_commit"
        assert aad._empty_changes("custom")["source"] == "custom"

    def test_all_counts_are_zero(self):
        result = aad._empty_changes("test")
        assert result["files_changed"] == 0
        assert result["lines_added"] == 0
        assert result["lines_deleted"] == 0
        assert result["total_lines"] == 0
        assert result["code_files"] == []


class TestShouldExcludeFile:
    """Test should_exclude_file() filtering logic."""

    def test_excludes_claude_config(self):
        assert aad.should_exclude_file(".claude/settings.json")
        assert aad.should_exclude_file(".claude/agents/test.md")

    def test_excludes_git_internals(self):
        assert aad.should_exclude_file(".git/config")
        assert aad.should_exclude_file(".git/hooks/pre-commit")

    def test_excludes_markdown(self):
        assert aad.should_exclude_file("README.md")
        assert aad.should_exclude_file("CLAUDE.md")
        assert aad.should_exclude_file("docs/guide.md")

    def test_excludes_config_files(self):
        assert aad.should_exclude_file("config.json")
        assert aad.should_exclude_file("settings.yml")
        assert aad.should_exclude_file("pyproject.toml")

    def test_does_not_exclude_python_files(self):
        assert not aad.should_exclude_file("main.py")
        assert not aad.should_exclude_file("src/utils.py")

    def test_does_not_exclude_code_files(self):
        assert not aad.should_exclude_file("app.ts")
        assert not aad.should_exclude_file("lib.rs")
        assert not aad.should_exclude_file("main.go")


class TestIsCodeFile:
    """Test is_code_file() detection."""

    def test_python_files(self):
        assert aad.is_code_file("main.py")
        assert aad.is_code_file("test_module.py")
        assert aad.is_code_file("src/deep/module.py")

    def test_javascript_typescript(self):
        assert aad.is_code_file("app.js")
        assert aad.is_code_file("component.tsx")
        assert aad.is_code_file("utils.ts")
        assert aad.is_code_file("server.mjs")

    def test_rust_go_c(self):
        assert aad.is_code_file("main.rs")
        assert aad.is_code_file("server.go")
        assert aad.is_code_file("utils.c")
        assert aad.is_code_file("header.h")

    def test_code_directories(self):
        # Files in code directories should be detected even without extension
        assert aad.is_code_file("src/unknown")
        assert aad.is_code_file("tests/conftest")
        assert aad.is_code_file("api/routes")

    def test_non_code_files(self):
        assert not aad.is_code_file("README.md")
        assert not aad.is_code_file("config.json")
        assert not aad.is_code_file("data.csv")


class TestCalculateOptimalRounds:
    """Test calculate_optimal_rounds() complexity heuristics."""

    def test_minimal_changes(self):
        changes = {"total_lines": 20, "files_changed": 1}
        assert aad.calculate_optimal_rounds(changes) == 2

    def test_moderate_changes(self):
        changes = {"total_lines": 75, "files_changed": 2}
        assert aad.calculate_optimal_rounds(changes) == 3

    def test_significant_changes(self):
        changes = {"total_lines": 150, "files_changed": 3}
        assert aad.calculate_optimal_rounds(changes) == 4

    def test_major_changes(self):
        changes = {"total_lines": 350, "files_changed": 5}
        result = aad.calculate_optimal_rounds(changes)
        assert 5 <= result <= 7  # 5 base + 1 file factor

    def test_massive_changes(self):
        changes = {"total_lines": 800, "files_changed": 10}
        result = aad.calculate_optimal_rounds(changes)
        assert result == 10  # Capped at MAX_ROUNDS

    def test_many_files_increases_rounds(self):
        # Same lines but more files = more rounds
        few_files = {"total_lines": 100, "files_changed": 2}
        many_files = {"total_lines": 100, "files_changed": 10}
        assert aad.calculate_optimal_rounds(many_files) > aad.calculate_optimal_rounds(
            few_files
        )


class TestShouldTriggerAlphaDebug:
    """Test should_trigger_alpha_debug() decision logic."""

    def test_no_code_files_returns_false(self):
        changes = aad._empty_changes("test")
        result, reason = aad.should_trigger_alpha_debug("done", changes)
        assert result is False
        assert "No code files" in reason

    def test_insufficient_lines_returns_false(self):
        changes = {
            "total_lines": 10,  # Below MIN_LINES_CHANGED (20)
            "code_files": ["main.py"],
            "files_changed": 1,
        }
        result, reason = aad.should_trigger_alpha_debug("done", changes)
        assert result is False
        assert "10 lines" in reason

    def test_speckit_indicator_triggers(self):
        changes = {
            "total_lines": 50,
            "code_files": ["main.py"],
            "files_changed": 1,
        }
        result, reason = aad.should_trigger_alpha_debug("speckit complete", changes)
        assert result is True
        assert "SpecKit" in reason

    def test_implementation_keyword_triggers(self):
        changes = {
            "total_lines": 50,
            "code_files": ["main.py"],
            "files_changed": 1,
        }
        result, reason = aad.should_trigger_alpha_debug("feature implemented", changes)
        assert result is True

    def test_large_changes_trigger_regardless(self):
        changes = {
            "total_lines": 150,  # >= 100 triggers regardless
            "code_files": ["main.py", "utils.py"],
            "files_changed": 2,
            "lines_added": 100,
            "lines_deleted": 50,
        }
        result, reason = aad.should_trigger_alpha_debug("random text", changes)
        assert result is True
        assert "Significant" in reason


class TestShouldUseAlphaEvolve:
    """Test should_use_alpha_evolve() detection."""

    def test_explicit_marker_triggers(self):
        result, reason = aad.should_use_alpha_evolve("[E] implement new feature")
        assert result is True
        assert "[E]" in reason

    def test_evolve_keyword_triggers(self):
        result, reason = aad.should_use_alpha_evolve("use alpha-evolve for this")
        assert result is True

    def test_context_keyword_with_implement(self):
        result, reason = aad.should_use_alpha_evolve(
            "implement core algorithm from scratch"
        )
        assert result is True

    def test_context_keyword_alone_no_trigger(self):
        # Context keyword without implementation word should NOT trigger
        result, reason = aad.should_use_alpha_evolve("the algorithm is interesting")
        assert result is False

    def test_normal_implementation_no_evolve(self):
        result, reason = aad.should_use_alpha_evolve("fixed the bug")
        assert result is False


# =============================================================================
# UNIT TESTS: Commit Tracking
# =============================================================================


class TestCommitTracking:
    """Test commit tracking functions to prevent re-triggering."""

    def test_is_commit_already_analyzed_empty_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # No file exists yet
                assert aad.is_commit_already_analyzed("abc123") is False

    def test_mark_and_check_commit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # Mark a commit
                aad.mark_commit_analyzed("abc123")

                # Should now be found
                assert aad.is_commit_already_analyzed("abc123") is True
                assert aad.is_commit_already_analyzed("def456") is False

    def test_keeps_only_last_50_commits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # Add 60 commits
                for i in range(60):
                    aad.mark_commit_analyzed(f"commit_{i:03d}")

                # First 10 should be evicted
                assert aad.is_commit_already_analyzed("commit_000") is False
                assert aad.is_commit_already_analyzed("commit_009") is False

                # Last 50 should remain
                assert aad.is_commit_already_analyzed("commit_010") is True
                assert aad.is_commit_already_analyzed("commit_059") is True

    def test_handles_corrupted_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # Create corrupted file
                tracking_file = (
                    Path(tmpdir) / ".claude" / "stats" / aad.ANALYZED_COMMITS_FILE
                )
                tracking_file.parent.mkdir(parents=True, exist_ok=True)
                tracking_file.write_text("not valid json {{{")

                # Should handle gracefully
                assert aad.is_commit_already_analyzed("abc123") is False

                # Should be able to write new data
                aad.mark_commit_analyzed("abc123")


# =============================================================================
# UNIT TESTS: State File Creation
# =============================================================================


class TestCreateStateFile:
    """Test create_state_file() for enabling dispatcher detection."""

    def test_creates_alpha_debug_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                result = aad.create_state_file("alpha-debug", 5)
                assert result is True

                state_file = (
                    Path(tmpdir) / ".claude" / "stats" / "alpha_debug_state.json"
                )
                assert state_file.exists()

                data = json.loads(state_file.read_text())
                assert data["active"] is True
                assert data["max_rounds"] == 5
                assert data["current_round"] == 0

    def test_creates_alpha_evolve_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                result = aad.create_state_file("alpha-evolve", 3)
                assert result is True

                state_file = (
                    Path(tmpdir) / ".claude" / "stats" / "alpha_evolve_state.json"
                )
                assert state_file.exists()

                data = json.loads(state_file.read_text())
                assert data["active"] is True
                assert data["debug_rounds_after"] == 3

    def test_returns_false_for_unknown_type(self):
        result = aad.create_state_file("unknown-type", 5)
        assert result is False


# =============================================================================
# INTEGRATION TESTS: Git Operations (Mocked)
# =============================================================================


class TestGetGitChanges:
    """Test get_git_changes() with mocked subprocess."""

    def test_returns_empty_on_subprocess_error(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("git not found")
            result = aad.get_git_changes()
            assert result["files_changed"] == 0
            assert result["source"] == "uncommitted"

    def test_returns_empty_on_timeout(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 5)
            result = aad.get_git_changes()
            assert result["files_changed"] == 0
            assert result["source"] == "uncommitted"

    def test_filters_out_non_code_files(self):
        with patch("subprocess.run") as mock_run:
            # Mock git diff --name-only responses
            mock_run.side_effect = [
                MagicMock(
                    returncode=0,
                    stdout="main.py\nREADME.md\nconfig.json\n",
                ),
                MagicMock(returncode=0, stdout=""),  # staged
                MagicMock(
                    returncode=0, stdout="10\t5\tmain.py\n3\t2\tREADME.md\n"
                ),  # numstat cached
                MagicMock(returncode=0, stdout=""),  # numstat unstaged
            ]

            result = aad.get_git_changes()
            assert result["code_files"] == ["main.py"]
            assert "README.md" not in result["code_files"]


class TestGetLastCommitChanges:
    """Test get_last_commit_changes() fallback logic."""

    def test_returns_empty_if_commit_too_old(self):
        old_timestamp = int(time.time()) - (10 * 60)  # 10 minutes ago

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=f"{old_timestamp} abc123def456",
            )

            result = aad.get_last_commit_changes()
            assert result["files_changed"] == 0
            assert result["source"] == "last_commit"

    def test_returns_changes_if_commit_recent(self):
        recent_timestamp = int(time.time()) - 60  # 1 minute ago

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(
                    returncode=0, stdout=f"{recent_timestamp} abc123def456"
                ),  # log
                MagicMock(returncode=0, stdout="main.py\nutils.py\n"),  # files
                MagicMock(
                    returncode=0, stdout="20\t5\tmain.py\n10\t3\tutils.py\n"
                ),  # numstat
            ]

            with patch.object(aad, "is_commit_already_analyzed", return_value=False):
                result = aad.get_last_commit_changes()
                assert result["files_changed"] == 2
                assert result["source"] == "last_commit"
                assert result["commit_hash"] == "abc123def456"

    def test_returns_empty_if_already_analyzed(self):
        recent_timestamp = int(time.time()) - 60

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=f"{recent_timestamp} abc123",
            )

            with patch.object(aad, "is_commit_already_analyzed", return_value=True):
                result = aad.get_last_commit_changes()
                assert result["files_changed"] == 0


# =============================================================================
# INTEGRATION TESTS: Main Function
# =============================================================================


class TestMainFunction:
    """Test main() dual-source detection flow."""

    def test_exits_with_continue_false_when_no_changes(self):
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = json.dumps({"stop_reason": "done"})
            mock_stdin.__iter__ = lambda self: iter(
                [json.dumps({"stop_reason": "done"})]
            )

            with patch.object(
                aad, "get_git_changes", return_value=aad._empty_changes("uncommitted")
            ):
                with patch.object(
                    aad,
                    "get_last_commit_changes",
                    return_value=aad._empty_changes("last_commit"),
                ):
                    with patch("json.load", return_value={"stop_reason": "done"}):
                        with patch("builtins.print") as mock_print:
                            with pytest.raises(SystemExit) as exc_info:
                                aad.main()

                            assert exc_info.value.code == 0
                            # Should have printed {"continue": false}
                            output_call = mock_print.call_args_list[-1]
                            output = json.loads(output_call[0][0])
                            assert output["continue"] is False

    def test_triggers_alpha_debug_on_uncommitted_changes(self):
        changes = {
            "files_changed": 3,
            "lines_added": 50,
            "lines_deleted": 20,
            "total_lines": 70,
            "code_files": ["main.py", "utils.py", "api.py"],
            "source": "uncommitted",
        }

        with patch("json.load", return_value={"stop_reason": "feature implemented"}):
            with patch.object(aad, "get_git_changes", return_value=changes):
                with patch.object(aad, "create_state_file", return_value=True):
                    with patch("builtins.print") as mock_print:
                        with pytest.raises(SystemExit) as exc_info:
                            aad.main()

                        assert exc_info.value.code == 0
                        output = json.loads(mock_print.call_args_list[-1][0][0])
                        assert output["continue"] is True
                        assert "AUTO ALPHA-DEBUG" in output["systemMessage"]

    def test_falls_back_to_last_commit(self):
        last_commit_changes = {
            "files_changed": 2,
            "lines_added": 30,
            "lines_deleted": 10,
            "total_lines": 40,
            "code_files": ["main.py", "lib.py"],
            "source": "last_commit",
            "commit_hash": "abc123",
            "commit_age_minutes": 2.5,
        }

        with patch("json.load", return_value={"stop_reason": "done"}):
            with patch.object(
                aad, "get_git_changes", return_value=aad._empty_changes("uncommitted")
            ):
                with patch.object(
                    aad, "get_last_commit_changes", return_value=last_commit_changes
                ):
                    with patch.object(aad, "create_state_file", return_value=True):
                        with patch.object(aad, "mark_commit_analyzed") as mock_mark:
                            with patch("builtins.print") as mock_print:
                                with pytest.raises(SystemExit):
                                    aad.main()

                                # Should have marked commit as analyzed
                                mock_mark.assert_called_once_with("abc123")

                                output = json.loads(mock_print.call_args_list[-1][0][0])
                                assert output["continue"] is True
                                assert "[LAST COMMIT]" in output["systemMessage"]

    def test_uses_alpha_evolve_when_indicated(self):
        changes = {
            "files_changed": 2,
            "lines_added": 100,
            "lines_deleted": 20,
            "total_lines": 120,
            "code_files": ["algorithm.py", "core.py"],
            "source": "uncommitted",
        }

        with patch(
            "json.load", return_value={"stop_reason": "[E] implement new algorithm"}
        ):
            with patch.object(aad, "get_git_changes", return_value=changes):
                with patch.object(aad, "create_state_file", return_value=True):
                    with patch("builtins.print") as mock_print:
                        with pytest.raises(SystemExit):
                            aad.main()

                        output = json.loads(mock_print.call_args_list[-1][0][0])
                        assert output["continue"] is True
                        assert "AUTO ALPHA-EVOLVE" in output["systemMessage"]


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Test robustness against various error conditions."""

    def test_handles_invalid_json_input(self):
        with patch("json.load", side_effect=json.JSONDecodeError("error", "doc", 0)):
            with pytest.raises(SystemExit) as exc_info:
                aad.main()
            assert exc_info.value.code == 0

    def test_handles_non_string_stop_reason(self):
        with patch("json.load", return_value={"stop_reason": 12345}):
            with patch.object(
                aad, "get_git_changes", return_value=aad._empty_changes("uncommitted")
            ):
                with patch.object(
                    aad,
                    "get_last_commit_changes",
                    return_value=aad._empty_changes("last_commit"),
                ):
                    with patch("builtins.print"):
                        with pytest.raises(SystemExit) as exc_info:
                            aad.main()
                        assert exc_info.value.code == 0

    def test_truncates_long_stop_reason(self):
        # Very long stop reason should be truncated
        long_reason = "x" * 20000

        with patch("json.load", return_value={"stop_reason": long_reason}):
            with patch.object(
                aad, "get_git_changes", return_value=aad._empty_changes("uncommitted")
            ):
                with patch.object(
                    aad,
                    "get_last_commit_changes",
                    return_value=aad._empty_changes("last_commit"),
                ):
                    with patch("builtins.print"):
                        # Should not crash
                        with pytest.raises(SystemExit) as exc_info:
                            aad.main()
                        assert exc_info.value.code == 0


# =============================================================================
# SUBPROCESS TIMEOUT TESTS
# =============================================================================


class TestSubprocessTimeouts:
    """Verify all subprocess calls have appropriate timeouts."""

    def test_all_subprocess_calls_have_timeout(self):
        """Parse source and verify every subprocess.run has timeout=5."""
        source_file = Path(__file__).parent / "auto-alpha-debug.py"
        source = source_file.read_text()

        # Count subprocess.run calls
        import re

        run_calls = re.findall(r"subprocess\.run\(", source)
        timeout_calls = re.findall(r"subprocess\.run\([^)]*timeout=5", source)

        # All subprocess.run calls should have timeout=5
        assert len(run_calls) == len(timeout_calls), (
            f"Found {len(run_calls)} subprocess.run calls but only {len(timeout_calls)} have timeout=5"
        )


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================


def run_standalone_tests():
    """Run tests in standalone mode (without pytest)."""
    import traceback

    test_classes = [
        TestEmptyChanges,
        TestShouldExcludeFile,
        TestIsCodeFile,
        TestCalculateOptimalRounds,
        TestShouldTriggerAlphaDebug,
        TestShouldUseAlphaEvolve,
        TestCommitTracking,
        TestCreateStateFile,
        TestGetGitChanges,
        TestGetLastCommitChanges,
        TestMainFunction,
        TestErrorHandling,
        TestSubprocessTimeouts,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        instance = test_class()
        methods = [m for m in dir(instance) if m.startswith("test_")]

        for method_name in methods:
            total_tests += 1
            method = getattr(instance, method_name)

            try:
                method()
                passed_tests += 1
                print(f"  ✓ {test_class.__name__}.{method_name}")
            except Exception as e:
                failed_tests.append((test_class.__name__, method_name, e))
                print(f"  ✗ {test_class.__name__}.{method_name}")
                traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"Results: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print(f"\nFailed tests ({len(failed_tests)}):")
        for cls_name, method, error in failed_tests:
            print(f"  - {cls_name}.{method}: {error}")
        return 1

    print("\n✅ All tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(run_standalone_tests())
