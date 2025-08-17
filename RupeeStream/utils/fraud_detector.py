import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import random
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import DBSCAN
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import streamlit as st
import threading
import time
import json

from config import Config

# Helper class for the rule-based system
class _RuleEvaluator:
    def __init__(self, rules: List[Tuple[callable, int]]):
        self.rules = rules

    def evaluate(self, transaction: Dict[str, Any]) -> float:
        """Evaluates a transaction against a set of rules."""
        total_risk = 0
        for rule_func, risk_value in self.rules:
            try:
                if rule_func(transaction):
                    total_risk += risk_value
            except Exception:
                continue # Ignore rule if it fails
        return min(100.0, float(total_risk))

class SynchronizedAIFraudDetector:
    """
    A thread-safe, advanced fraud detection system combining multiple models.
    """
    
    def __init__(self):
        self.config = Config()
        
        # Multiple ML models for ensemble detection
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.random_forest = RandomForestClassifier(n_estimators=100, random_state=42)
        self.dbscan_model = DBSCAN(eps=0.5, min_samples=5)
        
        # Scalers for different model types
        self.standard_scaler = StandardScaler()
        self.robust_scaler = RobustScaler()
        
        # AI-powered pattern recognition
        self.pattern_memory = []
        self.fraud_signatures = {}
        self.model_performance = {'accuracy': 0.0, 'last_updated': datetime.now()}
        
        # Synchronization components
        self.sync_lock = threading.Lock()
        self.real_time_queue = []
        self.batch_size = 50
        
        # Traditional rule-based components (simplified for AI enhancement)
        self.fraud_patterns = {
            'velocity_rules': self._create_velocity_rules(),
            'amount_rules': self._create_amount_rules(),
            'behavior_rules': self._create_behavior_rules(),
            'temporal_rules': self._create_temporal_rules()
        }
        
        # Start real-time processing thread
        self._start_realtime_processor()

    def _create_velocity_rules(self) -> _RuleEvaluator:
        """Creates velocity-based fraud rules."""
        # Note: These rules are simplified as they don't have access to full user history here.
        # The main AI model handles more complex velocity checks.
        rules = [
            (lambda t: t.get('velocity_risk_indicator', 0) > 5, 40), # Placeholder for a pre-calculated indicator
        ]
        return _RuleEvaluator(rules)

    def _create_amount_rules(self) -> _RuleEvaluator:
        """Creates amount-based fraud rules."""
        rules = [
            (lambda t: t.get('amount', 0) > 5_000_000, 30), # High amount
            (lambda t: 9900 < t.get('amount', 0) % 10000 < 9999, 50), # Structuring/Smurfing attempt
            (lambda t: t.get('amount', 0) % 1000 == 0 and t.get('amount', 0) > 10000, 15), # Round numbers
        ]
        return _RuleEvaluator(rules)

    def _create_behavior_rules(self) -> _RuleEvaluator:
        """Creates behavior-based fraud rules."""
        rules = [
            (lambda t: t.get('is_new_counterparty', False), 25), # Transaction to a new beneficiary
            (lambda t: t.get('source') == 'SWIFT' and t.get('corridor') in ['IN-RU', 'IN-AE'], 40), # High-risk channel/corridor combo
        ]
        return _RuleEvaluator(rules)

    def _create_temporal_rules(self) -> _RuleEvaluator:
        """Creates time-based fraud rules."""
        rules = [
            (lambda t: pd.to_datetime(t.get('timestamp')).hour < 6 or pd.to_datetime(t.get('timestamp')).hour > 22, 35), # Late night/early morning
            (lambda t: pd.to_datetime(t.get('timestamp')).weekday() >= 5, 15), # Weekend transaction
        ]
        return _RuleEvaluator(rules)
        
    def calculate_risk_score(self, transaction: Dict[str, Any]) -> float:
        """Calculate comprehensive AI-powered risk score for a transaction"""
        
        with self.sync_lock:
            # Add to real-time processing queue
            self.real_time_queue.append(transaction)
        
        risk_components = []
        
        # Advanced AI pattern recognition (highest weight)
        ai_risk = self._calculate_ai_pattern_risk(transaction)
        risk_components.append(('ai_pattern', ai_risk, 0.35))
        
        # Ensemble ML models
        ensemble_risk = self._calculate_ensemble_ml_risk(transaction)
        risk_components.append(('ensemble_ml', ensemble_risk, 0.25))
        
        # Traditional rule-based risk (reduced weight)
        rule_risk = self._calculate_rule_based_risk(transaction)
        risk_components.append(('rules', rule_risk, 0.20))
        
        # Behavioral anomaly detection
        behavioral_risk = self._calculate_behavioral_anomaly_risk(transaction)
        risk_components.append(('behavioral', behavioral_risk, 0.15))
        
        # Real-time contextual analysis
        context_risk = self._calculate_realtime_context_risk(transaction)
        risk_components.append(('realtime_context', context_risk, 0.05))
        
        # Dynamic weighted average based on model confidence
        confidence_weights = self._calculate_model_confidence(transaction)
        total_risk = sum(
            risk * weight * confidence_weights.get(component, 1.0) 
            for component, risk, weight in risk_components
        )
        
        # Store transaction for pattern learning
        self._update_pattern_memory(transaction, total_risk)
        
        # Ensure risk is between 0 and 100
        return max(0, min(100, total_risk))
    
    def _calculate_rule_based_risk(self, transaction: Dict[str, Any]) -> float:
        """
        Calculates risk based on a set of predefined traditional rules.
        Combines risks from different rule categories.
        """
        risks = []
        
        # Evaluate each rule category from the fraud_patterns dictionary
        for rule_name, rule_evaluator in self.fraud_patterns.items():
            try:
                risk = rule_evaluator.evaluate(transaction)
                risks.append(risk)
            except Exception:
                # In case a rule fails, append a neutral risk
                risks.append(5) 
        
        # Return the average risk from all rule categories
        return np.mean(risks) if risks else 0.0

    def _start_realtime_processor(self):
        """Start background thread for real-time fraud detection processing"""
        def process_realtime():
            while True:
                try:
                    if len(self.real_time_queue) >= self.batch_size:
                        with self.sync_lock:
                            batch = self.real_time_queue[:self.batch_size]
                            self.real_time_queue = self.real_time_queue[self.batch_size:]
                        
                        # Process batch for pattern learning
                        self._process_batch_for_learning(batch)
                    
                    time.sleep(5)  # Check every 5 seconds
                except Exception as e:
                    st.warning(f"Real-time fraud processing error: {str(e)}")
                    time.sleep(10)
        
        # Start daemon thread
        thread = threading.Thread(target=process_realtime, daemon=True)
        thread.start()
    
    def _calculate_ai_pattern_risk(self, transaction: Dict[str, Any]) -> float:
        """AI-powered pattern recognition for fraud detection"""
        try:
            # Extract transaction signature
            signature = self._extract_transaction_signature(transaction)
            
            # Check against known fraud patterns
            pattern_risk = 0.0
            
            for known_signature, risk_level in self.fraud_signatures.items():
                similarity = self._calculate_signature_similarity(signature, known_signature)
                if similarity > 0.8:  # High similarity threshold
                    pattern_risk = max(pattern_risk, risk_level * similarity)
            
            # Behavioral anomaly detection
            if len(self.pattern_memory) > 10:
                behavioral_score = self._detect_behavioral_anomaly(transaction)
                pattern_risk = max(pattern_risk, behavioral_score)
            
            return min(100, pattern_risk)
            
        except Exception:
            return 25  # Default moderate risk
    
    def _calculate_ensemble_ml_risk(self, transaction: Dict[str, Any]) -> float:
        """Ensemble ML model risk calculation"""
        try:
            features = self._extract_enhanced_features(transaction)
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            scaled_features = self.standard_scaler.fit_transform(features_array)
            robust_features = self.robust_scaler.fit_transform(features_array)
            
            risks = []
            
            # Isolation Forest (Anomaly Detection)
            if hasattr(self.isolation_forest, 'decision_function'):
                anomaly_score = self.isolation_forest.decision_function(scaled_features)[0]
                # Convert to risk score (lower scores = higher risk)
                isolation_risk = max(0, (0.5 - anomaly_score) * 100)
                risks.append(isolation_risk)
            
            # Clustering-based anomaly detection
            cluster_risk = self._cluster_based_risk(robust_features[0])
            risks.append(cluster_risk)
            
            # Statistical anomaly detection
            statistical_risk = self._statistical_anomaly_risk(features)
            risks.append(statistical_risk)
            
            # Return weighted average
            return np.mean(risks) if risks else 25
            
        except Exception:
            return 25
    
    def _calculate_behavioral_anomaly_risk(self, transaction: Dict[str, Any]) -> float:
        """Advanced behavioral anomaly detection"""
        try:
            # Time-series analysis of user behavior
            user_id = transaction.get('counterparty', 'unknown')
            
            # Get historical transactions for this user
            user_history = [
                t for t in self.pattern_memory 
                if t.get('counterparty') == user_id
            ]
            
            if len(user_history) < 3:
                return 15  # New user - moderate risk
            
            # Analyze spending patterns
            amounts = [t.get('amount', 0) for t in user_history]
            avg_amount = np.mean(amounts)
            std_amount = np.std(amounts)
            
            current_amount = transaction.get('amount', 0)
            
            # Z-score based anomaly
            if std_amount > 0:
                z_score = abs(current_amount - avg_amount) / std_amount
                if z_score > 3:  # 3-sigma rule
                    return min(80, z_score * 15)
            
            # Frequency analysis
            recent_transactions = [
                t for t in user_history 
                if pd.to_datetime(t.get('timestamp', datetime.now())) > datetime.now() - timedelta(hours=24)
            ]
            
            if len(recent_transactions) > 10:  # Too many transactions
                return 60
            
            return 10  # Normal behavior
            
        except Exception:
            return 20
    
    def _calculate_realtime_context_risk(self, transaction: Dict[str, Any]) -> float:
        """Real-time contextual analysis"""
        try:
            risk = 0.0
            
            # Current time analysis
            current_time = datetime.now()
            transaction_time = transaction.get('timestamp', current_time)
            if isinstance(transaction_time, str):
                transaction_time = pd.to_datetime(transaction_time)
            
            # Holiday/weekend premium
            if current_time.weekday() >= 5:
                risk += 10
            
            # Late night/early morning
            if current_time.hour < 6 or current_time.hour > 22:
                risk += 15
            
            # Recent suspicious activity check
            recent_high_risk = [
                t for t in self.real_time_queue[-20:]  # Last 20 transactions
                if t.get('calculated_risk', 0) > 70
            ]
            
            if len(recent_high_risk) > 3:
                risk += 25
            
            # Geographic/corridor risk (simulated)
            corridor = transaction.get('corridor', '')
            high_risk_corridors = ['IN-RU', 'IN-AE', 'IN-TR']
            if corridor in high_risk_corridors:
                risk += 20
            
            return min(100, risk)
            
        except Exception:
            return 5
    
    def _extract_transaction_signature(self, transaction: Dict[str, Any]) -> str:
        """Extract unique signature from transaction for pattern matching"""
        # Create a unique signature based on key transaction features
        amount_range = self._categorize_amount(transaction.get('amount', 0))
        time_category = self._categorize_time(transaction.get('timestamp', datetime.now()))
        source = transaction.get('source', 'unknown')
        corridor = transaction.get('corridor', 'unknown')
        
        signature = f"{amount_range}_{time_category}_{source}_{corridor}"
        return signature
    
    def _calculate_signature_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between two transaction signatures"""
        parts1 = sig1.split('_')
        parts2 = sig2.split('_')
        
        if len(parts1) != len(parts2):
            return 0.0
        
        matches = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
        return matches / len(parts1)
    
    def _extract_enhanced_features(self, transaction: Dict[str, Any]) -> List[float]:
        """Extract enhanced feature set for ML models"""
        features = []
        
        # Amount features
        amount = transaction.get('amount', 0)
        features.extend([
            np.log1p(amount),  # Log amount
            amount / 1000000,  # Amount in millions
            1 if amount > 1000000 else 0,  # High amount flag
        ])
        
        # Time features
        timestamp = transaction.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        
        features.extend([
            timestamp.hour,
            timestamp.weekday(),
            1 if timestamp.hour < 6 or timestamp.hour > 22 else 0,  # Off-hours
            1 if timestamp.weekday() >= 5 else 0,  # Weekend
        ])
        
        # Categorical features (encoded)
        source_map = {'UPI': 0, 'NEFT': 1, 'RTGS': 2, 'SRVA-INR': 3, 'SRVA-Non-INR': 4, 'SWIFT': 5}
        currency_map = {'INR': 0, 'USD': 1, 'EUR': 2, 'GBP': 3, 'SGD': 4, 'RUB': 5, 'AED': 6}
        corridor_map = {'IN-US': 0, 'IN-EU': 1, 'IN-GB': 2, 'IN-SG': 3, 'IN-AE': 4, 'IN-RU': 5, 'IN-JP': 6}
        
        features.extend([
            source_map.get(transaction.get('source', ''), -1),
            currency_map.get(transaction.get('currency', ''), -1),
            corridor_map.get(transaction.get('corridor', ''), -1),
        ])
        
        # Risk and processing features
        features.extend([
            transaction.get('risk_score', 0),
            transaction.get('processing_time', 0),
        ])
        
        return features
    
    def _cluster_based_risk(self, features: np.ndarray) -> float:
        """Calculate risk based on clustering analysis"""
        try:
            if len(self.pattern_memory) < 10:
                return 20  # Not enough data for clustering
            
            # Use features from pattern memory for clustering
            historical_features = [
                self._extract_enhanced_features(t) for t in self.pattern_memory[-100:]
            ]
            
            if len(historical_features) > 5:
                X = np.array(historical_features)
                
                # Fit DBSCAN
                clusters = self.dbscan_model.fit_predict(X)
                
                # Find cluster for current transaction
                distances = [np.linalg.norm(features - f) for f in historical_features]
                min_distance = min(distances)
                
                # If very far from any cluster, higher risk
                if min_distance > np.std(distances) * 2:
                    return 70
                
            return 15
            
        except Exception:
            return 20
    
    def _statistical_anomaly_risk(self, features: List[float]) -> float:
        """Statistical anomaly detection"""
        try:
            if len(self.pattern_memory) < 5:
                return 15
            
            # Compare with historical statistics
            historical_features = [
                self._extract_enhanced_features(t) for t in self.pattern_memory
            ]
            
            risk = 0
            for i, feature_val in enumerate(features):
                historical_vals = [hf[i] for hf in historical_features if len(hf) > i]
                
                if len(historical_vals) > 2:
                    mean_val = np.mean(historical_vals)
                    std_val = np.std(historical_vals)
                    
                    if std_val > 0:
                        z_score = abs(feature_val - mean_val) / std_val
                        if z_score > 3:  # 3-sigma anomaly
                            risk += min(20, z_score * 5)
            
            return min(100, risk)
            
        except Exception:
            return 15
    
    def _calculate_model_confidence(self, transaction: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence weights for different model components"""
        confidence = {
            'ai_pattern': 1.0,
            'ensemble_ml': 1.0,
            'rules': 1.0,
            'behavioral': 1.0,
            'realtime_context': 1.0
        }
        
        # Reduce confidence for new patterns
        if len(self.pattern_memory) < 10:
            confidence['ai_pattern'] = 0.5
            confidence['behavioral'] = 0.3
        
        # Reduce ML confidence if insufficient training data
        if len(self.pattern_memory) < 50:
            confidence['ensemble_ml'] = 0.7
        
        return confidence
    
    def _update_pattern_memory(self, transaction: Dict[str, Any], risk_score: float):
        """Update pattern memory with new transaction"""
        try:
            # Add calculated risk to transaction
            transaction_copy = transaction.copy()
            transaction_copy['calculated_risk'] = risk_score
            transaction_copy['processing_timestamp'] = datetime.now()
            
            # Add to memory
            self.pattern_memory.append(transaction_copy)
            
            # Keep only recent patterns (last 1000 transactions)
            if len(self.pattern_memory) > 1000:
                self.pattern_memory = self.pattern_memory[-1000:]
            
            # Update fraud signatures for high-risk transactions
            if risk_score > 75:
                signature = self._extract_transaction_signature(transaction)
                self.fraud_signatures[signature] = max(
                    self.fraud_signatures.get(signature, 0), 
                    risk_score / 100
                )
            
        except Exception:
            pass  # Silent fail for memory updates
    
    def _categorize_amount(self, amount: float) -> str:
        """Categorize transaction amount"""
        if amount < 10000:
            return 'micro'
        elif amount < 100000:
            return 'small'
        elif amount < 1000000:
            return 'medium'
        elif amount < 10000000:
            return 'large'
        else:
            return 'macro'
    
    def _categorize_time(self, timestamp) -> str:
        """Categorize transaction time"""
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        
        hour = timestamp.hour
        if 6 <= hour < 10:
            return 'morning'
        elif 10 <= hour < 14:
            return 'midday'
        elif 14 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def _process_batch_for_learning(self, batch: List[Dict[str, Any]]):
        """Process batch of transactions for continuous learning"""
        try:
            if len(batch) < 5:
                return
            
            # Extract features from batch
            features = [self._extract_enhanced_features(t) for t in batch]
            
            # Update models with new data (simplified retraining)
            if len(features) > 10:
                X = np.array(features)
                
                # Update isolation forest
                self.isolation_forest.fit(X)
                
                # Update performance metrics
                self.model_performance['last_updated'] = datetime.now()
                
        except Exception:
            pass  # Silent fail for batch processing
    
    def _detect_behavioral_anomaly(self, transaction: Dict[str, Any]) -> float:
        """Advanced behavioral anomaly detection using AI patterns"""
        try:
            # Pattern frequency analysis
            signature = self._extract_transaction_signature(transaction)
            similar_patterns = [
                t for t in self.pattern_memory[-200:]  # Recent patterns
                if self._calculate_signature_similarity(
                    signature, 
                    self._extract_transaction_signature(t)
                ) > 0.6
            ]
            
            if len(similar_patterns) == 0:
                return 60  # Completely new pattern
            
            # Analyze historical risk of similar patterns
            avg_historical_risk = np.mean([
                t.get('calculated_risk', 25) for t in similar_patterns
            ])
            
            if avg_historical_risk > 60:
                return min(85, avg_historical_risk * 1.2)
            
            return max(5, avg_historical_risk * 0.8)
            
        except Exception:
            return 25
    
    def get_fraud_flags(self, transaction: Dict[str, Any]) -> List[str]:
        """Get detailed fraud flags for transaction"""
        flags = []
        
        # High amount flag
        amount = transaction.get('amount', 0)
        if amount > 10000000:
            flags.append('HIGH_AMOUNT')
        
        # Off-hours flag
        timestamp = transaction.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        
        if timestamp.hour < 6 or timestamp.hour > 22:
            flags.append('OFF_HOURS')
        
        # High-risk corridor
        corridor = transaction.get('corridor', '')
        if corridor in ['IN-RU', 'IN-AE']:
            flags.append('HIGH_RISK_CORRIDOR')
        
        # Pattern-based flags
        signature = self._extract_transaction_signature(transaction)
        if signature in self.fraud_signatures:
            if self.fraud_signatures[signature] > 0.7:
                flags.append('KNOWN_FRAUD_PATTERN')
        
        # Velocity flag
        user_id = transaction.get('counterparty', 'unknown')
        recent_transactions = [
            t for t in self.pattern_memory[-50:]
            if t.get('counterparty') == user_id
        ]
        
        if len(recent_transactions) > 5:
            flags.append('HIGH_VELOCITY')
        
        return flags

    def generate_fraud_alerts(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fraud alerts for a list of transactions."""
        alerts = []
        for txn in transactions:
            flags = self.get_fraud_flags(txn)
            if flags:
                severity = 'high' if len(flags) > 2 else 'medium' if len(flags) > 1 else 'low'
                message = f"Fraud flags in txn {txn.get('id', 'unknown')}: {', '.join(flags)} (Risk: {txn.get('risk_score', 0):.1f})"
                alerts.append({'severity': severity, 'message': message})
        return alerts

    def _update_model_from_db(self):
        """Update internal models and patterns from the central database"""
        try:
            # Placeholder for database fetch
            # In real implementation, this would pull new data and model updates from a database
            new_data = []  # Fetch new transaction data
            updated_signatures = {}  # Fetch updated fraud signatures
            
            with self.sync_lock:
                # Update pattern memory with new data
                for transaction in new_data:
                    self._update_pattern_memory(transaction, transaction.get('risk_score', 0))
                
                # Update fraud signatures
                self.fraud_signatures.update(updated_signatures)
        
        except Exception as e:
            st.warning(f"Model update error: {str(e)}")
            time.sleep(10)  # Wait before retrying

# Backward compatibility alias
FraudDetector = SynchronizedAIFraudDetector

