# NautilusTrader - #bybit

**Period:** Last 90 days
**Messages:** 25
**Last updated:** 2026-01-07 01:29:50

---

#### [2025-10-25 07:03:11] @cjdsellers

@everyone 🚀 **Call for Testing: Bybit Adapter Rust Port**

The Bybit adapter has been fully ported to Rust (with a thin Python layer for the legacy system like BitMEX and OKX) is available from the `rust-bybit` branch **and is ready for community testing!**
This brings significant performance and reliability improvements.

📦 Branch: **rust-bybit**

```
git checkout rust-bybit
make build-debug
```

✨ **What's New**
- Full Rust implementation of HTTP and WebSocket clients
- Option support - trade Bybit options alongside SPOT/LINEAR/INVERSE
- Cleaner architecture - WebSocket-based order routing (no HTTP/WS toggle)
- Better performance - Native Rust HTTP client with built-in retry logic
- Simplified configuration - Removed now redundant options when we transitioned from HTTP to the WS trade API

🔧 **Breaking Changes**
- Removed `use_ws_trade_api` - Orders now always use WebSocket (better performance)
- Changed `from nautilus_trader.adapters.bybit import get_bybit_http_client` to  `from nautilus_trader.adapters.bybit import get_cached_bybit_http_client`

🧪 **What to Test**

**High Priority**
- Option trading - Submit/modify/cancel option orders
- Multi-product configs - Mix SPOT + LINEAR + OPTION
- WebSocket stability - Long-running connections (24h+)
- Order execution - All order types across all products
- Account state - Balance updates, position tracking

**Standard Testing**
- Data streaming (orderbook deltas, trades, quotes, bars)
- Instrument provider (loading instruments for all products)
- Historical data requests
 - Reconnection handling
- Error handling and retries

**Configuration Testing**
- Single product type (SPOT, LINEAR, INVERSE, OPTION)
- Mixed product types (SPOT, LINEAR, OPTION)
- Testnet vs mainnet

🐛 **Reporting issues**

 Please report any issues found straight to this channel for fast turn around!

🙏** Thank You!**

Your testing helps ensure a smooth transition to a production release. All feedback welcome - from "works perfectly" to "broke everything" - it all helps!

**Target merge:** Post the next release and once we've received sufficient feedback

---

#### [2025-10-26 03:02:11] @cjdsellers

Some important updates were just pushed to the `rust-bybit` branch that fix post-only rejects

---

#### [2025-10-27 05:01:18] @joker06326

In new release, when I get my position from wallet  in spot margin mode, the debt is removed automatically, right?

---

#### [2025-10-27 07:34:36] @cjdsellers

Hey <@1162973750787051560> 
That is correct `walletBalance - spotBorrow = actual_balance`. This should be consistent for both the current `develop` Python-based version and the Rust-based version on `rust-bybit`

---

#### [2025-10-29 04:39:13] @cjdsellers

⚠️ 🦀 ** Bybit port to Rust landed on develop branch** 🛬 

After consulting with some Bybit power users, and in the interests of progress - the Bybit Rust port has now landed on `develop` branch.

Theoretically there should be no breaking changes other than the removal of the `use_ws_trade_api` config option toggle (redundant now that we always use the WebSocket trade API).

Please report any issues as they come up to this channel and we'll address them promptly!

---

#### [2025-11-28 19:56:02] @dxwil

Hey, when using the bybit integration, my stop market order gets instantly filled (I'm trying to create a stop-loss).

Edit: It doesn't matter if I set the stop market order trigger price to be above or below the current price, it still triggers on the same bar regardless.

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/1151424136283947028/1444054248324071625/message.txt?ex=695eba52&is=695d68d2&hm=dceb86215bb16ae1c6eda3f08f01a91ccc4eee26becee2cdb5a2200a861050bd&)

---

#### [2025-12-04 11:28:08] @violet.250

hey anyone know if bybit exection support on_order callback

---

#### [2025-12-05 06:35:10] @cjdsellers

Hey <@574471770720043010> 

Looking at your logs, the stop BUY was set at trigger 91101.00 when price was ~91117.80. A STOP BUY triggers when price is at or above the trigger - since 91117.80 >= 91101.00, it triggers immediately. That's expected behavior.

For a SHORT position stop-loss, set the trigger above your entry (e.g., 91200.00)

Are you currently using the released Python-based Bybit adapter, or development wheels Rust-based?

---

#### [2025-12-05 06:38:32] @cjdsellers

Hey <@1405497295683846165> if you're referring to the `on_order_event` handler then it's agnostic to a specific adapter or environment context - so should work backtest and live for all integrations

---

#### [2025-12-06 16:24:48] @dxwil

I later looked through the source code and noticed that the specific "stop-loss" part was modified in the development wheel (Rust-based). So I tried with that and without changing any of my code, it placed the stop-loss order correctly.

---

#### [2025-12-06 16:30:42] @dxwil

Another thing that I noticed in the development build, is that when I request_bars, it returns all full closed bars correctly except the last bar returned is the current bar that has not yet closed. When trading based on bars, I personally only care about bars that have fully closed, and this behaviour is messing with the indicators, so I don't know if this is expected behaviour or not. (In the logs, the time is the open of the bar) 

```
2025-12-06T16:19:39.587006000Z [INFO] TESTER-001.DistanceStrategy: Received historical bar: BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL, time=2025-12-06T16:17:00+00:00, O=89870.30, H=89883.60, L=89844.60, C=89872.80
2025-12-06T16:19:39.587052000Z [INFO] TESTER-001.DistanceStrategy: Received historical bar: BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL, time=2025-12-06T16:18:00+00:00, O=89872.80, H=89881.30, L=89846.30, C=89846.30
2025-12-06T16:19:39.587100000Z [INFO] TESTER-001.DistanceStrategy: Received historical bar: BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL, time=2025-12-06T16:19:00+00:00, O=89846.30, H=89897.00, L=89844.70, C=89881.00
2025-12-06T16:19:39.587177000Z [INFO] TESTER-001.DistanceStrategy: Received <Bar[386]> data for BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL
2025-12-06T16:20:00.468758000Z [INFO] TESTER-001.DistanceStrategy: Received bar: BTCUSDT-LINEAR.BYBIT-1-MINUTE-LAST-EXTERNAL, time=2025-12-06T16:19:00+00:00, O=89846.30, H=89897.00, L=89844.70, C=89871.40
```

---

#### [2025-12-07 02:59:11] @cjdsellers

Hi <@574471770720043010> thanks for the report on this. Should now be fixed and available soon in latest development wheels https://github.com/nautechsystems/nautilus_trader/commit/a15a0f295d0b3f4856066c7290a92045ae047267

**Links:**
- Fix Bybit historical bars requests partial bar filtering · nautech...

---

#### [2025-12-07 13:16:30] @violet.250

Thanks for your answer you are right

---

#### [2025-12-09 06:06:01] @lukeg_38673

<@224557998284996618>  <@757548402689966131> was positionIdx for hedge mode  included in the Rust new Bybit adapter? Or is it still something that needs to be implemented?

---

#### [2025-12-11 05:33:50] @gz00000

I'm not entirely sure either. Might need to check the code to confirm.

---

#### [2025-12-11 07:52:45] @_davidlin

Partially - the infrastructure (enum, field) exists but is NOT wired up. The  submit_order() function does not set position_idx, so hedge mode orders cannot currently be placed.

---

#### [2025-12-11 07:53:57] @_davidlin

- **Path**: `nautilus_trader/crates/adapters/bybit/src/http/client.rs`
- **Lines**: 1920–1949 of 3761

---

#### [2025-12-11 07:54:26] @_davidlin

Missing for Hedge Mode:
No parameter for position mode - Cannot specify:
- One-way mode (positionIdx=0)
- Long hedge (positionIdx=1)
- Short hedge (positionIdx=2)

---

#### [2025-12-11 07:55:00] @_davidlin

The current implementation only supports basic market/limit orders with no hedge mode, no stop orders, and no TP/SL.

---

#### [2025-12-20 18:25:14] @axelch97

Hi,
Bellow you will find details about a bug found inthe bybit adapter code.

Bug Report: Bybit WebSocket Bar Timestamps Not Respecting bars_timestamp_on_close Configuration

Summary
WebSocket bar data from the Bybit adapter does not respect the bars_timestamp_on_close configuration option, causing a 1-bar timestamp offset between WebSocket-delivered bars and HTTP-requested bars.

Affected Component
nautilus_trader/adapters/bybit/data.py - BybitDataClient

Severity
High - Causes data inconsistency that affects backtesting accuracy and indicator calculations.

Environment
NautilusTrader version: Latest (as of Dec 2025)
Exchange: Bybit (Linear perpetuals)
Python: 3.11+

Problem Description
Expected Behavior
When bars_timestamp_on_close=True (the default), all bars should have ts_event set to the bar's CLOSE time. For example, a 1-minute bar spanning 16:33:00-16:34:00 should have ts_event=16:34:00.
This should apply consistently to:
Bars requested via HTTP (request_bars)
Bars received via WebSocket subscription (subscribe_bars)

Actual Behavior
HTTP bars: Correctly use CLOSE timestamps (the timestamp_on_close parameter is passed to request_bars)
WebSocket bars: Use OPEN timestamps (the configuration is NOT applied)
This creates a 1-bar offset where WebSocket bars have ts_event one bar duration earlier than HTTP bars for the same OHLCV data.
Evidence

Comparing bar data from the same instrument at the same moment:
Source    ts_event    Open Price    Expected ts_event
HTTP Bar    16:34:00    1.9286    16:34:00 ✓
WebSocket Bar    16:33:00    1.9286    16:34:00 ✗
The WebSocket bar has the same OHLCV data but timestamp is 1 minute earlier.

---

#### [2025-12-20 18:27:30] @axelch97

Hi, <@757548402689966131> More details about the bybit adapter bug  here

**Attachments:**
- [IMG-20251220-WA0003.jpg](https://cdn.discordapp.com/attachments/1151424136283947028/1452004501702840513/IMG-20251220-WA0003.jpg?ex=695ea592&is=695d5412&hm=379339f9fcbde4baf82ff19a4806833e23c18ff915363bb89addbcc8499fd423&)

---

#### [2025-12-21 23:41:40] @dxwil

I'm looking into how to add this now but need a suggestion. To set the positionIdx parameter, we need to know the order side and position mode. The former is already passed as a parameter to the `submit_order` function, so we only need to figure out if the order is hedged or not. But here I see 2 ways to go about it: 1. Figure this out in the http client itself (maybe make an api call or save a variable, don't know yet); 2. Pass `is_hedged` or similar through `params` of `submit_order` function (like how `'is_leverage` is done now). So my question, which way would be more correct for the architure? Then I can definitely implement it.

---

#### [2025-12-21 23:43:04] @lukeg_38673

Yeah I solved it using the same approach as is_leverage. Been testing it since I mentioned it. I can push a PR up with the change for you to use.

---

#### [2025-12-22 08:15:46] @dxwil

That would be great

---

#### [2025-12-22 22:26:30] @cjdsellers

Hey <@136668228700078081> 
Thanks for the detailed report. Bybit timestamp on open by default, so we just needed to be passing through the `bars_timestamp_on_close` config to the websocket - now fixed:

https://github.com/nautechsystems/nautilus_trader/commit/2a505d661c95e72bc444fc0e4181b50b9f5aba8e

**Links:**
- Fix Bybit WebSocket bars to respect timestamp_on_close config · na...

---
