"""
Data Processing Pipeline for Customer Support Twitter Data
Loads, cleans, and analyzes multi-turn customer support conversations
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import json
import re
from datetime import datetime

class DataProcessor:
    def __init__(self, data_path):
        """Initialize with path to CSV file"""
        self.data_path = data_path
        self.df = None
        self.conversations = {}
        self.brands = {}
        
    def load_data(self, sample_size=None):
        """Load and initial cleanup"""
        print(f"Loading data from {self.data_path}...")
        self.df = pd.read_csv(self.data_path)
        
        if sample_size:
            self.df = self.df.sample(n=min(sample_size, len(self.df)), random_state=42)
        
        # Clean column names
        self.df.columns = [col.strip() for col in self.df.columns]
        
        # Remove duplicates
        self.df = self.df.drop_duplicates(subset=['tweet_id'])
        
        print(f"Loaded {len(self.df)} tweets from {self.df['author_id'].nunique()} unique authors")
        return self
    
    def extract_brands(self):
        """Identify brands (support accounts)"""
        # Brands are typically the ones sending support responses
        support_authors = self.df[self.df['inbound'] == False]['author_id'].value_counts()
        self.brands = {
            brand: count for brand, count in support_authors.items() 
            if count > 20  # At least 20 support messages
        }
        print(f"Identified {len(self.brands)} support brands")
        print(f"Top brands: {list(self.brands.items())[:5]}")
        return self
    
    def build_conversations(self, brand=None):
        """Reconstruct multi-turn conversations"""
        if brand:
            # Filter for specific brand
            data = self.df[
                (self.df['author_id'] == brand) | 
                (self.df['in_response_to_tweet_id'].notna())
            ].copy()
        else:
            data = self.df.copy()
        
        conversations = defaultdict(list)
        
        for _, row in data.iterrows():
            tweet_id = row['tweet_id']
            conv_id = self._get_conversation_root(row)
            conversations[conv_id].append({
                'tweet_id': tweet_id,
                'author': row['author_id'],
                'text': row['text'],
                'timestamp': row['created_at'],
                'inbound': row['inbound'],
                'is_support': row['author_id'] in self.brands
            })
        
        # Sort each conversation by time
        for conv_id in conversations:
            try:
                conversations[conv_id] = sorted(
                    conversations[conv_id],
                    key=lambda x: pd.to_datetime(x['timestamp'], errors='coerce')
                )
            except:
                # Keep original order if sorting fails
                pass
        
        self.conversations = dict(conversations)
        print(f"Reconstructed {len(self.conversations)} conversations")
        return self
    
    def _get_conversation_root(self, row):
        """Find the root tweet of a conversation thread"""
        root_id = row['tweet_id']
        visited = set()
        
        while pd.notna(row.get('in_response_to_tweet_id', None)):
            if root_id in visited:  # Avoid infinite loops
                break
            visited.add(root_id)
            
            parent_id = row.get('in_response_to_tweet_id')
            if pd.isna(parent_id):
                break
            
            # Try to find parent in dataframe
            parent_rows = self.df[self.df['tweet_id'] == parent_id]
            if len(parent_rows) == 0:
                break
            
            row = parent_rows.iloc[0]
            root_id = parent_id
        
        return root_id
    
    def extract_intents(self):
        """Analyze conversation patterns to define intents"""
        intent_keywords = {
            'Order Status': [
                'order', 'track', 'tracking', 'delivery', 'when', 'where', 'package',
                'shipment', 'shipped', 'arrive', 'arriving', 'status', 'pending',
                'processing', 'delivered'
            ],
            'Returns & Refunds': [
                'return', 'refund', 'send back', 'exchange', 'wrong item',
                'damaged', 'broken', 'defective', 'money back', 'reimbursement',
                'return label', 'rma'
            ],
            'Billing & Payment': [
                'charge', 'bill', 'payment', 'invoice', 'price', 'cost', 'fee',
                'subscription', 'cancel subscription', 'double charged', 'overcharge',
                'credit card', 'payment method'
            ],
            'Technical Issue': [
                'error', 'bug', 'crash', 'not working', 'app', 'website', 'login',
                'password', 'account', 'down', 'offline', 'slow', 'broken feature',
                'glitch', 'problem'
            ],
            'Account & Access': [
                'account', 'login', 'password', 'access', 'reset', 'username',
                'locked', 'suspended', 'banned', 'verify', 'verification'
            ],
            'Product Inquiry': [
                'feature', 'how to', 'help', 'question', 'information', 'what is',
                'where', 'size', 'color', 'availability', 'stock'
            ],
            'Complaint & Escalation': [
                'angry', 'frustrated', 'disappointed', 'terrible', 'awful', 'worst',
                'never', 'unacceptable', 'sue', 'lawsuit', 'manager', 'supervisor',
                'complaint'
            ]
        }
        
        # Classify conversations
        conversation_intents = defaultdict(list)
        
        for conv_id, turns in self.conversations.items():
            if len(turns) == 0:
                continue
            
            # Look at customer messages (first or inbound messages)
            customer_messages = [t['text'] for t in turns if t['inbound']]
            
            if not customer_messages:
                continue
            
            combined_text = ' '.join(customer_messages).lower()
            
            # Find best matching intent
            best_intent = 'General Inquiry'
            max_matches = 0
            
            for intent, keywords in intent_keywords.items():
                matches = sum(1 for kw in keywords if kw in combined_text)
                if matches > max_matches:
                    max_matches = matches
                    best_intent = intent
            
            conversation_intents[best_intent].append({
                'conv_id': conv_id,
                'turns': turns,
                'customer_message': customer_messages[0] if customer_messages else '',
                'support_response': [t['text'] for t in turns if not t['inbound']]
            })
        
        self.intents = conversation_intents
        print("\nIntent Distribution:")
        for intent, conversations in self.intents.items():
            print(f"  {intent}: {len(conversations)} conversations")
        
        return self
    
    def get_statistics(self):
        """Generate comprehensive statistics"""
        stats = {
            'total_tweets': len(self.df),
            'total_conversations': len(self.conversations),
            'unique_brands': len(self.brands),
            'avg_messages_per_conv': np.mean([len(t) for t in self.conversations.values()]),
            'intent_distribution': {k: len(v) for k, v in self.intents.items()},
            'brands': dict(sorted(self.brands.items(), key=lambda x: x[1], reverse=True)[:10]),
        }
        return stats


class ResponseDatabase:
    """Build historical response patterns for each intent"""
    
    def __init__(self, processor):
        self.processor = processor
        self.db = {}
    
    def build(self):
        """Extract common response patterns per intent"""
        for intent, conversations in self.processor.intents.items():
            responses = []
            examples = []
            
            for conv in conversations[:20]:  # Top 20 examples
                if conv['support_response']:
                    responses.extend(conv['support_response'])
                    examples.append({
                        'customer': conv['customer_message'][:150],
                        'response': conv['support_response'][0][:200] if conv['support_response'] else ''
                    })
            
            self.db[intent] = {
                'total_conversations': len(conversations),
                'common_responses': responses[:10],
                'example_conversations': examples[:5],
                'response_patterns': self._extract_patterns(responses)
            }
        
        return self
    
    def _extract_patterns(self, responses):
        """Extract common phrases from responses"""
        patterns = {
            'gratitude': 0,
            'apology': 0,
            'proactive': 0,
            'escalation': 0
        }
        
        for response in responses:
            text = response.lower()
            if any(w in text for w in ['thank', 'appreciate', 'grateful']):
                patterns['gratitude'] += 1
            if any(w in text for w in ['sorry', 'apologize', 'apologise']):
                patterns['apology'] += 1
            if any(w in text for w in ['help', 'assist', 'support', 'happy to']):
                patterns['proactive'] += 1
            if any(w in text for w in ['escalate', 'supervisor', 'manager', 'team']):
                patterns['escalation'] += 1
        
        return patterns
    
    def save(self, path='response_database.json'):
        """Save to JSON"""
        # Convert to serializable format
        data = {}
        for intent, info in self.db.items():
            data[intent] = {
                'total_conversations': info['total_conversations'],
                'common_responses': info['common_responses'][:5],
                'example_conversations': info['example_conversations'],
                'response_patterns': info['response_patterns']
            }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Response database saved to {path}")
        return self


if __name__ == '__main__':
    # Load and process data
    processor = DataProcessor('/mnt/user-data/uploads/twcs.csv')
    processor.load_data(sample_size=50000)  # Use 50k samples for speed
    processor.extract_brands()
    processor.build_conversations()
    processor.extract_intents()
    
    # Print statistics
    stats = processor.get_statistics()
    print("\n=== DATASET STATISTICS ===")
    print(json.dumps(stats, indent=2, default=str))
    
    # Build response database
    db = ResponseDatabase(processor)
    db.build().save('/home/claude/response_database.json')
    
    print("\n✓ Data processing complete!")
