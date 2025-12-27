"""
API Contract: Evolution Configuration

This module defines the public interface for configuration management.
Implementation should match these signatures exactly.
"""

from pathlib import Path
from typing import Optional


class EvolutionConfig:
    """
    Configuration for evolution process.

    Supports loading from YAML file with environment variable overrides.
    """

    # Evolution parameters
    population_size: int  # Max strategies (default: 500)
    archive_size: int  # Protected performers (default: 50)
    elite_ratio: float  # Elite selection ratio (default: 0.1)
    exploration_ratio: float  # Random selection ratio (default: 0.2)
    max_concurrent: int  # Max parallel evals (default: 2)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "EvolutionConfig":
        """
        Load configuration from file and environment.

        Args:
            config_path: Path to YAML config file (optional)

        Returns:
            EvolutionConfig instance

        Raises:
            ValidationError: If parameters are invalid

        Priority:
            1. Environment variables (EVOLVE_POPULATION_SIZE, etc.)
            2. YAML config file
            3. Default values

        Example:
            >>> config = EvolutionConfig.load()
            >>> config.population_size
            500
            >>> config = EvolutionConfig.load(Path("custom.yaml"))
        """
        ...

    def validate(self) -> None:
        """
        Validate configuration parameters.

        Raises:
            ValueError: If parameters are invalid

        Validations:
            - population_size >= 10
            - archive_size >= 1
            - archive_size < population_size
            - 0.0 <= elite_ratio <= 1.0
            - 0.0 <= exploration_ratio <= 1.0
            - elite_ratio + exploration_ratio <= 1.0
            - max_concurrent >= 1
        """
        ...

    def to_dict(self) -> dict:
        """
        Export configuration as dictionary.

        Returns:
            Dict with all configuration values
        """
        ...
