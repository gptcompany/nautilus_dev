# NautilusTrader - #announcements

**Period:** Last 90 days
**Messages:** 1
**Last updated:** 2026-01-07 01:29:22

---

#### [2025-10-27 07:51:49] @cjdsellers

📊 ** Backtest visualization with interactive Plotly tearsheets** 📊 

@everyone Introducing the initial backtest visualization capability with interactive Plotly tearsheets! (now available on `develop` branch for the latest development wheels).

This has been a long time coming and adds built-in support for local single-node backtesting workflows per the recent [ROADMAP](https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md#additional-enhancements) update - meaning users don't have to "reinvent the wheel".

Per the overview in the [docs](https://nautilustrader.io/docs/nightly/concepts/visualization), this adds:
- **Chart Registry** - Decoupled chart definitions that can be extended with custom visualizations.
- **Theme System** - Consistent styling with built-in and custom themes.
- **Configuration** - Declarative specification of what to render and how to display it (fluent API).

As I'm not actively backtesting at the moment, the idea is that we can iterate improvements to this basic framework based on actual needs and use cases - keeping it within the [open-source scope](https://github.com/nautechsystems/nautilus_trader/blob/develop/ROADMAP.md#open-source-scope) as a local Plotly based tool for now. I've also set up a dedicated channel for this purpose <#1432271716712714331> where changes/enhancement can be discussed, such as additional built-in charting options and layout changes/customizations.

A simple way to get started is to run [this example](https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/backtest/crypto_ema_cross_ethusdt_trade_ticks.py) and if `plotly` is installed then a HTML tearsheet will be automatically emitted at the end of the backtest run.

I hope this improves the backtesting experience with Nautilus and provides some value! 📈 

https://github.com/nautechsystems/nautilus_trader/commit/4233cc1d80faf5e9797d672bf4b6f04b1dc40be7

https://nautilustrader.io/docs/nightly/concepts/visualization

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/924498306372083713/1432275582904963102/image.png?ex=695eb955&is=695d67d5&hm=62919e04d448fcc835d45ba6e68c8a3c8f0faea54cb4b110668c45b6fe56e9ec&)

**Links:**
- nautilus_trader/examples/backtest/crypto_ema_cross_ethusdt_trade_ti...
- Add initial backtest visualization tearsheets · nautechsystems/nau...

---
