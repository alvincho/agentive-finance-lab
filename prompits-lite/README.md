# Prompits Lite

The smallest generic layer used by the demos:

- `Pit` identity and cards
- discoverable capabilities with generic input/output schemas
- a correlation trace
- in-memory `Plaza` registration, search, and invocation

It deliberately excludes networking, authentication, pools, durable state,
billing, and process management. It must not import from `phemacast_lite` or a
demo package.
