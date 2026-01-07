# NautilusTrader - #releases

**Period:** Last 90 days
**Messages:** 3
**Last updated:** 2026-01-07 01:29:59

---

#### [2025-10-27 04:19:19] @cjdsellers

@everyone **NautilusTrader v1.221.0 has been released!** 🦀🐍

See full release notes at: https://github.com/nautechsystems/nautilus_trader/releases/tag/v1.221.0

Hey everyone 👋

We’re pleased to bring you another massive NautilusTrader release with v1.221.0! This one comes loaded with significant new features, internal improvements and refinements, deeper exchange/adapter support, and also some important breaking changes - **so please review carefully before upgrading**.

**We continue to see growing traction in the community with more first time contributors joining in the development effort this cycle** 👏 this has helped accelerate development of the platform and iron out more of the rough edges.

🎇  **Notable enhancements**
- Support for `OrderBookDepth10` requests, thanks to <@965894631017578537> 
- Support for quotes from book deltas and depth updates, thanks to <@965894631017578537> 
- Added Renko bar support, thanks <@965894631017578537> 
- Added `subscribe_order_fills(...)` and `unsubscribe_order_fills(...)` for Actor
- Added Binance BBO `price_match` parameter support
- BitMEX adapter improvements: batch cancels, conditional and contingent orders, historical data requests
- OKX adapter improvements: spot margin support, conditional (algo) orders, demo accounts, batch cancels
- Bybit support for spot margin with spot position reporting
- Polymarket native market orders, IOC time in force, quote quantity support
- Interactive Brokers fixes and improvements (numerous)
- Significant improvements to internal error handling, core arithmetic ops hardening, FFI correctness on panics
- Caching of topic strings in the `ExecutionEngine` resulting in some good performance gains
- Ported all portfolio statistics to Rust (and removed the Python equivalents)
- Too many more to mention, see the _pages_ of enhancements and refinements in the release notes 😄 

📣 ** Breaking changes to call out**
- Removed `nautilus_trader.analysis.statistics subpackage` - all statistics are now implemented in Rust and must be imported from `nautilus_trader.analysis` (e.g., `from nautilus_trader.analysis import WinRate`)
- Removed partial bar functionality from bar aggregators and subscription APIs, thanks <@965894631017578537> 
- Polymarket execution client no longer accepts market BUY orders unless `quote_quantity=True`

🦀  **Rust port**
All of the groundwork has been laid for final wiring to start testing some of the Rust adapter ports (**including execution**), which is the goal for this next cycle! we are getting closer to the promised lands of pure Rust each month 📈. We are also in the final testing phase of the Bybit port to Rust!

🎉 **New integrations will begin soon**
The community will be pleased to know some exciting new integrations will be starting _soon_ (within the next 1-2 weeks). Huge effort has been put into standardizing foundational patterns and documentation to improve development efficiency, and this is set to continue.

📊 **Backtest visualization**
Some exciting developments for backtest visualization will be introduced later today! 👀

🙏 **Thank you**
Once again I would like to thank everyone who has taken the time to reach out with clear feedback and/or detailed bug/issue reports! This is a huge help for improving the quality of the platform, and achieving ever greater levels of stability and reliability. Thank you for your continued support on the journey as we grow this project!

I hope everyone has a great week of trading ahead! <:ferrisBased:920768834930094111>

**Links:**
- Release NautilusTrader 1.221.0 Beta · nautechsystems/nautilus_trader

---

#### [2026-01-07 00:51:38] @cjdsellers

@everyone **NautilusTrader v1.222.0 has been released!** 🦀🐍

See full release notes at: https://github.com/nautechsystems/nautilus_trader/releases/tag/v1.222.0

Hey everyone 👋

We’re pleased to finally bring you another **huge** NautilusTrader release with v1.222.0, assisted by a **record 35 total contributors**! This release comes *loaded* with significant new features, internal improvements/refinements, additional adapter features/support, and also some important breaking changes - so please review carefully before upgrading.

**We continue to see growing traction in the community with even more first time contributors joining in the development effort this cycle 👏 **

🎇  **Notable enhancements**
- Added support for Python 3.14
- Added Kraken integration adapter
- Added Cap'n Proto (`capnp`) serialization for efficient zero-copy data interchange
- Added initial backtest visualization tearsheets with plotly (per previous announcement - finally landed in a release)
- Added matching engine `liquidity_consumption` config option to track per-level consumption
- Added matching engine trade consumption tracking
- Added price protection support for market orders, thanks to @Antifrajz (GH)
- Added `PolymarketDataLoader` for loading historical data with docs and example
- Added Polymarket Gamma API support for instrument loading, thanks to <@210739600115630080> 
- Added OKX historical trades requests
- Introduced `PositionAdjusted` events for tracking quantity/PnL changes outside normal order fills

Too many more to mention, see the *pages* of enhancements and refinements in the release notes 😉 

A special thanks to <@965894631017578537> who has been progressing the platform in multiple data related areas, also improving multi-account support (pending review), and improving+fixing the IB adapter 👏 

📣  **Breaking changes to call out**
- Dropped support for Python 3.11
- Removed `prob_fill_on_stop` parameter from `FillModel` and `FillModelConfig` 
- Removed `use_ws_trade_api` config option from Bybit execution client (using WebSocket trade API only)
- Renamed `parse_instrument` to `parse_polymarket_instrument` in Polymarket adapter for clarity
- Renamed `ExecTesterConfig.enable_buys` to `enable_limit_buys`
- Renamed `ExecTesterConfig.enable_sells` to `enable_limit_sells`
- Changed `ParquetDataCatalog.register_data` to now treat `files=[]` as registering no files; pass `files=None` (default) to include all files
- Standardized data catalog directory naming: Order book data directory names now use plural forms to align with the Rust catalog and Tardis Machine conventions; this ensures data written by the Python `StreamingFeatherWriter` can be read by the Rust catalog

🦀  **Rust port**
We are *very* close to reaching parity with the legacy v1 system for live execution. You will notice pure Rust live node examples popping up for Binance Spot (SBE), OKX, Deribit, and more. We're still ironing out some rough edges with reconciliation and general system operation before we're comfortable making more noise about this - but we're getting _close_.

The natural next progression for the port will be focusing attention on backtesting (the final boss). Much of the machinery necessary has already been built out, and it will be a matter of some small redesigns to suit Rust idioms and final wiring + testing. As usual, too much variance to be giving concrete estimates, but I predict we're down to ~ single digit months now for the complete port to v2.

**Links:**
- Release NautilusTrader 1.222.0 Beta · nautechsystems/nautilus_trader

---

#### [2026-01-07 00:51:46] @cjdsellers

🎉 **New integrations** (all Rust-based with a Python API layer)
You may have noticed work on several new integration adapters, here is a quick summary of current status:
- **Architect AX Exchange** (perpetual futures on traditional assets): has begun, data side progressing nicely (still in `building` phase and not considered usable)
- **Binance Spot (SBE)**: data basically done, execution is progressing (still in `building` phase and not considered usable)
- **Binance Futures**: some groundwork laid, will be under the `binance_v2` namespace initially - will commence once spot and spot margin is done
- **Deribit**: has progressed nicely over the last several weeks thanks to <@660054559477071893> , we're moving into execution testing this week (still in `building` phase and not considered usable)
- **dYdX v4**: the new Cosmos-based chain with improved performance and reliability, we're moving into final execution testing _soon_ (still in `building` phase and not considered usable)
- **Hyperliquid**: final execution testing is in play, expect more progress and landing the final solutions over the next few weeks (still in `building` phase and not considered usable)
- **Kraken**: initial work completed and now in a `beta` testing phase. Users are invited to test and provide feedback in the <#1455317454313099469> channel 🐙 
- **Polymarket**: expect the port to Rust to start within the next few weeks 🔮

🌌 **Future developments**
We will soon be landing the **NautilusTrader Pro** user portal with an **MCP server** as the first product 🤖. This will come with a free tier (rate limited requests per day) to help users with code reviews, understanding concepts, finding examples, and generally developing and working with NautilusTrader. A **live trading dashboard** is also in development - **more details soon**.

📈 **Trending on GitHub**
We are again on the [trending front page of GitHub Rust projects](https://github.com/trending/rust?since=daily)!

🙏 ** Thank you**
Once again, I would like to thank everyone who has taken the time to curate PRs and reach out with clear feedback and/or detailed bug/issue reports! This is a huge help for improving the quality of the platform, and achieving ever greater levels of stability and reliability. Thank you for your continued support on the journey as we grow this project, lets gooo! 🚀 

I hope everyone has a great week of trading ahead! <:ferrisBased:920768834930094111> <a:ferrisWave:590685315161915392>

---
