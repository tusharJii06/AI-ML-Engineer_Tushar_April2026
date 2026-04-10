from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BugSummary(BaseModel):
    symptoms: str
    scope: str
    severity: Literal["low", "medium", "high", "critical"]


class EvidenceItem(BaseModel):
    kind: Literal["log_line", "stack_trace"]
    content: str


class PatchPlan(BaseModel):
    files_modules: list[str]
    approach: str
    risks: str


class ValidationPlan(BaseModel):
    tests_to_add: list[str]
    regression_checks: list[str]


class BugTriageReport(BaseModel):
    bug_summary: BugSummary
    evidence: list[EvidenceItem]
    repro_steps: list[str]
    repro_artifact_path: str
    root_cause_hypothesis: str
    root_cause_confidence: float = Field(ge=0.0, le=1.0)
    patch_plan: PatchPlan
    validation_plan: ValidationPlan
    open_questions: list[str]
