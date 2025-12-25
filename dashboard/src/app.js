/**
 * Trading Dashboard - Main Application Entry Point
 *
 * Initializes charts, WebSocket connection, and UI components.
 */

import { createDashboardWebSocket } from './data/ws-client.js';
import { DataBuffer, MarkerBuffer } from './data/buffer.js';
import { createChart, createLineSeries, THEME, saveChartState, restoreChartState } from './charts/base-chart.js';
import { formatOI, formatFundingRate, formatCountdown, formatDateTime, getFundingColorClass } from './utils/format.js';
import { APIClient } from './data/api-client.js';
import { DateRangeSelector } from './ui/date-range.js';

// =============================================================================
// Application State
// =============================================================================

const state = {
    currentSymbol: 'BTCUSDT-PERP',
    connectionStatus: 'disconnected',
    chartState: null,  // Preserved zoom/pan state

    // Data buffers
    oiBuffer: new DataBuffer(50000),
    fundingBuffer: new DataBuffer(10000),
    liquidationBuffer: new MarkerBuffer(10000),

    // Chart instances
    oiChart: null,
    oiSeries: null,
    oiHistoricalSeries: null,  // Historical data (faded)
    fundingChart: null,
    fundingSeries: null,
    fundingHistoricalSeries: null,  // Historical data (faded)

    // WebSocket client
    ws: null,

    // API client for historical data
    apiClient: null,

    // Date range selector
    dateRangeSelector: null,

    // Historical data loading state
    isLoadingHistorical: false,

    // Tab visibility state (T059)
    tabActive: true,
    inactiveTimer: null,

    // B41: Track initialization to prevent duplicate listeners
    initialized: false,

    // B47/B51: Track symbol switch in progress
    symbolSwitchPending: false,
    symbolSwitchTimeout: null,

    // UI elements
    elements: {},
};

// =============================================================================
// Initialization
// =============================================================================

/**
 * Initialize the dashboard application.
 */
export function init() {
    // B41: Prevent duplicate initialization
    if (state.initialized) {
        console.warn('[Dashboard] Already initialized, skipping');
        return;
    }

    console.log('[Dashboard] Initializing...');

    // Cache DOM elements
    cacheElements();

    // Initialize charts
    initCharts();

    // Initialize API client for historical data
    initAPIClient();

    // Initialize date range selector
    initDateRangeSelector();

    // Initialize WebSocket
    initWebSocket();

    // Setup event listeners
    setupEventListeners();

    // Handle visibility change (pause updates when tab inactive)
    document.addEventListener('visibilitychange', handleVisibilityChange);

    state.initialized = true;
    console.log('[Dashboard] Initialization complete');
}

/**
 * B74: Cleanup function for proper resource disposal.
 */
export function destroy() {
    console.log('[Dashboard] Destroying...');

    // Clear timers
    if (state.inactiveTimer) {
        clearTimeout(state.inactiveTimer);
        state.inactiveTimer = null;
    }
    if (state.symbolSwitchTimeout) {
        clearTimeout(state.symbolSwitchTimeout);
        state.symbolSwitchTimeout = null;
    }

    // Disconnect WebSocket
    if (state.ws) {
        state.ws.disconnect();
        state.ws = null;
    }

    // Remove charts - B28: Disconnect ResizeObserver to prevent memory leak
    if (state.oiChart) {
        if (state.oiChart._resizeObserver) {
            state.oiChart._resizeObserver.disconnect();
        }
        state.oiChart.remove();
        state.oiChart = null;
        state.oiSeries = null;
        state.oiHistoricalSeries = null;
    }
    if (state.fundingChart) {
        if (state.fundingChart._resizeObserver) {
            state.fundingChart._resizeObserver.disconnect();
        }
        state.fundingChart.remove();
        state.fundingChart = null;
        state.fundingSeries = null;
        state.fundingHistoricalSeries = null;
    }

    // Clear buffers
    state.oiBuffer.clear();
    state.fundingBuffer.clear();
    state.liquidationBuffer.clear();

    // Remove event listeners
    document.removeEventListener('visibilitychange', handleVisibilityChange);

    state.initialized = false;
    console.log('[Dashboard] Destroyed');
}

/**
 * Cache frequently used DOM elements.
 */
function cacheElements() {
    state.elements = {
        connectionStatus: document.getElementById('connection-status'),
        statusText: document.querySelector('#connection-status .status-text'),
        symbolSelector: document.getElementById('symbol-selector'),
        fundingValue: document.getElementById('funding-value'),
        fundingNext: document.getElementById('funding-next'),
        oiChartContainer: document.getElementById('oi-chart'),
        fundingChartContainer: document.getElementById('funding-chart'),
        lastUpdate: document.getElementById('last-update'),
        // Historical data controls
        dateFrom: document.getElementById('date-from'),
        dateTo: document.getElementById('date-to'),
        loadHistoricalBtn: document.getElementById('load-historical'),
        historicalProgress: document.getElementById('historical-progress'),
    };
}

// =============================================================================
// Chart Initialization
// =============================================================================

/**
 * Initialize TradingView Lightweight Charts.
 */
function initCharts() {
    // OI Chart
    if (state.elements.oiChartContainer) {
        state.oiChart = createChart(state.elements.oiChartContainer);

        // Historical series (faded, rendered first/behind)
        state.oiHistoricalSeries = createLineSeries(state.oiChart, {
            color: 'rgba(38, 166, 154, 0.3)',  // Faded teal
            lineWidth: 1,
            title: 'OI (Historical)',
            priceFormat: {
                type: 'custom',
                formatter: (price) => formatOI(price),
            },
        });

        // Live series (bright, rendered on top)
        state.oiSeries = createLineSeries(state.oiChart, {
            color: THEME.oiLine,
            lineWidth: 2,
            title: 'OI',
            priceFormat: {
                type: 'custom',
                formatter: (price) => formatOI(price),
            },
        });
    }

    // Funding Chart
    if (state.elements.fundingChartContainer) {
        state.fundingChart = createChart(state.elements.fundingChartContainer);

        // Historical series (faded)
        state.fundingHistoricalSeries = state.fundingChart.addHistogramSeries({
            color: 'rgba(128, 128, 128, 0.3)',  // Faded gray
            priceFormat: {
                type: 'custom',
                formatter: (price) => `${(price * 100).toFixed(4)}%`,
            },
        });

        // Live series (bright)
        state.fundingSeries = state.fundingChart.addHistogramSeries({
            color: THEME.fundingPositive,
            priceFormat: {
                type: 'custom',
                formatter: (price) => `${(price * 100).toFixed(4)}%`,
            },
        });
    }
}

// =============================================================================
// WebSocket Setup
// =============================================================================

/**
 * Initialize WebSocket connection.
 */
function initWebSocket() {
    state.ws = createDashboardWebSocket();

    // Status change handler
    state.ws.onStatusChange = (status) => {
        state.connectionStatus = status;
        updateConnectionStatus(status);
    };

    // Data handlers
    state.ws.onOI = handleOIUpdate;
    state.ws.onFunding = handleFundingUpdate;
    state.ws.onLiquidation = handleLiquidationUpdate;
    state.ws.onStatus = handleServerStatus;

    // B9: Subscribe in onOpen callback to avoid race condition
    state.ws.onOpen = () => {
        console.log('[Dashboard] WebSocket connected, subscribing to:', state.currentSymbol);
        state.ws.subscribe([state.currentSymbol]);
    };

    // Connect (subscribe will be called in onOpen)
    state.ws.connect();
}

// =============================================================================
// API Client & Historical Data
// =============================================================================

/**
 * Initialize API client for historical data.
 */
function initAPIClient() {
    state.apiClient = new APIClient();

    // Progress callback
    state.apiClient.onProgress = (percent, message) => {
        updateHistoricalProgress(percent, message);
    };

    // Error callback
    state.apiClient.onError = (error) => {
        console.error('[Dashboard] API error:', error);
        updateHistoricalProgress(0, `Error: ${error.message}`);
    };
}

/**
 * Initialize date range selector.
 */
function initDateRangeSelector() {
    if (state.elements.dateFrom && state.elements.dateTo) {
        state.dateRangeSelector = new DateRangeSelector({
            from: state.elements.dateFrom,
            to: state.elements.dateTo,
        }, {
            onRangeChange: (from, to) => {
                console.log(`[Dashboard] Date range changed: ${from} to ${to}`);
            },
        });
    }

    // Load historical button
    if (state.elements.loadHistoricalBtn) {
        state.elements.loadHistoricalBtn.addEventListener('click', loadHistoricalData);
    }
}

/**
 * Load historical data from API.
 * B20: Use proper guard with early return and button disable.
 */
async function loadHistoricalData() {
    // B20: Double-check guard and immediately disable button
    if (state.isLoadingHistorical) {
        console.log('[Dashboard] Historical data already loading');
        return;
    }

    // Set flag immediately to prevent race
    state.isLoadingHistorical = true;

    if (!state.dateRangeSelector) {
        console.warn('[Dashboard] Date range selector not initialized');
        state.isLoadingHistorical = false;
        return;
    }

    const { from, to } = state.dateRangeSelector.getRange();

    if (!from || !to) {
        console.warn('[Dashboard] Invalid date range');
        state.isLoadingHistorical = false;
        return;
    }

    console.log(`[Dashboard] Loading historical data: ${from} to ${to}`);

    // Disable button during load
    if (state.elements.loadHistoricalBtn) {
        state.elements.loadHistoricalBtn.disabled = true;
    }

    try {
        const data = await state.apiClient.loadHistoricalData(
            state.currentSymbol,
            from,
            to
        );

        // Apply historical data to charts
        applyHistoricalData(data);

    } catch (error) {
        console.error('[Dashboard] Failed to load historical data:', error);
    } finally {
        state.isLoadingHistorical = false;

        if (state.elements.loadHistoricalBtn) {
            state.elements.loadHistoricalBtn.disabled = false;
        }
    }
}

/**
 * Apply historical data to charts.
 * B93/B95: Added error handling for partial failures.
 * B53/B119: Fixed duplicate marker handling.
 * @param {Object} data - Historical data { oi, funding, liquidations }
 */
function applyHistoricalData(data) {
    try {
        // Clear historical series
        if (state.oiHistoricalSeries) {
            state.oiHistoricalSeries.setData([]);
        }
        if (state.fundingHistoricalSeries) {
            state.fundingHistoricalSeries.setData([]);
        }

        // Apply OI historical data
        if (data.oi && data.oi.length > 0 && state.oiHistoricalSeries) {
            const oiPoints = data.oi
                .filter(d => d && d.timestamp && d.open_interest_value !== undefined)
                .map(d => ({
                    time: Math.floor(d.timestamp / 1000),
                    value: d.open_interest_value,
                }))
                .sort((a, b) => a.time - b.time);

            state.oiHistoricalSeries.setData(oiPoints);
            console.log(`[Dashboard] Applied ${oiPoints.length} historical OI points`);
        }

        // Apply Funding historical data
        if (data.funding && data.funding.length > 0 && state.fundingHistoricalSeries) {
            const fundingPoints = data.funding
                .filter(d => d && d.timestamp && d.funding_rate !== undefined)
                .map(d => ({
                    time: Math.floor(d.timestamp / 1000),
                    value: d.funding_rate,
                    color: d.funding_rate > 0 ? 'rgba(239, 83, 80, 0.3)' : 'rgba(38, 166, 154, 0.3)',
                }))
                .sort((a, b) => a.time - b.time);

            state.fundingHistoricalSeries.setData(fundingPoints);
            console.log(`[Dashboard] Applied ${fundingPoints.length} historical funding points`);
        }

        // Apply historical liquidations as markers
        if (data.liquidations && data.liquidations.length > 0 && state.oiSeries) {
            const historicalMarkers = data.liquidations
                .filter(liq => liq && liq.timestamp && liq.side)
                .map(liq => ({
                    time: Math.floor(liq.timestamp / 1000),
                    position: liq.side === 'LONG' ? 'belowBar' : 'aboveBar',
                    color: liq.side === 'LONG' ? '#EF5350' : '#26A69A',
                    shape: 'circle',
                    size: 0.5,  // Smaller for historical
                    isHistorical: true,  // B53: Mark as historical for dedup
                }))
                .sort((a, b) => a.time - b.time);

            // B53/B119/B37: Deduplicate markers by time+position+text (finer granularity)
            const liveMarkers = state.liquidationBuffer.getMarkers();
            const seenKeys = new Set();
            const allMarkers = [...historicalMarkers, ...liveMarkers]
                .filter(m => {
                    // B37: Use time+position+text for finer granularity to avoid data loss
                    const key = `${m.time}-${m.position}-${m.text || ''}`;
                    if (seenKeys.has(key)) return false;
                    seenKeys.add(key);
                    return true;
                })
                .sort((a, b) => a.time - b.time);

            state.oiSeries.setMarkers(allMarkers);
            console.log(`[Dashboard] Applied ${historicalMarkers.length} historical + ${liveMarkers.length} live markers (deduped to ${allMarkers.length})`);
        }

        // Fit chart to show all data
        if (state.oiChart) {
            state.oiChart.timeScale().fitContent();
        }
        if (state.fundingChart) {
            state.fundingChart.timeScale().fitContent();
        }
    } catch (error) {
        // B95: Handle apply errors gracefully
        console.error('[Dashboard] Error applying historical data:', error);
        // Don't throw - leave charts in current state
    }
}

/**
 * Update historical data loading progress.
 * @param {number} percent - Progress percentage (0-100)
 * @param {string} message - Status message
 */
function updateHistoricalProgress(percent, message) {
    if (state.elements.historicalProgress) {
        if (percent === 0 && !message.startsWith('Error')) {
            state.elements.historicalProgress.textContent = '';
            state.elements.historicalProgress.style.display = 'none';
        } else {
            state.elements.historicalProgress.textContent = `${message} (${percent}%)`;
            state.elements.historicalProgress.style.display = 'inline';
        }
    }
}

// =============================================================================
// Data Handlers
// =============================================================================

/**
 * Handle OI update from WebSocket.
 * @param {Object} msg - OI update message
 */
function handleOIUpdate(msg) {
    if (msg.symbol !== state.currentSymbol) return;

    // Transform to chart format (timestamp in seconds)
    const point = {
        time: Math.floor(msg.timestamp / 1000),
        value: msg.open_interest_value,
    };

    // Add to buffer and update chart
    state.oiBuffer.add(point);

    if (state.oiSeries) {
        state.oiSeries.update(point);
    }

    // Update last update time
    updateLastUpdate();

    // Check for significant change (>5% in 1 min)
    checkSignificantOIChange(msg);
}

/**
 * Handle Funding update from WebSocket.
 * @param {Object} msg - Funding update message
 */
function handleFundingUpdate(msg) {
    if (msg.symbol !== state.currentSymbol) return;

    // Update funding display
    if (state.elements.fundingValue) {
        state.elements.fundingValue.textContent = formatFundingRate(msg.funding_rate);
        state.elements.fundingValue.className = `funding-value ${getFundingColorClass(msg.funding_rate)}`;
    }

    if (state.elements.fundingNext && msg.next_funding_time) {
        state.elements.fundingNext.textContent = `Next: ${formatCountdown(msg.next_funding_time)}`;
    }

    // Transform to chart format
    const point = {
        time: Math.floor(msg.timestamp / 1000),
        value: msg.funding_rate,
        color: msg.funding_rate > 0 ? THEME.fundingPositive : THEME.fundingNegative,
    };

    // Add to buffer and update chart
    state.fundingBuffer.add(point);

    if (state.fundingSeries) {
        state.fundingSeries.update(point);
    }

    updateLastUpdate();
}

/**
 * Handle Liquidation event from WebSocket.
 * @param {Object} msg - Liquidation message
 */
function handleLiquidationUpdate(msg) {
    if (msg.symbol !== state.currentSymbol) return;

    // Add to marker buffer
    state.liquidationBuffer.addLiquidation(msg);

    // Update markers on OI chart
    if (state.oiSeries) {
        state.oiSeries.setMarkers(state.liquidationBuffer.getMarkers());
    }

    updateLastUpdate();
}

/**
 * Handle server status message.
 * @param {Object} msg - Status message
 */
function handleServerStatus(msg) {
    console.log('[Dashboard] Server status:', msg);
}

/**
 * Check for significant OI change (>5% in 1 minute).
 * @param {Object} msg - Current OI message
 */
function checkSignificantOIChange(msg) {
    const data = state.oiBuffer.getAll();
    if (data.length < 2) return;

    const now = Math.floor(Date.now() / 1000);
    const oneMinuteAgo = now - 60;

    // Find the oldest point within the last minute
    const recentData = data.filter(p => p.time >= oneMinuteAgo);
    if (recentData.length < 2) return;

    const oldest = recentData[0];
    const newest = recentData[recentData.length - 1];

    const change = (newest.value - oldest.value) / oldest.value;

    if (Math.abs(change) > 0.05) {
        console.log(`[Dashboard] Significant OI change: ${(change * 100).toFixed(2)}%`);
        // Could trigger visual highlight here
    }
}

// =============================================================================
// UI Updates
// =============================================================================

/**
 * Update connection status indicator.
 * @param {string} status - 'connected', 'disconnected', or 'reconnecting'
 */
function updateConnectionStatus(status) {
    const { connectionStatus, statusText } = state.elements;

    if (connectionStatus) {
        connectionStatus.className = `status ${status}`;
    }

    if (statusText) {
        const labels = {
            connected: 'Connected',
            disconnected: 'Disconnected',
            reconnecting: 'Reconnecting...',
            connecting: 'Connecting...',
        };
        statusText.textContent = labels[status] || status;
    }
}

/**
 * Update last update timestamp.
 */
function updateLastUpdate() {
    if (state.elements.lastUpdate) {
        state.elements.lastUpdate.textContent = `Last update: ${formatDateTime(Date.now())}`;
    }
}

// =============================================================================
// Event Handlers
// =============================================================================

/**
 * Setup UI event listeners.
 */
function setupEventListeners() {
    // Symbol selector
    if (state.elements.symbolSelector) {
        state.elements.symbolSelector.addEventListener('change', handleSymbolChange);
    }
}

/**
 * Handle symbol change from dropdown.
 * B47/B51: Fixed race conditions and duplicate timeouts.
 * @param {Event} event
 */
function handleSymbolChange(event) {
    const newSymbol = event.target.value;

    if (newSymbol === state.currentSymbol) return;

    // B47: Cancel any pending symbol switch timeout
    if (state.symbolSwitchTimeout) {
        clearTimeout(state.symbolSwitchTimeout);
        state.symbolSwitchTimeout = null;
    }

    // B51: Prevent rapid switching race conditions
    if (state.symbolSwitchPending) {
        console.warn('[Dashboard] Symbol switch already pending, queuing...');
    }
    state.symbolSwitchPending = true;

    console.log(`[Dashboard] Switching symbol: ${state.currentSymbol} -> ${newSymbol}`);

    // Save chart state
    if (state.oiChart) {
        state.chartState = saveChartState(state.oiChart);
    }

    // B51: Unsubscribe and clear BEFORE updating symbol
    const oldSymbol = state.currentSymbol;
    state.ws.unsubscribe([oldSymbol]);

    // Clear buffers and charts immediately
    clearChartData();

    // Update state and subscribe to new symbol
    state.currentSymbol = newSymbol;
    state.ws.subscribe([newSymbol]);

    // B47: Track the timeout for potential cancellation
    if (state.chartState && state.oiChart) {
        state.symbolSwitchTimeout = setTimeout(() => {
            state.symbolSwitchTimeout = null;
            state.symbolSwitchPending = false;
            restoreChartState(state.oiChart, state.chartState);
        }, 500);
    } else {
        state.symbolSwitchPending = false;
    }
}

/**
 * Clear all chart data for symbol switch.
 */
function clearChartData() {
    // Clear buffers
    state.oiBuffer.clear();
    state.fundingBuffer.clear();
    state.liquidationBuffer.clear();

    // Clear live chart series
    if (state.oiSeries) {
        state.oiSeries.setData([]);
        state.oiSeries.setMarkers([]);
    }

    if (state.fundingSeries) {
        state.fundingSeries.setData([]);
    }

    // Clear historical chart series
    if (state.oiHistoricalSeries) {
        state.oiHistoricalSeries.setData([]);
    }

    if (state.fundingHistoricalSeries) {
        state.fundingHistoricalSeries.setData([]);
    }

    // Reset funding display
    if (state.elements.fundingValue) {
        state.elements.fundingValue.textContent = '--';
        state.elements.fundingValue.className = 'funding-value neutral';
    }

    if (state.elements.fundingNext) {
        state.elements.fundingNext.textContent = 'Next: --';
    }
}

/**
 * Handle browser tab visibility change (T059).
 * Pause updates when tab is inactive to save resources.
 */
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('[Dashboard] Tab inactive - pausing updates');
        state.tabActive = false;

        // Disconnect WebSocket when tab is hidden for >30 seconds
        state.inactiveTimer = setTimeout(() => {
            if (state.ws && state.ws.isConnected()) {
                console.log('[Dashboard] Disconnecting due to inactivity');
                state.ws.disconnect();
            }
        }, 30000);
    } else {
        console.log('[Dashboard] Tab active - resuming updates');
        state.tabActive = true;

        // Cancel inactivity timer
        if (state.inactiveTimer) {
            clearTimeout(state.inactiveTimer);
            state.inactiveTimer = null;
        }

        // Reconnect if disconnected
        if (state.ws && !state.ws.isConnected()) {
            console.log('[Dashboard] Reconnecting after tab activation');
            state.ws.connect();
        }
    }
}

// =============================================================================
// Startup
// =============================================================================

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

export default { init, destroy, state };
