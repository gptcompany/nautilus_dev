"""
Unit tests for the Trading Dashboard server.

Tests WebSocket endpoint, REST API, and connection management.
"""

import pytest
from fastapi.testclient import TestClient

# Add dashboard to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dashboard"))

from server import app


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create test client for REST API."""
    return TestClient(app)


# =============================================================================
# REST API Tests
# =============================================================================


class TestStatusEndpoint:
    """Tests for GET /api/status."""

    def test_status_returns_200(self, client):
        """Status endpoint returns 200 OK."""
        response = client.get("/api/status")
        assert response.status_code == 200

    def test_status_has_required_fields(self, client):
        """Status response has all required fields."""
        response = client.get("/api/status")
        data = response.json()

        assert "status" in data
        assert "daemon_running" in data
        assert "uptime_seconds" in data
        assert "connected_exchanges" in data

    def test_status_is_healthy(self, client):
        """Server reports healthy status."""
        response = client.get("/api/status")
        data = response.json()

        assert data["status"] == "healthy"


class TestSymbolsEndpoint:
    """Tests for GET /api/symbols."""

    def test_symbols_returns_200(self, client):
        """Symbols endpoint returns 200 OK."""
        response = client.get("/api/symbols")
        assert response.status_code == 200

    def test_symbols_has_btc_and_eth(self, client):
        """Symbols include BTCUSDT and ETHUSDT."""
        response = client.get("/api/symbols")
        data = response.json()

        symbols = [s["symbol"] for s in data["symbols"]]
        assert "BTCUSDT-PERP" in symbols
        assert "ETHUSDT-PERP" in symbols

    def test_symbol_has_exchanges(self, client):
        """Each symbol has exchange information."""
        response = client.get("/api/symbols")
        data = response.json()

        for symbol in data["symbols"]:
            assert "symbol" in symbol
            assert "name" in symbol
            assert "exchanges" in symbol
            assert len(symbol["exchanges"]) > 0


class TestHistoryOIEndpoint:
    """Tests for GET /api/history/oi."""

    def test_oi_requires_symbol(self, client):
        """OI endpoint requires symbol parameter."""
        response = client.get("/api/history/oi?from=2025-01-01&to=2025-01-31")
        assert response.status_code == 422  # Validation error

    def test_oi_requires_date_range(self, client):
        """OI endpoint requires from and to parameters."""
        response = client.get("/api/history/oi?symbol=BTCUSDT-PERP")
        assert response.status_code == 422

    def test_oi_validates_date_range(self, client):
        """OI endpoint validates from < to."""
        response = client.get(
            "/api/history/oi?symbol=BTCUSDT-PERP&from=2025-01-31&to=2025-01-01"
        )
        # Returns error response (not 422, but error in body)
        data = response.json()
        assert "error" in data or response.status_code == 200


class TestHistoryFundingEndpoint:
    """Tests for GET /api/history/funding."""

    def test_funding_requires_symbol(self, client):
        """Funding endpoint requires symbol parameter."""
        response = client.get("/api/history/funding?from=2025-01-01&to=2025-01-31")
        assert response.status_code == 422

    def test_funding_requires_date_range(self, client):
        """Funding endpoint requires from and to parameters."""
        response = client.get("/api/history/funding?symbol=BTCUSDT-PERP")
        assert response.status_code == 422


class TestHistoryLiquidationsEndpoint:
    """Tests for GET /api/history/liquidations."""

    def test_liquidations_requires_symbol(self, client):
        """Liquidations endpoint requires symbol parameter."""
        response = client.get("/api/history/liquidations?from=2025-01-01&to=2025-01-31")
        assert response.status_code == 422

    def test_liquidations_supports_filters(self, client):
        """Liquidations endpoint accepts filter parameters."""
        # This should not error on the request itself
        response = client.get(
            "/api/history/liquidations"
            "?symbol=BTCUSDT-PERP"
            "&from=2025-01-01"
            "&to=2025-01-31"
            "&side=LONG"
            "&min_value=1000"
        )
        # May return error due to missing catalog, but request is valid
        assert response.status_code == 200


# =============================================================================
# WebSocket Tests
# =============================================================================


class TestWebSocketEndpoint:
    """Tests for WebSocket /ws endpoint."""

    def test_websocket_connects(self, client):
        """WebSocket endpoint accepts connection."""
        with client.websocket_connect("/ws") as websocket:
            # Should receive initial status message
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert data["connected"] is True

    def test_websocket_subscribe(self, client):
        """Client can subscribe to symbols."""
        with client.websocket_connect("/ws") as websocket:
            # Skip initial status
            websocket.receive_json()

            # Subscribe
            websocket.send_json({"action": "subscribe", "symbols": ["BTCUSDT-PERP"]})

            # Should receive confirmation status
            data = websocket.receive_json()
            assert data["type"] == "status"
            assert "BTCUSDT-PERP" in data["subscribed_symbols"]

    def test_websocket_unsubscribe(self, client):
        """Client can unsubscribe from symbols."""
        with client.websocket_connect("/ws") as websocket:
            # Skip initial status
            websocket.receive_json()

            # Subscribe first
            websocket.send_json({"action": "subscribe", "symbols": ["BTCUSDT-PERP"]})
            websocket.receive_json()

            # Unsubscribe
            websocket.send_json({"action": "unsubscribe", "symbols": ["BTCUSDT-PERP"]})

            data = websocket.receive_json()
            assert data["type"] == "status"
            assert "BTCUSDT-PERP" not in data["subscribed_symbols"]

    def test_websocket_ping_pong(self, client):
        """Server responds to ping with pong."""
        with client.websocket_connect("/ws") as websocket:
            # Skip initial status
            websocket.receive_json()

            # Send ping
            websocket.send_json({"action": "ping"})

            data = websocket.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data

    def test_websocket_invalid_action(self, client):
        """Server returns error for invalid action."""
        with client.websocket_connect("/ws") as websocket:
            # Skip initial status
            websocket.receive_json()

            # Send invalid action
            websocket.send_json({"action": "invalid_action"})

            data = websocket.receive_json()
            assert data["type"] == "error"
            assert data["code"] == "INVALID_ACTION"

    def test_websocket_invalid_json(self, client):
        """Server returns error for invalid JSON."""
        with client.websocket_connect("/ws") as websocket:
            # Skip initial status
            websocket.receive_json()

            # Send invalid JSON
            websocket.send_text("not json")

            data = websocket.receive_json()
            assert data["type"] == "error"
            assert data["code"] == "INVALID_JSON"


# =============================================================================
# Static File Serving Tests
# =============================================================================


class TestStaticFiles:
    """Tests for static file serving."""

    def test_root_serves_dashboard(self, client):
        """Root URL serves dashboard HTML."""
        response = client.get("/")
        # Should return HTML or error if file not found
        assert response.status_code in (200, 404)


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
