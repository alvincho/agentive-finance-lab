# Data Agent Network Demo

A compact, inspectable collaboration between a Data User and a Data Consultant.
The task is intentionally narrow: compare one security with one benchmark using
real adjusted daily history retrieved through `yfinance`.

## Agent responsibilities

1. **Data User** validates the symbols and period and owns the user-facing
   request.
2. **Plaza** discovers a Persona advertising the Data Consultant role and the
   required Pulse capability.
3. **Data Consultant** retrieves both histories through the sole financial-data
   adapter, aligns the dates, and calculates descriptive metrics.
4. **Data User** checks source, coverage, and quality evidence before presenting
   the result.

The UI exposes the request, normalized comparison chart, metrics, quality
checks, exact source query, and one correlation trace across every hop. This is
the demonstrable benefit: specialist work is delegated through a visible
contract without coupling the Data User to the consultant implementation.

## Run

From the repository root after installing the project:

```bash
python -m data_agent_network_demo --open
```

Or launch directly from a source checkout:

```bash
python demos/data-agent-network-demo/run.py --open
```

Visit [http://127.0.0.1:8000](http://127.0.0.1:8000). Opening
`static/index.html` directly does not run the API and is unsupported.

Example request:

```bash
curl -s http://127.0.0.1:8000/api/run \
  -H 'content-type: application/json' \
  -d '{"primary_symbol":"MSFT","benchmark_symbol":"SPY","period":"1y"}'
```

## Data behavior

- Provider adapter: `yfinance==1.6.0`
- Upstream data: Yahoo Finance as accessed by `yfinance`
- History: daily interval with automatic price adjustment
- Inputs: supported ticker symbols and a bounded period from the UI/API
- Output: descriptive historical comparison, not a forecast or recommendation
- Failure: explicit partial/unavailable result; no synthetic or alternate source

The demo has no persistence or background collection. Each run makes live
requests, subject to network availability, upstream availability, symbol
coverage, and rate limits. It is for education and personal experimentation,
not for operating a public data proxy or redistributing provider data.
