# NautilusTrader - #dev-python

**Period:** Last 90 days
**Messages:** 46
**Last updated:** 2025-10-23 04:00:39

---

#### [2025-07-27 20:35:34] @premysl_22228

Hi. I am looking for a volunteer, who will cross check my changes to TimeBarAggregator after merged to develop branch. The branch is getting too long lived (few months) and advanced testing with A->B->C <-> A->C, request_data=subscribe_data or reimplementation testing is currently blocked by memory leaks (absence of real data in pipelines was workaround by synthetic data). Some of the tests passed (not the whole comprehensive test suite), so I have small confidence, it is correct, but I need a second eyes to test my changes, so we don't release buggy implementation. Is here anyone willing to test my changes after they are merged? (Warning: simple log comparison isn't enough, since the current implementation has several bugs already)

---

#### [2025-07-28 19:21:21] @faysou.

I'll have a look when you're done, I'll be curious about it as I've worked on this before.

---

#### [2025-07-29 20:33:01] @premysl_22228

After further thinking, I will then maybe limit the amount the verifications before creating a PR. It's taking too long, I have in plan one two further refactorizations of that (much smaller one, but controversial...I want to keep that discussion later, when it will be from implementation evident, that e.g. LEFT_OPEN/RIGHT_OPEN makes no sense) One more pair of eyes helps me to move further faster. **Thanks.** (It's open question for me, whether I will wait until memleaks are resolved...I have been working for few last days on advanced detectors, which should help pinpoint memleak to a source in Rust...)

---

#### [2025-07-29 20:33:43] @premysl_22228

<@965894631017578537>

---

#### [2025-07-29 20:36:59] @faysou.

Ok

---

#### [2025-07-29 20:47:34] @premysl_22228

Little offtopic, as this is rust-dev, but... <@965894631017578537>  : There are possibly tens/hundreds of memory leaks in "pure Rust". I don't trust the detectors yet, but I would like to know your opinion whether we want pure Rust memleak detections everywhere (on every test), if we find out, these are true positive. It would be nice to know, whether I am the only one, who wants to tests in nightly builds memleaks even in parts of code, which are considered safe. (If these findings I made comes out as true positive...)

---

#### [2025-07-29 20:49:24] @premysl_22228

To be clear, Chris didn't responded to the findings yet. He didn't want it in moment, when there was no suggestion, something is wrong with pure code.

---

#### [2025-07-29 22:23:32] @faysou.

On decisions like this it's Chris who decides. I would tend to agree that we should assume that the rust language doesn't create memory leaks easily. And that there are bigger problems to work on at the moment, ie. the migration to rust.

---

#### [2025-07-29 22:25:40] @faysou.

It's actually possible to work on other things than the migration to rust, but currently this is the biggest task Chris is working on.

---

#### [2025-07-29 22:49:54] @premysl_22228

It is partially commutative. It doesn't depend on the order much, memory leaks must be addressed in my opinion before v2 is released. - There is problem, that the assumption is currently being broken. I will maybe create a dummy PR with the memleak check code, so you and Chris can crosscheck - it depends on whether this is a result of a bug in the memleak test, or assumption is fully broken. Maybe I can crosscheck against Valgrind, whether the numbers about leaks will be the same. If yes, I would be getting more confident, we can no longer depend on the "safetiness", when it comes to memory leaks. - Memory leaks are pretty serious. It blocks the optimization, if you don't fork before each cycle, blocks loading data without a fork and might put your trading machine OOM.

---

#### [2025-07-29 22:51:10] @premysl_22228

(loading data into catalog)

---

#### [2025-07-29 22:52:04] @premysl_22228

It depends on how you do things, and I ran into memory leaks several times over last few months as a bad complication.

---

#### [2025-07-30 00:44:37] @cjdsellers

There are some existing memory leak tests here (none of which reveal issues at this time): https://github.com/nautechsystems/nautilus_trader/tree/develop/tests/mem_leak_tests

I just added another one for the high-level backtest API to capture the catalog streaming and its use of `CVec` across the FFI:
https://github.com/nautechsystems/nautilus_trader/commit/15070a27f01fbdbce6838f0cb4be5c5e1d93180a

Run with `memray` after 128 iterations it showed stable heap allocations of ~2.1 GB. If there _was_ a leak then it would have to be extremely subtle and slow growing, so not definitive yet.

<@1353826739851362345> given many of your leak detection tests are finding leaks in safe Rust, does this suggest an issue with the Rust language itself?
Should we consider confirming with more established profiling tools before continuing investigating with your custom tooling?

Are there any other users who might suspect memory leak(s)?

**Attachments:**
- [2025-07-30_10-39.png](https://cdn.discordapp.com/attachments/1192983338173079583/1399915557297586176/2025-07-30_10-39.png?ex=68facbf6&is=68f97a76&hm=c70875010b829731811a12c2d18405ca5465834f682f27751ed77e6f18f12ed4&)

---

#### [2025-07-30 01:20:03] @premysl_22228

I don't know yet, I would rather suspect that proclamed safetiness does not cover some kinds of memory leaks. **I need to still verify, that mistake is not on my side.** (Some of memory leaks protections are not guaranteed by design like circular dependency gc, which might cause some of leaks given the architecture of NT - we should definitely add memleak checks to safe code if we missed some already)

Yes, absolutely, there might be bugs, I would recommend to use Valgrind, to see the current status and review the source code of the tooling. As I have no experience with memrey, I can nor confirm or deny, that it is a valid tooling for given situation. I am personally surprised, that memleak wasn't caught by it (if it monitor the whole heap and not just Python subset)...the source code for the memleak in Python was at least twice verified (by you and me), is basically trivial and the mistake on our side is not so much probable. The >50 MiB increase is just suspicious and further investigation is in my opinion in place. 

Would you please try to run memray on the whole testset to verify, it catches the Rust memleaks and not only Python one. (Or confirm please, that you know for sure, it monitors the whole heap) The heap on my loca grows, I think, over 4 GiB and this presents much more probable memory leak. If this is replicatable in your environment, it would answer, whether memray is appropriate tooling.

In worst case, I have prepared test set using high level API, which allocates over >64 GiB - this should be definitely detected.

---

#### [2025-07-30 02:07:11] @premysl_22228

Just a thought about memray: Are the fixures reused or recreated each time? Maybe the leak might be in some fixure, if the test have some specific present.

---

#### [2025-07-30 13:58:00] @premysl_22228

I finished the verification of the memleak test implementation - it was mostly false positive. But there are some memory leaks (please ignore the integration tests and tests, which failed on their own) probably outside the safe code zone. To replicate, run `CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUNNER="valgrind --error-exitcode=1 --leak-check=full --show-reachable=no --show-possibly-lost=no --errors-for-leak-kinds=definite,indirect" cargo nextest run --no-fail-fast 2>&1 | tee valgrind.output`

**Attachments:**
- [valgrind.output](https://cdn.discordapp.com/attachments/1192983338173079583/1400115217379102793/valgrind.output?ex=68fadd28&is=68f98ba8&hm=a617b3637de1ff6c019ae5008991a630b77a462e383245524d4cfe8c635210fe&)

---

#### [2025-07-31 21:00:17] @premysl_22228

I will try to get an output with possibly lost too. It seems, there are some false positives, but as I dig deeper, we maybe can't get circular dependencies leaks without it.

---

#### [2025-08-03 21:34:57] @premysl_22228

I need an advice. I am making the synthetic data generator and I had an idea to let AI cover all scenarios which it had in mind. Sum(ideas)=198. Now it is implementing the 198 different scenarios...it is basically unreviewable code, which are all nondeterministic. I am wondering, is this something useful for community as they will be able to test their algos on "30 types of flash crashes", or it is useless and I should limit the amount of scenarios to what might be useful for NT testing? I am able to review code like brownian movement, which is #1 for me for synthetic data for testing, and some unrealistic scenerios like sin, sign,..., but the rest... How should I resolve this? - I am marking <@965894631017578537> and <@757548402689966131> as they will have probably the strongest opinion, but it is open discussion.

---

#### [2025-08-03 21:38:34] @premysl_22228

It is an absolute overkill for the aggregation testing. But it might be useful for users itself.

---

#### [2025-08-04 02:57:07] @cjdsellers

Hi <@1353826739851362345>,
I think the synthetic data with predictable properties is a great idea, especially from a testing perspective. Why don't we start with a minimal set though, i.e. instead of "30 types of flash crashes", we could just have 1-2 and then expand as required? Thereby keeping the initial changes smaller just to establish the synthetic data generation and usage patterns

---

#### [2025-08-04 06:16:06] @melonenmann

I think this is very useful. Do you write an generator where I can select type of events/situations or is that one dataset where everything is in? 

If it's one dataset it could be hard to identify on which event the algo the works.
But if I have an generator to create special dataset would be the most convenient option.

---

#### [2025-08-04 20:06:25] @premysl_22228

Hi. This sounds like a good idea. It will be hard for me to cut it down, because many of those scenarios are something, I would be protected from and optimally profit from. (too explain, why there is so many of them by examples: flash crashes may be with high volatility, "quantum" with no volume, synthetic by hacker attack - if e.g. hacker attack block on side of trading execution, stop loss/liquidation run,...). Or there are just good breaking tools to show bugs, I would like to use to break my own code and NT (sign function, harmonic data, negative prices - when these happened on electricity exchange in Czechia some time before, some trading systems broke combined with traders doing transactions without any sense). There is so many of them and many makes a sense, which makes this hard.

I must somehow identify, which of these to keep. I will cut down the options and opening events, since I have 0 experience with those. Also I will cut down majority of news events like new tariffs/taxes/..., since I can't review them at all, I have never investigated the market microstructure of market on these happening. All of those can be added later by somebody, who have some experience with it.

I will create a new module nautilus_trader/generators for it, first implementing it in Cython. I try to keep it simple, with few optional augmentations like adding white noise (there will be usually some trader subset, which together generate "high quality random numbers"), correlations between price changes and volumes, correlations between tick clustering and volume, and order splitting ticks.

---

#### [2025-08-04 20:14:23] @premysl_22228

A generator, which will always generate a new dataset. (if the parameters with seed will be the same, the outcome should be the same - I will unit test this) But basically, you put parameters like beginning price, scenario, correlations, noise,..., and get unique scenario each time if seed is not set.

---

#### [2025-08-04 20:16:14] @melonenmann

Sounds really great

---

#### [2025-08-14 07:46:30] @cjdsellers

⚠️ @everyone this last commit is quite a large breaking change as most indicator import paths will change (simplify), and **I also recommend devs do a `make clean` to clear out stale dynamic libs**: https://github.com/nautechsystems/nautilus_trader/commit/2ab02f28e956d948a47eb97016a6d8bdba543579

This change was necessary to get binary wheels consistently back below 100 MB for releases

**Links:**
- Consolidate indicators to reduce binary size and flatten imports ·...

---

#### [2025-08-16 08:30:20] @premysl_22228

Hi. I am currently thinking about making a fork before each backtest. It would solve a lot of problems, but data outside the cache would not be accessible after backtest is done. I was asked by Chris few months ago to make a prototype/experiment with it, but more I think about it, I am not sure whether get to prototyping that as it would might make more damage then improvement.

Reasons for autofork:
* Clean logging system every time (there are some issues with current logging, including the normal print doesn't work as it should between two runs of backtest)
* Memory leaks can be solved by a more relaxed approach
* Clean heap and cache every time, the performance degrade over long running applications
* We can be more courageous in the tainting of Python kernel, no more worries about the application running after or between is working
* The 0,5 GiB usage drops back to much lower number after backtest is run (this is a hypothesis, not tested)
* We will be one step closer for more advanced pathological tests like simulating venues freezes when under DDoS (the concept of these backtest wasn't yet published by me, but it makes it little bit more cleaned up - currently it is nice-to-have, but if more devs are available in the future, it might be a reality)

Disadvantages:
* No memory sharing outside the cache
* The cache have to be either serialized and piped to main thread (performance hit) or mmap with custom allocator must be used (this might be challenging)
* Many hacks used by users might stop working

Disadvantage by Chris (I don't agree, that we should care much):
* It is against standards, how should Python OSS library behave. (I didn't found the exact standard in our old chat, if you can fill the gap, it would be great, <@757548402689966131>)

I would like to hear more opinions about this as this would be a large breaking change for everybody.

---

#### [2025-08-19 02:09:57] @premysl_22228

I decided, I won't do the experiment for now, as there are no pro/contra arguments as I think the user should have ability to decide, whether he wants to fork. 

I will amend the logging bugs and the stashed rest, which would be solved by forking, to the backlog on the GitHub.

---

#### [2025-08-19 02:54:43] @premysl_22228

<@757548402689966131> Do you mind, if I put small personal bug backlog to NT without retesting it on newer version, if I am almost sure, that the bug wasn't solved in the meantime? I have stopped recording them long time ago since I stopped testing trading with NT entirely and focused on dev, where it can be usually fixed on the run.

I will try to report some of the aggregation bugs too. Do you want somewhere to upload the current changes - they are not properly tested, and faysou showed, that get_start_function can be written in a way, so there is no need for correctness proof, but should fix some of the bugs if I am not wrong (must revise notes to see, what was ought to fix, hopefully I have some record of them - it started with validations discussions, which blocked the now wanted feature, and ended with wider refactor as I read from May-17 notes), but since badly locked deep now in it and don't have much time now (and wouldn't have probably in following months),** I offer to upload it to some branch as the solution** of some bugs I will hopefully report (if in notes). 

The reported bugs should be reminder to anyone to either fix them, or to finish my unfinished work to anyone. And allow to anyone in the community to work on my personal bug backlog as I will be probably too busy to solve them.

---

#### [2025-08-19 03:38:16] @premysl_22228

<@757548402689966131> , going through notes, I have some disputed issues already on GitHub. Would you mind, if I reopen them with a reason, if I dig to a one. (e.g. a one was closed with requirement for rewrite from Jupyter notebook to shell file), I rewrote it, and it got never opened again.

---

#### [2025-08-19 08:00:18] @cjdsellers

Hi <@1353826739851362345> 
I'd anticipate the discussion on those issues stopped because there was either a lack of alignment, or a low priority - I understand you're making a record of the current status of things. How about you comment on those you feel the need to and I will circle around to it when I can?

---

#### [2025-08-19 08:50:21] @premysl_22228

Majority is low priority. (In compared to what should be done and what bugs are being reported - the one I am working on is maybe fatal bug and as I am not so much experienced with this part of NT, it might be better if you took things on the bug from me after identifying possible multiple causes, if things shouldn't take too long, but it is up to you) But I would like to keep them open (even with e.g. low-priority-bug instead of bug label) as they shouldn't be forgotten. There should be some remainders of what will be needed to done, e.g, destruction of logger after backtest is done (or other, but more complicated solution). I will try later today or tommorow put down some list. (Your timezone in day, 2 days).

---

#### [2025-08-19 10:58:38] @premysl_22228

<@757548402689966131>, <@965894631017578537> Ad the GitHub issue (I am on my phone without proper access to GitHub account), please wait at least 2 days with the merge. I am trying to refresh memory, why I made that change (I usually have tons of reasons, before doing such thing, and I am not sure now, how many I had for this change) and not-None might be required for fixing the bug with request not returning proper data out of internal aggregation. I must browse my code for detail probably. As faysou says there are tons of edge cases with request data, and this was probably one of them, which was not properly handled. (Btw, In my implementation, there is complete refactor of some functions to get rid some of edge cases.) I try to get to it soon.

---

#### [2025-08-19 12:04:25] @premysl_22228

<@965894631017578537> u Why do you need it reverted to know the urgency? <@757548402689966131> Why have you changed the opinion after we throughout discussed this, if I correctly remember, together? I am missing reason why let me implement that, merge it and then revert that out of nowhere?

---

#### [2025-08-19 12:19:18] @cjdsellers

Premysl, the PR is partly completing the implementation of making start required for most requests by removing the default None on Actor.

We can continue the discussion on the relevant PR

---

#### [2025-08-20 17:08:45] @premysl_22228

Hi, I am sorry, but I have a bad headache and I am not able deliver promised today. Will deliver as soon as possible (the list of potential bugs and the discussion about the issue).

---

#### [2025-08-24 09:47:06] @cjdsellers

⚠️ **Breaking change heads up**
As part of ongoing work to reduce binary wheel size, the `backtest.exchange` and `backtest.matching_engine` modules have been consolidated into `backtest.engine` on `develop` branch. This saves ~5 MB and brings us closer to the next release.

Most users should see no impact on import paths. Developers may, and anyone working from source will need to run `make clean` or manually remove stale libs to avoid issues.

Thanks for your patience with these changes and with the delay since the last release!

---

#### [2025-09-06 08:50:24] @3sberzerk

Hello, between yesterday and today the logs are no longer visible, I installed `nautilus-trader==1.220.0a20250905` specifically
Was this an intended change or a small bug?

Edit: 
The issue is only in 1.220.0a20250905, while 1.220.0a20250904 works fine

---

#### [2025-09-06 09:04:23] @cjdsellers

Hi <@312252646314737666> 
Thanks for reporting. Yes, we were working on a logging feature and a single commit slipped out which caused logs to not be flushed properly.
Fixed from [this commit](https://github.com/nautechsystems/nautilus_trader/commit/9ebc1ea2b4f93bc66a8a2f01562a7dccbce215b6) and I currently see normal logs with and without `use_pyo3=True`

---

#### [2025-09-06 09:06:09] @cjdsellers

If you're working from source then you might need to recompile

---

#### [2025-09-06 09:11:55] @3sberzerk

Thanks <@757548402689966131>  for the reply, working using the mentioned flag

---

#### [2025-09-07 08:04:32] @3sberzerk

Hello, I noticed that this function is raising an exception within the exception message:
https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/data/engine.pyx#L2451

This happens in both the stable and nightly builds.
I tried using the VOLUME_IMBALANCE BarType, but it looks like it’s not supported. The error I received was:

AttributeError: 'nautilus_trader.model.data.BarSpecification' object has no attribute 'aggregation_string_c' instead of the intended RuntimeError

From the code, it seems that this type of bar isn’t available in the open-source release. Could you clarify if this is actually part of a closed-source version (and if so, what does it take to get access to it), or if it’s planned to be added in the future?

---

#### [2025-09-07 09:27:04] @cjdsellers

Hi <@312252646314737666> 
The `VOLUME_IMBALANCE` is one of the aggregation methods not yet implemented - there's an open issue here: https://github.com/nautechsystems/nautilus_trader/issues/2603
I've added to my list to make this error clearer

**Links:**
- Implement remaining bar aggregation methods · Issue #2603 · naute...

---

#### [2025-09-07 10:36:52] @mk27mk

Hey <@757548402689966131> , I noticed that if you subscribe to bars inside an `Actor` and a `BarType` does not have any matching data on the `ParquetDataCatalog` NT does not give you any warning.

Could adding a warning/error at `BacktestDataConfig` level be a good idea?

---

#### [2025-09-19 14:54:03] @gabj_94927

hey, trying to get historic OHLCV crypto data via binance + live data. Any recommendations on the approach via nautilus for example where to store etc, i want to then run my own classification engine and compute signals (engine already built in python but not in NT)

---

#### [2025-09-23 14:51:52] @bemdacz

Hi guys <@757548402689966131> 
According to the documentation, NT can set Strategy OMS = HEDGING and Venue OMS = NETTING (https://nautilustrader.io/docs/latest/concepts/execution#oms-configuration
).

In backtests, the OMS for the venue is set like this:

venue_config = BacktestVenueConfig(
    name="BINANCE",
    oms_type="NETTING",
    ...
)


But how do you do this for live trading? I haven’t found any option to set the OMS for live for Venue.
I’m specifically interested in Binance Futures (my account on the exchange is set to one-way).

Thanks.
David

**Links:**
- NautilusTrader Documentation

---

#### [2025-10-20 17:55:48] @faysou.

I think that in live it's the broker who is responsible for this, it depends on your live account

---
