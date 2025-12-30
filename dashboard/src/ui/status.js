/**
 * Status Indicator - Connection status component.
 *
 * Features:
 * - Visual status indicator (connected/reconnecting/disconnected)
 * - Color coding (green/yellow/red)
 * - Status text display
 */

/**
 * Connection status states
 */
export const ConnectionState = {
    CONNECTED: 'connected',
    RECONNECTING: 'reconnecting',
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
};

/**
 * Status Indicator Component
 */
export class StatusIndicator {
    /**
     * Create status indicator.
     * @param {HTMLElement} container - Container element with .status-dot and .status-text
     */
    constructor(container) {
        this.container = container;
        this.dotElement = container?.querySelector('.status-dot');
        this.textElement = container?.querySelector('.status-text');

        // State
        this.currentStatus = ConnectionState.DISCONNECTED;

        // Status labels
        this.labels = {
            [ConnectionState.CONNECTED]: 'Connected',
            [ConnectionState.RECONNECTING]: 'Reconnecting...',
            [ConnectionState.DISCONNECTED]: 'Disconnected',
            [ConnectionState.CONNECTING]: 'Connecting...',
        };
    }

    /**
     * Set connection status.
     * @param {string} status - One of ConnectionState values
     */
    setStatus(status) {
        this.currentStatus = status;

        // Update container class
        if (this.container) {
            this.container.className = `status ${status}`;
        }

        // Update text
        if (this.textElement) {
            this.textElement.textContent = this.labels[status] || status;
        }
    }

    /**
     * Get current status.
     * @returns {string}
     */
    getStatus() {
        return this.currentStatus;
    }

    /**
     * Check if connected.
     * @returns {boolean}
     */
    isConnected() {
        return this.currentStatus === ConnectionState.CONNECTED;
    }
}

export default StatusIndicator;
