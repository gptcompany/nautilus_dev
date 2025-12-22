# NautilusTrader - #general

**Period:** Last 90 days
**Messages:** 171
**Last updated:** 2025-12-22 18:01:37

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
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1425224828373434450/image.png?ex=694a58ce&is=6949074e&hm=a1d84d07d577574521de79a6eef9bab40fb83acd4a07088f415bd3ca0f7e9685&)

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
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1426929729432322130/image.png?ex=694a9dde&is=69494c5e&hm=e18ae3fc8babe3ee755a09c387a0b3f512073a6ca6308774ad0400c42cf19802&)

---

#### [2025-10-14 02:00:19] @details777

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

#### [2025-10-17 19:38:48] @deleted_user_3434563

Hey, also trader since before and new here. How does NautilusTrader compare to VectorBT Pro and AmiBroker? I am looking to develop intraday strategies for microcap shorting. And which data source is recommended for intraday bars that is supported with Nautilus?

---

#### [2025-10-18 15:04:38] @faysou.

databento for intraday data. It a big plus that nautilus supports it, it's the best historical data provider in my opinion

---

#### [2025-10-18 19:57:23] @faysou.

It's also relatively recent, so we're lucky it exists

---

#### [2025-10-18 20:32:21] @deleted_user_3434563

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

#### [2025-10-25 18:16:15] @_minhyo



**Attachments:**
- [image0.gif](https://cdn.discordapp.com/attachments/924498804835745853/1431707949847412848/image0.gif?ex=694a33af&is=6948e22f&hm=be1b20104857fdca3b35d5e784b50ef5102a07679a8caeac3d11bba31a4c4af6&)

---

#### [2025-10-27 19:27:20] @euriska

This would be a good time to add adapters for tasty and tradier

---

#### [2025-10-30 03:55:34] @ajay_kumar_joshi

Hi <@757548402689966131> , I was going through some past messages and saw that the community’s still waiting for a beginner course on getting started with algo trading using NT. Just wanted to check if we’re working on that yet?

Also, in the meantime, could you please suggest any good resources for someone completely new to algo trading?

Thanks!

---

#### [2025-10-30 06:28:56] @cjdsellers

Hi <@949959605809737838> 
Thanks for reaching out. Unfortunately we haven't had any extra bandwidth to devote to those sorts of educational resources - but it will happen eventually. In the mean time I don't have any specific recommendations, but will offer two tips: 
1) try to seek the source of knowledge, rather than "trading education" products build on top, 
2) get started with coding and trading on a demo or very small size sooner than later - to put knowledge into practice early (learning will be fastest in this way).

Don't expect results to happen quickly, this space rewards the careful, disciplined, patient approach. I hope that helps and good luck!

---

#### [2025-10-30 06:33:25] @ajay_kumar_joshi

Thanks! I’m a Python dev with a bit of trading knowledge — mainly just looking to build and backtest some strategies based on what I know. I’ll start with your suggestions, really appreciate the tips! 🙏

---

#### [2025-10-30 13:17:56] @akajbug

Food for thought for anyone that has time and would like to help others, potentially build some credibility in this space (algo trading/backtesting and software engineering), and learn exponentially faster:

Learn Nautilus Trader by teaching others. Don’t add pressure to yourself - just do something that you enjoy and find fun and document the journey with simple blog posts, YouTube or any other medium. I’ve considered it myself and may still approach it soon. I may focus on building Rust adapters since that’s my primary focus of learning ATM on top of learning more about Nautilus overall.

---

#### [2025-10-30 13:18:06] @akajbug

sorry for that essay ha!

---

#### [2025-10-31 12:26:44] @ayoze5798

Hello,
Is there a similar, non-open source project like Nautilus Trader where the algo engine core is written in a compiled language (C++, Rust, etc.) and core Algo API functions are exposed in an easier scripting language or with a Garbage Collector (Python, Lua, TypeScript)?
I need specifications from that type of industry-grade software. If you can provide them, I would be thankful. (I'm writing my own specs for an Algo API implemented by embedding Lua into C++, but I have trouble writing the specifications because I don't know where to start and what to focus on.)

---

#### [2025-10-31 12:50:14] @akajbug

I’m curious what “industry grade” means? Would Nautilus Trader not be considered that? Or does Open-Source exclude it? Genuinely curious because Nautilus Trader is fantastic and better than anything I’ve tried by far

---

#### [2025-10-31 13:10:37] @ayoze5798

I'm seraching for some API specs used by big banks

---

#### [2025-10-31 13:36:37] @fudgemin

No likley not. Good luck in finding 'information' about such systems as well. There is zero need for any fund to enlighten you about proprietary execution technology. Most firms dont even use such, its largely discretion based. Its just easier to act upon, easier to blame, easier to scale. They execute manually. 

I suspect anything MFT, HFT, is purely custom, implemented in-house and built/iterated on over many years. The entire algo/quant space is actually still fairly fresh imo. If you built a system using Ocaml, you dont make secondary python hooks/api calls. You tell your devs to code in ocaml. solved.

---

#### [2025-10-31 16:37:14] @faintent

really interesting, what other libraries you tried?

---

#### [2025-10-31 16:37:50] @faintent

or like algo trading platforms

---

#### [2025-10-31 16:38:35] @faintent

also have you approached building an algo bot from scratch yet? out of curiosity

---

#### [2025-10-31 17:45:21] @fudgemin

https://www.youtube.com/watch?v=uhVTMBZe7p0

**Links:**
- Nautilus Trader & Grafana

---

#### [2025-11-01 19:05:40] @ayoze5798

I don't need infomration. I need specs that they are sending to their clients

---

#### [2025-11-01 19:25:06] @javdu10

Hello there! any mcp server for the documentation ?

---

#### [2025-11-03 19:33:29] @joebiden404

Hi, 
Anyone tries to run NT inside Google Collab and the Backtester logs aren't shown to stdout? or it Is just me?
I'd like a little help in that one.

---

#### [2025-11-05 14:15:59] @hyperanar

gm guys, just ran across Nautilus - excited to try it out

---

#### [2025-11-05 21:13:35] @q4202018

Total newbee to git hub n such.  Anyone willing to direct me?

---

#### [2025-11-07 02:32:31] @jonathanbytesio

We can do it together

---

#### [2025-11-09 07:50:08] @dem070699

Hi guys, is there a version of Nautilus Trader thats fully in Rust?

---

#### [2025-11-09 10:33:12] @bibamoney

so it's works well ?

---

#### [2025-11-10 18:36:17] @q4202018

<@756122725495472138> hi Johnathan.

---

#### [2025-11-10 20:19:39] @dariohett

<@757548402689966131> I was surprised to see that there are two MessageBus implementations - one in Rust, one in Cython. Any specific reason for the duplication? Or am I missing where the Cython impl calls into the Rust one?

---

#### [2025-11-11 13:10:40] @jonathanbytesio

Hi

---

#### [2025-11-12 01:58:08] @cjdsellers

Hi <@797412687784312862> there is a Rust core shared between both v1 and v2 versions of the system, then there are certain components where the Rust impl is not entirely compatible with the v1/legacy system and so the Cython equivalent has to remain until the port is completed and the message bus is one of these components - so it's not by design (topic string matching for the message bus is implemented in Rust only)

---

#### [2025-11-16 18:45:30] @christosconst

Hi all, new to NautulusTrader and reading about it. I can see that Nautech will be 10 years old next month, happy anniversary to the team!

---

#### [2025-11-17 14:29:22] @maxwell1999.

Hi guys, you doing great job here.

---

#### [2025-11-17 14:29:53] @maxwell1999.

Just curious to know how long we've to wait for official full working Hyperliquid Connector?

---

#### [2025-11-17 15:32:27] @spec_leon

hi traders
i am a software engineer, typescript/python is my strongest language, having played with them for about a decade.
i have about 5 years of experience in blockchain, that's where i played with nautilus, i have worked on crypto trading projects on this.
i also have done many trading-related works, like integrating ai into leverage trading platform for forex, crypto assets on base chain, etc.

if you are looking for a dev who can actually help you, setting up strategy(i have background in math), implementing in actual code, implement automation solution etc, let's talk!

---

#### [2025-11-17 16:20:09] @christosconst

<@370720733141139468> I think most people here are developers

---

#### [2025-11-17 16:21:22] @spec_leon

really?

---

#### [2025-11-17 16:21:45] @spec_leon

anyway, i am open to any kind of connections, i like meeting new people

---

#### [2025-11-18 13:40:42] @maxwell1999.

Better way to pitch yourself is solve issues in github and than get noticed by that.

---

#### [2025-11-19 15:11:45] @dhksms

Can u invite me to the chinese channel? Thank u!!

---

#### [2025-11-19 17:11:35] @dun02

bro i finally got a backtest to run

---

#### [2025-11-26 18:23:19] @nehemiahs

I am thinking about switching over from Quantconnect to Nautilus so that I can process big data effectively. I am curious if anyone can provide any insights into dynamic universe modeling on Nautilus. It would seem to me that this is a place where Nautilus might make it very challenging to dynamically screen thousands of stocks by technicals and fundamentals with point-in-time accuracy. Thus, making switching from Quantconnect more challenging. Does anyone have any experience in creating and testing dynamic stock selection strategies on Nautilus? Do you have any recommendations on constructing the pipeline? -Thanks!

---

#### [2025-11-27 10:49:17] @river7816

I do not think nautilus is a suitable framework for testing dynamic stock selection because it is used for HFT trading not for portfolio management

---

#### [2025-11-28 02:55:00] @oldbachaso

Historical for EOD has basically no coverage (7 years)

---

#### [2025-11-28 15:58:26] @.cy19

Hi, can u invite me to the Chinese channel? Thank u very much!!

---

#### [2025-11-29 04:52:44] @null_12954_42083

Hi, could you please invite me to the Chinese channel too? Thanks!

---

#### [2025-11-29 08:48:28] @eleelegentbanboo

me too

---

#### [2025-11-29 08:49:29] @eleelegentbanboo

能邀请一下我吗 <@224557998284996618>

---

#### [2025-11-29 08:50:17] @gz00000

All done.

---

#### [2025-11-29 12:02:03] @luminous05191

能邀请一下我吗，谢谢

---

#### [2025-11-29 15:52:38] @ufviuz

🙋‍♂️

---

#### [2025-11-30 04:05:30] @a3ak

me too, please, many thanks <@224557998284996618>

---

#### [2025-11-30 10:31:41] @fangbin9101

can you please let me join the Chinese channel too, thx.

---

#### [2025-12-01 23:20:27] @fudgemin

<@757548402689966131> can you make a discord channel, strickly for docs? Want to post brief snippets of solutions, that are not covered in current documentation. Not a discussion channel. Simply just for collecting summaries of solutions from user or ai. 

I spent the last 2 hours on a very nuanced issue, that im sure others have covered themselves. Im was using a consumer and published node on the cache. Trying to sub to custom data on the consumer:

        self.subscribe_data(
            DataType(FlowBaseMetrics),
            client_id=ClientId("FEATURES_EXT"),
        )

Needed to add client ID. Not specified anywhere in docs. Had to read source to determine how type were defined or called. Went of serialization, class renames, many wasted steps. 

You should start collecting these use cases, and thats what the channel is for. SImply summarize or allowing users to parse those messages may save us all a bit of time

---

#### [2025-12-02 05:46:31] @cjdsellers

<@391823539034128397> docs can always be clearer and better. That one is documented under [Custom data](https://nautilustrader.io/docs/nightly/concepts/data#custom-data) though

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1445290012806610994/image.png?ex=694ad577&is=694983f7&hm=480808cd1e42b47bfe2a002c20f1e23fdc8aee06f394d8864099bf12f19308ae&)

---

#### [2025-12-02 14:16:22] @fudgemin

You know after solving the issue, i had this strange feeling I saw this mentioned before.  I was working from the cache and msg bus docs. This is proof Ai is making me dumber

---

#### [2025-12-03 16:13:54] @thisisrahul.

I have encountered a bug with backtestdataconfig. It doesn’t honor the bar_spec or the bar_type while retrieving. I dived  a bit deeper and looks like while querying the files, it is using only the ‘identifier’ for filtering out the files. And identifier is only the instrument_id for the bar data_cls

---

#### [2025-12-03 16:21:56] @christosconst

Is importing in the parquet catalog supposed to slow down as the catalog becomes larger? I'm importing 10k daily bar files (~390 bars per file). Seeing some performance degradation as they import and wondering if I should be looking into my import script

---

#### [2025-12-05 11:28:46] @roaringkittyexception

the issue may be you have big number of tiny files, have you tries compacting into a less files ?

---

#### [2025-12-05 11:48:52] @faysou.

I likely have solved this recently in the develop branch. To create one catalog session for all files of a data type instead of one per file.

---

#### [2025-12-05 11:49:10] @faysou.

You can try to compile or install the develop branch

---

#### [2025-12-08 11:44:19] @ghosttrader1377

What is the difference between the latest version and nightly version?

---

#### [2025-12-09 15:20:20] @courage521915

anyone can  let me join the Chinese channel ？

---

#### [2025-12-10 03:00:11] @kevinthm

by latest i am assuming you meant develop version. from what i understand,

develop version is simply the latest of the latest version that the team is working on.

at the end of the day, they will package that into a nightly version, so that is slightly slower.

finally stable versions are the slowest, being only released weeks to months interval, but have the confidence from the team to be used in production

---

#### [2025-12-12 12:47:29] @marksnow_

您好<@224557998284996618> ,帮邀请进入中文频道可以吗?谢谢

---

#### [2025-12-12 14:15:34] @stringer_fan_51598

i wanna in Chinese channel too🫶 Can anyone invite me in？thanks～

---

#### [2025-12-13 04:43:20] @_davidlin

<@224557998284996618> 可否邀請加入中文頻道嗎? 謝謝

---

#### [2025-12-14 09:18:42] @yixinfx

<@224557998284996618> 可否邀請加入中文頻道嗎? 謝謝

---

#### [2025-12-14 21:33:31] @windows95world

Hey guys,
can anyone share how they deal with ticker name changes in their backtests? E.g. Meta going from "FB" to "META" in 2022. Or do you solve this problem at the data level and normalize the data beforehand? 

Does Nautilus support something dynamic like this? E.g. a ticker name change event comes in and all the positions etc update to reference this new ticker name. The same issue also applies to splits and reverse splits. 

Hoping to get any advice before building something purely custom, thanks!

---

#### [2025-12-15 04:04:32] @even_27404

<@224557998284996618> 可否邀請加入中文頻道嗎? 謝謝

---

#### [2025-12-15 08:11:30] @cjdsellers

Hey <@585120053046018058> 
That's always a tricky security master / corporate actions type issue (as you surely know). Nothing is built in to handle this out of the box. My advice for you would be to handle it as the data would have been presented in real time (point-in-time PIT), rather than pre-processing - but then again, I haven't done much backtesting on equities that need to handle this sort of thing, so there may be various techniques that involve pre-processing as well

---

#### [2025-12-15 12:45:32] @vtoptomoon

<@224557998284996618> 可否邀請加入中文頻道嗎? 謝謝

---

#### [2025-12-15 15:12:22] @francomascarelo_ai

<@224557998284996618> 可否邀請加入中文頻道嗎? 謝謝

---

#### [2025-12-15 19:15:24] @windows95world

Thanks Chris, yea ideally it needs to work during live trading too so a dynamic solution would be best. Do you think updating all open positions etc. with the new symbol is simple? Essentially something similar to what I mentioned before - a ticker name change signal (or stock split) signal comes in and everything should be updated.

If this is not supported out of the box - is this something you want to support in the future?

---

#### [2025-12-15 19:16:46] @windows95world

If you have any advice on updating the state in Nautilus before I get started I would appreciate it.

---

#### [2025-12-15 22:43:15] @cjdsellers

Hey <@585120053046018058> best was forward here is if you raise an enhancement request on GitHub with some detailed requirement specs

---

#### [2025-12-15 23:04:51] @windows95world

Sounds good! Will do

---

#### [2025-12-16 18:57:31] @windows95world

Here you go: https://github.com/nautechsystems/nautilus_trader/issues/3307

Feel free to provide insights in terms of how you envision this and I'll try my best to implement it. I might've missed something obvious for you.

**Links:**
- Add support for ticker name changes, stock splits and corporate act...

---

#### [2025-12-17 14:17:48] @idrtis

possible to do custom integrations? would it be easy? like for hyperliquid etc?

---

#### [2025-12-18 08:26:15] @christosconst

It's my one month anniversary of starting to play with NautilusTrader. Watch my vibe coded bot lose money with style on 0DTE options https://youtu.be/qK_Sy5LCOFE

**Links:**
- Screen Recording 2025 12 18 at 10 17 44 AM

---

#### [2025-12-18 08:33:26] @simowgoat

yes, it takes some effort though 
check https://nautilustrader.io/docs/nightly/developer_guide/adapters

**Links:**
- Adapters | NautilusTrader Documentation

---

#### [2025-12-19 00:40:00] @faysou.

I think though that spending more time on strategy development is better for getting to the money. Fancy UI looks good but it doesn't make money (I know that from past experience). Once the money is there, it can make sense though to make things look better.

---

#### [2025-12-19 00:41:00] @faysou.

Jupyeter is enough for a user interface and marimo looks great for interactivity in a notebook, I need to look more at it

---

#### [2025-12-19 07:07:08] @christosconst

Eh, its a starting point that will help me find bugs in the strategy's code. It was mostly an environment setup in the last month. I now have to spend a couple of months figuring out entry/exit conditions. Got any alpha tips for the homeless? 🙂

---

#### [2025-12-19 07:09:09] @faysou.

Yes, I suppose it helped you learn some aspects of the library.

---

#### [2025-12-19 07:11:52] @christosconst

At the moment its just astrology, I look at TA indicators, if some of them align, I enter

---

#### [2025-12-19 07:44:47] @cjdsellers

Hey <@364189605907660811> 
Well done on the progress. One approach is to keep it as simple and understandable as possible, based on some market dynamic or factor that exists in reality (so probably not astrology- although I can’t unequivocally state that doesn’t work either 😄), then build a model or a TA setup to detect it specifically

As for what this could be, that’s the fun part up to your own creative exploration

---

#### [2025-12-21 18:00:25] @akatsuki_alpha__42583

I have a similar use case and have been working to find a good solution. Definitely possible but will likely take some customization of nautilus. Happy to share any developments I make

---

#### [2025-12-22 05:02:33] @bart04262_88665

“Switching over from Quantconnect so I can process big data effectively”
What do you see as a limitation of QC that Nautilus solves?

---
