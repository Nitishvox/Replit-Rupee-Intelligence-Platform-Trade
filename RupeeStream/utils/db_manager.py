import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st
from config import Config

class DatabaseManager:
    """Database manager supporting both SQLite (local) and MySQL (production)"""
    
    def __init__(self):
        self.config = Config()
        self.connection = None
        self.db_type = 'sqlite' if self.config.USE_SQLITE else 'mysql'
        
    def get_connection(self):
        """Get database connection"""
        try:
            if self.db_type == 'sqlite':
                self.connection = sqlite3.connect(self.config.SQLITE_DB_PATH, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row  # Enable column access by name
            else:
                # MySQL connection would be implemented here
                # For demo purposes, falling back to SQLite
                self.connection = sqlite3.connect(self.config.SQLITE_DB_PATH, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row
            
            return self.connection
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            return None
    
    def initialize_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Create tables
            self._create_srva_accounts_table(cursor)
            self._create_transactions_table(cursor)
            self._create_settlements_table(cursor)
            self._create_exchange_rates_table(cursor)
            self._create_audit_logs_table(cursor)
            self._create_partner_countries_table(cursor)
            self._create_privacy_logs_table(cursor)
            self._create_fraud_flags_table(cursor)
            self._create_system_status_table(cursor)
            
            # Initialize partner countries data
            self._initialize_partner_countries(cursor)
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Database initialization failed: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def _create_srva_accounts_table(self, cursor):
        """Create SRVA accounts table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS srva_accounts (
                account_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                partner_country TEXT NOT NULL,
                bank_name TEXT,
                currency TEXT NOT NULL,
                trade_limit REAL NOT NULL,
                compliance_status TEXT NOT NULL,
                corridor TEXT NOT NULL,
                balance REAL DEFAULT 0.0,
                frozen_amount REAL DEFAULT 0.0,
                compliance_flags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_transactions_table(self, cursor):
        """Create transactions table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                corridor TEXT NOT NULL,
                counterparty TEXT,
                narrative TEXT,
                encrypted_counterparty TEXT,
                encrypted_narrative TEXT,
                status TEXT NOT NULL,
                risk_score REAL,
                processing_time REAL,
                fees REAL,
                reference TEXT,
                nlp_entities TEXT,
                fraud_flags TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_settlements_table(self, cursor):
        """Create settlements table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settlements (
                settlement_id TEXT PRIMARY KEY,
                settlement_date TIMESTAMP NOT NULL,
                total_amount REAL NOT NULL,
                currency_groups TEXT,
                status TEXT NOT NULL,
                transaction_ids TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_exchange_rates_table(self, cursor):
        """Create exchange rates table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rates TEXT NOT NULL,
                source TEXT DEFAULT 'API'
            )
        ''')
    
    def _create_audit_logs_table(self, cursor):
        """Create audit logs table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                user_role TEXT,
                ip_address TEXT
            )
        ''')
    
    def _create_partner_countries_table(self, cursor):
        """Create partner countries table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partner_countries (
                country_name TEXT PRIMARY KEY,
                currency TEXT NOT NULL,
                trade_limit REAL NOT NULL,
                compliance_flags TEXT,
                corridor TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_privacy_logs_table(self, cursor):
        """Create privacy operations log table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS privacy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                operation_type TEXT NOT NULL,
                entity_id TEXT,
                privacy_budget_used REAL,
                details TEXT
            )
        ''')
    
    def _create_fraud_flags_table(self, cursor):
        """Create fraud flags table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fraud_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                flag_type TEXT NOT NULL,
                risk_score REAL NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
    
    def _create_system_status_table(self, cursor):
        """Create system status monitoring table"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                service_name TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                error_message TEXT,
                metrics TEXT
            )
        ''')
    
    def _initialize_partner_countries(self, cursor):
        """Initialize partner countries data"""
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM partner_countries")
        if cursor.fetchone()[0] > 0:
            return  # Data already exists
        
        countries_data = [
            ('Russia', 'RUB', 50000000, 'sanctions_check,kyc_enhanced', 'IN-RU'),
            ('Germany', 'EUR', 100000000, 'eu_regulations,aml_standard', 'IN-EU'),
            ('UK', 'GBP', 75000000, 'uk_regulations,brexit_compliance', 'IN-GB'),
            ('Singapore', 'SGD', 80000000, 'mas_regulations,asean_trade', 'IN-SG')
        ]
        
        cursor.executemany('''
            INSERT INTO partner_countries 
            (country_name, currency, trade_limit, compliance_flags, corridor)
            VALUES (?, ?, ?, ?, ?)
        ''', countries_data)
    
    # SRVA Account Operations
    def insert_srva_account(self, account_data: Dict[str, Any]) -> bool:
        """Insert new SRVA account"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO srva_accounts 
                (account_id, name, partner_country, bank_name, currency, trade_limit, 
                 compliance_status, corridor, balance, frozen_amount, compliance_flags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_data['account_id'],
                account_data['name'],
                account_data['partner_country'],
                account_data['bank_name'],
                account_data['currency'],
                account_data['trade_limit'],
                account_data['compliance_status'],
                account_data['corridor'],
                account_data['balance'],
                account_data['frozen_amount'],
                account_data['compliance_flags']
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Failed to insert SRVA account: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_all_srva_accounts(self) -> List[Dict[str, Any]]:
        """Get all SRVA accounts"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM srva_accounts ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            accounts = []
            for row in rows:
                account = dict(row)
                accounts.append(account)
            
            return accounts
            
        except Exception as e:
            st.error(f"Failed to retrieve SRVA accounts: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_srva_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get specific SRVA account"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM srva_accounts WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            st.error(f"Failed to retrieve SRVA account: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def update_account_balance(self, account_id: str, new_balance: float) -> bool:
        """Update account balance"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE srva_accounts 
                SET balance = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE account_id = ?
            ''', (new_balance, account_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            st.error(f"Failed to update account balance: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_accounts_by_corridor(self, corridor: str) -> List[Dict[str, Any]]:
        """Get accounts by trading corridor"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM srva_accounts WHERE corridor = ?", (corridor,))
            rows = cursor.fetchall()
            
            accounts = []
            for row in rows:
                accounts.append(dict(row))
            
            return accounts
            
        except Exception as e:
            st.error(f"Failed to retrieve accounts by corridor: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    # Transaction Operations
    def insert_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Insert transaction record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions 
                (id, source, amount, currency, corridor, counterparty, narrative,
                 encrypted_counterparty, encrypted_narrative, status, risk_score,
                 processing_time, fees, reference, nlp_entities, fraud_flags, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction_data['id'],
                transaction_data['source'],
                transaction_data['amount'],
                transaction_data['currency'],
                transaction_data['corridor'],
                transaction_data.get('counterparty'),
                transaction_data.get('narrative'),
                transaction_data.get('encrypted_counterparty'),
                transaction_data.get('encrypted_narrative'),
                transaction_data['status'],
                transaction_data.get('risk_score'),
                transaction_data.get('processing_time'),
                transaction_data.get('fees'),
                transaction_data.get('reference'),
                json.dumps(transaction_data.get('nlp_entities', {})),
                json.dumps(transaction_data.get('fraud_flags', [])),
                transaction_data.get('timestamp', datetime.now())
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Failed to insert transaction: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_transactions(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get transaction records"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            transactions = []
            for row in rows:
                transaction = dict(row)
                # Parse JSON fields
                transaction['nlp_entities'] = json.loads(transaction.get('nlp_entities', '{}'))
                transaction['fraud_flags'] = json.loads(transaction.get('fraud_flags', '[]'))
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            st.error(f"Failed to retrieve transactions: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    # Settlement Operations
    def insert_settlement(self, settlement_data: Dict[str, Any]) -> bool:
        """Insert settlement record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO settlements 
                (settlement_id, settlement_date, total_amount, currency_groups, 
                 status, transaction_ids)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                settlement_data['settlement_id'],
                settlement_data['settlement_date'],
                settlement_data['total_amount'],
                json.dumps(settlement_data['currency_groups']),
                settlement_data['status'],
                json.dumps(settlement_data['transaction_ids'])
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Failed to insert settlement: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_settlements_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get settlements by status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM settlements WHERE status = ? ORDER BY created_at DESC", (status,))
            rows = cursor.fetchall()
            
            settlements = []
            for row in rows:
                settlement = dict(row)
                settlement['currency_groups'] = json.loads(settlement.get('currency_groups', '{}'))
                settlement['transaction_ids'] = json.loads(settlement.get('transaction_ids', '[]'))
                settlements.append(settlement)
            
            return settlements
            
        except Exception as e:
            st.error(f"Failed to retrieve settlements: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_settlement(self, settlement_id: str) -> Optional[Dict[str, Any]]:
        """Get specific settlement"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM settlements WHERE settlement_id = ?", (settlement_id,))
            row = cursor.fetchone()
            
            if row:
                settlement = dict(row)
                settlement['currency_groups'] = json.loads(settlement.get('currency_groups', '{}'))
                settlement['transaction_ids'] = json.loads(settlement.get('transaction_ids', '[]'))
                return settlement
            
            return None
            
        except Exception as e:
            st.error(f"Failed to retrieve settlement: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def update_settlement_status(self, settlement_id: str, status: str) -> bool:
        """Update settlement status"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE settlements 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE settlement_id = ?
            ''', (status, settlement_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            st.error(f"Failed to update settlement status: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    # Exchange Rate Operations
    def insert_exchange_rates(self, rate_data: Dict[str, Any]) -> bool:
        """Insert exchange rate data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO exchange_rates (timestamp, rates, source)
                VALUES (?, ?, ?)
            ''', (
                rate_data['timestamp'],
                rate_data['rates'],
                rate_data['source']
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Failed to insert exchange rates: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_latest_exchange_rates(self) -> Optional[Dict[str, Any]]:
        """Get latest exchange rates"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM exchange_rates ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            st.error(f"Failed to retrieve exchange rates: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_historical_exchange_rates(self, days: int) -> List[Dict[str, Any]]:
        """Get historical exchange rates"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            cursor.execute('''
                SELECT * FROM exchange_rates 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
            ''', (cutoff_date,))
            
            rows = cursor.fetchall()
            
            rates = []
            for row in rows:
                rate_record = dict(row)
                rates.append(rate_record)
            
            return rates
            
        except Exception as e:
            st.error(f"Failed to retrieve historical exchange rates: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    # Audit Log Operations
    def insert_audit_log(self, log_data: Dict[str, Any]) -> bool:
        """Insert audit log entry"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_logs 
                (timestamp, entity_type, entity_id, action, details, user_role, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_data.get('timestamp', datetime.now()),
                log_data['entity_type'],
                log_data['entity_id'],
                log_data['action'],
                log_data.get('details'),
                log_data.get('user_role'),
                log_data.get('ip_address')
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Failed to insert audit log: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_audit_logs(self, limit: int = 1000, entity_type: str = None, 
                      hours_back: int = 24) -> List[Dict[str, Any]]:
        """Get audit logs"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            if entity_type:
                cursor.execute('''
                    SELECT * FROM audit_logs 
                    WHERE timestamp >= ? AND entity_type = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (cutoff_time, entity_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM audit_logs 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (cutoff_time, limit))
            
            rows = cursor.fetchall()
            
            logs = []
            for row in rows:
                logs.append(dict(row))
            
            return logs
            
        except Exception as e:
            st.error(f"Failed to retrieve audit logs: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    # System Status Operations
    def insert_system_status(self, status_data: Dict[str, Any]) -> bool:
        """Insert system status record"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_status 
                (service_name, status, response_time, error_message, metrics)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                status_data['service_name'],
                status_data['status'],
                status_data.get('response_time'),
                status_data.get('error_message'),
                json.dumps(status_data.get('metrics', {}))
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Failed to insert system status: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_latest_system_status(self) -> List[Dict[str, Any]]:
        """Get latest system status for all services"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM system_status s1
                WHERE timestamp = (
                    SELECT MAX(timestamp) FROM system_status s2 
                    WHERE s2.service_name = s1.service_name
                )
                ORDER BY service_name
            ''')
            
            rows = cursor.fetchall()
            
            status_records = []
            for row in rows:
                record = dict(row)
                record['metrics'] = json.loads(record.get('metrics', '{}'))
                status_records.append(record)
            
            return status_records
            
        except Exception as e:
            st.error(f"Failed to retrieve system status: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    # Utility Methods
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute custom query"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append(dict(row))
            
            return results
            
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = ['srva_accounts', 'transactions', 'settlements', 'exchange_rates', 
                     'audit_logs', 'partner_countries', 'privacy_logs', 'fraud_flags', 'system_status']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[f'{table}_count'] = count
            
            # Database size (SQLite specific)
            if self.db_type == 'sqlite':
                import os
                if os.path.exists(self.config.SQLITE_DB_PATH):
                    stats['database_size_mb'] = os.path.getsize(self.config.SQLITE_DB_PATH) / (1024 * 1024)
                else:
                    stats['database_size_mb'] = 0
            
            # Most recent activity
            cursor.execute("SELECT MAX(timestamp) FROM audit_logs")
            last_activity = cursor.fetchone()[0]
            stats['last_activity'] = last_activity
            
            return stats
            
        except Exception as e:
            st.error(f"Failed to get database stats: {str(e)}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> bool:
        """Clean up old records based on retention policy"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Clean old audit logs
            cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_date,))
            
            # Clean old exchange rates (keep more recent)
            cursor.execute("DELETE FROM exchange_rates WHERE timestamp < ?", (cutoff_date,))
            
            # Clean old system status records
            cursor.execute("DELETE FROM system_status WHERE timestamp < ?", (cutoff_date,))
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Database cleanup failed: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
