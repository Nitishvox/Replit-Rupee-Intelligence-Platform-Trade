import streamlit as st
import pandas as pd
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class DataGenerator:
    """Data Generator for creating random transactions and SRVA accounts for testing and demonstration"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        self.currencies = ["USD", "EUR", "GBP", "RUB", "SGD", "AUD", "JPY", "CAD", "CHF", "CNY"]
        
        self.countries = [
            "Russia", "Germany", "United Kingdom", "Singapore", "Malaysia",
            "Thailand", "South Korea", "Japan", "Australia", "New Zealand",
            "UAE", "Saudi Arabia", "Egypt", "South Africa", "Brazil",
            "Mexico", "Turkey", "Bangladesh", "Sri Lanka", "Myanmar"
        ]
        
        self.banks = [
            "State Bank of India", "ICICI Bank", "HDFC Bank", "Axis Bank",
            "Punjab National Bank", "Bank of Baroda", "Union Bank of India",
            "Canara Bank", "Indian Overseas Bank", "Central Bank of India"
        ]
        
        self.transaction_types = [
            "export_settlement", "import_payment", "service_export", 
            "service_import", "investment_income", "dividend_payment",
            "interest_payment", "other_trade_related"
        ]
        
        self.company_names = [
            "Global Trading Corp", "International Export Ltd", "Premium Imports Inc",
            "Tech Services Global", "Manufacturing Solutions", "Energy Trading Co",
            "Textile Exports Ltd", "Pharma International", "Auto Components Inc",
            "Chemical Industries Ltd", "Food Processing Corp", "Steel Trading Co",
            "Electronics Export Ltd", "Machinery International", "Oil & Gas Trading"
        ]
        
        self.spam_indicators = [
            "suspicious_amount_pattern", "unusual_frequency", "fake_documentation",
            "blacklisted_entity", "high_risk_country", "unusual_timing",
            "duplicate_transaction", "invalid_account_details"
        ]
    
    def generate_random_transactions(self, count: int = 100, include_spam: bool = True, 
                                   spam_percentage: int = 10) -> List[Dict]:
        """Generate random transactions with optional spam transactions"""
        transactions = []
        
        # Calculate number of spam transactions
        spam_count = int(count * spam_percentage / 100) if include_spam else 0
        legitimate_count = count - spam_count
        
        # Generate legitimate transactions
        for _ in range(legitimate_count):
            transaction = self._generate_single_transaction(is_spam=False)
            transactions.append(transaction)
        
        # Generate spam transactions
        for _ in range(spam_count):
            transaction = self._generate_single_transaction(is_spam=True)
            transactions.append(transaction)
        
        # Shuffle the list to mix legitimate and spam transactions
        random.shuffle(transactions)
        
        return transactions
    
    def _generate_single_transaction(self, is_spam: bool = False) -> Dict:
        """Generate a single random transaction"""
        
        # Base transaction data
        transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Random datetime within last 90 days
        days_ago = random.randint(0, 90)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        created_date = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Random account selection
        from_account = f"SRVA-{random.choice(['RUS', 'GER', 'UK', 'SG', 'JP'])}-{random.randint(1000, 9999)}"
        to_account = f"SRVA-{random.choice(['IND', 'USA', 'EU', 'AS'])}-{random.randint(1000, 9999)}"
        
        # Ensure from and to accounts are different
        while to_account == from_account:
            to_account = f"SRVA-{random.choice(['IND', 'USA', 'EU', 'AS'])}-{random.randint(1000, 9999)}"
        
        currency = random.choice(self.currencies)
        country = random.choice(self.countries)
        transaction_type = random.choice(self.transaction_types)
        
        # Generate amount based on transaction type and spam flag
        if is_spam:
            # Spam transactions might have unusual amounts
            if random.random() < 0.3:  # 30% chance of very high amount
                amount = random.uniform(50000000, 1000000000)  # 5 Cr to 100 Cr (suspicious)
            elif random.random() < 0.3:  # 30% chance of very low amount
                amount = random.uniform(0.01, 100)  # Very small amounts (suspicious)
            else:
                amount = random.uniform(1000, 10000000)  # Normal range but will have other spam indicators
        else:
            # Legitimate transactions have more realistic amounts
            if transaction_type in ["export_settlement", "import_payment"]:
                amount = random.uniform(100000, 50000000)  # 1L to 5Cr
            elif transaction_type in ["service_export", "service_import"]:
                amount = random.uniform(50000, 5000000)  # 50K to 50L
            else:
                amount = random.uniform(10000, 1000000)  # 10K to 10L
        
        # Exchange rate (mock - in real system would come from API)
        exchange_rates = {
            'USD': random.uniform(82, 85),
            'EUR': random.uniform(88, 92),
            'GBP': random.uniform(103, 107),
            'RUB': random.uniform(0.85, 0.95),
            'SGD': random.uniform(60, 63),
            'AUD': random.uniform(53, 57),
            'JPY': random.uniform(0.54, 0.58),
            'CAD': random.uniform(60, 64),
            'CHF': random.uniform(90, 95),
            'CNY': random.uniform(11, 12)
        }
        
        exchange_rate = exchange_rates.get(currency, 83.0)
        inr_amount = amount * exchange_rate
        
        # Status based on creation time and spam flag
        if is_spam:
            # Spam transactions might be rejected or on hold more frequently
            status = random.choices(
                ['pending', 'completed', 'rejected', 'on_hold'],
                weights=[20, 30, 35, 15]  # Higher chance of rejection
            )[0]
        else:
            # Legitimate transactions are more likely to be completed
            if created_date < datetime.now() - timedelta(days=2):
                status = random.choices(
                    ['completed', 'rejected', 'on_hold'],
                    weights=[85, 10, 5]
                )[0]
            elif created_date < datetime.now() - timedelta(hours=4):
                status = random.choices(
                    ['completed', 'pending', 'rejected'],
                    weights=[70, 25, 5]
                )[0]
            else:
                status = random.choices(
                    ['pending', 'completed'],
                    weights=[60, 40]
                )[0]
        
        # Description
        if is_spam:
            descriptions = [
                "Urgent payment required",
                "CONFIDENTIAL TRANSACTION", 
                "High priority settlement",
                "Special trade arrangement",
                "Immediate processing needed"
            ]
        else:
            descriptions = [
                f"Export payment for {random.choice(['machinery', 'textiles', 'chemicals', 'pharmaceuticals', 'electronics'])}",
                f"Import settlement for {random.choice(['raw materials', 'components', 'finished goods', 'services'])}",
                f"Trade settlement - Invoice #{random.randint(10000, 99999)}",
                f"Business payment for {random.choice(['consulting', 'software', 'manufacturing', 'trading'])} services",
                f"Export proceeds for {random.choice(['Q1', 'Q2', 'Q3', 'Q4'])} {datetime.now().year}"
            ]
        
        description = random.choice(descriptions)
        
        transaction = {
            'transaction_id': transaction_id,
            'from_account': from_account,
            'to_account': to_account,
            'amount': round(amount, 2),
            'currency': currency,
            'exchange_rate': round(exchange_rate, 4),
            'inr_amount': round(inr_amount, 2),
            'transaction_type': transaction_type,
            'description': description,
            'country': country,
            'status': status,
            'created_date': created_date.isoformat(),
            'processed_date': (created_date + timedelta(hours=random.randint(1, 48))).isoformat() if status == 'completed' else None,
            'is_spam': 1 if is_spam else 0
        }
        
        # Add spam indicators for spam transactions
        if is_spam:
            transaction['spam_indicators'] = random.sample(self.spam_indicators, random.randint(1, 3))
        
        return transaction
    
    def generate_srva_accounts(self, count: int = 20) -> List[Dict]:
        """Generate random SRVA accounts"""
        accounts = []
        
        for i in range(count):
            country_code_map = {
                'Russia': 'RUS', 'Germany': 'GER', 'United Kingdom': 'UK',
                'Singapore': 'SG', 'Japan': 'JP', 'Australia': 'AU',
                'UAE': 'UAE', 'South Korea': 'KR', 'Malaysia': 'MY',
                'Thailand': 'TH'
            }
            
            country = random.choice(list(country_code_map.keys()))
            country_code = country_code_map[country]
            
            account_id = f"SRVA-{country_code}-{1000 + i:04d}"
            
            company_name = f"{random.choice(self.company_names)} ({country})"
            
            bank = random.choice(self.banks)
            
            # Currency based on country
            currency_map = {
                'Russia': 'RUB', 'Germany': 'EUR', 'United Kingdom': 'GBP',
                'Singapore': 'SGD', 'Japan': 'JPY', 'Australia': 'AUD',
                'UAE': 'AED', 'South Korea': 'KRW', 'Malaysia': 'MYR',
                'Thailand': 'THB'
            }
            
            primary_currency = currency_map.get(country, 'USD')
            
            # Random balance
            balance = random.uniform(0, 10000000)  # 0 to 1 Cr
            
            # Account status
            status = random.choices(
                ['active', 'suspended', 'closed'],
                weights=[85, 10, 5]
            )[0]
            
            # Creation date within last 2 years
            days_ago = random.randint(0, 730)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            account = {
                'account_id': account_id,
                'account_name': company_name,
                'bank': bank,
                'country': country,
                'currency': primary_currency,
                'balance': round(balance, 2),
                'status': status,
                'created_date': created_date.isoformat(),
                'updated_date': created_date.isoformat()
            }
            
            accounts.append(account)
        
        return accounts
    
    def insert_transactions_to_db(self, transactions: List[Dict]) -> int:
        """Insert generated transactions to database"""
        success_count = 0
        
        for transaction in transactions:
            if self.db_manager.insert_transaction(transaction):
                success_count += 1
        
        return success_count
    
    def insert_accounts_to_db(self, accounts: List[Dict]) -> int:
        """Insert generated accounts to database"""
        success_count = 0
        
        for account in accounts:
            if self.db_manager.insert_srva_account(account):
                success_count += 1
        
        return success_count
    
    def generate_time_series_data(self, days: int = 90, transactions_per_day_range: tuple = (10, 50)) -> List[Dict]:
        """Generate time series transaction data for analytics"""
        transactions = []
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            
            # Weekend effect - fewer transactions on weekends
            if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                daily_transactions = random.randint(
                    transactions_per_day_range[0] // 2,
                    transactions_per_day_range[1] // 2
                )
            else:
                daily_transactions = random.randint(*transactions_per_day_range)
            
            # Generate transactions for this day
            for _ in range(daily_transactions):
                transaction = self._generate_single_transaction(is_spam=random.random() < 0.05)  # 5% spam
                
                # Override created_date to be on the specific day
                hour = random.randint(9, 17)  # Business hours
                minute = random.randint(0, 59)
                
                transaction['created_date'] = date.replace(hour=hour, minute=minute).isoformat()
                
                transactions.append(transaction)
        
        return transactions
    
    def generate_seasonal_data(self, months: int = 12) -> List[Dict]:
        """Generate seasonal transaction data with realistic patterns"""
        transactions = []
        
        # Seasonal multipliers for different months
        seasonal_multipliers = {
            1: 0.8,   # January - slower start
            2: 0.9,   # February
            3: 1.1,   # March - financial year end
            4: 1.2,   # April - new financial year
            5: 1.0,   # May
            6: 0.9,   # June
            7: 1.0,   # July
            8: 1.1,   # August
            9: 1.2,   # September - festive season prep
            10: 1.3,  # October - peak festive season
            11: 1.1,  # November - post festive
            12: 1.4   # December - year-end rush
        }
        
        base_date = datetime.now() - timedelta(days=30*months)
        
        for month_offset in range(months):
            current_date = base_date + timedelta(days=30*month_offset)
            month = current_date.month
            
            multiplier = seasonal_multipliers.get(month, 1.0)
            base_transactions = int(500 * multiplier)  # Base 500 transactions per month
            
            # Generate transactions for this month
            for _ in range(base_transactions):
                transaction = self._generate_single_transaction(is_spam=random.random() < 0.03)  # 3% spam
                
                # Random date within the month
                day_offset = random.randint(0, 29)
                transaction_date = current_date + timedelta(days=day_offset)
                
                transaction['created_date'] = transaction_date.isoformat()
                
                transactions.append(transaction)
        
        return transactions
    
    def generate_stress_test_data(self, peak_tps: int = 100, duration_minutes: int = 60) -> List[Dict]:
        """Generate stress test data with varying transaction rates"""
        transactions = []
        
        start_time = datetime.now()
        
        for minute in range(duration_minutes):
            current_time = start_time + timedelta(minutes=minute)
            
            # Simulate varying load - peak in the middle
            load_factor = abs(minute - duration_minutes//2) / (duration_minutes//2)
            load_factor = 1 - load_factor  # Invert so peak is at 1.0
            
            transactions_this_minute = int(peak_tps * load_factor)
            
            for second in range(0, 60, max(1, 60//transactions_this_minute)):
                if len(transactions) >= peak_tps * duration_minutes:
                    break
                    
                transaction = self._generate_single_transaction(is_spam=random.random() < 0.01)
                
                transaction_time = current_time + timedelta(seconds=second)
                transaction['created_date'] = transaction_time.isoformat()
                
                transactions.append(transaction)
        
        return transactions
    
    def clear_generated_data(self):
        """Clear all generated data from the database"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear transactions
                cursor.execute("DELETE FROM transactions WHERE transaction_id LIKE 'TXN-%'")
                
                # Clear accounts
                cursor.execute("DELETE FROM srva_accounts WHERE account_id LIKE 'SRVA-%'")
                
                conn.commit()
                
                return True
        except Exception as e:
            print(f"Error clearing generated data: {e}")
            return False
    
    def get_generation_statistics(self) -> Dict:
        """Get statistics about generated data"""
        transactions_df = self.db_manager.get_transactions(limit=10000)
        accounts_df = self.db_manager.get_srva_accounts()
        
        stats = {
            'total_transactions': len(transactions_df),
            'total_accounts': len(accounts_df),
            'spam_transactions': len(transactions_df[transactions_df['is_spam'] == 1]) if 'is_spam' in transactions_df.columns else 0,
            'legitimate_transactions': len(transactions_df[transactions_df['is_spam'] == 0]) if 'is_spam' in transactions_df.columns else len(transactions_df),
            'active_accounts': len(accounts_df[accounts_df['status'] == 'active']) if not accounts_df.empty else 0,
            'countries_covered': accounts_df['country'].nunique() if not accounts_df.empty else 0,
            'currencies_used': transactions_df['currency'].nunique() if not transactions_df.empty else 0,
            'date_range': {
                'earliest': transactions_df['created_date'].min() if not transactions_df.empty else None,
                'latest': transactions_df['created_date'].max() if not transactions_df.empty else None
            }
        }
        
        return stats
