# Data Recording Scripts

Scripts per registrare dati live da exchange usando NautilusTrader nightly (Rust adapters).

## Setup

```bash
# Attiva ambiente nightly
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# Verifica versione
python -c "import nautilus_trader; print(nautilus_trader.__version__)"
# Expected: 1.222.0.dev...
```

## Scripts

### `record_binance_hyperliquid.py`

Registra dati da Binance Futures e Hyperliquid simultaneamente.

```bash
python record_binance_hyperliquid.py
```

**Dati registrati:**
- Trade ticks (ogni trade)
- Quote ticks (bid/ask)

**Instruments (default):**
- Binance: BTCUSDT-PERP, ETHUSDT-PERP, SOLUSDT-PERP
- Hyperliquid: BTC-USD-PERP, ETH-USD-PERP, SOL-USD-PERP

## Output

I dati vengono salvati in formato Feather (streaming) in:
```
/media/sam/1TB/nautilus_dev/data/live_catalog/
├── trade_tick/
├── quote_tick/
└── logs/
```

## Convertire a Parquet

Dopo la registrazione, converti i file feather in parquet:

```python
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.data import TradeTick, QuoteTick

catalog = ParquetDataCatalog("/media/sam/1TB/nautilus_dev/data/live_catalog")

# Converti trade ticks
catalog.convert_stream_to_data(
    instance_id="YOUR_INSTANCE_ID",  # Dal log di avvio
    data_cls=TradeTick,
    subdirectory="live",
)

# Converti quote ticks
catalog.convert_stream_to_data(
    instance_id="YOUR_INSTANCE_ID",
    data_cls=QuoteTick,
    subdirectory="live",
)
```

## Environment Variables (opzionali)

Per dati pubblici non servono credenziali. Per orderbook depth o dati privati:

```bash
# Binance
export BINANCE_API_KEY="your_key"
export BINANCE_API_SECRET="your_secret"

# Hyperliquid (solo per trading)
export HYPERLIQUID_PK="your_private_key"
```

## Modifica Instruments

Edita le liste in `record_binance_hyperliquid.py`:

```python
BINANCE_INSTRUMENTS = [
    "BTCUSDT-PERP.BINANCE",
    "ETHUSDT-PERP.BINANCE",
    # Aggiungi altri...
]

HYPERLIQUID_INSTRUMENTS = [
    "BTC-USD-PERP.HYPERLIQUID",
    # Aggiungi altri...
]
```

## Symbology

| Exchange | Format | Esempio |
|----------|--------|---------|
| Binance Futures | `{BASE}{QUOTE}-PERP.BINANCE` | `BTCUSDT-PERP.BINANCE` |
| Binance Spot | `{BASE}{QUOTE}.BINANCE` | `BTCUSDT.BINANCE` |
| Hyperliquid Perp | `{BASE}-USD-PERP.HYPERLIQUID` | `BTC-USD-PERP.HYPERLIQUID` |
| Hyperliquid Spot | `{BASE}-USDC-SPOT.HYPERLIQUID` | `PURR-USDC-SPOT.HYPERLIQUID` |
