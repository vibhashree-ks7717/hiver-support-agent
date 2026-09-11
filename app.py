"""
Flask Web App for the Hiver AI Customer Support Agent.

This web layer uses the actual support_pipeline.py so that
the browser demo matches the evaluated AI support pipeline.
"""

from flask import Flask, render_template, request, jsonify
import time

from support_pipeline import run_support_agent

app = Flask(__name__)

# Stores messages handled during the current app session
conversation_history = []


def get_first(result, *keys, default=None):
    """Return the first available value from a dictionary."""
    for key in keys:
        if key in result and result[key] is not None:
            return result[key]
    return default


def normalize_result(result, message):
    """
    Convert the support_pipeline result into a consistent
    format for the web frontend.
    """

    # ---------------------------------------------------------
    # INTENT
    # ---------------------------------------------------------
    intent = get_first(
        result,
        "predicted_intent",
        "intent",
        "predictedIntent",
        default="General / Other"
    )

    # ---------------------------------------------------------
    # CONFIDENCE
    # ---------------------------------------------------------
    confidence = get_first(
        result,
        "intent_confidence",
        "confidence",
        "confidence_score",
        "intentConfidence",
        default=0
    )

    try:
        confidence = float(confidence)

        # Pipeline normally returns confidence between 0 and 1.
        # Convert it to percentage for the UI.
        if confidence <= 1:
            confidence = confidence * 100

        confidence = round(confidence, 1)

    except (TypeError, ValueError):
        confidence = 0.0

    # ---------------------------------------------------------
    # REPLY
    # ---------------------------------------------------------
    reply = get_first(
        result,
        "reply",
        "generated_reply",
        "draft_reply",
        default="I am sorry, but I could not generate a response."
    )

    # ---------------------------------------------------------
    # ESCALATION
    # ---------------------------------------------------------
    escalation_value = get_first(
        result,
        "escalate",
        "should_escalate",
        "escalation",
        "escalation_decision",
        default=False
    )

    reasons = []

    # Sometimes escalation_decision is a dictionary.
    if isinstance(escalation_value, dict):

        escalate = bool(
            get_first(
                escalation_value,
                "escalate",
                "should_escalate",
                default=False
            )
        )

        decision_text = str(
            get_first(
                escalation_value,
                "decision",
                default=""
            )
        ).upper()

        if decision_text == "ESCALATE":
            escalate = True

        elif decision_text == "AUTO-HANDLE":
            escalate = False

        reasons = get_first(
            escalation_value,
            "reasons",
            default=[]
        ) or []

    else:
        # If pipeline directly returns True/False
        escalate = bool(escalation_value)

    # ---------------------------------------------------------
    # TOP-LEVEL DECISION
    # ---------------------------------------------------------
    decision_value = get_first(
        result,
        "decision",
        default=""
    )

    decision_text = str(decision_value).upper()

    if decision_text == "ESCALATE":
        escalate = True

    elif decision_text == "AUTO-HANDLE":
        escalate = False

    # ---------------------------------------------------------
    # ESCALATION REASONS
    # ---------------------------------------------------------
    top_reasons = get_first(
        result,
        "escalation_reasons",
        "reasons",
        default=[]
    )

    if isinstance(top_reasons, list) and top_reasons:
        reasons = top_reasons

    if not reasons:

        if escalate:
            reasons = [
                "The message meets the escalation rules."
            ]

        else:
            reasons = [
                "The issue is suitable for automated handling."
            ]

    # ---------------------------------------------------------
    # HISTORICAL CASES
    # ---------------------------------------------------------
    historical_cases = get_first(
        result,
        "historical_cases",
        "similar_cases",
        default=[]
    ) or []

    # ---------------------------------------------------------
    # FINAL WEB RESULT
    # ---------------------------------------------------------
    return {
        "success": True,
        "customer_message": message,
        "intent": str(intent),
        "confidence": confidence,
        "reply": str(reply),
        "escalate": escalate,
        "decision": "ESCALATE" if escalate else "AUTO-HANDLE",
        "reasons": reasons,
        "historical_cases": historical_cases
    }


# =============================================================
# HOME PAGE
# =============================================================

@app.route("/")
def home():
    return render_template("index.html")


# =============================================================
# CHAT API
# =============================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return jsonify({
            "error": "Empty message"
        }), 400

    start_time = time.time()

    try:

        # IMPORTANT:
        # Use the actual evaluated support pipeline.
        raw_result = run_support_agent(message)

        # Convert it into the format expected by index.html.
        result = normalize_result(
            raw_result,
            message
        )

        result["processing_time_ms"] = round(
            (time.time() - start_time) * 1000,
            2
        )

        # Save this conversation for statistics.
        conversation_history.append(result)

        return jsonify(result)

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": f"Support pipeline error: {exc}"
        }), 500


# =============================================================
# STATISTICS API
# =============================================================

@app.route("/api/stats", methods=["GET"])
def stats():

    total = len(conversation_history)

    if total == 0:

        return jsonify({
            "total_messages": 0,
            "auto_handled": 0,
            "escalated": 0,
            "auto_handle_rate": 0,
            "escalation_rate": 0,
            "avg_confidence": 0
        })

    escalated = sum(
        1
        for item in conversation_history
        if item["escalate"]
    )

    auto_handled = total - escalated

    avg_confidence = sum(
        float(item["confidence"])
        for item in conversation_history
    ) / total

    return jsonify({

        "total_messages": total,

        "auto_handled": auto_handled,

        "escalated": escalated,

        "auto_handle_rate": round(
            auto_handled / total * 100,
            1
        ),

        "escalation_rate": round(
            escalated / total * 100,
            1
        ),

        "avg_confidence": round(
            avg_confidence,
            1
        )
    })


# =============================================================
# START APPLICATION
# =============================================================
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    print()
    print("=" * 60)
    print("HIVER AI CUSTOMER SUPPORT AGENT")
    print("=" * 60)
    print("Web application starting...")
    print("=" * 60)
    print()

    app.run(
        debug=False,
        host="0.0.0.0",
        port=port
    )