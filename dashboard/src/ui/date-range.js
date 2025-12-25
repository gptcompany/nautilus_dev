/**
 * Date Range Selector - Date range picker for historical data.
 *
 * Features:
 * - From/To date inputs
 * - Preset ranges (1D, 7D, 30D)
 * - Validation
 */

/**
 * Date Range Selector Component
 */
export class DateRangeSelector {
    /**
     * Create date range selector.
     * @param {Object} elements - DOM elements
     * @param {HTMLInputElement} elements.from - From date input
     * @param {HTMLInputElement} elements.to - To date input
     * @param {Object} options - Options
     */
    constructor(elements, options = {}) {
        this.elements = elements;
        this.options = options;

        // Callbacks
        this.onRangeChange = options.onRangeChange || null;

        // State
        this.fromDate = null;
        this.toDate = null;

        // B22: Store bound handlers for cleanup
        this._boundHandleChange = this._handleChange.bind(this);

        this._init();
    }

    /**
     * Initialize component.
     */
    _init() {
        // Set default dates (last 7 days)
        const now = new Date();
        const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

        this.toDate = this._formatDate(now);
        this.fromDate = this._formatDate(sevenDaysAgo);

        // Initialize inputs - B22: Use stored bound handler for cleanup
        if (this.elements.from) {
            this.elements.from.value = this.fromDate;
            this.elements.from.addEventListener('change', this._boundHandleChange);
        }

        if (this.elements.to) {
            this.elements.to.value = this.toDate;
            this.elements.to.addEventListener('change', this._boundHandleChange);
        }
    }

    /**
     * Cleanup event listeners.
     * B22: Added destroy method to prevent memory leaks.
     */
    destroy() {
        if (this.elements.from) {
            this.elements.from.removeEventListener('change', this._boundHandleChange);
        }
        if (this.elements.to) {
            this.elements.to.removeEventListener('change', this._boundHandleChange);
        }
    }

    /**
     * Handle date input change.
     */
    _handleChange() {
        const from = this.elements.from?.value;
        const to = this.elements.to?.value;

        if (from && to) {
            // Validate range
            if (new Date(from) > new Date(to)) {
                console.warn('[DateRange] Invalid range: from > to');
                return;
            }

            this.fromDate = from;
            this.toDate = to;

            if (this.onRangeChange) {
                this.onRangeChange(from, to);
            }
        }
    }

    /**
     * Format date for input value.
     * @param {Date} date
     * @returns {string}
     */
    _formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    /**
     * Set preset range.
     * @param {string} preset - '1D', '7D', '30D', '90D'
     */
    setPreset(preset) {
        const now = new Date();
        let from;

        switch (preset) {
            case '1D':
                from = new Date(now.getTime() - 1 * 24 * 60 * 60 * 1000);
                break;
            case '7D':
                from = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case '30D':
                from = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                break;
            case '90D':
                from = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
                break;
            default:
                return;
        }

        this.setRange(from, now);
    }

    /**
     * Set date range.
     * @param {Date} from
     * @param {Date} to
     */
    setRange(from, to) {
        this.fromDate = this._formatDate(from);
        this.toDate = this._formatDate(to);

        if (this.elements.from) {
            this.elements.from.value = this.fromDate;
        }

        if (this.elements.to) {
            this.elements.to.value = this.toDate;
        }

        if (this.onRangeChange) {
            this.onRangeChange(this.fromDate, this.toDate);
        }
    }

    /**
     * Get current range.
     * @returns {Object}
     */
    getRange() {
        return {
            from: this.fromDate,
            to: this.toDate,
        };
    }
}

export default DateRangeSelector;
