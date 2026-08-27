# Architecture

This repository extracts and reduces the existing FinMAS architecture. The
rule for every reduction is: preserve the original interface and execution
path, then remove services the demo does not need.

Prompits, Phemacast, and Attas are owned by
[Retis AI Pte Ltd](https://retis.ai/). The source mapping below records how
their FinMAS components correspond to this public reduction.

## Dependency layers

```text
demos/* -> phemacast-lite -> prompits-lite
```

Prompits Lite contains no Persona, content, or finance concepts. Phemacast Lite
contains no finance concepts. The Data Agent Network demo owns all financial
roles, Pulses, endpoint contracts, source execution, and UI copy.

## Source mapping

| Reduced module | FinMAS source |
| --- | --- |
| `prompits_lite.pit` | `prompits/core/pit.py` |
| `prompits_lite.practice` | `prompits/core/practice.py` |
| `prompits_lite.message` | `prompits/core/message.py` |
| `prompits_lite.agent` | `prompits/agents/base.py`, `standby.py` |
| `prompits_lite.plaza` | Prompits Plaza register/search/routing behavior |
| `prompits_lite.directory_runtime` | `prompits/core/directory_runtime.py` |
| `phemacast_lite.pulser` | `phemacast/agents/pulser.py`, `practices/pulser.py` |
| `phemacast_lite.persona` | `phemacast/agents/persona.py` |
| `phemacast_lite.pulse_runtime` | `phemacast/core/pulse_runtime.py` thin wrapper |
| demo agents and sources | `attas/data_agent_network/scaffold/` |
| demo UI | `attas/data_agent_network/ui/` |

The standalone repository does not import the original packages at runtime.

## Runtime inheritance

```text
Pit
  -> BaseAgent
    -> StandbyAgent
      -> Pulser
        -> Persona
          -> RAGPersona
```

Plaza is a coordinator, not a superclass. It holds original-shaped agent cards,
supports the original search filters, resolves Pit addresses, and dispatches a
registered Practice when an agent calls `UsePractice`.

Each Pulser advertises `GetPulseDataPractice`. Its supported Pulses remain
dictionaries in `agent_card.meta.supported_pulses`. A network call retains the
original shape:

```python
caller.UsePractice(
    "get_pulse_data",
    {"pulse_name": pulse_name, "params": input_data},
    pit_address=target,
)
```

The target Pulser resolves the Pulse definition and runs
`get_pulse_data -> fetch_pulse_payload`.

## Demo networks

The application contains three reduced examples. Each creates its own
in-process Plaza so participant names and catalogs remain scoped to that demo.

- **Demo 1: Data Agent / Single Source** registers three participants: Data
  User Persona, Data Consultant Persona, and YFinance Data Source Pulser.
- **Demo 2: Data Agent / Multiple Sources** registers five participants: Data
  User Persona, Data Consultant Persona, and YFinance, Alpha Vantage, and FRED
  Data Source Pulsers.
- **Demo 3: Data Agent / Real Data** instantiates the same existing five-agent
  network and makes its bounded live-fetch path explicit in the shared UI.

Demos 2 and 3 reuse the same `MultipleSourceDataAgentNetworkDemo`, Data User
and Data Consultant Persona implementations, Plaza search, Pulse contracts,
catalog synchronization, and direct-source path. Demo 2 emphasizes catalog and
specification comparison; Demo 3 exposes the existing live-fetch controls.
Demo 1's three-participant network, YFinance-only catalog, and routes remain
unchanged.

## Startup sequence

Demo 1 starts in this order:

```text
1. Create in-process Plaza
2. Create and register YFinanceDataSource
3. Create and register DataConsultantPersona
4. Consultant searches Plaza for the Data Source
5. Consultant calls data_availability with query=""
6. Consultant stores endpoint/field documentation in transient RAG memory
7. Create and register DataUserPersona
```

Demos 2 and 3 follow the same sequence with three source Pulsers:

```text
1. Create in-process Plaza
2. Create and register YFinanceDataSource
3. Create and register AlphaVantageDataSource
4. Create and register FREDDataSource
5. Create and register DataConsultantPersona
6. Consultant searches Plaza for all Data Sources
7. Consultant calls each source's data_availability with query=""
8. Consultant stores all endpoint/field documents in transient RAG memory
9. Create and register DataUserPersona
```

The empty query is the original complete-catalog synchronization convention.
It is not a separate synchronization Pulse.

## Advisory sequence

```text
Browser POST configured Pulse endpoint, pulse_name=data_request
  -> DataUserPersona.get_pulse_data
  -> DataUserPersona.data_request
  -> Plaza search for Data Consultant
  -> UsePractice(get_pulse_data, pulse_name=data_advice)
  -> DataConsultantPersona.data_advice
  -> lexical retrieval over synchronized endpoint/field documents
  -> original-shaped advice response
```

No provider I/O occurs. The public reduction omits the original optional LLM,
embeddings, persistent memory, settings, and feedback learning.

## Direct-source sequence

```text
Browser POST configured Pulse endpoint, pulse_name=data_spec or data_fetch
  -> DataUserPersona
  -> Data Consultant:data_source_status
  <- selected source card and Pit address
  -> selected Data Source:data_spec or data_fetch
```

`data_spec` reads the selected source's reduced bundled catalog. `data_fetch`
alone calls that source's provider boundary. The Consultant and Plaza do not
proxy, merge, cache, or fall back between provider requests or responses.

Demo 1 always resolves YFinance. Demos 2 and 3 can resolve YFinance, Alpha
Vantage, or FRED. The reduced operations are:

| Source | Operations |
| --- | --- |
| YFinance | `ticker.history`, `ticker.fast_info`, `ticker.info` |
| Alpha Vantage | `time_series_daily`, `global_quote`, `overview` |
| FRED | `series/observations`, `series/vintagedates` |

`ALPHA_VANTAGE_API_KEY` and `FRED_API_KEY` are optional server-side
environment variables read only by the owning source during live `data_fetch`.
The host loads an ignored repository-root `.env` without overriding existing
process variables. Catalog synchronization, advice, source status, and
`data_spec` do not require keys. The browser receives boolean readiness only,
has no credential fields, and secrets do not enter a Pulse request, response,
or log.

## HTTP host and UI

FastAPI only hosts the standalone repository shell and the Data User Persona's
application boundary:

- `/` — repository landing page
- `/demos/data-agent-network/` and `/data-user` — Demo 1 copied/reduced Data
  User UI
- `/demos/data-agent-network/multiple-sources/` — canonical Demo 2 Data User UI
- `/demos/data-agent-network/real-data/` — canonical Demo 3 Data User UI
- `/data-user-static/*` — original-named UI assets
- `POST /api/pulse` — preserved Demo 1 Data User Pulse envelope
- `/api/data-user/bootstrap` — reduced Data User bootstrap
- `POST /api/multiple-sources/pulse` and `POST /api/real-data/pulse` — the same
  Data User Pulse envelope for Demos 2 and 3
- `/api/multiple-sources/data-user/bootstrap` and
  `/api/real-data/data-user/bootstrap` — safe source/readiness bootstrap views
- `/health`, `/api/multiple-sources/health`, and `/api/real-data/health` —
  isolated localhost process/network health views

The original `index.html`, `data-user.css`, and `data-user.js` are the shared UI
baseline for all three demos. Reduction removes settings, credential entry,
history, ratings, LLM controls, and vendor-direct bypasses; it retains the chat,
requirements, source advice, endpoint specification, fetch form, and result
rendering. Demo 2 configures the interface for three catalog sources and hides
live execution in its catalog-oriented view. Demo 3 configures that same
interface with three bounded live samples; it does not fork a new chat
application. A compact Agentive Finance Lab frame sits outside that application
surface, identifies the active demo, and links back to the Lab, framework
overview, and demo catalog without becoming another participant.

## Removed production infrastructure

- separate agent processes and HTTP servers
- Plaza authentication, leases, tokens, relay, and billing
- heartbeat/reconnect and process management
- Pool and Persona persistence
- mailbox transport beyond the local compatibility Practice
- complete provider catalogs and ingestion jobs
- background/scheduled synchronization
- LLM/model routing and embeddings
- user accounts, UI credential collection, persisted secrets, settings, and
  feedback learning

These omissions do not change the ownership of work, Pulse names, Plaza search,
or the Data User-to-Consultant-to-source routing rules.
