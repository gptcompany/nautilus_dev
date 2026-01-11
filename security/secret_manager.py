#!/usr/bin/env python3
"""
Google Secret Manager Client with Environment Fallback.

Provides a unified interface for secret retrieval:
1. First tries Google Secret Manager (if credentials available)
2. Falls back to environment variables
3. Caches secrets in memory for performance

Usage:
    from security.secret_manager import get_secret, SecretManager

    # Simple usage (auto-initializes)
    jwt_secret = get_secret("JWT_SECRET")
    neo4j_password = get_secret("NEO4J_PASSWORD")

    # Advanced usage with explicit manager
    sm = SecretManager(project_id="my-project")
    secret = sm.get("API_KEY", required=True)

Requirements:
    pip install google-cloud-secret-manager

Environment Variables:
    GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON (optional)
    GCP_PROJECT_ID: GCP project ID (optional, can auto-detect)
    SECRET_MANAGER_ENABLED: Set to "false" to disable GSM entirely
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from google.cloud.secretmanager_v1 import SecretManagerServiceClient

logger = logging.getLogger(__name__)

# Global cache for secrets (in-memory, cleared on process restart)
_secret_cache: dict[str, str] = {}


class SecretManagerError(Exception):
    """Base exception for secret manager errors."""

    pass


class SecretNotFoundError(SecretManagerError):
    """Secret not found in any source."""

    pass


class SecretManager:
    """
    Google Secret Manager client with environment fallback.

    Priority order:
    1. In-memory cache
    2. Google Secret Manager (if enabled and credentials available)
    3. Environment variables
    """

    def __init__(
        self,
        project_id: str | None = None,
        enabled: bool | None = None,
    ):
        """
        Initialize SecretManager.

        Args:
            project_id: GCP project ID. Auto-detects if not provided.
            enabled: Force enable/disable GSM. Auto-detects if None.
        """
        self._client: SecretManagerServiceClient | None = None
        self._project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self._enabled = self._determine_enabled(enabled)
        self._initialization_attempted = False

    def _determine_enabled(self, enabled: bool | None) -> bool:
        """Determine if GSM should be enabled."""
        if enabled is not None:
            return enabled

        # Check explicit disable
        env_enabled = os.getenv("SECRET_MANAGER_ENABLED", "true").lower()
        if env_enabled == "false":
            return False

        # Check if credentials are available
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            return True

        # Check if running on GCP (has default credentials)
        try:
            import google.auth

            google.auth.default()
            return True
        except Exception:
            return False

    def _get_client(self) -> SecretManagerServiceClient | None:
        """Lazy-load GSM client."""
        if self._initialization_attempted:
            return self._client

        self._initialization_attempted = True

        if not self._enabled:
            logger.debug("Secret Manager disabled, using env fallback")
            return None

        try:
            from google.cloud import secretmanager_v1

            self._client = secretmanager_v1.SecretManagerServiceClient()

            # Auto-detect project ID if not set
            if not self._project_id:
                try:
                    import google.auth

                    _, self._project_id = google.auth.default()
                except Exception:
                    pass

            if self._project_id:
                logger.info(f"Secret Manager initialized for project: {self._project_id}")
            else:
                logger.warning("Secret Manager client created but no project ID available")
                self._client = None

            return self._client

        except ImportError:
            logger.debug("google-cloud-secret-manager not installed, using env fallback")
            return None
        except Exception as e:
            logger.warning(f"Failed to initialize Secret Manager: {e}")
            return None

    def _get_from_gsm(self, name: str, version: str = "latest") -> str | None:
        """
        Get secret from Google Secret Manager.

        Args:
            name: Secret name (without project/version path)
            version: Secret version (default: "latest")

        Returns:
            Secret value or None if not found/error
        """
        client = self._get_client()
        if not client or not self._project_id:
            return None

        try:
            # Build the resource name
            resource_name = f"projects/{self._project_id}/secrets/{name}/versions/{version}"

            response = client.access_secret_version(request={"name": resource_name})
            secret_value = response.payload.data.decode("UTF-8")

            logger.debug(f"Secret '{name}' retrieved from GSM")
            return secret_value

        except Exception as e:
            # Log at debug level to avoid noise for expected misses
            logger.debug(f"Secret '{name}' not found in GSM: {e}")
            return None

    def _get_from_env(self, name: str) -> str | None:
        """Get secret from environment variable."""
        value = os.getenv(name)
        if value:
            logger.debug(f"Secret '{name}' retrieved from environment")
        return value

    def get(
        self,
        name: str,
        default: str | None = None,
        required: bool = False,
        version: str = "latest",
    ) -> str | None:
        """
        Get a secret value.

        Args:
            name: Secret name
            default: Default value if not found
            required: Raise exception if not found
            version: GSM version (default: "latest")

        Returns:
            Secret value

        Raises:
            SecretNotFoundError: If required=True and secret not found
        """
        # Check cache first
        if name in _secret_cache:
            logger.debug(f"Secret '{name}' retrieved from cache")
            return _secret_cache[name]

        # Try GSM first
        value = self._get_from_gsm(name, version)

        # Fall back to environment
        if value is None:
            value = self._get_from_env(name)

        # Use default
        if value is None:
            value = default

        # Handle required secrets
        if value is None and required:
            raise SecretNotFoundError(
                f"Required secret '{name}' not found in GSM or environment. "
                f"Set {name} environment variable or add to Google Secret Manager."
            )

        # Cache successful lookups
        if value is not None:
            _secret_cache[name] = value

        return value

    def set_cache(self, name: str, value: str) -> None:
        """
        Manually set a cached secret value.

        Useful for testing or overriding values.
        """
        _secret_cache[name] = value

    def clear_cache(self, name: str | None = None) -> None:
        """
        Clear cached secrets.

        Args:
            name: Specific secret to clear, or None to clear all
        """
        if name:
            _secret_cache.pop(name, None)
        else:
            _secret_cache.clear()

    def list_secrets(self) -> list[str]:
        """
        List available secret names from GSM.

        Returns:
            List of secret names (without version info)
        """
        client = self._get_client()
        if not client or not self._project_id:
            return []

        try:
            parent = f"projects/{self._project_id}"
            secrets = []

            for secret in client.list_secrets(request={"parent": parent}):
                # Extract just the secret name from the full path
                name = secret.name.split("/")[-1]
                secrets.append(name)

            return secrets

        except Exception as e:
            logger.warning(f"Failed to list secrets: {e}")
            return []

    def create_secret(self, name: str, value: str) -> bool:
        """
        Create a new secret in GSM.

        Args:
            name: Secret name
            value: Secret value

        Returns:
            True if created successfully
        """
        client = self._get_client()
        if not client or not self._project_id:
            logger.error("Cannot create secret: GSM not available")
            return False

        try:
            parent = f"projects/{self._project_id}"

            # Create the secret
            secret = client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

            # Add the secret version
            client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": value.encode("UTF-8")},
                }
            )

            logger.info(f"Secret '{name}' created in GSM")
            return True

        except Exception as e:
            logger.error(f"Failed to create secret '{name}': {e}")
            return False

    @property
    def is_gsm_available(self) -> bool:
        """Check if GSM is available and configured."""
        client = self._get_client()
        return client is not None and self._project_id is not None


# Global singleton instance
@lru_cache(maxsize=1)
def _get_default_manager() -> SecretManager:
    """Get or create the default SecretManager instance."""
    return SecretManager()


def get_secret(
    name: str,
    default: str | None = None,
    required: bool = False,
) -> str | None:
    """
    Get a secret value using the default manager.

    This is the recommended way to retrieve secrets.

    Args:
        name: Secret name
        default: Default value if not found
        required: Raise exception if not found

    Returns:
        Secret value

    Examples:
        # Optional secret with default
        api_key = get_secret("API_KEY", default="dev-key")

        # Required secret (raises if not found)
        jwt_secret = get_secret("JWT_SECRET", required=True)
    """
    return _get_default_manager().get(name, default=default, required=required)


def get_secrets(names: list[str], required: bool = False) -> dict[str, str | None]:
    """
    Get multiple secrets at once.

    Args:
        names: List of secret names
        required: Raise exception if any not found

    Returns:
        Dict mapping secret names to values
    """
    manager = _get_default_manager()
    return {name: manager.get(name, required=required) for name in names}


def is_gsm_available() -> bool:
    """Check if Google Secret Manager is available."""
    return _get_default_manager().is_gsm_available


# Trading-specific secret helpers
def get_trading_secrets() -> dict[str, str | None]:
    """
    Get all trading-related secrets.

    Returns dict with keys:
        - HYPERLIQUID_PK
        - HYPERLIQUID_WALLET_ADDRESS
        - DISCORD_WEBHOOK_URL
        - TELEGRAM_BOT_TOKEN
        - NEO4J_PASSWORD
        - GRAFANA_ADMIN_PASSWORD
    """
    trading_secrets = [
        "HYPERLIQUID_PK",
        "HYPERLIQUID_WALLET_ADDRESS",
        "DISCORD_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "NEO4J_PASSWORD",
        "GRAFANA_ADMIN_PASSWORD",
    ]
    return get_secrets(trading_secrets)


def validate_trading_secrets() -> tuple[bool, list[str]]:
    """
    Validate that all required trading secrets are set.

    Returns:
        Tuple of (all_valid, missing_secrets)
    """
    required = ["HYPERLIQUID_PK", "HYPERLIQUID_WALLET_ADDRESS"]
    manager = _get_default_manager()

    missing = []
    for name in required:
        if not manager.get(name):
            missing.append(name)

    return len(missing) == 0, missing


if __name__ == "__main__":
    import sys

    # Simple CLI for testing
    logging.basicConfig(level=logging.DEBUG)

    manager = SecretManager()

    if len(sys.argv) > 1:
        secret_name = sys.argv[1]
        value = manager.get(secret_name)
        if value:
            # Only show first/last 4 chars for security
            masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
            print(f"{secret_name}: {masked}")
        else:
            print(f"{secret_name}: NOT FOUND")
    else:
        print("Secret Manager Status:")
        print(f"  GSM Available: {manager.is_gsm_available}")
        print(f"  Project ID: {manager._project_id or 'Not set'}")

        if manager.is_gsm_available:
            secrets = manager.list_secrets()
            print(f"  Secrets in GSM: {len(secrets)}")
            for s in secrets[:10]:  # Show first 10
                print(f"    - {s}")
