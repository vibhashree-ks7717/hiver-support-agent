import os

from response_retriever import analyze_customer_message


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def fallback_reply(intent):
    replies = {
        "Delivery & Order Tracking":
            "I'm sorry about the delivery delay. Please check the latest tracking update for your order. If the package still hasn't arrived by the updated delivery date, please contact Amazon support for further assistance.",

        "Returns & Refunds":
            "I'm sorry you're having trouble with your return or refund. Please check the current return or refund status for your order. If the refund is still missing after the expected processing period, please contact Amazon support so the issue can be reviewed.",

        "Account & Access":
            "I'm sorry you're having trouble accessing your account. Please check your account details and follow the available account recovery or verification steps. If you still cannot access the account, please contact Amazon support.",

        "Payment & Billing":
            "I'm sorry you're experiencing a payment or billing issue. Please review the payment method and transaction details associated with the order. If the issue remains unresolved, please contact Amazon support so the transaction can be reviewed.",

        "Product & Seller Issues":
            "I'm sorry you're having an issue with the product or seller. Please review the order and product details first. If the issue remains unresolved, please contact Amazon support for further assistance.",

        "Technical / App Issues":
            "I'm sorry you're experiencing a technical issue. Please try refreshing the page or restarting the app and check whether the issue continues. If it persists, please contact Amazon support.",

        "Customer Service / Complaint":
            "I'm sorry that your issue has not been resolved. Please contact Amazon support so a representative can review the previous interactions and help with the next steps.",

        "General / Other":
            "I'm sorry you're experiencing this issue. Please provide the relevant order or account details to Amazon support so the issue can be reviewed."
    }

    return replies.get(
        intent,
        "I'm sorry you're experiencing this issue. Please contact Amazon support so the issue can be reviewed."
    )


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        return client

    except Exception as error:
        print("Could not initialize Gemini.")
        print("Error:", error)
        return None


def build_prompt(customer_message, predicted_intent, historical_cases):

    evidence = ""

    for number, case in enumerate(historical_cases[:5], start=1):

        evidence += (
            "\nHistorical Case "
            + str(number)
            + "\nCustomer: "
            + str(case["customer_message"])
            + "\nAmazon Response: "
            + str(case["amazon_response"])
            + "\nSimilarity: "
            + str(round(case["similarity"], 4))
            + "\n"
        )

    prompt = """
You are an AI customer-support reply assistant for Amazon.

Draft a concise, professional customer-support response.

Customer message:
""" + customer_message + """

Predicted intent:
""" + predicted_intent + """

Historical support examples:
""" + evidence + """

Rules:

1. Ground the response in the historical support examples.
2. Do not invent Amazon policies.
3. Do not invent refunds, replacements, credits, delivery dates, or tracking information.
4. Do not claim that you checked the customer's order or account.
5. Do not promise an action that has not been confirmed.
6. Do not include unsupported URLs.
7. Acknowledge the customer's problem.
8. Give a useful next step when possible.
9. Be concise and professional.
10. Do not mention that you are an AI.
11. Do not mention the historical examples.
12. Do not copy historical responses word-for-word.

Write only the customer-facing reply.
"""

    return prompt


def generate_gemini_reply(
    customer_message,
    predicted_intent,
    historical_cases
):

    client = get_gemini_client()

    if client is None:
        return None

    prompt = build_prompt(
        customer_message,
        predicted_intent,
        historical_cases
    )

    try:

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        if response is not None:

            if response.text:

                return response.text.strip()

        print("Gemini returned an empty response.")

        return None

    except Exception as error:

        print()
        print("Gemini generation failed.")
        print("Error:", error)

        return None


def generate_reply(customer_message, top_k=5):

    analysis = analyze_customer_message(
        customer_message,
        top_k=top_k
    )

    predicted_intent = analysis["predicted_intent"]

    historical_cases = analysis["historical_cases"]

    reply = generate_gemini_reply(
        customer_message,
        predicted_intent,
        historical_cases
    )

    if reply:

        generation_mode = "Gemini grounded generation"

    else:

        print()
        print("Using grounded fallback reply instead.")

        reply = fallback_reply(predicted_intent)

        generation_mode = "Grounded fallback"

    return {
        "customer_message": customer_message,
        "predicted_intent": predicted_intent,
        "generation_mode": generation_mode,
        "reply": reply,
        "historical_cases": historical_cases
    }


if __name__ == "__main__":

    print("=" * 70)
    print("HIVER SUPPORT AGENT - GEMINI REPLY GENERATOR")
    print("=" * 70)

    test_message = (
        "My package was supposed to arrive yesterday "
        "but I still haven't received it. Can you check?"
    )

    print()
    print("Customer message:")
    print(test_message)

    print()
    print("Generating reply...")

    result = generate_reply(
        test_message,
        top_k=5
    )

    print()
    print("Predicted intent:")
    print(result["predicted_intent"])

    print()
    print("Generation mode:")
    print(result["generation_mode"])

    print()
    print("Generated reply:")
    print(result["reply"])

    print()
    print("Historical evidence used:")

    for number, case in enumerate(
        result["historical_cases"],
        start=1
    ):

        print()
        print("CASE " + str(number))
        print(
            "Similarity: "
            + str(round(case["similarity"], 4))
        )
        print(
            "Customer: "
            + str(case["customer_message"])
        )
        print(
            "Amazon response: "
            + str(case["amazon_response"])
        )

    print()
    print("=" * 70)
    print("REPLY GENERATION TEST COMPLETE")
    print("=" * 70)