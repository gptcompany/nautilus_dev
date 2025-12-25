/**
 * Formatters - Number and time formatting utilities.
 */

/**
 * Format a large number with K/M/B suffixes.
 * @param {number} value - Number to format
 * @param {number} decimals - Decimal places (default: 2)
 * @returns {string}
 */
export function formatLargeNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return '--';
    }

    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : '';

    if (absValue >= 1e12) {
        return `${sign}${(absValue / 1e12).toFixed(decimals)}T`;
    }
    if (absValue >= 1e9) {
        return `${sign}${(absValue / 1e9).toFixed(decimals)}B`;
    }
    if (absValue >= 1e6) {
        return `${sign}${(absValue / 1e6).toFixed(decimals)}M`;
    }
    if (absValue >= 1e3) {
        return `${sign}${(absValue / 1e3).toFixed(decimals)}K`;
    }

    return `${sign}${absValue.toFixed(decimals)}`;
}

/**
 * Format Open Interest value in USD.
 * @param {number} value - OI value in USD
 * @returns {string}
 */
export function formatOI(value) {
    return `$${formatLargeNumber(value, 2)}`;
}

/**
 * Format funding rate as percentage.
 * @param {number} rate - Funding rate as decimal (0.0001 = 0.01%)
 * @param {number} decimals - Decimal places (default: 4)
 * @returns {string}
 */
export function formatFundingRate(rate, decimals = 4) {
    if (rate === null || rate === undefined || isNaN(rate)) {
        return '--';
    }

    const percentage = rate * 100;
    const sign = percentage > 0 ? '+' : '';
    return `${sign}${percentage.toFixed(decimals)}%`;
}

/**
 * Format liquidation value.
 * @param {number} value - USD value
 * @returns {string}
 */
export function formatLiquidation(value) {
    return `$${formatLargeNumber(value, 0)}`;
}

/**
 * Format Unix timestamp (seconds) to time string.
 * @param {number} timestamp - Unix timestamp in seconds
 * @returns {string}
 */
export function formatTime(timestamp) {
    if (!timestamp) return '--';

    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });
}

/**
 * Format Unix timestamp (milliseconds) to date/time string.
 * @param {number} timestamp - Unix timestamp in milliseconds
 * @returns {string}
 */
export function formatDateTime(timestamp) {
    if (!timestamp) return '--';

    const date = new Date(timestamp);
    return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * Format countdown to next funding.
 * @param {number} nextFundingTime - Unix timestamp in milliseconds
 * @returns {string}
 */
export function formatCountdown(nextFundingTime) {
    if (!nextFundingTime) return '--';

    const now = Date.now();
    const diff = nextFundingTime - now;

    if (diff <= 0) return 'Now';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

/**
 * Format price with appropriate decimals.
 * @param {number} price - Price value
 * @param {number} decimals - Decimal places (default: 2)
 * @returns {string}
 */
export function formatPrice(price, decimals = 2) {
    if (price === null || price === undefined || isNaN(price)) {
        return '--';
    }

    return price.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

/**
 * Format quantity.
 * @param {number} qty - Quantity value
 * @param {number} decimals - Decimal places (default: 4)
 * @returns {string}
 */
export function formatQuantity(qty, decimals = 4) {
    if (qty === null || qty === undefined || isNaN(qty)) {
        return '--';
    }

    return qty.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals,
    });
}

/**
 * Get color class for funding rate.
 * @param {number} rate - Funding rate as decimal
 * @returns {string} - CSS class name
 */
export function getFundingColorClass(rate) {
    if (rate === null || rate === undefined || rate === 0) {
        return 'neutral';
    }
    return rate > 0 ? 'positive' : 'negative';
}

export default {
    formatLargeNumber,
    formatOI,
    formatFundingRate,
    formatLiquidation,
    formatTime,
    formatDateTime,
    formatCountdown,
    formatPrice,
    formatQuantity,
    getFundingColorClass,
};
