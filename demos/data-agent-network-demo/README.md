# Data Agent demos

This package contains three reduced examples of the FinMAS Data Agent Network.
All keep the original Plaza behavior, Pulse names, Persona roles,
direct-source path, application boundary, and Data User interface while
removing production-only services.

Attas, Phemacast, and Prompits are owned by
[Retis AI Pte Ltd](https://retis.ai/).

## Demo 1: Data Agent / Single Source

Demo 1 is the YFinance-only reduction. It has exactly three participants:

1. `YFinanceDataSource(Pulser)` registers its source card and three Pulses.
2. `DataConsultantPersona(RAGPersona)` registers, Plaza-searches for
   `pit_type=DataSource`, `party=attas`, and `pulse_name=data_availability`, then
   synchronizes the source catalog using an empty-query `data_availability`
   request.
3. `DataUserPersona(RAGPersona)` registers and exposes the original Data User
   Pulse surface to the browser.

All cross-participant calls use the original reduced mechanism:

```python
agent.UsePractice(
    "get_pulse_data",
    {"pulse_name": "data_advice", "params": payload},
    pit_address=target,
)
```

There is no `DemoClient`, `DemoNetwork`, custom capability protocol, or custom
trace workflow. The original `DataAgentNetworkDemo` and `DemoQuestion` harness
remain the programmatic entry points.

Demo 1's registration order, three participants, YFinance-only catalog, Pulse
surfaces, and direct-source behavior remain unchanged by Demos 2 and 3.

## Demo 2: Data Agent / Multiple Sources

Demo 2 duplicates the same reduced application design and expands only the
source set. Its one Plaza contains exactly five registered participants:

1. `YFinanceDataSource(Pulser)`;
2. `AlphaVantageDataSource(Pulser)`;
3. `FREDDataSource(Pulser)`;
4. `DataConsultantPersona(RAGPersona)`; and
5. `DataUserPersona(RAGPersona)`.

The three source agents register the same `data_spec`, `data_availability`, and
`data_fetch` Pulse surfaces. The Consultant Plaza-searches for all three source
cards and synchronizes their reduced documentation with the same empty-query
`data_availability` convention used by Demo 1. The User and Consultant are the
same reduced Persona implementations; Demo 2 does not introduce a second
workflow, custom router, or provider-comparison service. Demo 2's UI exposes
catalog advice and `data_spec`; Demo 3 exposes the retained live `data_fetch`
contract.

## Demo 3: Data Agent / Real Data

Demo 3 instantiates the existing `MultipleSourceDataAgentNetworkDemo` in its
own Plaza and reuses the same five participants and Pulse paths. It changes the
UI emphasis from catalog comparison to bounded live `data_fetch` calls; it
does not introduce another workflow or provider service.

The three samples are:

1. fetch AAPL history from YFinance and attempt the matching Alpha Vantage
   endpoint without a key; with Yahoo Finance reachable, the first call
   completes and the second returns an explicit `authentication_required`
   result;
2. add `ALPHA_VANTAGE_API_KEY` to the repository-root `.env`, restart, and call
   both source agents separately; and
3. obtain a free FRED API key, add `FRED_API_KEY`, restart, and fetch twelve
   `CPIAUCSL` observations from FRED.

The browser submits one normal `data_fetch` Pulse per source. It does not merge
responses, carry keys, or add a provider-comparison endpoint.

## Run

From the repository root:

```bash
python -m pip install -e .
python demos/data-agent-network-demo/run.py --open
```

The landing page is at `/`. Demo 1's Data User application remains at
`/demos/data-agent-network/` and `/data-user`. Demo 2 uses the canonical route
`/demos/data-agent-network/multiple-sources/`. Demo 3 uses
`/demos/data-agent-network/real-data/`. The outer Agentive Finance Lab
frame identifies the active demo and links to Lab home, the framework overview,
and the demo catalog; the copied Data User application remains inside that
frame for all three examples.

## HTTP boundary

The copied/reduced Data User JavaScript keeps one Pulse-envelope boundary per
demo. Demo 1's endpoint is:

```http
POST /api/pulse
content-type: application/json
```

```json
{
  "pulse_name": "data_request",
  "input": {
    "query": "Which YFinance endpoint provides daily AAPL prices and volume?",
    "use_case": "research prototype",
    "preferences": {"cost": "free or low cost"}
  }
}
```

The server returns the original wrapper:

```json
{"status": "success", "result": {}}
```

The three API boundaries are:

| Demo | Pulse | Bootstrap | Health |
| --- | --- | --- | --- |
| 1 | `POST /api/pulse` | `GET /api/data-user/bootstrap` | `GET /health` |
| 2 | `POST /api/multiple-sources/pulse` | `GET /api/multiple-sources/data-user/bootstrap` | `GET /api/multiple-sources/health` |
| 3 | `POST /api/real-data/pulse` | `GET /api/real-data/data-user/bootstrap` | `GET /api/real-data/health` |

Demos 2 and 3 use the same `pulse_name` plus `input` envelope at their API
bases. They must not replace that boundary with separate chat, specification,
fetch, or provider REST workflows.

## Shared Pulse paths

Advice:

```text
Data User:data_request
  -> Plaza search for Data Consultant
  -> Data Consultant:data_advice
  -> synchronized catalog memory
```

Specification or data:

```text
Data User:data_spec or data_fetch
  -> Data Consultant:data_source_status
  <- source identity and address
  -> selected Data Source:data_spec or data_fetch
```

In Demo 1, the selected source is always YFinance. In Demos 2 and 3, it can be
YFinance, Alpha Vantage, or FRED. The Consultant never receives a provider
payload. `data_request`, `data_source_status`, and `data_spec` perform no
provider I/O.

## Supported source operations

| Endpoint ID | yfinance operation | Purpose |
| --- | --- | --- |
| `yfinance.ticker.history` | `Ticker.history` | historical OHLCV and events |
| `yfinance.ticker.fast_info` | `Ticker.fast_info` | compact quote metadata |
| `yfinance.ticker.info` | `Ticker.info` | company profile and fundamentals |

Demos 2 and 3 add only the following operations:

| Source | Reduced operations |
| --- | --- |
| Alpha Vantage | `time_series_daily`, `global_quote`, `overview` |
| FRED | `series/observations`, `series/vintagedates` |

`ALPHA_VANTAGE_API_KEY` and `FRED_API_KEY` are optional server-side
environment variables. Copy `.env.example` to the ignored `.env`, fill only
the key you want to use, and restart. Existing process variables take
precedence. Keys are read only inside the owning source Pulser when a live
`data_fetch` executes. Catalog synchronization, advice, source status, and
`data_spec` work without keys. Missing keys produce explicit fetch errors; the
UI has no credential fields and provider secrets are never Pulse inputs.

## Intentionally omitted

- providers beyond YFinance, Alpha Vantage, and FRED
- complete production endpoint snapshots
- per-agent HTTP servers and distributed transport
- authentication, credential storage or UI entry, billing, leases, and heartbeat
- persistent memory, scheduled catalog refresh, embeddings, and LLM synthesis
- settings, UI/API credential entry, prompt history, feedback learning, and
  vendor-direct mode
- provider caches, synthetic results, and fallback data

`yfinance` is unaffiliated with Yahoo. Yahoo Finance data is intended for
personal use and is subject to applicable terms. This demo does not provide
investment advice or guarantee availability, freshness, or accuracy. Alpha
Vantage and FRED access remains subject to their respective API terms and
limits; this repository grants no provider-data rights.
