# DPR AI Simulator — Architecture

## 1. Goals & Non-Goals

### Goals (what we WILL build)

1. **AI-powered DPR simulation** — Simulate the three core functions of Indonesia's House of Representatives (DPR RI): absorbing, compiling, and following up on citizen aspirations.
2. **Multi-agent parliamentary deliberation** — Each DPR member is an independent AI agent with unique persona (faction ideology, electoral district, expertise).
3. **Cost-efficient processing** — Process 50–575 agents for under $0.10 using gpt-4.1-nano, with real-time cost tracking.
4. **Interactive web interface** — Gradio-based UI for inputting aspirations and visualizing simulation results with data tables and council transcripts.
5. **Realistic parliamentary dynamics** — Council Discussion stage simulates multi-round debates with faction positions, coalition vs. opposition dynamics, and consensus building.

### Non-Goals (what we WON'T build — prevents scope creep)

1. **Real legislative drafting** — The system generates action plans and recommendations, not actual RUU (Rancangan Undang-Undang) drafts with legal force.
2. **Persistent database storage** — No database layer; all simulation state is in-memory per request.
3. **Authentication / user management** — No login system; API keys are entered per session via the UI.
4. **Real-time streaming LLM responses** — Each agent call is a complete async request; no streaming tokens to the UI.
5. **Integration with actual DPR systems** — This is a simulation/educational tool, not connected to any government API.

## 2. Core Principles

1. **Markdown and JSON are the universal intermediate formats** — All agent prompts and outputs use structured JSON; UI renders markdown.
2. **Batch parallel processing over individual sequential calls** — Agent invocations are grouped into batches (default 10) with async `gather()` to maximize throughput.
3. **Every agent is a persona, not a generic LLM** — Each agent prompt injects faction ideology, commission scope, and electoral district context to produce politically realistic responses.
4. **Cost transparency by design** — Every API call tracks token usage and calculates USD cost; totals are surfaced in the UI and logs.
5. **Fail-soft per agent** — If one agent fails (network, JSON parse error), the pipeline continues with that agent marked as error; no single failure aborts the simulation.

## 3. System Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐     ┌─────────────┐
│   User      │────▶│  Gradio UI   │────▶│  DPRSimulator       │────▶│  Results    │
│  (Browser)  │     │  (src/ui)    │     │  (src/core)         │     │  (UI + Log) │
└─────────────┘     └──────────────┘     └─────────────────────┘     └─────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
           ┌────────────────┐          ┌────────────────┐          ┌────────────────┐
           │ MemberFactory  │          │  Agent Pool    │          │  Komisi Data   │
           │ (create/filter)│          │ (4 agents)     │          │ (13 komisi)    │
           └────────────────┘          └────────────────┘          └────────────────┘
```

**Data Flow:**

```
User submits aspiration
        │
        ▼
┌──────────────────┐
│ 1. CREATE MEMBERS│  ──▶ DPRMemberFactory generates N members with
│    (MemberFactory)│      faction, komisi, dapil, expertise, province
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 2. FILTER        │  ──▶ Get relevant members by komisi (primary)
│    (Relevance)   │      and province (secondary), up to sample_size
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 3. ABSORB        │  ──▶ AbsorbAgent (N parallel batch calls)
│    (Stage 1)     │      Output: AbsorpsiResponse per member
│                  │      (relevansi, sentiment, quote, poin_kunci)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 4. COMPILE       │  ──▶ CompileAgent (1 call)
│    (Stage 2)     │      Output: KompilasiResponse
│                  │      (ringkasan, tema_utama, fraksi_terlibat)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 5. COUNCIL       │  ──▶ CouncilDiscussionAgent (1 call)
│    DISCUSSION    │      Output: CouncilDiscussionResponse
│    (Stage 3)     │      (diskusi multi-putaran, posisi_fraksi, konsensus)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 6. FOLLOW-UP     │  ──▶ FollowUpAgent (1 call)
│    (Stage 4)     │      Output: TindakLanjutResponse
│                  │      (langkah, timeline, anggaran, pihak_terlibat)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ 7. AGGREGATE     │  ──▶ PipelineResult with all stages + SimulationDetails
│    (Result)      │      Displayed in Gradio UI as chat + dataframes
└──────────────────┘
```

## 4. Tech Stack

| Component       | Library                       | Version      | Role                                                   |
| --------------- | ----------------------------- | ------------ | ------------------------------------------------------ |
| LLM Framework   | LangChain                     | >=1.2.7      | Agent orchestration, prompt templates, output parsing  |
| LLM Provider    | OpenAI (via langchain-openai) | >=2.16.0     | gpt-4.1-nano for all agent inference                   |
| Web UI          | Gradio                        | >=6.4.0      | Interactive web interface with chatbot and data tables |
| Data Validation | Pydantic                      | >=2.12.5     | Model schemas, settings management, response parsing   |
| Settings        | pydantic-settings             | >=2.12.0     | Environment-based configuration                        |
| Data Processing | pandas                        | (via gradio) | DataFrame conversion for member tables                 |
| Package Manager | uv                            | latest       | Fast Python dependency management                      |
| Python Runtime  | CPython                       | >=3.12       | Async/await, type hints, modern syntax                 |

**Avoided alternatives:**

- **FastAPI + React** — Would add frontend complexity; Gradio is sufficient for this data-science-style UI.
- **CrewAI / AutoGen** — Overkill for this fixed pipeline; LangChain gives precise control over prompts and batching.
- **Local LLMs (Ollama)** — Would require GPU infrastructure; OpenAI API keeps costs low and setup minimal.
- **Streamlit** — Less flexible for custom CSS/theming compared to Gradio 6.x.

## 5. Project Structure

```
dpr-simulator/
├── main.py                          # Entry point: initializes logging, launches Gradio
├── pyproject.toml                   # Project metadata + dependencies (uv)
├── README.md                        # User-facing documentation (Indonesian)
├── uv.lock                          # Locked dependency versions
├── requirements.txt                 # Fallback requirements file
├── .env                             # Local environment variables (gitignored)
├── logs/
│   └── app.log                      # Runtime application logs
├── assets/
│   └── project_header.png           # README header image
├── others/                          # Documentation and marketing artifacts
│   ├── linkedin_post.md
│   ├── komisi_dpr.md
│   ├── api_call_breakdown.md
│   ├── response_example.md
│   └── additional_info*.md
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py              # Exports settings, setup_logger
│   │   ├── settings.py              # Pydantic Settings (env vars, defaults)
│   │   ├── logging_config.py        # Structured logging setup
│   │   └── examples.py              # Pre-loaded aspiration examples for UI
│   ├── models/
│   │   ├── __init__.py              # Exports all Pydantic models
│   │   ├── dpr_member.py            # DPRMember: id, name, faction, komisi, dapil, province, expertise
│   │   ├── aspirasi.py              # Aspirasi: id, source, category, content, priority, timestamp
│   │   └── responses.py             # All response models:
│   │                                  # AbsorpsiResponse, KompilasiResponse,
│   │                                  # CouncilDiscussionResponse, TindakLanjutResponse,
│   │                                  # SimulationDetails, PipelineResult
│   ├── core/
│   │   ├── __init__.py              # Exports DPRSimulator, DPRMemberFactory
│   │   ├── simulator.py             # DPRSimulator: pipeline orchestrator
│   │   ├── member_factory.py        # DPRMemberFactory: member creation + relevance filtering
│   │   ├── faction_data.py          # FACTION_PERSONAS: 17 faction ideologies
│   │   ├── komisi_data.py           # 13 Komisi definitions, category→komisi mapping
│   │   └── agents/
│   │       ├── __init__.py          # Exports all agents
│   │       ├── base.py              # BaseAgent: LLM init, cost calc, abstract methods
│   │       ├── absorb_agent.py      # AbsorbAgent: Stage 1 — member-level aspiration analysis
│   │       ├── compile_agent.py     # CompileAgent: Stage 2 — aggregate responses into consensus
│   │       ├── council_discussion_agent.py  # CouncilDiscussionAgent: Stage 3 — multi-member deliberation
│   │       └── followup_agent.py    # FollowUpAgent: Stage 4 — concrete action plan + budget
│   └── ui/
│       ├── __init__.py              # Exports launch_app
│       └── app.py                   # Gradio UI: create_app(), process_aspirasi_async/sync
├── .github/
│   └── workflows/
│       └── sync.yml                 # GitHub Actions: sync to Hugging Face Spaces
└── .cursor/
    └── rules/
        └── development-agent-rules.mdc  # Cursor IDE rules for AI coding agents
```

## 6. Data Model

### Core Entities

**DPRMember** — Represents a simulated parliament member.

- `id`, `name`, `faction` (fraksi), `komisi`, `dapil`, `province`, `expertise[]`
- `to_prompt_context()` formats member data for LLM prompts.

**Aspirasi** — Represents a citizen aspiration submitted for processing.

- `id`, `source` (province), `category`, `content`, `priority` (Tinggi/Sedang/Rendah), `timestamp`
- `to_prompt_context()` formats aspiration data for LLM prompts.

### Pipeline Response Models

**AbsorpsiResponse** — Output of Stage 1 (per member)

- `relevansi`: Tinggi/Sedang/Rendah
- `alasan_relevansi`: technical explanation
- `sentiment`: Positif/Negatif/Netral/Kritis
- `quote`: verbal political statement in faction persona style
- `poin_kunci`: list of key points
- `rekomendasi_awal`: initial recommendation
- `cost_usd`: API call cost

**KompilasiResponse** — Output of Stage 2

- `status`: terkumpul / tidak_relevan
- `ringkasan`: consensus summary
- `tema_utama`: main themes
- `fraksi_terlibat`: involved factions
- `rekomendasi_tindak_lanjut`: follow-up recommendation

**CouncilDiscussionResponse** — Output of Stage 3

- `diskusi`: list of rounds, each with interventions (pemaparan/tanggapan)
- `posisi_fraksi`: faction → position mapping
- `konsensus`: sepenuhnya/setengah/terbagi/deadlock
- `rekomendasi_kolektif`: collective recommendation

**TindakLanjutResponse** — Output of Stage 4

- `langkah_tindak_lanjut`: concrete steps
- `komisi_penanggung_jawab`: responsible commission
- `timeline`: estimated timeline
- `estimasi_anggaran`: budget estimate in Rupiah
- `rincian_anggaran`: per-item budget breakdown
- `sumber_dana`: funding sources (APBN/APBD)
- `pihak_terlibat`: stakeholders to involve

**PipelineResult** — Aggregates all stages

- `aspirasi`, `tanggapan_anggota[]`, `kompilasi`, `council_discussion`, `tindak_lanjut`
- `simulation_details`: member selection stats, relevance breakdown, cost
- `total_cost_usd`: sum of all API call costs

## 7. Agent Design

All agents inherit from `BaseAgent` and follow the same pattern:

1. **System Prompt** — Defines role and rules (in Indonesian)
2. **User Prompt Builder** — Injects dynamic context (member data, aspiration, prior responses)
3. **LLM Invocation** — `ainvoke()` via LangChain ChatOpenAI
4. **JSON Parsing** — Strip markdown fences, `json.loads()`, map to Pydantic model
5. **Cost Calculation** — Extract `token_usage` from `response_metadata`, compute USD cost
6. **Error Handling** — Catch exceptions, return response with `error` field set

### Agent Specializations

| Agent                      | Temperature | Input                                       | Output                    | Key Behavior                                                                                                                                          |
| -------------------------- | ----------- | ------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **AbsorbAgent**            | 0.7         | Member + Aspirasi                           | AbsorpsiResponse          | Injects faction persona via `get_faction_persona()`. Prioritizes Komisi over Dapil for relevance. Generates natural political quotes.                 |
| **CompileAgent**           | 0.7         | Aspirasi + AbsorpsiResponse[]               | KompilasiResponse         | Filters to Tinggi/Sedang relevance only. Aggregates themes and factions.                                                                              |
| **CouncilDiscussionAgent** | 0.8         | Aspirasi + AbsorpsiResponse[] + DPRMember[] | CouncilDiscussionResponse | Simulates multi-round (default 2) parliamentary debate. Each intervention includes member_id, name, faction, type (pemaparan/tanggapan), and content. |
| **FollowUpAgent**          | 0.7         | Aspirasi + KompilasiResponse                | TindakLanjutResponse      | Generates realistic Indonesian government budget estimates with per-item breakdowns and funding sources.                                              |

## 8. Pipeline Orchestration

**DPRSimulator** is the central orchestrator:

```python
# Simplified flow
async def process_aspirasi(aspirasi, sample_size, komisi_filter):
    # 1. Filter members
    relevant = MemberFactory.get_relevant_members(members, category, source, komisi_filter, sample_size)

    # 2. Absorb (batched parallel)
    for batch in relevant[::batch_size]:
        responses += await gather([absorb_agent.invoke(m, aspirasi) for m in batch])
        await sleep(rate_limit_delay)

    # 3. Compile
    kompilasi = await compile_agent.invoke(aspirasi, responses)

    # 4. Council Discussion (only if compilation succeeded)
    if kompilasi.status == "terkumpul":
        council = await council_discussion_agent.invoke(aspirasi, responses, relevant_members)

    # 5. Follow-up (only if compilation succeeded)
    if kompilasi.status == "terkumpul":
        tindak_lanjut = await followup_agent.invoke(aspirasi, kompilasi)

    # 6. Aggregate
    return PipelineResult(...)
```

**Batching Strategy:**

- Default batch size: 10 members
- Default rate limit delay: 1 second between batches
- Uses `asyncio.gather()` within each batch for parallel execution
- Total API calls formula: `N + 3` where N = sample size

## 9. Member Factory & Relevance Engine

**DPRMemberFactory.create_members(count)**

- Generates `count` members with cyclical distribution across:
  - 17 factions (PDI-P, Golkar, Gerindra, PKB, Nasdem, PKS, Demokrat, PAN, PPP, PSI, Perindo, Hanura, Garuda, PBB, PKPI, Gelora, Ummat)
  - 13 Komisi (Komisi I – Komisi XIII)
  - 33 provinces
  - 16 expertise areas
- Members are named `Anggota_DPR_{id}` for deterministic generation.

**DPRMemberFactory.get_relevant_members(members, category, source, komisi_filter, limit)**

1. Determine target Komisi from `CATEGORY_TO_KOMISI` mapping (or explicit filter)
2. Filter members whose `komisi` is in target list
3. Fallback to expertise match if no Komisi match (defensive)
4. Sort by province match (source province members first)
5. Return top `limit` members

## 10. Configuration

All configuration is via `pydantic-settings` with environment variable fallbacks:

| Variable                    | Default        | Description                           |
| --------------------------- | -------------- | ------------------------------------- |
| `OPENAI_API_KEY`            | `""`           | OpenAI API key (also accepted via UI) |
| `OPENAI_MODEL`              | `gpt-4.1-nano` | Model for all agents                  |
| `PROMPT_COST_PER_1K`        | `0.0001`       | Prompt token cost (USD)               |
| `COMPLETION_COST_PER_1K`    | `0.0004`       | Completion token cost (USD)           |
| `DEFAULT_MEMBER_COUNT`      | `50`           | Default members generated             |
| `BATCH_SIZE`                | `10`           | Parallel batch size for absorb stage  |
| `RATE_LIMIT_DELAY`          | `1.0`          | Seconds between batches               |
| `GRADIO_SERVER_NAME`        | `127.0.0.1`    | Gradio host                           |
| `GRADIO_SERVER_PORT`        | `7860`         | Gradio port                           |
| `GRADIO_SHARE`              | `False`        | Public Gradio share                   |
| `COUNCIL_DISCUSSION_ROUNDS` | `2`            | Number of council debate rounds       |

**Security note:** The application does **not** use `.env` files for the API key in production. The key is entered per session via the Gradio UI and is never persisted to disk.

## 11. UI Design

**Gradio Layout (2-column):**

| Left Column (Input)                    | Right Column (Output)           |
| -------------------------------------- | ------------------------------- |
| OpenAI API Key input (password)        | Chatbot (progress + results)    |
| Simulation settings (sliders)          | Simulation details (accordions) |
| Aspiration content (textarea)          | All members dataframe           |
| Category / Komisi / Priority dropdowns | Relevant members dataframe      |
| Source province dropdown               | Responding members dataframe    |
| Submit button                          | Council discussion transcript   |
| Example aspirations (7 presets)        | API call breakdown (dev info)   |

**Visual Design:**

- Dark theme with slate/blue gradient background
- Custom CSS variables for theming
- IBM Plex Sans font
- Orange accent color for primary actions and highlights
- Data tables use Gradio's native Dataframe component

## 12. Cost Model

Using `gpt-4.1-nano` (default):

| Sample Size | Stage 1 (Absorb) | Stage 2 (Compile) | Stage 3 (Council) | Stage 4 (Follow-up) | Total API Calls | Est. Cost     |
| ----------- | ---------------- | ----------------- | ----------------- | ------------------- | --------------- | ------------- |
| 20          | 20               | 1                 | 1                 | 1                   | 23              | ~$0.002–0.005 |
| 50          | 50               | 1                 | 1                 | 1                   | 53              | ~$0.005–0.01  |
| 100         | 100              | 1                 | 1                 | 1                   | 103             | ~$0.01–0.02   |
| 575         | 575              | 1                 | 1                 | 1                   | 578             | ~$0.05–0.10   |

**Comparison:** Actual DPR RI annual budget is approximately **Rp 5 Trillion**.

## 13. Error Handling Strategy

| Layer              | Strategy                                                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **Agent level**    | Try/except around `ainvoke()` and JSON parsing; return response with `error` field populated                                 |
| **Batch level**    | `asyncio.gather()` with individual task exceptions; failed agents logged but don't stop batch                                |
| **Pipeline level** | If compilation returns `tidak_relevan`, skip Council and Follow-up with warning messages                                     |
| **UI level**       | Try/except around entire pipeline; display error in chatbot with ❌ prefix                                                   |
| **Logging**        | Structured logging with `logging.getLogger("dpr_simulator.{module}")`; debug-level token usage, info-level stage transitions |

## 14. Deployment

**Primary target:** [Hugging Face Spaces](https://huggingface.co/spaces/mcikalmerdeka/dpr-simulator)

- SDK: Gradio
- Entry point: `main.py`
- Sync via GitHub Actions (`.github/workflows/sync.yml`)

**Local development:**

```bash
uv sync
uv run python main.py
# Access at http://127.0.0.1:7860
```

## 15. Observability

**Logging hierarchy:**

- `dpr_simulator` — App lifecycle (startup, shutdown)
- `dpr_simulator.simulator` — Pipeline stage transitions, member counts, costs
- `dpr_simulator.agents` — Agent initialization
- `dpr_simulator.agents.{absorb,compile,council,followup}` — Per-agent invocations, token usage, errors
- `dpr_simulator.members` — Member factory operations
- `dpr_simulator.ui` — UI events (submissions, errors)

Log output: `logs/app.log` (file) + stdout (console, via Gradio).

## 16. Implementation Status

| Phase            | Status  | Description                                                              |
| ---------------- | ------- | ------------------------------------------------------------------------ |
| Core Pipeline    | ✅ Done | 4-stage pipeline (Absorb, Compile, Council, Follow-up) fully implemented |
| Agent System     | ✅ Done | All 4 agents with persona injection, JSON parsing, cost tracking         |
| Member Factory   | ✅ Done | 17 factions, 13 komisi, 33 provinces, relevance filtering                |
| Gradio UI        | ✅ Done | Dark-themed UI with chatbot, data tables, council transcript panel       |
| Cost Tracking    | ✅ Done | Per-call and total cost calculation with USD and IDR display             |
| Example Data     | ✅ Done | 7 pre-loaded aspiration examples                                         |
| Logging          | ✅ Done | Structured logging across all modules                                    |
| HF Spaces Deploy | ✅ Done | Live deployment with GitHub Actions sync                                 |

## 17. Decision Log

| Decision           | Chosen                            | Rejected                      | Reason                                                                                   |
| ------------------ | --------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------------- |
| LLM Provider       | OpenAI API (gpt-4.1-nano)         | Local LLMs, Claude, Gemini    | Lowest cost ($0.05 for 575 agents), zero infrastructure, consistent JSON output          |
| UI Framework       | Gradio 6.x                        | Streamlit, FastAPI+React      | Built-in chatbot, dataframe, and theme support; fastest path to interactive demo         |
| Agent Framework    | LangChain                         | CrewAI, AutoGen, raw OpenAI   | Precise prompt control, easy JSON output parsing, familiar async patterns                |
| Config Management  | pydantic-settings                 | python-dotenv, dynaconf       | Type-safe, validated, auto-documented; integrates with Pydantic models                   |
| Package Manager    | uv                                | pip, poetry                   | Fastest installs, lockfile support, modern Python tooling                                |
| Member Naming      | `Anggota_DPR_{id}`                | Real names (fictional), UUIDs | Deterministic, no cultural bias, easy debugging                                          |
| Council Simulation | Single LLM call with full context | Multi-agent debate loop       | 1 call vs N calls = massive cost savings; LLM can simulate multiple personas effectively |
| Language           | Indonesian (prompts + UI)         | English                       | Target audience is Indonesian citizens; political quotes must feel authentic             |
| API Key Input      | UI per-session                    | .env file                     | Security: no keys in repo, no disk persistence in shared environments (HF Spaces)        |
| Data Persistence   | None (in-memory)                  | SQLite, PostgreSQL            | Stateless by design; each request is independent, no user accounts                       |

## 18. Project Status

**This project is complete.** All core functionality has been implemented, tested, and deployed. No further upgrades or new features are planned.

The system is stable and ready for use as-is. Any future changes would be limited to maintenance (dependency updates, bug fixes) rather than feature expansion.
