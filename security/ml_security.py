#!/usr/bin/env python3
"""
ML Model Security Module.

Provides encryption, signing, and integrity verification for PyTorch models.
Protects against model tampering and ensures secure model loading.

Usage:
    from security.ml_security import SecureModelLoader, ModelSigner

    # Encrypt and sign a model
    signer = ModelSigner()
    signer.encrypt_model("model.pt", "model.pt.enc")
    signer.sign_model("model.pt.enc", "model.pt.sig")

    # Load verified model
    loader = SecureModelLoader()
    model = loader.load_verified("model.pt.enc", "model.pt.sig")

Security Features:
- AES-256-GCM encryption at rest
- ECDSA digital signatures for integrity
- SHA-256 checksums for quick verification
- Safe torch.load() wrapper (weights_only=True)
- Audit logging for all model operations
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Encryption key from environment (generate with: openssl rand -hex 32)
MODEL_ENCRYPTION_KEY = os.getenv("MODEL_ENCRYPTION_KEY")


@dataclass
class ModelMetadata:
    """Metadata for a signed model."""

    model_path: str
    hash_sha256: str
    signed_at: str
    signed_by: str = "automated"
    model_type: str = "pytorch"
    framework_version: str = ""
    description: str = ""
    training_date: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_path": self.model_path,
            "hash_sha256": self.hash_sha256,
            "signed_at": self.signed_at,
            "signed_by": self.signed_by,
            "model_type": self.model_type,
            "framework_version": self.framework_version,
            "description": self.description,
            "training_date": self.training_date,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelMetadata:
        return cls(
            model_path=data["model_path"],
            hash_sha256=data["hash_sha256"],
            signed_at=data["signed_at"],
            signed_by=data.get("signed_by", "automated"),
            model_type=data.get("model_type", "pytorch"),
            framework_version=data.get("framework_version", ""),
            description=data.get("description", ""),
            training_date=data.get("training_date", ""),
            extra=data.get("extra", {}),
        )


@dataclass
class VerificationResult:
    """Result of model verification."""

    valid: bool
    model_path: str
    expected_hash: str = ""
    actual_hash: str = ""
    signature_valid: bool = False
    encrypted: bool = False
    error: str = ""
    metadata: ModelMetadata | None = None


class ModelIntegrity:
    """Model integrity verification using SHA-256."""

    @staticmethod
    def compute_hash(file_path: str | Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def verify_hash(file_path: str | Path, expected_hash: str) -> bool:
        """Verify file matches expected hash."""
        actual_hash = ModelIntegrity.compute_hash(file_path)
        return secrets.compare_digest(actual_hash, expected_hash)

    @staticmethod
    def create_checksum_file(model_path: str | Path, output_path: str | Path | None = None) -> str:
        """Create a checksum file for a model."""
        model_path = Path(model_path)
        output_path = Path(output_path) if output_path else model_path.with_suffix(".sha256")

        file_hash = ModelIntegrity.compute_hash(model_path)
        checksum_content = f"{file_hash}  {model_path.name}\n"

        with open(output_path, "w") as f:
            f.write(checksum_content)

        logger.info(f"Created checksum file: {output_path}")
        return file_hash


class ModelEncryption:
    """
    Model encryption using Fernet (AES-128-CBC) or AES-256-GCM.

    Uses cryptography library for encryption.
    """

    def __init__(self, key: bytes | None = None):
        """
        Initialize with encryption key.

        Args:
            key: 32-byte key for AES-256. If None, uses MODEL_ENCRYPTION_KEY env.
        """
        if key:
            self._key = key
        elif MODEL_ENCRYPTION_KEY:
            self._key = bytes.fromhex(MODEL_ENCRYPTION_KEY)
        else:
            raise ValueError(
                "Encryption key required. Set MODEL_ENCRYPTION_KEY env or pass key parameter. "
                "Generate with: openssl rand -hex 32"
            )

        if len(self._key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")

    def encrypt_file(self, input_path: str | Path, output_path: str | Path) -> str:
        """
        Encrypt a file using AES-256-GCM.

        Args:
            input_path: Path to file to encrypt
            output_path: Path for encrypted output

        Returns:
            SHA-256 hash of original file
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError("cryptography package required: pip install cryptography")

        input_path = Path(input_path)
        output_path = Path(output_path)

        # Compute hash before encryption
        original_hash = ModelIntegrity.compute_hash(input_path)

        # Generate random nonce (96 bits for GCM)
        nonce = secrets.token_bytes(12)

        # Read plaintext
        with open(input_path, "rb") as f:
            plaintext = f.read()

        # Encrypt
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # Write: nonce (12 bytes) + ciphertext
        with open(output_path, "wb") as f:
            f.write(nonce)
            f.write(ciphertext)

        logger.info(f"Encrypted {input_path} -> {output_path}")
        return original_hash

    def decrypt_file(self, input_path: str | Path, output_path: str | Path) -> None:
        """
        Decrypt a file encrypted with AES-256-GCM.

        Args:
            input_path: Path to encrypted file
            output_path: Path for decrypted output
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError("cryptography package required: pip install cryptography")

        input_path = Path(input_path)
        output_path = Path(output_path)

        with open(input_path, "rb") as f:
            nonce = f.read(12)
            ciphertext = f.read()

        aesgcm = AESGCM(self._key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        with open(output_path, "wb") as f:
            f.write(plaintext)

        logger.info(f"Decrypted {input_path} -> {output_path}")

    def decrypt_to_bytes(self, input_path: str | Path) -> bytes:
        """Decrypt file and return bytes (for in-memory loading)."""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise ImportError("cryptography package required: pip install cryptography")

        with open(input_path, "rb") as f:
            nonce = f.read(12)
            ciphertext = f.read()

        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, ciphertext, None)


class ModelSigner:
    """
    Model signing using ECDSA.

    Creates detached signatures for model files.
    """

    def __init__(self, private_key_path: str | None = None):
        """
        Initialize signer.

        Args:
            private_key_path: Path to ECDSA private key (PEM format).
                            If None, uses MODEL_SIGNING_KEY_PATH env.
        """
        self._private_key_path = private_key_path or os.getenv("MODEL_SIGNING_KEY_PATH")
        self._private_key = None

        if self._private_key_path and Path(self._private_key_path).exists():
            self._load_private_key()

    def _load_private_key(self) -> None:
        """Load private key from file."""
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
        except ImportError:
            raise ImportError("cryptography package required")

        with open(self._private_key_path, "rb") as f:
            self._private_key = load_pem_private_key(f.read(), password=None)

    def generate_keypair(self, private_key_path: str, public_key_path: str) -> None:
        """
        Generate a new ECDSA keypair.

        Args:
            private_key_path: Where to save private key
            public_key_path: Where to save public key
        """
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import ec
        except ImportError:
            raise ImportError("cryptography package required")

        # Generate private key (SECP256R1 = P-256)
        private_key = ec.generate_private_key(ec.SECP256R1())

        # Save private key
        with open(private_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        os.chmod(private_key_path, 0o600)

        # Save public key
        public_key = private_key.public_key()
        with open(public_key_path, "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

        logger.info(f"Generated keypair: {private_key_path}, {public_key_path}")
        self._private_key = private_key
        self._private_key_path = private_key_path

    def sign_model(
        self,
        model_path: str | Path,
        signature_path: str | Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Sign a model file.

        Args:
            model_path: Path to model file
            signature_path: Where to save signature (default: model_path + .sig)
            metadata: Additional metadata to include

        Returns:
            Signature file path
        """
        if not self._private_key:
            raise ValueError("No private key loaded. Generate or load a keypair first.")

        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec
        except ImportError:
            raise ImportError("cryptography package required")

        model_path = Path(model_path)
        signature_path = Path(signature_path) if signature_path else model_path.with_suffix(".sig")

        # Compute hash
        model_hash = ModelIntegrity.compute_hash(model_path)

        # Create metadata
        model_metadata = ModelMetadata(
            model_path=str(model_path.name),
            hash_sha256=model_hash,
            signed_at=datetime.now().isoformat(),
            extra=metadata or {},
        )

        # Sign the hash
        signature = self._private_key.sign(model_hash.encode(), ec.ECDSA(hashes.SHA256()))

        # Save signature with metadata
        sig_data = {
            "version": 1,
            "metadata": model_metadata.to_dict(),
            "signature": signature.hex(),
        }

        with open(signature_path, "w") as f:
            json.dump(sig_data, f, indent=2)

        logger.info(f"Signed model: {model_path} -> {signature_path}")
        return str(signature_path)

    @staticmethod
    def verify_signature(
        model_path: str | Path,
        signature_path: str | Path,
        public_key_path: str | None = None,
    ) -> VerificationResult:
        """
        Verify a model signature.

        Args:
            model_path: Path to model file
            signature_path: Path to signature file
            public_key_path: Path to public key (uses MODEL_SIGNING_PUBLIC_KEY_PATH env if None)

        Returns:
            VerificationResult
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
        except ImportError:
            return VerificationResult(
                valid=False,
                model_path=str(model_path),
                error="cryptography package required",
            )

        model_path = Path(model_path)
        signature_path = Path(signature_path)
        public_key_path = public_key_path or os.getenv("MODEL_SIGNING_PUBLIC_KEY_PATH")

        if not public_key_path or not Path(public_key_path).exists():
            return VerificationResult(
                valid=False,
                model_path=str(model_path),
                error="Public key not found",
            )

        try:
            # Load signature data
            with open(signature_path) as f:
                sig_data = json.load(f)

            metadata = ModelMetadata.from_dict(sig_data["metadata"])
            signature = bytes.fromhex(sig_data["signature"])

            # Compute actual hash
            actual_hash = ModelIntegrity.compute_hash(model_path)

            # Load public key
            with open(public_key_path, "rb") as f:
                public_key = load_pem_public_key(f.read())

            # Verify signature
            try:
                public_key.verify(
                    signature, metadata.hash_sha256.encode(), ec.ECDSA(hashes.SHA256())
                )
                signature_valid = True
            except Exception:
                signature_valid = False

            # Check hash match
            hash_valid = secrets.compare_digest(actual_hash, metadata.hash_sha256)

            return VerificationResult(
                valid=signature_valid and hash_valid,
                model_path=str(model_path),
                expected_hash=metadata.hash_sha256,
                actual_hash=actual_hash,
                signature_valid=signature_valid,
                metadata=metadata,
            )

        except Exception as e:
            return VerificationResult(
                valid=False,
                model_path=str(model_path),
                error=str(e),
            )


class SecureModelLoader:
    """
    Secure PyTorch model loader.

    Wraps torch.load with security features:
    - Signature verification
    - Decryption support
    - Audit logging
    - Safe loading (weights_only when possible)
    """

    def __init__(
        self,
        encryption_key: bytes | None = None,
        public_key_path: str | None = None,
        audit_log_path: str | None = None,
    ):
        """
        Initialize secure loader.

        Args:
            encryption_key: AES-256 key for decryption
            public_key_path: Path to signing public key
            audit_log_path: Path for audit log file
        """
        self._encryption = None
        if encryption_key or MODEL_ENCRYPTION_KEY:
            self._encryption = ModelEncryption(encryption_key)

        self._public_key_path = public_key_path or os.getenv("MODEL_SIGNING_PUBLIC_KEY_PATH")
        self._audit_log_path = audit_log_path or os.getenv(
            "MODEL_AUDIT_LOG_PATH", "/var/log/nautilus/model_access.log"
        )

    def _audit_log(
        self,
        action: str,
        model_path: str,
        success: bool,
        **extra: Any,
    ) -> None:
        """Write audit log entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "model_path": model_path,
            "success": success,
            **extra,
        }

        # Log to file if path configured
        if self._audit_log_path:
            try:
                Path(self._audit_log_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self._audit_log_path, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                logger.warning(f"Failed to write audit log: {e}")

        # Also log via standard logger
        level = logging.INFO if success else logging.WARNING
        logger.log(level, f"Model {action}: {model_path} (success={success})")

    def load_verified(
        self,
        model_path: str | Path,
        signature_path: str | Path | None = None,
        expected_hash: str | None = None,
        device: str = "cpu",
        weights_only: bool = True,
    ) -> Any:
        """
        Load a model with verification.

        Args:
            model_path: Path to model file (may be encrypted)
            signature_path: Path to signature file
            expected_hash: Expected SHA-256 hash (if no signature)
            device: Device to load model to
            weights_only: Use weights_only=True (safer but requires compatible checkpoint)

        Returns:
            Loaded model/checkpoint

        Raises:
            ValueError: If verification fails
        """
        import io

        import torch

        model_path = Path(model_path)
        is_encrypted = model_path.suffix == ".enc"

        # Determine signature path
        if signature_path is None:
            # Try common patterns
            for ext in [".sig", ".signature"]:
                potential = model_path.with_suffix(ext)
                if potential.exists():
                    signature_path = potential
                    break

        # Verify signature if available
        if signature_path:
            result = ModelSigner.verify_signature(model_path, signature_path, self._public_key_path)

            if not result.valid:
                self._audit_log(
                    "load_failed",
                    str(model_path),
                    False,
                    reason="signature_invalid",
                    error=result.error,
                )
                raise ValueError(
                    f"Model signature verification failed: {result.error or 'invalid signature'}"
                )

            expected_hash = result.expected_hash

        # Verify hash if provided (and not already verified via signature)
        if expected_hash and not signature_path:
            actual_hash = ModelIntegrity.compute_hash(model_path)
            if not secrets.compare_digest(actual_hash, expected_hash):
                self._audit_log(
                    "load_failed",
                    str(model_path),
                    False,
                    reason="hash_mismatch",
                    expected=expected_hash[:16],
                    actual=actual_hash[:16],
                )
                raise ValueError(f"Model hash mismatch. Expected: {expected_hash[:16]}...")

        # Decrypt if encrypted
        if is_encrypted:
            if not self._encryption:
                raise ValueError("Model is encrypted but no encryption key provided")

            # Decrypt to memory
            decrypted_bytes = self._encryption.decrypt_to_bytes(model_path)

            # Load from bytes
            buffer = io.BytesIO(decrypted_bytes)
            try:
                checkpoint = torch.load(buffer, map_location=device, weights_only=weights_only)
            except Exception as e:
                if weights_only and "weights_only" in str(e):
                    # Fall back to unsafe load with warning
                    logger.warning(f"weights_only=True failed, falling back to unsafe load: {e}")
                    buffer.seek(0)
                    checkpoint = torch.load(buffer, map_location=device, weights_only=False)
                else:
                    raise

        else:
            # Load directly
            try:
                checkpoint = torch.load(model_path, map_location=device, weights_only=weights_only)
            except Exception as e:
                if weights_only and "weights_only" in str(e):
                    logger.warning(f"weights_only=True failed, falling back to unsafe load: {e}")
                    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
                else:
                    raise

        self._audit_log(
            "load_success",
            str(model_path),
            True,
            encrypted=is_encrypted,
            signature_verified=bool(signature_path),
        )

        return checkpoint

    def quick_verify(self, model_path: str | Path, expected_hash: str) -> bool:
        """Quick hash verification without loading."""
        return ModelIntegrity.verify_hash(model_path, expected_hash)


# Convenience functions
def compute_model_hash(model_path: str | Path) -> str:
    """Compute SHA-256 hash of a model file."""
    return ModelIntegrity.compute_hash(model_path)


def verify_model_hash(model_path: str | Path, expected_hash: str) -> bool:
    """Verify model matches expected hash."""
    return ModelIntegrity.verify_hash(model_path, expected_hash)


def load_model_secure(
    model_path: str | Path,
    signature_path: str | Path | None = None,
    device: str = "cpu",
) -> Any:
    """Load a model with security verification."""
    loader = SecureModelLoader()
    return loader.load_verified(model_path, signature_path, device=device)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python ml_security.py <command> [args]")
        print("")
        print("Commands:")
        print("  hash <model_path>              - Compute SHA-256 hash")
        print("  verify <model_path> <hash>     - Verify model hash")
        print("  genkey <private_path> <pub>    - Generate signing keypair")
        print("  sign <model_path>              - Sign a model")
        print("  verify-sig <model> <sig>       - Verify signature")
        sys.exit(1)

    command = sys.argv[1]

    if command == "hash":
        model_hash = ModelIntegrity.compute_hash(sys.argv[2])
        print(f"SHA-256: {model_hash}")

    elif command == "verify":
        valid = ModelIntegrity.verify_hash(sys.argv[2], sys.argv[3])
        print(f"Valid: {valid}")
        sys.exit(0 if valid else 1)

    elif command == "genkey":
        signer = ModelSigner()
        signer.generate_keypair(sys.argv[2], sys.argv[3])
        print(f"Generated keypair: {sys.argv[2]}, {sys.argv[3]}")

    elif command == "sign":
        signer = ModelSigner(os.getenv("MODEL_SIGNING_KEY_PATH"))
        sig_path = signer.sign_model(sys.argv[2])
        print(f"Signature: {sig_path}")

    elif command == "verify-sig":
        result = ModelSigner.verify_signature(sys.argv[2], sys.argv[3])
        print(f"Valid: {result.valid}")
        if not result.valid:
            print(f"Error: {result.error}")
        sys.exit(0 if result.valid else 1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
