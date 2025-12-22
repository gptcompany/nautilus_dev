# NautilusTrader - #trading

**Period:** Last 90 days
**Messages:** 13
**Last updated:** 2025-12-22 18:01:52

---

#### [2025-09-24 04:39:54] @joker06326

<@757548402689966131> I use manage_gtd to push gtc order on bybit, but sometimes the cancel time was an error.

**Attachments:**
- [message.txt](https://cdn.discordapp.com/attachments/931763076930367608/1420268487250808872/message.txt?ex=694ac5da&is=6949745a&hm=0f9e5c6eb3772509ea6c1faf939ea6664fa18ca1373689da7b3f9d2ac4a50e9a&)

---

#### [2025-09-25 01:56:52] @cjdsellers

Hi <@1162973750787051560> thanks for reporting, I'll investigate these logs soon

---

#### [2025-10-03 22:27:53] @donaldcuckman

sharing the strategies will only make it harder for everyoneelse and do something fucky to the economy. Though probably a push in the right direction

---

#### [2025-10-03 22:28:36] @donaldcuckman

maybe not actually, all the common strategies would just become less profitable

---

#### [2025-10-03 22:28:41] @donaldcuckman

for the small fry

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
