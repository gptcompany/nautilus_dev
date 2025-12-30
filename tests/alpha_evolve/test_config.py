"""Tests for Evolution Configuration."""

from pathlib import Path

import pytest


class TestEvolutionConfigDefaults:
    """Test default configuration values."""

    def test_config_load_defaults(self):
        """T040: Load config with default values."""
        from scripts.alpha_evolve.config import EvolutionConfig

        config = EvolutionConfig.load()

        assert config.population_size == 500
        assert config.archive_size == 50
        assert config.elite_ratio == 0.1
        assert config.exploration_ratio == 0.2
        assert config.max_concurrent == 2


class TestEvolutionConfigYAML:
    """Test YAML configuration loading."""

    def test_config_load_from_yaml(self, sample_config_yaml: Path):
        """T041: Load config from YAML file."""
        from scripts.alpha_evolve.config import EvolutionConfig

        config = EvolutionConfig.load(sample_config_yaml)

        assert config.population_size == 100
        assert config.archive_size == 10
        assert config.elite_ratio == 0.15
        assert config.exploration_ratio == 0.25
        assert config.max_concurrent == 4

    def test_config_partial_override(self, partial_config_yaml: Path):
        """T042: Partial YAML overrides only specified values."""
        from scripts.alpha_evolve.config import EvolutionConfig

        config = EvolutionConfig.load(partial_config_yaml)

        # Overridden values
        assert config.population_size == 200
        assert config.archive_size == 20
        # Default values
        assert config.elite_ratio == 0.1
        assert config.exploration_ratio == 0.2
        assert config.max_concurrent == 2


class TestEvolutionConfigValidation:
    """Test configuration validation."""

    def test_config_validation_error(self, invalid_config_yaml: Path):
        """T043: Invalid config raises ValidationError."""
        from pydantic import ValidationError

        from scripts.alpha_evolve.config import EvolutionConfig

        with pytest.raises(ValidationError):
            EvolutionConfig.load(invalid_config_yaml)

    def test_config_validation_population_size_min(self, temp_db_dir: Path):
        """Population size must be >= 10."""
        from pydantic import ValidationError

        from scripts.alpha_evolve.config import EvolutionConfig

        config_path = temp_db_dir / "invalid.yaml"
        config_path.write_text("population_size: 5")

        with pytest.raises(ValidationError):
            EvolutionConfig.load(config_path)

    def test_config_validation_archive_less_than_population(self, temp_db_dir: Path):
        """Archive size must be less than population size."""
        from pydantic import ValidationError

        from scripts.alpha_evolve.config import EvolutionConfig

        config_path = temp_db_dir / "invalid.yaml"
        config_path.write_text("""
population_size: 50
archive_size: 100
""")

        with pytest.raises(ValidationError):
            EvolutionConfig.load(config_path)

    def test_config_validation_ratios_sum(self, temp_db_dir: Path):
        """Elite + exploration ratio must be <= 1.0."""
        from pydantic import ValidationError

        from scripts.alpha_evolve.config import EvolutionConfig

        config_path = temp_db_dir / "invalid.yaml"
        config_path.write_text("""
elite_ratio: 0.6
exploration_ratio: 0.6
""")

        with pytest.raises(ValidationError):
            EvolutionConfig.load(config_path)


class TestEvolutionConfigEnv:
    """Test environment variable overrides."""

    def test_config_env_override(self, monkeypatch):
        """T044: Environment variables override defaults."""
        from scripts.alpha_evolve.config import EvolutionConfig

        monkeypatch.setenv("EVOLVE_POPULATION_SIZE", "1000")
        monkeypatch.setenv("EVOLVE_MAX_CONCURRENT", "8")

        config = EvolutionConfig.load()

        assert config.population_size == 1000
        assert config.max_concurrent == 8
        # Non-overridden defaults
        assert config.archive_size == 50

    def test_config_env_override_yaml(self, sample_config_yaml: Path, monkeypatch):
        """Environment variables take priority over YAML."""
        from scripts.alpha_evolve.config import EvolutionConfig

        monkeypatch.setenv("EVOLVE_POPULATION_SIZE", "2000")

        config = EvolutionConfig.load(sample_config_yaml)

        # Env takes priority
        assert config.population_size == 2000
        # YAML values still used for non-env
        assert config.archive_size == 10


class TestEvolutionConfigMethods:
    """Test utility methods."""

    def test_config_to_dict(self):
        """Config can be exported as dictionary."""
        from scripts.alpha_evolve.config import EvolutionConfig

        config = EvolutionConfig.load()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "population_size" in config_dict
        assert config_dict["population_size"] == 500

    def test_config_validate_explicit(self, temp_db_dir: Path):
        """Validate method catches invalid state."""
        from scripts.alpha_evolve.config import EvolutionConfig

        # Valid config should not raise
        config = EvolutionConfig.load()
        config.validate()  # Should not raise
