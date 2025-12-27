"""Tests for Alpha-Evolve Mutator."""


import pytest

from scripts.alpha_evolve.mutator import (
    LLMMutator,
    MockMutator,
    MutationRequest,
    MutationResponse,
)
from scripts.alpha_evolve.store import FitnessMetrics


# === FIXTURES ===


@pytest.fixture
def sample_parent_code() -> str:
    """Sample parent strategy with EVOLVE-BLOCK."""
    return '''"""Momentum strategy."""

from nautilus_trader.trading.strategy import Strategy


class MomentumEvolveStrategy(Strategy):
    """Momentum strategy."""

    def on_start(self):
        """Initialize."""
        self.ema = ExponentialMovingAverage(period=20)

    def on_bar(self, bar):
        """Handle bar."""
        self.ema.handle_bar(bar)
        # === EVOLVE-BLOCK: decision_logic ===
        if self.ema.value > bar.close * 1.02:
            self.buy()
        elif self.ema.value < bar.close * 0.98:
            self.sell()
        # === END EVOLVE-BLOCK ===
'''


@pytest.fixture
def sample_metrics() -> FitnessMetrics:
    """Sample fitness metrics."""
    return FitnessMetrics(
        sharpe_ratio=1.5,
        calmar_ratio=2.0,
        max_drawdown=0.15,
        cagr=0.30,
        total_return=0.45,
        trade_count=100,
        win_rate=0.55,
    )


@pytest.fixture
def llm_mutator() -> LLMMutator:
    """LLM mutator with default settings."""
    return LLMMutator(max_retries=3, retry_delay=0.01)


# === PHASE 5: USER STORY 3 - LLM MUTATION TESTS (T032-T037) ===


class TestMutationRequestCreation:
    """T032: Test MutationRequest creation."""

    def test_mutation_request_valid(
        self, sample_parent_code: str, sample_metrics: FitnessMetrics
    ):
        """Valid mutation request passes validation."""
        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=sample_metrics,
            block_name="decision_logic",
        )

        assert request.parent_code == sample_parent_code
        assert request.parent_metrics == sample_metrics
        assert request.block_name == "decision_logic"
        assert request.retry_count == 0

    def test_mutation_request_with_guidance(
        self, sample_parent_code: str, sample_metrics: FitnessMetrics
    ):
        """Mutation request accepts guidance."""
        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=sample_metrics,
            guidance="Focus on reducing drawdown",
        )

        assert request.guidance == "Focus on reducing drawdown"

    def test_mutation_request_invalid_retry_count_negative(
        self, sample_parent_code: str
    ):
        """Negative retry count raises error."""
        with pytest.raises(ValueError, match="retry_count must be >= 0"):
            MutationRequest(
                parent_code=sample_parent_code,
                parent_metrics=None,
                retry_count=-1,
            )

    def test_mutation_request_invalid_retry_count_too_high(
        self, sample_parent_code: str
    ):
        """Retry count > 3 raises error."""
        with pytest.raises(ValueError, match="retry_count must be <= 3"):
            MutationRequest(
                parent_code=sample_parent_code,
                parent_metrics=None,
                retry_count=5,
            )


class TestMutationResponseSuccess:
    """T033: Test successful MutationResponse."""

    def test_mutation_response_success(self):
        """Successful response has mutated code."""
        response = MutationResponse(
            success=True,
            mutated_code="# mutated code",
        )

        assert response.success is True
        assert response.mutated_code == "# mutated code"
        assert response.error is None
        assert response.error_type is None

    def test_mutation_response_fields(self):
        """Response has expected fields."""
        response = MutationResponse(
            success=True,
            mutated_code="code",
        )

        assert hasattr(response, "success")
        assert hasattr(response, "mutated_code")
        assert hasattr(response, "error")
        assert hasattr(response, "error_type")


class TestMutationResponseSyntaxError:
    """T034: Test MutationResponse with syntax error."""

    def test_mutation_response_syntax_error(self):
        """Failed response with syntax error."""
        response = MutationResponse(
            success=False,
            error="SyntaxError at line 5",
            error_type="syntax",
        )

        assert response.success is False
        assert response.mutated_code is None
        assert "SyntaxError" in response.error
        assert response.error_type == "syntax"

    def test_mutation_response_block_not_found(self):
        """Failed response when block not found."""
        response = MutationResponse(
            success=False,
            error="Block 'entry_logic' not found",
            error_type="block_not_found",
        )

        assert response.success is False
        assert response.error_type == "block_not_found"


class TestLLMMutatorRetryOnSyntaxError:
    """T035: Test LLM mutator retry on syntax error."""

    @pytest.mark.asyncio
    async def test_llm_mutator_retry_on_syntax_error(
        self, sample_parent_code: str, sample_metrics: FitnessMetrics
    ):
        """Mutator retries on syntax error."""
        mutator = LLMMutator(max_retries=3, retry_delay=0.01)

        # Track call count
        call_count = [0]
        original_call_llm = mutator._call_llm

        async def mock_call_llm(prompt, request):
            call_count[0] += 1
            if call_count[0] < 3:
                # Return invalid syntax first 2 times
                return "if True\n    pass"  # Missing colon
            # Return valid syntax on 3rd attempt
            return """if self.ema.value > bar.close * 1.03:
    self.buy()
elif self.ema.value < bar.close * 0.97:
    self.sell()"""

        mutator._call_llm = mock_call_llm

        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=sample_metrics,
            block_name="decision_logic",
        )

        response = await mutator.mutate(request)

        # Should have retried
        assert call_count[0] == 3


class TestLLMMutatorMaxRetries:
    """T036: Test LLM mutator max retries."""

    @pytest.mark.asyncio
    async def test_llm_mutator_max_retries(
        self, sample_parent_code: str, sample_metrics: FitnessMetrics
    ):
        """Mutator gives up after max retries."""
        mutator = LLMMutator(max_retries=3, retry_delay=0.01)

        # Always return invalid syntax
        async def mock_call_llm(prompt, request):
            return "if True\n    pass"  # Always invalid

        mutator._call_llm = mock_call_llm

        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=sample_metrics,
            block_name="decision_logic",
        )

        response = await mutator.mutate(request)

        # Should fail after all retries
        assert response.success is False
        assert response.error_type == "llm_error"
        assert "retries" in response.error.lower()


class TestMutationPromptIncludesMetrics:
    """T037: Test mutation prompt includes metrics."""

    def test_build_prompt_includes_metrics(
        self, sample_parent_code: str, sample_metrics: FitnessMetrics, llm_mutator
    ):
        """Prompt includes parent metrics."""
        from scripts.alpha_evolve.patching import extract_blocks

        blocks = extract_blocks(sample_parent_code)
        prompt = llm_mutator._build_prompt(
            MutationRequest(
                parent_code=sample_parent_code,
                parent_metrics=sample_metrics,
            ),
            blocks.get("decision_logic", ""),
        )

        # Check metrics are included
        assert "Calmar" in prompt
        assert "Sharpe" in prompt
        assert "Drawdown" in prompt
        assert "Win Rate" in prompt

    def test_build_prompt_without_metrics(self, sample_parent_code: str, llm_mutator):
        """Prompt works without metrics."""
        from scripts.alpha_evolve.patching import extract_blocks

        blocks = extract_blocks(sample_parent_code)
        prompt = llm_mutator._build_prompt(
            MutationRequest(
                parent_code=sample_parent_code,
                parent_metrics=None,
            ),
            blocks.get("decision_logic", ""),
        )

        # Should still contain instructions
        assert "EVOLVE-BLOCK" in prompt
        assert "mutating" in prompt.lower()


# === MOCK MUTATOR TESTS ===


class TestMockMutator:
    """Tests for MockMutator."""

    @pytest.mark.asyncio
    async def test_mock_mutator_no_mutations(self, sample_parent_code: str):
        """Mock mutator returns original when no mutations configured."""
        mutator = MockMutator()

        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=None,
            block_name="decision_logic",
        )

        response = await mutator.mutate(request)

        assert response.success is True
        assert response.mutated_code is not None

    @pytest.mark.asyncio
    async def test_mock_mutator_with_mutations(self, sample_parent_code: str):
        """Mock mutator returns configured mutations in sequence."""
        mutations = [
            "# mutation 1\npass",
            "# mutation 2\npass",
        ]
        mutator = MockMutator(mutations=mutations)

        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=None,
            block_name="decision_logic",
        )

        # First call
        response1 = await mutator.mutate(request)
        assert response1.success is True
        assert "mutation 1" in response1.mutated_code

        # Second call
        response2 = await mutator.mutate(request)
        assert response2.success is True
        assert "mutation 2" in response2.mutated_code

        # Third call wraps around
        response3 = await mutator.mutate(request)
        assert response3.success is True
        assert "mutation 1" in response3.mutated_code


# === LLM MUTATOR BLOCK NOT FOUND ===


class TestLLMMutatorBlockNotFound:
    """Test LLM mutator when block not found."""

    @pytest.mark.asyncio
    async def test_mutate_block_not_found(self, llm_mutator: LLMMutator):
        """Mutator returns error when block not found."""
        code_without_block = '''"""Simple strategy."""

class SimpleStrategy:
    def on_bar(self, bar):
        pass
'''

        request = MutationRequest(
            parent_code=code_without_block,
            parent_metrics=None,
            block_name="decision_logic",
        )

        response = await llm_mutator.mutate(request)

        assert response.success is False
        assert response.error_type == "block_not_found"
        assert "decision_logic" in response.error


# === LLM MUTATOR SUCCESS ===


class TestLLMMutatorSuccess:
    """Test successful LLM mutations."""

    @pytest.mark.asyncio
    async def test_mutate_success(
        self,
        sample_parent_code: str,
        sample_metrics: FitnessMetrics,
        llm_mutator: LLMMutator,
    ):
        """Successful mutation returns patched code."""
        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=sample_metrics,
            block_name="decision_logic",
        )

        response = await llm_mutator.mutate(request)

        # Mock mutator returns modified code
        assert response.success is True
        assert response.mutated_code is not None
        # Should still have EVOLVE-BLOCK markers
        assert "EVOLVE-BLOCK" in response.mutated_code


# === VALIDATION TESTS ===


class TestMutationValidation:
    """Test mutation syntax validation."""

    def test_validate_mutation_valid(self, llm_mutator: LLMMutator):
        """Valid code passes validation."""
        valid_code = """if self.ema.value > bar.close:
    self.buy()"""

        error = llm_mutator._validate_mutation(valid_code)
        assert error is None

    def test_validate_mutation_invalid(self, llm_mutator: LLMMutator):
        """Invalid syntax returns error."""
        invalid_code = """if True
    pass"""  # Missing colon

        error = llm_mutator._validate_mutation(invalid_code)
        assert error is not None
        assert "syntax" in error.lower() or "Syntax" in error


# === RETRY PROMPT TESTS ===


class TestRetryPrompt:
    """Test retry prompt building."""

    def test_build_retry_prompt_includes_error(
        self, sample_parent_code: str, sample_metrics: FitnessMetrics, llm_mutator
    ):
        """Retry prompt includes error context."""
        request = MutationRequest(
            parent_code=sample_parent_code,
            parent_metrics=sample_metrics,
        )

        failed_code = "if True\n    pass"
        error = "SyntaxError: invalid syntax"

        retry_prompt = llm_mutator._build_retry_prompt(request, failed_code, error)

        assert "PREVIOUS ATTEMPT FAILED" in retry_prompt
        assert "SyntaxError" in retry_prompt
        assert failed_code in retry_prompt
