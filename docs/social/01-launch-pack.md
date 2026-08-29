---
episode: 1
status: ready_from_live_canonical
canonical_url: "https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in"
prepared_at: 2026-08-28 Asia/Taipei
downstream_authorization: verified_live_substack
---

# Episode 1 launch pack

The live canonical Substack publication authorizes these downstream variants. Hashes and account checks protect integrity and destination identity; they are not additional editorial approval gates.

## Launch insight

MCP standardizes access to tools. Skills standardize repeatable operating instructions. In finance, the next scaling problem is ownership: who understands a provider, who recommends it, who executes it, and who reports a failure without hiding provenance?

Episode 1 demonstrates a narrow answer: Data User owns intent, Data Consultant owns catalog advice, YFinance Source owns provider execution, and Plaza coordinates the named Pulse handoffs. The claim is inspectability and replaceable ownership—not better forecasts or returns.

Canonical article: https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in

Repository demo: https://github.com/alvincho/agentive-finance-lab#demo-1-data-agent--single-source

## Launch post variants

### LinkedIn

Financial professionals need more than another AI demo with a single assistant calling a long list of tools.

We built an open-source repository to demonstrate how to use a multi-agent system for financial applications. The design gives each component a clear responsibility, keeps handoffs inspectable, and isolates provider-specific execution.

Episode 1 implements one runnable financial-data path:

• Data User owns the request and intent
• Data Consultant recommends YFinance from catalog documentation
• YFinance Source executes the provider call
• Plaza coordinates the handoffs

This is a practical architecture example, not a trading strategy. It does not promise better forecasts or returns. It shows who selected the provider, who executed the request, and where a failure belongs.

Read the design and reasoning: https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in

Explore and run the repository: https://github.com/alvincho/agentive-finance-lab#demo-1-data-agent--single-source

#MultiAgentSystems #FinTech #MCP #OpenSource

### X

MCP standardizes tool access. The next finance scaling problem is ownership.

Episode 1 makes one path inspectable:
Data User → Plaza → Data Consultant → YFinance Source.

No forecast claims. No hidden fallback.
https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in

### Threads

A finance assistant can have 1,000 tools and still be unable to explain who owned the provider decision.

Episode 1 separates intent, catalog advice, and YFinance execution—and keeps every handoff visible through Plaza.

Canonical article: https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in

### Instagram caption

Choose a specialist before choosing among thousands of provider functions.

Episode 1 traces one implemented path: Data User asks, Data Consultant recommends YFinance from catalog documentation, and Data User invokes the selected YFinance source through Plaza.

The demo proves visible ownership and handoffs. It does not promise better predictions or returns.

Canonical article: https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in

#MultiAgent #FinTech #MCP #OpenSource

### TikTok caption

What breaks when finance exposes 1,000 tools? Ownership. This 37-second demo shows one YFinance-only path with explicit handoffs. Educational demo; not investment advice. #MultiAgent #FinTech #MCP

## Short demo / UI clip variants

All variants reuse `docs/media/01/01-short-master-en-9x16.mp4`. Do not crop from a different source or replace it with a multi-source capture.

| Destination | Asset treatment | Caption variant | Identity status |
| --- | --- | --- | --- |
| TikTok | Upload the 9:16 master unchanged; platform UI may add safe-zone text only after review. | Use the TikTok caption above. | Blocked until the exact account is allowlisted. |
| YouTube Shorts | Upload the master unchanged with `01-short-master-en.vtt`; audience is `not_made_for_kids`. | Use the selected title and description below. | Allowlisted only as Agentive Finance Lab / @AgentiveFinanceLab / `UCBUlIH03zTzZyhEnOls6Aqw`. |
| Instagram Reels | Upload the master unchanged. Do not replace the English burned-in text. | Use the Instagram caption above. | Blocked until the exact account is allowlisted. |
| Facebook Reels | Reuse the same pixels; attach the reviewed Traditional Chinese subtitle file only after it is prepared and reviewed. | Use the Taiwan Facebook edition as source copy. | Blocked until the exact Taiwan page/account is allowlisted. |
| LinkedIn / X / Threads clip | Reuse the first 30 seconds or the complete 37-second master; never splice in Demo 2 or Demo 3. | Use the matching launch variant above. | Blocked until exact accounts are allowlisted. |

Capture evidence: the local 2026-08-28 Asia/Taipei run used only Demo 1. It showed deterministic YFinance catalog advice, `yfinance.ticker.history`, a direct `data_fetch` call by Data User through Plaza, and a 23-row canonical YFinance result. The market values are not quoted in any post. No Alpha Vantage or FRED screen was opened or captured.

## YouTube Shorts metadata

Identity allowlist (only):

- Account: `Agentive Finance Lab`
- Handle: `@AgentiveFinanceLab`
- Immutable channel ID: `UCBUlIH03zTzZyhEnOls6Aqw`
- Channel URL: https://www.youtube.com/@AgentiveFinanceLab
- Delivery mode: `youtube_studio`
- Never use Alvin Cho’s personal channel.

Selected title:

`Why 1,000 Finance Tools Need Clear Owners`

Selected description:

`One implemented path, made visible: Data User asks, Data Consultant recommends YFinance from catalog documentation, and Data User calls the selected YFinance Source through Plaza. The Consultant never receives the provider result.`

`Agentive Finance Lab is an educational software demo—not investment advice. yfinance is unaffiliated with Yahoo; Yahoo Finance data is intended for personal use and remains subject to applicable terms.`

The description intentionally has no dependency on a clickable external URL. Do not append a Related Video unless its exact YouTube video ID is configured in the release manifest.

- Audience: `not_made_for_kids`
- Caption track: `docs/media/01/01-short-master-en.vtt`
- Caption language: English (`en`)
- Caption validation: timing, wording, names, endpoint, disclaimer, and no-Alpha-Vantage/no-FRED boundary validated on 2026-08-28 Asia/Taipei
- Related Video: none; attach only when an exact video ID is configured

## Discussion prompt

When a financial-data request fails, which boundary should own the explanation: the user-facing agent, the source-selection specialist, or the provider-specific source—and what evidence would you require before allowing a fallback?

Short X / Threads version:

If a financial-data request fails, which component should explain it—and what evidence would you require before allowing a provider fallback?

## Educational disclaimer

Agentive Finance Lab is an educational software demonstration. It does not provide investment advice, trading recommendations, data rights, or guarantees about provider availability, freshness, completeness, or accuracy. Live data remains subject to each provider’s terms and limits.
