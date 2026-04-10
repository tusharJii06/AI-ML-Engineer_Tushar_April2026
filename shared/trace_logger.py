from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class TraceLogger:
    """Structured traces to stdout and optional file (assessment requirement: traceability)."""

    file_path: Path | None = None
    _lines: list[str] = field(default_factory=list)

    def _emit(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False, default=str)
        print(line, file=sys.stderr)
        self._lines.append(line)
        if self.file_path:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def agent_step(self, agent: str, phase: str, summary: str, details: dict[str, Any] | None = None) -> None:
        self._emit(
            {
                "ts": _ts(),
                "type": "agent",
                "agent": agent,
                "phase": phase,
                "summary": summary,
                "details": details or {},
            }
        )

    def tool_call(self, name: str, args: dict[str, Any], result_summary: str, result: Any = None) -> None:
        payload: dict[str, Any] = {
            "ts": _ts(),
            "type": "tool",
            "tool": name,
            "args": args,
            "result_summary": result_summary,
        }
        if result is not None and isinstance(result, (dict, list, str, int, float, bool)):
            payload["result"] = result
        self._emit(payload)

    def orchestrator(self, message: str, details: dict[str, Any] | None = None) -> None:
        self._emit({"ts": _ts(), "type": "orchestrator", "message": message, "details": details or {}})
