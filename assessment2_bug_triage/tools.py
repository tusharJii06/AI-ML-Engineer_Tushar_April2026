from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def search_logs(log_path: Path, pattern: str, max_lines: int = 200) -> dict[str, Any]:
    """Ripgrep-like search using regex over a log file (stdlib; no external rg required)."""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    rx = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
    matches = []
    for i, line in enumerate(text.splitlines(), start=1):
        if rx.search(line):
            matches.append({"line_no": i, "line": line[:500]})
        if len(matches) >= max_lines:
            break
    return {"pattern": pattern, "match_count": len(matches), "matches": matches}


def extract_stack_traces(log_text: str) -> list[dict[str, Any]]:
    """Extract traceback blocks from noisy logs (stop at next ISO-timestamp line)."""
    blocks: list[dict[str, Any]] = []
    lines = log_text.splitlines()
    i = 0
    ts = re.compile(r"^\d{4}-\d{2}-\d{2}T")
    while i < len(lines):
        if lines[i].strip() == "Traceback (most recent call last):":
            start = i
            j = i + 1
            while j < len(lines):
                if ts.match(lines[j]) and not lines[j].lstrip().startswith(" "):
                    break
                j += 1
            block_lines = lines[start:j]
            excerpt = "\n".join(block_lines).strip()
            m_file = re.search(r'File "([^"]+)", line (\d+), in (\w+)', excerpt)
            m_err = re.search(r"^(\w+Error|AssertionError):.*$", excerpt, re.MULTILINE)
            blocks.append(
                {
                    "excerpt": excerpt[:4000],
                    "file": m_file.group(1) if m_file else None,
                    "line": int(m_file.group(2)) if m_file else None,
                    "function": m_file.group(3) if m_file else None,
                    "error_type": m_err.group(1) if m_err else None,
                }
            )
            i = j
            continue
        i += 1
    return blocks


def run_pytest(target: Path, *, cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    """Execute pytest as a subprocess (required tool usage: run tests)."""
    cmd = [sys.executable, "-m", "pytest", str(target), "-q", "--tb=short"]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env={**__import__("os").environ, **(env or {})},
        timeout=120,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-8000:],
    }


def read_text_safe(path: Path, limit: int = 200_000) -> str:
    return path.read_text(encoding="utf-8", errors="replace")[:limit]
