# NautilusTrader - #data

**Period:** Last 90 days
**Messages:** 226
**Last updated:** 2025-10-23 04:00:19

---

#### [2025-07-26 11:25:08] @melonenmann

I develop a strategy on 30min TF with LMT entries/exits. For backtest would it be still better to have 5 Min data and aggregate to 30 Min? Or what is the best approach to have good backtest performance? I'm wondering if the trades might not be precise in the backtest.

---

#### [2025-08-02 11:50:22] @premysl_22228

Hi, <@340916580449779713>. You have to decide between performance and accuracy. The smaller units will have the underlying bars, the more accurate outcome you got. Are you using any conditional orders like TP/SL? If your trading depends entirely on 30 minutes bars, I would recommend first to run optimizations using it (Do I suppose, you run some kind of hyperoptimization?) and then running the backtest on smallest unit possible to be sure, you won't get liquidated during the historical backtest.

---

#### [2025-08-02 19:13:18] @melonenmann

Yes, perhaps I will start with M30 and compare it then with additional   M5 Data. 
Yes, I have TP&SL which I want to create as Braket-Orders. Perhaps I'll try some trailing SL later. 
But the trading does not depend on M30 only. I take FVGs on the M30 and calculate the entries there.

---

#### [2025-08-02 19:22:05] @premysl_22228

How tight are your TP&SL? (eg. in percents of the value of the contract + leverage) Do you know, what is average length of your trade? Maybe, you will need even more detailed data, if you use the trailing stop loss or the duration is too small to get accurate backtest.

---

#### [2025-08-02 19:29:21] @premysl_22228

Do you know what is average profit you make out of trade + sigma [sqrt(VAR)]? If your average profit is too small and sigma too large, I would maybe recommend you to run the final backtest on tick data and train on smaller units like 5M. - Shortly said, the more detail your algo depends on, the smaller units you will need. You can find out the optimal combination by selecting smaller and smaller units and compering, and compare how fast the outcomes converges.

---

#### [2025-08-02 19:30:55] @premysl_22228

You need to find the compromise between performance and accuracy yourself.

---

#### [2025-08-03 10:50:35] @melonenmann

My trades take hours, and the TP is dynamic, but I would test if depending on ATR I can exclude the trades that are too tight or too wide. I aim a RR 1:2 and current Backtests shows a profit factor of around 4. Win rate is quite high (80%)... and I don't trust these numbers 😉 
I will just try out and compare the trades ... 
Thanks for your thoughts, I think, my strategy is not depending on low timeframe (at least not now) and therefore I start with the M30 data.

---

#### [2025-08-03 12:13:43] @premysl_22228

You are welcome. I don't know the instrument you are running on, but check also the liqudity if this is the case. I happended to me once, I had an algo with 300% profit per month running on 5M and backtesting on 1M and the bottleneck was the market liqudity, not necessary the market data resolution. 

And I also recommend to try to use paper trading...it shows some of the flaws in algo. I am not sure, whether we support paper trading with market depth consideration in NT ( <@757548402689966131> , <@965894631017578537> - do you know?), but it might be one of the way how to be more sure, whether you can trust it. Then trying lower amount of money, if you get true positive outcome and then you may try real money. If the low liqudity problem is the case, I recommend to not run on larger amounts of money until you get either L2/L3 backtest conformation or paper trading with depth consideration conformation, that you are ok and you still make money.

---

#### [2025-08-03 12:23:18] @melonenmann

<@1353826739851362345> fully agree, I tested on major FX and some higher-Liquidity minor FX pairs. AUDNZD had a really bad spread over night and this was not tradeable. Additionally I want to try out some stocks that institutionals own 35-80% of them and I had some good experience to check the average volume compared to previous days or weeks, but stocks are a bit special, and perhaps I need to reduce the trading times there to market open time. Let's see. Perhaps, I just go for indices. First, I need to get everything running and then I will start with very small money (2-3$ per trade)

---

#### [2025-08-03 21:31:52] @tobias.p

guys i am stuck with loading / adding my own data into the engine. (low level api)… first i got client id errors, then i added it… i cannot find any relvant docks as they all just publish the data inside the strategy.. and i get all sorts of weird errors. can some hint towards a simple example. My usecase are precomputed ML predictions and using these levels inside many optimization runs to speed it up and remove the gpu inference bottleneck as the exact inferences dont change.. i add the data successfully to the engine dataclient but get erros in cannot handle this datatype. i used the customdataclass decorator as per docs

---

#### [2025-08-03 21:34:13] @tobias.p

cannot handle request: unrecognized data type…

---

#### [2025-08-04 03:27:59] @cjdsellers

Hi <@211176121281019905> 
Are you passing the `client_id` to be associated with the data when adding to the engine? https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/backtest/engine.pyx#L650

Otherwise, it's either a mismatch with how you're arranging the data, or a bug in the data engine. Looking more deeply at the engine, the error you're seeing is occurring here https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/data/engine.pyx#L1540 in a path which only handles bars, quotes, and trades for some reason (custom data requests are supported and used to / should work)

---

#### [2025-08-04 07:20:32] @tobias.p

Thank you, I am looking at the engine.data right now and i noticed that my type is very long because thats how i import it from my own code.. Should this be a naming problem?
type(preds)
<class 'list'>
type(preds[0])
<class 'tradecore.strategy_v5.events.MLPredictionEvent'>

- Also, what am I excpected to use as the client id ? Right now i only see BINANCE.  i just want to inject the data.... can i just use my own made up string? this would be a great example for the git repo. thanks

---

#### [2025-08-04 07:25:16] @tobias.p

for what its worth: this is part of the optimization script where i prepare all the low level backtest stuff: (full script in attached file)
mainly this part:
```py

def get_confs(identifier: str) -> BacktestConfig:
    instrument_id_str = "BTCUSDT-PERP.BINANCE"

    # Create timeframes with both bid and ask bars
    timeframes = []
    for m in (1, 5, 15, 30, 60, 240, 1440):
        bid_bar = strategy.Timeframe(
            m, f"{instrument_id_str}-{str(int(m))}-MINUTE-BID-EXTERNAL"
        )
        ask_bar = strategy.Timeframe(
            m, f"{instrument_id_str}-{str(int(m))}-MINUTE-ASK-EXTERNAL"
        )
        timeframes.extend([bid_bar, ask_bar])

    bt = BacktestConfig(
        ideal_from_ts_unix=dt_to_unix_nanos(pd.Timestamp("2024-01-01")),
        ideal_to_ts_unix=dt_to_unix_nanos(pd.Timestamp("2024-04-01")),
        CATALOG_PATH=CATALOG_PATH,
        identifier=identifier,
        conf=strategy.Config(
            instrument_id=str(instrument_id_str),
            bar_type=f"{instrument_id_str}-{str(15)}-MINUTE-BID-EXTERNAL",
            IDENTIFIER=identifier,
            MODEL_VERSION="v20250518_183417",
            timeframes=timeframes,
            n_bars=100,
            trade_logic_bar_type_str=f"{instrument_id_str}-{str(15)}-MINUTE-BID-EXTERNAL",
        ),
    )

    return bt
````

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/924504069433876550/1401828320034816030/message.txt?ex=68fa811c&is=68f92f9c&hm=4e628dabb2298638271caff77103d7e257bc6f787e2f5acb874dc6ed65cc1db4&)

---

#### [2025-08-04 07:26:42] @tobias.p

```py
    bars = prepare_bars_fixed(
        catalog,
        conf.conf.timeframes,
        conf.ideal_from_ts_unix,
        conf.ideal_to_ts_unix,)
    ticks = prepare_ticks_fixed(
        catalog,
        conf.conf.instrument_id,
        conf.ideal_from_ts_unix,
        conf.ideal_to_ts_unix,
        additional_lookback_periods=2,
    )
    engine: BacktestEngine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id="TESTER-001",)  )
    engine.add_instrument(instrument)
    bar_evts = prepare_bar_events(bars)
    engine.add_data(bar_evts)
    if conf.inject_ML_Prediction_events:
        l.info("loading ML Prediction events")
        reader = prediction_reader.QuestDBReader(
            conf=prediction_reader.QDBReaderConfig(
                pgwire_conf=prediction_reader.PGWireConfig(
                    host="127.0.0.1",
                    port=8812,
                    user="admin",
                    password="quest",
                    dbname="qdb",
                ),
                model_version=conf.conf.MODEL_VERSION,
            )
        )
        l.info("QDBReader Config: " + str(reader.conf))
        import codetiming

        with codetiming.Timer(name="QDBReader MLPredictionEvents"):
            preds: list[events.MLPredictionEvent] = reader.read_ml_predictions_events()
        l.info("read " + str(len(preds)) + " events")
        l.info("injecting ML Prediction events: start")
        engine.add_data(preds, client_id=ClientId("MY_ADAPTER"))
        l.info("injecting ML Prediction events: end")

    s = strategy.Strat(strategy.NautilusStrategyConfig(main=conf.conf))
    engine.add_strategy(strategy=s)

    exec_algorithm = TWAPExecAlgorithm()
    engine.add_exec_algorithm(exec_algorithm)

    return Backtest_stuff(venue=BINANCE, engine=engine, bar_events=bar_evts, ml_prediction_events=preds)
````

---

#### [2025-08-04 07:29:49] @tobias.p

```py
from typing import List

import pandas as pd
import pyarrow as pa
from nautilus_trader.core import Data
from nautilus_trader.core.datetime import unix_nanos_to_iso8601
from nautilus_trader.model.custom import customdataclass

# predictions: dict: "{'60': {'classification_signal': [0.30673956871032715, 0.00540204718708992, 0.07710819691419601]}}"


@customdataclass
class MLPredictionEvent(Data):
    """
    Event containing ML prediction data.
    The @customdataclass decorator automatically handles the __init__ method,
    serialization (to_dict, etc.), and timestamp properties.
    """

    symbol_id: int
    horizon: str
    sell_prob: float
    hold_prob: float
    buy_prob: float
    raw_sell: float
    raw_hold: float
    raw_buy: float
    model_version: str

    processing_ts_real: int = 0  # Real-world wall-clock timestamp
    clock_now_ts: int = 0  # The 'current' time from the simulation clock

    def __repr__(self) -> str:
        # Manually format all fields for a consistent look
        return (
            f"MLPredictionEvent("
            f"symbol_id={self.symbol_id}, "
            f"horizon='{self.horizon}', "
            f"model_version='{self.model_version}', "
            f"buy_prob={self.buy_prob:.4f}, "
            f"ts_event={unix_nanos_to_iso8601(self.ts_event)}, "
            f"ts_init={unix_nanos_to_iso8601(self.ts_init)}, "
            f"clock_now_ts={unix_nanos_to_iso8601(self.clock_now_ts)}, "
            f"processing_ts_real={unix_nanos_to_iso8601(self.processing_ts_real)}"
            f")"
        )
````

i only overwrote the __repr__ as this is not done by the decorator.

---

#### [2025-08-04 07:37:09] @tobias.p

```py
before:
engine.kernel.data_engine.registered_clients
[ClientId('BINANCE')]
after:
engine.kernel.data_engine.registered_clients
[ClientId('BINANCE'), ClientId('MY_ADAPTER')]
```
Some of the error logs:
```sh
2025-01-03T10:00:00.000000000Z [ERROR] TRADER-000.DataEngine: Cannot handle data: unrecognized type <class 'tradecore.strategy_v5.events.MLPredictionEvent'> MLPredictionEvent(symbol_id=0, horizon='60', model_version='v20250518_183417', buy_prob=0.3136, ts_event=2025-01-03T10:00:00.000000000Z, ts_init=2025-01-03T10:00:00.000000000Z, clock_now_ts=2025-01-03T10:00:00.000000000Z, processing_ts_real=2025-08-02T21:37:39.412563200Z)

```

---

#### [2025-08-04 07:49:23] @tobias.p

OK so for anyone else in the future with a similar issue:

By searching this discord, i found <@757548402689966131> posts about using CustomData and how this is the other type that the data engine can handle, which solved my issue:

```py
preds_custom = [CustomData(data_type=DataType(type=type(p)),data=p) for p in preds]
        l.info(f"preds_custom[0]: {preds_custom[0]}")
        engine.add_data(preds_custom, client_id=ClientId("MY_ADAPTER"))
```

```sh
2025-01-06T22:00:00.000000000Z [INFO] TRADER-000.Strat: on_data: <class 'tradecore.strategy_v5.events.MLPredictionEvent'>MLPredictionEvent(symbol_id=0, horizon='60', model_version='v20250518_183417', buy_prob=0.3136, ts_event=2025-01-06T22:00:00.000000000Z, ts_init=2025-01-06T22:00:00.000000000Z, clock_now_ts=2025-01-06T22:00:00.000000000Z, processing_ts_real=2025-08-02T21:43:24.822571008Z)
```


again, if anyone is interested in writing the MT5 adapter in rust i have now found both a REST Api and a ZMQ api on github that seem to work, otherwise i thought about running the pyRPC MT5 api inside rust to get these few result account/position/ or tick/bar values easily that way.

---

#### [2025-08-04 19:40:46] @aleburgos.

someone tried  connect NT to articDB?

---

#### [2025-08-06 16:42:32] @premysl_22228

What do you need it for? For cache (this is very probably a lost battle) or as data source?

---

#### [2025-08-07 12:12:54] @aleburgos.

data source

---

#### [2025-08-09 01:31:01] @shuo.zheng

I couldn't seem to find this in the documentation - is there a way to subscribe and work with option chain data of an underlying symbol? (if the root symbol is a derivative of the underlying, ie. SPXW -> SPX)
is this a use case for Custom Data?

---

#### [2025-08-10 12:54:27] @saruman9490

Hi all, got a question - do composite bars get rebuilt on request_bars? ie. does the engine request the underlying bars and then rebuilds the composites? Last time I checked this was not the case esp. for the binance client

---

#### [2025-08-10 16:32:14] @faysou.

Yes it's possible. I worked on this a lot last year. You need to use request_aggregated_bars

---

#### [2025-08-10 16:32:49] @faysou.

There's an example doing this, it's also in the documentation

---

#### [2025-08-10 18:09:29] @saruman9490

Shouldn't both work

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924504069433876550/1404164772353671340/image.png?ex=68fa6f59&is=68f91dd9&hm=6c85680e3ecc3b785776a7cb62ee5d0bf3674bd87673d72150a3894595b8da63&)

---

#### [2025-08-10 18:09:30] @saruman9490

?

---

#### [2025-08-10 18:09:40] @saruman9490

why the need for a separate method?

---

#### [2025-08-10 18:12:11] @faysou.

request_aggregated_bars can aggregate several bars from one request. So basically it's a different method, it takes a list as argument.

---

#### [2025-08-10 18:13:25] @faysou.

You can even do nested aggregation, 1m external aggregated to 5m internal itself aggregated to 1 hour internal for example

---

#### [2025-08-10 18:21:08] @melonenmann

I needed to add the catalog to the config (the is somewhere a comment from me) to get the aggregated bars working.
And in <#924499913386102834> is a question from me because the aggregated bars contain wrong high values.

---

#### [2025-08-10 19:19:20] @faysou.

You need an MRE (minimum reproducible example) so someone can have a look. Just saying there's a problem doesn't mean there is one if your problem can't be reproduced, I have no idea what you have done. If you have an MRE I'll be happy to fix it.

---

#### [2025-08-10 19:30:41] @melonenmann

Thanks, I'll prepare it and send it here

---

#### [2025-08-10 19:32:08] @faysou.

Ok

---

#### [2025-08-10 20:27:45] @saruman9490

but if I need only 1 aggregated bar or want to build them separately should the normal request_bars work?

---

#### [2025-08-10 20:31:52] @faysou.

No

---

#### [2025-08-10 20:32:19] @faysou.

request_bars doesn't aggregate

---

#### [2025-08-10 20:33:48] @faysou.

I wanted initially to do like you say, but <@757548402689966131> preferred a separate function. It's ok, it still works.

---

#### [2025-08-11 05:09:01] @saruman9490

Ok, thanks for the clarification!

---

#### [2025-08-11 05:09:35] @saruman9490

Because in documentation it seemed like both composite and normal were supported by request_bars, but if it does not and aggregated does it does make more sense 🙂

---

#### [2025-08-11 06:18:25] @melonenmann

I'm super sorry, I found the bug on my side while preparing the reproducer. I used a bit AI for generating some code (I'm not so familiar with python and still struggeling a bit with the syntax) and it generated in the log output bar.close and not bar.high
I guess thats the price of using AI ... it's often just wrong. But still quite helpful, when you don't know the syntax, yet

---

#### [2025-08-11 08:31:37] @didierblacquiere

Try using VSCode with Kilocode extention

---

#### [2025-08-11 09:01:36] @melonenmann

PyCharm is much better then VSCode in my opinion. I just need to control the output a bit more. Its often too easy to just press Tab 🙂

---

#### [2025-08-11 10:28:07] @melonenmann

<@965894631017578537> Now here is a reproducer, when I call request_aggregation_bar from on_bar.
First time I receive correct values for the W1 bars (when called from on_start).
And then I call it from on_start (after a new weekly bar came in) --> goal is to calculate the weekly highs from last 12 weeks (and re-new every week)
In the zip file is a log with more logs, here just summarized:

-> the on-bar incoming bar is correct
`2025-04-07T00:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: 1week bar detected: EUR/USD.SIM-1-WEEK-LAST-INTERNAL,1.08317,1.11465,1.07779,1.09555,246000000,1743984000000000000 | Bar time: 2025-04-07 00:00:00+00:00`

--> and here I receive 12 W1 bars but with all the same data except the date in (also the one that I receive already in on_bar 2025-04-07)
`2025-04-07T00:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: historical data reveived: 2025-01-13T00:00:00.000000000Z h=1.09555
2025-04-07T00:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: bar in: 2025-01-20 EUR/USD.SIM-1-WEEK-LAST-INTERNAL,1.09555,1.09555,1.09555,1.09555,0,1737331200000000000
2025-04-07T00:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: bar in: 2025-01-27 EUR/USD.SIM-1-WEEK-LAST-INTERNAL,1.09555,1.09555,1.09555,1.09555,0,1737936000000000000
...
2025-04-07T00:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: bar in: 2025-04-07 EUR/USD.SIM-1-WEEK-LAST-INTERNAL,1.09826,1.09832,1.09451,1.09555,1000000,1743984000000000000
2025-04-07T00:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: historical data reveived: 2025-04-07T00:00:00.000000000Z h=1.09832
`

**Attachments:**
- [repro.zip](https://cdn.discordapp.com/attachments/924504069433876550/1404411051671289989/repro.zip?ex=68faabf7&is=68f95a77&hm=a8c3c2412cbea004fe78ffffe1f66bf91ba17821e974dd0acd4b2a21da77749e&)

---

#### [2025-08-11 10:30:29] @faysou.

request_aggregated_bars shouldn't be called from on_bar

---

#### [2025-08-11 10:30:45] @faysou.

it's designed to be called in on_start to update indicators

---

#### [2025-08-11 10:31:01] @faysou.

and update the cache with past bars when a backtest or live starts

---

#### [2025-08-11 10:34:50] @melonenmann

Ok, understand. Than I will store the data and update it when a new W1 bar is coming in

---

#### [2025-08-11 10:35:00] @faysou.

what happens is that probably you mess up the cache by updating with past values in the middle of a stream of new bars

---

#### [2025-08-11 10:35:21] @faysou.

I don't think you need to store new bars, they are stored in the cache

---

#### [2025-08-11 10:35:51] @faysou.

I recommend you to clone the project and look at the code that the's fastest way to know what is done exactly in the code

---

#### [2025-08-11 10:36:50] @faysou.

look at actor.pyx for data functions, strategy.pyx for order functions, look at the data engine.pyx as the coordinator for data requests and responses, look for the execution engine.pyx for orders and execution coordinator

---

#### [2025-08-11 10:36:59] @faysou.

then there are more components available but that's a start

---

#### [2025-08-11 10:38:20] @faysou.

https://deepwiki.com/nautechsystems/nautilus_trader

**Links:**
- nautechsystems/nautilus_trader | DeepWiki

---

#### [2025-08-11 10:38:29] @faysou.

look here as well it's getting updated it seems

---

#### [2025-08-11 10:38:38] @melonenmann

I will do so. I'm still at the very beginning and often not sure how to do things correct within the given architecture.

---

#### [2025-08-11 10:38:56] @faysou.

and use an agent to ask questions about the code once you have cloned the code, they are very powerful

---

#### [2025-08-11 10:39:09] @faysou.

it's ok, no problem, as long you learn and make progress it's fine

---

#### [2025-08-11 10:39:19] @faysou.

at least you're trying

---

#### [2025-08-11 10:40:07] @faysou.

I've said it in the past I use augment code, it's very powerful to understand the nautilus code as there are a lot of files. I don't understand why not more agent alternatives emphasize context engineering.

---

#### [2025-08-11 10:41:59] @faysou.

it will be easier for LLMs to understand nautilus' code once the migration away from cython will be done, then there will be just rust and python code and not two versions of the same code as is the case currently, which is normal during a migration

---

#### [2025-08-11 10:42:24] @faysou.

also rust can be debugged unlike cython which will be great

---

#### [2025-08-11 10:43:18] @faysou.

I've even added a few weeks ago some instructions to do mixed debugging with python and rust from a jupyter notebook inside vscode. which is basically the most useful thing we can wish for for debugging

---

#### [2025-08-11 10:43:46] @faysou.

ok it requires vscode, but at least it's possible

---

#### [2025-08-11 11:32:56] @melonenmann

That was a good hint, that there is a cache 😉 Found it and solved the problem. Thanks
I will keep on reading ...

---

#### [2025-08-11 15:14:50] @shuo.zheng

Bump on this in case it got missed

---

#### [2025-08-12 20:30:41] @saruman9490

I'm testing this in a live setup and was wondering do I need to change anything in the data engine configuration as I don't see the aggregated bars being shipped back. I see the request but nothing comes back. I'm using a Binance Client and non-aggregated requests worked so far. Any ideas?

---

#### [2025-08-12 20:31:06] @saruman9490

should I set a callback?

---

#### [2025-08-13 04:43:02] @saruman9490

Adding an MRE which request_aggregated_bars, but I am only managing to capture the raw 1-MINUTE-EXTERNAL. Let me know if this works otherwise for you 🙂
(Also, my first ever MRE! 🙂 )

**Attachments:**
- [request_aggregated_bars.py](https://cdn.discordapp.com/attachments/924504069433876550/1405048983663018056/request_aggregated_bars.py?ex=68fa5b16&is=68f90996&hm=652e3d556688c7eb8b6a5e035014bf3ac81c17e54ad3b16ac960c089b32d5b6d&)

---

#### [2025-08-13 04:44:38] @saruman9490

Attaching the logs as well 🙂

**Attachments:**
- [logs.mre.txt](https://cdn.discordapp.com/attachments/924504069433876550/1405049388954419252/logs.mre.txt?ex=68fa5b76&is=68f909f6&hm=c92d0ca1e005bc71795613ff13cff416e6edb704c953c782df1a490b456480b1&)

---

#### [2025-08-13 07:14:06] @cjdsellers

Hi <@694719618396192838> 
You may find some helpful information on option chains [here](https://nautilustrader.io/docs/nightly/integrations/ib#option-chain-retrieval-with-catalog-storage)

**Links:**
- NautilusTrader Documentation

---

#### [2025-08-13 07:14:43] @cjdsellers

Hi <@337157623352655873> thanks for the MRE!

---

#### [2025-08-13 15:12:26] @faysou.

I'm not using binance so I can't debug this. Adapters are in python currently and can be debugged. You would need to put some breakpoints in data.py to see which part of the code is reached. You can also debug which part of the code is reached in the data engine by putting some log instructions and rebuilding with make build-debug.

---

#### [2025-08-13 15:17:38] @saruman9490

Is aggregation happening on the client? Or in the engine?

---

#### [2025-08-13 15:18:33] @saruman9490

Yeah I'll try to trace where the issue happens, just thought that's it happens at the engine level instead of adapter

---

#### [2025-08-13 15:19:01] @saruman9490

Which adapter did you develop tho? Maybe could get hints there

---

#### [2025-08-13 15:47:42] @melonenmann

Do you use a catalog, <@337157623352655873>? If yes, Try to add the catalog to the config. Not only the data

---

#### [2025-08-13 16:36:03] @faysou.

Yes

---

#### [2025-08-13 17:20:53] @saruman9490

yeah, I do

---

#### [2025-08-13 17:21:44] @saruman9490

tho not for live

---

#### [2025-08-13 17:22:08] @saruman9490

is catalog necessary for live as well?

---

#### [2025-08-13 18:25:55] @saruman9490

Question atm my assumption is that the aggregation is done at the data client level. Wouldn't it make sense to do it at the data engine level tho? Since aggregation is something which could be applicable to all the adapters

---

#### [2025-08-13 18:30:56] @saruman9490

OR an actor which would capture these requests.

---

#### [2025-08-13 18:33:53] @saruman9490

Actually could someone hint me how I could intercept a data request, convert it to client received and then do the aggregation. Similar to execution_algorithm but on the data side. An approach could be to use a custom venue ( eg. SIMULATED ) and have a data client matched to it which would

---

#### [2025-08-14 12:59:32] @finddata_49439_09644

where is the permanent data code example , i tried many times the code still cant work , i want use the database or permanant file

---

#### [2025-08-15 05:41:42] @saruman9490

The stack [here](https://github.com/nautechsystems/nautilus_trader/blob/af72cab918489a04a7a3846231b6bac8a3ff1da0/nautilus_trader/data/engine.pyx#L2082) is just ideal to do what I need, but I just don't get what is going wrong 😄 Is there an example of this working live?

---

#### [2025-08-15 09:00:49] @saruman9490

I think I've figured out what is the problem!

The reason why TimeBarAggregator fails on live is because it is usint ts_init which when live is always set to when the requested data is returned.

In particular [this bit ](https://github.com/nautechsystems/nautilus_trader/blob/46f924b5a38bfbd106637d70c8c21dfa9324b456/nautilus_trader/data/aggregation.pyx#L1067-L1088)

It also explains why this works in backtest since ts_init there is pretty much ts_event. Moreover, it explains why it works on subscriptions, but not when running live after requests

---

#### [2025-08-15 09:10:40] @saruman9490

I'd even suggest to rebuild aggregators off tsevent as it would make it consistent with external systems

---

#### [2025-08-16 01:05:35] @premysl_22228

I am working on refactor of TimeBarAggregator, as it is a bit in bad shape. Even through I agree with you, that current ts_event logic makes no sense, I would still keep it...in a little bit form.

I understood, that you use externally aggregated bars, so TimeBarAggregator code shouldn't be involved. Is that correct?

---

#### [2025-08-16 04:13:01] @saruman9490

I have a limited set of externally aggregated bars which I want to supplement with internally aggregated ones, so using TimeBarAggregator is necessary. My biggest issue with it was that I cannot preload the buffers with request_aggregated_bars in live deployment and now I know why 🙂

---

#### [2025-08-16 04:14:11] @saruman9490

I've reviewed the most of TimeBarAggregator while I was digging and I don't find it particularly bad, just the choice for ts_init was a weirder one. Note that non-bar update does use the ts_event so I am curious to hear why is that

---

#### [2025-08-16 08:18:26] @saruman9490

Question, does nautilus support custom aggregations?

---

#### [2025-08-16 08:23:57] @faysou.

I don't know why you regularly say that the time bar aggregator is in bad shape. It's been months you say this and I'm still not convinced of what is wrong with it. I've spent a significant amount of time in making it work for aggregating past bars, this feature didn't exist before, and all I read is critics. You're free to improve it instead of just criticising.

---

#### [2025-08-16 08:44:35] @premysl_22228

By 95% the phase 1 is done, only tests are missing. I don't solve there the few lines mentioned yet...if I remember correctly, you told me, it was copy paste, as you didn't understand what it is doing. Now I am with relatively high confidence, that the few lines, which repeats across the whole aggregator doesn't make much sense. I tried to give them some sense for hours and came out with this result. I even tried to reimplement the things, which I thought the lines might be for and the end result was always, it does nothing useful, not implementing new features like RIGHT_OPEN.

---

#### [2025-08-16 08:46:11] @premysl_22228

The tests take so long, because I need test data, Chris is due to licensing and T&C unable to publish data on R2 and I have to make sythetic data generator, so the tests are persited.

---

#### [2025-08-16 08:59:43] @premysl_22228

(If I am talking about the wrong part of code, I am sorry. There was much of discussion about it. But the point remains the same for the whole TimeBarAggregator, there are parts you yourself as an author told you don't understand and you just passed on, and after throughful investigation I think, I almost know, there are parts of code, which has no real purpose and is sometimes potential source of bugs - I didn't just to refactor it without a reason, so I digged deeper for original meaning. Either I have done some bad mistake multiple times, or...)

---

#### [2025-08-16 09:05:09] @premysl_22228

To be complete, I won't be able to document every line in PR, it was a long multiweek investigation before I started dropping things either in concepts/plans or later in the code. The understanding and believing some parts of code are code are correct took me a substantial amount of time, much more the reimplementation, that's second reason why I call it low quality code. But to not to say only bad things, the start_time computation is really nice, I have only optimized for performance using some algebra and added proof of correctness, my own reimplementation wasn't so nice.

---

#### [2025-08-16 09:19:58] @premysl_22228

<@965894631017578537>, feel free to question my judgment about the TimeBarAggregator code, I will gladly explain, why I think, I am truthful now, or apologize for making bad judgment, if you show me, that my judgment is really bad. In principle, it does nothing to do whether my redactor is submitted or not, as I mainly critize the methodics by critizing the code of submitting something you don't (or anyone else) understand and I think we should always at least mark the parts of code, which we are not sure about, to be part of throughful manual code review procedure by Chris or someone else. The opposite is dangerous antipattern in my opinion, which promote bugs and makes codebase readability much worse.

---

#### [2025-08-16 10:17:16] @faysou.

I understand your thinking and I see your intentions are good. At the time I worked on this part of the code I was less seasoned in modifying nautilus so didn't dare to remove code I didn't understand. Still there were tons of edge cases for simulating time when aggregating bars in the past. I welcome a new refactor, that's actually the point of releasing contributions as open source, so other people have the opportunity to improve them, which is good for me as well.

---

#### [2025-08-18 10:41:33] @baerenstein.

hi guys, i am trying to get trade data and saw that tradetick objects exist. is there also directly a tradeevent or just trade object that resembles the on market executed trades?

---

#### [2025-08-18 11:12:56] @faysou.

that's what tradetick is for

---

#### [2025-08-20 23:02:11] @mk27mk

Hi to everyone, I need an advice.
I’m currently using Bar data and I would like to add an open_interest attribute to the class and some other methods to make the api suit my needs.

Would subclassing Data be the right approach for that? And then use on_data instead of on_bar inside MyStrategy?

---

#### [2025-08-21 07:41:28] @cjdsellers

Hi <@1260594339407597569> 
I'd recommend the same approach as `BinanceBar` and just subclass `Bar`, hope that helps!

---

#### [2025-08-21 09:42:08] @mk27mk

Thank you <@757548402689966131> ! I hadn't seen the `BinanceBar` class.
I'm going to subclass `Bar`, do I have to change the `on_bar` handler like this?

```py
def on_data(self, data):
  if isinstance(data, MyFancyBar):
    ...
```

Then I think I'll have to change how I read/write this data to catalog a bit but I'll figure it out later.
P.S. I don't want to sound silly, I'm  digging into the docs, but some cognitive overload kicked in 😵‍💫

---

#### [2025-08-23 18:13:39] @mk27mk

Hey <@757548402689966131> and others,  I got another question 😅 .
After implementing something like `FractalPattern(Data)` or `LondonSessionStats(Data)`, the correct way to store them in `Cache` is through `Cache.add` (correct me if I'm wrong).
But `Cache._general` dictionary doesn't allow me to store whole deques of data like is done with `Cache._bars`.

Would extending `Cache` adding something like this be a good way to approach the problem? Or I'm gonna break something?

```python
# inside MyCache(Cache)
self._patterns = dict[str, deque[FractalPattern]] = {}
# define other methods for retrieval and manipulation
```

p.s. I'm not using strategy attributes because I need to share this data across strategies

---

#### [2025-08-23 18:18:03] @mk27mk

p.p.s I realized  I can probably use a custom Actor to accomplish this data sharing between strategies, gotta go back to the docs.
once again, thank you for reading, have a good weekend😁

---

#### [2025-08-24 00:34:15] @cjdsellers

Hey <@1260594339407597569> 
You're on the right track. Using actors and publishing on the message bus is the most straight forward way for working with custom types and functionality like that 👌

---

#### [2025-08-24 11:13:23] @mk27mk

Glad to hear that! I'll update you once I've built a solution (or encountered bigger problems 🤪 )

---

#### [2025-08-24 20:35:38] @ido3936

Indeed, externally built bars align with internally aggregated ones when both are indexed by `ts_init`, but not when indexed by `ts_event`. Shouldn't it be the other way around?

---

#### [2025-08-25 04:41:54] @saruman9490

This is the interplay between the adapter which sets the ts_init and aggregator which assumes that ts_init/ts_event are something particular and only if those two understandings match the aggregator gives consistent results. Eg. now the requirement coming from the TimeBarAggregator is that the adapter sets ts_init as the bar start time,  which I've confirmed Binance does not do and Databento does. So works for one but not the other 🙂 I've personally rebuilt the aggregator to work with ts_event and now all is consistent. I've opened [this issue](https://github.com/nautechsystems/nautilus_trader/issues/2857) concerning it, so feel free to comment there.

---

#### [2025-08-25 07:31:24] @faysou.

Backtests and request_aggregated_bars need ts_init to be correct to order data. So I don't understand what you want to do with ts_event.

---

#### [2025-08-25 07:33:42] @faysou.

Also ts_event can be the start or end of a bar, so ts_init is the variable that is used to aggregate bars for time bars.

---

#### [2025-08-25 07:35:42] @faysou.

Because ts_init is always at the end of a bar or shortly after, the time it's received in nautilus.

---

#### [2025-08-25 07:43:57] @ido3936

From my POV right now its just a technicality: internally and externally aggregated historical  bars match on ts_init, not on ts_event - as opposed the documentation (as I understood it): 

```
ts_event: UNIX timestamp (nanoseconds) representing when an event actually occurred.
ts_init: UNIX timestamp (nanoseconds) representing when Nautilus created the internal object representing that event.
```

What I really want to make sure of is that one can trade live in IB (which depends on internally aggregated bars)

---

#### [2025-08-25 13:20:16] @saruman9490

Took me a while as well to get used to the ts_init and ts_event concept, so I support <@1074995464316928071> . ts_init being the bar_close_timestamp is a hacky patch imo and breaks for bar requests. ts_event should be end of bar for left-open bars and bar open timestamp for right open, tho using the latter should be greatly penalized imo as its too easy to make a mistake.

---

#### [2025-08-25 13:27:16] @faysou.

so what is there to change then ?

---

#### [2025-08-25 13:27:19] @faysou.

it's not clear

---

#### [2025-08-25 13:32:26] @faysou.

I don't think it's a hacky patch, ts_init is what is used for backtests, so it should be at the end of a bar

---

#### [2025-08-25 13:34:54] @faysou.

or what you are saying is that ts_event should always be at the end ? the problem is that backtests are still using ts_init. so it's better to focus on it.

---

#### [2025-08-25 13:37:25] @faysou.

basically the most important variable is ts_init, not ts_event

---

#### [2025-08-25 18:49:57] @saruman9490

Backtest uses ts_init to sort the data events and then delivers them to the strategy one by one, which is the purpose of ts_init in general. Having ts_init set as close times might actually deliver them too quickly in high frequency scenarios.

In an ideal world ts_event and ts_init would be the same and there would be no problem.

Consider these 1m bars:

ts_init, ts_event, ..., close
00:01, 00:01, ..., 1
00:02, 00:02, ..., 2
00:02, 00:03, ..., 3
00:04, 00:04, ..., 4
00:06, 00:05, ..., 5

Here with the last row I simulate data latency issue. 

Suppose I wanted to do 5m aggregations based on ts_init aggregation close would be 4 and based on ts_event would be 5. Moreover an external 5m aggregation would also give 5 as the close. ts_init based aggregation would mask the data latency issue and, furthermore, might even use the delayed bar as an opening bar.

Obv, such lag is overkill for 1m bars, but for 1s might not be as infrequent as you'd think. Moreover, using ts_event as aggregation clock makes more sense in the case of requested bars where ts_init and ts_event are not related as all the bars get created at pretty much the same moment.

So back to original thought, I think that keeping ts_init fixed to the object initiation time and using ts_event for aggregation is safer and more consistent and that needs to be fixed in the aggregator instead of adapters.

---

#### [2025-08-25 18:51:51] @faysou.

Well you can see with <@757548402689966131> what he thinks and work on it if he accepts. It's easy to say we should, but then someone needs to do it.

---

#### [2025-08-25 18:53:22] @saruman9490

Yeah, I agree we need a 3rd opinion to break the tie 🙂 Wrt the code, I've shared the changes required public together with the issue description, we just need to convert it from Python to Rust in the worst case if we decide to go that way

---

#### [2025-08-25 18:54:41] @faysou.

The code to change is actually in cython first. Then the change to rust is more straightforward as the logic is done.

---

#### [2025-08-25 18:55:25] @saruman9490

You're right, forgot that the aggregator is cython indeed. That does make the implementation easier tho

---

#### [2025-08-27 10:12:08] @mk27mk

Update: I was able to replicate the approach used with `BinanceBar`.
Now I have `MyBar(Bar)` which, with a custom data wrangler, registration to arrow and to the`MessageBus` , works fine👌 .

It gets passed through the `on_bar` handler, gets added to `Cache._bars`, and can be persisted without problems (for now).

The next step could be reimplementing it in cython since things seems to have slowed down a bit.

---

#### [2025-08-28 12:09:49] @0xturdle

Hi, if I have quotes saved in the catalog, can I create aggregated bars by loading this data and then save those bars to the catalog? What is the most straightforward way to do this? Most of the examples seem to relate to loading & aggregating for running a strategy, or loading from raw format to be written to the catalog, not catalog->catalog

---

#### [2025-08-28 13:12:41] @faysou.

I would say record bars with streamingfeatherwriter then convert to catalog. I've sent the links of the corresponding code to use a few days ago, if you search for it on this discord server you will find.

---

#### [2025-08-28 13:17:28] @0xturdle

Thanks <@965894631017578537> Will have a look, which channel?

---

#### [2025-08-28 13:19:31] @faysou.

https://discord.com/channels/924497682343550976/924506736927334400/1409799879135465522

---

#### [2025-08-28 13:37:16] @0xturdle

Thanks!

---

#### [2025-08-28 20:22:28] @faysou.

You would then need to modify part of the folder names from internal to external as only external bars can be loaded from catalogs.

---

#### [2025-08-28 20:26:58] @faysou.

Internal in bar types is a signal to start an aggregator

---

#### [2025-08-28 20:27:16] @faysou.

Of quotes, trades or bars

---

#### [2025-08-29 06:21:20] @0xturdle

Thanks - tried this, having some issues opening the feather files that get generated for the bars, I think maybe the metadata isn't getting attached for bars vs some of the other data types  (_create_writer vs _create_instrument_writer)

---

#### [2025-08-29 06:25:16] @0xturdle

(or stop me if you think what I'm trying to do with the data is flawed in some way)

---

#### [2025-08-29 07:50:40] @mk27mk

Guys I noticed that

```python
from nautilus_trader.model.data import BarType

bar_type = BarType.from_str("6E.0.XCME-1-MINUTE-LAST-EXTERNAL")
type(bar_type.spec.aggregation)
```
out:
```
int
```

When the code in data.pyx states:

```python
    @property
    def aggregation(self) -> BarAggregation:
```

Maybe we should fix the type hinting?

---

#### [2025-08-29 08:35:59] @faysou.

BarAggregation is an enum, so it maps to an int, that's how enums work

---

#### [2025-08-29 10:36:27] @mk27mk

```python
bar_type = BarType.from_str("6E.0.XCME-1-MINUTE-LAST-EXTERNAL")
```
```python
# aggregation(self) -> BarAggregation: wrong
# im gonna get errors if I treat it like an Enum, as type hinting states.
integer = bar_type.spec.aggregation
print(type(integer))  # <class 'int'>
integer.name # AttributeError: 'int' object has no attribute 'name'
```
```python
# aggregation(self) -> int:
# ok, so I know I need to convert the int to an enum
aggregation = BarAggregation(bar_type.spec.aggregation)
print(type(aggregation))  # <flag 'BarAggregation'>
aggregation.name # "MINUTE"
```

---

#### [2025-08-30 06:46:26] @cjdsellers

Hi <@1260594339407597569> 
Enums defined through Cython are essentially just named integer constants backed by C int values. Unfortunately because of this there isn't actually much type safety and they don't play so well with the Python type system

---

#### [2025-08-30 11:31:17] @mk27mk

Hi <@757548402689966131>, I understand. 
With the Rust port in mind, it’s just as well to not care too much about it, since cython is going to be obliterated 🔫

---

#### [2025-09-01 13:06:53] @veracious69_77345

Question regarding indicators, I guess the `handle_bar` gets called on every incremental update of a candlestick/bar? So, do I understand the SimpleMovingAverage indicator correctly if the period is not the amount of bars it is calculated on, but simply the average of the latest x (period) values added to the input deque?

For example, lets say a strategy establishes a connection to the binance websocket for bar-updated. A 20 period moving average on 1min bars would expect to give the average closing value of the last 20 1min bars, but the handle_bar will get updated with every new update received from the websocket, so it will just be an average of the last 20 updates from the data-source?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924504069433876550/1412061152120279182/image.png?ex=68fad12d&is=68f97fad&hm=5cfd7f42174acf86ca9fd3582c90ddccca8fb1b4eb3b43b000f394cc81e11799&)

---

#### [2025-09-02 16:25:10] @faysou.

there's no incremental update of candlesticks, only full candlesticks flow through the system

---

#### [2025-09-04 15:17:48] @ido3936

I had the same experience while trying to persist bars <@428920475427799061> .
I tried to debug it but could not get it off the ground. I think that bars should be using the `_create_instrument_writer` (with schema metadata), but instead are using `_create_writer` (which does not save the metadata).
In any case eventually I ended up using my own mechanism for persisting bars

---

#### [2025-09-04 16:06:06] @baerenstein.

Hey! I have been working out a way to store my data efficiently and have faced a few bottlenecks, maybe someone can help me with general conventions in this regards.
I am fetching quote, orderbook, and trade data for underlying spot and options data and am writing everything to the NT catalog on S3. Because of the option contracts, usually a few hundred, the data writing becomes quite slow.  I am considering now to first store all the data on a local instance of the data catalog, and then with a lazy helper push all data from the catalog to s3 so that i can better handle batch operations. another thing is query performance- does it make sense to have a hot storage such as clickhouse or questdb to handle these large option datasets (and also for dashboards or similar) or ist the NT catalog equally fast?

Basically the goal is to have a stable data collector that i can run without too much headaches on a server so that i can backtest and research ideas. All this data management is quite new to me, so any help or guidance would be warmly appreciated 🙂

---

#### [2025-09-08 14:40:00] @0xturdle

Hi - just wanted to check for adding Tardis data to the catalog, is it generally faster to download the zipped CSV files & load them or use run_tardis_machine_replay() with the tardis server

---

#### [2025-09-09 07:36:32] @cjdsellers

Hi <@428920475427799061>
If you're running repeated backtests then using either of those methods to write data to a catalog in Nautilus Parquet format would be fastest. The `run_tardis_machine_replay()` is doing this and will be faster than loading from CSVs on every run https://nautilustrader.io/docs/nightly/integrations/tardis#running-tardis-machine-historical-replays

---

#### [2025-09-10 01:18:34] @0xturdle

Thanks <@757548402689966131> 🙏 not planning this for repeated runs, just to initially bulk download some data into the catalog

---

#### [2025-09-10 16:39:59] @bartoelli

From what sources do you get data for backtesting? I'm looking for OHLC 1d from 2000 until now for stocks.

---

#### [2025-09-10 16:49:10] @apercu_16113

For this, I like [Tiingo](https://www.tiingo.com/products/end-of-day-stock-price-data). But haven't integrated it with NT yet (just starting out here)

**Links:**
- Stock Market Tools | Tiingo

---

#### [2025-09-10 16:51:53] @bartoelli

$250 a month 😮 I am looking data for backtesting, so maybe do you know something cheaper 😅

---

#### [2025-09-10 16:55:07] @apercu_16113

Not sure what you need... I'm on the Individual Power plan for $7 (as I subscribed some years ago) 🙂

---

#### [2025-09-10 20:39:15] @bartoelli

Lucky you, now basic plan is $30 per month for personal use

---

#### [2025-09-11 21:01:58] @yunshen8_47168

Hi， I'm trying to use a custom data catalog in backtests with BacktestDataConfig,  but got this error.

RuntimeError(unsupported `data_cls` for Rust parquet, was ReturnPredictions)

Does this mean custom data is not supposed to be used this way?

---

#### [2025-09-12 02:42:23] @cjdsellers

Hi <@1261147783264604192> 
Correct, custom data is not yet supported by the Rust-based DataFusion *streaming* backend. If you remove the `chunk_size` param then it should work as a "one-shot load" backtest run. Otherwise, it's possible to write your own custom streaming using the docstrings as a guide - although this is more work

---

#### [2025-09-12 13:02:09] @yunshen8_47168

I see, thanks!

---

#### [2025-09-26 19:05:11] @baerenstein.

Hi guys, I have been trying to get options trade ticks but it just doesn't seem to find any trades. has anyone tried this before? im using bybit now, will try OKX next.

---

#### [2025-09-26 20:44:38] @baerenstein.

Brief update on this issue:
There exists a connection for each options trade websocket, but it is not streaming anything, its empty. Now the rest api works and is able to retrieve options trade ticks. I will write to their support and see where things go now. Anyhow, do you know whether options trade tick data works with binance or okx? A brief reply would be great <@965894631017578537>

---

#### [2025-09-26 22:48:48] @faysou.

I don't work with binance or okx, I don't know.

---

#### [2025-09-27 06:56:23] @baerenstein.

do you know of anyone else who has been working with crypto options to whom i could reach out to?

---

#### [2025-09-27 08:13:47] @faysou.

No

---

#### [2025-09-30 11:23:17] @drose1

Seems like NautilusTrader cannot backtest with any cloud storage (gcs/aws/azure) currently. 
Each provider has different parameter names in Python (fsspec) vs Rust (object_store).

Not sure if there's a workaround or we need to implement `Protocol-Specific Normalization` .. I have some ideas for this.. but I heard we are also moving the catalog entirely into rust.

---

#### [2025-09-30 14:28:10] @faysou.

You can add another parameter to the python catalog to optionally use a different config for data not yet covered in rust.

---

#### [2025-10-02 08:08:49] @e23099

Can a catalog be shared between different platforms?

For example, inside a ubuntu 22.04 wsl2, I write TradeBars to a local ParquetDataCatalog on my host machine.  And in my windows host machine, I use the same version of nautilus_trader (1.220.0) to query from that ParquetDataCatalog, and I get a `'tokio-runtime-worker' panicked at crates\serialization\src\arrow\mod.rs:84:46`. 

Is catalog not supposed to be used like this?

---

#### [2025-10-07 15:32:14] @mark.el89

Hi guys 
I’m in research phase of using NT and I think my question is more general to the trading of CFDs and such:

im coming from a freqtrade /Algo and CCXT for crypto trading and got into shock to find that the data is actually not free or not available like as easy as ccxt would provide for CFDs and gold…

Till now (pre installation/testing phase) and I like what I am reading, FT’s main 2 issues is no support for out of ccxt context and the RL env is very basic and 95% different than actual trading env which is not as good as needed and NT seems to have this sorted out ❤️

my question is:
is my understanding correct that data need to be purchased or am I missing something?

---

#### [2025-10-10 07:27:31] @cjdsellers

Hi <@447422131891077120> this might not work because the precision-mode is different by default between Windows and Linux:
https://nautilustrader.io/docs/nightly/getting_started/installation#precision-mode I hope that helps!

---

#### [2025-10-10 07:43:30] @cjdsellers

Hi <@1362988845766934679> 
Welcome and thanks for reaching out! The short answer is the project focuses on the core platform, so it's expected you would source your own data https://nautilustrader.io/docs/nightly/concepts/data

---

#### [2025-10-12 12:28:22] @mark.el89

Thanks <@757548402689966131> for the answer 
I presumed that was the case before, but with Binance and Bybit available and Bybit having XAUT, dosnt it make sense to utilize something like ccxt to download the data automatically? And keep externals as a separate way maybe 🤔

---

#### [2025-10-12 20:35:41] @mheise

Hi Everyone!

I am trying to use bars from a catalog in a backtest strategy in nautilus trader 1.219.0:
- when I add a catalog to BacktestEngineConfig via DataCatalogConfig and use request_bars() directly in the Strategy the RequestBars event returns "Received <Bar[0]> data for unknown bar type"
- everything works fine though when I call the following after the identical code abobe but before the engine.run()
                engine.add_instrument(engine.kernel.catalogs['historical_data'].instruments()[0])
                engine.add_data(engine.kernel.catalogs['historical_data'].bars(instrument_ids=[str(instrument.id)]))
   the strategy is populated correctly

Does the BacktestEngine not automatically populate data from the catalog when configuring in with DataCatalogConfig in BacktestEngineConfig or am I missing something important?

Thank you in advance!

---

#### [2025-10-12 21:15:07] @one_lpb



---

#### [2025-10-12 21:15:34] @one_lpb

<@718089270304440371> maybe it will help, but better use high level api if no real need of low level api

---

#### [2025-10-12 21:27:35] @mheise

Thanks <@391133967056896001>  for the help.
Just to clarify once more. I have the correct bars in the catalog which I request in the strategy. The only thing that I dont understand is why I have to re-add the bars and instruments when it has already been been done via DataCatalogConfig. The confirmation that the catalog is registered in the engine is that I re-add the bars from the catalog that I retrieve from the engine as shown in my code above. Really strange…
Any further help would be greatly appreciated!

---

#### [2025-10-13 02:52:46] @megafil_

I have a similar issue but I am not even using aggregated bars, just raw external bars which work fine to create on_bar events but fail with request_bars
`2021-01-01...Z [INFO] BACKTEST-Test.Trading: [REQ]--> RequestBars(bar_type=BTCUSDT-PERP.BINANCE-1-DAY-LAST-EXTERNAL, start=1970-01-01 00:00:00+00:00, end=2021-01-01 00:00:00+00:00, limit=0, client_id=None, venue=BINANCE, data_type=Bar, params={'update_catalog': False})
2021-01-01T00:00:00.000000000Z [DEBUG] BACKTEST-Test.Cache: Received <Bar[]> data with no ticks

2021-01-01...Z [DEBUG] BACKTEST-Test.OrderMatchingEngine(BINANCE): Processing Bar(BTCUSDT-PERP.BINANCE-1-DAY-LAST-EXTERNAL,28948.19,29668.86,28627.12,29337.16,6099858325.420,1609459200000000000)`

---

#### [2025-10-13 09:03:53] @one_lpb

Maybe someone correct me if I’m wrong because I’m new to NT but I think that if you go through low level API you HAVE TO add data manually, it’s not autoloading with catalog

---

#### [2025-10-13 09:07:19] @cjdsellers

Hi <@391133967056896001> 
It's possible to register a data catalog with a `BacktestEngine` (this is what `BacktestNode` does internally), and it will then be used to serve requests, aggregations etc. This means everything you can achieve with a `BacktestNode` / high-level API you can achieve with the low-level `BacktestEngine`, and replicates live trading flows. It's just set up in a different way, the high-level API can also leverage that data fusion streaming backend which typically ends up being faster than using wranglers to load from disk every time. https://nautilustrader.io/docs/nightly/concepts/backtesting#choosing-an-api-level

---

#### [2025-10-13 09:08:36] @cjdsellers

There are some additional functionalities possible through high-level only I think which are quite new from **faysou**, such as on-the-fly data downloading etc

---

#### [2025-10-13 10:42:07] @faysou.

A backtestnode is basically taking care of what someone would have to set up manually with the low level API. 99% of people wouldn't need more than this, and if they did they can look at the backtestnode code to see what's done exactly.

---

#### [2025-10-13 11:00:53] @mk27mk

Hi everyone,

I'm trying to persist internally aggregated bars through `ParquetDataCatalog.convert_stream_to_data` but I'm getting this error:

```bash
Traceback (most recent call last):
  File "~/Documents/code/rev/scripts/actors_backtest.py", line 157, in <module>
    engine, results = run_backtest(save=True)
                      ~~~~~~~~~~~~^^^^^^^^^^^
  File "~/Documents/code/rev/scripts/actors_backtest.py", line 150, in run_backtest
    catalog.convert_stream_to_data(results[0].instance_id, Bar)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/Documents/code/rev/.venv/lib/python3.13/site-packages/nautilus_trader/persistence/catalog/parquet.py", line 2264, in convert_stream_to_data
    custom_data_list = self._handle_table_nautilus(feather_table, data_cls)
  File "~/Documents/code/rev/.venv/lib/python3.13/site-packages/nautilus_trader/persistence/catalog/parquet.py", line 1898, in _handle_table_nautilus
    data = ArrowSerializer.deserialize(data_cls=data_cls, batch=table)
  File "~/Documents/code/rev/.venv/lib/python3.13/site-packages/nautilus_trader/serialization/arrow/serializer.py", line 285, in deserialize
    return ArrowSerializer._deserialize_rust(data_cls=data_cls, table=batch)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "~/Documents/code/rev/.venv/lib/python3.13/site-packages/nautilus_trader/serialization/arrow/serializer.py", line 310, in _deserialize_rust
    wrangler = Wrangler.from_schema(table.schema)
  File "~/Documents/code/rev/.venv/lib/python3.13/site-packages/nautilus_trader/persistence/wranglers_v2.py", line 57, in from_schema
    **{k.decode(): decode(k, v) for k, v in metadata.items() if k not in cls.IGNORE_KEYS},
                                            ^^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'items'
```

---

#### [2025-10-13 11:03:26] @mk27mk

This is the content of `feather_files` inside `convert_stream_to_data` (I debugged it):
```
0 =
PosixPath('~/Documents/nautilus/backtest/46528cde-b80d-4431-a853-ee5e81c1f938/bar_0.feather')
1 =
PosixPath('~/Documents/nautilus/backtest/46528cde-b80d-4431-a853-ee5e81c1f938/bar_6e.0.xcme-1-day-last-internal@1-minute-external_1582588800000000000.feather')
2 =
PosixPath('~/Documents/nautilus/backtest/46528cde-b80d-4431-a853-ee5e81c1f938/bar_6e.0.xcme-1-day-last-internal_1582758000000000000.feather')
3 =
PosixPath('~/Documents/nautilus/backtest/46528cde-b80d-4431-a853-ee5e81c1f938/bar_6e.0.xcme-1-minute-last-external_1582588800000000000.feather')
4 =
PosixPath('~/Documents/nautilus/backtest/46528cde-b80d-4431-a853-ee5e81c1f938/bar_6e.0.xcme-4-hour-last-internal@1-minute-external_1582588800000000000.feather')
5 =
PosixPath('~/Documents/nautilus/backtest/46528cde-b80d-4431-a853-ee5e81c1f938/bar_6e.0.xcme-4-hour-last-internal_1582614000000000000.feather')
```

---

#### [2025-10-13 11:04:44] @mk27mk

The error is triggered while `ParquetDataCatalog.convert_stream_to_data` is iterating on `bar_0.feather` which apparently hasn't any metadata

---

#### [2025-10-13 15:13:10] @mafiosi72

Hi <@718089270304440371> ,

I encountered a very similar issue and spent several days trying to resolve it. Ultimately, the only solution that worked for me was switching from the low-level Backtesting API to the high-level API and feeding the data directly into the strategy.
I'm not entirely sure why the low-level API behaved that way—perhaps there's something unusual about it, or I may have been using it incorrectly. In any case, the high-level API was the only approach that delivered consistent results.

also refer to my other post here https://discord.com/channels/924497682343550976/924498804835745853/1425500933495853298 .

Hope that helps.

---

#### [2025-10-13 17:06:51] @ido3936

Hey <@1260594339407597569> , I had the same problem. See https://discord.com/channels/924497682343550976/924504069433876550/1413181261739982898

I ended up ditching the NT persistence mechanism and writing my own

---

#### [2025-10-13 17:37:36] @faysou.

Something that would help is to try to debug and fix stuff instead of ditching stuff. The library is open source so it can be modified. Note that I'm just a contributor, even though a big one, I fix and improve the library to help myself first, but if I help myself I help others as well as they will need the same things at some point and I make my contributions public with PRs.

---

#### [2025-10-13 17:39:11] @faysou.

You can also post an issue on GitHub with an MRE (mininum reproducible example) and not just an error message which greatly increases the chance that something will get fixed if you don't find a solution.

---

#### [2025-10-13 17:40:25] @faysou.

Also note that AI agents can solve a huge amount of things if you show them an example that doesn't work.

---

#### [2025-10-13 18:05:09] @faysou.

it's actually impressive because one year ago there was no AI agent and the AI chats like cody could only vaguely answer questions about the code with a lot of hallucinations.

---

#### [2025-10-13 18:05:41] @faysou.

so let's see where will be in one year, although I doubt the jump will be this big, but who knows

---

#### [2025-10-13 19:31:11] @codepumper

Hi everyone!

My strategy would be simple i buy at open price, and sell same days close price. Can someone confirm this is not possible or give me a hint how to workaround?

---

#### [2025-10-13 20:05:53] @faysou.

I've managed to do it, will do a PR soon

---

#### [2025-10-14 14:06:32] @ido3936

Thanks <@965894631017578537>! . Note however that there is an economy of sorts with OS contributions, and especially with Nautilus. There is a huge up front 'payment' before you manage to do anything, and then still for a long time you will be 'paying' dearly for debugging it . 

You managed to fix this issue in 3 hours it seems  - I've spent twice as much time on this and only managed to get an idea of how the code works and where it breaks

Apart from the scope and complexity of the code, there is also the lacking documentation (considering scope/complexity) - documentation helps humans and AI alike, and the re is also the Python/Cython/Rust combination.

In short - we all do what we can... and still its amazing that you contribute so much of your free time to this project. Fantastic work!

---

#### [2025-10-14 14:24:02] @faysou.

I agree with you, and thanks for reporting bugs. I've spent thousands of hours on nautilus in about a year and a half (when I like something I do it all the time), so yes I can solve things faster, using AI as well to accelerate things. Still working on it, will update my PR, this will evolve the streaming solution so it's better.

---

#### [2025-10-14 14:29:25] @faysou.

something nice with AI is that it allows to do a first version of a solution, it's often not the final one but at least it orients for where to look at (OODA loop)

---

#### [2025-10-14 14:30:55] @faysou.

the key to work fast with AI is to ask it to write debug logs in the code, then it can reason on something, else it can go into stupid mode by just making assumptions and not making progress

---

#### [2025-10-14 14:32:00] @faysou.

also make sure to make a commit before asking AI to write something, you don't want that some good uncommited code gets wasted by the AI (which it can do, that's why commits are there)

---

#### [2025-10-14 14:34:03] @faysou.

one key advantage of open source is that more users means more bugs reported and fixed

---

#### [2025-10-14 18:10:00] @faysou.

I think I'm done with the PR

---

#### [2025-10-14 19:04:44] @ido3936

I'll give it a shot on the next develop build

---

#### [2025-10-15 21:40:56] @mk27mk

<@965894631017578537> You did an amazing job with the PR!

---

#### [2025-10-15 21:42:32] @faysou.

Thanks

---

#### [2025-10-15 21:42:58] @mk27mk

Do you ask it in every prompt or do you use an AGENTS.md/rules/prompt file?

---

#### [2025-10-15 21:45:21] @faysou.

I have a rule on the fact that it should investigate using debug logs and recompile. Also to not create new test files if I want to test a specific file. Basically the more you have an idea of what to do the faster it does it. I also tell in the prompt to add debug logs when it's unclear where there's a problem

---

#### [2025-10-15 21:47:04] @mk27mk

Also, something that I tried and seemed to work really well is making the Agent use TDD.

---

#### [2025-10-15 21:47:52] @mk27mk

Do you think using augment code makes a big difference?

---

#### [2025-10-15 21:48:18] @faysou.

I don't know as I've just used it

---

#### [2025-10-15 21:48:33] @faysou.

Will switch to copilot maybe, or codex

---

#### [2025-10-15 21:48:44] @faysou.

Copilot is cheap

---

#### [2025-10-15 21:49:02] @faysou.

Will test other things when I move away from augment

---

#### [2025-10-15 21:50:37] @faysou.

Things change all the time, Gemini 3 is arriving soon as well

---

#### [2025-10-15 21:51:32] @mk27mk

I recommend you trying copilot! The seamless integration with vsc is what it makes it great

---

#### [2025-10-16 12:28:14] @ido3936

Persisting bars to feather works for me too. Thanks <@965894631017578537> 🙏

---

#### [2025-10-16 13:25:25] @faysou.

Cool, yes it was a feature often asked for, including for recording live data. It seems the feature is good now, I've also added something that allows to filter what is converted into parquet. Also bars have folders as well, and even custom data can be split by instrument id, so that's some good evolution.

---

#### [2025-10-16 13:25:58] @faysou.

The nice thing about these things is that the logic is there, it will remain when ported to rust as well.

---

#### [2025-10-16 13:26:33] @faysou.

And migrating from python to rust is not as hard as it used to be.

---

#### [2025-10-16 13:26:58] @faysou.

(with some good architecture of course, that <@757548402689966131> works on)

---

#### [2025-10-16 13:50:13] @ido3936

I think that I may have been too hasty. As I try to convert to parquet I get errors reading the feather files, so I try to read them into pandas - and even that fails (with `ArrowInvalid: Not a Feather V1 or Arrow IPC file`). I've tries this on Equity and on Bar feather files

---

#### [2025-10-16 13:51:04] @ido3936

(not hasty in thanking - just in assuming that it works perfectly...)

---

#### [2025-10-16 14:15:50] @faysou.

Send some code to reproduce it and I'll have a look. Too often people just send the error, I can't do anything with that.

---

#### [2025-10-16 14:57:54] @ido3936

the zip contains a single instrument's catalog ( equity and bar data), and the python file matches the instrument
you might still need to play with the `CATALOG_PATH` to point it in the right direction
the python script just runs a base strategy with streaming activated
then it tries to load the resultant feather files using pandas' `read_feather` and returns errors

**Attachments:**
- [single_ticker.zip](https://cdn.discordapp.com/attachments/924504069433876550/1428396544775684106/single_ticker.zip?ex=68faeb32&is=68f999b2&hm=9c2fdab9b467716e50d58db4c0b3ebae3da1aed23220da3ebe4dc15026dc1b4c&)

---

#### [2025-10-16 14:58:51] @ido3936



**Attachments:**
- [minimal_backtest_example.py](https://cdn.discordapp.com/attachments/924504069433876550/1428396780743295096/minimal_backtest_example.py?ex=68faeb6a&is=68f999ea&hm=bf40841f223054774611da519258a0ae2275a423693bc1f52133ec98f841aaad&)

---

#### [2025-10-16 15:02:49] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/persistence/catalog/parquet.py#L2209

---

#### [2025-10-16 15:03:41] @faysou.

I don't think the written feather files are meant to be read with pandas

---

#### [2025-10-16 15:32:01] @ido3936

I see, thanks. 
Replacing `pd.read_feather` with `convert_stream_to_data` works! - at least for Bar, although not for Equity,  which is a good enough start
I'll work with this for the time being, to figure out why even converting Bars doesn't work on my strategy

---

#### [2025-10-16 16:15:51] @ido3936

Playing around some more with the simple example, the catalog now contains two bar types from the same instrument.
Feather files are created for each, but `convert_stream_to_data` only manages to create a parquet file for one of them.

**Attachments:**
- [minimal_backtest_example.py](https://cdn.discordapp.com/attachments/924504069433876550/1428416158729768970/minimal_backtest_example.py?ex=68fa54b6&is=68f90336&hm=60a54798b88e08bd8a3b382d54381738a8cd91cdd873efe2983470dd040515af&)
- [single_ticker_2.zip](https://cdn.discordapp.com/attachments/924504069433876550/1428416159048532028/single_ticker_2.zip?ex=68fa54b7&is=68f90337&hm=f87097f7aea70a78b062d61867f3cd36aad10263236b6ca2ae5baae72d920f61&)

---

#### [2025-10-16 16:17:10] @faysou.

I'm not going to be able to debug any bug you have, you will need to try more

---

#### [2025-10-16 16:52:55] @ido3936

I think that it is a bug in the NT's persistence mechanism, not in my code, but that's OK
It will get fixed at some point I guess

---

#### [2025-10-21 13:04:35] @one_lpb

Hello!

I noticed that, for example, Polygon.io provides SIP historical quote data (aggregated from Nasdaq, dark pools, etc.), while Databento delivers historical data based solely on Nasdaq ITCH quotes. I compared both datasets for the same days on Polygon and Databento, and the prices can differ by almost 0.01% (for TESLA).

When working with low time frames and tight TP/SL levels, that difference can have a significant impact — especially if the broker executes orders on Nasdaq ITCH while we’re using SIP data.

What do you think about that?

---
