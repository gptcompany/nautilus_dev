"""Tests for EVOLVE-BLOCK patching system."""

import pytest


class TestApplyPatch:
    """Tests for apply_patch function."""

    def test_apply_patch_full_replace(self, sample_strategy_single_block: str):
        """T007: Full code replacement via diff['code']."""
        from scripts.alpha_evolve.patching import apply_patch

        new_code = "# Completely new code\npass"
        diff = {"code": new_code}

        result = apply_patch(sample_strategy_single_block, diff)

        assert result == new_code
        assert "MomentumStrategy" not in result

    def test_apply_patch_block_replace(self, sample_strategy_single_block: str):
        """T008: Surgical block replacement via diff['blocks']."""
        from scripts.alpha_evolve.patching import apply_patch

        diff = {"blocks": {"entry_logic": "if bar.close > self.ema.value:\n    self.sell()"}}

        result = apply_patch(sample_strategy_single_block, diff)

        # Original structure preserved
        assert "class MomentumStrategy" in result
        assert "def on_bar" in result
        # Old logic replaced
        assert "self.buy()" not in result
        # New logic present
        assert "self.sell()" in result
        assert "bar.close > self.ema.value" in result

    def test_apply_patch_preserves_indentation(self, sample_strategy_nested_indentation: str):
        """T009: Indentation preserved when replacing blocks."""
        from scripts.alpha_evolve.patching import apply_patch

        # New logic without leading indentation - should be auto-indented
        diff = {"blocks": {"inner_logic": "result = i * 3 + 1"}}

        result = apply_patch(sample_strategy_nested_indentation, diff)

        # Check indentation is preserved (4 levels: class, def, if, for)
        lines = result.split("\n")
        for line in lines:
            if "result = i * 3 + 1" in line:
                # Should have proper indentation (16 spaces or 4 tabs)
                leading = len(line) - len(line.lstrip())
                assert leading >= 16, f"Expected indentation >= 16, got {leading}"
                break
        else:
            pytest.fail("New logic not found in result")

    def test_apply_patch_multiple_blocks(self, sample_strategy_multiple_blocks: str):
        """T010: Multiple blocks can be replaced in one patch."""
        from scripts.alpha_evolve.patching import apply_patch

        diff = {
            "blocks": {
                "indicators": "self.rsi = RelativeStrengthIndex(period=14)",
                "entry_logic": "if self.rsi.value < 30:\n    self.buy()",
                "exit_logic": "if self.rsi.value > 70:\n    self.sell()",
            }
        }

        result = apply_patch(sample_strategy_multiple_blocks, diff)

        # Check all blocks replaced
        assert "RelativeStrengthIndex" in result
        assert "rsi.value < 30" in result
        assert "rsi.value > 70" in result
        # Old logic gone
        assert "ema_fast" not in result
        assert "ema_slow" not in result

    def test_apply_patch_malformed_markers(self, sample_strategy_malformed: str):
        """T013a: ValueError raised for malformed markers."""
        from scripts.alpha_evolve.patching import apply_patch

        diff = {"blocks": {"broken": "new_code()"}}

        with pytest.raises(ValueError, match="malformed|missing|END"):
            apply_patch(sample_strategy_malformed, diff)


class TestExtractBlocks:
    """Tests for extract_blocks function."""

    def test_extract_blocks_single(self, sample_strategy_single_block: str):
        """T011: Extract single block from code."""
        from scripts.alpha_evolve.patching import extract_blocks

        blocks = extract_blocks(sample_strategy_single_block)

        assert "entry_logic" in blocks
        assert "self.buy()" in blocks["entry_logic"]
        assert len(blocks) == 1

    def test_extract_blocks_multiple(self, sample_strategy_multiple_blocks: str):
        """Extract multiple blocks from code."""
        from scripts.alpha_evolve.patching import extract_blocks

        blocks = extract_blocks(sample_strategy_multiple_blocks)

        assert len(blocks) == 3
        assert "indicators" in blocks
        assert "entry_logic" in blocks
        assert "exit_logic" in blocks
        assert "ema_fast" in blocks["indicators"]

    def test_extract_blocks_empty(self, sample_strategy_no_blocks: str):
        """Extract returns empty dict when no blocks."""
        from scripts.alpha_evolve.patching import extract_blocks

        blocks = extract_blocks(sample_strategy_no_blocks)

        assert blocks == {}


class TestValidateSyntax:
    """Tests for validate_syntax function."""

    def test_validate_syntax_valid(self):
        """T012: Valid Python code returns (True, '')."""
        from scripts.alpha_evolve.patching import validate_syntax

        code = """
def hello():
    return "world"

class Foo:
    pass
"""
        valid, msg = validate_syntax(code)

        assert valid is True
        assert msg == ""

    def test_validate_syntax_invalid(self):
        """T013: Invalid Python code returns (False, error_message)."""
        from scripts.alpha_evolve.patching import validate_syntax

        code = """
def broken(
    return "missing paren"
"""
        valid, msg = validate_syntax(code)

        assert valid is False
        assert msg != ""
        assert "line" in msg.lower() or "Line" in msg

    def test_validate_syntax_empty(self):
        """Empty code is valid."""
        from scripts.alpha_evolve.patching import validate_syntax

        valid, msg = validate_syntax("")

        assert valid is True
        assert msg == ""

    def test_validate_syntax_strategy(self, sample_strategy_single_block: str):
        """Real strategy code validates correctly."""
        from scripts.alpha_evolve.patching import validate_syntax

        valid, msg = validate_syntax(sample_strategy_single_block)

        assert valid is True
        assert msg == ""
