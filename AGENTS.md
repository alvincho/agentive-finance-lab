# Repository guardrails

This public repository provides small, runnable demonstrations of multi-agent
use cases for finance. Keep each demo understandable in one reading session and
runnable on a laptop. Put application examples under `demos/` so later use
cases can be added without expanding the lite frameworks into products.

## Dependency direction

```text
demos/* -> phemacast-lite -> prompits-lite
```

- `prompits-lite` owns generic Pit identity, Practice and Message contracts,
  `BaseAgent` and `StandbyAgent` runtime behavior, cards, and Plaza
  registration, search, and `UsePractice` routing.
- `phemacast-lite` may import `prompits_lite` and owns generic Pulse, Pulser,
  and Persona behavior. Its `Pulser` must extend Prompits
  Lite's `StandbyAgent`, as the original Phemacast Pulser extends the Prompits
  agent runtime.
- Demo packages may import both lite packages and own all finance-specific
  participants, catalogs, adapters, requests, labels, and UI text.
- Reverse imports are not allowed.

## Public boundary

- Prompits, Phemacast, and Attas are owned by Retis AI Pte Ltd
  (`https://retis.ai`). Preserve that attribution in public documentation,
  notices, and package metadata.
- This repository is a reduced extraction of FinMAS. Start from the existing
  Prompits, Phemacast, and Data Agent Network implementations, then remove only
  the production services that the demo does not run. Do not replace original
  interfaces with newly designed abstractions.
- Do not import `prompits`, `phemacast`, or `attas` from the original repository
  at runtime. The public repository must contain its own reduced copies.
- Do not copy credentials, personal data, generated artifacts, private runtime
  state, or complete production catalogs from FinMAS.
- Do not add investment advice, trading, portfolio actions, UI credential
  collection, persisted credentials, user accounts, data persistence, or
  production claims. The two optional server-side provider keys belong to the
  shared source adapters and are surfaced only through Demo 3's live-fetch UI;
  they are the only credential exception.
- Do not turn the localhost demo into a hosted data API, proxy, scraper, bulk
  collector, or redistribution service.
- Do not add providers outside the explicit source set of a named demo, a
  hosted proxy, a runtime synthetic fallback, or a cache of provider responses.
- Browser storage is not a source of truth. The current UI uses none.

## Lite means reduced, not redesigned

Preserve the original architectural spine:

```text
Pit
  -> BaseAgent
    -> StandbyAgent
      -> Pulser
        -> Persona
```

`Plaza` coordinates agents by composition; it is not part of that inheritance
tree. Every registered Data Agent Network participant must inherit
`BaseAgent`. The browser is the Data User Persona's HTTP interface, not an
additional network participant.

The lite Agent keeps the original identity, card, lifecycle state, Plaza
registration, `search`, and `UsePractice` interfaces. It deliberately omits the
original runtime's per-agent HTTP server, authentication, credential management,
heartbeat/reconnect loop, Pool persistence, mailbox, billing, and distributed
transport. Do not rename these interfaces or replace them with a new
`discover`/`invoke` protocol. Do not omit the Agent layer merely because those
production features are excluded.

## Demo 1 invariant: Data Agent / Single Source

Demo 1 has exactly three addressable network participants:

- **Data User Persona** — user-facing chat and direct source access;
- **Data Consultant Persona** — source status and catalog-grounded advice;
- **YFinance Data Source Pulser** — source documentation and execution.

Preserve these Pulse surfaces:

| Participant | Pulses in Demo 1 |
| --- | --- |
| Data User Persona | `data_request`, `data_source_status`, `data_spec`, `data_fetch` |
| Data Consultant Persona | `data_advice`, `data_source_status` |
| YFinance Data Source Pulser | `data_spec`, `data_availability`, `data_fetch` |

The full system has consultant settings and feedback Pulses. They are
intentionally outside the lite demo and must not be recreated here.

The advisory path is:

```text
User chat
  -> Data User:data_request
  -> Data Consultant:data_advice
  -> ephemeral endpoint/field catalog synchronized from
     YFinance Data Source:data_availability
  -> evidence-grounded advice
```

Advice uses deterministic lexical retrieval over the consultant's in-memory
catalog and a templated response. It does not call Yahoo Finance, fetch market
observations, run an LLM, or perform financial analysis. This is a small
catalog retrieval-augmented response, not a production or generative RAG stack.

After the user selects a source and endpoint, the direct path is:

```text
Data User
  -> Data Consultant:data_source_status
  <- selected source identity and address

Data User:data_spec or data_fetch
  -> YFinance Data Source:data_spec or data_fetch
  -> yfinance only when data_fetch executes
```

The consultant provides source status for resolution, but it never proxies a
provider payload, a provider request, or credentials. Retrieval failures must
be surfaced explicitly; never hide them behind fixtures, synthetic values,
cached results, or another source.

Preserve Demo 1's existing local application route,
`/demos/data-agent-network/`, and its `POST /api/pulse` envelope. Adding another
demo must not change Demo 1's three-participant registration, YFinance-only
catalog, Pulse surfaces, or direct-source path.

## Demo 2 invariant: Data Agent / Multiple Sources

Demo 2 extends the same reduced Data Agent Network design to exactly five
addressable participants in one in-process Plaza:

- **Data User Persona** — user-facing chat and direct selected-source access;
- **Data Consultant Persona** — source status and catalog-grounded advice;
- **YFinance Data Source Pulser**;
- **Alpha Vantage Data Source Pulser**; and
- **FRED Data Source Pulser**.

Do not create a new workflow for Demo 2. The Data User and Data Consultant use
the same Persona behavior and Pulse surfaces as Demo 1. Each source Pulser owns
the same `data_spec`, `data_availability`, and `data_fetch` contracts. At
startup, the Consultant Plaza-searches for all three source Pulsers and
synchronizes each source's documentation into transient catalog memory.

The advisory path remains:

```text
User chat
  -> Data User:data_request
  -> Data Consultant:data_advice
  -> lexical retrieval over the synchronized catalogs from
     YFinance, Alpha Vantage, and FRED
  -> catalog-grounded source and endpoint advice
```

Advice, source status, and specification do not call any upstream provider.
Once the user selects an endpoint, the direct path remains:

```text
Data User
  -> Data Consultant:data_source_status
  <- selected source identity and address

Data User:data_spec or data_fetch
  -> selected Data Source Pulser:data_spec or data_fetch
```

The Consultant must not fetch, merge, forward, or cache provider observations.
Plaza discovers and resolves participants but does not become a provider-data
proxy. Demo 2's canonical UI route is
`/demos/data-agent-network/multiple-sources/`.

Both networks retain the original `data_fetch` Pulse contract. Demo 2's UI is
catalog/specification-only; Demo 3 is the live-execution view.

Keep only this reduced provider surface in Demos 2 and 3:

| Source | Reduced operations |
| --- | --- |
| YFinance | `ticker.history`, `ticker.fast_info`, `ticker.info` |
| Alpha Vantage | `time_series_daily`, `global_quote`, `overview` |
| FRED | `series/observations`, `series/vintagedates` |

`ALPHA_VANTAGE_API_KEY` and `FRED_API_KEY` are optional server-side
environment variables used only by their source Pulser when live `data_fetch`
executes. Catalog synchronization, advice, source status, and `data_spec` must
work without them. Never expose credential fields in the UI, accept provider
secrets in Pulse input, return secrets in results, or log them.

## Demo 3 invariant: Data Agent / Real Data

Demo 3 is the live-execution view of the same five-participant network used by
Demo 2. It may create an isolated Plaza instance, but it must instantiate the
existing `MultipleSourceDataAgentNetworkDemo`; it must not add another
workflow, Pulse, provider, proxy, merge service, or fallback path.

The canonical route is `/demos/data-agent-network/real-data/`. The shared Data
User UI may run these bounded examples through the existing `data_fetch` Pulse:

1. With Yahoo Finance reachable, YFinance AAPL daily history succeeds without a
   key while Alpha Vantage deterministically returns `authentication_required`
   when its key is absent.
2. After the visitor adds `ALPHA_VANTAGE_API_KEY` to the repository-root
   `.env` and restarts, YFinance and Alpha Vantage are called separately and
   both results remain separate.
3. After the visitor obtains a free FRED API key, adds `FRED_API_KEY`, and
   restarts, the FRED source retrieves a bounded `CPIAUCSL` observations
   response.

The UI may expose only boolean readiness states such as key needed, key set,
or fetch verified. It must never display, accept, persist, or send a key. A
checked-in `.env.example` contains blank values only; `.env` must remain
ignored. An existing process environment takes precedence over `.env`.

Demo 2 remains catalog/specification oriented in its UI. Demo 3 makes the
already-implemented source fetch controls visible. Whether an adapter exists
and whether its credential is currently configured are separate facts: a
missing key must produce the source's explicit authentication result rather
than making the implemented route disappear.

## Concept ownership

- Preserve `Pit`, `BaseAgent`, `StandbyAgent`, `Plaza`, `Pulse`, `Pulser`, and
  `Persona` as recognizable concepts and preserve their dependency order.
- Do not invent an acronym expansion for Pit.
- Keep Persona configuration distinct from the runtime `Persona` class.
- A `Pulse` is a named, structured interaction contract; do not substitute ad
  hoc method calls for network interactions.
- Use the original Plaza metadata, `search`, and `UsePractice` behavior for
  registration, discovery, resolution, and routing. Do not hard-code a Data
  User-to-Consultant or Data User-to-Source object call.
- Registered participants must enter Plaza through their Agent registration
  lifecycle and use inherited `search`/`UsePractice` helpers. Do not reduce
  them back to raw `Pit` objects routed only by orchestration code.

## Source boundaries

- In Demo 1, `yfinance` is the only external financial-data source. Keep its
  dependency pinned to `yfinance==1.6.0` and preserve its current three-entry
  catalog.
- In Demos 2 and 3, the only sources are YFinance, Alpha Vantage, and FRED,
  with only the reduced operations listed above.
- Provider I/O belongs only in the selected Data Source Pulser. Alpha Vantage
  and FRED HTTP requests must use their documented APIs and server-side key;
  browser scraping and Consultant-side provider access are not allowed.
- The in-memory consultant catalog contains endpoint and field documentation,
  not cached provider observations.
- Do not add streaming feeds, another data source, LLM-generated data,
  persistent/background collection, provider-response caching, cross-source
  fallback, or provider-payload proxying.
- Deterministic fakes are allowed in tests only and must never be selectable as
  a runtime source or fallback.

## HTTP and UI

- Preserve the Data User interface's `POST /api/pulse` request envelope with
  `pulse_name` and `input`. Do not replace the Pulse boundary with separate
  chat, specification, or fetch REST workflows.
- Reuse the reduced Data User interface for all demos. Demos 2 and 3 may
  configure labels, suggestions or samples, source lists, API bases, and live
  fetch visibility, but they must not fork a new chat application or invent a
  second interaction model.
- Keep the landing page focused on repository purpose and framework concepts,
  then lead the user into the Data Agent Network demo.
- Duplicate the original Data User HTML, CSS, and JavaScript, then remove only
  unavailable production features. Keep its layout, terminology, interaction
  model, source/endpoint rendering, and Pulse calls recognizable.
- Keep the demo compact and action-oriented. Make participant, Pulse, source,
  endpoint, provenance, and errors inspectable through the existing Data User
  surfaces. Do not add a replacement trace or workflow UI.
- When loaded with `file://`, explain that the local server is required instead
  of attempting broken API calls.
- Preserve keyboard labels, reduced-motion behavior, and text-safe DOM updates.
- Do not add `localStorage`, `sessionStorage`, or unsanitized `innerHTML`.

## Documentation and claims

- State that `yfinance` is unaffiliated with Yahoo and that Yahoo Finance data
  is intended for personal use, subject to applicable terms.
- State that Alpha Vantage and FRED access remains subject to their respective
  API terms and limits; the repository grants no provider-data rights.
- Never imply data licensing, guaranteed availability, real-time accuracy,
  production readiness, predictive benefit, or improved investment outcomes.
- Describe the multi-agent benefit as visible ownership, discovery, structured
  contracts, traceability, and replaceability.
- Do not describe the consultant as a live market-data proxy or analyst.

## Required checks

```bash
python -m pytest
python -m compileall -q prompits-lite phemacast-lite demos/data-agent-network-demo
```
