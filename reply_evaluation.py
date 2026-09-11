import pandas as pd
import re
from pathlib import Path

from response_retriever import retrieve_similar_cases
from intent_predictor import predict_intent_with_confidence
from reply_generator import fallback_reply, generate_llm_reply
from escalation_agent import escalation_decision


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).parent
TWCS = BASE / "twcs"

GOLD_FILE = TWCS / "golden_eval_set.csv"
OUTPUT_FILE = TWCS / "reply_evaluation_results.csv"


# ============================================================
# TEXT FUNCTIONS
# ============================================================

def normalize_text(text):
    """
    Normalize text for comparison.
    """

    if pd.isna(text):
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text).strip()

    return text


def word_set(text):
    """
    Return a set of normalized words.
    """

    text = normalize_text(text)

    return set(
        re.findall(r"\b[a-z0-9]+\b", text)
    )


def lexical_overlap(reply, historical_response):
    """
    Measure how many words in the generated reply
    also occur in a historical response.
    """

    reply_words = word_set(reply)

    historical_words = word_set(
        historical_response
    )

    if not reply_words:
        return 0.0

    overlap = reply_words.intersection(
        historical_words
    )

    return len(overlap) / len(reply_words)


def contains_unsafe_claim(reply):
    """
    Detect claims that the system should not make
    without actually checking a customer's account/order.
    """

    reply_lower = normalize_text(reply)

    risky_patterns = [
        "i checked your order",
        "i have checked your order",
        "your order is",
        "your refund has been processed",
        "your refund was processed",
        "your package will arrive",
        "your package has arrived",
        "i can see your order",
        "i checked the tracking",
        "i have checked the tracking",
        "i checked your account",
        "i have checked your account",
        "your account has been",
        "your payment has been",
        "the charge has been reversed",
        "the refund is on its way",
    ]

    for phrase in risky_patterns:

        if phrase in reply_lower:
            return True

    return False


def asks_for_details(reply):
    """
    Check whether the response asks for useful
    information or gives a useful next step.
    """

    reply_lower = normalize_text(reply)

    useful_phrases = [
        "provide",
        "share",
        "order details",
        "case details",
        "tracking",
        "tracking number",
        "order number",
        "contact amazon support",
        "contact support",
        "check the status",
        "check your order",
        "check the latest",
        "please check",
        "please provide",
        "please share",
        "let us know",
    ]

    for phrase in useful_phrases:

        if phrase in reply_lower:
            return True

    return False


# ============================================================
# LEAKAGE-FREE RETRIEVAL
# ============================================================

def get_filtered_cases(customer_message, top_k=5):
    """
    Retrieve historical cases while removing exact copies
    of the evaluation example.

    This reduces evaluation leakage where the evaluation
    message itself is retrieved as historical evidence.
    """

    normalized_query = normalize_text(
        customer_message
    )

    # Retrieve more candidates than required.
    # This gives us enough cases after removing duplicates.
    candidates = retrieve_similar_cases(
        customer_message,
        top_k=20
    )

    filtered_cases = []

    for case in candidates:

        retrieved_message = normalize_text(
            case["customer_message"]
        )

        # Remove exact copy of evaluation message.
        if retrieved_message == normalized_query:
            continue

        filtered_cases.append(case)

        if len(filtered_cases) >= top_k:
            break

    return filtered_cases


# ============================================================
# REPLY GENERATION FOR EVALUATION
# ============================================================

def generate_evaluation_reply(
    customer_message,
    intent,
    historical_cases
):
    """
    Generate a reply using only the filtered historical
    evidence.

    If Anthropic API configuration is available,
    use the LLM.

    Otherwise use the deterministic grounded fallback.
    """

    llm_reply = generate_llm_reply(
        customer_message,
        intent,
        historical_cases
    )

    if llm_reply:

        return (
            llm_reply,
            "LLM + historical grounding"
        )

    fallback = fallback_reply(
        customer_message,
        intent,
        historical_cases
    )

    return (
        fallback,
        "Grounded fallback"
    )


# ============================================================
# EXTRACT INTENT PREDICTION
# ============================================================

def extract_prediction(prediction):
    """
    Extract predicted intent and confidence from the
    return value of predict_intent_with_confidence().

    Supports:
        - dictionary
        - tuple
        - list

    This makes the evaluation script robust to the exact
    return format used by intent_predictor.py.
    """

    # --------------------------------------------------------
    # Dictionary format
    # --------------------------------------------------------

    if isinstance(prediction, dict):

        predicted_intent = prediction.get(
            "intent"
        )

        if predicted_intent is None:

            predicted_intent = prediction.get(
                "predicted_intent"
            )

        intent_confidence = prediction.get(
            "confidence"
        )

        if intent_confidence is None:

            intent_confidence = prediction.get(
                "intent_confidence",
                0.0
            )

    # --------------------------------------------------------
    # Tuple / list format
    # --------------------------------------------------------

    elif isinstance(
        prediction,
        (tuple, list)
    ):

        if len(prediction) < 2:

            raise ValueError(
                "Prediction tuple/list does not contain "
                "both intent and confidence."
            )

        predicted_intent = prediction[0]
        intent_confidence = prediction[1]

    # --------------------------------------------------------
    # Unsupported format
    # --------------------------------------------------------

    else:

        raise ValueError(
            "Unexpected prediction format: "
            f"{type(prediction)} -> {prediction}"
        )

    # --------------------------------------------------------
    # Validate intent
    # --------------------------------------------------------

    if predicted_intent is None:

        raise ValueError(
            "Could not extract predicted intent "
            f"from prediction: {prediction}"
        )

    # --------------------------------------------------------
    # Convert confidence to float
    # --------------------------------------------------------

    try:

        intent_confidence = float(
            intent_confidence
        )

    except Exception:

        intent_confidence = 0.0

    return (
        str(predicted_intent),
        intent_confidence
    )


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    print("=" * 70)
    print("REPLY EVALUATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Check golden evaluation file
    # --------------------------------------------------------

    if not GOLD_FILE.exists():

        print()
        print(
            "ERROR: Golden evaluation file not found."
        )

        print(
            f"Expected file: {GOLD_FILE}"
        )

        return

    # --------------------------------------------------------
    # Load golden set
    # --------------------------------------------------------

    gold = pd.read_csv(
        GOLD_FILE
    )

    print()
    print(
        f"Golden examples loaded: {len(gold)}"
    )

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    required_columns = [
        "customer_message",
        "amazon_response",
        "gold_intent"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in gold.columns
    ]

    if missing_columns:

        print()
        print(
            "ERROR: Missing required columns:"
        )

        print(
            missing_columns
        )

        return

    # --------------------------------------------------------
    # Evaluation results
    # --------------------------------------------------------

    results = []

    # --------------------------------------------------------
    # Evaluate every golden example
    # --------------------------------------------------------

    for index, row in gold.iterrows():

        customer_message = str(
            row["customer_message"]
        ).strip()

        historical_response = str(
            row["amazon_response"]
        ).strip()

        gold_intent = str(
            row["gold_intent"]
        ).strip()

        print(
            f"\rEvaluating "
            f"{index + 1}/{len(gold)}",
            end=""
        )

        try:

            # =================================================
            # 1. INTENT PREDICTION
            # =================================================

            prediction = (
                predict_intent_with_confidence(
                    customer_message
                )
            )

            (
                predicted_intent,
                intent_confidence
            ) = extract_prediction(
                prediction
            )

            # =================================================
            # 2. LEAKAGE-FREE RETRIEVAL
            # =================================================

            historical_cases = (
                get_filtered_cases(
                    customer_message,
                    top_k=5
                )
            )

            # =================================================
            # 3. BEST RETRIEVAL SIMILARITY
            # =================================================

            if historical_cases:

                best_similarity = float(
                    historical_cases[0][
                        "similarity"
                    ]
                )

            else:

                best_similarity = 0.0

            # =================================================
            # 4. GENERATE REPLY
            # =================================================

            (
                reply,
                generation_mode
            ) = generate_evaluation_reply(
                customer_message,
                predicted_intent,
                historical_cases
            )

            # =================================================
            # 5. LEXICAL OVERLAP
            # =================================================

            overlap = lexical_overlap(
                reply,
                historical_response
            )

            # =================================================
            # 6. UNSAFE CLAIM CHECK
            # =================================================

            unsafe = contains_unsafe_claim(
                reply
            )

            # =================================================
            # 7. NEXT-STEP / ACTIONABILITY CHECK
            # =================================================

            next_step = asks_for_details(
                reply
            )

            # =================================================
            # 8. ESCALATION DECISION
            # =================================================

            escalation = escalation_decision(
                customer_message,
                predicted_intent,
                intent_confidence,
                historical_cases
            )

            # =================================================
            # 9. INTENT CORRECTNESS
            # =================================================

            intent_correct = (
                predicted_intent == gold_intent
            )

            # =================================================
            # 10. STORE RESULT
            # =================================================

            results.append({

                "example_id":
                    row.get(
                        "example_id",
                        index + 1
                    ),

                "customer_message":
                    customer_message,

                "gold_intent":
                    gold_intent,

                "predicted_intent":
                    predicted_intent,

                "intent_confidence":
                    intent_confidence,

                "intent_correct":
                    intent_correct,

                "best_retrieval_similarity":
                    best_similarity,

                "reply":
                    reply,

                "generation_mode":
                    generation_mode,

                "lexical_overlap":
                    overlap,

                "unsafe_claim":
                    unsafe,

                "asks_for_next_step":
                    next_step,

                "escalation_decision":
                    escalation[
                        "decision"
                    ],

                "escalation_score":
                    escalation[
                        "score"
                    ],

                "escalation_reasons":
                    " | ".join(
                        escalation[
                            "reasons"
                        ]
                    ),

                "historical_case_count":
                    len(
                        historical_cases
                    ),

            })

        # =====================================================
        # ERROR HANDLING
        # =====================================================

        except Exception as error:

            print()
            print()

            print(
                f"ERROR while evaluating "
                f"example {index + 1}: "
                f"{type(error).__name__}: {error}"
            )

            results.append({

                "example_id":
                    row.get(
                        "example_id",
                        index + 1
                    ),

                "customer_message":
                    customer_message,

                "gold_intent":
                    gold_intent,

                "predicted_intent":
                    "ERROR",

                "intent_confidence":
                    0.0,

                "intent_correct":
                    False,

                "best_retrieval_similarity":
                    0.0,

                "reply":
                    "",

                "generation_mode":
                    "ERROR",

                "lexical_overlap":
                    0.0,

                "unsafe_claim":
                    False,

                "asks_for_next_step":
                    False,

                "escalation_decision":
                    "ERROR",

                "escalation_score":
                    0,

                "escalation_reasons":
                    (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),

                "historical_case_count":
                    0,

            })

    print()
    print()

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # SUMMARY METRICS
    # ========================================================

    valid_results = results_df[
        results_df[
            "generation_mode"
        ] != "ERROR"
    ].copy()

    print("=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print()

    print(
        f"Total examples: "
        f"{len(results_df)}"
    )

    print(
        f"Successful evaluations: "
        f"{len(valid_results)}"
    )

    print(
        f"Failed evaluations: "
        f"{len(results_df) - len(valid_results)}"
    )

    # ========================================================
    # CALCULATE METRICS ONLY IF VALID RESULTS EXIST
    # ========================================================

    if len(valid_results) > 0:

        # ----------------------------------------------------
        # Intent accuracy
        # ----------------------------------------------------

        intent_accuracy = (
            valid_results[
                "intent_correct"
            ].mean()
        )

        # ----------------------------------------------------
        # Retrieval similarity
        # ----------------------------------------------------

        average_similarity = (
            valid_results[
                "best_retrieval_similarity"
            ].mean()
        )

        # ----------------------------------------------------
        # Lexical overlap
        # ----------------------------------------------------

        average_overlap = (
            valid_results[
                "lexical_overlap"
            ].mean()
        )

        # ----------------------------------------------------
        # Unsafe claim rate
        # ----------------------------------------------------

        unsafe_rate = (
            valid_results[
                "unsafe_claim"
            ].mean()
        )

        # ----------------------------------------------------
        # Next-step rate
        # ----------------------------------------------------

        next_step_rate = (
            valid_results[
                "asks_for_next_step"
            ].mean()
        )

        # ----------------------------------------------------
        # Auto-handle rate
        # ----------------------------------------------------

        auto_handle_rate = (
            (
                valid_results[
                    "escalation_decision"
                ]
                == "AUTO-HANDLE"
            ).mean()
        )

        # ----------------------------------------------------
        # Escalation rate
        # ----------------------------------------------------

        escalation_rate = (
            (
                valid_results[
                    "escalation_decision"
                ]
                == "ESCALATE"
            ).mean()
        )

        # ----------------------------------------------------
        # LLM count
        # ----------------------------------------------------

        llm_count = (
            valid_results[
                "generation_mode"
            ]
            .eq(
                "LLM + historical grounding"
            )
            .sum()
        )

        # ----------------------------------------------------
        # Fallback count
        # ----------------------------------------------------

        fallback_count = (
            valid_results[
                "generation_mode"
            ]
            .eq(
                "Grounded fallback"
            )
            .sum()
        )

        # ====================================================
        # PRINT METRICS
        # ====================================================

        print()

        print(
            f"Intent accuracy: "
            f"{intent_accuracy:.4f}"
        )

        print(
            f"Average best retrieval similarity: "
            f"{average_similarity:.4f}"
        )

        print(
            f"Average lexical overlap: "
            f"{average_overlap:.4f}"
        )

        print(
            f"Unsafe-claim rate: "
            f"{unsafe_rate:.4f}"
        )

        print(
            f"Next-step/actionability rate: "
            f"{next_step_rate:.4f}"
        )

        print(
            f"Auto-handle rate: "
            f"{auto_handle_rate:.4f}"
        )

        print(
            f"Escalation rate: "
            f"{escalation_rate:.4f}"
        )

        print()

        print(
            f"LLM-generated replies: "
            f"{llm_count}"
        )

        print(
            f"Fallback replies: "
            f"{fallback_count}"
        )

    else:

        print()
        print(
            "No successful evaluations were produced."
        )

        print(
            "Check the error messages above."
        )

    # ========================================================
    # OUTPUT FILE
    # ========================================================

    print()

    print(
        "Results saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    print("=" * 70)
    print("DONE")
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()