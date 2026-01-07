# NautilusTrader - #trading

**Period:** Last 90 days
**Messages:** 12
**Last updated:** 2026-01-07 01:29:42

---

#### [2025-12-09 04:02:56] @saruman9490

Can Nautilus strategy spawn another strategy? If so, could maybe someone give me an example?

---

#### [2025-12-10 01:01:24] @petioptrv

You need to add the strategy to the Trader, and the strategy itself doesn’t have access to the trader. I usually create an overarching strategy that inherits from the NT strategy base class, subscribes to the necessary data, and then forwards the data to a map of subscribers that it maintains (the "spawned strategies")

---

#### [2025-12-10 01:05:46] @cjdsellers

Thanks <@706300741270110330>, hey <@337157623352655873> also consider the `Controller` and its `create_strategy` method: https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/trading/controller.py#L123

We reserve this capability for the `Controller` just so there is some hierarchy so that strategies can't just spawn other strategies and so on. It keeps the system simpler and easier to reason about this way

---

#### [2025-12-10 05:18:16] @saruman9490

Exactly, how I've been doing as well 😄

---

#### [2025-12-10 05:18:46] @saruman9490

I'll need to have a look into that controller! Thanks for the pointer 🙂

---

#### [2025-12-10 06:59:59] @saruman9490

That looks pretty good, are there any examples with it by any chance/

---

#### [2025-12-10 15:13:12] @saruman9490

Should I add the controller as an actor to the trader with add_actor?

---

#### [2025-12-10 15:48:47] @saruman9490

Got this error - so it seems like I cant add strategies dynamically, right?
```
2025-12-10T15:47:54.318921193Z [ERROR] TEST-001.TEST-001: Cannot add a strategy to a running trader
```

---

#### [2025-12-28 02:13:44] @courage521915

<@757548402689966131> Hello, I often encounter the following warning after an order reaches OrderSubmitted. After several retries, the order eventually gets OrderRejected, and many of my orders fail to be placed successfully.

I would like to ask whether this issue could be related to using a VPN, or if there might be other possible causes.
2025-12-27T01:04:27.578840300Z [WARN] TESTER-001.ExecClient-POLYMARKET: Did not receive OrderStatusReport from request
courage — 09:37
This issue is very common in my environment. About half of my orders fail to be successfully placed because of this problem.

---

#### [2025-12-28 07:35:22] @faysou.

You have written the same message several times already. There's no guarantee you will get an answer when you ask something.

---

#### [2025-12-28 10:19:12] @courage521915

Sorry, I'll be more careful from now on.I've really been struggling with this problem for a long time.

---

#### [2025-12-28 10:54:19] @faysou.

I understand, but other people can't always solve a problem that is too specific to what you do. There's no need to send the same message several times, there are not that many messages being sent on this discord server, they are all read. If you want that your issue is not forgotten better to create an issue on GitHub.

---
