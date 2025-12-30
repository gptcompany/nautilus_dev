/**
 * API Client - REST API client for historical data.
 *
 * Features:
 * - Historical data loading with progress
 * - Data aggregation for large ranges
 * - Error handling and graceful degradation
 */

/**
 * API Client for dashboard REST endpoints.
 */
export class APIClient {
    /**
     * Create API client.
     * @param {string} baseUrl - Base URL for API (default: auto-detect)
     */
    constructor(baseUrl = null) {
        if (!baseUrl) {
            // Auto-detect based on current page location
            const protocol = window.location.protocol;
            const host = window.location.host || 'localhost:8765';
            baseUrl = `${protocol}//${host}/api`;
        }

        this.baseUrl = baseUrl;

        // Callbacks
        this.onProgress = null;
        this.onError = null;
    }

    /**
     * Fetch server status.
     * @returns {Promise<Object>}
     */
    async getStatus() {
        return this._fetch('/status');
    }

    /**
     * Fetch available symbols.
     * @returns {Promise<Object>}
     */
    async getSymbols() {
        return this._fetch('/symbols');
    }

    /**
     * Fetch historical OI data.
     * @param {string} symbol - Trading pair
     * @param {string} from - Start date (YYYY-MM-DD)
     * @param {string} to - End date (YYYY-MM-DD)
     * @param {Object} options - Additional options
     * @returns {Promise<Object>}
     */
    async getHistoricalOI(symbol, from, to, options = {}) {
        const params = new URLSearchParams({
            symbol,
            from,
            to,
            ...(options.venue && { venue: options.venue }),
            ...(options.limit && { limit: options.limit }),
        });

        const data = await this._fetch(`/history/oi?${params}`);

        // Aggregate if needed
        if (options.aggregate && data.data?.length > 1000) {
            data.data = this._aggregateData(data.data, options.aggregateInterval || 3600);
        }

        return data;
    }

    /**
     * Fetch historical funding data.
     * @param {string} symbol - Trading pair
     * @param {string} from - Start date
     * @param {string} to - End date
     * @param {Object} options - Additional options
     * @returns {Promise<Object>}
     */
    async getHistoricalFunding(symbol, from, to, options = {}) {
        const params = new URLSearchParams({
            symbol,
            from,
            to,
            ...(options.venue && { venue: options.venue }),
            ...(options.limit && { limit: options.limit }),
        });

        return this._fetch(`/history/funding?${params}`);
    }

    /**
     * Fetch historical liquidations.
     * @param {string} symbol - Trading pair
     * @param {string} from - Start date
     * @param {string} to - End date
     * @param {Object} options - Additional options
     * @returns {Promise<Object>}
     */
    async getHistoricalLiquidations(symbol, from, to, options = {}) {
        const params = new URLSearchParams({
            symbol,
            from,
            to,
            ...(options.venue && { venue: options.venue }),
            ...(options.side && { side: options.side }),
            ...(options.minValue && { min_value: options.minValue }),
            ...(options.limit && { limit: options.limit }),
        });

        return this._fetch(`/history/liquidations?${params}`);
    }

    /**
     * Load all historical data for a symbol.
     * @param {string} symbol - Trading pair
     * @param {string} from - Start date
     * @param {string} to - End date
     * @returns {Promise<Object>}
     */
    async loadHistoricalData(symbol, from, to) {
        this._notifyProgress(0, 'Loading OI data...');

        try {
            // Load OI data
            const oiData = await this.getHistoricalOI(symbol, from, to, { aggregate: true });
            this._notifyProgress(33, 'Loading funding data...');

            // Load funding data
            const fundingData = await this.getHistoricalFunding(symbol, from, to);
            this._notifyProgress(66, 'Loading liquidation data...');

            // Load liquidation data
            const liquidationData = await this.getHistoricalLiquidations(symbol, from, to);
            this._notifyProgress(100, 'Complete');

            return {
                oi: oiData.data || [],
                funding: fundingData.data || [],
                liquidations: liquidationData.data || [],
            };

        } catch (error) {
            this._notifyProgress(0, 'Error loading data');
            throw error;
        }
    }

    /**
     * Check if historical catalog is available.
     * @returns {Promise<boolean>}
     */
    async isHistoricalAvailable() {
        try {
            const status = await this.getStatus();
            return status.status === 'healthy';
        } catch (error) {
            return false;
        }
    }

    /**
     * Load historical data with graceful degradation (T060).
     * Falls back to empty data if catalog unavailable.
     * @param {string} symbol
     * @param {string} from
     * @param {string} to
     * @returns {Promise<Object>}
     */
    async loadHistoricalDataSafe(symbol, from, to) {
        const available = await this.isHistoricalAvailable();

        if (!available) {
            console.warn('[APIClient] Historical catalog unavailable, using empty data');
            this._notifyProgress(100, 'Historical data unavailable');
            return {
                oi: [],
                funding: [],
                liquidations: [],
                degraded: true
            };
        }

        return this.loadHistoricalData(symbol, from, to);
    }

    // =========================================================================
    // Private Methods
    // =========================================================================

    /**
     * Fetch from API.
     * @param {string} endpoint - API endpoint
     * @returns {Promise<Object>}
     */
    async _fetch(endpoint) {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url);

            // Check HTTP status (T058)
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
            }

            const data = await response.json();

            // Check for error response
            if (data.error) {
                throw new Error(`${data.error}: ${data.message}`);
            }

            return data;

        } catch (error) {
            // Handle network errors (T058)
            let userFriendlyMessage = error.message;
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                userFriendlyMessage = 'Network error: Unable to reach server';
            }

            console.error(`[APIClient] Fetch error: ${url}`, error);

            if (this.onError) {
                this.onError(new Error(userFriendlyMessage));
            }

            throw error;
        }
    }

    /**
     * Aggregate data points by time interval.
     * @param {Object[]} data - Data points
     * @param {number} intervalSeconds - Aggregation interval in seconds
     * @returns {Object[]}
     */
    _aggregateData(data, intervalSeconds) {
        if (data.length === 0) return [];

        const intervalMs = intervalSeconds * 1000;
        const aggregated = [];
        let bucket = [];
        let bucketStart = data[0].timestamp;

        for (const point of data) {
            if (point.timestamp - bucketStart >= intervalMs) {
                // Close current bucket
                if (bucket.length > 0) {
                    aggregated.push(this._aggregateBucket(bucket));
                }

                // Start new bucket
                bucket = [point];
                bucketStart = point.timestamp;
            } else {
                bucket.push(point);
            }
        }

        // Close last bucket
        if (bucket.length > 0) {
            aggregated.push(this._aggregateBucket(bucket));
        }

        return aggregated;
    }

    /**
     * Aggregate a bucket of data points.
     * @param {Object[]} bucket
     * @returns {Object}
     */
    _aggregateBucket(bucket) {
        // Use last value for OI (it's cumulative)
        const last = bucket[bucket.length - 1];
        return {
            timestamp: last.timestamp,
            venue: last.venue,
            open_interest: last.open_interest,
            open_interest_value: last.open_interest_value,
        };
    }

    /**
     * Notify progress callback.
     * @param {number} percent
     * @param {string} message
     */
    _notifyProgress(percent, message) {
        if (this.onProgress) {
            this.onProgress(percent, message);
        }
    }
}

/**
 * Create API client for dashboard.
 * @returns {APIClient}
 */
export function createAPIClient() {
    return new APIClient();
}

export default APIClient;
