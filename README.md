# 🚀 Purple Merit — AI/ML Engineer Assessment (April 2026)

This repository contains **two production-grade multi-agent AI systems**:

1. **Assessment 1 — Launch War Room**  
   Simulates a product launch decision system → outputs **Proceed / Pause / Roll Back**

2. **Assessment 2 — Bug Triage System**  
   Parses bug reports + logs → generates repro → outputs **root cause + patch plan**

---

## ⚡ Quick Start (Under 1 minute)

```bash
pip install -r requirements.txt

# Assessment 1
python -m assessment1_launch_war_room.run --mock-llm

# Assessment 2
python -m assessment2_bug_triage.run --mock-llm

📁 Outputs are generated in: artifacts/

🧠 What This Project Demonstrates
Multi-agent orchestration
Tool-driven reasoning (not just LLM responses)
Deterministic execution (--mock-llm)
Reproducible pipelines
Structured outputs (JSON/YAML)
🧩 System Architecture
🔹 Assessment 1 — Launch War Room
Coordinator
   ↓
Data Analyst (metrics tools)
   ↓
Marketing/Comms (sentiment analysis)
   ↓
Product Manager (decision framing)
   ↓
Risk/Critic (challenge assumptions)
   ↓
Engineering/SRE (system impact)
   ↓
Final Decision (JSON/YAML)
🔹 Assessment 2 — Bug Triage
Triage Agent
   ↓
Log Analyst
   ↓
Reproduction Agent (generate + run pytest)
   ↓
Fix Planner
   ↓
Reviewer/Critic
   ↓
Final Output (JSON/YAML)
⚙️ Tech Stack
Python 3.11+
pytest (execution + repro validation)
OpenAI-compatible LLM (optional)
Custom multi-agent orchestration
CLI-based workflows
🔐 Environment Setup (Optional)

Create .env from .env.example:

Variable	Description
OPENAI_API_KEY	API key for LLM
OPENAI_BASE_URL	Default: OpenAI endpoint
OPENAI_MODEL	Default: gpt-4o-mini

👉 No API key? Use:

--mock-llm
▶️ Running the Systems
✅ Assessment 1 — Launch War Room
python -m assessment1_launch_war_room.run \
  --mock-llm \
  --out artifacts/launch_decision.json
Inputs
metrics.csv
feedback.txt
release_notes.md
Tools Used
aggregate_metrics
detect_anomalies
compare_trends
summarize_feedback_sentiment
🐞 Assessment 2 — Bug Triage
python -m assessment2_bug_triage.run \
  --mock-llm \
  --out artifacts/bug_triage_result.yaml
Tools Used
search_logs
extract_stack_traces
run_pytest
🔬 Reproduction (Expected Failure)
python -m pytest assessment2_bug_triage/artifacts/repro/test_repro_checkout.py -q
python -m pytest assessment2_bug_triage/mini_repo/tests -q

👉 Expected: 1 failing test (discount applied twice)

📊 Example Outputs
Assessment 1
{
  "decision": "Pause",
  "rationale": "Retention drop + spike in error rate",
  "confidence": 0.68
}
Assessment 2
{
  "bug_summary": "Discount applied twice",
  "root_cause": "Duplicate invocation of apply_promo",
  "patch_plan": "Ensure idempotent discount logic",
  "confidence": 0.82
}
🧠 Decision Logic (Assessment 1)
Condition	Decision
Stable metrics + positive feedback	Proceed
Mixed signals / anomalies	Pause
Severe degradation / errors	Roll Back
📈 Traceability (Assignment Requirement)

Structured traces are generated as JSONL logs:

artifacts/traces/assessment1_trace.jsonl
artifacts/traces/assessment2_trace.jsonl

Each entry includes:

agent step
tool call
orchestrator action
🧠 Design Decisions
Multi-Agent Approach
Mirrors real-world cross-functional teams
Enables modular reasoning
Tool-Driven Execution
Reduces hallucination
Improves reliability
Mock LLM Mode
Ensures reproducibility
Removes external dependency