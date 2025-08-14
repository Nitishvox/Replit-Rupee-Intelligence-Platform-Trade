import sqlite3
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

class DatabaseManager:
    """Manage SQLite database operations for SRVA system"""
    
    def __init__(self, db_name: str = "srva_system.db"):
        self.db_name = db_name
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize SQLite database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        transaction_id TEXT PRIMARY KEY,
                        from_account TEXT,
                        to_account TEXT,
                        amount REAL,
                        currency TEXT,
                        exchange_rate REAL,
                        inr_amount REAL,
                        transaction_type TEXT,
                        description TEXT,
                        country TEXT,
                        status TEXT,
                        created_date TEXT,
                        processed_date TEXT,
                        is_spam INTEGER,
                        priority TEXT,
                        trade_license TEXT,
                        invoice_number TEXT,
                        regulatory_approval TEXT,
                        compliance_officer TEXT,
                        customer_risk TEXT,
                        transaction_risk TEXT,
                        aml_status TEXT
                    )
                """)
                
                # SRVA Accounts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS srva_accounts (
                        account_id TEXT PRIMARY KEY,
                        account_name TEXT,
                        bank TEXT,
                        country TEXT,
                        currency TEXT,
                        balance REAL,
                        status TEXT,
                        account_type TEXT,
                        purpose TEXT,
                        description TEXT,
                        compliance_docs TEXT,
                        created_date TEXT,
                        updated_date TEXT
                    )
                """)
                
                # Fraud detection history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fraud_detection_history (
                        detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_id TEXT,
                        amount REAL,
                        currency TEXT,
                        country TEXT,
                        is_fraud INTEGER,
                        risk_score REAL,
                        reason TEXT,
                        timestamp TEXT
                    )
                """)
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        return sqlite3.connect(self.db_name, check_same_thread=False)
    
    def insert_transaction(self, transaction: Dict) -> bool:
        """Insert a transaction into the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (
                        transaction_id, from_account, to_account, amount, currency,
                        exchange_rate, inr_amount, transaction_type, description, country,
                        status, created_date, processed_date, is_spam, priority,
                        trade_license, invoice_number, regulatory_approval,
                        compliance_officer, customer_risk, transaction_risk, aml_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.get('transaction_id'),
                    transaction.get('from_account'),
                    transaction.get('to_account'),
                    transaction.get('amount'),
                    transaction.get('currency'),
                    transaction.get('exchange_rate'),
                    transaction.get('inr_amount'),
                    transaction.get('transaction_type'),
                    transaction.get('description'),
                    transaction.get('country'),
                    transaction.get('status'),
                    transaction.get('created_date'),
                    transaction.get('processed_date'),
                    transaction.get('is_spam', 0),
                    transaction.get('priority'),
                    transaction.get('trade_license'),
                    transaction.get('invoice_number'),
                    transaction.get('regulatory_approval'),
                    transaction.get('compliance_officer'),
                    transaction.get('customer_risk'),
                    transaction.get('transaction_risk'),
                    transaction.get('aml_status')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error inserting transaction: {e}")
            return False
    
    def insert_srva_account(self, account: Dict) -> bool:
        """Insert an SRVA account into the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO srva_accounts (
                        account_id, account_name, bank, country, currency,
                        balance, status, account_type, purpose, description,
                        compliance_docs, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account.get('account_id'),
                    account.get('account_name'),
                    account.get('bank'),
                    account.get('country'),
                    account.get('currency'),
                    account.get('balance'),
                    account.get('status'),
                    account.get('account_type'),
                    account.get('purpose'),
                    account.get('description'),
                    account.get('compliance_docs'),
                    account.get('created_date'),
                    account.get('updated_date')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error inserting account: {e}")
            return False
    
    def get_transactions(self, limit: int = 1000) -> pd.DataFrame:
        """Retrieve transactions from the database"""
        try:
            with self.get_connection() as conn:
                query = f"SELECT * FROM transactions LIMIT {limit}"
                df = pd.read_sql_query(query, conn)
                return df
        except sqlite3.Error as e:
            print(f"Error retrieving transactions: {e}")
            return pd.DataFrame()
    
    def get_srva_accounts(self) -> pd.DataFrame:
        """Retrieve SRVA accounts from the database"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM srva_accounts"
                df = pd.read_sql_query(query, conn)
                return df
        except sqlite3.Error as e:
            print(f"Error retrieving accounts: {e}")
            return pd.DataFrame()
    
    def get_dashboard_stats(self) -> Dict:
        """Get summary statistics for dashboard"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Active accounts
                cursor.execute("SELECT COUNT(*) FROM srva_accounts WHERE status = 'active'")
                active_accounts = cursor.fetchone()[0]
                
                # Total settlements
                cursor.execute("SELECT SUM(inr_amount) FROM transactions WHERE status = 'completed'")
                total_settlements = cursor.fetchone()[0] or 0
                
                # Settlements this month
                current_month = datetime.now().strftime('%Y-%m')
                cursor.execute("""
                    SELECT SUM(inr_amount) 
                    FROM transactions 
                    WHERE status = 'completed' 
                    AND strftime('%Y-%m', created_date) = ?
                """, (current_month,))
                settlements_this_month = cursor.fetchone()[0] or 0
                
                # Pending transactions
                cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'pending'")
                pending_transactions = cursor.fetchone()[0]
                
                # Active countries
                cursor.execute("SELECT COUNT(DISTINCT country) FROM srva_accounts")
                active_countries = cursor.fetchone()[0]
                
                # New accounts this month
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM srva_accounts 
                    WHERE strftime('%Y-%m', created_date) = ?
                """, (current_month,))
                new_accounts_this_month = cursor.fetchone()[0]
                
                return {
                    'active_accounts': active_accounts,
                    'total_settlements': total_settlements,
                    'settlements_this_month': settlements_this_month,
                    'pending_transactions': pending_transactions,
                    'active_countries': active_countries,
                    'new_accounts_this_month': new_accounts_this_month
                }
        except sqlite3.Error as e:
            print(f"Error retrieving dashboard stats: {e}")
            return {}
    
    def get_settlement_by_country(self) -> pd.DataFrame:
        """Get settlement volume by country"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT country, SUM(inr_amount) as settlement_amount
                    FROM transactions
                    WHERE status = 'completed'
                    GROUP BY country
                    ORDER BY settlement_amount DESC
                """
                df = pd.read_sql_query(query, conn)
                return df
        except sqlite3.Error as e:
            print(f"Error retrieving settlement by country: {e}")
            return pd.DataFrame()
    
    def get_transaction_trend(self) -> pd.DataFrame:
        """Get transaction trend data"""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT 
                        date(created_date) as date,
                        SUM(CASE WHEN transaction_type IN ('export_settlement', 'service_export') 
                            THEN inr_amount ELSE 0 END) as exports,
                        SUM(CASE WHEN transaction_type IN ('import_payment', 'service_import') 
                            THEN inr_amount ELSE 0 END) as imports
                    FROM transactions
                    WHERE status = 'completed'
                    GROUP BY date(created_date)
                    ORDER BY date(created_date)
                """
                df = pd.read_sql_query(query, conn)
                return df
        except sqlite3.Error as e:
            print(f"Error retrieving transaction trend: {e}")
            return pd.DataFrame()
    
    def get_recent_activities(self, limit: int = 5) -> pd.DataFrame:
        """Get recent transaction activities"""
        try:
            with self.get_connection() as conn:
                query = f"""
                    SELECT transaction_id, amount, currency, status, created_date
                    FROM transactions
                    ORDER BY created_date DESC
                    LIMIT {limit}
                """
                df = pd.read_sql_query(query, conn)
                return df
        except sqlite3.Error as e:
            print(f"Error retrieving recent activities: {e}")
            return pd.DataFrame()
    
    def insert_fraud_detection(self, detection: Dict) -> bool:
        """Insert fraud detection result into the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO fraud_detection_history (
                        transaction_id, amount, currency, country,
                        is_fraud, risk_score, reason, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection.get('transaction_id'),
                    detection.get('amount'),
                    detection.get('currency'),
                    detection.get('country'),
                    detection.get('is_fraud', 0),
                    detection.get('risk_score'),
                    detection.get('reason'),
                    detection.get('timestamp')
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error inserting fraud detection: {e}")
            return False
    
    def get_detection_history(self) -> pd.DataFrame:
        """Retrieve fraud detection history"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM fraud_detection_history ORDER BY timestamp DESC"
                df = pd.read_sql_query(query, conn)
                return df
        except sqlite3.Error as e:
            print(f"Error retrieving detection history: {e}")
            return pd.DataFrame()