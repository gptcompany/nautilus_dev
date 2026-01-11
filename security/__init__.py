"""
Security module for NautilusTrader.

Provides:
- Secrets validation
- Secret management integration
- Security utilities
"""

from security.secrets_validator import SecretValidator, validate_secrets

__all__ = ["validate_secrets", "SecretValidator"]
