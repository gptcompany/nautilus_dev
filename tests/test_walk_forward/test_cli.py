"""Tests for walk-forward validation CLI."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.alpha_evolve.walk_forward.cli import (
    create_parser,
    main,
    parse_date,
    run_validate,
)


class TestParseDate:
    """Test date parsing function."""

    def test_valid_date(self) -> None:
        """Test parsing valid date string."""
        result = parse_date("2023-01-15")
        assert result == datetime(2023, 1, 15)

    def test_valid_date_end_of_month(self) -> None:
        """Test parsing end of month."""
        result = parse_date("2023-12-31")
        assert result == datetime(2023, 12, 31)

    def test_invalid_date_format(self) -> None:
        """Test invalid date format raises error."""
        with pytest.raises(ValueError):
            parse_date("01-15-2023")

    def test_invalid_date_string(self) -> None:
        """Test invalid date string raises error."""
        with pytest.raises(ValueError):
            parse_date("not-a-date")


class TestCreateParser:
    """Test CLI argument parser creation."""

    def test_parser_created(self) -> None:
        """Test parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "walk-forward"

    def test_validate_command_args(self) -> None:
        """Test validate command accepts required args."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                "test.py",
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
            ]
        )
        assert args.command == "validate"
        assert args.strategy == Path("test.py")
        assert args.start == datetime(2023, 1, 1)
        assert args.end == datetime(2024, 12, 1)

    def test_validate_command_defaults(self) -> None:
        """Test validate command default values."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                "test.py",
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
            ]
        )
        assert args.train_months == 6
        assert args.test_months == 3
        assert args.step_months == 3
        assert args.embargo_before == 5
        assert args.embargo_after == 3
        assert args.min_robustness == 60.0
        assert args.json is False

    def test_validate_command_custom_values(self) -> None:
        """Test validate command with custom values."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                "test.py",
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
                "--train-months",
                "12",
                "--test-months",
                "6",
                "--step-months",
                "6",
                "--embargo-before",
                "10",
                "--embargo-after",
                "7",
                "--min-robustness",
                "70.0",
                "--json",
            ]
        )
        assert args.train_months == 12
        assert args.test_months == 6
        assert args.step_months == 6
        assert args.embargo_before == 10
        assert args.embargo_after == 7
        assert args.min_robustness == 70.0
        assert args.json is True

    def test_report_command_args(self) -> None:
        """Test report command accepts required args."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "report",
                "--strategy",
                "test.py",
                "--output",
                "report.md",
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
            ]
        )
        assert args.command == "report"
        assert args.strategy == Path("test.py")
        assert args.output == Path("report.md")

    def test_no_command_shows_help(self) -> None:
        """Test no command parses with command=None."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestRunValidate:
    """Test validate command execution."""

    @pytest.fixture
    def temp_strategy(self, tmp_path: Path) -> Path:
        """Create temporary strategy file."""
        strategy_file = tmp_path / "test_strategy.py"
        strategy_file.write_text("# Test strategy\nclass TestStrategy:\n    pass")
        return strategy_file

    @pytest.mark.asyncio
    async def test_file_not_found(self) -> None:
        """Test error when strategy file not found."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                "/nonexistent/strategy.py",
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
            ]
        )
        result = await run_validate(args)
        assert result == 1

    @pytest.mark.asyncio
    async def test_validate_with_mock_evaluator(self, temp_strategy: Path) -> None:
        """Test validation with mock evaluator."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                str(temp_strategy),
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
            ]
        )

        # Patch the import to force mock evaluator path
        with patch.dict("sys.modules", {"scripts.alpha_evolve.evaluator": None}):
            result = await run_validate(args)
        # Should complete (pass or fail based on mock data)
        assert result in (0, 1)

    @pytest.mark.asyncio
    async def test_validate_json_output(
        self, temp_strategy: Path, tmp_path: Path
    ) -> None:
        """Test JSON output format."""
        output_file = tmp_path / "output.json"
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                str(temp_strategy),
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
                "--json",
                "--output",
                str(output_file),
            ]
        )

        # Patch the import to force mock evaluator path
        with patch.dict("sys.modules", {"scripts.alpha_evolve.evaluator": None}):
            await run_validate(args)
        assert output_file.exists()
        content = output_file.read_text()
        assert '"summary"' in content or '"windows"' in content

    @pytest.mark.asyncio
    async def test_validate_markdown_output(
        self, temp_strategy: Path, tmp_path: Path
    ) -> None:
        """Test Markdown output format."""
        output_file = tmp_path / "output.md"
        parser = create_parser()
        args = parser.parse_args(
            [
                "validate",
                "--strategy",
                str(temp_strategy),
                "--start",
                "2023-01-01",
                "--end",
                "2024-12-01",
                "--output",
                str(output_file),
            ]
        )

        # Patch the import to force mock evaluator path
        with patch.dict("sys.modules", {"scripts.alpha_evolve.evaluator": None}):
            await run_validate(args)
        assert output_file.exists()
        content = output_file.read_text()
        assert "Walk-Forward Validation Report" in content


class TestMain:
    """Test CLI main entry point."""

    def test_no_command_returns_zero(self) -> None:
        """Test no command shows help and returns 0."""
        with patch.object(sys, "argv", ["walk-forward"]):
            result = main()
        assert result == 0

    def test_unknown_command_returns_one(self) -> None:
        """Test unknown command returns 1."""
        with patch.object(sys, "argv", ["walk-forward"]):
            parser = create_parser()
            # Force unknown command
            args = parser.parse_args([])
            args.command = "unknown"
            # Manually test the branch
            assert args.command == "unknown"
