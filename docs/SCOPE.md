# Public demo scope

The repository exists to demonstrate the benefit of explicit multi-agent
ownership in finance applications. It is intentionally too small for
production use.

Prompits, Phemacast, and Attas are owned by
[Retis AI Pte Ltd](https://retis.ai/). This repository includes only the
reduced FinMAS components needed for the public demonstrations described here.

## Included

- reduced copies of the original Prompits Pit, Practice, Agent, and Plaza
  behavior;
- reduced copies of the original Phemacast Pulse, Pulser, and Persona behavior;
- the original Data Agent Network roles and Pulse names;
- in-process Plaza registration, search, Pit resolution, and `UsePractice`;
- one transient Data Consultant endpoint/field catalog per demo network;
- the original Data User interface copied and reduced;
- Demo 1, **Data Agent / Single Source**, with one Data User Persona, one Data
  Consultant Persona, and one YFinance Data Source Pulser;
- Demo 2, **Data Agent / Multiple Sources**, with one Data User Persona, one
  Data Consultant Persona, and YFinance, Alpha Vantage, and FRED Data Source
  Pulsers;
- Demo 3, **Data Agent / Real Data**, which instantiates the same five-agent
  network in an isolated Plaza and exposes bounded live-fetch samples through
  the reused Data User interface;
- the reduced operations for each source: YFinance `ticker.history`,
  `ticker.fast_info`, and `ticker.info`; Alpha Vantage `time_series_daily`,
  `global_quote`, and `overview`; and FRED `series/observations` and
  `series/vintagedates`;
- direct, request-scoped provider access only when `data_fetch` executes;
- optional server-side `ALPHA_VANTAGE_API_KEY` and `FRED_API_KEY` environment
  variables for live fetches from those sources; and
- deterministic provider fakes in tests only.

## Excluded

- investment advice, trading, orders, portfolio actions, forecasts, or signals;
- production hosting, reliability, security, licensing, or accuracy claims;
- user accounts, OAuth, UI credential fields, Pulse-carried secrets, persistent
  credentials, or credential collection;
- persistent data, browser storage, background collection, and provider caches;
- synthetic or cached market observations, provider-response proxies, and
  alternate-source fallbacks;
- financial-data providers beyond YFinance, Alpha Vantage, and FRED, or
  operations beyond each reduced catalog;
- bulk downloads, scraping, streaming, or redistribution services;
- LLM synthesis, embeddings, model routing, and learning from feedback;
- distributed transport, Plaza authentication, billing, leases, and heartbeat;
- the complete private FinMAS catalogs, configuration, runtime state, or data.

## Demonstrated multi-agent benefit

The examples demonstrate only these architectural benefits:

- the Data User owns user intent and direct selected-source access;
- the Data Consultant owns catalog memory and source advice;
- the Data Source owns provider documentation and execution;
- Plaza discovers and resolves replaceable participants by their cards;
- Pulses make cross-agent interactions explicit and inspectable;
- provider data does not pass through an advisory agent.

It does not claim that multiple agents improve returns, predictions, data
quality, latency, or cost.

## Demo boundaries

Demo 1 remains the original three-participant, YFinance-only reduction at
`/demos/data-agent-network/`. Demo 2 uses the canonical UI route
`/demos/data-agent-network/multiple-sources/`; Demo 3 uses
`/demos/data-agent-network/real-data/`. Demos 2 and 3 each instantiate the
existing five-participant network. Adding them must not change Demo 1's
registration, routes, Pulse surfaces, catalog, or direct-source behavior.

Demos 2 and 3 follow the same path:

```text
Data User:data_request
  -> Data Consultant:data_advice
  -> transient source-document catalog

Data User:data_spec or data_fetch
  -> Data Consultant:data_source_status
  <- selected source identity and address
  -> selected Data Source Pulser directly
```

Both networks retain the original `data_fetch` Pulse contract. Demo 2's UI is
catalog/specification-only; Demo 3 is the live-execution view.

The Consultant owns catalog advice, not provider retrieval. Plaza registers,
discovers, and resolves participants; it is not a provider-data proxy. Neither
component merges observations or hides one provider's failure by selecting
another.

## Data-source boundary

Demo 1 uses only `yfinance==1.6.0`. Demos 2 and 3 use YFinance plus the
documented Alpha Vantage and FRED APIs. Provider I/O occurs only inside the
selected Data Source Pulser's `data_fetch` Pulse. Catalog advice, source status,
and endpoint specification are local and work without live provider access.

Alpha Vantage and FRED keys are optional server-process environment variables
used only for live `data_fetch`; the browser never collects or stores them.
The repository-root `.env` is ignored, its checked-in example contains blank
values only, and process variables take precedence. When a required key is
absent, the source returns an explicit `authentication_required` result. The
runtime must not substitute another provider, proxy the request through the
Consultant, or expose a secret in UI, Pulse input, result, or log.

Failures remain failures. The runtime must not replace them with test fixtures,
synthetic prices, cached responses, or another provider.

`yfinance` is not affiliated with Yahoo. Yahoo Finance data is intended for
personal use and remains subject to applicable terms. This repository does not
grant data rights or guarantee availability, freshness, completeness, or
accuracy. Alpha Vantage and FRED access likewise remains subject to their
respective API terms, entitlements, and limits.
