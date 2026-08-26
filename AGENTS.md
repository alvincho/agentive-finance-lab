# Repository guardrails

This is a small public demonstration repository. Keep it understandable in one
reading session and runnable on a laptop.

## Dependency direction

```text
demos/data-agent-network-demo -> phemacast-lite -> prompits-lite
```

- `prompits-lite` owns only generic Pit identity, cards, traces, and Plaza
  registration, discovery, and routing.
- `phemacast-lite` may import `prompits_lite` and owns only generic Pulse,
  Pulser, PersonaProfile, and Persona contracts.
- Demo packages may import both lite packages and own every finance-specific
  role, request, adapter, analytic, label, and UI string.
- Reverse imports are not allowed.

## Public boundary

- Do not copy implementation files, schemas, configs, snapshots, generated
  artifacts, credentials, or personal data from FinMAS.
- Do not import `prompits`, `phemacast`, or `attas` from the original repository.
- Do not add investment advice, trading, portfolio actions, credentials, user
  accounts, data persistence, or production claims.
- Do not turn the localhost demo into a hosted data API, proxy, scraper, bulk
  collector, or redistribution service.
- Browser storage is not a source of truth. The current UI uses none.

## First-demo invariant

The first demo has one task and one runtime data path:

```text
Data User -> Plaza -> Data Consultant -> yfinance
```

- The request compares one primary symbol with one benchmark over a supported
  period using adjusted daily history.
- `yfinance` is the only external source of financial data. Keep its dependency
  pinned to `yfinance==1.6.0` for this demo.
- Provider I/O belongs to the Data Consultant side of the boundary. Keep the
  import and provider-specific normalization isolated in the yfinance adapter.
- Do not add another provider, direct HTTP scraping, browser scraping, provider
  routing, streaming feeds, or LLM-generated data.
- Do not add a runtime fixture, synthetic series, stale cache, or alternate
  fallback. Surface retrieval failures explicitly.
- Deterministic fakes are allowed in tests only and must be injected through the
  source protocol; production construction must always select yfinance.
- Output is descriptive historical analysis, never a prediction,
  recommendation, signal, or suitability judgment.

## Concept ownership

- Preserve `Pit`, `Plaza`, `Pulser`, and `Persona` as recognizable concepts.
- Do not invent an acronym expansion for Pit.
- Keep `PersonaProfile` distinct from the runtime `Persona` class.
- The Data User must discover the specialist through Plaza metadata and a typed
  Pulse, never a hard-coded direct call to the Data Consultant.
- Keep the Data User responsible for request/acceptance and the Data Consultant
  responsible for retrieval/analysis.

## UI

- Keep the main page compact and action-oriented.
- Make the comparison result primary and keep request, route, quality,
  provenance, provider errors, and correlation trace inspectable.
- When loaded with `file://`, explain that the local server is required instead
  of attempting broken API calls.
- Preserve keyboard labels, reduced-motion behavior, and text-safe DOM updates.
- Do not add `localStorage`, `sessionStorage`, or unsanitized `innerHTML`.

## Documentation and claims

- State that `yfinance` is unaffiliated with Yahoo and that Yahoo Finance data is
  intended for personal use, subject to applicable terms.
- Never imply data licensing, guaranteed availability, real-time accuracy,
  production readiness, predictive benefit, or improved investment outcomes.
- Describe the multi-agent benefit as visible ownership, discovery, contract,
  traceability, and replaceability.

## Required checks

```bash
python -m pytest
python -m compileall -q prompits-lite phemacast-lite demos/data-agent-network-demo
```
