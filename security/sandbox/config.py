"""Sandbox Configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NetworkMode(Enum):
    """Network isolation modes."""

    NONE = "none"
    INTERNAL = "internal"
    BRIDGE = "bridge"


class SandboxMode(Enum):
    """Sandbox operation modes."""

    MALWARE = "malware"
    SECURITY = "security"
    GENERAL = "general"


@dataclass
class SandboxConfig:
    """Base sandbox configuration."""

    timeout_seconds: int = 300
    memory_limit: str = "512m"
    cpu_limit: float = 2.0
    network_mode: NetworkMode = NetworkMode.NONE
    read_only: bool = True
    working_dir: str = "/workspace"


@dataclass
class MalwareSandboxConfig(SandboxConfig):
    """Malware analysis sandbox config."""

    timeout_seconds: int = 60
    memory_limit: str = "256m"
    cpu_limit: float = 1.0
    max_file_size_mb: int = 10
    enable_bandit: bool = True
    working_dir: str = "/analysis"


@dataclass
class SecuritySandboxConfig(SandboxConfig):
    """Security testing sandbox config."""

    timeout_seconds: int = 600
    memory_limit: str = "1g"
    network_mode: NetworkMode = NetworkMode.INTERNAL
    read_only: bool = False
    redis_host: str = "security-sandbox-redis"
    redis_port: int = 6379
    questdb_url: str = "http://security-sandbox-questdb:9000"


@dataclass
class DockerSandboxConfig(SandboxConfig):
    """General Docker sandbox config."""

    image: str = "python:3.12-slim"
    read_only: bool = False
    environment: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)


@dataclass
class Threat:
    """Detected threat."""

    type: str
    severity: str
    description: str
    location: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "location": self.location,
            "confidence": self.confidence,
        }


@dataclass
class AnalysisResult:
    """Malware analysis result."""

    is_clean: bool
    threats: list[Threat] = field(default_factory=list)
    scan_duration_ms: int = 0
    file_hash: str = ""
    file_size: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict."""
        return {
            "is_clean": self.is_clean,
            "threats": [t.to_dict() for t in self.threats],
            "scan_duration_ms": self.scan_duration_ms,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "details": self.details,
        }


@dataclass
class ExecutionResult:
    """Sandbox execution result."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_ms: int = 0

    @property
    def success(self) -> bool:
        """Check if successful."""
        return self.exit_code == 0 and not self.timed_out


@dataclass
class TestResult:
    """Single test result."""

    name: str
    passed: bool
    duration_ms: int = 0
    assertions_passed: int = 0
    assertions_failed: int = 0
    error_message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResults:
    """Aggregated test results."""

    scenario_name: str
    results: list[TestResult] = field(default_factory=list)
    total_duration_ms: int = 0

    @property
    def scenarios_passed(self) -> int:
        """Count passed."""
        return sum(1 for r in self.results if r.passed)

    @property
    def scenarios_failed(self) -> int:
        """Count failed."""
        return sum(1 for r in self.results if not r.passed)

    @property
    def all_passed(self) -> bool:
        """Check all passed."""
        return all(r.passed for r in self.results)
