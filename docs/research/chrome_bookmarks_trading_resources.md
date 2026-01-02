# Chrome Bookmarks - Trading Resources Ranked

**Estratto**: 2026-01-02
**Bookmark analizzati**: ~800+
**Focus**: Risorse implementabili in NautilusTrader

---

## TIER S - Implementazione Immediata (ROI Altissimo)

Risorse con codice pronto o API dirette per NautilusTrader.

### S1. GitHub Repositories - Trading Systems

| # | Risorsa | URL | Perché TIER S |
|---|---------|-----|---------------|
| 1 | **hftbacktest** | https://github.com/nkaz001/hftbacktest | HFT backtest con orderbook L2, latency modeling, Python/Numba |
| 2 | **Awesome-Quant-ML-Trading** | https://github.com/grananqvist/Awesome-Quant-Machine-Learning-Trading | Curated list ML trading resources |
| 3 | **ML Algorithmic Trading 2nd Ed** | https://github.com/PacktPublishing/Machine-Learning-for-Algorithmic-Trading-Second-Edition | Codice completo libro Jansen |
| 4 | **awesome-quant** | https://github.com/wilsonfreitas/awesome-quant | 500+ quant resources |
| 5 | **financial-machine-learning** | https://github.com/firmai/financial-machine-learning | Practical ML finance tools |
| 6 | **trading-momentum-transformer** | https://github.com/kieranjwood/trading-momentum-transformer | Paper implementation + code |
| 7 | **pandas-ta** | https://github.com/twopirllc/pandas-ta | 130+ indicators, vectorized |
| 8 | **vectorbt** | https://vectorbt.dev/ | Fast backtesting, portfolio optimization |
| 9 | **mlfinlab (Hudson Thames)** | https://github.com/mnewls/MLFINLAB | AFML implementations |
| 10 | **ccxt orderbooks** | https://github.com/ccxt/ccxt/blob/master/examples/py/async-fetch-many-orderbooks-continuously.py | Multi-exchange orderbook streaming |

### S2. Academic Papers - Implementabili

| # | Paper | URL | Alpha Potenziale |
|---|-------|-----|------------------|
| 1 | **Slow Momentum + Fast Reversion** | https://arxiv.org/abs/2105.13727 | Deep learning + changepoint detection |
| 2 | **Momentum Transformer** | https://arxiv.org/pdf/2112.08534.pdf | Transformer per momentum trading |
| 3 | **Modeling Momentum & Reversals** | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4064260 | SSRN strategy paper |
| 4 | **Well-Diversified Arbitrage** | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4873205 | Attentional Autoencoder |
| 5 | **Bitcoin Volatility Analysis** | https://www.researchgate.net/profile/Taisei_Kaizoji/publication/321827427 | Time series analysis |
| 6 | **VPIN HFT** | https://github.com/theopenstreet/VPIN_HFT | Volume-Synchronized PIN |
| 7 | **Alpha101 WorldQuant** | https://github.com/laox1ao/Alpha101-WorldQuant | 101 alpha factors |

### S3. Data APIs - Pronte all'uso

| # | Risorsa | URL | Dati Disponibili |
|---|---------|-----|------------------|
| 1 | **CoinGlass Liquidation Map** | https://www.coinglass.com/pro/futures/LiquidationMap | Liquidation zones (già usato!) |
| 2 | **CryptoQuant** | https://cryptoquant.com/asset/btc/chart/derivatives/taker-buy-sell-ratio | Taker ratio, OI, flows |
| 3 | **Coinalyze OI** | https://coinalyze.net/bitcoin/open-interest/ | Open Interest multi-exchange |
| 4 | **FRED API** | https://fred.stlouisfed.org/series/WM2NS | M2, macro indicators (FREE) |
| 5 | **Deribit Insights** | https://insights.deribit.com/ | Options analytics, skew |
| 6 | **Laevitas Options** | https://app.laevitas.ch/assets/options/skew-bf/BTC/DERIBIT | Skew, butterfly spreads |

---

## TIER A - Alta Priorità (Codice/Tutorial Dettagliati)

### A1. Orderflow & Market Microstructure

| # | Risorsa | URL | Contenuto |
|---|---------|-----|-----------|
| 1 | **Order Flow Imbalance Signal** | https://medium.com/@a.botsula/using-kalman-filters-to-derive-predictive-factors-from-limit-order-book-data-2242eef97d80 | Kalman + LOB |
| 2 | **LOB Imbalance Trading** | https://ariel-silahian.medium.com/leveraging-limit-order-book-imbalances-for-profitable-trading-6ce2952353ad | Imbalance strategy |
| 3 | **Limit-Order-Book-Imbalance** | https://github.com/shubham98r/Limit-Order-Book-Imbalance | VOI analysis notebook |
| 4 | **Order Book Analysis Crypto** | https://medium.com/intotheblock/order-book-analysis-for-crypto-assets-in-a-few-fascinating-metrics-bcc29130bc42 | Metrics explained |
| 5 | **Binance Orderbook Explorer** | https://tiao.io/post/exploring-the-binance-cryptocurrency-exchange-api-orderbook/ | Python tutorial |
| 6 | **LOBster** | https://github.com/Jeonghwan-Cheon/LOBster | LOB microstructure estimation |
| 7 | **Order Book Shape Analysis** | https://datasciencedrivein.medium.com/bitcoin-order-book-shape-analysis-dfc1495a6c7d | Shape metrics |

### A2. Volume Profile & Market Structure

| # | Risorsa | URL | Contenuto |
|---|---------|-----|-----------|
| 1 | **Composite Volume Profile** | https://www.ticinotrader.ch/composite-volume-profile-chartbook-for-intraday-trading/ | Intraday VP |
| 2 | **MarketDelta Footprint** | https://www.ticinotrader.ch/ | Footprint chartbook |
| 3 | **Volume Dots Sierra** | https://futures.io/sierra-chart/39271-volume-dots-sierra-chart-4.html | Volume visualization |
| 4 | **Volume Extension DepthHouse** | https://www.tradingview.com/script/JJ8S2NVt-Volume-Extension-DepthHouse/ | TradingView reference |

### A3. Machine Learning Trading

| # | Risorsa | URL | Contenuto |
|---|---------|-----|-----------|
| 1 | **ML for Trading (Udacity)** | https://www.udacity.com/course/machine-learning-for-trading--ud501 | FREE course |
| 2 | **Quantra ML/DL Finance** | https://quantra.quantinsti.com/learning-track/machine-learning-deep-learning-in-financial-markets | Comprehensive track |
| 3 | **AFML Notebooks** | https://github.com/peng3738/Selfstudy-note-for-advances-in-financial-machine-learning | De Prado book code |
| 4 | **Financial ML Bars** | https://towardsdatascience.com/financial-machine-learning-part-0-bars-745897d4e4ba | Time/Volume/Dollar bars |
| 5 | **Imbalance Bars** | https://towardsdatascience.com/information-driven-bars-for-financial-machine-learning-imbalance-bars-dda9233058f0 | Information-driven bars |
| 6 | **Meta-labeling Momentum** | https://medium.com/mlearning-ai/momentum-trading-use-machine-learning-to-boost-your-day-trading-skill-meta-labeling-509f11d10184 | Practical ML |
| 7 | **Lorentzian Classification** | https://www.tradingview.com/script/ (jdehorty) | ML indicator TradingView |

### A4. Regime Detection

| # | Risorsa | URL | Contenuto |
|---|---------|-----|-----------|
| 1 | **Two Sigma Regime Modeling** | https://www.twosigma.com/articles/a-machine-learning-approach-to-regime-modeling/ | ML regimes |
| 2 | **Market Regime Classification** | https://quantdare.com/classification-of-market-regimes/ | HMM, clustering |
| 3 | **LSEG Regime Detection** | https://developers.lseg.com/en/article-catalog/article/market-regime-detection | Statistical + ML |
| 4 | **Short Volatility Strategy** | https://medium.datadriveninvestor.com/mastering-market-regimes-a-sharpe-2-strategy-for-short-volatility-trading-c517482a1844 | Sharpe 2+ |

---

## TIER B - Media Priorità (Reference/Educational)

### B1. On-Chain Analytics

| # | Risorsa | URL | Uso |
|---|---------|-----|-----|
| 1 | **LookIntoBitcoin Charts** | https://www.lookintobitcoin.com/ | NUPL, NVT, Whale Shadows |
| 2 | **HODL Waves** | https://unchained.com/hodlwaves/ | Long-term holder behavior |
| 3 | **Power Law Oscillator** | https://stats.buybitcoinworldwide.com/power-law-oscillator/ | Valuation model |
| 4 | **IntoTheBlock** | https://app.intotheblock.com/ | On-chain metrics |
| 5 | **Metcalfe's Law UTXO** | https://charts.bitcoin.com/btc/chart/metcalfe-utxo | Network value |
| 6 | **Supply Shock (Woobull)** | https://woobull.com/quantifying-supply-shock/ | Intent quantification |

### B2. Macro Data

| # | Risorsa | URL | Uso |
|---|---------|-----|-----|
| 1 | **M2 Money Supply (FRED)** | https://fred.stlouisfed.org/series/WM2NS | Liquidity regime |
| 2 | **NY Fed Reverse Repo** | https://www.newyorkfed.org/markets/desk-operations/reverse-repo | Liquidity drain |
| 3 | **Treasury General Account** | https://en.macromicro.me/charts/34339/us-treasury-general-account | Fiscal liquidity |
| 4 | **Yardeni Research** | https://www.yardeni.com/ | Market technicals |
| 5 | **Chatham Swap Rates** | https://www.chathamfinancial.com/technology/us-market-rates | Interest rates |

### B3. Binance/Exchange Tools

| # | Risorsa | URL | Uso |
|---|---------|-----|-----|
| 1 | **binance-bulk-downloader** | https://github.com/aoki-h-jp/binance-bulk-downloader | Historical data |
| 2 | **bybit-bulk-downloader** | https://github.com/aoki-h-jp/bybit-bulk-downloader | Bybit data |
| 3 | **unicorn-binance-websocket** | https://unicorn-binance-websocket-api.docs.lucit.tech/ | WebSocket wrapper |
| 4 | **Liquidation Tracker** | https://github.com/juanlanuza/Liquidation-Tracker | SQLite + Flask |
| 5 | **Binance volatility bot** | https://github.com/CyberPunkMetalHead/Binance-volatility-trading-bot | Reference bot |

### B4. Options & Derivatives

| # | Risorsa | URL | Uso |
|---|---------|-----|-----|
| 1 | **Implied Volatility Analysis** | https://medium.com/@crisvelasquez/implied-volatility-analysis-for-insights-on-market-sentiment-525fef5daf03 | IV sentiment |
| 2 | **Options Greeks Python** | https://medium.com/@pavel.zapolskii/essentials-for-option-trading-with-python-implied-volatility-and-greeks-6c14ca5c88c0 | Greeks calc |
| 3 | **Deribit Analytics** | https://insights.deribit.com/industry/crypto-derivatives-analytics-report-week-8-2025/ | Weekly reports |

---

## TIER C - Reference (Educational/Background)

### C1. Courses & Books

| # | Risorsa | URL | Tipo |
|---|---------|-----|------|
| 1 | **Quantopian Lectures** | https://gist.github.com/ih2502mk/50d8f7feb614c8676383431b056f4291 | Quant fundamentals |
| 2 | **QuantInsti Algo Trading** | https://quantra.quantinsti.com/learning-track/algorithmic-trading-for-everyone | Complete track |
| 3 | **Coursera ML** | https://www.coursera.org/learn/machine-learning | Andrew Ng |
| 4 | **ML From Scratch** | https://github.com/eriklindernoren/ML-From-Scratch | NumPy implementations |
| 5 | **Math of ML (Berkeley)** | https://www.datasciencecentral.com/tutorial-the-math-of-machine-learning-berkeley-university/ | Foundations |

### C2. TradingView References

| # | Risorsa | URL | Uso |
|---|---------|-----|-----|
| 1 | **TD/VixFix/Momentum** | https://www.tradingview.com/script/XlaUdjIi | Multi-indicator |
| 2 | **Trend Following MAs** | https://www.tradingview.com/script/Vb8jW3I2 | LonesomeTheBlue |
| 3 | **Wyckoff Orderflow** | https://www.tradingview.com/chart/BTCUSD/1Ix7sUeu | Wyckoff + liquidity |
| 4 | **TradingShot Analysis** | https://www.tradingview.com/u/TradingShot/ | Long-term BTC |

### C3. Sentiment & Social

| # | Risorsa | URL | Uso |
|---|---------|-----|-----|
| 1 | **Fear & Greed Index** | https://alternative.me/crypto/fear-and-greed-index/ | Sentiment regime |
| 2 | **Scalpex Index** | https://scalpexindex.com/app | Social sentiment |
| 3 | **CNN Fear & Greed** | https://edition.cnn.com/markets/fear-and-greed | Traditional markets |

---

## Implementazione Prioritaria NautilusTrader

### Quick Wins (< 1 giorno)

```python
# 1. FRED M2 Indicator
from fredapi import Fred
fred = Fred(api_key='YOUR_KEY')
m2 = fred.get_series('WM2NS')
# Signal: YoY growth > 10% = expansionary regime

# 2. Fear & Greed Integration
import requests
fg = requests.get('https://api.alternative.me/fng/').json()
# Signal: < 25 = extreme fear (buy), > 75 = extreme greed (sell)

# 3. Liquidation Map (già fatto!)
# strategies/converted/liquidation_heatmap/
```

### Medium Effort (1-3 giorni)

```python
# 4. LOB Imbalance Indicator
# Ref: https://github.com/shubham98r/Limit-Order-Book-Imbalance
def calculate_voi(bid_qty, ask_qty, bid_price, ask_price):
    """Volume Order Imbalance"""
    return (bid_qty - ask_qty) / (bid_qty + ask_qty)

# 5. Regime Detection (HMM)
# Ref: https://quantdare.com/classification-of-market-regimes/
from hmmlearn import hmm
model = hmm.GaussianHMM(n_components=3)  # Bull/Bear/Neutral

# 6. VPIN (Volume-Synchronized PIN)
# Ref: https://github.com/theopenstreet/VPIN_HFT
```

### High Effort (1+ settimana)

```python
# 7. Momentum Transformer
# Ref: https://github.com/kieranjwood/trading-momentum-transformer
# Requires: PyTorch, training data

# 8. HFT Backtest Integration
# Ref: https://github.com/nkaz001/hftbacktest
# Requires: L2 orderbook data, latency modeling
```

---

## API Keys Necessarie

| Servizio | Costo | Priority |
|----------|-------|----------|
| FRED | FREE | S |
| CoinGlass | Freemium | S |
| CryptoQuant | Paid ($50+/mo) | A |
| Alternative.me | FREE | A |
| Coinalyze | Freemium | B |
| Deribit | FREE | B |

---

## Statistiche Finali

| Categoria | Bookmarks Trovati | Implementabili |
|-----------|-------------------|----------------|
| GitHub Repos | 45+ | 15 |
| Academic Papers | 12 | 7 |
| Data APIs | 20+ | 10 |
| ML/DL Resources | 35+ | 12 |
| Orderflow/Microstructure | 18 | 8 |
| On-Chain | 15 | 6 |
| **TOTALE UTILI** | **145+** | **58** |

---

*Generato: 2026-01-02*
*Fonte: Chrome Bookmarks (~800+ analizzati)*
*Focus: NautilusTrader implementation readiness*
