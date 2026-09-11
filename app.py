"""
Flask Web App for AI Customer Support Agent
Simplified version that actually works
"""

from flask import Flask, render_template, request, jsonify
import json
import random
from datetime import datetime
import time
import os

app = Flask(__name__)

class SupportAgent:
    """AI Support Agent"""
    
    def __init__(self, response_db_path, brand_name='Support'):
        self.brand = brand_name
        self.conversation_history = []
        
        try:
            with open(response_db_path, 'r') as f:
                self.response_db = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Cannot find {response_db_path}")
            raise
        
        self.intents = list(self.response_db.keys())
    
    def classify_intent(self, message):
        text = message.lower()
        keywords_map = {
            'Order Status': ['order', 'track', 'tracking', 'delivery', 'package', 'shipment', 'when', 'where', 'status'],
            'Returns & Refunds': ['return', 'refund', 'send back', 'exchange', 'damaged', 'wrong item', 'broken'],
            'Billing & Payment': ['charge', 'bill', 'payment', 'invoice', 'price', 'subscription', 'money'],
            'Technical Issue': ['error', 'bug', 'crash', 'not working', 'app', 'website', 'login', 'slow'],
            'Account & Access': ['account', 'login', 'password', 'access', 'locked', 'verify', 'reset'],
            'Product Inquiry': ['feature', 'how to', 'help', 'question', 'what is', 'size', 'available'],
            'Complaint & Escalation': ['angry', 'frustrated', 'terrible', 'awful', 'worst', 'manager', 'lawsuit'],
            'General Inquiry': []
        }
        
        best_intent = 'General Inquiry'
        max_matches = 0
        
        for intent, keywords in keywords_map.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > max_matches:
                max_matches = matches
                best_intent = intent
        
        confidence = min(75 + (max_matches * 5), 95) if max_matches > 0 else 40
        return best_intent, confidence
    
    def generate_reply(self, customer_message, intent):
        reply_templates = {
            'Order Status': [
                "Thank you for contacting us! I'd be happy to help you track your order. Could you please provide your order number so I can check the current status and delivery timeline?",
                "Thanks for reaching out! Your order status is important to us. Please share your order ID and I'll get you the latest delivery update.",
                "I'm happy to help! To locate your order, please provide your order number and I'll check the tracking information for you right away."
            ],
            'Returns & Refunds': [
                "We appreciate your patience and want to make this right. Please provide your order number and details about the issue. We'll process your return or refund promptly.",
                "I sincerely apologize for the inconvenience. Our returns process is straightforward - just provide your order number and we'll send you a prepaid return label.",
                "Thank you for giving us a chance to resolve this. Please share your order details and we'll arrange a return or refund immediately."
            ],
            'Billing & Payment': [
                "We sincerely apologize for any billing concerns. This needs urgent attention. Could you please provide your account details via private message? We'll investigate and resolve this within 24 hours.",
                "Thank you for bringing this to our attention. Billing accuracy is critical to us. Please send us your account information privately so we can verify and correct any issues.",
                "I apologize for the billing issue. Please share your account details and we'll make sure this is resolved correctly and fairly."
            ],
            'Technical Issue': [
                "I'm sorry you're experiencing technical difficulties. Let's troubleshoot together: 1) Try clearing your cache, 2) Check your internet connection, 3) Restart the app. Let me know if this helps!",
                "We're here to help with technical issues. Please try these steps: reinstall the app, update to the latest version, or try a different browser. Keep me posted!",
                "Thank you for reporting this. Technical issues are our priority. Try refreshing or restarting, and if it persists, we'll escalate to our technical team."
            ],
            'Account & Access': [
                "Let's get you back into your account! Try clicking 'Forgot Password' to reset it. If that doesn't work, reply with your email and we can verify your identity.",
                "I'm happy to help you regain access. First, try the password reset option. If you're still locked out, let me know your account email and we'll assist.",
                "Don't worry, we can fix this! Use the password reset feature first. If you need more help, we can manually verify your identity and grant you access."
            ],
            'Product Inquiry': [
                "Great question! I'd be happy to provide more information about our products. What specifically would you like to know? Features, pricing, availability, or something else?",
                "Thank you for your interest! Please let me know what product details you need - I'm here to help you make the best choice.",
                "Excellent question! To best assist you, could you tell me which product you're interested in and what information would help your decision?"
            ],
            'Complaint & Escalation': [
                "I sincerely apologize for your experience. This is not the standard we strive for. I'm immediately escalating your concern to our management team, and they will prioritize your case.",
                "Thank you for bringing this serious issue to our attention. I'm escalating this to our senior team right now. You'll hear from a manager within the hour.",
                "I take your complaint very seriously. I'm immediately escalating this to our leadership team for urgent review and resolution. Someone senior will contact you shortly."
            ],
            'General Inquiry': [
                "Thank you for reaching out! I'm here to help. Could you provide a bit more detail about what you need assistance with?",
                "Hello! Thanks for contacting us. I'd be happy to assist. What can I help you with today?",
                "Thanks for getting in touch! I'm here to help. Please let me know what you need."
            ]
        }
        
        templates = reply_templates.get(intent, reply_templates['General Inquiry'])
        return random.choice(templates)
    
    def decide_escalation(self, customer_message, intent):
        escalation_keywords = {
            'urgent': ['urgent', 'emergency', 'asap', 'critical', 'now'],
            'emotion': ['angry', 'furious', 'hate', 'worst', 'disgusted'],
            'legal': ['lawyer', 'lawsuit', 'sue', 'attorney'],
            'escalation': ['manager', 'supervisor', 'escalate', 'speak to'],
        }
        
        text = customer_message.lower()
        escalation_score = 0
        
        for category, keywords in escalation_keywords.items():
            matches = sum(1 for kw in keywords if kw in text)
            escalation_score += matches
            if category == 'legal':
                escalation_score += 20
        
        if intent == 'Complaint & Escalation':
            escalation_score += 10
        
        return escalation_score >= 5
    
    def process_message(self, customer_message):
        start_time = time.time()
        
        intent, confidence = self.classify_intent(customer_message)
        reply = self.generate_reply(customer_message, intent)
        should_escalate = self.decide_escalation(customer_message, intent)
        
        processing_time = time.time() - start_time
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'customer_message': customer_message,
            'intent': intent,
            'confidence': confidence,
            'reply': reply,
            'should_escalate': should_escalate,
            'processing_time_ms': round(processing_time * 1000, 2)
        }
        
        self.conversation_history.append(result)
        return result

# Initialize agent with proper file path
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'response_database.json')

try:
    agent = SupportAgent(db_path, brand_name='Support')
    print("✓ Agent initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize agent: {e}")
    agent = None

@app.route('/')
def home():
    """Main chat page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process customer message"""
    if not agent:
        return jsonify({'error': 'Agent not initialized'}), 500
    
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Empty message'}), 400
    
    try:
        result = agent.process_message(message)
        return jsonify({
            'success': True,
            'intent': result['intent'],
            'confidence': result['confidence'],
            'reply': result['reply'],
            'escalate': result['should_escalate'],
            'processing_time_ms': result['processing_time_ms']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get agent statistics"""
    if not agent or not agent.conversation_history:
        return jsonify({'total_messages': 0})
    
    history = agent.conversation_history
    total = len(history)
    escalated = sum(1 for r in history if r['should_escalate'])
    
    return jsonify({
        'total_messages': total,
        'auto_handled': total - escalated,
        'escalated': escalated,
        'auto_handle_rate': round((total - escalated) / total * 100, 1),
        'avg_confidence': round(sum(r['confidence'] for r in history) / total, 1)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)