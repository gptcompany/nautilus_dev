# NautilusTrader - #dydx

**Period:** Last 90 days
**Messages:** 24
**Last updated:** 2025-12-22 18:02:04

---

#### [2025-09-23 18:17:03] @saruman9490

A race between what?

---

#### [2025-09-23 18:59:44] @.davidblom

Not sure. Maybe the message counter. But that results in a different error.

---

#### [2025-10-02 04:03:09] @saruman9490

Does anyone know how to use the subbacounts on dydx?

---

#### [2025-10-08 03:09:16] @saruman9490

Ok su apparently currently access to subaccounts is API-only, so if anyone needs help setting it up let me know.

---

#### [2025-10-08 03:09:41] @saruman9490

Meanwhile, I see these duplicate fills in the positions cache. They match in all except event_id. Any ideas?

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1425319211265167432/image.png?ex=694ab0b5&is=69495f35&hm=de9494412bb70b85076a7f13110177412c6861da7727e520005e79d6d3a77496&)

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
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426045665515016253/image.png?ex=694ab245&is=694960c5&hm=eed03cae6534e506ed1b4ed6ab1984e35fb03e98f6114a036192571331072cfe&)

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
- [message.txt](https://cdn.discordapp.com/attachments/1277067872111300618/1426054314882760794/message.txt?ex=694aba53&is=694968d3&hm=85a69f2a26ebc3814964851c61829a3ecdf907b0a55388cbfcbb7c61c04c3cff&)

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
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426185331228545166/image.png?ex=694a8b98&is=69493a18&hm=d7e20433259df4c07e2f925c5265447c34a2022ae98a8b103ebd2f5bd2a5c710&)

---

#### [2025-10-10 12:31:32] @saruman9490



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426185382931730536/image.png?ex=694a8ba4&is=69493a24&hm=af9004a6572d0043074f534d3dd12c4cf707e6440fcaa4c100e06e5c8675b792&)

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
