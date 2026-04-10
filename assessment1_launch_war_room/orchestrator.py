from __future__ import annotations

import json
from pathlib import Path

from shared.llm import chat_completion
from shared.trace_logger import TraceLogger

from assessment1_launch_war_room.schemas import (
    ActionItem,
    CommunicationPlan,
    LaunchDecision,
    RiskItem,
)
from assessment1_launch_war_room.tools import (
    aggregate_metrics,
    compare_trends,
    detect_anomalies,
    load_feedback_file,
    load_metrics_csv,
    summarize_feedback_sentiment,
)


NUMERIC_KEYS = [
    "activation_rate",
    "dau",
    "retention_d1",
    "retention_d7",
    "error_rate",
    "p95_latency_ms",
    "support_tickets",
    "funnel_completion",
    "churn_rate",
]


def _agent_llm(
    trace: TraceLogger,
    agent: str,
    system: str,
    user: str,
    *,
    mock_llm: bool,
) -> str:
    trace.agent_step(agent, "reasoning", "Calling LLM for narrative", {"chars": len(user)})
    content = chat_completion(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        mock=mock_llm,
    )
    trace.agent_step(agent, "output", "LLM response received", {"preview": content[:280]})
    return content


def run_war_room(
    data_dir: Path,
    trace: TraceLogger,
    *,
    mock_llm: bool,
) -> LaunchDecision:
    metrics_path = data_dir / "metrics.csv"
    feedback_path = data_dir / "feedback.txt"
    release_path = data_dir / "release_notes.md"

    trace.orchestrator("Loading mock dashboard inputs", {"metrics": str(metrics_path)})

    rows = load_metrics_csv(metrics_path)
    feedback = load_feedback_file(feedback_path)
    release_notes = release_path.read_text(encoding="utf-8") if release_path.exists() else ""

    # --- Data Analyst: programmatic tools ---
    agg = aggregate_metrics(rows, NUMERIC_KEYS)
    trace.tool_call("aggregate_metrics", {"keys": NUMERIC_KEYS}, "Computed first-half vs last-3d rollups", agg)

    anom_err = detect_anomalies(rows, "error_rate", z_threshold=1.8)
    trace.tool_call("detect_anomalies", {"key": "error_rate"}, f"Found {len(anom_err['anomalies'])} points", anom_err)

    trend_lat = compare_trends(rows, "p95_latency_ms")
    trace.tool_call("compare_trends", {"key": "p95_latency_ms"}, trend_lat["direction"], trend_lat)

    sent = summarize_feedback_sentiment(feedback)
    trace.tool_call(
        "summarize_feedback_sentiment",
        {"lines": len(feedback)},
        f"pos={sent['counts']['positive']} neg={sent['counts']['negative']}",
        sent,
    )

    analyst_context = json.dumps(
        {"aggregate_metrics": agg, "error_rate_anomalies": anom_err, "p95_trend": trend_lat, "feedback": sent},
        indent=2,
    )[:12000]

    _agent_llm(
        trace,
        "DataAnalyst",
        "You are a data analyst. Summarize quantitative evidence in 5 bullet points. Reference concrete numbers.",
        analyst_context,
        mock_llm=mock_llm,
    )

    _agent_llm(
        trace,
        "ProductManager",
        "You are a PM. Frame go/no-go criteria vs observed metrics and user impact. Be concise.",
        analyst_context + "\n\nRelease notes:\n" + release_notes[:4000],
        mock_llm=mock_llm,
    )

    _agent_llm(
        trace,
        "MarketingComms",
        "You are marketing/comms. Propose internal and external messaging given mixed feedback and stability concerns.",
        analyst_context,
        mock_llm=mock_llm,
    )

    risk_user = (
        analyst_context
        + "\nChallenge optimistic interpretations. List top risks and what evidence is still missing."
    )
    _agent_llm(trace, "RiskCritic", "You are a skeptical risk officer.", risk_user, mock_llm=mock_llm)

    sre_slice = json.dumps(
        {
            "error_rate": agg["series"].get("error_rate"),
            "p95_latency_trend": trend_lat,
            "error_rate_anomalies": anom_err.get("anomalies", []),
        },
        indent=2,
    )
    _agent_llm(
        trace,
        "EngineeringSRE",
        "You are SRE. Assess error budget / SLO risk from metrics and suggest infra mitigations (caching, rollbacks, canaries).",
        sre_slice,
        mock_llm=mock_llm,
    )

    # --- Coordinator: merge tools + heuristics into structured decision ---
    trace.orchestrator("Coordinator synthesizing structured launch decision")

    last_err = float(rows[-1]["error_rate"])
    err_early = agg["series"]["error_rate"]["first_half_mean"]
    err_late3 = agg["series"]["error_rate"]["last_3d_mean"]
    tickets_late = agg["series"]["support_tickets"]["last_3d_mean"]
    tickets_early = agg["series"]["support_tickets"]["first_half_mean"]

    error_spike = err_late3 > err_early * 1.4 or last_err > 0.015
    latency_worse = trend_lat["direction"] == "up" and trend_lat["delta_pct"] > 5
    neg_ratio = sent["counts"]["negative"] / max(1, sent["counts"]["total"])
    stability_theme = sent["themes"].get("stability", 0) + sent["themes"].get("payment_checkout", 0)

    if error_spike and (latency_worse or neg_ratio >= 0.35):
        decision = "Roll Back"
    elif error_spike or (tickets_late > tickets_early * 1.15 and neg_ratio >= 0.28):
        decision = "Pause"
    else:
        decision = "Proceed"

    rationale = (
        f"Decision {decision} driven by tool outputs: error_rate latest={last_err:.3f} vs first_half_mean={err_early:.3f}; "
        f"last_3d_mean={err_late3:.3f}. p95 latency trend {trend_lat['direction']} ({trend_lat['delta_pct']}% vs early/late thirds). "
        f"Feedback sentiment: {sent['counts']['positive']} positive / {sent['counts']['negative']} negative / {sent['counts']['neutral']} neutral "
        f"with themes {list(sent['themes'].keys())[:5]}. Anomalies in error_rate series: {len(anom_err['anomalies'])} day(s) flagged."
    )

    risk_register = [
        RiskItem(
            risk="Payment/checkout instability may erode trust and increase refunds.",
            mitigation="Enable feature flag rollback; hotfix duplicate webhook handling; add canary on payment path.",
            severity="high" if stability_theme >= 4 else "medium",
        ),
        RiskItem(
            risk="Latency regression under peak load if regional caches are cold.",
            mitigation="Pre-warm caches; scale checkout workers; temporarily cap rollout percentage.",
            severity="medium",
        ),
        RiskItem(
            risk="Mixed customer perception could amplify social complaints if external comms lag reality.",
            mitigation="Publish known-issues page; proactive status updates; align support macros.",
            severity="medium",
        ),
    ]

    action_plan = [
        ActionItem(action="Triage payment errors with provider logs; confirm duplicate webhook hypothesis.", owner="Engineering", window_hours=24),
        ActionItem(action="Run anomaly dashboard review for error_rate, p95, support tickets; set alert thresholds.", owner="Data", window_hours=24),
        ActionItem(action="Draft internal summary + external status comms acknowledging elevated errors.", owner="Marketing", window_hours=36),
        ActionItem(action="Prepare staged rollback playbook and verify feature flag ownership.", owner="PM", window_hours=48),
    ]

    if decision == "Roll Back":
        action_plan.insert(
            0,
            ActionItem(action="Execute rollback to previous stable build for impacted cohorts.", owner="Engineering", window_hours=12),
        )

    comms = CommunicationPlan(
        internal="Share tool-derived summary: error_rate spike, latency trend, ticket volume vs baseline; explicit go/pause/rollback trigger table.",
        external="Transparent messaging: we are investigating elevated payment errors; workaround steps; ETA for update." if error_spike else "Positive rollout narrative with monitoring link; invite feedback channel.",
    )

    confidence = 0.55
    if len(anom_err["anomalies"]) <= 1 and not error_spike:
        confidence += 0.15
    if sent["counts"]["total"] >= 25:
        confidence += 0.1
    confidence = min(0.92, max(0.35, confidence))
    if decision == "Roll Back":
        confidence -= 0.05

    what_more = (
        "More confidence with longer post-fix bake time, provider-side confirmation of webhook behavior, "
        "and segmented error attribution (client vs server vs third-party)."
    )

    return LaunchDecision(
        decision=decision,  # type: ignore[arg-type]
        rationale=rationale,
        risk_register=risk_register,
        action_plan=action_plan,
        communication_plan=comms,
        confidence=round(confidence, 2),
        what_would_increase_confidence=what_more,
    )
