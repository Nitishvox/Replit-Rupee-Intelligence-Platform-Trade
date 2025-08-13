import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class AIFraudDetector:
    """AI-powered fraud detection system using machine learning algorithms"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        self.model_path = 'fraud_detection_model.pkl'
        self.scaler_path = 'fraud_detection_scaler.pkl'
        self.encoders_path = 'fraud_detection_encoders.pkl'
        
        # Fraud detection thresholds
        self.thresholds = {
            'low_risk': 0.3,
            'medium_risk': 0.6,
            'high_risk': 0.8,
            'critical_risk': 0.9
        }
        
        # Feature importance weights
        self.feature_weights = {
            'amount': 0.25,
            'frequency': 0.20,
            'timing': 0.15,
            'country_risk': 0.15,
            'account_history': 0.10,
            'transaction_pattern': 0.15
        }
        
        # Load or initialize models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models or initialize new ones"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                
                if os.path.exists(self.encoders_path):
                    self.encoders = joblib.load(self.encoders_path)
                else:
                    self.encoders = {}
                
                st.session_state.model_loaded = True
            else:
                self.model = None
                self.scaler = None
                self.encoders = {}
                st.session_state.model_loaded = False
                
        except Exception as e:
            st.error(f"Error loading ML models: {str(e)}")
            self.model = None
            self.scaler = None
            self.encoders = {}
            st.session_state.model_loaded = False
    
    def detect_fraud_single(self, transaction_data: Dict) -> Dict:
        """Detect fraud for a single transaction"""
        try:
            # Calculate risk score using rule-based approach
            risk_score = self._calculate_rule_based_risk(transaction_data)
            
            # If ML model is available, use it for additional scoring
            if self.model is not None:
                ml_features = self._extract_features(transaction_data)
                if ml_features is not None:
                    ml_score = self._predict_ml_risk(ml_features)
                    # Combine rule-based and ML scores
                    risk_score = (risk_score * 0.6) + (ml_score * 0.4)
            
            # Determine risk level and fraud status
            risk_level = self._get_risk_level(risk_score)
            is_fraud = risk_score > self.thresholds['medium_risk']
            
            # Generate explanation
            reason = self._generate_fraud_reason(transaction_data, risk_score)
            
            result = {
                'transaction_id': transaction_data.get('transaction_id', 'unknown'),
                'risk_score': round(risk_score, 3),
                'risk_level': risk_level,
                'is_fraud': is_fraud,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'detection_method': 'hybrid' if self.model else 'rule_based'
            }
            
            # Save detection result
            self.db_manager.insert_fraud_detection(result)
            
            return result
            
        except Exception as e:
            st.error(f"Error in fraud detection: {str(e)}")
            return {
                'transaction_id': transaction_data.get('transaction_id', 'unknown'),
                'risk_score': 0.5,
                'risk_level': 'medium',
                'is_fraud': False,
                'reason': 'Detection error occurred',
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_rule_based_risk(self, transaction_data: Dict) -> float:
        """Calculate risk score using rule-based approach"""
        risk_factors = []
        
        # Amount-based risk
        amount = transaction_data.get('amount', 0)
        if amount > 10000000:  # > 1 Cr
            risk_factors.append(0.8)
        elif amount > 5000000:  # > 50L
            risk_factors.append(0.6)
        elif amount < 100:  # Very small amounts
            risk_factors.append(0.4)
        else:
            risk_factors.append(0.1)
        
        # Country risk
        high_risk_countries = ['Country1', 'Country2']  # Mock high-risk countries
        country = transaction_data.get('country', '')
        if country in high_risk_countries:
            risk_factors.append(0.7)
        else:
            risk_factors.append(0.2)
        
        # Currency risk
        currency = transaction_data.get('currency', '')
        if currency in ['BTC', 'ETH']:  # Crypto currencies
            risk_factors.append(0.9)
        elif currency in ['USD', 'EUR', 'GBP']:  # Standard currencies
            risk_factors.append(0.1)
        else:
            risk_factors.append(0.3)
        
        # Timing risk (transactions outside business hours)
        try:
            timestamp = datetime.fromisoformat(transaction_data.get('timestamp', datetime.now().isoformat()))
            hour = timestamp.hour
            if hour < 6 or hour > 22:  # Outside business hours
                risk_factors.append(0.5)
            else:
                risk_factors.append(0.1)
        except:
            risk_factors.append(0.2)
        
        # Account pattern risk
        from_account = transaction_data.get('from_account', '')
        to_account = transaction_data.get('to_account', '')
        
        if from_account == to_account:
            risk_factors.append(0.9)  # Self-transfer
        else:
            risk_factors.append(0.1)
        
        # Transaction type risk
        transaction_type = transaction_data.get('type', '')
        if 'urgent' in transaction_type.lower() or 'immediate' in transaction_type.lower():
            risk_factors.append(0.6)
        else:
            risk_factors.append(0.2)
        
        # Calculate weighted average
        return sum(risk_factors) / len(risk_factors)
    
    def _extract_features(self, transaction_data: Dict) -> Optional[np.ndarray]:
        """Extract features for ML model"""
        try:
            features = []
            
            # Numerical features
            features.append(transaction_data.get('amount', 0))
            features.append(len(transaction_data.get('description', '')))
            
            # Time-based features
            try:
                timestamp = datetime.fromisoformat(transaction_data.get('timestamp', datetime.now().isoformat()))
                features.extend([
                    timestamp.hour,
                    timestamp.weekday(),
                    timestamp.day
                ])
            except:
                features.extend([12, 1, 15])  # Default values
            
            # Categorical features (encoded)
            categorical_features = ['currency', 'country', 'type']
            for feature in categorical_features:
                value = transaction_data.get(feature, 'unknown')
                if feature in self.encoders:
                    try:
                        encoded_value = self.encoders[feature].transform([value])[0]
                    except:
                        encoded_value = 0  # Unknown category
                else:
                    encoded_value = hash(value) % 100  # Simple hash encoding
                features.append(encoded_value)
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            st.error(f"Error extracting features: {str(e)}")
            return None
    
    def _predict_ml_risk(self, features: np.ndarray) -> float:
        """Predict risk using ML model"""
        try:
            if self.model and self.scaler:
                # Scale features
                features_scaled = self.scaler.transform(features)
                
                # Predict anomaly score
                if hasattr(self.model, 'decision_function'):
                    # Isolation Forest
                    score = self.model.decision_function(features_scaled)[0]
                    # Normalize score to 0-1 range
                    normalized_score = max(0, min(1, (1 - score) / 2))
                else:
                    # Random Forest probability
                    proba = self.model.predict_proba(features_scaled)[0]
                    normalized_score = proba[1] if len(proba) > 1 else proba[0]
                
                return float(normalized_score)
            
            return 0.5  # Neutral score if model not available
            
        except Exception as e:
            st.error(f"Error in ML prediction: {str(e)}")
            return 0.5
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score >= self.thresholds['critical_risk']:
            return 'Critical'
        elif risk_score >= self.thresholds['high_risk']:
            return 'High'
        elif risk_score >= self.thresholds['medium_risk']:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_fraud_reason(self, transaction_data: Dict, risk_score: float) -> str:
        """Generate explanation for fraud detection result"""
        reasons = []
        
        amount = transaction_data.get('amount', 0)
        if amount > 10000000:
            reasons.append("Unusually high transaction amount")
        elif amount < 100:
            reasons.append("Unusually low transaction amount")
        
        country = transaction_data.get('country', '')
        high_risk_countries = ['Country1', 'Country2']
        if country in high_risk_countries:
            reasons.append(f"High-risk country: {country}")
        
        # Timing analysis
        try:
            timestamp = datetime.fromisoformat(transaction_data.get('timestamp', datetime.now().isoformat()))
            if timestamp.hour < 6 or timestamp.hour > 22:
                reasons.append("Transaction outside business hours")
        except:
            pass
        
        # Account pattern
        from_account = transaction_data.get('from_account', '')
        to_account = transaction_data.get('to_account', '')
        if from_account == to_account:
            reasons.append("Self-transfer detected")
        
        if not reasons:
            if risk_score > 0.7:
                reasons.append("Multiple risk factors detected")
            elif risk_score > 0.4:
                reasons.append("Moderate risk indicators present")
            else:
                reasons.append("Low risk transaction")
        
        return "; ".join(reasons)
    
    def scan_recent_transactions(self, days: int = 7) -> List[Dict]:
        """Scan recent transactions for fraud"""
        try:
            # Get recent transactions
            transactions_df = self.db_manager.get_transactions(limit=1000)
            
            if transactions_df.empty:
                return []
            
            # Filter by date
            transactions_df['created_date'] = pd.to_datetime(transactions_df['created_date'])
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_transactions = transactions_df[transactions_df['created_date'] >= cutoff_date]
            
            results = []
            
            for _, txn in recent_transactions.iterrows():
                transaction_data = txn.to_dict()
                fraud_result = self.detect_fraud_single(transaction_data)
                results.append(fraud_result)
            
            return results
            
        except Exception as e:
            st.error(f"Error scanning recent transactions: {str(e)}")
            return []
    
    def train_model(self) -> Optional[Dict]:
        """Train fraud detection model using historical data"""
        try:
            # Get historical transaction data
            transactions_df = self.db_manager.get_transactions(limit=5000)
            
            if len(transactions_df) < 50:
                st.warning("Insufficient data for model training. Need at least 50 transactions.")
                return None
            
            # Prepare training data
            X, y = self._prepare_training_data(transactions_df)
            
            if X is None or len(X) == 0:
                st.error("Failed to prepare training data")
                return None
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            if np.sum(y_train) > 5:  # Enough positive samples for supervised learning
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
                self.model.fit(X_train_scaled, y_train)
                
                # Evaluate model
                y_pred = self.model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
            else:  # Use unsupervised learning
                self.model = IsolationForest(contamination=0.1, random_state=42)
                self.model.fit(X_train_scaled)
                
                # Evaluate with anomaly detection
                anomalies = self.model.predict(X_test_scaled)
                accuracy = np.mean(anomalies == -1) * 100  # Anomaly rate
            
            # Save models
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            joblib.dump(self.encoders, self.encoders_path)
            
            st.session_state.model_loaded = True
            
            return {
                'accuracy': accuracy,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'model_type': type(self.model).__name__,
                'trained_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            st.error(f"Error training model: {str(e)}")
            return None
    
    def _prepare_training_data(self, transactions_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from historical transactions"""
        try:
            features_list = []
            labels_list = []
            
            # Initialize encoders for categorical variables
            categorical_features = ['currency', 'country', 'transaction_type']
            for feature in categorical_features:
                if feature in transactions_df.columns:
                    unique_values = transactions_df[feature].unique()
                    encoder = LabelEncoder()
                    encoder.fit(unique_values)
                    self.encoders[feature] = encoder
            
            for _, txn in transactions_df.iterrows():
                try:
                    # Extract numerical features
                    features = [
                        float(txn.get('amount', 0)),
                        len(str(txn.get('description', ''))),
                        float(txn.get('inr_amount', 0)),
                    ]
                    
                    # Time-based features
                    try:
                        timestamp = pd.to_datetime(txn['created_date'])
                        features.extend([
                            timestamp.hour,
                            timestamp.weekday(),
                            timestamp.day
                        ])
                    except:
                        features.extend([12, 1, 15])  # Default values
                    
                    # Categorical features
                    for feature in categorical_features:
                        if feature in self.encoders:
                            try:
                                value = str(txn.get(feature, 'unknown'))
                                encoded_value = self.encoders[feature].transform([value])[0]
                            except:
                                encoded_value = 0
                        else:
                            encoded_value = 0
                        features.append(encoded_value)
                    
                    # Label (fraud indicator)
                    # Use is_spam column if available, otherwise use heuristics
                    if 'is_spam' in txn and pd.notna(txn['is_spam']):
                        label = int(txn['is_spam'])
                    else:
                        # Use heuristic: rejected transactions or very high/low amounts
                        amount = float(txn.get('amount', 0))
                        status = str(txn.get('status', ''))
                        
                        if status == 'rejected':
                            label = 1
                        elif amount > 50000000 or amount < 10:  # Very high or very low amounts
                            label = 1
                        else:
                            label = 0
                    
                    features_list.append(features)
                    labels_list.append(label)
                    
                except Exception as e:
                    continue  # Skip problematic rows
            
            if features_list:
                X = np.array(features_list)
                y = np.array(labels_list)
                return X, y
            else:
                return None, None
                
        except Exception as e:
            st.error(f"Error preparing training data: {str(e)}")
            return None, None
    
    def get_model_info(self) -> Optional[Dict]:
        """Get information about the current model"""
        try:
            if not st.session_state.get('model_loaded', False):
                return None
            
            model_info = {
                'type': type(self.model).__name__ if self.model else 'Not loaded',
                'last_trained': 'Unknown',
                'samples': 'Unknown'
            }
            
            # Try to get model file info
            if os.path.exists(self.model_path):
                stat = os.stat(self.model_path)
                model_info['last_trained'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            return model_info
            
        except Exception as e:
            st.error(f"Error getting model info: {str(e)}")
            return None
    
    def get_detection_history(self) -> pd.DataFrame:
        """Get fraud detection history"""
        try:
            return self.db_manager.get_fraud_detections(limit=500)
        except Exception as e:
            st.error(f"Error getting detection history: {str(e)}")
            return pd.DataFrame()
    
    def update_thresholds(self, new_thresholds: Dict):
        """Update fraud detection thresholds"""
        try:
            self.thresholds.update(new_thresholds)
            
            # Save to session state
            st.session_state.fraud_thresholds = self.thresholds
            
        except Exception as e:
            st.error(f"Error updating thresholds: {str(e)}")
    
    def export_model(self) -> Optional[str]:
        """Export trained model as base64 string"""
        try:
            if not self.model:
                return None
            
            import pickle
            import base64
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'encoders': self.encoders,
                'thresholds': self.thresholds,
                'exported_at': datetime.now().isoformat()
            }
            
            pickled_data = pickle.dumps(model_data)
            encoded_data = base64.b64encode(pickled_data).decode()
            
            return encoded_data
            
        except Exception as e:
            st.error(f"Error exporting model: {str(e)}")
            return None
    
    def import_model(self, encoded_model: str) -> bool:
        """Import model from base64 string"""
        try:
            import pickle
            import base64
            
            decoded_data = base64.b64decode(encoded_model.encode())
            model_data = pickle.loads(decoded_data)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.encoders = model_data['encoders']
            self.thresholds = model_data.get('thresholds', self.thresholds)
            
            # Save imported models
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            joblib.dump(self.encoders, self.encoders_path)
            
            st.session_state.model_loaded = True
            
            return True
            
        except Exception as e:
            st.error(f"Error importing model: {str(e)}")
            return False
    
    def get_fraud_statistics(self) -> Dict:
        """Get fraud detection statistics"""
        try:
            detections_df = self.get_detection_history()
            
            if detections_df.empty:
                return {
                    'total_detections': 0,
                    'fraud_count': 0,
                    'fraud_rate': 0,
                    'avg_risk_score': 0
                }
            
            stats = {
                'total_detections': len(detections_df),
                'fraud_count': len(detections_df[detections_df['is_fraud'] == 1]),
                'fraud_rate': len(detections_df[detections_df['is_fraud'] == 1]) / len(detections_df) * 100,
                'avg_risk_score': detections_df['risk_score'].mean(),
                'high_risk_count': len(detections_df[detections_df['risk_score'] > self.thresholds['high_risk']]),
                'risk_distribution': {
                    'low': len(detections_df[detections_df['risk_score'] < self.thresholds['low_risk']]),
                    'medium': len(detections_df[(detections_df['risk_score'] >= self.thresholds['low_risk']) & 
                                               (detections_df['risk_score'] < self.thresholds['medium_risk'])]),
                    'high': len(detections_df[(detections_df['risk_score'] >= self.thresholds['medium_risk']) & 
                                             (detections_df['risk_score'] < self.thresholds['high_risk'])]),
                    'critical': len(detections_df[detections_df['risk_score'] >= self.thresholds['high_risk']])
                }
            }
            
            return stats
            
        except Exception as e:
            st.error(f"Error getting fraud statistics: {str(e)}")
            return {}
