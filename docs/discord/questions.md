# NautilusTrader - #questions

**Period:** Last 90 days
**Messages:** 551
**Last updated:** 2025-10-23 04:00:27

---

#### [2025-07-26 02:33:47] @ajay_kumar_joshi

Hi folks, when will Quant Trader Course will be available.

---

#### [2025-07-26 02:35:11] @ajay_kumar_joshi

I want to learn about Quant trading. I'm confident with Python. How can I start learning about algo trading? Any suggestion will be helpful.
Thanks in advance.

---

#### [2025-07-26 13:21:01] @aleburgos.

Hello!, I created a couple of indicators which I would like to get the data from a backtest run, it is possible? exists a mechanism to get the data generated from a strategy/indicator?

---

#### [2025-07-26 13:45:16] @aleburgos.

the plan is to be able to use python and rust in the future? or only rust?

---

#### [2025-07-26 13:53:16] @faysou.

Python and rust

---

#### [2025-07-26 13:54:26] @faysou.

There are python bindings in the rust code. In theory it should be possible to do the same thing in python and rust. A rust only strategy would allow skipping calls to the python interpreter.

---

#### [2025-07-26 13:55:39] @faysou.

I think in theory it would even be possible to write a rust strategy from a python notebook. We'll see.

---

#### [2025-07-26 14:12:14] @faysou.

Another idea would be working in a rust notebook as well

---

#### [2025-07-26 16:34:25] @river7816

<@757548402689966131> Hi, can I use the ‘from nautilus_trader.core.nautilus_pyo3 import MessageBus’ messagebus from pyo3. I encounter No constructor defined for MessageBus

---

#### [2025-07-26 19:15:45] @phirox412

Still waiting on a response to this question.

My question is really  about clarification on the different OMS types: https://nautilustrader.io/docs/latest/concepts/execution#order-management-system-oms

`HEDGING: Multiple positions per instrument ID are supported (both long and short)`

When it says multiple positions per instrument ID, would it be better to say that every filled long/short Order maps to a Position? (I am only interested in LONG positions at the moment in case that makes it simpler to explain.)

**Links:**
- NautilusTrader Documentation

---

#### [2025-07-27 00:35:30] @aleburgos.

means that you can open a long and short position at the same time for the same instrument id. Now if you open two longs orders it map into one long position. (entry price would be the avg price between the two order filled price and the position size would be sum of the two orders)

---

#### [2025-07-27 00:41:04] @phirox412

Thanks for clarifying. Am I able to see all long orders that map into a single position?

---

#### [2025-07-28 03:43:38] @cjdsellers

Hi <@500837139198771201> 
Both yourself and <@1065996825590513675> were having an interesting conversation last week. I do intend on responding soon

---

#### [2025-07-29 11:37:59] @haakonflaar

When contributing to the project (right now I'd like to add a couple of indicators), should new functionality be written in pure rust, pure cython or both? Are there clever ways of converting cython code to rust code and/or the other way around?

---

#### [2025-07-30 22:55:42] @aleburgos.

same question, I wrote some missing indicators in python (max_drawdown, cagr, skew, kurtosis, calmar)

---

#### [2025-07-31 03:32:39] @cjdsellers

Hi <@244099030156574730> 

Ideally both, and with tests verifying output parity. It shouldn’t be too hard these days with claude / LLMs if you implement first in the language you’re most comfortable with, referring to existing indicator impls and testing patterns

---

#### [2025-07-31 09:43:18] @tr4derjoe.

Hi, after updating to version 1.219 I am experiencing some problems with my MarketDataClients.
After this line was added (https://github.com/nautechsystems/nautilus_trader/blob/master/nautilus_trader/data/engine.pyx#L1978) I get the following failure when invoking _handle_data_response where data is of the type OrderBookDeltas .
```Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "nautilus_trader/data/client.pyx", line 1142, in nautilus_trader.data.client.MarketDataClient._handle_data_response
  File "nautilus_trader/data/client.pyx", line 1154, in nautilus_trader.data.client.MarketDataClient._handle_data_response
  File "nautilus_trader/common/component.pyx", line 2510, in nautilus_trader.common.component.MessageBus.send
  File "nautilus_trader/data/engine.pyx", line 713, in nautilus_trader.data.engine.DataEngine.response
  File "nautilus_trader/data/engine.pyx", line 725, in nautilus_trader.data.engine.DataEngine.response
  File "nautilus_trader/data/engine.pyx", line 1871, in nautilus_trader.data.engine.DataEngine._handle_response
  File "nautilus_trader/data/engine.pyx", line 1913, in nautilus_trader.data.engine.DataEngine._handle_query_group
  File "nautilus_trader/data/engine.pyx", line 1922, in nautilus_trader.data.engine.DataEngine._handle_query_group_aux
  File "nautilus_trader/data/engine.pyx", line 1978, in nautilus_trader.data.engine.DataEngine._check_bounds
TypeError: object of type 'nautilus_trader.model.data.OrderBookDeltas' has no len()```

**Links:**
- nautilus_trader/nautilus_trader/data/engine.pyx at master · nautec...

---

#### [2025-08-01 02:38:36] @brokenhead36

is this crypto platform bitunix?

---

#### [2025-08-01 06:50:54] @tomtom8726

Hey guys, I have a question.

I got order book data with only 5 levels, but I need 10 levels(type: OrderBookDepth10).
Could I fill the missing spots like this?
    •    Empty spots: set price = -1 and size = 0
    •    Market orders: set price = 0 but keep the original size

Is this okay? Will it work for backtest? Really appreciate your answer!

---

#### [2025-08-01 15:11:07] @bluesky.json

Hi yall, I worry if my question would be so amateur yet I come here to ask few things. I am new to nautilus and now trying to wire bybit data to backtest. my goal is to just simply put ema indicator based on the historical data.

I have loaded order book data from bybit and configured backtest as given in the first image.  

when I run, I get the following warning:

2025-06-01T00:00:01.172999936Z [INFO] BACKTESTER-001.TickDataReader: [REQ]--> RequestBars(bar_type=BTCUSDT-LINEAR.BYBIT-100-MILLISECOND-MID-EXTERNAL, start=None, end=None, limit=0, client_id=None, venue=BYBIT, data_type=Bar, params={'update_catalog_mode': None})

2025-06-01T00:00:01.172999936Z [WARN] BACKTESTER-001.DataEngine: Cannot handle request: no client registered for 'None', RequestBars(bar_type=BTCUSDT-LINEAR.BYBIT-100-MILLISECOND-MID-EXTERNAL, start=None, end=None, limit=0, client_id=None, venue=BYBIT, data_type=Bar, params={'update_catalog_mode': None})

2025-06-01T00:00:01.172999936Z [INFO] BACKTESTER-001.TickDataReader: [CMD]--> SubscribeBars(bar_type=BTCUSDT-LINEAR.BYBIT-100-MILLISECOND-MID-EXTERNAL, await_partial=False, client_id=None, venue=BYBIT)

2025-06-01T00:00:01.172999936Z [WARN] BACKTESTER-001.DataEngine: Cannot handle request: no client registered for 'None', RequestBars(bar_type=BTCUSDT-LINEAR.BYBIT-100-MILLISECOND-MID-EXTERNAL, start=2025-06-01 00:00:01.172999936+00:00, end=2025-06-01 00:01:40.972999936+00:00, limit=0, client_id=None, venue=BYBIT, data_type=Bar, params={'start': None, 'subscription_name': 'BTCUSDT-LINEAR.BYBIT-100-MILLISECOND-MID-EXTERNAL'})

since I get

[INFO] BACKTESTER-001.BacktestEngine: Added 54_743 BTCUSDT-LINEAR.BYBIT OrderBookDelta elements

I guess data is being loaded correctly but what is wrong?

**Attachments:**
- [Screenshot_2025-08-02_at_12.07.55_AM.png](https://cdn.discordapp.com/attachments/924506736927334400/1400858394335907983/Screenshot_2025-08-02_at_12.07.55_AM.png?ex=68faee4b&is=68f99ccb&hm=a9843dc86841b2ca1ba262eccc034388ff531ef4592ae18990cce16ffe327b69&)

---

#### [2025-08-02 00:56:23] @cjdsellers

Hi <@1377275524786688101> 
Welcome and thanks for reaching out!
I can see you're adding the `BYBIT` venue, so unsure why you would be getting a `no client registered for 'None'`. This suggests the venue was not found. Could you show a snippet of how you're making the requests including the imports at the top? (make sure you're not referring to anything with pyo3 in the name)

---

#### [2025-08-02 03:35:04] @bluesky.json

<@757548402689966131> so many thnx for helping me out!

this is the onlt code that preceeds the previous config snippit. perhaps should I include the strategy code too. env I am running this is jupyter notebook with python venv.

**Attachments:**
- [Screenshot_2025-08-02_at_12.34.59_PM.png](https://cdn.discordapp.com/attachments/924506736927334400/1401045612790812682/Screenshot_2025-08-02_at_12.34.59_PM.png?ex=68faf3e8&is=68f9a268&hm=23db3df4c49bbad315dea3d8eb8290c824c467631f3f44974cf5258fda5aadfa&)

---

#### [2025-08-02 03:36:44] @bluesky.json

<@757548402689966131> the strategy:

```python
class TickDataReaderConfig(StrategyConfig, frozen=True, kw_only=True):
    instrument_id: InstrumentId
    bar_type: BarType
    request_bars_and_ticks: bool = False
    request_data_start: datetime.datetime | None = None
    subscribe_quote_ticks: bool = False
    subscribe_trade_ticks: bool = False
    update_catalog: bool = False
    ema_period: int = 10
    debug_ticks: bool = False

class TickDataReader(Strategy):
    def __init__(self, config: TickDataReaderConfig):
        super().__init__(config)
        self.ema = ExponentialMovingAverage(self.config.ema_period)
        self.replay_start = self.config.request_data_start
        
    def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.config.instrument_id}")
            self.stop()
            return
    
        self.register_indicator_for_bars(self.config.bar_type, self.ema)
        self.request_bars(self.config.bar_type)
            
        self.subscribe_bars(self.config.bar_type)
    
    # Add a handler for the debug subscription
    def on_quote_tick(self, tick: QuoteTick) -> None:
        self.log.info(f"DEBUG: Received {tick!r}")
        
    def on_historical_data(self, data: Data) -> None:
        print(f"EMA: {self.ema.value}")

    def on_bar(self, bar: Bar) -> None:
        self.log.info(repr(bar), LogColor.CYAN)
        
        if not self.indicators_initialized():
            self.log.info(
                f"Waiting for indicators to warm up: {self.cache.bar_count(self.config.bar_type)}",
                LogColor.CYAN
            )
            return
        
        if bar.is_single_price():
            self.log.info(
                f"Single price bar: {bar.single_price()}",
                LogColor.CYAN
            )
            return
        
        print(f"EMA: {self.ema.value}")
```

---

#### [2025-08-05 07:27:31] @morino_rinze3056

Hi, I'm new to this and have encountered some issues. When I try to subscribe to data, it only provides thousands of previous data points, going up to 20 minutes ago, and then stops delivering new bars entirely. What should I do to fix this

---

#### [2025-08-05 08:27:31] @frzgunr

hi<@757548402689966131>,Do you have any good ideas for implementing a bracket order that is set to have only take profit and stop loss (no entry orders)? I'm implementing Coin's stepped take profit approach (current idea is to implement a set of oco orders with different tp prices for the same sl price), however I read in the NT documentation that NT's bracket orders must have an entry order. Do you have any suggestions in this regard?

---

#### [2025-08-05 08:28:09] @frzgunr

Kindly looking forward to your suggestion！

---

#### [2025-08-05 09:39:30] @cjdsellers

Hi <@899697082791780364> 
The order factory bracket method is just a convenience which gives you an entry + SL and TP bracketing orders.

It’s possible to assemble your own order list with linked orders in the way you’d like, but you’ll need to construct it manually for now (refer to the bracket source code for clues)

---

#### [2025-08-05 10:32:04] @frzgunr

thx for your help!

---

#### [2025-08-05 12:48:46] @haakonflaar

Is it possible to run multiple backtests asynchronously?

---

#### [2025-08-05 12:50:08] @haakonflaar

And what is the recommended way of running multiple backtests to optimize strategy parameters? Those backtests will share the same data so data loading shouldn't be required for each backtest.

---

#### [2025-08-05 17:41:48] @daws6561

I'm also interested in this, I asked a similar question in the 'general' chat.

---

#### [2025-08-06 06:09:59] @frzgunr

Hi<@757548402689966131>, I have a latency issue here and still not sure after checking NT documentation. I have designed my strategy to signal the end of a 1-minute bar in spot and then receive the signal in futures and execute the trade with the same minute bar data in futures. Will this be a delayed sequential problem in the NT framework? (i.e. is it possible that the spot has already signaled and the futures execute the signal before receiving the same minute bar, resulting in incorrectly using the previous minute's data for calculations and trades?)🧐 🧐 🧐

---

#### [2025-08-06 07:04:45] @cjdsellers

Hi <@899697082791780364> 
There's too many variables in play here to know precisely what you mean. Internal or external bars?

---

#### [2025-08-06 08:04:14] @frzgunr

external bars

---

#### [2025-08-06 08:09:47] @frzgunr

I know that in binance, spot and futures have exactly equal ts_event for the same 1 minute bar. However I'm not sure if such a logic would be seriously changed by the timing of the futures receiving bar: spot receives bar → spot bar triggers a signal → futures receives a signal triggering a trade (the current bar of the futures is used)

---

#### [2025-08-06 08:10:55] @frzgunr

Is it possible that the current bar of the futures actually incorrectly corresponds to the previous bar of the spot?

---

#### [2025-08-06 08:22:02] @frzgunr

Good news: I've come up with a new implementation logic: each bar of the futures tries to perform an order placing judgment (if the timestamp of the current bar is exactly equal to that of the trade signal, then the order placing logic is triggered, otherwise not). This ensures that the data used by the futures must come from that correct bar.😃 😃 😃

---

#### [2025-08-06 10:59:16] @haakonflaar

Would greatly appreciate your take on this <@757548402689966131>

---

#### [2025-08-06 11:46:33] @haakonflaar

And btw, I tested reusing data with the low-level API (`engine.reset()`), but I hardly saw any performance gain compared to using the high-level api without triggering`engine.reset()` or similar.  Could be that the low-level API allows for async backtests? Or will that mess with the engine?

---

#### [2025-08-06 12:24:22] @faysou.

There's no support for parallel backtests or reuse of data in parallel threads. It's a question that often comes up. You just need to run the same thing in parallel kernels. Also there's no plan to support parallel backtests, it's written somewhere in the roadmap I think. Because there are too many ways to do it, and it would be hard to support it.

---

#### [2025-08-06 12:28:24] @ajay_kumar_joshi

<@757548402689966131> Can you help with this?

---

#### [2025-08-06 12:28:46] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md

---

#### [2025-08-06 12:33:43] @ajay_kumar_joshi

<@965894631017578537> Thanks for sharing. Can you suggest any book/youtube tutorial or something which can help us to learn and use nautilus traders?

---

#### [2025-08-06 12:35:05] @faysou.

Clone the repository and look at the examples folder. Use an AI agent to ask questions about the code base or to write you some tutorials. It's impressive what they can do, especially since claude 4 in May this year.

---

#### [2025-08-06 12:35:48] @ajay_kumar_joshi

Got it, I’ll try it. Thanks again. ❤️

---

#### [2025-08-06 12:35:54] @faysou.

You're welcome

---

#### [2025-08-06 12:37:36] @faysou.

Use make build-debug to build the project. Use some print or log statements to see where the code executes (cython can't be debugged, but python and rust can, it will be easier to debug when cython will be completely migrated to rust)

---

#### [2025-08-06 12:38:28] @faysou.

Try to run the examples. Some can be run out of the box (the ones in the notebooks folders are from me, and that's the case for them)

---

#### [2025-08-06 12:40:26] @ajay_kumar_joshi

I’ll do that. I want to learn how can I contribute to this project. I know Python but don’t know how can I contribute to a Rust+Python codebase. Also, want to get hands on practice with algo trading.

---

#### [2025-08-06 12:41:39] @ajay_kumar_joshi

Got it, I’ll try to understand how it works. Thank you so much for support. 🙂

---

#### [2025-08-06 13:05:39] @gabadia5003

Is there any update on the cloud deployment ?  I am currently working on testing an in-house deployment of Nautilus Trader but rather use yours.  Do you have an ETA ?

---

#### [2025-08-06 18:49:59] @premysl_22228

I think cloud deployment won't be done any time soon. Some basic things are still missing. I think, we will work now heavily on v2 and few other initiatives. (See the ROADMAP and dev-* chats) But feel free to run EC2 instance and deploy it there on your own - you get one small for free and it should be enough unless you need some hardcore kind of HFT or have other not standard requirements.

---

#### [2025-08-06 21:46:54] @haakonflaar

Got it, thanks for the response 🙂 The roadmap mentions "... While externally orchestrated workflows are technically compatible..." and "... Users can integrate their own optimization frameworks ...". Have you tested and/or can you recommend a workflow/framework that facilitates parallell backtesting with nautilus?

---

#### [2025-08-06 22:43:43] @faysou.

No, I haven't worked on that

---

#### [2025-08-06 23:53:15] @premysl_22228

I recommend https://docs.python.org/3/library/multiprocessing.html . Don't forget to set maxtasksperchild=1, if you run thousands of backtests...there is some yet uncleaned mess like memory leaks, which backtests leave behind, and generally performance degrade over long running processes (haven't measured it here, this is more a general rule). You can load all data before spawning backtest, if they are small enough to fit your RAM, they shouldn't get replicated.

**Links:**
- multiprocessing — Process-based parallelism

---

#### [2025-08-07 01:04:42] @premysl_22228

I forgot to mention you to use the Pool object. With e.g. map.

---

#### [2025-08-07 09:35:21] @baerenstein.

Hi! I have been working on setting up my data pipeline with nautilus on EC2 and have run into a small issue regarding memory usage. I was wondering if someone already has had expierence with something similar. My main question is whether the internal nautilus buffers accumulate over time, slowly filling up the memory, or if it is a leak i haven't found inside my script

---

#### [2025-08-07 10:33:31] @cjdsellers

Hi <@322841069366804491> 
It could well be one of the leaks we’ve fixed on `develop` branch which will be releasing very soon. You could test it early by installing a recent development wheel (see readme)

---

#### [2025-08-07 13:16:42] @baerenstein.

I see that it works only for linux, so best to test it via docker or a virtual machine, right? (im on mac)

---

#### [2025-08-07 13:44:12] @haakonflaar

Got it, thanks for the help! 🙂 Do you recommend using the low-level api or the high-level api for running backtests in parallell?

---

#### [2025-08-07 14:09:02] @premysl_22228

It depends on how many data you have. If you have something, which fits into your RAM well with a reserve, then I recommend low-level API. You preload all data, add it to the engine and then fork. If you have large amount data, then I recommend high level API with chunk_size set.

---

#### [2025-08-07 14:09:36] @haakonflaar

Okay, I'll do some experimenting - thanks 👍

---

#### [2025-08-07 14:41:06] @haakonflaar

Have I understood it correctly that for now there is no way of re-using data in backtests using the high-level api (data are re-loaded for each config your pass to the BacktestNode)?

---

#### [2025-08-07 14:44:00] @premysl_22228

If you use chunk_size, you can't reuse it since all data but the last chunk gets deleted. If you don't use it, I am not sure. <@757548402689966131> might know more.

---

#### [2025-08-07 15:50:33] @mrpandami

Is anyone using NT for treasury desk / corporate cash management and doing complex risk management?

I have a rather complex set of inter related functional areas across different lines of business and need to trade across different asset classes and time horizons etc. 

Less quant , more treasury desk 🙂 a bit of algo trading for sure , but not in (as i understand it) the traditional sense.

---

#### [2025-08-08 07:49:23] @prockgrammer

Good day everyone, hope you are well. I am stuck when running the example live(Binace test error).I get this error

**Attachments:**
- [Screenshot_from_2025-08-08_09-48-07.png](https://cdn.discordapp.com/attachments/924506736927334400/1403283939686219876/Screenshot_from_2025-08-08_09-48-07.png?ex=68fa86c2&is=68f93542&hm=41d3b1181770302284a8b6a634715b0567df26a43351ba14fc26e57d73b5c23d&)

---

#### [2025-08-10 22:40:47] @cjdsellers

Hi <@944693521477160990> 
Welcome, thanks for the report. This was caused by Binance adding a couple of variants to one of the enums, and `msgspec` is very strict on unknown enum variants (this situation needs to be improved at some stage).

This has been fixed on the `develop` branch, you could install with a [development wheel](https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#development-wheels) or the next release will be soon

---

#### [2025-08-11 01:56:10] @eclipsephage

Are there any plans to develop a Coinbase (US) adapter?  Especially now that they have a derivative exchange?

---

#### [2025-08-11 08:26:17] @cjdsellers

Hi <@307301397609840640> yes, it would be a good integration - no timelines yet though

---

#### [2025-08-11 08:29:05] @chaintrader

how to get started?

---

#### [2025-08-11 08:30:55] @didierblacquiere

Hi Everyone, I have a simple question. 

Im looking to add True Level 2 Data, has anyone managed to do this?  Im looking at using rithmic but if theres a different data provider out there that has done this please let me know?

---

#### [2025-08-12 16:38:08] @finddata_49439_09644

i want to know how to store data in database, i tried several days , plz help

---

#### [2025-08-12 16:41:56] @finddata_49439_09644

i dont know why the code cant work

---

#### [2025-08-12 16:42:28] @finddata_49439_09644

i read all documents and some code , but i dont find the data persistant example

---

#### [2025-08-12 22:31:57] @donaldcuckman

Hey! im coming from ccxt, expanding my strategy to use multithreading and running into some issues with ccxt. 

Is it worth migrating to nautilus?

---

#### [2025-08-13 01:50:35] @eclipsephage

databento is the best.  Their free creds and plan generous, and their data catalog very flexible (only take what you need). Live, they're priced right at what a lot of brokers charge, only they're sitting right on the CME and direct to you, so they're faster, can get historical of course, and their requests are inherently programmatic... meaning you can connect it to your strat, an AI, etc.

---

#### [2025-08-13 02:06:18] @eclipsephage

Honestly, the databento connector is worth a whole separate app.

---

#### [2025-08-13 02:06:54] @eclipsephage

I'm a quant from LANL, and I will say yes.  For reasons.

---

#### [2025-08-13 02:07:41] @eclipsephage

... and dont bother looking for 'better'.  There holistically isnt.  Not even Quant Connect (which is now paywalled btw, largely).  Your other choice is code from scratch (Part Time Larry has to moved this fyi, kinda away from QC), but you will lose a lot doing so.

---

#### [2025-08-13 02:10:47] @donaldcuckman

Is nautilusTrader "thread safe"?

---

#### [2025-08-13 02:12:27] @eclipsephage

No python thread is inherently thread safe, technically.  But Nautilus is a rust core, so yes. Full rust, more so. That said, depends on your code.  And of course you can always thread at will, run separate process, etc.

---

#### [2025-08-13 02:13:06] @eclipsephage

The only true "safety" in any system is dependent on your watchdogs, which you will have to produce.

---

#### [2025-08-13 02:13:24] @donaldcuckman

sounds like its worth the effort of migrating then

---

#### [2025-08-13 02:14:26] @eclipsephage

I do AIML for a living, and I'd say yes, once you understand it.  Otherwise, scratch your own code.

---

#### [2025-08-13 02:14:44] @eclipsephage

Granted, my needs are fairly... eccentric

---

#### [2025-08-13 02:15:39] @donaldcuckman

all im using ccxt for is to unify api access to various exchanges

---

#### [2025-08-13 02:15:49] @donaldcuckman

rest is from scratch

---

#### [2025-08-13 02:16:36] @eclipsephage

Yah, you can always build a connector for Nautilus (to whatever broker).  The entire codebase and docs are open source; meaning this is relatively trivial to do now.

---

#### [2025-08-13 07:16:45] @cjdsellers

Hi <@915128495561113691> 
I think there is a regression here - as we no longer join the logging thread on shutdown. A work around for now is to add a 1 second (or as required) sleep at the end of your backtest run to ensure the log file is completely written before the program ends. I've added this to my list to look at soon

---

#### [2025-08-13 07:19:04] @didierblacquiere

Thanks for the advice, I really appreciate it!! 

We’ve decided to go with Databento since the adapter and so forth. Will see how It turns out. 

Once again thank you for the advice!!

---

#### [2025-08-13 09:25:53] @cjdsellers

Good to know, this commit should finally fix it by introducing reference counting for the log guard: https://github.com/nautechsystems/nautilus_trader/commit/e5d21eabc05b65573a2d9c8141fd14decfda0345

When you get a chance, let me know if this fixes your issue without the need for the `sleep` 🙏

**Links:**
- Implement LogGuard reference counting for proper thread lifecycle ...

---

#### [2025-08-13 14:03:43] @haakonflaar

<@965894631017578537> Seeing you have worked quite a bit with the data catalog - do you know if there is a way to aggregate data in a query to the catalog? For example passing `"1-HOUR-LAST-INTERNAL@1-MINUTE-EXTERNAL"` as bar type to receive 1 hour bars when all the data you have stored is 1-minute data? If not, how do you add aggregated data to the engine when backtesting using the low-level API? Do you have to fetch 1-min data from the catalog, manually converting to the preferred aggregate (by converting to pandas dataframe, perform the aggregation and then instantiate a wrangler to get the data back to nautilus format)?

---

#### [2025-08-13 14:29:39] @faysou.

No you subscribe to internal@external and an aggregator will produce the longer time frame. Catalogs only store external bars, internal means produced in nautilus.

---

#### [2025-08-13 14:59:19] @faysou.

If you want to understand what's going on look at actor.pyx and data engine.pyx and aggregator.pyx

---

#### [2025-08-14 06:27:00] @haakonflaar

Does the kernel crash when you try to import anything from nautilus? Looks like you are building on Windows. The `develop` branch does not always build on Windows. The `master` branch (and possibly the `nightly`)  branch does build on Windows. I moved my nautilus project to WSL to be able to use the `develop` branch. Maybe this should be stated more clearly in the docs and readme <@757548402689966131>?

---

#### [2025-08-14 06:35:36] @cjdsellers

Yes, unfortunately we lost the windows build for some inexplicable reason I have not been able to pin point yet. It's at the top of my todo list to recover because it's now blocking the release

---

#### [2025-08-14 07:43:16] @faysou.

I started like this with nautilus, windows and wsl, then didn't like my computer overheating when using wsl, so I switched to a macbook (I love my macbook). super happy about it. so unless you're in a corporate context where you need windows, switching to a mac could be a good idea.

---

#### [2025-08-15 02:20:44] @Wick



**Links:**


---

#### [2025-08-15 02:24:43] @Wick



**Links:**


---

#### [2025-08-15 02:32:25] @Wick



**Links:**


---

#### [2025-08-15 02:47:40] @Wick



**Links:**


---

#### [2025-08-15 02:55:25] @Wick



**Links:**


---

#### [2025-08-15 02:55:53] @cjdsellers

Apologies <@915128495561113691> I can't seem to adjust these wick settings properly

---

#### [2025-08-15 07:30:24] @melonenmann

I'm python beginner and I do not get it how to increase a Price.
 sl: Price = Price.from_int( bar.high.as_double() + 0.0001 ) --> not working (clear)
sl: Price = bar.high + 0.0001 --> result is a float
sl: Price = bar.high + Price.from_str("0.0001") --> result is a decimal (why is Price + Price a decimal?) --> this was the AI proposal

I looked into the object.pyx and Price has a cdef add(), but 
bar.high.add(0.0001) is not existing in python.

Could someone please give me a hint, how to modify a Price? (this does not feel like I'm programming for 30 years)

Is there a better way than this?
prec = bar.high.precision
p = bar.high.to_formatted_str().partition(".")
p2 = int(p[2]) + 10
p2s = f"{p2:0{prec}d}"        
sl: Price = Price.from_str(p[0] + "." + p2s)

---

#### [2025-08-15 16:05:10] @shinhwas

Hi, I'm getting the following error message when I set the environment variable NAUTILUS_NUMBER_FORMAT = ".2f":
Can anyone help?

2025-08-15 08:52:32,814 - ERROR - Detected invalid numeric format spec used by Money; ensured number format '.2f' (no grouping) at process start via env vars.
  File "nautilus_trader/model/objects.pyx", line 976, in nautilus_trader.model.objects.Money.__init__
ValueError: invalid format string

---

#### [2025-08-16 01:12:57] @premysl_22228

This seems like a "bug". Price + Price should be in my opinion Price. Would you file RFC to GitHub please? Add there also the note, that add should be changed from cdef to cpdef to be usable from Python. In the meantime I recommend to convert it to decimal, do the arithmetics and convert it back to Price. I would like to see API, which supports Price + decimal -> Price.

---

#### [2025-08-16 01:37:44] @cjdsellers

Hi <@340916580449779713>

There is a `make_price` helper method on instruments which may be useful, then you can pass any type which can be cast to a `float` and you will get in return a `Price` with the correct precision for the instrument: https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/model/instruments/base.pyx#L494

(there is also a similar `make_qty` method).

I wouldn't recommend using strings for price arithmetic, only for parsing back into a `Price` domain object.

---

#### [2025-08-16 01:46:07] @cjdsellers

Hi <@1353826739851362345>,

The domain value types (in objects module) have evolved over time, there are some ancient RFC's on this and the decision on `Price` + `Price` returning a `Decimal` for the current Cython is probably foregone at this point.

For other arithmetic ops, demoting to the rhs primitive is correct - but certainly common (and preferred) in DDD to remain within the domain where possible, so your point is valid (this is actually how it works in Rust as well).

We could consider exposing the `add`, `sub` etc to Python with `cpdef` as you suggest if it would assist usability, there are similar methods on the Rust types as well. Probably they were left as C only `cdef` for simplicity / a smaller API surface

---

#### [2025-08-16 06:07:43] @melonenmann

Add and sub would be good. But I will try out the instrument functions which makes sense because of the precision, first. Long-term, it's already implemented in rust.

Btw. Is there a risk calculation helper that returns the correct quantity for given price and sl?

---

#### [2025-08-16 13:53:31] @shahisma3il

How much is the RAM & CPUs requirements to run NT smoothly?
Our use case is to run python code for algo auto-trading on Nasdaq stocks, precious metals, cryptos etc. and we may run forex trading in future.

---

#### [2025-08-16 14:03:46] @premysl_22228

Hi, <@690236989991157922> . It depends on operating system, whether you are running with GUI and whether you want the highest possible performance (e.g. for HFT cases), or you are okey with some extra microseconds.

---

#### [2025-08-16 14:08:52] @shahisma3il

I am thinking of deploying NT on Alma Linux (ro Fedora) console only online server (Hetzner cloud) with VPS (4-CPUs-AMD Zen2 and 16-GB RAM). Afterwards, I hope to make it available through my own sub-domain url and access it from web-browsers on our client machines.
For web server, I hope to use Traefik (Golang based), which may also add some latencies.

---

#### [2025-08-16 14:09:43] @shahisma3il

So I suppose, my setup can't do HFT cases (like forex trading) but good enough for auto-trading with micro-sec delays?

---

#### [2025-08-16 14:11:45] @shahisma3il

and for HFT cases, I might have to use dedicated online server (VDS) setup using Alma Linux (or Fedora), install it on docker and access it thru Nginx -- am I on the right track?

---

#### [2025-08-16 14:18:23] @premysl_22228

Before answering the rest, I can't help to say the following: **be sure, you use proper VPN like Wireguard, setup iptables/nft properly, and that your domain remain "secret"...assigning a trading machine public DNS record on known domain is like asking for DDoS from people, who don't like you, if you have some**...it's a great honeypod to know, when somebody want to make damage to you, but it begins and ends with this.

---

#### [2025-08-16 14:21:50] @premysl_22228

With such small setup, you don't survive DDoS...it better to be careful before disclosing your IP address by assigning it to DNS record. It can be walked through e.g. by DNSSEC records, if not secured properly. (Which is honestly not easy task)

---

#### [2025-08-16 14:27:13] @premysl_22228

Your setup is overkill on nonHFT trading. 4 GiB of RAM should be enough even if I count the memory leaks into the game. Be sure not to use SWAP and regularly restart (e.g. every midnight) the NT (yes, it is not a nice solution, but leaks are still being reported by users)

---

#### [2025-08-16 14:29:03] @premysl_22228

2 CPU should be also enough for nonHFT trading. 1 is for your ssh instance, if you do some computationally hard operation, so your trading operation is running uninterrupted. 1 for NT.

---

#### [2025-08-16 14:30:04] @premysl_22228

Golang webservers aren't so much hungry, if I am correct.

---

#### [2025-08-16 14:32:13] @premysl_22228

For answering HFT case, how would you connect nginx to NT? If you are thinking about running webserver directly in NT process, it is guaranteed to slow down the process, especially during requests.

---

#### [2025-08-16 14:33:51] @gz00000

In my HFT strategy, I use `aiohttp` to start an HTTP server, allowing me to dynamically adjust some parameters via an HTTP API.

---

#### [2025-08-16 14:34:38] @shahisma3il

Cloudflare CDN (or BunnyCDN) provides security in most of these cases

---

#### [2025-08-16 14:34:42] @gz00000

https://discord.com/channels/924497682343550976/924498804835745853/1390710473426731008

The monitoring and observability of the strategy are implemented as follows

---

#### [2025-08-16 14:35:22] @gz00000

What is the purpose of your web server?

---

#### [2025-08-16 14:36:27] @premysl_22228

It slows down the process. If you care about the microseconds, I wouldn't do it. Your setup could be optimized to be more predictable in my opinion.

---

#### [2025-08-16 14:38:23] @gz00000

I even care about nanoseconds; in my current strategy, the optimization unit is already at the nanosecond level. If you have better suggestions and are willing to share, I would greatly appreciate it.

---

#### [2025-08-16 14:42:44] @premysl_22228

<@224557998284996618> If you care about nanoseconds: Run a separate process with web server and connect it via message bus. Bind the trading process to one CPU (kill the hyperthreading twin), set it up the lowest possible nice number, compile your kernel for real time systems, if not done already,... I don't know details about your setup, so I just predict, what might be improved. Should I continue?

---

#### [2025-08-16 14:44:27] @gz00000

I understand the points you're making. Apart from those related to the web server, we've basically done everything else, including kernel and network card driver optimizations. DPDK is in the plan, but it hasn't been implemented yet.

---

#### [2025-08-16 14:44:27] @shahisma3il

NT running using docker compose (in docker containers), with Nginx installed on the cloud-instance host and Nginx config file prepared to serve the docker containers

---

#### [2025-08-16 14:45:46] @shahisma3il

I'm thinking of setting up webserver, Nginx, is to be installed on the cloud-instance host that serves docker-containerised NT

---

#### [2025-08-16 14:46:33] @gz00000

We also have a separate market data system, and the JSON parser within it is custom-built to achieve some speed improvements.

---

#### [2025-08-16 14:47:24] @premysl_22228

I see there a code architecture in NT, which might be DPDK friendly. Chris haven't answered me, whether it is on purpose, you have more information about the DPDK? The kernel calls are one of the largest latency increasers in the stack.

---

#### [2025-08-16 14:48:45] @premysl_22228

Don't you have some info, whether "life yield" without kernel in the path will be implemented soon too?

---

#### [2025-08-16 14:49:01] @gz00000

We have plans for DPDK, but we haven't had the time to test it yet, so there's no additional information at the moment. Once we start testing and deployment, I'll share the relevant information.

---

#### [2025-08-16 15:29:11] @faysou.

https://www.dpdk.org/

---

#### [2025-08-16 16:08:59] @premysl_22228

It will be really great contribution to the HFT part of community, if done properly. I am really looking forward for any update, <@224557998284996618>! With this, Rust strategy implementation and few tricks, how to get closest to the server in AWS/Equinox, I think NT might be institutional compatible even on known HFT strategies.😍

---

#### [2025-08-16 16:28:04] @premysl_22228

<@224557998284996618> Will you also put Redis on DPDK? I know its a little bit obscure, but communication via network virtual functions (PCI roundtrip) is I think faster then one syscall. Redis has already its port for DPDK, if I am not wrong. The machines would probably need 3 virtual functions, one for OS, one for Redis and one for NT, if NT doesn't use some framework, which is "stackable". I hope, AWS network cards do find the shortcut via loopback, so it is VPC-less. Or do you plan it to do it other way? 🙂

---

#### [2025-08-16 17:37:15] @premysl_22228

I would like to say, you don't want to have public CDN before private site. It increases your exposition to even automatized attacks a lot. You will have to check OWASPs and many further things for the website, if you don't want get pwed. I would really recommend to setup silent VPN like Wireguard on random port and use it to the trading user interface access and maybe SSH, without any other exposition to the internet. It greatly reduces a risk you get pwed. (I personally run tuns of public SSH servers, to be completely honest, as I use them as last fallback when I need to connect to the infrastructure when I am without any of my devices...but this isn't probably your case. It took me a lot time to secure them properly, you can avoid this by using VPN)

---

#### [2025-08-16 17:41:24] @premysl_22228

I read your message once more and understood it in one more different meaning: So you want the nginx to get NT Docker artifacts? Why?

If you could elaborate a little bit, it would be great. 🙂

---

#### [2025-08-16 17:50:16] @shahisma3il

I generally self-host apps either using dokploy (docker compose and Traefik) or I install Nginx directly on VPS host to expose other dockerised apps.
But I get your point: for low-latency, security and simplicity purposes, I must use VPN and a private access port (custom SSH port) to use it.

---

#### [2025-08-16 17:51:21] @shahisma3il

Alternatively, I can also install it on a VPS server with desktop access: install Rustdesk, install dockerised NT locally on the VPS and have me and my friends connect to the VPS thru Rustdesk and access NT thru Rustdesk remote session access.

---

#### [2025-08-16 23:15:04] @wenis7429

Hi!  I recently discovered Nautilus and so far I am very impressed.  Thank you all for your hard work on such an amazing piece of software and releasing it open source.  I will say, the learning curve is pretty steep, especially considering I have had 0 previous experience with Rust, Cython, or Python.  Anyway, to get to the point.  Is there a way to aggregate 65-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL?  Looking at the source for BarSpecification, it looks like this is not possible in the current implementation: composite_spec = BarSpecification(65, BarAggregation.MINUTE, PriceType.LAST). There are 390 minutes in the regular session of a trading day so 65 divides perfectly.

---

#### [2025-08-17 01:22:44] @wenis7429



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1406448128907018353/image.png?ex=68fad4e4&is=68f98364&hm=80186937065668380f7786170b7434a3c877de1a4259a83776ca6de32ff42e16&)

---

#### [2025-08-17 05:25:00] @cjdsellers

Hi <@310249999348924416> 
Thanks for reaching out with the kind words. This may have changed recently, because it was previously supported to have a flexible `step` for use cases exactly like this

---

#### [2025-08-17 08:51:47] @premysl_22228

Hi, <@310249999348924416>. I am not sure, whether this can be now supported, since the alignment is now to standard timeframes. 65-MINUTES, even if allowed, wouldn't probably work as it should. There quasiperiodic aggregator idea at the table, where alignment (if any) is user responsibility, but isn't implemented yet and agreed upon. How much do you need this type of bars?

---

#### [2025-08-17 09:00:47] @premysl_22228

<@757548402689966131>, you need to align somehow 65 minutes to 390 frame=6.5 hours, which is not easy to do in general and didn't work before probably. At least I don't see the reason, why it should have worked. There is no proof of correctness and the one I made is for standard timeframes. I might I think make a proof it wasn't supported in general case, if you need me to to keep the constraints as I put them.

---

#### [2025-08-17 09:06:38] @premysl_22228

<@310249999348924416>, excuse my ignorance, but what instrument are you trading, so you get so exotic trading conditions? Are beginning of trading sessions at least aligned to the beginning of the hour?

---

#### [2025-08-17 10:10:29] @wenis7429

<@1353826739851362345> I trade stocks.  Coming from TC2000 I am used to 65 minute aggregates as they split the trading day equally.  Regarding how dependent I am on this, I'm not married to the idea, but I think its logically the best way to organize "an hour" of trading in a regular US session of stocks.  <@757548402689966131>  Is the idea of a "trading session" already designed into the system?  I understand there are so many instruments in Nautilus and markets that are 24/7.  It would seem logical to create an object for a trading session.  Aggregates could be aligned to the start of a session.  <@1353826739851362345> I don't think the job of an aggregator should be to align bars... It should just aggregate as its told, 3min, 5min, 7min, etc.  Maybe allow the user to specify the timestamp for start of aggregation?

---

#### [2025-08-17 10:48:00] @premysl_22228

<@310249999348924416> I thought about the alignment a little bit, and reasons, why alignment should be done on at least one of the aggregators (if we add quasiaggregator later, which would be working as you wish to):

a) It is a standard. You want to see the same graph for TimeBarAggregator as you see on venues. (If you dig deeper, you will find out, there are some yet unverified bugs reported, when this doesn't apply, but in my opinion this expectation is utterly justified)

b) You want to see, what are retail traders trading on. You can predict upcoming manipulations and market movements by that.
-> You want to have ability to trade on this fast enough...(if you dig deeper, you will find out, we have offset setup, which enables you to do so. There are further proposals from me to have partial bars propagated through the system when you enable it and there might be a proposal for general based delay, but I haven't thought it throughfully...we want to keep API minimalistic, but fully featured, as there are some things like complexity budget and new user onboarding barricade) 

Concretely, one of my strategies are depending on proper alignment (if my few months old research isn't obsoleted), a delay of even one minute further on 5 minute timeframe changes the profitability significantly...the strategy is almost useless, if offset of 1 minute to the alignment happens (out of what might be optimized out of it). So I wouldn't be much happy if we dropped the alignment feature.

If you have any further arguments, why we should drop the alignment feature or anything else, I am happy to discuss. 🙂

---

#### [2025-08-17 11:37:30] @premysl_22228

<@310249999348924416> But you got good point. The quasiperiodic aggregation is now more prioritized thing in my mind and will somehow get it done if there is an opportunity and <@757548402689966131> agrees with me, we want to also support aggregation with no alignment. 🙂

By the way, I am not allowed to do any stocks trading due to insider trading legal issues, which might come up. So I know almost nothing about it and didn't saw the argument myself before. Thanks for your input. 🙂

---

#### [2025-08-17 11:47:15] @wenis7429

Thank you for thinking about this and your patience with my ignorance as I learn.  I'm not sure what your vision is for quasiperiodic aggregation, but here are a couple of my thoughts:  I think a simple TradingSessions model could work and its a simple solution.  BarSpecification could include an optional TradingSession, and if provided, get_time_bar_start could use it like this:

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1406605294603341875/image.png?ex=68fabe83&is=68f96d03&hm=4867a935b4f0f4a4a386f96a4f0f229d0b3fee30dc1fbf375afcce12d0d5d367&)

---

#### [2025-08-17 11:50:21] @wenis7429

I totally understand the priority of correctness, and balancing this with "providing sharp tools" to the community.  I am definitely going to get cut using Nautilus.

---

#### [2025-08-17 11:53:34] @wenis7429

I think deciding what to do with the remainder of the bar aggregate is the challenge.  You could just deny a user from creating any aggregate that doesn't divide evenly into the trading session.  Or give an option to place the remainder at the end of the session.

---

#### [2025-08-17 11:55:36] @wenis7429

Either way I think something like this should be able to be added without affecting the existing logic of the aggregator.

---

#### [2025-08-17 12:51:55] @premysl_22228

I get your point. But, I think quasiperiodic aggregator, where user either set up any start_time he wants or let the default behavior, which would be start_time=now, is much simplier solution. The quasiperiodic aggregator would always get the start_time, which is one before the current time in the series (or at the exact time).

I also think, that session_start_utc should be somehow deducible from the instrument, we might add a new method into the instrument, so you get the next session_start_utc after given time (or at exact the time).

User then just get next session_start_utc from the instrument and passes it to quasiperiodic aggregator via BarSpecification. And everything works without introducing much complexity. 

"Or give an option to place the remainder at the end of the session." I don't think, we want this. Partial bars (also on request) + clock scheduled event is in my opinion better solution. Partial bars are already preapproved by Chris.

What do you think?

You seem to be interested in the dev of NT by the way. 🙂 The fastest way, how to get this done is by the contribution (after we all agree on what is the correct solution - I am also pinging <@965894631017578537>, as he might have some input on this). If you want to, we might start a thread out of this discussion, and we might help you to get this implemented. Do you need it in the Cython version v1, or Rust version v2 is good enough?

---

#### [2025-08-17 13:05:47] @premysl_22228

If you want me to, I will explain further the quasiperiodic series aggregator concept to you. It's just TimeBarAggregator with arbitrary start time and arbitrary (very probably decimal or double) step. So you are able to do something like "3.1415-QUASI-MINUTES-STARTING-20250717T145455". 

We might need a custom (lexer&)parser for this...LL(1) is probably good enough for this, but must think more about it. Parser making is not entirely my strongest ability. Some (optionally monadic) LL(n) library without lexing in Rust might be the best solution given that we will support more complicated BarSpecification later for information based aggregation.

---

#### [2025-08-17 13:07:43] @premysl_22228

Btw. Any idea for good syntax is welcomed. 😄

---

#### [2025-08-17 13:09:56] @premysl_22228

Eg. 3.1415-QUASI-MINUTES(20250717T145455) or 3.1415-QUASI-MINUTES with default behavior might be better. I haven't think about this much yet.

---

#### [2025-08-17 13:29:32] @premysl_22228

Or we can make quasiperiodic time aggregators like "3.1415-MINUTES(20250717)" resp. "3.1415-MINUTES(NOW)". This seems even more elegant. The panic would come only if user haven't specified the argument. I would put there directly further arguments like offset and things which are now data engine setup.

---

#### [2025-08-17 13:56:16] @faysou.

I have the impression that these aperiodic intervals are pointless. The goal of technical analysis is to capture group effects on collectively observed indicators, not to do some maths that nobody is aware of.

---

#### [2025-08-17 13:57:39] @faysou.

For the start time we could do a modulo on the interval so it still works with 65 minutes for example, that's how it was before.

---

#### [2025-08-17 13:58:04] @faysou.

I'll have a look and reintroduce in the next days

---

#### [2025-08-17 14:00:09] @faysou.

Actually 65 minutes is still periodic

---

#### [2025-08-17 14:14:11] @premysl_22228

Oh, you are right, any racional number will be periodic. Therefore any number, which can be represented, will be periodic, not quasiperiodic. My mistake...

---

#### [2025-08-17 14:15:04] @premysl_22228

I put the name of the aggregator to ice, it is not good name.

---

#### [2025-08-17 14:23:15] @premysl_22228

It will take me some time, before I better understand, what modulo is doing. <@965894631017578537>, if you could elaborate, why, it would help me a lot.

---

#### [2025-08-17 14:23:44] @faysou.

65 mod 60 = 5

---

#### [2025-08-17 14:24:20] @faysou.

but I think I'll floor the now time at day, so we can have an arbitrary origin during a day

---

#### [2025-08-17 14:24:42] @wenis7429

I would love to eventually contribute to this project!  I planned on learning Rust just to code my own trading ideas, which is how I stumbled upon NT.  At this point, to say I am a novice would even be an overstatement and it would be embarrassing for me to submit anything useful.  I'm trying to get an understanding of the system and its a bit like drinking through a firehose!

---

#### [2025-08-17 14:26:37] @premysl_22228

Yes. But why would you align to arbitrary number? What about eg. 71-MINUTE?

---

#### [2025-08-17 14:26:57] @faysou.

https://deepwiki.com/nautechsystems/nautilus_trader

**Links:**
- nautechsystems/nautilus_trader | DeepWiki

---

#### [2025-08-17 14:27:00] @faysou.

look here

---

#### [2025-08-17 14:27:53] @faysou.

I think best to floor at midnight, then origin can be set anywhere in a day

---

#### [2025-08-17 14:28:09] @wenis7429

Even if you used the same TA, same math, organizing the data at alternate aggregates will produce different results.

---

#### [2025-08-17 14:28:55] @faysou.

you need to look at TimeBarAggregator.get_start_time and introduce what you think is useful

---

#### [2025-08-17 14:29:08] @wenis7429

I was just taking this concept a step further by introducing the idea of a trading session.

---

#### [2025-08-17 14:29:40] @wenis7429

a 24x7 session type would have its floor at midnight.

---

#### [2025-08-17 14:30:05] @wenis7429

a US regular session 9:30.

---

#### [2025-08-17 14:31:40] @faysou.

this question of sessions comes up sometimes, if you search on discord at some point we found some libraries to give session times, someone would need to create an actor that sends messages indicating the start and end of a session

---

#### [2025-08-17 14:31:44] @wenis7429

By the way, Thank you all for the responses and not just immediately telling me I am a moron.

---

#### [2025-08-17 14:32:15] @faysou.

from my experience, if you want something the fastest way is to work on it yourself, else you can submit an issue on github so it doesn't get forgotten

---

#### [2025-08-17 14:33:33] @faysou.

I've gotten to a level where I can do pretty much anything with nautilus, but I can't implement whatever people want, I work mainly on things I need

---

#### [2025-08-17 14:33:42] @premysl_22228

I don't think this is a right approach, if I understand you correctly. You propose function generalization baseless of any reason for it.

---

#### [2025-08-17 14:34:10] @faysou.

I won't work on it anyway, so you can do what you think is best

---

#### [2025-08-17 14:34:45] @melonenmann

It was somewhere mentioned that I can create my own reports. I cannot find the api for that. Could you please give me an entry point?

---

#### [2025-08-17 14:35:25] @wenis7429

Its hard to know whats best when you don't understand the full system.  I feel like thats where I'm at.  All I do understand is I shouldn't ask the aggregator to give me 65m bars and have it return a 35m bar.

---

#### [2025-08-17 14:36:10] @faysou.

maybe just start with what the system allows for now, then if you start understanding the code you'll be able to modify it

---

#### [2025-08-17 14:36:21] @wenis7429

Thanks for all your help.

---

#### [2025-08-17 14:40:31] @premysl_22228

I will try to better understand the reasons behind it. But I would be rather if we didn't introduce a start_time function, which isn't a proper generalization of a base function. Proper generalization would have to be just one and it should be evident, why it can't be generalized other nonequivalent way.

---

#### [2025-08-17 14:46:13] @premysl_22228

Even alignment to 1-MINUTE for numbers >1-MINUTE, which don't divide smallest greater unit, is a generalization, which works. But it doesn't mean, we should use it since user expectation will be proper alignment to his series.

---

#### [2025-08-17 14:47:17] @faysou.

I was thinking more that if we need intervals like 65m or 90m then instead of flooring the time with a 1h precision for the time origin, we can floor it at the start of a day. So we have more possibilities for the origin.

---

#### [2025-08-17 14:48:04] @faysou.

I wasn't thinking about functions for next time, although in effect it's what's used for monthly aggregation.

---

#### [2025-08-17 14:55:05] @premysl_22228

In my opinion, we should always focus, on what user expects, and if we can't give him, what he would in 99% expected, we should raise an exception. This way, we can ensure, that users can trust NT and won't get any bogus outputs, even through well defined (and usually undocumented). 

The other way around is dangerous in my opinion.

I would propose rather to focus, that "3.1415-MINUTES(20250717)" is working, as user know exactly what he gets. 

For 65-MINUTE aggregation, who can tell what is the proper origin, if for 5-MINUTE aggregation is proper origin well defined by the series, which align with series of higher units?

---

#### [2025-08-17 14:56:25] @premysl_22228

To explain: 65-MINUTE series can't never align with 1 hour series, like 5-MINUTE does.

---

#### [2025-08-17 14:59:38] @premysl_22228

<@965894631017578537> If I asked you, what is the start_time of 5-MINUTE aggregation, when now=16:57, you know exactly, what it should be. If I asked you, what is the start_time of 65-MINUTE aggregation you have no idea without studying the underlying implementation and would probably expect something else, then you found there. Am I correct, or am I missing something?

---

#### [2025-08-17 15:02:44] @premysl_22228

If we generalize like this in other places in NT, we should in my opinion reconsider. User expectation should be the "first class citizen of NT"...so I thought it were just unvalidated inputs.

---

#### [2025-08-17 15:15:16] @faysou.

you can know the origin with time_bar_origin, we can say that arbitrarily the default origin is the start of the day and it can be adjusted with time_bar_origin

---

#### [2025-08-17 15:15:39] @faysou.

if I needed this, that's what I would do, but I don't think it's a priority for now

---

#### [2025-08-17 15:25:12] @premysl_22228

Would this align with the user expecting, his data from INTERNAL aggregator is (almost) identical to EXTERNAL?

---

#### [2025-08-17 15:34:48] @premysl_22228

<@965894631017578537>, we shouldn't in my opinion make arbitrary implementations and then repeat users (or devs), their expectation is bogus and that reported bug is indeed feature (when day is sunny), but we should focus on fulfilling user (and devs) expectations. And users (and devs) expect, that 5-MINUTE bar is indeed what they get from venues as 5-MINUTE. And nobody knows how 11-MINUTE data is looking out of raw data. I think, it is that simple.

---

#### [2025-08-17 15:40:22] @wenis7429

I am going to mock something up in a TradingSession model as a learning experience.  This might not be the best approach, or might just be plain stupid, but I'm going to do it anyway.  I asked my AI overlords and they told me "This approach aligns with SOLID principles by giving TradingSession a single responsibility (defining session boundaries and aligning timestamps), integrates cleanly with the existing codebase, and avoids complexity while fixing the issue where 65-minute bars close prematurely (e.g., after ~34 minutes due to UTC hour alignment in get_time_bar_start)."

---

#### [2025-08-17 15:48:07] @premysl_22228

I think, the person should be always in the control of the AI, not the other way around. LLM is good servant, but really bad overlord. I would generally recommend a thinking session before accepting AI architecture advice. (I don't use it for architecture at all, because what comes out of it is usually more harmful then useful). I think, it won't work as you expect, but I don't have full information of you are doing, so I can't say with confidence. It is at least good exercise. 🙂

---

#### [2025-08-17 15:48:37] @faysou.

Then you do a loop from the origin until you get to a time before the now time. The loop can be modulo one day.

---

#### [2025-08-17 15:49:42] @faysou.

I agree we shouldn't focus on this, there are better things to focus on

---

#### [2025-08-17 15:55:25] @premysl_22228

Last words from me on this issue for now: You are right, for 5-MINUTES works it right and fulfills 99% of user expectation (I have changed the loop to mathematical functions, so I thought about it wrong - it leads to faster initialization), for 13-MINUTES or 65-MINUTES it will generate SOMETHING, but nobody will be sure what it is unless knowing underlying implementation.

---

#### [2025-08-17 15:57:41] @faysou.

I just know I can do it if I need it one day, but I won't do it now. Sometimes we don't do things to avoid having to support people who don't look at the code. Most people don't look at the code of nautilus, but I think they should, it's the fastest way to know what is possible to do and how things work. That's the benefit of an open source library. A closed source library needs more documentation as there's no way to see the underlying code. Also another benefit of an open source library is that you can add features you think are missing. The best thing to do in my opinion is to start using the library, find some bugs or missing features and try to implement them. Very few people do this though. But mechanically over time, more people will. A fraction of a bigger user base is still bigger.

---

#### [2025-08-17 16:03:01] @premysl_22228

You will be fully supported by the other solution, if approved by Chris. You will have no reason to implement it in my opinion. I can't foresee any reason, why would you need it implement it this way, if you got working 65-MINUTE bars working exactly as you want by "65-MINUTES({now.floor("d")})"

---

#### [2025-08-17 16:05:25] @premysl_22228

If I was on Chris place, I would refuse such PR. And will be redundant if approved. But he is main maintainer. We have to wait for him to say final words.

---

#### [2025-08-17 16:09:06] @premysl_22228

I think, it is good, we at least come out with some solution, even we both think, the optimal solution is different.

---

#### [2025-08-17 17:54:03] @gz00000

We already have many techniques for speed optimization, but I've been hesitant to share them all because it affects our ability to profit in this competitive environment. In some types of our strategies, the majority of our efforts are focused on speed optimization.

---

#### [2025-08-17 17:55:20] @gz00000

I haven't used Redis in our HFT strategies, so I don't have experience with it in that context.

---

#### [2025-08-17 18:03:06] @premysl_22228

Monitoring must be painful fight between seeing more and performance hits without the Redis, I guess. Is it so?

---

#### [2025-08-17 18:04:58] @gz00000

Yes, the timing statistics for each step are only conducted during small-scale testing. Once the system stabilizes, we try to minimize these statistics, keeping them only in very critical areas.

---

#### [2025-08-17 18:05:46] @gz00000

What are the main reasons you use Redis?

---

#### [2025-08-17 18:24:39] @premysl_22228

I don't use it yet. I plan to use it, so the computed data are asyncly saved to a place, which can be accessed by a monitoring. There is no official way, how to do async operations from inside the strategy, I know about. This is how I understood, the NT should be used for HFT. (I hope everything about the cache is async and full of race conditions, as it should be so cache is performant enough. I have no key-value cache in agenda once NT v2 lands + maybe mmap of cache...I will want a dual API for Rust, one for HFT and very large amount of optimizations and one for the rest of the community - this is still in the discussions)

---

#### [2025-08-17 18:28:46] @gz00000

If your strategy is stateful and requires data preservation, you can either save the data when the program stops or choose to dump it at longer intervals. In a stateless strategy, I only keep the data in memory. If it's for statistics/monitoring, you might consider:

---

#### [2025-08-17 18:28:54] @gz00000



---

#### [2025-08-17 18:29:02] @premysl_22228

I must say, you are either courageous or have really good testing. Many bugs are discovered by me on production (it won't be so much fun, if you didn't know about the fact) and I am always paranoid enough about new versions deployed. The sufficient testing costs more then is my budget.

---

#### [2025-08-17 18:31:23] @gz00000

I primarily use the execution part, as we have a separate market data system. I wrote an adapter to integrate this market data system. For information like positions, I directly interfaced with the exchange using monkey patching, without using the built-in features.

---

#### [2025-08-17 18:32:02] @gz00000

If you're willing, you can share the bugs you've discovered, and we can discuss with other maintainers how to resolve them.

---

#### [2025-08-17 18:35:51] @premysl_22228

It is about the detail. I want to see each bar short after deployment. Some of my strategies trades a lot, so I debug them fast, but some are generating tons of orders which gets executed rarely. Eg. once it happened to me, that limit order for happy path closure and market order for less happy path race conditioned and I was left with unmaintained positions. But it was before NT, architecture here will hopefully allow me to have closed everything for sure. Hopefully.😀 - There are missing still things like overkill stop market order, when your whole trading machine gets KO, but I believe, this will get resolved.

---

#### [2025-08-17 18:36:40] @premysl_22228

(Reduce only)

---

#### [2025-08-17 18:41:57] @premysl_22228

I stopped to recording them few months ago. I have some leftovers recorded. I will get back to you, once I try to get back to the trading. I am now working on discovering discrepancies between other trading platform outcomes and NT output systematically. It is not evident, where different numbers come from, so I go one-by-one. I started with aggregation improvement.

---

#### [2025-08-17 18:44:15] @gz00000

Perhaps you could try setting up a separate system to record market data for observation. Instead of relying on the strategy program to do so.

---

#### [2025-08-17 18:44:47] @premysl_22228

And thank you for your offer. 🙂 And <@224557998284996618>, if you are willing, I would like to be added to Chinese Discord channel, if there are more maintainers discussion happening there.

---

#### [2025-08-17 18:45:43] @gz00000

Do you speak Chinese? 
PS: Most of the users in the Chinese channel are users, not maintainers.

---

#### [2025-08-17 18:48:23] @premysl_22228

No, I don't, but I feel, it is blocking me in finance world and it might be a good beginning of me starting to understand Chinese a little bit more. I would use AI to translate and to learn. - But if there are no more maintainer discussion there, then there is no reason for me to be there.

---

#### [2025-08-17 18:50:03] @premysl_22228

(not blocking utterly, but Chinese seems to me to be something like a Russian in information security...not primary language, but you suffer by not getting the whole picture, you would otherwise get)

---

#### [2025-08-17 18:50:29] @gz00000

The Chinese channel only invites Chinese-speaking users. So, sorry... Thanks for understanding.

---

#### [2025-08-17 18:51:11] @gz00000

There are basically no maintainers in the Chinese channel; it's mostly discussions among users about usage issues.

---

#### [2025-08-17 18:54:47] @premysl_22228

Yes, I understood. No need to be there. 🙂 - I don't remember the name of the trading platform, which was unusable without the Chinese, and had to skip it in my throughout testing of opensource market. Maybe you know better and might tell me whether the one Chinese only opensource platform (there is only one internationally known as far as I know) is something which deserves greater attention or it is just another...

---

#### [2025-08-17 18:56:04] @premysl_22228

From pictures it seemed as professional platform, but didn't understood much thing.

---

#### [2025-08-17 18:56:31] @gz00000

I can't think of which one it is. Do you have more information? Or do you still have the image you're talking about?

---

#### [2025-08-17 18:57:08] @premysl_22228

Give me a minute, I try to find it in my notes, if I noted it.

---

#### [2025-08-17 19:03:42] @premysl_22228

I remembered wrong, there was more of them. Eg, https://github.com/yutiansut/QUANTAXIS. It's totally undiscovered Hic sunt dragones part of map. Can you compare them with NT if you have your own research? I guess you have done one including the Chinese projects before starting with NT.

---

#### [2025-08-17 19:05:35] @gz00000

I know about this. However, before using NT, I hadn't used any other frameworks. Before NT, we used an internally developed framework, and we still do. New strategies use NT, while older ones use our own framework.

---

#### [2025-08-17 19:08:49] @premysl_22228

Okey. I should still do my homework somehow. I am little worried, whether Chinese on the sites isn't on purpose to get China an advantage over the rest of the world. Should start learning Chinese soon I guess, if I want to find out. 😀

---

#### [2025-08-17 19:09:51] @premysl_22228

And there is a ton of research on finance which is Chinese only...at least I could get some alpha from it if nothing else learning Chinese is good for.

---

#### [2025-08-17 19:14:31] @premysl_22228

I guess it will be for me as hard as for you the English and this always stops me. It's a shame, basically any other world language including Japanese would be easier for me to learn. 😀

---

#### [2025-08-17 19:37:36] @premysl_22228

If I run into religio, I am sorry, I put you into the position. I have limited information income from the mainland, I am slowly getting my feet wet using AI to understand things better, scrapping China internet a lot. I will probably never visit it after what I have already done there, if by some miracle I don't get diplomatic passport. (chance 0.000x) 😀

---

#### [2025-08-18 03:37:05] @cjdsellers

Hi <@310249999348924416> 
There seems to be two different topics under discussion here:
- 1) Trading session tracking / trading calendar
- 2) Time bar aggregation / bar specifications

For 1) It's definitely a feature we'd be interested in supporting, calendars are notoriously tricky to do a good job of though. There are some existing open-source projects being maintained to varying degrees. To meet a narrow use case of just a single venue, it probably wouldn't be too hard. To design something truly general and extensible would take some further effort. It's not a priority at this stage and there may be an existing GH feature request for it you could comment on if you like. Otherwise, feel free to raise a GH ticket, or we can continue discussing if this is something you might be interested in working on?

For 2) My impression is the existing behavior for time bars was changed in an attempt to increase validation and correctness of time periods and aggregations. I would prefer we take a simpler approach more like the original behavior which was simply aggregating within time range bounds, at some interval using a timer, from some origin point / start time. I think we've layered on top of that some additional opinions about period alignments, potentially trading sessions, and some notion of matching externally aggregated data provided by venues. I don't think the basic implementation should consider any of these things.

This has resulted in a surprising outcome for <@310249999348924416> where what appears to be a simple use case of aggregating 65-MINUTE bars is no longer possible. In the same way we can aggregate any number of `TICK` bars, the `step` should be flexible within a reasonable range, and an origin time offset - start time can be used to satisfy various use cases. If the implementation is clear enough to understand and explain in documentation, then I don't see a reason to make things more complex for now? (refactorings for code improvement and documentation clarity probably still necessary in any case)

---

#### [2025-08-18 11:15:38] @faysou.

<@310249999348924416>  65 minutes doesn't make sense in the context of nautilus as it's not periodic over 24 hours. It only makes sense in the context of trading sessions where a timer would be reset at the beginning of a trading session but that's not implemented at the moment. It would require a different aggregator, and writing aggregators is quite complex, I don't think there's a real benefit in implementing non periodic bars over 24 hours. maybe the period is over several days, but it doesn't really make sense in most cases.

---

#### [2025-08-18 11:16:31] @faysou.

longer periods than 60 minutes make sense though, as long as they are periodic over 24 hours

---

#### [2025-08-18 16:28:19] @melonenmann

Is this intended that the aggregated bar (W1) has the ts_event/ts_init (same) from the end of the bar period?
The underlying M30 (external) data is fitting, the ts_event is at beginning.
But 
`EUR/USD.SIM-1-WEEK-LAST-INTERNAL,1.17255,1.18293,1.17074,1.17824,239000000,1751846400000000000 | Bar time: 2025-07-07 00:00:00+00:00`
should have 30.06.2025
Or is the logic that an aggregated bar has the date at the end of the period? (which is strange but would be ok, than I will substract the bar length from the ts_event)
https://prnt.sc/jyei8eenDHSw

**Links:**
- Screenshot

---

#### [2025-08-19 00:31:57] @premysl_22228

~~I think, you introduced backward incompatibility in your PR. daily_time_origin should be in my opinion added to closest_time. I wonder, how this passed the testing. ~~ After rethinking, it works even better this way - daily_time_origin can be anything this way upon the limits of Timestamp. No more need for validation...

Even though I don't agree this is a good change, I think, you represented it in more performant and readable way then before (and more readable then me in the preparing change). I think, the WEEK and MONTH variant should be also made to look similarly.

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1407160123515994132/image.png?ex=68fac8fd&is=68f9777d&hm=424ca43c13c5e0ea045a1135731b71a5a3ae8bd4f671417ac6daa8e39321e021&)

---

#### [2025-08-19 01:26:04] @premysl_22228

Basically, we can make day_start some of anything else like week, 5*day, 2\*week, 11\*week, 13\*week, 11\*13\*week, 1990-01-01 (monday), 1970 (beginning of time in datetime),... The alignment to day is just too much arbitrary to be expected, this must be documented well...but on the other side I must admit it is an interesting idea.

To explain: I might ask why we don't align everything to 1990-01-01 as this would allow more exotic bar specifications, while keeping WEEK aligned to it. But in the same time, I might ask, why we not align everything to p1 \* p2 \* ... \* pn \* week, where p1 \* p2 \* ... \* pn are prime numbers larger than 7 for some ARBITRARY n, if this would allow user to run 11-MINUTE, or even 35 minute (for this alignment to week should be enough). And what about aligning everything to 1970-01-01 since it is beginning of time, but for WEEK alignment, which needs to be aligned to Monday, so 1990-01-01 be it for it again. There is "unlimited" amount of possibilities...

I tried to make my points here as clean as possible, why user can't know, what to expected behavior is and why should we therefore avoid supporting this. It works for standard timeframes, but for nonstandard timeframes, it was demonstrated, the day floor is as arbitrary as choosing year 1990-01-01.

<@965894631017578537> , <@757548402689966131> , if you still persist on the changes, couldn't it be at least 1990-01-01, so it is universal for all units, much more steps are possible, and has at least some reason behind it (1990-01-01 is smallest year starting with monday as first day after 1970 and it can be easily remembered).

---

#### [2025-08-19 01:34:20] @premysl_22228

(To not forgot, the obvious: When user asks for 35-MINUTE, he might not want TimeBarAggregator aligned to a week, but to start of the session. Therefore exceptions are recommended by me very much. But in the generalization of the system implemented by faysou, the logic is opposite, give him something, even if it is not what he expects. This generates bug reports and community distrust to NT stability, even if documented. - I would say, that >95% of such misaligned expectations get unreported and there is no way, how to convince the user, this was his mistake not to read the docs properly before using the function.)

---

#### [2025-08-19 01:39:44] @premysl_22228

Taking the 1990 proposal and years examples back, leap years break this bad. But beginning of week would be in the logic better than day.

---

#### [2025-08-19 01:40:40] @wenis7429

Thank you for the changes to the get_time_bar_start.  If I'm understanding this code correctly, I should just be able to offset to "market open" with the time_bars_origin_offset configuration option?

---

#### [2025-08-19 01:56:29] @premysl_22228

I think, 35-MINUTE is not now supported. And even if, since every day the offset would be different and offset is now configurable only via Data Engine config, it won't work, if I am not wrong. The offset configuration should be somehow moved to BarSpecification, I would propose like "1-MINUTE(offset=30s)", but can't speak for others

---

#### [2025-08-19 02:10:03] @wenis7429

<@1353826739851362345> <@965894631017578537> This seems like a very simple solution to this problem to me, if I am understanding this correctly.  I don't think its really a big deal from a user perspective to add a configuraiton for the dataengine.  Right now I am only trying to use this for historical data aggregating bars internally.  I wonder how/if this solution will work with live streaming data...

---

#### [2025-08-19 02:14:42] @premysl_22228

You will probably want to run the backtest over multiple sessions. Data engine setup happens only once at the beggining of the backtest. If N is your offset on the monday, and M is your offset on thusday, you can set up only N or M, not both, if N != M, to the dataengine. That's the whole problem.

---

#### [2025-08-19 13:39:51] @wenis7429

Thank you for the response Chris.  What I need is probably beyond the scope of the aggregator.  As a user, I want to aggregate data for some period (market session) at a user defined interval (time bar length).  In the current implementation of the aggregator, this is not possible.  I would be interested in contributing a system-wide feature for TradingSessions, but again I am very uncomfortable with my current understanding of NT.  I'd be happy to discuss this further on how you'd like this implemented.

---

#### [2025-08-19 14:47:07] @makeroftools

Hi all. Is `start, end = self._validate_datetime_range(start, end)` necessary for the "start" param? Is this a new and necessary construct? Because the  start param seems to be optional in `cdef class RequestData`. Thanks.

---

#### [2025-08-19 14:47:26] @makeroftools

I am using current develop branch

---

#### [2025-08-19 15:04:03] @makeroftools

Also, I thought that is was normal for exchanges to provide default for start params, making this optional param worthy? Maybe that's not the case.

---

#### [2025-08-19 22:05:45] @cjdsellers

Hi <@860860251624308758> 
It so happens that we're discussing this very topic in [this PR](https://github.com/nautechsystems/nautilus_trader/pull/2867). Many API's allow optional range parameters for their endpoints, and by NT always requiring `start`, we lose the ability to leverage certain endpoint behaviors (such as reasonable or expected defaults).

I think it comes down to flexibility which is simpler for the platform to implement vs consistency which needs an extra layer of complexity to achieve.

It would be helpful to understand more about your use case when/if you get a chance, did you find that a required `start` was difficult to use?

---

#### [2025-08-20 00:25:42] @premysl_22228

Hi, <@757548402689966131> and <@965894631017578537> I am just reminding my self, that you didn't responded to why alignment to beginning of day is maybe not best choose. I would like to discuss the topic, as it still in my opinion deserves some attention. If my chat messages aren't understandable enough, please, tell me so and I try to reformulate.

---

#### [2025-08-20 06:41:18] @faysou.

Flooring at start of day is enough in most cases for using a more precise time origin for longer periods like 90m. The current solution is better already. If there's a need for more later, we'll do more.

---

#### [2025-08-20 08:28:00] @melonenmann

Its working when I'm using external data. So, I avoid using aggregated bars from now on.

---

#### [2025-08-21 08:13:31] @premysl_22228

Do anyone have experience with running NT as a gym for ML? I haven't get much useful answer from the AI. Could you describe how you do it in smaller detail? (I am not much experienced in reinforcement learning, so it is probable, I am just missing something.) You can skip the inference part, I know how to do it correctly, I am rather interested in training.

---

#### [2025-08-21 09:16:37] @premysl_22228

Probably got finally something, what might be useful https://claude.ai/public/artifacts/c24b34f2-4d03-4150-b79e-3c1b00ce8c49 . But still, if you got any real life experience, I am eager to hear. 🙂

**Links:**
- NautilusTrader AI Gym Environment - Complete Example | Claude

---

#### [2025-08-21 09:16:49] @.davidblom

Pearl has an API to split act, observe and training. https://github.com/facebookresearch/Pearl. Then you don’t need to use the gym environment which combines all these which doesn’t work with event driven back testing.

---

#### [2025-08-21 09:18:59] @premysl_22228

I will look it up. Thanks.

---

#### [2025-08-22 15:33:28] @mk27mk

Hi, I've noticed this in the docs:

"Bar timestamps (`ts_event`) are expected to represent the close time of the bar. This approach is most logical because it represents the moment when the bar is fully formed and its aggregation is complete."

But externally aggregated data generally comes with the time of the Bar aligned with the time of its opening. 
Does this mean that we need to manually adjust the time of the bars? Maybe by adding a `pd.Timedelta(bar_duration)` to the index before doing `wrangler.process`?

---

#### [2025-08-22 18:03:08] @wenis7429

<@1260594339407597569> check DataEngineConfig.  I believe there is an option time_bars_timestamp_on_close that can be set to false.

---

#### [2025-08-22 18:03:29] @wenis7429

https://deepwiki.com/search/dataengine-config_3fe5a4ce-325e-4279-8bb8-5861d2033cc1

**Links:**
- Search | DeepWiki

---

#### [2025-08-22 18:37:22] @mk27mk

Thank you <@310249999348924416> !  
After texting here I tried asking DeepWiki too and came up with the same result.
Now that you gave me confirmation I'll dive a little bit deeper on that argument.

(see Notes at the end of the response)
https://deepwiki.com/search/relevantcontextthis-query-was_3538c2e3-f06a-4f77-8542-0812f3795f80

**Links:**
- Search | DeepWiki

---

#### [2025-08-22 22:20:39] @makeroftools

Hi <@757548402689966131> . Well, It was initially an expectation, but I see that there maybe an abstraction issue for a particular adapter's use-case, or so. I see it more as a user's flexibility issue rather than a necessity, atp. Thanks!

---

#### [2025-08-22 22:23:28] @cjdsellers

Thanks for the feedback <@860860251624308758>

---

#### [2025-08-22 22:29:06] @cjdsellers

Hi <@1260594339407597569> 
I would say bar timestamps are 50:50 open or close across venues and providers (notably Databento uses the open). The `time_bars_timestamp_on_close` config option that <@310249999348924416> kindly suggested applies to internally aggregated bars, so if you preferred this method then at least you have a way to achieve it.

However, when processing historical bar data for backtesting, *if* you intend on using them to drive execution (this is optional), then yes - you do need to pre-process by adding the interval to the open time so that bars are timestamped on close. I hope that helps!

---

#### [2025-08-23 07:10:13] @faysou.

ts_event can be at the start or end of bar, for execution what is used is ts_init and it should always be at the end of a bar or slightly after.

---

#### [2025-08-23 11:14:40] @mk27mk

Thank you <@757548402689966131>  and <@965894631017578537> !
So, if I got it right, what I can do is leave the `ts_event` of my bars unaltered and rather set `ts_init_delta` equal to the bar step size and maybe a little bit more, if I want to simulate real-world latency as <@965894631017578537> said.
`ts_init_delta` is 0 by default because `ts_event` equal to the close time of the bar is assumed.

---

#### [2025-08-23 11:23:45] @faysou.

I don't know about ts_init_delta, but in a backtest context ts_init is the variable used for ordering events.

---

#### [2025-08-23 11:24:58] @faysou.

In a live context events are processed when they arrive with some checks in the data engine to avoid processing events out of order.

---

#### [2025-08-23 11:26:12] @mk27mk

Thank you!

---

#### [2025-08-24 20:02:02] @.islero

Hi everyone,
I’m struggling with request_bars and could really use some help. I’ve already spent 3 days debugging without success.
No matter what I try, I always get:
Received <Bar[0]> data for unknown bar type
and nothing ever arrives in on_historical_data. I also see warnings like:
[WARN] BACKTESTER-001.MessageBus: Subscription(topic=data.trades.XMT5.BTCUSDT-PERP,
  handler=<bound method BarAggregator.handle_trade_tick of <nautilus_trader.data.aggregation.TimeBarAggregator>>,
  priority=0) not found

Context
    •    Running in backtester
        •       NT V1.220, but also tried a stable one
    •    My Parquet catalog contains only 1-minute EXTERNAL bars (no ticks)
    •    I suspect the problem might be that request_bars doesn’t work without TradeTick data in the catalog?

Code Example
I’ve tried calling it in on_start and also later after some backtest time has passed.
I’ve tried on_start and outside of on_start waited when some data pass into cache, but I always get the same error.

instrument = TestMT5InstrumentProvider.btcusdt_perp_mt5()
bar_type_request = BarType.from_str(
    f"{instrument.id.value}-5-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL"
)

start_time = pd.Timestamp("2020-12-11", tz="UTC")
self.strategy.request_bars(bar_type_request, start=start_time)

Question
Is it possible to request bars in backtesting without having TradeTick data in the catalog, using only existing 1-minute EXTERNAL bars? Or is this a bug?

---

#### [2025-08-25 06:25:15] @haakonflaar

Is it possible to enforce 2 or more ticks of slippage during backtests? Setting `prob_slippage` to 1 only enforces 1 tick of slippage.

---

#### [2025-08-25 06:45:20] @faysou.

Are you using a DataCatalogConfig ?

---

#### [2025-08-25 06:50:44] @.islero

No, I’m using BacktestDataConfig

data = BacktestDataConfig(
  catalog_path=str(data_catalog.path),
    data_cls=Bar,
    bar_types=[bar_type],
    instrument_id=instrument.id,
    start_time=start_ns,
    end_time=end_ns
)

And the bar_type is external 1m bars from a parquet catalog:

bar_type = BarType.from_str(f"{instrument.id.value}-1-MINUTE-LAST-EXTERNAL")

---

#### [2025-08-25 07:13:00] @faysou.

Then that's why request doesn't work

---

#### [2025-08-25 07:13:10] @faysou.

You need DataCatalogConfig

---

#### [2025-08-25 08:57:14] @.islero

<@965894631017578537> Thanks for help, but maybe I’m doing something wrong — I tried your method, and I created a DataCatalogConfig and added it to the BacktestEngineConfig, but I didn’t make any other changes.

catalog_cfg = DataCatalogConfig(
    path=str(data_catalog.path),
    fs_protocol="file",
    name="local"
)
engine = BacktestEngineConfig(
…

catalogs=[catalog_cfg]
)
[ERROR] BACKTESTER-001: Received <Bar[0]> data for unknown bar type
[WARN] BACKTESTER-001.MessageBus: Subscription(topic=data.trades.XMT5.BTCUSDT-PERP, handler=<bound method BarAggregator.handle_trade_tick of <nautilus_trader.data.aggregation.TimeBarAggregator object at 0x132717ac0>>, priority=0) not found

---

#### [2025-08-25 09:36:06] @lan.phan

Hi, I have a quick question. When running Nautilus Trader in paper trading mode, do I need to use my real Binance API key and secret?
Right now, I’m using a fake key and secret — the system runs and retrieves data fine. But when it tries to submit an order, I get an error saying the instrument ID is invalid, even though I’m using something like BTCUSDT-PERP.BINANCE, which should be valid.

---

#### [2025-08-25 10:19:28] @faysou.

https://github.com/nautechsystems/nautilus_trader/tree/develop/examples/backtest/notebooks

---

#### [2025-08-25 10:19:59] @faysou.

You can look at the two examples here, they use the high level API, but it should work similarly with the low level API.

---

#### [2025-08-25 10:20:58] @faysou.

Personally I only use the high level API as it is a similar setup to live trading. Also it avoids developing things that wouldn't work in Live, like passing config arguments that cannot be passed in a live config.

---

#### [2025-08-25 10:21:48] @.islero

<@965894631017578537> Thank you so much, you saved me a ton of time — I don’t know when I would have found this on my own. Despite the warning, the data started coming into on_historical_data🙏

---

#### [2025-08-25 10:22:09] @faysou.

Also with something I've added recently, BacktestConfig are not always needed, backtest data can be added on the fly from a catalog.

---

#### [2025-08-25 10:22:59] @.islero

Is this in a nightly build already?

---

#### [2025-08-25 10:23:30] @faysou.

databento_options_greeks.py works without backtest data

---

#### [2025-08-25 10:23:46] @faysou.

Yes it is

---

#### [2025-08-25 10:23:47] @.islero

Got you

---

#### [2025-08-25 10:24:18] @faysou.

It's been like this for a few months, but I would always use the develop branch or nightly build as bugs are quickly solved there.

---

#### [2025-08-25 10:25:10] @faysou.

There's even something to download market data on the fly, I've tested it only with databento but it should work with other adapters.

---

#### [2025-08-25 10:25:31] @.islero

Wow, great!

---

#### [2025-08-25 10:25:51] @faysou.

If you try to understand how it works it's very interesting. The key is to follow the messages.

---

#### [2025-08-25 10:26:41] @faysou.

Or ask an agent to explain you how it works, they understand a lot of things and it's not just hallucination like one year ago, it's really good. Personally augment code is what I use

---

#### [2025-08-25 10:27:18] @faysou.

I prefer to understand what I use, and I definitely understand as I've done it 🙂. Overall I've improved many things on the data side of nautilus over the last year, ie. how data flows through the system.

---

#### [2025-08-25 10:35:49] @.islero

Are you referring to following the debug messages provided by the engine?

---

#### [2025-08-25 10:37:43] @.islero

I’m still learning Nautilus Trader, and I find the idea and implementation in Nautilus Trader very interesting — and the decision to use Rust as the foundation is brilliant. It’s truly a very interesting platform, and thank you for replying to my message and help!

---

#### [2025-08-25 10:40:58] @.islero

I’m also mainly using the high-level API, but so far only for backtesting — I haven’t gotten to live trading yet 😊

---

#### [2025-08-25 11:26:09] @faysou.

No the messages that flow through the message bus, in the code

---

#### [2025-08-25 11:27:04] @.islero

Alright, thanks. I’ll look into that.

---

#### [2025-08-25 15:13:04] @faysou.

see here https://github.com/nautechsystems/nautilus_trader/blob/8182262957d6bd734d0169402fc27b3ebf9ce334/docs/concepts/fill_models.md  , this doc or probably part of it should be added back soon to the repo

---

#### [2025-08-25 15:14:54] @faysou.

also here https://github.com/nautechsystems/nautilus_trader/blob/8182262957d6bd734d0169402fc27b3ebf9ce334/nautilus_trader/backtest/fill_models.py

---

#### [2025-08-26 05:19:32] @haakonflaar

Great, I'll do some experimenting, thanks 👍

---

#### [2025-08-26 05:34:07] @haakonflaar

Have I understood it correctly that if I am going to create a FillModel that adds let's say 3 ticks of slippage to every trade I need to set 0 volume for the current tick, as well as 0 value 1 and 2 ticks away, and unlimited volume 3 ticks away? And does creating an order book as is done in the class `OneTickSlippageFillModel(FillModel)` example work when my data is only bars?

---

#### [2025-08-26 05:55:42] @faysou.

Not sure about that you will need to experiment on this, I've implemented the specs of someone else, the idea makes sense but I haven't used it

---

#### [2025-08-26 06:26:49] @fdoooch

Hi everyone!
I want to use NautilusTrader to capture and store real-time market data, such as the trades stream and L2 order book updates.
I’m starting a TradingNode and adding an Actor.
I can implement the on_trade_tick() and on_quote_tick() methods to save the data, but is there a more efficient way to achieve this?

---

#### [2025-08-26 07:17:08] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/backtest/models/fill.pyx there are examples here

---

#### [2025-08-26 07:18:59] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/persistence/writer.py#L52

---

#### [2025-08-26 07:19:52] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/persistence/catalog/parquet.py#L2177

---

#### [2025-08-26 07:21:24] @faysou.

You can record data with streamfeatherwriter and then convert it to a catalog / parquet files for reuse in backtests. As above you will need to experiment and look at the code for more details, I haven't done this before.

---

#### [2025-08-27 02:18:58] @braindr0p

Hi, I'm following the tutorial here https://nautilustrader.io/docs/latest/tutorials/databento_data_catalog#preparing-a-month-of-aapl-trades
After downloading and writing the data to the catalog,  I want to use it in backtesting.  Does it also require writing an Instrument definition to the catalog as well?  Are there any examples of using the  DatabentoInstrumentProvider to get the Instrument?

**Links:**
- NautilusTrader Documentation

---

#### [2025-08-27 07:38:22] @cjdsellers

Hi <@84040758922842112> 
Yes, you generally need an instrument definition persisted in the catalog. It's acknowledged that tutorials are lacking which makes life harder for anyone new to the platform, and we'll be investing bandwidth here soon - I hope that helps!

---

#### [2025-08-28 00:07:43] @primalleous

Just looking into this again. I did ask a followup months ago asking if the FSM (finite state machine) is related, but looking again I don't see how that's possible (for delivery guarantee). Are there messaging delivery guarantees (e.g. most once, at least once, exactly once)? If not, why is this not an issue? I would think you'd want these guarantees for handling orders/balance related things at minimum.

Should I assume it's up to the user to implement these somehow?

Edit: Was told, extensive testing done and very small edge case/this is a single process, not distributed, so likely not an issue. I'm just working on CQRS myself and seeing what is/isn't in nautilus.

---

#### [2025-08-31 12:46:12] @label_3

Hi <@757548402689966131> There is still an issue with CashAccount calculating frozen funds.

---

#### [2025-08-31 12:50:25] @label_3

In the Multi Currency CashAccount model, the types of frozen assets are different when there are both outstanding buy and sell orders. When calculating sellable assets, the quantity is simultaneously included in the frozen assets of the quote_currency.

---

#### [2025-08-31 13:05:53] @label_3

This issue can occur in the maker strategy

---

#### [2025-08-31 14:01:48] @lisiyuan666

Hello everyone, does request_aggregated_bars() support fetching from local catalogs like request_bars()? I would like to fetch some historical data to initialize the indicators but request_bars() doesn't support bar aggregation. So i have to aggregate in advance and insert the data to the catalog or use request_aggregated_bars() but has to fetch the whole dataset from the exchange. Are there better ways to fetch historical data from local catalog and initialize the indicators?

---

#### [2025-08-31 14:30:16] @rodguze



---

#### [2025-08-31 14:48:36] @daddysxvnt

Do I have to upload my own market data? Or just my code for my strategy?

---

#### [2025-08-31 16:32:09] @rodguze

you'll need to supply market data to use nautilus trader

---

#### [2025-08-31 18:03:25] @faysou.

Yes it works with catalog and/or market data client.

---

#### [2025-08-31 18:04:03] @faysou.

One year ago I had the same question and realised it wasn't implemented so I did it.

---

#### [2025-09-01 02:05:21] @lisiyuan666

It seems that when using request_bars the local catalog is checked first and if some data is missing they are fetched from the exchange. But when using request_aggregated_bars only the local catalog is used, if there are some data missing it kind of blocked there. I'm using "BTCUSDT-PERP.BINANCE-1-HOUR-LAST-INTERNAL@1-MINUTE-EXTERNAL". Is there something wrong?

---

#### [2025-09-01 02:12:33] @lisiyuan666

Also with request_bars the indicators are not updated automatically, but with request_aggregated_bars they are updated. I asked Gemini about this and it give me the following answer. So indicators for internal bars are updated automatically when backtesting and should be updated manually when live trading? Am i correct here?

**Attachments:**
- [screenshot_1756692636.png](https://cdn.discordapp.com/attachments/924506736927334400/1411896485343133696/screenshot_1756692636.png?ex=68fae091&is=68f98f11&hm=93e9e31ca9edcab5c0f8b5961ffc46292bebf1dcc6267959c6ee9a6f4eedfb66&)

---

#### [2025-09-01 02:17:57] @faysou.

Likely something wrong in what you are doing, request aggregated bars is converted to the same request as for request bars with some post treatment. The fastest way for you to find what's wrong is to set up a dev environment and debug with some log statements to see what is reached, in the actor, data engine and the adapter you use, that's what I would do if I were you.

---

#### [2025-09-01 02:18:31] @lisiyuan666



**Attachments:**
- [screenshot_1756693067.png](https://cdn.discordapp.com/attachments/924506736927334400/1411897986111508582/screenshot_1756693067.png?ex=68fae1f7&is=68f99077&hm=02fa527ba4bc575f59cddcd9732ed661c61ee1ec2a54d0c68176c7854bf9f34f&)

---

#### [2025-09-01 17:24:56] @label_3

How to use `log_component_levels` to control the output content of component logs? When I use the following configuration to execute a backtest, the output logs still contain a large number of log levels that do not meet the requirements.
```
# Configure backtest engine
config = BacktestEngineConfig(
    trader_id=TraderId("BACKTESTER-001"),
    logging=LoggingConfig(
        log_level="ERROR",
        log_level_file="INFO",
        log_file_name='BACKTESTER-001.log',
        # log_file_format="json",
        log_component_levels={ "BacktestEngine": "INFO", "Portfolio": "WARN" },
        # use_pyo3=True,
        clear_log_file=True,
        bypass_logging=False,
        print_config=True,
    ),
)

# Build the backtest engine
engine = BacktestEngine(config=config)
```

---

#### [2025-09-01 17:41:11] @faysou.

I had the same issue a few weeks ago, this config is for overriding what's displayed for a given component compared to the current global logging level while leaving other components untouched, ie. displaying at the global level. I would rather have it be that all components are blocked except the ones we choose.

---

#### [2025-09-01 17:46:58] @label_3

Have you solved this problem yet?

---

#### [2025-09-01 17:54:33] @label_3

Additionally, when I use the `use_pyo3` parameter, the `log_component_levels` parameter is not passed to the underlying Logger.

---

#### [2025-09-01 18:59:54] @faysou.

No I haven't, I think it would be better if <@757548402689966131> would have a look at this first as the logger is quite an important component and he would need to approve a change on this first.

---

#### [2025-09-01 19:01:58] @faysou.

It's just the way the logger is implemented yet, maybe we would need an extra configuration where we can discard all other components except the ones in the loglevel dict, to avoid losing the existing functionality that may already be used by other people.

---

#### [2025-09-02 02:06:04] @lisiyuan666

After some logging, i found that there are no "bars" in response for this callback. The **request** generated is: "2025-09-02T01:54:01.201565206Z [INFO] TESTER-001.EMACross: [REQ]--> RequestBars(bar_type=BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL, start=2025-08-23 01:54:01.201397516+00:00, end=2025-08-24 01:54:01.201428191+00:00, limit=0, client_id=Non
e, venue=BINANCE, data_type=Bar, params={'bar_type': BarType(BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL), 'bar_types': (BarType(BTCUSDT-PERP.BINANCE-10-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL),), 'include_external_data': False, 'update_subs
criptions': True, 'update_catalog': False, 'bars_market_data_type': 'bars'})". The **response** is: "2025-09-02T01:54:02.348064601Z [INFO] TESTER-001.EMACross: Received aggregated bars response: DataResponse(client_id=BINANCE, venue=BINANCE, data_type=Bar{'bar_type': BarType(BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL), 'partial': BinanceB
ar(bar_type=BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL, open=115458.00, high=115662.30, low=115253.00, close=115253.00, volume=0.475, quote_volume=54894.23170, count=27, taker_buy_base_volume=0.447, taker_buy_quote_volume=51666.95290, take
r_sell_base_volume=0.028, taker_sell_quote_volume=3227.27880, ts_event=1756000499999000064, ts_init=1756778041211228322)})". So the callback did nothing and returned. What could be the possible problem here?

**Attachments:**
- [screenshot_1756778509.png](https://cdn.discordapp.com/attachments/924506736927334400/1412257237748940930/screenshot_1756778509.png?ex=68fadf0b&is=68f98d8b&hm=e1f4fcf8fe5650df7e72e08ab3767cc88771b54a1913cf533428cf66148c2c6d&)

---

#### [2025-09-02 11:43:07] @lisiyuan666

Correct me if I'm wrong, but it looks like this ts_init here maybe ts_event: https://github.com/nautechsystems/nautilus_trader/blob/919840a97443c60234b2584e37bb5790606370ac/nautilus_trader/data/aggregation.pyx#L392

**Links:**
- nautilus_trader/nautilus_trader/data/aggregation.pyx at 919840a9744...

---

#### [2025-09-02 12:48:09] @faysou.

Bars are aggregated with ts_init

---

#### [2025-09-02 12:49:04] @faysou.

I think it creates confusion that sometimes it's aggregated with ts_init and sometimes with ts_event (for quotes and trades), maybe we should always aggregate time bars with ts_init.

---

#### [2025-09-02 13:19:13] @lisiyuan666

After changing to ts_event, request_aggregated_bars seems to work fine, else no bars will be returned, is there something wrong? ts_init of bars fetched from binance seems to be the current run time of the machine.

---

#### [2025-09-02 13:20:16] @lisiyuan666

I'm using "BTCUSDT-PERP.BINANCE-1-HOUR-LAST-INTERNAL@1-MINUTE-EXTERNAL" for testing.

---

#### [2025-09-02 13:23:04] @faysou.

I think it's a problem mentioned earlier that ts_init of binance bars is not well defined, someone needs to fix this

---

#### [2025-09-02 13:23:18] @faysou.

I don't use binance so someone else needs to do this

---

#### [2025-09-02 13:30:56] @lisiyuan666

Ok, is there something i can do to get rid of this problem? Maybe update historical bars manually?

---

#### [2025-09-02 14:14:05] @faysou.

Modify the adapter to generate ts_init at the end of a bar for historical data.

---

#### [2025-09-02 14:18:55] @lisiyuan666

After some digging i found that i have exactly the same problem with https://discord.com/channels/924497682343550976/924504069433876550/1409397353735262251 😂

---

#### [2025-09-02 15:28:07] @faysou.

Well someone should fix it

---

#### [2025-09-03 03:44:35] @label_3

It's too difficult to debug; I have to recompile every time, and it takes more than ten minutes each time.😭

---

#### [2025-09-03 03:45:18] @label_3

Why doesn't Rust provide a complete ABI specification?😭

---

#### [2025-09-03 06:14:32] @cjdsellers

Hi <@710319013967691857> 
Make sure to run `make build-debug` in case you are compiling a fully optimized release build

---

#### [2025-09-03 10:18:17] @boskoop10

Hi! Trying to get databento's CMBP-1 data into NT, which is not yet supported in the most recent release. I saw that a recent commit (93149a0) added some initial support for it; do you have any plans to finalize support by the next release? Thank you!

Btw, because I saw the pre-release commit, I tried to build from source on my M3 Pro MBP by following the instructions in `installation.md` and failed. I had to do the following (for which I have no insight if appropriate, but it worked -- thanks Claude)

```
# Set the Python executable path for PyO3
export PYO3_PYTHON=$(pwd)/.venv/bin/python

# Set macOS-specific RUSTFLAGS
export RUSTFLAGS="-C link-arg=-undefined -C link-arg=dynamic_lookup"

# Set library paths for your uv Python installation
PYTHON_LIB_DIR="/Users/$(whoami)/.local/share/uv/python/cpython-3.13.3-macos-aarch64-none/lib"
export LIBRARY_PATH="$PYTHON_LIB_DIR:$LIBRARY_PATH"
export LD_LIBRARY_PATH="$PYTHON_LIB_DIR:$LD_LIBRARY_PATH" 
export DYLD_LIBRARY_PATH="$PYTHON_LIB_DIR:$DYLD_LIBRARY_PATH"
```

Should I raise an issue to improve the documentation?

---

#### [2025-09-03 11:14:38] @faysou.

https://gist.github.com/faysou/7f910b545d4881433649551afce69029

**Links:**
- Install nautilus_trader dev env from scratch, using pyenv and uv

---

#### [2025-09-03 11:14:47] @faysou.

I use pyenv to avoid the issues you had

---

#### [2025-09-03 11:16:13] @faysou.

it's a bit unfortunate that a full uv solution doesn't work out of the box, uv is sold as this wonder solution, but it still needs some polishing with pyo3, it's still a relatively recent project

---

#### [2025-09-03 11:20:02] @faysou.

https://github.com/nautechsystems/nautilus_trader/pull/2924

**Links:**
- Refactor bar aggregators to use ts_init instead of ts_event by fays...

---

#### [2025-09-03 11:20:35] @faysou.

this PR will probably solve your issue, can you test it ? I don't use binance or bybit, but it will probably work

---

#### [2025-09-03 11:43:58] @faysou.

I was trying to use a full uv solution with intellijidea for a few months, on and off, but it wasn't working, now I'm sticking to pyenv + uv as it works well, I'll try a full uv solution in a long time, leaving time to the ecosystem to adapt instead of participating in the debugging

---

#### [2025-09-03 13:38:01] @lisiyuan666

Thank you very much for the help! I tested it and it worked correctly! But i got some question about ts_event and ts_init here, is the following explanation correct? If so, shouldn't we use ts_event to aggregate bars? In live trading, i found that all ts_inits are the system running time, if we use fetch historical data using request_aggregated_bars(). Then does it make more sense to aggregate by ts_event?

**Attachments:**
- [screenshot_1756906395.png](https://cdn.discordapp.com/attachments/924506736927334400/1412793762270285957/screenshot_1756906395.png?ex=68fad879&is=68f986f9&hm=da1b4cb62c3f7c98119bbde3d3d7ddc33b9b1734995ae3dca4f8346bd59a9b4a&)

---

#### [2025-09-03 13:39:52] @faysou.

It doesn't have to be like this, it was like this before, but I've changed ts_init to be equal to ts_event for historical requests and that's what the system needs for the catalog and backtests, ts_init needs to be well defined.

---

#### [2025-09-03 13:40:10] @faysou.

It's not meant to reflect the time of the request.

---

#### [2025-09-03 13:40:58] @faysou.

If it works now for you it's because of the change I've done, the change forces now adapters to define ts_init well.

---

#### [2025-09-03 13:41:36] @faysou.

I've modified some code for bybit and binance, I looked at the other adapters and they didn't seem to need to be changed.

---

#### [2025-09-03 13:42:26] @faysou.

I wouldn't believe too much what the agent says, I have more experience on this than the agent

---

#### [2025-09-03 13:44:39] @lisiyuan666

👍

---

#### [2025-09-03 13:45:22] @lisiyuan666

Thank you for the explanationand help!

---

#### [2025-09-03 13:45:34] @faysou.

You're welcome

---

#### [2025-09-03 13:46:29] @faysou.

Thank you for testing as well

---

#### [2025-09-03 15:59:26] @d_dot_zk

<@965894631017578537> https://github.com/wboayue/rust-ibapi  how'd you feel about this with NT?

**Links:**
- GitHub - wboayue/rust-ibapi: An implementation of the Interactive B...

---

#### [2025-09-03 16:00:03] @faysou.

Yes likely what we will use, when migrating the IB adapter to rust

---

#### [2025-09-03 16:04:23] @d_dot_zk

would you say Nautilus Trader is in a somewhat functional state to use this?

---

#### [2025-09-03 16:05:20] @d_dot_zk

or you reckon there'd be a plethora of bugs to iron out, i.e don't attempt to use an algo with it without expecting to do serious debugging

---

#### [2025-09-03 18:09:36] @faysou.

What do you mean with use this ? For now the IB adapter is in python as nautilus system is mostly in python/cython currently but the adapter will need to be migrated to rust when migrating to nautilus v2 which will be mostly in rust with python bindings.

---

#### [2025-09-03 18:11:20] @faysou.

The rust client above for IB is similar to what is used by the current IB nautilus adapter, so it should allow to retain the same structure of the adapater which should make the migration easier.

---

#### [2025-09-03 20:33:50] @d_dot_zk

by use this I meant coding in Rust then applying this adapter for the IB API via Nautilus, how buggy that would be / how much work would it need to get it done cleanly

---

#### [2025-09-03 20:34:31] @d_dot_zk

if it's a bit of tweaking and debugging or full blown development between the engine and the API

---

#### [2025-09-03 20:39:53] @faysou.

It will be done when moving to nautilus v2 will happen. It's a major development to implement/reimplement an adapter, especially one as complex as the IB one.

---

#### [2025-09-03 20:40:35] @faysou.

The IB one is complex because it needs to handle so many different asset classes.

---

#### [2025-09-05 14:00:18] @d_dot_zk

yeah I was wondering if I'd be able to do it but it seems like it might be a complicated process to get it to work properly, thanks though

---

#### [2025-09-05 21:07:41] @bartoelli

Hi, I'm playing with Quickstart from docs and something is wrong with indicators. I'm using Pycharm CE 2025.1 and uv.  Something is wrong with importing MovingAverageConvergenceDivergence indicator.

```python
from nautilus_trader.indicators import MovingAverageConvergenceDivergence
```
--> PyCharm: ```Cannot find reference 'MovingAverageConvergenceDivergence' in '__init__.py | __init__.py'```

In the __init__.py everything is commented out. Even if I uncomment all, then there is an error:
```
ImportError: cannot import name 'MovingAverageConvergenceDivergence' from 'nautilus_trader.indicators' (/home/XXX/Programs/Python/trader2/.venv/lib/python3.12/site-packages/nautilus_trader/indicators/__init__.py)
```

EDIT:

**The code still doesn't work however I found solution for this: 
```python
from nautilus_trader.indicators.macd import MovingAverageConvergenceDivergence``` -> need to add **.macd**

---

#### [2025-09-06 09:09:28] @cjdsellers

Hi <@542066292899708930> 
Apologies, this is because the examples are updated to use the `develop` branch version of the code, but you might be using the latest release from PyPI? next release will be very soon (the next day or so)

---

#### [2025-09-06 09:49:05] @bartoelli

Oh my bad, sorry. I am waiting impatiently for a new release :).

---

#### [2025-09-08 06:37:49] @joker06326



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1414499955346771989/image.png?ex=68fa75fd&is=68f9247d&hm=0671b498868ff27e31d41970e5b0e5d33ae47b8340cf5cffa9fb07a639692f86&)

---

#### [2025-09-08 06:38:26] @joker06326

My orderbook always has a zero price and quantity on ask, is it resonable?

---

#### [2025-09-08 07:06:52] @joker06326

The orderbook data comes from tardis orderbook_depth_5, loaded by TardisCSVDataLoader.load_depth10.

---

#### [2025-09-08 07:16:57] @joker06326

<@757548402689966131> I test this problem in live environment. In live, it works correctly. I think the problem comes from the loading of tardisloader.

---

#### [2025-09-08 13:32:55] @fdoooch

Is there any option to subscribe to Funding rate updates in NautilusTrader? Should I implement custom DataClient for this?

---

#### [2025-09-09 07:42:01] @cjdsellers

Hi <@1162973750787051560> 
Thanks for the report. This is probably a logical or parsing error for the loader method, looking into it

---

#### [2025-09-09 07:43:56] @cjdsellers

Hi <@670141000269955083> 
Actually funding rate updates are already wired through the platform, e.g. [subscribing from an actor](https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/common/actor.pyx#L1728) if you search docs and codebase you'll find where it's supported. Currently on `develop` and in dev wheels - next release very close now

---

#### [2025-09-09 08:20:26] @cjdsellers

Hi <@1162973750787051560> 
You were correct, this should now be fixed on `develop` branch. Please verify when/if you get a chance https://github.com/nautechsystems/nautilus_trader/commit/4d1ae566a1abe587c6cdf1d53d3f4224a19792ac

**Links:**
- Fix Tardis CSV loader for book snapshots · nautechsystems/nautilus...

---

#### [2025-09-10 02:52:00] @joker06326



**Attachments:**
- [2025-09-01.csv.gz](https://cdn.discordapp.com/attachments/924506736927334400/1415167902939746404/2025-09-01.csv.gz?ex=68fae9d0&is=68f99850&hm=56438b18e715cbc5ae2c57cc6a18614d4080f689f741f58306e3226661ba5ae4&)

---

#### [2025-09-10 02:52:26] @joker06326

This is a snapshot_5 tardis data of Bybit BTCUSDT SPOT.

---

#### [2025-09-10 02:55:00] @joker06326

<@757548402689966131> The problem remains. I shared more details of my code.
```
    def on_start(self):
        self.subscribe_order_book_at_interval(self.instrument_id, depth=5, interval_ms=100)

    def on_order_book(self, data):
        self.log.info(f"OrderBook: {self.cache.order_book(self.instrument_id)}")
        self.log.info(f"Spread: {self.cache.order_book(self.instrument_id).spread()}")
        self.log.info(f"MidPrice: {self.cache.order_book(self.instrument_id).midpoint()}")
```

---

#### [2025-09-10 03:02:02] @joker06326

I have used latest develop branch to reload the snapshot data, but the problem remains.

---

#### [2025-09-10 05:44:36] @joker06326

```
OrderBookDepth10(instrument_id=BTCUSDT-SPOT.BYBIT, bids=[BookOrder(side=BUY, price=108253.8, size=0.199572, order_id=0), BookOrder(side=BUY, price=108252.4, size=0.088222, order_id=0), BookOrder(side=BUY, price=108251.7, size=0.036457, order_id=0), BookOrder(side=BUY, price=108251.6, size=0.002277, order_id=0), BookOrder(side=BUY, price=108251.3, size=0.092369, order_id=0), BookOrder(side=BUY, price=0.0, size=0.000000, order_id=0), BookOrder(side=BUY, price=0.0, size=0.000000, order_id=0), BookOrder(side=BUY, price=0.0, size=0.000000, order_id=0), BookOrder(side=BUY, price=0.0, size=0.000000, order_id=0), BookOrder(side=BUY, price=0.0, size=0.000000, order_id=0)], asks=[BookOrder(side=SELL, price=108253.9, size=1.596319, order_id=0), BookOrder(side=SELL, price=108254.9, size=0.004618, order_id=0), BookOrder(side=SELL, price=108255.0, size=0.290031, order_id=0), BookOrder(side=SELL, price=108255.2, size=0.448830, order_id=0), BookOrder(side=SELL, price=108255.6, size=0.071549, order_id=0), BookOrder(side=SELL, price=0.0, size=0.000000, order_id=0), BookOrder(side=SELL, price=0.0, size=0.000000, order_id=0), BookOrder(side=SELL, price=0.0, size=0.000000, order_id=0), BookOrder(side=SELL, price=0.0, size=0.000000, order_id=0), BookOrder(side=SELL, price=0.0, size=0.000000, order_id=0)], bid_counts=[1, 1, 1, 1, 1, 0, 0, 0, 0, 0], ask_counts=[1, 1, 1, 1, 1, 0, 0, 0, 0, 0], flags=128, sequence=0, ts_event=1756684799850000000, ts_init=1756684800288729000)
```
After checking data in catalog, the orderbookdepth data is right. Maybe the problem occurs in the transformation of orderbookdepth10 to order book.

---

#### [2025-09-10 06:03:45] @joker06326

In additional, on_order_book_depth works correctly, but on_order_book works wrong.

---

#### [2025-09-13 14:46:58] @.islero

Hello everyone, I can’t find examples of using One-Triggers-Other (OTO), OCO, or OUO orders. Could you please suggest how to implement this? I’m using Bybit perps Venue, so this should work.

---

#### [2025-09-15 11:11:46] @.islero

I’ve already figured out the first issue, it’s probably done through a bracket, but here I have a much more serious problem, I’ll add the code below. last_quote is not None, a Market order opens for me but it immediately closes with a stop market order in live trading on Bybit Demo. And the same thing happens with a bracket: it works in backtesting, but not in live trading — and I don’t know what to do about it. Maybe the problem is with the Bybit Demo account itself.

BybitDataClientConfig uses Bybit Live API keys, while BybitExecClientConfig uses Demo API keys.

BYBIT: BybitDataClientConfig(
    api_key=os.getenv("BYBIT_INSTRUMENT_API_KEY"),  # 'BYBIT_API_KEY' env var
    api_secret=os.getenv("BYBIT_INSTRUMENT_API_SECRET"),  # 'BYBIT_API_SECRET' env var
    base_url_http=None,  # Override with a custom endpoint
    instrument_provider=InstrumentProviderConfig(load_all=True),
    product_types=[product_type],  # Will load all instruments
    testnet=False,  # If a client uses the testnet
    demo=False,
),

BYBIT: BybitExecClientConfig(
    api_key=os.getenv("BYBIT_API_KEY"),  # 'BYBIT_API_KEY' env var
    api_secret=os.getenv("BYBIT_API_SECRET"),  # 'BYBIT_API_SECRET' env var
    base_url_http=None,  # Override with a custom endpoint
    base_url_ws_private=None,  # Override with a custom endpoint
    instrument_provider=InstrumentProviderConfig(load_all=False),
    product_types=[product_type],
    testnet=False,  # If a client uses the testnet
    demo=True,
    max_retries=3,
    retry_delay_initial_ms=1_000,
    retry_delay_max_ms=10_000,
)

---

#### [2025-09-15 11:13:47] @.islero

And this is the code of the test method:
instrument:Instrument = self.strategy.cache.instrument(self.strategy.config.instrument_id)

        market_price = last_quote.ask_price if last_quote.ask_price is not None else last_quote.bid_price

        sl_val = market_price - (market_price * 4.0 / 100)
        tp_val = market_price + (market_price * 4.0 / 100)

        sl_price = instrument.make_price(sl_val) if sl_val is not None else None
        tp_price = instrument.make_price(tp_val) if tp_val is not None else None

        # 1) ENTRY
        entry_order = self.strategy.order_factory.market(
            instrument_id=instrument.id,
            order_side=OrderSide.BUY,
            quantity=instrument.min_quantity,
            time_in_force=TimeInForce.GTC,
            reduce_only=False,
            tags=["ENTRY"],
        )
        self.strategy.submit_order(entry_order)

        # 2) STOP-LOSS (no contingency kwargs supported by stop_market in this build)
        sl_order = self.strategy.order_factory.stop_market(
            instrument_id=instrument.id,
            order_side=OrderSide.SELL,
            quantity=instrument.min_quantity,
            trigger_price=sl_price,
            time_in_force=TimeInForce.GTC,
            reduce_only=True,  # prevents opening a new position
            tags=["STOP_LOSS"],
        )
        self.strategy.submit_order(sl_order)

---

#### [2025-09-15 15:22:41] @kompaktowl

Hello guys, I have a question that has been on my mind for sometime now.

In live markets, can I use historical data to initialise indicators faster?

---

#### [2025-09-15 15:35:13] @.islero

Yes, I’m using version 1.220, and I’m using request bars and request bars aggregated for live. It works fine.

---

#### [2025-09-15 15:37:06] @.islero

I’ve found the issue with my problem. The Bybit adapter wasn’t using the correct parameters for the Bybit API V5. So, I inherited the BybitExecutionClient and modified it, and now it works.

---

#### [2025-09-15 16:43:49] @faysou.

Yes look at request functions in actor.pyx

---

#### [2025-09-16 11:10:44] @nuppsknss

Hey guys, I'm backtesting futures with `NautilusTrader (v1.220.0)` at tick precision. 

I load raw TradeTick data from a Parquet catalog via `catalog.trade_ticks(instrument_ids=[instrument.id], start=BACKTEST_START, end=BACKTEST_END)`, then feed it directly to the backtest engine with `engine.add_data(data)`. The engine iterates over the ticks during `engine.run()` (no bars involved for full precision)

Any tips to optimize loading/iteration for large datasets, improve performance, or handle tick precision better? I am getting about 200k datapoints per second per core, sadly too slow for my usecase. 
Here's the key snippet:

```py

catalog = ParquetDataCatalog(CATALOG_PATH)

data = catalog.trade_ticks(
    instrument_ids=[str(instrument.id)],
    start=BACKTEST_START,
    end=BACKTEST_END,
)
if not data:
    logging.warning(f"No trade ticks found in catalog for {instrument.id} between {BACKTEST_START} and {BACKTEST_END}")
    return

config = BacktestEngineConfig(
    trader_id=TraderId("BACKTESTER-001"),
    logging=LoggingConfig(log_level=ENGINE_LOG_LEVEL),
)
engine = BacktestEngine(config=config)

engine.add_venue(venue=Venue(VENUE_CODE), oms_type=OmsType.NETTING, account_type=AccountType.MARGIN, base_currency=EUR, starting_balances=[Money(1_000_000.0, EUR)])
engine.add_instrument(instrument)
engine.add_data(data)  

strategy_config = EMACrossTWAPConfig(
    instrument_id=instrument.id,
    bar_type=BarType.from_str(f"{instrument.id.value}-{BAR_SPEC_INTERNAL}"),
    trade_size=TRADE_SIZE,
    fast_ema_period=FAST_EMA,
    slow_ema_period=SLOW_EMA,
)
strategy = EMACrossTWAP(config=strategy_config)
engine.add_strategy(strategy=strategy)


start_ns = dt_to_unix_nanos(pd.Timestamp(BACKTEST_START, tz="UTC"))
end_ns = dt_to_unix_nanos(pd.Timestamp(BACKTEST_END, tz="UTC"))
engine.run(start=start_ns, end=end_ns)
```

---

#### [2025-09-16 11:18:43] @faysou.

use BacktestNode and chunk_size

---

#### [2025-09-16 11:29:12] @faysou.

this will avoid loading all data at the same time. for iteration optimisation, I don't think much can be done except waiting that the new version using mainly rust gets released at some point.

---

#### [2025-09-16 12:11:13] @nuppsknss

Improved performance about 20%, thanks

---

#### [2025-09-16 12:11:26] @nuppsknss

still a lot away from desired outcome hahah

---

#### [2025-09-16 12:11:47] @faysou.

what's your desired outcome ?

---

#### [2025-09-16 12:11:49] @nuppsknss

yeah well
will fuck around some more

---

#### [2025-09-16 12:11:59] @nuppsknss

1M/s per core

---

#### [2025-09-16 12:12:11] @nuppsknss

Im switching from Openquant

---

#### [2025-09-16 12:12:29] @faysou.

maybe after the switch to rust

---

#### [2025-09-16 12:13:19] @nuppsknss

yea probably, thanks

---

#### [2025-09-16 17:44:51] @kompaktowl

Thank you.

---

#### [2025-09-16 17:45:11] @kompaktowl

Thank you.

---

#### [2025-09-16 19:30:34] @kompaktowl

Hello guys, what would you say is the approach to setting up one strategy on multiple instruments in a live environment?

`on_instrument` callback does not seem to be receiving data after requesting for instruments, currently using the Binance adapter.

Trying another approach where the instruments would be gotten from the cache in the `on_start` callback, is there a simpler approach or something different?

---

#### [2025-09-18 04:07:32] @cjdsellers

Hi <@749207824072179757> 
Looking into this, currently we just fetch the instrument(s) from the cache since they will be requested automatically at start with the default `InstrumentProviderConfig`. But if there is an explicit **request** then I think we should re-request instrument(s) from the external API? (current functonality can be maintained by just calling `self.cache.instrument` instead of making a request)

---

#### [2025-09-18 22:02:22] @shuo.zheng

Is there an example on how to dynamically subscribe to new instruments' data as the strategy is running? for example, at the start of each day, i want to subscribe to quotes/trades of all options with 1DTE of a specific underlying (SPX in this case):
* I assume I would need to first determine all the instruments that match "option where base symbol is SPX, 1DTE". **Is there some utility helpers to help with this**, ie like a `get_option_chain(base_symbol)` of some sort? **Or is this what `InstrumentProviderConfig` is for?**
* second, i would then need to iterate through all those instruments and subscribe to the data. **Where would be the best place within a strategy to do that?** Set up some sort of 24h timer to sub those instruments?
* I noticed that there's some way to do this with the IB adapters with `build_options_chain=True`, and still need to fully grok what's going on there, but wondering if there's **a data-provider agnostic way of approaching this?** I want to do this within a backtest using Databento

---

#### [2025-09-18 22:02:59] @shuo.zheng

maybe <@965894631017578537> you might know? seems like you've contributed quite a bit of work on options and IB adapter so figured you might be best to ask

---

#### [2025-09-19 02:22:17] @aaron_g0130

Hi guys, does anyone have a rough estimate of the backtesting speed benchmark.I want to know the baseline speed in general of each backtest form, especially 1min bar backtest. I've tried using empty on_bar function to just streaming bar for speed test, Starting backtest with 1951200 bars and completed in 36.71 seconds with no logic calculation at all. It runs 54000 bars per second ( all logs are disabled). I wonder is there any room for speed up.(maybe I did not correctly set up something or default setting is not the best performance setting). Maybe someone can shed some light on this question.

---

#### [2025-09-19 03:22:17] @dsalama345231

If I have multiple strategies running in the system, is there a way that I can query the "system" to get a status of the running strategies such as, which strategies are running, how many orders have they placed, how many orders have they closed, how many open orders they have, how many positions do they have, order-level p&l, etc. All this while the strategies are running.

---

#### [2025-09-19 03:26:30] @cjdsellers

Hi <@792981407122980875> 
Some kind of overview status method is not built-in. You could determine all of this with the combination of `Trader` and `Cache` though:
- https://nautilustrader.io/docs/nightly/concepts/cache
- https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/cache/base.pyx
- https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/trading/trader.py

You might also be interested in `Controller`: https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/trading/controller.py

---

#### [2025-09-19 03:36:34] @dsalama345231

Thank you <@757548402689966131>   Will definitely look at this and report back

---

#### [2025-09-19 10:19:07] @faysou.

Hi <@694719618396192838>  I suggest that you get more familiar with the platform before trying to use options. Also option features are experimental for now and not documented, you would need to look at the code to see what is possible.

---

#### [2025-09-19 10:22:04] @faysou.

There are some examples in the repo using these features, you can look in examples/backtest/notebooks and examples/live/interactive_brokers/notebooks

---

#### [2025-09-19 17:32:18] @spencer2929

Hi there! Two questions:

- I did a little searching, but haven't found much on connections to CQG for execution; am I missing any existing work on this?
- In terms of backtesting, we like to be able to backtest using a prescribed amount of time delay to understand latency effects. Is this achieveable in the current system?

Thanks! Happy to clarify anything.

---

#### [2025-09-22 01:20:59] @aaron_g0130

Hi everyone! Is there any other tricks to accelerate the backtest process (not considering strategy types) , for example: disable the log system.

---

#### [2025-09-22 03:27:58] @faysou.

Use cython for the strategy

---

#### [2025-09-22 03:52:14] @aaron_g0130

thanks I'll try

---

#### [2025-09-22 09:26:46] @gabadia5003

Good morning (US EST)I configured my trading node to subscribe to the message bug as follows. 

# -------- MessageBus → Redis (external stream for dashboards) ----------
        message_bus = MessageBusConfig(
            database=DatabaseConfig(
                type="redis",  
                host=os.getenv("REDIS_HOST", "nautilus-redis"),
                port= int(os.getenv("REDIS_PORT", "6379")),
                timeout=2,
            ),
            encoding="json",
            timestamps_as_iso8601=True,
            use_trader_id=False,
            use_trader_prefix=False,
            use_instance_id=False,
            streams_prefix=os.getenv("MBUS_STREAM_PREFIX", "demo")
            stream_per_topic=False,
            autotrim_mins=30,
        )

        TradingNodeConfig(
            trader_id=TraderId("Some Id"),
            logging=LoggingConfig(log_level=os.getenv("NAUTILUS_LOG_LEVEL", "INFO")),
            ...
            message_bus=message_bus,   # <— added
        )

I need to subscribe to redis streams to re-distribute the order and position state changes that my strategies run.  The mechanism seems to work well but I am having an issue with the stratgy_id that is included with the Redis stream data - see below

{"type":"OrderAccepted","trader_id":"TRADER-POLYGON-FIX","strategy_id":"BidAskStrategy-000",...}
{"type":"OrderFilled","trader_id":"TRADER-POLYGON-FIX","strategy_id":"BidAskStrategy-000",...}
{"type":"PositionOpened","trader_id":"TRADER-POLYGON-FIX","strategy_id":"BidAskStrategy-000",...}

No matter what I do, I always get "strategy_id":"StrategyName-000" and this prevents me from tracking all orders for one or other strategy.  And since I could be running tens of strategies this is a problem.  I have tried several approaches, including adding fields to the events, but have not been successful.

Any suggestions ?

---

#### [2025-09-22 15:51:03] @braindr0p

Take a look here:  https://nautilustrader.io/docs/latest/concepts/strategies#multiple-strategies
I think you have to set the order_id_tag in the StrategyConfig to something unique for the strategy instance.

**Links:**
- NautilusTrader Documentation

---

#### [2025-09-23 14:15:32] @user_top

Hello everyone. Can't find an information if options data (from Deribit) are supported in Nautilius via Tardis connector.

---

#### [2025-09-23 14:18:06] @user_top

Is there any way to play/backtest options data (like chains, quotes) in Nautilus in general?

---

#### [2025-09-24 01:56:57] @aaron_g0130

Hi there！Do I need to re-write BarDataWrangler from wranglers.pyx if I want to custom the fields of bar data (like: open,high,low,close,vwap,taker_buy,taker_sell etc.) or is there a general reusable template available？

---

#### [2025-09-24 22:47:21] @gabadia5003

The issue was the tag name.  I tried other tag names but not that one - thanks

---

#### [2025-09-25 00:19:27] @gabadia5003

Another question -  I am creating TradingNode's programatically and found out that one can only create a TradingNode once the strategy and all other configuration parameters for the TradingNode are know. I can work around this but would be great if I could create a TradingNode with the entire trading environment configured (market data and execution clients, etc.) except the strategy. Then when I know what strategy I want to execute I would just register/inject it with the TradingNode. Is this something that can be done ?

---

#### [2025-09-25 00:27:36] @yfclark

you need controller for dynamic strategies control

---

#### [2025-09-25 00:37:17] @topast

Does NautilusTrader take into account the impact on the OrderBook from simulated trades?
With candlesitcks it seems that I can fill in as many contracts regardless of volume.

---

#### [2025-09-25 01:29:57] @cjdsellers

Hi <@120670750326652928> 
Correct, there is no persistent market impact yet (I've made a note to spell this out more clearly in the backtesting docs). This is definitely a feature we can add once bandwidth opens up post Rust port of the core

---

#### [2025-09-25 12:07:10] @gabadia5003

Hi <@910880171576393728> , I do have some logic that I call a supervisor that allows me to configure and start many TradingNodes.  However, I have not been able to inject a strategy into the TradingNode onces it is created.  Could you please elaborate more on what a controller would do and what api it uses to do this.

---

#### [2025-09-25 12:12:13] @yfclark

I haven't looked into this for a long time. You can check here, and it might offer you some help.https://github.com/nautechsystems/nautilus_trader/issues/1936

**Links:**
- Add multi-instrument rotation trading example with Controller · Is...

---

#### [2025-09-29 03:56:34] @3sberzerk

Hi, I checked the docs and Discord but couldn’t find an answer to this:
How does the on_bar method in the Actor class behave for internal vs external bars?

For example, using 1-minute bar data:
 - Internal bars: It works as expected, with a new bar provided once per minute.
 - External bars: It seems to trigger on every tick, continuously updating the current 1-minute bar.

Is this the intended behavior?
I’m using Interactive Brokers with the latest stable version of Nautilus Trader.

---

#### [2025-09-29 04:40:21] @cjdsellers

Hi <@312252646314737666> 
Thanks for the report. This sounds like it could be a bug. While some traders would like to consume partial external bars continuously as they are formed, we *should* just be emitting closed bars per the spec

---

#### [2025-09-29 09:23:47] @mk27mk

Hi everyone!

I'm implementing a `NewsActor` to process and publish news events.
DeepWiki told me that I could publish all the events inside `on_start` and they would've been sorted by their `ts_init`, but they actually get consumed instantly by subscribers.
Am I missing something or I should publish each event inside `on_bar` when `bar.ts_init == event.ts_init`?
Thank you 😗 

```python
class NewsActorConfig(ActorConfig, frozen=True):
    start: str | int
    end: str | int
    impacts: set[NewsImpact] | None = None
    currencies: set[Currency] | None = None
    event_names: set[str] | None = None


class NewsActor(Actor):
    if TYPE_CHECKING:
        config: NewsActorConfig

    def __init__(self, config: NewsActorConfig) -> None:
        super().__init__(config)

    # ------------------------------------------------------------------
    # Start and stop
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        catalog = catalog_from_env()
        news_events = NewsEvent.from_catalog(
            catalog=catalog,
            start=self.config.start,
            end=self.config.end,
            impacts=self.config.impacts,
            currencies=self.config.currencies,
            event_names=self.config.event_names,
        )
        for e in news_events:
            self.publish_data(DataType(NewsEvent), e)
            self.log.info(f"Published {e}", color=LogColor.YELLOW)
```

edit: I was able to do it using alerts

---

#### [2025-09-30 13:29:03] @ido3936

Hello,
I am trying to modify the slippage model into something more severe, while running on a bars based strategy. 
For starters I tried the `OneTickSlippageFillModel`. When I run it - no order is fulfilled (these are MARKET orders). In fact, all of the fill model variants only fulfill demand if there is immediate supply available (BookOrder with positive quantity).

It is easy to show this also on a toy example.

When I asked the AI - based on code analysis - if this could be a bug, it responded with:
"You should verify your backtesting engine's market order implementation to ensure it can "walk the book" to find available liquidity at slipped prices."

Has anyone been able to make these fill models work with bars?

---

#### [2025-09-30 15:35:21] @haakonflaar

What number of bars/second can one expect from a backtest with no on_bar logic? I am currently seeing 20 000 bars/second which seems quite low. It's obviously CPU dependent but my CPU don't suck. I am running backtests through the low level API.

---

#### [2025-09-30 20:20:43] @theliminator

that seems pretty low, i vaguely recall my CPU doing 100-200k/s half a year ago

---

#### [2025-09-30 20:20:45] @theliminator

with no logic

---

#### [2025-09-30 20:20:54] @theliminator

might be your data loading?

---

#### [2025-10-01 03:49:31] @xcabel

I'm new to this and can be wrong. But I think you are mostly right that you need to publish per event but depends on how you define the NewsEvent class as subclass Data or Bar, you may want to publish in the on_data() and filter by data type to be NewsEvent

---

#### [2025-10-01 06:34:55] @haakonflaar

I am querying data from the catalog and adding it to the engine..I'll have to do some debugging

---

#### [2025-10-03 15:16:13] @ido3936

During reconciliation, what happens when a db-persisted cache contains information about open positions, but the client has already closed them? 
This is probably not meant to happen, but can still easily occur, and - in my case - had also caused my 'reduce only' order to open a new  SHORT position (as it tried to close  an already closed LONG position)
Both my understanding of the code, and actual runs, seem to point to this not being handled...

I will open a bug - but would love to learn that I got it wrong... <@757548402689966131> 

https://github.com/nautechsystems/nautilus_trader/issues/3023

**Links:**
- Reconcile positions that are open in the cache but closed in the cl...

---

#### [2025-10-04 11:26:03] @ido3936

I've created a bug with a minimal reproducing example. <@965894631017578537> ? Fixing cython code is beyond me

https://github.com/nautechsystems/nautilus_trader/issues/3031

**Links:**
- FillModel derived extensions do not "walk the order book" when usin...

---

#### [2025-10-04 12:44:24] @faysou.

I think that existing fill models are examples, you are supposed to write your own fill models. If you think the default models should be modified you can do a PR. Also cython is almost like Python, once you have a dev environment set up, you can do changes.

---

#### [2025-10-04 12:45:17] @faysou.

And with AI agents you have some help for programming and finding how to solve bugs.

---

#### [2025-10-04 13:52:31] @ido3936

My point is that they don't work (as advertised), and so also any variation on the same base model will not work at current
But if they are not on the main dev path - thats ok - at least theres now a bug with MRE set up

---

#### [2025-10-04 15:57:51] @faysou.

Ok thanks, I'll have a look at some point

---

#### [2025-10-04 20:13:14] @donaldcuckman

what do you guys use for visualizing your backtesting results? Just custom matplotlibs or is there something built in that i cant find?

---

#### [2025-10-05 00:10:00] @braindr0p

I'm just using customized mplfinance on top of matplotlibs .  Would be interesting to see what others are doing.

---

#### [2025-10-05 03:36:55] @fudgemin

if been using grafana for most everything visual, and am quite satisfied with the decision

**Attachments:**
- [grafana.png](https://cdn.discordapp.com/attachments/924506736927334400/1424238899936624650/grafana.png?ex=68faf456&is=68f9a2d6&hm=822042b1de631bd6fa41403fc55f9ff81bdab5d34c02d5665847d352c404a8c4&)

---

#### [2025-10-05 07:54:51] @dariohett

What is the standard way of interacting with a running system, such as changing a parameter without restarting? Is it defining an external stream and publishing on Redis?

---

#### [2025-10-05 14:36:14] @donaldcuckman

How long did that take to set up? Looks great!

---

#### [2025-10-05 16:23:13] @fudgemin

a day or two maybe. quite simple. Its using plugin charts, built ontop on js-react and  echarts. Allows near any custom panel i want. Data injestion is through QuestDB, simple query to the database with grafana. Ive used the platform for a year prior, but its faily intuitive once you play around. I dont think, actually im fully convinced i could not replicate the same thing, anywhere else, in such a fast manner, whille having it remain dynamic and scalable. This visual setup works across any strategy or backtest results i post to my database. Its once and done

---

#### [2025-10-05 16:24:27] @fudgemin

this is actually vectorbt backtest lol. I quick run against 150 sl, tp combos. Then i run event process tests in naut

---

#### [2025-10-05 16:56:52] @gabadia5003

Thanks for that example.  I created a "supervisor/manager" that receives strategies and launches them.  If I launch a new TradingNode for eah strategy it all works fine.  However, I do not think that is the best use of resources.  So, I was giving it a go to see if I could add/inject/register a Strategy to a running TradingNode.  I create my own controller following the example you gave, but unfortunately whatever I try I end up with errors like the ones below.  Can you please confirm or negate that it is possible to add new strategies to a running TradingNode.  And by new strategies I mean strategies that may not have even existed before the TradingNode was started.


2025-10-05T16:37:58.845224590Z [ERROR] TRADER-001.TRADER-001: Cannot add a strategy to a running trader
2025-10-05T16:37:58.845405090Z [ERROR] TRADER-001.BuyAtTheBidStrategy-82492e25: InvalidStateTrigger('PRE_INITIALIZED -> START') state PRE_INITIALIZED
2025-10-05T16:37:58.845422632Z [ERROR] TRADER-001.BuyAtTheBidStrategy-82492e25: InvalidStateTrigger('PRE_INITIALIZED -> START_COMPLETED') state PRE_INITIALIZED
2025-10-05T16:37:58.845467299Z [INFO] TRADER-001.DynamicStrategyController: Created and started strategy BuyAtTheBidStrategy-82492e25-ACCT-01
2025-10-05 16:37:58,845 - supervisor - INFO - Strategy created: BuyAtTheBidStrategy-82492e25-ACCT-01
2025-10-05 16:37:58,845 - supervisor - ERROR - DynamicStrategyController.add_strategy() failed: Strategy BuyAtTheBidStrategy-82492e25-ACCT-01 not registered in Trader after injection
2025-10-05 16:37:58,845 - supervisor - ERROR - Error type: RuntimeError
2025-10-05 16:37:58,845 - supervisor - ERROR - Trader state: 3
2025-10-05 16:37:58,845 - supervisor - ERROR - Current strategies in trader: []
2025-10-05 16:37:58,846 - supervisor - ERROR - Failed to execute strategy (job_id=82492e25): DynamicStrategyController failed to add strategy: Strategy BuyAtTheBidStrategy-82492e25-ACCT-01 not registered in Trader after injection

---

#### [2025-10-06 09:09:27] @ido3936

Hi <@797412687784312862> , much as I tried - I could not get the flow from Redis to the system working. I ended up setting an asyncio based server on a separate thread, with a handle to the message bus for passing on instructions. A client on a sperate process can then send instructions to the system

---

#### [2025-10-06 12:08:05] @donaldcuckman

what about for live trading?

---

#### [2025-10-06 12:09:00] @donaldcuckman

Im using rich in the terminal to display positions pnl etc but it kinda sucks

---

#### [2025-10-06 14:20:34] @gabadia5003

Hi there @imemo I have the same question now.  Did you ever figure out how to do this ?

---

#### [2025-10-06 14:21:47] @gabadia5003

Hi <@942323961809743892>, did you ever figure out how to add strategies to a running TradingNode ?

---

#### [2025-10-06 16:44:54] @dariohett

Appreciate the experience report, I’ll probably wrap the thing into FastApi then

---

#### [2025-10-07 16:07:12] @mohamadshoumar

Hey, we’re evaluating how to handle tick-level historical data for ~10 USDT pairs. Future plan is to add perpetuals pairs as well as all pairs for each coin. 
We had 2 options, add the data in house or use a 3rd party provider. 

Kaiko for example offers two options:
1️⃣ API-based – capped at 6,000 calls/min, each returning 1,000 ticks (≈6M ticks/min).
Given BTC averages ~500K ticks/day, that’s roughly a minute to fetch 12 days of data.
2️⃣ S3 dump – bulk historical data (CSV/Parquet) we can download directly (to be tested)

The other route is self-hosting on AWS (TimescaleDB), but it requires a proper data architecture (compression, tiering, etc.).

Our internal POC with NautilusTrader hit ~350K ticks/sec during backtests and ~500–600K ticks/sec retrieval from local TimescaleDB.

Curious if you’ve already tackled a setup like this before, or if you’d recommend one approach over the other or have a better provider in mind. 

Thanks

---

#### [2025-10-07 23:23:33] @topast

INB4 - I only use NautilusTrader for research purposes.

Personally, I would go with the S3 dump. If the data is in parquet format and you need an SQL like syntax you can use duckdb.

---

#### [2025-10-07 23:29:47] @topast

I mean, if you have the resources (human and capital) the timescaleDB is nice. But if you have such resources, I would just go for kdb or OneTick I suppose.

---

#### [2025-10-07 23:42:15] @topast

Thank you - to confirm your answer applies regardless if we are working with candlesticks, L1, L2 or L3 data correct?
In theory, it should be possible, or am I seeing something wrong?
https://github.com/nautechsystems/nautilus_trader/tree/develop/crates/execution

**Links:**
- nautilus_trader/crates/execution at develop · nautechsystems/nauti...

---

#### [2025-10-08 08:59:25] @cjdsellers

Hi <@120670750326652928> 
With L2 or L3 data you can simulate walking the book. The limitation right now is the next order to have execution simulated will see exactly the same data (it's always based on the historical data) - so no persistent changes to book state based on user orders yet. So yes, it is theoretically possible, just a future feature for now

---

#### [2025-10-08 09:49:31] @eleelegentbanboo

I’m having trouble backtesting with Tardis L2 market data.
I recorded the data using run_tardis_machine_replay, and here’s my configuration file: “{
  "tardis_ws_url": "ws://localhost:18001",
  "tardis_http_url": "http://localhost:18000",
  "normalize_symbols": true,
  "output_path": null,
  "options": [
    {
      "exchange": "bitmex",
      "symbols": [
        "linkusdt"
      ], 
      "data_types": [
        "book_change",
        "book_snapshot_2_50ms"
      ],
      "from": "2025-10-01",
      "to": "2025-10-03"
    }
  ]
}
”After recording, I only got one file like this:
/project/nautilus_trader/user_data/nt_oftrend/tardis/catalog/data/order_book_deltas/LINKUSDT-PERP.BINANCE/20251001.parquet

However, this file cannot be loaded directly using ParquetDataCatalog.

Has anyone successfully used this approach to build an L2 order book and run a backtest?

---

#### [2025-10-08 09:52:14] @eleelegentbanboo



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1425420516264640542/image.png?ex=68faa38e&is=68f9520e&hm=872aed1da594229c85690c63c331a661c1143f5cdaab0516ac940c352f786237&)

---

#### [2025-10-09 03:26:16] @cjdsellers

Hi <@960112626107547708> 
Thanks for the report. This should now be fixed: https://github.com/nautechsystems/nautilus_trader/commit/64040f21a1d7d1c6199642d02f59b3cf733bb2b7
You can install a [development wheel](https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#development-wheels) that includes the change, or compile head of `develop` branch. Let me know if you encounter further issues!

---

#### [2025-10-09 16:26:03] @eleelegentbanboo

Hi <@757548402689966131> 
First of all, thank you so much for fixing the previous issue — really appreciate your quick response! 🙏
However, I’ve run into a couple of new problems:
1. Path naming issue
The data currently recorded is saved under this path format:“/project/nautilus_trader/user_data/nt_oftrend/tardis/test/catalog/data/order_book_deltas/LINKUSDT-PERP.BINANCE/2025-10-01T00-00-00-000000000Z_2025-10-01T23-59-59-999999999Z.parquet
”But the loader expects it to be under:“/project/nautilus_trader/user_data/nt_oftrend/tardis/test/catalog/data/order_book_delta/...
” (Notice that order_book_delta should not have the trailing “s”).
Could this be aligned with the expected path?     2. Precision / schema issue
When running, I got the following error: "(trader) lyl@lyl:/project/nautilus_trader/crates/adapters/tardis$ python /project/nautilus_trader/user_data/nt_oftrend/src/run_l2_check.py
thread 'tokio-runtime-worker' panicked at crates/persistence/src/backend/session.rs:197:18:
called `Result::unwrap()` on an `Err` value: ParseError("price", "Invalid value length: expected 16, found 8")
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
" I compared it with a dataset that successfully runs backtests — that one has: "price: fixed_size_binary[16] not null
size: fixed_size_binary[16] not null
 ” But the Parquet files generated by the current code have:“price: fixed_size_binary[8] not null
size: fixed_size_binary[8] not null” The error happens at crates/persistence/src/backend/session.rs:197:18.
Should we update the schema to use the same 16-byte format for price and size as in the working dataset?
Thanks again for your help and for the previous fix!

---

#### [2025-10-09 16:37:25] @eleelegentbanboo

Hi <@757548402689966131> 

3. Parquet compression feature: snap disabled at compile time
   While recording data, I encountered this:
   thread 'main' panicked at /home/lyl/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/parquet-56.2.0/src/column/writer/mod.rs:364:62:
   called `Result::unwrap()` on an `Err` value: General("Disabled feature at compile time: snap")
   note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

This appears to be due to the parquet crate features in:
/project/nautilus_trader/crates/adapters/tardis/Cargo.toml

I changed:
parquet = { workspace = true }
to:
parquet = { workspace = true, version = "56", features = ["snap", "zstd", "lz4"] }

After that, recording no longer hit the above panic.
Would it make sense to enable "snap" (and possibly "zstd", "lz4") in the workspace defaults or in the adapter’s Cargo.toml so recording works out of the box?

Thanks again for your help! If it’s useful, I can provide a minimal repro (recording config + generated Parquet file) to validate the path, schema, and feature changes end-to-end.

---

#### [2025-10-09 16:41:03] @faysou.

Best thing if you find a solution is to do a PR.

---

#### [2025-10-10 07:44:57] @cjdsellers

Hi <@960112626107547708> 
Thanks for circling back with this feedback. I've added to my list and will try and get to it when I can. As faysou suggests, if you _did_ want to have a go at fixing anything then you'd be most welcome to submit a PR

---

#### [2025-10-10 12:09:34] @semihtekten

<@757548402689966131> asked this in <#924498804835745853> channel, asking here as well:
experienced metatrader expert advisor developer here. is there an ETA for visualization / GUI solution for NT? or is there any documentation that we can benefit, and use NT with? thanks in advance.

---

#### [2025-10-10 19:22:37] @patternmatching

This is probably a somewhat basic question, but I'm trying to confirm my understanding of how the clock works in Nautilus Trader.  Specifically, what are the various abstractions that can "fire" in an event-based fashion that advance the clock?  And to clarify, is this the only thing that moves the clock forward in time for a backtest?

---

#### [2025-10-10 21:23:06] @redyarlukas

Is there a good best practice how to handle option splits? E.g. SQQQ does a reverse split and when positioned the instrument becomes a non-standard SQQQ1 symbol. But for nautilus my position is still SQQQ and technically the new one is a different instrument. So I thought of replacing the instrument of my position. is this possible and the way to go?

---

#### [2025-10-11 09:38:37] @cjdsellers

Hi <@695636413344907306> 
Thanks for touching base on this again. This is actually something being worked on right now - a live trading dashboard, that will be one of the first premium products. Also per out-of-scope on the [ROADMAP](https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md#out-of-scope) not something that would be documented.

It would be premature to provide any ETA though, more like months than weeks - as we want to make sure it's of high quality.

As I mentioned in another thread, there's also a new subpackage for backtest `visualization` nearing completion, ETA for that 1-2 weeks.

Looking even further ahead, as we raise the bar on what's available in open source, we'll eventually make a lite version of the dashboard available to the community, and continually improve.

I hope that provides some more clarity!

---

#### [2025-10-11 14:00:07] @redyarlukas

I tried modifying the  instrument_id field of a position but its not writable when retrieving from the cache. <@757548402689966131> do you have a solution or workaround I can try? maybe via the messagebus? But how if this would be an option?

---

#### [2025-10-11 18:42:42] @semihtekten

thanks a lot. clarifies a lot. 🙏

---

#### [2025-10-12 20:46:32] @de.john

Hi everyone, what's the best practice to deploy a Nautilus strategy for high availability? Is there a neat way to run multiple instances of the same strategy for fault tolerance?

---

#### [2025-10-13 22:19:01] @donaldcuckman

Pretty sure my strategy has a lookforward bias. This cant be right lol

---

#### [2025-10-13 22:19:36] @donaldcuckman

is accessing the most recent bar in the cache a reasonable way of getting current price?

---

#### [2025-10-13 22:22:25] @donaldcuckman

In a pairs trading strategy how should i ensure the bar for each instrument is from the same "timestamp"?

---

#### [2025-10-13 22:25:26] @donaldcuckman



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1427422004180418620/image.png?ex=68faab56&is=68f959d6&hm=9b41aade94b704d6a52fd09d5049a9529b1e21e311a439a9f2e69994e9712caa&)

---

#### [2025-10-14 03:31:55] @stringer408

Is tauri suitable for data visualization for nautilus ?

---

#### [2025-10-14 08:48:59] @jftrades1_

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

#### [2025-10-14 11:43:25] @donaldcuckman

just didnt have any fees configured

---

#### [2025-10-14 13:02:35] @donaldcuckman

assumed they were inherent to the backtesting venue

---

#### [2025-10-15 14:14:20] @donaldcuckman

Anyone know what the timeline on hyperliquid integration looks like?

---

#### [2025-10-16 08:43:20] @georgey5145

anybody know how subscribe_instrument() works? if i call it in on_start(), it always raises error 'NotImplementedError: implement the `_subscribe_instrument` coroutine', but other methods like subscribe_quote_ticks() does not

---

#### [2025-10-16 16:53:38] @gz00000

I previously built a terminal-based dashboard using `textual`, but achieving high FPS in the terminal was challenging. So I later tried rewriting it with `Tauri` and only managed to create a demo. Now, I’m thinking of giving `iced` a try.

**Attachments:**
- [SCR-20240423-rpnc_.png](https://cdn.discordapp.com/attachments/924506736927334400/1428425670047957143/SCR-20240423-rpnc_.png?ex=68fa5d92&is=68f90c12&hm=dd51cf6fecdceb66d10a2ceec26997b4189866ad32159377c74e1c024f60c440&)

---

#### [2025-10-16 20:37:38] @one_lpb

Hello ! If we have Trades ticks and aggregating bars in 1 or 5 minutes, does trades are executed with Trades ticks précision or bars ? (sorry for my english)

---

#### [2025-10-17 14:00:25] @rmadanagopal_42070

Hello <@757548402689966131> I would like to simulate auction order fills in backtest. I gather that its not fully supported based on your comments above. Is this still  the case  or with the newer releases, it was supported. Also have a quick question regarding trade conditions and how nautilus simulated engine handles them. Like settlements, security close / open indication etc. Thank you

---

#### [2025-10-17 19:13:25] @mrforbes

I like to use https://github.com/plotly/plotly.py for graphs and just used tables for everything else. I could build some fancy elabrate UI as I'm a frontend engineer but doesn't seem like the best use of time. We're really just after the main data but visualizing charts like Equity curve and Drawdowns over a period is useful.

**Links:**
- GitHub - plotly/plotly.py: The interactive graphing library for Pyt...

---

#### [2025-10-17 20:56:48] @mrforbes

<@757548402689966131> really appreciate the work you and your team have done with Nautilus. It definetly allowed me to abandon the pure Rust backtester I was building. Question, I'm currently running a parameter grid with 51 runs which takes ~12 seconds on my machine. I ran the cProfile and notice the calls to analyzer eat up most of the processing time. I begin looking for ways to disable the calculate_statistics call in _log_post_run Cython but it looks like it's called by default. Is there another way to get around calling calculate_statistics?

---

#### [2025-10-17 21:10:30] @mrforbes

You can connect any frontend framework or raw HTML, CSS and Javascript with Tauri so you should be able to achieve your data visualization goals. You'll likely want to run your Tauri server, create a custom command that will trigger the backtest run like this:


#[tauri::command]
fn start_backtest(window: Window, name: &str) {
    ...
}

which can then be called from Javascript like this:

import { invoke, InvokeArgs } from "@tauri-apps/api/tauri";

 invoke("start_backtest");

---

#### [2025-10-17 21:18:49] @mrforbes

I end up using CPU-parallel parameter evaluation by chunking the parameter list, dispatch chunks via ProcessPoolExecutor (spawn context), then collect chunk results as they finish. Going from 12-14s to 2.5s run time

---

#### [2025-10-18 21:19:31] @questionablecube0988

How far into the middle office does Nautilus go - or plan to go in the future? For example, are there tools to reconcile a Nautilus position against IBKR? Similarly to feed a month's activity into an accounting system? Similarly to set risk limits?

---

#### [2025-10-19 01:48:37] @bre_n

Does anyone know why when you use the HistoricInteractiveBrokersClient and ask for data with start_time on the first day of the month, it gives you data from the 14th day of the previous month?

---

#### [2025-10-19 15:27:43] @donaldcuckman

very rough timeline? 1 yr? 1month?

---

#### [2025-10-20 04:35:00] @cjdsellers

Hi Raj, thanks for reaching out. It's one of those more advanced use cases that has been backlogged while we focus on the Rust port and some other things for now. We have simulations for contract expirations, including options although that's a little more advanced and experimental. Producing proper funding events and quanto settlements will be a goal for the cycle after this up coming release

---

#### [2025-10-20 04:36:14] @cjdsellers

Hi <@177932166859063296> 
On Hyperliquid there are many things being juggled, more like month units than year units of measurement though - many moving parts and high variance there

---

#### [2025-10-20 04:38:38] @cjdsellers

Hi <@678705087173885955> 
It's been a while since I profiled the backtest engine but this rings a bell. Did you check all of the configs? if there isn't one for this then it would be a good addition to be able to disable statistics calculations

---

#### [2025-10-20 04:42:05] @mrforbes

Hey <@757548402689966131> I checked all configs via the offical documentation and via Claude / Codex and found that calculate_statistics was being called from _log_post_run with no logic to disable. I wouldn't consider this a critical need but would be nice since it affects parameterized grid runs.

---

#### [2025-10-20 04:43:06] @cjdsellers

Thanks, agreed - added to my backlog list as it should be a quick-ish change

---

#### [2025-10-20 06:52:27] @jst0478

Hi, I've been scratching my head all day over an order book problem I'm seeing in my backtests. Could someone please try to help?

I'm running a backtest and my strategy is using Databento L3_MBO data for a timespan of about 6 months. When running my strategy in NT I see that it opens a position and then later closes it. The problem is that the closing price for the position is wildly off. For now I'm just using market orders to open, and the strategy `close_all_positions(instrument_id)` method to close. I realize that market orders and slipping could cause the price to vary, but I'm seeing closing price results that don't align with the order book at all. It's about $5+ off even though there is plenty of liquidity at a lower price. (Note: I'm getting a better price than expected for the close, resulting in my P/L for the trade being much higher than expected).

To debug, I've been opening up the Databento DBN file for that day and using ParquetDataCatalog `query(..)` method to examine order book data around the timestamp of closing the trade. Of course the DBN data is fine. And the ParquetDataCatalog query data also looks fine when querying it in isolation outside of the strategy. So the problem seems to be happening in my strategy somewhere. To debug in the strategy I'm printing the order book just before calling `close_all_positions(instrument_id)`. When doing this I see the incorrect prices printed by the book while the strategy is running.

Keeping in mind that my strategy is running for about 6 months of data, one interesting thing I found is that the price of opening the position and data in the order book at that time looks perfectly fine. It's only the close (about 5 months later during the backtest) where the order book is giving bad prices. It seems as if the order book is getting corrupted as time goes on in the backtest.

---

#### [2025-10-20 06:52:42] @jst0478

Am I doing something wrong with the order book? I'm simply calling `apply_deltas` in my strategy's `on_order_book_deltas` method like this:

```python
def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
    """
    Actions to be performed when the strategy is running and receives order book
    deltas.

    Parameters
    ----------
    deltas : OrderBookDeltas
        The order book deltas received.

    """
    self.instrument_1_book.apply_deltas(deltas)
```

I can't figure out what is going wrong. The only thing I can imagine is that NT's order book gets corrupted over time.

Any ideas?

---

#### [2025-10-20 07:06:56] @jst0478

Maybe it comes from gaps in MBO data? Should I be creating a new book each trading day or something?

---

#### [2025-10-20 08:11:57] @jst0478

Oh, maybe I figured it out..

I didn't make the connection that NT is also maintaining the order book internally, and that I can get it from the cache. I was trying to maintain a separate one myself in the strategy. I'll see if using the cached book fixes things.

---

#### [2025-10-20 08:25:30] @jst0478

Hmm, using the book from the cache didn't fix it. I get the incorrect prices from the cached book too.

---

#### [2025-10-20 08:31:09] @faysou.

From what I read about L3 in databento there's a daily snapshot in the data, I wonder if this could interfere somehow. You should look in the data engine.pyx that's where the logic is I think for maintaining the order book. I haven't checked the logic as I don't use L3 for now.

---

#### [2025-10-20 08:31:22] @jst0478

I dunno if this helps but here's a screenshot showing the order book printout from NT vs. what is in the DBN data for the same times

**Attachments:**
- [Screenshot_20251020_172951.png](https://cdn.discordapp.com/attachments/924506736927334400/1429748820719304714/Screenshot_20251020_172951.png?ex=68fa909a&is=68f93f1a&hm=3369341002ee7958575447ee1c49434571455b30c4e46b7bd8b3a4fb04d3ebea&)

---

#### [2025-10-20 08:31:52] @jst0478

The order book is badly corrupted.. ask prices below bids..

---

#### [2025-10-20 08:40:46] @deploya.dev_martin

What do people use in order to visualize backtests?

---

#### [2025-10-20 13:24:08] @donaldcuckman

Thank you!

---

#### [2025-10-20 15:23:14] @jst0478

Continuing this investigation...

I started checking the book at the beginning of each trading day during my strategy and saw that there is stale data in the book from the previous day.

After looking over DBN data and comparing it to the NT Catalog data, I believe DatabentoDataLoader's `from_dbn_file` method isn't returning order book events for Databento ["Clear"](https://databento.com/docs/standards-and-conventions/common-fields-enums-types#action?historical=python&live=python&reference=python) actions.

If I use DatabentoDataLoader to load a DBN file with a "Clear" action (which seems to be present at the start of every day of their data), it isn't giving me back any OrderBookDeltas for "Clear" actions. As a result, my NT Catalog has no order book delta for clearing the book, and during backtesting, the book is never cleared, leading to the stale data from previous days.

Can anyone else confirm?

And I don't know enough about Rust to really follow what's going on in DatabentoDataLoader. The code does seem to handle DBN Clear actions, but I'm not getting them back for some reason. I think the code is in https://github.com/nautechsystems/nautilus_trader/blob/develop/crates/adapters/databento/src/decode.rs#L345 for parsing MBO data.

I don't know if NT code needs to be fixed or not, but I think a workaround in the meantime is to manually add an order book delta with a "clear" action at the beginning of each day to my NT Catalog

**Links:**
- nautilus_trader/crates/adapters/databento/src/decode.rs at develop ...
- Common fields, enums and types | Databento standards

---

#### [2025-10-20 15:24:59] @jst0478

I'll try it tomorrow

---

#### [2025-10-20 18:00:47] @spitfire_rus

Hi, I found this platform while searching tool for backtesting L2 order books. In docs I cant find any info what backtest features does it have? OOS, walk-forward, some genetic/monte-carlo simulations? Any GUI btw?

---

#### [2025-10-20 18:01:28] @spitfire_rus

and I see it has only 10 depth order book data. Can I use 20 depth for example?

---

#### [2025-10-21 06:58:14] @oikoikoik14

Hi

I am a quant researcher for a mid sized prop firm. In my spare time, I have been building up a backend for nautilus trader for a while (getting data integrated and working for NT). This has all been done and tested, I am looking for way to visualize my results. Is there anybody that has some good experience, or even better, a repo to take some inspiration from? If so, please shoot a DM

---

#### [2025-10-21 15:31:19] @stringer408

is this built with tauri please?

---

#### [2025-10-21 15:32:29] @gz00000

The one in the screenshot was built using Textual.

---

#### [2025-10-21 15:33:36] @stringer408

have you built a tauri proj

---

#### [2025-10-21 15:36:52] @gz00000

As I mentioned earlier, I once built a demo similar to the one in the screenshot using `tauri`, but now I’m leaning toward using something like `egui` or `iced`. Based on recent research, `egui` might be the better fit. However, both the old `Cryptowatch` and the current `Kraken Desktop` were built with `iced`.

---

#### [2025-10-21 15:37:50] @stringer408

have you open the textual code 😄

---

#### [2025-10-21 15:38:24] @stringer408

can it be used for backtest

---

#### [2025-10-21 15:40:53] @gz00000

No, I eventually stopped using it myself — the FPS couldn’t keep up under HFT conditions. It’s not suitable for backtesting since it only connects to real-time data.

---

#### [2025-10-21 15:44:33] @deploya.dev_martin

Look into Dioxus, it might be a decent alternative based on specific requirements. Or you could go with Svelte + Tauri for desktop app. Or simply nextjs and have it based on the web.

---

#### [2025-10-21 15:47:18] @gz00000

Thanks for the information — I’ll do some research and take a closer look.

---

#### [2025-10-21 15:48:38] @gz00000

I used to work with `Svelte + Tauri + Tailwind`.

---

#### [2025-10-21 15:49:28] @deploya.dev_martin

Its a great setup aswell

---

#### [2025-10-21 15:49:53] @deploya.dev_martin

But what do you get from a desktop application that web can’t deliver?

---

#### [2025-10-21 15:50:28] @gz00000

And then I used `lightweight-charts` to draw the charts.

---

#### [2025-10-21 15:51:17] @gz00000

It’s purely a personal preference — I just like terminal or desktop applications better than web ones. 🙂

---

#### [2025-10-21 15:56:55] @gz00000

`Dioxus`, like `Tauri`, seems to rely on the system’s browser for rendering. That might mean extra effort is needed to handle cross-platform differences.

---

#### [2025-10-21 17:51:29] @deploya.dev_martin

Yes they do for now. Dioxus working on a replacement called Blitz

---

#### [2025-10-21 17:52:00] @deploya.dev_martin

Tauri might be able to render via Servo but its experimental

---

#### [2025-10-22 16:16:31] @c3max

whats the best way to start learning this as a noob like literal dummy noob

---

#### [2025-10-22 19:46:52] @fudgemin

experience? im self taught, 2 years dev. Ive been playing for a week or two now. Its quite daunting at first, lacking robust docs and examples. However, very well designed system. Once you grasp the components and configs, its fairly intuitive. Starts coming together quickly once you get the hang of the codebase

---

#### [2025-10-22 21:34:29] @sojourner6568

So thats what the issue was! Would you mind sharing some more details or code how you solved it?

---
