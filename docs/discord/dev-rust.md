# NautilusTrader - #dev-rust

**Period:** Last 90 days
**Messages:** 63
**Last updated:** 2026-01-07 01:29:46

---

#### [2025-10-09 01:53:04] @.epicism.

Good to know, thank you

---

#### [2025-10-10 09:51:30] @veracious69_77345

Hi, I noticed the stubs generated for enums have different casing in python vs rust. For example AccountType has UpperCamelCase in rust vs SCREAMING_SNAKE_CASE in python, what is the convention here if I want to contribute with some of my code?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/990065045763391498/1426145109321318480/image.png?ex=695ed562&is=695d83e2&hm=34aaba5a0b74ec0077913aed79268ccef42571467330ecfa8015085b0711f672&)
- [image.png](https://cdn.discordapp.com/attachments/990065045763391498/1426145109732233377/image.png?ex=695ed562&is=695d83e2&hm=f44132519e15e1b5ffe766ac5c1eabe6bd860a83f1fd0582fe8bf4b7ac9c119e&)

---

#### [2025-10-10 22:49:07] @cjdsellers

Hi <@1186669514394452098> 
Thanks for seeking clarity here. This is a good explanation:

```
  The Pattern

  Rust side (crates/model/src/enums.rs:64-76):
  #[strum(serialize_all = "SCREAMING_SNAKE_CASE")]
  pub enum AccountType {
      Cash = 1,    // UpperCamelCase in Rust
      Margin = 2,
      Betting = 3,
  }

  Python side (runtime behavior):
  AccountType.CASH    # SCREAMING_SNAKE_CASE in Python
  AccountType.MARGIN
  AccountType.BETTING

  Why This Works

  1. Rust conventions: Enum variants are written in UpperCamelCase (Cash, Margin) - this is idiomatic Rust
  2. Strum attribute: The #[strum(serialize_all = "SCREAMING_SNAKE_CASE")] attribute automatically converts variants to Python's convention when exposed
  via PyO3
  3. Python conventions: Enum members are accessed as SCREAMING_SNAKE_CASE (CASH, MARGIN) - this is idiomatic Python

  Documentation

  This pattern is explicitly documented in docs/developer_guide/rust.md:188-199, showing the exact enum pattern with all required attributes including
  the strum serialization directive.

  Guidance for Contributors

  In Rust:
  - Define variants using UpperCamelCase: Cash, Margin ✅
  - Always include #[strum(serialize_all = "SCREAMING_SNAKE_CASE")] ✅
  - The conversion happens automatically

  In Python:
  - Access using SCREAMING_SNAKE_CASE: AccountType.CASH ✅
  - Stubs will reflect this convention ✅

  This ensures both languages follow their idiomatic conventions while maintaining seamless interoperability. The user feedback shows this is working as
  designed - contributors should follow the Rust naming conventions in Rust code, and the tooling handles the Python conversion automatically.

```

---

#### [2025-10-13 01:34:39] @jason__codes

How did you go with the Rithmic integration? I'm interested in using Nautilus with Rithmic API and am wondering if I need to develop it myself or something already exists?

---

#### [2025-10-13 07:49:40] @agedvagabond

I am doing my own engine, specific to my use case so I dont expect to continue. You could easily take the api client from me and make it compatible with nautilus. My rithmic api client didnt use the same pattern as nautilus. I was passing a 'self: Arc<Self>' where nautilus uses an inner and outer client.

Inner only uses the api types and is fully clonable by using Arc<Property>.
The outer just wraps the inner client and provides functions to request by parsing nautilus types and responses from the client.

If I was going to continue I would do it the way nautilus does it. Like I did with the projectX adapter. 

The other shortcut would be to use databento for data and only build a rithmic execution client.

The projectX adapter is in here (its not finished) 
github.com/BurnOutTrader/nautilus_trader

My latest rithmic api is in a private repo, I want to change the design pattern of it soon for my engine, the pattern will be compatible with nautilus, but the python support and outer layer would need to be added/modified.

I can let you know after ive changed it to the same design pattern as nautilus. Its something i will be doing soon.

---

#### [2025-10-13 20:07:04] @jason__codes

No worries, I'll start on a Rithmic adapter today.

---

#### [2025-10-13 20:35:18] @faysou.

https://github.com/pbeets/rithmic-rs

**Links:**
- GitHub - pbeets/rithmic-rs: Connect to RithmicAPI using Rust for Al...

---

#### [2025-10-13 20:35:44] @faysou.

there's a rithmic client here, not for nautilus, but it could help for developing one for nautilus

---

#### [2025-10-13 20:54:18] @jason__codes

yes this is very helpful. I don't see a reason to reinvent the wheel, so I will explore leveraging rithmic-rs as an external library for the adapter

---

#### [2025-10-13 20:55:22] @faysou.

at some point there will be a need to migrate the IB adapter to rust, there's a similar rust client for IB and I'll use it. maintaining a client is very difficult so if someone else does it, it's better

---

#### [2025-10-13 20:56:11] @faysou.

I think the one above doesn't have all functionalities for rithmic, but if you need new ones you could do a PR to the project above

---

#### [2025-10-13 20:57:20] @jason__codes

yeh he says Contributions encouraged and welcomed!

---

#### [2025-10-13 20:57:28] @jason__codes

so this is definitely the right approach

---

#### [2025-10-13 20:57:37] @faysou.

also if there's an already existing architecture it's much easier to evolve things, same for nautilus

---

#### [2025-10-13 20:58:57] @jason__codes

yeh for sure, pooling community resources makes a lot of sense

---

#### [2025-10-15 13:42:00] @mlewis11.

there's a lot of interest in this

---

#### [2025-10-28 19:22:26] @gravity6946

pls, could someone give some guidance on how to write strategies in rust ?

---

#### [2025-10-29 11:05:05] @mk1ngzz

you cannot do that yet

---

#### [2025-10-31 16:47:02] @faintent

hold on what? i thought the rust libraries let you do exactly that

---

#### [2025-10-31 22:12:48] @cjdsellers

Hey <@758705730059763742> to clarify: the core is mostly Rust at this point - it's just not possible to write trading strategies and run trading nodes in Rust yet (but it's close)

---

#### [2025-10-31 22:25:07] @faintent

so you have to use python? that would suck bc rust wrecks python performance wise

---

#### [2025-11-01 08:13:15] @pbeets

<@965894631017578537> hey I'm the creator of the rithmic-rs crate, and happy to help or answer any questions. I don't use NautilusTrader as I have my own setup, but open to contributing!

---

#### [2025-11-07 13:14:44] @nuvie1929

Hello ,  i was wondering if i could get in touch with you regarding rithmic R | Diamond API™  R Api implementation

---

#### [2025-11-08 17:55:29] @pbeets

Yes of course! But I have not used the diamond api

---

#### [2025-11-08 18:32:05] @mlewis11.

Hey Jason. Just curious if you made any progress on the Rithmic Adapter?

---

#### [2025-11-09 00:04:34] @traderdughetto

This Rithmic Adapter is a brillant idea! love it

---

#### [2025-11-09 11:12:36] @nuvie1929

I am considering it as it seems to have the fastest execution.  I have a setup in mind i would like to share with you . whats the best way to get it to you ?

---

#### [2025-11-09 15:52:16] @pbeets

Feel free to DM me! However, I do not believe Diamond API is through websockets, I think it might be a C++ lib.

---

#### [2025-11-11 06:53:45] @dem070699

Hi guys. I came through across Reddit thread and they say there's a Rust migration going on. Is that true? What's the status of that process?

---

#### [2025-11-11 10:09:35] @dem070699

Hi <@757548402689966131> any status on rust migration?

---

#### [2025-11-12 01:53:57] @cjdsellers

Hi <@1295686906012635189> yes there is a Rust port of the core underway (there will always be a public Python API). We'll make a more detailed Rust port update in the next release announcement, maybe a week or so away

---

#### [2025-11-17 23:59:19] @danielbak

Are there any recommended first-contribution issues?

---

#### [2025-11-18 20:53:45] @ratatata6559

Sigh... Wish I had come across this before I started my project. Just noticed add_strategy is not implemented in the rust code.
Does the python part not use the rust part? I thought it did. How does the python API have add_strategy implemented but not the rust part (This is confusing to me)?
Edit: I'm using BacktestEngine should  I be using Trader instead? It seems to implement add_strategy.

---

#### [2025-11-20 02:34:09] @cjdsellers

Hi <@430510337213726720> 
Welcome! the shorter answer is that the Rust port is ongoing, and there are essentially two versions of the system in play right now - v1, and v2 - both sharing the same Rust core. Running strategies in Rust hasn'tt been implemented yet, but is being actively worked on, so you're just a little early here. I hope that helps to clarify things!

---

#### [2025-11-23 02:41:18] @dem070699

Hi <@757548402689966131> I have a question. Once Rust migration is done, is it true that I can use NautilusTrader entirely in Rust?

---

#### [2025-11-23 02:41:53] @cjdsellers

Hi <@1295686906012635189> correct, that is the goal

---

#### [2025-11-23 02:58:45] @dem070699

Excellent. I know this has been asked several times, but do you have in your mind when it might be done? Just an estimation is okay. 
I recently just started buidling a trading engine for my own. But I guess it'd be better waiting Rust version released and work on top of that 🙂 So i really really want to know how long i should wait

---

#### [2025-11-23 20:52:33] @.alfredch

Hi team
My code was running prior to Commit 4fc460c in developer branch (few hours ago). Now there is a problem:
File "/home/alfred/Projekte/nautilus-trading-bot/nautilus_trader/nautilus_trader/core/__init__.py", line 29, in <module>
    from nautilus_trader.core.message import Command
  File "nautilus_trader/core/message.pyx", line 1, in init nautilus_trader.core.message
ImportError: /home/alfred/Projekte/nautilus-trading-bot/nautilus_trader/nautilus_trader/core/uuid.cpython-312-x86_64-linux-gnu.so: undefined symbol: PyObject_DelAttr
Any thoughts on this are welcome.

---

#### [2025-11-23 21:33:20] @cjdsellers

Hey <@1295686906012635189> 
Too much variance to give a concrete estimate, in month units though. If you find working on your own trading engine rewarding then I would encourage you to do that regardless, also for the learning experience. If your main goal is to be running algo trading with an all Rust stack and want to use Nautilus for that, then you probably won't be waiting too much longer now

---

#### [2025-11-23 21:42:18] @cjdsellers

Hi <@1050045223486619698> 
That file for the `uuid` extension module hasn't change in any material way, looks like it might be environmental such as compiling with one interpreter and then running with another. Double check the build from source steps in the README, especially all env vars

---

#### [2025-11-24 01:37:52] @dem070699

Thanks for the answer. Yes I just want to have my entire system running in Rust stack, basically backtest and live trade algo.
I think at the moment while waiting for Rust version, I'll get to understand the Rust NT codebase. May i ask what branch atm is the latest development for Rust migration?
Also compare the main version that uses cython and python, what still is missing from Rust version at the moment?

---

#### [2025-11-24 01:50:52] @dem070699

Also is there a docs that walks through each NT feature in Rust?

---

#### [2025-12-06 17:55:16] @__paladine__

Hi, I just started using Nautilus and in the process of posting my strategies. I noticed the Stochastics in Nautilus is somewhat different than the ones in cTrader/MT/TV in that it doesn't do ÷K smoothing and having ÷D smoothed via a moving average. This results in a more widely fluctuating K, while D is more or less similar. If I was to propose  a PR that could add support for the slowing/MA logic, would that be appropriate? That would mean some value changes in some cases though, unless we put a mode type config. If the current Stochastic is considered more standard than the one I am talking about, then this is ok and we dont need my pr

---

#### [2025-12-07 03:01:04] @cjdsellers

Hi <@794035895044800514> thanks for reaching out. Yes, we would welcome a PR to standardize this - at your discretion. I agree it would be correct to provide a config and retain existing behavior for now

---

#### [2025-12-07 03:53:56] @__paladine__

No problem, I will finish that and propose a PR

---

#### [2025-12-11 15:26:14] @__paladine__

Hi, I made the updates and proposed a PR in github. Tested against cTrader only as this is what I had before, and it works as the current Stochastic with the same arguments, but with the additional slowing and MA arguments gives identical results to cTrader. Please let me know if you would like any changes to it

---

#### [2025-12-11 19:16:19] @mk1ngzz

https://depot.dev/blog/sccache-in-github-actions

**Links:**
- Fast Rust Builds with sccache and GitHub Actions

---

#### [2025-12-11 21:23:57] @cjdsellers

https://releases.rs/docs/1.92.0/
https://doc.rust-lang.org/stable/cargo/guide/build-performance.html

**Links:**
- Rust Changelogs
- Optimizing Build Performance - The Cargo Book

---

#### [2025-12-17 21:50:16] @dariohett

<@757548402689966131> Polymarket just dropped a Rust-based client, posting link in 1s

---

#### [2025-12-17 21:51:01] @dariohett

https://github.com/Polymarket/rs-clob-client

**Links:**
- GitHub - Polymarket/rs-clob-client: Polymarket Rust CLOB Client

---

#### [2025-12-18 03:44:07] @optionalcoin

Came here to make sure they knew this as well

---

#### [2025-12-25 12:19:40] @javdu10

At the same time there is subscribe/unsubsribe for market available in the websockets

---

#### [2025-12-29 13:35:19] @afterblaze

Hey everyone, happy holidays!
I'd like to start contributing to Nautilus Trader again, are there any open issues that I can take up? Preferably something simple to start with, as the repo has changed quite a bit since I last saw it.

---

#### [2026-01-01 14:57:07] @mk1ngzz

https://github.com/binance/binance-connector-rust

**Links:**
- GitHub - binance/binance-connector-rust: Simple Rust connector to B...

---

#### [2026-01-01 16:34:20] @javdu10

Hello Hello, seeing the message above -  if anything, it could be translating some python adapters to rust? For example polymarket has an official rust package - and the current python adapter also use the official python version

---

#### [2026-01-01 16:35:51] @javdu10

Not very novel but could be something - or maybe some indicators and some rough edge around the data and parquet file, not all types are deserialized with rust yet - example IndexPriceUpdate still need a pyarrow translator

---

#### [2026-01-02 14:33:09] @traderdughetto

Hello,
Would you consider developing Rithmic adapter? 
This would enable users to backtest and live-trade through prop firms. 
Since QuantConnect has no plans to support these vendors, it could be a strong differentiator for Nautilus.
That said, I understand if the focus is on serious retail traders rather than the prop firm market.

happy new year!

---

#### [2026-01-02 16:38:05] @mk1ngzz

might be worth setting up https://cubic.dev or https://coderabbit.ai for automated pr reviews

**Links:**
- AI code reviews for complex codebases | cubic | Try free now
- AI Code Reviews | CodeRabbit | Try for Free

---

#### [2026-01-02 16:38:28] @mk1ngzz

free for open source

---

#### [2026-01-03 05:06:30] @exeutiy

lol code rabbit? DIdn't you see what their deaf CEO did recently on x

---

#### [2026-01-03 08:36:27] @mk1ngzz

I don't use X. What'd he do?

---

#### [2026-01-03 08:39:37] @exeutiy

massive crash out over recommendations from a user.

---

#### [2026-01-06 21:34:27] @javdu10

Hello there!

I’m not quite sure what to do with the request_id from a strategy after doing request_data

My custom adapter correctly receives the data then does « msgbus::send_response » with the request_id and the response but I see an error that no handler where found

Is there anything particular apart from the on_data on the Actor ?

---
