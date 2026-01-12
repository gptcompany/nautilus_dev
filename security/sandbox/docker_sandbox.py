"""General Docker Sandbox."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from security.sandbox.config import DockerSandboxConfig, ExecutionResult, NetworkMode

logger = logging.getLogger(__name__)


class DockerSandbox:
    """General purpose Docker sandbox."""

    def __init__(self, config: DockerSandboxConfig | None = None, **kwargs):
        """Initialize sandbox."""
        self.config = config or DockerSandboxConfig()
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def run(
        self,
        command: str | list[str],
        workdir: str | None = None,
        environment: dict[str, str] | None = None,
    ) -> ExecutionResult:
        """Run command in sandbox."""
        start_time = time.time()
        cmd = self._build_docker_command(command, workdir, environment)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except subprocess.TimeoutExpired as e:
            return ExecutionResult(
                exit_code=-1,
                stdout=e.stdout.decode() if e.stdout else "",
                stderr=e.stderr.decode() if e.stderr else "Timed out",
                timed_out=True,
                duration_ms=int((time.time() - start_time) * 1000),
            )

    def run_script(self, script_path: Path, args: list[str] | None = None) -> ExecutionResult:
        """Run script in sandbox."""
        if not script_path.exists():
            return ExecutionResult(
                exit_code=1, stdout="", stderr=f"Script not found: {script_path}"
            )

        start_time = time.time()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_copy = temp_path / script_path.name
            shutil.copy2(script_path, script_copy)

            interpreters = {".py": "python", ".sh": "bash", ".js": "node"}
            interpreter = interpreters.get(script_path.suffix.lower(), "python")
            command = [interpreter, f"/workspace/{script_path.name}"] + (args or [])
            cmd = self._build_docker_command(
                command,
                workdir="/workspace",
                extra_volumes=[f"{temp_path}:/workspace:ro"],
            )

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=self.config.timeout_seconds
                )
                return ExecutionResult(
                    exit_code=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    duration_ms=int((time.time() - start_time) * 1000),
                )
            except subprocess.TimeoutExpired as e:
                return ExecutionResult(
                    exit_code=-1,
                    stdout=e.stdout.decode() if e.stdout else "",
                    stderr="Timed out",
                    timed_out=True,
                    duration_ms=int((time.time() - start_time) * 1000),
                )

    def run_python(self, code: str) -> ExecutionResult:
        """Run Python code."""
        escaped_code = code.replace("'", "'\"'\"'")
        return self.run(["python", "-c", escaped_code])

    def _build_docker_command(
        self,
        command: str | list[str],
        workdir: str | None = None,
        environment: dict[str, str] | None = None,
        extra_volumes: list[str] | None = None,
    ) -> list[str]:
        """Build Docker run command."""
        cmd = ["docker", "run", "--rm"]

        if self.config.network_mode == NetworkMode.NONE:
            cmd.extend(["--network", "none"])
        elif self.config.network_mode == NetworkMode.INTERNAL:
            cmd.extend(["--network", "nautilus-sandbox-isolated"])

        if self.config.read_only:
            cmd.append("--read-only")
            cmd.extend(["--tmpfs", "/tmp:size=100M,mode=1777"])

        cmd.extend(["--security-opt", "no-new-privileges:true"])
        cmd.extend(["--memory", self.config.memory_limit])
        cmd.extend(["--cpus", str(self.config.cpu_limit)])

        if workdir:
            cmd.extend(["--workdir", workdir])

        all_env = {**self.config.environment, **(environment or {})}
        for key, value in all_env.items():
            cmd.extend(["-e", f"{key}={value}"])

        for volume in self.config.volumes + (extra_volumes or []):
            cmd.extend(["-v", volume])

        cmd.append(self.config.image)

        if isinstance(command, str):
            cmd.extend(["sh", "-c", command])
        else:
            cmd.extend(command)

        return cmd

    def is_docker_available(self) -> bool:
        """Check Docker availability."""
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
