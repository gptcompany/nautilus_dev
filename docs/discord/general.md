# NautilusTrader - #general

**Period:** Last 90 days
**Messages:** 169
**Last updated:** 2026-01-07 01:29:25

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
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1426929729432322130/image.png?ex=695e645e&is=695d12de&hm=7fb32b7dee4fbf78eb7a1872396146989c93ef4d39ea37af81a0f2804360c4a6&)

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

#### [2025-10-17 19:38:48] @Deleted User

Hey, also trader since before and new here. How does NautilusTrader compare to VectorBT Pro and AmiBroker? I am looking to develop intraday strategies for microcap shorting. And which data source is recommended for intraday bars that is supported with Nautilus?

---

#### [2025-10-18 15:04:38] @faysou.

databento for intraday data. It a big plus that nautilus supports it, it's the best historical data provider in my opinion

---

#### [2025-10-18 19:57:23] @faysou.

It's also relatively recent, so we're lucky it exists

---

#### [2025-10-18 20:32:21] @Deleted User

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
- [image0.gif](https://cdn.discordapp.com/attachments/924498804835745853/1431707949847412848/image0.gif?ex=695ea2ef&is=695d516f&hm=d3c54d3321c1dfbc67a3e24b4fe31ca5c68140ed23709c25ec7d1fd4136b57ba&)

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

#### [2025-11-03 19:33:29] @joejoe404

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
- [image.png](https://cdn.discordapp.com/attachments/924498804835745853/1445290012806610994/image.png?ex=695e9bf7&is=695d4a77&hm=5955c7dff5e3f9956c96ff5925f74dc770afe84562246fb37633d7b4496c2596&)

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

#### [2025-12-23 21:10:41] @thisisrahul.

I’m planning to build a adapter for Indian market. I went through the developer documentation, is it a must to implement the adapter in rust core? Or can I code in the python layer? I won’t be making raw http calls but would be leveraging my stockbrokers python library

---

#### [2025-12-24 14:55:28] @gsswllnvrknw

Hello! I’m looking for a trading terminal for a lighter. Does anyone know if there is such a product? Something like Tiger Trade, MetaScalp, CScalp

---

#### [2025-12-24 17:41:05] @valeratrades

is there a good way to have actors know full OB data at every step? Say I have a different implementation for full aggregated cross-exchange OB. Sending through the bus would be way too expensive, - am I limited to accessing it outside of the system and syncing state manually?

---

#### [2025-12-24 20:41:23] @gmdavid12

Hi guys, is anyone here using Nautilus for polymarket

---

#### [2025-12-25 09:02:34] @dhanush_tummala

I am

---

#### [2025-12-25 09:11:09] @gmdavid12

I am new here so i dont know much, but is Nautilus good for backtesting, There is a lot of info online but i prefer to hear directly from a user if thats ok

---

#### [2025-12-25 10:04:54] @dhanush_tummala

Yes it is good for backtesting as well as Production deployment, It is well written, well maintained, and well documented. Moreover, it is fast. However, there is a bit of a steep learning curve to get things moving initially.

---

#### [2025-12-28 01:50:05] @.algo3

I have done this.  

I use my brokers (alpaca) snapshot api endpoint to get a bulk snapshot of the bars im interested in.  

I then save daily snapshots of these thousands of equities (the api filters some things like liquid, easy to short/borrow etc), it includes data like volume for my period. 

I use these snapshots as candidate parsing lists for each backtest day, and a live screener with the same logic and api call.  

My backtest script essentially runs a separate backtest for each day and combines the results, this allows me to constrain the minute data in memory to just my 50 different candidates daily from a universe of thousands of equities.

My strategy is intraday but if you are holding for a long time you might be more concerned about suvrivorship bias than I am, but the alpaca endpoint will return inactive symbols.

To be fair, in quantconnect, I had to do something similar because their coarse universe updates only in premarket hours.

---

#### [2025-12-29 06:19:14] @jakob_56860

can we create custom instrument types without needing to go wire it into the rust backend and still have it work (basically trying to implement a custom version of the BinaryOption)

---

#### [2025-12-29 08:32:28] @cjdsellers

Hey <@1357916439453110355> that's non trivial, no easy way other than to implement it everywhere. Was there a specific field you needed on binary options?

---

#### [2025-12-29 20:13:25] @jakob_56860

I want to make it more poly market specific and expose condition_id, token_id, and potentially a few other features as properties of the instrument. definltly understand that this can be done using the info but was just curious

---

#### [2025-12-29 20:13:34] @jakob_56860

thanks for the quick response and information though

---

#### [2025-12-29 20:14:04] @jakob_56860

(also completely understand that how its currently setup the ids are derived from the inst id)

---

#### [2025-12-29 20:57:07] @jakob_56860

ideally actually I would be able to break things down into the Polymarket Markets and then have a series of tokens (the binary options) as insturments within a given market. though as you say this would be very specific to polymarket and thus only really be a custom implmentation

---

#### [2025-12-29 21:49:35] @cjdsellers

Thanks <@1357916439453110355>, there will be improvements to the Polymarket integration over time, so this feedback is valuable for determining what is important for users

---

#### [2026-01-03 09:32:43] @.davidblom

Anyone tried setting up a backtest with options? Not sure if all the features are implemented to simulate selling puts for example.

---

#### [2026-01-03 11:54:35] @megafil_

Hi, having issues with the clock again. If you set a timer during a timer event, the clock becomes non-monotonic. How should this be done in the nautilus paradigm? 
Essentially it seems that timer events do not play the same role as, e.g., bars or data. LLM suggests to "set the clock time to each popped TimeEvent.ts_event while draining the heap",
is this doable?

```2020-01-01T00:00:00  received bar at 2020-01-01 00:00:00
2020-01-01T00:00:00  setting alert ALERT to trigger at 2020-01-01 00:00:02+00:00
2020-01-01T00:00:02  flush called ALERT.
2020-01-01T00:00:02  setting alert ALERT to trigger at 2020-01-01 00:00:04+00:00
2020-01-01T00:01:00  received bar at 2020-01-01 00:01:00
2020-01-01T00:01:00  alert ALERT already set to trigger at 2020-01-01 00:00:04, skipping set.
2020-01-01T00:00:04  flush called ALERT.
2020-01-01T00:00:04  setting alert ALERT to trigger at 2020-01-01 00:00:06+00:00
2020-01-01T00:02:00  received bar at 2020-01-01 00:02:00
2020-01-01T00:02:00  alert ALERT already set to trigger at 2020-01-01 00:00:06, skipping set.```

```class Probe(TimerProbeActor):
    def on_bar(self, bar) -> None:
        self.log.info(f"received bar at {pd.to_datetime(bar.ts_event)}")
        self.set_alert()
    def flush(self, evt=None) -> None:
        self.log.info(f"flush called {evt}.")
        self.set_alert()
    def set_alert(self) -> None:
        if self._alert_name in self.clock.timer_names:
            self.log.info(f"alert {self._alert_name} already set to trigger at {pd.to_datetime(self.clock.next_time_ns(self._alert_name))}, skipping set.")
        else:
            self.log.info(f"setting alert {self._alert_name} to trigger at {self.clock.utc_now() + self._alert_delay}")
            self.clock.set_time_alert(
            name=self._alert_name,
            alert_time=self.clock.utc_now() + self._alert_delay,
            override=True,
            allow_past=True,
            callback = self.flush
        )```

---

#### [2026-01-03 13:47:33] @tearsinrain__

hey everyone! happy to be here. been in quant / ai since 2016. currently building out an automated research system for my quant development. digging into nautilus trader right now and it looks like exactly the missing piece ive been searching for!

---

#### [2026-01-03 13:47:51] @tearsinrain__

has anyone made a dashboard type tool yet?

---

#### [2026-01-03 13:49:56] @megafil_

As I am looking into implementing a fix, i am seeing TestClock: heap: BinaryHeap<ScheduledTimeEvent>, // TODO: Deprecated - move to global time event heap,
this "global time event" is potentially what i need, is this already available and if so, how to use it?

---

#### [2026-01-03 14:06:09] @tearsinrain__

do you have a line number associated with that error / reference to where in the codebase thats being thrown

---

#### [2026-01-03 15:05:42] @bigcheddarr

Cool

---

#### [2026-01-03 15:06:34] @bigcheddarr

For the ai component do u guys hire h100s directly per hour or wat do u do for the ai bit using Claude max plan or any of these things seem restrictive

---

#### [2026-01-03 15:07:09] @tearsinrain__

depends on the use case

---

#### [2026-01-03 15:07:27] @tearsinrain__

my system allows me to plug in whatever model works so for a lot of stuff, smaller and cheaper models do fine

---

#### [2026-01-03 15:07:47] @tearsinrain__

and i can run some pretty powerful stuff locally like gpt oos 120bn and thats good enough for most loads

---

#### [2026-01-03 15:08:25] @tearsinrain__

but frankly, this is less of an issue besides when it comes to cost because when youre generating millions upon millions of tokens in an automated fashion, it really starts to add up

---

#### [2026-01-03 15:09:24] @tearsinrain__

in most cases, renting an h100 or something cheap from a provider like salad is way way way cheaper and you can get literally insane tokens per second. like with a gwen 8bn model which is good for most structured generative workloads (and fine tunable), you can get something like 5000 - 8000 tokens per second

---

#### [2026-01-03 15:10:15] @tearsinrain__

so if i estimate a 20,000,000 token job / 80,000 tps = 2,500s = 41 minutes. less than an hour of compute time. so like $2 on most cloud compute providers for an h100

---

#### [2026-01-03 15:34:04] @megafil_

that would be clock.rs i believe. that string should be easy to find in the code base

---

#### [2026-01-03 15:52:09] @tearsinrain__

thats not really enough context to allow me to do a traceback or anything

---

#### [2026-01-03 16:09:40] @megafil_

i might not have explained myself well enough, the problem is that the clock is not able to process injected alerts in order of ts_event and breaks monotonicity (see log output above with actor example), i was going to modify the event heap and stumbled across this string in the code base with a "TODO" that kind of sounded like what i was trying to achieve, which is to create a global clock to make sure i can simulate just as it would be in live. hope this clarifies it more

---

#### [2026-01-03 22:57:36] @megafil_

ok my fix is not working. what is the point of timers if you cannot backtest them? shouldn't a timer event also advance the internal clock by itself? seems to be an unnecessary restriction to wait for a bar or other external input, just add into sorted queue and advance until next event, of course this would slow down stuff in the backtest but there are other optimizations that could be done to minimize the impact, anyway is there a better forum to discuss this? maybe i could connect with the person in charge of the scheduler

---

#### [2026-01-03 23:02:26] @javdu10

Maybe it has something todo with the timzone ? 

I'm doing this, don't know if it can help you : 

```
self.clock.set_time_alert(
            name= str(uuid4()),
            callback=self.setup_next_thing,
            alert_time= (datetime.fromtimestamp(self.some_unix_time, timezone.utc) + timedelta(minutes=3, seconds=0)),
        )
```

---

#### [2026-01-03 23:02:54] @javdu10

and the backtest timer work as expected

---

#### [2026-01-03 23:05:33] @megafil_

thank you, maybe the issue is that i reuse the timer name? else i am just using the clock.utc time plus some delta which is happening before the next bar event, will try that

---

#### [2026-01-03 23:51:54] @megafil_

ok this wasnt it. i have filed a bug report in case it helps https://github.com/nautechsystems/nautilus_trader/issues/3384

**Links:**
- TestClock not monotonic: Repeated TimeEvents do not obey monotonici...

---

#### [2026-01-04 01:05:34] @cjdsellers

Hey <@1309590087243141140> 
Welcome! we're currently working on a live dashboard as a premium product

---

#### [2026-01-04 01:22:56] @megafil_

<@757548402689966131> i think i have a fix which passes my test and also my original problem which is a bit more complicated. it is a smallish change in BacktestEngine,  _process_raw_time_event_handlers (engine.pyx) where events are pushed on a heap and then processed in order of timestamp. would be good if someone with a bit more experience with the scheduler could review

---

#### [2026-01-04 01:24:18] @cjdsellers

Hey <@882228657265979393> thanks for the issue report and explanation. This sounds like something we have looked at before to solve a couple of things so might be a viable direction, will look when I can

---

#### [2026-01-04 02:00:08] @.a11onsy

Hi guys

---

#### [2026-01-04 02:00:13] @.a11onsy

I have a question

---

#### [2026-01-04 02:00:57] @.a11onsy

The whole api_ref doc looks like auto generated: https://github.com/nautechsystems/nautilus_trader/tree/develop/docs/api_reference

**Links:**
- nautilus_trader/docs/api_reference at develop · nautechsystems/nau...

---

#### [2026-01-04 02:01:07] @.a11onsy

How can I generate the doc locally?

---

#### [2026-01-04 02:01:09] @.a11onsy

Ty

---

#### [2026-01-05 01:35:54] @megafil_

please take a look https://github.com/nautechsystems/nautilus_trader/pull/3390)

---

#### [2026-01-05 04:08:37] @cjdsellers

Hey <@498306535064338444> 
There's a clue in the make file https://github.com/nautechsystems/nautilus_trader/blob/develop/Makefile#L327
You might be able to just run `make docs-python`, hope that helps!

**Links:**
- nautilus_trader/Makefile at develop · nautechsystems/nautilus_trader

---

#### [2026-01-05 04:10:51] @.a11onsy

Ty

---

#### [2026-01-05 04:11:18] @.a11onsy

Helps a lot

---

#### [2026-01-05 17:47:16] @mohammad02639

Hello I hope you are well. I noticed https://nautilustrader.io/docs/nightly/integrations/hyperliquid/ is under active development. Is the documentation on the site the features that can be used right now (I am assuming the additional ones being worked on will be added when finished) ?

**Links:**
- Hyperliquid | NautilusTrader Documentation

---

#### [2026-01-05 22:02:58] @notceo777

hello can someone helpme to build a simulated exchange for paper trading?

DataEngine

RiskEngine

ExecutionEngine

OrderEmulator

---

#### [2026-01-05 22:05:14] @cjdsellers

Hi <@1274556847902429260> welcome, I think the most efficient approach for this these days is to pose the same question to an LLM. It should quickly be able to iterate on your individual data and use cases as well

---

#### [2026-01-06 02:03:09] @bobbyjohnson_

Gm

---

#### [2026-01-06 02:03:42] @bobbyjohnson_

Anybody using the backrest to track bitcoin monthly candle wicks? Or even daily candle wicks?

---

#### [2026-01-06 02:19:48] @.a11onsy

If possible, kindly ask if we can have a complied version of docs in github repo, thanks for all your guys work!

---

#### [2026-01-06 02:19:50] @.a11onsy

<@757548402689966131>

---

#### [2026-01-06 02:21:05] @.a11onsy

sorry if im asking for too much

---
