# NautilusTrader - #feedback

**Period:** Last 90 days
**Messages:** 33
**Last updated:** 2026-01-07 01:29:39

---

#### [2025-10-11 19:35:31] @_minhyo

docs/tutorials/     Jupyter notebook tutorials demonstrating common workflows.
docs/concepts/     Concept guides with concise code snippets illustrating key features.


both links are dead

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/926698977678737418/1426654467264217118/image.png?ex=695eb582&is=695d6402&hm=22fa9967fef1424f77d8ff11813659647d5d9d2fd23e60cb1829c554184ef77f&)

---

#### [2025-10-11 19:36:38] @_minhyo

seems to be a github issue

---

#### [2025-10-11 19:36:45] @_minhyo

i see its working on the mainsite

---

#### [2025-10-24 02:59:52] @jst0478

FYI I think the doc here for listing versions has a small typo:
https://nautilustrader.io/docs/latest/getting_started/installation#available-versions

There's an extra parenthesis that renders the whole command useless

**Attachments:**
- [Screenshot_20251024_115047.png](https://cdn.discordapp.com/attachments/926698977678737418/1431114946833289336/Screenshot_20251024_115047.png?ex=695e74e8&is=695d2368&hm=1d5eaa6b08dafb8a13a439e0b3624fcf6393bc6e60ea5189f83ce2f22c9d30d3&)

---

#### [2025-10-25 04:02:33] @cjdsellers

Thanks for pointing this out <@296261099630755841> now fixed
https://github.com/nautechsystems/nautilus_trader/commit/658152668d386ce069789a3887223f51880ba11c

**Links:**
- Fix typo in installation docs grep command · nautechsystems/nautil...

---

#### [2025-10-27 10:39:30] @trueorfalse

it seems we have a problem with new package or I'm doing something wrong.... 
```
warning: The package `nautilus-trader==1.221.0` does not have an extra named `visualization`
```

---

#### [2025-10-27 10:52:00] @cjdsellers

Hi <@208806459214004225> 
The `visualization` extra only landed on `develop` so far (development wheels). I'll update the announcement to be clearer about that

---

#### [2025-10-27 10:53:17] @trueorfalse

thank you very much for the information.

---

#### [2025-10-28 20:32:39] @1e4

I think there is a problem with the type declarations, they don't seem to work by default, for example `TestInstrumentProvider.btcusdt_perp_binance()` shows type `Unknown` in VS Code, and I need to import `CryptoPerpetual` from `nautilus_trader.core.nautilus_pyo3` (which is a `.pyi` file) for the type declarations to work:

```python
from typing import TYPE_CHECKING

from nautilus_trader.test_kit.providers import TestInstrumentProvider

if TYPE_CHECKING:
    # from nautilus_trader.model.instruments import CryptoPerpetual
    from nautilus_trader.core.nautilus_pyo3 import CryptoPerpetual

def main() -> None:
    inst: CryptoPerpetual = TestInstrumentProvider.btcusdt_perp_binance()
    print(inst)

if __name__ == "__main__":
    main()
```

---

#### [2025-10-28 20:33:43] @1e4



**Attachments:**
- [2025-10-28_223328.png](https://cdn.discordapp.com/attachments/926698977678737418/1432829707828859174/2025-10-28_223328.png?ex=695ec327&is=695d71a7&hm=41b452c083f995673da613adfdbb5d3f2e4a84c3d7738b9b53c8bb9aa689c086&)

---

#### [2025-10-31 23:57:53] @javdu10

Hello there! as a non native english speaker -> book.get_quantity_for_price is very confusing :

Currently: "Return the total quantity for the given price"

Something like the following makes the intent clearer IMO : 

"Return the cumulative quantity for the given price"

I was expecting O(1) access to the size from the price this way

---

#### [2025-11-07 16:54:40] @younggilga

Great experience so far tying in databento! Would love to see a projectx integration. Fingers crossed that's in the pipeline.

---

#### [2025-11-08 01:06:13] @cjdsellers

Hi <@798633203677003818> thanks for the feedback! there is another traditional finance integration coming very soon

---

#### [2025-11-08 01:07:21] @cjdsellers

Hey <@300644159566381060> some of these book analytics methods might be useful for you https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/model/book.pyx#L551

**Links:**
- nautilus_trader/nautilus_trader/model/book.pyx at develop · nautec...

---

#### [2025-11-10 08:38:24] @helo._.

There are many bugs with rounding floating points.
This happens because floating point 1.035 is actually 1.0349999999, so simply raising digits then rounding it gives wrong results.
(as in function f64_to_fixed_i64()) 
Examples:
`Price(1.005, 2):1.00
Price(1.015, 2):1.01
Price(1.035, 2):1.03
Price(1.055, 2):1.06
Price(1.075, 2):1.08
Price(1.095, 2):1.10`
You could consider only accepting Decimal from Price(). Or only use customized round function that converts to decimal before rounding.

---

#### [2025-11-10 09:03:01] @cjdsellers

Hey <@356336934626525186> this is a fairly extensive topic, I agree that floats can be problematic. That constructor is just taking a float and rounding to a precision. There are also dedicated methods in Rust such as `from_decimal` which could have an equivalent implementing in Python (an issue raised on this recently here: https://github.com/nautechsystems/nautilus_trader/issues/3143)
If you need to guarantee more accuracy without rounding errors then `from_str` (or `from_raw`) is probably your best option, but you do have to be careful how that is done as well, the classic:
```
>>> from decimal import Decimal
>>> str(Decimal(1.1))
'1.100000000000000088817841970012523233890533447265625'
```

---

#### [2025-11-10 09:30:37] @helo._.

I think being able to accept the decimal value is good, as in the Github issue.
Currently, Price(1.035, 2) also returns 1.03, due to lack of from_decimal(), so is converted to floating point(double).
from_str() is also dangerous, as you described.

---

#### [2025-11-10 09:31:55] @cjdsellers

Yes, `from_decimal` will be useful

---

#### [2025-11-11 03:08:23] @rk2774

Fractional share reporting going live in US in Feb of 2026. This most likely will impact us.

https://www.finra.org/filing-reporting/technical-notices/update-fractional-shares-reporting-20250328

**Links:**
- Update - Fractional Shares Reporting Effective Date Set for Februar...

---

#### [2025-11-19 15:06:40] @1e4

is there any way to get account equity over time for a backtest? it seems only realized pnl is available from `ReportProvider.generate_account_report`, unrealized pnl is not retrivable. I implemented my own equity computation (realized+unrealized), but it was somewhat involved, since to do that I needed position average price over time, which is another thing that NT doesn't seem to provide (only position open/close data points, but no position modified data points)
something which compute the green line, NT only provides the blue/orange line

**Attachments:**
- [2025-11-19_170606.png](https://cdn.discordapp.com/attachments/926698977678737418/1440719938963636365/2025-11-19_170606.png?ex=695e7680&is=695d2500&hm=954e4a88190badba3e5dfb5db4a44519601ed337af815551e6679ffbae1c61f3&)

---

#### [2025-11-20 01:33:09] @jst0478

Did you try the visualizations announced here? It looks like it has equity over time, but I guess it's only in the develop branch until the next release
https://discord.com/channels/924497682343550976/924498306372083713/1432275582707699722

---

#### [2025-11-20 01:33:34] @jst0478

If you need the raw data points then I don't know

---

#### [2025-11-20 02:36:49] @cjdsellers

Hi <@399282197552562193> 
Implementing equity is probably the next most important accounting feature to add. iirc, the `visualization` has some dedicated functionality for calculating this post hoc - otherwise, what you're doing there is the next best workaround. <@296261099630755841> thanks for helping with the explanation 🙏

---

#### [2025-11-20 07:25:26] @1e4

i did look at the new `visualization`, the name `equity` in the function name confused me, it looks to me that it is only tracking realized pnl. am I misunderstanding and returns somehow also contains unrealized pnl?
```python
def create_equity_curve(
    returns: pd.Series,
    output_path: str | None = None,
    title: str = "Equity Curve",
    benchmark_returns: pd.Series | None = None,
    benchmark_name: str = "Benchmark",
) -> go.Figure:
    # ...
    # Calculate cumulative returns (equity curve)
    equity = (1 + returns).cumprod()
```

---

#### [2025-11-25 21:27:29] @yegu88

Is there any sample code to make PnL reporting to output anything? I've been banging my head for days now. I somehow got a final unrealized PnL and no other stats.

---

#### [2025-11-25 21:30:01] @yegu88

Without reporting I'm not sure what's the value of backtesting. Zipline (Reload) provides full tear sheets but here I can't seem to get even the basics. To use the NT internal engineer, what simulated venue should i be using for trades that also drives PnL calculations?

---

#### [2025-12-01 15:02:27] @dun02

what do you mean by PNL reporting?  during the backtest in your strategy?  or after the backtest is done?

---

#### [2025-12-01 20:34:06] @yegu88

Daily equity curve. At the end of backtest run. I ended up writing my own since I could find a way for NT to produce it. My current strategy doesn’t run everyday so the NT internal doesn’t update the account balance

---

#### [2025-12-03 15:18:30] @javdu10

Hello <@757548402689966131> , just wanted to give you an update on my contribution for the synthetic instrument

i've refined the idea from the AI slop and will send an update tonight, this time I ran the complete integration test suite and no segfault 🫡

---

#### [2025-12-07 16:26:53] @akajbug

At work we use Kapa AI to help answer questions commonly asked or documented in internal/external docs, slack threads, and public/private repos - it’s been very helpful for us to farm out questions to AI bot before going to others. Also, we can chime in when Kapa is wrong to correct it overtime.

A suggestion I have for this discord as well is to adopt some Ask AI channel fine-tuned on your public docs, code, and discord. Could be a `#ask-ai` channel and hopefully prevent you guys from getting tagged as much.

<@757548402689966131>

---

#### [2025-12-09 19:07:31] @nebur_33181

what a pleasant surprise to find out that there is already a component (StreamingFeatherWriter) and some examples of how to record live data. It was the first thing I wanted to work on but this is much better than anything I could have come up with, thanks!!

---

#### [2025-12-09 21:08:29] @faysou.

with open source things get better over time as long as people use them, there were for examples existing things regarding streaming feather writer and catalog, and I've made them better, then some people report bugs sometimes and it makes the things even better, because over time there's no more bugs. also people can have requests for new features that improve things as well.

---

#### [2026-01-01 22:55:00] @deep_val_algo

Hey <@1434239765137326213> , are you talking about the bybit_options_data_collector.py file (doesnt seem to use StreamingFeatherWriter) ? or are there other examples?

---
