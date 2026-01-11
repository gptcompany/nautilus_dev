"""
Security module for NautilusTrader.

Provides:
- Secrets validation (secrets_validator)
- Google Secret Manager integration with env fallback (secret_manager)
- Security utilities
"""

from security.secret_manager import (
    SecretManager,
    SecretManagerError,
    SecretNotFoundError,
    get_secret,
    get_secrets,
    get_trading_secrets,
    is_gsm_available,
    validate_trading_secrets,
)
from security.secrets_validator import SecretValidator, validate_secrets

__all__ = [
    # Secret Manager
    "SecretManager",
    "SecretManagerError",
    "SecretNotFoundError",
    "get_secret",
    "get_secrets",
    "get_trading_secrets",
    "is_gsm_available",
    "validate_trading_secrets",
    # Secrets Validator
    "SecretValidator",
    "validate_secrets",
]
