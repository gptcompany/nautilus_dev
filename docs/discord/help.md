# NautilusTrader - #help

**Period:** Last 90 days
**Messages:** 285
**Last updated:** 2025-12-22 18:01:42

---

#### [2025-09-23 19:19:07] @kadyrleev

Hello! A quick Q: has macosx_14_0_arm64 support been dropped? Cannot install the latest version using UV - getting error and hint: You're on macOS (`macosx_14_0_arm64`), but `nautilus-trader` (v1.220.0) only has wheels for the following platforms: `manylinux_2_35_aarch64`, `manylinux_2_35_x86_64`, `macosx_15_0_arm64`, `win_amd64`;

---

#### [2025-09-23 19:25:57] @kadyrleev

It's still a supported macOS version receiving updates.

---

#### [2025-09-23 20:51:50] @ido3936

Hello, 

I am trying to work out whether NT is robust enough to pick up on state after having been stopped. Currently trying out reconciliation. NT version is 1.221.0a20250921. I have `reconciliation=True` and `external_order_claims` set to a single instrument's id. I am running on top of IB paper trading.

In a previous run I had bought some shares of a stock:
```
2025-09-23T15:18:02.605317353Z [WARN] IB_LIVE-001.U_spread: Order filled: STOP_MARKET BUY U 2025-09-23 1
2025-09-23T15:18:02.605524933Z [INFO] IB_LIVE-001.U_spread: <--[EVT] PositionOpened(instrument_id=U.NYSE
2025-09-23T15:18:02.606139770Z [WARN] IB_LIVE-001.U_spread: POSITION OPENED: STOP_MARKET PRICE: 45.9
```

I  then stop NT, and restart it. Reconciliation is at work, and the existing position is picked up
`2025-09-23T15:20:00.073033728Z [INFO] IB_LIVE-001.U_spread: Is in position: Position(LONG 3 U.NYSE, id=U.NYSE-EXTERNAL)`

My strategy then correctly closes the position:
```2025-09-23T15:20:00.073676424Z [INFO] IB_LIVE-001.U_spread: Market sell order submitted (3 shares)
2025-09-23T15:20:02.452011084Z [WARN] IB_LIVE-001.U_spread: Order filled: MARKET SELL U 2025-09-23 15:20:00.073133549 
```

AND THIS IS THE STRANGE PART: I get a PositionOpened event, as NT interprets what has hapened as a new SHORT position:
`2025-09-23T15:20:02.452206601Z [INFO] IB_LIVE-001.U_spread: <--[EVT] PositionOpened`


My questions:
1. There are quite a few flags and params related to reconciliation - should I be setting them, in prder to avoid this ?
2. I've also tried using redis to persist the cache , but could not understand its interaction with the reconciliation mechanism so I dropped it. Should I be using it instead of reconciliation? Or on top of it?
3. Final option: is this a bug in NT?

---

#### [2025-09-24 15:06:20] @roma_21514

Hi friends, 
I need some help.

Instrument: BTCUSDT-PERP.BINANCE
Catalog: ./catalog → actually /home/ubuntu/nautilus/catalog
Data: OrderBookDelta (L2 MBP) for 2025-08-01 12:00:00Z–15:00:00Z

Problem
After downloading/saving the instrument settings to a file, a different price precision is written than what the actual order book data requires.

Download by using function
async def instrument():
    http_client = nautilus_pyo3.TardisHttpClient()
    catalog = ParquetDataCatalog('./catalog')

    symbols = ['BTCUSDT']
    exchange = 'binance-futures'

    pairs = []
    for symbol in symbols:
        instr_tardis = (await http_client.instruments(exchange=exchange, symbol=symbol))[0]
        pair = CurrencyPair.from_dict(instr_tardis.to_dict())
        print(f"Received: {pair}")
        pairs.append(pair)

    catalog.write_data(pairs)


Logs:
INSTRUMENT\_ID: BTCUSDT-PERP.BINANCE
INSTRUMENT (catalog): CurrencyPair(... instrument\_class=SPOT, price\_precision=2, price\_increment=0.01, size\_precision=3, size\_increment=0.001, lot\_size=1, ...)
...
2025-08-01T12:00:41.106159000Z \[ERROR] BACKTESTER-001.BacktestNode: Error running backtest
RuntimeError(fill\_price.precision=1 did not match instrument price\_prec=2)
...
price\_increment (engine): 0.01
qty\_increment (engine):   0.0
lot\_size (engine):        1.0

If I dump the instrument dict I see:
CurrencyPair(id=BTCUSDT-PERP.BINANCE, raw\_symbol=BTCUSDT, asset\_class=CRYPTOCURRENCY, instrument\_class=SPOT, quote\_currency=USDT, is\_inverse=False, price\_precision=2, price\_increment=0.01, size\_precision=3, size\_increment=0.001, multiplier=1, lot\_size=1, margin\_init=0, margin\_maint=0, maker\_fee=0.0002, taker\_fee=0.0004, info={})

Actual prices in OrderBookDelta are multiples of 0.1 (precision=1), while the catalog/engine instrument has price\_precision=2 and price\_increment=0.01. As a result, the backtest fails with a precision validation error when simulating fills.

---

#### [2025-09-24 15:06:21] @roma_21514

What I tried

* Checked the instrument via ParquetDataCatalog: it shows price\_precision=2, price\_increment=0.01.
* Tried passing price\_increment\_override=0.1 into the strategy — doesn’t help (the engine validates against the instrument from the catalog).

When saving instrument settings to a file, the parameters should be consistent with the real data granularity (in my case price\_precision=1, price\_increment=0.1), or the original PERP-class instrument should be correctly preserved instead of SPOT. I could update the file manually, but that would be fragile on overwrite and may surface for other instruments. Right now the file ends up with price\_precision=2, price\_increment=0.01, and even instrument\_class=SPOT, which doesn’t match the data or the \*-PERP identifier.

Could you advise where the substitution/incorrect writing of instrument metadata might be happening during export to the catalog? How can I reliably set price\_precision=1, price\_increment=0.1, size/qty\_increment=0.001, lot\_size≈0.001, and the correct class (PERP) so that both the backtest and engine.cache.instrument(...) read these values? 

If I choose ETHUSDT or BTCUSDC as the instrument, the issue does not occur — those load correctly.

---

#### [2025-09-24 16:11:02] @ido3936

continuing https://discord.com/channels/924497682343550976/924499913386102834/1420150693909762069

When I try to use the DB backed cache for persistence - I get these errors when pre-existing positions (aka EXTERNAL) are analyzed by NT:
Maybe this is the result of the same problem  - Nautilus confuses the closing of a LONG position with the opening of a SHORT one ?
<@757548402689966131> does this make any sense? Any idea about how to go about it would be appreciated


```
2025-09-24T15:55:03.255048949Z [ERROR] IB_LIVE-001.ExecClient-INTERACTIVE_BROKERS: Error handling position update: invalid `value` less than `QUANTITY_MIN` 0.0, was -9.0
2025-09-24T15:55:03.258742878Z [ERROR] IB_LIVE-001.ExecClient-INTERACTIVE_BROKERS: Error handling position update: invalid `value` less than `QUANTITY_MIN` 0.0, was -4.0
2025-09-24T15:55:03.577197295Z [ERROR] IB_LIVE-001.ExecEngine: Unexpected exception in event queue processing: TypeError('Encoding objects of type nautilus_trader.model.objects.Price is unsupported')
TypeError(Encoding objects of type nautilus_trader.model.objects.Price is unsupported)
Traceback (most recent call last):
  File "/home/ido/code/Trading/.venv/lib/python3.12/site-packages/nautilus_trader/live/execution_engine.py", line 523, in _run_evt_queue
    self._handle_event(event)
...
  File "nautilus_trader/execution/engine.pyx", line 1371, in nautilus_trader.execution.engine.ExecutionEngine._apply_event_to_order
  File "nautilus_trader/cache/cache.pyx", line 2390, in nautilus_trader.cache.cache.Cache.update_order
  File "nautilus_trader/cache/database.pyx", line 1159, in nautilus_trader.cache.database.CacheDatabaseAdapter.update_order
  File "nautilus_trader/serialization/serializer.pyx", line 110, in nautilus_trader.serialization.serializer.MsgSpecSerializer.serialize
```

---

#### [2025-09-25 01:34:51] @cjdsellers

Hi <@972768642636853309> 
We only support the version of macOS the GH `macos-latest` runner images are using (we don't have the capacity to support multiple macOS versions as it would mean an additional 3 CI jobs and 3 wheels produced). I've updated the installation guide to describe this more clearly https://github.com/nautechsystems/nautilus_trader/blob/develop/docs/getting_started/installation.md
I would expect you could still build from source though - I hope that helps!

---

#### [2025-09-25 01:41:40] @cjdsellers

Hi <@1074995464316928071> 
You already found the `external_order_claims` config, which is the main one which trips people up when restarting without a backing cache and expecting strategies to take control of external orders (this must be specified explicitly with `external_order_claims` as you're doing). I think the issue with the position going SHORT is how Nautilus treats spot-like assets. i.e. it doesn't by default regard holding a spot asset as automatically having a long position, but treats this as a "delta" from a starting state if that makes sense.

We did incorporate spot position reports into Bybit recently which is opt-in and represents any positive wallet balance as a LONG position, or negative wallet balance (borrowing) as a SHORT (care must be taken as Nautilus will then "liquidate" these positions to the quote asset if `close_all_positions()` is then called). There are no plans currently to make this more generic across the platform. I hope that sheds some more light!

- https://nautilustrader.io/docs/nightly/concepts/live#reconciliation
- https://nautilustrader.io/docs/nightly/concepts/live#execution-reconciliation

---

#### [2025-09-25 03:33:48] @aaron_g0130

I need some help on learning nt, if I want to understand the underlying running order and logic of NautilusTrader  (such as the order in which various on_ events are triggered and under what circumstances they are triggered or not), which part of the source code should I focus on

---

#### [2025-09-25 11:54:15] @fatcat3531

Hi, do you have plans to make the bitget adapter public?

---

#### [2025-09-25 18:24:20] @kadyrleev

No worries at all! Thanks for clarifying this 🙏

---

#### [2025-09-26 05:20:08] @ido3936

Thanks <@757548402689966131> , after some hours debugging this I realized that my interpretation of what was going on was wrong: NT was not confusing the closing and opening of positions  - it was simply allowing both to exist simultaneously. 
So what was happening was that the oms_type for the strategy was not being set explicitly as NETTING. Once I set it during strategy initialization the problem was solved (still others remain but one at a time...)
Maybe someone will find this useful down the road

---

#### [2025-09-26 05:23:21] @cjdsellers

Hey <@1074995464316928071> glad to hear you managed to get to the bottom of that one. Here are some more useful docs if it helps (and describes that config default): https://nautilustrader.io/docs/nightly/concepts/execution#oms-configuration

**Links:**
- NautilusTrader Documentation

---

#### [2025-09-27 14:44:34] @redyarlukas

I'm implementing an option straddle strategy that needs to dynamically discover and subscribe to option instruments during backtesting. The strategy successfully finds option contracts from the catalog, but fails when trying to subscribe to their quote data:

ERROR: Cannot find instrument XLP170224C00052000.OPRA to subscribe for QuoteTick data, No data has been loaded for this instrument

When I understand correctly, the BacktestDataConfig requires pre-specifying all instruments `instrument_ids`. You cannot dynamically subscribe to instruments during a backtest that weren't pre-loaded.
Whats the recommended approach for strategies that need to dynamically subscribe to instruments (especially options) during backtests? Simply loading all instruments would mean all data must fit into the memory right? So in this case this would not be an option.

---

#### [2025-09-28 06:29:57] @herhz

I have a simliar problem. don't know if the solution fits your case. here's how I solved it with `DataCatalogConfig`. I ask chatgpt to write a function to trigger the data engine find the instrument and load it into the cache dynamically. I hope there's a more direct way to achieve this.

https://github.com/nautechsystems/nautilus_trader/blob/490a6297ce5da493dc5268791ebfb614095f9b51/nautilus_trader/data/engine.pyx#L1404

```
def find(self, instrument_id: InstrumentId) -> Instrument | None:
    # expects the instrument exists in catalog, issues a request to trigger query
    params = {}
    params["update_catalog"] = False

    request_id = UUID4()
    request = RequestInstrument(
        instrument_id=instrument_id,
        start=None,
        end=self._clock.utc_now(),
        client_id=None,
        venue=instrument_id.venue,
        callback=self._handle_instruments_response,
        request_id=request_id,
        ts_init=self._clock.timestamp_ns(),
        params=params,
    )

    fut: asyncio.Future = self._loop.create_future()
    self._pending_requests[request_id] = fut

    self._msgbus.request(endpoint="DataEngine.request", request=request)

    try:
        result = self._loop.run_until_complete(fut)
        return result
    finally:
        self._pending_requests.pop(request_id, None)

def _handle_instruments_response(self, response: DataResponse) -> None:
    fut = self._pending_requests.get(response.correlation_id)
    if not fut:
        return

    # assuming response contains `instrument`
    if not fut.done():
        fut.set_result(response.data)

```

**Links:**
- nautilus_trader/nautilus_trader/data/engine.pyx at 490a6297ce5da493...

---

#### [2025-09-28 07:14:31] @redyarlukas

Thanks for the hint. But if it's that easy, why is it not supported officially? Where is the catch? 

Currently I try to get around with a small chunking_size but loading tens of  thousands of instruments this does not feel right and does not scale (and I still run into memory issues).

---

#### [2025-09-28 07:15:48] @redyarlukas

@faysou I think your solution might help me. What did you do?

---

#### [2025-09-28 07:28:52] @faysou.

Look in the code and the examples

---

#### [2025-09-28 07:34:01] @faysou.

Look for the word duration

---

#### [2025-09-29 15:29:49] @redyarlukas

Mh, I am sorry but I think I cannot follow. Could you guide me a bit more into the right direction?

---

#### [2025-09-29 15:31:50] @faysou.

The feature is still experimental and undocumented, you will need to look at the source code to see how it works.

---

#### [2025-09-29 15:33:49] @redyarlukas

Okay will do, but i dont understand the duration part

---

#### [2025-09-29 15:35:30] @faysou.

Search for this string in the repo and you will see where this feature is used.

---

#### [2025-09-29 22:25:46] @porciletto

Hi! I’m having an issue with my backtesting (using 1.220.0). Here’s my process:

* At the start of the day, I load the bars of the securities I know will pass the first filter, to avoid loading too much data.
* I run my logic.
* When I’m about to submit an order, I inject the next 20 minutes of ticks for that security into the engine (again using engine.add_data()).

Here’s what happens:
* The first time each security is processed, everything works as expected.
* The second time (and any subsequent time) in the same run that the same security is processed, it seems as if the very last tick from the first period is still being considered. In my case, that tick ends up triggering an order.

I don’t think this is a bug in Nautilus, but rather the result of me forcing things with the “dynamic injections” I mentioned above. Any suggestions?

I tried using engine.clear_data() at the end of the day to remove the used data, but that just stops the run. I also tried setting the tick capacity of CacheConfig to a very low value, but I’m probably missing something.

That said, if you think this might be a bug, I can work on a minimal reproduction. If you’re interested, I’ve attached a log: search for `44.81` and it should be very clear.

Thanks in advance!

**Attachments:**
- [LUV3.txt.zip](https://cdn.discordapp.com/attachments/924499913386102834/1422348659734876210/LUV3.txt.zip?ex=694a6e2a&is=69491caa&hm=b85b6c234f08d19b9b13e0b4941fc61d2718c5cffd6d9c2ff567831a287778b9&)

---

#### [2025-09-30 03:23:55] @xcabel

sry to dig out one year old thread but do we know what this ClientId is for?
there are many objects having class/object functions that will take in ClientId. But do we have any pointer to some walkthrough how we should organize them?
I search the doc but cannot find useful info and the channel it seems to be relevant multiple venue and multiple instrutments?

---

#### [2025-10-02 08:26:51] @manofculture5873

could anyone point me to an example of backtesting option strategies?

---

#### [2025-10-02 11:00:35] @porciletto

Hi! I’m having an issue with my

---

#### [2025-10-04 20:21:35] @haakonflaar

What is the name of the parameter to set a bar offset from start of day (do you have a list of params - I can't seem to find it in the code)? Can I use it to enforce a bar to always be formed from regular trading hours market open (say for 50-minute bars from 9:30 AM ET to 10:20 AM)?

---

#### [2025-10-04 20:24:03] @haakonflaar

Also, if I request 50-min bars and enforce a bar to form at 10:20 AM (market open - 9:30-10:20 AM), can I also enforce a bar to be closed at market close even though the full 50-min is not formed yet (in this case the 3:20-4:00 PM 40-min bar)? That is how the "Break at end of day" logic at NinjaTrader works.

---

#### [2025-10-04 20:28:53] @faysou.

the timebaraggregator only supports regular bars for now. you can look in aggregation.pyx for more details, also in the data engine.pyx to see how the time bar origin is passed, it's either through a data engine config or through  a params dict

---

#### [2025-10-04 20:46:54] @haakonflaar

Hmm, so are you using `time_bars_origin_offset` to set the offset from midnight (00:00 UTC)?

---

#### [2025-10-04 20:47:15] @faysou.

yes

---

#### [2025-10-04 20:58:32] @haakonflaar

Hmm, I am having trouble setting hours + minutes as offset, but I guess I can fix it by starting the backtest at the desired time. In any case it will cause a problem for when using bars that does not divide by 24 hrs, such as 50-minute bars - on the next day the bar closing time will shift by 10 minutes. Maybe it could be nice with some break at end of day functionality.

---

#### [2025-10-04 20:59:43] @faysou.

there's no concept of trading day in nautilus yet. for now nautilus is mostly designed for cryptos, and cryptos are on all the time

---

#### [2025-10-04 21:00:32] @faysou.

but yes, best thing to use for now are bar lengths that are periodic daily

---

#### [2025-10-04 23:31:39] @xcabel

```
offset = self.atr.value * self.config.trailing_atr_multiple
        order: TrailingStopMarketOrder = self.order_factory.trailing_stop_market(
            instrument_id=self.config.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.config.trade_size),
            # limit_offset=Decimal(f"{offset / 2:.{self.instrument.price_precision}f}"),
            # price=self.instrument.make_price(last_quote.bid_price.as_double() - offset),
            trailing_offset=Decimal(f"{offset:.{self.instrument.price_precision}f}"),
            trailing_offset_type=TrailingOffsetType[self.config.trailing_offset_type],
            trigger_type=TriggerType[self.config.trigger_type],
            reduce_only=True,
            emulation_trigger=TriggerType[self.config.emulation_trigger],
        )

        self.trailing_stop = order
        self.submit_order(order, position_id=self.position_id)
```

I followed the strategy example code to submit a trailing stop market order. but I got an order that my trigger_price is none. I searched around but cannot find similar issue.

---

#### [2025-10-05 04:31:19] @rk2774

this is from `cdef class BarSpecification:` in `nautilus_trader\model\data.pxd`

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1424252592950870057/image.png?ex=694ac3d7&is=69497257&hm=51c13c350f1981772cb165f5d812fb35fa36f1da416050734dddd00a7bbcd0da&)

---

#### [2025-10-05 05:00:36] @cjdsellers

Hey <@950260043637465128> 
Thanks for the report. We definitely need more information to be able to help:
- Is this backtest or live?
- Which adapter and instrument?
- Which version?

---

#### [2025-10-05 08:59:40] @haakonflaar

Right, I have no issue aggregating to say 40 or 50 min bars though (no error is raised). However, controlling first bar of day is trickier.

---

#### [2025-10-05 18:28:02] @xcabel

thanks!  it can definitely be my user error. I figured it out myself which is to set the trigger_instrument_id manually by carrying over from instrument_id then it works fine. It can be b/c my strategy subscribe to multiple instrument id data.

1. this is backtest instead of live
2. im using some features from polymarket adapter and binaryoption instrument
2.1 im not sure I use the adapter right b/c I also notice that polymarket order side enum in polymarket is not mapped to an integer this was also causing me generic order factory market order initiation failure (but it can be that I should use some polymarket specfic order factory?) I fixed that issue by using generic order side
3. version=1.220.0

---

#### [2025-10-06 01:18:04] @wi11r2492

Does anyone know if I can use MlFinLab https://hudsonthames.org/mlfinlab/  ,along with my databento historical data on Nautilus Trader to build a trading strategy ?

**Links:**
- MlFinLab - Hudson & Thames

---

#### [2025-10-06 18:28:40] @dariohett

Just asked in <#1332664677041442816>  but are there any concerns querying portfolio.net_position(instrument_id) from an actor? I’ve observed a Buy resulting in a negative net_position, but it might be an adapter-specific issue (despite the portfolio correctly finding a positive position on restart)

---

#### [2025-10-08 00:56:15] @falls7202

does  "nautilus_trader/adapters/okx " support this feature :  "set leverage"  ?

---

#### [2025-10-08 14:15:47] @projectmillen1507

Thank you very much. I did the Dockerized connection and it works. It just a hassle of having to rebuild the portfolio monitor while TWS provides a native one...

---

#### [2025-10-09 09:15:31] @one_lpb

Hello !

I'm having a little issue with data loading. I have this code to load historical data before "live data" in backtesting but nothing is logged in my on_historical_data method... logs and code in .txt attached.

Thanks for the help !

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/924499913386102834/1425773664720261151/message.txt?ex=694a5db3&is=69490c33&hm=dbb0f89c86697d787ec6344c4335ce476b2db7660255048721e0fe4d9a4fe800&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793206624456764/image.png?ex=694a6fe6&is=69491e66&hm=8a0112e57e0f492dc730d84d15d900dd6f455cc5a4c82c725ccf857068ada150&)
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793207010328698/image.png?ex=694a6fe6&is=69491e66&hm=290aa5b3218bbe834437efec771c226ec267b8008b88eff7e0ec41c526de9015&)
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793207433822299/image.png?ex=694a6fe6&is=69491e66&hm=9848ebb8fbba01fb04a42249674807c95bef32b2fd3d5b373bc62fb2babd2b00&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1426653445313532004/image.png?ex=694a454f&is=6948f3cf&hm=63fec4695522d12a2a824ae29a6a9543aedd72a583db7e1e29a39e9988a47add&)

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
- [logs.rtf](https://cdn.discordapp.com/attachments/924499913386102834/1428392145982717953/logs.rtf?ex=694aa9d9&is=69495859&hm=58b9d0a87382e49cccb218eba3696c06fe82643a17c38060a2f655480093383c&)

---

#### [2025-10-16 15:42:46] @one_lpb

I made some tests and it looks like that on TP (SELL LIMIT when LONG on futures) NT fill half of total position contracts and cancel  STOP_MARTKET and LIMIT orders, instead of continuing to reduce order sizes... Maybe there is something I didn't catch ?

---

#### [2025-10-16 15:49:47] @one_lpb



**Attachments:**
- [logs.rtf](https://cdn.discordapp.com/attachments/924499913386102834/1428409601749028885/logs.rtf?ex=694aba1b&is=6949689b&hm=f54230ef19026d968041bbb0c0bdd77a3d1256f7a701c186be813007337d9660&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430081112419340308/image.png?ex=694a3752&is=6948e5d2&hm=d2be67e820c2440fa189429284e50f6b3f75346286e56e16d522845b05e0c147&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430490527274373182/image.png?ex=694a631e&is=6949119e&hm=4105acdb8d0c5f851394b1155f39beaf6598f06e40df392f898f73d2b3fcd625&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430582634265710592/image.png?ex=694ab8e6&is=69496766&hm=02e837bb870df739acda6a6e18892239a5693b479a232ed868dc04477a14e03b&)

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
- [simple_test_run.py](https://cdn.discordapp.com/attachments/924499913386102834/1431692384483410101/simple_test_run.py?ex=694acdf0&is=69497c70&hm=216bff4e921233103bd7ef7ccd7a4811094d1fe7e7798f83fa6ba585973186a6&)

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
- [logs.txt](https://cdn.discordapp.com/attachments/924499913386102834/1433263344059551875/logs.txt?ex=694a9641&is=694944c1&hm=86a28534472f516c5a31cf00cf0ca3ef22f37d5c7b29a409a7183d81009b128a&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1433972894240870501/image.png?ex=694a8813&is=69493693&hm=8af2dd45cbe1d2e3cb8373b74d31699617d13d7fea6a3c9d15fb9aff17730f53&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435202086034870292/image.png?ex=694a639a&is=6949121a&hm=07ce2262fc286b9d2f6491505adc06f80f584deec652c64cf6f438bfaf08fe7f&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435212583664615456/image.png?ex=694a6d60&is=69491be0&hm=a94e478b62c17615147bdaa338a48b55f474431ff35035b043706cdfa1309936&)

---

#### [2025-11-04 10:23:36] @jonathanbytesio

And I ran the polymarket_data_tester.py on jupyterlab

---

#### [2025-11-04 10:23:44] @jonathanbytesio

It suddenly closed

---

#### [2025-11-04 11:39:49] @jonathanbytesio



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435232063019028511/image.png?ex=694a7f85&is=69492e05&hm=13511f7a98f0862a605dee72fd1db54fec9a911d828365a1c00b2dc6085466f1&)

---

#### [2025-11-04 12:05:52] @jonathanbytesio

from nautilus_trader.cache.cache import Cache
  File "nautilus_trader/cache/cache.pyx", line 1, in init nautilus_trader.cache.cache
KeyError: '__reduce_cython__'

---

#### [2025-11-04 21:23:55] @joebiden404

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

#### [2025-11-05 00:01:15] @joebiden404

Yep, so basically:
Using latest version with Python;

1. I’ve loaded the my past 3 days MBO data with the databento loader into the parquet catalog.

2. Then every operation I’m doing it is just panicking for some reason..

For example

---

#### [2025-11-05 00:01:17] @joebiden404

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

#### [2025-11-05 00:02:12] @joebiden404

not only 
> catalog.order_book_deltas()[0]

almost every function crushing it 🙁

---

#### [2025-11-05 00:06:14] @joebiden404

Lmk if you need more info

---

#### [2025-11-05 02:54:25] @jonathanbytesio

I see, you updated this, but it's in nightly version, right?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435462231717580863/image.png?ex=694aad21&is=69495ba1&hm=7b8c18729f2a49198b546ddf1568ea93e5b6ac9991c0fe4cf2b3626f584dd509&)

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

#### [2025-11-05 17:29:02] @joebiden404

do you know what I should I look for? Undefined prices?

---

#### [2025-11-05 17:32:41] @joebiden404

The data gets loaded, then boom...

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435683255675519128/image.png?ex=694ad239&is=694980b9&hm=3829219b8f0e2614d488ba6385bd3a6dc7f08e79b0b871fe8349320435bb8db8&)

---

#### [2025-11-05 18:28:19] @joebiden404

breaks here

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1435697255490519051/image.png?ex=694a3683&is=6948e503&hm=3e510b2488c4f00e7cbdd27708ce0c0d2a7a9182e7c522cc806ee4d4de846643&)

---

#### [2025-11-05 18:32:00] @joebiden404

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

#### [2025-11-07 04:31:14] @joebiden404

Hey, Is there any way I can handle it myself?

---

#### [2025-11-07 04:32:30] @joebiden404

I meant, on which row/col of the parquet may cause this dramatic fail

---

#### [2025-11-07 07:52:57] @javdu10

In the github itself there are few adapters you can take example on under the « adapters » folder

---

#### [2025-11-07 12:13:40] @bre_n

Does anyone use BacktestNode? I'm always getting the below error. All the examples use BacktestEngine, should I just go for that instead?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1436327744530157608/image.png?ex=694a8773&is=694935f3&hm=bd823552c377e581b352f3db8bab444c15914de72fbdac36d1fcd5df06c80f2e&)

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

#### [2025-11-07 16:03:33] @joebiden404

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

#### [2025-11-07 16:04:55] @joebiden404

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

#### [2025-11-08 00:26:10] @joebiden404

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
- [Screenshot_2025-11-11_at_09.33.53.png](https://cdn.discordapp.com/attachments/924499913386102834/1437737819064766515/Screenshot_2025-11-11_at_09.33.53.png?ex=694a62af&is=6949112f&hm=cf1ca3431ac07cd975352221b0c2ea085c523ae79e3cfe6b2cf66a631ab52f61&)

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
- [compile-fail.txt](https://cdn.discordapp.com/attachments/924499913386102834/1438481390680408114/compile-fail.txt?ex=694a7431&is=694922b1&hm=35a6d7cf2db37a0833489cf8acb0bf37d4d739387bb1ca31bc042c091afd4ed1&)

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
- [image0.png](https://cdn.discordapp.com/attachments/924499913386102834/1441668289930461375/image0.png?ex=694ad779&is=694985f9&hm=1b82805ae70daf8d628a32431101aa95adff56351e4d3412b83d6b7c6f5857b2&)

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

#### [2025-11-28 03:36:28] @cauta

hi <@965894631017578537> i created an issue: https://github.com/nautechsystems/nautilus_trader/issues/3233
i believe this is missing while implementation `replace_existing` in `StreamingConfig`

**Links:**
- `replace_existing` is not using for setting up `StreamingFeatherWri...

---

#### [2025-11-28 08:05:40] @cauta

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
- [Screenshot_2025-12-18_at_14.55.16.png](https://cdn.discordapp.com/attachments/924499913386102834/1451217303021813830/Screenshot_2025-12-18_at_14.55.16.png?ex=694aa4ef&is=6949536f&hm=80390bd67e36748e04c78fb8d4a284f9e46bd70989de9897d885ababf4eb2158&)
- [Screenshot_2025-12-18_at_15.05.23.png](https://cdn.discordapp.com/attachments/924499913386102834/1451217303365484574/Screenshot_2025-12-18_at_15.05.23.png?ex=694aa4ef&is=6949536f&hm=1e0cde645a3578914ec83600497fd4a03a27662b7ea35e96df5d4d89182dfb0f&)

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
