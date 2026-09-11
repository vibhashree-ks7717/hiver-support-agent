from response_retriever import analyze_customer_message
from reply_generator import generate_reply
from escalation_agent import escalation_decision
from intent_predictor import predict_intent_with_confidence


def run_support_agent(customer_message):

    # ---------------------------------------------------------
    # 1. INTENT + REAL CONFIDENCE
    # ---------------------------------------------------------

    prediction = predict_intent_with_confidence(customer_message)

    intent = prediction["intent"]
    confidence = prediction["confidence"]

    # ---------------------------------------------------------
    # 2. HISTORICAL SUPPORT RETRIEVAL
    # ---------------------------------------------------------

    analysis = analyze_customer_message(
        customer_message,
        top_k=5
    )

    historical_cases = analysis["historical_cases"]

    # ---------------------------------------------------------
    # 3. GENERATE GROUNDED REPLY
    # ---------------------------------------------------------

    reply_result = generate_reply(customer_message)

    reply = reply_result["reply"]
    generation_mode = reply_result["generation_mode"]

    # ---------------------------------------------------------
    # 4. ESCALATION DECISION
    # ---------------------------------------------------------

    decision = escalation_decision(
        customer_message=customer_message,
        predicted_intent=intent,
        intent_confidence=confidence,
        historical_cases=historical_cases
    )

    # ---------------------------------------------------------
    # 5. FINAL RESULT
    # ---------------------------------------------------------

    return {
        "customer_message": customer_message,
        "intent": intent,
        "intent_confidence": confidence,
        "historical_cases": historical_cases,
        "reply": reply,
        "generation_mode": generation_mode,
        "decision": decision["decision"],
        "escalation_score": decision["score"],
        "escalation_reasons": decision["reasons"]
    }


# =============================================================
# TESTING
# =============================================================

if __name__ == "__main__":

    test_cases = [
        "My package was supposed to arrive yesterday but I still haven't received it.",
        "I returned my item two weeks ago but I still haven't received my refund.",
        "This is ridiculous. I want to speak to a manager right now.",
        "I can't log into my Amazon account.",
        "I was charged twice for the same order."
    ]

    print("=" * 80)
    print("HIVER AI SUPPORT AGENT - COMPLETE PIPELINE")
    print("=" * 80)

    for i, message in enumerate(test_cases, 1):

        print("\n" + "=" * 80)
        print(f"TEST CASE {i}")
        print("=" * 80)

        result = run_support_agent(message)

        print("\nCUSTOMER MESSAGE:")
        print(result["customer_message"])

        print("\nINTENT:")
        print(result["intent"])

        print("\nINTENT CONFIDENCE:")
        print(f"{result['intent_confidence']:.4f}")

        print("\nGENERATED REPLY:")
        print(result["reply"])

        print("\nGENERATION MODE:")
        print(result["generation_mode"])

        print("\nFINAL DECISION:")
        print(result["decision"])

        print("\nESCALATION SCORE:")
        print(result["escalation_score"])

        print("\nESCALATION REASONS:")

        for reason in result["escalation_reasons"]:
            print(f"- {reason}")

    print("\n" + "=" * 80)
    print("COMPLETE PIPELINE TEST FINISHED")
    print("=" * 80)