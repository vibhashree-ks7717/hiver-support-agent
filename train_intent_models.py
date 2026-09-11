import pandas as pd
import joblib
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)
from sklearn.pipeline import Pipeline


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).parent
TWCS = BASE / "twcs"

TRAIN_FILE = TWCS / "intent_training_data.csv"
GOLD_FILE = TWCS / "golden_eval_set.csv"

MODEL_DIR = BASE / "models"
MODEL_DIR.mkdir(exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("HIVER SUPPORT AGENT - INTENT CLASSIFIER TRAINING")
print("=" * 70)

print("\nLoading training data...")
train = pd.read_csv(TRAIN_FILE)

print("Loading golden evaluation set...")
gold = pd.read_csv(GOLD_FILE)

print(f"\nTraining examples : {len(train):,}")
print(f"Golden examples   : {len(gold):,}")

X_train = train["customer_message"].fillna("")
y_train = train["intent"]

X_gold = gold["customer_message"].fillna("")
y_gold = gold["gold_intent"]


# ============================================================
# CHECK GOLD LABELS
# ============================================================

print("\nChecking golden labels...")

missing_gold = y_gold.isna() | (y_gold.astype(str).str.strip() == "")

if missing_gold.any():
    print(
        f"WARNING: {missing_gold.sum()} golden examples "
        "do not have a gold_intent."
    )

    gold = gold.loc[~missing_gold].copy()

    X_gold = gold["customer_message"].fillna("")
    y_gold = gold["gold_intent"]

print(f"Usable golden examples: {len(gold)}")


# ============================================================
# COMMON TF-IDF
# ============================================================

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2,
    max_features=50000,
    sublinear_tf=True
)


# ============================================================
# BASELINE 1
# MAJORITY CLASS
# ============================================================

print("\n" + "=" * 70)
print("BASELINE 1 - MAJORITY CLASS")
print("=" * 70)

majority_class = y_train.value_counts().idxmax()

majority_predictions = [majority_class] * len(y_gold)

majority_accuracy = accuracy_score(
    y_gold,
    majority_predictions
)

majority_f1 = f1_score(
    y_gold,
    majority_predictions,
    average="macro"
)

print(f"Majority class: {majority_class}")
print(f"Accuracy      : {majority_accuracy:.4f}")
print(f"Macro F1      : {majority_f1:.4f}")


# ============================================================
# BASELINE 2
# TF-IDF + LOGISTIC REGRESSION
# ============================================================

print("\n" + "=" * 70)
print("BASELINE 2 - TF-IDF + LOGISTIC REGRESSION")
print("=" * 70)

logistic_model = Pipeline([
    ("tfidf", vectorizer),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        )
    )
])

print("\nTraining Logistic Regression...")
logistic_model.fit(X_train, y_train)

print("Evaluating...")

logistic_predictions = logistic_model.predict(X_gold)

logistic_accuracy = accuracy_score(
    y_gold,
    logistic_predictions
)

logistic_f1 = f1_score(
    y_gold,
    logistic_predictions,
    average="macro"
)

print(f"Accuracy : {logistic_accuracy:.4f}")
print(f"Macro F1 : {logistic_f1:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_gold,
        logistic_predictions,
        zero_division=0
    )
)

joblib.dump(
    logistic_model,
    MODEL_DIR / "intent_logistic.pkl"
)


# ============================================================
# MAIN MODEL
# TF-IDF + LINEAR SVM
# ============================================================

print("\n" + "=" * 70)
print("MAIN MODEL - TF-IDF + LINEAR SVM")
print("=" * 70)

svm_model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_features=50000,
        sublinear_tf=True
    )),
    (
        "classifier",
        LinearSVC(
            class_weight="balanced",
            random_state=42
        )
    )
])

print("\nTraining Linear SVM...")
svm_model.fit(X_train, y_train)

print("Evaluating...")

svm_predictions = svm_model.predict(X_gold)

svm_accuracy = accuracy_score(
    y_gold,
    svm_predictions
)

svm_f1 = f1_score(
    y_gold,
    svm_predictions,
    average="macro"
)

print(f"Accuracy : {svm_accuracy:.4f}")
print(f"Macro F1 : {svm_f1:.4f}")

print("\nClassification Report:")
print(
    classification_report(
        y_gold,
        svm_predictions,
        zero_division=0
    )
)

joblib.dump(
    svm_model,
    MODEL_DIR / "intent_svm.pkl"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

labels = sorted(y_gold.unique())

cm = confusion_matrix(
    y_gold,
    svm_predictions,
    labels=labels
)

cm_df = pd.DataFrame(
    cm,
    index=labels,
    columns=labels
)

cm_file = TWCS / "intent_confusion_matrix.csv"

cm_df.to_csv(cm_file)


# ============================================================
# SAVE PREDICTIONS
# ============================================================

results = gold.copy()

results["majority_prediction"] = majority_predictions
results["logistic_prediction"] = logistic_predictions
results["svm_prediction"] = svm_predictions

results_file = TWCS / "intent_evaluation_results.csv"

results.to_csv(
    results_file,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

summary = pd.DataFrame({
    "model": [
        "Majority Class",
        "TF-IDF + Logistic Regression",
        "TF-IDF + Linear SVM"
    ],
    "accuracy": [
        majority_accuracy,
        logistic_accuracy,
        svm_accuracy
    ],
    "macro_f1": [
        majority_f1,
        logistic_f1,
        svm_f1
    ]
})

summary_file = TWCS / "intent_model_comparison.csv"

summary.to_csv(
    summary_file,
    index=False
)


print("\n" + "=" * 70)
print("FINAL MODEL COMPARISON")
print("=" * 70)

print(
    summary.to_string(
        index=False
    )
)

print("\nSaved models:")
print(MODEL_DIR / "intent_logistic.pkl")
print(MODEL_DIR / "intent_svm.pkl")

print("\nSaved evaluation files:")
print(cm_file)
print(results_file)
print(summary_file)

print("\n" + "=" * 70)
print("INTENT MODEL TRAINING COMPLETE")
print("=" * 70)