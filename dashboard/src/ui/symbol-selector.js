/**
 * Symbol Selector - Symbol dropdown component.
 *
 * Features:
 * - Symbol switching with callback
 * - Dynamic symbol list population
 */

/**
 * Symbol Selector Component
 */
export class SymbolSelector {
    /**
     * Create symbol selector.
     * @param {HTMLSelectElement} selectElement - Select DOM element
     * @param {Object} options - Options
     */
    constructor(selectElement, options = {}) {
        this.element = selectElement;
        this.options = options;

        // Callbacks
        this.onSymbolChange = options.onSymbolChange || null;

        // State
        this.currentSymbol = null;
        this.symbols = [];

        this._init();
    }

    /**
     * Initialize component.
     */
    _init() {
        if (this.element) {
            this.element.addEventListener('change', this._handleChange.bind(this));

            // Set initial value
            this.currentSymbol = this.element.value;
        }
    }

    /**
     * Handle select change event.
     * @param {Event} event
     */
    _handleChange(event) {
        const newSymbol = event.target.value;

        if (newSymbol !== this.currentSymbol) {
            const oldSymbol = this.currentSymbol;
            this.currentSymbol = newSymbol;

            if (this.onSymbolChange) {
                this.onSymbolChange(newSymbol, oldSymbol);
            }
        }
    }

    /**
     * Set available symbols.
     * @param {Object[]} symbols - Array of symbol info objects
     */
    setSymbols(symbols) {
        this.symbols = symbols;

        if (this.element) {
            // Clear existing options
            this.element.innerHTML = '';

            // Add new options
            for (const sym of symbols) {
                const option = document.createElement('option');
                option.value = sym.symbol;
                option.textContent = sym.symbol;
                this.element.appendChild(option);
            }

            // Restore selection if possible
            if (this.currentSymbol && symbols.some(s => s.symbol === this.currentSymbol)) {
                this.element.value = this.currentSymbol;
            } else if (symbols.length > 0) {
                this.currentSymbol = symbols[0].symbol;
                this.element.value = this.currentSymbol;
            }
        }
    }

    /**
     * Get current symbol.
     * @returns {string|null}
     */
    getCurrentSymbol() {
        return this.currentSymbol;
    }

    /**
     * Set current symbol programmatically.
     * @param {string} symbol
     */
    setCurrentSymbol(symbol) {
        if (this.element) {
            this.element.value = symbol;
            this.currentSymbol = symbol;
        }
    }

    /**
     * Disable selector.
     */
    disable() {
        if (this.element) {
            this.element.disabled = true;
        }
    }

    /**
     * Enable selector.
     */
    enable() {
        if (this.element) {
            this.element.disabled = false;
        }
    }
}

export default SymbolSelector;
