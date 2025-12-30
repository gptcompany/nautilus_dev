/**
 * ReconnectingWebSocket - WebSocket client with automatic reconnection.
 *
 * Features:
 * - Exponential backoff reconnection
 * - Subscribe/unsubscribe message handling
 * - Ping/pong heartbeat mechanism
 * - Event-based API
 */

export class ReconnectingWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.options = {
            initialDelay: options.initialDelay || 1000,
            maxDelay: options.maxDelay || 30000,
            pingInterval: options.pingInterval || 30000,
            ...options
        };

        this.ws = null;
        this.currentDelay = this.options.initialDelay;
        this.reconnectTimer = null;
        this.pingTimer = null;
        this.subscribedSymbols = new Set();
        this.messageSequence = 0;
        this.lastReceivedSequence = -1;

        // Gap detection state
        this.expectedSequence = 0;
        this.gapDetected = false;
        this.gapRecoveryInProgress = false;

        // Event handlers
        this.onOpen = null;
        this.onClose = null;
        this.onMessage = null;
        this.onError = null;
        this.onStatusChange = null;

        // Data type handlers
        this.onOI = null;
        this.onFunding = null;
        this.onLiquidation = null;
        this.onStatus = null;

        // Gap detection handler
        this.onGapDetected = null;
    }

    /**
     * Connect to the WebSocket server.
     * B40: Validates URL and prevents infinite reconnect on invalid URLs.
     */
    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        // B40: Validate WebSocket URL before connecting
        if (!this.url || !this._isValidWebSocketUrl(this.url)) {
            console.error('[WS] Invalid WebSocket URL:', this.url);
            this._notifyStatusChange('disconnected');
            if (this.onError) {
                this.onError(new Error(`Invalid WebSocket URL: ${this.url}`));
            }
            return;  // Don't attempt to connect with invalid URL
        }

        this._notifyStatusChange('connecting');

        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = (event) => {
                console.log('[WS] Connected');
                this.currentDelay = this.options.initialDelay;
                this.connectionFailures = 0;  // B40: Reset failure count on success
                this._notifyStatusChange('connected');
                this._startPing();

                // B99: Reset gap detection state on reconnect
                this.resetGapDetection();

                // Resubscribe to symbols
                if (this.subscribedSymbols.size > 0) {
                    this.subscribe([...this.subscribedSymbols]);
                }

                if (this.onOpen) {
                    this.onOpen(event);
                }
            };

            this.ws.onclose = (event) => {
                console.log('[WS] Disconnected:', event.code, event.reason);
                this._stopPing();
                this._notifyStatusChange('disconnected');

                if (this.onClose) {
                    this.onClose(event);
                }

                // B7: Only reconnect if not intentional disconnect (code 1000)
                if (event.code !== 1000) {
                    this._scheduleReconnect();
                }
            };

            this.ws.onerror = (event) => {
                console.error('[WS] Error:', event);
                this.connectionFailures = (this.connectionFailures || 0) + 1;
                if (this.onError) {
                    this.onError(event);
                }
            };

            this.ws.onmessage = (event) => {
                this._handleMessage(event);
            };

        } catch (error) {
            console.error('[WS] Connection error:', error);
            this.connectionFailures = (this.connectionFailures || 0) + 1;

            // B40: Stop reconnecting after too many failures
            if (this.connectionFailures < 10) {
                this._scheduleReconnect();
            } else {
                console.error('[WS] Too many connection failures, stopping reconnect');
                this._notifyStatusChange('disconnected');
            }
        }
    }

    /**
     * Disconnect from the server.
     */
    disconnect() {
        this._stopPing();
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.close(1000, 'Client disconnect');
            this.ws = null;
        }
    }

    /**
     * Subscribe to symbols.
     * @param {string[]} symbols - Array of symbol names
     */
    subscribe(symbols) {
        symbols.forEach(s => this.subscribedSymbols.add(s));

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this._send({
                action: 'subscribe',
                symbols: symbols
            });
        }
    }

    /**
     * Unsubscribe from symbols.
     * @param {string[]} symbols - Array of symbol names
     */
    unsubscribe(symbols) {
        symbols.forEach(s => this.subscribedSymbols.delete(s));

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this._send({
                action: 'unsubscribe',
                symbols: symbols
            });
        }
    }

    /**
     * Get current subscribed symbols.
     * @returns {string[]}
     */
    getSubscriptions() {
        return [...this.subscribedSymbols];
    }

    /**
     * Check if connected.
     * @returns {boolean}
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }

    /**
     * Request backfill data to recover from a gap.
     * @param {string} symbol - Symbol to backfill
     * @param {number} fromSequence - Starting sequence number
     * @param {number} toSequence - Ending sequence number
     */
    requestBackfill(symbol, fromSequence, toSequence) {
        if (this.gapRecoveryInProgress) {
            return;
        }

        this.gapRecoveryInProgress = true;
        console.log(`[WS] Requesting backfill: ${symbol} seq ${fromSequence}-${toSequence}`);

        this._send({
            action: 'backfill',
            symbol: symbol,
            from_sequence: fromSequence,
            to_sequence: toSequence
        });
    }

    /**
     * Reset gap detection state.
     */
    resetGapDetection() {
        this.expectedSequence = 0;
        this.gapDetected = false;
        this.gapRecoveryInProgress = false;
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    _send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    _handleMessage(event) {
        try {
            const msg = JSON.parse(event.data);

            // Check for sequence gaps (T050)
            if (msg.sequence !== undefined) {
                this._checkSequenceGap(msg);
            }

            // Route to type-specific handlers
            switch (msg.type) {
                case 'oi':
                    if (this.onOI) this.onOI(msg);
                    break;
                case 'funding':
                    if (this.onFunding) this.onFunding(msg);
                    break;
                case 'liquidation':
                    if (this.onLiquidation) this.onLiquidation(msg);
                    break;
                case 'status':
                    if (this.onStatus) this.onStatus(msg);
                    break;
                case 'pong':
                    // Heartbeat response - no action needed
                    break;
                case 'backfill':
                    // Gap recovery complete
                    this.gapRecoveryInProgress = false;
                    this.gapDetected = false;
                    console.log('[WS] Backfill received, gap recovery complete');
                    break;
                case 'error':
                    console.error('[WS] Server error:', msg.code, msg.message);
                    // Notify error handler (T057)
                    if (this.onError) {
                        this.onError(new Error(`Server error [${msg.code}]: ${msg.message}`));
                    }
                    break;
                default:
                    console.warn('[WS] Unknown message type:', msg.type);
            }

            // Generic message handler
            if (this.onMessage) {
                this.onMessage(msg);
            }

        } catch (error) {
            console.error('[WS] Failed to parse message:', error);
        }
    }

    /**
     * Check for sequence gaps in messages (T050).
     * @param {Object} msg - Message with sequence number
     */
    _checkSequenceGap(msg) {
        const seq = msg.sequence;

        // First message - initialize expected sequence
        if (this.expectedSequence === 0) {
            this.expectedSequence = seq + 1;
            return;
        }

        // Check for gap
        if (seq > this.expectedSequence) {
            const gapSize = seq - this.expectedSequence;
            console.warn(`[WS] Gap detected: expected ${this.expectedSequence}, got ${seq} (gap size: ${gapSize})`);

            this.gapDetected = true;

            // Notify gap handler (T051 - gap recovery)
            if (this.onGapDetected && !this.gapRecoveryInProgress) {
                this.onGapDetected({
                    symbol: msg.symbol,
                    expectedSequence: this.expectedSequence,
                    actualSequence: seq,
                    gapSize: gapSize
                });
            }
        }

        // Update expected sequence
        this.expectedSequence = seq + 1;
    }

    _scheduleReconnect() {
        if (this.reconnectTimer) {
            return;
        }

        this._notifyStatusChange('reconnecting');
        console.log(`[WS] Reconnecting in ${this.currentDelay}ms...`);

        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, this.currentDelay);

        // Exponential backoff
        this.currentDelay = Math.min(this.currentDelay * 2, this.options.maxDelay);
    }

    _startPing() {
        this._stopPing();
        this.pingTimer = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this._send({ action: 'ping' });
            }
        }, this.options.pingInterval);
    }

    _stopPing() {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
    }

    _notifyStatusChange(status) {
        if (this.onStatusChange) {
            this.onStatusChange(status);
        }
    }

    /**
     * B40: Validate WebSocket URL format.
     * @param {string} url - URL to validate
     * @returns {boolean}
     */
    _isValidWebSocketUrl(url) {
        try {
            const parsed = new URL(url);
            return parsed.protocol === 'ws:' || parsed.protocol === 'wss:';
        } catch {
            return false;
        }
    }
}

/**
 * Create a configured WebSocket client for the dashboard.
 * @param {string} serverUrl - WebSocket server URL (default: auto-detect)
 * @returns {ReconnectingWebSocket}
 */
export function createDashboardWebSocket(serverUrl = null) {
    if (!serverUrl) {
        // Auto-detect based on current page location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || 'localhost:8765';
        serverUrl = `${protocol}//${host}/ws`;
    }

    return new ReconnectingWebSocket(serverUrl);
}

export default ReconnectingWebSocket;
