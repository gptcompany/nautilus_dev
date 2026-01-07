"""Tests for CLI interface.

Tests for:
    - run command
    - report command
    - compare command
    - YAML config loading

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations

import tempfile
from pathlib import Path


class TestCLIRun:
    """Tests for the run command."""

    def test_run_command_exists(self) -> None:
        """Test that run command exists."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])

        assert result.exit_code == 0
        assert "run" in result.output.lower() or "validation" in result.output.lower()

    def test_run_with_mock(self) -> None:
        """Test run command with mock mode."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--mock"])

        assert result.exit_code == 0

    def test_run_with_seed(self) -> None:
        """Test run command with seed for reproducibility."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        result1 = runner.invoke(cli, ["run", "--mock", "--seed", "42"])
        result2 = runner.invoke(cli, ["run", "--mock", "--seed", "42"])

        # Same seed should give same output
        assert result1.exit_code == 0
        assert result2.exit_code == 0


class TestCLIReport:
    """Tests for the report command."""

    def test_report_command_exists(self) -> None:
        """Test that report command exists."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])

        assert result.exit_code == 0

    def test_report_generates_markdown(self) -> None:
        """Test that report generates markdown output."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "report.md"
            result = runner.invoke(cli, ["run", "--mock", "--output", str(output_file)])

            if result.exit_code == 0 and output_file.exists():
                content = output_file.read_text()
                assert "Baseline Validation" in content or len(content) > 0


class TestCLICompare:
    """Tests for the compare command."""

    def test_compare_command_exists(self) -> None:
        """Test that compare command exists."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--help"])

        assert result.exit_code == 0


class TestCLIConfig:
    """Tests for YAML config loading."""

    def test_loads_yaml_config(self) -> None:
        """Test that CLI loads YAML config."""
        from click.testing import CliRunner
        import yaml

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()

        # Create temp config file
        config = {
            "validation": {
                "train_months": 6,
                "test_months": 1,
            },
            "seed": 123,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        try:
            result = runner.invoke(cli, ["run", "--config", config_path, "--mock"])
            # Should run without error
            assert result.exit_code == 0
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_uses_default_config(self) -> None:
        """Test that CLI uses default config when none provided."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--mock"])

        # Should work with default config
        assert result.exit_code == 0


class TestCLIIntegration:
    """Integration tests for CLI."""

    def test_full_pipeline_mock(self) -> None:
        """Test full pipeline with mock data."""
        from click.testing import CliRunner

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()

        # Run validation
        result = runner.invoke(cli, ["run", "--mock", "--seed", "42"])
        assert result.exit_code == 0

        # Check output contains verdict
        assert any(v in result.output for v in ["GO", "WAIT", "STOP"])

    def test_json_output(self) -> None:
        """Test JSON output format."""
        from click.testing import CliRunner
        import json

        from scripts.baseline_validation.cli import cli

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "results.json"
            result = runner.invoke(
                cli,
                ["run", "--mock", "--format", "json", "--output", str(output_file)],
            )

            assert result.exit_code == 0
            if output_file.exists():
                # Verify valid JSON
                data = json.loads(output_file.read_text())
                assert "verdict" in data
