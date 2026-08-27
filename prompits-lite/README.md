# Prompits Lite

A faithful in-process reduction of the original Prompits agent runtime.
Prompits is owned by [Retis AI Pte Ltd](https://retis.ai/).

Retained from the original implementation:

- `PitAddress` and `Pit` identity;
- `Practice` and `Message`;
- `BaseAgent` and `StandbyAgent`;
- original-shaped agent cards and Practice metadata;
- Plaza registration and search result shapes;
- `search`, `lookup_agent_info`, `lookup_agent`, and `send`;
- `UsePractice` and `UsePracticeAsync`.

The Lite Plaza resolves registered Pit addresses and dispatches Practices in one
process. Distributed HTTP transport, authentication, persistence, policy,
billing, leases, heartbeat, and process hosting are omitted.

Prompits Lite has no Phemacast, finance, or Data Agent Network concepts.
