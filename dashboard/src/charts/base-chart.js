/**
 * Base Chart - Shared chart setup with dark theme.
 *
 * Provides common configuration for TradingView Lightweight Charts.
 */

// Dark theme color palette
export const THEME = {
    background: '#1a1a2e',
    text: '#e0e0e0',
    textSecondary: '#a0a0a0',
    grid: '#2a2a4a',
    border: '#3a3a5a',

    // Chart colors
    oiLine: '#2196F3',
    fundingPositive: '#ff5722',
    fundingNegative: '#4caf50',
    liquidationLong: '#f44336',
    liquidationShort: '#00c853',

    // Historical data (faded)
    historicalOpacity: 0.5,
};

// Default chart options
export const DEFAULT_CHART_OPTIONS = {
    layout: {
        background: { type: 'solid', color: THEME.background },
        textColor: THEME.text,
    },
    grid: {
        vertLines: { color: THEME.grid },
        horzLines: { color: THEME.grid },
    },
    rightPriceScale: {
        borderColor: THEME.border,
    },
    timeScale: {
        borderColor: THEME.border,
        timeVisible: true,
        secondsVisible: false,
    },
    crosshair: {
        mode: 1, // Magnet mode
        vertLine: {
            color: THEME.text,
            width: 1,
            style: 2, // Dashed
            labelBackgroundColor: THEME.background,
        },
        horzLine: {
            color: THEME.text,
            width: 1,
            style: 2,
            labelBackgroundColor: THEME.background,
        },
    },
    handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
    },
    handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
    },
};

/**
 * Create a chart with dark theme.
 * B31: Added try/catch for CDN failure handling.
 * B85: Added validation for container dimensions.
 * @param {HTMLElement} container - DOM element to render chart in
 * @param {Object} options - Additional options to merge
 * @returns {IChartApi|null}
 */
export function createChart(container, options = {}) {
    // B31: Check if LightweightCharts is available (CDN may have failed)
    if (typeof LightweightCharts === 'undefined') {
        console.error('[Chart] LightweightCharts library not loaded. Check CDN connection.');
        return null;
    }

    // B85: Validate container has valid dimensions
    const width = container.clientWidth || options.width || 400;
    const height = container.clientHeight || options.height || 300;

    if (width <= 0 || height <= 0) {
        console.warn('[Chart] Container has zero dimensions, using defaults');
    }

    const chartOptions = {
        ...DEFAULT_CHART_OPTIONS,
        width: Math.max(width, 100),  // B85: Minimum dimensions
        height: Math.max(height, 100),
        ...options,
    };

    try {
        // B31: Wrap chart creation in try/catch
        const chart = LightweightCharts.createChart(container, chartOptions);

        // Handle resize
        const resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                const { width: w, height: h } = entry.contentRect;
                // B85: Only resize if dimensions are valid
                if (w > 0 && h > 0) {
                    chart.applyOptions({ width: w, height: h });
                }
            }
        });
        resizeObserver.observe(container);

        // Store resize observer for cleanup
        chart._resizeObserver = resizeObserver;

        return chart;
    } catch (error) {
        console.error('[Chart] Failed to create chart:', error);
        return null;
    }
}

/**
 * Create a line series with default styling.
 * @param {IChartApi} chart - Chart instance
 * @param {Object} options - Series options
 * @returns {ISeriesApi}
 */
export function createLineSeries(chart, options = {}) {
    return chart.addLineSeries({
        color: THEME.oiLine,
        lineWidth: 2,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        ...options,
    });
}

/**
 * Create a histogram series (for funding rate).
 * @param {IChartApi} chart - Chart instance
 * @param {Object} options - Series options
 * @returns {ISeriesApi}
 */
export function createHistogramSeries(chart, options = {}) {
    return chart.addHistogramSeries({
        color: THEME.fundingPositive,
        ...options,
    });
}

/**
 * Create an area series (for historical data overlay).
 * @param {IChartApi} chart - Chart instance
 * @param {Object} options - Series options
 * @returns {ISeriesApi}
 */
export function createAreaSeries(chart, options = {}) {
    return chart.addAreaSeries({
        lineColor: THEME.oiLine,
        topColor: `${THEME.oiLine}40`,
        bottomColor: `${THEME.oiLine}10`,
        lineWidth: 1,
        ...options,
    });
}

/**
 * Add visual distinction for historical data.
 * @param {ISeriesApi} series - Series to style
 * @param {boolean} isHistorical - Whether data is historical
 */
export function setHistoricalStyle(series, isHistorical) {
    if (isHistorical) {
        series.applyOptions({
            color: `${THEME.oiLine}${Math.floor(THEME.historicalOpacity * 255).toString(16)}`,
        });
    } else {
        series.applyOptions({
            color: THEME.oiLine,
        });
    }
}

/**
 * Save chart state (zoom level, visible range).
 * @param {IChartApi} chart - Chart instance
 * @returns {Object} State object
 */
export function saveChartState(chart) {
    const timeScale = chart.timeScale();
    return {
        visibleRange: timeScale.getVisibleRange(),
        logicalRange: timeScale.getVisibleLogicalRange(),
    };
}

/**
 * Restore chart state.
 * @param {IChartApi} chart - Chart instance
 * @param {Object} state - State object from saveChartState
 */
export function restoreChartState(chart, state) {
    if (state && state.visibleRange) {
        const timeScale = chart.timeScale();
        timeScale.setVisibleRange(state.visibleRange);
    }
}

/**
 * Cleanup chart resources.
 * @param {IChartApi} chart - Chart instance
 */
export function destroyChart(chart) {
    if (chart._resizeObserver) {
        chart._resizeObserver.disconnect();
    }
    chart.remove();
}

export default {
    THEME,
    createChart,
    createLineSeries,
    createHistogramSeries,
    createAreaSeries,
    setHistoricalStyle,
    saveChartState,
    restoreChartState,
    destroyChart,
};
