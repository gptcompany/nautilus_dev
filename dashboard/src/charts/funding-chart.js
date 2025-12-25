/**
 * Funding Chart - Funding rate chart component.
 *
 * Features:
 * - Real-time funding rate updates
 * - Color coding (positive=red, negative=green)
 * - Percentage formatting
 * - Extreme value handling
 */

import { createChart, THEME } from './base-chart.js';
import { DataBuffer } from '../data/buffer.js';
import { formatFundingRate, getFundingColorClass } from '../utils/format.js';

// Extreme value threshold (1000% = 10)
const EXTREME_VALUE_THRESHOLD = 10;

/**
 * Funding Chart Component
 */
export class FundingChart {
    /**
     * Create Funding chart.
     * @param {HTMLElement} container - DOM container for chart
     * @param {Object} options - Chart options
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;

        // Chart instances
        this.chart = null;
        this.series = null;

        // Data buffer
        this.buffer = new DataBuffer(10000);

        // State
        this.currentRate = null;
        this.nextFundingTime = null;

        this._init();
    }

    /**
     * Initialize chart.
     */
    _init() {
        // Create chart
        this.chart = createChart(this.container);

        // Create histogram series for funding rates
        this.series = this.chart.addHistogramSeries({
            color: THEME.fundingPositive,
            priceFormat: {
                type: 'custom',
                formatter: (price) => this._formatRate(price),
            },
        });
    }

    /**
     * Format rate for chart display.
     * @param {number} rate - Funding rate as decimal
     * @returns {string}
     */
    _formatRate(rate) {
        // Handle extreme values
        if (Math.abs(rate) > EXTREME_VALUE_THRESHOLD) {
            const sign = rate > 0 ? '+' : '';
            return `${sign}${(rate * 100).toFixed(0)}%`;
        }
        return formatFundingRate(rate);
    }

    /**
     * Update chart with new funding data.
     * @param {Object} msg - Funding update message from WebSocket
     */
    update(msg) {
        // Transform to chart format
        const point = this.transformToChartPoint(msg);

        // Handle extreme values (cap for display)
        const displayValue = this._clampExtremeValue(point.value);

        const chartPoint = {
            ...point,
            value: displayValue,
            color: this._getColor(msg.funding_rate),
        };

        // Add to buffer
        this.buffer.add(chartPoint);

        // Update chart
        this.series.update(chartPoint);

        // Update state
        this.currentRate = msg.funding_rate;
        this.nextFundingTime = msg.next_funding_time;
    }

    /**
     * Transform WebSocket message to chart data point.
     * @param {Object} msg - Funding update message
     * @returns {Object}
     */
    transformToChartPoint(msg) {
        return {
            time: Math.floor(msg.timestamp / 1000),
            value: msg.funding_rate,
        };
    }

    /**
     * Get color based on funding rate.
     * @param {number} rate - Funding rate
     * @returns {string} - Hex color
     */
    _getColor(rate) {
        if (rate > 0) {
            return THEME.fundingPositive;  // Red - longs pay
        } else if (rate < 0) {
            return THEME.fundingNegative;  // Green - shorts pay
        }
        return THEME.text;  // Neutral
    }

    /**
     * Clamp extreme values for display.
     * @param {number} value - Raw funding rate
     * @returns {number} - Clamped value
     */
    _clampExtremeValue(value) {
        if (Math.abs(value) > EXTREME_VALUE_THRESHOLD) {
            console.warn(`[FundingChart] Extreme funding rate: ${(value * 100).toFixed(2)}%`);
            // Cap at threshold but preserve sign
            return value > 0 ? EXTREME_VALUE_THRESHOLD : -EXTREME_VALUE_THRESHOLD;
        }
        return value;
    }

    /**
     * Set all data (for historical load).
     * @param {Object[]} data - Array of funding data points
     */
    setData(data) {
        const chartData = data.map(d => {
            const rate = d.funding_rate;
            return {
                time: Math.floor(d.timestamp / 1000),
                value: this._clampExtremeValue(rate),
                color: this._getColor(rate),
            };
        });

        this.buffer.setData(chartData);
        this.series.setData(chartData);

        // Fit content
        this.chart.timeScale().fitContent();
    }

    /**
     * Clear all chart data.
     */
    clear() {
        this.buffer.clear();
        this.series.setData([]);
        this.currentRate = null;
        this.nextFundingTime = null;
    }

    /**
     * Get current funding rate.
     * @returns {number|null}
     */
    getCurrentRate() {
        return this.currentRate;
    }

    /**
     * Get next funding time.
     * @returns {number|null}
     */
    getNextFundingTime() {
        return this.nextFundingTime;
    }

    /**
     * Get current data buffer.
     * @returns {DataBuffer}
     */
    getData() {
        return this.buffer;
    }

    /**
     * Cleanup chart resources.
     */
    destroy() {
        if (this.chart) {
            if (this.chart._resizeObserver) {
                this.chart._resizeObserver.disconnect();
            }
            this.chart.remove();
            this.chart = null;
        }
    }
}

export default FundingChart;
