/**
 * Liquidation Layer - Liquidation marker component for charts.
 *
 * Features:
 * - Marker positioning (LONG=below, SHORT=above)
 * - Color coding (LONG=red, SHORT=green)
 * - Aggregation for rapid events (>10/min)
 * - Value text display
 */

import { MarkerBuffer } from '../data/buffer.js';
import { THEME } from './base-chart.js';

// Aggregation settings
const AGGREGATION_WINDOW_MS = 60000;  // 1 minute
const AGGREGATION_THRESHOLD = 10;     // Aggregate if more than 10 in window

/**
 * Liquidation Layer Component
 */
export class LiquidationLayer {
    /**
     * Create liquidation layer.
     * @param {ISeriesApi} series - Chart series to attach markers to
     * @param {Object} options - Options
     */
    constructor(series, options = {}) {
        this.series = series;
        this.options = {
            aggregationWindow: options.aggregationWindow || AGGREGATION_WINDOW_MS,
            aggregationThreshold: options.aggregationThreshold || AGGREGATION_THRESHOLD,
            ...options,
        };

        // Marker buffer
        this.buffer = new MarkerBuffer(10000);

        // Aggregation state
        this.pendingLiquidations = [];
        this.aggregationTimer = null;
    }

    /**
     * Add liquidation event.
     * @param {Object} liquidation - Liquidation data from WebSocket
     */
    addLiquidation(liquidation) {
        // Add to pending for potential aggregation
        this.pendingLiquidations.push(liquidation);

        // Check if we should aggregate
        if (this._shouldAggregate()) {
            this._scheduleAggregation();
        } else {
            // Add individual marker
            const marker = this._createMarker(liquidation);
            this.buffer.add(marker);
            this._updateMarkers();
        }
    }

    /**
     * Create chart marker from liquidation data.
     * @param {Object} liq - Liquidation data
     * @returns {Object} Marker object
     */
    _createMarker(liq) {
        const isLong = liq.side === 'LONG';
        const valueK = this._formatValue(liq.value);

        return {
            time: Math.floor(liq.timestamp / 1000),
            position: isLong ? 'belowBar' : 'aboveBar',
            color: isLong ? THEME.liquidationLong : THEME.liquidationShort,
            shape: isLong ? 'arrowDown' : 'arrowUp',
            text: `${liq.side} $${valueK}`,
        };
    }

    /**
     * Create aggregated marker from multiple liquidations.
     * @param {Object[]} liquidations - Array of liquidation data
     * @returns {Object} Aggregated marker
     */
    _createAggregatedMarker(liquidations) {
        if (liquidations.length === 0) return null;

        // Calculate totals
        const totalValue = liquidations.reduce((sum, l) => sum + l.value, 0);
        const longCount = liquidations.filter(l => l.side === 'LONG').length;
        const shortCount = liquidations.filter(l => l.side === 'SHORT').length;

        // Use latest timestamp
        const latestTime = Math.max(...liquidations.map(l => l.timestamp));

        // Determine dominant side
        const isLongDominant = longCount >= shortCount;
        const valueK = this._formatValue(totalValue);

        return {
            time: Math.floor(latestTime / 1000),
            position: 'aboveBar',  // Aggregated always above
            color: isLongDominant ? THEME.liquidationLong : THEME.liquidationShort,
            shape: 'circle',
            text: `${liquidations.length} LIQs $${valueK}`,
        };
    }

    /**
     * Format value for marker text.
     * @param {number} value - USD value
     * @returns {string}
     */
    _formatValue(value) {
        if (value >= 1e6) {
            return `${(value / 1e6).toFixed(1)}M`;
        }
        return `${(value / 1000).toFixed(0)}K`;
    }

    /**
     * Check if we should aggregate pending liquidations.
     * @returns {boolean}
     */
    _shouldAggregate() {
        return this.pendingLiquidations.length >= this.options.aggregationThreshold;
    }

    /**
     * Schedule aggregation processing.
     */
    _scheduleAggregation() {
        if (this.aggregationTimer) return;

        this.aggregationTimer = setTimeout(() => {
            this._processAggregation();
            this.aggregationTimer = null;
        }, 1000);  // Wait 1 second for more liquidations
    }

    /**
     * Process pending liquidations into aggregated marker.
     */
    _processAggregation() {
        if (this.pendingLiquidations.length === 0) return;

        const marker = this._createAggregatedMarker(this.pendingLiquidations);
        if (marker) {
            this.buffer.add(marker);
            this._updateMarkers();
        }

        // Clear pending
        this.pendingLiquidations = [];
    }

    /**
     * Update markers on the chart series.
     */
    _updateMarkers() {
        if (this.series) {
            this.series.setMarkers(this.buffer.getMarkers());
        }
    }

    /**
     * Set all markers (for historical data).
     * @param {Object[]} liquidations - Array of liquidation data
     */
    setData(liquidations) {
        // Process in batches by time window
        const windows = this._groupByTimeWindow(liquidations);

        const markers = [];
        for (const window of windows) {
            if (window.length >= this.options.aggregationThreshold) {
                const aggMarker = this._createAggregatedMarker(window);
                if (aggMarker) markers.push(aggMarker);
            } else {
                for (const liq of window) {
                    markers.push(this._createMarker(liq));
                }
            }
        }

        this.buffer.setData(markers);
        this._updateMarkers();
    }

    /**
     * Group liquidations by time window for aggregation.
     * @param {Object[]} liquidations
     * @returns {Object[][]}
     */
    _groupByTimeWindow(liquidations) {
        if (liquidations.length === 0) return [];

        const sorted = [...liquidations].sort((a, b) => a.timestamp - b.timestamp);
        const windows = [];
        let currentWindow = [sorted[0]];

        for (let i = 1; i < sorted.length; i++) {
            const liq = sorted[i];
            const windowStart = currentWindow[0].timestamp;

            if (liq.timestamp - windowStart <= this.options.aggregationWindow) {
                currentWindow.push(liq);
            } else {
                windows.push(currentWindow);
                currentWindow = [liq];
            }
        }

        if (currentWindow.length > 0) {
            windows.push(currentWindow);
        }

        return windows;
    }

    /**
     * Clear all markers.
     */
    clear() {
        this.buffer.clear();
        this.pendingLiquidations = [];
        if (this.aggregationTimer) {
            clearTimeout(this.aggregationTimer);
            this.aggregationTimer = null;
        }
        this._updateMarkers();
    }

    /**
     * Get marker buffer.
     * @returns {MarkerBuffer}
     */
    getMarkers() {
        return this.buffer;
    }

    /**
     * Cleanup resources.
     */
    destroy() {
        if (this.aggregationTimer) {
            clearTimeout(this.aggregationTimer);
        }
    }
}

export default LiquidationLayer;
