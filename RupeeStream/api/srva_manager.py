import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from utils.db_manager import DatabaseManager
from utils.encryption import encrypt_data, decrypt_data
from config import Config
import streamlit as st

class SRVAManager:
    """Manages SRVA (Special Rupee Vostro Account) lifecycle operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.config = Config()
        
    def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new SRVA account"""
        try:
            # Generate unique account ID
            account_id = str(uuid.uuid4())[:12].upper()
            
            # Get partner country configuration
            country_config = self.config.get_partner_country_config(account_data['partner_country'])
            
            # Validate trade limit against country limits
            if account_data['trade_limit'] > country_config.get('trade_limit', float('inf')):
                return {
                    'success': False,
                    'message': f"Trade limit exceeds maximum for {account_data['partner_country']}"
                }
            
            # Encrypt sensitive information
            encryption_key = st.session_state.get('encryption_key')
            if encryption_key:
                encrypted_bank_name = encrypt_data(account_data['bank_name'], encryption_key)
                encrypted_name = encrypt_data(account_data['name'], encryption_key)
            else:
                encrypted_bank_name = account_data['bank_name']
                encrypted_name = account_data['name']
            
            # Prepare account record
            account_record = {
                'account_id': account_id,
                'name': encrypted_name,
                'partner_country': account_data['partner_country'],
                'bank_name': encrypted_bank_name,
                'currency': account_data['currency'],
                'trade_limit': account_data['trade_limit'],
                'compliance_status': account_data['compliance_status'],
                'corridor': country_config.get('corridor', 'IN-XX'),
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'balance': 0.0,
                'frozen_amount': 0.0,
                'compliance_flags': ','.join(country_config.get('compliance_flags', []))
            }
            
            # Insert into database
            success = self.db.insert_srva_account(account_record)
            
            if success:
                # Log the account creation
                self._log_account_action(account_id, 'CREATED', f"Account created for {account_data['partner_country']}")
                
                return {
                    'success': True,
                    'account_id': account_id,
                    'message': 'Account created successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Database insertion failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Account creation failed: {str(e)}'
            }
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Retrieve all SRVA accounts"""
        try:
            accounts = self.db.get_all_srva_accounts()
            
            # Decrypt sensitive fields for display
            encryption_key = st.session_state.get('encryption_key')
            if encryption_key and accounts:
                for account in accounts:
                    if account.get('name'):
                        account['name'] = decrypt_data(account['name'], encryption_key)
                    if account.get('bank_name'):
                        account['bank_name'] = decrypt_data(account['bank_name'], encryption_key)
            
            return accounts
            
        except Exception as e:
            st.error(f"Failed to retrieve accounts: {str(e)}")
            return []
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get specific SRVA account by ID"""
        try:
            account = self.db.get_srva_account(account_id)
            
            if account:
                # Decrypt sensitive fields
                encryption_key = st.session_state.get('encryption_key')
                if encryption_key:
                    account['name'] = decrypt_data(account['name'], encryption_key)
                    account['bank_name'] = decrypt_data(account['bank_name'], encryption_key)
            
            return account
            
        except Exception as e:
            st.error(f"Failed to retrieve account: {str(e)}")
            return None
    
    def update_account_balance(self, account_id: str, amount: float, operation: str = 'credit') -> Dict[str, Any]:
        """Update account balance for settlements"""
        try:
            account = self.get_account_by_id(account_id)
            if not account:
                return {'success': False, 'message': 'Account not found'}
            
            current_balance = account.get('balance', 0.0)
            
            if operation == 'credit':
                new_balance = current_balance + amount
            elif operation == 'debit':
                if current_balance < amount:
                    return {'success': False, 'message': 'Insufficient balance'}
                new_balance = current_balance - amount
            else:
                return {'success': False, 'message': 'Invalid operation'}
            
            # Update in database
            success = self.db.update_account_balance(account_id, new_balance)
            
            if success:
                self._log_account_action(account_id, f'BALANCE_{operation.upper()}', 
                                       f"{operation.title()} of {amount} {account['currency']}")
                return {
                    'success': True,
                    'new_balance': new_balance,
                    'message': f'Balance updated successfully'
                }
            else:
                return {'success': False, 'message': 'Database update failed'}
                
        except Exception as e:
            return {'success': False, 'message': f'Balance update failed: {str(e)}'}
    
    def compute_settlement(self, transactions: List[Dict[str, Any]], 
                          settlement_date: datetime = None) -> Dict[str, Any]:
        """Compute settlement for a batch of transactions"""
        try:
            if not transactions:
                return {'success': False, 'message': 'No transactions provided'}
            
            if not settlement_date:
                settlement_date = datetime.now()
            
            # Group transactions by corridor and currency
            settlement_groups = {}
            total_settlement_amount = 0
            
            for transaction in transactions:
                corridor = transaction.get('corridor', 'Unknown')
                currency = transaction.get('currency', 'INR')
                amount = transaction.get('amount', 0)
                
                key = f"{corridor}_{currency}"
                
                if key not in settlement_groups:
                    settlement_groups[key] = {
                        'corridor': corridor,
                        'currency': currency,
                        'total_amount': 0,
                        'transaction_count': 0,
                        'transactions': []
                    }
                
                settlement_groups[key]['total_amount'] += amount
                settlement_groups[key]['transaction_count'] += 1
                settlement_groups[key]['transactions'].append(transaction['id'])
                total_settlement_amount += amount
            
            # Create settlement record
            settlement_id = str(uuid.uuid4())[:12].upper()
            settlement_record = {
                'settlement_id': settlement_id,
                'settlement_date': settlement_date,
                'total_amount': total_settlement_amount,
                'currency_groups': settlement_groups,
                'status': 'PENDING',
                'created_at': datetime.now(),
                'transaction_ids': [t['id'] for t in transactions]
            }
            
            # Store settlement in database
            success = self.db.insert_settlement(settlement_record)
            
            if success:
                return {
                    'success': True,
                    'settlement_id': settlement_id,
                    'total_amount': total_settlement_amount,
                    'groups': settlement_groups,
                    'message': 'Settlement computed successfully'
                }
            else:
                return {'success': False, 'message': 'Settlement storage failed'}
                
        except Exception as e:
            return {'success': False, 'message': f'Settlement computation failed: {str(e)}'}
    
    def get_pending_settlements(self) -> List[Dict[str, Any]]:
        """Get all pending settlements"""
        try:
            return self.db.get_settlements_by_status('PENDING')
        except Exception as e:
            st.error(f"Failed to retrieve settlements: {str(e)}")
            return []
    
    def process_settlement(self, settlement_id: str) -> Dict[str, Any]:
        """Process a pending settlement"""
        try:
            settlement = self.db.get_settlement(settlement_id)
            if not settlement:
                return {'success': False, 'message': 'Settlement not found'}
            
            if settlement['status'] != 'PENDING':
                return {'success': False, 'message': 'Settlement already processed'}
            
            # Simulate settlement processing
            # In a real system, this would involve actual bank transfers
            processing_result = self._simulate_settlement_processing(settlement)
            
            if processing_result['success']:
                # Update settlement status
                self.db.update_settlement_status(settlement_id, 'COMPLETED')
                
                # Update related account balances
                for group in settlement['currency_groups'].values():
                    # Find corresponding SRVA account
                    accounts = self.get_accounts_by_corridor(group['corridor'])
                    if accounts:
                        account = accounts[0]  # Use first matching account
                        self.update_account_balance(account['account_id'], 
                                                  group['total_amount'], 'credit')
                
                self._log_settlement_action(settlement_id, 'PROCESSED', 
                                          f"Settlement of {settlement['total_amount']} processed")
                
                return {
                    'success': True,
                    'message': 'Settlement processed successfully'
                }
            else:
                # Update settlement status to failed
                self.db.update_settlement_status(settlement_id, 'FAILED')
                return processing_result
                
        except Exception as e:
            return {'success': False, 'message': f'Settlement processing failed: {str(e)}'}
    
    def get_accounts_by_corridor(self, corridor: str) -> List[Dict[str, Any]]:
        """Get accounts by trading corridor"""
        try:
            return self.db.get_accounts_by_corridor(corridor)
        except Exception as e:
            st.error(f"Failed to retrieve accounts by corridor: {str(e)}")
            return []
    
    def _simulate_settlement_processing(self, settlement: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate settlement processing (placeholder for real bank integration)"""
        import random
        import time
        
        # Simulate processing time
        time.sleep(random.uniform(0.5, 2.0))
        
        # Simulate success/failure (95% success rate)
        if random.random() < 0.95:
            return {
                'success': True,
                'processing_time': random.uniform(1, 5),
                'bank_reference': f"BNK{random.randint(100000, 999999)}"
            }
        else:
            return {
                'success': False,
                'message': 'Bank processing failed - insufficient liquidity'
            }
    
    def _log_account_action(self, account_id: str, action: str, details: str):
        """Log account-related actions for audit trail"""
        log_entry = {
            'timestamp': datetime.now(),
            'entity_type': 'SRVA_ACCOUNT',
            'entity_id': account_id,
            'action': action,
            'details': details,
            'user_role': st.session_state.get('user_role', 'system')
        }
        self.db.insert_audit_log(log_entry)
    
    def _log_settlement_action(self, settlement_id: str, action: str, details: str):
        """Log settlement-related actions for audit trail"""
        log_entry = {
            'timestamp': datetime.now(),
            'entity_type': 'SETTLEMENT',
            'entity_id': settlement_id,
            'action': action,
            'details': details,
            'user_role': st.session_state.get('user_role', 'system')
        }
        self.db.insert_audit_log(log_entry)
    
    def get_account_statistics(self) -> Dict[str, Any]:
        """Get SRVA account statistics"""
        try:
            accounts = self.get_all_accounts()
            
            if not accounts:
                return {
                    'total_accounts': 0,
                    'total_balance': 0,
                    'by_country': {},
                    'by_currency': {},
                    'compliance_status': {}
                }
            
            df = pd.DataFrame(accounts)
            
            stats = {
                'total_accounts': len(accounts),
                'total_balance': df['balance'].sum(),
                'by_country': df['partner_country'].value_counts().to_dict(),
                'by_currency': df['currency'].value_counts().to_dict(),
                'compliance_status': df['compliance_status'].value_counts().to_dict(),
                'avg_trade_limit': df['trade_limit'].mean(),
                'max_trade_limit': df['trade_limit'].max(),
                'min_trade_limit': df['trade_limit'].min()
            }
            
            return stats
            
        except Exception as e:
            st.error(f"Failed to calculate statistics: {str(e)}")
            return {}
