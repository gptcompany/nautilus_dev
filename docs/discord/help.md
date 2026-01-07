# NautilusTrader - #help

**Period:** Last 90 days
**Messages:** 269
**Last updated:** 2026-01-07 01:29:30

---

#### [2025-10-09 09:15:31] @one_lpb

Hello !

I'm having a little issue with data loading. I have this code to load historical data before "live data" in backtesting but nothing is logged in my on_historical_data method... logs and code in .txt attached.

Thanks for the help !

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/924499913386102834/1425773664720261151/message.txt?ex=695eccf3&is=695d7b73&hm=ea9d67a5a850e5b34dff653ef817978b7c5105958020672e7b9a948b8b2b9738&)

---

#### [2025-10-09 09:19:33] @faysou.

Hi, you can look in the <#924498804835745853>  channel, I've sent yesterday links to examples. If you do by analogy you should be able to get it to work.

---

#### [2025-10-09 09:29:29] @one_lpb

Wow ok ! I'll take a look thank you !

---

#### [2025-10-09 09:50:47] @one_lpb

You don't have examples with low level API ? if not i'll try with high level API...

---

#### [2025-10-09 09:54:33] @one_lpb

You know what never mind i'll use high level, you convinced me in earlier comment "Personally I only use the high level API as it is a similar setup to live trading. Also it avoids developing things that wouldn't work in Live" 🙂

---

#### [2025-10-09 09:58:22] @faysou.

Yep

---

#### [2025-10-09 10:13:29] @one_lpb

Do you know why you are using request_aggregated_bars instead of simply request_bars ? because it works with request_aggregated_bars  and not request_bars. I'm using aggregation from TradeTicks

---

#### [2025-10-09 10:33:10] @one_lpb

Looks likes answers are there. request_bars must have already aggregated bars in catalog as request_aggregated_bars  cant do it on the fly.
And "Received <Bar[0]> data for unknown bar type" mean that request_bars didn't find any already aggregated bars in catalog.

Hope can help future dev with same error 🙂
Special thanks to <@965894631017578537>, help much appreciated

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793206624456764/image.png?ex=695edf26&is=695d8da6&hm=6bd7a7fe5e27d8f3d3cce3618b97e378f5215c0bcf64b706410201209a1f1d09&)
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793207010328698/image.png?ex=695edf26&is=695d8da6&hm=8456f62627882979fccf66b291aa5414764f140d5c1e00087b6a1efb3a54ea44&)
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793207433822299/image.png?ex=695edf26&is=695d8da6&hm=779dec61115fa0c0c6b206f5a456fb87da124f6243aee55e40c9d4191dac4659&)

---

#### [2025-10-09 11:08:57] @faysou.

The idea is to have external bars in the catalog and aggregater bars can be recomputed in nautilus

---

#### [2025-10-09 11:10:10] @faysou.

Even for before the start of a backtest or live, I worked on this a lot last year and am doing a PR for the currently to make it more general (event driven instead of imperative for aggregating historical data)

---

#### [2025-10-09 12:17:56] @ido3936

Hello, I've filed a new bug describing the remaining issues with reconciliation in the IB account - as the discussion was spilling onto other GH bugs <@757548402689966131> <@965894631017578537> 
https://github.com/nautechsystems/nautilus_trader/issues/3054

**Links:**
- [Interactive Brokers, Reconciliation] Flat positions not closed ent...

---

#### [2025-10-09 15:39:50] @one_lpb

Can we generate reports with high level API ? In doc I can only see engine.trader.generate_order_fills_report() engine.trader.generate_xxx() in low level API

---

#### [2025-10-10 07:25:51] @cjdsellers

Hi <@391133967056896001> 
It's possible to get a reference to the backtest nodes internal engines and then use that API you mentioned https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/backtest/node.py#L149.
There's about to be a large upgrade to backtest reporting and visualization (maybe next week).

---

#### [2025-10-10 07:58:37] @one_lpb

Wow that would be great ! Can’t wait ! Thanks you

---

#### [2025-10-10 13:54:10] @one_lpb

Is there a doc for strategy optimization ? Should we do it manually with a for loop of node.run() with different BacktestRunConfig ?

---

#### [2025-10-10 17:37:43] @faysou.

it's a question that often comes up, it's out of scope. https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md

---

#### [2025-10-11 19:31:27] @_minhyo

i did it 😄

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1426653445313532004/image.png?ex=695eb48f&is=695d630f&hm=bced450aab339dfffeabc540faf5eb4d7bcfe833b988e85707510119f50655e8&)

---

#### [2025-10-13 13:49:40] @dxwil

Hi, while backtesting, is it possible to directly pull data from the exchange (e.g. binance), I didn't find any examples doing that?

---

#### [2025-10-13 16:20:07] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/backtest/notebooks/databento_backtest_with_data_client.py

---

#### [2025-10-13 16:20:15] @faysou.

There's an example here with databento

---

#### [2025-10-13 16:20:55] @faysou.

I haven't tried with other market data clients, you would need to try and see if it works

---

#### [2025-10-13 16:26:28] @faysou.

if you try to understand how it works, it's super interesting

---

#### [2025-10-13 20:15:18] @jftrades1_

Hello everyone, i have the following question (v1.220.0): 
when executing trades (triggered after on_bar entry logic) i am wondering why my entry price does not equal the bar.close . I am using High Level API with default fill_model.
example:
bar ts: 1735963200000000000
bar high: 0.3485000
bar low: 0.2992300
bar close: 0.3120100
bar open: 0.3450100
order initalized ts: 1735963200000000000
order filled ts: 1735963200000000000
position opened ts: 1735963200000000000
avg_px_open=0.31644

-> same for exiting trades…

---

#### [2025-10-14 00:53:33] @fudgemin

RE GIL logging release, example strategies:

Is there a reason i need to add print statement or other GIL release logic to a strategy?  The examples provided, do not complete a full log in console, as they are provided in the source. I needed to update those, with additional print statement or buffer logic, in the on_bar methods. 

Doing so, resulted in a full run/completion of the engine, and its logs. Otherwise, the logs would not write all, but only partial. Both console and file. 

So gpt says its GIL release, and since logging is async. Using a print or other check, forces i/o, which gives immediate release. 

if there is a standard way to do this, please inform. Currently just flushing on n bar count.

---

#### [2025-10-14 22:39:15] @cjdsellers

Hi <@391823539034128397> 
Welcome, are you on Windows per chance?

---

#### [2025-10-14 22:40:09] @fudgemin

i am not.

---

#### [2025-10-14 22:43:22] @cjdsellers

Understood, it's a little unclear what you were trying to achieve there. It's not necessary to be handling GIL release yourself and if logs are truncated then that's a known issue on Windows which is why I asked

---

#### [2025-10-14 22:46:11] @fudgemin

yea i actually brought it up with a colleague of yours a few months back. It was reproducing. The only fix, is to add print statements or time.sleep checks. If the strategy is strictly using built in logger, it wont flush or release...or wont finish engine. it doesnt even dispose. It not just on examples. It happens across the entire engine. Just ran into it again, when reading instrument definitions. I dont know honestly

---

#### [2025-10-16 08:29:46] @oikoikoik14

CryptoOption problem

When attempting to write a CryptoOption instance to a ParquetDataCatalog, the Arrow serializer throws an error related to the option_kind field:

`ArrowInvalid: Could not convert 'CALL' with type str: tried to convert to uint8`


This happens even when the option_kind is passed as the OptionKind enum, suggesting the class internally converts it to a string or the schema expects a small integer (uint8) but receives a string.

---

#### [2025-10-16 08:32:09] @oikoikoik14

To reproduce this issue, the following code can be used

```
from decimal import Decimal
import pytz
import pandas as pd

from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoOption
from nautilus_trader.model.objects import Price, Quantity, Money
from nautilus_trader.model.currencies import BTC, USDT
from nautilus_trader.model.enums import OptionKind
from nautilus_trader.persistence.catalog.parquet import ParquetDataCatalog

start_ns = int(pd.Timestamp("2024-09-25T00:00:00", tz=pytz.UTC).value)
expiry_ns = int(pd.Timestamp("2024-09-25T08:00:00", tz=pytz.UTC).value)

instrument = CryptoOption(
    instrument_id=InstrumentId.from_str("BTCUSDT-250924-111500-C.BYBIT"),
    raw_symbol=Symbol("BTCUSDT-250924-111500-C"),
    underlying=BTC,
    quote_currency=USDT,
    settlement_currency=BTC,
    is_inverse=False,
    option_kind=OptionKind.CALL,          # <-- using enum, still fails
    strike_price=Price.from_str("111500"),
    activation_ns=start_ns,
    expiration_ns=expiry_ns,
    price_precision=1,
    size_precision=2,
    price_increment=Price.from_str("0.1"),
    size_increment=Quantity.from_str("0.01"),
    multiplier=Quantity.from_int(1),
    maker_fee=Decimal("0.002"),
    taker_fee=Decimal("0.003"),
    margin_init=Decimal("0"),
    margin_maint=Decimal("0"),
    max_quantity=Quantity.from_str("9000"),
    min_quantity=Quantity.from_int(1),
    min_notional=Money.from_str("10.00 USDT"),
    ts_event=0,
    ts_init=0,
)

catalog = ParquetDataCatalog.from_uri("path/to/catalog")
catalog.write_data([instrument])
```

Some behavior i have noticed is that 

*OptionContract works fine with OptionKind enums.

Using CryptoOption with fractional contracts (min_quantity < 1) is not compatible with the current lot_size=1 default.

This effectively blocks writing crypto options to the catalog or using them in backtests if they have fractional sizes.*

---

#### [2025-10-16 10:35:06] @cjdsellers

Hi <@401500931931373569> 
Thanks for the detailed report! I’ll fix this tomorrow

---

#### [2025-10-16 14:39:38] @one_lpb

Hello ! Is it true that bracket order on BacktestVenue are not working properly ? I mean I have bracket order with TP SL with OUO but only 5/10 contrats fills then resting 5 contracts are canceled...

---

#### [2025-10-16 14:40:25] @one_lpb



**Attachments:**
- [logs.rtf](https://cdn.discordapp.com/attachments/924499913386102834/1428392145982717953/logs.rtf?ex=695e7059&is=695d1ed9&hm=9da9265c7999832b10bd9b36843a3a59fe8e2af44b21d0df8f21dee222ef91ee&)

---

#### [2025-10-16 15:42:46] @one_lpb

I made some tests and it looks like that on TP (SELL LIMIT when LONG on futures) NT fill half of total position contracts and cancel  STOP_MARTKET and LIMIT orders, instead of continuing to reduce order sizes... Maybe there is something I didn't catch ?

---

#### [2025-10-16 15:49:47] @one_lpb



**Attachments:**
- [logs.rtf](https://cdn.discordapp.com/attachments/924499913386102834/1428409601749028885/logs.rtf?ex=695e809b&is=695d2f1b&hm=6fd514adfe4e3dd6e2ac69fd1ef89429edc58bb56822661557bd5f0ab045162f&)

---

#### [2025-10-16 16:41:17] @one_lpb

I changed my bracket order TP to MARKET_IF_TOUCHED and it looks like to work but I don't really get the difference with LIMIT...

---

#### [2025-10-17 10:26:53] @georgey5145

anybody know how subscribe_instrument() works? if i call it in on_start(), it always raises error 'NotImplementedError: implement the _subscribe_instrument coroutine', but other methods like subscribe_quote_ticks() does not

---

#### [2025-10-21 02:39:33] @aaron_g0130

"pip index versions nautilus-trader --index-url=https://packages.nautechsystems.io/simple
ERROR: No matching distribution found for nautilus-trader" Can some one help me with this error?

---

#### [2025-10-21 03:45:18] @cjdsellers

Hi <@1418078113161674900> unsure, maybe you don't have a platform compatible with any of the wheels?
```
pip index versions nautilus-trader --index-url=https://packages.nautechsystems.io/simple
WARNING: pip index is currently an experimental command. It may be removed/changed in a future release without prior warning.
nautilus-trader (1.221.0)
Available versions: 1.221.0, 1.220.0, 1.219.0, 1.218.0, 1.217.0, 1.216.0
```

---

#### [2025-10-21 04:03:31] @aaron_g0130

my platform is Python 3.13.9 on Ubuntu

---

#### [2025-10-21 06:31:46] @aaron_g0130

it seems my ubuntu version is not updated enough for dev version

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430081112419340308/image.png?ex=695ea692&is=695d5512&hm=9279e19c06c34772c03b243b313f0f5f331b8dbeacb2681dd13affdd47272326&)

---

#### [2025-10-21 06:56:59] @faysou.

Just build from source

---

#### [2025-10-21 08:21:34] @aaron_g0130

I upgrade ubuntu to 22.04, fixed this problem.thx

---

#### [2025-10-22 04:23:58] @jst0478

Is there something we have to enable/configure to get unrealized PnL in the backtest reports? I always just get a 'None' like this:

> 2025-10-22T03:49:03.589349037Z [INFO] BACKTESTER-001.BacktestEngine: Unrealized PnLs (included in totals):
> 2025-10-22T03:49:03.589420690Z [INFO] BACKTESTER-001.BacktestEngine: None

So I'm manually calculating it for now after a run completes

---

#### [2025-10-22 09:09:28] @cjdsellers

Hi <@296261099630755841> 
There should only be unrealized PnLs if you have open positions at the end of the backtest run, is this the case?

---

#### [2025-10-22 09:38:39] @georgey5145

can anyone help me with this error? i'm just running the example using default redis config, but when an order is submitted, this error occurs

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430490527274373182/image.png?ex=695ed25e&is=695d80de&hm=5808841482901e868ed523a254b27c9887b7c1fb7be919e3b7e5524e4b638dee&)

---

#### [2025-10-22 10:42:05] @jst0478

Yes, quite a few open positions at the end, according to the positions report. Not at my PC now but let me know if there's something I can do to help figure it out later

---

#### [2025-10-22 13:40:23] @dxwil

I need to backtest against data from a few years, when loading csv files that can easily be 100GB per year of data. Is there any way to stream data from e.g. Binance to backtest (BacktestEngine), or is downloading all of that data and loading it at once the only option?

---

#### [2025-10-22 15:44:39] @sandesh_2027

<#924499913386102834> im trying to to create a indian broker adapter, i observed a behaviour for REJECTED status orders , in  reports im not able to see venue_order_id. Is it expected or it should come. this i observed for mass reconciliation at startup.

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430582634265710592/image.png?ex=695e7f66&is=695d2de6&hm=c6431a596e097e5204b034a0681ff6061759bf00fc25280649eb99fa6484d7f3&)

---

#### [2025-10-23 07:08:15] @jst0478

I'll try to run it in debug mode, but my first thought is maybe there are no prices in the cache when using MBO data?  Am looking at this code to calculate unrealized pnl for reference:
https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/portfolio/portfolio.pyx#L1874

---

#### [2025-10-23 07:24:27] @faysou.

I think something similar to this needs to be added when using L3 https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/data/engine.pyx#L1803

---

#### [2025-10-23 07:25:19] @faysou.

ie. producing top of book bid and ask quotes

---

#### [2025-10-23 08:33:06] @faysou.

fyi, just did a PR for it

---

#### [2025-10-24 03:26:53] @jst0478

<@757548402689966131> , <@965894631017578537> 
I confirmed that turning on `emit_quotes_from_book` fixed the Unrealized PnLs line in the report (at least, I assume that's what fixed it - I haven't touched anything else).  Thank you~

It does have an impact on backtest performance, though I guess it can't be helped. L3 is a LOT of data...

Before:

> BACKTESTER-001.BacktestEngine: Run config ID:  ..snip...
> BACKTESTER-001.BacktestEngine: Run ID:         ..snip...
> BACKTESTER-001.BacktestEngine: Run started:    2025-10-24T03:05:56.877185000Z
> BACKTESTER-001.BacktestEngine: Run finished:   2025-10-24T03:09:26.788867000Z
> **BACKTESTER-001.BacktestEngine: Elapsed time:   0 days 00:03:29.911682**
> BACKTESTER-001.BacktestEngine: Backtest start: 2025-08-01T07:04:56.980761114Z
> BACKTESTER-001.BacktestEngine: Backtest end:   2025-10-20T23:57:01.111921735Z
> BACKTESTER-001.BacktestEngine: Backtest range: 80 days 16:52:04.131160621
> BACKTESTER-001.BacktestEngine: Iterations: 38_027_569
> BACKTESTER-001.BacktestEngine: Total events: 4
> BACKTESTER-001.BacktestEngine: Total orders: 2
> BACKTESTER-001.BacktestEngine: Total positions: 2

After:

> BACKTESTER-001.BacktestEngine: Run config ID:  ..snip...
> BACKTESTER-001.BacktestEngine: Run ID:         ..snip...
> BACKTESTER-001.BacktestEngine: Run started:    2025-10-24T03:14:26.568665000Z
> BACKTESTER-001.BacktestEngine: Run finished:   2025-10-24T03:19:42.839529000Z
> **BACKTESTER-001.BacktestEngine: Elapsed time:   0 days 00:05:16.270864**
> BACKTESTER-001.BacktestEngine: Backtest start: 2025-08-01T07:04:56.980761114Z
> BACKTESTER-001.BacktestEngine: Backtest end:   2025-10-20T23:57:01.111921735Z
> BACKTESTER-001.BacktestEngine: Backtest range: 80 days 16:52:04.131160621
> BACKTESTER-001.BacktestEngine: Iterations: 38_027_569
> BACKTESTER-001.BacktestEngine: Total events: 4
> BACKTESTER-001.BacktestEngine: Total orders: 2
> BACKTESTER-001.BacktestEngine: Total positions: 2

---

#### [2025-10-24 06:10:08] @faysou.

it could be useful to avoid having portfolio.pyx update on every quote but on a timer interval instead which is what's useful practically

---

#### [2025-10-24 06:10:38] @faysou.

I won't add this feature now, but if I was working on this, that's what I would do

---

#### [2025-10-24 17:43:14] @cgeneva

Hi, I try to store in cache unrealized PNLs at each on_bar triggered. 
That way, I can retrieve it once backtest is done and add it to account_report. I would like to create a complete equity curve.
How can i store a timeserie in bytes into the cache ? I must add this code in each strategy implementation : Is it a good way to implement that feature? Many thanks

---

#### [2025-10-25 02:47:53] @cjdsellers

Hi <@692775065586106378> 
There are `add` and `get` methods for the cache that allow you to store arbitrary bytes. But you might also be interested in the position snapshots that automatically capture position state (including unrealized PnL) at regular intervals. This
is configured through the `ExecutionEngineConfig`:

```python
  from nautilus_trader.config import ExecEngineConfig

  config = ExecEngineConfig(
      snapshot_positions=True,  # Enable position snapshots
      snapshot_positions_interval_secs=5.0,  # Take snapshots every 5 seconds
  )
```
I hope that helps!

---

#### [2025-10-25 09:33:54] @cgeneva

Hi, thank you for feedback. I am able to call position.unrealized_pnl(current_price) , use cache.add in the strategy and retrieve all unrealized pnls to construct equity curves at the end of the backtest. This is working but it forces me to add same code in each strategies. LiveExecEngineConfig seems ideal for live as it is inside engine. Does this same config exist for backtests ?

---

#### [2025-10-25 09:52:33] @cjdsellers

Hey <@692775065586106378> 
Yes, it's actually part of the `ExecEngineConfig` which is common to all environment contexts including backtests (because it uses a timer which is agnostic to the env context):
https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/execution/config.py#L45

**Links:**
- nautilus_trader/nautilus_trader/execution/config.py at develop · n...

---

#### [2025-10-25 10:25:47] @cgeneva

I see. But using the option snapshot_positions_interval_secs=1 sec seems unsuitable if my backtest runs in 2 sec. I am probably missing an important point here.

---

#### [2025-10-25 10:36:17] @cjdsellers

The timer would be simulated, so works the same way backtest and live relative to the passage of time

---

#### [2025-10-25 17:14:24] @cgeneva

I try to reproduce a simple case with the following code. Where do i find the list of position snapshots done every 86400 Sec (for daily bars) ?  I have added exec_engine_config and quotes. So i am expecting to find somewhere a list of snapshot where i can get unrealized pnl for each bars with open positions. May be with "engine.portfolio.unrealized_pnls(venue)" but it is empty.

**Attachments:**
- [simple_test_run.py](https://cdn.discordapp.com/attachments/924499913386102834/1431692384483410101/simple_test_run.py?ex=695e9470&is=695d42f0&hm=cfe8fbe41430449afc4c28f38231840e6fce99bbe410aa3666680188017cc781&)

---

#### [2025-10-27 04:02:19] @kib5546

Hi thanks for your work and it is amazing.

I am looking at bybit orderbook backtesting tutorial using `BacktestingNode`. 

it works fine but how do I see the report of my strategy including stats, trade history and its pnl 

is using `node.get_engine` the only way to see it?

---

#### [2025-10-27 14:04:43] @jst0478

I'm trying to get that latest dev version with visualization but it's not working for some reason:

> $ uv pip install nautilus_trader==1.222.0.dev20251027 --index-url=https://packages.nautechsystems.io/simple
> Resolved 15 packages in 3.96s
>   × Failed to download `nautilus-trader==1.222.0.dev20251027+11620`
>   ├─▶ Failed to extract archive:
>   │   nautilus_trader-1.222.0.dev20251027+11620-cp312-cp312-manylinux_2_35_x86_64.whl
>   ├─▶ I/O operation failed during extraction
>   ╰─▶ Failed to download distribution due to network timeout. Try increasing UV_HTTP_TIMEOUT (current
>       value: 30s).

It always gets stuck about half-way through downloading (the first 49 MiB happens quickly, then it just stops)

> Resolved 15 packages in 2.11s
> ⠇ Preparing packages... (0/1)
> nautilus-trader      ------------------------------ 49.12 MiB/98.09 MiB   

Then times out after 30 sec. I tried clearing the uv cache but it still doesn't work.

---

#### [2025-10-27 14:07:32] @jst0478

It also hangs at the same spot if I try to download the wheel from the browser at https://packages.nautechsystems.io/simple/nautilus-trader/index.html. Is there some way you can check if the wheel was created/uploaded properly and is complete?

---

#### [2025-10-27 14:09:35] @jst0478

The cp313 wheel downloads fine. Seems like it's just the cp312 wheel for manylinux that's broken

---

#### [2025-10-27 15:40:02] @eldineros_33574

Hi, quick question, how does the **Rust Decimal type** get exposed to Python through PyO3?
I see it being used in the Rust structs (e.g Quantity), but I can’t find where the conversion or wrapper is actually defined (e.g. the FromPyObject / IntoPy mapping).
Can you point me to the spot in the code where that’s handled?

---

#### [2025-10-27 16:33:08] @faysou.

you shouldn't use the pyo3 types for now, use the cython types. pyo3 types are for the next version of the library mainly in rust that is not operational yet.

---

#### [2025-10-27 20:56:23] @cjdsellers

Hi <@296261099630755841> 
I was able to download it and inspected OK, maybe network related? the github action would fail if the upload does not complete successfully (and all greens)

---

#### [2025-10-28 01:49:43] @jst0478

Yeah it works fine today 🤷‍♂️  Thanks~

---

#### [2025-10-28 16:27:38] @rgauny_74023

Hi all...i found a bug in NautilisTrader where i cant connect to my minio with datafusion:  Summary of Findings
Root cause: Nautilus Rust code registers the object store with s3://trademan-data (bucket-specific URL), but DataFusion expects s3:// (generic URL).
Evidence:
Rust pattern (s3://trademan-data): FAILS with "No suitable object store found"
Python pattern (s3://): WORKS and returns 194,968 rows
Nautilus Rust Code Location:
File: nautilus_trader/crates/persistence/src/backend/catalog.rs lines 946-948
Current (broken) code:
Fix Required:
Change line 946 to register with "s3://" instead of "s3://trademan-data"........Using NautilusTrader version 1.221.0

---

#### [2025-10-29 16:38:51] @one_lpb

How unique the TradeId has to be unique ? "The unique ID assigned to the trade entity once it is received or matched by the exchange or central counterparty."

It has to be unique for Nautilus OR by default unique because it comes from a venue so should be unique ? Can I create TradeTick with same id over different days, like if I put a counter as trade id and reset it every day

---

#### [2025-10-29 18:52:28] @faysou.

TraderId identifies a trading node or backtest node, there's only one TraderId per process. The idea being that in theory you could have several nodes/traders interacting with each other. It was confusing with me as well what this TraderId means. I don't think that TradeTick and trader id are related.

---

#### [2025-10-29 18:52:39] @faysou.

TradeTick is market data

---

#### [2025-10-29 18:59:51] @one_lpb

Hi <@965894631017578537> ! Each TradeTick has a TradeId 🙂 not talking about TraderId

---

#### [2025-10-29 19:00:07] @faysou.

Ah sorry

---

#### [2025-10-29 19:01:08] @faysou.

Not sure about that, I suppose you could find the answer by using an AI agent. Augment code used to be good but it's getting overly expensive.

---

#### [2025-10-30 01:16:49] @sandesh_2027

<#924506736927334400> 

can we subscribe to external orders? using actors or strategies. 

will this work? 
from nautilus_trader.common.actor import Actor  
from nautilus_trader.config import ActorConfig  
from nautilus_trader.model.events import OrderEvent  
  
class OrderSpreadGuardConfig(ActorConfig):  
    spread_threshold: float  

  
class OrderSpreadGuardActor(Actor):  # Use Actor, not Strategy  
    def __init__(self, config: OrderSpreadGuardConfig):  
        super().__init__(config)  
          
    def on_start(self):  
        self.msgbus.subscribe(topic="events.order.*", handler=self.on_order_event)  
          
    def on_order_event(self, event: OrderEvent):  
        self.log.info(f"Order event: {type(event).__name__}")


im tried but its not working, only internal orders events im able to see, for external im able to see only OSR.

**Attachments:**
- [logs.txt](https://cdn.discordapp.com/attachments/924499913386102834/1433263344059551875/logs.txt?ex=695f0581&is=695db401&hm=1c594840f1c5bf682959094bbe05256b9c857cf3cb96cf522ddc7045ee673a0e&)

---

#### [2025-10-30 18:23:15] @kvg1

2025-10-30T18:14:55.684776224Z [INFO] TESTER-001.DYDXInstrumentProvider: Loading all instruments...
2025-10-30T18:15:03.542972920Z [INFO] TESTER-001.DYDXInstrumentProvider: Loaded 2 instruments
2025-10-30T18:15:03.542978930Z [INFO] TESTER-001.DYDXInstrumentProvider: Initialized instruments
2025-10-30T18:15:03.543031400Z [INFO] TESTER-001.DataClient-DYDX: Initializing websocket connection
2025-10-30T18:15:05.484219692Z [INFO] TESTER-001.DYDXWebsocketClient: Connected to wss://indexer.dydx.trade/v4/ws
2025-10-30T18:15:05.484381702Z [INFO] TESTER-001.DataClient-DYDX: Websocket connected
2025-10-30T18:15:05.484512392Z [INFO] TESTER-001.DataClient-DYDX: Connected
2025-10-30T18:15:06.070151281Z [INFO] TESTER-001.DYDXInstrumentProvider: Loaded 284 instruments

Dydx instrument provider ignores config load_all False
Firstly it loads only 2, but later - more

---

#### [2025-11-01 00:16:20] @javdu10

Hello there, while looking at the types and docs, I could only find on how to get the cumulative quantity (book.get_quantity_for_price), but I would like to get the exact quantity of a level

is looping the only way ?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1433972894240870501/image.png?ex=695ef753&is=695da5d3&hm=12a3c5fc31dc610f0a603c5d5bbe1dbf3d72d3bed40d0796f9e81434a2f1e8b1&)

---

#### [2025-11-01 15:18:07] @jonathanbytesio

pip install -U nautilus_trader

---

#### [2025-11-01 15:18:17] @jonathanbytesio

hint: This usually indicates a problem with the package or the build environment.

---

#### [2025-11-01 15:18:25] @jonathanbytesio

Someone know this issue?

---

#### [2025-11-02 10:56:14] @sinaatra

Hey anyone has an idea of why isn't my callback called?
```
# Strategy
class IntegrationTestStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.logger = Logger("IntegrationTestStrategy")

    def on_start(self) -> None:
        self.request_instruments(Venue("Aster"), callback=self.on_instruments)

    def on_instruments(self, request_id: UUID4) -> None:
        self.logger.info(f"Instruments loaded, request ID: {request_id}")

# Market Data Client
    async def _request_instruments(self, command: RequestInstruments) -> None:
        await self._instrument_provider.load_all_async()

# Instrument Provider
 async def load_all_async(self, filters: dict | None = None) -> None:
        ...
        self.add(instrument) # This is called for sure
        ...
        return
```
Thanks in advance

---

#### [2025-11-02 11:37:43] @sinaatra

Found the answer for the next ones
I had to call `self._handle_instruments_py(self.venue, instruments, request.id, request.start, request.end, request.params)`
Inside MarketDataClient to resolve the request
Then in my Strategy I could call `self.instruments = self.cache.instruments(venue=self.venue)`

---

#### [2025-11-03 02:29:17] @jonathanbytesio

What's the strategy you are working on now

---

#### [2025-11-03 14:48:35] @one_lpb

Hello ! 

Does Nautilus can use  OHLCV bars while no open positions and use the Trades only to manage positions. This way it prevent going through all the millions Trades on each run?

---

#### [2025-11-03 20:39:04] @sinaatra

i am just getting the field ready for some experimental strategies, probably arbitrage, also wanna plug some AI

---

#### [2025-11-04 08:00:57] @jonathanbytesio

Good idea

---

#### [2025-11-04 08:01:27] @jonathanbytesio

Have the exact plan or thinking for now

---

#### [2025-11-04 09:01:05] @jonathanbytesio

cannot import name 'PolymarketDataLoader' from 'nautilus_trader.adapters.polymarket'

---

#### [2025-11-04 09:01:19] @jonathanbytesio

Someone know this issue when importing 

from nautilus_trader.adapters.polymarket import PolymarketDataLoader

---

#### [2025-11-04 09:02:47] @cjdsellers

Hi <@756122725495472138> 
This should help https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/backtest/polymarket_simple_quoter.py#L39
`from nautilus_trader.adapters.polymarket.loaders import PolymarketDataLoader`

I'll update the docs and also add a re-export so it works without the nested `loaders`

---

#### [2025-11-04 09:06:50] @jonathanbytesio

Ohhh. it's in the loader.py Class now, I tried whole day to handle this

---

#### [2025-11-04 09:07:05] @jonathanbytesio

i thought It's problem from my UV env

---

#### [2025-11-04 09:07:59] @jonathanbytesio

HI <@757548402689966131> I sending friend request, I saw your message before

---

#### [2025-11-04 09:40:42] @jonathanbytesio



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435202086034870292/image.png?ex=695ed2da&is=695d815a&hm=798a0198796a81cc4309d1e611a7edff9b67f613f17e3ce738fdf406f69138f9&)

---

#### [2025-11-04 10:18:42] @cjdsellers

It hasn’t been released yet, the docs are on nightly. You could install a recent development wheel though

---

#### [2025-11-04 10:22:07] @jonathanbytesio

I see

---

#### [2025-11-04 10:22:12] @jonathanbytesio

I m testing now

---

#### [2025-11-04 10:22:24] @jonathanbytesio



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435212583664615456/image.png?ex=695edca0&is=695d8b20&hm=11619b8d83f5219ef578e73e45d5bfe11a1b45479605d4bcf2a2f1b84a26260f&)

---

#### [2025-11-04 10:23:36] @jonathanbytesio

And I ran the polymarket_data_tester.py on jupyterlab

---

#### [2025-11-04 10:23:44] @jonathanbytesio

It suddenly closed

---

#### [2025-11-04 11:39:49] @jonathanbytesio



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435232063019028511/image.png?ex=695eeec5&is=695d9d45&hm=020809b1758dd9c986eaa185d8fd90d1df9dc953ca58f786ee232090980e6f99&)

---

#### [2025-11-04 12:05:52] @jonathanbytesio

from nautilus_trader.cache.cache import Cache
  File "nautilus_trader/cache/cache.pyx", line 1, in init nautilus_trader.cache.cache
KeyError: '__reduce_cython__'

---

#### [2025-11-04 21:23:55] @joejoe404

Someone got this crash?

... catalog = ParquetDataCatalog("./catalog/")
... 
... catalog_path = Path("./catalog/")
... 
... catalog.order_book_deltas()[0]
... 

thread 'tokio-runtime-worker' panicked at crates/model/src/types/price.rs:193:14:
Condition failed: `precision` must be 0 when `raw` is PRICE_UNDEF

Stack backtrace:
   0: _PyInit_core
stack backtrace:
note: Some details are omitted, run with `RUST_BACKTRACE=full` for a verbose backtrace.

thread 'tokio-runtime-worker' panicked at crates/model/src/types/price.rs:193:14:
Condition failed: `precision` must be 0 when `raw` is PRICE_UNDEF

Stack backtrace:
   0: _PyInit_core
fish: Job 1, 'python3.13' terminated by signal SIGABRT (Abort)

I'm trying to figure out how to solve it

---

#### [2025-11-04 23:52:16] @cjdsellers

Hey <@756122725495472138> 
That Polymarket backtest example is now updated with cleaner imports and matches the example script: https://nautilustrader.io/docs/nightly/integrations/polymarket#complete-backtest-example
It's not recommended to run a live trading node in a jupyter notebook, there can be event loop issues. Added a note to the `live.md` although will reduce that admonition level from "danger" to warning: https://nautilustrader.io/docs/nightly/concepts/live/

---

#### [2025-11-04 23:52:42] @cjdsellers

Do you have any further context or information on when this happens?

---

#### [2025-11-04 23:53:51] @cjdsellers

Hi <@789226697052258304> 
Thanks for the report. That's an invariant where we expect an undefined price to have a precision of zero, anything else suggests a parsing issue or something which shouldn't be happening - so it fails fast with a panic. Do you have any further information on when this occurred, currently not enough information to debug this

---

#### [2025-11-05 00:01:15] @joejoe404

Yep, so basically:
Using latest version with Python;

1. I’ve loaded the my past 3 days MBO data with the databento loader into the parquet catalog.

2. Then every operation I’m doing it is just panicking for some reason..

For example

---

#### [2025-11-05 00:01:17] @joejoe404

```python
from pathlib import Path

DATA_DIR = Path("./daily/")
trade_files = sorted(DATA_DIR.glob("glbx-mdp3-*.mbo.dbn.zst"))

for f in trade_files:
    trades_iter = loader.from_dbn_file(
        path=f,
        as_legacy_cython=False,      # trades are fine with Rust types
        use_exchange_as_venue=False, # must match definitions
    )
    catalog.write_data(trades_iter)
    print("Wrote mbo from:", f.name)
```


```python
catalog = ParquetDataCatalog("./catalog/")

catalog_path = Path("./catalog/")

catalog.order_book_deltas()[0]
```

PANICKED!!!!!

---

#### [2025-11-05 00:02:12] @joejoe404

not only 
> catalog.order_book_deltas()[0]

almost every function crushing it 🙁

---

#### [2025-11-05 00:06:14] @joejoe404

Lmk if you need more info

---

#### [2025-11-05 02:54:25] @jonathanbytesio

I see, you updated this, but it's in nightly version, right?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435462231717580863/image.png?ex=695e73a1&is=695d2221&hm=92c7eec9b66171ee28ddcb1bd6a55c0c3d6db6df0f5e1cb51bc90ee2d2aea64a&)

---

#### [2025-11-05 02:58:36] @jonathanbytesio

Actually, I am trying to market maker on polymarket, we are investment company, I am trying to find more examples to help me understand how to implement my strategy

---

#### [2025-11-05 03:09:53] @jonathanbytesio

Yeah , I have ran on terminal instead of jupyter yesterday since I found the loop issue

---

#### [2025-11-05 03:15:21] @jonathanbytesio

/nautilus_trader/adapters/polymarket/scripts/list_updown_markets.py
Fetching active Polymarket markets...

Found 200 total active markets

================================================================================
BTC UPDOWN MARKETS (0 found)
================================================================================

================================================================================
ETH UPDOWN MARKETS (0 found)
================================================================================

This script seems also need to update

---

#### [2025-11-05 03:22:13] @jonathanbytesio

2025-11-05T03:20:49.683243000Z [WARN] TESTER-001.RiskEngine: SubmitOrder for O-20251105-032049-001-000-421 DENIED: NOTIONAL_EXCEEDS_FREE_BALANCE: free=0.000000 USDC.e, balance_impact=-1.150000 USDC.e
2025-11-05T03:20:49.683382000Z [WARN] TESTER-001.ExecTester: <--[EVT] OrderDenied(instrument_id=0x44dce36f5fe5d8a1554d402d5705eb5a837e8785a003c71bb92875a8c553d40b-110721708563829309626441524339337100777360025073350502319412072033397801403428.POLYMARKET, client_order_id=O-20251105-032049-001-000-421, reason='NOTIONAL_EXCEEDS_FREE_BALANCE: free=0.000000 USDC.e, balance_impact=-1.150000 USDC.e')


And I ran the polymarket_exec_tester.py, it showed this error

---

#### [2025-11-05 03:22:39] @jonathanbytesio

I have set allowances and deposited USDC on polygon also have POL

---

#### [2025-11-05 03:23:31] @cjdsellers

<@756122725495472138> Thanks for all the feedback, this is useful. Any chance we could move this into a thread in the <#1332664677041442816> channel? then we can keep track of it and won't interleave with other users messaging in this channel 🙏 https://discord.com/channels/924497682343550976/1435469919612571758 (we could also copy into that thread if you like as well, up to you)

---

#### [2025-11-05 07:08:20] @jst0478

As a next step I would try inspecting your catalog with a parquet file viewer and make sure the imported data looks good.  I'm using Databento MBO data as well and have no problem, but I'm using equities data

---

#### [2025-11-05 17:29:02] @joejoe404

do you know what I should I look for? Undefined prices?

---

#### [2025-11-05 17:32:41] @joejoe404

The data gets loaded, then boom...

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435683255675519128/image.png?ex=695e98b9&is=695d4739&hm=2a3bceddd0a9b7313cd49bd83a18b461fdd217f31ca8bf14cec6a7f38f3ca089&)

---

#### [2025-11-05 18:28:19] @joejoe404

breaks here

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435697255490519051/image.png?ex=695ea5c3&is=695d5443&hm=9687732667010f0e1b98b65493f149c77b778e1f7ba28f8d68f5b5f6c2c60e56&)

---

#### [2025-11-05 18:32:00] @joejoe404

Got it friends, the issue was on the 29/10 NQ MBO file... just crashed everything... why there is no try-catch statement for this one tho hahaha <@757548402689966131> ?

---

#### [2025-11-06 13:52:31] @dxwil

Hey all, I'm trying to follow these docs to create a tearsheet: https://github.com/nautechsystems/nautilus_trader/blob/develop/docs/concepts/visualization.md, but I can't import TearsheetConfig or create_tearsheet (they don't exist in my local instance), I have installed plotly. Edit: Seems like the feature is so new that it's not in the master branch yet.

---

#### [2025-11-07 01:21:35] @cjdsellers

Hey <@789226697052258304> the reason is because a malformed `PRICE_UNDEF` like that indicates either data corruption or a decoder implementation issue, which should fail loudly and spectacularly. Later on we can improve the error handling ergonomics for these cases, especially as the API stabilized into v2

---

#### [2025-11-07 02:27:58] @wayne_92798

hi, i am new to NautilusTrader and wish to create my own adapter to connect to other broker API, is there any tutorial guide or example on this topic? thanks!

---

#### [2025-11-07 04:31:14] @joejoe404

Hey, Is there any way I can handle it myself?

---

#### [2025-11-07 04:32:30] @joejoe404

I meant, on which row/col of the parquet may cause this dramatic fail

---

#### [2025-11-07 07:52:57] @javdu10

In the github itself there are few adapters you can take example on under the « adapters » folder

---

#### [2025-11-07 12:13:40] @bre_n

Does anyone use BacktestNode? I'm always getting the below error. All the examples use BacktestEngine, should I just go for that instead?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1436327744530157608/image.png?ex=695ef6b3&is=695da533&hm=31e06b8f16e64adaf1ef2841eff44277eee78907260cbee76c3973bd3203a206&)

---

#### [2025-11-07 13:45:25] @fudgemin

```catalog_path = "/root/furtim_alpha/nautilis_catalog"
    
    # Define catalog config
    catalog_config = DataCatalogConfig(
        path=catalog_path,
    )
    
    # Create backtest configuration with all settings nested
    config = BacktestRunConfig(
        engine=BacktestEngineConfig(
            trader_id=TraderId("SIGNAL_STRATEGY-001"),
            logging=FurtimLoggingConfig(),
            catalogs=[catalog_config],  # Pass catalog here
            cache=CacheConfig(
                bar_capacity=10000,
                tick_capacity=10000,
            ),
        ),
        venues=[
            BacktestVenueConfig(
                name="TWELVEDATA",
                oms_type=OmsType.HEDGING,
                account_type=AccountType.MARGIN,
                base_currency=USD,
                starting_balances=[Money(20000, USD)],
            )
        ],
        data=[
            # Load bar data for specific instruments
            BacktestDataConfig(
                catalog_path=catalog_path,
                data_cls="nautilus_trader.model.instruments:Equity",
                client_id="TWELVEDATA",
                instrument_ids=[],  # Specify instruments to load bars for
            ),
            # Load signal data
            BacktestDataConfig(
                catalog_path=catalog_path,
                data_cls=StrikeProxsumSignal,
                client_id="SIGNALS",
                
            ),
        ],
        start="2024-01-01T00:00:00Z",
        end="2025-01-01T00:00:00Z",
    )
    
    # Add strategy
    strategy_config = ImportableStrategyConfig(
        strategy_path=SignalDrivenStrategy.fully_qualified_name(),
        config_path=StrategyConfig.fully_qualified_name(),
        config={},  # No additional config needed
    )
    config.engine.strategies.append(strategy_config)
  
    node = BacktestNode(configs=[config])
    node.run()```

---

#### [2025-11-07 16:03:33] @joejoe404

This issue is critical for me because I love NT and want to use only it haaa<3 

In every parquet file I bought from databento (specifically MBO futures), each day starts with `PRICE_UNDEF`.

```python
import pandas as pd

# Load your parquet (as you already do)
df = pd.read_parquet("./week/data/order_book_delta/NQZ5.GLBX/2025-10-19T11-10-43-318369482Z_2025-10-24T21-00-00-169480096Z.parquet")

# i128::MAX in little-endian bytes: 15 x 0xFF then 0x7F
PRICE_UNDEF_BYTES = b"\xff" * 15 + b"\x7f"

# Boolean mask and indices where price equals PRICE_UNDEF
mask = df["price"] == PRICE_UNDEF_BYTES
undef_idx = df.index[mask]

print("Count:", mask.sum())
print("Indices:", undef_idx.to_list())

#output:

# Count: 6
# Indices: [0, 389435, 12943941, 26782684, 48388754, 63209607]
```

**The crash only happens when I'm trying to backtest from one date to another:**

for example:

```python
start = pd.Timestamp("2025-10-27T23:00:00.076602376Z").value
end =  pd.Timestamp("2025-10-28T22:00:00.076602376Z").value
```

---

#### [2025-11-07 16:04:55] @joejoe404

<@757548402689966131> I really dont know how to solve this issue, I tried to change this price_undef thingy to something else but it keeps crushing it.

I truly want this bug to be fixed, or at least fixed at my side (if the problem is in my data)

---

#### [2025-11-08 00:06:55] @cjdsellers

Hey <@789226697052258304> this *should* be fixed now: https://github.com/nautechsystems/nautilus_trader/commit/8b55d43f8445df6ae5499890bdc644f4dc3a146d
Available in [development wheels](https://github.com/nautechsystems/nautilus_trader#development-wheels) from build 11828+

**Links:**
- Fix Databento MBO data decoding of PRICE_UNDEF · nautechsystems/na...
- GitHub - nautechsystems/nautilus_trader: A high-performance algorit...

---

#### [2025-11-08 00:26:10] @joejoe404

Thank you sir!

---

#### [2025-11-08 02:19:04] @bre_n

thanks will give it a go when i get home. i should be doing pretty much what you have shown

---

#### [2025-11-08 07:47:32] @arandott

Has anyone seen this with aws EC2?
After running fine for a while, SSH suddenly stops working. Port 22 is reachable (nc -vz <public-ip> 22 succeeds), but ssh -vvv ubuntu@<ip> fails with: kex_exchange_identification: read: Connection reset by peer🥲

---

#### [2025-11-08 12:19:11] @bre_n

Nope it's still happening. Try running the below

```python
from nautilus_trader.config import LoggingConfig

from nautilus_trader.backtest.node import BacktestDataConfig
from nautilus_trader.backtest.node import BacktestEngineConfig
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.backtest.node import BacktestRunConfig
from nautilus_trader.backtest.node import BacktestVenueConfig
from nautilus_trader.config import ImportableStrategyConfig
from nautilus_trader.persistence.config import DataCatalogConfig

catalog_path = "./catalog"

catalog_config = DataCatalogConfig(
    path=catalog_path,
)

data_configs = [
    BacktestDataConfig(
        catalog_path="./catalog",
        data_cls="nautilus_trader.model.instruments:Equity",
        client_id="SIGNALS"
    )
]

venues_configs = [
    BacktestVenueConfig(
        name="ASX",
        oms_type="NETTING",
        account_type="CASH",
        base_currency="AUD",
        starting_balances=["1_000_000 AUD"]
    )
]

strategies = [
    ImportableStrategyConfig(
        strategy_path="nautilus_trader.examples.strategies.blank:BlankStrategy",
        config_path="nautilus_trader.examples.strategies.blank:BlankStrategyConfig",
        config = {}
    )
]

# Define multiple run configurations
configs = [
    BacktestRunConfig(
        engine=BacktestEngineConfig(
            strategies=strategies,
            logging=LoggingConfig(log_level="ERROR"),
            catalogs=[catalog_config]
        ),
        data=data_configs,
        venues=venues_configs,
        start="2025-01-04T00:00:00Z",
        end="2025-06-01T00:00:00Z",
    ),

]

node = BacktestNode(configs=configs)
results = node.run()
```

---

#### [2025-11-08 12:20:39] @bre_n

<@391823539034128397> error is ```[ERROR] BACKTESTER-001.BacktestNode: Error running backtest
AttributeError('NoneType' object has no attribute 'logger')```

---

#### [2025-11-08 17:36:26] @fudgemin

not sure, but error seems clear to point to logger. that error reminds me of the default python logger module. Are you importing both? 

NT internal logger should resolve with no errors on the config above. you may have a build or dependency issue?

---

#### [2025-11-08 17:43:57] @fudgemin

try wrapping the strategy import class direct, not by file location. or add via factory, to the node after, like i had done.

---

#### [2025-11-10 06:11:36] @greenbone

Hey folks I’m trying to expose some Rust functions to Cython and currently testing out orderbook_spread() under a new name. After running build.py, the function compiles correctly into the .so file, but it doesn’t show up in the generated header file.

Has anyone run into this before? Any idea why a function would make it into the .so but get skipped during header generation? I could manually add it to the header, but I’m curious why cbindgen might be omitting it, even though the ffi feature flag is enabled during the build. 

I’m still pretty new to Rust, so I’d really appreciate any insight!

---

#### [2025-11-10 06:44:06] @cjdsellers

Hey <@1024150660519825418> 
You're in some territory known to be occupied by dragons there, but some quick things I can suggest:
- Make sure you have a `#[unsafe(no_mangle)]` attribute above the `pub extern "C" fn`
- Make sure the function is actually used by Rust somewhere, even if it's `pub`, `cbindgen` might not generate headers unless it's used
- Try exporting the `high_precision=true` env var, then building, *or* unsetting that if it was set already to force cargo to detect an environment change (sometimes that can trigger it)

---

#### [2025-11-10 15:29:00] @greenbone

hey <@757548402689966131> thank you for your suggestions! I'll give these a shot

---

#### [2025-11-11 08:03:24] @jst0478

Hi, I'm seeing something strange going on with reconciliation and Interactive Brokers (although it may not be directly related to IB).

I'm paper trading and was using NT without a persistent cache for a while. Some orders were made during this time and filled, opening positions.

Now I've enabled persistent caching with a Redis backend (https://nautilustrader.io/docs/latest/concepts/cache#database-configuration) and also enabled `external_order_claims` (https://nautilustrader.io/docs/latest/concepts/live#reconciliation-configuration).

The strange behavior I see is this:

---

#### [2025-11-11 08:03:47] @jst0478

1. When first starting after enabling persistent caching, I saw that NT created some orders/positions for me during reconciliation, matching the orders/positions made above (when persistent caching was off). The client order IDs for these orders are all set to simply the instrument ID (I guess it makes sense since the original ones were lost). The order types are set correctly. Order price is not set. Most of the other data looks okay. (I'm looking at the orders/positions reports generated by NT, as well as inspecting the data in Redis).

2. I stop NT and restart it. Now I get some strange behavior -- NT creates some *additional* orders (but not positions) for me during reconciliation, matching the orders made originally (when persistent caching was off). This time, they are given some randomly generated client order IDs that look like "O-0c189d6b-73ff-4ef2-ba51-e7652e723bf5". The *order types are wrong* (original ones were MARKET orders but these are set to LIMIT for some reason). Some other fields are also wrong: time_in_force and liquidity_side (it's set to 'NO_LIQUIDITY_SIDE'). This time, price is set. I think other data looks okay, such as quantity, avg_px, etc. However, new values for init_id, last_trade_id, ts_init, etc. are all created for these new orders.

So now I have a bunch of duplicate open (I guess?) orders in the reports/Redis data for all the orders.

---

#### [2025-11-11 08:04:05] @jst0478

3. Every time I stop and start NT, another duplicate set of orders are created with new order IDs. This part also strikes me as odd. I expected NT to find the existing order IDs and use them instead. The duplicate orders with wrong type and such just keep piling up.

I tried stopping NT and nuking everything in Redis, but the behavior persists and is reproducable.

Is this a known problem, or am I just reading these reports/Redis data wrong? Any solution? Is it fine to ignore?

Let me know if you need to see some more data.

CC <@757548402689966131> as I think you're working on reconciliation now in a branch.

---

#### [2025-11-11 08:21:13] @jst0478

I think what I'd expect is something like: during step 1 reconciliation above, NT generates new client order IDs for me like "O-..." instead of using instrument ID, and then use those order IDs from then on for those external orders instead of reconciling to new orders each time, but idk.. this is over my head

---

#### [2025-11-11 09:15:04] @faysou.

That's typically the kind of complex case an AI agent is good to work with, if the agent has a case to work with and test, it will likely find the answer. If you send an MRE (minimum reproducible example) I could try to fix it.

---

#### [2025-11-11 09:36:47] @nobita0313

Hi, newbie here, when i do 
print(catalog.instruments()[0:5])

[Equity(id=A.XNAS, raw_symbol=A, asset_class=EQUITY, instrument_class=SPOT, quote_currency=USD, is_inverse=False, price_precision=2, price_increment=0.01, size_precision=0, size_increment=1, multiplier=1, lot_size=100, margin_init=0, margin_maint=0, maker_fee=0, taker_fee=0, info={}), Equity(id=A.XNAS, raw_symbol=A, asset_class=EQUITY, instrument_class=SPOT, quote_currency=USD, is_inverse=False, price_precision=2, price_increment=0.01, size_precision=0, size_increment=1, multiplier=1, lot_size=100, margin_init=0, margin_maint=0, maker_fee=0, taker_fee=0, info={}), Equity(id=A.XNAS, raw_symbol=A, asset_class=EQUITY, instrument_class=SPOT, quote_currency=USD, is_inverse=False, price_precision=2, price_increment=0.01, size_precision=0, size_increment=1, multiplier=1, lot_size=100, margin_init=0, margin_maint=0, maker_fee=0, taker_fee=0, info={}), Equity(id=A.XNAS, raw_symbol=A, asset_class=EQUITY, instrument_class=SPOT, quote_currency=USD, is_inverse=False, price_precision=2, price_increment=0.01, size_precision=0, size_increment=1, multiplier=1, lot_size=100, margin_init=0, margin_maint=0, maker_fee=0, taker_fee=0, info={}), Equity(id=A.XNAS, raw_symbol=A, asset_class=EQUITY, instrument_class=SPOT, quote_currency=USD, is_inverse=False, price_precision=2, price_increment=0.01, size_precision=0, size_increment=1, multiplier=1, lot_size=100, margin_init=0, margin_maint=0, maker_fee=0, taker_fee=0, info={})]

it return the same instrument multiple time, is it normal? should i do something to correct it?

is it because my bar data is splited in multiple file? (see the image)

**Attachments:**
- [Screenshot_2025-11-11_at_09.33.53.png](https://cdn.discordapp.com/attachments/924499913386102834/1437737819064766515/Screenshot_2025-11-11_at_09.33.53.png?ex=695ed1ef&is=695d806f&hm=5cf1c356a907e8030e155fec041c5f47593465aa6a38b5f7e72b6aed78913459&)

---

#### [2025-11-11 17:00:22] @ido3936

Does this bug seem to describe the issue? https://github.com/nautechsystems/nautilus_trader/issues/3046

**Links:**
- [Reconciliation] Duplicate trade IDs and fill replay on node restar...

---

#### [2025-11-12 04:12:22] @jst0478

I saw your ticket when I was investigating my problem, but I don't think it's the same. I don't see any duplicate trades or KeyErrors popping up in logs.

---

#### [2025-11-12 07:52:54] @jst0478

https://github.com/nautechsystems/nautilus_trader/issues/3176
I tried letting Claude figure it out.  CC <@757548402689966131> (related to reconciliation)

---

#### [2025-11-12 07:58:58] @faysou.

Thanks for the report. I haven't used the redis cache before but trying to solve this could be a good way to learn about it.

---

#### [2025-11-12 08:09:40] @jst0478

I hope it helps. And, this may be really low priority. Ideally I'd have persistent caching on from the start rather than turning it on after orders were made.  I'm going to check and make sure that is working next

---

#### [2025-11-12 16:34:07] @ido3936

I don't know about the NT team's priorities - but note that issues with persistence could be relevant under multiple scenarios where the trading system is not running 24/7. It could be that it was stopped on purpose, or it could be that it crashed, etc. etc.

Here's my (limited) understanding of what is going on:
I think that the orders that you describe are 'artificial': they are made in order to align the NT's book keeping with whatever the client is telling it is the current state.
I think that the use of LIMIT in place of MARKET is just a convenience
But then - these orders should all be filled  -  if they are still open then that's a problem

---

#### [2025-11-13 06:04:02] @jst0478

I noticed in my cache, and we can see from the NT code, that they're all marked as filled - it's making duplicated filled orders. So maybe it's not a big problem, but it does bloat the reports with duplicates and incorrect data. But could there be any other side effects to the trading system? It looks like NT associates the filled orders (the latest duplicated one) with open positions

---

#### [2025-11-13 07:39:00] @cjdsellers

Hi <@296261099630755841> and <@1074995464316928071> just a quick note to say that I'm aware of this thread and associated issues in GitHub. My initial impression is there is some specific interactions with the IB adapter and recon. I'm unable to test with IB myself - and have not yet allocated bandwidth to looking at this next round of reconciliation fixes/improvements yet (also, there is no longer a separate `reconciliation` branch, that was merged already after the last release)

---

#### [2025-11-13 10:51:29] @henryc4053

Greetings all, hope someone can help. I am using macos (on intel - yes, yes... will upgrade when the money's there) so cannot use: 

```
pip install --only-binary :all: nautilus_trader
```
since there are only binaries for M series (correct?).

I have tried:
```
git clone --branch develop --depth 1 https://github.com/nautechsystems/nautilus_trader
cd nautilus
cd nautilus_trader/
uv sync --all-extras
```

Which naturally downloads the source and attempts to compile. Currently trying:
```
pip install -U nautilus-trader --extra-index-url=https://packages.na
utechsystems.io/simple
```

All fail to compile, presumably due to a dependency or other issue. I'm hoping for some guidance to get this to compile (fair disclosure: I'm familiar with C/C++/others, far less so with Python/Rust). The compilation log is attached. Using an anaconda3 env.

More info:
```
      =====================================================================
      Nautilus Builder 1.221.0
      =====================================================================
      System: Darwin x86_64
      Clang:  17.0.0 (clang-1700.4.4.1)
      Rust:   1.91.1 (ed61e7d7e 2025-11-07)
      Python: 3.13.5 (/opt/anaconda3/envs/forexStrategies/bin/python3.13)
      Cython: 3.1.6
      NumPy:  2.3.4
      
      RUSTUP_TOOLCHAIN=stable
      BUILD_MODE=release
      BUILD_DIR=build/optimized
      HIGH_PRECISION=True
      PROFILE_MODE=False
      ANNOTATION_MODE=False
      PARALLEL_BUILD=True
      COPY_TO_SOURCE=True
      FORCE_STRIP=False
      PYO3_ONLY=False
      LDFLAGS=-L/usr/local/opt/readline/lib
```

Thanks

**Attachments:**
- [compile-fail.txt](https://cdn.discordapp.com/attachments/924499913386102834/1438481390680408114/compile-fail.txt?ex=695ee371&is=695d91f1&hm=a787146afa5d35ec745c7a496f12a8169c132053edd4d5df0ae60ee53cf71130&)

---

#### [2025-11-13 11:41:50] @cjdsellers

Hi <@810430622128537600> welcome!
Those linker issues can be tricky, it may just be a case of some env vars. The [CI for macos](https://github.com/nautechsystems/nautilus_trader/blob/develop/.github/actions/common-wheel-build/action.yml#L74) may offer some clues there (although it is building on an arm64 runner)

---

#### [2025-11-13 12:27:43] @henryc4053

Thanks - I'll dig into that file and see what there is to see

---

#### [2025-11-13 13:45:46] @jst0478

I'm a noob here too, but it looks like it's failing around stuff for pyo3.  Did you also do this part?

> # Set the library path for the Python interpreter (in this case Python 3.13.4)
> export LD_LIBRARY_PATH="$HOME/.local/share/uv/python/cpython-3.13.4-linux-x86_64-gnu/lib:$LD_LIBRARY_PATH"
> 
> # Set the Python executable path for PyO3
> export PYO3_PYTHON=$(pwd)/.venv/bin/python

It's listed after `uv sync --all-extras` in the docs, but I think when I compiled from source I had the same problem and it was because of this. Worth a try anyway

---

#### [2025-11-13 14:42:35] @henryc4053

Hey @jst, yes I saw that too, but ```$HOME/.local/share/uv``` does not exist for me. I have no idea where it is.

I'm starting to believe it's because I'm using Anaconda. I'm flailing about a bit now when there's abstraction involved and I don't know where stuff is... going to go back to basics without Anaconda and simplify things.

---

#### [2025-11-13 15:07:06] @faysou.

don't use anaconda, I used to use it when I started with nautilus, it doesn't work

---

#### [2025-11-13 15:07:25] @faysou.

https://gist.github.com/faysou/7f910b545d4881433649551afce69029

---

#### [2025-11-13 15:07:29] @faysou.

I use this currently with pyenv and uv

---

#### [2025-11-13 15:07:48] @faysou.

and this https://gist.github.com/faysou/c7adc018e99ac05c9a63ac092a06e7f5 for uv only

**Links:**
- Install nautilus_trader dev env from scratch using uv only

---

#### [2025-11-13 15:08:52] @faysou.

uv only requires extra lines related to the compiler to make it compile, it's not clear to me which ones, everytime I try there are issues with uv only, and haven't spent the time to fix them, whereas pyenv with uv always works

---

#### [2025-11-13 15:09:46] @faysou.

uv presents itself as a universal thing to replace everything, but it's not there yet

---

#### [2025-11-13 15:10:25] @faysou.

being able to compile nautilus is a big plus as this allows to understand better how it works, or let someone or an AI agent try things

---

#### [2025-11-13 15:13:44] @henryc4053

Thanks <@965894631017578537> - yes, I don't have time for complexity and issues. Just want to compile nautilus so I can focus on what's important. Going to take a step back and keep it simple.

---

#### [2025-11-13 15:24:20] @jst0478

I think you just need to tell the compiler where the python development libraries are. I'm not so familiar with macos, but it sounds like if you install python with brew or something then the development libraries come with it? Then add the path where those headers are to LD_LIBRARY_PATH and try to compile again

---

#### [2025-11-14 07:10:00] @jst0478

Update: https://github.com/nautechsystems/nautilus_trader/issues/3176#issuecomment-3531218556
I think the problem is my fault. Beware of putting colons in the order ID tag! I'm going to rename my order ID tag and do some more testing to confirm.
CC <@965894631017578537> , <@1074995464316928071>

---

#### [2025-11-14 17:13:31] @nuppsknss

still didn't figure this one out, any help would be appreciated 
https://discord.com/channels/924497682343550976/924506736927334400/1437861201261629490

---

#### [2025-11-14 21:09:51] @faysou.

I've worked on this today and managed to reproduce it and likely fixed it. I need to review the code more and will do a PR when I think it's ready.

---

#### [2025-11-14 21:17:33] @faysou.

This allowed me to learn about the redis cache, it's quite interesting, first time I've used it.

---

#### [2025-11-16 13:21:23] @toriarty

Hi guys，I used (subscribed_order_book_at_interval) successfully on the live trading,  also could get orderbook snapshot on func (on_order_book) , but I cannot find the orderbook snapshot on my redis. Only have orderbook deltas, so are there any way to save the orderbook snapshot on redis persistently？

---

#### [2025-11-19 07:49:15] @jst0478

Thanks for working on it. I'm trying `nautilus-trader==1.222.0a20251118` to see if my problems are fixed or not. I need some more time to check reconciliation.

But in the meantime I noticed some new errors popping up in the logs with this new version of NT. It seems to be reaching IBKR's API limits when starting my strategies' subscriptions:

> 2025-11-19T07:36:31.199307179Z [WARN] PAPER-TRADER-001.InteractiveBrokersClient-001: Unknown subscription error: 10190 for req_id 10009
> 2025-11-19T07:36:31.199293827Z [ERROR] PAPER-TRADER-001.InteractiveBrokersClient-001: Max number of tick-by-tick requests has been reached. (code: 10190, req_id=10009)

.. then on shutdown:
> 2025-11-19T07:50:18.096910744Z [WARN] PAPER-TRADER-001.InteractiveBrokersClient-001: Unhandled error: 300 for req_id 10009
> 2025-11-19T07:50:18.096901428Z [ERROR] PAPER-TRADER-001.InteractiveBrokersClient-001: Can't find EId with tickerId:10009 (code: 300, req_id=10009)
(repeat this X times for most quote tick subscriptions in my NT strategies - emphasis on *most* of them, not all of them. The first handful seem to work fine)

It's not doing this on the latest stable NT release `nautilus-trader==1.221.0` (I rolled back to confirm).  I don't really know what to do.

Is new reconciliation code being more aggressive with the IBKR API or something? Or is it maybe caused by some other unrelated new changes?

I'll start trying to investigate but let me know if anyone has any ideas

---

#### [2025-11-19 07:51:52] @faysou.

I think a change was made to subscribe to the granular ticks by default. I think the default should be to subscribe to snapshot ticks by default. It's not from the reconciliation change, it's another change.

---

#### [2025-11-19 07:52:15] @faysou.

I think this conversation should be in the IB channel

---

#### [2025-11-20 16:39:18] @dun02

I'm trying to do multiple runs and have a separate log file get created, but instead it takes the first ticker in the list as the file name, then concatenates the 3 results into that one log file, is there anything I'm doing wrong?
```
LOG_DIR = os.getenv('LOG_DIR')

tickers = []
with open('mr_tickers.txt', 'r') as file:
    for line in file:
        ticker = line.strip()
        if ticker: 
            tickers.append(ticker)

for ticker in tickers[:3]:
    current_time = pd.Timestamp.now()
    current_time_formatted = current_time.strftime('%Y-%m-%d-%H:%M:%S')
    log_file_name = f"naut_bt_{ticker}_{current_time_formatted}.log"
    print(log_file_name)
    engine_config = BacktestEngineConfig(
        logging=LoggingConfig(
            log_level="ERROR",
            log_level_file="INFO",
            log_file_name=log_file_name,
            log_directory=LOG_DIR
        )
    )
    engine = BacktestEngine(
        config=engine_config       
    )
    ....
    engine.reset()
```

---

#### [2025-11-21 06:24:22] @cjdsellers

Hey <@966200006010863656> I'd suggest looking into the streaming feather writer for persisting market data

---

#### [2025-11-22 05:55:05] @wave8718

<@1354119061407141922>  hi can you share the fyers adapter, is it open-source? How can I get it .


 <@757548402689966131> if you have this pl show me the way to get it. 

Thank you in advance..

**Attachments:**
- [image0.png](https://cdn.discordapp.com/attachments/924499913386102834/1441668289930461375/image0.png?ex=695e9df9&is=695d4c79&hm=cf944ee90b691ee390a568e79e8bf04cb9474ddea8549a43cdda07628a5ec197&)

---

#### [2025-11-23 11:05:06] @faysou.

I've updated this gist so it works well with uv. There was a problem when running make cargo-test with a uv managed python installation, a PYTHONHOME env variable needs to exist, I've added an instruction to add it to .cargo/config.toml, I've also updated the documentation for this.

---

#### [2025-11-25 03:05:06] @zschei44

Hey folks I'm trying to work my way through the examples but I'm getting the folloing error:

---------------------------------------------------------------------------
ModuleNotFoundError                       Traceback (most recent call last)
File ~/anaconda_projects/nautilus_trader-develop/examples/backtest/example_03_bar_aggregation/run_example.py:21
     17 from decimal import Decimal
     19 from strategy import DemoStrategy
---> 21 from examples.utils.data_provider import prepare_demo_data_eurusd_futures_1min
     22 from nautilus_trader.backtest.engine import BacktestEngine
     23 from nautilus_trader.config import BacktestEngineConfig

ModuleNotFoundError: No module named 'examples'

That module seems to be called in every backtesting example.  I would appreciate any help.

---

#### [2025-11-25 12:32:54] @dxwil

Hey, I'm having a problem, when I request_bars (with the intention of them warming up the indicators for live trading), the historical bars come in order of newest to oldest (which from what I observed warms up the indicators in an incorrect order). Is this a bug? Or the correct behaviour, and I should warm up the indicators differently?

```
2025-11-25T12:43:35.815505000Z [INFO] TESTER-001.DistanceStrategy: Received historical bar: BTC-USD-PERP.DYDX-1-MINUTE-LAST-EXTERNAL, time=2025-11-25T12:43:00+00:00, O=87461, H=87582, L=87442, C=87582
2025-11-25T12:43:35.815574000Z [INFO] TESTER-001.DistanceStrategy: Received historical bar: BTC-USD-PERP.DYDX-1-MINUTE-LAST-EXTERNAL, time=2025-11-25T12:42:00+00:00, O=87442, H=87469, L=87442, C=87469
2025-11-25T12:43:35.815617000Z [INFO] TESTER-001.DistanceStrategy: Received historical bar: BTC-USD-PERP.DYDX-1-MINUTE-LAST-EXTERNAL, time=2025-11-25T12:41:00+00:00, O=87455, H=87479, L=87425, C=87436
2025-11-25T12:44:02.828040000Z [INFO] TESTER-001.DistanceStrategy: Received bar: BTC-USD-PERP.DYDX-1-MINUTE-LAST-EXTERNAL, time=2025-11-25T12:44:00+00:00, O=87607, H=87731, L=87591, C=87731
2025-11-25T12:45:04.253359000Z [INFO] TESTER-001.DistanceStrategy: Received bar: BTC-USD-PERP.DYDX-1-MINUTE-LAST-EXTERNAL, time=2025-11-25T12:45:00+00:00, O=87756, H=87799, L=87657, C=87661

```

---

#### [2025-11-25 14:57:33] @conayuki

is there a way to quickly clone a rejected order and resubmit it as a simulated one? it looks tedious to recreate the order using order_factory since each order type has its own method.

---

#### [2025-11-25 17:50:41] @to19

Hello guys I'm trying this lib out. Anyone is using vscode based ides ? Using it with cython is weird there is no code navigation and stuff :/

---

#### [2025-11-25 18:08:54] @faysou.

use intellijidea ultimate, that's what I use, it works well with cython, python and rust at the same time. at some point cython won't be used anymore, and vscode based IDEs will be more usable with nautilus. currently I use cursor for using an AI agent and look at the code and edit it manually in intellijidea

---

#### [2025-11-25 18:12:40] @to19

what you mean by it won't be used anymore ? nautilus is going full rust ?

---

#### [2025-11-25 18:12:52] @faysou.

yes, full rust and python

---

#### [2025-11-25 18:12:54] @faysou.

no cython anymore

---

#### [2025-11-25 18:13:14] @faysou.

but not yet, there's a migration in progress, for now what's usable is python + cython + rust

---

#### [2025-11-25 18:13:46] @faysou.

but the rust side will have the same structure as cython, so what you learn with cython, it will be me mostly the same in rust

---

#### [2025-11-25 18:14:09] @faysou.

but it will be easier to understand the whole code in rust and debug it, as cython can't be debugged

---

#### [2025-11-25 18:14:20] @to19

I prefer to avoid intellij I used to be a intellij nerd but now it sucks. Any vim/neovim plugin alternative ?

---

#### [2025-11-25 18:15:13] @faysou.

<@757548402689966131> knows about nvim, I've never managed to motivate myself to learn it, watched several videos about it, but preferred coding some new stuff than learn it

---

#### [2025-11-25 18:15:46] @faysou.

especially as most code is written by agents now, I'm more reviewing the agent now, although still coding manually sometimes if it's really subtle

---

#### [2025-11-25 18:16:29] @faysou.

I don't have the impression that intellijidea sucks, I prefer it to vscode

---

#### [2025-11-25 18:18:18] @to19

you are using cursor agents ?

---

#### [2025-11-25 18:18:29] @faysou.

yes

---

#### [2025-11-25 18:19:04] @to19

do you have a link to pr/discussions about it please ?

---

#### [2025-11-25 18:21:49] @faysou.

no I don't, it's a thing ongoing for several years that the maintainer of the project <@757548402689966131> is working on, as well as a few other people, but <@757548402689966131> is the main person working on this

---

#### [2025-11-25 18:24:12] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md

---

#### [2025-11-25 18:24:17] @to19

they went from a banger ide to a slow ass shit 10min startup ide in like 2 years. I still prefer debugging and database tools from intellij tho

---

#### [2025-11-25 18:24:35] @faysou.

maybe you are using windows

---

#### [2025-11-25 18:24:52] @faysou.

it used to be the case for me on windows before switching to macbook

---

#### [2025-11-25 18:24:56] @faysou.

on macbook it works well

---

#### [2025-11-25 18:25:07] @to19

I used it with mostly linux and macos

---

#### [2025-11-25 18:26:05] @faysou.

all I can say is that currently it works well for me on a macbook air m4

---

#### [2025-11-28 02:22:47] @falls7202

I need to manually pause my running Strategy process. What is the standard best practice for this?

I'm currently thinking of spawning a listener thread within the process that reads pause command from a pipe, and then pushes the pause command into the main process's msgbus.

---

#### [2025-11-28 03:36:28] @mrrothz

hi <@965894631017578537> i created an issue: https://github.com/nautechsystems/nautilus_trader/issues/3233
i believe this is missing while implementation `replace_existing` in `StreamingConfig`

**Links:**
- `replace_existing` is not using for setting up `StreamingFeatherWri...

---

#### [2025-11-28 08:05:40] @mrrothz

i created a PR for fix this bug: https://github.com/nautechsystems/nautilus_trader/pull/3234

**Links:**
- Fix _setup_streaming with replace_existing config by cauta · Pull ...

---

#### [2025-12-01 21:49:31] @greenbone

Hey everyone quick question. It's taking ~20s to query one days worth of orderbook deltas for a single instrument roughly 50m orderbook deltas. I'm calling query_typed_data from Rust. Is that in the right ballpark or should I expect much faster?

---

#### [2025-12-02 05:49:04] @cjdsellers

Hey <@1024150660519825418> depends on a couple of factors such as exact hardware, I'd expect in that range up to about ~2x faster. DataFusion is very good at leveraging more cores to read in parallel, so maybe try scaling up a little and see if that helps

---

#### [2025-12-02 07:41:05] @kulig1985

Hi, found this tutorial.. https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook but there isn’t even a word about that how to provide historical order book data for this… and how this data should look like.. can anyone help me?

**Links:**
- Backtest: Binance OrderBook data | NautilusTrader Documentation

---

#### [2025-12-02 20:42:25] @greenbone

Thank you for the response! Could you clarify what you mean by "scaling up"? I thought DataFusion defaults to using all available cores.

---

#### [2025-12-03 02:35:26] @cjdsellers

Hey <@1024150660519825418> I meant scaling vertically with even more cores, but it might be worth figuring out what the bottleneck actually is before that - I would expect more performance than what you're reporting

---

#### [2025-12-05 15:50:10] @ido3936

Thanks <@965894631017578537> and <@757548402689966131> , I've been away for a while but I started to test again the possibility of running NT over multiple sessions with persistence and reconciliation in between.
I think that for the most part it works!! 🙏 
I did come upon this minor difficulty today (I thikn that there is a missing check in the line) but apart from that it has been running smoothly for several days

```line 3570, in _find_matching_cached_order
    if price is not None and cached_order.price is not None and cached_order.price != price:
                             ^^^^^^^^^^^^^^^^^^
AttributeError: 'nautilus_trader.model.orders.market.MarketOrder' object has no attribute 'price'```

---

#### [2025-12-05 16:27:04] @faysou.

Good, over time all bugs get fixed as long as people use the library and report bugs.

---

#### [2025-12-05 16:28:57] @faysou.

Note that better reproduction codes or reports allow to fix bugs more easily instead of interpreting an error message.

---

#### [2025-12-05 18:44:38] @faysou.

Also better to log issues on GitHub

---

#### [2025-12-05 19:55:58] @ido3936

link to my comment in GH (FWIW, as the PR is already merged)

https://github.com/nautechsystems/nautilus_trader/pull/3185#issuecomment-3618384069

**Links:**
- Refactor execution engine reconciliation by faysou · Pull Request ...

---

#### [2025-12-05 23:48:03] @cjdsellers

Thanks for the report <@1074995464316928071>, this should now be fixed: https://github.com/nautechsystems/nautilus_trader/commit/dc6cce9321574f4cd6b076d79e3d27d73ba53765

**Links:**
- Fix matching market order price AttributeError · nautechsystems/na...

---

#### [2025-12-06 01:42:33] @albert_09059

I am sorry for the bother, I am a very very very junior to this repository (though it is the best I find so far), may I ask where I can obtain dataset similar to Binance`depth-snap.csv`  such that I can run `crypto_orderbook_imbalance.py`. I am mainly interested in modelling with regards to orderbook data instead of Kline because they have richer mathematical properties, but I am not sure the workflow of it, I will appreciate any advices and thank you very much for building such a good project.

---

#### [2025-12-06 13:51:22] @hadi_loo

Hi everyone! I’m new to Nautilus Trader and am currently working through some examples to get familiar with the platform. I'm really enjoying the architecture so far!

I’ve hit a stumbling block regarding how the BacktestEngine handles simulated fills against L3 data, and I’m hoping someone can point me in the right direction.

The Scenario: I am running a backtest using a custom L3DataWrangler and a simple CSV data feed.

```Python
# Data Snippet
("2024-01-01 09:00:00", 3.8, 100, "sell", "OID-1") 
("2024-01-01 10:00:00", 3.5, 100, "buy", "OID-2")
# No subsequent 'DELETE' or 'MATCH' event exists for OID-3 in the CSV.
```

My strategy submits a Limit Buy order (size 100 @ 3.8) every 10 minutes.

The Expected Behavior:

- At 09:10, the first Buy order matches with OID-3. 
OID-3 is fully consumed/filled.

- At 09:20, the second Buy order is submitted but should not fill (or should rest), because the liquidity at 3.8 was taken by my previous trade.

The Actual Behavior: Every single Buy order I submit gets filled at 3.8. It seems like the simulated exchange "resets" the liquidity based on the Data Feed rather than persisting the state change caused by my strategy's execution.

My Question: Is there a specific configuration for SimulatedExchange or BacktestEngine that enforces stateful liquidity consumption? I want my simulated fills to permanently remove orders from the internal simulation book, even if the Data Feed doesn't explicitly send a delete event for them.

Thanks in advance for any help!

---

#### [2025-12-07 14:58:16] @thisisrahul.

Hello, I’m using the nightly build, while plotting the tear sheet, the equity curve as well as the monthly returns seem start from 1970 (start of epoch) instead of the start of backtest

I debugged the code and it seems that the problem is I have a open position at the end of the backrest ( this assigns the close time of the position to 0, equivalent to 1970 )

Is there a way for me to close the position when backtest stops? 
I already have close_all_positions inside on_stop

---

#### [2025-12-15 04:46:39] @even_27404

When will the hybrid cloud be available? I'm willing to pay to use it <@757548402689966131>

---

#### [2025-12-15 07:22:47] @cjdsellers

Hi <@1413850358488371271> thanks for your interest. We're working on it at the moment, too early to be giving concrete time frames but it will be one of the major themes of next year when the Rust port is out of the way (getting closer on that every day). More updates on the state of the Rust port in the next release announcement (likely this week)

---

#### [2025-12-15 07:58:35] @javdu10

Nice I was going to put « release tag » on my wish list

---

#### [2025-12-16 03:31:21] @cjdsellers

Hi <@692998608600956969> 
Thanks for reaching out.
We don’t yet simulate user-driven state changes against historical book data, so fills don’t persistently remove liquidity in the backtest engine (this would be more realistic though). This is planned after the Rust port 🦀

---

#### [2025-12-18 14:14:38] @redyarlukas

Is there any simple configuration option I dont see which allows me to guarantee always complete fills even though the actual liquidity is not provided? I could manually overwrite the historical sizes during data load but this would take hours and I would lose the option to switch on partial fills.

---

#### [2025-12-18 14:19:27] @heliusdk

Working on a new strategy and want to ask if anyone here have tried to optimize a mean reversion strategy before?

I have a 75.9% win rate, however my avg win is $24.81 and my avg loss is -$85.38.
Using bayesian optimization by point distance from signal to actual price I got the avg loss down to -$59.64, and the avg trade from -$1.73 down to -$0.67, at the cost of a 73.8% win rate instead.

The backtest is for 1 year, where it generates 2532 orders.


recipe:
- Constantly in the market
- Dynamic position scaling based on point distance and win/loss ratio over the last 200 trades with bayesian optimization
- Stoploss, well none I do not have good experience with stoplosses and for this strategy it would probably be a killer for the winrate.
- Base trigger classic vwap above and below
- exit trigger the reverse
- fill and transaction costs ofc included

I've looked into:
- large volume periods had a large say in this, hence given my dynamic position sizing.
- Grouped by time of day to look for patterns, because the exchange open and close periods had a say


Right now I am looking into to trying to do a regression over the z-score as well as strategy signals, which may or may not overfit it.
Also doing market regime identification for better trade confidence together with Markov models.

But overall I am asking for inspiration or ideas for new angels to look at the data from, would appricate if anyone would share a chunk or their experince in this area, or feedback or even just a sketchy technical paper they want to share 😀 👏

**Attachments:**
- [Screenshot_2025-12-18_at_14.55.16.png](https://cdn.discordapp.com/attachments/924499913386102834/1451217303021813830/Screenshot_2025-12-18_at_14.55.16.png?ex=695e6b6f&is=695d19ef&hm=08b8cb7c51784c56b612eb605e9bf30985b5b610c01da0972fc0616263c44b02&)
- [Screenshot_2025-12-18_at_15.05.23.png](https://cdn.discordapp.com/attachments/924499913386102834/1451217303365484574/Screenshot_2025-12-18_at_15.05.23.png?ex=695e6b6f&is=695d19ef&hm=5c413f16de2edd218bb48213918e9e542b58ad2b7c050a4f54ebec7193ae6539&)

---

#### [2025-12-19 07:55:50] @cjdsellers

Hi <@1273010294033219642> 
Seems like you have some avenues to investigate there - nice work on the progress and vis! My only comment would be that I’d still suggest having some way of expressing a point where the strategy is definitely wrong about the potential reversion, to manage risk. 

Otherwise, you’re hoping that some huge Cauchy outlier doesn’t steamroll the last couple of months of profits with a sharp correction into a regime change

---

#### [2025-12-19 13:15:49] @heliusdk

Thanks for the feedback, I will do that 🙂

---

#### [2025-12-19 14:27:30] @dun02

I'm getting these errors on a backtest of EUR/CHF spot FX.  I assume I need to provide CHF/USD or USD/CHF daily prices so that it can do currency conversions?  How should I resolve?
Bar:
```
Bar(EUR/CHF.SIM-1-MINUTE-LAST-EXTERNAL,0.96719,0.96720,0.96718,0.96719,5,1718234940000000000)
```
Error:
```
2024-06-13T05:03:00.000000000Z [ERROR] BACKTESTER-001.Cache: Cannot calculate exchange rate: ValueError('Quote maps must not be empty')
2024-06-13T05:03:00.000000000Z [ERROR] BACKTESTER-001.Portfolio: Cannot calculate account state: insufficient data for CHF/USD
```

---

#### [2025-12-21 13:02:00] @oikoikoik14

I have a hard time understanding the matching logic in nautilus_trader

I have level 2 data and TradeData for a instrument (being a option, but this should not matter)

The scenario is that

Level 2 data which has the following top of book (Snapshot):

Best Bid: 1000 @ 0.27

Best Ask: 100 @ 0.37

My Orders (Accepted & Open):

Limit Buy: 1 @ 0.28 (Better than best bid)

Limit Sell: 1 @ 0.36 (Better than best ask)

The Issue: A trade tick comes in as a SELLER at 0.27. Since my Buy order is sitting at 0.28, I would expect this to match and fill my order immediately.

However, the tick is just passed through and filled with a order that is at 0.27. It doesn't seem to trigger any fill logic, and it looks like it doesn't even reach the FillModel.

Has anyone experienced this behavior where price improvement inside the spread is ignored during simulation? Is there a configuration setting for matching logic or FillModel that I might be missing? I have already turned on trade_execution=True in the BacktestVenueConfig

Thanks!

---

#### [2025-12-21 13:27:41] @oikoikoik14

Running the 

tests/unit_tests/backtest
/test_matching_engine/TestOrderMatchingEngine.test_trade_execution_fills_better_priced_orders_for_buys 

locally produces a error.... Has the logick changed since then? <@757548402689966131>

---

#### [2025-12-22 22:38:55] @cjdsellers

Hey <@401500931931373569> 
The test passes on the current `develop` branch. This behavior was fixed by
 the "transient override" feature added here: https://github.com/nautechsystems/nautilus_trader/commit/7d4a503de
 - Ensure you have the latest from `develop` (install a recent development wheel)
 - Confirm `trade_execution=True` is set in `BacktestVenueConfig`

 So for your scenario, the matching logic now correctly fills limit orders that are "better priced"
 than the trade - a BUY LIMIT at 0.28 WILL fill on a SELLER trade at 0.27

**Links:**
- Improve trade execution matching with transient override · nautech...

---

#### [2025-12-26 04:52:31] @yb05379

Hi! I’m currently running a backtest using QuoteTick data and trying to implement a TrailingStopMarketOrder with an activation price. But the issue I am having is that the order is submitted successfully, but it never transitions to Active or triggers, even when the market price clearly crosses the activation_price. Has anyone encountered this "failure to activate" issue with Quote data?

---

#### [2025-12-28 02:12:02] @yite7836

Hi team,
I am currently running the example and facing the problem: https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/live/bybit/bybit_ema_cross.py, for the first run, it looks good.  However, it is looks like it caches something, and lead to some failure after I re-run it, can you give me some suggestion for further study it?

**Attachments:**
- [fail.log](https://cdn.discordapp.com/attachments/924499913386102834/1454658123221700673/fail.log?ex=695e69b2&is=695d1832&hm=e1b545eb02cb8494db03b6c25f4d73a57177f80be5dad76679ab217967f17c1e&)

---

#### [2025-12-28 07:53:21] @georgey5145

```
2025-12-28T07:42:31.769776976Z [ERROR] TESTER-001.TradingNode: Error on run
RuntimeError(cannot recalculate balance when no current balance)
Traceback (most recent call last):
  File "/home/ubuntu/venvs/nt_trader/lib/python3.13/site-packages/nautilus_trader/live/node.py", line 298, in run
    self.kernel.loop.run_until_complete(self.run_async())
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "uvloop/loop.pyx", line 1518, in uvloop.loop.Loop.run_until_complete
  File "/home/ubuntu/venvs/nt_trader/lib/python3.13/site-packages/nautilus_trader/live/node.py", line 349, in run_async
    await self.kernel.start_async()
  File "/home/ubuntu/venvs/nt_trader/lib/python3.13/site-packages/nautilus_trader/system/kernel.py", line 1030, in start_async
    self._initialize_portfolio()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/ubuntu/venvs/nt_trader/lib/python3.13/site-packages/nautilus_trader/system/kernel.py", line 1292, in _initialize_portfolio
    self._portfolio.initialize_positions()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "nautilus_trader/portfolio/portfolio.pyx", line 324, in nautilus_trader.portfolio.portfolio.Portfolio.initialize_positions
  File "nautilus_trader/portfolio/portfolio.pyx", line 385, in nautilus_trader.portfolio.portfolio.Portfolio.initialize_positions
  File "nautilus_trader/accounting/manager.pyx", line 425, in nautilus_trader.accounting.manager.AccountsManager.update_positions
  File "nautilus_trader/accounting/accounts/margin.pyx", line 377, in nautilus_trader.accounting.accounts.margin.MarginAccount.update_margin_maint
  File "nautilus_trader/accounting/accounts/margin.pyx", line 476, in 
nautilus_trader.accounting.accounts.margin.MarginAccount._recalculate_balance
```
i encountered this error when i was trying to run node with 2 exec clients BYBIT and IB, but i can run successfully with either one of them, can anyone help me on this?

code here: https://github.com/nautechsystems/nautilus_trader/discussions/3354

**Links:**
- RuntimeError(cannot recalculate balance when no current balance) ·...

---

#### [2025-12-28 09:32:37] @cjdsellers

Hi <@765636132636590130> 
Thanks for the report, you were hitting an edge case when the positions currency has no corresponding account balance. This should now be fixed (made more robust) and available in development wheels soon: https://github.com/nautechsystems/nautilus_trader/commit/d13aa0a2bc8be1634762f34b5158daade4ffe768

**Links:**
- Improve margin account balance recalculation robustness · nautechs...

---

#### [2025-12-29 08:09:04] @georgey5145

thanks for quick reply! i've tested and it works now!

---

#### [2025-12-30 09:05:06] @georgey5145

but there  is another issue, when i tried to retrieve account info using self.portfolio.account(venue) in a strategy, i always got IB account info no matter the venue parameter is IB_VENUE or BYBIT_VENUE when i ran node with both BYBIT and IB settings, i can only get BYBIT account info if i only run node with BYBIT, is this normal?

---

#### [2025-12-31 14:33:48] @heliusdk

Hey just wanted to thank you for the advice, have this in forward testing right now, and its killing it.

After watching what went wrong on a chart a few days, I paired it with some weak stationarity, and sprinkled a little multi timeframe overview on the top, making it less jumpy and less prone to sideways markets.

Probably also a good idea to look into volatility scaling given distributions, but thats for 2026, the image is for roughly 4k trades.

Also thanks for all the hard work in Nautilus to you and the team 😀 
Happy new year 🎆

**Attachments:**
- [vwap.jpeg](https://cdn.discordapp.com/attachments/924499913386102834/1455931955987091721/vwap.jpeg?ex=695e6ecc&is=695d1d4c&hm=c25da7ae8a716d74bb374b70ec9cb5338cbd4f2de7c4552ada2da96468b56f2f&)

---

#### [2025-12-31 14:45:20] @faysou.

I like your graphs 🙂 if you can see how to improve the recently introduced visualisation in nautilus it would be great.

---

#### [2026-01-01 23:15:22] @heliusdk

Thanks <@965894631017578537> , I'll look at it next week 🙂

---

#### [2026-01-04 05:55:32] @thisisrahul.

While backtesting, request_bars doesn’t give out any data(doesn’t call on historical data), it works fine while live trading. Is request_bars only to be used for live trading?
The data present in the catalogue has data older than the backtesting start date so shouldn’t be a problem

---

#### [2026-01-04 15:51:07] @haakonflaar

Are you using the high level or low level API? I am curious of the same thing, but I am using the low level API and naturally only add data equal to the length of the backtest which is why I think request_bars doesn't actually fetch any data (should work if I add data prior to backtest start though, but haven't tried). I believe it should work seamlessly with the high level API though as I believe it fetches data directly from the catalog.

---

#### [2026-01-04 15:55:46] @thisisrahul.

I have tried both, in low level I have added data older than the start time to the engine. Doesn’t work
In high level, I have provided the path to the catalogue, ensured it contains data older than the start time of the strategy, then passed in manually created start time (older than start of backtest) to request_bars, but it doesn’t work.
Subscribe bars works as expected

---

#### [2026-01-04 15:57:10] @thisisrahul.

I can’t debug the code as the engine.pyx is in cython

---

#### [2026-01-04 17:43:30] @thisisrahul.

Found the issue. Had to add the DataCatalogConfig to BacktestEngineConfig. Now it’s working

---

#### [2026-01-04 17:44:52] @thisisrahul.

So we have to add the catalogue twice, once in BacktestDataConfig and once in BacktestEngineConfig as mentioned above

---

#### [2026-01-04 20:50:53] @_yourfriend

is it possible to do paper trading with polymarket out of the box or is anything needed?

---

#### [2026-01-05 04:06:35] @cjdsellers

Hey <@645331124335411255> if by paper trading you meant live data with simulated execution (by Nautilus, not a real-time paper trading account with Polymarket) - then yes, it's theoretically possible to set this up - it would just take a bit of work. There will be some time invested into the Polymarket adapter (Rust port) and further tutorials very soon (within Q1)

---

#### [2026-01-05 04:09:19] @_yourfriend

got it, thanks!

---

#### [2026-01-05 19:09:50] @heliusdk

My suggestion and someting I wont mind contributing with would be:
- Buy and hold comparison per asset on the equity curve, just like my visuals, one thing is profitable, an other is if you actually gain anything.
- Trade calander just optional
- Anuallized return distribution

The other things I have added seems niche and not really for everyone, for example my drawdown chart has number of trades as bars below, to display if there is a connection between good/bad dradown and number of trades, e.g a few trades running up a backtest and the rest just being bad.

The trade distribution by time of day, but that also enters a space thats harder to model, because if you have instruments backtested at the same time, and they have different opening hours its just noise and confusion to people.

I dont think any of my more advanced charts would be of value either.

Can anyone provide some feedback if they see a value in getting that information and something I should make a pull request for in Nautilus?

---

#### [2026-01-05 19:11:52] @heliusdk



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1457813874278404106/image.png?ex=695eaff8&is=695d5e78&hm=a29f42b08143e8c183b50296d362ec4faf376435dcd8ee8b9be86450204ee00d&)

---

#### [2026-01-05 19:14:56] @faysou.

Thanks for your reply. I think that given the visualisation feature is modular the more options the better.  If you think something is useful it's likely useful to other people.

---

#### [2026-01-05 19:16:51] @heliusdk

Okay I guess that makes sense 😅 
I'll make a PR 🙂

---

#### [2026-01-06 06:54:11] @thisisrahul.

Thanks, the visualisation looks really beautiful, if you are at it, is it possible to scale the drawdown chart? It’s hard to read the red line

---

#### [2026-01-06 08:41:01] @faysou.

I think better to let <@1273010294033219642> do something first, then it can be modified if needed.

---

#### [2026-01-06 14:55:02] @acecuffs

hey<@1032691280448323636>

---

#### [2026-01-06 14:55:16] @acecuffs

Hey<@1273010294033219642>

---

#### [2026-01-06 23:33:47] @akatsuki_alpha__42583

Hey all — I'm deploying Nautilus Trader in a Kubernetes cluster and trying to use GCP Memorystore (Redis) over PSC with TLS. The MessageBus Redis connection fails with TLS validation errors (unknown CA / hostname mismatch). It looks like Memorystore’s server cert SAN doesn’t match the PSC endpoint, so strict hostname verification fails even when the CA is trusted. Has anyone successfully connected NT’s MessageBus to Memorystore via PSC? Any pointers would help — thanks!

---
