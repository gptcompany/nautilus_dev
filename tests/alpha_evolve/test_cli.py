"""Tests for Alpha-Evolve CLI."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scripts.alpha_evolve.cli import evolve
from scripts.alpha_evolve.store import FitnessMetrics, ProgramStore


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_db(temp_db_path: Path) -> ProgramStore:
    """Temporary database with sample data."""
    store = ProgramStore(temp_db_path)

    # Add sample strategies
    for i in range(5):
        store.insert(
            code=f"# Strategy {i}",
            metrics=FitnessMetrics(
                sharpe_ratio=float(i),
                calmar_ratio=float(i) + 0.5,
                max_drawdown=0.10,
                cagr=0.15,
                total_return=0.20,
                trade_count=50,
                win_rate=0.50,
            ),
            experiment="test_exp",
        )

    return store


# === PHASE 6: USER STORY 4 - CLI TESTS (T044-T048) ===


class TestCLIStartBasic:
    """T044: Test CLI start command."""

    def test_cli_start_help(self, cli_runner: CliRunner):
        """Start command shows help."""
        result = cli_runner.invoke(evolve, ["start", "--help"])
        assert result.exit_code == 0
        assert "--seed" in result.output
        assert "--iterations" in result.output
        assert "--experiment" in result.output

    def test_cli_start_requires_seed(self, cli_runner: CliRunner):
        """Start command requires --seed."""
        result = cli_runner.invoke(evolve, ["start"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


class TestCLIStatusJSON:
    """T045: Test CLI status command JSON output."""

    def test_cli_status_json_output(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """Status command outputs valid JSON."""
        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "status", "test_exp", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "experiment" in data
        assert data["experiment"] == "test_exp"
        assert "status" in data
        assert "population_size" in data

    def test_cli_status_not_found(self, cli_runner: CliRunner, temp_db_path: Path):
        """Status command handles missing experiment."""
        # Create empty store
        ProgramStore(temp_db_path)

        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "status", "nonexistent"]
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestCLIBestTopK:
    """T046: Test CLI best command with top-k."""

    def test_cli_best_default(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """Best command shows top strategies."""
        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "best", "test_exp"]
        )

        assert result.exit_code == 0
        assert "Top" in result.output
        assert "Calmar" in result.output

    def test_cli_best_top_k(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """Best command respects --top-k option."""
        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "best", "test_exp", "-k", "3"]
        )

        assert result.exit_code == 0
        # Should show only 3 strategies
        assert "Top 3" in result.output

    def test_cli_best_json(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """Best command outputs valid JSON."""
        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "best", "test_exp", "--json", "-k", "2"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        assert "calmar" in data[0]


class TestCLIExportStrategy:
    """T047: Test CLI export command."""

    def test_cli_export_strategy(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """Export command creates file."""
        # Get a strategy ID
        top = temp_db.top_k(k=1, experiment="test_exp")
        strategy_id = top[0].id

        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                evolve,
                ["--db", str(temp_db_path), "export", strategy_id, "-o", "output.py"],
            )

            assert result.exit_code == 0
            assert "Exported" in result.output
            assert Path("output.py").exists()

            # Check content
            content = Path("output.py").read_text()
            assert "Evolved Strategy" in content
            assert strategy_id in content

    def test_cli_export_not_found(self, cli_runner: CliRunner, temp_db_path: Path):
        """Export command handles missing strategy."""
        ProgramStore(temp_db_path)

        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "export", "nonexistent"]
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestCLIListExperiments:
    """T048: Test CLI list command."""

    def test_cli_list_experiments(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """List command shows experiments."""
        result = cli_runner.invoke(evolve, ["--db", str(temp_db_path), "list"])

        assert result.exit_code == 0
        assert "Experiments" in result.output
        assert "test_exp" in result.output

    def test_cli_list_json(
        self, cli_runner: CliRunner, temp_db: ProgramStore, temp_db_path: Path
    ):
        """List command outputs valid JSON."""
        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "list", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "test_exp"

    def test_cli_list_empty(self, cli_runner: CliRunner, temp_db_path: Path):
        """List command handles empty database."""
        ProgramStore(temp_db_path)

        result = cli_runner.invoke(evolve, ["--db", str(temp_db_path), "list"])

        assert result.exit_code == 0
        assert "No experiments" in result.output


# === PHASE 7: USER STORY 5 - EXPERIMENT MANAGEMENT TESTS ===


class TestCLIResumeCommand:
    """T060: Test CLI resume command."""

    def test_cli_resume_help(self, cli_runner: CliRunner):
        """Resume command shows help."""
        result = cli_runner.invoke(evolve, ["resume", "--help"])
        assert result.exit_code == 0
        assert "EXPERIMENT" in result.output
        assert "--iterations" in result.output

    def test_cli_resume_not_found(self, cli_runner: CliRunner, temp_db_path: Path):
        """Resume command handles missing experiment."""
        ProgramStore(temp_db_path)

        result = cli_runner.invoke(
            evolve, ["--db", str(temp_db_path), "resume", "nonexistent"]
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower()


# === ADDITIONAL CLI TESTS ===


class TestCLIGlobalOptions:
    """Test global CLI options."""

    def test_cli_help(self, cli_runner: CliRunner):
        """Main CLI shows help."""
        result = cli_runner.invoke(evolve, ["--help"])
        assert result.exit_code == 0
        assert "Alpha-Evolve" in result.output
        assert "--config" in result.output
        assert "--db" in result.output

    def test_cli_db_option(self, cli_runner: CliRunner, temp_db_path: Path):
        """--db option works."""
        ProgramStore(temp_db_path)

        result = cli_runner.invoke(evolve, ["--db", str(temp_db_path), "list"])
        assert result.exit_code == 0


class TestCLIStopCommand:
    """Test stop command."""

    def test_cli_stop_help(self, cli_runner: CliRunner):
        """Stop command shows help."""
        result = cli_runner.invoke(evolve, ["stop", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output


class TestCLIExportWithLineage:
    """Test export with lineage."""

    def test_cli_export_with_lineage(self, cli_runner: CliRunner, temp_db_path: Path):
        """Export with lineage includes parent chain."""
        store = ProgramStore(temp_db_path)

        # Create lineage
        parent_id = store.insert(
            code="# Parent",
            metrics=FitnessMetrics(
                sharpe_ratio=1.0,
                calmar_ratio=1.5,
                max_drawdown=0.10,
                cagr=0.15,
                total_return=0.20,
                trade_count=50,
                win_rate=0.50,
            ),
            experiment="test_lineage",
        )

        child_id = store.insert(
            code="# Child",
            metrics=FitnessMetrics(
                sharpe_ratio=2.0,
                calmar_ratio=2.5,
                max_drawdown=0.08,
                cagr=0.20,
                total_return=0.35,
                trade_count=75,
                win_rate=0.55,
            ),
            parent_id=parent_id,
            experiment="test_lineage",
        )

        with cli_runner.isolated_filesystem():
            result = cli_runner.invoke(
                evolve,
                [
                    "--db",
                    str(temp_db_path),
                    "export",
                    child_id,
                    "-o",
                    "output.py",
                    "--with-lineage",
                ],
            )

            assert result.exit_code == 0
            content = Path("output.py").read_text()
            assert "Lineage:" in content
            assert parent_id[:8] in content
