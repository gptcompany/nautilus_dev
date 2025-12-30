"""Entry point for running CCXT pipeline as a module.

Usage:
    python -m scripts.ccxt_pipeline fetch-oi BTCUSDT-PERP
    python -m scripts.ccxt_pipeline fetch-funding BTCUSDT-PERP
"""

from scripts.ccxt_pipeline.cli import main

if __name__ == "__main__":
    main()
