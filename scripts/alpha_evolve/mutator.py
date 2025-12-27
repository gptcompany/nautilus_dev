"""
Alpha-Evolve Mutator - LLM-based code mutation.

Provides code mutation capabilities using Claude Code alpha-evolve agent.
Implements retry logic, syntax validation, and graceful degradation.

Part of spec-009: Alpha-Evolve Controller & CLI
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from scripts.alpha_evolve.store import FitnessMetrics

from scripts.alpha_evolve.patching import apply_patch, extract_blocks, validate_syntax

logger = logging.getLogger("alpha_evolve.mutator")


@dataclass
class MutationRequest:
    """Request payload for LLM mutation."""

    parent_code: str
    parent_metrics: FitnessMetrics | None
    block_name: str = "decision_logic"
    guidance: str = ""

    previous_error: str | None = None
    retry_count: int = 0

    def __post_init__(self) -> None:
        """Validate request parameters."""
        if self.retry_count < 0:
            raise ValueError("retry_count must be >= 0")
        if self.retry_count > 3:
            raise ValueError("retry_count must be <= 3")


@dataclass
class MutationResponse:
    """Response from LLM mutation request."""

    success: bool
    mutated_code: str | None = None
    error: str | None = None
    error_type: str | None = None  # "syntax", "block_not_found", "llm_error"


class Mutator(Protocol):
    """Protocol for code mutation providers."""

    async def mutate(self, request: MutationRequest) -> MutationResponse:
        """
        Generate mutation for strategy code.

        Args:
            request: Mutation request with parent code and metrics

        Returns:
            MutationResponse with mutated code or error
        """
        ...


class LLMMutator:
    """LLM-based code mutation using alpha-evolve agent."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize LLM mutator.

        Args:
            max_retries: Maximum retry attempts per mutation
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def mutate(self, request: MutationRequest) -> MutationResponse:
        """
        Request mutation via alpha-evolve agent.

        Args:
            request: Mutation request with parent code and metrics

        Returns:
            MutationResponse with patched code or error
        """
        # Extract existing block
        blocks = extract_blocks(request.parent_code)
        if request.block_name not in blocks:
            return MutationResponse(
                success=False,
                error=f"Block '{request.block_name}' not found in parent code",
                error_type="block_not_found",
            )

        # Build prompt
        prompt = self._build_prompt(request, blocks[request.block_name])

        # Attempt mutation with retries
        for attempt in range(self.max_retries):
            try:
                mutated_block = await self._call_llm(prompt, request)

                if mutated_block is None:
                    logger.warning(f"LLM returned None (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    continue

                # Validate syntax of the new block
                validation_error = self._validate_mutation(mutated_block)
                if validation_error:
                    logger.warning(
                        f"Syntax error in mutation (attempt {attempt + 1}): {validation_error}"
                    )
                    # Update prompt with error context for retry
                    prompt = self._build_retry_prompt(
                        request, mutated_block, validation_error
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    continue

                # Apply patch to parent code
                patched_code = apply_patch(
                    request.parent_code,
                    request.block_name,
                    mutated_block,
                )

                # Final syntax check on complete code
                full_validation = validate_syntax(patched_code)
                if full_validation:
                    logger.warning(
                        f"Full code syntax error (attempt {attempt + 1}): {full_validation}"
                    )
                    prompt = self._build_retry_prompt(
                        request, mutated_block, full_validation
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                    continue

                logger.info(f"Mutation successful after {attempt + 1} attempt(s)")
                return MutationResponse(
                    success=True,
                    mutated_code=patched_code,
                )

            except Exception as e:
                logger.error(f"LLM call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                continue

        # All retries exhausted
        return self._handle_unavailable(request)

    def _build_prompt(self, request: MutationRequest, current_block: str) -> str:
        """
        Build mutation prompt for LLM.

        Args:
            request: Mutation request
            current_block: Current code in the EVOLVE-BLOCK

        Returns:
            Formatted prompt string
        """
        metrics_str = ""
        if request.parent_metrics:
            m = request.parent_metrics
            metrics_str = f"""Parent Strategy Performance:
- Calmar Ratio: {m.calmar_ratio:.4f}
- Sharpe Ratio: {m.sharpe_ratio:.4f}
- Max Drawdown: {m.max_drawdown:.2%}
- CAGR: {m.cagr:.2%}
- Win Rate: {m.win_rate:.2%}
- Trade Count: {m.trade_count}
"""

        guidance_str = ""
        if request.guidance:
            guidance_str = f"\nMutation Guidance:\n{request.guidance}\n"

        return f"""You are mutating a trading strategy's decision logic to improve performance.

{metrics_str}
Current EVOLVE-BLOCK ({request.block_name}):
```python
{current_block}
```
{guidance_str}
Requirements:
1. Return ONLY the new code for the EVOLVE-BLOCK body
2. Use native NautilusTrader indicators (no custom implementations)
3. Maintain the same function signature and return type
4. Focus on improving the Calmar ratio (CAGR / Max Drawdown)
5. Consider adding/modifying conditions, thresholds, or indicator combinations

Return ONLY the Python code, no explanations or markdown formatting.
"""

    def _build_retry_prompt(
        self,
        request: MutationRequest,
        failed_code: str,
        error: str,
    ) -> str:
        """
        Build retry prompt with error context.

        Args:
            request: Original mutation request
            failed_code: Code that failed validation
            error: Error message

        Returns:
            Updated prompt with error context
        """
        blocks = extract_blocks(request.parent_code)
        current_block = blocks.get(request.block_name, "")

        base_prompt = self._build_prompt(request, current_block)

        return f"""{base_prompt}

PREVIOUS ATTEMPT FAILED with error:
{error}

Failed code:
```python
{failed_code}
```

Please fix the syntax error and return valid Python code.
"""

    def _validate_mutation(self, code: str) -> str | None:
        """
        Validate Python syntax of mutated code block.

        Args:
            code: Code block to validate

        Returns:
            Error message if invalid, None if valid
        """
        # Wrap in function definition for syntax check
        wrapped = f"def _check():\n{_indent(code, 4)}"
        return validate_syntax(wrapped)

    def _handle_unavailable(self, request: MutationRequest) -> MutationResponse:
        """
        Handle graceful degradation when LLM is unavailable.

        Args:
            request: Original mutation request

        Returns:
            MutationResponse indicating failure
        """
        logger.warning("LLM unavailable after all retries, returning failure")
        return MutationResponse(
            success=False,
            error=f"LLM unavailable after {self.max_retries} retries",
            error_type="llm_error",
        )

    async def _call_llm(
        self,
        prompt: str,
        request: MutationRequest,
    ) -> str | None:
        """
        Call LLM to generate mutated code.

        This is a placeholder for actual LLM integration.
        In production, this would use the alpha-evolve agent.

        Args:
            prompt: Formatted prompt
            request: Original mutation request

        Returns:
            Generated code or None
        """
        # TODO: Integrate with alpha-evolve agent via Task tool
        # For now, return a simple modification for testing
        logger.debug("LLM call placeholder - returning mock mutation")

        blocks = extract_blocks(request.parent_code)
        if request.block_name not in blocks:
            return None

        # Return original block with a minor tweak for testing
        original = blocks[request.block_name]

        # Simple mutation: adjust thresholds slightly
        # This is a placeholder - real LLM would generate meaningful mutations
        mutated = original.replace("0.02", "0.025")
        if mutated == original:
            mutated = original.replace("0.03", "0.028")
        if mutated == original:
            # No change possible, just return original
            return original

        return mutated


class MockMutator:
    """Mock mutator for testing that returns deterministic mutations."""

    def __init__(self, mutations: list[str] | None = None) -> None:
        """
        Initialize mock mutator.

        Args:
            mutations: List of code blocks to return in sequence
        """
        self._mutations = mutations or []
        self._index = 0

    async def mutate(self, request: MutationRequest) -> MutationResponse:
        """Return next mutation in sequence."""
        if not self._mutations:
            # If no mutations provided, make a simple change to parent
            blocks = extract_blocks(request.parent_code)
            if request.block_name in blocks:
                patched = apply_patch(
                    request.parent_code,
                    request.block_name,
                    blocks[request.block_name],
                )
                return MutationResponse(success=True, mutated_code=patched)
            return MutationResponse(
                success=False,
                error="No mutations configured",
                error_type="llm_error",
            )

        if self._index >= len(self._mutations):
            self._index = 0

        mutation = self._mutations[self._index]
        self._index += 1

        # Apply mutation
        try:
            patched = apply_patch(
                request.parent_code,
                request.block_name,
                mutation,
            )
            return MutationResponse(success=True, mutated_code=patched)
        except Exception as e:
            return MutationResponse(
                success=False,
                error=str(e),
                error_type="syntax",
            )


def _indent(code: str, spaces: int) -> str:
    """Indent code by specified spaces."""
    prefix = " " * spaces
    lines = code.split("\n")
    return "\n".join(prefix + line if line.strip() else line for line in lines)
