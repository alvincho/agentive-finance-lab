# Architecture

## One process, real contracts

The first demo runs in one Python process so a reader can understand it without
containers or service orchestration. The roles are still separate runtime
objects with advertised contracts:

```text
Demo UI client
  -> Plaza.invoke(data_request)
    -> Data User Persona
      -> Plaza.search(PIT=Persona, role=data-consultant, Pulse=data_advice)
      -> Plaza.invoke(data_advice)
        -> Data Consultant Persona
      <- structured source evidence
    <- validated user-facing result
```

One `Trace` and correlation id cross every hop.

## Prompits Lite

`prompits_lite` is the lower layer.

- `PitAddress`: stable local identity
- `Capability`: advertised operation metadata with generic input/output schemas
- `PitCard`: public discovery view
- `Pit`: abstract addressable component
- `Plaza`: in-memory directory and router
- `Trace`: correlation-scoped sequence of observable events

Plaza has no awareness of financial requests, Pulse semantics, or Persona roles.

## Phemacast Lite

`phemacast_lite` builds on Prompits Lite.

- `PulseSpec`: named field and runtime-type contract
- `Pulser`: Pit with input/output-validated Pulse handlers
- `PersonaProfile`: role, purpose, and instructions value object
- `Persona`: runtime Pulser carrying a PersonaProfile

## Demo layer

The demo contains all financial behavior:

- deterministic prompt interpretation
- fictional data-product catalog
- transparent, rule-based product scoring
- Data User acceptance and degraded result logic
- FastAPI endpoints and the browser UI

The Data User never imports or directly calls the Data Consultant class during a
request. It searches Plaza for a `Persona` card with role `data-consultant` and
capability `data_advice`, then routes through Plaza.

## Why the trace matters

The UI makes architectural claims observable:

1. The Data User emits its interpreted needs.
2. Plaza records the discovery query and match.
3. Plaza records the routed Pulse call.
4. The consultant records execution and structured output.
5. The Data User records validation and presentation.

The offline toggle removes the consultant registration. The same Data User then
returns an explicit degraded response instead of inventing a recommendation.
