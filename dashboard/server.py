"""
Trading Dashboard Server.

FastAPI server providing:
- WebSocket bridge for real-time OI, Funding, and Liquidation data
- REST API for historical data and status

Integrates with existing DaemonRunner from Spec 001 CCXT Pipeline.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models import (
    ConnectionStatus,
    ErrorMessage,
    ErrorResponse,
    FundingUpdate,
    HistoricalDataPoint,
    HistoricalResponse,
    LiquidationEvent,
    OIUpdate,
    PongMessage,
    StatusResponse,
    SymbolInfo,
    SymbolsResponse,
)

# =============================================================================
# Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dashboard.server")

# Parquet catalog path (from Spec 001)
CATALOG_PATH = Path("/media/sam/1TB/nautilus_dev/data/catalog/ccxt")

# Supported symbols
SUPPORTED_SYMBOLS = [
    SymbolInfo(
        symbol="BTCUSDT-PERP",
        name="Bitcoin Perpetual",
        exchanges=["BINANCE", "BYBIT", "HYPERLIQUID"],
    ),
    SymbolInfo(
        symbol="ETHUSDT-PERP",
        name="Ethereum Perpetual",
        exchanges=["BINANCE", "BYBIT", "HYPERLIQUID"],
    ),
]

# Server state
server_start_time = time.time()
fetch_count = 0
error_count = 0
liquidation_count = 0


# =============================================================================
# WebSocket Connection Manager
# =============================================================================


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        self.active_connections: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[websocket] = set()
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection."""
        async with self._lock:
            self.active_connections.pop(websocket, None)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, symbols: list[str]) -> list[str]:
        """Subscribe to symbols. Returns list of valid subscribed symbols."""
        valid_symbols = [
            s for s in symbols if s in {si.symbol for si in SUPPORTED_SYMBOLS}
        ]
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket].update(valid_symbols)
        return valid_symbols

    async def unsubscribe(self, websocket: WebSocket, symbols: list[str]) -> None:
        """Unsubscribe from symbols."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections[websocket] -= set(symbols)

    async def get_subscriptions(self, websocket: WebSocket) -> list[str]:
        """Get current subscriptions for a connection."""
        async with self._lock:
            return list(self.active_connections.get(websocket, set()))

    async def broadcast(
        self, message: dict[str, Any], symbol: str | None = None
    ) -> None:
        """Broadcast message to all connections (optionally filtered by symbol)."""
        async with self._lock:
            connections = list(self.active_connections.items())

        for ws, subscribed_symbols in connections:
            try:
                if symbol is None or symbol in subscribed_symbols:
                    await ws.send_json(message)
            except Exception:
                # Connection will be cleaned up on next message
                pass

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()


# =============================================================================
# DaemonRunner Integration (Callback Hooks)
# =============================================================================


async def on_oi_update(
    timestamp: datetime,
    symbol: str,
    venue: str,
    open_interest: float,
    open_interest_value: float,
) -> None:
    """Callback for OI updates from DaemonRunner."""
    global fetch_count
    fetch_count += 1

    msg = OIUpdate(
        timestamp=int(timestamp.timestamp() * 1000),
        symbol=symbol,
        venue=venue,
        open_interest=open_interest,
        open_interest_value=open_interest_value,
    )
    await manager.broadcast(msg.model_dump(), symbol=symbol)


async def on_funding_update(
    timestamp: datetime,
    symbol: str,
    venue: str,
    funding_rate: float,
    next_funding_time: datetime | None = None,
    predicted_rate: float | None = None,
) -> None:
    """Callback for Funding Rate updates from DaemonRunner."""
    global fetch_count
    fetch_count += 1

    msg = FundingUpdate(
        timestamp=int(timestamp.timestamp() * 1000),
        symbol=symbol,
        venue=venue,
        funding_rate=funding_rate,
        next_funding_time=int(next_funding_time.timestamp() * 1000)
        if next_funding_time
        else None,
        predicted_rate=predicted_rate,
    )
    await manager.broadcast(msg.model_dump(), symbol=symbol)


async def on_liquidation(
    timestamp: datetime,
    symbol: str,
    venue: str,
    side: str,
    quantity: float,
    price: float,
    value: float,
) -> None:
    """Callback for Liquidation events from DaemonRunner."""
    global liquidation_count
    liquidation_count += 1

    msg = LiquidationEvent(
        timestamp=int(timestamp.timestamp() * 1000),
        symbol=symbol,
        venue=venue,
        side=side,
        quantity=quantity,
        price=price,
        value=value,
    )
    await manager.broadcast(msg.model_dump(), symbol=symbol)


# =============================================================================
# Lifespan (Startup/Shutdown)
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Dashboard server starting...")
    logger.info(f"Catalog path: {CATALOG_PATH}")
    logger.info(f"Supported symbols: {[s.symbol for s in SUPPORTED_SYMBOLS]}")
    yield
    logger.info("Dashboard server shutting down...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Trading Dashboard API",
    description="Real-time OI, Funding, and Liquidation data",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# =============================================================================
# WebSocket Endpoint
# =============================================================================


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    await manager.connect(websocket)

    try:
        # Send initial status
        status = ConnectionStatus(
            connected=True,
            exchanges=["BINANCE", "BYBIT", "HYPERLIQUID"],
            subscribed_symbols=[],
        )
        await websocket.send_json(status.model_dump())

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # B67: Validate msg is a dict before accessing
                if not isinstance(msg, dict):
                    error = ErrorMessage(
                        code="INVALID_MESSAGE", message="Message must be a JSON object"
                    )
                    await websocket.send_json(error.model_dump())
                    continue
                action = msg.get("action")

                if action == "subscribe":
                    symbols = msg.get("symbols", [])
                    valid = await manager.subscribe(websocket, symbols)
                    # Send confirmation status
                    subs = await manager.get_subscriptions(websocket)
                    status = ConnectionStatus(
                        connected=True,
                        exchanges=["BINANCE", "BYBIT", "HYPERLIQUID"],
                        subscribed_symbols=subs,
                    )
                    await websocket.send_json(status.model_dump())
                    logger.info(f"Client subscribed to: {valid}")

                elif action == "unsubscribe":
                    symbols = msg.get("symbols", [])
                    await manager.unsubscribe(websocket, symbols)
                    subs = await manager.get_subscriptions(websocket)
                    status = ConnectionStatus(
                        connected=True,
                        exchanges=["BINANCE", "BYBIT", "HYPERLIQUID"],
                        subscribed_symbols=subs,
                    )
                    await websocket.send_json(status.model_dump())
                    logger.info(f"Client unsubscribed from: {symbols}")

                elif action == "ping":
                    pong = PongMessage(timestamp=int(time.time() * 1000))
                    await websocket.send_json(pong.model_dump())

                else:
                    error = ErrorMessage(
                        code="INVALID_ACTION", message=f"Unknown action: {action}"
                    )
                    await websocket.send_json(error.model_dump())

            except json.JSONDecodeError:
                error = ErrorMessage(
                    code="INVALID_JSON", message="Invalid JSON message"
                )
                await websocket.send_json(error.model_dump())

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


# =============================================================================
# REST API Endpoints
# =============================================================================


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Server health check and daemon status."""
    uptime = time.time() - server_start_time

    return StatusResponse(
        status="healthy",
        daemon_running=True,  # TODO: Check actual daemon status
        uptime_seconds=uptime,
        last_fetch=datetime.now().isoformat() if fetch_count > 0 else None,
        connected_exchanges=["BINANCE", "BYBIT", "HYPERLIQUID"],
        fetch_count=fetch_count,
        error_count=error_count,
        liquidation_count=liquidation_count,
    )


@app.get("/api/symbols", response_model=SymbolsResponse)
async def get_symbols():
    """List available trading symbols."""
    return SymbolsResponse(symbols=SUPPORTED_SYMBOLS)


@app.get("/api/history/oi")
async def get_history_oi(
    symbol: str = Query(..., description="Trading pair (e.g., BTCUSDT-PERP)"),
    from_date: str = Query(..., alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: str = Query(..., alias="to", description="End date (YYYY-MM-DD)"),
    venue: str | None = Query(None, description="Filter by exchange"),
    limit: int = Query(10000, ge=1, le=50000, description="Max records"),
):
    """Fetch historical Open Interest data."""
    con = None
    try:
        # B61: Validate date format
        try:
            from_dt = datetime.fromisoformat(from_date)
            to_dt = datetime.fromisoformat(to_date)
        except ValueError as e:
            return ErrorResponse(
                error="INVALID_DATE_FORMAT", message=f"Invalid date format: {e}"
            )

        if from_dt > to_dt:
            return ErrorResponse(
                error="INVALID_DATE_RANGE", message="from date must be before to date"
            )

        # B102: Validate symbol to prevent path traversal
        if not symbol.replace("-", "").replace("_", "").isalnum():
            return ErrorResponse(
                error="INVALID_SYMBOL", message="Symbol contains invalid characters"
            )

        # Query Parquet files
        oi_path = CATALOG_PATH / "open_interest"
        if not oi_path.exists():
            return ErrorResponse(
                error="CATALOG_NOT_FOUND", message="OI catalog not available"
            )

        # B71: Use try/finally to ensure connection is closed
        con = duckdb.connect()
        query = f"""
            SELECT
                epoch_ms(timestamp) as timestamp,
                venue,
                open_interest,
                open_interest_value
            FROM read_parquet('{oi_path}/**/*.parquet')
            WHERE symbol = ?
              AND timestamp >= ?
              AND timestamp <= ?
        """
        params = [symbol, from_dt, to_dt + timedelta(days=1)]

        if venue:
            query += " AND venue = ?"
            params.append(venue)

        # B106: Use parameterized limit
        query += " ORDER BY timestamp LIMIT ?"
        params.append(limit)

        result = con.execute(query, params).fetchall()

        data = [
            HistoricalDataPoint(
                timestamp=row[0],
                venue=row[1],
                open_interest=row[2],
                open_interest_value=row[3],
            )
            for row in result
        ]

        return HistoricalResponse(
            symbol=symbol,
            from_=from_date,
            to=to_date,
            count=len(data),
            data=data,
        )

    except FileNotFoundError:
        return ErrorResponse(error="NO_DATA", message=f"No OI data found for {symbol}")
    except Exception as e:
        logger.exception("Error fetching OI history")
        return ErrorResponse(error="INTERNAL_ERROR", message=str(e))
    finally:
        # B71: Ensure connection is always closed
        if con is not None:
            con.close()


@app.get("/api/history/funding")
async def get_history_funding(
    symbol: str = Query(..., description="Trading pair"),
    from_date: str = Query(..., alias="from", description="Start date"),
    to_date: str = Query(..., alias="to", description="End date"),
    venue: str | None = Query(None, description="Filter by exchange"),
    limit: int = Query(1000, ge=1, le=10000, description="Max records"),
):
    """Fetch historical funding rate data."""
    con = None
    try:
        # B61: Validate date format
        try:
            from_dt = datetime.fromisoformat(from_date)
            to_dt = datetime.fromisoformat(to_date)
        except ValueError as e:
            return ErrorResponse(
                error="INVALID_DATE_FORMAT", message=f"Invalid date format: {e}"
            )

        if from_dt > to_dt:
            return ErrorResponse(
                error="INVALID_DATE_RANGE", message="from date must be before to date"
            )

        # B102: Validate symbol
        if not symbol.replace("-", "").replace("_", "").isalnum():
            return ErrorResponse(
                error="INVALID_SYMBOL", message="Symbol contains invalid characters"
            )

        funding_path = CATALOG_PATH / "funding_rate"
        if not funding_path.exists():
            return ErrorResponse(
                error="CATALOG_NOT_FOUND", message="Funding catalog not available"
            )

        con = duckdb.connect()
        query = f"""
            SELECT
                epoch_ms(timestamp) as timestamp,
                venue,
                funding_rate,
                epoch_ms(next_funding_time) as next_funding_time
            FROM read_parquet('{funding_path}/**/*.parquet')
            WHERE symbol = ?
              AND timestamp >= ?
              AND timestamp <= ?
        """
        params = [symbol, from_dt, to_dt + timedelta(days=1)]

        if venue:
            query += " AND venue = ?"
            params.append(venue)

        # B106: Use parameterized limit
        query += " ORDER BY timestamp LIMIT ?"
        params.append(limit)

        result = con.execute(query, params).fetchall()

        data = [
            HistoricalDataPoint(
                timestamp=row[0],
                venue=row[1],
                funding_rate=row[2],
                next_funding_time=row[3],
            )
            for row in result
        ]

        return HistoricalResponse(
            symbol=symbol,
            from_=from_date,
            to=to_date,
            count=len(data),
            data=data,
        )

    except FileNotFoundError:
        return ErrorResponse(
            error="NO_DATA", message=f"No funding data found for {symbol}"
        )
    except Exception as e:
        logger.exception("Error fetching funding history")
        return ErrorResponse(error="INTERNAL_ERROR", message=str(e))
    finally:
        if con is not None:
            con.close()


@app.get("/api/history/liquidations")
async def get_history_liquidations(
    symbol: str = Query(..., description="Trading pair"),
    from_date: str = Query(..., alias="from", description="Start date"),
    to_date: str = Query(..., alias="to", description="End date"),
    venue: str | None = Query(None, description="Filter by exchange"),
    side: str | None = Query(None, description="Filter by side (LONG, SHORT)"),
    min_value: float | None = Query(None, description="Minimum USD value"),
    limit: int = Query(5000, ge=1, le=50000, description="Max records"),
):
    """Fetch historical liquidation events."""
    con = None
    try:
        # B61: Validate date format
        try:
            from_dt = datetime.fromisoformat(from_date)
            to_dt = datetime.fromisoformat(to_date)
        except ValueError as e:
            return ErrorResponse(
                error="INVALID_DATE_FORMAT", message=f"Invalid date format: {e}"
            )

        if from_dt > to_dt:
            return ErrorResponse(
                error="INVALID_DATE_RANGE", message="from date must be before to date"
            )

        # B102: Validate symbol
        if not symbol.replace("-", "").replace("_", "").isalnum():
            return ErrorResponse(
                error="INVALID_SYMBOL", message="Symbol contains invalid characters"
            )

        # Validate side parameter
        if side and side not in ("LONG", "SHORT"):
            return ErrorResponse(
                error="INVALID_SIDE", message="Side must be LONG or SHORT"
            )

        liq_path = CATALOG_PATH / "liquidation"
        if not liq_path.exists():
            return ErrorResponse(
                error="CATALOG_NOT_FOUND", message="Liquidation catalog not available"
            )

        con = duckdb.connect()
        query = f"""
            SELECT
                epoch_ms(timestamp) as timestamp,
                venue,
                side,
                quantity,
                price,
                value
            FROM read_parquet('{liq_path}/**/*.parquet')
            WHERE symbol = ?
              AND timestamp >= ?
              AND timestamp <= ?
        """
        params = [symbol, from_dt, to_dt + timedelta(days=1)]

        if venue:
            query += " AND venue = ?"
            params.append(venue)

        if side:
            query += " AND side = ?"
            params.append(side)

        if min_value:
            query += " AND value >= ?"
            params.append(min_value)

        # B106: Use parameterized limit
        query += " ORDER BY timestamp LIMIT ?"
        params.append(limit)

        result = con.execute(query, params).fetchall()

        data = [
            HistoricalDataPoint(
                timestamp=row[0],
                venue=row[1],
                side=row[2],
                quantity=row[3],
                price=row[4],
                value=row[5],
            )
            for row in result
        ]

        return HistoricalResponse(
            symbol=symbol,
            from_=from_date,
            to=to_date,
            count=len(data),
            data=data,
        )

    except FileNotFoundError:
        return ErrorResponse(
            error="NO_DATA", message=f"No liquidation data found for {symbol}"
        )
    except Exception as e:
        logger.exception("Error fetching liquidation history")
        return ErrorResponse(error="INTERNAL_ERROR", message=str(e))
    finally:
        if con is not None:
            con.close()


# =============================================================================
# Static Files (Dashboard)
# =============================================================================

# Serve static files
dashboard_path = Path(__file__).parent
if (dashboard_path / "styles").exists():
    app.mount(
        "/styles", StaticFiles(directory=dashboard_path / "styles"), name="styles"
    )
if (dashboard_path / "src").exists():
    app.mount("/src", StaticFiles(directory=dashboard_path / "src"), name="src")


@app.get("/")
async def serve_dashboard():
    """Serve the dashboard HTML."""
    index_path = dashboard_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Dashboard not found"}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8765,
        reload=True,
        log_level="info",
    )
