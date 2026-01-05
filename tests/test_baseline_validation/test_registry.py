"""Unit tests for contender registry.

Tests for:
    - ContenderRegistry
    - get_default_contenders

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations

import pytest

from scripts.baseline_validation.registry import (
    ContenderRegistry,
    get_default_contenders,
)
from scripts.baseline_validation.sizers import (
    AdaptiveSizer,
    BuyAndHoldSizer,
    ContenderSizer,
    FixedFractionalSizer,
)


class TestContenderRegistry:
    """Tests for ContenderRegistry."""

    def test_init_empty(self) -> None:
        """Test empty initialization."""
        registry = ContenderRegistry()
        assert len(registry) == 0

    def test_register(self) -> None:
        """Test registering a contender."""
        registry = ContenderRegistry()
        sizer = FixedFractionalSizer(risk_pct=0.02)

        registry.register("fixed", sizer)

        assert len(registry) == 1
        assert "fixed" in registry

    def test_register_duplicate_raises(self) -> None:
        """Test that registering duplicate raises ValueError."""
        registry = ContenderRegistry()
        sizer = FixedFractionalSizer(risk_pct=0.02)

        registry.register("fixed", sizer)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("fixed", sizer)

    def test_unregister(self) -> None:
        """Test unregistering a contender."""
        registry = ContenderRegistry()
        sizer = FixedFractionalSizer(risk_pct=0.02)

        registry.register("fixed", sizer)
        registry.unregister("fixed")

        assert len(registry) == 0
        assert "fixed" not in registry

    def test_unregister_missing_raises(self) -> None:
        """Test that unregistering missing raises KeyError."""
        registry = ContenderRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.unregister("nonexistent")

    def test_get(self) -> None:
        """Test getting a contender."""
        registry = ContenderRegistry()
        sizer = FixedFractionalSizer(risk_pct=0.02)
        registry.register("fixed", sizer)

        retrieved = registry.get("fixed")

        assert retrieved is sizer

    def test_get_missing_raises(self) -> None:
        """Test that getting missing raises KeyError."""
        registry = ContenderRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.get("nonexistent")

    def test_has(self) -> None:
        """Test checking if contender exists."""
        registry = ContenderRegistry()
        sizer = FixedFractionalSizer(risk_pct=0.02)
        registry.register("fixed", sizer)

        assert registry.has("fixed") is True
        assert registry.has("nonexistent") is False

    def test_all(self) -> None:
        """Test iterating over all contenders."""
        registry = ContenderRegistry()
        fixed = FixedFractionalSizer(risk_pct=0.02)
        buyhold = BuyAndHoldSizer()

        registry.register("fixed", fixed)
        registry.register("buyhold", buyhold)

        items = list(registry.all())

        assert len(items) == 2
        assert ("fixed", fixed) in items
        assert ("buyhold", buyhold) in items

    def test_names(self) -> None:
        """Test getting list of names."""
        registry = ContenderRegistry()
        registry.register("fixed", FixedFractionalSizer())
        registry.register("buyhold", BuyAndHoldSizer())

        names = registry.names()

        assert "fixed" in names
        assert "buyhold" in names
        assert len(names) == 2

    def test_contains(self) -> None:
        """Test __contains__ protocol."""
        registry = ContenderRegistry()
        registry.register("fixed", FixedFractionalSizer())

        assert "fixed" in registry
        assert "nonexistent" not in registry


class TestContenderRegistryFromConfig:
    """Tests for ContenderRegistry.from_config."""

    def test_from_config_all_enabled(self) -> None:
        """Test creating registry from config with all enabled."""
        config = {
            "adaptive": {"enabled": True, "config": {}},
            "fixed": {"enabled": True, "config": {"risk_pct": 0.02}},
            "buyhold": {"enabled": True, "config": {}},
        }

        registry = ContenderRegistry.from_config(config)

        assert len(registry) == 3
        assert "adaptive" in registry
        assert "fixed" in registry
        assert "buyhold" in registry

    def test_from_config_some_disabled(self) -> None:
        """Test creating registry with some disabled."""
        config = {
            "adaptive": {"enabled": False, "config": {}},
            "fixed": {"enabled": True, "config": {}},
            "buyhold": {"enabled": True, "config": {}},
        }

        registry = ContenderRegistry.from_config(config)

        assert len(registry) == 2
        assert "adaptive" not in registry
        assert "fixed" in registry
        assert "buyhold" in registry

    def test_from_config_with_custom_config(self) -> None:
        """Test that custom config is applied."""
        config = {
            "fixed": {"enabled": True, "config": {"risk_pct": 0.05}},
        }

        registry = ContenderRegistry.from_config(config)
        sizer = registry.get("fixed")

        assert isinstance(sizer, FixedFractionalSizer)
        assert "Fixed 5%" in sizer.name

    def test_from_config_default_enabled(self) -> None:
        """Test that enabled defaults to True."""
        config = {
            "fixed": {"config": {}},  # No enabled field
        }

        registry = ContenderRegistry.from_config(config)

        assert "fixed" in registry


class TestContenderRegistryDefault:
    """Tests for ContenderRegistry.default."""

    def test_default_has_three_contenders(self) -> None:
        """Test default creates three contenders."""
        registry = ContenderRegistry.default()
        assert len(registry) == 3

    def test_default_has_adaptive(self) -> None:
        """Test default includes adaptive."""
        registry = ContenderRegistry.default()

        assert "adaptive" in registry
        assert isinstance(registry.get("adaptive"), AdaptiveSizer)

    def test_default_has_fixed(self) -> None:
        """Test default includes fixed."""
        registry = ContenderRegistry.default()

        assert "fixed" in registry
        assert isinstance(registry.get("fixed"), FixedFractionalSizer)

    def test_default_has_buyhold(self) -> None:
        """Test default includes buyhold."""
        registry = ContenderRegistry.default()

        assert "buyhold" in registry
        assert isinstance(registry.get("buyhold"), BuyAndHoldSizer)


class TestGetDefaultContenders:
    """Tests for get_default_contenders function."""

    def test_returns_dict(self) -> None:
        """Test returns dict of contenders."""
        contenders = get_default_contenders()

        assert isinstance(contenders, dict)
        assert len(contenders) == 3

    def test_has_all_contenders(self) -> None:
        """Test has all three contenders."""
        contenders = get_default_contenders()

        assert "adaptive" in contenders
        assert "fixed" in contenders
        assert "buyhold" in contenders

    def test_contenders_implement_protocol(self) -> None:
        """Test all contenders implement ContenderSizer."""
        contenders = get_default_contenders()

        for name, sizer in contenders.items():
            assert isinstance(sizer, ContenderSizer), (
                f"{name} should implement ContenderSizer"
            )
