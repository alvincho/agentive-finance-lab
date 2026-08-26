# Data Agent Network Demo

Two role-aware Personas collaborate through Plaza:

1. Data User interprets a financial-data question.
2. Plaza discovers a Data Consultant by PIT metadata and Pulse capability.
3. Data Consultant ranks a fictional checked-in catalog.
4. Data User validates and presents the evidence.

Run from an installed checkout:

```bash
python -m data_agent_network_demo --open
```

The **Simulate consultant outage** control proves that the Data User returns a
clear degraded result when the specialist is not registered.
