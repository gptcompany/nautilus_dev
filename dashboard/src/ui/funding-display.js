/**
 * Funding Display - Funding rate display panel component.
 *
 * Features:
 * - Prominent current rate display
 * - Color coding (positive=red, negative=green)
 * - Next funding countdown
 */

import { formatFundingRate, formatCountdown, getFundingColorClass } from '../utils/format.js';

/**
 * Funding Display Component
 */
export class FundingDisplay {
    /**
     * Create funding display.
     * @param {Object} elements - DOM element references
     * @param {HTMLElement} elements.value - Element for rate value
     * @param {HTMLElement} elements.next - Element for next funding time
     */
    constructor(elements) {
        this.elements = elements;

        // State
        this.currentRate = null;
        this.nextFundingTime = null;

        // Countdown timer
        this.countdownTimer = null;

        this._startCountdownTimer();
    }

    /**
     * Update display with new funding data.
     * @param {Object} msg - Funding update message
     */
    update(msg) {
        this.currentRate = msg.funding_rate;
        this.nextFundingTime = msg.next_funding_time;

        // Update rate display
        if (this.elements.value) {
            this.elements.value.textContent = formatFundingRate(this.currentRate);
            this.elements.value.className = `funding-value ${getFundingColorClass(this.currentRate)}`;
        }

        // Update countdown
        this._updateCountdown();
    }

    /**
     * Update countdown display.
     */
    _updateCountdown() {
        if (this.elements.next) {
            if (this.nextFundingTime) {
                this.elements.next.textContent = `Next: ${formatCountdown(this.nextFundingTime)}`;
            } else {
                this.elements.next.textContent = 'Next: --';
            }
        }
    }

    /**
     * Start countdown timer for live updates.
     */
    _startCountdownTimer() {
        // Update countdown every minute
        this.countdownTimer = setInterval(() => {
            this._updateCountdown();
        }, 60000);
    }

    /**
     * Clear display.
     */
    clear() {
        this.currentRate = null;
        this.nextFundingTime = null;

        if (this.elements.value) {
            this.elements.value.textContent = '--';
            this.elements.value.className = 'funding-value neutral';
        }

        if (this.elements.next) {
            this.elements.next.textContent = 'Next: --';
        }
    }

    /**
     * Get current rate.
     * @returns {number|null}
     */
    getCurrentRate() {
        return this.currentRate;
    }

    /**
     * Cleanup resources.
     */
    destroy() {
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
            this.countdownTimer = null;
        }
    }
}

export default FundingDisplay;
