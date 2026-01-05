"""Contender registry for baseline validation.

This module provides a registry pattern for contender discovery and management.
Allows easy addition of new contenders without modifying core validation logic.

Usage:
    >>> registry = ContenderRegistry()
    >>> registry.register("adaptive", AdaptiveSizer())
    >>> registry.register("fixed", FixedFractionalSizer())
    >>>
    >>> for name, sizer in registry.all():
    ...     result = validate(sizer)
"""

from __future__ import annotations

from typing import Iterator

from scripts.baseline_validation.sizers import (
    AdaptiveSizer,
    BuyAndHoldSizer,
    ContenderSizer,
    FixedFractionalSizer,
    create_sizer,
)


class ContenderRegistry:
    """Registry for contender sizers.

    Provides:
        - Registration and lookup of contenders
        - Factory-based instantiation from config
        - Iteration over all registered contenders
        - Default contender configuration (A, B, C)
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._contenders: dict[str, ContenderSizer] = {}

    def register(self, name: str, sizer: ContenderSizer) -> None:
        """Register a contender.

        Args:
            name: Unique identifier for the contender.
            sizer: ContenderSizer instance.

        Raises:
            ValueError: If name is already registered.
        """
        if name in self._contenders:
            raise ValueError(f"Contender '{name}' is already registered")
        self._contenders[name] = sizer

    def unregister(self, name: str) -> None:
        """Remove a contender from the registry.

        Args:
            name: Contender identifier.

        Raises:
            KeyError: If name is not registered.
        """
        if name not in self._contenders:
            raise KeyError(f"Contender '{name}' is not registered")
        del self._contenders[name]

    def get(self, name: str) -> ContenderSizer:
        """Get a contender by name.

        Args:
            name: Contender identifier.

        Returns:
            ContenderSizer instance.

        Raises:
            KeyError: If name is not registered.
        """
        if name not in self._contenders:
            raise KeyError(f"Contender '{name}' is not registered")
        return self._contenders[name]

    def has(self, name: str) -> bool:
        """Check if a contender is registered.

        Args:
            name: Contender identifier.

        Returns:
            True if registered.
        """
        return name in self._contenders

    def all(self) -> Iterator[tuple[str, ContenderSizer]]:
        """Iterate over all registered contenders.

        Yields:
            Tuple of (name, sizer) for each contender.
        """
        yield from self._contenders.items()

    def names(self) -> list[str]:
        """Get list of registered contender names.

        Returns:
            List of contender names.
        """
        return list(self._contenders.keys())

    def __len__(self) -> int:
        """Number of registered contenders."""
        return len(self._contenders)

    def __contains__(self, name: str) -> bool:
        """Check if name is registered."""
        return name in self._contenders

    @classmethod
    def from_config(cls, config: dict) -> "ContenderRegistry":
        """Create registry from configuration dict or Pydantic models.

        Args:
            config: Dict with contender configurations.
                Expected format (plain dict):
                {
                    "adaptive": {"enabled": True, "config": {...}},
                    "fixed": {"enabled": True, "config": {...}},
                    "buyhold": {"enabled": True, "config": {...}},
                }
                Or dict of ContenderConfig Pydantic models.

        Returns:
            Configured ContenderRegistry.
        """
        registry = cls()

        for contender_type, contender_config in config.items():
            # Handle both Pydantic ContenderConfig and plain dicts
            if hasattr(contender_config, "enabled"):
                # Pydantic model
                if not contender_config.enabled:
                    continue
                sizer_config = contender_config.config
            else:
                # Plain dict
                if not contender_config.get("enabled", True):
                    continue
                sizer_config = contender_config.get("config", {})

            sizer = create_sizer(contender_type, sizer_config)
            registry.register(contender_type, sizer)

        return registry

    @classmethod
    def default(cls) -> "ContenderRegistry":
        """Create registry with default contenders (A, B, C).

        Returns:
            ContenderRegistry with:
                - adaptive: SOPS+Giller+Thompson
                - fixed: Fixed 2%
                - buyhold: Buy & Hold
        """
        registry = cls()

        # Contender A: Adaptive (SOPS+Giller+Thompson)
        registry.register("adaptive", AdaptiveSizer())

        # Contender B: Fixed 2%
        registry.register("fixed", FixedFractionalSizer(risk_pct=0.02))

        # Contender C: Buy & Hold
        registry.register("buyhold", BuyAndHoldSizer())

        return registry


def get_default_contenders() -> dict[str, ContenderSizer]:
    """Get default contenders as a dict.

    Convenience function for quick access to default configuration.

    Returns:
        Dict mapping contender name to sizer instance.
    """
    return {
        "adaptive": AdaptiveSizer(),
        "fixed": FixedFractionalSizer(risk_pct=0.02),
        "buyhold": BuyAndHoldSizer(),
    }
