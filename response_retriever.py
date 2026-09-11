import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).parent
TWCS = BASE / "twcs"
MODELS = BASE / "models"

TRAIN_FILE = TWCS / "amazonhelp_training_pairs.csv"
INTENT_MODEL_FILE = MODELS / "intent_svm.pkl"


# ============================================================
# LOAD HISTORICAL AMAZON SUPPORT DATA
# ============================================================

print("=" * 70)
print("HIVER SUPPORT AGENT - HISTORICAL RESPONSE RETRIEVER")
print("=" * 70)

print("\nLoading Amazon historical conversations...")

data = pd.read_csv(TRAIN_FILE)

data = data.dropna(
    subset=["customer_message", "amazon_response"]
).copy()

data["customer_message"] = (
    data["customer_message"]
    .astype(str)
    .str.strip()
)

data["amazon_response"] = (
    data["amazon_response"]
    .astype(str)
    .str.strip()
)

data = data[
    (data["customer_message"] != "") &
    (data["amazon_response"] != "")
].reset_index(drop=True)

print(f"Historical support pairs: {len(data):,}")


# ============================================================
# TRAIN TF-IDF RETRIEVER
# ============================================================

print("\nBuilding TF-IDF retrieval index...")

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2,
    max_features=30000
)

customer_vectors = vectorizer.fit_transform(
    data["customer_message"]
)

print(f"TF-IDF matrix shape: {customer_vectors.shape}")


# ============================================================
# LOAD INTENT CLASSIFIER
# ============================================================

print("\nLoading intent classifier...")

intent_model = joblib.load(INTENT_MODEL_FILE)

print("Intent classifier loaded successfully.")


# ============================================================
# RETRIEVE SIMILAR HISTORICAL CASES
# ============================================================

def retrieve_similar_cases(
    customer_message,
    top_k=5
):
    """
    Find historically similar Amazon customer messages
    and return the corresponding Amazon responses.
    """

    query_vector = vectorizer.transform(
        [customer_message]
    )

    similarities = cosine_similarity(
        query_vector,
        customer_vectors
    ).flatten()

    top_indices = np.argsort(
        similarities
    )[::-1][:top_k]

    results = []

    for index in top_indices:
        results.append({
            "customer_message": data.iloc[index]["customer_message"],
            "amazon_response": data.iloc[index]["amazon_response"],
            "similarity": float(similarities[index])
        })

    return results


# ============================================================
# PREDICT INTENT
# ============================================================

def predict_intent(customer_message):
    """
    Predict the support intent using the trained SVM.
    """

    prediction = intent_model.predict(
        [customer_message]
    )[0]

    return prediction


# ============================================================
# COMPLETE RETRIEVAL PIPELINE
# ============================================================

def analyze_customer_message(
    customer_message,
    top_k=5
):

    intent = predict_intent(
        customer_message
    )

    similar_cases = retrieve_similar_cases(
        customer_message,
        top_k=top_k
    )

    return {
        "customer_message": customer_message,
        "predicted_intent": intent,
        "historical_cases": similar_cases
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_message = (
        "My package was supposed to arrive yesterday "
        "but I still haven't received it. Can you check?"
    )

    print("\n" + "=" * 70)
    print("TESTING RETRIEVER")
    print("=" * 70)

    result = analyze_customer_message(
        test_message,
        top_k=5
    )

    print("\nCustomer message:")
    print(result["customer_message"])

    print("\nPredicted intent:")
    print(result["predicted_intent"])

    print("\nTop historical Amazon cases:")

    for i, case in enumerate(
        result["historical_cases"],
        start=1
    ):

        print("\n" + "-" * 70)
        print(f"CASE {i}")
        print(f"Similarity: {case['similarity']:.4f}")

        print("\nPrevious customer:")
        print(case["customer_message"][:500])

        print("\nHistorical Amazon response:")
        print(case["amazon_response"][:500])

    print("\n" + "=" * 70)
    print("RETRIEVER TEST COMPLETE")
    print("=" * 70)