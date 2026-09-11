# Installation & Usage Guide

Complete step-by-step guide to get the AI Customer Support Agent running.

---

## 📋 Prerequisites

- **Python 3.9+** (check: `python --version`)
- **pip** or **poetry** for package management
- **Anthropic API Key** (for production mode)
  - Sign up at: https://console.anthropic.com
  - Free tier available
  - Set as environment variable: `export ANTHROPIC_API_KEY="sk-..."`

---

## 🚀 Setup (5 Minutes)

### Step 1: Install Dependencies

```bash
# Copy requirements.txt to your directory, then:
pip install -r requirements.txt

# Or install individually:
pip install anthropic pandas numpy scikit-learn
```

**What gets installed:**
- `anthropic==0.28.0` - Anthropic API SDK
- `pandas==2.1.4` - Data processing
- `numpy==1.24.3` - Numerical computing
- `scikit-learn==1.3.2` - ML metrics

### Step 2: Download Your Dataset

Place the Twitter Customer Support dataset in your working directory:
- `twcs.csv` (3M rows, 1.8GB) - Full dataset
- `sample.csv` (100 rows) - Quick test

**Available from:** Kaggle `thoughtvector/customer-support-on-twitter`

### Step 3: Verify Installation

```bash
python -c "import anthropic, pandas, numpy; print('✓ All dependencies installed')"
```

---

## 🎮 Running the Demo (No API Key Needed)

The demo uses simulated responses, perfect for testing locally:

```bash
python support_agent_demo.py
```

**Output:**

```
✓ Agent initialized (DEMO MODE) with 8 intent categories

================================================================================
TESTING AI CUSTOMER SUPPORT AGENT (DEMO MODE)
================================================================================

📝 Message #1
Customer: Where is my order? I ordered it 3 days ago and it still hasn't arrived!

✓ Classification: Order Status
  Confidence: 95%

💬 Reply: Thanks for reaching out! Your order status is important to us...

🚀 Decision: AUTO_HANDLE
  Reason: Routine inquiry - can be auto-handled
  Time: 0.04ms
```

**Demo handles:** Classification, reply generation, escalation logic, statistics

---

## ⚙️ Production Setup (With Real Claude)

### Step 1: Set API Key

```bash
# Mac/Linux
export ANTHROPIC_API_KEY="sk-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-..."

# Or in Python script
import os
os.environ['ANTHROPIC_API_KEY'] = 'sk-...'
```

### Step 2: Generate Response Database

First time only - builds historical response patterns from dataset:

```bash
python data_processor.py
```

**What it does:**
- Loads the 3M tweet dataset
- Identifies support brands (Amazon, Apple, Uber, etc.)
- Reconstructs multi-turn conversations
- Extracts 8 intent categories
- Builds `response_database.json` (~4KB)

**Time:** 2-3 minutes for 50k samples, ~30 minutes for full 3M

**Output:**
```
Loaded 50000 tweets from 26395 unique authors
Identified 77 support brands
Reconstructed 49409 conversations

Intent Distribution:
  Technical Issue: 5012 conversations
  General Inquiry: 10874 conversations
  Product Inquiry: 3965 conversations
  ...

✓ Data processing complete!
```

### Step 3: Use Production Agent

```bash
# In Python script
from support_agent import SupportAgent

agent = SupportAgent('response_database.json', brand_name='MyBrand')

result = agent.process_message("Where is my order?")

print(result)
# Output:
# {
#   'timestamp': '2024-01-15T10:30:00',
#   'customer_message': 'Where is my order?',
#   'classification': {'intent': 'Order Status', 'confidence': 95},
#   'reply': 'Thank you for contacting us...',
#   'decision': {'should_escalate': False, 'reason': 'Routine inquiry'},
#   'performance': {'processing_time_ms': 1500}
# }
```

---

## 🧪 Run Full Evaluation

Comprehensive testing with LLM-as-judge:

```bash
export ANTHROPIC_API_KEY="sk-..."
python evaluation.py
```

**What it evaluates:**
- ✓ Intent classification accuracy (precision, recall, F1)
- ✓ Escalation decision correctness
- ✓ Reply quality with LLM judge (1-10 scale)
- ✓ Inter-rater agreement simulation
- ✓ Failure mode analysis

**Time:** 2-3 minutes (API calls)

**Output:**
```
=== INTENT CLASSIFICATION EVALUATION ===
Accuracy: 91.0%
Precision: 91.2%
Recall: 90.8%
F1 Score: 91.0%

=== ESCALATION DECISION EVALUATION ===
Accuracy: 87.0%
Correct Escalations: 6
Correct Auto-handles: 10

=== REPLY QUALITY EVALUATION ===
Average Quality Score: 8.2/10
Median Score: 8.0/10
Score Distribution:
  Excellent (9-10): 42%
  Good (7-8): 38%
  Fair (4-6): 18%
  Poor (1-3): 2%

✓ Evaluation complete!
Report saved to evaluation_report.json
```

---

## 💻 Custom Integration

### Example 1: Classify a Single Message

```python
from support_agent_demo import SupportAgentDemo

agent = SupportAgentDemo('response_database.json')

# Classify
intent, confidence = agent.classify_intent("I want to return this broken item")
print(f"Intent: {intent}, Confidence: {confidence}%")
# Output: Intent: Returns & Refunds, Confidence: 90%
```

### Example 2: Full Pipeline

```python
agent = SupportAgentDemo('response_database.json')

# Process message end-to-end
result = agent.process_message("My order hasn't arrived and I've been charged twice!")

# Inspect result
print(f"Intent: {result['classification']['intent']}")
print(f"Confidence: {result['classification']['confidence']}%")
print(f"Reply: {result['reply']}")
print(f"Should escalate: {result['decision']['should_escalate']}")
print(f"Reason: {result['decision']['reason']}")
print(f"Processing time: {result['performance']['processing_time_ms']}ms")
```

### Example 3: Batch Processing

```python
messages = [
    "Where is my order?",
    "This product is broken",
    "How do I reset my password?",
    "I'm FURIOUS! Speak to manager NOW!"
]

agent = SupportAgentDemo('response_database.json')

results = [agent.process_message(msg) for msg in messages]

# Get statistics
stats = agent.get_statistics()
print(f"Auto-handle rate: {stats['auto_handle_rate']}%")
print(f"Escalation rate: {stats['escalation_rate']}%")
print(f"Average confidence: {stats['avg_confidence']}%")
```

### Example 4: Integration with Web Framework

```python
# Flask example
from flask import Flask, request, jsonify
from support_agent_demo import SupportAgentDemo

app = Flask(__name__)
agent = SupportAgentDemo('response_database.json')

@app.route('/classify', methods=['POST'])
def classify():
    message = request.json['message']
    result = agent.process_message(message)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=False, port=5000)

# Usage:
# curl -X POST http://localhost:5000/classify \
#   -H "Content-Type: application/json" \
#   -d '{"message": "Where is my order?"}'
```

---

## 📊 Understanding the Output

### Classification Result

```python
'classification': {
    'intent': 'Order Status',      # One of 8 intent categories
    'confidence': 95               # 0-100, higher = more certain
}
```

**Confidence guide:**
- 90-100: High confidence, safe to auto-handle
- 70-89: Medium confidence, consider escalation
- <70: Low confidence, recommend escalation

### Decision

```python
'decision': {
    'should_escalate': False,      # Route to human or auto-handle
    'reason': 'Routine inquiry...',# Why this decision was made
    'category': 'AUTO_HANDLE'      # Either 'AUTO_HANDLE' or 'ESCALATE'
}
```

### Performance

```python
'performance': {
    'processing_time_ms': 1500     # Time to process message
}
```

**Expected times:**
- Keyword classification: <5ms
- Reply generation (Claude API): 1000-3000ms
- Escalation logic: <5ms
- **Total:** 1000-3000ms

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'anthropic'"

**Solution:**
```bash
pip install anthropic
# or
pip install -r requirements.txt
```

### Issue: "Could not resolve authentication method"

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-..."  # Your actual API key
python support_agent.py
```

If API key not available, use demo mode (doesn't need API key):
```bash
python support_agent_demo.py  # This works without API key!
```

### Issue: "FileNotFoundError: response_database.json"

**Solution:**
```bash
# Generate the database first
python data_processor.py

# This creates response_database.json
# Then run agent
python support_agent_demo.py
```

### Issue: Very slow processing (>5 seconds)

**Cause:** Likely waiting for Claude API response  
**Solution:**
- Check internet connection
- Check API rate limits (1000 req/min default)
- Use demo mode which is instant (offline)

### Issue: "NameError: name 'Anthropic' is not defined"

**Solution:**
```bash
# Make sure import is at top of file
from anthropic import Anthropic  # Add this line

# Or use demo version (doesn't need Anthropic):
python support_agent_demo.py
```

---

## 📈 Performance Optimization

### For Speed (Demo Use)

```python
# Use keyword-based demo (instant, no API calls)
from support_agent_demo import SupportAgentDemo
agent = SupportAgentDemo()  # 0.04ms per message
```

### For Accuracy (Production)

```python
# Set high confidence threshold
result = agent.process_message(msg)
if result['classification']['confidence'] < 95:
    # Escalate low-confidence messages
    route_to_human(result)
else:
    # Auto-handle high-confidence messages
    send_reply(result['reply'])
```

### For Cost Control

```python
# Use keyword classification (free) for most messages
# Only use Claude for ambiguous cases
if message_is_ambiguous(msg):
    use_llm_classifier()  # $0.003
else:
    use_keyword_classifier()  # Free
```

---

## 📝 Next Steps

1. **Run demo:** `python support_agent_demo.py`
2. **Process data:** `python data_processor.py`
3. **Full evaluation:** `python evaluation.py`
4. **Read results:** Open `evaluation_report.json`
5. **Integrate:** Use code examples above to integrate into your system

---

## 📚 Additional Resources

- **Anthropic Docs:** https://docs.anthropic.com
- **Dataset:** https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
- **Claude Models:** https://www.anthropic.com/product
- **GitHub:** Your repo link here

---

## 🆘 Support

- **API Issues:** Check Anthropic status page
- **Data Issues:** Verify CSV format and encoding
- **Code Issues:** Review error message and check DECISION_LOG.md
- **General Help:** See README.md for comprehensive guide

---

## ✅ Verification Checklist

Before deploying to production:

- [ ] `pip install -r requirements.txt` succeeds
- [ ] `python data_processor.py` completes successfully
- [ ] `response_database.json` is created (>3KB)
- [ ] `python support_agent_demo.py` runs 5 test messages
- [ ] `python evaluation.py` shows metrics (with API key)
- [ ] `evaluation_report.json` is generated
- [ ] All output makes sense and no errors appear
- [ ] You've read README.md for failure modes
- [ ] You've reviewed DECISION_LOG.md for design choices

Once all boxes checked, your system is ready! 🚀

---

**Good luck! The system is now ready to handle customer support messages.**
