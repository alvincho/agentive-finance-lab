# Agentive Finance Lab: 10-Episode Repository Introduction

## Season position

**Series name:** *Build a Multi-Agent Finance Lab*

**Season promise:** In ten episodes, a reader will clone the public
repository, understand its reduced Prompits Lite and Phemacast Lite foundations,
work through all three Data Agent demo routes, and learn the contract a future
demo must preserve.

**Primary audience:** Python developers, financial-data practitioners, and
technical product builders who understand APIs but may be new to multi-agent
systems.

**Cadence:** Episode 1 launched on 27 August 2026. Twice-weekly Tuesday and
Friday publication begins with Episode 2 on 1 September 2026 at 20:00
Asia/Taipei.

Each episode should contain one concrete idea, one repository artifact, one
runnable action, and one honest boundary or limitation. Aim for a 6–8 minute
read. Use “structured Pulse contract,” not “typed contract,” and avoid claims
that multi-agent systems universally outperform Model Context Protocol (MCP),
skills, or single-agent applications.

Define FinMAS on first use as the original full financial multi-agent
application from which this public lab was reduced. Also expand
retrieval-augmented generation (RAG), Agent-to-Agent (A2A), and bring your own
key (BYOK) on first use.

## Publication schedule

| Episode | Publish date | Working title | Reader outcome | Runnable action and primary CTA | Lead visual |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-08-27 | [**MCP and Skills Hit Their Limits in Finance: The Multi-Agent Solution**](https://agentivefinancelab.substack.com/p/mcp-and-skills-hit-their-limits-in) | See where a flat model-facing tool catalog reaches scale, selection, ownership, and finance-policy limits—and how coordinated specialist agents address them without claiming better predictions or returns. Meet Data User, Data Consultant, and Data Source as separate responsibilities. | Open the landing page, subscribe to the series, and star or bookmark the repository. | Responsibility map: User → Consultant → Source, coordinated by Plaza. |
| 2 | 2026-09-01 | **Clone the Lab and Meet the Network** | Install the project in a virtual environment, start the local UI, verify health, and locate all three demos before learning framework vocabulary. | Clone, run `python demos/data-agent-network-demo/run.py --open`, and verify `/health`. | Short screen recording from terminal clone to the running UI. |
| 3 | 2026-09-04 | **Lite Is a Boundary, Not a Rewrite** | Understand the dependency direction `demos → phemacast-lite → prompits-lite`, why this repository is a reduced extraction separate from FinMAS—the original full financial multi-agent application—and which production services were deliberately removed. | Match the three repository layers to `docs/SCOPE.md` and `docs/ARCHITECTURE.md`. | Layer diagram showing allowed dependency direction and removed production services. |
| 4 | 2026-09-08 | **Prompits Lite: Identity, Practice, and Plaza** | Learn Pit identity, cards, discovery, the local invocation boundary called `UsePractice`, and centralized Plaza coordination. Use a short sidebar to contrast this ownership model with MCP, skills, and a loose A2A mesh. | Inspect `prompits-lite/`, then follow one Data User request through Plaza resolution. | Pit cards entering one Plaza; keep the MCP/skills/A2A comparison to a compact sidebar. |
| 5 | 2026-09-11 | **Phemacast Lite: Pulses, Pulsers, and Personas** | Learn one distinction: a Pulse defines the structured interaction, a Pulser exposes it, and a Persona adds a role and behavior. Data Sources are Pulsers; Data User and Consultant are Personas. | Trace one supported Pulse from definition to handler in `phemacast-lite/`. | Responsibility map: Pit → Pulser → Persona, with Pulse beside the call boundary. |
| 6 | 2026-09-15 | **Demo 1: Advice Without Fetching Data** | Trace source registration, `data_availability`, Consultant catalog synchronization, and deterministic documentation retrieval under the retained `catalog_rag` policy label. Establish that the lite path has no LLM generation step and makes no provider call. | Run the three Single Source questions and inspect the returned endpoint evidence. | Single Source advisory sequence with the provider boundary visibly unopened. |
| 7 | 2026-09-18 | **Demo 1: The User Calls YFinance Directly** | Separate advisory and execution planes: Consultant recommends and resolves; Data User invokes `data_spec` or `data_fetch` directly on YFinance. | Execute one YFinance history request and trace `data_source_status → data_fetch`. | Direct-source sequence diagram and one real result screenshot. |
| 8 | 2026-09-22 | **Demo 2: Three Sources, the Same Workflow** | See YFinance, Alpha Vantage, and FRED register compatible source cards without rewriting Data User or Consultant. Keep the UI catalog/specification-only. | Compare equity and CPI endpoint specifications without making an upstream provider call. | Multiple Sources topology with three separate source-owned catalogs. |
| 9 | 2026-09-25 | **Demo 3: A Missing Key Is an Honest Result** | Run the keyless baseline: with Yahoo Finance reachable, YFinance returns live AAPL history while Alpha Vantage returns `authentication_required`. Learn why visible failure is better than a fixture, proxy, or fallback. | Launch `?sample=no-key`, inspect both separate result cards, and confirm no provider response passed through the Consultant. | Split-screen capture of YFinance rows and the Alpha Vantage key boundary. |
| 10 | 2026-09-29 | **Bring Your Own Keys, FRED, and the Extension Contract** | Focus on one idea: credentials belong to source agents. Show the Alpha Vantage and FRED server-side paths, then close with a one-page checklist for preserving the same boundary in future demos. | Copy `.env.example` to the gitignored `.env`, choose either the Alpha Vantage or FRED guided track to run after restart, then use the source-card checklist to propose one bounded extension in a discussion or pull request. | `.env` → source-agent boundary; offer the extension contract as a downloadable closing checklist. |

Episode 2 deliberately gives readers a working result before vocabulary.
Episode 3 then establishes scope and dependency boundaries before Episodes 4–5
explain framework internals.

## Repeatable episode shape

Use the same five-part structure so readers know what to expect:

1. **Problem:** one finance-development problem stated without framework jargon.
2. **Concept:** the single architecture idea needed for this episode.
3. **Repository walk-through:** two or three files, not a broad code tour.
4. **Run it:** one command or browser action with an observable result.
5. **Boundary and next step:** what the demo intentionally does not prove, then
   a teaser for the next episode.

## Twice-weekly editorial and distribution rhythm

- **Saturday (for Tuesday) or Tuesday (for Friday), 09:00 (T−3):** Prepare the full Substack draft, Medium
  adaptation, channel-specific copy, Taiwan Facebook edition, mainland-China
  WeChat (Weixin) edition, diagram, and one reusable 9:16 short demo clip for
  TikTok, YouTube Shorts, and Instagram Reels. Prepare the selected YouTube
  title, description, audience setting, and caption track with the same asset.
  Mark the release bundle `prepared`; nothing is public at this stage.
- **T−3 through publication:** Alvin may revise the prepared Substack draft.
  The publication job rechecks links, figures, runnable commands, social copy,
  media, and hashes before it publishes; there is no separate readiness or
  approval job.
- **Tuesday or Friday, 20:00:** Publish the full Substack episode and repository
  CTA after the three-day revision window. A verified live canonical URL is the
  authorization for every downstream job; no additional approval is required.
- **Wednesday or Saturday, 08:00 (T+1):** Run one consolidated downstream
  repost job. It submits the Medium adaptation to *Agentive Futures*, creates
  or publishes the standalone Simplified Chinese WeChat edition for
  `AI智域边界` (`retis_ai`), and publishes the prepared video or channel-specific
  variant to TikTok, YouTube Shorts, Instagram Reels, Facebook Reels, LinkedIn,
  X, Threads, and Alvin Cho's Taiwan-facing Facebook account. It reads receipts
  first, skips matching successes, and handles every incomplete destination
  independently. The verified Substack URL is the authorization; there is no
  separate downstream approval or later discussion-wave job.

Every downstream channel action occurs no later than two calendar days after
its canonical Substack episode.

The YouTube Shorts destination is the branded `Agentive Finance Lab` channel,
handle `@AgentiveFinanceLab`, with immutable channel ID
`UCBUlIH03zTzZyhEnOls6Aqw`. Its machine-readable allowlist is
`docs/channels/youtube-shorts.json`. Never substitute Alvin Cho's personal
channel, even when that account is also signed in.

Each episode stores its Medium source in `docs/medium/`, reviewable channel copy
in `docs/social/NN-launch-pack.md`, its Taiwan Facebook source in
`docs/locales/zh-TW/NN-facebook.md`, its mainland-China WeChat source in
`docs/locales/zh-CN/NN-weixin.md`, and the validated body and asset hashes in
`docs/releases/NN-release.json`. Any content or asset change requires hashes and
technical validation to be refreshed, but never creates a new approval gate.
Automated publication records each attempt, successful destination, locale, remote ID,
and URL in `docs/social/NN-receipts.json`; a destination with a successful
receipt must never be published a second time by a retry. An interrupted
`attempting` record must be reconciled against the remote platform before
retrying. Failure on one channel must not be hidden by success on another
channel.

The Taiwan Facebook edition is a localized explanation, not a literal
translation: retain framework names in English, introduce them in Traditional
Chinese on first use, and use Taiwan financial-technology terminology. The
WeChat edition must stand on its own because access to external destinations can
vary. It includes the complete argument, native cover and inline images, concise
code excerpts, the educational disclaimer, and only links or QR destinations
verified during preparation. WeChat credentials remain server-side; no AppID,
secret, access token, or login cookie belongs in the repository or browser
storage. API publishing is enabled only after the account type, verification,
API permission, delivery mode, and allowlisted account identity are confirmed.
When API publishing is unavailable, the scheduled job uses the allowlisted
persistent Chrome session to prepare the complete dashboard item automatically.
It never asks the user to copy, paste, upload, or configure the article.

As recorded on 28 August 2026, the mainland-China destination is the WeChat
Official Account `AI智域边界`, public-account ID `retis_ai`, and its dashboard
shows both account and personal verification as unverified. Its release-manifest
delivery mode is therefore `browser_automation` until verification and API
permissions make unattended official-API publishing available. Never substitute
another signed-in Official Account, even when its session is available. The
machine-readable allowlist is `docs/channels/weixin-cn.json`.

Keep the Substack post as the canonical source. Link to it directly from social
messages and also link to the relevant repository section or demo, not only the
repository root. The WeChat edition references the canonical source only when
the destination is allowed and verified; its core explanation and runnable
context must not depend on following an external link.

## Season-wide editorial guardrails

- Describe the repository as a reduced, runnable extraction rather than a new
  framework or production platform.
- Preserve the concepts `Pit`, `Plaza`, `Pulser`, `Pulse`, and `Persona`.
- Keep the Data Consultant’s deterministic catalog search separate from
  provider retrieval; explain that `catalog_rag` is a retained policy label,
  not a claim that the lite path runs an LLM generation step.
- State that live data remains subject to provider availability and terms.
- Keep `.env` gitignored and server-side; never place provider keys in the UI,
  browser storage, Pulse input, screenshots, or published examples.
- Never present the project as investment advice or imply improved returns.
- Show explicit authentication and provider failures; do not hide them with
  fixtures, synthetic data, or cross-source fallback.
