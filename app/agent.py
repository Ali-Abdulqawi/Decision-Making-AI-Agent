from typing import List
from .models import OpportunityInput, DecisionOutput
from .scoring import score_opportunity


def mock_decision(inp: OpportunityInput) -> DecisionOutput:
    # Run deterministic scoring
    s = score_opportunity(inp)

    # ------------------------
    # Decision logic
    # ------------------------
    if s.total_score > 70:
        decision = "ACCEPT"
        confidence = 85

    elif s.total_score < 55:
        decision = "REJECT"
        confidence = 75

    else:
        decision = "NEEDS_INFO"
        confidence = 50

    # ------------------------
    # Reasons & risks
    # ------------------------
    key_reasons: List[str] = []
    risks: List[str] = []

    if s.roi > 0:
        key_reasons.append(f"Positive ROI ({s.roi:.2f}).")

    key_reasons.append(
        f"Feasibility score: {s.feasibility_score}/25 (time + ability)."
    )
    key_reasons.append(
        f"Risk score: {s.risk_score}/25 (client level + concerns)."
    )

    if s.red_flags:
        risks.extend(s.red_flags)

    if inp.risks_and_concerns:
        risks.append(f"Review stated concerns: {inp.risks_and_concerns}")

    # ------------------------
    # Next actions
    # ------------------------
    next_actions: List[str] = []

    if decision == "NEEDS_INFO":
        next_actions = [
            "Clarify exact deliverables (what is in-scope vs out-of-scope).",
            "Confirm payment terms and any upfront deposit.",
            "Confirm timeline + who provides content/assets.",
        ]

    # ------------------------
    # Final output
    # ------------------------
    return DecisionOutput(
        decision=decision,
        confidence=confidence,
        summary=(
            f"{decision}: Score {s.total_score}/100. "
            f"ROI={s.roi:.2f}, "
            f"Risk={s.risk_score}/25, "
            f"Feasibility={s.feasibility_score}/25."
        ),
        key_reasons=key_reasons,
        risks=risks,
        next_actions=next_actions,
        score={
            "roi": s.roi,
            "roi_score": s.roi_score,
            "feasibility_score": s.feasibility_score,
            "risk_score": s.risk_score,
            "motivation_score": s.motivation_score,
            "total_score": s.total_score,
            "red_flags": s.red_flags,
        },
    )

