# NautilusTrader - #dydx

**Period:** Last 90 days
**Messages:** 24
**Last updated:** 2026-01-07 01:29:53

---

#### [2025-10-09 15:40:08] @.davidblom

I see a couple differences.

---

#### [2025-10-09 15:40:19] @.davidblom

Are they the same fill event?

---

#### [2025-10-09 16:11:07] @saruman9490

they're the same, at least I get only single even OrderFilled event in the logs

---

#### [2025-10-09 18:35:16] @senordongato1

What do you guys think of dydx as an exchange

---

#### [2025-10-10 03:16:21] @saruman9490

Sorry wrong screenshot, indeed these ones come from different client orders, but the ones I have match in everything execpt event_ts. I wonder if this is a caching thing?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426045665515016253/image.png?ex=695e78c5&is=695d2745&hm=1e2f26861a776a78e1870bca5cbdaa11490127ca0e7ad66a6186f49b2d796f7e&)

---

#### [2025-10-10 03:16:52] @saruman9490

For me its too early to tell conclusively but so far so good.

---

#### [2025-10-10 03:50:43] @saruman9490

Ok, I think I've figured it out but need help to figure out the fix this

I'm attaching the log of the position lifetime from the screenshot.

What I suspect happens is that since there is a single position on DYDX (ie. it nets) and if within an order I go from long to short it triggers both position close and position open ( of the same position ) and the order gets appended to the position twice - once on the close and once on the open. 

Ideas what's the proper way to fix this? I'm thinking of just having distinct position ids once they close

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/1277067872111300618/1426054314882760794/message.txt?ex=695e80d3&is=695d2f53&hm=8b40ad038e914ef3788303f9814ff05a6fdcf2dcb7f56bdd6a6a352e6f9a8d14&)

---

#### [2025-10-10 03:52:43] @saruman9490

Tho how to do it, I have no idea 😄

---

#### [2025-10-10 04:09:56] @saruman9490

Actually the issue is on the loading side, not the storing since I get this error

```
KeyError: "Duplicate TradeId('9525135d-8973-5337-b6fb-8c9d6e6a727c') in events OrderFilled(instrument_id=ETH-USD-PERP.DYDX, client_order_id=O-20251007-063005-003-026-5, venue_order_id=93d8c365-0a80-5e47-ba03-4cb48444c3d4, account_id=DYDX-dydx18l256stt4xe05p650y9euk5cmr7cjrez0gr9w2-1, trade_id=9525135d-8973-5337-b6fb-8c9d6e6a727c, position_id=ETH-USD-PERP.DYDX-ss.ta-hawk.15m-026, order_side=BUY, order_type=MARKET, last_qty=0.005, last_px=4_679.2 USDC, commission=0.00935850 USDC, liquidity_side=TAKER, ts_event=1759818605747000000) OrderFilled(instrument_id=ETH-USD-PERP.DYDX, client_order_id=O-20251007-063005-003-026-5, venue_order_id=93d8c365-0a80-5e47-ba03-4cb48444c3d4, account_id=DYDX-dydx18l256stt4xe05p650y9euk5cmr7cjrez0gr9w2-1, trade_id=9525135d-8973-5337-b6fb-8c9d6e6a727c, position_id=ETH-USD-PERP.DYDX-ss.ta-hawk.15m-026, order_side=BUY, order_type=MARKET, last_qty=0.005, last_px=4_679.2 USDC, commission=0.00935850 USDC, liquidity_side=TAKER, ts_event=1759818605747000000)"
```

So maybe I need to fix the loading side instead of the fixing. Comments & Suggestions welcome

---

#### [2025-10-10 04:53:28] @.davidblom

Not sure. Do you have an exception trace when the KeyErr is thrown?

---

#### [2025-10-10 12:31:20] @saruman9490



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426185331228545166/image.png?ex=695efad8&is=695da958&hm=fef60a555fabf37a1df3b5aa0f954be127a9b2cbee78d0e626ea81c71aecd954&)

---

#### [2025-10-10 12:31:32] @saruman9490



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426185382931730536/image.png?ex=695efae4&is=695da964&hm=256a82b9b38154d9848bc004940632a09d9fd6f54a88c8a5b7383d479d958f10&)

---

#### [2025-10-10 12:31:44] @saruman9490

Ok, I think the answer is to have a position per opening order I guess

---

#### [2025-10-10 12:31:59] @saruman9490

need to trace where that position_id is created tho

---

#### [2025-10-10 16:32:08] @.davidblom

Thanks. Could you create a ticket? That would be helpful

---

#### [2025-10-14 03:35:12] @saruman9490

thanks for the wait, its here - https://github.com/nautechsystems/nautilus_trader/issues/3081

**Links:**
- DYDX strategy fails to restart due error while loading the cache ·...

---

#### [2025-10-14 18:24:39] @.davidblom

Pull request is open. Does it fix your issue?

---

#### [2025-10-19 16:19:58] @saruman9490

Sorry still need to test, got myself into some major refactoring now unfortunately

---

#### [2025-10-19 16:20:02] @saruman9490

I'll keep you posted

---

#### [2026-01-03 20:57:00] @donaldcuckman

Timeline for v4 being workable?

---

#### [2026-01-03 20:58:54] @donaldcuckman

```[ERROR] DYDX-V4-MM-001.DataEngine: Unexpected exception in DataResponse queue processing: TypeError('Cannot convert nautilus_trader.core.nautilus_pyo3.model.Bar to nautilus_trader.core.data.Data')
TypeError(Cannot convert nautilus_trader.core.nautilus_pyo3.model.Bar to nautilus_trader.core.data.Data)
Traceback (most recent call last):
  File "E:\Sync\kalLIQ\.venv\Lib\site-packages\nautilus_trader\live\data_engine.py", line 460, in _run_res_queue
    self._handle_response(response)
  File "nautilus_trader/data/engine.pyx", line 2241, in nautilus_trader.data.engine.DataEngine._handle_response
  File "nautilus_trader/data/engine.pyx", line 2275, in nautilus_trader.data.engine.DataEngine._handle_response```

this is from running the example in github

---

#### [2026-01-04 13:24:46] @dxwil

Hey, currently the v4 adapter does not support funding rate updates. Is this feature planned or what's the status on it?

---

#### [2026-01-05 03:59:08] @cjdsellers

Hey <@177932166859063296> 
The dYdX v4 adapter is still in `building`status (so not considered usable yet). It will receive some attention over the next couple of weeks though and is getting closer

---

#### [2026-01-05 04:00:06] @cjdsellers

Hi <@574471770720043010> yes, since Nautilus supports funding rates and they are available from dYdX then eventually they will be implemented

---
