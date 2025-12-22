# NautilusTrader - #dydx

**Period:** Last 90 days
**Messages:** 66
**Last updated:** 2025-10-23 04:00:40

---

#### [2025-08-30 06:19:49] @saruman9490

is anyone trading actively DYDX?

---

#### [2025-08-30 11:00:51] @.davidblom

I’m aware of some traders. You need the latest develop branch or nightly branch though due to some changes to the message schemas by the venue.

---

#### [2025-08-31 04:47:30] @saruman9490

def seems to be the case as I've not been able to get it reliable for a while

---

#### [2025-08-31 05:28:29] @.davidblom

Thanks for the feedback. Feel free to report or open issues if you run into any

---

#### [2025-08-31 05:32:34] @saruman9490

Could you elaborate about why best effort cancelled is skipped.

While revieweing I noticed that my web app shoes the order as cancelled when Nautilus receives this message

```2025-08-31T05:05:49.111891054Z [INFO] TESTER-003.ExecClient-DYDX: Skip order message: DYDXWsOrderSubaccountMessageContents(id='3c89352b-823c-5f0c-8d55-297e812168c8', ticker='BTC-USD', status=<DYDXOrderStatus.BEST_EFFORT_CANCELED: 'BEST_EFFORT_CANCELED'>, orderFlags='0', reduceOnly=True, postOnly=False, timeInForce=<DYDXTimeInForce.IOC: 'IOC'>, type=<DYDXOrderType.LIMIT: 'LIMIT'>, price='1', size='0.0004', side=<DYDXOrderSide.BUY: 'BUY'>, clientMetadata='1', clobPairId='0', clientId='2602749346', subaccountId='926cd8b4-fda5-5919-99d3-bccddc262920', totalFilled=None, totalOptimisticFilled='0', goodTilBlock='54234550', goodTilBlockTime=None, removalReason='ORDER_REMOVAL_REASON_IMMEDIATE_OR_CANCEL_WOULD_REST_ON_BOOK', createdAtHeight=None, triggerPrice=None, updatedAt=None, updatedAtHeight=None, builderAddress=None, feePpm=None, duration=None, interval=None, priceTolerance=None, orderRouterAddress=None)```

---

#### [2025-08-31 05:34:25] @.davidblom

Best effort canceled isn’t the final state. The adapter waits until it is canceled. Due to the distributed nature of the exchange, the cancel can be reverted

---

#### [2025-08-31 05:34:49] @saruman9490

How late can the actual cancel be?

---

#### [2025-08-31 05:35:23] @.davidblom

Should come within a couple seconds

---

#### [2025-08-31 05:36:53] @saruman9490

Ok I'll be on the lookout for that

---

#### [2025-08-31 05:37:52] @saruman9490

While we are on the subject are long term orders supported or not?
```2025-08-31T05:27:37.508796383Z [WARN] TESTER-003.ss.ta-hawk.5m.test: <--[EVT] OrderRejected(instrument_id=BTC-USD-PERP.DYDX, client_order_id=O-20250831-052737-003-026-1, account_id=DYDX-dydx18l256stt4xe05p650y9euk5cmr7cjrez0gr9w2-0, reason='Cannot submit order: long term market order not supported by dYdX', ts_event=1756618057507284072)```

---

#### [2025-08-31 05:38:32] @.davidblom

Yeah, they are supported. The docs show how to submit them.  You’ll need to add a tag to an order

---

#### [2025-08-31 05:39:34] @saruman9490

Is tag enought since I have it set like this
```
  tags = [ DYDXOrderTags(is_short_term_order=False, market_order_price=str( market_order_price ) ).value ]
```

---

#### [2025-08-31 05:41:07] @.davidblom

Market orders are always short term. Only limit orders can be set to long term. This is restricted by the venue.

---

#### [2025-08-31 06:01:45] @saruman9490

What could be causing this
```
2025-08-31T06:00:05.968358461Z [WARN] TESTER-003.ExecClient-DYDX: DYDXGRPCError('Failed to place the order: tx_response {\n  txhash: "3B514BED1AF19A5CA272E703051AA5D243605D2917D585AF381CE4260C1E8E00"\n  codespace: "sdk"\n  code: 4\n  raw_log: "signature verification failed; please verify account number (0) and chain-id (dydx-mainnet-1): (unable to verify single signer signature): unauthorized"\n}\n')
```
2 minutes ago from the same note the buy order opened normally

---

#### [2025-08-31 06:10:57] @saruman9490

additional question - why do orders cancel? do we go over the blocks?

---

#### [2025-08-31 06:17:40] @.davidblom

Short term orders are valid up to 20 blocks. You can configure the maximum with an order tag. After 20 blocks, they are always canceled, even if a message is not sent by the venue. This isn’t implemented yet in the adapter though.

---

#### [2025-08-31 06:18:13] @saruman9490

You mean that the cancel is not captured by the adapter?

---

#### [2025-08-31 06:18:45] @.davidblom

The adapter doesn’t create a cancel after N blocks if it didn’t receive it from the venue.

---

#### [2025-08-31 06:19:11] @saruman9490

how'd you go about it? Is there a block tracker somewhere? I could have a look into it

---

#### [2025-08-31 06:19:32] @.davidblom

Yeah, the adapter listens for block updates and tracks them.

---

#### [2025-08-31 06:20:20] @.davidblom

Feel free to take a stab at it. Much appreciated

---

#### [2025-08-31 06:20:27] @saruman9490

So seems like, I'd create a task to track the cancel after receiving beset_effort_cancel

---

#### [2025-08-31 06:20:41] @saruman9490

otherwise, I'd just keep polling for active orders or smth

---

#### [2025-08-31 06:20:43] @saruman9490

which way you'd recommend?

---

#### [2025-08-31 06:22:19] @.davidblom

I’d create a task after order submission. When submitting an short term order, the max block is set. If that block is later received, the order is canceled if not yet filled.

---

#### [2025-08-31 06:22:38] @.davidblom

This is only applicable to short term orders though, for example market orders.

---

#### [2025-08-31 06:23:52] @.davidblom

Not sure about this one. Is it retried later? I remember adding some retry logic but not sure if this one is retried.

---

#### [2025-09-02 21:00:06] @saruman9490

Correct me if I'm wrong but seems like best_effort_calcelled is pretty reliable, so I'm thinking attaching a loop to track block hight exceeding goodtilblock once I get taht. I could also do that after order is accepted. What do you think?

---

#### [2025-09-02 21:01:07] @saruman9490

Btw, do you know if the block is inclusive or not? 😄 Ie if block_height = goodtilblock, does that mean order has been canceled?

---

#### [2025-09-03 04:20:32] @.davidblom

It is inclusive as far as I know. If block height => goodtilblock, it has been cancelled.

---

#### [2025-09-03 04:21:49] @.davidblom

You could check all open orders when a block height update is received.

---

#### [2025-09-03 18:37:03] @saruman9490

When restarting the strategy I often get this - 
```
KeyError: "Duplicate TradeId('83fbf437-97d0-5fa1-8b46-3d6be42a9cda') in events OrderFilled(instrument_id=BTC-USD-PERP.DYDX, client_order_id=O-20250903-182620-003-026-2, venue_order_id=79004904-0b8f-57a8-8832-4b77aeb37b85, account_id=DYDX-dydx18l256stt4xe05p650y9euk5cmr7cjrez0gr9w2-0, trade_id=83fbf437-97d0-5fa1-8b46-3d6be42a9cda, position_id=BTC-USD-PERP.DYDX-ss.ta-hawk.5m.test-026, order_side=SELL, order_type=MARKET, last_qty=0.0004, last_px=112_235 USDC, commission=0.01795800 USDC, liquidity_side=TAKER, ts_event=1756923980138000000) OrderFilled(instrument_id=BTC-USD-PERP.DYDX, client_order_id=O-20250903-182620-003-026-2, venue_order_id=79004904-0b8f-57a8-8832-4b77aeb37b85, account_id=DYDX-dydx18l256stt4xe05p650y9euk5cmr7cjrez0gr9w2-0, trade_id=83fbf437-97d0-5fa1-8b46-3d6be42a9cda, position_id=BTC-USD-PERP.DYDX-ss.ta-hawk.5m.test-026, order_side=SELL, order_type=MARKET, last_qty=0.0004, last_px=112_235 USDC, commission=0.01795800 USDC, liquidity_side=TAKER, ts_event=1756923980138000000)"
```
Seems to be a problem in hte cache. Any ideas/ suggestions? I've noticed that all the position_ids are the same. Never had this before with non DYDX.

---

#### [2025-09-03 20:15:32] @.davidblom

Does this happen during initial reconciliation?

---

#### [2025-09-04 03:51:44] @saruman9490

yes

---

#### [2025-09-11 18:31:42] @saruman9490

I've been debugging dydx and noticed that all the positions have the same ID. is that how it should be?

---

#### [2025-09-11 18:32:32] @saruman9490

is that by design since DYDX nets the positions and just has one per instrument?

---

#### [2025-09-12 05:36:39] @.davidblom

Havent been able to get to this yet, it is a restriction of the venue I believe.

---

#### [2025-09-12 05:38:43] @.davidblom

https://docs.dydx.xyz/types/perpetual_position_response_object

**Links:**
- dYdX Documentation

---

#### [2025-09-16 03:25:52] @saruman9490

Still digging deeper and I think I'm closing in on the issue. Why are you by default ignoring the fill message and relying on the http endpoint to confirm the order submission? I've had a case where polling lagged and it created a discrepancy between what dydx position is and what nautilus thinks it is.

---

#### [2025-09-18 04:44:40] @.davidblom

The fill is applied twice if it is not ignored . The venue sends the fill in two places

---

#### [2025-09-21 13:14:37] @saruman9490

Ocassionaly I'm getting this error

```
DYDXGRPCError('Failed to place the order: tx_response {\n  txhash: "6817362C1B848B913699C2A25D4D3E618DDAC33CBC755F9622FBC9E1F818731E"\n  codespace: "sdk"\n  code: 4\n  raw_log: "signature verification failed; please verify account number (0) and chain-id (dydx-mainnet-1): (unable to verify single signer signature): unauthorized"\n}\n')[0m
[1m2025-09-21T09:00:05.826905553Z[0m [1;33m[WARN] TESTER-003.ss.ta-hawk.5m.test: <--[EVT] OrderRejected(instrument_id=BTC-USD-PERP.DYDX, client_order_id=O-20250921-090005-003-026-4, account_id=DYDX-dydx18l256stt4xe05p650y9euk5cmr7cjrez0gr9w2-0, reason='Failed to place the order: tx_response {
  txhash: "6817362C1B848B913699C2A25D4D3E618DDAC33CBC755F9622FBC9E1F818731E"
  codespace: "sdk"
  code: 4
  raw_log: "signature verification failed; please verify account number (0) and chain-id (dydx-mainnet-1): (unable to verify single signer signature): unauthorized"
}
', due_post_only=False, ts_event=1758445205824724545)[0m
```
any ideas why? The retries don't help either

---

#### [2025-09-23 05:17:46] @.davidblom

Thanks for reporting. Perhaps a race condition?

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
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1425319211265167432/image.png?ex=68faedf5&is=68f99c75&hm=89ed22ad9c7dc2141321a0d9d8b86d5d3f58724336c2e341d28bc06d675ae499&)

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
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426045665515016253/image.png?ex=68faef85&is=68f99e05&hm=84d2d0a7850b08b872710f19a73c4c25d0e4b36726876dc907c51e0c6ba4a6de&)

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
- [message.txt](https://cdn.discordapp.com/attachments/1277067872111300618/1426054314882760794/message.txt?ex=68faf793&is=68f9a613&hm=531bc718f9b66ad6343fec70a4769a1310ea014f6c4320ef1ec6f6be2617474a&)

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
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426185331228545166/image.png?ex=68fac8d8&is=68f97758&hm=c876260499ba77b1296ba098489e202fe2b19d0f871c8d57ee21847e67883bb4&)

---

#### [2025-10-10 12:31:32] @saruman9490



**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/1277067872111300618/1426185382931730536/image.png?ex=68fac8e4&is=68f97764&hm=bbd11df1705d3ec2f2b59eb012e67e0b076ba0742fd17c346febcb811f8bddf5&)

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
