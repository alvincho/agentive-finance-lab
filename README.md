# Multi-Agent Finance Demos

Small, runnable demonstrations of multi-agent patterns for financial
applications from [Agentive Finance Lab](https://github.com/agentive-finance-lab).

The first demo answers one concrete question: how did a security behave against
a benchmark over a selected period? It uses two deliberately narrow agents and
one financial-data source:

- **Data User** accepts and validates the comparison request, discovers a
  specialist, checks the returned evidence, and presents the result.
- **Data Consultant** retrieves adjusted daily history through `yfinance`,
  aligns the two series, and calculates descriptive comparison metrics.

The demo does not claim that two agents improve arithmetic. It makes the useful
parts of collaboration visible: role ownership, capability-based discovery,
typed handoff, a shared trace, and a replaceable specialist contract.

## What it does

Choose a primary symbol, a benchmark symbol, and a period. The result includes:

- adjusted daily history for both symbols;
- aligned coverage and observation counts;
- period return, annualized volatility, and maximum drawdown;
- return spread, daily-return correlation, and beta;
- normalized chart points, recent observations, quality checks, provenance,
  and the complete agent trace.

`yfinance` is the only external financial-data source. The runtime does not
substitute fixtures, synthetic prices, cached results, or another provider when
retrieval fails; it reports the failure.

## Architecture

```text
Browser / JSON API
       |
       v
Data User Persona -- discover + invoke --> Plaza
       ^                                     |
       |                                     v
       +-- checked result -- Data Consultant Persona -- yfinance --> Yahoo Finance

Persona -> Pulser -> Pit
demo -> phemacast-lite -> prompits-lite
```

The vocabulary is intentionally retained:

| Concept | Lite contract |
| --- | --- |
| `Pit` | Smallest addressable identity with a card and capabilities. The name is not expanded as an acronym. |
| `Plaza` | In-memory registration, discovery, and routing plane. |
| `Pulser` | Pit that advertises named, typed Pulse handlers. |
| `Persona` | Role-aware Pulser with a purpose and instructions. |

## Repository layout

```text
prompits-lite/                         generic Pit + Plaza contracts
phemacast-lite/                        generic Pulse + Pulser + Persona contracts
demos/
  data-agent-network-demo/             Data User, Data Consultant, yfinance adapter, API, and UI
docs/                                  architecture and public scope boundaries
tests/                                 contract, workflow, boundary, API, and analytics tests
```

## Run locally

Python 3.11 or newer and an internet connection are required. No market-data API
key is needed.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m data_agent_network_demo --open
```

Then visit [http://127.0.0.1:8000](http://127.0.0.1:8000). Do not open the
checked-in HTML with a `file://` URL; the UI depends on the local API.

For a source-checkout launch after installing the dependencies:

```bash
python demos/data-agent-network-demo/run.py --open
```

## Try the API

```bash
curl -s http://127.0.0.1:8000/api/run \
  -H 'content-type: application/json' \
  -d '{"primary_symbol":"AAPL","benchmark_symbol":"SPY","period":"1y"}'
```

The intentionally small HTTP surface is:

- `GET /health`
- `GET /api/about`
- `GET /api/network`
- `GET /api/examples`
- `POST /api/run`

## Verify

```bash
python -m pytest
python -m compileall -q prompits-lite phemacast-lite demos/data-agent-network-demo
```

Deterministic tests use injected in-memory histories so ordinary test runs do
not depend on the network. Those histories are test doubles only; they are not
available to the application as a runtime fallback.

## Deliberate limits

This repository is an educational demonstration, not a production runtime, a
market-data service, or a drop-in replacement for FinMAS.

- no LLM is required and no claim of autonomous investment judgment is made;
- no recommendation, investment advice, portfolio construction, or trading;
- no data persistence, cache, database, browser storage, accounts, or secrets;
- no authentication, authorization, distributed transport, or failover;
- no alternate data-provider routing or runtime synthetic fallback;
- no public proxy, bulk download, redistribution, or production serving of
  Yahoo Finance data;
- no Phema, Phemar, Castr, content studio, or original FinMAS implementation.

`yfinance` is an open-source library that is not affiliated with, endorsed by,
or vetted by Yahoo. Its own documentation states that Yahoo Finance data is
intended for personal use only. Review the
[yfinance documentation](https://github.com/ranaroussi/yfinance) and applicable
Yahoo terms before use. See [docs/SCOPE.md](docs/SCOPE.md) for the complete
boundary.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
