import joblib
from pathlib import Path


BASE = Path(__file__).parent
MODELS = BASE / "models"

SVM_FILE = MODELS / "intent_svm.pkl"
LOGISTIC_FILE = MODELS / "intent_logistic.pkl"


# Load models once
svm_model = joblib.load(SVM_FILE)
logistic_model = joblib.load(LOGISTIC_FILE)


def predict_intent_with_confidence(message):

    # SVM gives the final predicted class
    intent = svm_model.predict([message])[0]

    # Logistic Regression gives probability estimates
    probabilities = logistic_model.predict_proba([message])[0]

    classes = logistic_model.classes_

    # Find probability corresponding to predicted SVM intent
    if intent in classes:
        intent_index = list(classes).index(intent)
        confidence = float(probabilities[intent_index])
    else:
        confidence = float(max(probabilities))

    # Also calculate the highest probability
    max_probability = float(max(probabilities))

    return {
        "intent": intent,
        "confidence": confidence,
        "max_probability": max_probability
    }


if __name__ == "__main__":

    test_messages = [
        "My package is late",
        "I need a refund for my returned item",
        "I can't log into my account",
        "Something is wrong with the app",
        "I was charged twice"
    ]

    print("=" * 70)
    print("INTENT PREDICTION + REAL CONFIDENCE TEST")
    print("=" * 70)

    for message in test_messages:

        result = predict_intent_with_confidence(message)

        print("\nCustomer:")
        print(message)

        print("Intent:")
        print(result["intent"])

        print("Confidence:")
        print(f"{result['confidence']:.4f}")

        print("Maximum probability:")
        print(f"{result['max_probability']:.4f}")

    print("\n" + "=" * 70)
    print("CONFIDENCE TEST COMPLETE")
    print("=" * 70)