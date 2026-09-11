# ============================================================
# HIVER SUPPORT AGENT - ESCALATION AGENT
# ============================================================

ESCALATION_PHRASES = [
    "speak to a human",
    "talk to a human",
    "speak to someone",
    "talk to someone",
    "speak to an agent",
    "talk to an agent",
    "speak to a representative",
    "talk to a representative",
    "speak to a manager",
    "talk to a manager",
    "manager",
    "supervisor",
    "escalate",
    "escalation",
    "human agent",
    "real person"
]


FRUSTRATION_PHRASES = [
    "ridiculous",
    "terrible",
    "unacceptable",
    "worst",
    "angry",
    "frustrated",
    "disappointed",
    "useless",
    "horrible",
    "fed up",
    "sick of"
]


BILLING_RISK_PHRASES = [
    "charged twice",
    "charged two times",
    "double charged",
    "duplicate charge",
    "duplicate payment",
    "unauthorized charge",
    "unknown charge",
    "fraud",
    "stolen card",
    "card was stolen",
    "account hacked"
]


HIGH_RISK_INTENTS = [
    "Customer Service / Complaint"
]


def escalation_decision(
    customer_message,
    predicted_intent,
    intent_confidence,
    historical_cases
):

    message = customer_message.lower()

    score = 0
    reasons = []

    # --------------------------------------------------------
    # 1. EXPLICIT HUMAN REQUEST
    # --------------------------------------------------------

    human_request = any(
        phrase in message
        for phrase in ESCALATION_PHRASES
    )

    if human_request:
        score += 4
        reasons.append(
            "Customer explicitly requests human assistance or escalation."
        )

    # --------------------------------------------------------
    # 2. FRUSTRATION
    # --------------------------------------------------------

    frustration = any(
        phrase in message
        for phrase in FRUSTRATION_PHRASES
    )

    if frustration:
        score += 2
        reasons.append(
            "Customer language indicates strong frustration or dissatisfaction."
        )

    # --------------------------------------------------------
    # 3. COMPLAINT INTENT
    # --------------------------------------------------------

    if predicted_intent in HIGH_RISK_INTENTS:
        score += 2
        reasons.append(
            "The predicted intent is a customer-service complaint."
        )

    # --------------------------------------------------------
    # 4. BILLING / SECURITY RISK
    # --------------------------------------------------------

    billing_risk = any(
        phrase in message
        for phrase in BILLING_RISK_PHRASES
    )

    if billing_risk:
        score += 4
        reasons.append(
            "The message indicates a potentially sensitive billing or account-security issue requiring human review."
        )

    # --------------------------------------------------------
    # 5. LOW INTENT CONFIDENCE
    # --------------------------------------------------------

    if intent_confidence < 0.50:
        score += 2
        reasons.append(
            "Intent classification confidence is low."
        )

    # --------------------------------------------------------
    # 6. HISTORICAL EVIDENCE QUALITY
    # --------------------------------------------------------

    if not historical_cases:
        score += 2
        reasons.append(
            "No sufficiently similar historical support cases were retrieved."
        )

    else:

        best_similarity = historical_cases[0]["similarity"]

        if best_similarity < 0.25:
            score += 2
            reasons.append(
                "Historical support evidence is weak for this message."
            )

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    if score >= 3:

        decision = "ESCALATE"

    else:

        decision = "AUTO-HANDLE"

        reasons.append(
            "The issue appears suitable for an automated response based on intent confidence and historical support evidence."
        )

    return {
        "decision": decision,
        "score": score,
        "reasons": reasons
    }