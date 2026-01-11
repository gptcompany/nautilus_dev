"""
Secrets validation module.

Validates that all required secrets are properly configured
and don't contain insecure default values.
"""

import os
import re
import sys
from dataclasses import dataclass

# Forbidden default values that indicate insecure configuration
FORBIDDEN_DEFAULTS = [
    "whale-dashboard-secret-dev",
    "admin",
    "password",
    "secret",
    "dev-secret",
    "test-secret",
    "change-me",
    "changeme",
    "default",
    "example",
    "placeholder",
    "research123",  # Neo4j default found in codebase
]

# Minimum lengths for different secret types
MIN_LENGTHS = {
    "JWT_SECRET": 32,
    "API_SECRET_KEY": 32,
    "GRAFANA_ADMIN_PASSWORD": 12,
    "REDIS_PASSWORD": 16,
    "WEBSOCKET_SECRET_KEY": 24,
    "HYPERLIQUID_TESTNET_PK": 64,
    "HYPERLIQUID_MAINNET_PK": 64,
}


@dataclass
class ValidationResult:
    """Result of secret validation."""

    secret_name: str
    is_valid: bool
    error: str | None = None
    warning: str | None = None


class SecretValidator:
    """Validates secrets configuration for security compliance."""

    def __init__(self, required_secrets: list[str] | None = None):
        """
        Initialize validator with required secrets list.

        Args:
            required_secrets: List of environment variable names that must be set.
                            If None, uses default critical secrets.
        """
        self.required_secrets = required_secrets or [
            "JWT_SECRET",
            "GRAFANA_ADMIN_PASSWORD",
        ]
        self.results: list[ValidationResult] = []

    def validate_secret(self, name: str) -> ValidationResult:
        """Validate a single secret."""
        value = os.getenv(name, "")

        # Check if set
        if not value:
            return ValidationResult(
                secret_name=name,
                is_valid=False,
                error=f"{name} is not set",
            )

        # Check for forbidden defaults
        value_lower = value.lower()
        for forbidden in FORBIDDEN_DEFAULTS:
            if forbidden in value_lower:
                return ValidationResult(
                    secret_name=name,
                    is_valid=False,
                    error=f"{name} contains forbidden default value",
                )

        # Check minimum length
        min_length = MIN_LENGTHS.get(name, 8)
        if len(value) < min_length:
            return ValidationResult(
                secret_name=name,
                is_valid=False,
                error=f"{name} is too short (min {min_length} chars)",
            )

        # Check for private key format
        if "PK" in name or "PRIVATE_KEY" in name:
            # Should be 64 hex characters (optionally with 0x prefix)
            clean_value = value.lower().removeprefix("0x")
            if not re.match(r"^[a-f0-9]{64}$", clean_value):
                return ValidationResult(
                    secret_name=name,
                    is_valid=False,
                    error=f"{name} is not a valid private key format (64 hex chars)",
                )

        # Check entropy (basic check - no repeated patterns)
        if len(set(value)) < len(value) / 4:
            return ValidationResult(
                secret_name=name,
                is_valid=True,
                warning=f"{name} has low entropy - consider regenerating",
            )

        return ValidationResult(
            secret_name=name,
            is_valid=True,
        )

    def validate_all(self) -> tuple[bool, list[ValidationResult]]:
        """
        Validate all required secrets.

        Returns:
            Tuple of (all_valid, results)
        """
        self.results = []
        all_valid = True

        for secret_name in self.required_secrets:
            result = self.validate_secret(secret_name)
            self.results.append(result)
            if not result.is_valid:
                all_valid = False

        return all_valid, self.results

    def print_report(self) -> None:
        """Print validation report to console."""
        print("\n" + "=" * 60)
        print("SECRETS VALIDATION REPORT")
        print("=" * 60 + "\n")

        for result in self.results:
            if result.is_valid:
                status = "PASS"
                if result.warning:
                    status = "WARN"
                    print(f"  [{status}] {result.secret_name}: {result.warning}")
                else:
                    print(f"  [{status}] {result.secret_name}")
            else:
                print(f"  [FAIL] {result.secret_name}: {result.error}")

        print("\n" + "-" * 60)

        failed = [r for r in self.results if not r.is_valid]
        if failed:
            print(f"RESULT: {len(failed)} secret(s) failed validation")
            print("\nTo generate secure secrets, run:")
            print("  ./scripts/security/generate_secrets.sh")
        else:
            print("RESULT: All secrets validated successfully")

        print("=" * 60 + "\n")


def validate_secrets(
    required: list[str] | None = None,
    exit_on_failure: bool = True,
) -> bool:
    """
    Validate secrets and optionally exit on failure.

    Args:
        required: List of required secret names
        exit_on_failure: If True, exits with code 1 on validation failure

    Returns:
        True if all secrets valid, False otherwise
    """
    validator = SecretValidator(required)
    all_valid, _ = validator.validate_all()
    validator.print_report()

    if not all_valid and exit_on_failure:
        sys.exit(1)

    return all_valid


if __name__ == "__main__":
    # When run directly, validate critical secrets
    critical_secrets = [
        "JWT_SECRET",
        "GRAFANA_ADMIN_PASSWORD",
    ]

    # Add optional secrets if they exist
    optional_secrets = [
        "HYPERLIQUID_TESTNET_PK",
        "HYPERLIQUID_MAINNET_PK",
        "DISCORD_WEBHOOK_URL",
        "SENTRY_DSN",
    ]

    for secret in optional_secrets:
        if os.getenv(secret):
            critical_secrets.append(secret)

    validate_secrets(critical_secrets)
