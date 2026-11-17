import json
import os
from typing import List, Optional

from .models import OpportunityInput, DecisionOutput
from .scoring import score_opportunity, detect_risk_factors

ACCEPT_THRESHOLD = 70
REJECT_THRESHOLD = 55
TARGET_ROI = 1.0  # used to suggest a counter-offer price (earnings = 2x cost)


# ----------------------------------------------------------------------
# Optional LLM review (OpenAI). Runs only if OPENAI_API_KEY is set;
# otherwise the agent stays fully rule-based and still works.
# ----------------------------------------------------------------------
def llm_review(inp: OpportunityInput, decision: str, score: dict) -> Optional[dict]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=20)
        prompt = f"""You are a business advisor helping a freelancer decide on an opportunity.
The rule-based scoring already decided: {decision} (score {score['total_score']}/100).

Opportunity:
- Title: {inp.opportunity_title}
- Client type: {inp.client_type} (client level: {inp.client_level})
- Description: {inp.description}
- Time: {inp.expected_time_days} days, cost {inp.cost_to_fulfill}, earnings {inp.expected_earnings}
- Benefits: {inp.expected_benefits}
- Can close in time: {inp.can_close_within_timeframe}
- Stated risks: {inp.risks_and_concerns}

Return JSON only, with keys:
"insight": one or two sentences of judgement specific to this opportunity,
"hidden_risks": up to 3 risks the freelancer did NOT mention (short sentences),
"next_actions": up to 3 concrete next steps for this exact deal (short sentences)."""
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return None  # never let the LLM break the app


def _confidence(decision: str, total: int) -> int:
    # Further from the threshold = more confident.
    if decision == "ACCEPT":
        return min(95, 60 + (total - ACCEPT_THRESHOLD) * 2)
    if decision == "REJECT":
        return min(95, 60 + (REJECT_THRESHOLD - total) * 2)
    return 50


def mock_decision(inp: OpportunityInput) -> DecisionOutput:
    s = score_opportunity(inp)
    profit = inp.expected_earnings - inp.cost_to_fulfill

    # ------------------------
    # Decision logic
    # ------------------------
    if s.roi < 0:
        decision = "REJECT"  # never accept a deal that loses money
    elif s.total_score > ACCEPT_THRESHOLD:
        decision = "ACCEPT"
    elif s.total_score < REJECT_THRESHOLD:
        decision = "REJECT"
    else:
        decision = "NEEDS_INFO"
    confidence = _confidence(decision, s.total_score)

    # ------------------------
    # Strengths and weaknesses
    # ------------------------
    strengths: List[str] = []
    weaknesses: List[str] = []

    if s.roi >= 1.0:
        strengths.append(f"Strong return: {profit:,.0f} profit (ROI {s.roi:.2f}).")
    elif s.roi >= 0.3:
        strengths.append(f"Acceptable return: {profit:,.0f} profit (ROI {s.roi:.2f}).")
    elif s.roi >= 0:
        weaknesses.append(f"Weak return: only {profit:,.0f} profit for "
                          f"{inp.expected_time_days} days of work (ROI {s.roi:.2f}).")
    else:
        weaknesses.append(f"Loss-making: you would lose {abs(profit):,.0f} (ROI {s.roi:.2f}).")

    if s.feasibility_score >= 22:
        strengths.append(f"Feasible timeline ({inp.expected_time_days} days) and you can close it.")
    else:
        weaknesses.append(f"Feasibility is limited ({s.feasibility_score}/25).")

    if s.risk_score >= 15:
        strengths.append(f"Low risk ({s.risk_score}/25).")
    elif s.risk_score < 10:
        weaknesses.append(f"High risk ({s.risk_score}/25, higher = safer).")

    if inp.excitement_level >= 7:
        strengths.append(f"You are motivated ({inp.excitement_level}/10).")
    elif inp.excitement_level <= 3:
        weaknesses.append(f"Low personal motivation ({inp.excitement_level}/10).")

    benefits = inp.expected_benefits.lower()
    has_upside = any(w in benefits for w in ("retainer", "referral", "monthly", "long-term"))
    negated = any(n in benefits for n in ("no retainer", "no referral", "not expected", "one-time"))
    if has_upside and not negated:
        strengths.append("Long-term upside beyond this project (retainer or referrals).")

    # Lead with what explains the decision.
    if decision == "ACCEPT":
        key_reasons = strengths + weaknesses
    elif decision == "REJECT":
        key_reasons = weaknesses + strengths
    else:
        key_reasons = weaknesses + strengths

    # ------------------------
    # Risks (explained, not echoed back)
    # ------------------------
    risks: List[str] = list(s.red_flags)
    for _, explanation in detect_risk_factors(inp.risks_and_concerns, inp.description):
        if explanation not in risks:
            risks.append(explanation)

    # ------------------------
    # Next actions (always specific)
    # ------------------------
    text = f"{inp.risks_and_concerns} {inp.description}".lower()
    next_actions: List[str] = []

    if s.roi < TARGET_ROI:
        target_price = inp.cost_to_fulfill * (1 + TARGET_ROI)
        next_actions.append(
            f"Counter-offer at about {target_price:,.0f} (instead of {inp.expected_earnings:,.0f}) "
            f"or reduce the scope to bring cost down."
        )
    if any(k in text for k in ("after delivery", "payment after", "goes live", "pay later", "no deposit")):
        next_actions.append("Require a 50% upfront deposit before starting.")
    if any(k in text for k in ("unclear", "no clear", "vague", "scope", "changing")):
        next_actions.append("Write a one-page scope: what is included, what is not, and the revision limit.")
    if not inp.can_close_within_timeframe or "unrealistic" in text:
        next_actions.append("Propose a realistic timeline, or split the work into phases with separate deadlines.")
    if any(k in text for k in ("integration", "api", "pos")):
        next_actions.append("Check the integration is technically possible before committing to it.")

    if decision == "ACCEPT":
        next_actions.insert(0, "Send a proposal with scope, timeline, payment milestones and revision limit.")
    elif decision == "REJECT" and next_actions:
        next_actions.insert(0, "Decline as offered. Reconsider only if the client accepts these terms:")
    elif decision == "REJECT":
        next_actions.append("Decline politely and keep the relationship open for future work.")
    elif decision == "NEEDS_INFO":
        next_actions += [
            "Clarify exact deliverables (what is in-scope vs out-of-scope).",
            "Confirm payment terms and any upfront deposit.",
            "Confirm timeline + who provides content/assets.",
        ]

    # ------------------------
    # Optional AI review
    # ------------------------
    score_dict = {
        "roi": s.roi,
        "roi_score": s.roi_score,
        "feasibility_score": s.feasibility_score,
        "risk_score": s.risk_score,
        "motivation_score": s.motivation_score,
        "total_score": s.total_score,
        "red_flags": s.red_flags,
    }
    summary = (f"{decision}: Score {s.total_score}/100. ROI={s.roi:.2f}, "
               f"Risk={s.risk_score}/25, Feasibility={s.feasibility_score}/25.")

    review = llm_review(inp, decision, score_dict)
    if review:
        if review.get("insight"):
            summary += f" AI insight: {review['insight']}"
        risks += [f"(AI) {r}" for r in review.get("hidden_risks", [])[:3]]
        next_actions += [f"(AI) {a}" for a in review.get("next_actions", [])[:3]]

    return DecisionOutput(
        decision=decision,
        confidence=confidence,
        summary=summary,
        key_reasons=key_reasons,
        risks=risks,
        next_actions=next_actions,
        score=score_dict,
    )
