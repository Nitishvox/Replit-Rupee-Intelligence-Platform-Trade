import os
from datetime import timedelta

class Config:
    """Configuration settings for RIPT application"""
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'ript_db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    
    # SQLite fallback for local development
    SQLITE_DB_PATH = 'ript_local.db'
    USE_SQLITE = os.getenv('USE_SQLITE', 'True').lower() == 'true'
    
    # API Configuration
    RBI_API_KEY = os.getenv('RBI_API_KEY', 'default_rbi_key')
    EXCHANGE_RATE_API_URL = os.getenv('EXCHANGE_RATE_API_URL', 'https://api.exchangerate-api.com/v4/latest/INR')
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    ENCRYPTION_KEY_SIZE = 32  # AES-256
    
    # Privacy Configuration
    PRIVACY_BUDGET_TOTAL = 10.0
    PRIVACY_BUDGET_WARNING_THRESHOLD = 0.8
    K_ANONYMITY_VALUE = 5
    L_DIVERSITY_VALUE = 3
    
    # Partner Countries Configuration
    PARTNER_COUNTRIES = {
        'Russia': {
            'currency': 'RUB',
            'trade_limit': 50000000,
            'compliance_flags': ['sanctions_check', 'kyc_enhanced'],
            'corridor': 'IN-RU'
        },
        'Germany': {
            'currency': 'EUR',
            'trade_limit': 100000000,
            'compliance_flags': ['eu_regulations', 'aml_standard'],
            'corridor': 'IN-EU'
        },
        'UK': {
            'currency': 'GBP',
            'trade_limit': 75000000,
            'compliance_flags': ['uk_regulations', 'brexit_compliance'],
            'corridor': 'IN-GB'
        },
        'Singapore': {
            'currency': 'SGD',
            'trade_limit': 80000000,
            'compliance_flags': ['mas_regulations', 'asean_trade'],
            'corridor': 'IN-SG'
        }
    }
    
    # Transaction Configuration
    TRANSACTION_TIMEOUT = timedelta(minutes=30)
    MAX_DAILY_TRANSACTIONS = 10000
    HIGH_RISK_THRESHOLD = 75
    MEDIUM_RISK_THRESHOLD = 50
    
    # Performance Configuration
    CACHE_TTL = 300  # 5 minutes
    MAX_TRANSACTION_HISTORY = 100000
    TPS_CALCULATION_WINDOW = timedelta(minutes=5)
    
    # Export Configuration
    EXPORT_BATCH_SIZE = 1000
    SUPPORTED_EXPORT_FORMATS = ['XML', 'CSV', 'JSON']
    
    # Monitoring Configuration
    HEALTH_CHECK_INTERVAL = 60  # seconds
    ALERT_RETENTION_DAYS = 30
    LOG_RETENTION_DAYS = 90
    
    # QR Code Configuration
    QR_CODE_SIZE = 300
    QR_CODE_BORDER = 4
    QR_CODE_ERROR_CORRECTION = 'M'  # Medium error correction
    
    @classmethod
    def get_database_url(cls):
        """Get database connection URL"""
        if cls.USE_SQLITE:
            return f"sqlite:///{cls.SQLITE_DB_PATH}"
        else:
            return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
    
    @classmethod
    def get_partner_country_config(cls, country):
        """Get configuration for a specific partner country"""
        return cls.PARTNER_COUNTRIES.get(country, {})
    
    @classmethod
    def is_high_risk_amount(cls, amount, currency='INR'):
        """Check if transaction amount is considered high risk"""
        if currency == 'INR':
            return amount > 10000000  # 1 crore
        elif currency == 'USD':
            return amount > 120000  # ~1 crore
        elif currency == 'EUR':
            return amount > 110000  # ~1 crore
        elif currency == 'GBP':
            return amount > 95000   # ~1 crore
        elif currency == 'SGD':
            return amount > 160000  # ~1 crore
        elif currency == 'RUB':
            return amount > 8000000 # ~1 crore
        else:
            return amount > 100000  # Default threshold
