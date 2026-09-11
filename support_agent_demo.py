"""
AI Customer Support Agent (DEMO MODE - Simulated Responses)
- Intent Classification
- Reply Generation (grounded in historical patterns)
- Escalation Decision (with reasoning)

NOTE: This demo uses simulated Claude responses for demonstration.
In production, set ANTHROPIC_API_KEY environment variable to use real API.
"""

import json
import os
from datetime import datetime
import time
import random

class SupportAgentDemo:
    """Demo version with simulated responses"""
    
    def __init__(self, response_db_path='response_database.json', brand_name='Support'):
        """Initialize agent with response database and brand context"""
        self.brand = brand_name
        self.conversation_history = []
        
        # Load response database
        with open(response_db_path, 'r') as f:
            self.response_db = json.load(f)
        
        self.intents = list(self.response_db.keys())
        print(f"✓ Agent initialized (DEMO MODE) with {len(self.intents)} intent categories")
        print(f"  Intents: {', '.join(self.intents)}\n")
    
    def classify_intent(self, message):
        """Classify customer message using keyword matching"""
        text = message.lower()
        
        keywords_map = {
            'Order Status': ['order', 'track', 'tracking', 'delivery', 'package', 'shipment', 'when', 'where', 'status', 'arrive', 'arrived'],
            'Returns & Refunds': ['return', 'refund', 'send back', 'exchange', 'damaged', 'wrong item', 'broken'],
            'Billing & Payment': ['charge', 'bill', 'payment', 'invoice', 'price', 'subscription', 'money', 'cost'],
            'Technical Issue': ['error', 'bug', 'crash', 'not working', 'app', 'website', 'login', 'slow', 'broken', 'down'],
            'Account & Access': ['account', 'login', 'password', 'access', 'locked', 'verify', 'reset'],
            'Product Inquiry': ['feature', 'how to', 'help', 'question', 'what is', 'size', 'availability', 'stock'],
            'Complaint & Escalation': ['angry', 'frustrated', 'terrible', 'awful', 'worst', 'manager', 'lawsuit', 'furious'],
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
        """Generate a reply grounded in historical patterns"""
        
        # Get historical context
        historical = self.response_db.get(intent, {})
        common_responses = historical.get('common_responses', [])[:3]
        
        # Create contextual reply based on patterns
        reply_templates = {
            'Order Status': [
                "Thank you for contacting us! I'd be happy to help you track your order. Could you please provide your order number so I can check the current status and delivery timeline?",
                "Thanks for reaching out! Your order status is important to us. Please share your order ID and I'll check the tracking information for you right away.",
                "I'm happy to help! To locate your order, please provide your order number and I'll get you the latest delivery update."
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
    
    def decide_escalation(self, customer_message, intent, reply):
        """Decide if this message needs human escalation"""
        
        escalation_keywords = {
            'urgent': ['urgent', 'emergency', 'asap', 'immediately', 'critical', 'now'],
            'emotion': ['angry', 'furious', 'hate', 'worst', 'disgusted', 'unacceptable'],
            'legal': ['lawyer', 'lawsuit', 'sue', 'attorney', 'court', 'legal'],
            'escalation': ['manager', 'supervisor', 'escalate', 'speak to'],
            'intensity': ['never', 'always', 'completely broken', 'ruined']
        }
        
        text = customer_message.lower()
        escalation_score = 0
        escalation_reasons = []
        
        # Score escalation indicators
        for category, keywords in escalation_keywords.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                escalation_score += matches
                if category == 'legal':
                    escalation_score += 20
                    escalation_reasons.append(f"Legal language detected")
                elif category == 'emotion':
                    escalation_reasons.append(f"High emotion detected ({matches} indicators)")
                elif category == 'escalation':
                    escalation_reasons.append("Customer explicitly requested escalation")
                elif category == 'urgent':
                    escalation_reasons.append("Urgency indicators present")
        
        # Intent-based escalation
        if intent == 'Complaint & Escalation':
            escalation_score += 10
        
        # Long/complex messages
        if len(customer_message) > 300:
            escalation_score += 5
            escalation_reasons.append("Complex inquiry (length suggests multiple issues)")
        
        should_escalate = escalation_score >= 5
        
        if not escalation_reasons:
            escalation_reasons.append("Routine inquiry - can be auto-handled" if not should_escalate else "Escalation threshold exceeded")
        
        return should_escalate, "; ".join(escalation_reasons)
    
    def process_message(self, customer_message):
        """Complete pipeline: classify → reply → decide escalation"""
        start_time = time.time()
        
        # Step 1: Classify
        intent, confidence = self.classify_intent(customer_message)
        
        # Step 2: Generate reply (simulated)
        reply = self.generate_reply(customer_message, intent)
        
        # Step 3: Decide escalation
        should_escalate, escalation_reason = self.decide_escalation(customer_message, intent, reply)
        
        processing_time = time.time() - start_time
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'customer_message': customer_message,
            'classification': {
                'intent': intent,
                'confidence': confidence
            },
            'reply': reply,
            'decision': {
                'should_escalate': should_escalate,
                'reason': escalation_reason,
                'category': 'ESCALATE' if should_escalate else 'AUTO_HANDLE'
            },
            'performance': {
                'processing_time_ms': round(processing_time * 1000, 2)
            }
        }
        
        # Store in history
        self.conversation_history.append(result)
        
        return result
    
    def get_statistics(self):
        """Get statistics from processed messages"""
        if not self.conversation_history:
            return None
        
        total = len(self.conversation_history)
        escalated = sum(1 for r in self.conversation_history if r['decision']['should_escalate'])
        auto_handled = total - escalated
        avg_confidence = sum(r['classification']['confidence'] for r in self.conversation_history) / total
        avg_time = sum(r['performance']['processing_time_ms'] for r in self.conversation_history) / total
        
        intent_counts = {}
        for result in self.conversation_history:
            intent = result['classification']['intent']
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return {
            'total_messages': total,
            'auto_handled': auto_handled,
            'escalated': escalated,
            'auto_handle_rate': round((auto_handled / total) * 100, 1),
            'escalation_rate': round((escalated / total) * 100, 1),
            'avg_confidence': round(avg_confidence, 1),
            'avg_processing_time_ms': round(avg_time, 2),
            'intent_distribution': intent_counts
        }


if __name__ == '__main__':
    # Test the agent
    agent = SupportAgentDemo('response_database.json', brand_name='TechSupport')
    
    # Test messages
    test_messages = [
        "Where is my order? I ordered it 3 days ago and it still hasn't arrived!",
        "I want to return this product, it's broken and defective",
        "How do I reset my password? I can't access my account",
        "I'm absolutely FURIOUS! This is the worst experience ever. I want to speak to a manager NOW!",
        "Does your app work on Android devices?"
    ]
    
    print("="*80)
    print("TESTING AI CUSTOMER SUPPORT AGENT (DEMO MODE)")
    print("="*80 + "\n")
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n📝 Message #{i}")
        print(f"Customer: {msg}")
        result = agent.process_message(msg)
        print(f"\n✓ Classification: {result['classification']['intent']}")
        print(f"  Confidence: {result['classification']['confidence']}%")
        print(f"\n💬 Reply: {result['reply']}")
        print(f"\n🚀 Decision: {result['decision']['category']}")
        print(f"  Reason: {result['decision']['reason']}")
        print(f"  Time: {result['performance']['processing_time_ms']}ms")
        print("-" * 80)
    
    # Print statistics
    stats = agent.get_statistics()
    print("\n" + "="*80)
    print("AGENT STATISTICS")
    print("="*80)
    print(json.dumps(stats, indent=2))
