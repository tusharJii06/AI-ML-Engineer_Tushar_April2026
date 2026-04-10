# Purple Merit — AI/ML Engineer assessments (April 2026)

Monorepo with **two** runnable multi-agent systems:

1. **Assessment 1 — Launch war room:** mock dashboard (metrics + feedback + release notes) → coordinated PM / Data / Marketing / Risk / **Engineering-SRE** perspectives → structured **Proceed / Pause / Roll Back** decision.
2. **Assessment 2 — Bug triage:** bug report + noisy logs + **mini repo** → triage → log analysis → generated minimal repro → pytest runs → root-cause + patch + validation plan.

## Requirements

- Python **3.11+** (tested on 3.11+; 3.14 works with current dependencies)
- Install: `pip install -r requirements.txt`

## Environment variables (optional LLM)

Copy [`.env.example`](.env.example) to `.env` and set:

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | If set, agents call an OpenAI-compatible Chat Completions API for narrative steps |
| `OPENAI_BASE_URL` | Default `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Default `gpt-4o-mini` |

**Without a key**, use `--mock-llm` on both CLIs: tool calls and structured outputs still run deterministically; LLM steps use a stub response (final JSON/YAML is still produced from tool-derived logic).

## Assessment 1 — run end-to-end

From the **repository root** (`purple/`):

```bash
python -m assessment1_launch_war_room.run --mock-llm --out artifacts/launch_decision.json
```

YAML output:

```bash
python -m assessment1_launch_war_room.run --mock-llm --format yaml --out artifacts/launch_decision.yaml
```

- **Inputs:** [`assessment1_launch_war_room/data/`](assessment1_launch_war_room/data/) (`metrics.csv`, `feedback.txt`, `release_notes.md`)
- **Agents:** Data Analyst (tools), Product Manager, Marketing/Comms, Risk/Critic, Engineering/SRE (extra), Coordinator
- **Tools (programmatic):** `aggregate_metrics`, `detect_anomalies`, `compare_trends`, `summarize_feedback_sentiment`
- **Structured output:** decision, rationale, risk register, 24–48h action plan, communication plan, confidence + what would increase confidence

## Assessment 2 — run end-to-end

```bash
python -m assessment2_bug_triage.run --mock-llm --out artifacts/bug_triage_result.yaml
```

JSON output:

```bash
python -m assessment2_bug_triage.run --mock-llm --format json --out artifacts/bug_triage_result.json
```

- **Inputs:** [`assessment2_bug_triage/fixtures/`](assessment2_bug_triage/fixtures/) (bug report + logs), [`assessment2_bug_triage/mini_repo/`](assessment2_bug_triage/mini_repo/) (intentional bug in `checkoutcalc.apply_promo`)
- **Agents (handoffs):** Triage → Log Analyst → Reproduction → Fix Planner → Reviewer/Critic
- **Tools:** `search_logs`, `extract_stack_traces`, `run_pytest` (mini-repo suite + generated repro)
- **Generated repro:** `assessment2_bug_triage/artifacts/repro/test_repro_checkout.py` (created/overwritten each run; **fails** until the bug is fixed)

### Repro only (expected failure)

```bash
python -m pytest assessment2_bug_triage/artifacts/repro/test_repro_checkout.py -q
```

```bash
python -m pytest assessment2_bug_triage/mini_repo/tests -q
```

Expect **one failed** test demonstrating doubled discount (`80.0` vs `90.0`).

## Traces (assessment requirement)

Both runners emit **JSON lines on stderr** (agent steps + tool calls). Optional log files:

- Assessment 1: `--trace-file artifacts/traces/assessment1_trace.jsonl` (default)
- Assessment 2: `--trace-file artifacts/traces/assessment2_trace.jsonl` (default)

Read traces: each line is one JSON object with `type` of `orchestrator`, `agent`, or `tool`.

## Demo video (per brief)

Record silently:

1. Run Assessment 1 command; show terminal + `artifacts/launch_decision.json` (or YAML) in an editor.
2. Run Assessment 2 command; show pytest failure + `artifacts/bug_triage_result.yaml` (or JSON).

## Submission naming

Use the employer’s filename/email subject conventions from the assessment PDF when you submit your fork.
