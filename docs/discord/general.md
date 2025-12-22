# NautilusTrader - #general

**Period:** Last 90 days
**Messages:** 251
**Last updated:** 2025-10-23 04:00:09

---

#### [2025-07-28 15:52:20] @aleburgos.

I'm testing the latest version, the performance improved a lot! some backtest reduce his time to seconds instead of minutes

---

#### [2025-07-29 14:11:25] @tobias.p

zero comission, very low spread and high leverage especially on dax and nasdaq cfds with almost no spread. i just love the simplicity of the platform and competition between brokers to offer the best liquidity.

---

#### [2025-07-29 14:11:43] @tobias.p

also xauusd / gold

---

#### [2025-07-29 14:12:12] @tobias.p

and prop firms like ftmo and others offer mt5 as their main platform

---

#### [2025-07-30 07:07:42] @faysou.

I suppose the difficulty is to get a rest api to mt5. If you have that then you could write an adapter in rust for it. If you get an openapi spec to the rest api you should be able to use a tool like https://openapi-generator.tech to generate a rust base client, then you would need to integrate it with a nautilus adapter. I once did this client generation for interactive brokers but haven't worked more on it yet.

**Links:**
- Hello from OpenAPI Generator | OpenAPI Generator

---

#### [2025-08-01 10:01:06] @fourofspades4

<@757548402689966131> 

<@1268644683945480354> is an impersonator. Probably should ban them.

---

#### [2025-08-02 16:32:28] @zupet

What? What has changed that caused such a dramatic improvement?

---

#### [2025-08-03 11:32:16] @liguifan

Hi guys , do you know will Nautilus Trader support more exchanges such as gateio, coinex in near future?

---

#### [2025-08-03 12:29:42] @premysl_22228

Hi. I am not sure, but I would say, that unless some good sole implements an adaptor and PR it, I would say, that no. The main focus in terms of adaptors is now on major exchanges, not the minor ones.

---

#### [2025-08-03 12:31:55] @premysl_22228

But if you need it really bad, you are welcomed to implement it in both v1 (Python) and v2 (Rust), or if you need it some time later, then v2 (Rust). 🙂 Or you can hire someone via <#1318519015643025509>  to do it for yourself.

---

#### [2025-08-03 13:10:24] @puregamma

Should we open source a strategy library, including the basic A-S MODEL high-frequency strategy and the LPPLS MODEL short-selling short coin strategy?

---

#### [2025-08-03 13:11:05] @puregamma

I am happy to share my experience and running strategies

---

#### [2025-08-03 13:17:19] @premysl_22228

It's a great idea. By the way, I think, later, we should make some repo Awesome Nautilus Trader, where we accumulate all the useful community resources (as a links to other repos), which accumulates here in chat and on GitHub.

---

#### [2025-08-03 13:40:13] @premysl_22228

Later, I would like to have some website like this: https://strat.ninja/ranking.php, but probably it will be outside my capacity to make the website itself, but I have basic framework to convert freqtrade strategy to NT strategy (it is still in Cython, I will need to rewrite it to Python + Rust)...when community grows, I hope, I will find out someone to help me with this - if I make the framework universal and fully automatic, we have tons of strategies ready at disposal and ready for creation next strategies together with more reliable benchmarks then freqtrade provides.

---

#### [2025-08-04 07:50:23] @tobias.p

Following up on this "thread" again, if anyone is interested in working together on writing the MT5 "Meta Trader 5" adapter in rust (i am still learning rust) -> I have now found both a REST Api and a ZMQ api on github that seem to work, otherwise i thought about running the pyRPC MT5 api inside rust to get these few result account/position/ or tick/bar values easily that way. mt5linux: (https://github.com/lucas-campagna/mt5linux)
kasmavnc/wine/mt5lin ux container that makes it easy to run on x86 architecture servers:  (https://github.com/gmag11/MetaTrader5-Docker-Image) -> if anyone has trouble running this i fixed the Dockerimage to make this repo work again due to naming changes upstream. I can provide the "fork" of the repo if needed.

**Links:**
- GitHub - lucas-campagna/mt5linux: MetaTrader5 for linux users
- GitHub - gmag11/MetaTrader5-Docker-Image: Docker image that runs Me...

---

#### [2025-08-04 07:51:17] @puregamma

I'm using freqtrade, which is suitable for low-frequency trading strategies. Currently, I manage the entire hedge fund's risk management and strategy by myself. Nautilus is suitable for HFT strategies.

---

#### [2025-08-04 07:53:01] @puregamma

^^

---

#### [2025-08-04 07:57:55] @tobias.p

what do you mean exactly with your ds vs. deep blue statement? any blogs or reading material on this topic? what exactly happened in 2014?

---

#### [2025-08-05 02:45:52] @daws6561

Hi, I'm just getting started, I wanted to do a parameter grid search to get a feel for things. How do I ensure I'm only running over the dataset once rather than once per parameter combination?

---

#### [2025-08-05 02:57:53] @daws6561

Or is this something the user is expected to build out themselves?

---

#### [2025-08-05 19:37:47] @daws6561

Where is this system at in regards to visualizations and post-process analysis?

---

#### [2025-08-06 07:01:27] @cjdsellers

Hi <@907401512299401328> 
Welcome and thanks for reaching out.
Potentially this is along the lines of what you had in mind, or maybe not: https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/common/config.py#L169

---

#### [2025-08-06 13:02:05] @kylemac1919

Hi Nautilus Traders! Im new here, but very interested in learning rust for algorithmic trading. Should I start learning rust on (https://www.rust-lang.org/learn) . Or is there a better suggested roadmap to be able to eventually contribute to Nautilus Trader?

**Links:**
- Learn Rust

---

#### [2025-08-06 14:43:02] @cmdrhodes

Hi all. I am a senior dev and tech lead at a family office that has implemented a very similar architecture to Nautilus for my firm internally.

Although I have only just found the project due to it being so high on HN, I just wanted to extend a thanks to the team here for opening the core with such thorough documentation. Building a system to enable our traders to execute has been a massive challenge as I am sure you all know.

Working with mostly trading oriented quants, having Nautilus to point to when I make similar decisions will be a god send.

I just wanted to extend my appreciation for what you all are doing and wish you the best!

---

#### [2025-08-06 16:51:22] @premysl_22228

Hi. What is your background? If you know C/C++, I would recommend you to pick a simple task from issues and start immediately with LLM covering your back. It's very similar to modern C++. If you don't know it, I would recommend you to start with tutorial, then use some LLM (like Claude Opus) to give you some coding tasks and let it review it after you are done, and once you are confident enough, you understand RAII, some basic concepts,  etc., DM me and I will find you some simple task to start on (e.g. there are some aggregators, which needs to be implemented in Rust and gives you hands on experience).

---

#### [2025-08-06 16:58:15] @kylemac1919

Hi <@1353826739851362345>, my background is in computer science and extends in algorithmic trading. main language is c++ with more recently doing algo trading on python. thanks for the recommendations! Going to take a look at some trivial issues and see if i can work alongisde the LLM. I'd love to send you a DM, going to take sometime to dive into the documentation and the issues you recommended 🦀

---

#### [2025-08-06 17:45:08] @premysl_22228

That's great background for this kind of work! Let me know, if you have some problems with setting up your dev environment (there are some obsticals for fluent flow, if you don't setup it correctly) and the https://github.com/nautechsystems/nautilus_trader/issues/2603 is just nicely isolated as a starting point. I think, it is enough to implement it just in Rust, as soon we will migrate all Cython to Rust PyO3.

**Links:**
- Implement remaining bar aggregation methods · Issue #2603 · naute...

---

#### [2025-08-06 17:46:31] @premysl_22228

I recommend using IDEA Ultimate, but it's up to your preferences. Some of us use pure neovim and some VS Code.

---

#### [2025-08-06 17:57:10] @kylemac1919

Wow, thanks for this. I'll definitely keep in touch with any issues I have. Tonight is going to be my first dive into Rust so Ill make sure to start there.

---

#### [2025-08-06 17:58:15] @kylemac1919

I was also thinking of making the switch to vim from traditional vs code, I think I've played enough vim adventures to make the leap! 😄

---

#### [2025-08-06 18:06:41] @premysl_22228

Do, as you wish.😀  I have long resisted (for 5 years at least) to all IDEs and used vim even in corporates. It was hardcore, since my productivity was reduced due to it, needed to generate website documentation of projects, have specific requirements,... and since I switched to IDE, my productivity just grew for I would say 20%. 😀 Vim is good for understanding the complete basics, for server setup, config files, quick edits, for fun and for feeling being the "hacker", but in reality, you just sacrifice part of the energy you have to problems, which might be solved automatically.

---

#### [2025-08-06 18:11:11] @premysl_22228

But to people who never done that, I would recommend to try develop some time just in vim. It's good experience - you start seeing things you haven't seen before eg. in language designs (never thought Java is so ugly language until developing in it in vim 😀) and so on.

---

#### [2025-08-07 06:43:21] @gz00000



---

#### [2025-08-07 08:10:49] @premysl_22228

Just out of pure curiosity, the Discord is accessible out of mainland or is it Taiwan and Hong Kong based?

---

#### [2025-08-07 08:24:03] @gz00000

Discord is accessible from mainland. 🙂

---

#### [2025-08-07 14:07:47] @cgeneva

Hi, I would like to Nautilus to implement several equity strategies. I am on windows, v1.219, use python in vscode. I struggle to find the correct data structures to use in general. Each classes seems to be accessible from various place with different constructor.  Let's take Instrument or InstrumentId.  if i use :  from nautilus_trader.model.identifiers import InstrumentId instrument_id=InstrumentId(symbol=api.Symbol(symbol), venue=api.Venue(VENUE_NAME)) .   I get TypeError: __init__() takes at least 8 positional arguments (2 given)

---

#### [2025-08-07 14:09:01] @cgeneva

It should be working if I check  test_kit\provider.py file

---

#### [2025-08-07 14:23:45] @cgeneva

Should I always create Instrument the way it is done in TestInstrumentProvider ? no other choices ?

---

#### [2025-08-10 19:37:57] @chaintrader

what is the average profit you guys are making in here?

---

#### [2025-08-10 22:31:01] @drose1

Question about static analysis:
I installed nautilus trader with `uv`

Got my lib inside site-packages
`.venv/lib/python3.11/site-packages/nautilus_trader/backtest/engine.pyx`

I work in Cursor and was wondering how to get syntax highlighting? Are `.pyi` or stubs supported or do I need to write them myself?

Is the best way to just clone the repo and look a the source code on my other monitor?

---

#### [2025-08-10 22:33:30] @drose1

Ah nevermind there's a thread from before https://discord.com/channels/924497682343550976/924506736927334400/1304947233636221051

---

#### [2025-08-10 22:44:53] @cjdsellers

Hi <@319835782485508106> 
Yes, unfortunately this is a big pain point and not so easily solved all things considered. It has been attempted a couple of times and this PR was the best attempt yet but was closed in the end (see discussion for reasons) https://github.com/nautechsystems/nautilus_trader/pull/2819

We can look forward to type stubs auto generated on build for v2, and it is possible to either write them yourself, or I think @woung717 intends on making their work available on GH

---

#### [2025-08-11 09:25:10] @didierblacquiere

Hi Put, im looking to use mt5 have you got a couple minutes for a convo or messsages just for me to get an idea around what you have built and how i can replicate it?

---

#### [2025-08-11 12:43:53] @chaintrader

what is the average profit you guys are making in here?

---

#### [2025-08-11 12:44:01] @chaintrader

I do my own trading bot

---

#### [2025-08-11 15:31:31] @melonenmann

0

---

#### [2025-08-11 15:43:27] @chaintrader

0??

---

#### [2025-08-11 15:43:33] @chaintrader

How?

---

#### [2025-08-11 15:49:46] @melonenmann

I'm a beginner and do demo trades 😉  I guess, no pro trader will answer this here in public, so I wanted to be polite. What do you want to know? RR or DD or PF or Win rate?

---

#### [2025-08-11 18:59:31] @tobias.p

hey, you can add me and we can chat or call, i am available now

---

#### [2025-08-11 19:00:02] @didierblacquiere

Great,  I sent you a request

---

#### [2025-08-11 19:01:11] @didierblacquiere

Just added you

---

#### [2025-08-14 12:56:37] @finddata_49439_09644

how to store data and use permanant data ,  where is the code example.  plz help

---

#### [2025-08-15 01:37:41] @donaldcuckman

how much data do you validate with? 

Currently im optimizing on 15k and validating on 5k, is that a reasonable ratio? 5min timeframe

---

#### [2025-08-15 21:07:11] @premysl_22228

Hi, it depends on your strategy, but yes, this is reasonable ratio. If your strategy is working independently of dynamic market structures and microstructures, I would recommend rather keeping 1/3 of data for validation and splitting it into smaller pieces (data used for algo validation auto - 40%, data used for algo validation manually - 30%, sacred secret data - 30%), where the last piece is sacred and you almost never touch it unless you are deploying to live. The data from validation gets through you and the validation algo (if you got one) to the training process and to be sure, you haven't polluted the training process and the strategy with validation data, it is good to have the last piece of data for "ceremonial" occassions. It's a nice way, how to prevent overfitting.

---

#### [2025-08-15 21:40:12] @premysl_22228

Btw. I recommend to run validations on higher frequency bars, optimally on quote/trade ticks depending on whether you more make or take. If everything was working (WIP here, I would say) and you are taking considerable amount of liqudity, I would recommend to validate on L2/L3 data + trade ticks, but things aren't on our side ready for this type of tests. But pure L2/L3 data for fine grade taker strategy validation is a good option even some features for making maker strategy more accurate through trade ticks usage still missing. (Be also aware that dynamic market simulation is still WIP, you can take same liqudity twice with current implementation.)

---

#### [2025-08-15 22:00:44] @donaldcuckman

Strategy is just using close price data.

Do you mean just look at the graph when you say manual algo validation?

---

#### [2025-08-15 22:01:29] @donaldcuckman

pretty new at this still, I appreciate your tips

---

#### [2025-08-15 22:01:47] @donaldcuckman

in backtesting ~%40/month

---

#### [2025-08-15 23:24:30] @premysl_22228

By manual validation, yes, I mean just look at the graph and stats (NT allows you btw. to add custom stats, highly recommended to consider using geometric mean instead of arithmetic, if your profits are so high). Usually you change the algo based on looking on the graph and you might unintentionally move some information from your data to your algo. It unfortunatelly happens sometimes, so it is better to have one blind validation test, where you don't want to have even the graph, but just some basic stats, so you can't learn from it and risk "overfitting" the algo.

---

#### [2025-08-15 23:30:53] @premysl_22228

Congrats by the way. If this is true positive, you are on the good way. If you don't test edge cases, I also recommend to use at most the half of money. In one point, there might come some excessive market condition (I am currently making a synthetic data generator for simulating such situations), where you are liquidated and you can continue to trade with half of the half. This way, you can ensure exponential growth until the limits of the market. After that you probably fallback into linear growth with lower profits and lower risk, but it might the good idea to make all stats geometric rather then arithmetic until you reach the point. Let us know, how it is going. 🙂

---

#### [2025-08-15 23:37:47] @premysl_22228

And one more thing, I recommend you to be sure not to use grid or marginale trap, if you are not HFT trader with really good plan (based on timeframe, I consider you regular frequency trader). If you do that, usually E[initial_money] > E[end_result], which is rather hazard then trading, even through backtests may say otherwise.

---

#### [2025-08-15 23:44:13] @premysl_22228

And look carefully, whether you weren't liqudated in some point. Proper liqudation is still WIP, I understood from <@757548402689966131> it might not be triggered in some cases on margin/futures accounts, even it should. There is some "patch" in the forum to get equity, so you might use jt for checking you are not KO. (Please fix me <@757548402689966131> , if I am wrong.)

---

#### [2025-08-16 00:01:45] @premysl_22228

Btw. check carefully and regurarly the market liqudity and structure. At one point you start losing money without realizing it. 30% monthly means 2300% yearly and 542000% in 2 years. Somebody (makers) might notice losing such money on the condition you are exploiting and the market might change under your hands. Nothing, especially such profitable exploits, survives forever and at some point, if somebody understand what is happening, you are KO with half of money against a human trader, or you just reached the amount of paper, the market is eager to accept and your slippage start killing the profits. Monitor carefully. 🙂

---

#### [2025-08-16 00:13:02] @premysl_22228

(to explain: market manipulation to get instant profit on understanding, that market is overlevaraged by someone and on which side is even through illegal a common thing as it is usually unprovable...getting somebody with milions of dolars on I guess 1:10-1:50 is just too delicious for many to not to do it...just open opposite limit orders on the correct side, one monster market order, and you are KO and mr. anonymous gets your money)

---

#### [2025-08-16 01:41:13] @donaldcuckman

this is a concern for me already, less that someone will notice and change the market but more that my orders themselves will change the market. Even on the very small $50 order scale

---

#### [2025-08-16 01:42:36] @donaldcuckman

ive done all this work on hyperliquid/crypto  but the markets seem to change just after a week or two of live trading

---

#### [2025-08-16 01:44:09] @donaldcuckman

Im not yet integrated into Nautilus just using ccxt for order management and from scratch python for the rest. 
I think my next step should be integrating into nautilus

---

#### [2025-08-16 01:44:30] @donaldcuckman

just need more vacation days! doing this after work sucks

---

#### [2025-08-16 02:30:40] @premysl_22228

If you are running on altercrypto, I would trust the 30% outcome monthly more. Try to run on L2/L3 and setup your algo to get the most of it. (I used min(proposed_trade, liqudity_on_side_until_geometric_mean_of_trade_slippage) function in history for similar purpose) The altcoins are usually small liqudity unusually predictable and you can get touch of how much you can get out of it by running with the full order book history.

---

#### [2025-08-16 08:10:34] @chaintrader

do you have the script? sine its open sourced

---

#### [2025-08-16 09:44:26] @donaldcuckman

lmao no

---

#### [2025-08-17 09:46:32] @premysl_22228

I would like to share a good message for people who are running optimizations on Optuna. In 2026, it will be probably possible to run optimizations with pure Rust strategy without usage of Python. This might help to improve running the optimizations faster then before. 

https://github.com/optuna/optuna/discussions/5362#discussioncomment-13977189

**Links:**
- Prototyping a Faster Optuna Implementation in Rust · optuna optuna...

---

#### [2025-08-17 09:47:35] @premysl_22228

From my point of view, the is one of the last essential pieces of the ecosystem around NT, which needs to be migrated to Rust, to get rid of Python overhead.

---

#### [2025-08-17 14:15:59] @baerenstein.

Hi, i have been wondering, is there a general nautilus setup with docker? I only found something regarding jupyter notebooks on the website. Maybe this is also a relevant update in the documentation. thanks in advance!

---

#### [2025-08-18 03:12:12] @cjdsellers

Hi <@322841069366804491> 
We provide [these files](https://github.com/nautechsystems/nautilus_trader/tree/develop/.docker) under the `.docker/` dir. The `nautilus_trader.dockerfile` is a base image intended for users to build on as required. I hope that helps!

---

#### [2025-08-18 10:36:14] @baerenstein.

yes, thanks!

---

#### [2025-08-18 19:22:36] @avihai0882_03319

Hi guys, I went through the documentation, probably missed it , I cannot see the Nautilus system support for trading the stock market,

Is the Nautilus system supports stock market algotrading? 

Thanks

---

#### [2025-08-18 19:46:05] @dkimot

it can actually only algotrade the sock market, once the rust migration is complete we'll see if they can add support for the stock market (serious answer: the point of NT is to trade various markets via standardized adapters. you figure out an adapter and the system doesn't really care what you're trading. it only knows instruments, orders, etc. doesn't matter if you're trading SPY, gourd futures, or [lord miles completing a 40-day water fast](https://polymarket.com/event/lord-miles-completes-40-day-water-fast-in-the-dessert) )

---

#### [2025-08-18 20:09:59] @avihai0882_03319

Thanks, I hope you weren't serious about the need to finish the full rust migration before it's possible to use it for the stock market😁

So it's up to me on figuring out how to create adapter for the stock market, or if maybe someone actually published those adapters maybe we can reuse...

I did saw in the messages history here that the stock market he's unsupported due to legal issues, so I hope this can be workaround as you've mentioned

---

#### [2025-08-18 20:40:56] @dkimot

no hate, i think you should do some more research on investopedia.com. it sounds like you're pretty new to this. we all started somewhere but i would suggest not trading with real money for a bit.

the stock market is not a homogenous thing you can interface with. it has no address. it's a conceptual umbrella that colloquially includes trading venues for equities and equity derivatives (options). the US stock market consists of dozens of venues, some lit and unilt. NT uses adapters to integrate with brokers and data vendors. some companies (like IB) can do both

unless you're colocated with an exchange you don't really trade with the stock market. you send orders to a broker and they handle the orders per their policies (commission-free brokers are generally PFOF and might execute your trade in an unlit environment whereas brokers where you pay commission generally let you router to specific exchanges and you can pay/receive the exchange specific commission/rebates)

i think NT is great but it's a tool within your toolbox. i would suggest looking for a toolbox to start with or prepare for a significant learning curve

finally, stay away from options for a long time. small conceptual misunderstandings can blow up your account very quickly

---

#### [2025-08-18 20:46:17] @dkimot

also, legal issues would be specific to your jursidiction. NT is a library/program you run on your machine. you're entirely responsible for managing your legal liability.

i'm US based so I can't access polymarket while in the US. i don't know the rules for people outside of the US to trade in the US markets. in the US, for futures/commodities and equities/options (the latter being the stock market), you need to either be a broker or have an account with a broker. the brokerage (like interactive brokers) will decide what you can trade. i can have an IB account but legally cannot trade CFD's with them. nautilus can't do anything to change that.

---

#### [2025-08-19 05:21:43] @avihai0882_03319

Thanks for all the good advices💯

---

#### [2025-08-20 09:53:49] @chaintrader

I have custom indicators. How can I implement into Nautilus trader?

---

#### [2025-08-20 19:36:13] @hottweelz

i relied heavily on github copilot using claude and deepseek (not GPT) to convert my PINE Strategies into Nautilus Strategies... was a lot easier than i anticpated.

---

#### [2025-08-20 19:45:19] @neupsh

Hello, I have asked this on <#1138719912286748672> channel, but wanted to ask here for visibility, 

What is a typical throughput you can get while running backtests (say simple MACD strategy on 1 minute bars for about 50 days?) I am getting slow throughput and wondering if that is normal or if I am doing something wrong. 
For me simple strategy with 1 minute bars for 50 days is taking 51 minutes to complete. Is this close to how everyone else gets?

---

#### [2025-08-21 09:30:57] @optic_swagger

Hey everyone, any ICT traders here? I'm working with a well-respected ICT trader (>10k subs on Twitter) to implement ICT concepts using machine learning. If you're also working on automation for ICT strategies, send me a DM. I'm new to the NautilusTrader community, but I am planning to use it for production trade-execution.

---

#### [2025-08-23 06:28:04] @xxxholic_ai

there are more than 1.6m bars in the example in tutorial  which cost me less than a minute.my cpu is e5 2673v4 which is not good in nowdays.I think a amd 7700x and above will spend a half of the time or less.50days only exist 100k bars.So I guess there should be something wrong.

---

#### [2025-08-23 20:29:33] @.jxcv

Hi all! Just discovered Nautilus and I'm loving it. Wondering if anyone else uses OANDA? I will need to write a connector soon and it would be awesome if it wasn't from scratch 😄

---

#### [2025-08-24 20:17:48] @zupet

That is crazy slow, must be sth wrong on your side, can you share the code or is it super-confidential?

---

#### [2025-08-25 13:26:28] @neupsh

Thank you <@781031943859863553> and <@780089963009277962> ,that helps baseline my expectations and it is super slow for me. Here is the code I am running https://discord.com/channels/924497682343550976/1138719912286748672/1407733143624220802

---

#### [2025-08-25 13:47:47] @neupsh

claude sonnet found that I was loading 661K rows of data instead of just 50 days on the engine, when I was testing for 50 days. That was the biggest performance killer. Fixing that brought it down to 32 seconds for 50 days. (still far from what <@781031943859863553> is seeing but managable. I will continue to check on what I can do to improve it). If anyone has suggestions please let me know 🙂

---

#### [2025-08-25 16:08:55] @neupsh

Hello, where can we download the files in the tutorial (like BTCUSDT_T_DEPTH_2022-11-01_depth_snap.csv) ? I tried running the nightly docker to see if it contains it but could not find it in there as well.

---

#### [2025-08-26 03:07:27] @domp2948

Hi all new here. I looked at examples and not much on backtesting tick data (using databento historical). Is there a super simple example on L1 data anywhere?. Something like Calculate VWAP of current session using second bars and tick bars and then use either of those to enter if the quote comes in within X ticks? TIA

---

#### [2025-08-27 02:19:23] @shahisma3il

Can you kindly share your fixed py file?

---

#### [2025-08-27 10:34:41] @aria.k.3000

def calculate_daily_returns(portfolio: Portfolio) -> pd.Series:
        """
        Calculate daily returns using a multiplicative approach.
        """
        # Get raw intraday returns and remove NaNs
        raw_returns = portfolio.analyzer.returns().dropna()

        # Compound the intraday returns into daily returns
        # - Add 1 to each return, resample by day, and multiply all returns in that day
        # - Subtract 1 to get the final compounded daily return
        daily_returns = (1 + raw_returns).resample("D").prod() - 1

        # Filter to keep only non-zero daily returns
        return daily_returns[daily_returns != 0]

---

#### [2025-08-27 10:40:39] @Wick



**Links:**


---

#### [2025-08-27 10:47:43] @aria.k.3000

Hi, Thanks for the info. I am trying to calculate daily portfolio returns for Quantstats and I found the one I wrote you earlier. Please let me know your thoughts if you like. I tried to include it in one message but Discord didn't let me (thought I was spamming). Thanks in advance.

---

#### [2025-08-27 11:09:31] @aria.k.3000

For trade tick market data daily returns (benchmark)  I found:
def calculate_benchmark_daily_returns(df: pd.DataFrame) -> pd.Series:
    """
    Calculate benchmark daily returns from a DataFrame.
    """
    # Resample to daily prices using the last price of each day
    daily_prices = df["price"].resample("D").last()

    # Calculate benchmark returns and remove any NaN values
    benchmark_returns = daily_prices.pct_change().dropna()

    # Filter to keep only non-zero returns
    return benchmark_returns[benchmark_returns != 0]

---

#### [2025-08-27 14:25:06] @barlawwwww

Hi, 
I have noticed something strange in backtest. When you send 2 bracket orders (that is, 6 leaf orders), and both entry orders get filled, then take profit and stop-loss orders are updated with the summed-up quantity of both entry orders. Strange. Those two bracket orders should not affect each other.

---

#### [2025-08-27 14:26:30] @neupsh

here you go

**Attachments:**
- [download_data_nautilus.py](https://cdn.discordapp.com/attachments/924498804835745853/1410269250580643911/download_data_nautilus.py?ex=68fae3d6&is=68f99256&hm=8618c63e5ca100fc0453a0aedfb1608ede2f9caf857213b62905a193cf9e7579&)

---

#### [2025-08-27 14:50:50] @shahisma3il

Awesome -- appreciate it.

---

#### [2025-08-27 15:09:35] @neupsh

Has anyone built adapter for charles schwab? (thinkorswim apis)

---

#### [2025-08-27 15:09:54] @faysou.

No

---

#### [2025-08-27 15:11:05] @faysou.

I notice several new people asking for the adapter of the broker they use, if it's not in the repo it means there's no adapter. The fastest way would be for a person who needs one to create one, and maybe share it to others for further development.

---

#### [2025-08-27 15:12:44] @neupsh

I am not ready to build one yet, but was wondering if anyone else has tinkered around (even if it is incomplete).

---

#### [2025-08-28 00:33:44] @greeny_the_trading_snake

I just wanted to tell you guys that good job - it's incredible software

---

#### [2025-08-28 00:33:49] @greeny_the_trading_snake

👏

---

#### [2025-08-28 15:27:20] @colinshen

<@757548402689966131> Hi, someone is using your avatar and similar name for scamming.

---

#### [2025-08-28 15:28:11] @colinshen



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1410647160550326403/image.png?ex=68faf24b&is=68f9a0cb&hm=b1259b1f799d1d98caab86e30d9a467d05ba730f268ddfc9d9b4b1e678e75203&)

---

#### [2025-08-29 00:55:48] @rodguze

hello! i am just getting started and notice that the installation guide (https://nautilustrader.io/docs/latest/getting_started/installation) instructs to use `uv` but all the commands on the page are `pip`. not sure if that's intended, but it'd be nice if the commands were `uv add` for copypastability.

thank you for making NT, btw, i am just getting started today, but it looks like an incredible piece of software made increadibly well and i'm looking forward to working with it!

**Links:**
- NautilusTrader Documentation

---

#### [2025-08-29 11:44:41] @alphatraderjoe

hi, i'm new to Nautilus Trader, but been backtesting using BackTrader and personal python code in the past.

2 quick questions:
1. When running the example "example_01_load_bars_from_custom_csv"  , with log_level="DEBUG", running it in the terminal shows all logging statements, but running it in an interactive window in VS Code doesn't show any logs. I tried setting print_config=True, but it still doesn't work. Is there any workaround?
2. I previously saved all my price data in a MySQL database, is it possible to connect it to Nautilus? Or should i just re-save the data in CSV format?

---

#### [2025-08-29 13:15:50] @faysou.

For 2) you could build something to query data, convert it to nautilus objects, then write it to a nautilus catalog with catalog.write_data

---

#### [2025-08-29 13:16:19] @faysou.

And then use a catalog with a BacktestNode

---

#### [2025-08-29 15:18:55] @rodguze

4 out of the 5 the links in this section are borked, only `examples/` works: https://nautilustrader.io/docs/latest/getting_started/#examples-in-repository

**Links:**
- NautilusTrader Documentation

---

#### [2025-08-29 16:23:25] @faysou.

Yes, clone the repo and find examples that work. Examples in notebooks folders work out of the box, I know because I've done them and had the same difficulties as you when I started. There are some in backtest and some in interactive_brokers.

---

#### [2025-08-29 18:51:36] @faysou.

Also the best way to use the library is to clone the repo and search in the code when you don't understand how something works. The library is big, but the only way to get more familiar with it is to start looking at it. And it's organised logically and you can use an LLM agent to help you in the understanding, they are super powerful.

---

#### [2025-08-29 18:52:47] @rodguze

yeah, thanks! that's my part of my MO more broadly  -- i have a repomix file of any tool that i use. i then have the llms read those and answer my questions

---

#### [2025-08-29 18:53:37] @faysou.

That's good, I sometimes see basic questions or some people getting stuck on basic things, they should use LLMs.

---

#### [2025-08-29 18:54:08] @faysou.

LLMs can also solve some bugs of the library, this could lead to more people contributing.

---

#### [2025-08-29 18:54:43] @faysou.

But people need to have a sufficiently good level in programming to understand what the LLM does.

---

#### [2025-08-29 18:58:10] @faysou.

I know that LLMs allow me to do more ambitious things and faster for nautilus. Sometimes I don't know how to do something and an agent can do a good first version, then I just need to polish it.

---

#### [2025-08-29 21:35:25] @primalleous

Do you provide contexts files for it? / docs of sorts or does it just figure it out based on description?

---

#### [2025-08-29 21:36:19] @faysou.

I use augment code, I have the repo available as context and it finds what it needs almost all the time.

---

#### [2025-08-29 23:38:03] @rodguze

i am having good luck with claude code + a repomix of the NT repo (https://repomix.com/, https://github.com/yamadashy/repomix). i have an instruction in CLAUDE.md to consult the repomix file for documentation about NT and it seems to be working very well

---

#### [2025-08-30 01:44:06] @alphatraderjoe

thanks for sharing abt repomix! first time i heard of it, checking it out now

---

#### [2025-08-30 08:30:02] @alphatraderjoe

I tried using repomix, but the xml file is too large for Claude, even at higher tiers. I also excluded tests folders and csv files but they are still too large. 

Could you share your workaround please?

---

#### [2025-08-30 12:49:09] @rodguze

i generate the file as markdown and use claude code

---

#### [2025-08-30 15:06:01] @gz00000

try context7

https://context7.com/websites/nautilustrader_io-docs-latest
https://context7.com/nautechsystems/nautilus_trader

**Links:**
- NautilusTrader
- Nautilus Trader

---

#### [2025-08-30 18:44:38] @rodguze

s'pose i am writing a strategy that will sell iron condors: it selects strikes/expirations and then enters the position. is it idiomatic to use `Strategy.add_synthetic()` to track the trade?  basically, once the strategy finds the contracts it wants, it creates a `SyntheticInstrument` with them as components, adds it, and immediately buys it?

if that's not the idiom, what's the recommended way to track multi-leg trades?

---

#### [2025-08-30 22:16:33] @sol_maniac

Anyone working on a HyperLiquid adapter for Nautilus? Would be great to have

---

#### [2025-08-31 09:11:52] @gz00000

https://github.com/nautechsystems/nautilus_trader/tree/develop/nautilus_trader/adapters/hyperliquid

---

#### [2025-08-31 16:32:59] @sol_maniac

you are a legend <@224557998284996618> - thanks for pointing it out

---

#### [2025-09-08 23:10:01] @cancington42

hello, I just completed installing nautilus on a NixOS machine. I created documentation of the install process and all dependancies. It was a bit of a struggle installing on NixOS and I am wondering if the developers would be interested in the documentation to be included in your repository for other NixOS users. If you are interested, please let me know the best way to get the documentation to you. Thank you!

---

#### [2025-09-09 07:13:46] @cjdsellers

Hi <@1088141934217936936> 
Thanks for reaching out. Absolutely, these docs would be valuable. Feel free to raise a discussion or even a PR on GH

---

#### [2025-09-11 17:01:58] @maxcomx

nautilus trader vs freqatrdde?

---

#### [2025-09-12 00:44:21] @cancington42

That’s great to hear! I’ll get that setup and reach out through GitHub. Thank you!

---

#### [2025-09-13 00:29:17] @zay3030

Hey, random question guys

---

#### [2025-09-13 00:30:06] @zay3030

I have no idea how to program. I started learning rust like a week ago to try and start building an arbitrage bot and have stumbled on nautilus. Looks better than my wildest dreams.

---

#### [2025-09-13 00:30:53] @zay3030

Should i take a python and quant course to learn how to use it or should i pay a dev on fiver to build out a dashboard so i can tweak it easier

---

#### [2025-09-13 00:31:45] @zay3030

Or can i pay one of you fine gentlemen to teach me and help me get this working lol

---

#### [2025-09-13 00:32:02] @zay3030

Or am i in way over my head and i should step off 👀

---

#### [2025-09-13 02:01:55] @cjdsellers

Hi <@837768478785142851> 
Welcome and thanks for reaching out! The platform is quite developer-centric at the moment. There is no frontend although this is something we’re currently working on. The learning curve is also very steep with the current state of the docs severely lacking tutorials - so it does require some amount of coding knowledge, even with AI tools. I’d recommend learning more about the space in general and trying some more approachable platforms before circling back if you discover Nautilus has things you definitely need. I hope that helps!

---

#### [2025-09-14 02:19:22] @anderson.developer.sc

https://deepwiki.com/nautechsystems/nautilus_trader

**Links:**
- nautechsystems/nautilus_trader | DeepWiki

---

#### [2025-09-14 05:14:20] @faysou.

That's a nice link, it pops up periodically on this discord server. I wouldn't say it's completely accurate but it gives many ideas about what exists in nautilus.

---

#### [2025-09-14 06:30:37] @yfclark

zread also provide one,you can ask ai questions for it:https://zread.ai/nautechsystems/nautilus_trader

**Links:**
- Overview | nautechsystems/nautilus_trader | Zread

---

#### [2025-09-14 10:40:56] @faysou.

Nice I didn't know about this one

---

#### [2025-09-15 00:03:14] @tobias.p

guys my logs are empty and i tried everything going back to 217,218,219... the logs dir is created but and log files but they are empty.. it worked the last few days no problem...

---

#### [2025-09-15 00:03:37] @tobias.p

i am on windows.. i will try to replicate on linux to see if thats the issue

---

#### [2025-09-15 00:19:23] @tobias.p

found a fix, was my issue in configuration

---

#### [2025-09-16 06:35:13] @stringer408

excuse me . does it have user interface extension which can handle mouse click

---

#### [2025-09-16 06:35:56] @cjdsellers

Hi <@1320997622210629672> 
There is no GUI interface at this stage, this is something we're actively working on

---

#### [2025-09-16 06:37:00] @stringer408

okay , it will be wonderful if gui is written with rust too

---

#### [2025-09-16 06:53:53] @cjdsellers

Indeed it will be

---

#### [2025-09-17 12:30:56] @dsalama345231

Trying to dive deeper and learn to use NT properly. I have some general questions, I’d appreciate some help with (all in the context of options trading):
1) the website talks about the RiskEngine. Is there a way to define global risk management rules that apply across the board to all strategies or positions? For example, setting a hard rule that the system will close any trade when it reaches a 50% loss on the premium?
2) somewhat related question. If a strategy is running and places some trades, can I stop the algorithm, make some tweaks, and restart it without closing the positions it had opened previously and still be able to manage those positions?
3) some data providers have connection limits. If I were to run 10 different strategies all subscribing to the same data provider, does NT reuse a single connection or does it try to establish a separate connection per strategy?
4) If I have a separate Redis server, where do I configure the host, port, user/pwd, to connect to it instead of running the local docker?
Thank your again

---

#### [2025-09-19 07:19:13] @cjdsellers

Hi <@792981407122980875> 
1) The risk engine as it stands is probably not as configurable as you need, there are only some basic pre-trade risk checks and you can set max notional per order (per `instrument_id`): https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/risk/config.py#L33
2) Yes, you'd want to set `external_order_claims` for the strategy. I recommend a deep dive into the config options to understand what's possible:
- https://nautilustrader.io/docs/latest/concepts/live
- https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/trading/config.py#L31
3) Data connections are not related to strategies but to [DataClient](https://nautilustrader.io/docs/latest/concepts/adapters#data-clients)s. Limitations are integration-specific and so there are a range of approaches to overcome limitations, such as Binance distributing many subscriptions across multiple websocket clients. The short answer is, there will be typically one data connection per provider (unless many subscriptions), per node (not per strategy, which can subscribe to the same streams on the message bus)
4) This can be configured with [DatabaseConfig](https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/cache/config.py#L29), that can be set for `CacheConfig` and `MessageBusConfig`

I hope that helps a little. I'd suggest you would find many answers searching docs + code

---

#### [2025-09-19 11:20:00] @dsalama345231

Thank you again <@757548402689966131> for there insights and dot pointing me in the right direction

---

#### [2025-09-22 09:07:26] @alexabramov_dune_86569

Hello! Apologies in advance if this is the wrong channel to this post this question to, but I'm looking to hire an expert in Nautilus as a consultant to help my quant team set it up as fast as possible to support multiple strategies (options, grid, pairs trading), can anyone point me in the right direction?

---

#### [2025-09-22 10:06:35] @tobias.p

is anyone here experienced with the Questdb and related technologies especially its python client library?

---

#### [2025-09-22 10:07:32] @gz00000

I'm using victoriametrics.

---

#### [2025-09-22 10:10:40] @tobias.p

interesting, have only heard of it. short story i tried tweaking every server and client side config and connection option to maximize write speed for nautilus quoteticks and bars into questdb using dataframes of up to 4 million rows. and i reach a maximum write speed of 100k rows per second far from the 1-2 million per second on their benchmark graphs on their site. hardware is also decent consumer grade. may i ask what you achieve roughly in write speed for a table containing basically nautilus bars to_dict as a dataframe so a few string, float and timestamp columns. thank you

---

#### [2025-09-22 10:13:34] @gz00000

My use case is different from yours; I mainly focus on storing metrics data during the strategy execution process and haven't conducted any stress tests.

---

#### [2025-09-22 10:16:22] @tobias.p

ok so during a live trading scenario? i am guessing you wont hit more than a thousand ingress rows per second?

---

#### [2025-09-22 11:01:05] @gz00000

No, it won't. Although multiple strategies feed data into a single VictoriaMetrics instance, the data is aggregated over time.

---

#### [2025-09-23 16:27:12] @lwxwd

May I ask if there is a Chinese channel

---

#### [2025-09-24 00:06:40] @cjdsellers

Hi <@1336621765006462976> 
Welcome, yes and <@224557998284996618> can help you there

---

#### [2025-09-24 05:02:24] @gz00000

<@1336621765006462976> Welcome! I've already invited you to the Chinese channel. Let's communicate more. 🙂

---

#### [2025-09-24 16:58:30] @lwxwd

thank you so much

---

#### [2025-09-24 21:02:43] @shinzoabe

Quick Q, is this project mainly for stocks / crypto and others along the same line predictions, or can we pump data such as for the Euro league, NBA, tennis?

---

#### [2025-09-25 01:32:08] @cjdsellers

Hi <@149228888403214337> 
Welcome, there is a Betfair adapter which might be of interest to you. Nautilus doesn't really make a distinction on these asset classes / market types, as long as the data can be parsed or decoded into the expected data types

---

#### [2025-09-25 19:41:34] @0x1nfor_19886

invite me plz~~

---

#### [2025-09-26 01:50:58] @ml087870

Hi everyone, I’m currently focusing on day trading SPY and QQQ options. Is anyone else doing the same? Happy to connect and communicate more.

---

#### [2025-09-26 02:53:49] @gz00000

Done. Welcome

---

#### [2025-09-26 08:08:10] @webstar_web3

邀请我一下，谢谢

---

#### [2025-09-26 08:20:11] @gz00000

Done. Welcome 🙂

---

#### [2025-09-26 12:14:12] @ml087870

有研究美股日內當沖的 可以加我一下 感謝

---

#### [2025-09-26 12:58:23] @emmanuel_genieys

In my dream I also see an MT5 interface... would this be in the pipe line?

---

#### [2025-09-27 08:53:23] @mk1ngzz

i'd suggest clickhouse

---

#### [2025-09-27 08:56:22] @mk1ngzz

if u want efficient storage for observability data, historical trading data and the ability to replay for backtesting, then i'd suggest that.
i only recently discovered nautilus while building my own trading bot, so idk if the database adapter supports that

---

#### [2025-09-27 08:58:28] @mk1ngzz

just setup the clickhouse client to use async inserts

---

#### [2025-09-27 09:01:55] @mk1ngzz

Are you open to PRs?

---

#### [2025-09-27 09:24:13] @mk1ngzz

Is it possible to use Rust instead of Python?

---

#### [2025-09-27 09:45:34] @cjdsellers

Hi <@223930266207518721> 
Welcome, we currently have a lot on right now with the Rust port of the core - also see the open-source scope for where the focus is right now
https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md#open-source-scope
There's an effort to complete live execution capabilities in Rust, at that point you could write trading strategies entirely in Rust

---

#### [2025-09-27 09:50:04] @corn15

Invite me please 🙏

---

#### [2025-09-27 10:35:22] @gz00000

Done. Welcome !

---

#### [2025-09-28 21:35:11] @xcabel

seeking advice on loading offline trained and persisited models for online serving for the use of decision making in some strategy. The use case is that say 
- I have a sklearnmodel class instance offline trained and stored to predict some instrustment price for the next five minutes. 
- to do the inference it requires some features data input which can come from some data class say trade tick or quote tick or customized newsdata and etc. This also indicates that the model is dependent on a set of data classes
- Note that the model instance is static in the sense that it requires no retraining, its parameters, and dependency on data is fix. It also requires no future persistence and should be fully serializable
- Also the model is strategy agnostic, i.e., it only predicts prices at some lead time that can be used by mulitple strategies.


Given the above property, I think 
- a dataclass to load the model sounds does not make sense as it is static
- but dataclass to stream and persist the model input and output seems good for traceability
- but my question is how to integrate the model in the some module in the NT? should that be a customied Actor to load the model and do the say feature preparation, inference and etc subscribing the raw data and pub processed feature and response to a stream?

---

#### [2025-09-29 10:00:47] @faysou.

https://github.com/limx0/nautilus_talks/tree/main/20220617

**Links:**
- nautilus_talks/20220617 at main · limx0/nautilus_talks

---

#### [2025-09-29 10:00:51] @faysou.

this should help you

---

#### [2025-09-29 10:03:42] @faysou.

I think that an actor is the way to handle what you want to do. Actors have helpers to deal with market data, strategies inherit the Actor class and have helpers for passing orders as well. These helpers deal with sending messages and callback methods (on_bar is a callback for a subscription for example (actually it's handle_bar but it's the same idea))

---

#### [2025-09-29 11:36:23] @faysou.

the link above maybe doesn't work as it's using a nautilus version from a few years ago, but you can likely use ideas from it

---

#### [2025-09-30 02:01:35] @fudgemin

hey i trade same assets as well. working on automated setup. have many custom features with predictive power. looking to collab with some ml, quant engineers

---

#### [2025-09-30 03:25:21] @xcabel

this is really helpful! thanks for the pointer!

---

#### [2025-10-01 07:09:15] @xcabel

how to get recent history for a custom data class from cache in backtest setting?
- I have a custom data class subclassing Data type directly instead of Bar or etc. This data class is not associated with one specific instuctment but more generic such as NewsEventData. I don't have metadata set for it (tho I can add it in backtest dataconfig)
- I persist the data in catalog and port into backtest eng via backtestdataconfig and catalog
- in this case, i wonder how in the strategy or generic actor that I can get the recent history as a list of this data class instances from self.cache.*? For now, I hack it by put it in a deque as an actor data field and manually update this deque in on_data().

---

#### [2025-10-01 09:39:39] @lisiyuan666

Hi, i've been working on an adapter for schwab recently. It's adapted from the schwab-py library. For now the basic data/execution logic for equities is kind of working, but there are still lots of works for options, futures, etc. Also the logic for reconciliation is pretty much untouched. It would be great if we could develop these together so that there are less bugs and more complete:) I can create a pull request if anyone can help!

---

#### [2025-10-02 10:41:57] @tiny.z

<@224557998284996618> Invite me please🙏

---

#### [2025-10-03 02:23:34] @rk2774

Hi, appears that JupyterLab was not released with 1.220?
Trying to download on Windows (command line).. cannot see the package on released packages

`C:\Users\rk> docker pull ghcr.io/nautechsystems/jupyterlab:latest@sha256:d0acd58d4cbfa78c2fa85514f81cfdfb034765686ea10e8dcf308674f10b2740 --platform linux/amd64
Error response from daemon: manifest unknown`

---

#### [2025-10-04 23:52:01] @rk2774

I was able to get it working using (was earlier trying to pull a specific version - not sure how it is done):

`docker pull ghcr.io/nautechsystems/jupyterlab:latest --platform linux/amd64`

---

#### [2025-10-05 16:04:50] @drrocky_40374

new to Nautilus and developing an intra-day equities strategy ... i have a basic question that i can't seem to find an answer to or an example. How can i load up some historical data (for example, the past N 1-min bars) in my live strategy? I need to get them to warm up my strategy indicators before it is ready to trade. When I start the strategy, I don't want to have to wait N minutes for the live feed to populate the arrays, but instead look back and get the past historical data. I am also using Interactive Brokers, so if there is a specific example for them even better. Thanks

---

#### [2025-10-05 16:31:56] @fudgemin

your essentially asking how to build a strategy. If its your first question, then your likley already on a path to failure. 

i had to seperate my historical from my live. Its not feasible to compute on demand: past n features, for past n timeframes, for n symbols. 
You can focus on one ticker, and maybe do it all on demand, within reason. However, the goal here would be to never have a 'warm up', You build features at end of day, pass the information to the intraday state. The two actually dont have any dependancy, unless you using windowed features. Which i do, and at that point, your talking about an entire feature system

---

#### [2025-10-05 18:02:20] @drrocky_40374

I'm not asking how to build a strategy as such, I actually have the strategy already. I have ran it on a lot of stocks in the Nautilus backtester and now want to paper trade it via my Interactive Brokers account... When running as the backtester it is not a big deal as it is fine to start the backtest and use up the first N=300 minutes because it will then run for however long the backtest is set for and the 300 minutes is small compared to the length of the backtest. But in the live scenario, if I have to use up the first 300 minutes of the day, it will be near market close by the time it is warmed up. Whilst I am debugging and papertrading and testing everything, having to wait like this is a nightmare... What I want/need is to start the live strategy and immediately fetch the previous 300 minutes of data  (idally from IB's historic data fetcher), could be out of hours trading or the previous day's bars and use those 300 data points to warm up the strategy (think some technical indicators, rather than trade some ML model with features). I think this should be quite easy, I feel I am just missing something obvious... I can see there are some classes and methods that should support it, for example RequestBars in https://github.com/nautechsystems/nautilus_trader/blob/431d02203c54df4592d64f5de1e84fac14db50f6/nautilus_trader/data/messages.pyx. Also this example EMA Strategy subscribes to both live data and also requests some historical data to hydrate the indicators at the start: https://nautilustrader.io/docs/latest/concepts/strategies#handler-example. I guess my question is has anyone combined this type of strategy (with a live feed and an initial request to fetch historic data) with Interactive Brokers and got it all connected up and running?

**Links:**
- NautilusTrader Documentation

---

#### [2025-10-05 18:36:26] @faysou.

You should use request_aggregated_bars, also the IB adapter is likely working, use the develop branch for the latest updates

---

#### [2025-10-05 18:36:50] @faysou.

Look in actor.pyx and data engine.pyx to understand what's going on. Or ask an AI agent.

---

#### [2025-10-05 19:03:30] @drrocky_40374

OK, thanks for the pointers... will dig into it

---

#### [2025-10-06 00:02:29] @fudgemin

Anyone interested in collab? Looking to expand network. Self taught. no proffessional exp. I have some really good predictive features, not based on TA, but options data. I target >50%, have strategies. Most are manual parameter sets right now, not optimized by any means. Have done some minor ML with good results. Dont have the time to fully focus on one aspect. Eventually working towards a fully operational fund. Need assistance. Please reach out if interested

---

#### [2025-10-06 15:55:43] @.jxcv

Hi all, I have started on an OANDA adapter. Anyone interested in working on it with me?

---

#### [2025-10-06 21:48:33] @semihtekten

experienced metatrader expert advisor developer here. is there an ETA for visualization / GUI solution for NT? or is there any documentation that we can benefit, and use NT with? thanks in advance.

---

#### [2025-10-06 21:54:35] @mafiosi72

Hi DrRocky,

i am looking at the exact same thing here as well and getting nuts since days trying to find my way through this. Whatever i have tried so far i always winded up in getting 

[WARN] BACKTESTER-001.DemoStrategy: Received <Bar[0]> data for unknown bar type

when requesting for historical data via request_bars().
Please let me know if you figure out a proper way to do it, or if you want to work together on that one.

---

#### [2025-10-07 19:13:50] @drrocky_40374

Hi <@1061003276696440883> yes I did, I have it working now - I'm pulling historical bars and live ticks from Interactive Brokers and hydrating my strategy in live trading. 

To make it work, I looked at what <@965894631017578537> suggested and ended up including a call to the self.request_bars() function in my Strategy on_start handler and then also added the necessary on_historical_data() function in the Strategy to handle the actual historic bars as they come in.

---

#### [2025-10-07 20:54:38] @drrocky_40374

actually maybe there are others it might be useful to... this is the code snippet I added to pull in historical data before the live trading kicks in ... see self.request_bars(). if there is historical data, then you also need another function in your Strategy called "on_historical_data()" which processes the incoming historical data. the _warm_up_complete() function is just a callback that gets executed after the historical bars have loaded. Hope that helps and you get your strategy working too

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1425224828373434450/image.png?ex=68fa960e&is=68f9448e&hm=c1b183bb4c6d3f75c8048f5d3c23a82f6fcfbdd26ac4a5cd73c7b9e70599649b&)

---

#### [2025-10-07 20:59:03] @faysou.

https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/backtest/notebooks/databento_test_request_bars.py

---

#### [2025-10-07 20:59:13] @faysou.

you can look here as well

---

#### [2025-10-07 21:00:14] @faysou.

and the notebook works out of the box there's some test data inside the repo for it

---

#### [2025-10-07 21:06:43] @faysou.

https://github.com/nautechsystems/nautilus_trader/tree/develop/examples/live/databento/notebooks
https://github.com/nautechsystems/nautilus_trader/tree/develop/examples/live/interactive_brokers/notebooks
https://github.com/nautechsystems/nautilus_trader/tree/develop/examples/backtest/notebooks

these are notebooks I've worked on for testing features I add. it looks small but there's a lot of work behind, especially for the code being called

---

#### [2025-10-07 21:11:29] @faysou.

the complexity of some things is not apparent, but if you try to understand how some things work and look at the source code (not just of the notebooks but how it's done in the code actually), you will learn a lot of stuff

---

#### [2025-10-07 21:13:10] @faysou.

best thing is to clone the repo and setup a dev environment, and get familiar with the code (it's not easy but it's easier with some AI agent to ask questions about the code, and adding some debug logs to see what's happening inside cython, cython can't be debugged)

---

#### [2025-10-07 21:13:44] @faysou.

but rust can be debugged, so it will actually get easier to understand the rust code base when it will become the main system after the transition from cython to rust

---

#### [2025-10-07 21:15:23] @faysou.

for people who read these messages, you can learn a lot of stuff from it. sometimes people complain that examples don't work out of the box, I had the same problem, and these examples I've done work out of the box

---

#### [2025-10-07 21:29:54] @drrocky_40374

the examples are very helpful. they are never going to cover everyones needs but they are good starting to point to help learn the code structure and adapt to your specific needs...

---

#### [2025-10-08 07:02:12] @faysou.

Exactly, it took me a lot of time to understand how to do basic things, but with examples it's much faster. Still I think the best documentation is the source code and it's available. I can give you a few principal component axis to understand nautilus. You have the data side with the data engine, the actor class and market data clients, and the order side with the execution engine, the strategy class and execution clients. Then you need something to assemble everything, and that's the kernel, backtest node, backtest engine and live node. The storage side is the catalog and the cache. The communication side is the message bus. And the clocks and timers are important too. Also don't forget to read the documentation (the concept pages, not the help about functions, better to look at the code for this), even if you don't understand everything at first.

---

#### [2025-10-08 15:11:47] @mafiosi72

Hi <@1421216025650663436> + <@965894631017578537> ,
thanks for sharing your code and the references to the notebooks, they are indeed helpful.
BUT: 
I had similar code like you have shared already available and it was fed by the Backtesting "low-level API"., which means that i had 
- created a BackTestEngine (bt_engine) and added 
- the venue () to the engine -> bt_engine.add_venue()
- the instrument -> bt_engine.add_instrument()
- the data bars -> bt_engine.add_data()
- the strategy -> bt_engine.add_startegy()
and started the engine with bt_engin.run()

No matter what i have tried i was not able to get the history data via request_bars() . 

I just re-wrote my code to use the high-level API instead (via BackTestNode() .... not the BackTestEngine) and voila: The same strategy was working immediately and iw as able to capture the historical bars.

I am not sure what i have done wrong with the low level API but always when i wanted to fetch the historical data via request_bars() i got 
[WARN] BACKTESTER-001.DemoStrategy: Received <Bar[0]> data for unknown bar type 

while the subscribe_bars() was working very well.

So again, thanks a lot for pointing me in that direction and helping to finding my way to get i working finally!

---

#### [2025-10-08 20:18:56] @faysou.

DataCatalogConfig, that's what you need

---

#### [2025-10-08 20:20:12] @faysou.

For querying hisorical bars. You don't even need BacktestDataConfigs to subscribe to data with catalogs, the queried data will be added to the backtest data on the fly, I've worked on this a lot a few months ago.

---

#### [2025-10-08 20:21:46] @faysou.

It's much easier when you start from a working example

---

#### [2025-10-08 20:22:35] @faysou.

There was no example for me to use DataCatalogConfig when I was studying this a year ago. I actually found it by looking at the source code. And did many related improvements after.

---

#### [2025-10-10 17:50:21] @one_lpb

Hey everyone,

I just wanted to take a moment to thank you all for the incredible work core team and community have done on Nautilus Trader. The library is insanely well built. Fast, elegant, and a real pleasure to use. The sheer amount of functionality it offers is mind-blowing, and the documentation is top-notch.

It’s rare to find a project that combines such performance, clarity, and thoughtful design. You’ve clearly put a ton of expertise and care into it, and it really shows.

Massive respect for what you’ve accomplished, it’s a joy to build with Nautilus Trader.

Cheers

---

#### [2025-10-11 12:48:48] @drrocky_40374

i'll second that, it works very nicely. probably saved me and my team years of collective engineering time

---

#### [2025-10-12 13:49:18] @gz00000



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1426929729432322130/image.png?ex=68fadb1e&is=68f9899e&hm=06386ece5a6f72bf8fc53fc3f3a31b85538534cb95939172eba8b3b7a7d8540e&)

---

#### [2025-10-14 02:00:19] @details_1337

the strategy can't read the 1-min bars of the last day from the broker/api? why it has to be from historical data you saved?

---

#### [2025-10-14 21:07:38] @sinaatra

hey guys, is there some open source code build on top of nautilus trader? I am struggling configuring  it and particularly with live engine because i don't find much ressources

---

#### [2025-10-14 21:11:43] @cjdsellers

Hi <@420311971389374464> 
Not that I’m aware of - there isn’t an open-source project built *on top of*  NautilusTrader. We’re working on improving the documentation and resources around the live engine though, so that should get a lot easier soon
Did you try using an LLM to help with this by the way? they're good at diving into and understanding the code to help you achieve what you're after

---

#### [2025-10-15 07:19:47] @dariohett

<@757548402689966131> Thank you for fixing the Polymarket issue earlier today.

Would you mind sharing your current development set up and how you zero’d in on the issue? The tests do not seem to cover it, so I’m wondering if it is sheer experience. 

Also for mixed mode debugging and IDE experience, I’ve found PyCharm to have much better support for the Cython side than Vscode- on the latter I cannot even follow references from Python to Cython.

---

#### [2025-10-15 11:09:25] @a1ecbr0wn

Hi <@757548402689966131>, I am thinking of writing an adapter for an API that you don't currently support.  Are you accepting PRs for other APIs, subject to code review etc.?

---

#### [2025-10-15 19:35:20] @sinaatra

hey, thanks for your answer, so far gpt5 provided some outdated or wrong code snippets which makes it even more difficult to understand. I am referring to the doc + github only but ngl that would be cool to have more examples

---

#### [2025-10-16 03:10:25] @ehwha

Hey guys, I've been taking a look at NT to learn about trading platforms. I'm in Canada and I use questrade, which doesn't allow automated execution, but I think it could be interesting to build a questrade adapter just for backtesting. Would anyone be interested in this?

---

#### [2025-10-16 03:13:54] @ehwha

cyright is a language server for cython, I think vscode has an extension that uses it, but ya it doesn't support all the cython definitions

---

#### [2025-10-16 04:53:29] @cjdsellers

Hey <@797412687784312862> 
Sure, just using a fairly vanilla tmux + neovim setup. So mostly a mixture of knowing where to look having written that adapter and ~10 years in the codebase. LLMs can help for initial PR review/summaries as well which I think I also used here (claude). There should be more tests for Polymarket as well though

---

#### [2025-10-16 05:01:37] @cjdsellers

Hey <@442782643344506890> 
There's a bit of a blurb on adapters on the [ROADMAP](https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md#community-contributed-integrations) for context. It's tricky at the moment because patterns in Rust are improving but still fairly fluid, so it might not be the best time to be introducing more community adapters

---

#### [2025-10-17 18:44:40] @mrforbes

Using Claude or Codex is the way to go here. It will greatly speed up your configuration.

---

#### [2025-10-17 19:38:48] @deploya.dev_martin

Hey, also trader since before and new here. How does NautilusTrader compare to VectorBT Pro and AmiBroker? I am looking to develop intraday strategies for microcap shorting. And which data source is recommended for intraday bars that is supported with Nautilus?

---

#### [2025-10-18 15:04:38] @faysou.

databento for intraday data. It a big plus that nautilus supports it, it's the best historical data provider in my opinion

---

#### [2025-10-18 19:57:23] @faysou.

It's also relatively recent, so we're lucky it exists

---

#### [2025-10-18 20:32:21] @deploya.dev_martin

What makes you say Databento is better than Polygon. Have you done any comparision?

---

#### [2025-10-18 20:44:00] @faysou.

I haven't

---

#### [2025-10-19 10:05:42] @one_lpb

Databento could be very expensive at Trades downloads, and Polygon doesn't support futures right now. Anyone is using other data sources ?

---

#### [2025-10-19 10:46:38] @faysou.

If you need trades resolution it means you have a certain level of sophistication, the price of the data is relatively cheap compared to the money you can make with futures. You can also download 1m bars with databento, or 1m quotes. This reduces the price a lot for not precise research, which could still be enough.

---

#### [2025-10-19 10:48:26] @faysou.

I don't think there's a similar alternative to databento in terms of data quality and affordability.

---

#### [2025-10-19 12:18:14] @aulegabriel

<@757548402689966131> 

Hello cjdsellers,

I’m Gabriel, a Python/Django developer with over 4 years of experience. Recently, while researching how to build a trading bot, I came across your GitHub repo and was impressed by the community’s work. I’m eager to contribute to open-source projects and would love to join your community.

I’m a fast learner and dedicated developer, and I’d be thrilled to take on a Python-related task to showcase my skills. Please let me know if there’s an opportunity for me to contribute, especially in areas like trading bots or general Python development. I’d be happy to hear from you!

Thank you,
Gabriel

---

#### [2025-10-19 13:59:15] @cluborange_93575

Hi guys, I think given Kalshi is now available across the world, building an integration to them will be pretty valuable for the community. Looking at the APIs, there are a lot of similarities with Polymarket, so hopefully some things can be reused and adapted.

---

#### [2025-10-19 15:22:46] @sinaatra

thks for the tip

---

#### [2025-10-19 17:11:27] @one_lpb

I need Trades to have real volume and position resolution as real as possible, with 1 minute bars I don't have enough precision at which price I'm SL or TP. But ok maybe i'll wait for Polygon to release Futures API.

---

#### [2025-10-23 02:38:18] @jgalent

Hi guys, i did read through some messages saying postgres as a backend has no timeframe, I did go through the code and saw there's a postgres database that could be initialised with the nautilus cli. Was wondering what functionality leveraging postgres cache or catalog would be possible? I still need to get across some of the concepts around caching and the catalogs, but it would be awesome to have it as a backing database. Thanks for all the work on this - had gone through some of the tutorials and current capabilities of it is amazing.

---
