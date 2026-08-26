# Multi-Agent Finance Demos

Small, runnable demonstrations of multi-agent patterns for financial
applications from [Agentive Finance Lab](https://github.com/agentive-finance-lab).

The first demo is a **Data Agent Network** with two deliberately narrow roles:

- **Data User** preserves the human request, delegates specialist work, checks
  the response, and presents the result.
- **Data Consultant** ranks a checked-in fictional data catalog by coverage,
  freshness, cost, access, and reproducibility.

The point is not that more agents are automatically better. The demo makes four
specific benefits testable: separation of responsibility, capability-based
discovery, one visible correlation trace, and replaceable specialist roles.

## Architecture

```text
Browser
   |
   v
Data User Persona -- discover by PIT + Pulse --> Plaza
   ^                                              |
   |                                              v
   +------------ structured advice ------ Data Consultant Persona

Persona -> Pulser -> Pit
demo -> phemacast-lite -> prompits-lite
```

The vocabulary is intentionally retained:

| Concept | Lite contract |
| --- | --- |
| `Pit` | Smallest addressable identity with a card and capabilities. The name is not expanded as an acronym. |
| `Plaza` | In-memory registration, discovery, and routing plane. |
| `Pulser` | Pit that advertises named, typed Pulse handlers. |
| `Persona` | Role-aware Pulser with purpose and instructions. |

## Repository layout

```text
prompits-lite/                         generic Pit + Plaza contracts
phemacast-lite/                        generic Pulse + Pulser + Persona contracts
demos/
  data-agent-network-demo/             finance-specific roles, fixtures, API, and UI
docs/                                  architecture and public scope boundaries
tests/                                 contract, workflow, boundary, and API tests
```

## Run locally

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m data_agent_network_demo --open
```

Then visit [http://127.0.0.1:8000](http://127.0.0.1:8000).

For a source-checkout launch after installing the runtime dependencies:

```bash
python demos/data-agent-network-demo/run.py --open
```

## Verify

```bash
python -m pytest
python -m compileall -q prompits-lite phemacast-lite demos/data-agent-network-demo
```

The HTTP surface is intentionally small:

- `GET /health`
- `GET /api/about`
- `GET /api/network`
- `GET /api/examples`
- `POST /api/run`

Example:

```bash
curl -s http://127.0.0.1:8000/api/run \
  -H 'content-type: application/json' \
  -d '{"prompt":"Design a reproducible volatility check for ACME using daily closes."}'
```

## Deliberate limits

This repository is a teaching surface, not a production runtime and not a
drop-in replacement for FinMAS.

- no live market data or real vendor connectors
- no API keys, secrets, OAuth, or delegated accounts
- no LLM requirement
- no investment recommendations or trading actions
- no durable memory, database, browser storage, billing, or user accounts
- no distributed transport, authentication, leases, heartbeat, or failover
- no Phema/Phemar/Castr content runtime

Every financial name and catalog entry in the demo is fictional. See
[docs/SCOPE.md](docs/SCOPE.md) for the full boundary.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
