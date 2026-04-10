from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RiskItem(BaseModel):
    risk: str
    mitigation: str
    severity: Literal["low", "medium", "high"] = "medium"


class ActionItem(BaseModel):
    action: str
    owner: str
    window_hours: int = Field(ge=1, le=48, description="Within 24-48h window")


class CommunicationPlan(BaseModel):
    internal: str
    external: str


class LaunchDecision(BaseModel):
    decision: Literal["Proceed", "Pause", "Roll Back"]
    rationale: str = Field(description="Key drivers with metric references + feedback summary")
    risk_register: list[RiskItem]
    action_plan: list[ActionItem]
    communication_plan: CommunicationPlan
    confidence: float = Field(ge=0.0, le=1.0)
    what_would_increase_confidence: str
