/**
 * OI Chart - Open Interest line chart component.
 *
 * Features:
 * - Real-time OI updates via WebSocket
 * - Significant change detection (>5% in 1 min)
 * - Visual highlighting for large moves
 * - Liquidation markers overlay
 */

import { createChart, createLineSeries, THEME, saveChartState, restoreChartState } from './base-chart.js';
import { DataBuffer, MarkerBuffer } from '../data/buffer.js';
import { formatOI } from '../utils/format.js';

/**
 * OI Chart Component
 */
export class OIChart {
    /**
     * Create OI chart.
     * @param {HTMLElement} container - DOM container for chart
     * @param {Object} options - Chart options
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;

        // Chart instances
        this.chart = null;
        this.series = null;

        // Data buffers
        this.oiBuffer = new DataBuffer(50000);
        this.markerBuffer = new MarkerBuffer(10000);

        // State
        this.currentSymbol = null;
        this.lastOIValue = null;
        this.significantChangeThreshold = options.significantChangeThreshold || 0.05;
        this.highlightTimeout = null;  // B44: Track timeout for cleanup
        this.lastUpdateTime = 0;  // B36: Track last timestamp to prevent out-of-order updates

        // Callbacks
        this.onSignificantChange = options.onSignificantChange || null;

        this._init();
    }

    /**
     * Initialize chart.
     */
    _init() {
        // Create chart with dark theme
        this.chart = createChart(this.container);

        // Create line series for OI
        this.series = createLineSeries(this.chart, {
            color: THEME.oiLine,
            lineWidth: 2,
            title: 'OI (USD)',
            priceFormat: {
                type: 'custom',
                formatter: (price) => formatOI(price),
            },
        });
    }

    /**
     * Update chart with new OI data point.
     * B36: Added try/catch for out-of-order timestamp handling.
     * @param {Object} msg - OI update message from WebSocket
     */
    update(msg) {
        // Transform to chart format
        const point = this.transformToChartPoint(msg);

        // B36: Skip out-of-order updates (TradingView throws on these)
        if (point.time <= this.lastUpdateTime) {
            console.warn('[OIChart] Skipping out-of-order update:', point.time, '<=', this.lastUpdateTime);
            return;
        }

        // Add to buffer
        this.oiBuffer.add(point);

        // Update chart with error handling
        try {
            this.series.update(point);
            this.lastUpdateTime = point.time;  // B36: Track successful update time
        } catch (error) {
            console.error('[OIChart] Failed to update series:', error);
            return;
        }

        // Check for significant change
        this._checkSignificantChange(point);

        // Store last value
        this.lastOIValue = point.value;
    }

    /**
     * Transform WebSocket message to chart data point.
     * @param {Object} msg - OI update message
     * @returns {Object} ChartDataPoint
     */
    transformToChartPoint(msg) {
        return {
            time: Math.floor(msg.timestamp / 1000),
            value: msg.open_interest_value,
        };
    }

    /**
     * Add liquidation marker to chart.
     * @param {Object} liquidation - Liquidation event
     */
    addLiquidationMarker(liquidation) {
        this.markerBuffer.addLiquidation(liquidation);
        this.series.setMarkers(this.markerBuffer.getMarkers());
    }

    /**
     * Set all data (for historical load).
     * @param {Object[]} data - Array of OI data points
     */
    setData(data) {
        const chartData = data.map(d => ({
            time: Math.floor(d.timestamp / 1000),
            value: d.open_interest_value,
        }));

        this.oiBuffer.setData(chartData);
        this.series.setData(chartData);

        // Fit content
        this.chart.timeScale().fitContent();
    }

    /**
     * Clear all chart data.
     */
    clear() {
        this.oiBuffer.clear();
        this.markerBuffer.clear();
        this.series.setData([]);
        this.series.setMarkers([]);
        this.lastOIValue = null;
    }

    /**
     * Save chart state (zoom/pan).
     * @returns {Object}
     */
    saveState() {
        return saveChartState(this.chart);
    }

    /**
     * Restore chart state.
     * @param {Object} state
     */
    restoreState(state) {
        restoreChartState(this.chart, state);
    }

    /**
     * Get current data buffer.
     * @returns {DataBuffer}
     */
    getData() {
        return this.oiBuffer;
    }

    /**
     * Check for significant OI change.
     * @param {Object} point - Latest data point
     */
    _checkSignificantChange(point) {
        const data = this.oiBuffer.getAll();
        if (data.length < 2) return;

        const now = point.time;
        const oneMinuteAgo = now - 60;

        // Find data points in last minute
        const recentData = data.filter(p => p.time >= oneMinuteAgo);
        if (recentData.length < 2) return;

        const oldest = recentData[0];
        const newest = recentData[recentData.length - 1];

        // B3: Guard against division by zero
        if (!oldest.value || oldest.value === 0) return;

        const change = (newest.value - oldest.value) / oldest.value;
        const absChange = Math.abs(change);

        if (absChange > this.significantChangeThreshold) {
            const direction = change > 0 ? 'increase' : 'decrease';

            console.log(`[OIChart] Significant ${direction}: ${(absChange * 100).toFixed(2)}%`);

            // Apply visual highlight
            this._applySignificantChangeStyle(direction);

            // Trigger callback
            if (this.onSignificantChange) {
                this.onSignificantChange({
                    change: change,
                    direction: direction,
                    oldValue: oldest.value,
                    newValue: newest.value,
                    timestamp: newest.time,
                });
            }
        }
    }

    /**
     * Apply visual highlight for significant change.
     * B44: Track timeout to prevent firing on destroyed chart.
     * @param {string} direction - 'increase' or 'decrease'
     */
    _applySignificantChangeStyle(direction) {
        const color = direction === 'decrease' ? THEME.liquidationLong : THEME.oiLine;

        // Temporarily change color
        this.series.applyOptions({ color });

        // B44: Clear any existing highlight timeout
        if (this.highlightTimeout) {
            clearTimeout(this.highlightTimeout);
        }

        // Reset after 5 seconds - B44: Store timeout for cleanup
        this.highlightTimeout = setTimeout(() => {
            // B44: Check if chart still exists before applying
            if (this.series) {
                this.series.applyOptions({ color: THEME.oiLine });
            }
            this.highlightTimeout = null;
        }, 5000);
    }

    /**
     * Cleanup chart resources.
     * B44: Clear highlight timeout on destroy.
     */
    destroy() {
        // B44: Clear highlight timeout
        if (this.highlightTimeout) {
            clearTimeout(this.highlightTimeout);
            this.highlightTimeout = null;
        }

        // B36: Reset update time tracking
        this.lastUpdateTime = 0;

        if (this.chart) {
            if (this.chart._resizeObserver) {
                this.chart._resizeObserver.disconnect();
            }
            this.chart.remove();
            this.chart = null;
        }
        this.series = null;  // B44: Clear series reference
    }
}

export default OIChart;
