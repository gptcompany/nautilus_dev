"""Reconnection utilities with exponential backoff.

This module provides utilities for handling WebSocket reconnections
with exponential backoff delays.
"""

import asyncio
from dataclasses import dataclass
from typing import Callable, TypeVar

from scripts.ccxt_pipeline.utils.logging import get_logger

logger = get_logger("reconnect")

T = TypeVar("T")


@dataclass
class ExponentialBackoff:
    """Exponential backoff calculator for reconnection delays.

    Calculates delays following the pattern: initial * (multiplier ^ attempt)
    Delays are capped at max_delay.

    Attributes:
        initial_delay: Initial delay in seconds (default: 1.0).
        max_delay: Maximum delay in seconds (default: 16.0).
        max_retries: Maximum number of retries before giving up (default: 5).
        multiplier: Multiplier for each retry (default: 2.0).
    """

    initial_delay: float = 1.0
    max_delay: float = 16.0
    max_retries: int = 5
    multiplier: float = 2.0

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: Zero-based attempt number (0 = first retry).

        Returns:
            Delay in seconds, capped at max_delay.
        """
        delay = self.initial_delay * (self.multiplier**attempt)
        return min(delay, self.max_delay)

    def should_retry(self, attempt: int) -> bool:
        """Check if another retry should be attempted.

        Args:
            attempt: Zero-based attempt number.

        Returns:
            True if attempt < max_retries, False otherwise.
        """
        return attempt < self.max_retries


class ReconnectingStream:
    """Wrapper for WebSocket streams with automatic reconnection.

    Handles connection errors with exponential backoff and automatic
    reconnection. Resets retry counter on successful data receipt.

    Attributes:
        backoff: ExponentialBackoff configuration.
    """

    def __init__(
        self,
        backoff: ExponentialBackoff | None = None,
    ) -> None:
        """Initialize the reconnecting stream.

        Args:
            backoff: Backoff configuration. Uses defaults if None.
        """
        self.backoff = backoff or ExponentialBackoff()
        self._retry_count = 0
        self._running = False

    def reset_retries(self) -> None:
        """Reset retry counter after successful data receipt."""
        self._retry_count = 0

    async def run(
        self,
        stream_func: Callable[[], T],
        process_func: Callable[[T], None],
        symbol: str,
    ) -> None:
        """Run the stream with automatic reconnection.

        Args:
            stream_func: Async function that returns stream data.
            process_func: Function to process received data.
            symbol: Symbol being streamed (for logging).

        Raises:
            ConnectionError: If max retries exceeded.
            asyncio.CancelledError: If stream is cancelled.
        """
        self._running = True

        while self._running:
            try:
                data = await stream_func()
                self.reset_retries()
                process_func(data)

            except asyncio.CancelledError:
                logger.info(f"Stream cancelled for {symbol}")
                raise

            except Exception as e:
                if not self.backoff.should_retry(self._retry_count):
                    logger.error(
                        f"Max retries exceeded for {symbol} after {self._retry_count} attempts"
                    )
                    raise ConnectionError(f"Max retries exceeded ({self._retry_count})") from e

                delay = self.backoff.get_delay(self._retry_count)
                logger.warning(
                    f"Stream error for {symbol}: {e}. "
                    f"Retry {self._retry_count + 1}/{self.backoff.max_retries} in {delay}s"
                )
                self._retry_count += 1
                await asyncio.sleep(delay)

    def stop(self) -> None:
        """Stop the stream."""
        self._running = False
