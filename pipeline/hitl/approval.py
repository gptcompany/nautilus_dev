"""
Human-in-the-Loop approval gates.

Provides ApprovalGate for requesting and waiting for human approval
when pipeline stages produce low-confidence results.
"""

import asyncio

# Python 3.10 compatibility
import datetime as _dt
import json
from dataclasses import dataclass, field
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from pathlib import Path
from typing import Any, Protocol

from pipeline.core.types import ProgressEvent, StageResult, StageType


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


@dataclass
class ApprovalRequest:
    """Request for human approval."""

    pipeline_id: str
    stage: StageType
    result: StageResult
    prompt: str
    options: list[str] = field(default_factory=lambda: ["approve", "reject", "modify"])
    timeout_seconds: int = 3600  # 1 hour default
    created_at: datetime = field(default_factory=_utc_now)


@dataclass
class ApprovalResponse:
    """Response from human reviewer."""

    approved: bool
    action: str
    modifications: dict[str, Any] | None = None
    reviewer: str = "human"
    feedback: str = ""
    timestamp: datetime = field(default_factory=_utc_now)


class NotificationService(Protocol):
    """Protocol for notification services (Discord, Slack, etc)."""

    async def send_approval_request(self, request: ApprovalRequest) -> None:
        """Send notification about pending approval."""
        ...

    async def send_progress_update(self, event: ProgressEvent) -> None:
        """Send pipeline progress update."""
        ...


class FileBasedApprovalWaiter:
    """
    Wait for approval via file system.

    Human creates approval file with JSON response.
    """

    def __init__(self, approval_dir: Path):
        self.approval_dir = approval_dir
        self.approval_dir.mkdir(parents=True, exist_ok=True)

    def get_approval_file_path(self, request: ApprovalRequest) -> Path:
        """Get path where approval file should be created."""
        return self.approval_dir / f"approval_{request.pipeline_id}_{request.stage.value}.json"

    async def wait_for_approval(
        self,
        request: ApprovalRequest,
        poll_interval: float = 5.0,
    ) -> ApprovalResponse:
        """
        Poll for approval file.

        Args:
            request: The approval request
            poll_interval: Seconds between file checks

        Returns:
            ApprovalResponse when file is found
        """
        approval_path = self.get_approval_file_path(request)
        elapsed = 0.0

        while elapsed < request.timeout_seconds:
            if approval_path.exists():
                with open(approval_path) as f:
                    data = json.load(f)

                # Clean up approval file
                approval_path.unlink()

                return ApprovalResponse(
                    approved=data.get("approved", False),
                    action=data.get("action", "reject"),
                    modifications=data.get("modifications"),
                    reviewer=data.get("reviewer", "human"),
                    feedback=data.get("feedback", ""),
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Timeout - auto-reject
        return ApprovalResponse(
            approved=False,
            action="timeout",
            feedback=f"Approval timed out after {request.timeout_seconds}s",
        )

    def write_request_info(self, request: ApprovalRequest) -> Path:
        """Write request info for human to review."""
        info_path = self.approval_dir / f"pending_{request.pipeline_id}_{request.stage.value}.json"

        with open(info_path, "w") as f:
            json.dump(
                {
                    "pipeline_id": request.pipeline_id,
                    "stage": request.stage.value,
                    "prompt": request.prompt,
                    "options": request.options,
                    "timeout_seconds": request.timeout_seconds,
                    "created_at": request.created_at.isoformat(),
                    "approval_file": str(self.get_approval_file_path(request)),
                    "confidence": request.result.confidence.name,
                    "review_reason": request.result.review_reason,
                },
                f,
                indent=2,
            )

        return info_path


class ApprovalGate:
    """
    Human-in-the-loop approval gate.

    Requests human approval when stage results have low confidence.
    """

    def __init__(
        self,
        notification_service: NotificationService | None = None,
        approval_dir: Path | None = None,
    ):
        self.notification_service = notification_service
        self.file_waiter = (
            FileBasedApprovalWaiter(approval_dir)
            if approval_dir
            else FileBasedApprovalWaiter(Path("/tmp/pipeline_approvals"))
        )
        self._pending: dict[str, ApprovalRequest] = {}

    def _build_prompt(self, result: StageResult) -> str:
        """Build human-readable prompt for approval."""
        lines = [
            f"Stage: {result.stage.value}",
            f"Status: {result.status.name}",
            f"Confidence: {result.confidence.name}",
        ]

        if result.review_reason:
            lines.append(f"Review Reason: {result.review_reason}")

        if result.metadata:
            lines.append(f"Metadata: {json.dumps(result.metadata, indent=2)}")

        lines.extend(
            [
                "",
                "Options: approve | reject | modify",
                "",
                'To approve, create a JSON file with: {"approved": true, "action": "approve"}',
            ]
        )

        return "\n".join(lines)

    async def request_approval(
        self,
        pipeline_id: str,
        result: StageResult,
    ) -> ApprovalResponse:
        """
        Request human approval for stage result.

        Args:
            pipeline_id: Pipeline identifier
            result: Stage result requiring approval

        Returns:
            ApprovalResponse from human reviewer
        """
        prompt = self._build_prompt(result)

        request = ApprovalRequest(
            pipeline_id=pipeline_id,
            stage=result.stage,
            result=result,
            prompt=prompt,
        )

        self._pending[pipeline_id] = request

        # Write info file for human
        self.file_waiter.write_request_info(request)

        # Notify if service available
        if self.notification_service:
            await self.notification_service.send_approval_request(request)

        # Wait for response
        response = await self.file_waiter.wait_for_approval(request)

        # Clean up pending
        del self._pending[pipeline_id]

        return response

    def get_pending_requests(self) -> dict[str, ApprovalRequest]:
        """Get all pending approval requests."""
        return self._pending.copy()
