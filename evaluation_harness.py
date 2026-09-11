import pandas as pd
import joblib

from pathlib import Path
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix
)

BASE = Path(__file__).parent
TWCS = BASE / "twcs"
MODELS = BASE / "models"

GOLD_FILE = TWCS / "golden_eval_set.csv"
SVM_FILE = MODELS / "intent_svm.pkl"
LOGISTIC_FILE = MODELS / "intent_logistic.pkl"

OUTPUT_RESULTS = TWCS / "final_intent_evaluation.csv"
OUTPUT_CONFUSION = TWCS / "final_intent_confusion_matrix.csv"


# ============================================================
# LOAD GOLDEN DATA
# ============================================================

print("=" * 80)
print("HIVER SUPPORT AGENT - INTENT EVALUATION HARNESS")
print("=" * 80)

print("\nLoading golden evaluation set...")

gold = pd.read_csv(GOLD_FILE)

gold = gold.dropna(
    subset=["customer_message", "gold_intent"]
).copy()

gold["customer_message"] = (
    gold["customer_message"]
    .astype(str)
    .str.strip()
)

gold["gold_intent"] = (
    gold["gold_intent"]
    .astype(str)
    .str.strip()
)

print(f"Golden examples: {len(gold)}")


# ============================================================
# LOAD MODELS
# ============================================================

print("\nLoading trained models...")

svm_model = joblib.load(SVM_FILE)
logistic_model = joblib.load(LOGISTIC_FILE)

print("SVM loaded.")
print("Logistic Regression loaded.")


# ============================================================
# MAJORITY BASELINE
# ============================================================

print("\n" + "=" * 80)
print("BASELINE 1: MAJORITY CLASS")
print("=" * 80)

majority_class = gold["gold_intent"].value_counts().idxmax()

print(f"Majority class: {majority_class}")

majority_predictions = [
    majority_class
] * len(gold)


# ============================================================
# KEYWORD BASELINE
# ============================================================

print("\n" + "=" * 80)
print("BASELINE 2: SIMPLE KEYWORD RULES")
print("=" * 80)


KEYWORD_RULES = {

    "Delivery & Order Tracking": [
        "delivery",
        "delivered",
        "package",
        "parcel",
        "shipping",
        "shipment",
        "tracking",
        "track my",
        "where is my order",
        "late",
        "arrive",
        "arrived",
        "not arrived"
    ],

    "Returns & Refunds": [
        "refund",
        "refunded",
        "return",
        "returned",
        "money back",
        "reimbursement",
        "a-to-z",
        "a to z"
    ],

    "Account & Access": [
        "account",
        "login",
        "log in",
        "password",
        "locked",
        "verification",
        "verify",
        "two factor",
        "2fa"
    ],

    "Payment & Billing": [
        "payment",
        "paid",
        "charge",
        "charged",
        "billing",
        "bill",
        "credit card",
        "debit card",
        "amazon pay",
        "charged twice"
    ],

    "Product & Seller Issues": [
        "seller",
        "product",
        "item",
        "price",
        "pricing",
        "authentic",
        "fake",
        "counterfeit"
    ],

    "Technical / App Issues": [
        "app",
        "website",
        "site",
        "technical",
        "error",
        "bug",
        "crash",
        "not working",
        "login error"
    ],

    "Customer Service / Complaint": [
        "complaint",
        "manager",
        "supervisor",
        "human",
        "agent",
        "escalate",
        "terrible",
        "ridiculous",
        "frustrated",
        "unacceptable",
        "worst",
        "angry"
    ]
}


def keyword_predict(text):

    text = text.lower()

    scores = {}

    for intent, keywords in KEYWORD_RULES.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        scores[intent] = score

    best_intent = max(
        scores,
        key=scores.get
    )

    # If no keyword matches,
    # use General / Other.

    if scores[best_intent] == 0:
        return "General / Other"

    return best_intent


keyword_predictions = [
    keyword_predict(message)
    for message in gold["customer_message"]
]


# ============================================================
# MODEL PREDICTIONS
# ============================================================

print("\nGenerating model predictions...")

svm_predictions = svm_model.predict(
    gold["customer_message"]
)

logistic_predictions = logistic_model.predict(
    gold["customer_message"]
)


# ============================================================
# EVALUATION FUNCTION
# ============================================================

def evaluate_model(name, y_true, y_pred):

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    macro_f1 = f1_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )

    weighted_f1 = f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )

    macro_precision = precision_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )

    macro_recall = recall_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )

    return {
        "model": name,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall
    }


# ============================================================
# RUN EVALUATION
# ============================================================

y_true = gold["gold_intent"]

results = []

results.append(
    evaluate_model(
        "Majority Baseline",
        y_true,
        majority_predictions
    )
)

results.append(
    evaluate_model(
        "Keyword Baseline",
        y_true,
        keyword_predictions
    )
)

results.append(
    evaluate_model(
        "Logistic Regression",
        y_true,
        logistic_predictions
    )
)

results.append(
    evaluate_model(
        "Linear SVM",
        y_true,
        svm_predictions
    )
)


# ============================================================
# PRINT RESULTS
# ============================================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 80)
print("OVERALL RESULTS")
print("=" * 80)

print(
    results_df.to_string(
        index=False,
        formatters={
            "accuracy": "{:.4f}".format,
            "macro_f1": "{:.4f}".format,
            "weighted_f1": "{:.4f}".format,
            "macro_precision": "{:.4f}".format,
            "macro_recall": "{:.4f}".format
        }
    )
)


# ============================================================
# BEST MODEL
# ============================================================

best_model = results_df.loc[
    results_df["macro_f1"].idxmax()
]

print("\n" + "=" * 80)
print("BEST MODEL")
print("=" * 80)

print(
    f"Model: {best_model['model']}"
)

print(
    f"Accuracy: {best_model['accuracy']:.4f}"
)

print(
    f"Macro F1: {best_model['macro_f1']:.4f}"
)


# ============================================================
# SVM CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 80)
print("LINEAR SVM - PER CLASS RESULTS")
print("=" * 80)

print(
    classification_report(
        y_true,
        svm_predictions,
        zero_division=0
    )
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

labels = sorted(
    y_true.unique()
)

cm = confusion_matrix(
    y_true,
    svm_predictions,
    labels=labels
)

cm_df = pd.DataFrame(
    cm,
    index=labels,
    columns=labels
)

cm_df.to_csv(
    OUTPUT_CONFUSION
)


# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    OUTPUT_RESULTS,
    index=False
)

print("\nSaved results to:")
print(OUTPUT_RESULTS)

print("\nSaved confusion matrix to:")
print(OUTPUT_CONFUSION)

print("\n" + "=" * 80)
print("EVALUATION COMPLETE")
print("=" * 80)