---
series: Build a Multi-Agent Finance Lab
episode: 2 of 10
status: prepared
scheduled_at: 2026-09-01 20:00 Asia/Taipei
title: "Clone the Lab and Meet the Network"
subtitle: Start the reduced finance-agent network locally, verify its health, and find all three demos before learning the framework vocabulary.
preview: One clone, one Python environment, and one command are enough to start the Agentive Finance Lab and inspect its three Data Agent routes.
repository_url: "https://github.com/alvincho/agentive-finance-lab"
subscribe_url: "https://agentivefinancelab.substack.com/subscribe"
canonical_url: null
---

# Clone the Lab and Meet the Network

*Start the reduced finance-agent network locally, verify its health, and find
all three demos before learning the framework vocabulary.*

![A terminal-to-browser path: clone the Agentive Finance Lab repository, create a Python environment, run the local launcher, verify the health endpoint, and open the three Data Agent demos.](../media/02/02-launch-map.png)

*Figure 1. Episode 2 is deliberately practical: get one local result first.
The same host exposes a repository guide, three isolated demo routes, and a
machine-readable health check.*

Architecture is easier to understand after it runs.

That sounds obvious, but multi-agent projects often ask readers to absorb a
new vocabulary, deployment model, and diagram before they can see anything
work. Agentive Finance Lab takes the opposite route in Episode 2. We will
clone the repository, create an isolated Python environment, start the local
host, verify the first network, and locate all three demos.

You do not need an API key, database, Node.js installation, hosted agent
service, or model account for this walkthrough. You need Git, CPython 3.11 or
later, and internet access while installing the Python package.

The goal is not to prove production readiness. It is to produce one
observable local result that we can inspect in later episodes.

## The problem: a diagram is not a runnable boundary

An architecture diagram can make almost any system look coherent. Boxes have
names. Arrows point in the right direction. Failures do not appear.

A runnable repository is less forgiving. The package must install. The host
must start. Routes must resolve. Participants must register. A health endpoint
must report something concrete. If the system calls a provider, that boundary
must be visible rather than hidden behind a screenshot or fixture.

This lab is a reduced, runnable extraction from **FinMAS**, the original full
financial multi-agent application. It retains the parts of Prompits, Phemacast,
and the Data Agent Network needed for the demonstrations, while omitting
production services such as distributed transport, authentication, billing,
persistent memory, model routing, and user accounts.

“Reduced” matters. This is not a hosted financial-data product and not a claim
that a local process is production infrastructure. The point is to preserve a
real interaction boundary in a repository small enough to run and inspect.

## The concept: get one working result before the vocabulary

Episode 2 uses a simple test:

1. Can a reader install the repository in a clean environment?
2. Can one launcher start the local application?
3. Does `/health` report the first agent network as ready?
4. Can the reader locate the Single Source, Multiple Sources, and Real Data
   demos?

If those four checks pass, we have a stable base for the rest of the series.
Episode 3 can then explain why the dependency direction is
`demos → phemacast-lite → prompits-lite`. Episodes 4 and 5 can introduce Pit,
Plaza, Practice, Pulse, Pulser, and Persona without asking readers to trust a
diagram alone.

For now, you only need to notice the visible responsibilities:

- the **Data User** owns the request-facing interface;
- the **Data Consultant** owns source-catalog advice; and
- each **Data Source** owns its provider contract and execution boundary.

The local coordinator is called Plaza. The structured interactions are called
Pulses. We will open both concepts later; today, we only verify that the
participants start together and answer through the preserved application
surface.

## Repository walk-through: three files, not a grand tour

Begin with the repository root:

```text
agentive-finance-lab/
├── README.md
├── demos/data-agent-network-demo/
├── phemacast-lite/
└── prompits-lite/
```

Three files are enough for this episode.

### 1. `README.md`: the operator path

The root README is the source of truth for prerequisites, installation,
startup, route locations, and troubleshooting. It also states the project’s
limits: no trading, forecasts, provider failover, secret entry in the browser,
or guarantees about upstream data.

### 2. `demos/data-agent-network-demo/run.py`: the checkout launcher

The launcher adds the three local package roots to Python’s import path and
then delegates to the demo’s command-line entry point. That is why the same
command works from a source checkout before you learn the package internals:

```bash
python demos/data-agent-network-demo/run.py --open
```

The `--open` flag asks your default browser to open the landing page after the
server starts. If the browser does not open automatically, the host still runs
and you can visit `http://127.0.0.1:8000/` yourself.

### 3. `docs/SCOPE.md`: the honesty boundary

The scope document separates what the lab includes from what it deliberately
omits. Read it before interpreting a successful local run as a broader claim.
The demo shows explicit ownership, discovery, and request paths. It does not
show investment performance, production reliability, data entitlements, or
universal superiority over Model Context Protocol (MCP), skills, or a
single-agent application.

## Run it: clone, install, start, verify

### Check Python

On macOS or Linux:

```bash
python3 --version
```

On Windows:

```powershell
py -3 --version
```

The version must be 3.11 or later.

### Clone the repository

```bash
git clone https://github.com/alvincho/agentive-finance-lab.git
cd agentive-finance-lab
```

### Create an isolated environment

macOS or Linux with Bash or Zsh:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If PowerShell blocks activation, call the environment’s interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

### Start the lab

From the repository root, with the environment active:

```bash
python demos/data-agent-network-demo/run.py --open
```

Keep that terminal open. The process serves the lab until you stop it with
`Ctrl+C`.

Wait for the host to report:

```text
Uvicorn running on http://127.0.0.1:8000
```

### Verify the first network

In a second terminal:

```bash
curl --fail --silent http://127.0.0.1:8000/health
```

The compatibility health view reports the Single Source network:

```json
{
  "status": "ok",
  "demo": "data-agent-network",
  "participants": 3,
  "sources": 1,
  "provider": "yfinance"
}
```

This response is intentionally modest. It confirms that the local Demo 1
network started with three registered participants and one YFinance source. It
does not guarantee that Yahoo Finance is reachable, that a future live fetch
will succeed, or that any returned observation is current or suitable for a
particular use.

## Meet the three demos

The landing page links to three routes:

- **Demo 1 — Data Agent / Single Source:**
  `http://127.0.0.1:8000/demos/data-agent-network/`
- **Demo 2 — Data Agent / Multiple Sources:**
  `http://127.0.0.1:8000/demos/data-agent-network/multiple-sources/`
- **Demo 3 — Data Agent / Real Data:**
  `http://127.0.0.1:8000/demos/data-agent-network/real-data/`

Demo 1 registers Data User, Data Consultant, and a YFinance Data Source. Demo 2
registers the same user-facing and consultant roles with YFinance, Alpha
Vantage, and FRED sources, while keeping its UI catalog- and
specification-oriented. Demo 3 uses the same five-participant shape in an
isolated local Plaza and exposes bounded live-fetch samples.

You do not need provider keys to open any route, request catalog advice, or
inspect endpoint specifications. YFinance itself requires no key. Live Alpha
Vantage or FRED fetches require optional server-side keys in the gitignored
`.env`; keys never belong in browser storage or a Pulse request.

For the first interaction, open Demo 1 and ask:

```text
I need free daily prices and volume for AAPL.
```

The advice path searches synchronized endpoint documentation. It does not call
an upstream provider and does not run a language-model generation step. A
subsequent `data_fetch` request is the only action that crosses the provider
boundary.

That distinction will matter later. Today, simply confirm that advice and
execution are visibly separate actions.

## Troubleshooting without hiding the failure

If port 8000 is already in use, choose another port:

```bash
python demos/data-agent-network-demo/run.py --port 8010 --open
```

If Python reports `ModuleNotFoundError`, return to the repository root,
activate the intended environment, and run `python -m pip install -e .` again.

If the browser does not open, visit the local URL directly. If an upstream
provider later fails, keep the failure visible. The lab does not replace a
failed request with cached observations, synthetic prices, test fixtures, or a
different provider.

## Boundary and next step

You now have a local host, a machine-readable health result, and three demo
routes. That is the entire claim for Episode 2.

We have not yet explained why the repository contains two lite framework
layers, how a participant registers, how Plaza resolves it, or how a Pulse
crosses the local Practice boundary. We also have not claimed that a local
health result proves provider availability, data accuracy, security,
scalability, or production readiness.

In Episode 3, we will open the dependency direction and show why “lite” means a
boundary around a reduced extraction—not a rewrite of the original
architecture.

**Clone and run the lab:** https://github.com/alvincho/agentive-finance-lab#quick-start-clone-and-run-the-ui

**Subscribe to the series:** https://agentivefinancelab.substack.com/subscribe

---

*Agentive Finance Lab is an educational software demonstration. It does not
provide investment advice, trading recommendations, data rights, or guarantees
about provider availability, freshness, completeness, or accuracy. Live data
remains subject to each provider’s terms and limits.*
