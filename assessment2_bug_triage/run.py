from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from shared.trace_logger import TraceLogger

from assessment2_bug_triage.orchestrator import run_pipeline


def main() -> None:
    p = argparse.ArgumentParser(description="Assessment 2: bug triage multi-agent pipeline")
    root = Path(__file__).resolve().parents[1]
    p.add_argument("--fixtures", type=Path, default=Path(__file__).resolve().parent / "fixtures")
    p.add_argument("--mini-repo", type=Path, default=Path(__file__).resolve().parent / "mini_repo")
    p.add_argument("--workspace-root", type=Path, default=root, help="Repo root for pytest cwd resolution")
    p.add_argument(
        "--repro-out",
        type=Path,
        default=Path(__file__).resolve().parent / "artifacts" / "repro" / "test_repro_checkout.py",
    )
    p.add_argument("--out", type=Path, default=Path("artifacts/bug_triage_result.yaml"))
    p.add_argument("--format", choices=("json", "yaml"), default="yaml")
    p.add_argument("--trace-file", type=Path, default=Path("artifacts/traces/assessment2_trace.jsonl"))
    p.add_argument("--mock-llm", action="store_true")
    args = p.parse_args()

    trace = TraceLogger(file_path=args.trace_file)
    trace.orchestrator("Starting Assessment 2 pipeline", {"mock_llm": args.mock_llm})

    report = run_pipeline(
        args.fixtures,
        args.mini_repo,
        args.repro_out,
        args.workspace_root,
        trace,
        mock_llm=args.mock_llm,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump()
    if args.format == "json":
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        args.out.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    print(yaml.safe_dump(payload, sort_keys=False))
    trace.orchestrator("Wrote structured triage output", {"path": str(args.out)})


if __name__ == "__main__":
    main()
    sys.exit(0)
