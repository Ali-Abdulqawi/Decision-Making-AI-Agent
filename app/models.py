from typing import Literal, List
from pydantic import BaseModel, Field, conint, confloat

ClientLevel = Literal["sensitive", "high", "normal", "low"]
Decision = Literal["ACCEPT", "REJECT", "NEEDS_INFO"]

class OpportunityInput(BaseModel):
    opportunity_title: str = Field(..., min_length=3, max_length=120)
    client_type: str = Field(..., min_length=2, max_length=80)
    description: str = Field(..., min_length=10, max_length=4000)

    expected_time_days: conint(ge=1, le=365)

    cost_to_fulfill: confloat(ge=0)
    expected_earnings: confloat(ge=0)

    expected_benefits: str = Field(..., min_length=3, max_length=1500)
    can_close_within_timeframe: bool

    risks_and_concerns: str = Field(default="", max_length=2000)

    excitement_level: conint(ge=0, le=10)
    client_level: ClientLevel

class ScoreBreakdown(BaseModel):
    roi: float
    roi_score: int
    feasibility_score: int
    risk_score: int
    motivation_score: int
    total_score: int
    red_flags: List[str] = []

class DecisionOutput(BaseModel):
    decision: Decision
    confidence: conint(ge=0, le=100)
    summary: str = Field(..., min_length=5, max_length=300)
    key_reasons: List[str] = Field(default_factory=list, max_length=7)
    risks: List[str] = Field(default_factory=list, max_length=7)
    next_actions: List[str] = Field(default_factory=list, max_length=7)
    score: ScoreBreakdown
