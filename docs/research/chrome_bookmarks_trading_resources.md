# Chrome Bookmarks - Trading Resources per NautilusTrader

Estratto dai bookmark Chrome, filtrato per risorse utili allo sviluppo di strategie e indicatori NautilusTrader.

## Federal Reserve / Macro Data (Alta Priorità)

| Risorsa | URL | Uso NautilusTrader |
|---------|-----|-------------------|
| M2 Money Supply (FRED) | https://fred.stlouisfed.org/series/WM2NS | Macro indicator, liquidity regime |
| Reverse Repo Operations | https://www.newyorkfed.org/markets/desk-operations/reverse-repo | Liquidity drain indicator |
| Central Bank Liquidity Swaps | https://www.newyorkfed.org/markets/desk-operations/central-bank-liquidity-swap-operations | Global liquidity flows |
| Treasury General Account | https://en.macromicro.me/charts/34339/us-treasury-general-account | Fiscal liquidity indicator |
| 10-Year Swap Rates (Chatham) | https://www.chathamfinancial.com/technology/us-market-rates | Interest rate regime |

## On-Chain Crypto Analytics (Alta Priorità)

| Risorsa | URL | Uso NautilusTrader |
|---------|-----|-------------------|
| BTC Liquidation Map (CoinGlass) | https://www.coinglass.com/pro/futures/LiquidationMap | Liquidation zones (già implementato!) |
| CryptoQuant Taker Buy/Sell Ratio | https://cryptoquant.com/asset/btc/chart/derivatives/taker-buy-sell-ratio | Orderflow delta |
| Bitcoin Open Interest (Coinalyze) | https://coinalyze.net/bitcoin/open-interest/ | OI-based signals |
| IntoTheBlock Analytics | https://app.intotheblock.com/ | On-chain metrics |
| HODL Waves (Unchained) | https://unchained.com/hodlwaves/ | Long-term holder behavior |
| Whale Shadows (LookIntoBitcoin) | https://www.lookintobitcoin.com/charts/whale-shadows/ | Whale activity |
| Advanced NVT Signal | https://www.lookintobitcoin.com/charts/advanced-nvt-signal/ | Network value indicator |
| Relative Unrealized P/L | https://www.lookintobitcoin.com/charts/relative-unrealized-profit--loss/ | Market sentiment |
| Power Law Oscillator | https://stats.buybitcoinworldwide.com/power-law-oscillator/ | Valuation model |

## Market Data Platforms (Media Priorità)

| Risorsa | URL | Uso NautilusTrader |
|---------|-----|-------------------|
| Hyperliquid Stats | https://stats.hyperliquid.xyz/ | DEX orderflow/liquidations |
| ViewBase Long/Short Ratio | https://www.viewbase.com/long_short_position | Position ratio |
| HyblockCapital Exchange Graph | https://hyblockcapital.com/chart | Exchange flow analysis |
| GoCharting (Orderflow) | https://gocharting.com/ | Orderflow charting reference |
| IBIT Borrow Rate | https://chartexchange.com/symbol/nasdaq-ibit/borrow-fee/ | ETF sentiment |

## Sentiment Indicators

| Risorsa | URL | Uso NautilusTrader |
|---------|-----|-------------------|
| Fear & Greed Index (CNN) | https://edition.cnn.com/markets/fear-and-greed | Sentiment regime |
| Scalpex Index | https://scalpexindex.com/app | Social sentiment |

## Educational / Research

| Risorsa | URL | Uso |
|---------|-----|-----|
| Quantopian Lectures (GitHub) | https://gist.github.com/ih2502mk/50d8f7feb614c8676383431b056f4291 | Quant trading fundamentals |
| Yardeni Research | https://www.yardeni.com/#MarketTechnicals | Market technicals |

---

## Potenziale Implementazione NautilusTrader

### Indicatori Macro-Based (da FRED/NY Fed)
```python
# Esempio: M2 Growth Rate Indicator
class M2GrowthIndicator(Indicator):
    """Track M2 money supply growth for liquidity regime detection."""
    def __init__(self, fred_api_key: str):
        # Fetch M2 data from FRED API
        # Calculate YoY growth rate
        # Signal: >10% = expansionary, <5% = contractionary
```

### On-Chain Signals (da CryptoQuant/CoinGlass)
```python
# Esempio: Taker Buy/Sell Ratio Strategy
class TakerRatioStrategy(Strategy):
    """Trade based on aggregated taker buy/sell ratio."""
    # API: CryptoQuant (richiede subscription)
    # Signal: Ratio > 1.1 = bullish pressure
    # Signal: Ratio < 0.9 = bearish pressure
```

### Liquidation Zone Integration
- Già implementato: `LiquidationHeatMapIndicator` (da BigBeluga)
- Potenziale: Fetch real-time liquidation data da CoinGlass API

---

## API Richieste

| Servizio | API Disponibile | Costo |
|----------|-----------------|-------|
| FRED | Sì (gratuita) | Free |
| CoinGlass | Sì | Freemium |
| CryptoQuant | Sì | Paid |
| Coinalyze | Sì | Freemium |
| LookIntoBitcoin | No API pubblica | - |

---

*Generato: 2026-01-02*
*Fonte: Chrome Bookmarks (~500 bookmark analizzati)*
