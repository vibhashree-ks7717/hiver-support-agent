"""
AI Customer Support Agent
- Intent Classification
- Reply Generation (grounded in historical patterns)
- Escalation Decision (with reasoning)
"""

import json
import os
from anthropic import Anthropic
from datetime import datetime
import time

class SupportAgent:
    def __init__(self, response_db_path='response_database.json', brand_name='Support'):
        """Initialize agent with response database and brand context"""
        self.client = Anthropic()
        self.brand = brand_name
        self.conversation_history = []
        
        # Load response database
        with open(response_db_path, 'r') as f:
            self.response_db = json.load(f)
        
        self.intents = list(self.response_db.keys())
        print(f"Agent initialized with {len(self.intents)} intent categories")
        print(f"Intents: {', '.join(self.intents)}")
    
    def classify_intent(self, message, use_llm=True):
        """
        Classify customer message into one of the defined intents
        Returns: (intent, confidence_score)
        """
        
        if use_llm:
            # Use Claude for intelligent classification
            response = self.client.messages.create(
                model="claude-opus-4-6",
                max_tokens=150,
                messages=[{
                    "role": "user",
                    "content": f"""Classify this customer support message into ONE of these categories:
{chr(10).join(f"- {intent}" for intent in self.intents)}

Message: "{message}"

Respond with ONLY:
INTENT: [exact intent name from list above]
CONFIDENCE: [0-100]

No explanation needed."""
                }]
            )
            
            result = response.content[0].text
            lines = result.strip().split('\n')
            
            intent = 'General Inquiry'
            confidence = 50
            
            for line in lines:
                if 'INTENT:' in line:
                    intent = line.split('INTENT:')[1].strip()
                elif 'CONFIDENCE:' in line:
                    try:
                        confidence = int(line.split('CONFIDENCE:')[1].strip())
                    except:
                        confidence = 50
            
            # Ensure intent is valid
            if intent not in self.intents:
                intent = 'General Inquiry'
            
            return intent, min(confidence, 100)
        
        else:
            # Fallback: keyword-based classification
            return self._classify_keywords(message)
    
    def _classify_keywords(self, message):
        """Keyword-based fallback classification"""
        text = message.lower()
        
        keywords_map = {
            'Order Status': ['order', 'track', 'tracking', 'delivery', 'package', 'shipment', 'when', 'where', 'status'],
            'Returns & Refunds': ['return', 'refund', 'send back', 'exchange', 'damaged', 'wrong item'],
            'Billing & Payment': ['charge', 'bill', 'payment', 'invoice', 'price', 'subscription', 'refund'],
            'Technical Issue': ['error', 'bug', 'crash', 'not working', 'app', 'website', 'login', 'slow'],
            'Account & Access': ['account', 'login', 'password', 'access', 'locked', 'verify'],
            'Product Inquiry': ['feature', 'how to', 'help', 'question', 'what is', 'size', 'availability'],
            'Complaint & Escalation': ['angry', 'frustrated', 'terrible', 'awful', 'worst', 'manager', 'lawsuit']
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
        """
        Generate a contextual reply grounded in historical brand patterns
        """
        
        # Get historical context
        historical = self.response_db.get(intent, {})
        common_responses = historical.get('common_responses', [])[:3]
        examples = historical.get('example_conversations', [])[:2]
        
        # Build prompt with grounding
        example_text = ""
        if examples:
            example_text = "\n\nHistorical examples of similar conversations:\n"
            for ex in examples:
                example_text += f"- Customer: {ex['customer']}\n  Reply: {ex['response']}\n"
        
        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"""You are a customer support agent for {self.brand}.

Customer's message: "{customer_message}"
Message type: {intent}

Your task: Draft a helpful, empathetic support reply that:
1. Directly addresses their specific issue or question
2. Matches the professional yet friendly tone of {self.brand}
3. Offers concrete next steps or solutions
4. Is concise (2-3 sentences max)
5. Avoids making promises you can't keep

{example_text}

Draft your reply now (only the reply text, no preamble):"""
            }]
        )
        
        return response.content[0].text.strip()
    
    def decide_escalation(self, customer_message, intent, reply):
        """
        Decide if this message needs human agent escalation
        Returns: (should_escalate, reason)
        """
        
        escalation_indicators = {
            'high_urgency': ['urgent', 'urgent', 'emergency', 'asap', 'immediately', 'critical', 'now'],
            'high_emotion': ['angry', 'furious', 'hate', 'worst', 'disgusted', 'unacceptable', 'outrageous'],
            'legal_threat': ['lawyer', 'lawsuit', 'sue', 'attorney', 'court', 'legal'],
            'request_escalation': ['manager', 'supervisor', 'escalate', 'speak to', 'want to talk'],
            'complaint_intensity': ['never', 'always', 'completely broken', 'ruined', 'wasted']
        }
        
        text = customer_message.lower()
        escalation_reasons = []
        escalation_score = 0
        
        for category, keywords in escalation_indicators.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                escalation_score += matches
                if category == 'legal_threat':
                    escalation_score += 20  # High weight
                    escalation_reasons.append(f"Legal threat detected ({matches} keywords)")
                elif category == 'high_emotion':
                    escalation_reasons.append(f"High emotion detected ({matches} keywords)")
                elif category == 'request_escalation':
                    escalation_reasons.append("Customer explicitly requested escalation")
                elif category == 'high_urgency':
                    escalation_reasons.append("High urgency signal detected")
                elif category == 'complaint_intensity':
                    escalation_reasons.append("Intense complaint language detected")
        
        # Intent-based escalation
        if intent == 'Complaint & Escalation':
            escalation_score += 10
        
        # Check if message is too complex (multi-turn needed)
        if len(customer_message) > 300:
            escalation_score += 5
            escalation_reasons.append("Complex multi-issue inquiry")
        
        should_escalate = escalation_score >= 5
        
        if not escalation_reasons:
            if should_escalate:
                escalation_reasons.append("Escalation score threshold exceeded")
            else:
                escalation_reasons.append("Routine inquiry - auto-handle appropriate")
        
        return should_escalate, "; ".join(escalation_reasons)
    
    def process_message(self, customer_message, return_timing=True):
        """
        Complete pipeline: classify → reply → decide escalation
        """
        start_time = time.time()
        
        # Step 1: Classify
        intent, confidence = self.classify_intent(customer_message)
        
        # Step 2: Generate reply
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
    agent = SupportAgent('/home/claude/response_database.json', brand_name='TechSupport')
    
    # Test messages
    test_messages = [
        "Where is my order? I ordered it 3 days ago and it still hasn't arrived!",
        "I want to return this product, it's broken",
        "How do I reset my password?",
        "I'm furious! This is the worst experience ever. I want to speak to a manager NOW!",
        "Does your app work on Android?"
    ]
    
    print("=== TESTING SUPPORT AGENT ===\n")
    
    for msg in test_messages:
        print(f"Customer: {msg}")
        result = agent.process_message(msg)
        print(f"Intent: {result['classification']['intent']} (confidence: {result['classification']['confidence']}%)")
        print(f"Reply: {result['reply']}")
        print(f"Decision: {result['decision']['category']} - {result['decision']['reason']}")
        print(f"Processing time: {result['performance']['processing_time_ms']}ms")
        print("-" * 80 + "\n")
    
    # Print statistics
    stats = agent.get_statistics()
    print("\n=== AGENT STATISTICS ===")
    print(json.dumps(stats, indent=2))
