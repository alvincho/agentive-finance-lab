# Open-source scope and boundaries

## Purpose

This public repository contains only enough framework and application code to
make one multi-agent benefit inspectable: a Data User delegates specialized
market-data work to a discoverable Data Consultant through a typed contract,
then checks the evidence before presenting it.

## Included

- addressable Pit identities and public cards;
- in-memory Plaza registration, discovery, and routing;
- named, typed Pulse contracts;
- role-aware Persona runtimes;
- one Data User and one Data Consultant;
- a security-versus-benchmark historical comparison;
- live adjusted daily history through `yfinance` as the only financial-data
  source;
- deterministic descriptive analytics and quality checks;
- request and provider provenance with a shared trace;
- a compact localhost browser UI and JSON API;
- injected deterministic test histories that are never runtime fallbacks.

The lite packages and demo are independently implemented for this repository.
They preserve selected architectural vocabulary, not private product code.

## Explicitly excluded

### Production runtime

- HTTP agent-to-agent transport or distributed execution;
- authentication, authorization, tokens, identity proof, or trust systems;
- persistence, databases, durable queues, caching, leases, heartbeat, agent-level
  retries, or failover orchestration (the yfinance adapter permits one bounded
  library retry for a transient connection failure);
- user accounts, tenancy, billing, settlement, admin controls, or deployment
  automation;
- a hosted market-data API, public proxy, bulk collection service, or service-
  level guarantees.

### Phemacast product surface

- Phema, Phemar, Castr, graph, map, rendering, and content-studio runtimes;
- long-term Persona memory, RAG, social ingestion, voice, or delegated OAuth;
- feedback learning, model routing, or model-provider configuration.

### Financial product surface

- any financial-data provider other than `yfinance`;
- alternate-provider routing, failover, scraping, or feed reconciliation;
- runtime fixture, synthetic, generated, stale, or cached price fallback;
- live streaming quotes, order books, filings, news, fundamentals, macro series,
  licensed vendor catalogs, or proprietary datasets;
- credential collection, entitlements, redistribution, resale, or public serving
  of provider data;
- forecasts, signals, personalized recommendations, portfolio construction,
  orders, execution, risk approval, or investment advice.

## Data-use boundary

The application calls `yfinance`, an unaffiliated open-source library, for
historical Yahoo Finance data. The project does not grant data rights. The
`yfinance` project states that Yahoo Finance data is intended for personal use
only; users are responsible for reviewing the library documentation and all
applicable provider terms.

The demo is intended for education and personal experimentation. It should not
be deployed as a public data service, used to redistribute responses, or relied
upon for production financial decisions.

## Failure behavior

Provider, network, rate-limit, symbol, or coverage failures are expected
operational outcomes. The runtime must expose them as errors or an unavailable
result with trace evidence. It must never invent values or hide a failure behind
test data, another source, a previous run, or browser state.

## Security posture

The demo binds to localhost by default, accepts no provider secrets, writes no
browser storage, and persists no retrieved history. It lacks the security and
operational controls required for internet exposure.

## Compatibility statement

Prompits Lite and Phemacast Lite preserve concepts, not API compatibility. They
are not drop-in replacements for the original Prompits, Phemacast, or FinMAS
packages. Future additions should remain small enough to make a specific demo
benefit visible; production features belong outside this repository.
