"""Trade Classification Module (Spec 025).

This module provides trade classifiers for determining whether a trade
was buyer-initiated (BUY) or seller-initiated (SELL).

Classification Methods:
- TickRule: Uses price movement direction
- BVC (Bulk Volume Classification): Uses bar price range position
- CloseVsOpen: Uses bar open/close price comparison

References:
- Lee & Ready (1991): Tick rule classification
- Easley, Lopez de Prado, O'Hara (2012): VPIN and flow toxicity
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TradeSide(Enum):
    """Trade direction classification.

    Values:
        BUY: Trade was buyer-initiated (1)
        SELL: Trade was seller-initiated (-1)
        UNKNOWN: Cannot determine trade direction (0)
    """

    BUY = 1
    SELL = -1
    UNKNOWN = 0


@dataclass(frozen=True)
class TradeClassification:
    """Result of classifying a trade as buy or sell.

    Attributes:
        side: Classified direction (BUY, SELL, or UNKNOWN)
        volume: Trade volume
        price: Trade price
        timestamp_ns: Trade timestamp in nanoseconds
        method: Name of classification method used
        confidence: Confidence in classification [0.0, 1.0]
    """

    side: TradeSide
    volume: float
    price: float
    timestamp_ns: int
    method: str
    confidence: float = 1.0


class TickRuleClassifier:
    """Classify trades using the tick rule.

    The tick rule classifies trades based on price movement:
    - If price > previous price: BUY (uptick)
    - If price < previous price: SELL (downtick)
    - If price == previous price: Use previous classification (zero-tick rule)
    - If no previous classification: UNKNOWN

    This is the most common method for tick-by-tick data.

    References:
        Lee, C.M.C. & Ready, M.J. (1991). Inferring Trade Direction
        from Intraday Data. The Journal of Finance.
    """

    method_name: str = "tick_rule"

    def __init__(self) -> None:
        """Initialize the tick rule classifier."""
        self._prev_price: float | None = None
        self._prev_side: TradeSide = TradeSide.UNKNOWN

    def classify(
        self,
        price: float,
        volume: float,
        timestamp_ns: int,
        prev_price: float | None = None,
        open_price: float | None = None,  # noqa: ARG002
        high: float | None = None,  # noqa: ARG002
        low: float | None = None,  # noqa: ARG002
    ) -> TradeClassification:
        """Classify a trade using the tick rule.

        Args:
            price: Trade price (or bar close)
            volume: Trade volume
            timestamp_ns: Trade timestamp in nanoseconds
            prev_price: Previous price (optional, uses internal state if None)
            open_price: Unused (for interface compatibility)
            high: Unused (for interface compatibility)
            low: Unused (for interface compatibility)

        Returns:
            TradeClassification with side and metadata
        """
        # Use provided prev_price or internal state
        reference_price = prev_price if prev_price is not None else self._prev_price

        if reference_price is None:
            # First trade, no reference price
            side = TradeSide.UNKNOWN
        elif price > reference_price:
            # Uptick - buyer initiated
            side = TradeSide.BUY
        elif price < reference_price:
            # Downtick - seller initiated
            side = TradeSide.SELL
        else:
            # Zero tick - use previous classification
            side = self._prev_side

        # Update internal state
        self._prev_price = price
        if side != TradeSide.UNKNOWN:
            self._prev_side = side

        return TradeClassification(
            side=side,
            volume=volume,
            price=price,
            timestamp_ns=timestamp_ns,
            method=self.method_name,
            confidence=1.0,  # Tick rule has binary confidence
        )

    def reset(self) -> None:
        """Reset classifier state."""
        self._prev_price = None
        self._prev_side = TradeSide.UNKNOWN


class BVCClassifier:
    """Classify trades using Bulk Volume Classification (BVC).

    BVC splits volume based on the bar close price position within
    the bar's high-low range:
    - buy_ratio = (close - low) / (high - low)
    - If buy_ratio > 0.5: Classify as BUY
    - If buy_ratio <= 0.5: Classify as SELL

    Confidence is based on how far the ratio is from 0.5:
    - confidence = abs(0.5 - buy_ratio) * 2
    - A close near the high gives high BUY confidence
    - A close near the low gives high SELL confidence

    This method is designed for bar/candle data rather than tick data.

    References:
        Easley, D., Lopez de Prado, M., & O'Hara, M. (2012).
        The Volume Clock: Insights into the High-Frequency Paradigm.
    """

    method_name: str = "bvc"

    def classify(
        self,
        price: float,
        volume: float,
        timestamp_ns: int,
        prev_price: float | None = None,  # noqa: ARG002
        open_price: float | None = None,  # noqa: ARG002
        high: float | None = None,
        low: float | None = None,
    ) -> TradeClassification:
        """Classify a bar's volume using BVC.

        Args:
            price: Bar close price
            volume: Bar volume
            timestamp_ns: Bar timestamp in nanoseconds
            prev_price: Unused (for interface compatibility)
            open_price: Unused (for interface compatibility)
            high: Bar high price (required for BVC)
            low: Bar low price (required for BVC)

        Returns:
            TradeClassification with side and confidence

        Note:
            If high/low are not provided or high == low,
            returns UNKNOWN with zero confidence.
        """
        # Validate required parameters
        if high is None or low is None:
            return TradeClassification(
                side=TradeSide.UNKNOWN,
                volume=volume,
                price=price,
                timestamp_ns=timestamp_ns,
                method=self.method_name,
                confidence=0.0,
            )

        # Calculate bar range (add small epsilon to avoid division by zero)
        bar_range = high - low + 1e-10

        # Calculate buy ratio: position of close within the bar range
        # Close at high = 1.0, close at low = 0.0
        buy_ratio = (price - low) / bar_range

        # Determine side based on ratio
        if buy_ratio > 0.5:
            side = TradeSide.BUY
        else:
            side = TradeSide.SELL

        # Calculate confidence: distance from 0.5, scaled to [0, 1]
        # At extremes (0 or 1): confidence = 1.0
        # At midpoint (0.5): confidence = 0.0
        confidence = abs(0.5 - buy_ratio) * 2.0

        return TradeClassification(
            side=side,
            volume=volume,
            price=price,
            timestamp_ns=timestamp_ns,
            method=self.method_name,
            confidence=confidence,
        )

    def reset(self) -> None:
        """Reset classifier state (BVC is stateless)."""
        pass


class CloseVsOpenClassifier:
    """Classify trades by comparing bar close to open price.

    Simple classification based on bar direction:
    - If close > open: BUY (bullish bar)
    - If close < open: SELL (bearish bar)
    - If close == open: UNKNOWN (doji)

    This method is useful for bar/candle data when only
    open and close prices are available.
    """

    method_name: str = "close_vs_open"

    def classify(
        self,
        price: float,
        volume: float,
        timestamp_ns: int,
        prev_price: float | None = None,  # noqa: ARG002
        open_price: float | None = None,
        high: float | None = None,  # noqa: ARG002
        low: float | None = None,  # noqa: ARG002
    ) -> TradeClassification:
        """Classify a bar by comparing close to open.

        Args:
            price: Bar close price
            volume: Bar volume
            timestamp_ns: Bar timestamp in nanoseconds
            prev_price: Unused (for interface compatibility)
            open_price: Bar open price (required)
            high: Unused (for interface compatibility)
            low: Unused (for interface compatibility)

        Returns:
            TradeClassification with side

        Note:
            If open_price is not provided, returns UNKNOWN.
        """
        if open_price is None:
            return TradeClassification(
                side=TradeSide.UNKNOWN,
                volume=volume,
                price=price,
                timestamp_ns=timestamp_ns,
                method=self.method_name,
                confidence=0.0,
            )

        # Compare close to open
        if price > open_price:
            side = TradeSide.BUY
        elif price < open_price:
            side = TradeSide.SELL
        else:
            side = TradeSide.UNKNOWN

        return TradeClassification(
            side=side,
            volume=volume,
            price=price,
            timestamp_ns=timestamp_ns,
            method=self.method_name,
            confidence=1.0 if side != TradeSide.UNKNOWN else 0.0,
        )

    def reset(self) -> None:
        """Reset classifier state (CloseVsOpen is stateless)."""
        pass


def create_classifier(
    method: str,
) -> TickRuleClassifier | BVCClassifier | CloseVsOpenClassifier:
    """Factory function to create a trade classifier.

    Args:
        method: Classification method name
            - "tick_rule": Uses price movement direction
            - "bvc": Uses bar close position in high-low range
            - "close_vs_open": Uses bar close vs open comparison

    Returns:
        Classifier instance matching the requested method

    Raises:
        ValueError: If method is not recognized

    Example:
        >>> classifier = create_classifier("tick_rule")
        >>> result = classifier.classify(price=100.5, volume=10, timestamp_ns=12345)
    """
    classifiers = {
        "tick_rule": TickRuleClassifier,
        "bvc": BVCClassifier,
        "close_vs_open": CloseVsOpenClassifier,
    }

    if method not in classifiers:
        valid_methods = list(classifiers.keys())
        raise ValueError(
            f"Invalid classification method: '{method}'. "
            f"Valid methods: {valid_methods}"
        )

    return classifiers[method]()
