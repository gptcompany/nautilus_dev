# NautilusTrader - #performance

**Period:** Last 90 days
**Messages:** 35
**Last updated:** 2026-01-07 01:29:48

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
- [message.txt](https://cdn.discordapp.com/attachments/1138719912286748672/1430407939356758047/message.txt?ex=695e8574&is=695d33f4&hm=a3bc441cfdfefad9d7b4270a799b16460bdfda24fe9af5453078807ea447e9ea&)

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

#### [2025-11-01 08:34:11] @one_lpb

Hello ! 

Is it faster to pre-process the aggregated bars from the Trades and run from that pre-processing + the Trade data to get better accuracy on position fills, rather than requesting internal aggregation at each run?

So, in case 1, does Nautilus actually use the pre-aggregated bars directly and use the Trades only to manage positions, without going through all the Trades again on each run?

---

#### [2025-11-06 13:35:42] @one_lpb

No one ? 😄 I tried to figure it out but it looks like if I add Trades to backtestDataConfig and 1 minute bars, it will go through every Trades not only for resolving positions... And I only ask for bars in my on_start  method

---

#### [2025-11-06 16:30:37] @fudgemin

may need to confirm this, but as for price updates attached to order type requiring them:

NautilusTrader's matching engine uses:

If Quotes Available: Updates trailing stop on every bid/ask update
If Trades Available: Updates on every trade tick
If Only Bars: Updates only on bar close

In the case of pre agg, certainly any compute done externally, and loaded on demand without transformation would be less expensive on the running node if i understand correctly.

---

#### [2025-11-07 10:15:09] @one_lpb

Thanks for anwsering !
So there is no way to give Nautiluse access to Trades and bars and to tell him to use Trades only on opened positions ?

---

#### [2025-11-12 09:33:22] @estebang17.

Hey Greeny, coudl you give some insight on this? I'm thinking on how to improve the speed of things, as my backtests run quite slow at the moment

---

#### [2025-11-12 10:07:39] @greeny_the_trading_snake

in the end I wrote my own python engine which runs backtest day by day. on each core one day, this way I can run 20 days in parallel

---

#### [2025-11-13 18:50:17] @mk1ngzz

im running a hetzner dedi server with 32 cores (amd epyc 7502p), 128gb ram and 4tb nvme ssd for $125/mo

---

#### [2025-11-18 01:17:49] @micro_meso_macro



---

#### [2025-11-18 11:28:19] @jimk1401

gsx1wy

---

#### [2025-11-18 21:39:34] @fudgemin

di you run trading nodes on this setup? broker integration? Im wondering what the routing latency is like, assuming you  remote from USA? Ive been eyeing a migration to hetzer for some time now, simply based on cost. Lag was the only concern of mine, as simple ping to server was 100ms + from Canada. 

Im paying more then 3x that, for less then 3x the resources lol. Digital O

---

#### [2025-11-19 06:57:37] @mk1ngzz

no, i'll be running trading nodes in hong kong. the dedi server in hetzner is purely for backtesting, analytics and other core components

---

#### [2025-11-19 06:59:29] @mk1ngzz

but i'm considering cancelling the hetzner one given what u minimum have to pay for dedi servers in hong kong

---

#### [2025-11-29 09:12:52] @heliusdk

Degration surely is a biatch.....

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1138719912286748672/1444254779105742969/image.png?ex=695ecc54&is=695d7ad4&hm=609ac6cf086a0a329e42552c6225932ccd6bb52cf0350892adf1f694191949a4&)

---

#### [2025-11-29 10:01:47] @javdu10

Wow is that the visualization package or custom ?

---

#### [2025-11-29 14:25:36] @heliusdk

Custom, finished it yesterday

---

#### [2025-12-01 23:33:29] @fudgemin

why are you testing from 2016? Test the last year or two only. Then determine your benchmark based on that. I kno for fact market dynamics on most equities have changed, and do change. 0 dte inception rewrote the market. 

Suppose i told you i had a strategy, right now, that does 10% a week, and has for the past 6-10 weeks. Are you going to trade it, with discretion? or are you going to say its no good since you require 5 years of backtest or validated results?

start at now, and work backwards to validate. not the other way around

---

#### [2025-12-02 03:02:54] @lisiyuan666

Wow that's really good price! I checked it myself and the lowest they have for the same spec is $214.09 with 600GB ssd. How did you get it so cheap?

---

#### [2025-12-02 09:35:50] @mk1ngzz

you need to go to the auctions page

---
