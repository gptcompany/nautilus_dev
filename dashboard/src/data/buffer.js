/**
 * DataBuffer - Rolling window buffer for chart data.
 *
 * Features:
 * - Fixed maximum size with automatic cleanup
 * - Time-sorted data storage
 * - Efficient append and bulk operations
 */

export class DataBuffer {
    /**
     * Create a new data buffer.
     * @param {number} maxPoints - Maximum number of points to store (default: 50000)
     */
    constructor(maxPoints = 50000) {
        this.maxPoints = maxPoints;
        this.data = [];
    }

    /**
     * Add a single data point.
     * @param {Object} point - Data point with { time, value } or marker format
     */
    add(point) {
        // B1: Validate point has required fields
        if (!point || point.time === undefined || point.time === null) {
            console.warn('[DataBuffer] Invalid point, skipping:', point);
            return;
        }
        this.data.push(point);
        this._cleanup();
    }

    /**
     * Add multiple data points.
     * @param {Object[]} points - Array of data points
     */
    addBulk(points) {
        this.data.push(...points);
        this._sortByTime();
        this._cleanup();
    }

    /**
     * Set all data (replaces existing).
     * @param {Object[]} points - Array of data points
     */
    setData(points) {
        this.data = [...points];
        this._sortByTime();
        this._cleanup();
    }

    /**
     * Clear all data.
     */
    clear() {
        this.data = [];
    }

    /**
     * Get all data points.
     * @returns {Object[]}
     */
    getAll() {
        return this.data;
    }

    /**
     * Get data points in a time range.
     * @param {number} from - Start time (unix seconds)
     * @param {number} to - End time (unix seconds)
     * @returns {Object[]}
     */
    getRange(from, to) {
        return this.data.filter(p => p.time >= from && p.time <= to);
    }

    /**
     * Get the most recent N points.
     * @param {number} n - Number of points
     * @returns {Object[]}
     */
    getRecent(n) {
        return this.data.slice(-n);
    }

    /**
     * Get the latest data point.
     * @returns {Object|null}
     */
    getLast() {
        return this.data.length > 0 ? this.data[this.data.length - 1] : null;
    }

    /**
     * Get buffer size.
     * @returns {number}
     */
    get length() {
        return this.data.length;
    }

    /**
     * Check if buffer is empty.
     * @returns {boolean}
     */
    isEmpty() {
        return this.data.length === 0;
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    _cleanup() {
        if (this.data.length > this.maxPoints) {
            // Remove oldest 10% when limit exceeded
            const removeCount = Math.floor(this.data.length * 0.1);
            this.data = this.data.slice(removeCount);
        }
    }

    _sortByTime() {
        // B2: Filter out invalid points before sorting
        this.data = this.data.filter(p => p && p.time !== undefined && p.time !== null);
        this.data.sort((a, b) => a.time - b.time);
    }
}

/**
 * MarkerBuffer - Specialized buffer for chart markers (liquidations).
 *
 * Extends DataBuffer with marker-specific functionality.
 */
export class MarkerBuffer extends DataBuffer {
    /**
     * Create a new marker buffer.
     * @param {number} maxPoints - Maximum markers to store (default: 10000)
     */
    constructor(maxPoints = 10000) {
        super(maxPoints);
    }

    /**
     * Add a liquidation marker.
     * @param {Object} liquidation - Liquidation data from WebSocket
     */
    addLiquidation(liquidation) {
        const marker = this._createMarker(liquidation);
        this.add(marker);
    }

    /**
     * Get markers formatted for Lightweight Charts.
     * @returns {Object[]}
     */
    getMarkers() {
        return this.data;
    }

    /**
     * Create a chart marker from liquidation data.
     * @param {Object} liq - Liquidation data
     * @returns {Object}
     */
    _createMarker(liq) {
        const isLong = liq.side === 'LONG';
        const valueK = (liq.value / 1000).toFixed(0);

        return {
            time: Math.floor(liq.timestamp / 1000),
            position: isLong ? 'belowBar' : 'aboveBar',
            color: isLong ? '#f44336' : '#00c853',
            shape: isLong ? 'arrowDown' : 'arrowUp',
            text: `${liq.side} $${valueK}K`
        };
    }
}

export default DataBuffer;
