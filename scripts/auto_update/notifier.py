# NautilusTrader Auto-Update Pipeline - Notifier

"""Send notifications via Discord webhook and email."""

from __future__ import annotations

import smtplib
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def build_discord_embed(
    title: str,
    description: str,
    color: int = 0x5865F2,  # Discord blurple
    fields: list[dict[str, Any]] | None = None,
    footer: str | None = None,
    timestamp: bool = True,
) -> dict[str, Any]:
    """Build Discord embed object.

    Args:
        title: Embed title
        description: Embed description
        color: Embed color (hex integer)
        fields: List of field dicts with name, value, inline
        footer: Footer text
        timestamp: Include timestamp

    Returns:
        Discord embed dict
    """
    embed: dict[str, Any] = {
        "title": title,
        "description": description,
        "color": color,
    }

    if fields:
        embed["fields"] = fields

    if footer:
        embed["footer"] = {"text": footer}

    if timestamp:
        embed["timestamp"] = datetime.now(UTC).isoformat()

    return embed


def send_discord_notification(
    message: str,
    webhook_url: str | None,
    embed: bool = False,
    title: str | None = None,
    color: int = 0x5865F2,
    fields: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Send notification to Discord webhook.

    Args:
        message: Message content
        webhook_url: Discord webhook URL
        embed: Use rich embed format
        title: Embed title (if embed=True)
        color: Embed color
        fields: Embed fields
        dry_run: If True, don't send

    Returns:
        Dict with success status
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "channel": "discord",
            "message": message,
        }

    if not webhook_url:
        return {
            "success": False,
            "error": "Discord webhook URL not configured",
            "dry_run": False,
        }

    if not REQUESTS_AVAILABLE:
        return {
            "success": False,
            "error": "requests library not installed",
            "dry_run": False,
        }

    try:
        payload: dict[str, Any] = {}

        if embed:
            embed_obj = build_discord_embed(
                title=title or "NautilusTrader Auto-Update",
                description=message,
                color=color,
                fields=fields,
                footer="Auto-Update Pipeline",
            )
            payload["embeds"] = [embed_obj]
        else:
            payload["content"] = message

        response = requests.post(
            webhook_url,
            json=payload,
            timeout=30,
        )

        if response.status_code in (200, 204):
            return {
                "success": True,
                "dry_run": False,
                "channel": "discord",
                "status_code": response.status_code,
            }
        else:
            return {
                "success": False,
                "dry_run": False,
                "error": f"Discord returned {response.status_code}: {response.text}",
                "status_code": response.status_code,
            }

    except requests.RequestException as e:
        return {
            "success": False,
            "dry_run": False,
            "error": f"Network error: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
        }


def send_email_notification(
    subject: str,
    body: str,
    to_email: str,
    from_email: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int = 587,
    smtp_user: str | None = None,
    smtp_password: str | None = None,
    use_tls: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Send notification via email.

    Args:
        subject: Email subject
        body: Email body (plain text)
        to_email: Recipient email
        from_email: Sender email
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password
        use_tls: Use TLS encryption
        dry_run: If True, don't send

    Returns:
        Dict with success status
    """
    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "channel": "email",
            "to": to_email,
            "subject": subject,
        }

    if not smtp_host:
        return {
            "success": False,
            "error": "SMTP host not configured",
            "dry_run": False,
        }

    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_email or smtp_user or "noreply@localhost"
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()

            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)

            server.send_message(msg)

        return {
            "success": True,
            "dry_run": False,
            "channel": "email",
            "to": to_email,
        }

    except smtplib.SMTPException as e:
        return {
            "success": False,
            "dry_run": False,
            "error": f"SMTP error: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "dry_run": False,
            "error": str(e),
        }


def format_update_notification(
    version: str,
    previous_version: str,
    breaking_changes_count: int = 0,
    pr_url: str | None = None,
    status: str = "available",
) -> str:
    """Format update notification message.

    Args:
        version: New version
        previous_version: Current version
        breaking_changes_count: Number of breaking changes
        pr_url: Pull request URL
        status: Update status

    Returns:
        Formatted notification message
    """
    status_emoji = {
        "available": "📦",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
        "blocked": "🚫",
    }.get(status, "📦")

    lines = [
        f"{status_emoji} **NautilusTrader Update**",
        "",
        f"**Version**: {previous_version} → {version}",
        f"**Status**: {status.replace('_', ' ').title()}",
    ]

    if breaking_changes_count > 0:
        lines.append(f"**Breaking Changes**: {breaking_changes_count}")

    if pr_url:
        lines.append(f"**PR**: {pr_url}")

    return "\n".join(lines)


def send_notification(
    message: str,
    channel: str = "discord",
    webhook_url: str | None = None,
    email_config: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Send notification to specified channel.

    Args:
        message: Notification message
        channel: Channel type ('discord', 'email', 'all')
        webhook_url: Discord webhook URL
        email_config: Email configuration dict
        dry_run: If True, don't send

    Returns:
        Dict with results for each channel
    """
    results: dict[str, Any] = {"success": True}

    if channel in ("discord", "all"):
        discord_result = send_discord_notification(
            message=message,
            webhook_url=webhook_url,
            dry_run=dry_run,
        )
        results["discord"] = discord_result
        if not discord_result["success"]:
            results["success"] = False

    if channel in ("email", "all") and email_config:
        email_result = send_email_notification(
            subject=email_config.get("subject", "NautilusTrader Update"),
            body=message,
            to_email=email_config.get("to", ""),
            smtp_host=email_config.get("smtp_host"),
            smtp_port=email_config.get("smtp_port", 587),
            smtp_user=email_config.get("smtp_user"),
            smtp_password=email_config.get("smtp_password"),
            dry_run=dry_run,
        )
        results["email"] = email_result
        if not email_result["success"]:
            results["success"] = False

    return results
