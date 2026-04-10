from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any


def load_metrics_csv(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out: dict[str, Any] = {"date": row["date"]}
            for k, v in row.items():
                if k == "date":
                    continue
                out[k] = float(v) if "." in v or "e" in v.lower() else int(v)
            rows.append(out)
    return rows


def aggregate_metrics(rows: list[dict[str, Any]], numeric_keys: list[str]) -> dict[str, Any]:
    """Rollups: latest vs first week mean, last-3-day mean."""
    if not rows:
        return {}
    n = len(rows)
    mid = max(1, n // 2)
    first = rows[:mid]
    last3 = rows[-3:] if n >= 3 else rows

    def mean_block(block: list[dict[str, Any]], key: str) -> float:
        vals = [float(r[key]) for r in block if key in r]
        return sum(vals) / len(vals) if vals else 0.0

    summary: dict[str, Any] = {"days": n, "series": {}}
    for key in numeric_keys:
        summary["series"][key] = {
            "first_half_mean": round(mean_block(first, key), 4),
            "last_3d_mean": round(mean_block(last3, key), 4),
            "latest": rows[-1].get(key),
        }
    return summary


def detect_anomalies(
    rows: list[dict[str, Any]],
    key: str,
    z_threshold: float = 2.0,
) -> dict[str, Any]:
    """Simple z-score anomaly on a single series."""
    vals = [float(r[key]) for r in rows if key in r]
    if len(vals) < 3:
        return {"key": key, "anomalies": [], "note": "insufficient data"}
    mu = sum(vals) / len(vals)
    var = sum((x - mu) ** 2 for x in vals) / len(vals)
    sigma = math.sqrt(var) or 1e-9
    anomalies: list[dict[str, Any]] = []
    for i, v in enumerate(vals):
        z = abs((v - mu) / sigma)
        if z >= z_threshold:
            anomalies.append({"index": i, "date": rows[i].get("date"), "value": v, "z": round(z, 2)})
    return {"key": key, "mean": round(mu, 4), "stdev": round(sigma, 4), "anomalies": anomalies}


def compare_trends(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    """Compare mean of first third vs last third."""
    n = len(rows)
    if n < 6:
        return {"key": key, "direction": "flat", "delta_pct": 0.0}
    third = n // 3
    a = [float(r[key]) for r in rows[:third]]
    b = [float(r[key]) for r in rows[-third:]]
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    delta_pct = ((mb - ma) / ma * 100) if ma else 0.0
    if delta_pct > 3:
        direction = "up"
    elif delta_pct < -3:
        direction = "down"
    else:
        direction = "flat"
    return {"key": key, "direction": direction, "delta_pct": round(delta_pct, 2), "early_mean": ma, "late_mean": mb}


def summarize_feedback_sentiment(feedback_lines: list[str]) -> dict[str, Any]:
    """Lexicon-based sentiment + theme counts (tool, not prompt-only)."""
    pos = re.compile(
        r"\b(love|great|fast|smooth|awesome|works|helpful|easy|nice|good|excellent)\b",
        re.I,
    )
    neg = re.compile(
        r"\b(bug|crash|error|slow|broken|fail|terrible|awful|refund|stuck|latency|timeout|worst)\b",
        re.I,
    )
    scores: list[int] = []
    themes: Counter[str] = Counter()
    for line in feedback_lines:
        p = len(pos.findall(line))
        n = len(neg.findall(line))
        scores.append(1 if p > n else -1 if n > p else 0)
        low = line.lower()
        if "payment" in low or "checkout" in low:
            themes["payment_checkout"] += 1
        if "latency" in low or "slow" in low:
            themes["performance"] += 1
        if "crash" in low or "error" in low:
            themes["stability"] += 1
        if "onboard" in low or "signup" in low:
            themes["activation"] += 1

    pos_n = sum(1 for s in scores if s > 0)
    neg_n = sum(1 for s in scores if s < 0)
    neu_n = len(scores) - pos_n - neg_n
    return {
        "counts": {"positive": pos_n, "negative": neg_n, "neutral": neu_n, "total": len(feedback_lines)},
        "themes": dict(themes.most_common(8)),
        "sample_negative": next((t for t in feedback_lines if neg.search(t)), None),
        "sample_positive": next((t for t in feedback_lines if pos.search(t)), None),
    }


def load_feedback_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip()]
