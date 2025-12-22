# NautilusTrader - #help

**Period:** Last 90 days
**Messages:** 309
**Last updated:** 2025-10-23 04:00:15

---

#### [2025-07-26 20:07:48] @melonenmann

In https://nautilustrader.io/docs/latest/concepts/data#historical-data-requests-with-aggregation the example shows
self.request_bars(BarType.from_str("6EH4.XCME-1-MINUTE-LAST-EXTERNAL"))

In my strategy I create an aggregated 1W bartype
self.bar_type_1week = BarType.from_str(f"{self.config.instrument_id}-1-WEEK-LAST-INTERNAL")

And then I  want to request these
self.request_bars(self.bar_type_1week)

--> ValueError: The actor has not been registered

I also added the "@{instrument_id}-30-MINUTE-LAST-EXTERNAL" to the weekly bartype

And I also tried
self.request_aggregated_bars(self.bar_type_1week)

But this is not working as I need a list_bar and not BarType, is the example wrong or outdated?

**Links:**
- NautilusTrader Documentation

---

#### [2025-07-26 21:18:51] @faysou.

Yes request_aggregated_bars requires a list as argument, I'll update the doc

---

#### [2025-07-26 21:32:46] @faysou.

There's an examples folder in the repository, I recommend you to have a look at it

---

#### [2025-07-27 07:40:24] @melonenmann

thanks, found it

---

#### [2025-07-29 06:23:57] @melonenmann

I guess I do not get the concept.
Here is what I want: I have m30 data (2025-01-01 -> 7 month length) and load this in to the engine. 
My simulation shall start 12 weeks after 2025-01-01.
I aggregate to 1W bars and subscribe --> this is working and I receive all 1W bars from 2025-03-31
Now the problem:
I want to get the historical 1W bars beginning from 01.01.  (that I can calculate things an the 12 weeks of data)
` 
        self.bar_type_1week = BarType.from_str(f"{config.instrument_id}-1-WEEK-LAST-INTERNAL@30-MINUTE-EXTERNAL")
        self.bar_type_1week_for_match = BarType.from_str(f"{config.instrument_id}-1-WEEK-LAST-INTERNAL")

        self.request_aggregated_bars([self.bar_type_1week_for_match])
`

code is attached

**Attachments:**
- [barstrategy.py](https://cdn.discordapp.com/attachments/924499913386102834/1399638563313946705/barstrategy.py?ex=68fa72bd&is=68f9213d&hm=0d1d8f94f3bb0fa1f35245020d4131824b62348884bf2f61432cc8e87a31ab6c&)
- [run_example.py](https://cdn.discordapp.com/attachments/924499913386102834/1399638563682779196/run_example.py?ex=68fa72bd&is=68f9213d&hm=0fe3b73047cfc77db10ddd0918007a135419a01630c2cc4a8172511453a81c4c&)

---

#### [2025-07-29 09:28:13] @faysou.

You need to request aggregated bars for self.bar_type_1week. Also self.bar_type_1week_for_match = self.bar_type_1week.standard()

---

#### [2025-07-29 09:30:52] @faysou.

If you subscribe or request aggregated bars for the match version it will generate aggregators for quote or trade ticks (quotes if bid or ask or mid, trades if last)

---

#### [2025-07-29 09:32:02] @faysou.

When the bar type contains an @ it's a syntax to define a bar type from another bar type. That's a functionality that was missing and I added it about a year ago.

---

#### [2025-07-29 11:01:43] @melonenmann

This is still not working
`        self.request_aggregated_bars([self.bar_type_1week_for_match, self.bar_type_1week])  # , start=self.hist_start, end=self.config_now);

        # Subscribe to market data
        # This tells NautilusTrader what data we want to receive in our on_bar method
        # Without this subscription, we won't receive any market data updates
        self.subscribe_bars(self.bar_type_30min)
        self.log.info(f"Subscribed to {self.bar_type_30min}")

        # Aggregated 1-week bar data

        # Start receiving 1-week bar updates (created from 30-minute external data)
        self.subscribe_bars(self.bar_type_1week)
        self.subscribe_bars(self.bar_type_1week_for_match)
`

---

#### [2025-07-29 11:01:46] @melonenmann

Log:
`2025-03-26T21:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: [REQ]--> RequestTradeTicks(instrument_id=EUR/USD.SIM, start=None, end=None, limit=0, client_id=None, venue=SIM, data_type=TradeTick, params={'bar_type': BarType(EUR/USD.SIM-1-WEEK-LAST-INTERNAL), 'bar_types': (BarType(EUR/USD.SIM-1-WEEK-LAST-INTERNAL), BarType(EUR/USD.SIM-1-WEEK-LAST-INTERNAL@30-MINUTE-EXTERNAL)), 'include_external_data': False, 'update_subscriptions': False, 'update_catalog': False, 'bars_market_data_type': 'trade_ticks'})
2025-03-26T21:00:00.000000000Z [WARN] BACKTEST_TRADER-001.DataEngine: _handle_aggregated_bars: No data to aggregate
2025-03-26T21:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: [CMD]--> SubscribeBars(bar_type=EUR/USD.SIM-30-MINUTE-LAST-EXTERNAL, await_partial=False, client_id=None, venue=SIM)
2025-03-26T21:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: Subscribed to EUR/USD.SIM-30-MINUTE-LAST-EXTERNAL
2025-03-26T21:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: [CMD]--> SubscribeBars(bar_type=EUR/USD.SIM-1-WEEK-LAST-INTERNAL@30-MINUTE-EXTERNAL, await_partial=False, client_id=None, venue=SIM)
2025-03-26T21:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: [CMD]--> SubscribeBars(bar_type=EUR/USD.SIM-1-WEEK-LAST-INTERNAL, await_partial=False, client_id=None, venue=SIM)
2025-03-26T21:00:00.000000000Z [INFO] BACKTEST_TRADER-001.WHLStrategy: Subscribed to EUR/USD.SIM-1-WEEK-LAST-INTERNAL@30-MINUTE-EXTERNAL`

---

#### [2025-07-29 12:44:57] @faysou.

Try to make an existing example work and then modify it until yours works.

---

#### [2025-07-29 12:45:58] @faysou.

You can also clone the repository and add some log statements to see which code is reached.

---

#### [2025-07-29 12:46:28] @faysou.

Use make build-debug to recompile cython code.

---

#### [2025-07-29 12:54:07] @faysou.

For request bars, you need to use a datacatalogconfig. I recommend you to use the high level api like in here https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/backtest/notebooks/databento_test_request_bars.py

---

#### [2025-07-29 14:36:52] @helo._.

I noticed that many of the working codes are missing.
For example, when i see PerContractFeeModel, get_commission() function is empty. In fact, the vast majority of functions just do "pass"
Are they all supposed to be null function? If not, where can I see the actual code for those functions?

---

#### [2025-07-29 14:50:33] @faysou.

You must be using intellijidea and looking at some stub code from intellijidea. Make sure you open a pyx file.

---

#### [2025-07-29 15:04:07] @colinshen

Hi, Binance kline stream sends bar data during interval(1m), on_bar receives data after interval. Can I get the bar data when streaming?

---

#### [2025-07-29 15:22:11] @faysou.

No

---

#### [2025-07-29 15:24:23] @helo._.

Thanks for your answer!
Is it possible for intellij to go to .pyx file definition instead? It would be very unfortunate if I have to manually search/open the .pyx file, then go to definition there.

---

#### [2025-07-29 15:24:50] @faysou.

I don't know, I don't think so

---

#### [2025-07-29 15:32:27] @colinshen

Thanks,I will use trade_tick

---

#### [2025-07-30 18:36:42] @southwall01

Hey guys, when I run run_tardis_machine_replay(), I got this error: 
```
thread 'tokio-runtime-worker' panicked at C:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f\tokio-1.46.1\src\runtime\scheduler\multi_thread\mod.rs:86:9:
Cannot start a runtime from within a runtime. This happens because a function (like `block_on`) attempted to block the current thread while the thread is being used to drive asynchronous tasks.
```
I'm wondering how to solve this. Here is my python code:
```
import asyncio

from dotenv import load_dotenv

from nautilus_trader.core import nautilus_pyo3


async def run():
    await nautilus_pyo3.run_tardis_machine_replay(
        config_filepath="./config/tardis_config.json"
    )


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run())
```

---

#### [2025-07-31 03:30:51] @cjdsellers

Hi <@1205331489328472064> 

Which version are you on? I think this one was fixed recently

---

#### [2025-07-31 04:38:21] @southwall01

I’m using latest version 1.219.0

---

#### [2025-07-31 07:38:33] @cjdsellers

Understood, this is fixed on `develop` branch in 1.220.0, which will be release soon (possibly this week, but TBD)
You could also install via a development wheel (see README)

---

#### [2025-08-02 03:33:04] @k33gan_

Hey everyone! I have a question on how to solve something that seems to be eluding me these past couple of days. I have been attempting to develop a market screener that utilizes 1-minute external bar types from the catalog to generate a correlation matrix. However, when I attempt to load all equity instruments from the XNAS venue, the process returns an error.
```
(field("bar_type") == "ZZZ.XNAS-1-MINUTE-LAST-EXTERNAL-EXTERNAL")': maximum recursion depth exceeded during compilation)
Traceback (most recent call last):
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/config.py", line 99, in parse_filters_expr
    return eval(s, allowed_globals, {})  # noqa: S307
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
RecursionError: maximum recursion depth exceeded during compilation
```

---

#### [2025-08-02 03:33:12] @k33gan_

```
During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/node.py", line 455, in run
    result = self._run(
             ^^^^^^^^^^
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/node.py", line 494, in _run
    self._run_oneshot(
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/node.py", line 594, in _run_oneshot
    result: CatalogDataResult = self.load_data_config(config, start, end)
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/node.py", line 637, in load_data_config
    config_query = config.query
                   ^^^^^^^^^^^^
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/config.py", line 315, in query
    "filter_expr": parse_filters_expr(filter_expr),
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/keegan/Strategy/.venv/lib/python3.12/site-packages/nautilus_trader/backtest/config.py", line 102, in parse_filters_expr
    raise ValueError(f"Failed to parse filter expression '{s}': {e}")
```

---

#### [2025-08-02 03:33:25] @k33gan_

To give a little more information.
```When I limit the number of instruments to load, my code works perfectly as intended. 
I am running on WSL Ubuntu-24.04 for Windows 11
I am running Python 3.12.3
I am utilizing the latest version of NT```

My best guess is:
```A. I am implementing it wrong somehow (Most likely).

B. It is a hard Python constraint, see https://stackoverflow.com/questions/14222416/recursion-in-python-runtimeerror-maximum-recursion-depth-exceeded-while-callin. 

Though changing the sys.setrecursionlimit(n) to a high number does not seem to be working.```

Any help is much appreciated! It's probably something simple I have overlooked, so sorry in advance if that is the case.

**Attachments:**
- [strategies.py](https://cdn.discordapp.com/attachments/924499913386102834/1401045199634829333/strategies.py?ex=68faf385&is=68f9a205&hm=149c3f5ab77e199346b8c71a8f5713f1f20302dbee07f8c30ec67af7114f6305&)
- [run_strategy.py](https://cdn.discordapp.com/attachments/924499913386102834/1401045199953723414/run_strategy.py?ex=68faf385&is=68f9a205&hm=ce3b2dc8335139aa6c6c66baa59703d883fb8565355f944457e129d76526da81&)

---

#### [2025-08-02 16:19:25] @captainahab10

Two issues are stopping my strat from running.
cant use perps on binance/okx/bybit (NZ regulation i think)
binance spot fee: https://github.com/nautechsystems/nautilus_trader/issues/2689
when close_all_positions is called the sizes are different becuase no fee is applied so it doesnt close becuase the spot amount is less than what NT thinks.
That leaves dydx perps on fill i get the error: 
Failed to parse subaccounts channel data: {"type":"channel_data","connection_id":"  Object contains unknown field builderFee - at $.contents.fills[0]

**Links:**
- Commission not applied to position for crypto spot exchanges · Iss...

---

#### [2025-08-03 07:24:39] @.davidblom

<@342191223282597889> the dYdX issue is fixed in pull request #2824

---

#### [2025-08-05 06:21:45] @melonenmann

Finally I found out why the aggregated request are not working. I had to add the catalog to the BacktestEngineConfig.
But now there are a two questions.
1.) in the catalog are M30 bars, why do I have to put the bars as data additionally (with engine.add_data(filtered_bars))?
2.) one try was to add the W1 data also to the catalog (before I solved the problem), but when the aggregated data was working the external data was used instead of the internal/aggregated (-> with parameter include_external_data=False and True) -> not really a problem, I deleted the W1 data again

---

#### [2025-08-05 06:25:09] @quantumgirly_25

I am constantly getting this error
symbol not found in flat namespace '_CFRelease'
when I trying to run my option strategy. I have MacOS M4chip processor.

please help
even when i am installing nightly version

---

#### [2025-08-05 08:41:07] @cjdsellers

Hi <@1402154856294256701> 
Try setting the `PYO3_PYTHON` env var per this: https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#from-source
I hope that helps!

---

#### [2025-08-05 10:46:27] @haakonflaar

When subscribing to and requesting aggregated bars in a strategy I receive bars for time periods where no trade was made (no existing bars for the underlying bar type). This includes bars when the market is closed as well as during weekends and holidays. All bars are single price (Open=High=Low=Close). Is there a way to only receive aggregated bars for periods with existing bars for the underlying bar type?
Example:
```
bar_type_str = "MNQ.SIM-1-HOUR-LAST-INTERNAL@1-MINUTE-EXTERNAL"
bar_type = BarType.from_str(bar_type_str)
```
Strategy code `on_start`:
```
# Warm up indicators with history data
self.request_bars(
    self.config.bar_type,
    start=self._clock.utc_now() - pd.Timedelta(days=10),
)
# Subscribe to live bars
self.subscribe_bars(self.config.bar_type)
```

---

#### [2025-08-05 10:48:05] @haakonflaar

I am also wondering how to query aggregated bars from the catalog, as this does not work:
```
bar_type_str = "1-HOUR-LAST-INTERNAL@1-MINUTE-EXTERNAL"

bar_data = catalog.query(
    data_cls=Bar,
    identifiers=["MNQ.SIM"],
    metadata={"bar_type": bar_type_str},
    start="2023-01-01",
    end="2023-12-31",
)
```

---

#### [2025-08-05 16:20:56] @backroom_moonshine

I'm working through teh Backtest (low-level API)  getting started guide and hitting a snag `provider = TestDataProvider()
trades_df = provider.read_csv_ticks("binance/ethusdt-trades.csv") Jupyter Labs returns `

"Couldn't find test data directory, test data will be pulled from GitHub" i then get an error "FileNotFoundError: https://raw.githubusercontent.com/nautechsystems/nautilus_trader/develop/tests/test_data/binance/ethusdt-trades.csv" i have found the correct datafile but not in nautilus_trader/develop/. Is there a way to manually load this using TestDataProvider. Reading csv with pandas causes isuues with format later on

---

#### [2025-08-05 16:22:44] @backroom_moonshine

is there a reason its not looking here nautilus_trader/tests/test_data/binance/ethusdt-trades.csv

---

#### [2025-08-05 23:08:59] @daws6561

Did you experience a similar error on the previous tutorial, FX Bar Data? (asking because I did, and had the same question).

---

#### [2025-08-06 01:02:38] @quantumgirly_25

Thank you, I will try this approach

---

#### [2025-08-06 06:55:51] @lpoems_86721_19126

After enabling features such as historical order cleanup, NT continues to accumulate memory, though the growth is slower...

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1402545692869656656/image.png?ex=68fa7a37&is=68f928b7&hm=f0adece1b7e7770aefe004193f84c26ba45d90591ed53ca44fb070ed869169ce&)

---

#### [2025-08-06 07:03:07] @cjdsellers

Hi <@1208715992122007564> 
Thanks for the feedback, this could be account state events as we don't purge those yet. There are also some reference cycle type leaks as well, growth is much slower than it was and we continue to work to address them

---

#### [2025-08-06 07:05:13] @lpoems_86721_19126

Thank you for your reply🙏

---

#### [2025-08-06 09:28:27] @backroom_moonshine

no i havent done that one yet. I couldnt work it out, so i tired importing the data from csv as per the high level backtest in quickstart and it seems to be ok

---

#### [2025-08-06 16:25:41] @premysl_22228

What is your total amount of memory please, so we know, what total amount of leaks happens per day during live trading?

---

#### [2025-08-06 16:35:45] @premysl_22228

We are not aware (or at least me) of any circular dependency which are not cleaned during trading itself (if you are not doing some exotic things like repeatedly fetching historical trades during trading). There are lot of them, which aren't cleaned after, but I would rather account this to account state events, or some other type of leak. There is a possibility these will go away, after we go through Valgrind output debugging (which will be hopefully soon).

---

#### [2025-08-06 20:39:39] @ido3936

Hello smart people,

I am puzzled by a seeming inconsistency:
Shouldn't the realized PnL of a backtest run (as reported in the 'post run evaluation')  approx. equal the sum of PnLs in the positions report (assuming no open positions left)?

When my data (bars) are aggregated internallly - I get exactly this. 

When the data is aggregated externally - I get that this is not the case (and I mean **really** not the case) - the sum of position PnLs is much higher than the  realized PnL as reported in the 'post run evaluation'.

What could be the reason for this?
Any explanation would be most appreciated

---

#### [2025-08-07 00:07:56] @premysl_22228

Hi. No picture was attached. Can you send them? 

If sum(PnL) != total_PnL, after all positions being closed, it seems like major bug. I guess basic functionality being unit tested (even I am not sure in the case), so there will be probably some deeper pathology - my guess would be, that Portfolio PnL got somehow diverged from PnL in positions in caches. Could you submit MRE to the GitHub please?

---

#### [2025-08-07 00:12:49] @premysl_22228

If this is true positive, it's great inspiration for future testing. Assert that sum(PnL) is equal to what is in portfolio PnL in acceptance tests and possibly more further tests in yet unknown location, because bad computed PnL is really something we want to avoid...nothing much matters if basic functionality like this doesn't works properly.

---

#### [2025-08-07 07:24:24] @quantumgirly_25

Hi, I want to do backtest for my Optionpricing strategy, and i have written the startegy.py file and a YAML cofig file, But i am not able to have CLI for Nautilius-trader installe,

On running this command
naut backtest run backtest_config.yaml
i am getting error, naut command not found

I checked the examples for backtest on github, they are done using .py files only, so please help me on this, should I follow the github examples or is there a way to setup CLI for Nautilis-Trader

---

#### [2025-08-07 08:08:29] @ido3936

Hi <@1353826739851362345> , here's what I could quickly gather in terms of logs and explanations. 

```
  VERSIONING
 =========================
 nautilus_trader: 1.219.0
 python: 3.12.7
 numpy: 2.3.1
 pandas: 2.3.1
 msgspec: 0.19.0
 pyarrow: 20.0.0
 pytz: 2025.2
 uvloop: 0.21.0
```

My strategies use dual time frames: hours and days.
Hour bar types are the likes of  `ASX.NYSE-1-HOUR-LAST-EXTERNAL`
Day bars are either the likes of `ASX.NYSE-1-DAY-LAST-EXTERNAL`, or `ASX.NYSE-1-DAY-LAST-INTERNAL@1-HOUR-EXTERNAL` , the latter based on the above mentioned hour bars.

In both cases the sum of realized PnLs from the positions report is ~10_000$

But the post run reports are:
For the external hour bars:
```
 Total positions: 3_334
 [36m==========================================
 [36m SimulatedVenue NYSE
 [36m==========================================
 CashAccount(id=NYSE-001, type=CASH, base=USD)
 [36m------------------------------------------
 Balances starting:
 29_000.00 USD
 [36m------------------------------------------
 Balances ending:
 29_713.89 USD
```

and for the internally aggregated bars it is:
```
Total positions: 3_343
[36m==========================================
[36m SimulatedVenue NYSE
[36m==========================================
CashAccount(id=NYSE-001, type=CASH, base=USD)
[36m------------------------------------------
Balances starting:
29_000.00 USD
[36m------------------------------------------
Balances ending:
39_034.21 USD
```

(note that the number of postiions is more or less the same)

I hope this helps - I'm not sure how a minimally reproducible scenario would be devised here

---

#### [2025-08-07 11:01:19] @premysl_22228

Hi, I will try to extend the tests whether we can replicate this on acceptance testing (hopefully I get to this in few days, I am being very busy at the moment). And it looks like I there is furher bugs waiting for me in aggregation (I am currently working on a refactor with one unfinished test, which should catch exactly this kind of bug). But if I can't replicate it, there is nothing more I can do for you without the MRE at the moment.

---

#### [2025-08-07 11:04:43] @premysl_22228

(Out of the log it seems that ticks ->B -> C isn't equivalent to ticks -> C...I think the transformation at NYSE will be much more likely to be bugless then our own - are you running on official data without altering them any way just to be sure?)

---

#### [2025-08-07 11:05:00] @premysl_22228

<@1074995464316928071>

---

#### [2025-08-07 16:19:53] @ido3936

Hi, I will try to extend the tests

---

#### [2025-08-09 00:34:01] @_missing

So I still have a problem with market fills at weird prices like this when I run a backtest:
`2024-03-08T12:48:21.700000000Z [DEBUG] BACKTEST-NQ-001.OrderMatchingEngine(CME): Market: bid=1 @ 18520.25, ask=1 @ 18520.25, last=73.51
2024-03-08T12:48:21.700000000Z [DEBUG] BACKTEST-NQ-001.OrderMatchingEngine(CME): Applying fills to MarketOrder(SELL 1 NQM4.CME MARKET GTC, status=SUBMITTED, client_order_id=O-20240308-124821-001-001-36, venue_order_id=None, position_id=None, tags=None), venue_position_id=None, position=Position(LONG 1 NQM4.CME, id=NQM4.CME-OBStrat-001), fills=[(Price(73.51), Quantity(1))]`,  where there's no way the last trade price exists, and checking it against the tick data I generate, the value doesn't exist so not sure where its coming from since I have bar_execution disabled. 

Not sure if what I'm missing in the config but idk how this state is even possible, am I missing a setting in the configuration or something?

**Attachments:**
- [Screenshot_From_2025-08-08_20-24-37.png](https://cdn.discordapp.com/attachments/924499913386102834/1403536766971150366/Screenshot_From_2025-08-08_20-24-37.png?ex=68fac979&is=68f977f9&hm=028b12f050ef305a379e5dd0611067d8003ce98d3da0a0816d6f98a31ad22b03&)

---

#### [2025-08-09 00:35:10] @cjdsellers

Hi <@160288448958300161> 
Are you using latest `develop` branch? there was an unfortunate overflow bug found and fixed (next release will be soon)

---

#### [2025-08-09 00:35:54] @_missing

Uhhh no I think I'm still on 1.219, I can def swap over

---

#### [2025-08-09 00:37:36] @cjdsellers

This is an easier way of installing development wheels: https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#installation-commands

---

#### [2025-08-09 00:46:56] @_missing

ah alright this seems to have fixed it, thank you so much!

---

#### [2025-08-09 01:52:21] @eclipsephage

Hai guys.  So I'm still devving on 1.219.  Are we at a place where we can go with the Rust implementation yet? (on windows and linux).  I dont want to go too far with .219 if we're fundamentally good with the newer stuff (production/live-trade-wise)

---

#### [2025-08-09 02:07:35] @cjdsellers

Hi <@307301397609840640> 
The Rust core is being used by the current "production" `nautilus_trader` v1 package. A full cut-over is still months away, so you're not expending any wasted efforts building on top of 1.219.0. The API for v2 will be as similar as possible

---

#### [2025-08-09 02:08:31] @eclipsephage

roger. thanks

---

#### [2025-08-09 13:19:25] @eclipsephage

What do we lose by devving in Windows vs. Linux?  So far I can see I dont have uvloop.

---

#### [2025-08-10 12:48:30] @ayoze5798

Hello,

I wanted to contribute to this project, and I found this issue: https://github.com/nautechsystems/nautilus_trader/issues/1082

Since I didn't contribute to the project previously, I can't comment on the issues. Chris said here that a new field, price_protection / protection_points, should be added to the struct of the relevant order types.

I checked the provided documentation and saw that this is not a value the user enters. This is something that the exchange sets as a limit stop limit and stop market. Because of that, when submitting an order, this parameter can't be entered. In the execution reports received from the exchange, this parameter is calculated and set in the limit price field.

Can you check <@757548402689966131>

**Links:**
- Price protection for market and stop-market type orders · Issue #1...

---

#### [2025-08-12 22:55:08] @neupsh

hello, I am new to nautilus (and to algorithmic trading). Is there any good examples of using nautilus trader to backtest and live trade Futures contract? I was trying to find examples for popular ones like using ES historical data to backtest strategies, and then use it to live trade for MES. 
What is the best way to do that with IBKR integration?
So far, I was able to download the historical Bar data from IBKR, convert it to continuous back-adjusted data outside of nautilus.
Then load the back-adjusted data with bar wrangler in nautilus and run through a simple strategy.  Is there a better way to do this? I saw some old discussions [here](https://github.com/nautechsystems/nautilus_trader/discussions/935) and [here](https://github.com/nautechsystems/nautilus_trader/issues/1105) but I could not figure out what was done to support Futures (continuous) since then.

**Links:**
- Continuous futures instrument · nautechsystems nautilus_trader · ...
- Support for continuous futures contracts · Issue #1105 · nautechs...

---

#### [2025-08-13 07:12:36] @cjdsellers

Hi <@488137949838573568> 
Welcome and thanks for reaching out.

There are no good tutorials for futures outlining what you've figured out already. You're on the right track using wranglers to add data directly to a `BacktestEngine`. You could also consider using the high-level API where you can write Nautilus data to a Parquet data catalog https://nautilustrader.io/docs/latest/getting_started/backtest_high_level, this would be more efficient for repeated backtests on the same data.

For continuous contracts, people are either leveraging Databento or rolling their own handling for that - there is nothing built in (yet). I say "yet", because it would definitely be valuable but would require community contribution at this stage. There are those GH discussions you have found already.

I hope that helps a little!

---

#### [2025-08-13 09:16:37] @cjdsellers

Hi <@1012054021944656032> 

Welcome and thanks for reaching out offering to help!

This would be a great feature. I agree that the protection points are not "user-defined" but would be part of the venue configuration, e.g. `price_protection_points` being `None` by default.

Then we could have some kind of `price_protection` boolean flag for the market orders. This could be passed through when orders are submitted live, and simulated for backtesting where venues support it. The CME MDP3.0 spec would be a good reference here I think?

---

#### [2025-08-14 16:01:32] @qumn123

I'm curious about how this issue was resolved. I've encountered similar problems myself, but haven't been able to fix them yet. thanks a lot 🙏

---

#### [2025-08-15 03:37:05] @.xingtao

who know why log this: data_queue at capacity (100_000/100000), scheduled asynchronous put() onto queue

---

#### [2025-08-15 21:00:28] @ido3936

I gave up on redis as a means for controlling NT. Instead I set up an http server that has access to the message bus.
The server gets instructions from an http client, and distributes them to strategies using the bus

---

#### [2025-08-16 00:51:41] @premysl_22228

This is a little bit important for me, as I still want to control NT by Redis and message bus outside it... Why you gave up? What didn't work?

I am not eager to run http server or do other hacks as GIL kills the trading during Python http server script execution. And I don't see all consequences of possible race conditions. Does it work fine? No long freezes in trading during page loading?

---

#### [2025-08-16 01:30:22] @yfclark

maybe HTTP server in rust？I am consider about expose web endpoint for Nautilus so that it can interact with other program

---

#### [2025-08-16 02:16:25] @premysl_22228

It is question, whether there will be API, which will enable user to avoid race conditions. Hopefully it will be addable (it will be necessary to lock the core during the other thread doing its staff).

---

#### [2025-08-16 06:00:17] @ido3936

as to why I gave upon it: see here https://discord.com/channels/924497682343550976/949809536108228609/1393145437007122483

as to server blocking - I use `aiohttp` and the server is running on a different thread (not because it was slow, but due to event loop issues). I have not had an issue with this setting so far

---

#### [2025-08-16 07:12:01] @premysl_22228

This makes sense, but I am still worried a lot, something gets broken/corrupted/...when I see, how things are fragile. GIL is a friend in the current situation since it is locking the Python part of NT core, otherwise you would face race conditions, I think.

I also saw setup, where synchronous requests to HDD were made out of backtest to control/get data of backtest/live environment. 

These are all, I think, hacks to the current design. I was thinking a lot, whether there shouldn't be something like async actor, but it would complicate a lot of things a lot. I am trying to make get rid of all async behavior inside core (there are some cases, I described in RFCs), when you get async even through you would expect sync. I might have found a way (it will be one large ugly breaking change later, to get rid of request+subscribe combination to one command, which handles everything including buffering ticks/bars, which are now discarded, if Chris agrees). 

I think the http should always run in other process, communicating by message bus, in the current design, to not get broken anything.

---

#### [2025-08-16 15:37:57] @ido3936

I did not know that the message bus provides cross processs communication. In my case I only made sure to be running the http client through a different process (to the one running NT+http server)

---

#### [2025-08-16 15:40:44] @ido3936

<@1353826739851362345> one more thing that I'm reminded of: try as I might, I could not get the redis->NT communication channel to operate. There are sopme specific requirements for the topic etc, and as documentation is missing, I tried to get it rightr by trial and error (and failed).
In short - documentation for this possible approach is lacking (non existent AFAIK...)

---

#### [2025-08-16 15:56:58] @gz00000

Or you could try using a more lightweight solution like ZeroMQ instead of Redis?

---

#### [2025-08-16 17:22:16] @premysl_22228

Yes, documentation is unfortunately lacking. There are other subprojects which are prioritized over it.

Could you send me, what error it shows? 

I would also recommend to browse the source code with AI (or without it), it might tell you the requirements you are missing, if you give it the error and give it same information like you told me now.

---

#### [2025-08-16 19:09:04] @ido3936

`Could you send me, what error it shows? ` - no error message, it just wouldn't work

`I would also recommend to browse the source code with AI (or without it),` - absolutely, I do this all the time

---

#### [2025-08-17 19:43:44] @melonenmann

I'm struggling again with some points, some hints would be nice. AI is generating always useless stuff.
1. Is there a possibility to display the trades in a graphical way? 
2. Is there a risk calculation helper? (Fixed risk amount, outcome: quantity)
3. How can I create my custom reports?

---

#### [2025-08-17 21:00:33] @premysl_22228

Hi. To 1). Yes. If I get approval from <@416743722416472075>, I or him will share the code. Can I post it publicly? He has done a nice piece of work on this. (hopefully it will still work, it is few months old)
I won't answer to 2., as I am not sure, what you mean. Could you elaborate?
To 3., if I get approval, the code includes custom reports.

---

#### [2025-08-17 21:25:54] @melonenmann

1. Sounds nice, that would save me some time
2. Perhaps it's too easy that something exists. I meant, input is risk($) and SL ticks and you will get the quantity for the instrument as output.
3. I Found out that I can access, engine.trader._cache.orders but python makes it not very convenient to find all Infos, but I'll keep debugging

---

#### [2025-08-17 22:27:10] @premysl_22228

It's up to Stefan. Maybe he will DM you with it. 

I will later create a similar thing inspired by Stefan code, that should be sharable. (As soon as I need it to do something) Search in the forum history if you want to know, how it looks like for an inspiration.

---

#### [2025-08-18 04:15:40] @colinshen

Hi, I'm trying to backtest the Binance tickdata, I already save to 2M data into catalog. However, loading data need a lot of memory. I tried to load 3 or 4 days data(the average data per day is about 200M-250M) and the memory usage was up to 16G. Is there a way to load the data on demand?

---

#### [2025-08-18 04:27:27] @cjdsellers

Hi <@175701522644992000> 
Yes, try setting a `chunk_size` to enable streaming mode https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/backtest/config.py#L427. Which version are you on btw?

---

#### [2025-08-18 04:28:48] @colinshen

1.220.0a20250728

---

#### [2025-08-19 15:33:06] @colinshen

Hi, I just tried what you side..but I'm not sure why I get error `BACKTESTER-001.BacktestEngine: Requested instrument_ids=[InstrumentId('ETHUSDT.BINANCE'), InstrumentId('ETHUSDT-PERP.BINANCE_FUTURES')] from data_config not found in catalog` 
```
   data_configs = [
        BacktestDataConfig(
            catalog_path=str(CATALOG_PATH),
            data_cls=TradeTick,
            instrument_ids=[spot_instrument_id, futures_instrument_id],
            start_time=start,
            end_time=end,
        )
    ]
```
I could use ParquetDataCatalog.query to get data.

---

#### [2025-08-19 15:56:00] @colinshen

I found backtestengine.run also support stream `un(streaming=True)`, does this is as same as the chunk_size?

---

#### [2025-08-19 22:00:06] @cjdsellers

Hi <@175701522644992000> 
Yes, instruments associated with your market data need to be persisted in the catalog.

> I found backtestengine.run also support stream un(streaming=True), does this is as same as the chunk_size?
Yes, the `BacktestNode` is using the `streaming` functionality of `BacktestEngine.run` under the hood, as per the docstring

---

#### [2025-08-20 04:10:27] @colinshen

Hi @colinshen

---

#### [2025-08-20 09:53:12] @chaintrader

I have custom indicators

---

#### [2025-08-20 09:53:27] @chaintrader

How can I implement into Nautilus trader

---

#### [2025-08-20 12:11:35] @ido3936

I want to have uv install the develop branch (using uv add, to have a proper pyproject.toml) 
I tried `uv add git+https://github.com/nautechsystems/nautilus_trader --branch develop   ` and got an error:
`FileNotFoundError: [Errno 2] No such file or directory: 'clang'`

Using uv pip install I manage to install the branch w/o a problem. What am I doing wrong?

---

#### [2025-08-21 07:40:37] @cjdsellers

Hi <@1074995464316928071> 
This first error is because you need the Clang compiler installed, probably because you're attempting to build from source with a direct dependency on head of `develop` branch.

The `uv pip install` succeeds as it'll be grabbing the pre-compiled binary wheel from PyPI

---

#### [2025-08-21 07:50:41] @ido3936

the problem with `uv pip install`  is that the pyproject file does not reflect it
I assume that there must be a way for `uv add` to mimic the `uv pip install` functionality no (i.e. avoiding the build)?

---

#### [2025-08-21 08:01:18] @faysou.

I suppose if you ask an LLM it will probably know the answer

---

#### [2025-08-21 08:01:22] @faysou.

for this

---

#### [2025-08-21 14:10:05] @ido3936

The question has been posed, and this is how the reply starts:
```Yes, uv add can mimic uv pip install for installing packages from a Git branch without rebuilding, but the behavior depends on the specific use case and the package's configuration.```
I suppose its one of those cases where dev inside knowledge can really help

---

#### [2025-08-21 15:42:58] @premysl_22228

What prompt did you exactly put into what LLM? After putting the conversation into mine, the hallucinations were pretty limited and told me exactly, what you are doing wrong in the conclusion. 

You just need to build the project, the develop branch doesn't contain any build artifacts.

---

#### [2025-08-21 15:45:51] @ido3936

I don't really want to build it - it has a rather complex process
I posed the question because I saw that uv pip install manages to install w/o building, but it is not as 'orderly' as uv add (which updates the pyproject file and maintains locks on package versions)

---

#### [2025-08-21 15:47:22] @premysl_22228

Then add there package itself from nightly or PyPI repo, if you don't want to rebuild.

---

#### [2025-08-21 15:49:01] @faysou.

You should build the develop branch, I do it all the time

---

#### [2025-08-21 15:50:13] @faysou.

https://gist.github.com/faysou/7f910b545d4881433649551afce69029

**Links:**
- Install nautilus_trader dev env from scratch, using pyenv and uv

---

#### [2025-08-21 15:50:30] @faysou.

Use this, it's my up to date instructions, I literally use this when needed

---

#### [2025-08-21 15:50:45] @faysou.

pyenv allows the setup to work well with a debugger

---

#### [2025-08-21 15:51:35] @premysl_22228

He probably adds it as a dependency to other project. Makes not much sense to do this by building it.

---

#### [2025-08-21 15:52:05] @faysou.

But it makes sense to get the develop branch faster

---

#### [2025-08-21 15:54:18] @premysl_22228

Yes, you get latest commits, but you skip the nightly build checks (if there are some extra already in place...there will probably be) You prefer stability before other things when using it as a dep.

---

#### [2025-08-21 15:55:34] @premysl_22228

There are also dead places in develop branch, when CI/CD don't passes. Develop branch is good for development.

---

#### [2025-08-21 15:55:51] @premysl_22228

Of NT.

---

#### [2025-08-21 15:57:47] @premysl_22228

<@1074995464316928071>, what is your usecase?

---

#### [2025-08-21 15:58:53] @ido3936

I'm just a humble user - trying to utilize a stratgey that I backtested endlessly, usingNT and IB

---

#### [2025-08-21 16:01:51] @premysl_22228

Could you more elaborate please?

---

#### [2025-08-21 16:03:37] @premysl_22228

Where do you put your strategy file to run it?

---

#### [2025-08-21 16:05:44] @ido3936

You mean where so I run my setup from? A cloud provider

---

#### [2025-08-21 23:33:28] @cjdsellers

<@1074995464316928071> It's good to have the option of building from source if you need to. The README notes on this should work, or reference faysou's gist.

Otherwise, you can avoid that compile step by taking a dependency on [development wheels](https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#development-wheels), although these are subject to a finite retention (only latest `dev` wheel and last 30 nightly wheels), and only recommended for testing and dev - not running in production.

If you're using `uv` then you can specify the private package index:
```
[tool.uv.sources]
nautilus_trader = { index = "nautechsystems" }

[[tool.uv.index]]
name = "nautechsystems"
url = "https://packages.nautechsystems.io/simple"
```

Then in your dependencies:
```
dependencies = [
    "nautilus_trader==1.220.0a20250821",
```

---

#### [2025-08-22 10:59:04] @ido3936

Yay! I knew that there is a disciplined answer to  my question somewhere! Thanks <@757548402689966131>

---

#### [2025-08-24 12:10:48] @.xingtao

When I subscribe to many instruments, I’m already using a queue to send a request_bar every 200ms. However, Binance’s API rate limit still gets triggered. I suspect this might be because Nautilus’s message bus gets blocked when there are a large number of data reading tasks at the same time, which then causes the request tasks to be processed in batches, resulting in exceeding the API rate limit. How can I solve this problem?

---

#### [2025-08-25 10:05:57] @vinc0930

Hi, has anyone successfully installed the lib on Amazon Linux 2023 (EC2/AL2023)? 
I tried the two install commands from the README (PyPI and the project index with --pre), but both failed on AL2023. If you’ve got it working, could you share the exact steps. Thanks!

---

#### [2025-08-26 05:25:45] @haakonflaar

I ran into this interesting error message while running multiple backtests in parallel using the low-level API. Any idea why and a fix?

```
Traceback (most recent call last):
  File "/usr/lib/python3.12/concurrent/futures/process.py", line 263, in _process_worker
    r = call_item.fn(*call_item.args, **call_item.kwargs)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "src/utils/backtest_utils.py", line 467, in run_single_low_level_backtest
    raise e
  File "/src/utils/backtest_utils.py", line 390, in run_single_low_level_backtest
    engine = BacktestEngine(config=engine_config)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "nautilus_trader/backtest/engine.pyx", line 250, in nautilus_trader.backtest.engine.BacktestEngine.__init__
  File "/nautilus-algo-trading/libs/nautilus_trader/nautilus_trader/system/kernel.py", line 539, in __init__
    build_time_ms = nanos_to_millis(time.time_ns() - ts_build)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OverflowError: can't convert negative int to unsigned
```

---

#### [2025-08-26 09:48:49] @vinc0930

To specifically, on AWS (Amazon Linux 2023), `pip install -U nautilus_trader` in a clean venv fails with the error:
```subprocess.CalledProcessError: Command '['/home/infra/myproject/nautilus/bin/python3.12', 'build.py']' returned non-zero exit status 1.
      [end of output]

  note: This error originates from a subprocess, and is likely not a problem with pip.
  ERROR: Failed building wheel for nautilus_trader
Failed to build nautilus_trader
error: failed-wheel-build-for-install

× Failed to build installable wheels for some pyproject.toml based projects
╰─> nautilus_trader```

---

#### [2025-08-26 13:10:29] @christian.andresen

There must be more details in the error message that indicate the cause. 
I am not familiar with the AWS linux distributions, but I am somewhat surprised that the linux wheels cannot be found and a manual installation is attempted instead, which of course fails because some prerequisites are presumably not met.
Try `pip install --only-binary=:all: nautilus_trader` to enforce wheel installation.
Edit: The naked amazonlinux docker image has no python installed, so you must have done something beforehand? Where does this amazonlinux come from?

---

#### [2025-08-27 02:47:54] @vinc0930

There must be more details in the error

---

#### [2025-08-27 13:33:40] @d_dot_zk

I've had to completely drop my project from the QuantConnect's LEAN engine upon hearing that their engine cannot process moniker-based 0-DTE/Weekly Futures Options contracts. An example of this would be CME E-Mini S&P 500 Futures Options - E1A... E1B... (0-dte), EW1... EW3... (weeklies), EWQ... EWU... (monthlies/EOM), ESU5... ESZ5... (quarterlies). This is a base requirement for me, is Nautilus Trader able to process and handle data on these moniker-based Futures Options contracts?

---

#### [2025-08-27 15:00:52] @faysou.

Yes with the interactive brokers adapter

---

#### [2025-08-27 15:06:11] @helo._.

Is it possible to accelerate backtesting by allocating more RAM or CPU cores?

---

#### [2025-08-27 16:07:36] @d_dot_zk

just to confirm that was an answer directed towards me? That Nautilus Trader can process this data as long as i'm sourcing it through IBKR?

---

#### [2025-08-27 16:08:03] @faysou.

Yes

---

#### [2025-08-27 16:08:20] @d_dot_zk

thank you for that, I appreciate it highly

---

#### [2025-08-27 16:08:46] @faysou.

You can get histo and live data from databento as well

---

#### [2025-08-27 16:09:07] @faysou.

For now the only execution adapter for usual markets, not crypto, is IB

---

#### [2025-08-27 16:10:13] @faysou.

It's actually one of the reasons I started being interested in nautilus, support for IB and historical data.

---

#### [2025-08-27 16:10:58] @faysou.

And also the possibility to improve something existing rather than starting from scratch. Also the ongoing migration to rust with python bindings.

---

#### [2025-08-29 10:11:58] @faysou.

I've actually worked on this over the last year, to have IB and databento histo data compatible with instruments ids common between the two.

---

#### [2025-08-29 14:17:33] @d_dot_zk

huge achievement to say the least, it's crazy to me that QC who claim to be the SOTA industry standard for open-source algorithmic trading openly refuse to consider Weeklies on Futures Options a worthy endeveavour, which in today's world is the only data with real intrinsic value when it comes to U.S Stock market analysis. With this I can firmly say Nautilus Trader can take the top spot for open-source algo trading development, not only that but the usage of the Rust programming language aswell is just the cherry on top

---

#### [2025-08-29 14:24:07] @faysou.

What's currently being used is mostly cython but there's an active effort mostly done by <@757548402689966131> with the help of a few contributors for migrating to rust, so the library will indeed become the best open source solution without question.

---

#### [2025-08-29 14:25:58] @faysou.

I can comment on what I've done in the last year, I've been adding features I need in nautilus for options on futures, but have touched at many other aspects of the library as well.

---

#### [2025-08-29 14:26:39] @faysou.

Most users of nautilus are dealing more with cryptos, but personally I'm more interested in futures markets.

---

#### [2025-08-30 03:37:14] @yunshen8_47168

Hi, I'm trying to use `nautilus_pyo3.run_tardis_machine_replay` to create data catalogs directly from tardis machine replay. I'm using `book_snapshot_25_0ms `which should become `OrderBookDepth10 `according to the doc. But the data was somehow saved into OrderbookDeltas. How can I get OrderbookDepth10 using tardis machine?

I'm following this. https://nautilustrader.io/docs/latest/integrations/tardis#python-replays

---

#### [2025-08-30 06:39:03] @haakonflaar

<@757548402689966131>  Have you come across this one before? It doesn't happen all the time, and as of now it have only happened when I have run backtests in parallel.

---

#### [2025-08-30 06:41:29] @cjdsellers

Hi <@244099030156574730> 
I wouldn't recommend running more than one backtest in the same process

---

#### [2025-08-30 16:02:06] @zafaransari.

Is there any updated video tutorial available for beginners, explaining NautilusTrader concepts and showing how to build and back test strategies?

---

#### [2025-08-30 16:02:29] @zafaransari.

Or an article explaining the whole process step by step?

---

#### [2025-08-30 16:23:19] @d_dot_zk

start here: https://nautilustrader.io/docs/nightly/concepts/overview

**Links:**
- NautilusTrader Documentation

---

#### [2025-08-30 16:23:30] @d_dot_zk

then work your way through

---

#### [2025-08-30 16:25:47] @d_dot_zk

we talked about the IB API, do you guys use REST API or FIX? Also for a high-frequency trading algorithm would you recommend coding in Rust over Python? How does that question play in the context of using the IBKR API like we talked about, pulling moniker-based weeklies on Futures Options?

---

#### [2025-08-30 16:26:52] @d_dot_zk

i feel like if I want performance I go with Rust but if I want complete and utter compatibility then I go with Python, but if I know I can make it work fine with Rust then that's one to go with right?

---

#### [2025-08-30 16:28:25] @faysou.

Tws api, there's an example in the repo for requesting es option instruments. It's not possible to write strategies in rust yet, the system is still in development for rust with some substantial progress, but not done yet.

---

#### [2025-08-30 17:39:32] @d_dot_zk

thanks for that answer, my entire project is currently in C# but originally in Python, do you reckon I need to port and refactor back to Python for Nautlius Trader to be able work with it? Since the IB API accepts C# i'm wondering if I could make it work already with what i've got

---

#### [2025-08-30 18:01:39] @faysou.

🙂 I guess it's up to you to see. You can continue with what you have or migrate to nautilus.

---

#### [2025-08-30 18:02:59] @faysou.

One advantage of nautilus is that it's open source with more contributors than just you, so things improve over time even without you doing something on the library.

---

#### [2025-08-30 18:04:40] @faysou.

But if you want some unsupported features the fastest way is for you to implement them and either share them so they become integrated with the library or you maintain your own version by rebasing regularly the develop branch on your branch. There are many things I've added to the library because I need them but it's useful that more people than me use it and test it. That's probably the biggest plus point of open source libraries, more users so more testers.

---

#### [2025-08-31 00:11:14] @d_dot_zk

yeah dude I feel that, I guess if Nautilus doesn't have any native support for C# i could clone the repo and see if I can adapt it, could be a useful pull request in the future if I get it to work

---

#### [2025-08-31 00:12:42] @d_dot_zk

thing is i'm not really a programmer so to speak, I know how to use some R and statistical mathematics in programming because of my background but i'm not a dev at all, I might give it a shot if it's not a huge challenge but no promises haha 🤙

---

#### [2025-08-31 07:12:47] @faysou.

How did you get a C# code base ? I don't think there's desire to combine the language with C#, it's all about Python and rust now. Interestingly I think an earlier version of nautilus was in C# but it's not maintained anymore.

---

#### [2025-08-31 14:29:58] @rodguze



---

#### [2025-08-31 21:09:05] @apercu_16113

A few days ago I installed NT in a dev container using:
`/usr/local/bin/python -m pip install -U pip 'nautilus-trader'`

pip list is showing:
`nautilus_trader           1.219.0`

When I run the following example:
`/nautilus_trader/examples/backtest/example_07_using_indicators/run_example.py `

I receive this error:
`Traceback (most recent call last):
  File "/workspaces/nautilus-strategies/nautilus_trader/examples/backtest/example_07_using_indicators/run_example.py", line 19, in <module>
    from strategy import DemoStrategy
  File "/workspaces/nautilus-strategies/nautilus_trader/examples/backtest/example_07_using_indicators/strategy.py", line 20, in <module>
    from nautilus_trader.indicators import MovingAverageFactory
ImportError: cannot import name 'MovingAverageFactory' from 'nautilus_trader.indicators' (/home/vscode/.local/lib/python3.13/site-packages/nautilus_trader/indicators/__init__.py)`

I'm new to NT and cannot find how to fix this - can anyone help?

---

#### [2025-08-31 23:34:57] @cjdsellers

Hi <@1342779375023554644> 
There was a large refactoring which consolidated many indicator related modules together. Because of this import paths changed, examples were updated, but we have not yet released the new version (this is imminent within the next day or so)

---

#### [2025-09-01 10:50:04] @haakonflaar

Is it possible to have bars start at some arbitrary minute in an hour? For example, the US regular trading hours starts at 09:30 ET, so if I am running a strategy using for example 20 minute bars I want the first bar (within the trading hours) to go from 09:30-09:50 (normally you'd have a 09:20-09:40 and 09:40-10:00 bar). 

I want to implement "Break at end of day" logic: https://ninjatrader.com/support/helpguides/nt8/NT%20HelpGuide%20English.html?break_at_eod.htm

---

#### [2025-09-01 12:22:10] @faysou.

Yes it's possible

---

#### [2025-09-01 13:55:18] @haakonflaar

Care to elaborate how? 🙂

---

#### [2025-09-01 13:57:04] @faysou.

Look at the code of the time bar aggregator and you'll see how

---

#### [2025-09-01 14:19:44] @rodguze

this might be helpful: https://nautilustrader.io/docs/latest/concepts/data/#aggregation-sources

**Links:**
- NautilusTrader Documentation

---

#### [2025-09-01 14:20:56] @haakonflaar

It can be done by including a params attribute with the key `time_bars_origin_offset` in `self.subscribe_bars` like so:

```
self.subscribe_bars(
    self.config.bar_type,
    params={"time_bars_origin_offset": pd.Timedelta(minutes=30)},
)
```

---

#### [2025-09-01 14:23:09] @haakonflaar

I assume you should add the same attribute to `self.request_bars`

---

#### [2025-09-01 17:42:39] @faysou.

There's also as global setting using a data engine config

---

#### [2025-09-01 17:44:10] @faysou.

Also  offset is from the start of a day, to allow more precise origins. You can still specificy like you did for periods that are periodic across one hour.

---

#### [2025-09-01 17:45:25] @faysou.

The offset from start of the day is in the develop branch, personally it's the only one I use, it gets updated faster (also I regularly contribute to it, so it allows to build on previous things I do, and other contributors do as well)

---

#### [2025-09-01 20:32:24] @faysou.

first time I contribute as much to an open source project, it's really interesting to see how much can be done with a few contributors contributing regularly and some additional less regular contributors, or even sometimes once, but any contribution is useful

---

#### [2025-09-02 04:35:26] @ido3936

I am trying to build a debug env (make-debug) of nautilus-trader, and then add it as an editable dependency to my main project, that will be used to recreate some issues.
The problem is that even though I've built the NT package, when I add it as a  dependency uv starts to rebuild it - and most likely as a release build.

Is it possible to have a debug build added as an editable dependency? Or is there some other way to enable quick code/test iterations on NT, when the code is in another project?

---

#### [2025-09-02 07:23:30] @cjdsellers

Hi <@1074995464316928071> 
Yes, many of us are just using `make build-debug` from the active venv, which should give you what you're after.
If you look at the make target, its the `--no-sync` flag which is preventing that behavior you're seeing where the full package starts building again on a sync.

If you're adding `nautilus_trader` as a dependency to another project that might be trickier. If you're just putting together MRE's then that shouldn't be necessary though unless there are other things you're trying to achieve I'm not aware of.

---

#### [2025-09-02 08:57:43] @ido3936

Thanks <@757548402689966131> ,
`If you're adding nautilus_trader as a dependency to another project that might be trickier.` - yes, thats what I'm trying to do - if its not possible then I'll try to set up my use case as a small temporary notebook in the nautilus_trader project - but it would be awesome to be able to set up the former approach

---

#### [2025-09-03 16:59:52] @apercu_16113

<@757548402689966131> , while waiting for the next release, can I unblock myself by installing the nightly build? Or can you/anyone provide a hint how to get the examples working or how to work with indicators in general, with version 1.219.0 ?

---

#### [2025-09-04 03:23:41] @cjdsellers

Hi <@1342779375023554644> 
Yes, you could install a [development wheel](https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#development-wheels) for now

---

#### [2025-09-05 09:50:46] @veracious69_77345

Is nautilus not supported on MacOS intel processors?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1413461350641827851/image.png?ex=68faa336&is=68f951b6&hm=886a0deae7c661987c31c77c16512c601ff17ae4e15ad47abbd3f7b6b87b7d92&)

---

#### [2025-09-05 17:02:17] @bartoelli

Hello, I was programming in Python and JS/TS but with some web development or creating APIs. Starting with  the Nautilus is overwhelming to me. Would be here a kind soul that could help to start?

---

#### [2025-09-06 03:30:49] @rk2774

NT Getting Started:
https://nautilustrader.io/getting_started/

NT Official Documentation:
https://nautilustrader.io/docs/latest/

NT Examples:
https://github.com/nautechsystems/nautilus_trader/tree/develop/examples

AI Generated Documentation:
https://deepwiki.com/nautechsystems/nautilus_trader

Class/Module Hierarchy:
https://discord.com/channels/924497682343550976/924506736927334400/1363012698362613800

**Links:**
- NautilusTrader: The fastest, most reliable open-source trading plat...
- NautilusTrader Documentation
- nautilus_trader/examples at develop · nautechsystems/nautilus_trader
- nautechsystems/nautilus_trader | DeepWiki

---

#### [2025-09-06 10:41:06] @cjdsellers

Hi <@1186669514394452098> 
Correct, we chose not to support older x86 mac platforms because it adds 3 wheels for every CI nightly and release. You
_should_ still be able to compile from source though, it’s just not officially tested and supported

---

#### [2025-09-06 15:23:14] @apercu_16113

<@757548402689966131> , as I'm not so experienced with dev environments, this gave me some homework 🙂 
Now I have successfully installed nautilus_trader           1.220.0a20250905
But I could only do it using: pip install -U --pre nautilus_trader --**extra**-index-url=https://packages.nautechsystems.io/simple
Without the "extra-index-url" (instead of "index-url") I wasn't able to install the dependencies during dev container rebuild.

Now, also in 1.220.0a20250905, the example in nautilus_trader/examples/backtest/example_07_using_indicators/run_example.py is not executing because of ModuleNotFoundError: No module named 'nautilus_trader.indicators.average'.

Would it be possible for you or anyone to provide a working example on how to import/use an indicator in a strategy (1.219 or 1.220.*)? This seems so basic, but yet I don't see any way to get this working based on the documentation. Thanks!

---

#### [2025-09-06 22:34:12] @cjdsellers

Hi <@1342779375023554644> 
Thanks for reaching out with the feedback. Using `index-url` instead of `extra-index-url` assumes a user has previously installed `nautilus_trader` and its core dependencies. It's a bit of a trade off because as you point out pip can still pull dependencies from PyPI, but it also risks installing a compatible released wheel instead of the intended dev wheel - which I suspect *may* be what’s causing your import issue.

I’ve also scanned the codebase, and all example import paths are correct on the `develop` branch. A few were updated to use the cleaner re-exports we recently added.

So for the import issue, that [example currently on develop branch](https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/backtest/example_07_using_indicators/strategy.py#L20) is using the updated and correct path of `nautilus_trader.indicators` for that 1.220.0a20250905 version (we had to consolidate some modules together to optimize binary size). Are you able to `pip list` and confirm the version of nautilus you're running that examples script with? I hope that helps!

---

#### [2025-09-09 05:21:53] @luochaobo

"Can this platform provide video installation tutorials for the MAC system? I'm a newbie and don't know how to install it. MACMINI-M4 chip"

---

#### [2025-09-09 17:15:50] @anderson.developer.sc

How can I set up vscode to use nautilus trader in my own project?

---

#### [2025-09-09 18:51:13] @jafu6506

Hi, do you have an adapter for the options on Bybit, Binance or OKX?

---

#### [2025-09-10 09:52:20] @ido3936

Hello, I've run into positions in the positions report that are titled with `INTERNAL-DIFF`. What does this mean? Thanks

---

#### [2025-09-10 12:42:57] @rmadanagopal_42070

i’m evaluating the stable version of Nautilus. I use two DMA brokers—one for equities and one for futures—so I’ll create a Venue for each to send orders. I also subscribe to a market data vendor that streams quotes.

For instruments, each one must be tied to a Venue. Do I need to create a separate Venue for every listing exchange?

My goal is to consume market data from the vendor, and based on certain logic, route orders to either DMA_1 or DMA_2. The FIX message may also require me to include the instrument’s listing exchange. How can I retrieve the listing exchange for a given symbol in Nautilus?

---

#### [2025-09-10 21:58:49] @bartoelli

Still struggling with a quickstart 😄  - version 1.220@latest

1) Main error
```py
from nautilus_trader.indicators import MovingAverageConvergenceDivergence

class MACDStrategy(Strategy):
    def __init__(self, config: MACDConfig):
        super().__init__(config=config)
        # Our "trading signal"
        self.macd = MovingAverageConvergenceDivergence(
            int_fast_period=config.fast_period,
            int_slow_period=config.slow_period,
            PriceType_price_type=PriceType.MID,
        )
```
`2025-09-10T21:52:01.456967662Z [ERROR] BACKTESTER-001.BacktestNode: Error running backtest \n TypeError(__init__() got an unexpected keyword argument 'int_fast_period')`

It seems like the: ```File "nautilus_trader/indicators/trend.pyx", line 377, in nautilus_trader.indicators.trend.MovingAverageConvergenceDivergence.__init__``` generates the problem?

2) **Second error:**
```py
data = BacktestDataConfig(
        catalog_path=str(catalog.path),
        data_cls=QuoteTick,
        instrument_id=instruments[0].id,
        end_time="2020-01-10",
    )
```

`Expected type 'str', got 'Type[QuoteTick]' instead `

---

#### [2025-09-11 07:57:40] @mk27mk

```
             int_fast_period=config.fast_period,
             int_slow_period=config.slow_period,
             PriceType_price_type=PriceType.MID
```
Here you're prepending the type of the inputs to their parameter name, remove `int_` and `PriceType_`.

---

#### [2025-09-11 12:38:34] @lisiyuan666

Hi, when i use Redis to make the cache persistent, i got lots of warn and errors like the following image, the errors only appear if i run multiple instances of the strategy with different instruments or run one instance but change the instruments between different runs. Is there something wrong? I use this example here: https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/live/binance/binance_futures_testnet_ema_cross.py

**Attachments:**
- [screenshot_1757593902.png](https://cdn.discordapp.com/attachments/924499913386102834/1415677905702486056/screenshot_1757593902.png?ex=68faca8a&is=68f9790a&hm=717cc5eed7cf1376d74ba632c63148d91cc4594285e739f4a42e9d6e9eb80402&)
- [screenshot_1757594223.png](https://cdn.discordapp.com/attachments/924499913386102834/1415677906234900634/screenshot_1757594223.png?ex=68faca8a&is=68f9790a&hm=37544dd20e07217bb9ff968570742e6636288b4508f0f8139722966472a2def8&)
- [screenshot_1757594257.png](https://cdn.discordapp.com/attachments/924499913386102834/1415677906939805717/screenshot_1757594257.png?ex=68faca8b&is=68f9790b&hm=21d6d913c999dd0d988d6d090c14d5b7676253c6d304af62614b2c02bfceef14&)

**Links:**
- nautilus_trader/examples/live/binance/binance_futures_testnet_ema_c...

---

#### [2025-09-11 14:59:42] @bartoelli

I was trying that, but there was information that no parameter was found such as fast_period. I have to check it again - maybe that was a pycharm's cache problem? 🤔

**EDIT**:
Okay you were right. It is a problem with IDEs (Pycharm CE, Pycharm PRO). They look at in *nautillus_trader.indicator.trend.py* line:
```py
def __init__(self, int_fast_period, int_slow_period, MovingAverageType_ma_type=None, PriceType_price_type=None): # real signature unknown; restored from __doc__
        pass``` 

So it seems that my second error is also not relevant. IDEs have a problem with reading Cython files. I wonder is there a way to manage it?

---

#### [2025-09-14 09:37:51] @youdou24

Hi, how can i get some now data of Binance  for backtest . Best Wishes to You

---

#### [2025-09-17 13:43:09] @ido3936

given that the kernel's init first creates the trader object, then tries to load initialized strategies, and only then adds (initializes) strategies - is there any way to have the kernel still load strategies when the run begins?

```

        if self._load_state:
            self._trader.load()  #  at this point there are no strategies to load
[and then later down]

       # Create importable strategies
        for strategy_config in config.strategies:
            strategy: Strategy = StrategyFactory.create(strategy_config)
            self._trader.add_strategy(strategy)
```

---

#### [2025-09-18 03:21:53] @tobias.p

------------
ImportError                               Traceback (most recent call last)
Cell In[1], line 13
     10 from nautilus_trader.persistence.catalog import ParquetDataCatalog
     11 from nautilus_trader.test_kit.providers import TestInstrumentProvider
---> 13 from tradecore.strategy_v5.backtest import aggregate_ticks_to_bars

File ~/trading/tradecore/strategy_v5/backtest.py:11
      9 # Assuming this is available from your imports
     10 import pandas as pd
---> 11 from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
     12 from nautilus_trader.core.datetime import (
     13     dt_to_unix_nanos,
     14     unix_nanos_to_dt,
     15 )
     16 from nautilus_trader.examples.algorithms.twap import TWAPExecAlgorithm

ImportError: /home/put/trading/.venv/lib/python3.13/site-packages/nautilus_trader/backtest/engine.cpython-313-x86_64-linux-gnu.so: cannot enable executable stack as shared object requires: Invalid argument

----

NEED HELP! tried everything. i am on the newest version of endeavourOS (arch) and this error comes up with every module i try to import. I cannot downgrade glibc, i tried reinstalling the os 2 times no change. fresh install. i just downloaded uv as always and ran my usual git projects pyproject.toml. I am grateful for any clues, otherwise i will go back to using ubuntu for now... or maybe i try the docker containers.

---

#### [2025-09-18 03:30:35] @cjdsellers

Hi <@211176121281019905> 
This issue popped up recently, I believe its fixed here: https://github.com/nautechsystems/nautilus_trader/commit/ea18c2df32461448282377e15410dafc997996e2
You could try a [development wheel](https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#development-wheels) for now

---

#### [2025-09-18 03:31:23] @tobias.p

OMG thank you, i was about to reinstall a new distro nixos to finally fix this but i didnt think about the obvious thing to look at the github. I will try that and see

---

#### [2025-09-18 03:31:50] @tobias.p

i feel so dumb rn i spent 5 hours of my evening on this

---

#### [2025-09-18 03:59:01] @tobias.p

<@757548402689966131> As always, it worked. Thank you so much. Still gonna try nixos tho xD

---

#### [2025-09-18 04:15:49] @cjdsellers

I recommend nixos

---

#### [2025-09-18 04:16:44] @tobias.p

i will start with 25.05 and hopefully kde6 as i have Krohnkite tiling shortcuts already setup that i like. what are you using?

---

#### [2025-09-18 05:27:32] @avihai0882_03319

Hi guys, 
Please advice if there is any issue installing Nautilus system over aarch Linux distro. Thanx

---

#### [2025-09-18 07:06:36] @xcabel

hi here, I am trying to load some L2 LOB data by using wrangler OrderBookDepth10DataWranglerV2 to do some backtest but every time I got an exception read as

thread '<unnamed>' panicked at crates/model/src/types/price.rs:201:10:
Condition failed: raw value outside valid range, was 1164857706881071640503489007336816640

Stack backtrace:
   0: _PyInit_core
stack backtrace:
   0:        0x116c3f6dc - _PyInit_core
   1:        0x116c60870 - _PyInit_core
   2:        0x116c3bf78 - _PyInit_core
   3:        0x116c3f590 - _PyInit_core
   4:        0x116c40e34 - _PyInit_core
   5:        0x116c40c84 - _PyInit_core
   6:        0x116c418bc - _PyInit_core
   7:        0x116c414f0 - _PyInit_core
   8:        0x116c3fb88 - _PyInit_core
   9:        0x116c411cc - _PyInit_core
  10:        0x116d2f548 - _PyInit_core
  11:        0x116d2f880 - _PyInit_core
  12:        0x1169fbd20 - _PyInit_indicators
  13:        0x1147361c0 - _PyInit_persistence
  14:        0x11473a5b0 - _PyInit_persistence
  15:        0x114747cd4 - _PyInit_persistence
  16:        0x1147327f4 - _PyInit_live
  17:        0x1033425c8 - _method_vectorcall_FASTCALL_KEYWORDS
  18:        0x103457f84 - __PyEval_EvalFrameDefault
  19:        0x103449f7c - _PyEval_EvalCode
  20:        0x1034c339c - _pyrun_file
  21:        0x1034c2b6c - __PyRun_SimpleFileObject
  22:        0x1034c20ec - __PyRun_AnyFileObject
  23:        0x1034eb92c - _pymain_run_file_obj
  24:        0x1034eb110 - _pymain_run_file
  25:        0x1034ea924 - _Py_RunMain
  26:        0x1034ebaa8 - _pymain_main
  27:        0x1034ec2e0 - _Py_BytesMain

It errors out only after py arrow table is constructed but getting casted to Rust data type by self.from_arrow()

im not familiar with Rust. my package is 1.220 with arrow 55.2 and pyarrow 21.0.0.

---

#### [2025-09-18 07:09:44] @xcabel

I still need to transform it back to work with the cython engine so also open to any suggestion to use some v1 LOB wrangler to load the data to  work with cython engine directly.

appreciate any suggestion.

---

#### [2025-09-19 06:42:18] @maslovegor

Hi guys, Im testing my strategy with Nautilus and have faced some strange behavior
so Im placing limit spot order on binance and waiting for the filled event with
    `def on_order_event(self, order: OrderEvent) -> None:
        print(order)`
I even tried `on_order_filled` but still no result - it looks like Im not getting the filled event
However, I can see in the logs something like "reconciliation update" when the order fills, so I know its filled successfully, but I cant figure out whats wrong.

---

#### [2025-09-19 07:08:40] @cjdsellers

Hi <@259923289743425537> 
I just tried [this example script](https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/live/binance/binance_spot_exec_tester.py) and can see fills from limit orders when I set `tob_offset_ticks=0` (so orders are placed at the top of the book).
- Which version are you on?
- Are you loading all instruments for the venue?
- Did you try debug logs to see if any message processing is being skipped for some reason?

---

#### [2025-09-19 07:09:39] @cjdsellers

It could also be a strategy mismatch, so the order events are not making it to the strategy you intended

---

#### [2025-09-19 07:48:51] @maslovegor

Thank you for your reply!
version: 1.220.0
instruments: yes, Im loading all instruments
debug logs: nope, I will try
~~so, I tryed test config and Im receiving 
TESTER-001.ExecTester: <--[EVT] OrderFilled(instrument_id=ETHUSDT.BINANCE, ...)
but how I can get this event inside strategy? I tried on_order_filled and it doesnt work~~

thx so much for you help! just realized that there is a problem on my side since I modified ExampleScript with on_order_filled and it worked fine !

---

#### [2025-09-19 10:29:14] @stringer408

for newbie question ,how to add binance api to do backtesting .thanks~

---

#### [2025-09-19 11:36:56] @projectmillen1507

Hello, I tried to connect InteractiveBroker with Nautilus but I keeps gettting this error "Failed to receive server version information". I've tried everything

On TWS
- Enable ActiveX and socket : Checked
- Read only API: unchecked
- Socketport: 7497
- Master Client ID: 999
- Reset API order ID sequence: clicked mulitple times
- Allow connections from localhost only: Checked


On Nautilus:
- IB_ACCOUNT_ID= my paper trade account
- TWS_HOST=127.0.0.1
- TWS_PORT=7497                    
- IB_DATA_CLIENT_ID=105              
- IB_EXEC_CLIENT_ID=106         
- IB_TRADING_MODE=paper

Is there anything else I can do?

---

#### [2025-09-19 11:44:09] @projectmillen1507

Here is the error

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/924499913386102834/1418563314195103764/message.txt?ex=68fabdc9&is=68f96c49&hm=b0cc1f0482cd8952d930b1c2443ccf5a57428cede5c7bd6112d4724320745d26&)

---

#### [2025-09-19 12:01:47] @kasperlmc

[ERROR] SYMMETRIC-MM-001.ExecEngine: Cannot execute command: no execution client configured for BINANCE or `client_id` None, SubmitOrder(order=LimitOrder(SELL 0.100 ETHUSDT-PERP.BINANCE LIMIT @ 4_523.29 GTC, status=INITIALIZED, client_order_id=O-20250919-115930-001-000-10, venue_order_id=None, position_id=None, tags=None), position_id=None)

When I was using the sandbox, I encountered this error. Could you help me check what caused it? I’ve already set the client_id in the code.

---

#### [2025-09-20 20:32:25] @anderson.developer.sc

I gues the best way to connect to ib is using DockerizedIBGateway:
--dockerized_gateway.py--
`from nautilus_trader.adapters.interactive_brokers.config import DockerizedIBGatewayConfig
from nautilus_trader.adapters.interactive_brokers.gateway import DockerizedIBGateway
from config import settings

config = DockerizedIBGatewayConfig(
    username=settings.IB_USERNAME,
    password=settings.IB_PASSWORD,
    trading_mode=settings.IB_TRADING_MODE,
    read_only_api=False,
)

dockerized_gateway = DockerizedIBGateway(config=config)`


--main.py--
`
from common.dockerized_gateway import dockerized_gateway as gateway

async def main():
    # SECTION 1: Start and verify Dockerized IB Gateway
    gateway.start()
    await asyncio.sleep(5)  # Wait for the gateway to be fully up and running

    # Ensure the gateway is logged in and running
    assert gateway.is_logged_in(
        gateway.container), "Dockerized IB Gateway is not running"`

---

#### [2025-09-21 15:13:27] @faysou.

I've only tested the feature with databento. You will need to debug your use case with other marktet data providers.

---

#### [2025-09-21 15:13:55] @faysou.

Are you able to download historical data with a live trading node ?

---

#### [2025-09-21 15:14:14] @faysou.

If yes then it should work with the backtestnode

---

#### [2025-09-23 08:39:15] @cjdsellers

Hi <@766386312038318091> 
My initial impression is that you haven't written a `BTCUSDT.BINANCE` instrument to the catalog. I see this is using the newer download data feature so you might have to dig into the flow as faysou suggests.
To do it manually you'd need something like `catalog.write_data([BTCUSDT_BINANCE])` with the instrument there obtained from a test provider or venue data. Hope that helps a bit

---

#### [2025-09-23 13:23:42] @haakonflaar

Install via pip or build from source: https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#installation

**Links:**
- GitHub - nautechsystems/nautilus_trader: A high-performance algorit...

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
- [LUV3.txt.zip](https://cdn.discordapp.com/attachments/924499913386102834/1422348659734876210/LUV3.txt.zip?ex=68faab6a&is=68f959ea&hm=a3eabcd515d2a1a39f190870c2537fb30764ab6baaa50ef129bf9d2e3b30043c&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1424252592950870057/image.png?ex=68fa5857&is=68f906d7&hm=9e0499337d8630489a7f2f1ecb1990f34fd7ac17e85d5c089d482e60aabd1b58&)

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
- [message.txt](https://cdn.discordapp.com/attachments/924499913386102834/1425773664720261151/message.txt?ex=68fa9af3&is=68f94973&hm=d03f4e8fd6295c4e007c5e8eec81965941763a2be53c18c727595c7809cba33e&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793206624456764/image.png?ex=68faad26&is=68f95ba6&hm=80bf8dc554eefcd3f0f7a91cbe3255a741751872610547c1e063c4a17c522672&)
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793207010328698/image.png?ex=68faad26&is=68f95ba6&hm=1aa26040f885e6bfa0c9fa8fa07a2dd3e2daec71406f2436f597b4d59e429613&)
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1425793207433822299/image.png?ex=68faad26&is=68f95ba6&hm=8795a33637d64ef860adc6585d4cb15fe67e0a09f219255f77cc15c29b99a406&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1426653445313532004/image.png?ex=68fa828f&is=68f9310f&hm=6a5d2402d1770134ca81613090f826414f8094239c1d2da3112b2926e2725896&)

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
- [logs.rtf](https://cdn.discordapp.com/attachments/924499913386102834/1428392145982717953/logs.rtf?ex=68fae719&is=68f99599&hm=aa1303d2cb4fe99bff902d5e39b6cca38912d1f74aa59c8407969308acf7d46b&)

---

#### [2025-10-16 15:42:46] @one_lpb

I made some tests and it looks like that on TP (SELL LIMIT when LONG on futures) NT fill half of total position contracts and cancel  STOP_MARTKET and LIMIT orders, instead of continuing to reduce order sizes... Maybe there is something I didn't catch ?

---

#### [2025-10-16 15:49:47] @one_lpb



**Attachments:**
- [logs.rtf](https://cdn.discordapp.com/attachments/924499913386102834/1428409601749028885/logs.rtf?ex=68faf75b&is=68f9a5db&hm=e65b6a7fdf4b76ccfdb8b51f06efa083e891e92e9f7334352b57c857e7a6d6d1&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430081112419340308/image.png?ex=68fa7492&is=68f92312&hm=d73e9f7d10d12ca0eae84ef8c84441b7918d34dab1f7e18123db86f179fb6428&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430490527274373182/image.png?ex=68faa05e&is=68f94ede&hm=bf361d42bfa1587f86a97aa54bfef6422b3a3c54477d0c53ad91dfcf5b7ba83b&)

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
- [image.png](https://cdn.discordapp.com/attachments/924499913386102834/1430582634265710592/image.png?ex=68faf626&is=68f9a4a6&hm=af3c0f04ec5ce15d7ae88443c3210e03cbe87b86b32e7f07fbbfa9769a8d1629&)

---
