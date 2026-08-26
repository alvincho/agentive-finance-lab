# Open-source scope and boundaries

## Included

The public repository includes only enough code to demonstrate:

- addressable Pit identities and public cards
- in-memory Plaza registration, discovery, and routing
- named, typed Pulse contracts
- role-aware Persona runtimes
- a two-Persona financial-data collaboration
- deterministic fixture ranking and a shared trace
- a compact browser UI and JSON API

The code is independently implemented for this repository.

## Explicitly excluded

### Production runtime

- HTTP agent-to-agent transport
- authentication, authorization, tokens, trust, or identity proof
- persistence, databases, leases, heartbeat, retries, or distributed failover
- billing, quoting, settlement, or economic coordination
- multi-tenant hosting, admin controls, or deployment automation

### Phemacast product surface

- Phema, Phemar, Castr, graph, map, rendering, and content-studio runtimes
- long-term Persona memory, RAG, social ingestion, voice cloning, or OAuth
- feedback learning, provider routing, or model configuration

### Financial product surface

- real data vendors, endpoints, catalogs, snapshots, or licensed descriptions
- live prices, filings, news, fundamentals, or macroeconomic observations
- credentials, BYOK flows, entitlements, or provider redistribution rights
- portfolio construction, orders, execution, or investment advice

## Security posture

The demo binds to localhost by default, accepts no secrets, writes no browser
storage, and keeps runtime state in memory. It should not be exposed as a public
service without replacing the omitted security and operational layers.

## Compatibility statement

The lite packages preserve conceptual vocabulary, not API compatibility. They
are not drop-in replacements for the original Prompits, Phemacast, or FinMAS
packages. Future additions should remain small enough to support a visible demo
benefit; production features belong elsewhere.
