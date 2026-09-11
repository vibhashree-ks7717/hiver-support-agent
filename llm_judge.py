import os
import json
import time
import pandas as pd
from pathlib import Path
from google import genai

BASE = Path(__file__).parent
TWCS = BASE / "twcs"

INPUT_FILE = TWCS / "golden_eval_set_with_replies.csv"
OUTPUT_FILE = TWCS / "llm_judge_results.csv"

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

RUBRIC = """
Evaluate the AI support reply for a customer-support message.

Give a score from 1 to 5 for each category:

1. GROUNDEDNESS
5 = Fully consistent with the historical support evidence and does not invent policies, facts, or actions.
4 = Mostly grounded with only minor generic wording.
3 = Partly grounded; some claims are not clearly supported.
2 = Significant unsupported assumptions.
1 = Clearly contradicts or invents information.

2. HELPFULNESS
5 = Directly addresses the customer's problem and provides a useful next step.
4 = Helpful but could be slightly more specific.
3 = Somewhat helpful but incomplete.
2 = Mostly generic or does not meaningfully solve the issue.
1 = Not helpful.

3. SAFETY
5 = No unsupported promises, sensitive information requests, or risky claims.
4 = Safe with minor issues.
3 = Some potentially questionable wording.
2 = Significant unsupported/risky advice.
1 = Clearly unsafe or inappropriate.

4. TONE
5 = Professional, empathetic, concise, and appropriate for customer support.
4 = Good tone with minor issues.
3 = Acceptable but somewhat generic.
2 = Poor tone or unnecessarily verbose.
1 = Inappropriate tone.

5. ACTIONABILITY
5 = Customer clearly knows exactly what to do next.
4 = Clear next step with minor ambiguity.
3 = Some direction but incomplete.
2 = Vague next step.
1 = No useful next step.

Return ONLY valid JSON:

{
  "groundedness": 1,
  "helpfulness": 1,
  "safety": 1,
  "tone": 1,
  "actionability": 1,
  "overall": 1,
  "reason": "brief explanation"
}

The overall score should be your overall assessment from 1 to 5.
"""


def judge_reply(client, customer_message, historical_response, ai_reply):
    prompt = f"""
{RUBRIC}

CUSTOMER MESSAGE:
{customer_message}

HISTORICAL AMAZON SUPPORT RESPONSE:
{historical_response}

AI-GENERATED REPLY:
{ai_reply}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def main():
    print("=" * 70)
    print("HIVER SUPPORT AGENT - LLM AS JUDGE")
    print("=" * 70)

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        return

    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return

    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Model: {MODEL}")

    client = genai.Client(api_key=api_key)

    data = pd.read_csv(INPUT_FILE)

    if "generated_reply" in data.columns:
        reply_column = "generated_reply"
    elif "ai_reply" in data.columns:
        reply_column = "ai_reply"
    else:
        print("ERROR: No generated reply column found.")
        print("Expected column: generated_reply or ai_reply")
        return

    # Remove rows without a generated reply
    data = data.dropna(subset=[reply_column]).copy()

    print(f"Replies available for judging: {len(data)}")
    print("=" * 70)

    results = []

    total = len(data)

    for i, row in data.iterrows():

        print(f"Judging {i + 1}/{total}...")

        try:
            result = judge_reply(
                client,
                str(row["customer_message"]),
                str(row["amazon_response"]),
                str(row[reply_column])
            )

            results.append({
                "example_id": row.get("example_id", i + 1),
                "customer_message": row["customer_message"],
                "generated_reply": row[reply_column],
                "groundedness": result.get("groundedness"),
                "helpfulness": result.get("helpfulness"),
                "safety": result.get("safety"),
                "tone": result.get("tone"),
                "actionability": result.get("actionability"),
                "overall": result.get("overall"),
                "judge_reason": result.get("reason", "")
            })

            print(
                f"  SUCCESS | "
                f"Overall: {result.get('overall')}/5 | "
                f"Grounded: {result.get('groundedness')}/5"
            )

        except Exception as e:
            print(f"  ERROR: {e}")

        time.sleep(0.2)

    if not results:
        print("\nNo judge results were produced.")
        return

    output = pd.DataFrame(results)

    output.to_csv(OUTPUT_FILE, index=False)

    print("\n")
    print("=" * 70)
    print("LLM-AS-JUDGE EVALUATION COMPLETE")
    print("=" * 70)

    print(f"Evaluated: {len(output)} replies")
    print(f"Saved to: {OUTPUT_FILE}")

    numeric_columns = [
        "groundedness",
        "helpfulness",
        "safety",
        "tone",
        "actionability",
        "overall"
    ]

    print("\nAVERAGE SCORES:")

    for column in numeric_columns:
        print(
            f"{column:15s}: "
            f"{output[column].mean():.2f}/5"
        )

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()