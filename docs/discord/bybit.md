# NautilusTrader - #bybit

**Period:** Last 90 days
**Messages:** 30
**Last updated:** 2025-10-23 04:00:37

---

#### [2025-07-26 02:19:47] @cjdsellers

Hi <@322841069366804491> 
Thanks for reaching out. It looks like parsing `CryptoOption` instruments still needs to be completed [here](https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/adapters/bybit/providers.py#L262). I'd imagine that would be very similar to the others and adding `strike`, option `kind` etc.

Then it would just be a matter of attempting to use option instruments and incrementally fixing the issues. I'm unsure exactly what might be required beyond the instrument provider

---

#### [2025-07-28 14:33:47] @baerenstein.

I just finished implementing the options support for Bybit and would be happy to push it onto the Nautilus repo. I also already created an issue where I would link my feature branch to. https://github.com/nautechsystems/nautilus_trader/issues/2818 Should I add someone specific as assignee? <@757548402689966131>

**Links:**
- Bybit Options Support missing · Issue #2818 · nautechsystems/naut...

---

#### [2025-07-28 20:15:00] @faysou.

You just need to create a PR. Ensure to run the pre commit checks before as explained is the nautilus developer guide.

---

#### [2025-07-29 02:01:23] @cjdsellers

Hi <@322841069366804491> 
Thanks for the help on this! I can sort out ticketing and assignee once you open the PR

---

#### [2025-08-02 03:37:29] @valeratrades

unless I'm missing something, this shouldn't be an error on `Inverse`, no?
```
Error during node operation: `free` amount was negative
```

---

#### [2025-08-04 02:59:30] @cjdsellers

Hi <@474661840735961089> 
I'm unsure of the inputs / path which lead to this, so hard to comment on the cause. It's still possible to end up with a negative balance with inverse contracts though. Are you on 1.219.0 or later?

---

#### [2025-08-04 12:00:47] @valeratrades

yes, I'm on 1.219.0

"ending up" is completely fine, but it erroring doesn't seem to make sense in the Inverse contracts case, unless I'm missing something?

---

#### [2025-08-04 12:41:04] @cjdsellers

Hi <@474661840735961089> 
I'm not following what you mean based on the information provided - what is the scenario which lead to the error?

---

#### [2025-08-04 13:17:37] @valeratrades

with UTA, if a perp position shows unrealized loss, the USDT amount here could go negative.

so new position can be easily opened against BTC on the account, but NT panics when it sees negative number for spot USDT

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1151424136283947028/1401916991190859888/image.png?ex=68fad3b1&is=68f98231&hm=e0d49bfcb3320010e7cb033266937f1db27d20d80aece74c2b845c4c96b440d1&)

---

#### [2025-08-18 09:49:14] @joker06326

2025-08-18T09:47:10.001809489Z [WARN] zsg-bybit-02.RiskEngine: SubmitOrder for O-20250818-094710-02-MMtick-17 DENIED: NOTIONAL_EXCEEDS_FREE_BALANCE: free=0.41243685 USDC, balance_impact=-11.50789000 USDC
2025-08-18T09:47:10.001991693Z [WARN] zsg-bybit-02.VolatilityMarketMaker: <--[EVT] OrderDenied(instrument_id=BTCUSDC-SPOT.BYBIT, client_order_id=O-20250818-094710-02-MMtick-17, reason='NOTIONAL_EXCEEDS_FREE_BALANCE: free=0.41243685 USDC, balance_impact=-11.50789000 USDC')

---

#### [2025-08-18 09:50:04] @joker06326

How can i close the balance check? Because i open "isLeverage=1", it will borrow coin automatically.

---

#### [2025-08-18 09:52:05] @cjdsellers

Hi <@1162973750787051560> 
The latest `develop` version allows borrowing by default for Bybit. Which version are you using?

---

#### [2025-08-18 10:06:52] @joker06326

The latest pip version, not develop branch.

---

#### [2025-08-18 11:16:34] @cjdsellers

Understood, we will release the next version soon after some issues are resolved

---

#### [2025-09-15 03:25:12] @joker06326

<@757548402689966131> Hi, I saw the isLeverage update in the latest version. But I don't know how to set this True in ```self.order_factory.limit```.

---

#### [2025-09-15 03:33:18] @cjdsellers

Hi <@1162973750787051560> 
You can use the `params` dict to pass `is_leverage: True`. There are some docs here: https://nautilustrader.io/docs/nightly/integrations/bybit#order-parameters

---

#### [2025-09-15 03:48:46] @joker06326



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1151424136283947028/1416994128398520400/image.png?ex=68faf71e&is=68f9a59e&hm=4ba5ac6a1fa738851b0d8cbdd209d20db82894409f0670b0afa7e8e85330e884&)

---

#### [2025-09-15 03:49:04] @joker06326



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1151424136283947028/1416994202985693256/image.png?ex=68faf730&is=68f9a5b0&hm=eb6ab2937f24ef36df1d5a10c5d81f3150677a00e5c91c029300f98e4bb7af60&)

---

#### [2025-09-15 03:49:40] @joker06326

<@757548402689966131> There is no "params" in function param.

---

#### [2025-09-15 04:13:10] @cjdsellers

<@1162973750787051560> it's in the docs. The `params` dict is for `submit_order`

---

#### [2025-09-15 04:48:13] @joker06326

```
2025-09-15T04:46:29.001409647Z [WARN] zsg-bybit-01.RiskEngine: SubmitOrder for O-20250915-044629-01-MMtick-2696 DENIED: CUM_NOTIONAL_EXCEEDS_FREE_BALANCE: free=0.00081761 BTC, cum_notional=0.02000000 BTC
2025-09-15T04:46:29.001592689Z [INFO] zsg-bybit-01.ExecClient-BYBIT: Submit LimitOrder(BUY 0.020000 BTCUSDT-SPOT.BYBIT LIMIT @ 116_125.7 GTD 2025-09-15T04:46:44.000Z, status=INITIALIZED, client_order_id=O-20250915-044629-01-MMtick-2695, venue_order_id=None, position_id=None, tags=['MM'])
2025-09-15T04:46:29.001655527Z [WARN] zsg-bybit-01.VolatilityMarketMaker: <--[EVT] OrderDenied(instrument_id=BTCUSDT-SPOT.BYBIT, client_order_id=O-20250915-044629-01-MMtick-2696, reason='CUM_NOTIONAL_EXCEEDS_FREE_BALANCE: free=0.00081761 BTC, cum_notional=0.02000000 BTC')
```
I have set is_leverage=True. But order was still denied when I tried selling BTC with margin.

---

#### [2025-09-15 09:39:19] @cjdsellers

Thanks for the feedback. This is an interesting case - the risk engine isn’t considering the leverage available. There’s not a quick solution here other than to bypass the risk engine or stay within those balance limits

---

#### [2025-09-15 10:04:43] @joker06326

How can I bypass the risk engine？

---

#### [2025-09-15 21:04:10] @cjdsellers

<@1162973750787051560> you can use the `RiskEngineConfig.bypass` to achieve this: https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/risk/config.py#L27

**Links:**
- nautilus_trader/nautilus_trader/risk/config.py at develop · nautec...

---

#### [2025-09-17 12:38:02] @.islero

Hi, is it ok I’m not getting open orders after application restart? But the positions syncs correctly. 

reconciliation=True,
reconciliation_lookback_mins=1440,
        open_check_interval_secs=5.0,
        open_check_open_only=True,

---

#### [2025-09-17 13:11:09] @.islero

It looks like the only option is to store the cache in Redis so that after a restart it can restore the entire state that existed before the restart, right?

---

#### [2025-09-18 04:19:22] @cjdsellers

Hi <@785499022567145523> 
Which version are you on? there is currently a large overhaul/upgrade to reconciliation on `develop` branch (install from development wheels) which might fix this for you

---

#### [2025-09-18 06:42:47] @.islero

I’m using v1.220

---

#### [2025-09-18 06:49:28] @.islero

Ok, thanks. I think I’ve resolved the issue by completely disabling reconciliation and saving the cache to Redis.

---

#### [2025-09-18 09:56:17] @cjdsellers

<@785499022567145523> Understood. I do believe reconciliation is working for both v1.220.0 and the unreleased v1.221.0 (v1.221.0 has much more robust reconciliation though)

---
