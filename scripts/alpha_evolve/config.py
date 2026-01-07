"""
Evolution Configuration with Pydantic validation.

Supports loading from:
1. Environment variables (EVOLVE_* prefix)
2. YAML configuration file
3. Default values

Priority: Environment > YAML > Defaults
"""

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EvolutionConfig(BaseSettings):
    """
    Configuration for evolution process.

    Supports loading from YAML file with environment variable overrides.
    """

    model_config = SettingsConfigDict(
        env_prefix="EVOLVE_",
        case_sensitive=False,
        extra="ignore",
    )

    # Population Management
    population_size: int = Field(500, ge=10, description="Maximum strategies")
    archive_size: int = Field(50, ge=1, description="Protected performers")

    # Selection Ratios
    elite_ratio: float = Field(0.1, ge=0.0, le=1.0, description="Elite selection")
    exploration_ratio: float = Field(0.2, ge=0.0, le=1.0, description="Random selection")

    # Execution
    max_concurrent: int = Field(2, ge=1, description="Parallel evaluations")

    @field_validator("elite_ratio", "exploration_ratio", mode="before")
    @classmethod
    def validate_ratio(cls, v):
        """Ensure ratios are floats."""
        return float(v)

    @model_validator(mode="after")
    def validate_constraints(self):
        """Cross-field validation."""
        # Archive must be smaller than population
        if self.archive_size >= self.population_size:
            raise ValueError(
                f"archive_size ({self.archive_size}) must be < "
                f"population_size ({self.population_size})"
            )

        # Ratios must sum to <= 1.0
        if self.elite_ratio + self.exploration_ratio > 1.0:
            raise ValueError(
                f"elite_ratio ({self.elite_ratio}) + exploration_ratio "
                f"({self.exploration_ratio}) must be <= 1.0"
            )

        return self

    @classmethod
    def load(cls, config_path: Path | None = None) -> "EvolutionConfig":
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
        """
        import os

        yaml_values = {}

        # Load from YAML if provided
        if config_path and config_path.exists():
            with open(config_path) as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    yaml_values = yaml_data

        # Build final config: start with YAML, override with env
        # This ensures env > yaml > defaults priority
        final_values = {}

        # Get defaults from model fields
        field_names = list(cls.model_fields.keys())

        for name in field_names:
            # Check env first (highest priority)
            env_name = f"EVOLVE_{name.upper()}"
            if env_name in os.environ:
                # Env var exists, Pydantic will pick it up automatically
                continue
            # Otherwise use YAML value if present
            if name in yaml_values:
                final_values[name] = yaml_values[name]

        # Create config - Pydantic will use env > final_values > defaults
        return cls(**final_values)

    def validate(self) -> None:  # type: ignore[override]
        """
        Re-validate configuration parameters.

        This method re-runs Pydantic validation on the current instance.
        Useful after programmatic modifications to ensure constraints are met.

        Raises:
            ValidationError: If parameters are invalid

        Validations:
            - population_size >= 10
            - archive_size >= 1
            - archive_size < population_size
            - 0.0 <= elite_ratio <= 1.0
            - 0.0 <= exploration_ratio <= 1.0
            - elite_ratio + exploration_ratio <= 1.0
            - max_concurrent >= 1
        """
        # Re-run Pydantic validation
        self.model_validate(self.model_dump())

    def to_dict(self) -> dict:
        """
        Export configuration as dictionary.

        Returns:
            Dict with all configuration values
        """
        return self.model_dump()
