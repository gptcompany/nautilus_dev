# NautilusTrader - #okx

**Period:** Last 90 days
**Messages:** 10
**Last updated:** 2025-10-23 04:00:41

---

#### [2025-08-27 10:12:19] @joker06326

If I want to trade btcusdt spot, how should I define instrumentId in okx adapter?

---

#### [2025-08-28 06:24:28] @cjdsellers

Hi <@1162973750787051560> 
You'll find some clues in [this example](https://github.com/nautechsystems/nautilus_trader/blob/develop/examples/live/okx/okx_exec_tester.py#L45). Typically `{base}-{quote}` is the convention, the perps have a `-SWAP` suffix. I'll update the integration guide to provide more clarity around this

---

#### [2025-09-09 17:28:52] @kmilesz

I have a question about implementing the adaptor. Does it need to strictly adhere to the developer guide? For instance, I noticed that the type for _subscribe_order_book_deltas in the OKX data client is different from what's specified in the guide. Will this discrepancy cause some issues? Or does it not matter as long as the configuration is correct, and we don't need to be concerned with type uniformity? thanks!

---

#### [2025-09-14 23:34:23] @cjdsellers

Hi <@1288926845399732328> 
I think the guide was outdated, it should be updated now for the actual method signature used. The main thing is that all of the parsing and API clients are implemented in Rust. The Python under `nautilus_trader/adapters/` is only a thin translation layer back into the legacy Cython system.

[edit] The adapters guide has now been updated: https://nautilustrader.io/docs/nightly/developer_guide/adapters

---

#### [2025-10-13 22:28:58] @a1ecbr0wn

Has anyone else got this error:
```
  File "/Users/ΔǀΞȼ/.pyenv/versions/3.11.13/lib/python3.11/site-packages/nautilus_trader/common/config.py", line 131, in msgspec_encoding_hook
    raise TypeError(f"Encoding objects of type {obj.__class__} is unsupported")
TypeError: Encoding objects of type <class 'nautilus_trader.core.nautilus_pyo3.okx.OKXInstrumentType'> is unsupported
```

---

#### [2025-10-13 22:31:18] @a1ecbr0wn

It seems to be a reproducible issue for me, I get this when I run one of the tests in the code repo:
```
python3 examples/live/okx/okx_data_tester.py
```

---

#### [2025-10-15 12:30:54] @a1ecbr0wn

I guess it is only me then

---

#### [2025-10-16 04:29:45] @cjdsellers

Hi <@442782643344506890> 
Thanks for the feedback, I think this might just be because this type is not automatically registered with the `msgspec` [encoding hooks for serialization](https://github.com/nautechsystems/nautilus_trader/blob/develop/nautilus_trader/common/config.py#L107). In what sort of context are you trying to use the instrument type, one of the OKX configs?

(I don't get the same error when running that example 🤔)

---

#### [2025-10-16 04:30:49] @cjdsellers

As the OKX adapter is quite new, I'd encourage anyone who is trying to use it and running into issues to kindly report and I'll see about fixing as soon as I can!

---

#### [2025-10-16 08:04:33] @a1ecbr0wn

I was just trying to set up a `OKXDataClientConfig` as a part of a `TradingNodeConfig`:
```
            data_clients={
                OKX: OKXDataClientConfig(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    api_passphrase=self.api_passphrase,
                    instrument_provider=InstrumentProviderConfig(load_ids=instruments),
                    instrument_types=(OKXInstrumentType.SPOT,),
                ),
            },
```
I'll try building from source and see if that makes a difference.
I am still learning how to use this tool so I am sure it is just something I have missed from the documentation.

---
