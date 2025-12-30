# NautilusTrader - #binance

**Period:** Last 90 days
**Messages:** 40
**Last updated:** 2025-12-22 18:01:55

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
- [screenshot_1760170437.png](https://cdn.discordapp.com/attachments/954875368261693511/1426483251958124574/screenshot_1760170437.png?ex=694a4f8e&is=6948fe0e&hm=bbf8793254d1d2a2dea0955ddeee9d70fa56da82a58f5c4cf75a9d035844cc81&)

---

#### [2025-10-20 09:40:51] @kirillovdigital

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

#### [2025-11-01 15:11:11] @arandott

Hi everyone, new to Nautilus Trader here. Is there any ongoing work or plan for a Binance Rust adapter?
I searched the docs/issues/PRs but only found the Python adapter. Any pointers would be great—thanks!

---

#### [2025-11-01 15:11:18] @arandott

🥺

---

#### [2025-11-02 00:42:11] @cjdsellers

Hi <@1125321375842836542> 
We will get around to it soon, no time frame can be given yet though. The plan is to eventually port all existing adapters to Rust

---

#### [2025-11-02 08:57:46] @arandott

Got it, thanks! For context: in my fork I added Binance Vision–backed warmup plus some fallback/retry logic for the Binance adapter, and I’m running it in production. If an RFC for a Rust adapter comes out, I’ll try to contribute🦀 🚀

---

#### [2025-11-03 23:05:42] @aleburgos.

I'm trying to use the download data feature, but requesting instruments I always get the error " Cannot find instrument for ..", do I missing something?

```
import sys

from nautilus_trader.adapters.binance import BinanceAccountType
from nautilus_trader.adapters.binance.config import BinanceDataClientConfig
from nautilus_trader.adapters.binance.factories import BinanceLiveDataClientFactory
from nautilus_trader.backtest.node import BacktestNode
from nautilus_trader.common.config import InstrumentProviderConfig
from nautilus_trader.model.data import BarType
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.config import DataCatalogConfig

catalog_folder = "./catalog"
catalog = ParquetDataCatalog(catalog_folder)
catalog_config = DataCatalogConfig(path=catalog.path)

spot_data_client_config = BinanceDataClientConfig(
    account_type=BinanceAccountType.SPOT,
    instrument_provider=InstrumentProviderConfig(load_all=True),
    api_key="api_key",
    api_secret="api_secret",
)

data_clients: dict = {
    "BINANCE": spot_data_client_config,
}

bar_types = BarType.from_str("BTCUSDT.BINANCE-1-HOUR-LAST-EXTERNAL")

# Create the backtest node
node = BacktestNode([])

# Register the Binance data client factory
node.add_data_client_factory("BINANCE", BinanceLiveDataClientFactory)

# Build download engine
node.setup_download_engine(catalog_config, data_clients)


node.download_data(
    "request_instrument",
    instrument_id=bar_types.instrument_id,
)


node.dispose()


```

---

#### [2025-11-04 15:02:59] @bert_68749

@all I'd like to understand how to resolve this issue. As far as I know, "币安人生" is indeed a newly listed currency, but the system seems unable to recognize these Chinese characters.

**Attachments:**
- [1.png](https://cdn.discordapp.com/attachments/954875368261693511/1435283194466406520/1.png?ex=694aaf23&is=69495da3&hm=f3aa8a423f7077a1c8c787dd614021e54621c8d01f61e5096ff328812e4bda79&)

---

#### [2025-11-04 15:24:09] @joyj0767

Same question

---

#### [2025-11-04 15:47:48] @joyj0767

<@1173906305648431174> I think I found the solution. just run:
```
pip install nautilus_trader==1.221.0a20251026 --index-url=https://packages.nautechsystems.io/simple
``` 
or 
```
pip install nautilus_trader==1.221.0a20251026 \
    --index-url=https://pypi.org/simple \
    --extra-index-url=https://packages.nautechsystems.io/simple
```

---

#### [2025-11-04 15:48:19] @joyj0767

https://github.com/nautechsystems/nautilus_trader/issues/3053

**Links:**
- [Binance] Nautilus rejects a new '测试' symbol on Binance Futures...

---

#### [2025-11-04 15:50:07] @bert_68749

Thank you, I'll try it tomorrow.

---

#### [2025-11-20 10:05:29] @vraptor75011

on binance futures testnet, i keep getting errors due to ADL autoclose order sent by binance and not taken in account by nautilus. Anybody with same issue ?

**Attachments:**
- [Capture_decran_2025-11-20_a_09.02.22.png](https://cdn.discordapp.com/attachments/954875368261693511/1441006531226374256/Capture_decran_2025-11-20_a_09.02.22.png?ex=694a6969&is=694917e9&hm=7d94ef58faccecf0ac06b07b4fe5f9b60b2d484a3f871b98a57b750dd8e542fd&)

---

#### [2025-11-21 03:37:18] @cjdsellers

Hi <@823063792689610783> 
Thanks for the report, which version are you on? there were some improvements to Binance ADL handling released in 1.221.0. If you're on the latest then I can investigate more deeply
https://github.com/nautechsystems/nautilus_trader/commit/efd5e7a8783bc9e4d44c4b4ebf8a3a84f6292712

---

#### [2025-11-21 07:13:09] @vraptor75011

I m on 1.221.0. nautilus seems to receive notice of the ADL order issued by binance but doesn t "FILL" it and doesn t update position causing all subsequent pending order (tp/sl) to fail because position in Binance is at zero.

---

#### [2025-11-22 01:12:48] @cjdsellers

Thanks <@823063792689610783> 
It turns out Binance can send ADL fills with either `x=CALCULATED` or `x=TRADE` execution types, but we were only checking for `CALCULATED` which caused TRADE-type ADL fills to be dropped. The fix adds `X=FILLED` status as an additional check so both ADL message variants are properly handled. Let me know if you have any further issues with it.

https://github.com/nautechsystems/nautilus_trader/commit/32896d30bca8b9023f16568ed19dffb26cf1197b

**Links:**
- Fix Binance ADL orders with TRADE execution type · nautechsystems/...

---

#### [2025-11-22 12:58:00] @vraptor75011

Thanks , will try and let you know as soon as my Starlink recover from yesterday’s death 😡

---

#### [2025-11-29 06:23:12] @jakob_56860

just checking, the FundingRateUpdate subscrition isnt impelmented for binance or many of the other intergrations yet?

---

#### [2025-11-29 11:17:10] @cjdsellers

Hi <@1357916439453110355> 
Correct, not implemented for Binance yet - only for the Rust-based adapters. Binance will be ported in due course

---

#### [2025-11-30 01:53:50] @jakob_56860

No worries at all, I’ll just implement it in the python base class for now

---

#### [2025-12-01 17:52:32] @colinshen

Hi, does the AggressorSide in trade equals the buyer the market maker？seller = True  buyer = False in binance api？

---

#### [2025-12-09 08:44:27] @null_12954_42083

When I submitted a STOP_MARKET order, I received the following error message: `reason='{'code': -4120, 'msg': 'Order type not supported for this endpoint. Please use the Algo Order API endpoints instead.'}'`
I tried the Development wheels but still got an error.

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/954875368261693511/1447871508562182185/image.png?ex=694a566b&is=694904eb&hm=44a13e918a54b374331b56a8d3ac77c3dcd11ef134161a25e5a417f6f9a95a44&)

---

#### [2025-12-09 10:31:19] @null_12954_42083

I have submitted an issue. https://github.com/nautechsystems/nautilus_trader/issues/3287

**Links:**
- [BINANCE] Binance API change breaks conditional orders (STOP_MARKET...

---

#### [2025-12-10 00:41:17] @cjdsellers

https://github.com/nautechsystems/nautilus_trader/commit/62ef6f63a025fae5300da405b218fc625d7b7f97

**Links:**
- Fix Binance Futures Algo Order API for conditional orders · nautec...

---

#### [2025-12-12 08:52:12] @null_12954_42083

Does anyone know how to cancel a STOP_LIMIT or LIMIT_IF_TOUCHED order that has been triggered but not filled?

---

#### [2025-12-12 08:55:57] @null_12954_42083

Binance Futures, with Nautilus Trader.

---
