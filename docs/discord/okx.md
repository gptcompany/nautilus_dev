# NautilusTrader - #okx

**Period:** Last 90 days
**Messages:** 18
**Last updated:** 2025-12-22 18:02:05

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

#### [2025-11-01 05:05:19] @mk1ngzz

Does anyone know if OKX support SWAP as instrument type for algo orders? I'm getting this error `Authentication failed: Wrong URL or channel:orders-algo,instType:SWAP doesn't exist. Please use the correct URL, channel and parameters referring to API document.`

---

#### [2025-11-01 07:00:43] @trueorfalse

<@223930266207518721> they are recently making some big changes, I would suggest checking bussiness channel also

---

#### [2025-11-01 07:21:57] @mk1ngzz

apparently their customer service doesn't even know if its supported or not lol

---

#### [2025-11-01 22:31:49] @trueorfalse

that is interesting, could you share subscribe command 
with type of data source (http api, ws api) <@223930266207518721>

---

#### [2025-11-02 01:44:10] @mk1ngzz

their tech team reached out, and they do indeed support it

---

#### [2025-11-02 01:44:34] @mk1ngzz

wondering why it doesn't work then

---

#### [2025-11-02 01:46:08] @mk1ngzz

im using the rust adapter https://github.com/nautechsystems/nautilus_trader/blob/2a4e929e26a783375ac8d633c199433df1b1dc56/crates/adapters/okx/src/websocket/client.rs#L2136-L2147

---

#### [2025-11-02 11:29:03] @trueorfalse

I think it is channel issue they did some changes. may be we should look at the change log.

---

#### [2025-11-02 13:14:26] @mk1ngzz

yeah you're right. the business api has to be used

---

#### [2025-11-09 10:50:54] @mk1ngzz

does anyone know how to submit bracket orders to okx?

---

#### [2025-11-09 10:56:10] @mk1ngzz

i'm trying to use `attachAlgoOrds` when sending an order request, but it just fails with `invalid args`

---

#### [2025-11-10 11:57:55] @mk1ngzz

ok, apparently `attachAlgoOrds` is not supported with the ws api

---
