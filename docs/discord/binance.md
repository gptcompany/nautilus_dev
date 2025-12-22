# NautilusTrader - #binance

**Period:** Last 90 days
**Messages:** 80
**Last updated:** 2025-10-23 04:00:32

---

#### [2025-07-28 03:47:15] @liguifan

<@757548402689966131> I am trying to execute an limited "BTCUSDT-PERP.BINANCE" order and then try to get the updates of status of the order. However, I am experiencing an error below. I think the ```handle_order_trade_update``` function in user.py is trying to look for "BTCUSDT" rather than "BTCUSDT-PERP.BINANCE". Wondering is there a workaround to this issue? 

```2025-07-28T03:20:01.894162700Z [ERROR] Trader-LIVE.ExecClient-BINANCE: Error on handling b'{"stream":"ymozXKzomW0Suq16svRXfaisxRV7KElBDsJ3AUO52d7EXm3Vb9XSEMQlQEQGQ9gf","data":{"e":"ORDER_TRADE_UPDATE","T":1753672801773,"E":1753672801777,"o":{"s":"BTCUSDT","c":"O-20250728-032001-LIVE-000-7","S":"SELL","o":"LIMIT","f":"GTC","q":"0.046","p":"119394.4","ap":"0","sp":"0","x":"NEW","X":"NEW","i":5487238883,"l":"0","z":"0","L":"0","n":"0","N":"USDT","T":1753672801773,"t":0,"b":"0","a":"53414.6697","m":false,"R":false,"wt":"CONTRACT_PRICE","ot":"LIMIT","ps":"BOTH","cp":false,"rp":"0","pP":false,"si":0,"ss":0,"V":"EXPIRE_MAKER","pm":"NONE","gtd":0}}}'
ValueError(Cannot handle trade: instrument BTCUSDT-PERP.BINANCE not found)
Traceback (most recent call last):
  File "f:\git\hft-breakout-crypto\.venv\Lib\site-packages\nautilus_trader\adapters\binance\futures\execution.py", line 316, in handleuser_ws_message
    self._futures_user_ws_handlers[wrapper.data.e](raw)
  File "f:\git\hft-breakout-crypto\.venv\Lib\site-packages\nautilus_trader\adapters\binance\futures\execution.py", line 327, in handleorder_trade_update
    order_update.data.o.handle_order_trade_update(self)
  File "f:\git\hft-breakout-crypto\.venv\Lib\site-packages\nautilus_trader\adapters\binance\futures\schemas\user.py", line 302, in handle_order_trade_update
    raise ValueError(f"Cannot handle trade: instrument {instrument_id} not found")```

---

#### [2025-07-28 05:20:15] @liguifan

this could be reproduced by running examples/live/binance/binance_futures_testnet_market_maker.py

---

#### [2025-07-29 05:35:33] @sxb2882

self.portfolio.unrealized_pnl  The real market has been running, but the unrealized profit and loss obtained is sometimes right and sometimes wrong. Why is this? 
engine.trader.generate_positions_report().to_csv("./output/backtest_positions_report_v5.csv", index=False)
When backtesting, I submitted a closing order, but according to the final analysis, there is no information such as the closing time in the position history.
trader_id,strategy_id,instrument_id,account_id,opening_order_id,closing_order_id,entry,side,quantity,peak_qty,ts_init,ts_opened,ts_last,ts_closed,duration_ns,avg_px_open,avg_px_close,commissions,realized_return,realized_pnl
PAIR-SPREAD-BACKTEST,PairSpreadStrategy-000,NEARUSDT-PERP.BINANCE,BINANCE-001,O-20231202-180000-BACKTEST-000-1,,BUY,LONG,25,25,1701540000000000000,2023-12-02 18:00:00+00:00,1701540000000000000,,,1.993,,['0.02491250 USDT'],0.0,-0.02491250 USDT
<@757548402689966131>

---

#### [2025-07-31 03:35:39] @cjdsellers

Hi <@716325099464294429> 
Thanks for the report and how to reproduce, I’ll have a look when I can

---

#### [2025-07-31 03:37:56] @cjdsellers

Hi <@1090181860023353446> 
Thanks for the feedback.
I see two issues here:
1) Probably depends on the update timing/frequency between Binance and Nautilus. iirc we don’t recalculate unrealized PnL on every tick as this would be quite expensive to compute

2) All orders and positions should be accounting for in the reports. At the end of a backtest, if there are still open positions then the unrealized PnL will be reported separately. If you’re seeing a discrepancy then it’s impossible to tell without more information or an MRE

---

#### [2025-08-03 08:51:36] @frzgunr

Hi<@757548402689966131>,There seems to be a problem with the interface related to the Binance Spot Test Network (to verify that it's not a stupid problem, I copied the code examples/live/binance/binance_spot_testnet_ema_cross.py from the example and only modified the api for a secondary verification).

---

#### [2025-08-03 08:52:16] @frzgunr



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1401487828549894206/image.png?ex=68fa9580&is=68f94400&hm=390c0a9afacf03ce7c50ae508b3035a0470fab8118f8d11234f08bdda7ccec0c&)

---

#### [2025-08-03 08:53:20] @frzgunr

The test network for futures will be up and running, while the test network for spot will have a bug as shown here

---

#### [2025-08-03 12:58:59] @frzgunr



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1401549916672622622/image.png?ex=68facf53&is=68f97dd3&hm=f3c766b2e123d006ab3a83c8fa479b4be019e80252249da3283935843d343bcf&)

---

#### [2025-08-03 13:00:36] @frzgunr

Update: I opened an aws Tokyo server and still have the same problem. Futures is fine in the test network, spot will report an error as shown in the picture. live network is all fine. I don't know much about networking but I think it's some problem with NT framework networking.

---

#### [2025-08-04 03:15:46] @cjdsellers

Hi <@899697082791780364> 
Thanks for the report, this is now fixed (the streaming URL was incorrect and missing a `stream` in the path): https://github.com/nautechsystems/nautilus_trader/commit/841a44c7bf9787bf837ba1209beafd25c4094948

Would you like to be credited in the release notes? (if so provide your github username when you can)

**Links:**
- Fix Binance Spot testnet streaming URL · nautechsystems/nautilus_t...

---

#### [2025-08-04 05:04:56] @frzgunr

of course, id：Frzgunr1   https://github.com/Frzgunr1

**Links:**
- Frzgunr1 - Overview

---

#### [2025-08-04 05:05:20] @frzgunr

Glad I could help NT!

---

#### [2025-08-04 11:14:54] @frzgunr

hi <@757548402689966131>bro.  I think there may be a network related problem again. I made sure my api was set up and filled out with no problems. When executing the` examples/live/binance/binance_spot_and_futures_market_maker.py `code in the example, it appears that only the spot market data is available, and there is no data returned or api interaction for the futures market.

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1401886108018540624/image.png?ex=68fab6ed&is=68f9656d&hm=500ee57b475431ed9ee459db83154bc7b8bc231d21340e69b9e3e7b3bc0326c8&)
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1401886108358545478/image.png?ex=68fab6ee&is=68f9656e&hm=b6becd8502c7c27f95149f92d167fcaed11d6a6f16a071d91f36f25d137e4a80&)

---

#### [2025-08-04 11:19:20] @frzgunr

Also, using just the futures market will give the same error. just modify the api and testnet=False in `examples/live/binance/binance_futures_testnet_ema_cross.py`to reproduce the issue.

---

#### [2025-08-04 11:28:00] @frzgunr

Additional news: this is the normal case in a test network situation: both spot and futures markets return messages at the same time normally, hope this helps.

**Attachments:**
- [64221386aad59201e4530bcb7c76879.png](https://cdn.discordapp.com/attachments/954875368261693511/1401889408356974676/64221386aad59201e4530bcb7c76879.png?ex=68faba00&is=68f96880&hm=6c5c9190231bfd6134866625f57600f48f1067b3a1826e82afb9380fd7c36a31&)

---

#### [2025-08-04 12:39:21] @cjdsellers

Hi <@899697082791780364> 
This one looks like a permissions issue. The testnet and production API keys must be different, if you set `testnet` to False then it'll hit the real futures exchange which may not be allowed in your juristiction. All Binance examples run OK for me as is, except for `python examples/live/binance/binance_futures_market_maker.py` as I'm also not able to hit the real futures exchange from Australia

---

#### [2025-08-04 13:07:15] @frzgunr

Thank you for your response. Do you mean: the KYC area of the account itself will cause the account itself not to have certain trading features, is that right?

---

#### [2025-08-04 13:19:31] @frzgunr

I just successfully completed an order in the futures market (via Binance APP).  This is very confusing for me.

---

#### [2025-08-04 14:00:31] @frzgunr



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1401927786863656980/image.png?ex=68faddbe&is=68f98c3e&hm=ab4cf8b6ce2525d75a49f105f9ab5cd6dd5548b2561588ea2314b3a62158ee56&)

---

#### [2025-08-04 14:01:10] @frzgunr

I solved the problem. It's Binance's problem. Thank you for your help!

---

#### [2025-08-05 08:33:31] @cjdsellers

⚠️ Hi all, quick heads up on breaking changes to Binance API credentials on the last push to `develop` branch. These were refined down to just what was necessary to differentiate between testnet spot/futures and mainnet, **and shared between all key types** - which eliminated 10 redundant/confusing env vars.

https://github.com/nautechsystems/nautilus_trader/blob/develop/docs/integrations/binance.md#api-credentials

**  Mainnet (shared between Spot/Margin and Futures):**
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`

**  Testnet Spot/Margin :**
- `BINANCE_TESTNET_API_KEY`
- `BINANCE_TESTNET_API_SECRET`

**  Testnet Futures:**
- `BINANCE_FUTURES_TESTNET_API_KEY`
- `BINANCE_FUTURES_TESTNET_API_SECRET`

---

#### [2025-08-05 08:34:24] @cjdsellers

Also, Ed25519 key type is now working, but be sure to set `key_type=BinanceKeyType.ED25519` in your configs

---

#### [2025-08-05 18:00:00] @frzgunr

Do guys subscribe to 1 minute k-line data when using CoinSafe and get data loss i.e. don't get the target data? (This is a survivor bias issue, could you please reply to me with an emoticon to this message if it hasn't happened, and if it has could you please state the frequency)

---

#### [2025-08-10 22:41:02] @cjdsellers

Re current issue with the `BinanceSymbolFilterType` enum for Binance Spot (fixed on `develop` branch):
https://discord.com/channels/924497682343550976/924506736927334400/1404233045581500427

---

#### [2025-08-11 17:13:23] @frzgunr

Hi<@757548402689966131>, I'm realizing a strategy that determines the number of open positions based on available balance. So I need to implement the strategy to get the current available balance in the account before opening a position. I only see a reference to account balance in BinanceFuturesBalanceInfo Class in `nautilus_trader/nautilus_trader/adapters/binance/futures/schemas 
/account.py`, but I don't find where this class is called. Can you please tell me how to call the function in the BinanceFuturesBalanceInfo Class to get the current balance in the account?

---

#### [2025-08-12 00:35:02] @cjdsellers

Hi <@899697082791780364> 
You can call `self.portfolio.account(venue)` to get the `Account`:
https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/portfolio/base.pxd#L33

Then all of these methods are available:
https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/accounting/accounts/base.pxd#L61

---

#### [2025-08-12 09:51:46] @frzgunr

thx bro

---

#### [2025-08-12 13:26:49] @triflingtornado

Is there any documentation/tutorial on how I can ingest order book data delta updates gathered from the `@depth` webstream and perform backtesting. I looked at https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook/ but it does not explain what schema it expects for the CSVs provided as input or how to convert the webstream data into the appropriate schema for the tutorial

**Links:**
- NautilusTrader Documentation

---

#### [2025-08-16 01:20:11] @premysl_22228

There are unfortunately no docs yet. You will have to dive in into source codes of BinanceOrderBookDeltaDataLoader and find what are expected values from it. Let us know, if there is any problem.

---

#### [2025-08-16 01:27:25] @premysl_22228

I think, the activity we see on testnets are great for development on the contrary. It's great opportunity to debug, debug, debug, debug,... I am planning some tests on nightly for testnets, at least I will try to put it into a promised docs how to improve testing, if I don't get into it personally. We want data, which breaks the code, not the happy path in my opinion.

---

#### [2025-08-20 10:26:55] @vinc0930

Hi, does the library support place/cancel orders through WebSocket, or is it only REST for now?

---

#### [2025-08-20 13:52:26] @colinshen

Does anyone successfully run the backtest for Binance? Stream mode

---

#### [2025-08-21 07:44:24] @cjdsellers

Hi <@511076692543143936> 
The Binance adapter was an early one and is just using the REST API for execution, WebSocket for data. The Bybit adapter has the option of a "trading WebSocket" and OKX adapter uses WebSockets for both execution and data streams by default. I hope that helps!

---

#### [2025-08-21 09:21:47] @vinc0930

Glad to hear that Bybit and OKX support it. I hope Binance will be supported soon as well. Thanks again!

---

#### [2025-08-24 09:49:19] @cjdsellers

⚠️ **Breaking change heads up**
Binance adapter users should be aware of the following renames for more conventional terminology:
- Renamed `BinanceAccountType.USDT_FUTURE` to `USDT_FUTURES`
- Renamed `BinanceAccountType.COIN_FUTURE` to `COIN_FUTURES`

---

#### [2025-08-30 12:25:28] @germang8884

Hi. I;ve changed to BinanceAccountType.USDT_FUTURES, and now got the message: Error in trading loop: USDT_FUTURES. Some help will be appreciated

---

#### [2025-08-30 21:49:58] @cjdsellers

Hi <@808816390576013343> 
Are you able to copy paste the entire error message?

---

#### [2025-08-31 03:54:07] @germang8884

I'm afraid that's the only message that appeared.     Error in trading loop: USDT_FUTURES.

---

#### [2025-08-31 05:27:29] @saruman9490

Was there a change on Binance API? Getting this error all of a sudden

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1411583151620362361/image.png?ex=68fa6581&is=68f91401&hm=a36a03ef9e808283c23f5d93b4e2a0d92f6e64a7efa2fa7e143b23608fc9cb86&)

---

#### [2025-08-31 05:30:38] @saruman9490

Running nautilus v1.219

---

#### [2025-09-01 00:24:59] @cjdsellers

Hi <@337157623352655873> 
Yes the Binance API changed, they added a variant for that enum. This is fixed on `develop` branch / in development wheels. Next release will be very soon

---

#### [2025-09-02 14:02:41] @borislitvin

https://github.com/nautechsystems/nautilus_trader/issues/2914

<@757548402689966131>  i reopened this issue as i am getting getting error: '{"timestamp":1756821332836,"status":404,"error":"Not Found","message":"No message available","path":"/sapi/v1/asset/tradeFee"}' while running binance_spot_ema_cross.py example connecting to Binance US

**Links:**
- Binance https://docs.binance.us/?python#get-trade-fee is not workin...

---

#### [2025-09-02 14:19:22] @borislitvin

https://docs.binance.us/#get-trade-fee 

GET /sapi/v1/asset/query/trading-fee (HMAC SHA256)

---

#### [2025-09-02 21:28:14] @cjdsellers

https://github.com/nautechsystems/nautilus_trader/commit/5a0028f3c6aa2284efaedc910767b9f3791df9e8

**Links:**
- Fix Binance US trading fee endpoint URL · nautechsystems/nautilus_...

---

#### [2025-09-05 20:50:39] @borislitvin

<@757548402689966131> - thanks for fixing it, tried to build from the dev branch but build failed. do you have an ETA when you are going to push it to the pip? we  <@1413629533151563887>  would rather wait (if not too long)

---

#### [2025-09-05 21:53:05] @cjdsellers

Hi <@1049687206836568115> you can also install a [development wheel](https://github.com/nautechsystems/nautilus_trader?tab=readme-ov-file#development-wheels). It shouldn't be more than a couple of days now

---

#### [2025-09-07 10:04:21] @smooth2001

When MEXC exchange?

---

#### [2025-09-07 10:04:51] @cjdsellers

Hi <@966125037964890162> no plans right now

---

#### [2025-09-07 10:06:11] @smooth2001

Does that mean if one decides to contribute that part, it won't be accepted into the master?  <@757548402689966131>

---

#### [2025-09-07 10:08:09] @cjdsellers

I assumed you were asking when we would implement it (current maintainers). It might be tricky right now as patterns are still being established across the Rust-based adapters

---

#### [2025-09-07 10:09:36] @smooth2001

Oh okay. Please consider adding MEXC.

---

#### [2025-09-09 02:58:36] @kelvin.eung

I backtested using 1-minute candlestick data from Binance's perpetual swaps between January 1, 2025, and March 1, 2025. After the backtest, the data in the Returns Statistics section is all nan. What's the problem?

---

#### [2025-09-09 07:01:39] @cjdsellers

Hi <@921324609796730900> 
Do you see any orders or positions for the backtest run? all NaN values generally occurs when there are no trades for the backtest run

---

#### [2025-09-09 07:04:47] @kelvin.eung

Yes, I can see OrderFilled and PositionOpened event in the log file. but the problem may be related to my strategy, I will check it again

---

#### [2025-09-16 19:22:38] @kompaktowl

Is `_request_instruments` not yet implemented on the Binance adapter?

---

#### [2025-09-18 04:18:17] @cjdsellers

Correct, but per my message here https://discord.com/channels/924497682343550976/924506736927334400/1418086014047486094 I think it would be more proper to request instruments from Binance again?

---

#### [2025-09-18 04:20:02] @aaron_g0130

Does anyone has the example code or demo for download binance historical depth data and store to local via ParquetDataCatalog?

---

#### [2025-09-18 04:25:34] @cjdsellers

Hi <@1418078113161674900> there might be some clues in here if you haven't seen it already https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook

---

#### [2025-09-18 06:11:40] @aaron_g0130

thanks, is the data used in this example has the same format and structure as data here: https://github.com/nautechsystems/nautilus_trader/tree/master/tests/test_data/binance

**Links:**
- nautilus_trader/tests/test_data/binance at master · nautechsystems...

---

#### [2025-09-18 06:12:08] @aaron_g0130



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1418117371683672064/image.png?ex=68fa6ff8&is=68f91e78&hm=cf1a8791339357f696c0be460985bea2bc46aa6f7261cc424cc7a9c4febc9562&)

---

#### [2025-09-19 10:51:57] @kompaktowl

Yes or fetch from the cache and stream it to `on_instrument` handler 🤔

---

#### [2025-09-22 16:30:21] @svbst

Hi everyone. I’m new here and I have a few questions that I’d really like to get clear answers to, so I decided to reach out. I’m hoping for some help and good advice. Thank you!
I’m currently developing a trading bot for Binance Futures. I already have a strategy in place, but I’m not quite sure how to properly backtest it using the Nautilus Backtest Engine.

My more specific question is: does there already exist a well-prepared backtesting template for Binance Futures trading? I’d like to use a ready-made, reliable, and tested template ideally even an official one where I can simply integrate my own strategy.
Sorry if this is a basic or silly question, but I’m still a beginner and just getting familiar with this environment. Any advice from people with more experience in this area would be really valuable.

Thanks in advance I’d really appreciate your support and guidance.

---

#### [2025-09-23 08:35:47] @cjdsellers

Hi <@566195747608068098> 
Welcome and thanks for reaching out. The quick answer is, there's no template for this currently - but this is good signal that one would be appreciated by the community
There is only this specifically for Binance right now and it's not great quality, we're lacking good tutorials https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook

---

#### [2025-09-30 19:44:00] @borislitvin

<@757548402689966131> - we started executing orders on binance.us and noticed that OrderFilled events are not coming in.... given this is live trading it is difficult to give reproducable code. but we clearly see the fill on binance.us UI but nautilus logs (in DEBUG mode) dont show anything. the same is in the debugger - on_order_filled () is not getting triggered. 

Just observed partial fills generated [DEBUG] TAS-TESTER-001.ExecEngine: <--[RPT] OrderStatusReport(........) but not a PartialFill()

accepted/cancel/rejected - working well as expected.

FYI: <@1413629533151563887> <@767795125187248199>

---

#### [2025-10-03 21:21:25] @borislitvin

<@757548402689966131> - i reopned the issue as i still cant see fills when using development version containing the fix. i installed it from the wheel:
pip install nautilus_trader==1.221.0a20250926 --index-url=https://packages.nautechsystems.io/simple

---

#### [2025-10-05 05:38:54] @cjdsellers

The above is being tracking in this [GitHub issue](https://github.com/nautechsystems/nautilus_trader/issues/3006#issuecomment-3367216376).
It appears to be getting processed as an external order. I suspect somewhere in the flow an instrument isn't available with a silent return etc (there were some changes to accomodate nodes receiving messages for instruments not being traded) but remains TBD for now

---

#### [2025-10-11 05:39:50] @lisiyuan666

Anyone have problems with reconciliation on binance futures? I have two positions open currently on binance but after reconciliation there is only one position in cache.positions_open(). I tried to check the log and NT received two PositionStatusReports correctly but ends up with only one after the reconciliation.

---

#### [2025-10-11 05:40:15] @lisiyuan666

The part of the log that are related: "2025-10-11T05:17:57.852221925Z [DEBUG] TESTER-BTCUSDT_PERP_BINANCE.ExecClient-BINANCE: Received PositionStatusReport(account_id=BINANCE-USDT_FUTURES-master, instrument_id=BTCUSDT-PERP.BINANCE, venue_position_id=No
ne, position_side=LONG, quantity=0.004, signed_decimal_qty=0.004, report_id=0c43bb8e-78e0-44fb-b266-673fce87d62d, ts_last=1760159877852054420, ts_init=1760159877852054420)
2025-10-11T05:17:57.852634799Z [DEBUG] TESTER-BTCUSDT_PERP_BINANCE.ExecClient-BINANCE: Received PositionStatusReport(account_id=BINANCE-USDT_FUTURES-master, instrument_id=BTCUSDT-PERP.BINANCE, venue_position_id=No
ne, position_side=SHORT, quantity=0.004, signed_decimal_qty=-0.004, report_id=dcd88150-05fa-4d65-a441-465c2b0dd5d0, ts_last=1760159877852550586, ts_init=1760159877852550586)
2025-10-11T05:17:57.853284184Z [INFO] TESTER-BTCUSDT_PERP_BINANCE.ExecClient-BINANCE: Received 2 PositionStatusReports".

---

#### [2025-10-11 07:35:19] @woung717

If you want to open long and short position at the same time, did you set the OMS type as hedging?

---

#### [2025-10-11 08:02:43] @lisiyuan666

I tried to set the OMS as hedging in the strategy config, but there is no difference

---

#### [2025-10-11 08:15:10] @lisiyuan666

A quick survey with GPT-5 points to me a possible bug here, it seems to be only returning the last positions from PositionStatusReports.

**Attachments:**
- [screenshot_1760170437.png](https://cdn.discordapp.com/attachments/954875368261693511/1426483251958124574/screenshot_1760170437.png?ex=68fa8cce&is=68f93b4e&hm=40c2f59ee4e45a4a37a7e561094478c7b921085c787cfc7f8a40b035eedb69f9&)

---

#### [2025-10-20 09:40:51] @dimlaitman

Hello guys, I need 10-minute bars. Is this possible or do I need to create my own custom feed?

---

#### [2025-10-20 10:12:16] @aaron_g0130

Any suggestion on the Error caused by Chinese Token on Binance?

---

#### [2025-10-20 12:13:10] @null_12954_42083

I've run into the same issue too. 🥹 


BinanceFuturesInstrumentProvider: Loading all instruments...

thread '<unnamed>' panicked at crates/model/src/types/currency.rs:102:74:
Condition failed: invalid string for 'code' contained a non-ASCII char, was '币安人生'
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
Aborted (core dumped)

---

#### [2025-10-20 12:13:21] @russel_vs_hft

Saw that as well..

---

#### [2025-10-20 12:16:13] @russel_vs_hft

Is there a quick fix for this?

---

#### [2025-10-21 01:47:24] @duytruong1901

same problem 🙁

---

#### [2025-10-21 02:45:08] @aaron_g0130

I fixed it temporarily by adding a filter in binance.http.client func send_request()

---

#### [2025-10-21 02:46:55] @aaron_g0130

someone says install dev or nightly version can fix this problem, but I can't install them somehow, the command in front page didn't work.  "pip install -U nautilus_trader --pre --index-url=https://packages.nautechsystems.io/simple
Looking in indexes: https://packages.nautechsystems.io/simple
ERROR: Could not find a version that satisfies the requirement nautilus_trader (from versions: none)
ERROR: No matching distribution found for nautilus_trader"

---
