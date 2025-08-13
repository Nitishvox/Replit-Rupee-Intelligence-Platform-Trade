import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

class DatabaseManager:
    """Enhanced database manager for RIPT system with comprehensive SRVA support"""
    
    def __init__(self, db_path: str = "srva_system.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # SRVA Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS srva_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT UNIQUE NOT NULL,
                    account_name TEXT NOT NULL,
                    bank TEXT NOT NULL,
                    country TEXT NOT NULL,
                    currency TEXT DEFAULT 'INR',
                    balance REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    account_type TEXT DEFAULT 'Corporate',
                    purpose TEXT DEFAULT 'Both',
                    description TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    from_account TEXT NOT NULL,
                    to_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    exchange_rate REAL,
                    inr_amount REAL,
                    transaction_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    description TEXT,
                    country TEXT,
                    priority TEXT DEFAULT 'Normal',
                    trade_license TEXT,
                    invoice_number TEXT,
                    regulatory_approval TEXT,
                    compliance_officer TEXT DEFAULT 'system',
                    customer_risk TEXT DEFAULT 'Low',
                    transaction_risk TEXT DEFAULT 'Low',
                    aml_status TEXT DEFAULT 'Cleared',
                    settlement_date TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_date TIMESTAMP,
                    is_spam INTEGER DEFAULT 0
                )
            """)
            
            # Exchange rates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    date TEXT NOT NULL,
                    provider TEXT DEFAULT 'system',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Compliance records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    compliance_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    officer_id TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
                )
            """)
            
            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    old_values TEXT,
                    new_values TEXT,
                    user_id TEXT DEFAULT 'system',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Fraud detection results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    risk_score REAL NOT NULL,
                    is_fraud INTEGER NOT NULL,
                    reason TEXT,
                    model_version TEXT DEFAULT 'v1.0',
                    detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # QR codes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qr_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    qr_id TEXT UNIQUE NOT NULL,
                    qr_type TEXT NOT NULL,
                    data_content TEXT NOT NULL,
                    encrypted_data TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_date TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT UNIQUE NOT NULL,
                    document_type TEXT NOT NULL,
                    reference_id TEXT,
                    file_name TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    mime_type TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'system'
                )
            """)
            
            conn.commit()
    
    def insert_srva_account(self, account_data: Dict) -> bool:
        """Insert new SRVA account"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO srva_accounts 
                    (account_id, account_name, bank, country, currency, balance, status, 
                     account_type, purpose, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account_data['account_id'],
                    account_data['account_name'],
                    account_data['bank'],
                    account_data['country'],
                    account_data.get('currency', 'INR'),
                    account_data.get('balance', 0.0),
                    account_data.get('status', 'active'),
                    account_data.get('account_type', 'Corporate'),
                    account_data.get('purpose', 'Both'),
                    account_data.get('description', '')
                ))
                conn.commit()
                
                # Log the action
                self._log_audit('INSERT', 'srva_accounts', account_data['account_id'], None, account_data)
                return True
        except sqlite3.IntegrityError:
            print(f"Account with ID {account_data['account_id']} already exists")
            return False
        except Exception as e:
            print(f"Error inserting SRVA account: {e}")
            return False
    
    def insert_transaction(self, transaction_data: Dict) -> bool:
        """Insert new transaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions 
                    (transaction_id, from_account, to_account, amount, currency, exchange_rate, 
                     inr_amount, transaction_type, description, country, priority, trade_license,
                     invoice_number, regulatory_approval, compliance_officer, customer_risk,
                     transaction_risk, aml_status, settlement_date, is_spam)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_data['transaction_id'],
                    transaction_data['from_account'],
                    transaction_data['to_account'],
                    transaction_data['amount'],
                    transaction_data['currency'],
                    transaction_data.get('exchange_rate'),
                    transaction_data.get('inr_amount'),
                    transaction_data['transaction_type'],
                    transaction_data.get('description', ''),
                    transaction_data.get('country', ''),
                    transaction_data.get('priority', 'Normal'),
                    transaction_data.get('trade_license', ''),
                    transaction_data.get('invoice_number', ''),
                    transaction_data.get('regulatory_approval', 'No'),
                    transaction_data.get('compliance_officer', 'system'),
                    transaction_data.get('customer_risk', 'Low'),
                    transaction_data.get('transaction_risk', 'Low'),
                    transaction_data.get('aml_status', 'Cleared'),
                    transaction_data.get('settlement_date', ''),
                    transaction_data.get('is_spam', 0)
                ))
                conn.commit()
                
                # Log the action
                self._log_audit('INSERT', 'transactions', transaction_data['transaction_id'], None, transaction_data)
                return True
        except sqlite3.IntegrityError:
            print(f"Transaction with ID {transaction_data['transaction_id']} already exists")
            return False
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            return False
    
    def get_srva_accounts(self, status: str = None) -> pd.DataFrame:
        """Get SRVA accounts with optional status filter"""
        try:
            with self.get_connection() as conn:
                if status:
                    query = "SELECT * FROM srva_accounts WHERE status = ? ORDER BY created_date DESC"
                    df = pd.read_sql_query(query, conn, params=(status,))
                else:
                    query = "SELECT * FROM srva_accounts ORDER BY created_date DESC"
                    df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error fetching SRVA accounts: {e}")
            return pd.DataFrame()
    
    def get_transactions(self, limit: int = 100, status: str = None) -> pd.DataFrame:
        """Get transactions with optional status filter"""
        try:
            with self.get_connection() as conn:
                if status:
                    query = """
                        SELECT * FROM transactions 
                        WHERE status = ? 
                        ORDER BY created_date DESC 
                        LIMIT ?
                    """
                    df = pd.read_sql_query(query, conn, params=(status, limit))
                else:
                    query = """
                        SELECT * FROM transactions 
                        ORDER BY created_date DESC 
                        LIMIT ?
                    """
                    df = pd.read_sql_query(query, conn, params=(limit,))
                return df
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return pd.DataFrame()
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        stats = {
            'active_accounts': 0,
            'new_accounts_this_month': 0,
            'total_settlements': 0,
            'settlements_this_month': 0,
            'active_countries': 0,
            'new_countries_this_month': 0,
            'pending_transactions': 0
        }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Active accounts
                cursor.execute("SELECT COUNT(*) FROM srva_accounts WHERE status = 'active'")
                result = cursor.fetchone()
                stats['active_accounts'] = result[0] if result else 0
                
                # New accounts this month
                cursor.execute("""
                    SELECT COUNT(*) FROM srva_accounts 
                    WHERE created_date >= date('now', 'start of month')
                """)
                result = cursor.fetchone()
                stats['new_accounts_this_month'] = result[0] if result else 0
                
                # Total settlements
                cursor.execute("""
                    SELECT COALESCE(SUM(inr_amount), 0) FROM transactions 
                    WHERE status = 'completed'
                """)
                result = cursor.fetchone()
                stats['total_settlements'] = result[0] if result else 0
                
                # Settlements this month
                cursor.execute("""
                    SELECT COALESCE(SUM(inr_amount), 0) FROM transactions 
                    WHERE status = 'completed' AND created_date >= date('now', 'start of month')
                """)
                result = cursor.fetchone()
                stats['settlements_this_month'] = result[0] if result else 0
                
                # Active countries
                cursor.execute("SELECT COUNT(DISTINCT country) FROM srva_accounts WHERE status = 'active'")
                result = cursor.fetchone()
                stats['active_countries'] = result[0] if result else 0
                
                # Pending transactions
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'pending'")
                result = cursor.fetchone()
                stats['pending_transactions'] = result[0] if result else 0
                
        except Exception as e:
            print(f"Error fetching dashboard stats: {e}")
        
        return stats
    
    def get_settlement_by_country(self) -> pd.DataFrame:
        """Get settlement amounts by country for the last 30 days"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT 
                        country,
                        COUNT(*) as transaction_count,
                        COALESCE(SUM(inr_amount), 0) as settlement_amount
                    FROM transactions 
                    WHERE status = 'completed' 
                    AND created_date >= date('now', '-30 days')
                    AND country IS NOT NULL AND country != ''
                    GROUP BY country
                    ORDER BY settlement_amount DESC
                """
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error fetching settlement by country: {e}")
            return pd.DataFrame()
    
    def get_transaction_trend(self) -> pd.DataFrame:
        """Get transaction trend data for the last 30 days"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT 
                        date(created_date) as date,
                        COALESCE(SUM(CASE WHEN transaction_type LIKE '%export%' THEN inr_amount ELSE 0 END), 0) as exports,
                        COALESCE(SUM(CASE WHEN transaction_type LIKE '%import%' THEN inr_amount ELSE 0 END), 0) as imports
                    FROM transactions 
                    WHERE created_date >= date('now', '-30 days')
                    AND status = 'completed'
                    GROUP BY date(created_date)
                    ORDER BY date
                """
                df = pd.read_sql_query(query, conn)
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                return df
        except Exception as e:
            print(f"Error fetching transaction trend: {e}")
            return pd.DataFrame()
    
    def get_recent_activities(self) -> pd.DataFrame:
        """Get recent system activities"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT 
                        transaction_id,
                        transaction_type,
                        amount,
                        currency,
                        status,
                        country,
                        created_date
                    FROM transactions 
                    ORDER BY created_date DESC 
                    LIMIT 10
                """
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Error fetching recent activities: {e}")
            return pd.DataFrame()
    
    def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get old values for audit
                cursor.execute("SELECT status FROM transactions WHERE transaction_id = ?", (transaction_id,))
                old_status = cursor.fetchone()
                
                cursor.execute("""
                    UPDATE transactions 
                    SET status = ?, processed_date = CURRENT_TIMESTAMP 
                    WHERE transaction_id = ?
                """, (status, transaction_id))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    # Log the action
                    self._log_audit('UPDATE', 'transactions', transaction_id, 
                                  {'status': old_status[0] if old_status else None}, 
                                  {'status': status})
                    return True
                return False
        except Exception as e:
            print(f"Error updating transaction status: {e}")
            return False
    
    def insert_compliance_record(self, compliance_data: Dict) -> bool:
        """Insert compliance record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO compliance_records 
                    (transaction_id, compliance_type, status, notes, officer_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    compliance_data['transaction_id'],
                    compliance_data['compliance_type'],
                    compliance_data['status'],
                    compliance_data.get('notes', ''),
                    compliance_data.get('officer_id', 'system')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting compliance record: {e}")
            return False
    
    def insert_fraud_detection(self, detection_data: Dict) -> bool:
        """Insert fraud detection result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO fraud_detections 
                    (transaction_id, risk_score, is_fraud, reason, model_version, detection_date)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    detection_data.get('transaction_id'),
                    detection_data['risk_score'],
                    1 if detection_data['is_fraud'] else 0,
                    detection_data.get('reason', ''),
                    detection_data.get('model_version', 'v1.0')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting fraud detection: {e}")
            return False
    
    def get_fraud_detections(self, limit: int = 100) -> pd.DataFrame:
        """Get fraud detection results"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT fd.*, t.amount, t.currency, t.country
                    FROM fraud_detections fd
                    LEFT JOIN transactions t ON fd.transaction_id = t.transaction_id
                    ORDER BY fd.detection_date DESC
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(limit,))
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['detection_date'])
                return df
        except Exception as e:
            print(f"Error fetching fraud detections: {e}")
            return pd.DataFrame()
    
    def insert_qr_code(self, qr_data: Dict) -> bool:
        """Insert QR code record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO qr_codes 
                    (qr_id, qr_type, data_content, encrypted_data, expires_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    qr_data['qr_id'],
                    qr_data['qr_type'],
                    qr_data['data_content'],
                    qr_data.get('encrypted_data', ''),
                    qr_data.get('expires_date')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting QR code: {e}")
            return False
    
    def insert_document(self, document_data: Dict) -> bool:
        """Insert document record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO documents 
                    (document_id, document_type, reference_id, file_name, file_path, 
                     file_size, mime_type, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_data['document_id'],
                    document_data['document_type'],
                    document_data.get('reference_id'),
                    document_data.get('file_name'),
                    document_data.get('file_path'),
                    document_data.get('file_size'),
                    document_data.get('mime_type'),
                    document_data.get('created_by', 'system')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting document: {e}")
            return False
    
    def _log_audit(self, action: str, table_name: str, record_id: str, old_values: Any, new_values: Any):
        """Log audit trail"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_logs 
                    (action, table_name, record_id, old_values, new_values)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    action,
                    table_name,
                    record_id,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values, default=str) if new_values else None
                ))
                conn.commit()
        except Exception as e:
            print(f"Error logging audit: {e}")
    
    def get_audit_logs(self, limit: int = 100) -> pd.DataFrame:
        """Get audit logs"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT * FROM audit_logs 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """
                df = pd.read_sql_query(query, conn, params=(limit,))
                return df
        except Exception as e:
            print(f"Error fetching audit logs: {e}")
            return pd.DataFrame()
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old data (optional maintenance function)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean old exchange rates
                cursor.execute("""
                    DELETE FROM exchange_rates 
                    WHERE created_date < date('now', '-' || ? || ' days')
                """, (days,))
                
                # Clean old audit logs
                cursor.execute("""
                    DELETE FROM audit_logs 
                    WHERE timestamp < date('now', '-' || ? || ' days')
                """, (days,))
                
                # Clean expired QR codes
                cursor.execute("""
                    DELETE FROM qr_codes 
                    WHERE expires_date < datetime('now') AND expires_date IS NOT NULL
                """)
                
                conn.commit()
                print(f"Cleaned up data older than {days} days")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                tables = ['srva_accounts', 'transactions', 'compliance_records', 
                         'fraud_detections', 'qr_codes', 'documents', 'audit_logs']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    result = cursor.fetchone()
                    stats[f'{table}_count'] = result[0] if result else 0
                
                # Database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                result = cursor.fetchone()
                stats['database_size_bytes'] = result[0] if result else 0
                
        except Exception as e:
            print(f"Error fetching database stats: {e}")
        
        return stats
