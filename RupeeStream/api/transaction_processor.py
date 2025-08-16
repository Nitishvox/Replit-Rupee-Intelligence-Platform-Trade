import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import time
import streamlit as st

from utils.db_manager import DatabaseManager
from utils.encryption import encrypt_data, decrypt_data
from utils.fraud_detector import FraudDetector
from utils.nlp_parser import NLPParser
from config import Config

class TransactionProcessor:
    """Handles transaction processing, validation, and bulk generation"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.fraud_detector = FraudDetector()
        self.nlp_parser = NLPParser()
        self.config = Config()
        
    def process_manual_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a manually entered transaction"""
        try:
            # Generate transaction ID
            transaction_id = str(uuid.uuid4())[:12].upper()
            
            # Add metadata
            transaction = {
                'id': transaction_id,
                'timestamp': datetime.now(),
                'status': 'Processing',
                **transaction_data
            }
            
            # Validate transaction
            validation_result = self._validate_transaction(transaction)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"Validation failed: {validation_result['message']}"
                }
            
            # Encrypt sensitive data
            transaction = self._encrypt_transaction_data(transaction)
            
            # Run fraud detection
            fraud_score = self.fraud_detector.calculate_risk_score(transaction)
            transaction['risk_score'] = fraud_score
            
            # Process with NLP if narrative exists
            if transaction.get('narrative'):
                nlp_entities = self.nlp_parser.extract_entities(transaction['narrative'])
                transaction['nlp_entities'] = nlp_entities
            
            # Calculate processing time and fees
            transaction['processing_time'] = random.uniform(0.1, 5.0)
            transaction['fees'] = self._calculate_fees(transaction)
            
            # Determine final status based on risk score
            if fraud_score > self.config.HIGH_RISK_THRESHOLD:
                transaction['status'] = 'Review Required'
            elif fraud_score > self.config.MEDIUM_RISK_THRESHOLD:
                transaction['status'] = 'Pending'
            else:
                transaction['status'] = 'Completed'
            
            # Store in database
            success = self.db.insert_transaction(transaction)
            
            if success:
                self._log_transaction_action(transaction_id, 'CREATED', 'Manual transaction processed')
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'transaction': transaction
                }
            else:
                return {
                    'success': False,
                    'message': 'Database storage failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Transaction processing failed: {str(e)}'
            }
    
    def generate_bulk_transactions(self, count: int, 
                                 transaction_type: str = "Random",
                                 corridor: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate bulk transactions for testing and simulation"""
        start_time = time.time()
        
        transactions = []
        
        # Define generation parameters based on type
        if transaction_type == "High Risk":
            amount_multiplier = 5.0
            risk_bias = 30
        elif transaction_type == "Low Risk":
            amount_multiplier = 0.3
            risk_bias = -20
        elif transaction_type == "SRVA Only":
            sources = ["SRVA-INR", "SRVA-Non-INR"]
            amount_multiplier = 2.0
            risk_bias = 10
        else:  # Random
            sources = ["UPI", "NEFT", "RTGS", "SRVA-INR", "SRVA-Non-INR", "SWIFT"]
            amount_multiplier = 1.0
            risk_bias = 0
        
        for i in range(count):
            transaction = self._generate_realistic_transaction(
                corridor=corridor,
                amount_multiplier=amount_multiplier,
                risk_bias=risk_bias,
                sources=sources if 'sources' in locals() else None
            )
            
            # Add processing metadata
            transaction = self._process_generated_transaction(transaction)
            transactions.append(transaction)
        
        # Log generation performance
        duration = time.time() - start_time
        if 'performance_log' in st.session_state:
            st.session_state.performance_log["generation_times"].append((datetime.now(), duration))
        
        return transactions
    
    def _generate_realistic_transaction(self, corridor: Optional[str] = None,
                                      amount_multiplier: float = 1.0,
                                      risk_bias: float = 0,
                                      sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a single realistic transaction"""
        
        # Define options
        default_sources = ["UPI", "NEFT", "RTGS", "SRVA-INR", "SRVA-Non-INR", "SWIFT"]
        currencies = ["INR", "USD", "EUR", "AED", "SGD", "GBP", "RUB"]
        corridors = ["IN-US", "IN-EU", "IN-SG", "IN-AE", "IN-GB", "IN-JP", "IN-RU"]
        
        # Amount ranges by source
        amount_ranges = {
            "UPI": (100, 100000),
            "NEFT": (1000, 10000000),
            "RTGS": (200000, 100000000),
            "SRVA-INR": (50000, 50000000),
            "SRVA-Non-INR": (10000, 20000000),
            "SWIFT": (100000, 200000000)
        }
        
        # Selection logic
        available_sources = sources or default_sources
        selected_source = np.random.choice(available_sources, 
                                         p=self._get_source_probabilities(available_sources))
        
        selected_currency = np.random.choice(currencies, p=[0.4, 0.2, 0.15, 0.1, 0.08, 0.05, 0.02])
        selected_corridor = corridor or np.random.choice(corridors)
        
        # Amount calculation
        min_amt, max_amt = amount_ranges.get(selected_source, (1000, 1000000))
        base_amount = np.random.uniform(min_amt, max_amt) * amount_multiplier
        
        # Timestamp with realistic distribution (more during business hours)
        hour_weights = [0.02]*6 + [0.05]*3 + [0.08]*8 + [0.05]*4 + [0.02]*3  # 24 hours
        # Normalize to ensure sum equals 1
        hour_weights = [w/sum(hour_weights) for w in hour_weights]
        random_hour = np.random.choice(range(24), p=hour_weights)
        timestamp = datetime.now().replace(hour=random_hour, minute=random.randint(0, 59), 
                                         second=random.randint(0, 59))
        timestamp -= timedelta(seconds=random.randint(0, 86400))  # Random day offset
        
        # Risk calculation
        base_risk = np.random.uniform(10, 30) + risk_bias
        
        # Risk factors
        if base_amount > 10000000:
            base_risk += 25
        if selected_currency != "INR":
            base_risk += 15
        if selected_source.startswith("SRVA"):
            base_risk += 10
        if selected_corridor in ["IN-US", "IN-EU"]:
            base_risk += 8
        if timestamp.hour < 6 or timestamp.hour > 22:
            base_risk += 5  # Off-hours transactions
        
        # Status determination
        statuses = ["Completed", "Pending", "Failed", "Processing"]
        if base_risk > 75:
            status_weights = [0.4, 0.3, 0.2, 0.1]  # Higher failure rate for high risk
        else:
            status_weights = [0.7, 0.15, 0.05, 0.1]  # Normal distribution
        
        transaction = {
            'id': str(uuid.uuid4())[:12].upper(),
            'source': selected_source,
            'amount': round(base_amount, 2),
            'currency': selected_currency,
            'corridor': selected_corridor,
            'timestamp': timestamp,
            'status': np.random.choice(statuses, p=status_weights),
            'risk_score': min(max(base_risk + np.random.uniform(-5, 15), 0), 100),
            'processing_time': np.random.uniform(0.1, 5.0),
            'counterparty': f"Entity_{np.random.randint(1000, 9999)}",
            'reference': f"REF{np.random.randint(100000, 999999)}",
            'narrative': self._generate_narrative(selected_source, base_amount, selected_currency)
        }
        
        return transaction
    
    def _process_generated_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Process generated transaction with all validation and enhancement steps"""
        
        # Calculate fees
        transaction['fees'] = self._calculate_fees(transaction)
        
        # Run fraud detection
        fraud_score = self.fraud_detector.calculate_risk_score(transaction)
        transaction['fraud_flags'] = self.fraud_detector.get_fraud_flags(transaction)
        
        # Process narrative with NLP
        if transaction.get('narrative'):
            nlp_entities = self.nlp_parser.extract_entities(transaction['narrative'])
            transaction['nlp_entities'] = nlp_entities
        
        # Encrypt sensitive data if encryption key available
        if st.session_state.get('encryption_key'):
            transaction = self._encrypt_transaction_data(transaction)
        
        return transaction
    
    def _validate_transaction(self, transaction: Dict[str, Any]) -> Dict[str, bool]:
        """Validate transaction data"""
        
        # Required fields check
        required_fields = ['amount', 'currency', 'source', 'corridor']
        for field in required_fields:
            if field not in transaction or transaction[field] is None:
                return {'valid': False, 'message': f'Missing required field: {field}'}
        
        # Amount validation
        if transaction['amount'] <= 0:
            return {'valid': False, 'message': 'Amount must be positive'}
        
        if transaction['amount'] > 1000000000:  # 100 crore limit
            return {'valid': False, 'message': 'Amount exceeds maximum limit'}
        
        # Currency validation
        valid_currencies = ["INR", "USD", "EUR", "GBP", "SGD", "RUB", "AED", "JPY"]
        if transaction['currency'] not in valid_currencies:
            return {'valid': False, 'message': 'Invalid currency'}
        
        # Source validation
        valid_sources = ["UPI", "NEFT", "RTGS", "SRVA-INR", "SRVA-Non-INR", "SWIFT"]
        if transaction['source'] not in valid_sources:
            return {'valid': False, 'message': 'Invalid transaction source'}
        
        # Corridor validation
        valid_corridors = ["IN-US", "IN-EU", "IN-SG", "IN-AE", "IN-GB", "IN-JP", "IN-RU"]
        if transaction['corridor'] not in valid_corridors:
            return {'valid': False, 'message': 'Invalid trading corridor'}
        
        # Business logic validation
        if transaction['source'] == 'UPI' and transaction['amount'] > 100000:
            return {'valid': False, 'message': 'UPI transaction exceeds daily limit'}
        
        if transaction['source'] == 'RTGS' and transaction['amount'] < 200000:
            return {'valid': False, 'message': 'RTGS minimum amount is ₹2,00,000'}
        
        return {'valid': True, 'message': 'Transaction validated successfully'}
    
    def _encrypt_transaction_data(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive transaction data"""
        encryption_key = st.session_state.get('encryption_key')
        if not encryption_key:
            return transaction
        
        # Fields to encrypt
        sensitive_fields = ['counterparty', 'narrative', 'reference']
        
        for field in sensitive_fields:
            if field in transaction and transaction[field]:
                transaction[f'encrypted_{field}'] = encrypt_data(transaction[field], encryption_key)
                # Keep original for processing, remove before storage in production
        
        return transaction
    
    def _calculate_fees(self, transaction: Dict[str, Any]) -> float:
        """Calculate transaction fees"""
        amount = transaction['amount']
        source = transaction['source']
        
        # Fee structure by source
        fee_rates = {
            'UPI': 0.0,  # No fees for UPI
            'NEFT': 0.0005,  # 0.05%
            'RTGS': 0.001,   # 0.1%
            'SRVA-INR': 0.002,  # 0.2%
            'SRVA-Non-INR': 0.003,  # 0.3%
            'SWIFT': 0.005   # 0.5%
        }
        
        base_fee_rate = fee_rates.get(source, 0.002)
        
        # Apply volume discounts
        if amount > 50000000:  # 5 crore+
            base_fee_rate *= 0.5
        elif amount > 10000000:  # 1 crore+
            base_fee_rate *= 0.7
        
        # Minimum and maximum fees
        calculated_fee = amount * base_fee_rate
        min_fee = 10.0
        max_fee = amount * 0.01  # Max 1%
        
        return max(min_fee, min(calculated_fee, max_fee))
    
    def _generate_narrative(self, source: str, amount: float, currency: str) -> str:
        """Generate realistic transaction narratives"""
        narratives = [
            f"Export payment for goods via {source}",
            f"Import settlement {currency} {amount:,.2f}",
            f"Trade finance facility utilization",
            f"Cross-border payment for services",
            f"International trade settlement",
            f"Foreign exchange forward contract",
            f"Export invoice settlement",
            f"Import documentary credit",
            f"Trade receivables collection",
            f"International payment gateway"
        ]
        
        return random.choice(narratives)
    
    def _get_source_probabilities(self, sources: List[str]) -> List[float]:
        """Get probability distribution for transaction sources"""
        probs = []
        total_sources = len(sources)
        
        for source in sources:
            if source == "UPI":
                probs.append(0.3)
            elif source == "NEFT":
                probs.append(0.25)
            elif source == "RTGS":
                probs.append(0.15)
            elif source.startswith("SRVA"):
                probs.append(0.1)
            else:
                probs.append(0.1)
        
        # Normalize probabilities
        prob_sum = sum(probs)
        return [p/prob_sum for p in probs]
    
    def _log_transaction_action(self, transaction_id: str, action: str, details: str):
        """Log transaction-related actions"""
        log_entry = {
            'timestamp': datetime.now(),
            'entity_type': 'TRANSACTION',
            'entity_id': transaction_id,
            'action': action,
            'details': details,
            'user_role': st.session_state.get('user_role', 'system')
        }
        self.db.insert_audit_log(log_entry)

def calculate_tps() -> float:
    """Calculate current transactions per second"""
    if 'performance_log' not in st.session_state:
        return 0.0
    
    generation_times = st.session_state.performance_log.get("generation_times", [])
    if not generation_times:
        return 0.0
    
    # Consider transactions from the last 5 minutes
    cutoff_time = datetime.now() - timedelta(minutes=5)
    recent_generations = [
        t for t, _ in generation_times
        if t > cutoff_time
    ]
    
    if not recent_generations:
        return 0.0
    
    time_window = (max(recent_generations) - min(recent_generations)).total_seconds()
    if time_window == 0:
        return 0.0
    
    tps = len(recent_generations) / time_window
    return tps
