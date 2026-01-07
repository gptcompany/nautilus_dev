# Unit tests for NautilusTrader Auto-Update Notifier

"""Test notifier module for auto_update."""

from unittest.mock import MagicMock, patch

from scripts.auto_update.notifier import (
    build_discord_embed,
    send_discord_notification,
    send_email_notification,
)

# =============================================================================
# T062: Test send_discord_notification
# =============================================================================


class TestSendDiscordNotification:
    """Test send_discord_notification function."""

    def test_discord_dry_run(self):
        """Test dry-run doesn't send notification."""
        result = send_discord_notification(
            message="Test update notification",
            webhook_url="https://discord.com/api/webhooks/test",
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True

    @patch("requests.post")
    def test_discord_send_success(self, mock_post: MagicMock):
        """Test successful Discord notification."""
        mock_post.return_value = MagicMock(status_code=204)

        result = send_discord_notification(
            message="Test update notification",
            webhook_url="https://discord.com/api/webhooks/test",
            dry_run=False,
        )

        assert result["success"] is True
        assert mock_post.called

    @patch("requests.post")
    def test_discord_send_with_embed(self, mock_post: MagicMock):
        """Test Discord notification with rich embed."""
        mock_post.return_value = MagicMock(status_code=204)

        result = send_discord_notification(
            message="Test update notification",
            webhook_url="https://discord.com/api/webhooks/test",
            embed=True,
            title="NautilusTrader Update",
            color=0x00FF00,
            dry_run=False,
        )

        assert result["success"] is True
        # Verify embed was included in payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "embeds" in payload

    @patch("requests.post")
    def test_discord_send_failure(self, mock_post: MagicMock):
        """Test Discord notification failure handling."""
        mock_post.return_value = MagicMock(status_code=400, text="Bad Request")

        result = send_discord_notification(
            message="Test",
            webhook_url="https://discord.com/api/webhooks/test",
            dry_run=False,
        )

        assert result["success"] is False
        assert "error" in result

    @patch("requests.post")
    def test_discord_network_error(self, mock_post: MagicMock):
        """Test Discord notification with network error."""
        import requests

        mock_post.side_effect = requests.RequestException("Network error")

        result = send_discord_notification(
            message="Test",
            webhook_url="https://discord.com/api/webhooks/test",
            dry_run=False,
        )

        assert result["success"] is False
        assert "error" in result

    def test_discord_missing_webhook(self):
        """Test Discord notification without webhook URL."""
        result = send_discord_notification(
            message="Test",
            webhook_url=None,
            dry_run=False,
        )

        assert result["success"] is False
        assert "webhook" in result.get("error", "").lower()


# =============================================================================
# T063: Test send_email_notification
# =============================================================================


class TestSendEmailNotification:
    """Test send_email_notification function."""

    def test_email_dry_run(self):
        """Test dry-run doesn't send email."""
        result = send_email_notification(
            subject="Test Update",
            body="Test notification body",
            to_email="test@example.com",
            dry_run=True,
        )

        assert result["success"] is True
        assert result["dry_run"] is True

    @patch("smtplib.SMTP")
    def test_email_send_success(self, mock_smtp: MagicMock):
        """Test successful email notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = send_email_notification(
            subject="Test Update",
            body="Test notification body",
            to_email="test@example.com",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            dry_run=False,
        )

        assert result["success"] is True

    @patch("smtplib.SMTP")
    def test_email_send_failure(self, mock_smtp: MagicMock):
        """Test email notification failure handling."""
        import smtplib

        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")

        result = send_email_notification(
            subject="Test",
            body="Test body",
            to_email="test@example.com",
            smtp_host="smtp.example.com",
            dry_run=False,
        )

        assert result["success"] is False
        assert "error" in result

    def test_email_missing_config(self):
        """Test email notification without SMTP config."""
        result = send_email_notification(
            subject="Test",
            body="Test body",
            to_email="test@example.com",
            smtp_host=None,
            dry_run=False,
        )

        assert result["success"] is False
        assert "smtp" in result.get("error", "").lower()


# =============================================================================
# Additional helper tests
# =============================================================================


class TestBuildDiscordEmbed:
    """Test build_discord_embed helper function."""

    def test_build_embed_basic(self):
        """Test building basic Discord embed."""
        embed = build_discord_embed(
            title="Update Available",
            description="NautilusTrader v1.222.0 is available",
        )

        assert embed["title"] == "Update Available"
        assert "1.222.0" in embed["description"]

    def test_build_embed_with_fields(self):
        """Test building embed with fields."""
        embed = build_discord_embed(
            title="Update Report",
            description="Summary of changes",
            fields=[
                {"name": "Version", "value": "1.222.0", "inline": True},
                {"name": "Status", "value": "Ready", "inline": True},
            ],
        )

        assert len(embed["fields"]) == 2
        assert embed["fields"][0]["name"] == "Version"

    def test_build_embed_with_color(self):
        """Test building embed with custom color."""
        embed = build_discord_embed(
            title="Test",
            description="Test",
            color=0xFF0000,  # Red
        )

        assert embed["color"] == 0xFF0000

    def test_build_embed_with_footer(self):
        """Test building embed with footer."""
        embed = build_discord_embed(
            title="Test",
            description="Test",
            footer="Auto-Update Pipeline",
        )

        assert embed["footer"]["text"] == "Auto-Update Pipeline"
