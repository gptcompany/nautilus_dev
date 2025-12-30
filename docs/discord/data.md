# NautilusTrader - #data

**Period:** Last 90 days
**Messages:** 91
**Last updated:** 2025-12-22 18:01:43

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
- [single_ticker.zip](https://cdn.discordapp.com/attachments/924504069433876550/1428396544775684106/single_ticker.zip?ex=694aadf2&is=69495c72&hm=fb9d13b3eef2071056bca309fcdc4be6872e9fbdb0cd02f3f5e7eaba583c96c3&)

---

#### [2025-10-16 14:58:51] @ido3936



**Attachments:**
- [minimal_backtest_example.py](https://cdn.discordapp.com/attachments/924504069433876550/1428396780743295096/minimal_backtest_example.py?ex=694aae2a&is=69495caa&hm=c0e176111682018107b4e0a8b325dbf304da922bdd970c7d40f6d538f68bff23&)

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
- [minimal_backtest_example.py](https://cdn.discordapp.com/attachments/924504069433876550/1428416158729768970/minimal_backtest_example.py?ex=694ac036&is=69496eb6&hm=ca62809f198b7c7bd5737fdb3065ee9fdc539d2bf1a332bd4c69f33e57111c42&)
- [single_ticker_2.zip](https://cdn.discordapp.com/attachments/924504069433876550/1428416159048532028/single_ticker_2.zip?ex=694ac037&is=69496eb7&hm=85b3bebdee3db49180c1c337bbb7d4026d734416b5490b826f9ffb0014539b6e&)

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

#### [2025-10-26 01:13:33] @trueorfalse

Hi,  I'm utilizing Polars to create indicator values for backtesting,  when I look at  Data section what I see mostly related with ParquetDataCatalog and I'm not able to find correct place to utilize my parquet files with out entering Catalog. 
if is there defined way can someone redirect me ?

---

#### [2025-10-26 15:32:23] @colinshen

Hi，Does this docs mean I cant use streaming mode for low level api？https://nautilustrader.io/docs/latest/concepts/backtesting

**Links:**
- Backtesting | NautilusTrader Documentation

---

#### [2025-10-26 17:11:25] @trueorfalse

I think, in your case and my case only way is https://nautilustrader.io/docs/latest/concepts/message_bus

**Links:**
- Message Bus | NautilusTrader Documentation

---

#### [2025-10-26 17:12:34] @trueorfalse

not sure exactly

---

#### [2025-10-26 17:56:47] @trueorfalse

also you can save result, put data.,   rerun.

---

#### [2025-10-26 18:07:58] @fudgemin

nautilus_trader/persistence/config.py. Certainly possible in both back and live nodes

---

#### [2025-10-26 18:25:47] @trueorfalse

<@391823539034128397> what <@175701522644992000>  asks about low level api, persistence component related with catalogs. What I understand he has different source of truth. 
may be if he can provide a little bit more context would be better.

---

#### [2025-10-26 20:40:35] @one_lpb

Hello, I tried to find doc about creating a personnal adapter for live data ingestion from Trade data feed (from Polygon.io). Someone have a link ?

---

#### [2025-10-27 03:06:55] @trueorfalse

https://github.com/nautechsystems/nautilus_trader/tree/develop/nautilus_trader/adapters
would be helpful

**Links:**
- nautilus_trader/nautilus_trader/adapters at develop · nautechsyste...

---

#### [2025-10-29 10:55:15] @akajbug

Also helpful

https://nautilustrader.io/docs/nightly/developer_guide/adapters

**Links:**
- Adapters | NautilusTrader Documentation

---

#### [2025-11-02 21:13:49] @aleburgos.

Hi everyone, I was away for a while ( since version 1.219.0 ), I'm wondering if the possibility to download data still is underdevelopment? <@965894631017578537>

---

#### [2025-12-15 12:38:35] @francomascarelo_ai

Hi everyone. Is there a more optimized way to convert a CSV file of ticks to Parquet Nautilus? Every time I try, it uses up all my RAM and crashes WSL2.

---

#### [2025-12-15 12:57:38] @yfclark

use yield to write multi times

---

#### [2025-12-15 15:10:26] @francomascarelo_ai

Sorry, I didn't understand. I have 30GB of data in ticks from xauusd (forex).

---

#### [2025-12-15 15:11:05] @francomascarelo_ai

I'm trying to convert the CSV file to Parquet Full and Parquet Sessions.

---

#### [2025-12-15 21:42:04] @yfclark

I mean why don't you split the large file into smaller ones, then transform and write those smaller files. Yield is Python syntax that can help you achieve lazy loading for large files.

---

#### [2025-12-17 04:26:22] @pdlloyd

hi there. I'm trying to work through the Nautilus tutorials but there are a bunch of references to "short-term-interest.csv" which doesn't exist in the Docker image and I can't find it on the GitHub repos. Does anyone know where that file is located or where I can download it from?

---

#### [2025-12-17 04:28:16] @pdlloyd



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924504069433876550/1450706141104570471/image.png?ex=694ac320&is=694971a0&hm=b33ca5750b89be7a533b6c4ac12443d86735e4d4016b4c7a10faa46cecadfc59&)

---

#### [2025-12-17 04:28:38] @pdlloyd

I know it says it's optional, but it's all over the tutorials and I have no idea where it comes from

---

#### [2025-12-17 04:37:02] @pdlloyd

The plot thickens (and I need to read my error messages better). There's a problem with the fsspec dependency: `ImportError: Please install fsspec[http] to access github files >1 MB or git-lfs tracked files.`

However, if I run `!pip install fsspec[https]` in the notebook, I am told `Requirement already satisfied: fsspec[http] in /usr/local/lib/python3.13/site-packages (2025.12.0)` and the cell still fails

---

#### [2025-12-20 17:51:31] @aock

Hi, I’m new to Nautilus Trader.
I have historical data in CSV format (e.g. Binance public data or Tardis academic plan). Before backtesting, Nautilus requires an Instrument, but I’m not sure how to create it for historical data.
I tried using InstrumentProvider, but it seems to only return currently trading symbols, while my CSV may contain delisted or delivered instruments.
How should I properly create or define an Instrument for CSV-based backtesting?
Thanks in advance.

---
