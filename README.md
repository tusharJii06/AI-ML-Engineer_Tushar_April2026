# Purple Merit — AI/ML Engineer Assessment (April 2026)

This repository contains **two production-style multi-agent AI systems**:

1. **Assessment 1 — Launch War Room** — Simulates a product launch decision system and outputs **Proceed**, **Pause**, or **Roll Back**.
2. **Assessment 2 — Bug Triage System** — Parses bug reports and logs, generates a repro, and outputs **root cause** plus a **patch plan**.

---

## Quick start

```bash
pip install -r requirements.txt

# Assessment 1
python -m assessment1_launch_war_room.run --mock-llm

# Assessment 2
python -m assessment2_bug_triage.run --mock-llm
```

Generated artifacts are written under `artifacts/` (including trace logs under `artifacts/traces/`).

---

## What this project demonstrates

- Multi-agent orchestration
- Tool-driven reasoning (not chat-only responses)
- Deterministic runs via `--mock-llm`
- Reproducible pipelines
- Structured outputs (JSON / YAML)

---

## System architecture

### Assessment 1 — Launch War Room

```text
Coordinator
  → Data Analyst (metrics tools)
  → Marketing / Comms (sentiment)
  → Product Manager (decision framing)
  → Risk / Critic (challenge assumptions)
  → Engineering / SRE (system impact)
  → Final decision (JSON / YAML)
```

### Assessment 2 — Bug Triage

```text
Triage Agent
  → Log Analyst
  → Reproduction Agent (generate + run pytest)
  → Fix Planner
  → Reviewer / Critic
  → Final output (JSON / YAML)
```

---

## Tech stack

- Python 3.11+
- `pytest` (execution and repro validation)
- OpenAI-compatible LLM (optional)
- Custom multi-agent orchestration
- CLI-based workflows

Optional: install the project in editable mode with dev extras (see `pyproject.toml`):

```bash
pip install -e ".[dev]"
```

---

## Environment setup (optional)

Copy `.env.example` to `.env` and set variables as needed.

| Variable           | Description                    |
| ------------------ | ------------------------------ |
| `OPENAI_API_KEY`   | API key for the LLM            |
| `OPENAI_BASE_URL`  | Default: OpenAI-compatible URL |
| `OPENAI_MODEL`     | Default: `gpt-4o-mini`         |

No API key is required for local demos: pass **`--mock-llm`** on the run commands above.

---

## Running the systems

### Assessment 1 — Launch War Room

```bash
python -m assessment1_launch_war_room.run \
  --mock-llm \
  --out artifacts/launch_decision.json
```

**Inputs** (under `assessment1_launch_war_room/data/`):

- `metrics.csv`
- `feedback.txt`
- `release_notes.md`

**Tools used:** `aggregate_metrics`, `detect_anomalies`, `compare_trends`, `summarize_feedback_sentiment`

### Assessment 2 — Bug Triage

```bash
python -m assessment2_bug_triage.run \
  --mock-llm \
  --out artifacts/bug_triage_result.yaml
```

**Tools used:** `search_logs`, `extract_stack_traces`, `run_pytest`

---

## Reproduction (expected failure)

```bash
python -m pytest assessment2_bug_triage/artifacts/repro/test_repro_checkout.py -q
python -m pytest assessment2_bug_triage/mini_repo/tests -q
```

You should see **one failing test** (discount applied twice), which matches the triage scenario.

---

## Example outputs

### Assessment 1

```json
{
  "decision": "Pause",
  "rationale": "Retention drop + spike in error rate",
  "confidence": 0.68
}
```

### Assessment 2

```json
{
  "bug_summary": "Discount applied twice",
  "root_cause": "Duplicate invocation of apply_promo",
  "patch_plan": "Ensure idempotent discount logic",
  "confidence": 0.82
}
```

---

## Decision logic (Assessment 1)

| Condition                              | Decision   |
| -------------------------------------- | ---------- |
| Stable metrics + positive feedback     | Proceed    |
| Mixed signals / anomalies              | Pause      |
| Severe degradation / errors            | Roll Back  |

---

## Traceability

Structured traces are written as JSONL:

- `artifacts/traces/assessment1_trace.jsonl`
- `artifacts/traces/assessment2_trace.jsonl`

Each line typically records agent steps, tool calls, and orchestrator actions.

---

## Design decisions

- **Multi-agent approach** — Mirrors cross-functional teams; keeps reasoning modular.
- **Tool-driven execution** — Grounds behavior in tools to reduce hallucination and improve reliability.
- **Mock LLM mode** — Makes runs reproducible and removes the need for external API calls when demoing or testing.
