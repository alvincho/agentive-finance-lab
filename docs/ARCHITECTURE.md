# Architecture

## One process, real contracts, real retrieval

The first demo runs in one Python process so the entire collaboration remains
readable. The agents are separate runtime objects with advertised contracts;
they are not simulated chat transcripts.

```text
Demo UI or API client
  -> Plaza invokes comparison request on Data User Persona
    -> Data User validates primary symbol, benchmark symbol, and period
    -> Plaza searches for role=data-consultant plus the required Pulse
    -> Plaza invokes Data Consultant Persona
      -> yfinance adapter requests adjusted daily history for both symbols
      -> consultant aligns dates and calculates descriptive analytics
    <- structured histories, metrics, quality checks, and provenance
    -> Data User applies acceptance checks
  <- checked user-facing result plus end-to-end trace
```

One correlation id and `Trace` cross every hop. The trace shows which role owned
each decision and distinguishes discovery, retrieval, calculation, and
acceptance.

## Prompits Lite

`prompits_lite` is the lower layer.

- `PitAddress`: stable local identity
- `Capability`: advertised operation metadata with generic input/output schemas
- `PitCard`: public discovery view
- `Pit`: abstract addressable component
- `Plaza`: in-memory directory and router
- `Trace`: correlation-scoped sequence of observable events

Plaza has no awareness of finance, market symbols, `yfinance`, Pulse semantics,
or Persona roles.

## Phemacast Lite

`phemacast_lite` builds on Prompits Lite.

- `PulseSpec`: named field and runtime-type contract
- `Pulser`: Pit with input/output-validated Pulse handlers
- `PersonaProfile`: role, purpose, and instruction value object
- `Persona`: runtime Pulser carrying a `PersonaProfile`

Phemacast Lite has no finance-specific workflows or provider dependencies.

## Demo layer

The demo owns every finance-specific concern:

- structured security-versus-benchmark request validation;
- Data User and Data Consultant roles;
- the sole `yfinance` financial-data adapter;
- history normalization and date alignment;
- descriptive metrics, chart series, quality checks, and provenance;
- Data User acceptance and explicit provider-error behavior;
- FastAPI endpoints and the browser UI.

The Data User does not import or directly call the Data Consultant class during
a request. It searches Plaza metadata for an eligible Persona and routes the
typed Pulse through Plaza. The consultant owns provider I/O; the user agent owns
the final acceptance boundary.

## Source boundary

`yfinance` is the only runtime source of financial observations. The adapter
requests daily history with automatic adjustment, normalizes the provider
response into the demo's own small contract, and records query provenance.

Analytics operate only on that normalized contract. They do not call the
provider, scrape web pages, merge another feed, or estimate missing market
prices. If either required history cannot be retrieved, the collaboration
returns an explicit partial or unavailable result instead of silently using a
fixture, cache, stale result, synthetic series, or alternate provider.

Tests may inject deterministic histories through the same source protocol.
This verifies contracts and math without network flakiness; the test source is
not wired into the running application.

## What the architecture demonstrates

The multi-agent benefit is observable and deliberately modest:

1. **Ownership:** the Data User owns intent and acceptance; the Data Consultant
   owns retrieval and analysis.
2. **Discovery:** the user role selects a specialist by advertised role and
   capability, not a hard-coded object call.
3. **Contract:** the handoff is machine-checkable at the Pulse boundary.
4. **Traceability:** one trace connects the original request to provider query,
   calculations, checks, and presentation.
5. **Replaceability:** another implementation can satisfy the consultant Pulse
   without changing the user role. The first demo intentionally supplies only
   the `yfinance` implementation.

It does not demonstrate distributed agents, increased predictive accuracy,
autonomous investing, or production resilience.
