# NautilusTrader - #dev-rust

**Period:** Last 90 days
**Messages:** 84
**Last updated:** 2025-10-23 04:00:34

---

#### [2025-07-25 15:37:34] @premysl_22228

Hi, I am working on custom macro #[nttest], which will enable you (if I finish it successfully)
a) Memory trace all tests to detect memory leaks
b) To run it instead of #[tokio::test] with fixures enabled. (I won't rewrite all tests to use fixures, but it is now a possibility)
I am writing it here prematurely to know, whether there isn't some other functionality, which might be needed to be added now or later. Do you have any idea, what might be needed to be supported?

---

#### [2025-07-26 01:38:28] @cjdsellers

Hi <@1353826739851362345> 
This would be valuable, although I think we should limit such Rust tests to where we're using `unsafe` - otherwise we're probably just testing the language itself and there shouldn't be leaks by design. The Python mem leak testing you added was great 👌

---

#### [2025-07-26 16:13:41] @river7816

<@757548402689966131> Hi, can I use the ‘from nautilus_trader.core.nautilus_pyo3 import MessageBus’ messagebus from pyo3. I encounter No constructor defined for MessageBus

---

#### [2025-07-26 16:18:47] @river7816

Btw, does MessageBus support interprocess?

---

#### [2025-07-28 03:23:18] @cjdsellers

Hi <@1101117445508432033> 
The pyo3 message bus isn't meant to be constructed from Python and is only available for testing purposes, so no first-class support at this stage and it doesn't support IPC

---

#### [2025-07-28 03:24:01] @river7816

okay, got it

---

#### [2025-07-31 10:43:57] @faysou.

https://github.com/twitu/twitu/blob/main/fixing-frequent-full-rust-builds-with-cargo-fingerprints.md

**Links:**
- twitu/fixing-frequent-full-rust-builds-with-cargo-fingerprints.md a...

---

#### [2025-08-10 13:32:29] @yfclark

https://nico.engineer/blog/optimizing-rust-build

**Links:**
- Optimizing my Rust build from 238s to 25s | Nico's Blog

---

#### [2025-08-12 16:22:02] @dkimot

Is there a reason that the `persistence` crate includes the `serialization` crate with the `python` feature? This prevents Rust only builds, something the documentation talks about being possible.

---

#### [2025-08-13 07:30:50] @cjdsellers

Hi <@398553108482883584> 
Good catch, the `python` feature for `serialization` is only needed when it’s enabled from the `persistence` crate. I’ve removed it from the defaults, and that change will be in my next push

---

#### [2025-08-13 10:38:46] @dkimot

perfect, thank you! wasn’t sure if there was a specific reason/limitation

---

#### [2025-08-16 13:51:19] @shahisma3il

Hi all,
Quick question: does NT only provide a rust crate **nautilus-trading** to do forex sessions in rust or can we do more processing in rust-lang (instead of python) to run trading algo code as user-devs?

---

#### [2025-08-16 17:28:42] @premysl_22228

Hi. Soon it will be possible. Now, the Rust based strategy isn't supported yet. Many of us are waiting for this feature to come out.

---

#### [2025-08-17 09:38:50] @premysl_22228

Hi. Why are we stopping using bug label on GitHub? I would like to label few issues on GitHub a bug, but I am not sure, whether there isn't some deeper thought, like label can be given after confirmed by some maintainer. <@757548402689966131> Is there any problem, if I use my permissions this way?

---

#### [2025-08-17 09:40:52] @cjdsellers

Hi <@1353826739851362345> 
There has been no change to bug labeling, you can go ahead if you have a bug report

---

#### [2025-08-17 09:42:35] @premysl_22228

Ok, thanks. I would like to mark the https://github.com/nautechsystems/nautilus_trader/issues/2856 as a bug, not my own. For some reason, reported bugs are not no longer automatically assigned bug label.

**Links:**
- Discrepancy in PnL calculation · Issue #2856 · nautechsystems/nau...

---

#### [2025-08-17 09:45:53] @cjdsellers

Yes, go ahead - I think it should be marked as a bug. There has been no change to the issue template though

---

#### [2025-08-19 23:37:42] @premysl_22228

<@700524865265991682>, I am opening a new thread (the topic is your onboarding and implementing the new aggregators, the rest can still be DMed) as I will be taking some time off and don't want you to let you without the support, you will probably need. This way, anyone from the community can pick the questions you might have, even if I am offline for longer period of time.

---

#### [2025-08-19 23:41:28] @kylemac1919

Thanks <@1353826739851362345>  for the introduction. Hi everyone,  I’m looking forward to contributing to the NT community. Right now I’m slowly getting up to speed with Rust and working through some simple issues to fix as I build confidence. Excited to learn and help where I can!

---

#### [2025-08-19 23:42:33] @cjdsellers

Hi <@700524865265991682> welcome! sounds good

---

#### [2025-08-19 23:42:59] @kylemac1919

Happy to be here <@757548402689966131> ! 🦀

---

#### [2025-08-22 13:24:52] @deepeshkalura

hi, there i wanted my name is Deepesh Kalura i got a mail from Vadim, he give me reference this repo. I was looking for os contribution on rust projects. When i got mail  I kinda like  the project feel That why i am here  So nice to meet you all the maintainer and contributor. 

I like initial two issue which is little easy to resolve as it will increase the familiarity for this project. ( guidance in this will bhe really appreciated ) 
Thanks

---

#### [2025-09-01 05:56:38] @oriented_lin_41408

The examples for Binance in the documentation still use the Cython-implemented interfaces （https://nautilustrader.io/docs/latest/tutorials/backtest_binance_orderbook）. Running one day of OrderBookDelta data for BTC with the Imbalance strategy in the example takes over 2700 seconds. Is there a robust example that has already switched the entire pipeline from data to backtest to Rust implementation? Also, is this speed normal? After switching to Rust, what would be the approximate speed improvement?

---

#### [2025-09-02 01:27:02] @cjdsellers

Hi <@1410800354655862835> 
Thanks for reaching out. No, end-to-end backtesting in pure Rust is not yet possible - we're working on it. The pyo3 interface is not so efficient going from Python -> Rust with book deltas, we've seen a 4x slow down in fact over the Cython interface there. This won't be necessary when backtesting is possible in Rust though (and I'd *expect* a ~2-3x improvement). Performance figures there remain to be measured. I hope that helps!

---

#### [2025-09-02 16:36:35] @flypig5185

Hi! I am trying to use this example: `nautilus_trader/example/backtest/crypto_ema_cross_ethusdt_trade_ticks.py.` Unlike the example reads csv file, I am using my own data reader. To be compatible with my own raw data format and for fast data reading, I created my own Rust package and exposed pyo3 functions to Python for data reading. The function's output format uses <class 'nautilus_trader.core.nautilus_pyo3.model.TradeTick'>. 

Everything works fine until I try to use `TradeTick.from_pyo3_list(pyo3_ticks) `to convert from my custom function output to the format supported by the backtesting engine, when the program encounters a SIGSEGV issue. I have been debugging for a long time but still have no clue - it might be a runtime issue causing conflicts. 

Question: If I want to use my own Rust package to process some data (still using nautilus's data definitions and formats in Rust) and integrate with nautilus's backtest examples, what would be the best practice? Is there a timeline for implementing the backtest engine in Rust, since I find that going from rust->cpython->python makes it very difficult to identify problems? Thx in advance.

---

#### [2025-09-03 06:37:05] @cjdsellers

Hi <@878118921750839346> 

`TradeTick.from_pyo3_list()` eventually calls [TradeTick.from_pyo3_c](https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/model/data.pyx#L4986). I added some additional checks today if you'd like to test: https://github.com/nautechsystems/nautilus_trader/commit/0fee121a29de4aa8f22e132e7ecec87c6123ff20. This was just eliminating a couple of the segfault potentials though. Given you're interfacing your own custom code with Cython/PyO3 conversion, it's difficult for me to know what might be going wrong there.

There is no concrete timeline for backtesting in pure Rust, it's worked on as a priority as bandwidth allows. I agree this would be much smoother for you though - I hope that helps!

---

#### [2025-09-09 20:23:50] @bemdacz

Hi guys,
when I start a backtest I get a Rust error after a while.

thread '<unnamed>' panicked at crates\model\src\types\quantity.rs:196:10:
Condition failed: raw outside valid range, was 18446744073702551616


Although it looks like a bad quantity, this happens at a point where I’m not setting any quantity myself—I’m only receiving order updates from the “exchange.” I printed more info using RUST_BACKTRACE=full (see attachment), but I’m still none the wiser.

Could someone please advise on the best way to track this down? Python itself isn’t reporting any error.

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/990065045763391498/1415070216794411069/message.txt?ex=68fa8ed6&is=68f93d56&hm=54ba3b838fdaf19717e03b86440f052ffc4de913470444279ab7ec14fd173f4a&)

---

#### [2025-09-09 22:03:42] @cjdsellers

Hi <@1222958369808060538> 

Thanks for the report. Which version are you on?

---

#### [2025-09-10 06:26:14] @bemdacz

Hi, i am on the latest, 1.129.0

---

#### [2025-09-10 21:09:31] @cjdsellers

Thanks, let me know if the issue persists with the just released 1.220.0 version

---

#### [2025-09-11 09:04:13] @bemdacz

Wow, you really fixed it! Thank you! I spent so much time trying without success, so I’m really happy!

---

#### [2025-09-12 13:41:57] @kylemac1919

Hey guys.. quick question ... the Rust programming book and Rustlings.. im noticing that rustlings might be out of order, asking for chapter 5 to be vec exercises, but we havent done vecs yet and then 6 being move semantics but i dont explicitly remmeber move semnatics, only borrowing and ownership... do i just move on to rustlings 7 on structs?

---

#### [2025-09-13 02:08:43] @cjdsellers

Hey <@700524865265991682> 
It’s ok to jump around when learning a language. I’d also recommend having a go at making something small and useful for yourself, such as a CLI. That’s when learning will be the fastest and most engaging. Full disclaimer that Nautilus is not an easy codebase to approach with effectively 3 different languages and FFI, so don’t feel like you’re lacking anything if it’s hard to get going on something here. The project is at somewhat of a complexity peak

---

#### [2025-09-13 12:53:17] @kylemac1919

Thanks <@757548402689966131>, Yeah I've seen some of the complexities and thats when i starting diving deeper into the fundamentals thinking it could increase my ability to start contributing. I think what ill do is start build basic projects, finishing rustlings, continuing with my fundamentals and hopefully soon I can come around to start finding meaningful way to contribute to NT soon.

---

#### [2025-09-14 06:17:39] @braindr0p

Getting this error / crash :

`2024-11-12T18:58:03.071616963Z [INFO] BACKTESTER-001.DebugStrategy: <--[EVT] PositionChanged(instrument_id=ROL.XNYS, position_id=ROL.XNYS-DebugStrategy-000, account_id=XNYS-001, opening_order_id=O-20241112-183600-001-000-4, closing_order_id=None, entry=BUY, side=LONG, signed_qty=20.0, quantity=20, peak_qty=79, currency=USD, avg_px_open=50.99, avg_px_close=51.12, realized_return=0.00255, realized_pnl=7.67 USD, unrealized_pnl=2.60 USD, ts_opened=1731436560095483813, ts_last=1731437883071616963, ts_closed=0, duration_ns=0)

thread '<unnamed>' panicked at crates/model/src/types/quantity.rs:193:10:
Condition failed: raw outside valid range, was 340282366920938463462984607431768211456

Stack backtrace:
   0: <unknown>
stack backtrace:
   0:     0x70fdce93c262 - <std::sys::backtrace::BacktraceLock::print::DisplayBacktrace as core::fmt::Display>::fmt::hf435e8e9347709a8
   1:     0x70fdce98aa03 - core::fmt::write::h0a51fad3804c5e7c
   2:     0x70fdce930823 - <unknown>
   3:     0x70fdce93c0b2 - <unknown>
   4:     0x70fdce93fc8c - <unknown>
   5:     0x70fdce93fa8f - std::panicking::default_hook::h820c77ba0601d6bb
   6:     0x70fdce940692 - std::panicking::rust_panic_with_hook::h8b29cbe181d50030
   7:     0x70fdce94044a - <unknown>
   8:     0x70fdce93c769 - std::sys::backtrace::rust_end_short_backtrace::hd7b0c344383b0b61
   9:     0x70fdce9400dd - rustc[5224e6b81cd82a8f]::rust_begin_unwind
  10:     0x70fdce436890 - core::panicking::panic_fmt::hc49fc28484033487
  11:     0x70fdce436dd6 - core::result::unwrap_failed::h9e4c136384b1cfa3
  12:     0x70fdce59c57d - nautilus_model::types::quantity::Quantity::from_raw::hf833579856f184ba
  13:     0x70fdce5a615a - quantity_from_raw
Aborted (core dumped)`

---

#### [2025-09-14 06:18:08] @braindr0p

This is the code to generate the order:
`        expire_gtd: pd.Timestamp = self.clock.utc_now() + pd.Timedelta(hours=1)
        profitorder: LimitOrder = self.order_factory.limit(
            instrument_id=instrument_id,
            order_side=OrderSide.SELL,
            quantity=Quantity.from_int(80),
            price=Price(target_price, 2),
            time_in_force=TimeInForce.GTD,  # <-- optional (default GTC)
            expire_time=expire_gtd,  # <-- optional (default None)
            post_only=False,  # <-- optional (default False)
            reduce_only=True,  # <-- optional (default False)
            display_qty=None,  # <-- optional (default None which indicates full display)
            tags=['Profit'],  # <-- optional (default None)
        )`

---

#### [2025-09-14 06:18:25] @braindr0p

The error does not occur if I change the quantity to 79.  Notice the peak_qty value in the PositionChanged log event.  Also,  this only occurs if the quantity is more than the peak_qty AND reduce_only=True.

---

#### [2025-09-14 06:46:29] @braindr0p

I should also mention, this is on the latest release version. 1.220.0

---

#### [2025-09-15 00:30:54] @cjdsellers

Hi <@84040758922842112> 
Thanks for the detailed report, looking into it

---

#### [2025-09-15 01:50:18] @cjdsellers

<@84040758922842112> this should be fixed now https://github.com/nautechsystems/nautilus_trader/commit/1ae5684d7c6dad4e2a35e8f8e0501854eb79e0c5
please let me know if you experience further issues

**Links:**
- Fix reduce-only order panic when quantity exceeds position · naute...

---

#### [2025-09-19 16:39:07] @agedvagabond

Are you guys running any of the rust api actors  in release yet? If i build a new api in rust will I have any engine problems testing it?

---

#### [2025-09-19 17:34:02] @agedvagabond

Is it ok to use, self:Arc<Self> in my api crate. I seen mentioned in docs not to use Arc, I am wondering if it applies to API instance

---

#### [2025-09-19 18:00:39] @agedvagabond

so far ive just slapped in a copy paste of a working api client, I had to comment out anything that was using standardized types from my engine, ill just work through and replace to nautilus types. 
I am working on rithmic for nautilus now. I started building a new engine and got made my rithmic api flawless. But I think it'll be better to join a project like nautilus, so much is already done
https://github.com/BurnOutTrader/nautilus_trader/tree/develop/crates/adapters/rithmic/src

so far ive just copy pasted it in and commented out all the standardized conversion functions dependent on my engine, ill go through and convert them to nautilus standard types

**Links:**
- nautilus_trader/crates/adapters/rithmic/src at develop · BurnOutTr...

---

#### [2025-09-20 08:58:06] @mlewis11.

<@686727819262427308> This is huge! 

I’m very, very interested in a Rithmic adapter for Nautilus!! ✨✨✨✨✨✨✨✨✨✨

---

#### [2025-09-21 02:38:00] @agedvagabond

It won't be very hard, because ive had a working api for over a year. The only problem is I cant find any examples of how to integrate with the engine. I know in some places ill probably need to create wrappers for python, but on the rust side I am not sure how the engine is calling things like 'subscribe' etc. I was hoping it would be obvious when I looked at the other rust apis but I cant really find what I am looking for.
Once I have a list of those things I could knock out the whole api in a couple of days, excluding building tests. Its really just a matter of copy pasting old work and changing the engine specific types and event que

---

#### [2025-09-21 15:28:16] @gz00000

These two links might be of some reference value:
https://github.com/nautechsystems/nautilus_trader/tree/develop/crates/adapters/okx
https://nautilustrader.io/docs/latest/developer_guide/adapters

**Links:**
- nautilus_trader/crates/adapters/okx at develop · nautechsystems/na...
- NautilusTrader Documentation

---

#### [2025-09-21 17:32:41] @agedvagabond

Thanks mate, I will take a look tomorrow.

---

#### [2025-09-29 06:10:37] @agedvagabond

does anyone else use rust rover?

When i am developing api in nautilus repo, i get this weird situation where i have errors telling me "Method `xx` not found in the current scope for type `xx` [E0599]" 

But everything compiles fine and everything is found. I never had this problem on any other repo, could be an IDE issue since I updated at the same time as starting this project

**Attachments:**
- [Screenshot_2025-09-29_at_9.08.35_am.png](https://cdn.discordapp.com/attachments/990065045763391498/1422103257156681748/Screenshot_2025-09-29_at_9.08.35_am.png?ex=68fa6f9d&is=68f91e1d&hm=93ce8e9b5d65caf8cf5e05f86e3c90b4bc16df0da45fb6f9744d604ebde89992&)

---

#### [2025-09-29 06:11:31] @agedvagabond

i am going to focus on projectX rather than rithmic, it is an easier api for my first integration. I will do rithmic after i have my head around the engine.

---

#### [2025-09-29 09:18:42] @mlewis11.

totally understandable. I'm just glad to see more non-crypto adapters coming to the platform, I think that could dramatically increase the adoption of Nautilus. IBKR is good for options, but not the fastest for futures so not really benefiting from Nautilus' speed as much as it could.

---

#### [2025-09-29 09:44:32] @agedvagabond

ProjectX api won't be great for speed compared to rithmic. They do offer some amount of free hisorical data , plus they have 10 level orderbooks. I thought this would be perfect for me, since its a tiny api. This will be my first time contributing to a project so I am just trying to learn the ropes. Thowing python into the mix makes things interesting 😅

---

#### [2025-09-29 09:44:54] @faysou.

I think that there will be adapters for most brokers at some point, things will be easier to understand as well when most of the code will be in rust than in rust, cython and python currently. Also the more code for adapters exist the easier it is to do by analogy, especially with LLM agents.

---

#### [2025-09-29 09:45:35] @agedvagabond

I am curious why they havent used dynamics and traits for apis.

---

#### [2025-09-29 09:45:46] @faysou.

definitly use LLM agents to help you, augment code is great

---

#### [2025-09-29 09:46:23] @agedvagabond

I have GPT5 plus jetbrains Ai ultimate, which is basically autogpt in my ide

---

#### [2025-09-29 09:46:39] @faysou.

just go with the flow at the beginning, you can't just arrive and start making fundamental changes. if you become a regular contributor you could at some point.

---

#### [2025-09-29 09:50:36] @agedvagabond

Haha yeah. I wouldn't know where to start. My focus is futures trading so once I have a single api where I can use 'prop firms' i will be happy. I just feel like the time has come for me to learn how professional projects work, rather than continuing to spam my own code base without a sense of direction or fixed architecture

---

#### [2025-09-29 09:51:36] @faysou.

I actually wanted to do something similar to nautilus for myself before finding its existence, but it's actually much easier to contribute to nautilus than to start from scratch

---

#### [2025-09-29 09:53:21] @faysou.

I thought rust with pyo3 bindings would be ideal and that's where the library is being migrated to. Currently it's a mix of rust, cython and python. Still the architecture of the library will mostly be the same in rust so it's worth it to understand the library in cython.

---

#### [2025-09-29 09:53:37] @agedvagabond

Yes definitely, I was using quantconnect but their focus is on portfolio management rather than intraday and I only trade intraday. I avoided python, but after making 2 rust engines I understand the appeal of it, being able to hotload strategies, plus all the Ai libraries. I thinks its a worthy trade off.

---

#### [2025-09-29 09:55:01] @agedvagabond

Plus Jupyter is legendary

---

#### [2025-09-29 09:56:27] @agedvagabond

There is an obvious shortcut with the futures apis, that is to only support brokerage and just use databento for data. But in the interests of learning ill do both on my first api

---

#### [2025-09-29 09:57:50] @faysou.

I think over time there will be more adapters, it depends on more people contributing them, the benefit of it is that other people can use it and find bugs, and maybe contribute too

---

#### [2025-09-29 12:41:51] @agedvagabond

it appears they have, i guess i wasnt deep enough in 🙂

---

#### [2025-10-08 00:47:05] @.epicism.

Hey I'm playing around with NautilusTrader and I'm trying to determine if you can use Nautilus via just Rust. I'm struggling to find an example that shows how this was intended to be done

---

#### [2025-10-08 11:24:18] @cjdsellers

Hi <@381479142505316353> 
Welcome! The goal is pure Rust will be possible for backtesting and live trading (there will always be a Python API for this as well). Currently we’ve achieved pure Rust systems for live data and currently working on live execution. Backtesting is mostly done but requires more wiring up and work.

A good example of current capabilities is the Databento live node example, this might not be what you're after though https://github.com/nautechsystems/nautilus_trader/blob/develop/crates/adapters/databento/bin/node_test.rs

Better examples and tutorials for Rust will arrive when more is possible. I hope that helps!

**Links:**
- nautilus_trader/crates/adapters/databento/bin/node_test.rs at devel...

---

#### [2025-10-08 11:34:28] @.epicism.

Thank you, CJ!

---

#### [2025-10-08 12:36:10] @faysou.

Something to realise is that the rust and cython side will mostly have the same structure, so learning about the current structure of the library in cython is useful.

---

#### [2025-10-09 01:53:04] @.epicism.

Good to know, thank you

---

#### [2025-10-10 09:51:30] @veracious69_77345

Hi, I noticed the stubs generated for enums have different casing in python vs rust. For example AccountType has UpperCamelCase in rust vs SCREAMING_SNAKE_CASE in python, what is the convention here if I want to contribute with some of my code?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/990065045763391498/1426145109321318480/image.png?ex=68faa362&is=68f951e2&hm=423caf69997262278563fb72c67bbfee458487b0557a778018d2f4c8f07b53a3&)
- [image.png](https://cdn.discordapp.com/attachments/990065045763391498/1426145109732233377/image.png?ex=68faa362&is=68f951e2&hm=91e26f6250eeb37cd54bf0a672524fa7582b0711c1b55f3b657527a9c7b976aa&)

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
