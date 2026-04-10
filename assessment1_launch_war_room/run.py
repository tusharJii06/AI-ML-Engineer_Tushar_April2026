from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from shared.trace_logger import TraceLogger

from assessment1_launch_war_room.orchestrator import run_war_room


def main() -> None:
    p = argparse.ArgumentParser(description="Assessment 1: launch war room multi-agent run")
    p.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "data",
        help="Directory containing metrics.csv, feedback.txt, release_notes.md",
    )
    p.add_argument("--out", type=Path, default=Path("artifacts/launch_decision.json"))
    p.add_argument("--format", choices=("json", "yaml"), default="json")
    p.add_argument("--trace-file", type=Path, default=Path("artifacts/traces/assessment1_trace.jsonl"))
    p.add_argument("--mock-llm", action="store_true", help="Deterministic run without calling external LLM API")
    args = p.parse_args()

    trace = TraceLogger(file_path=args.trace_file)
    trace.orchestrator("Starting Assessment 1 pipeline", {"data_dir": str(args.data_dir), "mock_llm": args.mock_llm})

    decision = run_war_room(args.data_dir, trace, mock_llm=args.mock_llm)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = decision.model_dump()
    if args.format == "json":
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        args.out.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    trace.orchestrator("Wrote final structured output", {"path": str(args.out)})


if __name__ == "__main__":
    main()
    sys.exit(0)
