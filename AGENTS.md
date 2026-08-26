# Repository guardrails

This is a small public demonstration repository. Keep it understandable in one
reading session and runnable on a laptop.

## Dependency direction

```text
demos/data-agent-network-demo -> phemacast-lite -> prompits-lite
```

- `prompits-lite` owns only generic Pit identity, cards, traces, and Plaza
  registration/discovery/routing.
- `phemacast-lite` may import `prompits_lite` and owns only generic Pulse,
  Pulser, PersonaProfile, and Persona contracts.
- Demo packages may import both lite packages and own every finance-specific
  role, rule, fixture, label, and UI string.
- Reverse imports are not allowed.

## Public boundary

- Do not copy implementation files, schemas, configs, snapshots, generated
  artifacts, credentials, or personal data from FinMAS.
- Do not import `prompits`, `phemacast`, or `attas` from the original repository.
- Keep all sample data fictional, deterministic, and checked in.
- Do not add live vendor APIs, credential forms, investment advice, trading, or
  production claims to the first demo.
- Browser storage is not a source of truth. The current UI uses none.

## Concept ownership

- Preserve `Pit`, `Plaza`, `Pulser`, and `Persona` as recognizable concepts.
- Do not invent an acronym expansion for Pit.
- Keep `PersonaProfile` distinct from the runtime `Persona` class.
- A specialist must be discovered through Plaza metadata and a typed Pulse,
  never a hard-coded direct call from the Data User.

## UI

- Keep the main page compact and action-oriented.
- The trace, payload interpretation, source evidence, and degraded state must
  remain visible.
- Preserve keyboard labels, reduced-motion behavior, and text-safe DOM updates.
- Do not add `localStorage`, `sessionStorage`, or unsanitized `innerHTML`.

## Required checks

```bash
python -m pytest
python -m compileall -q prompits-lite phemacast-lite demos/data-agent-network-demo
```
