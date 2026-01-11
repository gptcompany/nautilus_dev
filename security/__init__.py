"""
Security module for NautilusTrader.

Provides:
- Secrets validation (secrets_validator)
- Google Secret Manager integration with env fallback (secret_manager)
- ML model security: encryption, signing, integrity (ml_security)
- Security utilities
"""

from security.audit_trail import (
    AuditEvent,
    AuditEventType,
    AuditTrail,
    audit_log,
    verify_audit_trail,
)
from security.fraud_detection import (
    AlertSeverity,
    FraudAlert,
    FraudDetectionConfig,
    FraudDetector,
    FraudType,
    check_fraud,
)
from security.ml_security import (
    ModelEncryption,
    ModelIntegrity,
    ModelMetadata,
    ModelSigner,
    SecureModelLoader,
    VerificationResult,
    compute_model_hash,
    load_model_secure,
    verify_model_hash,
)
from security.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RateLimitResult,
    check_rate_limit,
)
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
    # ML Security
    "ModelEncryption",
    "ModelIntegrity",
    "ModelMetadata",
    "ModelSigner",
    "SecureModelLoader",
    "VerificationResult",
    "compute_model_hash",
    "load_model_secure",
    "verify_model_hash",
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
    # Rate Limiter
    "RateLimitConfig",
    "RateLimiter",
    "RateLimitResult",
    "check_rate_limit",
    # Audit Trail
    "AuditEvent",
    "AuditEventType",
    "AuditTrail",
    "audit_log",
    "verify_audit_trail",
    # Fraud Detection
    "AlertSeverity",
    "FraudAlert",
    "FraudDetectionConfig",
    "FraudDetector",
    "FraudType",
    "check_fraud",
]
