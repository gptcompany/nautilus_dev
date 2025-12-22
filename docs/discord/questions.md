# NautilusTrader - #questions

**Period:** Last 90 days
**Messages:** 336
**Last updated:** 2025-12-22 18:01:49

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
- [grafana.png](https://cdn.discordapp.com/attachments/924506736927334400/1424238899936624650/grafana.png?ex=694ab716&is=69496596&hm=e543f45903e91108553f1620a61b279d9ecfa57b2bda67a91d353110803f80f4&)

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
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1425420516264640542/image.png?ex=694a664e&is=694914ce&hm=fc799f3ba51f176b822f443304e7931153fe042a056061356a0f4f7a2d81eff3&)

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
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1427422004180418620/image.png?ex=694a6e16&is=69491c96&hm=fefc009b50d6754500fbeca9a90272656f96955aecdcf98e5b2c9ac5fd3557ee&)

---

#### [2025-10-14 03:31:55] @rustace

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
- [SCR-20240423-rpnc_.png](https://cdn.discordapp.com/attachments/924506736927334400/1428425670047957143/SCR-20240423-rpnc_.png?ex=694ac912&is=69497792&hm=b4eaece737289e35ed7dac2b810082d938798c98b6e130233c8ad6ff52a37a97&)

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
- [Screenshot_20251020_172951.png](https://cdn.discordapp.com/attachments/924506736927334400/1429748820719304714/Screenshot_20251020_172951.png?ex=694a535a&is=694901da&hm=7ae0654225ed181a1b71bde5f54454e482312eb479cd36bde2ae39ae76fed3c2&)

---

#### [2025-10-20 08:31:52] @jst0478

The order book is badly corrupted.. ask prices below bids..

---

#### [2025-10-20 08:40:46] @deleted_user_3434563

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

#### [2025-10-21 15:31:19] @rustace

is this built with tauri please?

---

#### [2025-10-21 15:32:29] @gz00000

The one in the screenshot was built using Textual.

---

#### [2025-10-21 15:33:36] @rustace

have you built a tauri proj

---

#### [2025-10-21 15:36:52] @gz00000

As I mentioned earlier, I once built a demo similar to the one in the screenshot using `tauri`, but now I’m leaning toward using something like `egui` or `iced`. Based on recent research, `egui` might be the better fit. However, both the old `Cryptowatch` and the current `Kraken Desktop` were built with `iced`.

---

#### [2025-10-21 15:37:50] @rustace

have you open the textual code 😄

---

#### [2025-10-21 15:38:24] @rustace

can it be used for backtest

---

#### [2025-10-21 15:40:53] @gz00000

No, I eventually stopped using it myself — the FPS couldn’t keep up under HFT conditions. It’s not suitable for backtesting since it only connects to real-time data.

---

#### [2025-10-21 15:44:33] @deleted_user_3434563

Look into Dioxus, it might be a decent alternative based on specific requirements. Or you could go with Svelte + Tauri for desktop app. Or simply nextjs and have it based on the web.

---

#### [2025-10-21 15:47:18] @gz00000

Thanks for the information — I’ll do some research and take a closer look.

---

#### [2025-10-21 15:48:38] @gz00000

I used to work with `Svelte + Tauri + Tailwind`.

---

#### [2025-10-21 15:49:28] @deleted_user_3434563

Its a great setup aswell

---

#### [2025-10-21 15:49:53] @deleted_user_3434563

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

#### [2025-10-21 17:51:29] @deleted_user_3434563

Yes they do for now. Dioxus working on a replacement called Blitz

---

#### [2025-10-21 17:52:00] @deleted_user_3434563

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

#### [2025-10-23 20:39:59] @sinaatra

hey, i created an adapter following this doc https://nautilustrader.io/docs/latest/developer_guide/adapters#marketdataclient
What do I do with my MarketDataClient?
I was expecting to pass it in a `TradingNode` but I don't see how

**Links:**
- Adapters | NautilusTrader Documentation

---

#### [2025-10-24 02:08:20] @kvg1

Is it possible to cache opened positions without redis or other external db tool?

---

#### [2025-10-24 03:05:19] @fudgemin

you get sorted? you can do it a few ways, but i used data client factory config among other things. Add to the node after its built

---

#### [2025-10-24 03:06:58] @fudgemin

app uses in memory as default. i believe it stores all positions. Redis or postgres is for state managed. If you want to persist if the node is disposed

---

#### [2025-10-24 03:29:10] @jst0478

Yeah maybe check this?
https://nautilustrader.io/docs/latest/concepts/cache#positions
About how to get positions from the cache

---

#### [2025-10-24 03:30:11] @jst0478

They are already cached for you by the engine

---

#### [2025-10-26 08:02:59] @mk1ngzz

use llms to explain the architecture and components

---

#### [2025-10-26 13:05:55] @bother_47172

I have one question  about thread structure。the code "  thread_local! {
    static MESSAGE_BUS: OnceCell<Rc<RefCell<MessageBus>>> = const { OnceCell::new() };
}" will create thread local message bus， tokio runtime can use multiple thread param。How to ensure the temporal order of tasks across multiple "message buses"?

---

#### [2025-10-26 13:17:53] @bother_47172

Hi <@757548402689966131>  I read in architecture.md that single-threaded efficiency is better, but this issue was mentioned. Could you please explain it? Thank you.

---

#### [2025-10-28 02:24:00] @ml087870

Hi,
In examples/indicators/ema_python.py, there’s a comment recommending implementing indicators in Cython (as in the indicators subpackage). If my indicator isn’t for high-frequency trading and I only use 1–5 minute timeframes, is Cython still necessary?

---

#### [2025-10-28 03:24:35] @trueorfalse

it's a performance thing rather then requirement.

---

#### [2025-10-28 03:41:39] @yfclark

There's no need. When your strategy makes money, you'll naturally be motivated to come back and optimize it. If it doesn't make money, there's naturally no need to change it.

---

#### [2025-10-28 09:01:53] @jst0478

Is there some way to interact with a running strategy from outside the running NT instance? For example, if I'm running a strategy live and want to tell my strategy to do something manually (like force closing a position, or stop immediately, etc.).

Would I need to send a message to it on the message bus from a different program, and make sure the strategy can detect/handle that message? If this has been discussed before please point me in the right direction. I've been reading over https://nautilustrader.io/docs/latest/concepts/message_bus and it talks about publishing messages, but it's not clicking for me how to send a message to the strategy from the outside

---

#### [2025-10-28 12:49:05] @fudgemin

you can use a controller, however that is mostly for adding and removing entire strategies, actors etc into a running node. More like a bird eye lifecycle manager. 
What you speak of, is likley best suited for custom SignalData. Thats a one arg, single value data point, that can be subbed to in any strategy. Send the messages via a dedicated actor, and publish to all strategies. Use a simple check, on_data, if Signal, then close all positions etc. Could set up a simple CLI to your actor, so you could potentailly send custom signals on demand

---

#### [2025-10-28 12:57:07] @fudgemin

anyone interested in video/examples, on using Nt with grafana? loki itegration for logs, redis monitor on the cache, etc

---

#### [2025-10-28 13:31:46] @trueorfalse

oh this was good information and one of my requirements.. 

as I understand NT forces us to handle things like "event sourcing"  if I'm wrong please correct me.

---

#### [2025-10-28 14:14:30] @ido3936

I have been running a setup with an http server that has access to the NT message bus. I then use a client to send directives

---

#### [2025-10-28 23:11:56] @mistermm23

Hey guys! I was wondering if someone could answer this question, relating to nautilus performance: How exactly does python code get linked to the underlying rust core? More specifically,  while the core functionality does run on Rust, doesn't a python function need to be executed with the interpreter on, say, every event trigger of a strategy?

---

#### [2025-10-29 10:07:39] @bother_47172

Who can resolve my confusion? 🥹  I have verified the previous content related to actor threads and reviewed the code. Logically, I still think that in a multi-threaded environment,  thread_local will cause content switching when tokio executing tasks, then current thread can not read the pre threadLocal variables.

---

#### [2025-10-30 04:16:25] @bother_47172

I think it's like this: in rust code, Tokio must runs in  just a single thread. However, when some complex scenarios require parallelism, how should solve?

---

#### [2025-10-30 08:01:36] @kvg1

Are there plans to implement cache with sqlite instead of postgresql?

---

#### [2025-10-30 11:21:02] @mohamadshoumar

Is there a way to set the ticks in slippage for market order, the default is 1 tick which is a really small number, i want to add a param to set the number of ticks.

The way Nautilous Trader slippage model works for OHLC data is the following:

probability slippage defines the chance of slippage on market orders. At 0.0, fills are perfect; at 1.0, you always experience adverse slippage by 1 tick
After I implemented it, the difference in execution price for Long Market oder  with prob_slippage =0 is "avg_px": 118681.64 while with prob_slippage=1  "avg_px": 118681.65, so 1 tick diff

---

#### [2025-10-30 12:19:37] @faysou.

Look at FillModel

---

#### [2025-10-30 12:24:43] @faysou.

You can use custom FillModels

---

#### [2025-10-30 12:25:30] @faysou.

Like here for example

---

#### [2025-10-30 12:26:20] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/backtest/models/fill.pyx

---

#### [2025-10-30 12:26:56] @faysou.

It basically allows to create OrderBooks as you wish

---

#### [2025-10-30 12:27:05] @faysou.

Based on market data

---

#### [2025-10-30 12:31:49] @faysou.

https://github.com/nautechsystems/nautilus_trader/issues/2194

**Links:**
- Enhanced order-fill simulation in backtesting · Issue #2194 · nau...

---

#### [2025-10-30 12:32:10] @faysou.

More details here, someone did some nice specs that I later implemented

---

#### [2025-10-31 16:39:46] @faintent

isn’t sqlite much slower? why prefer that over psql

---

#### [2025-10-31 16:40:17] @faintent

or like it’s only single threaded or something like that idrk

---

#### [2025-10-31 19:57:48] @sinaatra

Thanks for your answer, unfortunatly not.
In fact I found `self.node.add_data_client_factory("Name", MyDataClientFactory)`
But I feel like this doesn't apply to `MarketDataClient`. I think I am getting it wrong but I can't figure out why

---

#### [2025-10-31 20:18:43] @sinaatra

Ok I managed to add the factory (I was using the same name which (in my exec) caused a silent crash. Now I need to succeed instanciating those clients

---

#### [2025-10-31 21:07:09] @sinaatra

gud

---

#### [2025-10-31 22:14:53] @cjdsellers

Hi <@420311971389374464> 
Thanks for sharing your experiences, if you happen to have any of the error outputs then we might be able to improve the exception/log messages

---

#### [2025-11-02 23:38:41] @yegu88

Hi all. I'm new to the Discord group. I'm evaluating NT, which seems to meet my needs. However, given my limited reading so far, am I correct to assume that NT is more of a framework than a backend platform (since I don't see any UI)? As such, should I assume that I should be creating workflows using Airflow etc outside of NT? For example, I have multiple trading strategies running at different intervals. Should I schedule these in my workflow system? I see that NT also has a Clock construct. If that's the case, should I deal with trade execution through a broker like Interactive Brokers that only allows one client connecting to their gateway software? Any advice would be greatly appreciated

---

#### [2025-11-03 01:46:59] @cjdsellers

Hi <@940399143774486568> 
Welcome, your assessment is basically correct. Those workflows you mention are out of scope (per the [ROADMAP](https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md#open-source-scope)) and so would need to be implemented to meet your individual requirements - various ways of approaching that as well, but what you mention sounds good. On IB that may not be a limitation, but would require further investigation.

On frontend / UI this is clearly needed and is something currently being worked on right now, no time frame for availability as yet though. There are some basic backtest tearsheets that just landed (on `develop` branch) and already being improved upon <#1432271716712714331> I hope that helps!

---

#### [2025-11-03 05:56:44] @yegu88

Do you have have sample code on how to create a live trading strategy that runs on a regular interval?

---

#### [2025-11-03 05:57:05] @yegu88

How do you handle market sessions?

---

#### [2025-11-03 05:57:22] @yegu88

<@757548402689966131>

---

#### [2025-11-03 06:36:52] @yegu88

I'm also trying to figure out how to map our ML code to NT. In a typical setup, I use a Pandas/Polars dataframe to store historical and live data (OLHC EOD prices, for example) for many hundred/thousand instruments (stocks) in rows (indexed by symbol + date), mix in other data (sentiment, etc.), add features into new columns and feed the dataframe into a ML model that ranks these stocks say for predicted forward returns. How would I do this in NT? Any examples I can look at?

---

#### [2025-11-03 19:13:56] @yegu88

In general, if I'm already using a data service like DataBento, do i still need to use the Data catalog? I get that it improves performance. It also adds quite a lot of complexity for my use cases. Again I need to process thousands of instruments, with both daily and intraday bar data of varying historical periods. If I use the Data catalog, how should i package the daily bars efficiently? Are EOD bar and intraday bars go into the same Parquet file? They're already aggregated by the data provider so I don't need NT to do that again.

---

#### [2025-11-03 20:38:14] @fudgemin

a good application will solve the needs and problems of many users and use cases. NT just does that. Its has a solution for nearly everything you describe. In fact, these are fairly mundane tasks for NT. 

I would suggest building out a playground of your own examples, to see how you may design your own system. Youll quickly start to see how you can leverage the codebase to solve these issues

---

#### [2025-11-03 21:01:58] @yegu88

No doubt that NT is very flexible and powerful. Precisely because of that I’m looking for tutorials on how to use it effectively. And there are things that even code experiments won’t tell me. For example if I run a backtest with 1 day bars I assume the strategy runs one bar at a time (ie once a day). If it generates a buy signal when does the buy happens? At next days open? If I’m working with multiple instruments and augment with other data, does NT automatically align the bars? If I rebalance my portfolio monthly based on daily prices, do I need to execute the strategy on intervening days? I really don’t want to have to look thru the source code to find the answers. I appreciate that you guys have built a great system. I’m in developing trading algorithms however. That’s why I’m interested in leveraging a trading system where I can just plug in our algos

---

#### [2025-11-04 02:03:29] @fudgemin

Well thats alot to take in. You dont want to have to look at source code? Then build your own system. 

Im a self taught dev, for 2 years. I dont think there is any scenario where i would prefer to avoid understanding what im working with, or the foundation behind it. A codebase its a tool, and its benefit would come in knowing how to apply that tool, which requires understanding of it. As well, i am not a contributor, require no thanks or credit.  

I also prefer to develop 'algos'. I spend a year learning/building many things, have very good feature system, predictive signals etc. However, none of that means anything if you cannot act upon that, or execute. NT solves that entire problem, and integrates very nicely into custom systems imo. 

I think your logic is flawed. The process at which you endeavor to accomplish something requires refinement

---

#### [2025-11-04 02:07:09] @cjdsellers

There has been a general theme of frustration at understanding how the system works, and usability. I completely understand this, ideally there should be many more tutorials to walk through all the complexity, no doubt it would improve the onboarding experience.

In hindsight more time could have been invested into the docs from the outset, although it does take a lot of bandwidth, which was instead invested into building. We do intend on improving documentation in the future, this is just where the project is at right now though

---

#### [2025-11-04 02:11:09] @cjdsellers

<@940399143774486568> There is a bar-based execution section in the backtesting concept guide in case it helps a bit https://nautilustrader.io/docs/nightly/concepts/backtesting#bar-based-execution

---

#### [2025-11-04 02:28:07] @yegu88

We can just agree to disagree and that’s ok. If you have to understand every framework’s inner workings instead of its encapsulated functionality where is the productivity gain? I’m sure that many of us are capable of creating things from scratch. That approach rarely serves anyone. Btw I did build my own system and it works just fine for what it does now. However I want something more capable and thus my interest in evaluating NT. Because of this switching cost I want to be able to make a determination without having to become an expert in it first. If I have to look thru the source code, which I’m sure we will at some point, it’s a deal breaker at this stage.

---

#### [2025-11-04 02:37:03] @fudgemin

you will not build this system yourself, it would be foolish to do so. You have to understand this is highly optimized over many years. I certainly dont think any single dev, 10x or not, could reproduce this from scratch with minimal effort. Just modifying a fork has required some investment.

This is because, again, the system is iterated upon over many work hours. Some of those iterations are strictly for performance gains, like entire port to rust or cython modules. Something like this doesnt happen overnight, nor over months. Its ranked top open source repo in the space, multiple times for a reason. Its solves the problems for many of people. It certainly would for you as well, if your willing to spend a bit of time undertstanding. Youll notice the design is quite intuitive and easily understood with a few days of experiments. Good luck in your search, i was not able to find anything else comparable.

---

#### [2025-11-04 02:41:16] @yegu88

I’m very much in agreement with you on its capabilities. I’m also a big fan of not reinventing the wheel. I just need to figure out how to implement what we have with this. It isn’t a decision I can make alone so it’s important that I can learn as much in the shortest amount of time as possible

---

#### [2025-11-04 02:43:35] @yegu88

Rust-core and Pythonic. What’s not to like?😜

---

#### [2025-11-04 02:58:42] @yegu88

In the doc, it says that I need to convert opening time to closing time. Does this apply to daily bars as well? That is, do i need to shift the date by 1 if i'm getting data from a non-Databento provider?

---

#### [2025-11-04 03:01:18] @yegu88

That's something that we would do to calculate for example forward returns in a ML model so if that's the case it makes sense

---

#### [2025-11-05 05:18:22] @yegu88

<@757548402689966131> could you pls clarify the above question on daily bars? Thank you

---

#### [2025-11-05 10:52:36] @s1korrrr

hey guys! Couldn't find Hyperliquid specific channel, so I'm posting it here 🙂 Could someone confirm whether the wildcard arm _ => {} in nautilus_trader/crates/adapters/hyperliquid/src/websocket/handler.rs (line 180) is intentionally left to drop all other HyperliquidWsMessage variants (trades, quotes, book updates, etc.), or is this the reason our Hyperliquid market data stream never forwards those payloads? or i'm doing something wrong? 🙂 <@757548402689966131>

---

#### [2025-11-05 23:14:47] @cjdsellers

Hi <@488283874909224971> the Hyperliquid adapter is still in the `building` phase and not yet operational

---

#### [2025-11-06 04:47:17] @micro_meso_macro

Hi! I have a conceptual question. Is `OrderMatchingEngine` only used in backtesting? I tried my best efforts of they day but I cannot reach this conclusion. AI says yes with confidence. But I still doubt it. On a high level, I see it's an independent crate outside of backtest crate.

---

#### [2025-11-06 05:39:41] @faysou.

Yes only in backtesting. In live a live exchange is responsible of this. I had the same question before as well.

---

#### [2025-11-06 08:31:35] @helo._.

Which schema most closely simulate backtesting?
I thought CMBP-1 is fine for high volume instruments, but CMBP-10/MBO is needed for low volume instruments.

---

#### [2025-11-06 09:59:45] @ido3936

Hello, I  have been using the `time_bars_origin_offset` to offset bar start/stop hours - thanks <@965894631017578537> !!
The only problem I see is that AFAIK it does not take DST hour shifts into account. There is a workaround I think (by aggregating two bar types: one for winter and one for summer) - but it seems wasteful
Has anyone else met with this issue and maybe solved it in a smarter way? 🙏

---

#### [2025-11-06 10:06:37] @faysou.

🙂 you're welcome, there's no concept of DST for now, the whole system runs on UTC, I think it could be an important thing to add at some point the knowledge of trading sessions for a given day, but for now it's not done, and how to take it into account with time bar aggregator. but I don't think I will work on this for now, I think it's better to continue working on the migration to rust, or let <@757548402689966131> work on this as he does this mostly, and we could add this feature maybe later. I think anything is possible if there's a desire for it, but there's a lot of things changing already, including with some of my changes, so I don't want to pile even more things. the positive thing is that AI agents are more and more capable, it's getting really impressive for example with cursor 2.0, so work can go faster over time for the migration. I was impressed with claude 4 in may, and I'm impressed in the last days with cursor 2.0, it's really fast and good

---

#### [2025-11-06 10:10:52] @helo._.

<@965894631017578537> Could you please recommend a good schema for backtesting in terms of simulation accuracy vs computation? I saw that you worked on CMBP/OrderBookDepth10, so I believe you're expert in this area

---

#### [2025-11-06 10:12:48] @faysou.

hi <@356336934626525186> it's up to you to do your own research, it's your business decision, I can discuss technical issues or bugs, but I can't start offering advice to anybody who asks, I've done it in the past, and then people are never happy, they always want more, so I won't do it again.

---

#### [2025-11-06 10:34:49] @helo._.

<@965894631017578537> I respect your decision. But you seem misunderstood. This is not a business question. It is a simple question asking which data NautilusTrader is primarily designed for. The documentation say it is designed for 'granular order book data', but that is a vague term.

---

#### [2025-11-06 10:36:57] @faysou.

I know, but I can't answer all simple questions, else I would do this all day. It's up to each person to do their own research.

---

#### [2025-11-06 10:41:43] @helo._.

I respect your decision to not answer. I just cleared out the misunderstanding that it was a business question.

---

#### [2025-11-06 10:51:30] @faysou.

I think it's a business decision because depending on the market data type you choose you will have more or less data to download and also this will affect your backtest speed. so it depends on the strategy you want to test, and the precision you need.

---

#### [2025-11-06 10:53:19] @faysou.

the most affordable data type in databento is 1m bars, but then it's less precise than more granular data types, so basically it's a choice to make.

---

#### [2025-11-06 10:54:05] @helo._.

<@965894631017578537> I'm not trying to argue with you. I really do respect your decision. You are great NT contributor, and I know you are busy.

---

#### [2025-11-06 10:54:18] @faysou.

yes I understand, thanks

---

#### [2025-11-07 01:30:42] @cjdsellers

Hi <@940399143774486568> to clarify, the requirement is that all bars used for execution need to have a `ts_init` (be timestamped on) the close of the bar (the `ts_event` can remain at the open if that's preferred for analytics or to maintain the venues/providers native time stamping). So this applies to daily bars as well, if that is the granularity of market updates you're working on for some backtest. There are also a couple of exceptions for when bars are not processed for execution (will not update the book):
- Internally aggregated
- Monthly
- When the book is other than L1 

This needs to be updated in the docs, along with the point faysou made about `ts_init` earlier (it's on my list). At the risk of exposing some low-level implementation details you understandably would prefer to be abstracted from, here is the section of code in the matching engine which handles this: https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/backtest/engine.pyx#L3929

**Links:**
- nautilus_trader/nautilus_trader/backtest/engine.pyx at develop · n...

---

#### [2025-11-07 16:23:33] @micro_meso_macro

Hi. For benchmarking (IAI), I am wondering if you guys can get it work on your side. I cannot run existing benches on my side.

---

#### [2025-11-08 01:04:09] @cjdsellers

Hi <@396846605623623681> the benches being run in CI with `make cargo-ci-bench` did not include all benches (such as the adapter specific ones). Those were broken due to a `rustls` import scoping issue (now fixing)

---

#### [2025-11-08 01:12:01] @micro_meso_macro

Thank you Chris!

---

#### [2025-11-08 05:11:48] @colinshen

Hi，`request_bars ` has warning `eceived empty bars response (no data returned)` . In order to test how the function works, I have both internal and external data in my catalog.
```
 self.request_bars(
      bar_type=self.config.spot_bar_type,  #BTCUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL
      start=self.clock.utc_now() - pd.Timedelta(days=5),
  )
```

---

#### [2025-11-10 12:27:16] @megafil_

hi. trying to transition from backtest to live, the node works fine and receives data, but i am struggling with the burn-in. on_historical doesn't work because the actors interact and the historical bars don't respect the clock (each actor gets hit with only the bars and and not other data) so i was thinking to perhaps run a backtest and then pass the initialized strategy to the live node.
what's the preferred way? or is there another way to combine backtest with live? cheers

---

#### [2025-11-10 14:25:51] @euriska

how hard is to create an integration for tastytrade, alpaca or tradier brokerages? I'm not a seasoned programmer but I do surprise myself at times?

---

#### [2025-11-10 18:00:13] @faysou.

https://nautilustrader.io/docs/latest/concepts/data/#working-with-bars-request-vs-subscribe

---

#### [2025-11-10 18:00:29] @faysou.

Look here, you can start a subscription as a callback to a request

---

#### [2025-11-11 02:12:00] @megafil_

Thanks for answering, in my particular case, I have 2 actors A,B, both receive bars, A is also emitting signals which B requires for its burn-in, so a joint initialization.
so in regular subscribe mode, the message bus/clock orchestration sequences like
A.on_bar (bar(20210101)) -> publish_data(Signal(20210101))
B.on_data(Signal(20210101))
B.on_bar(bar(20210101))
... advances the day and repeats the cycle with A.on_bar (bar(20210102))
[as an aside: is this order guaranteed or is it possible that B.on_bar is triggered before on_data? ]

however, in historical replay mode, i observe the sequence
A.on_start().request_bars()
A.on_historical()  ... called until exhausted of historical bars [20210101, 20210102, ...]
B.on_start().request_bars()
B.on_historical()  ... called until exhausted of historical bars [20210101, 20210102, ...]
so it is not respecting the clock of the bars and has also no interaction,  A.publish_data(...) is also not being picked up by B at all.

for back-testing, i decided to just not use .request_bars and instead just discard a bit of data for burn-in, but in live-trading i dont have the luxury so i need to be able to initialize.
i had the following ideas:
1. refactor to a bigger actor class so that no interactions are needed
2. run actors through backtest and pass the initialized objects to the live node
3. dump initialized values to data-catalog and load on startup
4. just had another idea: maybe i can request historical bars, then access the published data from the .cache when requesting the historical bars in the next actor.

probably there is another way, whats the best practice here or how was it intended to be used?
thanks again

---

#### [2025-11-11 09:08:57] @faysou.

That's an interesting question. And luckily for you I've just got a PR approved and merged where I refactored how the processing of historical works so it's close to how live data works. I think that your case would work if you use the develop branch. You would need to request bars only with A and subscribe to historical bars manually on actor B (look how it's done in actor.pyx) and do the rest as you currently do for historical data above. Note that an alternative would also be to save some state data about each actor so you don't need to replay the whole history every time, a bit like a snapshot in event sourcing. Also look at actor.pyx and in the data engine to better understand the flow of data (on the develop branch). I've been working on improving the flow of data in nautilus regularly for about a year and it's getting really good in my opinion. If you don't manage to make it work, send  me a working MRE (minimum reproducible example) and I'll try to make it work.

---

#### [2025-11-11 09:11:05] @faysou.

It could maybe be useful to add some convenience methods to subscribe to historical data without requesting it, but there are a lot of methods already in actor.pyx, not sure I'll do it.

---

#### [2025-11-11 17:47:04] @nuppsknss

I'm running a backtest on a large tick-data dataset and I'm trying to use the `chunk_size` parameter in `BacktestRunConfig` to manage memory usage. My understanding is that this should stream the data from my Parquet files in chunks rather than loading the entire date range into memory at once.

Despite setting `chunk_size`, my backtest process still consumes a very large amount of memory, as if it's loading the entire dataset from the start. I'm monitoring my system's RAM, and the usage spikes immediately, regardless of the `chunk_size` value I set (100000 or 50 - no changes in RAM allocation). 


Data structure: `nautilus_catalog/data/trade_tick/BTCUSDT-PERP.BINANCE/*.parquet`
Each parquet file contains ~1 day of trade ticks

```python
data_configs = [
    BacktestDataConfig(
        catalog_path=str(self.catalog_path),
        data_cls=TradeTick,
        instrument_id=instrument_id,
        start_time=start_ts,
        end_time=end_ts,
    ),
]

run_config = BacktestRunConfig(
    engine=engine_config,
    venues=[venue_config],
    data=data_configs,
    chunk_size=250_000,  # Setting this to 250k 100k or 50 doesnt change anything in RAM allocation
)

self.node = BacktestNode(configs=[run_config])
self.node.build()
# add strategy
self.node.run()
```

When backtesting I do however see these prints:
if chunk_size == 250_000:
```
[INFO] BACKTESTER-001.BacktestEngine: Added 250_000 data elements

```
if chunk_size == 500_000:
```
[INFO] BACKTESTER-001.BacktestEngine: Added 500_000 data elements
```
which would suggest that it is working

am I not using it correctly? 
What is the proper way of decreasing RAM usage?

The only thing that seems to help here is changing `start_date` and `end_date` of backtest but obviously I wouldnt want to do that

I am using Nautilus Trader 1.220.0

---

#### [2025-11-12 04:32:46] @megafil_

I am really puzzled by the sequencing. I am running the latest development, nautilus_trader-1.222.0a20251111
The following setup (can provide MWE if needed but the problem is obvious from the code)

Actors A & B subscribe to daily bar. 
Actor A publishes Data S and B subscribes to S

This is what happens
ActorA: receives Bar at 20200101 -> publishes S (at 20200101 + 1second)
ActorB: receives S
ActorB: receives same Bar at 20200101

so the publish_data() executes the callback immediately and does not respect some sort of queue. i have confirmed in the MessageBus that it just calls the handlers directly, but now it processes a newer event before the data-event. 
Is there a way to respect the clock? perhaps an event queue? i would have hoped that the Bar is in actor B's event queue and triggers on_bar before on_data

---

#### [2025-11-12 04:51:53] @megafil_

after digging a bit more, it seems you guys have made this by design. now i wonder why you decided against having a queue? and is there an elegant way to guarantee that the published events get handled after all the bars that come before? i just want to respect the clock ordering of events

---

#### [2025-11-12 10:30:36] @estebang17.

Good day everyone,

Bracket Orders are not OCO(One-Cancels-Other) right? I have to cancel the other order when one of the sides gets filled

---

#### [2025-11-12 11:23:24] @bibamoney

please show video where backtester on rust works or on real live trading? visually

---

#### [2025-11-12 21:28:01] @heliusdk

Whats the point when you know that a strategy is ready for forward or live testing?

Been working on a few strategies, and have two that seems okay, that I will be putting to forward testing soon, however just wanted to hear you guys out if you do anything besides following the sharp and sortino ratio?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1438279193992495145/image.png?ex=694a60a1&is=69490f21&hm=a935051772fe66f1bf7f894644fa19b8ae6400305966a965f3623eb8c9d9f328&)
- [image.png](https://cdn.discordapp.com/attachments/924506736927334400/1438279194541953045/image.png?ex=694a60a1&is=69490f21&hm=cdd858086e08e04f9c847b5b727d56ec07ad4d53356a42855f37089dd069a6aa&)

---

#### [2025-11-13 09:44:29] @estebang17.

real men test in prod

---

#### [2025-11-14 18:24:54] @nobita0313

is it possible to exclude pre/after market data when i do bar aggregation?
I am trying to combine 1 min bar to 1d bar
TSLA.XNAS-1-DAY-LAST-INTERNAL@1-MINUTE-EXTERNAL

---

#### [2025-11-16 16:50:26] @akatsuki_alpha__42583

Hi all, has anyone found an elegant, nautilus-native solution to handling corporate actions and other symbol changes dynamically? Perhaps using a perm ID such as FIGI and stitching tickers together? It seems important to have one unified identifier for requesting historical data, running performance attributions, etc.

Would love to hear what others have tried or come up with!

---

#### [2025-11-17 04:51:53] @micro_meso_macro

Hi guys. I am wondering if any of you have benchmarked the **performance of msgbus via redis**. In my testing with 2 customized data structs on external bus, 1 tx node and 1 rx node. I also run redis in docker (I use podman); all on the same machine. I get the following performance:

(microsecond)
min=60.3
mean=237.5
median=188.0
p95=593.4
p99=907.2
max=1015.4

And my 2 customized data structs
> @customdataclass
> class BestBidAsk(Data):
>     """Best bid/ask data for an instrument."""
>     instrument_id: InstrumentId
>     best_bid: float
>     best_ask: float
>     ts_data_node: int
> 
> 
> @customdataclass
> class SyntheticFeatures(Data):
>     """Synthetic trading features."""
>     btc_softmax: float
>     eth_softmax: float
>     sol_softmax: float
>     btc_change: float
>     eth_change: float
>     sol_change: float
>     ts_data_node: int
> 

It's quite slow compared to other components. Does this look normal to you? Any idea on improving the performance here?

---

#### [2025-11-17 12:06:20] @haakonflaar

Is there a smart solution to be able to use a rust indicator's `handle_bar` method in a strategy? It currently causes a typerror as the bar passed to the `on_bar` function is the cython version of `Bar`, and the rust indicator method expects the rust version. Is it possible to receive the Rust `Bar` in `on_bar`? I know you can use the `update_raw` method directly, but that is tedious.

---

#### [2025-11-17 12:24:20] @faysou.

rust objects are not supposed to be used now, they are not compatible with the existing cython system, they will be used when the rust system is usable, which is not now

---

#### [2025-11-17 21:07:41] @mheise

Hey everyone, hey <@965894631017578537>.  I am progressing a strategy from low-level backtesting API to high-level sandboxed API using the IBKR integration. Here I would like to use the update_catalog flag when requesting bars/instruments. I might be missing something obvious, but my question is the following: how do I add the catalog to the engine when using the high-level API. Currently I am getting the "DataEngine: No catalog available for appending data." warning add would like to add a catalog to save / load data from.

---

#### [2025-11-17 21:09:09] @faysou.

Hi, use DataCatalogConfig, look in the examples folder in the repo, there are some files I use to tests things, look in notebooks folders in backtesting and live/interactive_brokers

---

#### [2025-11-17 21:11:26] @mheise

Thanks, will do and revert if I still don't manage. Followed the IB sandbox example using the LiveDataEngineConfig and missing the catalog there.

---

#### [2025-11-17 21:12:41] @mheise

I'd greatly appreciate, if you could tell me the high-level API property that the DataCatalogConfig needs to be set into. The rest I can find the in code... many thanks

---

#### [2025-11-17 21:14:33] @faysou.

No I can't solve cases in details for you. I can give you a direction and up to you to work on it. You can clone the repo and use an AI agent to help you, they are powerful.

---

#### [2025-11-17 21:19:52] @mheise

Perfect, found it in notebooks/databento_historical_data.py. Set via TradingNodeConfig which is derived from NautilusKernelConfig in the "catalogs" property. Many thanks!

---

#### [2025-11-20 12:36:23] @javdu10

Hello there, to backtest BinaryOption, considering I subscribed to only 1 side (because the other side is synthetic and I can just do `1 - Other side price`) 

I only have parquet files for one 1 side, but the engine is complaining the other side has no data, why would I need data if I don't subscribe to it ?

Is there anyway around such things ? I still need the instument in the strategy for the other side and call self.cache.instrument, so i cannot just not include the BacktestDataConfig

```[ERROR] BACKTEST-TRADER.BacktestNode: Error running backtest
ValueError('data' collection was empty)```

---

#### [2025-11-20 12:36:45] @javdu10

is there any helpers to generate empty parquet or tell the engine "no worries I know" and not raise the error ?

---

#### [2025-11-20 14:20:06] @javdu10

Well, there is no need to go that road, making order with the engine will be rejected by the risk component because there is no orderbook any way, So i'll have to subscribe and save the data for both sides, so I'll just have to write deltas in the catalog then return in my on_order_book_deltas

---

#### [2025-11-20 16:27:46] @nuppsknss

What can cause the entire Trade Tick data from catalogue being loaded into the RAM memory when starting a backtest?

I've set `chunk_size` inside of `BacktestRunConfig` but it seems to be ignored and when initializing the backtest it still loads everything


here is how my configs look right now
```py

        strategies = [
            ImportableStrategyConfig(
                strategy_path=f"{__name__}:BreakoutStrategy",
                config_path=f"{__name__}:BreakoutConfig",
                config=strategy_config_kwargs,
            ),
        ]

        engine_config = BacktestEngineConfig(
            strategies=strategies,
            logging=LoggingConfig(log_level=self.log_level),
            cache=CacheConfig(
                encoding="bytes", 
                tick_capacity=100,  
                bar_capacity=200, 
            )
        )

        venue_config = BacktestVenueConfig(
            name=self.venue_name,
            oms_type=oms_type,
            account_type=account_type,
            base_currency=qc_code,
            starting_balances=[f"{self.starting_balance} {qc_code}"],
            default_leverage=Decimal("1.0"),
            book_type="L1_MBP",
        )

        data_configs = [
            BacktestDataConfig(
                catalog_path=str(self.catalog_path),
                data_cls=TradeTick,
                instrument_id=instrument_id,
                start_time=start_ts,
                end_time=end_ts,
            ),
        ]
        run_config = BacktestRunConfig(
            engine=engine_config,
            venues=[venue_config],
            data=data_configs,
            chunk_size=100000,
        )
        self.node = BacktestNode(configs=[run_config])
        self.node.run()
```

---

#### [2025-11-20 23:34:11] @nuppsknss

I tried adding DataCatalogConfig but its not working either, 

I added
```python
        catalog_config = DataCatalogConfig(
            path=str(self.catalog_path),
            fs_protocol="file",
            name="backtest_catalog",
        )
```
below `strategies` as well as `catalogs=[catalog_config]` in the `BacktestEngineConfig` but this doesnt seem to work as well.
any tips would be appreciated

---

#### [2025-11-21 08:10:57] @conayuki

```
[ERROR] TESTER-001.ExecClient-INTERACTIVE_BROKERS: Cannot reconcile execution state
ValueError(Instrument not found for contract IBContract(secType='BOND', conId=401820131, symbol='US-T', localSymbol='IBCID401820131', currency='USD', tradingClass='US-T', lastTradeDateOrContractMonth='20270131', strike=0.0, comboLegs=[]))
Traceback (most recent call last):
  File "/Users/samuel.nys/.pyenv/versions/py-3.13-def/lib/python3.13/site-packages/nautilus_trader/live/execution_client.py", line 489, in generate_mass_status
    reports = await asyncio.gather(
              ^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/samuel.nys/.pyenv/versions/py-3.13-def/lib/python3.13/site-packages/nautilus_trader/adapters/interactive_brokers/execution.py", line 439, in generate_order_status_reports
    instrument = await self.instrument_provider.get_instrument(position.contract)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/samuel.nys/.pyenv/versions/py-3.13-def/lib/python3.13/site-packages/nautilus_trader/adapters/interactive_brokers/providers.py", line 137, in get_instrument
    raise ValueError(f"Instrument not found for contract {contract}")

2025-11-21T07:43:50.942610000Z [WARN] TESTER-001.ExecEngine: No execution mass status available for reconciliation (likely due to an adapter client error when generating reports)
2025-11-21T07:43:50.942626000Z [ERROR] TESTER-001.TradingNode: Execution state could not be reconciled
```
Trying to connect to IbGateway and I got the above log. Is it a bug?

---

#### [2025-11-21 08:32:55] @conayuki

by setting filter_sec_types=['BOND', 'OPT'] in InteractiveBrokersInstrumentProviderConfig,
I got around the above error but now it is complaining some other symbols

```Instrument not found for contract IBContract(secType='STK', conId=509735674, exchange='PINK', symbol='NLCP', localSymbol='NLCP', currency='USD', tradingClass='OTCQX', strike=0.0, comboLegs=[]))
```

---

#### [2025-11-22 14:38:30] @nuppsknss

figured it out!

---

#### [2025-11-22 16:46:51] @svs26

Hey! I'm trying to follow this example from the docs https://nautilustrader.io/docs/nightly/concepts/reports#live-trading. But it seems that `self.trader` does not exist inside of an Actor. Am I missing something?

**Links:**
- Reports | NautilusTrader Documentation

---

#### [2025-11-23 21:07:24] @mheise

Hi everyone, hi <@965894631017578537>:
I would greatly appreciate your help in an issue I am having with a strategy running over multple years. I have timers set up for the first and last trading day on the month. When I have a bar subscription active, the backtest runs over the backtest period and the day timers are firing as expected. The problem is, when I have no subscription active, the backtest just exits on the first day and the timers are not fired. Is there any way I can have the backtest process every day of the backtest period without an active bar subscription? I am doing it this way, so that I can request the historic last month's data for many symbols at the end of the month, which exceed my IB 100 instrument limit for market data streams.

---

#### [2025-11-24 12:50:55] @estebang17.

trader is inside of the engine, try engine.trader.generate_xxx. This works for me on the nightly branch

---

#### [2025-11-24 12:53:09] @estebang17.

How did you solve this?

---

#### [2025-11-24 22:46:52] @yegu88

When I construct daily bar ParquetDataCatalog files for US stocks, do I need to set ts_init and ts_event to the UTC equivalents of 4:30pm and 9:30am NYC times?

---

#### [2025-11-24 22:47:35] @yegu88

My data provider just supplies the dates

---

#### [2025-11-25 01:44:32] @petioptrv

You can roll up your own `generate_positions_report` for your strategy as it has access to the cache. Here's `Trader.generate_positions_report` implementation
```
    def generate_positions_report(self) -> pd.DataFrame:
        """
        Generate a positions report.

        Returns
        -------
        pd.DataFrame

        """
        positions = self._cache.positions()
        snapshots = self._cache.position_snapshots()

        # Generate report with positions and snapshots
        return ReportProvider.generate_positions_report(positions, snapshots)
```

---

#### [2025-11-25 04:51:11] @cjdsellers

Hey <@940399143774486568> 
I would set `ts_init` to when you would have expected the bar to close live

---

#### [2025-11-25 08:15:23] @cauta

hi, i'm new here.
i'm trying to record data from live binance, and use for testing later.
i use `StreamingConfig` within trade node
```
config = TradingNodeConfig(
    trader_id="TRADER-PREPARE-DATA",
    environment=Environment.LIVE,  # use LIVE for real streaming; use SANDBOX/TEST if you wish
    # cache=CacheConfig(database=DatabaseConfig()),
    # message_bus=MessageBusConfig(database=DatabaseConfig()),
    streaming=StreamingConfig(
        catalog_path=str(catalog_path),
        flush_interval_ms=2000,
        rotation_mode=RotationMode.SIZE,
        max_file_size=128 * 1024 * 1024,
    ),
```
i've record it and have a live catalog data folder
and i'm trying to convert it to parquet files for backtest.
my convert code is:
```
    catalog = ParquetDataCatalog(path=settings.catalog_path)
    catalog.convert_stream_to_data(
        instance_id=instance_id,
        data_cls=CryptoFuture,
        subdirectory="live"
    )

    catalog.convert_stream_to_data(
        instance_id=instance_id,
        data_cls=TradeTick,
        subdirectory="live",
        identifiers=[f"{settings.symbol}.BINANCE"],
    )
```

The problem i met when running backtest from BacktestNode is There are no instrument in `self.cache.instrument`
and error happen when i try to convert CryptoFuture instrument to parquet
please help me find out what is the best practice for record live data prepare for testing and why error here?

**Attachments:**
- [anh.png](https://cdn.discordapp.com/attachments/924506736927334400/1442790761564471367/anh.png?ex=694a4f9b&is=6948fe1b&hm=aa0e877053481f1323194056dfb188f50b76b79f643feb239047cdc4d3389317&)

---

#### [2025-11-25 08:52:56] @k123111

Hey everyone, I'm trying to understand the correct way to run multiple accounts within a venue while trading same instruments.
Use case: 3 VenueX spot accounts (different API keys) trading the same instruments.
From the code, it looks like the approach is to create separate "virtual" venues per account (VenueX_ACC1, VenueX_ACC2, etc.), each with its own exec client and instrument provider and duplicate instruments (BTCUSDT.VenueX_ACC1, BTCUSDT.VenueX_ACC2).
Is this the intended pattern? 
Or is there a way use universal instrument definitions across accounts to avoid N identical copied instruments and hassle to match them with what market data provider sends in?

I am currently trying to use separate exec clients with virtual venues but a single instrument provider. So my instruments are looking as BTCUSDT.VenueX. With this approach I am getting portfolio initialization errors. I suppose what happens internally is nautilus trying to match separate venues VenueX_ACC1 and universal instruments BTCUSDT.VenueX, failing to do that.

edit: I am using external messaging through redis with data client decoupled from accounts. It streams prepared objects (Bar, QuoteTick, TradeTick) with universal instrument already set. I don't want to couple data provider with accounts setup, and in any case streaming N copies of each object sounds sub-optimal.

---

#### [2025-11-25 16:55:31] @yegu88

Has anyone used the NautilusTrader's built-in P&L reporting? Does it work?

---

#### [2025-11-25 16:56:10] @yegu88

I'm getting 0 realized gains/losses and a ton of unrealized ones

---

#### [2025-11-26 07:09:09] @jst0478

In backtest reports,I had some issues with it originally:
https://discord.com/channels/924497682343550976/924499913386102834/1430411337149714454
Maybe this thread will help you.  But it sounds like you have the opposite problem as I did

---

#### [2025-11-26 23:11:18] @yegu88

Is it normal to have most of the PnL and return stats to be 0 or NaN?

**Attachments:**
- [Screenshot_2025-11-26_at_3.10.11_PM.png](https://cdn.discordapp.com/attachments/924506736927334400/1443378614187069541/Screenshot_2025-11-26_at_3.10.11_PM.png?ex=694a78d6&is=69492756&hm=3966efefc3b0b225540a5c0b9d2ac7f434a46377ee6f76bdc309045f5f227c89&)

---

#### [2025-11-26 23:12:21] @yegu88

Also i got a "Long Ratio" of 0.84 in a long-only portfolio😂  How should i interpret that?

---

#### [2025-11-26 23:13:02] @yegu88

<@757548402689966131>

---

#### [2025-11-27 04:06:34] @cauta

hi <@965894631017578537> <@757548402689966131> , do we have best practice for recording live data for later using in backtest?
i did use streaming config and got feather files, which are large. Later i need to convert to parquet, cost time also

---

#### [2025-11-27 06:36:59] @faysou.

Hi <@872066994151776296>  , <@224557998284996618> has implemented a way to rotate files with the streaming config. If you look at the code you will see the parameters (the best documentation is the code, then you can see unambiguously how things work, and the code is available, so it's like in a work setting, all answers are there. Plus by getting familiar with the code you can modify it to suit what you want exactly and contribute back. This is more a general comment here for everybody)

---

#### [2025-11-28 06:38:38] @cauta

Do we have plan for write `CryptoPerpetual`, `CryptoFuture`, etc. which are `Instrument` childs when doing streaming?
i met problem when doing live data record for later backtest. there are only some of them has been recorded:
```
self._per_instrument_writers = {
            "bar",
            "order_book_delta",
            "order_book_depth10",
            "quote_tick",
            "trade_tick",
        }
```
this make `convert_stream_to_data` function doesn't have fully data which is missing instruments when prepare data for backtest.
If this is not against current data flow and future impelementation, i can provide a PR for doing that
<@965894631017578537> <@757548402689966131>

---

#### [2025-11-28 07:56:26] @faysou.

Of course you can do a PR if you need something. You can add some unit tests and add or modify an example so it's easy to test what you do. To be honest the development process is much easier on simple improvement issues like the above with agents like cursor. And the price to pay is quite cheap compared to the power you get.

---

#### [2025-11-28 07:58:54] @faysou.

But the more people are able to improve the code the better. Of course quality needs to be there, but I assume people who use nautilus are not beginner programmers.

---

#### [2025-11-28 08:00:41] @cauta

this is my recommend for streaming instrument into live data, which is necessary for later testing conversion:
```python
 try:
    writer.write_table(serialized)

    # Use the appropriate key for file size tracking
    if isinstance(obj, Bar):
        size_key = (table, str(obj.bar_type))
    elif isinstance(obj, Instrument): # => streaming for instrument
        size_key = (table, obj.id.value)
    elif use_per_instrument_writer:
        size_key = (table, actual_data.instrument_id.value)
    else:
        size_key = table  # type: ignore

    self._file_sizes[size_key] = self._file_sizes.get(size_key, 0) + serialized.nbytes
    self.check_flush()

    if self._check_file_rotation(size_key):
        if isinstance(obj, Bar) or use_per_instrument_writer:
            self._rotate_identifier_file(cls=cls, obj=actual_data)
        else:
            self._rotate_regular_file(table, cls)
```

---

#### [2025-11-28 08:01:58] @faysou.

You can do a PR and I'll check when it's done

---

#### [2025-11-28 09:16:29] @estebang17.

your sell orders are making you short, enable reduce only on your sell/stop order:
            stop_loss_order = self.order_factory.stop_market(
                instrument_id=inst_id,
                order_side=OrderSide.SELL,
                quantity=quantity_to_close,
                trigger_price=instrument.make_price(stop_loss_price),
                reduce_only=True,
            )

---

#### [2025-11-28 13:58:25] @faysou.

I've just done a PR with this and a subtle change so the conversion of streamed instruments to a catalog works

---

#### [2025-11-28 13:59:32] @cauta

Oh ok, i suppose to have pr tmr. Thank you let me check a bit

---

#### [2025-11-28 14:27:56] @cauta

it seem better version than mine. no need to have lots of folder for instrument.
i also draft a PR here: https://github.com/nautechsystems/nautilus_trader/pull/3236
help take a look

**Links:**
- Stream instrument to catalog by cauta · Pull Request #3236 · naut...

---

#### [2025-11-28 14:29:10] @cauta

it seem also solve this error, when i try to convert instrument feather files into catalog and met deserialize problem

---

#### [2025-11-28 16:16:58] @javdu10

Hello there is it possible when subscribing to a synthetic instruments it actually subscibe to all underlying instruments without subscribing to them in my strategy ? 

or I have to subcribe to each of them and filter them out in my on_xxx callbacks ?

---

#### [2025-11-28 17:20:00] @faysou.

not sure about it, look in the data engine.pyx

---

#### [2025-11-28 18:16:24] @javdu10

I’ll have a look, thank you! 🙏

---

#### [2025-11-29 03:59:48] @yegu88

My bad. I mistakenly use the venue's OmsType to hedging instead of netting

---

#### [2025-11-29 09:08:38] @heliusdk

1) Why not run redis natively without padman on the machine?, if its linux the overhead is minimal but will still be there, there are also different ways to optimize redis based on usage, like fast throughput for lots of requests or tweaking fast delivery of a few large, some of that also comes down to your kernel tweaks.
2) Do you use socket or tcp to communicate with redis, if you use tcp you might save a little by switching to socket based.

---

#### [2025-11-30 05:17:46] @mk1ngzz

If you're optimizing for performance, then you should do the following:
- Run processes directly on the OS without containers, ideally managed with e.g Hashicorp Nomad
- Use shared memory ring buffers for the fastest cross-process communication with almost zero performance overhead

---

#### [2025-11-30 12:46:56] @heliusdk

Was replying to <@396846605623623681> .

Running redis directly on the linux machine would be better, as you do not have the overhead of the c-gropups communicating, but I do not see the importance of throwing in Hashicorp Nomad, for a person asking help in performance optmization, here in my opinion simplicity would always be the first step, I dont get the sense that hes managing a complex cluster 😅

* Use shared memory ring buffers for the fastest cross-process communication with almost zero performance overhead*
could you perhaps elaborate on this part, because it can be a multitude of things and implementations

---

#### [2025-11-30 13:03:17] @micro_meso_macro

😀 I appreciate your input. I use TCP. Didn't know that NT supports socket. <@223930266207518721> And yeah, I am also curious what the shared memory ring buffer means here. That sounds like redo the architecture of NT. Is there a simple way to achieve this?

---

#### [2025-12-01 08:25:10] @cauta

<@965894631017578537> from `parquet.py` function `def _handle_table_nautilus(`
if data is empty then error list index throw
```
data = ArrowSerializer.deserialize(data_cls=data_cls, batch=table)
module = data[0].__class__.__module__
```
there might be empty data by any chances?
i'm doing recording with rotate 1 minute, if the bar is not receive in time, then it's empty?

---

#### [2025-12-01 08:52:00] @faysou.

I'll add a check, thanks

---

#### [2025-12-01 18:54:44] @bart04262_88665

Hi. I just discovered NT today and read through some of the docs but don't find the answer for my case. I want to backtest various option strategies for a time period of let's say 1 year. How can I during the backtest dynamically load the option chains within eg a 7 to 30 day DTE range, and maybe also other filter criteria (eg within a option delta range)? I read about the ParquetCatalog but that seems to imply you need to load all data prior to starting the backtest. The other reason all data cannot be pre-loaded is because the filter criteria for option chain data in an advanced strategy may change during the backtest based on portfolio and market parameters. I have the historical option pricing data in a database I control and can write an adaptor to retrieve the data.  So basically I think this comes down to: how do I during a backtest 1/ monitor the timestamp so I know when to load new data (eg when we're at start of a new trading day), 2/ load this new data, and  discard the old to avoid redundant data requests. Will be using Interactive Brokers after backtesting for live trading. Thanks in advance for your reply.

---

#### [2025-12-01 19:59:29] @javdu10

From what I can tell when backtesting the time is just like when your received an event like orderbook delta and was written in the parquet file

And during live trading it is the current time

---

#### [2025-12-01 20:00:29] @javdu10

There is « request_instrument » depending if your adapter implements it the way you want

---

#### [2025-12-01 20:14:03] @bart04262_88665

Thanks but I'm not quite clear. Fundamental question: can you change the instruments DURING backtesting? A google search for "nautilustrader change instruments during backtesting" gives this AI-generated reply: "You cannot change instruments mid-backtest in Nautilus specifically, as a backtest runs on a fixed historical dataset for a single instrument. To test a strategy on different instruments, you must run separate backtests for each one, or create a single backtest that runs for a longer period and includes data from different instruments if your strategy allows" Can someone say if this is a correct limitation? If this is true, then it seems what I'm asking for cannot be done with NT. To clarify why I need to load data dynamicallly: I use SPX options, and 1 year of minute-level options data is ~100GB in my Postgres database. So if I want to backtest over 1 year, I would need to pre-load 100GB of data for each backtest which is obviously not practical as only a small subset of this data needs to be used based on the strategy being tested and market conditions during the backtest.

---

#### [2025-12-01 23:12:21] @javdu10

Sorry, I tried few things and just realized I have the same issue as you and was only side stepping it. I do request instrument dynamically, but the data is still preloaded on my side taking 20Go of RAM - I would also be interested in a solution that only loads the data it needs with the high level backtest API. It can probably be done with the low level API, I did not dug this yet

---

#### [2025-12-01 23:25:22] @fudgemin

this is not an issue. you dont preload. its an option, not a requirement. the system can stream defined data types to the node. and whatever this story is above i cannot read it, but i can say Nautilis has a solution for any problem you can think of over a span of a few days. Its a 10 year dev product. Play with it for a few weeks or more then determine your actual issues.

---

#### [2025-12-01 23:33:43] @bart04262_88665

“Whatever this story is above I cannot read it” I thought I explained my question pretty clear - if not pls clarify what is unclear. And if it can be done it would be helpful to give some pointers rather than blanket statement “NT has a solution for any problem”. Thanks.

---

#### [2025-12-01 23:34:26] @fudgemin

one line questions and i will answer them for you.

---

#### [2025-12-01 23:36:23] @fudgemin

you load instrument 'IDS' before a backtest. this gives you access to those data types during a node run, which can be from x date to x date of any specification

---

#### [2025-12-01 23:37:44] @fudgemin

this is metadata. That metadata gives access to the actual data. The only data the system cannot 'stream' during a backtest, is custom. And even then you can built a streamer to feed the data, if its to large to hold in ram

---

#### [2025-12-01 23:38:04] @fudgemin

this is production. I have tb of custom data. I like the application

---

#### [2025-12-01 23:39:07] @fudgemin

aside, you can literally just 'chunk' a backtest. by building a node, and feeding it data in chunks. or by using the existing arg = *chunk_size*

---

#### [2025-12-01 23:41:53] @bart04262_88665

The issue is that you don’t know which instruments are needed for the whole backtest before starting it. So the instrument IDs are not known in advance. They cannot be preloaded because for eg a 1 year backtest there would be thousands of options. So my question remains how to dynamically load data of new instruments during the backtest run.

---

#### [2025-12-01 23:44:10] @fudgemin

you can load 10k insurments if you wanted? do you need more? i load and use 500 assets, and to load that metadata takes fractions of a second....
once those metadata objects are loaded, you now have access to that data: subscribe_data() in a strategy.

---

#### [2025-12-01 23:44:38] @fudgemin

100k assets would be like 1mb of data

---

#### [2025-12-01 23:46:49] @fudgemin

you can also read and access or load on demand. it just a secondary step

---

#### [2025-12-01 23:47:20] @bart04262_88665

SPX options have daily expirations so let’s say each expiry has 100 strikes that would be 2 (calls and puts) x 100 x 250 trading days/year = 50K instruments for a backtest that spans 1 year. Furthermore they are not all existing at the start of the backtest run as options are created by the exchange through the year.

---

#### [2025-12-02 00:07:38] @javdu10

I could not find mention about NOT preloading for the high level API,Although I can see the generator in the low level api, I was interested in the high level for this bullet point:

> Consider using the high-level API when:
> Your data stream exceeds available memory, requiring streaming data in batches.

I did not find this behavior yet 🙁
I am still of course learning many many things about NT, it is a very great tool and wrote few adapters for my need very happy with it, it’s just that the « discovery path » and example are rather rough

Another example would be the synthetic instruments, how do it play with « -SWAP » « -PERP » it does not play well with hyphens and I have yet to check the source code if it expects underscores or just cannot use instruments with hyphens in the names, the rstests either don’t mention this behavior 🙁

---

#### [2025-12-02 00:33:52] @fudgemin

use datacatalogconfig. Not sure about naming for instruments, but venues name dont like hyphens. If instruments start with hyphen, thats likely no go

``` catalog_path = "/root/furtim_alpha/nautilis_catalog"
    
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
                instrument_ids=[],  # Specify instruments to load bars for```

---

#### [2025-12-02 01:28:22] @bart04262_88665

So i haven't seen any proof that NT can support loading instruments dynamically during backtest as I explained is needed for my use case (this is NOT chunking of data of the same instrument) so I will for now conclude it is not possible and look for another solution. Maybe the founder can comment on this with a definitive statement <@757548402689966131>

---

#### [2025-12-02 04:32:26] @kulig1985

Hi, found this tutorial.. https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook but there isn’t even a word about that how to provide historical order book data for this… and how this data should look like.. can anyone help me?

**Links:**
- Backtest: Binance OrderBook data | NautilusTrader Documentation

---

#### [2025-12-02 05:51:25] @cjdsellers

Hey <@1280178449599823902> that use case is indeed different to simply chunking, and is actually supported. It's quite new and currently undocumented though, so one of those things that require hunting through the code or asking an LLM at this stage

---

#### [2025-12-02 05:59:27] @bart04262_88665

Thanks for the reply. I think I’ll wait though until it’s more mature and documented. I took a look meanwhile at QuantConnect and they support it and especially for options backtesting have extensive documentation. Their concept of “instrument universes” with filters that are run at configurable intervals to only load the instruments relevant to the strategy at that time, seems quite elegant.

---

#### [2025-12-02 06:04:53] @cjdsellers

Yes, I would suggest their platform if you want to get up and running quickly, it's been around for much longer

---

#### [2025-12-02 09:28:03] @manofculture5873

Good to know it’s supported! I’d really appreciate a few more hints, for example, which file or part of the source code should we look into? Thanks

---

#### [2025-12-02 20:37:47] @javdu10

Hey! Thank you for you message after further digging I was missing the undocumented property chunk_size !

```
run_config = BacktestRunConfig(
    engine=engine_config,
    data=data_configs,
    venues=venues,
    chunk_size=10_000,
)
```

---

#### [2025-12-02 20:40:13] @javdu10

Now my issue is that my pyarrow deserializer is not getting called for IndexPriceUpdate and it was called with preloading 🙁

---

#### [2025-12-03 00:42:39] @johnk3549

can you explain what you figured out? I'm having the same issue

---

#### [2025-12-03 08:41:02] @label_3

Hey <@757548402689966131>How should I understand the meaning of positive and negative fee rates in the system? During testing, I found that the fee rate obtained from OKX is negative, indicating a deduction of fees. When the fee rate is positive, it indicates a commission rebate. This logic seems to be used in other exchange adapters as well. However, in backtesting mode and Sandbox mode, a positive fee rate is used to represent deduction of transaction fees (reducing account funds) when calculating risk and slippage, while a negative value increases account funds.

---

#### [2025-12-03 10:57:43] @roaringkittyexception

Hellooo, I have one question regarding the synthetic instrument support in nautilus, as of now Ι've the impression that trading a synthetic instrument is not possible, you can only subscribe to synthetic quotes. Then today I went  through the documentation https://nautilustrader.io/docs/latest/concepts/instruments/#synthetic-instruments

```
Trigger instrument IDs

The platform allows for emulated orders to be triggered based on synthetic instrument prices. In the following example, we build upon the previous one to submit a new emulated order. This order will be retained in the emulator until a trigger from synthetic quotes releases it. It will then be submitted to Binance as a MARKET order:

order = self.strategy.order_factory.limit(
    instrument_id=ETHUSDT_BINANCE.id,
    order_side=OrderSide.BUY,
    quantity=Quantity.from_str("1.5"),
    price=Price.from_str("30000.00000000"),  # <-- Synthetic instrument price
    emulation_trigger=TriggerType.DEFAULT,
    trigger_instrument_id=self._synthetic_id,  # <-- Synthetic instrument identifier
)

self.strategy.submit_order(order)
```

I don't understand how a market order will be submitted to Binance, if trading a synthetic is not supported yet.

**Links:**
- Instruments | NautilusTrader Documentation

---

#### [2025-12-04 03:33:39] @cjdsellers

Hi <@710319013967691857> 
Thanks for reaching out about it. The convention is: positive fees represent charged commissions, negative fees represent rebates. For OKX, it was aligned earlier with this fix: https://github.com/nautechsystems/nautilus_trader/commit/d6aca8ff66eebf35fec577f4f728b4c0d5086369

Also documented more clearly here: https://github.com/nautechsystems/nautilus_trader/commit/ebece09536e8770f34393892a311ca15a63906e4

**Links:**
- Fix OKX fee rate sign convention · nautechsystems/nautilus_trader@...
- Document fee rate sign convention · nautechsystems/nautilus_trader...

---

#### [2025-12-04 03:35:43] @cjdsellers

Hi <@1058062076301553807> 
Quick answer is that the trigger instrument pricing being used there is synthetic, but the actual `instrument_id` for the order is ETHUSDT on Binance - so that is where the order will be routed when/if released by the emulator

---

#### [2025-12-06 13:40:16] @k123111

Hey team, hi <@757548402689966131> 
I have a question about the "virtual" positions created by reconciliation process. Using the venue not officially supported, so my own adapter. Using NETTING OMS - the only option in the venue and also set for nautilus.

I’m seeing synthetic INTERNAL-DIFF positions even though I’m not limiting reconciliation lookback. Scenario: at venue I’m long +1000 AAPL when Nautilus starts. Reconciliation runs and creates a +1000 INTERNAL-DIFF position. Then I buy +100 with my strategy (MyStrategy); the INTERNAL-DIFF stays +1000 and MyStrategy goes to +100, so net is +1100, and in practice I have 2 positions existing for a single instrument even though NETTING is set. 

Suppose next step I want to sell 500, then MyStrategy position goes short? Do I have to manage them like it's HEDGING?
Is there a way I can avoid this? Can I just reassign the position generated by reconciliation to belong to MyStrategy?

---

#### [2025-12-06 13:51:54] @faysou.

there have been many changes related to reconciliation in the develop branch, maybe try to use it to check if it would solve what you see

---

#### [2025-12-06 14:06:05] @k123111

Thanks, gonna try and report back

---

#### [2025-12-07 12:37:23] @_joomla_

Hey guys,
I'd like to share a single live tick data stream between traders running on different processes, via redis. With the ability to add and remote traders whenever. I'm trying to avoid streaming duplicate trade ticks from broker for each trader.
ie.
Process A -> Stream data from broker
Process B -> Trader 1 (listen to Redis stream from process A)
Process C -> Trader 2 (listen to Redis stream from process A)
Anyone attempted anything similar?

---

#### [2025-12-07 15:11:31] @javdu10

I am still far away to bother about this yet, but I’m also interested in this for the future, also curious about other kind of delivery mechanisms, like IPC and UDP multicast

---

#### [2025-12-08 04:32:49] @cauta

<@965894631017578537> <@757548402689966131> do we have any options that can stream our position while doing backtest?

---

#### [2025-12-08 06:23:59] @_joomla_

<@757548402689966131> - any implementation advice or gotchas would be much appreciated.

---

#### [2025-12-09 04:01:57] @fudgemin

i run a dedicated feature node like this. they are shared between nodes via redis 'streams'. It works like a charm. 
I 'produce' from feature node, with chaining transformers actors for feature engineering. Cast those features to custom data class so nautilis can serialize on the other end. This node pushes all features (1000+) to a redis backend, single stream topic. It filters out data types, which is a provided kwarg. As well, use no cache, only the message bus, and you can avoid orders, positions etc from going through the feature system. 

Then i have consumer nodes, which is only for trading strategies. These node receive data from the redis feature producer. Pretty scalable, easily set up using the configs provided. Happy with it so far. 

*Use data filter types, and you can make sure only certain data/events/orders flows through the system

---

#### [2025-12-09 04:11:31] @fudgemin

this was asked recently, but cannot find the post. 

there is a 'trader' class if i recall, which allows you to grab positions and orders. Should find an example config in the code, i forget where its located atm sorry. Im pretty sure it only accessible or callable at the end of a complete backtest. It was mentioned more work was going into the positions and orders module going forward, but currently not built in support. 

You can make an actor, to accomplish this yourself. Fairly intuitive to understand but just make a dedicated actor to track all positions and orders and push them via socket or preferred sink

---

#### [2025-12-09 04:23:24] @_joomla_

Thanks for the reply. I can't get my BacktestNode to ingest my Redis stream. 
Mind sharing your setup on the end that recieves the final transformed data for the TradingNode/BacktestNode?
I'm guessing my MessageBusConfig that is passed to my BacktestNode is not configured correctly.

---

#### [2025-12-09 04:26:58] @fudgemin

whicvh part? 

```    message_bus_config = MessageBusConfig(
        database=DatabaseConfig(
            type="redis",
            host="localhost",
            port=6379,
            timeout=2,
        ),
        encoding="json",  
        timestamps_as_iso8601=False,
        external_streams=["features"],  
    )```

---

#### [2025-12-09 04:30:54] @fudgemin

i dont use it for backtest node. but should be similar to how you add it. redis only works with supported data types and custom data you define.

---

#### [2025-12-09 04:35:53] @_joomla_

Thanks. That's what I was after. I'll try when I get home.
How do you define custom data types? Do you just create a structure and register it somewhere?

---

#### [2025-12-09 04:41:45] @fudgemin

yes define custom data classes:

1. ```@customdataclass
class FlowBaseMetrics(Data):
    """
    """
    instrument_id: InstrumentId
    trade: str = ""
    cp: str = ""
    side: str = "" 
...
from src.custom_data_class.flow_features_base import FlowBaseMetrics

        return FlowBaseMetrics(
            ts_event,  # Add your timestamps to the data when it is created
            ts_init,   # 
            instrument_id=data.instrument_id,
            trade=data.trade,
            cp=data.cp,
```
2.      publish:
                if isinstance(result, FlowBaseMetrics):
                    current_data = result
 self.publish_data(DataType(type(result)), result)

3. Add redis to consumer node:

    data_engine_config = LiveDataEngineConfig(
        external_clients=[ClientId("FEATURES_EXT")],  
    )

4.Subscirbe to data on consumer:

        self.subscribe_data(
            DataType(FlowBaseMetrics),
            client_id=ClientId("FEATURES_EXT"),
        )

---

#### [2025-12-09 04:57:27] @_joomla_

Thanks mate. Appreciate it.

---

#### [2025-12-09 22:59:16] @mohamadshoumar

🚨 [URGENT] Memory Issues with Large Tick Data Backtests - Seeking Streaming/Lazy-Loading Solutions

Hi 
We're hitting a critical memory blocker when running backtests with tick-level data and need guidance on memory-efficient approaches.

Our Setup
Fetching historical data from S3 (trade ticks or candles)
Using BacktestEngine with BarDataWrangler / TradeTickDataWrangler

The Problem
Even though we've optimized our data loading pipeline to call engine.add_data() multiple times with smaller chunks (avoiding one giant Pandas DataFrame), Nautilus still accumulates all data in memory before/during the backtest run.
> `# Our current approach - loading data in chunks
> for chunk_df in fetch_data_chunks(symbol, start_date, end_date):
>     wrangler = TradeTickDataWrangler(instrument)
>     ticks = wrangler.process(chunk_df)
>     engine.add_data(ticks)  # Multiple calls
> 
> engine.run()  # <-- At this point, all data is held in memory`
For long date ranges with tick data (e.g., several weeks of BTCUSDT ticks), the memory consumption spikes dramatically and crashes our infrastructure 

Our Questions
Is there a streaming or lazy-loading mechanism where Nautilus can read data incrementally during engine.run() rather than holding everything in memory upfront?
Is there a recommended way to run backtests on very large tick datasets (multi-month, 100s of millions of ticks) without requiring the full dataset in RAM?
Does the BacktestEngine support any form of data pagination - e.g., running the backtest in time-windowed segments while preserving strategy state?


**Env**
Nautilus Trader version: 1.202.0
Python 3.11+
Running in Kubernetes with memory limits

---

#### [2025-12-10 06:39:48] @courage521915

I'm encountering an error while running polymarket_data_tester.py. The log shows the following:

2025-12-10T05:53:32.010417543Z [ERROR] TESTER-001.DataClient-POLYMARKET: Error running 'Delayed start PolymarketWebSocketClient connection'
WebSocketClientError(IO error: Connection reset by peer (os error 104))

This appears to be a WebSocket connection issue—specifically, the remote server (Polymarket) is resetting the connection. Could you please help me ？

---

#### [2025-12-10 07:12:13] @cjdsellers

Hi <@1424700367899459666> 

Are you aware of the high-level API using a `BacktestNode` that allows you to stream data in chunks? https://nautilustrader.io/docs/nightly/concepts/backtesting#choosing-an-api-level

**Links:**
- Backtesting | NautilusTrader Documentation

---

#### [2025-12-10 07:12:56] @cjdsellers

Hey <@1447927112190398524> this can sometimes happen with certain VPNs, but I'm really not sure based on the information

---

#### [2025-12-10 08:43:48] @courage521915

Hello, I noticed that I don’t encounter this issue when running it in a Windows 11 environment, but it occurs when running it in a WSL environment.

---

#### [2025-12-10 14:22:50] @byron1051

Hey everyone
Any suggestions on how I could improve code completions in my IDE when dealing with cython compiled classes?

All the Python based classes and packages work fine obviously but when learning a new framework, and learning whats available, code completion is a big piece (for me at least). My IDE (vsc) however doesn't do any code completion, following, etc when non-python pieces 🙁

---

#### [2025-12-13 05:05:23] @petioptrv

Try PyCharm. Won’t be 100%, but from memory of last time I used VSC, PyCharm has better completions for Cython

---

#### [2025-12-15 06:48:12] @conayuki

<@757548402689966131> hello, one quick question here:
Without specifying a fill model in backtest, marketable stop market order blindly filled at non-existing trigger-price (no matter how crazy the price is!) with reject_stop_orders = False (backtesting on bar data only). Is it by design?
Using BestPriceFillModel fixes the problem.

---

#### [2025-12-15 07:25:44] @cjdsellers

Hi <@953244441982951434> 
Thanks for reaching out. I'm not sure of your exact data setup and config, but there *should* be a reason a price level was triggered (maybe the market moved through the price on one of your data points?). If you think there might be a bug then an MRE and/or detailed report will help us find the issue. Otherwise, if the `BestPriceFillModel` fixes the problem for you then that's good news!

---

#### [2025-12-15 08:00:33] @Wick



**Links:**


---

#### [2025-12-15 08:03:36] @conayuki

<@757548402689966131> the bot killed my message when I was editing it 🙁 see if you can recover it...

---

#### [2025-12-15 08:06:44] @cjdsellers

Did your message contain 3-4 images? that can trigger it sometimes. I'm not able to recover it unfortunately

---

#### [2025-12-15 08:12:52] @conayuki

yep let me try to repost, here is the order dataframe dump after backtesting. odd rows are the sell stop market orders in question. even rows are buy take profit limit orders working totally fine. observe the odd rows trigger_price and avg_px. I hardcoded the trigger price to 100000 on NQZ25 futures (dec 2025) when creating orders. I crosschecked the 1min bar data in catalog and they are perfectly fine. I did not use bid ask data in backtest however.

**Attachments:**
- [2025-12-15_4.07.42.png](https://cdn.discordapp.com/attachments/924506736927334400/1450037884718547055/2025-12-15_4.07.42.png?ex=694a4f04&is=6948fd84&hm=2b3000275618c759ed614d861ca11345b08c86f36de16627e54eea4dc2eb3438&)
- [2025-12-15_4.08.27.png](https://cdn.discordapp.com/attachments/924506736927334400/1450037885037445222/2025-12-15_4.08.27.png?ex=694a4f04&is=6948fd84&hm=e7a29250a0dd208d425f50bbfec358143b2194c941c0fa0c86b6aac734b23987&)

---

#### [2025-12-15 08:17:37] @conayuki

with BestPriceFillModel the avg_px is correct

**Attachments:**
- [2025-12-15_4.16.30.png](https://cdn.discordapp.com/attachments/924506736927334400/1450039080778862675/2025-12-15_4.16.30.png?ex=694a5021&is=6948fea1&hm=26b76a3849f5ada0063c37b104c8fcb323cb5b9d567e7d351b3e890c4e78bd1f&)

---

#### [2025-12-15 08:19:05] @conayuki

the way it calculates slippage is interesting tho

---

#### [2025-12-16 01:31:06] @cjdsellers

Hey <@953244441982951434> thanks for the additional info

This helped me to uncover a bug that I just pushed the fix for: stop market order fill prices in backtesting with bars.  Previously they'd always fill at the trigger price, even during gaps which wasn't realistic. Now it distinguishes gaps (fill at market, you get slipped) vs normal move-through (fill at trigger). It was also a good opportunity to confirm the testing and document fill price behavior properly
https://github.com/nautechsystems/nautilus_trader/commit/e394d48bf783ea3da151315071f3bd67ad010f1d

**Links:**
- Fix stop market order fill price in L1_MBP mode · nautechsystems/n...

---

#### [2025-12-19 11:58:43] @gabadia5003

Portfolio Venue Mapping Issue: "Cannot calculate realized PnL: no account registered for [VENUE]" on Cache Restoration

Hi team! I'm experiencing a race condition with Portfolio venue-to-account mapping during system startup when cached positions are restored from Redis.

Environment:

NautilusTrader 1.221.0
Dual-venue setup: POLYGON (market data) + ECX (execution via FIX)
Redis cache persistence enabled
Custom FIX ExecutionClient with AccountId format: FixExecutionClient-ECX-001

Issue:
After a restart, when the Portfolio restores cached positions, I get venue mapping errors:
[ERROR] MEMO-DESK.Portfolio: Cannot calculate realized PnL: no account registered for ECX
[ERROR] MEMO-DESK.Portfolio: Cannot calculate unrealized PnL: no account registered for ECX
[INFO] MEMO-DESK.Portfolio: SPY.ECX net_position=33  # position restored from cache

Startup Sequence Observed:

1. Account announced correctly: FixExecutionClient-ECX-001
2. AccountState generated with venue info: {'venue': 'ECX'}
3. Portfolio restores positions from cache → venue mapping fails
4. Portfolio can't find account for venue ECX during P&L calculations

Questions:

- Timing Issue: Is there a recommended way to ensure account announcements complete before cached position restoration?
- AccountId Format: Should account_id.get_id() return "ECX" to match the venue for proper mapping? - - Currently using format FixExecutionClient-ECX-001.
- Manual Re-mapping: Is there a way to force Portfolio to re-establish venue mappings after startup?

Working Fresh Start:
The system works perfectly on fresh startup without cached positions - the venue mapping is established correctly during live account announcements.

Workaround Attempted:
Currently clearing Redis cache (FLUSHALL) before each restart, but this defeats the purpose of persistence.

Any guidance on the proper AccountId format or startup sequence to ensure Portfolio venue mapping works with cached positions would be greatly appreciated!

---

#### [2025-12-19 12:45:59] @faysou.

use the develop version, a lot of improvements have been done to the reconciliation including with redis

---

#### [2025-12-19 12:46:15] @faysou.

the version you use is old at this stage

---

#### [2025-12-19 13:34:36] @gabadia5003

Thanks, will give it a try.  I believe there is a new version being released this week ?

---

#### [2025-12-19 13:35:31] @faysou.

I don't know

---

#### [2025-12-19 13:35:56] @faysou.

If I were you I would just use the develop version

---

#### [2025-12-20 09:51:45] @conayuki

hello again, I did more testing on my side:
I plotted the bottom 2 rows of Order(screenshot1) on a candle chart(screenshot2, the dotted line shows the trade). Shouldn't the SELL order(2nd last row) satisfy the `normal move-through` case? It however filled at the candle low. trigger_price: 25113.31 avg_px: 25080.5.
I also observed that all my other orders are filled at exact open high low close prices. (limit orders are filled with negative slippage at the best price the bar can provide, kind of a look-ahead bias).

maybe I should just switch to tick data, but then it will slow down the backtest by a lot I suppose.

**Attachments:**
- [2025-12-20_5.33.41.png](https://cdn.discordapp.com/attachments/924506736927334400/1451874710882226309/2025-12-20_5.33.41.png?ex=694a6631&is=694914b1&hm=130646159cfa1f7b9abe3b94a0f4d1d77beef9838b7119aa488ca2a2daf9cc4d&)
- [2025-12-20_5.34.44.png](https://cdn.discordapp.com/attachments/924506736927334400/1451874711310176391/2025-12-20_5.34.44.png?ex=694a6631&is=694914b1&hm=bd9e376ad01d09aa2294291afac99cbd9b0dfdbb785a266d19334a0634a04ce6&)

---

#### [2025-12-20 09:52:22] @conayuki

the above test is run on:
```uv pip show nautilus-trader
Name: nautilus-trader
Version: 1.222.0a20251219```

---

#### [2025-12-20 09:53:39] @conayuki

the first order is a sell stop-market and the second order is a buy stop-market.

---
