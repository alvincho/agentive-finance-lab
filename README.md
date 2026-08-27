# Multi-Agent Finance Demos

Runnable, reduced demonstrations of multi-agent use cases for finance from
Agentive Finance Lab.

This repository is separate from FinMAS. It contains reduced copies of the
parts of Prompits, Phemacast, and the FinMAS Data Agent Network required to run
each demonstration. Lite means production infrastructure was removed; it does
not mean the agents, Plaza, Pulses, or application were redesigned.

## Ownership and provenance

Prompits, Phemacast, and Attas are owned by
[Retis AI Pte Ltd](https://retis.ai/). This public lab preserves a reduced
subset of their FinMAS architecture under the repository's Apache License 2.0;
private production configuration, credentials, datasets, runtime state, and
complete provider catalogs are not included.

## Quick start: clone and run the UI

These steps start the local repository guide and three reduced Data Agent
Network examples. Each example uses an in-process Plaza and reuses the same
Data User interface and agent contracts.

### 1. Check the prerequisites

You need:

- Git;
- CPython 3.11 or later; and
- internet access while installing packages. Live `data_fetch` requests also
  need access to the selected upstream provider.

No API key, database, Node.js installation, or external agent service is
required to start the demos or use catalog advice and endpoint
specifications. YFinance needs no key. Live Alpha Vantage and FRED
`data_fetch` calls require their optional server-side keys, described below.

Check Python before continuing:

```bash
python3 --version
```

On Windows, use `py -3 --version`. The reported version must be 3.11 or later.

### 2. Clone the repository

On the public repository page, select **Code**, select **HTTPS**, and copy the
clone URL, or run:

```bash
git clone https://github.com/alvincho/agentive-finance-lab.git
cd agentive-finance-lab
```

### 3. Create an isolated environment and install

macOS or Linux with Bash or Zsh:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

With another shell, or without activation, use the environment's interpreter
directly:

```bash
./.venv/bin/python -m pip install -e .
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If PowerShell does not allow activation, call the environment's Python
directly to install instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

### 4. Start the agents and UI

To run the keyed examples in Demo 3, copy the safe template and add your own
Alpha Vantage and/or FRED key before starting the application. Skip this step
for catalog advice, specifications, or the keyless first real-data sample:

```bash
cp .env.example .env
# Edit .env, then set one or both blank values:
# ALPHA_VANTAGE_API_KEY=your-key
# FRED_API_KEY=your-key
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
# Edit .env, then set one or both blank values.
```

Keys stay on the server side. The UI has no credential fields, and provider
secrets are not Pulse inputs. Restart the server after changing `.env`.
Existing process environment variables take precedence over `.env`.
Obtain keys from the providers: [Alpha Vantage free-key
page](https://www.alphavantage.co/support/#api-key) and [FRED API-key
documentation](https://fred.stlouisfed.org/docs/api/api_key.html).

Run this command from the repository root with the environment activated:

```bash
python demos/data-agent-network-demo/run.py --open
```

Without activation, use the matching environment interpreter:

```bash
./.venv/bin/python demos/data-agent-network-demo/run.py --open
```

```powershell
.\.venv\Scripts\python.exe demos\data-agent-network-demo\run.py --open
```

The command keeps running while the demo is available. `--open` asks the
computer's default browser to open the landing page. Wait until the terminal
reports:

```text
Uvicorn running on http://127.0.0.1:8000
```

If the browser does not open, visit the URLs below manually:

- `http://127.0.0.1:8000/` — repository purpose and framework guide;
- `http://127.0.0.1:8000/demos/data-agent-network/` — Demo 1, Data Agent /
  Single Source;
- `http://127.0.0.1:8000/demos/data-agent-network/multiple-sources/` — Demo 2,
  Data Agent / Multiple Sources;
- `http://127.0.0.1:8000/demos/data-agent-network/real-data/` — Demo 3, Data
  Agent / Real Data; and
- `http://127.0.0.1:8000/health` — machine-readable network health.

Stop the demo with <kbd>Ctrl</kbd>+<kbd>C</kbd> in the terminal that started it.

### 5. Verify the agent network

In a second terminal, request the health endpoint:

```bash
curl --fail --silent http://127.0.0.1:8000/health
```

If `curl` is unavailable, open `http://127.0.0.1:8000/health` in a browser.

The compatibility health view verifies Demo 1 and reports its three registered
participants and one YFinance source:

```json
{
  "status": "ok",
  "demo": "data-agent-network",
  "participants": 3,
  "sources": 1,
  "provider": "yfinance"
}
```

Then open the Data User chat and try:

```text
I need free daily prices and volume for AAPL.
```

The advice path uses the Consultant's synchronized catalog and does not call an
upstream provider. Only a subsequent `data_fetch` request performs live
provider I/O.

### Troubleshooting

- **Port 8000 is already in use:** start with
  `python demos/data-agent-network-demo/run.py --port 8010 --open` and use port
  `8010` in the URLs.
- **`ModuleNotFoundError`:** confirm the virtual environment is active and run
  `python -m pip install -e .` again from the repository root.
- **PowerShell activation is blocked:** use
  `.\.venv\Scripts\python.exe demos\data-agent-network-demo\run.py --open` without
  activation.
- **Ubuntu reports that `venv` is unavailable:** install the matching operating
  system package, such as `python3.11-venv`, then recreate `.venv`.
- **You opened `index.html` directly:** the checked-in page can describe the
  project, but the agents and API require the Python server. Use the `http://`
  URLs printed by the launcher, not a `file://` URL, to run the demo.
- **The UI loads but a live fetch fails:** check internet access and provider
  availability, and confirm the optional server-side key is set when fetching
  from Alpha Vantage or FRED. Catalog advice, schemas, and the Plaza demo do not
  require a successful live market-data response.

## Demo 1: Data Agent / Single Source

This first example runs a reduced version of the original Data Agent Network
with its three-participant design and YFinance as the only financial-data
source:

- **Data User Persona** owns the user chat and selected-source access.
- **Data Consultant Persona** synchronizes source documentation and answers
  source-selection questions from its in-memory catalog.
- **YFinance Data Source Pulser** documents and executes the supported yfinance
  operations.

The Data Consultant never proxies market data. It reports source status and
catalog-grounded advice. After source resolution, the Data User invokes the
YFinance Data Source directly.

```text
Advice
Browser
  -> Data User:data_request
  -> Data Consultant:data_advice
  -> catalog memory

Direct source contract retained by the network
Data User
  -> Data Consultant:data_source_status
  <- YFinance identity and address
  -> YFinance Data Source:data_spec or data_fetch
```

Demo 1 remains YFinance-only. Its route, three participants, Pulse surfaces,
and direct-source behavior are preserved when Demos 2 and 3 are enabled.

## Demo 2: Data Agent / Multiple Sources

The second example keeps the same Data User, Data Consultant, Plaza, Persona,
and Pulse workflow while registering three independent source Pulsers. Its five
participants are:

- **Data User Persona**;
- **Data Consultant Persona**;
- **YFinance Data Source Pulser**;
- **Alpha Vantage Data Source Pulser**; and
- **FRED Data Source Pulser**.

At startup, each source registers with Plaza. The Consultant discovers all
three by their cards and synchronizes their endpoint and field documentation
through `data_availability`. A chat request calls `data_advice`, which searches
that transient multi-source catalog. It does not fetch market or economic
observations.

```text
Advice
Browser
  -> Data User:data_request
  -> Data Consultant:data_advice
  -> synchronized YFinance + Alpha Vantage + FRED catalog memory

Direct source access
Data User
  -> Data Consultant:data_source_status
  <- selected source identity and address
  -> selected Data Source:data_spec or data_fetch
```

The agents retain both direct-source contracts. Demo 2's UI exposes catalog
advice and `data_spec` only; Demo 3 exposes the existing live `data_fetch`
path. The Consultant and Plaza do not proxy, merge, cache, or fall back between
provider responses. Missing provider keys and upstream failures remain explicit
errors. The canonical local UI route is
`/demos/data-agent-network/multiple-sources/`.

Try these catalog-only questions and inspect the resulting endpoint
specifications:

- `Which sources provide daily AAPL prices and volume?`
- `Which source provides U.S. CPI observations and revision vintage dates?`
- `Compare AAPL profile, sector, industry, and market-cap data.`

## Demo 3: Data Agent / Real Data

The third example reuses the same five roles, Plaza discovery, Pulses, source
catalogs, and direct-source path as Demo 2. Its UI makes the existing live
`data_fetch` controls explicit and provides three bounded samples:

1. **Public source versus missing key** calls YFinance `ticker.history` for
   AAPL and then Alpha Vantage `time_series_daily`. With the repository's
   default keyless setup and Yahoo Finance reachable, YFinance returns live AAPL
   history while Alpha Vantage deterministically returns
   `authentication_required`.
2. **Bring your own Alpha Vantage key** asks the visitor to set
   `ALPHA_VANTAGE_API_KEY` in `.env`, restart the server, and repeat the two
   direct calls. The source responses remain separate; the browser does not
   merge or proxy them.
3. **FRED observations** asks the visitor to obtain a free FRED API key, set
   `FRED_API_KEY`, restart, and fetch a bounded set of `CPIAUCSL` observations
   from the FRED source.

The canonical route is `/demos/data-agent-network/real-data/`. Each browser
request retains the existing Pulse envelope. Data User first resolves source
status through Data Consultant and then invokes the selected Data Source
directly. If a key is already configured, Sample 1 truthfully reports that the
Alpha Vantage call may succeed instead of simulating a missing-key failure.

## Original framework spine

```text
Pit
  -> BaseAgent
    -> StandbyAgent
      -> Pulser
        -> Persona

Plaza coordinates registration, search, and UsePractice by composition.
```

The Lite packages retain the original public concepts and method names:

| Layer | Retained surface |
| --- | --- |
| Prompits Lite | `PitAddress`, `Pit`, `Practice`, `Message`, `BaseAgent`, `StandbyAgent`, `Plaza`, `search`, `UsePractice` |
| Phemacast Lite | `Pulse`, `PulsePractice`, `GetPulseDataPractice`, `Pulser`, `Persona`, `RAGPersona`, `supported_pulses`, `get_pulse_data` |
| Data Agent Network | `DataUserPersona`, `DataConsultantPersona`, source `Pulser` implementations, `DemoQuestion`, demo harnesses |

The demos omit distributed HTTP transport between agents, user authentication,
UI credential collection, leases, heartbeat/reconnect loops, persistent
Pool/Persona memory, billing, hosted services, model routing, settings, and
feedback learning. The two optional provider keys exist only in the server
environment loaded from process variables or the ignored repository-root
`.env` for live Demo 3 fetches.

## Pulse surface

| Participant | Pulses |
| --- | --- |
| Data User | `data_request`, `data_source_status`, `data_spec`, `data_fetch` |
| Data Consultant | `data_advice`, `data_source_status` |
| YFinance Data Source | `data_spec`, `data_availability`, `data_fetch` |
| Alpha Vantage Data Source | `data_spec`, `data_availability`, `data_fetch` |
| FRED Data Source | `data_spec`, `data_availability`, `data_fetch` |

The browser uses the original Data User envelope:

```json
{
  "pulse_name": "data_request",
  "input": {
    "query": "I need daily historical prices and volume for AAPL"
  }
}
```

## Call a Pulse directly

Example Demo 1 Pulse request:

```bash
curl -s http://127.0.0.1:8000/api/pulse \
  -H 'content-type: application/json' \
  -d '{"pulse_name":"data_request","input":{"query":"historical AAPL prices and volume"}}'
```

Each demo preserves the same Pulse-envelope boundary:

| Demo | Pulse | Bootstrap | Health |
| --- | --- | --- | --- |
| 1 | `POST /api/pulse` | `GET /api/data-user/bootstrap` | `GET /health` |
| 2 | `POST /api/multiple-sources/pulse` | `GET /api/multiple-sources/data-user/bootstrap` | `GET /api/multiple-sources/health` |
| 3 | `POST /api/real-data/pulse` | `GET /api/real-data/data-user/bootstrap` | `GET /api/real-data/health` |

## Reduced source catalogs

All three demos keep the same three entries from the reduced YFinance
endpoint snapshot:

- `yfinance.ticker.history`
- `yfinance.ticker.fast_info`
- `yfinance.ticker.info`

Demos 2 and 3 add only these reduced operations:

| Source | Operations |
| --- | --- |
| Alpha Vantage | `time_series_daily`, `global_quote`, `overview` |
| FRED | `series/observations`, `series/vintagedates` |

Catalog synchronization, advice, source status, and specification do not call
the providers and work without API keys. Only `data_fetch` performs provider
I/O. Failures are returned explicitly; the runtime has no fixture, response
cache, synthetic value, cross-source fallback, or advisory-agent proxy.

## Repository layout

```text
prompits-lite/                  reduced original agent and Plaza runtime
phemacast-lite/                 reduced original Pulse, Pulser, and Persona runtime
demos/
  data-agent-network-demo/      single-source, multi-source, and real-data views with one reused Data User UI
docs/                           architecture and public-scope boundaries
tests/                          deterministic tests with injected provider doubles
```

Dependency direction is one way:

```text
demos/* -> phemacast-lite -> prompits-lite
```

## Important data notice

This is an educational localhost demonstration, not an investment, trading, or
production data service. `yfinance` is not affiliated with, endorsed by, or
vetted by Yahoo. Yahoo Finance data is intended for personal use and remains
subject to Yahoo's terms and the yfinance project documentation. Alpha Vantage
and FRED access remains subject to their respective API terms, entitlements,
and limits. This repository grants no provider-data rights. Availability,
freshness, fields, and provider behavior are not guaranteed.

Apache-2.0. See [LICENSE](LICENSE), [NOTICE](NOTICE), and
[docs/SCOPE.md](docs/SCOPE.md).
