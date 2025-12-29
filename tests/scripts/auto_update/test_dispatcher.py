# Unit tests for NautilusTrader Auto-Update Dispatcher

"""Test dispatcher module for auto_update."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.auto_update.dispatcher import (
    build_task_prompt,
    dispatch_claude_code,
    monitor_agent_completion,
)
from scripts.auto_update.models import (
    AffectedFile,
    BreakingChange,
    ConfidenceLevel,
    ImpactReport,
    Recommendation,
    Severity,
)


def make_impact_report() -> ImpactReport:
    """Create test ImpactReport."""
    bc = BreakingChange(
        description="OldClass renamed to NewClass",
        severity=Severity.MEDIUM,
        affected_pattern="OldClass",
    )
    af = AffectedFile(
        path=Path("strategies/my_strategy.py"),
        line_numbers=[10, 25, 40],
        breaking_change=bc,
        can_auto_fix=False,
    )
    return ImpactReport(
        version="1.222.0",
        previous_version="1.221.0",
        breaking_changes=[bc],
        affected_files=[af],
        total_affected_lines=3,
        confidence_score=75.0,
        confidence_level=ConfidenceLevel.HIGH,
        can_auto_update=True,
        recommendation=Recommendation.DELAYED,
    )


# =============================================================================
# T060: Test build_task_prompt
# =============================================================================


class TestBuildTaskPrompt:
    """Test build_task_prompt function."""

    def test_build_prompt_basic(self):
        """Test building basic task prompt."""
        impact_report = make_impact_report()

        prompt = build_task_prompt(impact_report)

        assert "1.222.0" in prompt
        assert "OldClass" in prompt
        assert "NewClass" in prompt
        assert "strategies/my_strategy.py" in prompt

    def test_build_prompt_includes_breaking_changes(self):
        """Test prompt includes all breaking changes."""
        impact_report = make_impact_report()

        prompt = build_task_prompt(impact_report)

        assert "Breaking Changes" in prompt or "breaking" in prompt.lower()
        assert "OldClass renamed to NewClass" in prompt

    def test_build_prompt_includes_affected_files(self):
        """Test prompt includes affected files."""
        impact_report = make_impact_report()

        prompt = build_task_prompt(impact_report)

        assert "strategies/my_strategy.py" in prompt
        assert "10" in prompt or "line" in prompt.lower()

    def test_build_prompt_with_custom_instructions(self):
        """Test prompt with custom instructions."""
        impact_report = make_impact_report()

        prompt = build_task_prompt(
            impact_report,
            custom_instructions="Focus on backward compatibility",
        )

        assert "backward compatibility" in prompt.lower()

    def test_build_prompt_minimal(self):
        """Test prompt with minimal impact report."""
        bc = BreakingChange(
            description="Minor API change",
            severity=Severity.LOW,
            affected_pattern="old_method",
        )
        report = ImpactReport(
            version="1.222.0",
            previous_version="1.221.0",
            breaking_changes=[bc],
            affected_files=[],
            total_affected_lines=0,
            confidence_score=95.0,
            confidence_level=ConfidenceLevel.HIGH,
            can_auto_update=True,
            recommendation=Recommendation.AUTO,
        )

        prompt = build_task_prompt(report)

        assert "1.222.0" in prompt
        assert len(prompt) > 50  # Should have meaningful content


# =============================================================================
# T061: Test dispatch_claude_code
# =============================================================================


class TestDispatchClaudeCode:
    """Test dispatch_claude_code function."""

    def test_dispatch_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't spawn agent."""
        impact_report = make_impact_report()

        result = dispatch_claude_code(
            impact_report=impact_report,
            working_dir=tmp_path,
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["agent_id"] is None

    @patch("subprocess.Popen")
    def test_dispatch_spawns_agent(self, mock_popen: MagicMock, tmp_path: Path):
        """Test dispatching spawns Claude Code agent."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        impact_report = make_impact_report()

        result = dispatch_claude_code(
            impact_report=impact_report,
            working_dir=tmp_path,
            dry_run=False,
        )

        assert result["success"] is True
        assert mock_popen.called

    @patch("subprocess.Popen")
    def test_dispatch_with_timeout(self, mock_popen: MagicMock, tmp_path: Path):
        """Test dispatch with custom timeout."""
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        impact_report = make_impact_report()

        dispatch_claude_code(
            impact_report=impact_report,
            working_dir=tmp_path,
            timeout=3600,
            dry_run=False,
        )

        # Verify command was called
        assert mock_popen.called

    @patch("subprocess.Popen")
    def test_dispatch_error_handling(self, mock_popen: MagicMock, tmp_path: Path):
        """Test dispatch handles errors gracefully."""
        mock_popen.side_effect = FileNotFoundError("claude not found")

        impact_report = make_impact_report()

        result = dispatch_claude_code(
            impact_report=impact_report,
            working_dir=tmp_path,
            dry_run=False,
        )

        assert result["success"] is False
        assert "error" in result


# =============================================================================
# T066: Test monitor_agent_completion
# =============================================================================


class TestMonitorAgentCompletion:
    """Test monitor_agent_completion function."""

    def test_monitor_dry_run(self):
        """Test monitoring in dry-run mode."""
        result = monitor_agent_completion(
            agent_id="test-agent-123",
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True
        assert result["status"] == "dry_run"

    @patch("subprocess.run")
    def test_monitor_completed(self, mock_run: MagicMock):
        """Test monitoring completed agent."""
        # returncode=1 means process not found (completed)
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="",
        )

        result = monitor_agent_completion(
            agent_id="test-agent-123",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["status"] == "completed"

    @patch("scripts.auto_update.dispatcher.subprocess.run")
    def test_monitor_timeout(self, mock_run: MagicMock):
        """Test monitoring with timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)

        result = monitor_agent_completion(
            agent_id="test-agent-123",
            timeout=60,
            dry_run=False,
        )

        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower()
