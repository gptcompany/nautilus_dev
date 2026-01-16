"""
Notification services for HITL pipeline.

Supports Discord webhooks and console output.
"""

# Python 3.10 compatibility
import datetime as _dt
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from typing import Any

import httpx


def _utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(UTC)


@dataclass
class NotificationPayload:
    """Payload for notifications."""

    pipeline_id: str
    stage: str
    title: str
    message: str
    confidence: str
    needs_action: bool = False
    action_url: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = _utc_now()


class NotificationService(ABC):
    """Abstract notification service."""

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification. Returns True if successful."""
        ...

    @abstractmethod
    async def send_approval_request(self, request: Any) -> bool:
        """Send approval request notification."""
        ...

    @abstractmethod
    async def send_completion(self, pipeline_id: str, status: str, summary: dict[str, Any]) -> bool:
        """Send pipeline completion notification."""
        ...


class DiscordNotificationService(NotificationService):
    """Discord webhook notification service."""

    def __init__(self, webhook_url: str, username: str = "Pipeline Bot"):
        """
        Initialize Discord notification service.

        Args:
            webhook_url: Discord webhook URL
            username: Bot username to display
        """
        self.webhook_url = webhook_url
        self.username = username
        self._client = httpx.AsyncClient(timeout=30.0)

    async def send(self, payload: NotificationPayload) -> bool:
        """Send notification to Discord."""
        # Color based on needs_action
        color = 0xFF9900 if payload.needs_action else 0x00FF00  # Orange or Green

        embed = {
            "title": payload.title,
            "description": payload.message,
            "color": color,
            "fields": [
                {"name": "Pipeline", "value": payload.pipeline_id, "inline": True},
                {"name": "Stage", "value": payload.stage, "inline": True},
                {"name": "Confidence", "value": payload.confidence, "inline": True},
            ],
            "timestamp": payload.timestamp.isoformat() if payload.timestamp else None,
        }

        if payload.metadata:
            for key, value in list(payload.metadata.items())[:5]:
                embed["fields"].append({"name": key, "value": str(value)[:100], "inline": True})

        if payload.action_url:
            embed["url"] = payload.action_url

        discord_payload = {
            "username": self.username,
            "embeds": [embed],
        }

        try:
            response = await self._client.post(
                self.webhook_url,
                json=discord_payload,
            )
            return response.status_code in (200, 204)
        except Exception:
            return False

    async def send_approval_request(self, request: Any) -> bool:
        """Send approval request to Discord."""
        payload = NotificationPayload(
            pipeline_id=request.pipeline_id,
            stage=request.stage.value if hasattr(request.stage, "value") else str(request.stage),
            title="Approval Required",
            message=request.prompt if hasattr(request, "prompt") else "Human review required",
            confidence=request.result.confidence.name
            if hasattr(request.result, "confidence")
            else "UNKNOWN",
            needs_action=True,
            metadata={
                "review_reason": request.result.review_reason
                if hasattr(request.result, "review_reason")
                else None,
                "timeout": f"{request.timeout_seconds}s"
                if hasattr(request, "timeout_seconds")
                else None,
            },
        )
        return await self.send(payload)

    async def send_completion(self, pipeline_id: str, status: str, summary: dict[str, Any]) -> bool:
        """Send pipeline completion notification."""
        is_success = status in ("COMPLETED", "completed")

        payload = NotificationPayload(
            pipeline_id=pipeline_id,
            stage="COMPLETE",
            title=f"Pipeline {status}",
            message=f"Pipeline {pipeline_id} finished with status: {status}",
            confidence=summary.get("overall_confidence", "N/A"),
            needs_action=not is_success,
            metadata=summary,
        )
        return await self.send(payload)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


class ConsoleNotificationService(NotificationService):
    """Console/stdout notification service."""

    def __init__(self, prefix: str = "[PIPELINE]", verbose: bool = True):
        """
        Initialize console notification service.

        Args:
            prefix: Prefix for console output
            verbose: Include metadata in output
        """
        self.prefix = prefix
        self.verbose = verbose

    async def send(self, payload: NotificationPayload) -> bool:
        """Print notification to console."""
        icon = "!!" if payload.needs_action else "OK"
        timestamp = payload.timestamp.strftime("%H:%M:%S") if payload.timestamp else ""

        print(f"{self.prefix} [{icon}] {timestamp} {payload.title}")
        print(f"  Pipeline: {payload.pipeline_id} | Stage: {payload.stage}")
        print(f"  {payload.message}")
        print(f"  Confidence: {payload.confidence}")

        if self.verbose and payload.metadata:
            for key, value in payload.metadata.items():
                if value is not None:
                    print(f"  {key}: {value}")

        print()
        return True

    async def send_approval_request(self, request: Any) -> bool:
        """Print approval request to console."""
        print(f"\n{self.prefix} {'=' * 50}")
        print(f"{self.prefix} APPROVAL REQUIRED")
        print(f"{self.prefix} {'=' * 50}")
        print(f"{self.prefix} Pipeline: {request.pipeline_id}")
        print(
            f"{self.prefix} Stage: {request.stage.value if hasattr(request.stage, 'value') else request.stage}"
        )

        if hasattr(request, "prompt"):
            print(f"{self.prefix} {request.prompt}")

        if hasattr(request.result, "review_reason") and request.result.review_reason:
            print(f"{self.prefix} Reason: {request.result.review_reason}")

        print(
            f"{self.prefix} Options: {request.options if hasattr(request, 'options') else ['approve', 'reject']}"
        )
        print(f"{self.prefix} {'=' * 50}\n")
        return True

    async def send_completion(self, pipeline_id: str, status: str, summary: dict[str, Any]) -> bool:
        """Print pipeline completion to console."""
        icon = "DONE" if status in ("COMPLETED", "completed") else "FAIL"

        print(f"\n{self.prefix} {'=' * 50}")
        print(f"{self.prefix} [{icon}] Pipeline {status}")
        print(f"{self.prefix} {'=' * 50}")
        print(f"{self.prefix} ID: {pipeline_id}")

        for key, value in summary.items():
            print(f"{self.prefix} {key}: {value}")

        print(f"{self.prefix} {'=' * 50}\n")
        return True


class CompositeNotificationService(NotificationService):
    """Combines multiple notification services."""

    def __init__(self, services: list[NotificationService]):
        """
        Initialize composite service.

        Args:
            services: List of notification services to use
        """
        self.services = services

    async def send(self, payload: NotificationPayload) -> bool:
        """Send to all services."""
        results = []
        for service in self.services:
            try:
                result = await service.send(payload)
                results.append(result)
            except Exception:
                results.append(False)
        return any(results)

    async def send_approval_request(self, request: Any) -> bool:
        """Send approval request to all services."""
        results = []
        for service in self.services:
            try:
                result = await service.send_approval_request(request)
                results.append(result)
            except Exception:
                results.append(False)
        return any(results)

    async def send_completion(self, pipeline_id: str, status: str, summary: dict[str, Any]) -> bool:
        """Send completion to all services."""
        results = []
        for service in self.services:
            try:
                result = await service.send_completion(pipeline_id, status, summary)
                results.append(result)
            except Exception:
                results.append(False)
        return any(results)


def create_notification_service(
    discord_webhook_url: str | None = None,
    enable_console: bool = True,
    console_verbose: bool = True,
) -> NotificationService:
    """
    Factory to create appropriate notification service.

    Args:
        discord_webhook_url: Discord webhook URL (optional)
        enable_console: Enable console output
        console_verbose: Include metadata in console output

    Returns:
        NotificationService instance
    """
    services = []

    if enable_console:
        services.append(ConsoleNotificationService(verbose=console_verbose))

    if discord_webhook_url:
        services.append(DiscordNotificationService(webhook_url=discord_webhook_url))

    if len(services) == 0:
        # Default to console
        return ConsoleNotificationService()
    elif len(services) == 1:
        return services[0]
    else:
        return CompositeNotificationService(services)
