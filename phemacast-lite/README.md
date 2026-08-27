# Phemacast Lite

A faithful reduction of the original Phemacast Pulse and Persona runtime,
layered on Prompits Lite.

Phemacast and Prompits are owned by
[Retis AI Pte Ltd](https://retis.ai/).

Retained:

- dictionary Pulse definitions and `Pulse` normalization;
- `PulsePractice` and `GetPulseDataPractice`;
- `Pulser(StandbyAgent)`;
- `supported_pulses` in the agent card;
- `resolve_pulse_definition`, `transform`, and `get_pulse_data`;
- `Persona`, `RAGPersona`, and `CLIPersona` role configuration.

Content studios, durable memory, embeddings, model routing, production UIs,
hosting, and unrelated Persona product features are omitted.

Phemacast Lite may depend on Prompits Lite. It contains no finance or Data Agent
Network implementation.
