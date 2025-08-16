import numpy as np
import pandas as pd
import hashlib
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

from utils.encryption import encrypt_data, decrypt_data, create_pseudonym, hash_data
from config import Config

class PrivacyManager:
    """Comprehensive privacy management system"""
    
    def __init__(self):
        self.config = Config()
        self.safe_data_vault = SafeDataVault()
        self.utility_balancer = PrivacyUtilityBalancer()
        self.risk_analyzer = ReidentificationRiskAnalyzer()
        
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data using SafeDataVault"""
        return self.safe_data_vault.encrypt_field(data)
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.safe_data_vault.decrypt_field(encrypted_data)
    
    def pseudonymize_trader(self, trader_info: str) -> str:
        """Create pseudonym for trader information"""
        return self.safe_data_vault.pseudonymize_identity(trader_info)
    
    def get_privacy_budget_status(self) -> Dict[str, Any]:
        """Get current privacy budget status"""
        return self.utility_balancer.get_budget_status()
    
    def analyze_reidentification_risk(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze re-identification risk for transaction data"""
        return self.risk_analyzer.analyze_risk(transactions)
    
    def test_encryption_performance(self) -> Dict[str, float]:
        """Test encryption/decryption performance"""
        return self.safe_data_vault.performance_test()

class SafeDataVault:
    """Secure data vault for encryption and pseudonymization"""
    
    def __init__(self):
        self.encryption_stats = {
            'operations_count': 0,
            'total_time': 0.0,
            'last_operation': None
        }
    
    def encrypt_field(self, field_value: str) -> str:
        """Encrypt a data field"""
        start_time = datetime.now()
        
        try:
            encryption_key = st.session_state.get('encryption_key')
            if not encryption_key:
                return field_value
            
            encrypted = encrypt_data(field_value, encryption_key)
            
            # Update stats
            duration = (datetime.now() - start_time).total_seconds()
            self.encryption_stats['operations_count'] += 1
            self.encryption_stats['total_time'] += duration
            self.encryption_stats['last_operation'] = datetime.now()
            
            return encrypted or field_value
            
        except Exception as e:
            st.error(f"Encryption failed: {str(e)}")
            return field_value
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a data field"""
        start_time = datetime.now()
        
        try:
            encryption_key = st.session_state.get('encryption_key')
            if not encryption_key:
                return encrypted_value
            
            decrypted = decrypt_data(encrypted_value, encryption_key)
            
            # Update stats
            duration = (datetime.now() - start_time).total_seconds()
            self.encryption_stats['operations_count'] += 1
            self.encryption_stats['total_time'] += duration
            self.encryption_stats['last_operation'] = datetime.now()
            
            return decrypted
            
        except Exception as e:
            return f"Decryption failed: {str(e)}"
    
    def pseudonymize_identity(self, identity: str) -> str:
        """Create pseudonym for identity information"""
        try:
            # Generate consistent pseudonym
            pseudonym = create_pseudonym(identity)
            
            # Store mapping in session state for potential reversal
            if 'pseudonym_mapping' not in st.session_state:
                st.session_state.pseudonym_mapping = {}
            
            st.session_state.pseudonym_mapping[pseudonym] = identity
            
            return pseudonym
            
        except Exception as e:
            st.error(f"Pseudonymization failed: {str(e)}")
            return f"PSEUDO_{hash_data(identity)[:8]}"
    
    def mask_sensitive_fields(self, data: Dict[str, Any], 
                            sensitive_fields: List[str]) -> Dict[str, Any]:
        """Apply masking to sensitive fields"""
        masked_data = data.copy()
        
        for field in sensitive_fields:
            if field in masked_data:
                original_value = str(masked_data[field])
                
                if field.lower() in ['account', 'id', 'reference']:
                    # Mask account numbers/IDs
                    if len(original_value) > 4:
                        masked_data[field] = f"****{original_value[-4:]}"
                    else:
                        masked_data[field] = "****"
                
                elif field.lower() in ['name', 'counterparty']:
                    # Mask names
                    if len(original_value) > 2:
                        masked_data[field] = f"{original_value[0]}***{original_value[-1]}"
                    else:
                        masked_data[field] = "***"
                
                elif field.lower() in ['amount']:
                    # Mask amounts (show range)
                    try:
                        amount = float(original_value)
                        if amount < 10000:
                            masked_data[field] = "< ₹10,000"
                        elif amount < 100000:
                            masked_data[field] = "₹10,000 - ₹1,00,000"
                        elif amount < 1000000:
                            masked_data[field] = "₹1,00,000 - ₹10,00,000"
                        else:
                            masked_data[field] = "> ₹10,00,000"
                    except:
                        masked_data[field] = "***"
                
                else:
                    # Generic masking
                    masked_data[field] = "***"
        
        return masked_data
    
    def apply_k_anonymity(self, df: pd.DataFrame, k: int = 5, 
                         quasi_identifiers: List[str] = None) -> pd.DataFrame:
        """Apply k-anonymity to dataset"""
        if quasi_identifiers is None:
            quasi_identifiers = ['corridor', 'currency', 'source']
        
        # Group by quasi-identifiers
        groups = df.groupby(quasi_identifiers)
        
        # Remove groups with less than k records
        filtered_groups = []
        for name, group in groups:
            if len(group) >= k:
                filtered_groups.append(group)
        
        if filtered_groups:
            return pd.concat(filtered_groups, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def apply_l_diversity(self, df: pd.DataFrame, l: int = 3, 
                         sensitive_attribute: str = 'amount') -> pd.DataFrame:
        """Apply l-diversity to dataset"""
        if sensitive_attribute not in df.columns:
            return df
        
        # Create bins for sensitive attribute
        df['sensitive_bin'] = pd.qcut(df[sensitive_attribute], q=l, duplicates='drop')
        
        # Group by quasi-identifiers
        quasi_identifiers = ['corridor', 'currency', 'source']
        
        filtered_groups = []
        for name, group in df.groupby(quasi_identifiers):
            # Check if group has at least l distinct values in sensitive attribute
            distinct_values = group['sensitive_bin'].nunique()
            if distinct_values >= l:
                filtered_groups.append(group)
        
        if filtered_groups:
            result_df = pd.concat(filtered_groups, ignore_index=True)
            return result_df.drop('sensitive_bin', axis=1)
        else:
            return pd.DataFrame()
    
    def performance_test(self) -> Dict[str, float]:
        """Test encryption/decryption performance"""
        import time
        
        # Test data sizes
        test_sizes = [100, 1000, 10000]  # characters
        results = {}
        
        encryption_key = st.session_state.get('encryption_key')
        if not encryption_key:
            return {'error': 'No encryption key available'}
        
        for size in test_sizes:
            test_data = 'A' * size
            
            # Encryption test
            start_time = time.time()
            encrypted = encrypt_data(test_data, encryption_key)
            encrypt_time = time.time() - start_time
            
            # Decryption test
            if encrypted:
                start_time = time.time()
                decrypted = decrypt_data(encrypted, encryption_key)
                decrypt_time = time.time() - start_time
            else:
                decrypt_time = 0
            
            results[f'encrypt_{size}'] = encrypt_time
            results[f'decrypt_{size}'] = decrypt_time
        
        # Calculate speeds (MB/s)
        avg_encrypt_time = np.mean([results[f'encrypt_{size}'] for size in test_sizes])
        avg_decrypt_time = np.mean([results[f'decrypt_{size}'] for size in test_sizes])
        
        avg_size_mb = np.mean([size / 1024 / 1024 for size in test_sizes])
        
        return {
            'encrypt_speed': avg_size_mb / avg_encrypt_time if avg_encrypt_time > 0 else 0,
            'decrypt_speed': avg_size_mb / avg_decrypt_time if avg_decrypt_time > 0 else 0,
            'avg_encrypt_time': avg_encrypt_time,
            'avg_decrypt_time': avg_decrypt_time
        }

class PrivacyUtilityBalancer:
    """Balance privacy preservation with data utility"""
    
    def __init__(self):
        self.privacy_budget = {
            'total': Config.PRIVACY_BUDGET_TOTAL,
            'used': 0.0,
            'operations': []
        }
    
    def consume_privacy_budget(self, operation: str, epsilon: float) -> bool:
        """Consume privacy budget for an operation"""
        if self.privacy_budget['used'] + epsilon > self.privacy_budget['total']:
            return False
        
        self.privacy_budget['used'] += epsilon
        self.privacy_budget['operations'].append({
            'operation': operation,
            'epsilon': epsilon,
            'timestamp': datetime.now()
        })
        
        return True
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current privacy budget status"""
        used = self.privacy_budget['used']
        total = self.privacy_budget['total']
        remaining = total - used
        
        return {
            'total': total,
            'used': used,
            'remaining': remaining,
            'used_percentage': (used / total * 100) if total > 0 else 0,
            'operations_count': len(self.privacy_budget['operations']),
            'warning_threshold': total * Config.PRIVACY_BUDGET_WARNING_THRESHOLD
        }
    
    def apply_differential_privacy(self, data: List[float], epsilon: float) -> List[float]:
        """Apply differential privacy noise to numerical data"""
        if not self.consume_privacy_budget('differential_privacy', epsilon):
            st.warning("Insufficient privacy budget for differential privacy")
            return data
        
        # Add Laplace noise
        sensitivity = 1.0  # Assuming unit sensitivity
        scale = sensitivity / epsilon
        
        noisy_data = []
        for value in data:
            noise = np.random.laplace(0, scale)
            noisy_data.append(value + noise)
        
        return noisy_data
    
    def generate_synthetic_data(self, transactions: List[Dict[str, Any]], 
                              count: int) -> List[Dict[str, Any]]:
        """Generate synthetic transaction data for testing"""
        if not transactions:
            return []
        
        df = pd.DataFrame(transactions)
        synthetic_transactions = []
        
        # Statistical parameters from real data
        amount_stats = {
            'mean': df['amount'].mean(),
            'std': df['amount'].std(),
            'min': df['amount'].min(),
            'max': df['amount'].max()
        }
        
        risk_stats = {
            'mean': df['risk_score'].mean(),
            'std': df['risk_score'].std()
        }
        
        # Value distributions
        source_dist = df['source'].value_counts(normalize=True).to_dict()
        currency_dist = df['currency'].value_counts(normalize=True).to_dict()
        corridor_dist = df['corridor'].value_counts(normalize=True).to_dict()
        status_dist = df['status'].value_counts(normalize=True).to_dict()
        
        for i in range(count):
            # Generate synthetic transaction
            synthetic_txn = {
                'id': f"SYNTH_{uuid.uuid4().hex[:8].upper()}",
                'timestamp': datetime.now() - timedelta(
                    seconds=random.randint(0, 86400 * 30)  # Last 30 days
                ),
                'amount': max(0, np.random.normal(
                    amount_stats['mean'], 
                    amount_stats['std']
                )),
                'risk_score': max(0, min(100, np.random.normal(
                    risk_stats['mean'], 
                    risk_stats['std']
                ))),
                'source': np.random.choice(
                    list(source_dist.keys()), 
                    p=list(source_dist.values())
                ),
                'currency': np.random.choice(
                    list(currency_dist.keys()), 
                    p=list(currency_dist.values())
                ),
                'corridor': np.random.choice(
                    list(corridor_dist.keys()), 
                    p=list(corridor_dist.values())
                ),
                'status': np.random.choice(
                    list(status_dist.keys()), 
                    p=list(status_dist.values())
                ),
                'processing_time': np.random.uniform(0.1, 5.0),
                'counterparty': f"SYNTH_Entity_{random.randint(1000, 9999)}",
                'synthetic': True
            }
            
            synthetic_transactions.append(synthetic_txn)
        
        return synthetic_transactions
    
    def calculate_data_utility(self, original_data: List[Dict[str, Any]], 
                             processed_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate utility metrics for processed data"""
        if not original_data or not processed_data:
            return {'utility_score': 0.0}
        
        orig_df = pd.DataFrame(original_data)
        proc_df = pd.DataFrame(processed_data)
        
        utility_metrics = {}
        
        # Statistical utility
        for column in ['amount', 'risk_score']:
            if column in orig_df.columns and column in proc_df.columns:
                orig_mean = orig_df[column].mean()
                proc_mean = proc_df[column].mean()
                
                orig_std = orig_df[column].std()
                proc_std = proc_df[column].std()
                
                # Mean preservation
                mean_error = abs(orig_mean - proc_mean) / orig_mean if orig_mean != 0 else 0
                
                # Std preservation
                std_error = abs(orig_std - proc_std) / orig_std if orig_std != 0 else 0
                
                utility_metrics[f'{column}_mean_utility'] = 1 - mean_error
                utility_metrics[f'{column}_std_utility'] = 1 - std_error
        
        # Distribution utility
        for column in ['source', 'currency', 'corridor']:
            if column in orig_df.columns and column in proc_df.columns:
                orig_dist = orig_df[column].value_counts(normalize=True)
                proc_dist = proc_df[column].value_counts(normalize=True)
                
                # Calculate KL divergence approximation
                kl_div = 0
                for value in orig_dist.index:
                    if value in proc_dist.index:
                        p = orig_dist[value]
                        q = proc_dist[value]
                        if q > 0:
                            kl_div += p * np.log(p / q)
                
                utility_metrics[f'{column}_dist_utility'] = 1 / (1 + kl_div)
        
        # Overall utility score
        if utility_metrics:
            utility_metrics['utility_score'] = np.mean(list(utility_metrics.values()))
        else:
            utility_metrics['utility_score'] = 0.0
        
        return utility_metrics

class ReidentificationRiskAnalyzer:
    """Analyze re-identification risks in data"""
    
    def __init__(self):
        self.risk_thresholds = {
            'low': 0.33,
            'medium': 0.66,
            'high': 1.0
        }
    
    def analyze_risk(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive re-identification risk analysis"""
        if not transactions:
            return {
                'overall_risk': 0.0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'risk_factors': []
            }
        
        df = pd.DataFrame(transactions)
        
        # Calculate various risk factors
        risk_factors = []
        
        # Uniqueness risk
        uniqueness_risk = self._calculate_uniqueness_risk(df)
        risk_factors.append(('uniqueness', uniqueness_risk))
        
        # Linkability risk
        linkability_risk = self._calculate_linkability_risk(df)
        risk_factors.append(('linkability', linkability_risk))
        
        # Inference risk
        inference_risk = self._calculate_inference_risk(df)
        risk_factors.append(('inference', inference_risk))
        
        # Temporal correlation risk
        temporal_risk = self._calculate_temporal_risk(df)
        risk_factors.append(('temporal', temporal_risk))
        
        # Calculate per-transaction risk scores
        transaction_risks = []
        for _, transaction in df.iterrows():
            txn_risk = self._calculate_transaction_risk(transaction, df)
            transaction_risks.append(txn_risk)
        
        # Categorize risks
        high_risk_count = sum(1 for risk in transaction_risks if risk > self.risk_thresholds['medium'])
        medium_risk_count = sum(1 for risk in transaction_risks 
                               if self.risk_thresholds['low'] < risk <= self.risk_thresholds['medium'])
        low_risk_count = sum(1 for risk in transaction_risks if risk <= self.risk_thresholds['low'])
        
        # Overall risk score
        overall_risk = np.mean(transaction_risks) if transaction_risks else 0.0
        
        return {
            'overall_risk': overall_risk,
            'high_risk_count': high_risk_count,
            'medium_risk_count': medium_risk_count,
            'low_risk_count': low_risk_count,
            'risk_factors': risk_factors,
            'transaction_risks': transaction_risks
        }
    
    def _calculate_uniqueness_risk(self, df: pd.DataFrame) -> float:
        """Calculate risk based on unique attribute combinations"""
        if len(df) == 0:
            return 0.0
        
        # Check combinations of quasi-identifiers
        quasi_identifiers = ['corridor', 'currency', 'source']
        
        # Available quasi-identifiers in the data
        available_qi = [qi for qi in quasi_identifiers if qi in df.columns]
        
        if not available_qi:
            return 0.0
        
        # Calculate uniqueness for different combinations
        uniqueness_scores = []
        
        for i in range(1, len(available_qi) + 1):
            from itertools import combinations
            for combo in combinations(available_qi, i):
                combo_groups = df.groupby(list(combo)).size()
                unique_records = (combo_groups == 1).sum()
                uniqueness_ratio = unique_records / len(df)
                uniqueness_scores.append(uniqueness_ratio)
        
        return max(uniqueness_scores) if uniqueness_scores else 0.0
    
    def _calculate_linkability_risk(self, df: pd.DataFrame) -> float:
        """Calculate risk of linking records"""
        if len(df) < 2:
            return 0.0
        
        # Check for potential linking attributes
        linking_attributes = ['counterparty', 'reference', 'amount']
        
        linkability_scores = []
        
        for attr in linking_attributes:
            if attr in df.columns:
                if attr == 'amount':
                    # For amounts, check for exact matches
                    amount_counts = df[attr].value_counts()
                    repeated_amounts = (amount_counts > 1).sum()
                    linkability_scores.append(repeated_amounts / len(df))
                else:
                    # For categorical attributes
                    value_counts = df[attr].value_counts()
                    repeated_values = (value_counts > 1).sum()
                    linkability_scores.append(repeated_values / len(df))
        
        return max(linkability_scores) if linkability_scores else 0.0
    
    def _calculate_inference_risk(self, df: pd.DataFrame) -> float:
        """Calculate risk of inferring sensitive information"""
        if len(df) == 0:
            return 0.0
        
        # Check correlation between non-sensitive and sensitive attributes
        inference_risk = 0.0
        
        if 'amount' in df.columns and 'corridor' in df.columns:
            # Check if amount can be inferred from corridor
            corridor_amounts = df.groupby('corridor')['amount'].std()
            low_variance_corridors = (corridor_amounts < corridor_amounts.mean()).sum()
            inference_risk = max(inference_risk, low_variance_corridors / len(corridor_amounts))
        
        if 'risk_score' in df.columns and 'source' in df.columns:
            # Check if risk can be inferred from source
            source_risk = df.groupby('source')['risk_score'].std()
            low_variance_sources = (source_risk < source_risk.mean()).sum()
            inference_risk = max(inference_risk, low_variance_sources / len(source_risk))
        
        return inference_risk
    
    def _calculate_temporal_risk(self, df: pd.DataFrame) -> float:
        """Calculate temporal correlation risk"""
        if 'timestamp' not in df.columns or len(df) < 2:
            return 0.0
        
        # Convert timestamps and sort
        df_temp = df.copy()
        df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])
        df_temp = df_temp.sort_values('timestamp')
        
        # Check for temporal patterns
        temporal_risk = 0.0
        
        # Time clustering risk
        time_diffs = df_temp['timestamp'].diff().dt.total_seconds()
        short_intervals = (time_diffs < 300).sum()  # Less than 5 minutes
        temporal_risk = short_intervals / len(df_temp)
        
        return temporal_risk
    
    def _calculate_transaction_risk(self, transaction: pd.Series, full_df: pd.DataFrame) -> float:
        """Calculate re-identification risk for a single transaction"""
        risk_score = 0.0
        
        # Rarity risk - how rare are the attribute values
        for attr in ['corridor', 'currency', 'source']:
            if attr in transaction.index and attr in full_df.columns:
                value_frequency = (full_df[attr] == transaction[attr]).sum() / len(full_df)
                rarity_risk = 1 - value_frequency
                risk_score += rarity_risk * 0.2  # Weight: 20%
        
        # Amount risk - unusual amounts are riskier
        if 'amount' in transaction.index and 'amount' in full_df.columns:
            amount_percentile = (full_df['amount'] < transaction['amount']).mean()
            # Risk is higher at extremes
            amount_risk = 2 * abs(amount_percentile - 0.5)
            risk_score += amount_risk * 0.3  # Weight: 30%
        
        # Risk score risk - high risk scores are more identifiable
        if 'risk_score' in transaction.index:
            risk_percentile = transaction['risk_score'] / 100
            risk_score += risk_percentile * 0.3  # Weight: 30%
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def suggest_privacy_enhancements(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """Suggest privacy enhancement measures based on risk analysis"""
        suggestions = []
        
        overall_risk = risk_analysis.get('overall_risk', 0)
        high_risk_count = risk_analysis.get('high_risk_count', 0)
        
        if overall_risk > 0.7:
            suggestions.append("🚨 High overall risk detected - Consider applying k-anonymity with k≥5")
            suggestions.append("🔒 Implement stronger pseudonymization for identifiers")
        
        if high_risk_count > 0:
            suggestions.append(f"⚠️ {high_risk_count} high-risk transactions - Consider suppression or generalization")
        
        # Check specific risk factors
        risk_factors = risk_analysis.get('risk_factors', [])
        for factor_name, factor_risk in risk_factors:
            if factor_risk > 0.6:
                if factor_name == 'uniqueness':
                    suggestions.append("🔢 High uniqueness risk - Apply generalization to quasi-identifiers")
                elif factor_name == 'linkability':
                    suggestions.append("🔗 High linkability risk - Consider adding noise to linking attributes")
                elif factor_name == 'inference':
                    suggestions.append("🧠 High inference risk - Apply differential privacy or attribute suppression")
                elif factor_name == 'temporal':
                    suggestions.append("⏰ High temporal risk - Consider time bucketing or temporal noise")
        
        if not suggestions:
            suggestions.append("✅ Privacy risk levels are acceptable")
        
        return suggestions
