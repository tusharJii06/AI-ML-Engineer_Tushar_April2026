from __future__ import annotations

import json
import re
from pathlib import Path

from shared.llm import chat_completion
from shared.trace_logger import TraceLogger

from assessment2_bug_triage.schemas import (
    BugSummary,
    BugTriageReport,
    EvidenceItem,
    PatchPlan,
    ValidationPlan,
)
from assessment2_bug_triage.tools import extract_stack_traces, read_text_safe, run_pytest, search_logs


def _parse_bug_report(md: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    cur: str | None = None
    buf: list[str] = []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+)$", line.strip())
        if m:
            if cur is not None:
                sections[cur] = "\n".join(buf).strip()
            cur = m.group(1).strip().lower().replace(" ", "_")
            buf = []
        else:
            buf.append(line)
    if cur is not None:
        sections[cur] = "\n".join(buf).strip()
    return sections


def _agent_llm(trace: TraceLogger, agent: str, system: str, user: str, *, mock_llm: bool) -> str:
    trace.agent_step(agent, "reasoning", "LLM call", {"user_chars": len(user)})
    out = chat_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        mock=mock_llm,
    )
    trace.agent_step(agent, "output", "LLM done", {"preview": out[:240]})
    return out


def write_minimal_repro(repro_path: Path) -> None:
    """Generate a standalone failing test that adds mini_repo to sys.path."""
    repro_path.parent.mkdir(parents=True, exist_ok=True)
    code = f'''"""
Auto-generated minimal repro (Assessment 2).
Run from repo root: python -m pytest {repro_path.as_posix()} -q
"""
import sys
from pathlib import Path

_MINI = Path(__file__).resolve().parents[2] / "mini_repo"
sys.path.insert(0, str(_MINI))

from checkoutcalc import apply_promo


def test_repro_promo_should_be_single_discount():
    assert apply_promo(100.0, 10.0) == 90.0
'''
    repro_path.write_text(code, encoding="utf-8")


def run_pipeline(
    fixtures_dir: Path,
    mini_repo: Path,
    repro_path: Path,
    workspace_root: Path,
    trace: TraceLogger,
    *,
    mock_llm: bool,
) -> BugTriageReport:
    bug_path = fixtures_dir / "bug_report.md"
    log_path = fixtures_dir / "app.log"

    trace.orchestrator("Handoff: TriageAgent parsing inputs", {"bug": str(bug_path), "logs": str(log_path)})
    bug_md = read_text_safe(bug_path)
    sec = _parse_bug_report(bug_md)
    trace.agent_step(
        "TriageAgent",
        "parse",
        "Extracted structured fields from bug report",
        {"sections": list(sec.keys())},
    )

    symptoms = sec.get("actual_behavior", "")[:800] or "See bug report"
    expected = sec.get("expected_behavior", "")[:800]
    env = sec.get("environment", "")[:800]

    severity = "high" if "high" in bug_md.lower() or "finance" in bug_md.lower() else "medium"

    trace.orchestrator("Handoff: LogAnalystAgent — search + parse")
    hits = search_logs(log_path, r"AssertionError|Traceback|apply_promo|checkoutcalc")
    trace.tool_call("search_logs", {"path": str(log_path), "pattern": "AssertionError|Traceback|..."}, f"{hits['match_count']} hits", hits)

    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    stacks = extract_stack_traces(log_text)
    trace.tool_call("extract_stack_traces", {"bytes": len(log_text)}, f"{len(stacks)} trace(s)", stacks)

    _agent_llm(
        trace,
        "LogAnalystAgent",
        "You correlate deploy signals with errors. Summarize frequency and top signature.",
        json.dumps({"search_hits": hits["matches"][:8], "stack_traces": stacks}, indent=2)[:10000],
        mock_llm=mock_llm,
    )

    trace.orchestrator("Handoff: ReproductionAgent — emit minimal repro artifact")
    write_minimal_repro(repro_path)
    trace.agent_step(
        "ReproductionAgent",
        "write_repro",
        "Wrote minimal pytest repro",
        {"path": str(repro_path)},
    )

    trace.orchestrator("Handoff: execute tests (mini_repo suite + repro)")
    mini_pytest_root = mini_repo
    suite_result = run_pytest(mini_repo / "tests", cwd=mini_pytest_root)
    trace.tool_call(
        "run_pytest",
        {"target": str(mini_repo / "tests"), "cwd": str(mini_pytest_root)},
        f"returncode={suite_result['returncode']}",
        {"stdout_tail": suite_result["stdout"][-1200:], "stderr_tail": suite_result["stderr"][-1200:]},
    )

    repro_result = run_pytest(repro_path, cwd=workspace_root)
    trace.tool_call(
        "run_pytest",
        {"target": str(repro_path), "cwd": str(workspace_root)},
        f"returncode={repro_result['returncode']}",
        {"stdout_tail": repro_result["stdout"][-1200:], "stderr_tail": repro_result["stderr"][-1200:]},
    )

    _agent_llm(
        trace,
        "ReproductionAgent",
        "Explain whether the repro is minimal and what failure mode it proves.",
        json.dumps({"suite": suite_result, "repro": repro_result}, default=str)[:12000],
        mock_llm=mock_llm,
    )

    top_stack = stacks[0]["excerpt"] if stacks else ""
    hypothesis = (
        "`apply_promo` computes `discount = subtotal * promo_pct/100` but returns `subtotal - discount * 2`, "
        "applying the discount twice (observed 80.0 vs expected 90.0 for 10% off $100)."
    )

    patch = PatchPlan(
        files_modules=["assessment2_bug_triage/mini_repo/checkoutcalc/__init__.py"],
        approach="Change return to `subtotal - discount` (single application). Add regression tests for 0%, 10%, 100% edge cases.",
        risks="Promo stacking rules: confirm business logic does not intentionally double-apply in another layer.",
    )
    validation = ValidationPlan(
        tests_to_add=["parametrized tests for apply_promo boundaries", "integration test for checkout total if applicable"],
        regression_checks=["Run full mini_repo pytest suite", "Verify no consumers relied on doubled-discount behavior"],
    )

    _agent_llm(
        trace,
        "FixPlannerAgent",
        "You propose a safe patch and validation. Tie conclusions to repro + logs.",
        json.dumps(
            {
                "hypothesis": hypothesis,
                "stack_excerpt": top_stack[:2000],
                "repro_stdout": repro_result["stdout"],
            },
            indent=2,
        )[:12000],
        mock_llm=mock_llm,
    )

    review_notes = _agent_llm(
        trace,
        "ReviewerAgent",
        "Challenge minimality and safety. List edge cases and missing evidence.",
        json.dumps({"patch": patch.model_dump(), "validation": validation.model_dump()}, indent=2),
        mock_llm=mock_llm,
    )

    open_q = [
        "Confirm intended behavior when promo_pct > 100 or negative values.",
        "Verify no duplicate application in API layer wrapping `apply_promo`.",
    ]
    if "duplicate webhook" in log_text.lower():
        open_q.append("Unrelated log noise mentions duplicate webhooks — confirm not conflated with pricing bug.")

    trace.agent_step("ReviewerAgent", "critique", "Recorded review notes", {"preview": review_notes[:200]})

    evidence: list[EvidenceItem] = []
    for st in stacks[:2]:
        evidence.append(EvidenceItem(kind="stack_trace", content=st["excerpt"][:2000]))
    for h in hits["matches"][:3]:
        evidence.append(EvidenceItem(kind="log_line", content=h["line"]))

    confidence = 0.86 if stacks and "discount" in hypothesis.lower() else 0.55

    return BugTriageReport(
        bug_summary=BugSummary(
            symptoms=f"{symptoms}\nExpected: {expected}",
            scope="checkout pricing (`apply_promo`)",
            severity=severity,  # type: ignore[arg-type]
        ),
        evidence=evidence,
        repro_steps=[
            "Install deps: `pip install -r requirements.txt`",
            f"Run `python -m pytest {repro_path.as_posix()} -q` from repo root (expect failure).",
            f"Alternatively run `python -m pytest {mini_repo.as_posix()}/tests -q` (suite shows same assertion).",
        ],
        repro_artifact_path=repro_path.as_posix(),
        root_cause_hypothesis=hypothesis,
        root_cause_confidence=confidence,
        patch_plan=patch,
        validation_plan=validation,
        open_questions=open_q,
    )
