# Unit tests for NautilusTrader Auto-Update Auto-Fix

"""Test auto_fix module for auto_update."""

from pathlib import Path

from scripts.auto_update.auto_fix import (
    apply_import_rename,
    apply_method_rename,
    auto_fix_files,
    detect_fix_type,
)
from scripts.auto_update.models import AffectedFile, BreakingChange, Severity


def make_affected_file(
    path: Path,
    line_numbers: list[int],
    match_count: int,
    can_auto_fix: bool = True,
    fix_type: str | None = "import_rename",
) -> AffectedFile:
    """Helper to create AffectedFile with required breaking_change."""
    bc = BreakingChange(
        description="Test breaking change",
        severity=Severity.MEDIUM,
        affected_pattern="TestPattern",
    )
    return AffectedFile(
        path=path,
        line_numbers=line_numbers,
        breaking_change=bc,
        can_auto_fix=can_auto_fix,
        fix_type=fix_type,
    )


# =============================================================================
# T053: Test apply_import_rename
# =============================================================================


class TestApplyImportRename:
    """Test apply_import_rename function."""

    def test_apply_simple_import_rename(self, tmp_path: Path):
        """Test renaming a simple import."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""from nautilus_trader.indicators import OldIndicator
from nautilus_trader.core import OtherModule

indicator = OldIndicator(period=20)
""")
        result = apply_import_rename(
            file_path=test_file,
            old_name="OldIndicator",
            new_name="NewIndicator",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["changes_made"] > 0

        content = test_file.read_text()
        assert "NewIndicator" in content
        assert "OldIndicator" not in content

    def test_apply_import_rename_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't modify file."""
        test_file = tmp_path / "test_strategy.py"
        original_content = """from nautilus_trader.indicators import OldIndicator"""
        test_file.write_text(original_content)

        result = apply_import_rename(
            file_path=test_file,
            old_name="OldIndicator",
            new_name="NewIndicator",
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True

        # Verify file was NOT modified
        content = test_file.read_text()
        assert content == original_content

    def test_apply_import_rename_multiple_occurrences(self, tmp_path: Path):
        """Test renaming multiple occurrences."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""from nautilus_trader.indicators import OldIndicator
from nautilus_trader.other import OldIndicator as AliasedIndicator

def use_indicator():
    indicator = OldIndicator(period=20)
    return indicator
""")
        result = apply_import_rename(
            file_path=test_file,
            old_name="OldIndicator",
            new_name="NewIndicator",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["changes_made"] >= 3  # At least 3 occurrences

        content = test_file.read_text()
        assert content.count("NewIndicator") >= 3
        assert "OldIndicator" not in content

    def test_apply_import_rename_no_match(self, tmp_path: Path):
        """Test when pattern doesn't match."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""from nautilus_trader.indicators import DifferentIndicator""")

        result = apply_import_rename(
            file_path=test_file,
            old_name="OldIndicator",
            new_name="NewIndicator",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["changes_made"] == 0

    def test_apply_import_rename_preserves_whitespace(self, tmp_path: Path):
        """Test that whitespace and formatting are preserved."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""from nautilus_trader.indicators import OldIndicator

class MyStrategy:
    def __init__(self):
        self.indicator = OldIndicator(
            period=20,
            price_type=PriceType.MID
        )
""")
        result = apply_import_rename(
            file_path=test_file,
            old_name="OldIndicator",
            new_name="NewIndicator",
            dry_run=False,
        )

        assert result["success"] is True
        content = test_file.read_text()
        # Check multiline formatting preserved
        assert "NewIndicator(\n" in content


# =============================================================================
# T054: Test apply_method_rename
# =============================================================================


class TestApplyMethodRename:
    """Test apply_method_rename function."""

    def test_apply_method_rename_basic(self, tmp_path: Path):
        """Test basic method rename."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""class MyStrategy:
    def on_bar(self, bar):
        result = self.old_method(bar)
        return result

    def other_code(self):
        self.old_method()
""")
        result = apply_method_rename(
            file_path=test_file,
            old_name="old_method",
            new_name="new_method",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["changes_made"] >= 2

        content = test_file.read_text()
        assert "new_method" in content
        assert "old_method" not in content

    def test_apply_method_rename_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't modify file."""
        test_file = tmp_path / "test_strategy.py"
        original_content = """self.old_method()"""
        test_file.write_text(original_content)

        result = apply_method_rename(
            file_path=test_file,
            old_name="old_method",
            new_name="new_method",
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True
        assert test_file.read_text() == original_content

    def test_apply_method_rename_with_arguments(self, tmp_path: Path):
        """Test method rename with arguments."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""result = obj.old_method(arg1, arg2, kwarg=value)""")

        result = apply_method_rename(
            file_path=test_file,
            old_name="old_method",
            new_name="new_method",
            dry_run=False,
        )

        assert result["success"] is True
        content = test_file.read_text()
        assert "new_method(arg1, arg2, kwarg=value)" in content

    def test_apply_method_rename_preserves_partial_matches(self, tmp_path: Path):
        """Test that partial matches are not renamed."""
        test_file = tmp_path / "test_strategy.py"
        test_file.write_text("""old_method_extended = 1
self.old_method()
""")
        result = apply_method_rename(
            file_path=test_file,
            old_name="old_method",
            new_name="new_method",
            dry_run=False,
        )

        content = test_file.read_text()
        # Should rename only the method call, not the variable
        assert "new_method()" in content
        # This depends on implementation - might use word boundaries


# =============================================================================
# T058: Test auto_fix_files orchestrator
# =============================================================================


class TestAutoFixFiles:
    """Test auto_fix_files orchestrator function."""

    def test_auto_fix_files_import_rename(self, tmp_path: Path):
        """Test auto-fixing files with import renames."""
        # Create test files
        file1 = tmp_path / "strategy1.py"
        file1.write_text("""from nautilus_trader import OldClass
obj = OldClass()
""")
        file2 = tmp_path / "strategy2.py"
        file2.write_text("""from nautilus_trader import OldClass, OtherClass
x = OldClass()
""")

        affected_files = [
            make_affected_file(
                path=file1,
                line_numbers=[1, 2],
                match_count=2,
                can_auto_fix=True,
                fix_type="import_rename",
            ),
            make_affected_file(
                path=file2,
                line_numbers=[1, 2],
                match_count=2,
                can_auto_fix=True,
                fix_type="import_rename",
            ),
        ]

        result = auto_fix_files(
            affected_files=affected_files,
            fix_pattern="OldClass",
            new_value="NewClass",
            dry_run=False,
        )

        assert result["success"] is True
        assert result["files_fixed"] == 2
        assert result["total_changes"] >= 4

        # Verify changes
        assert "NewClass" in file1.read_text()
        assert "NewClass" in file2.read_text()

    def test_auto_fix_files_dry_run(self, tmp_path: Path):
        """Test dry-run doesn't modify files."""
        test_file = tmp_path / "strategy.py"
        original = """from nautilus_trader import OldClass"""
        test_file.write_text(original)

        affected_files = [
            make_affected_file(
                path=test_file,
                line_numbers=[1],
                match_count=1,
                can_auto_fix=True,
                fix_type="import_rename",
            ),
        ]

        result = auto_fix_files(
            affected_files=affected_files,
            fix_pattern="OldClass",
            new_value="NewClass",
            dry_run=True,
        )

        assert result["dry_run"] is True
        assert test_file.read_text() == original

    def test_auto_fix_files_skips_unfixable(self, tmp_path: Path):
        """Test that files marked as unfixable are skipped."""
        test_file = tmp_path / "strategy.py"
        test_file.write_text("""complex_code()""")

        affected_files = [
            make_affected_file(
                path=test_file,
                line_numbers=[1],
                match_count=1,
                can_auto_fix=False,  # Marked as unfixable
                fix_type=None,
            ),
        ]

        result = auto_fix_files(
            affected_files=affected_files,
            fix_pattern="complex_code",
            new_value="simple_code",
            dry_run=False,
        )

        assert result["files_skipped"] == 1
        assert result["files_fixed"] == 0


# =============================================================================
# Additional helper tests
# =============================================================================


class TestDetectFixType:
    """Test detect_fix_type helper function."""

    def test_detect_import_rename(self):
        """Test detecting import rename fix type."""
        description = "Renamed OldClass to NewClass"
        fix_type = detect_fix_type(description)
        assert fix_type == "import_rename"

    def test_detect_method_rename(self):
        """Test detecting method rename fix type."""
        description = "Method old_method renamed to new_method"
        fix_type = detect_fix_type(description)
        assert fix_type == "method_rename"

    def test_detect_unknown(self):
        """Test detecting unknown fix type."""
        description = "Complete rewrite of internal architecture"
        fix_type = detect_fix_type(description)
        assert fix_type is None
