from typing import List
from .models import OpportunityInput, ScoreBreakdown

def clamp_int(x: float, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, round(x))))

def compute_roi(cost: float, earnings: float) -> float:
    if cost <= 0:
        return 10.0 if earnings > 0 else 0.0
    return (earnings - cost) / cost

def roi_to_score(roi: float) -> int:
    if roi <= -0.25: return 0
    if roi <= 0: return 8
    if roi <= 0.5: return 16
    if roi <= 1.0: return 22
    if roi <= 2.0: return 27
    return 30

def feasibility_to_score(expected_time_days: int, can_close: bool) -> int:
    time_score = 25
    if expected_time_days > 120: time_score = 10
    elif expected_time_days > 60: time_score = 16
    elif expected_time_days > 30: time_score = 20
    elif expected_time_days > 14: time_score = 22
    close_bonus = 0 if can_close else -8
    return clamp_int(time_score + close_bonus, 0, 25)

def client_level_risk_modifier(level: str) -> int:
    return {"sensitive": -12, "high": -7, "normal": 0, "low": 3}.get(level, 0)

def risk_to_score(risks_text: str, client_level: str) -> int:
    base = 20
    t = (risks_text or "").lower()
    penalties = 0
    keywords = {
        "scope": 4, "unclear": 4, "urgent": 3, "deadline": 3,
        "legal": 6, "refund": 5, "complaint": 4, "chargeback": 6,
        "security": 5, "integration": 3, "api": 2, "unknown": 3,
        "no budget": 7, "delay": 3,
    }
    for k, p in keywords.items():
        if k in t:
            penalties += p
    score = base - penalties + client_level_risk_modifier(client_level)
    return clamp_int(score, 0, 25)

def motivation_to_score(excitement_level: int) -> int:
    return clamp_int((excitement_level / 10) * 20, 0, 20)

def red_flags(inp: OpportunityInput, roi: float) -> List[str]:
    flags = []
    if roi < 0:
        flags.append("Negative ROI (loss expected).")
    if inp.client_level in ("sensitive", "high") and inp.risks_and_concerns.strip():
        flags.append("High-sensitivity client + stated risks.")
    if not inp.can_close_within_timeframe:
        flags.append("You indicated you can't close within the timeframe.")
    if inp.expected_time_days > 120:
        flags.append("Very long expected time (>120 days).")
    if inp.cost_to_fulfill == 0 and inp.expected_earnings > 0:
        flags.append("Cost is 0 with positive earnings (confirm cost is truly zero).")
    return flags

def score_opportunity(inp: OpportunityInput) -> ScoreBreakdown:
    roi = compute_roi(inp.cost_to_fulfill, inp.expected_earnings)
    roi_score = roi_to_score(roi)  # 0..30
    feasibility_score = feasibility_to_score(inp.expected_time_days, inp.can_close_within_timeframe)  # 0..25
    risk_score = risk_to_score(inp.risks_and_concerns, inp.client_level)  # 0..25
    motivation_score = motivation_to_score(inp.excitement_level)  # 0..20
    total = roi_score + feasibility_score + risk_score + motivation_score  # 0..100

    return ScoreBreakdown(
        roi=float(round(roi, 4)),
        roi_score=roi_score,
        feasibility_score=feasibility_score,
        risk_score=risk_score,
        motivation_score=motivation_score,
        total_score=clamp_int(total, 0, 100),
        red_flags=red_flags(inp, roi),
    )
