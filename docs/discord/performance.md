# NautilusTrader - #performance

**Period:** Last 90 days
**Messages:** 57
**Last updated:** 2025-10-23 04:00:36

---

#### [2025-08-06 04:21:17] @daws6561

Is there support for shared indicator/feature caching across strategies? e.g, if 5 strategies all need a 20-period EMA, can we calculate it only once?

---

#### [2025-08-06 07:08:49] @cjdsellers

You could register an `ExponentialMovingAverage` indicator for updates with one actor/strategy, and then pass it to many. I haven't testing this myself though and nothing built-in for this. You can store arbitrary data in the cache although this isn't efficient, or publish signals on the message bus many actors/strategies can subscribe for (probably best practice at this point)

---

#### [2025-08-06 18:48:19] @daws6561

Thank you! I'll try that approach (publihsing signals to the message bus that actors/strategies subscribe to -- that's exactly what I'm looking for).

---

#### [2025-08-06 18:56:53] @premysl_22228

Be sure, that message bus overhead (message serialization and deserialization isn't cheap) isn't equivalent to the computational overhead of the indicator. I would recommend you to run controller which distributes the data downstream if the performance is what you are really after. But there are no examples of doing so and you will probably hit some bug, if you do it this way - it will be for longer run.

---

#### [2025-08-06 19:25:04] @daws6561

"I would recommend you to run controller" -- what's 'controller' in this context? And good point about the message bus overhead, thanks. For clarity, my intention here is to accomplish an efficient EMA cross grid search where it only passes over the dataset once, and only calculates each EMA once per datum (passing the value to whatever actors/strategies subscribe). Very new here so thanks for the help! Just trying to get the basics down.

---

#### [2025-08-06 19:40:22] @premysl_22228

Controller is an actor, which executes other actors and have direct method access to them. For example see: https://github.com/nautechsystems/nautilus_trader/pull/1939/files . But I think, to be fully working, the actor must be fully registered to the registry, message bus, linked to clock, etc...

**Links:**
- Add Multi-Instrument Rotation Trading Example with Controller for B...

---

#### [2025-08-06 19:41:28] @premysl_22228

(...we still have to make a working example of controller...)

---

#### [2025-08-06 19:46:39] @premysl_22228

What library are you using for the grid search? You are running hyperoptimization for the whole trading system at once or you are running more actors at once to speed up per generation?

---

#### [2025-08-06 20:00:38] @premysl_22228

Look here: https://github.com/nautechsystems/nautilus_trader/blob/adf5b331c4f7aab378edb8ae1b7d5d61f9b7ddd9/nautilus_trader/trading/controller.py#L42. Create a class which inherits from this and use methods to create actors.

---

#### [2025-08-06 20:04:20] @daws6561

I'm not using any library for the grid search currently since my goal is very minimal. I was intending to achieve a workflow where I could pass parameters in using something like `EMA_fast = range(5,30, 1)` and `EMA_slow = range(20,100, 5)` and have some code generate the strategies with those specific parameters, and handle plugging up components and subscriptions as specified. But bear in mind, it's possible I'm thinking about the whole thing wrong though or in a way that's not aligned with NT philosophy. I just want to ensure I'm doing things as efficient as able, i.e not passing over datasets multiple times or redundantly recomputing indicator values on every bar/tick. 

Thank you for the pointers! I'll check out that code and try that approach.

---

#### [2025-08-06 21:19:59] @premysl_22228

Won't your strategies interfere with each other if running under one instance of trader? What is your scoring function?

---

#### [2025-08-06 21:47:39] @Wick



**Links:**


---

#### [2025-08-06 21:53:40] @daws6561

Did that delete my message? I was just editing it for clarity.. Anyway, to recap, I don't know if that will interfere with `trader`, I'm only just getting my feet wet. I ran the EMA cross example, and wanted to try a grid search next, but couldn't figure out the canonical way to do it efficiently and avoid a) passing over the data once per parameter combo and b) minimizing redudant calculation of EMA values during the parameter sweep run.

In my previous system I'd often do runs with no execution/portfolio/risk modules, just signal generation (which I'd store and analyze later). That would be an easy workaround to avoid interfering with `trader` if that would be a problem.

---

#### [2025-08-06 22:50:21] @premysl_22228

If you just generate signal, it won't interfere. Be sure, to report any bug in GitHub please, as grid search done this way is something, which was probably never done before in my opinion, and might exploit something, we would like to have debugged.

---

#### [2025-08-06 22:55:59] @premysl_22228

(In your place, I would run a separate fork paraelly for each execution and this is probably the common modus operandi for hyperopt as there is no support for multithreading without GIL locking and on multicore system will run probably faster then your idea)

---

#### [2025-08-06 22:56:15] @premysl_22228

<@907401512299401328>

---

#### [2025-08-07 00:19:13] @daws6561

What is most performant is what I'm after, just trying to figure that part out, and in general I try to minimize iterations over the data for performance. Is there documentation or examples on this approach (seperate forks for each execution)?

---

#### [2025-08-07 01:03:27] @premysl_22228

No documentation is currently present on the issue. But it is really easy.  See https://docs.python.org/3/library/multiprocessing.html , use Pool with maxtasksperchild=1 (there are some mess like memleaks, which aren't cleaned up properly, so this ensures, you start with clean heap). You just map over some function and get results. If you have multicore system with >8 cores, this will be very probably more performing solution, even through you will be iterating the same dataset multiple times. Do you use low-level API or high-level API?

**Links:**
- multiprocessing — Process-based parallelism

---

#### [2025-08-07 20:07:48] @daws6561

Thanks! I'll check that out. I was using the low level API when I was getting things set up.

---

#### [2025-08-20 14:24:35] @neupsh

hi, 

I am backtesting a simple MACDStrategy based on the built in MovingAverageConvergenceDivergence indicator with historical futures 1-MINUTE-LAST bar data that is stored in parquet catalog.  It is taking awfully long time (51 minutes) to go through just 50 days of data.

This does not seem quite right, but I am very new to nautlius (and to trading in general) so wondering if it is expected to be this slow. I know event based systems will have less throughput than vectorized ones, but I was expecting at least thousands of bars per seconds (if not 10s of thousands). My machine is Dell laptop with i7 6820HQ processor (2.7ghz) if that helps correlate. The data itself is small and cpu usage and memory usage both are not high.

This makes me feel like I am doing something wrong or overlooking something.  (default configuration that throttles to give realistic wait, or because of logging or something along those lines). and I wanted to check with folks here 🙂 

What is a typical throughput for nautilus (ballpark as it would probably depend on the system it is running on) in terms of Bars processed per unit time?

BacktestEngine: Run started:    2025-08-20T13:22:14.485953000Z
BacktestEngine: Run finished:   2025-08-20T14:12:37.844968000Z
BacktestEngine: Elapsed time:   0 days 00:50:23.359015
BacktestEngine: Backtest start: 2023-08-01T00:00:00.000000000Z
BacktestEngine: Backtest end:   2023-09-20T00:00:00.000000000Z
BacktestEngine: Backtest range: 50 days 00:00:00
BacktestEngine: Iterations: 16_681
BacktestEngine: Total events: 34_886
BacktestEngine: Total orders: 16_350
BacktestEngine: Total positions: 16_350

---

#### [2025-08-20 14:28:55] @neupsh

Here is the script I used for that backtest.  `helpers.get_project_root()`  is from another file, but it just gives the Path to the project root.
If anyone can confirm this is normal, or point me towards what I am doing wrong, I would really appreciate it  🙏

**Attachments:**
- [backtest_highlevel.py](https://cdn.discordapp.com/attachments/1138719912286748672/1407733143305195651/backtest_highlevel.py?ex=68fae467&is=68f992e7&hm=dbedfa5119ae59d2f9c6d29fbf47cdd28fb6f2cb65fa088f124adc55fecb3f32&)

---

#### [2025-08-26 10:37:48] @zupet

Hi guys, after reading about the architecture of Nautilus, what is the best retail CPU on the market in terms of backtesting performance right now? 9950x3d? Intel 285k? Apple M4 family? Did anyone actually test it?

---

#### [2025-08-27 22:59:52] @greeny_the_trading_snake

Hi <@780089963009277962> 

I personally would go for ARM architecture with a lot of cores. currently I am running my backtests that way that I split it to separate days and run each day as separate process. I am running it on Apple M1 Ultra which has 20 cores - M4 Pro will be similar. from apple family I would go for M3 Ultra or wait for M4 Ultra..

my personal recc would be this crazy 192 core CPU where you can backtest 192 days in parallel at once lol 😄

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410398441892479027/image.png?ex=68fab368&is=68f961e8&hm=86917db0e82e1fabbaf9f84c6b6f39905899c578832fb935c09ea66b63d9a83f&)
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410398442169172091/image.png?ex=68fab368&is=68f961e8&hm=1b59f29dcfa1beb7e5682251d57b199cf4e53735ec89059ea89bca76b96c20b4&)

---

#### [2025-08-27 23:18:09] @greeny_the_trading_snake

here are some cheaper alternatives though - I would aim for parallelism

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410403040850083911/image.png?ex=68fab7b0&is=68f96630&hm=bbdadce0accc575c1c69abeb6fb6f6bf0ded1089dd5d045f2420f4dfbd016a6c&)
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410403041131106354/image.png?ex=68fab7b1&is=68f96631&hm=0eeb83e5314c4f1ef27adb5340209b7113626fb9137c72838a5f44947664e205&)

---

#### [2025-08-28 00:14:30] @dkimot

I believe they implied there will be no M4 Ultra. When asked about it I remember the answer was "Not every generation will get an Ultra"

---

#### [2025-08-28 00:16:18] @dkimot

Could look at the framework desktop. I looked at getting one for this but realized it was overkill for me rn. I can repurpose other stuff. Uses the new AMD AI chips. Can get a Max+ 395 with 16-core/32-thread CPU @ 5.1GHz and a 40-core GPU and 128GB of ram for $2k (before storage)

---

#### [2025-08-28 00:16:48] @greeny_the_trading_snake

they put M2 Ultra to these, I think they will put M4 Ultra maybe again to these

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410417802422124637/image.png?ex=68fac570&is=68f973f0&hm=962fcaa838e597730f4583524891a9c1f36aca27972c3f0c7a987e99ccdf1909&)

---

#### [2025-08-28 00:17:53] @dkimot

Then you have to pay the "Pro" premium. I remember the Mac Pro was 2x the price of the Mac Studio for the same SoC. The difference was ports and extensibility. Which, prob a non-issue for this use case--unless you want to record studio quality audio too

---

#### [2025-08-28 00:21:21] @dkimot

But, perks of the framework as well: it's *okay* for local LLM's, if that's your thing. Memory bandwidth is king and it's not great (256GB/s vs. the M3/M4's 400GB/s and it's dwarfed by the 5090's 1TB/s) but you can address up to 96GB of that 128GB to the GPU (same limitation as the Apple silicon)

Apple says the Ultra's can do 800GB/s but based on user reports they're getting there by saying 400GB/s + 400GB/s is 800GB/s. Which is technically true but for local LLM's you can only use 400GB/s for inference, as I understand it

---

#### [2025-08-28 00:21:22] @greeny_the_trading_snake

this was a good idea from chat GPT some dual CPU with 64 cores and you can backtest like a flash - me running with M1 Ultra on 20 cores, it's not bad but it takes some time

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410418953976549436/image.png?ex=68fac682&is=68f97502&hm=07b5fd58befdfcf7942eb100d73bf71d718df6027b07d4fe1f9bfd28e7754ec2&)

---

#### [2025-08-28 00:23:06] @dkimot

Yeah, it also depends on what you want to do with it. If you're talking about building a local backtest server, an older server CPU is probably what you want. If you want a local workstation I bet your M1 Ultra is better. I'd imagine orchestrating a backtest server to be somewhat labor intensive vs. running something locally

---

#### [2025-08-28 00:27:21] @dkimot

But, use what you have <@780089963009277962> and get something more specialized when you've hit real limits. Amazon also has refurbed Dell Optiplex's for super cheap sometimes. I've got a 4 year old one that was $120 and I've got a working quad-core computer. It's not my main computer but one of those running a backtest script on the shelf isn't a terrible idea either. It's significantly less than a $2k 10 year old server or an unproven framework desktop. Check craigslist/FB marketplace/whatever is applicable in your region or buy an old workstation from a business liquidation place

---

#### [2025-08-28 00:32:11] @greeny_the_trading_snake

we need more info about purpose and budget - if he needs rough performance then aim for most cores and parallelism, if he wants a workstation which can also run LLMs maybe get M3 Ultra Mac studio

---

#### [2025-08-28 11:46:06] @zupet

I am updating my daily workstation, which is both Windows + Linux and is usually CPU intensive, since I do a lot of backtesting. I've pre-ordered the Framework Desktop, but was thinking whether it was a good move in terms of performance, whether maybe 285k might be better for single threaded workloads. If I was only using Nautilus, I would probably wait for the M4 Ultra ("Hidra"), but I also use other software which is x86 architecture and it does not play well in Parallels, so I generally prefer my desktop to be x86 with Windows/Linux and laptop to be a Macbook Pro with ARM64 architecture.

So this made me think about Nautilus and what is currently the best overall CPU for backtesting (don't want to go crazy though, like the 192 cores mentioned above 🙂 )

---

#### [2025-08-28 15:04:37] @greeny_the_trading_snake

then what you mentioned above looks like a solid decision for a workstation. 

I think both are monsters, but I would maybe go for that 24 core intel then (even if intel is lately losing to amd) 

my reason would be the backtesting - I can run easily 24 processes with that in parallel. with AMD you can run only 16 effectively, because when you run one per thread then the second process on a single core will get only 20-30%. so 24 cores would be better for backtesting

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410641228390989845/image.png?ex=68faecc5&is=68f99b45&hm=5ef428f3c1b17297ea2ed6f22f2ce807374824f4d18c6577baf7a017dbf5f79d&)
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1410641229024333876/image.png?ex=68faecc5&is=68f99b45&hm=a7a6eddc85290b0e9525bd2a7e68b6079962876b1b646b488fff4d48ce69996a&)

---

#### [2025-08-28 15:04:44] @greeny_the_trading_snake

<@780089963009277962>

---

#### [2025-08-28 17:03:29] @zupet

Now that you mention it, I am leaning towards Intel too. I've read that Z890 is much less buggier (bios, drivers) compared to X870E boards, also someone mentioned that the 285k combined with CUDIMM 8000-8400 MT/s is pretty darn snappy (which was also said about Framework Desktop, I guess that is because of the 8000 MT/s soldered RAM and high bandwidth)

---

#### [2025-09-19 02:13:57] @aaron_g0130

i have the same question here, want to know the baseline speed in general of each backtest form, especially 1min bar backtest. I've tried using empty on_bar function to just streaming bar for speed test, Starting backtest with 1951200 bars and completed in 36.71 seconds with no logic calculation at all. It runs 54000 bars per second ( all logs are disabled).

---

#### [2025-09-22 12:17:51] @faysou.

Please don't duplicate messages across channels

---

#### [2025-09-22 12:19:16] @tobias.p

sry

---

#### [2025-10-12 15:56:42] @megafil_

hi guys, just getting started but i am pretty sure i am not using this the right way:
my plan was to use the ParquetDataCatalog to organize my data and feed the backtest engine, to keep it simple i started with daily bars for about 500 instruments.
instrument creation and import seems pretty slow, but what is really really slow is the query to get the bars into the engine. 
i do the following:
bars = catalog.bars() <- 40seconds for 20MB of bar data in 500 pq files.

also, lookup if an instrument is already registered is pretty slow. i assume it is because the catalog doesnt keep anything in memory.

---

#### [2025-10-12 15:57:52] @megafil_

should i avoid this catalog altogether? what is the most performant way to do this? i plan to process gigabytes of data at least but this seems infeasible with the parquetdatastore

---

#### [2025-10-19 21:00:49] @megafil_

slow read was cause i read data on a windows partition from wsl2 😢

---

#### [2025-10-19 21:53:22] @yfclark

change to wsl1，you will see improve in IO

---

#### [2025-10-19 23:00:21] @faysou.

change to a macbook and you will have a machine that flies. windows is really inferior, I've switched to mac last year, for a long time I was reluctant to move away from windows, but macbooks are like linux with no hardware problem (and great hardware as well)

---

#### [2025-10-20 12:02:57] @.islero

Hello everyone! Could you please help me to understand what’s causing Nautilus Trader 1.221.0a20250922 to run slowly for me? 
I’m running it in Jupyter Notebooks with log_level=”ERROR” and backtesting an empty strategy that only subscribes to 1-minute external bars (from 2021-01-01 to 2024-12-31) and just iterates over them, nothing else. It still takes around 1 minute to backtest that range, is it ok?
I assume the Jupyter Notebook is a bottleneck here and it’s the cause of the performance issues.
My machine: m3 max MacBook Pro

---

#### [2025-10-20 12:26:08] @.islero

I attempted the same backtest directly without using the Jupyter notebook. It took me 58.770255 seconds, whereas it took 60.121446 seconds on the Jupyter notebook. So, maybe it’s ok🤷‍♂️

---

#### [2025-10-22 02:31:15] @fudgemin

i think thats a bit slow. im still new to the system. I test COIN 1 min for 2 years, in 11 seconds. 

2025-10-22T02:28:57.936444463Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Run config ID:  2bdeb6d8580474611669dc73f191b10f4c382ebed05041cfc4634a8f9f2459d7
2025-10-22T02:28:57.936447512Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Run ID:         b9a3801d-6547-4122-be9a-0972083ac41b
2025-10-22T02:28:57.936462079Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Run started:    2025-10-22T02:28:46.535702000Z
2025-10-22T02:28:57.936468081Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Run finished:   2025-10-22T02:28:57.936312000Z
2025-10-22T02:28:57.936501955Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Elapsed time:   0 days 00:00:11.400610
2025-10-22T02:28:57.936504341Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Backtest start: 2023-08-01T00:00:00.000000000Z
2025-10-22T02:28:57.936506087Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Backtest end:   2025-07-31T15:59:00.000000000Z
2025-10-22T02:28:57.936514865Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Backtest range: 730 days 15:59:00
2025-10-22T02:28:57.936518113Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Iterations: 194_349
2025-10-22T02:28:57.936521801Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Total events: 0
2025-10-22T02:28:57.936530520Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Total orders: 0
2025-10-22T02:28:57.936541935Z [INFO] LAZY_LOAD_TEST-001.BacktestEngine: Total positions: 0


THats using very basic strategy logic, or nearly 'empty' as you say. Im on an 4cpu 16gb intel instance

---

#### [2025-10-22 04:07:25] @.islero

Thanks <@391823539034128397>. I’ll also try to backtest two years of data for comparison.

---

#### [2025-10-22 04:08:37] @fudgemin

yea ive run quite a few now. i can do 500k iterations in <15s. Your 60s is 'off'

---

#### [2025-10-22 04:10:27] @.islero

<@391823539034128397> For me, it was over 2 million iterations in my initial test

---

#### [2025-10-22 04:10:28] @fudgemin



**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/1138719912286748672/1430407939356758047/message.txt?ex=68fa5374&is=68f901f4&hm=5011d07b944c97b89fc2936d290b24ca81df45f896087951640f2887229e82c4&)

---

#### [2025-10-22 04:13:13] @fudgemin

2m on 1 min data? something wrong maybe? if thats the case, maybe your in line...

I think 1 min data is 390 minutes a day * 150 per year. only like 60k bars a year

---

#### [2025-10-22 04:17:08] @.islero

<@391823539034128397>  I’ve downloaded 5 years of futures data from the databento, idk should be ok. It’s a reliable source.

---

#### [2025-10-22 04:17:53] @fudgemin

oh yea those trade extended and regular hours i think

---

#### [2025-10-22 04:18:04] @fudgemin

certainly a relaiable source

---

#### [2025-10-22 09:04:27] @.islero

<@391823539034128397> you were right, there is duplicated data for S&P500 mini with different symbols.

---
