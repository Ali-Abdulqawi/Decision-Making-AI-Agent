from typing import List, Tuple
from .models import OpportunityInput, ScoreBreakdown


def clamp_int(x: float, lo: int, hi: int) -> int:
    return int(max(lo, min(hi, round(x))))


def compute_roi(cost: float, earnings: float) -> float:
    if cost <= 0:
        return 10.0 if earnings > 0 else 0.0
    return (earnings - cost) / cost


def roi_to_score(roi: float) -> int:
    # Stricter than before: a 20% return is a weak deal, not a decent one.
    if roi <= 0: return 0
    if roi <= 0.3: return 8
    if roi <= 0.6: return 14
    if roi <= 1.0: return 20
    if roi <= 2.0: return 26
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


# Each risk factor: (keywords that trigger it, penalty, plain-English explanation).
# One factor is counted once, even if several of its keywords appear.
RISK_FACTORS: List[Tuple[Tuple[str, ...], int, str]] = [
    (("payment after", "after delivery", "after the website goes live", "after it goes live",
      "pay later", "no deposit", "no upfront"), 7,
     "Payment only after delivery: you carry the full financial risk."),
    (("no budget", "low budget", "tight budget"), 7, "Client budget is missing or very limited."),
    (("scope creep", "scope", "keep changing", "keeps changing", "changing what they want",
      "changing requirements"), 5, "Scope is likely to grow beyond what was priced."),
    (("unclear", "no clear", "vague", "not defined", "no requirements"), 5,
     "Requirements are not clearly defined."),
    (("unrealistic", "impossible", "too short"), 5, "The timeline looks unrealistic for this scope."),
    (("urgent", "deadline", "rush", "asap"), 3, "Tight deadline increases pressure and error risk."),
    (("legal", "contract", "compliance"), 6, "Legal or contract requirements need review."),
    (("refund", "chargeback"), 6, "Refund or chargeback exposure."),
    (("complaint", "difficult client", "bad reviews"), 4, "Signs of a difficult client relationship."),
    (("discount", "lower the price", "negotiate down"), 3,
     "Client is already pushing on price."),
    (("security", "sensitive data", "personal data"), 5, "Security or data-protection responsibility."),
    (("integration", "api", "pos", "third-party", "third party"), 3,
     "Third-party integrations can fail or take longer than planned."),
    (("revision", "revisions"), 2, "Revision rounds may eat into your time."),
    (("unknown", "not sure", "may not be possible"), 3, "Key parts are uncertain or untested."),
    (("delay",), 3, "Risk of delays."),
]


def detect_risk_factors(*texts: str) -> List[Tuple[int, str]]:
    """Return (penalty, explanation) for every risk factor found in the given texts."""
    t = " ".join(x or "" for x in texts).lower()
    found = []
    for keywords, penalty, explanation in RISK_FACTORS:
        if any(k in t for k in keywords):
            found.append((penalty, explanation))
    return found


def risk_to_score(risks_text: str, client_level: str, description: str = "") -> int:
    # Higher = safer. Reads both the risks field and the description.
    base = 20
    penalties = sum(p for p, _ in detect_risk_factors(risks_text, description))
    score = base - penalties + client_level_risk_modifier(client_level)
    return clamp_int(score, 0, 25)


def motivation_to_score(excitement_level: int) -> int:
    return clamp_int((excitement_level / 10) * 20, 0, 20)


def red_flags(inp: OpportunityInput, roi: float) -> List[str]:
    flags = []
    if roi < 0:
        flags.append("Negative ROI: you would lose money on this deal.")
    elif roi < 0.3:
        flags.append(f"Very thin margin (ROI {roi:.2f}): little room for surprises.")
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
    risk_score = risk_to_score(inp.risks_and_concerns, inp.client_level, inp.description)  # 0..25
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
