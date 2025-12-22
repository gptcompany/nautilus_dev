# NautilusTrader - #feedback

**Period:** Last 90 days
**Messages:** 12
**Last updated:** 2025-10-23 04:00:29

---

#### [2025-08-14 10:35:29] @significant_0tter

hands down the most modular, modern and adaptive trading library I have seen so far. If an hibachi adapter can be thought of at some point (another dex agregator). Willl give a shot at coding the adapter once I get my head around the archi.

---

#### [2025-08-16 11:55:46] @maguiresfuture

Are there plans for a NautilisTrader MCP Server to connect to ChatGPT Pro or Claude?

---

#### [2025-08-16 12:17:51] @premysl_22228

A crazy idea, but after few minutes of thinking, it might be working, even with questionable outcomes.  Somebody might really program it, but I think, this is less then nice-to-have priority. It is much better idea to put Claude, ChatGPT/... API on message bus in other process and let the NT be "the master". If you do it, let us please know of the outcome and optionally publish the outcome, if you don't plan to trade on it... 🙂 

I heart some people are making this way real money on crypto, but I am not sure, whether it isn't Ponzi scheme trap. I would need to see some harder proof, than "I know a guy, who knows a guy, who knows a guy, that made 3000% in few months on $100000 in crypto..."

---

#### [2025-08-16 15:31:08] @maguiresfuture

Quantconnect recently launched a MCP server with Claude and ChatGPT but Nautilus is way better than Quantconnect so it would be nice to see that here.

---

#### [2025-08-16 16:47:09] @premysl_22228

Quantconnect is rather more "complete ecosystem" than NT package. NT is primarily a package for backtesting and live trading, every other feature like optimization must be imported from other library or implemented by yourself. There are some exceptions to the rule, but... Nobody tells you, how optimize, structure your project, etc., but the price is, there probably can't exist a meaningful equivalent. Try to use Claude Code with Opus model to strategy development, optimization, etc., after you feed it by few examples, how you imagine it is correctly done, and you might find out, you don't need MCP Integration at all.

---

#### [2025-08-16 16:57:15] @premysl_22228

I would say, try to use MCP integrations to get info out of GitHub and Discord, but last time I checked, the AI protested a lot I used it to resolving CAPTCHAS and it isn't easy to jailbreak it to get direct feed from Discord history search. You might must make the initial examples yourself. Adding symlink to acceptence tests, examples,... to the project will help AI a lot in the beginning, so it is easier for you. 🙂

---

#### [2025-08-26 13:57:43] @frzgunr

Hello <@757548402689966131> . Are you planning to add a price aggregation feature for candlesticks? (Such as Renko or RangeUS candlesticks). I've implemented RangeUS candlesticks as an indicator using Python, but it clearly consumes significant computational resources. If you are considering adding a price aggregation feature, I'd be happy to assist.

---

#### [2025-08-29 10:13:58] @faysou.

You could do a PR by analogy to aggregator.pyx. The difficult aggregator is the time bar aggregator, the price aggregators are relatively easy in logic, you could get them implemented by an LLM agent and review before doing a PR.

---

#### [2025-08-29 13:42:46] @frzgunr

got it, thx bro

---

#### [2025-10-11 19:35:31] @_minhyo

docs/tutorials/     Jupyter notebook tutorials demonstrating common workflows.
docs/concepts/     Concept guides with concise code snippets illustrating key features.


both links are dead

**Attachments:**
- [image.png](https://cdn.discordapp.com/attachments/926698977678737418/1426654467264217118/image.png?ex=68fa8382&is=68f93202&hm=b1f30972761471ae72954a6243841f0e2c72056eb486d94f622adff7785bba34&)

---

#### [2025-10-11 19:36:38] @_minhyo

seems to be a github issue

---

#### [2025-10-11 19:36:45] @_minhyo

i see its working on the mainsite

---
