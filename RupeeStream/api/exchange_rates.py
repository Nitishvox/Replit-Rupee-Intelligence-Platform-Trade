import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st
import time
import json

from config import Config
from utils.db_manager import DatabaseManager

class ExchangeRateManager:
    """Manages real-time exchange rate fetching and caching"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.cache_duration = 300  # 5 minutes cache
        
        # RBI-aligned base rates (approximate)
        self.base_rates = {
            "USDINR": 83.5,
            "EURINR": 90.2,
            "GBPINR": 105.3,
            "SGDINR": 61.8,
            "AEDINR": 22.7,
            "JPYINR": 0.56,
            "RUBINR": 0.91
        }
        
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_current_rates(_self) -> Dict[str, float]:
        """Get current exchange rates with caching"""
        try:
            # Try to fetch from external API first
            api_rates = _self._fetch_from_api()
            if api_rates:
                # Store in database for fallback
                _self._store_rates_in_db(api_rates)
                return api_rates
            else:
                # Fallback to database
                db_rates = _self._get_rates_from_db()
                if db_rates:
                    return db_rates
                else:
                    # Final fallback to simulated rates
                    return _self._generate_simulated_rates()
                    
        except Exception as e:
            st.warning(f"Rate fetching failed, using simulated rates: {str(e)}")
            return _self._generate_simulated_rates()
    
    def _fetch_from_api(self) -> Optional[Dict[str, float]]:
        """Fetch rates from external API"""
        try:
            # Using a free exchange rate API (fallback implementation)
            # In production, this would use RBI's official API
            api_url = self.config.EXCHANGE_RATE_API_URL
            api_key = self.config.RBI_API_KEY
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(api_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant rates and convert to INR base
                rates = {}
                if 'rates' in data:
                    base_rates = data['rates']
                    for pair in self.base_rates.keys():
                        if pair.replace('INR', '') in base_rates:
                            rates[pair] = base_rates[pair.replace('INR', '')]
                
                return rates if rates else None
            else:
                return None
                
        except requests.RequestException:
            return None
        except Exception:
            return None
    
    def _store_rates_in_db(self, rates: Dict[str, float]):
        """Store rates in database"""
        try:
            rate_record = {
                'timestamp': datetime.now(),
                'rates': json.dumps(rates),
                'source': 'API'
            }
            self.db.insert_exchange_rates(rate_record)
        except Exception:
            pass  # Silent fail for storage
    
    def _get_rates_from_db(self) -> Optional[Dict[str, float]]:
        """Get latest rates from database"""
        try:
            latest_record = self.db.get_latest_exchange_rates()
            if latest_record:
                # Check if data is not too old (max 1 hour)
                if (datetime.now() - latest_record['timestamp']).seconds < 3600:
                    return json.loads(latest_record['rates'])
            return None
        except Exception:
            return None
    
    def _generate_simulated_rates(self) -> Dict[str, float]:
        """Generate simulated rates with realistic fluctuations"""
        rates = {}
        current_time = datetime.now()
        
        for pair, base_rate in self.base_rates.items():
            # Add realistic volatility (±0.5%)
            volatility = np.random.normal(0, 0.005)
            
            # Add time-based trends (market hours effect)
            hour = current_time.hour
            if 9 <= hour <= 17:  # Market hours
                trend = np.random.normal(0, 0.002)
            else:
                trend = np.random.normal(0, 0.001)
            
            # Calculate final rate
            adjusted_rate = base_rate * (1 + volatility + trend)
            rates[pair] = round(adjusted_rate, 4)
        
        return rates
    
    def get_rate_for_corridor(self, corridor: str) -> float:
        """Get specific rate for a trading corridor"""
        corridor_mapping = {
            'IN-US': 'USDINR',
            'IN-EU': 'EURINR', 
            'IN-GB': 'GBPINR',
            'IN-SG': 'SGDINR',
            'IN-AE': 'AEDINR',
            'IN-JP': 'JPYINR',
            'IN-RU': 'RUBINR'
        }
        
        rates = self.get_current_rates()
        rate_pair = corridor_mapping.get(corridor)
        
        if rate_pair and rate_pair in rates:
            return rates[rate_pair]
        else:
            return self.base_rates.get(rate_pair, 83.5)  # Default to USDINR
    
    def calculate_conversion(self, amount: float, from_currency: str, 
                           to_currency: str = 'INR') -> Dict[str, Any]:
        """Calculate currency conversion"""
        try:
            if from_currency == to_currency:
                return {
                    'converted_amount': amount,
                    'rate': 1.0,
                    'original_amount': amount,
                    'from_currency': from_currency,
                    'to_currency': to_currency
                }
            
            # Get conversion rate
            if to_currency == 'INR':
                rate_pair = f"{from_currency}INR"
                rate = self.get_current_rates().get(rate_pair, 1.0)
                converted_amount = amount * rate
            elif from_currency == 'INR':
                rate_pair = f"{to_currency}INR"
                inr_rate = self.get_current_rates().get(rate_pair, 1.0)
                rate = 1 / inr_rate if inr_rate != 0 else 1.0
                converted_amount = amount * rate
            else:
                # Cross currency conversion via INR
                from_to_inr = self.get_current_rates().get(f"{from_currency}INR", 1.0)
                to_to_inr = self.get_current_rates().get(f"{to_currency}INR", 1.0)
                rate = from_to_inr / to_to_inr if to_to_inr != 0 else 1.0
                converted_amount = amount * rate
            
            return {
                'converted_amount': round(converted_amount, 2),
                'rate': round(rate, 4),
                'original_amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            return {
                'converted_amount': amount,
                'rate': 1.0,
                'original_amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'error': str(e)
            }
    
    def get_historical_rates(self, days: int = 30) -> pd.DataFrame:
        """Get historical exchange rate data"""
        try:
            # Try to get from database first
            historical_data = self.db.get_historical_exchange_rates(days)
            
            if historical_data and len(historical_data) > 10:
                return pd.DataFrame(historical_data)
            else:
                # Generate simulated historical data
                return self._generate_historical_data(days)
                
        except Exception:
            return self._generate_historical_data(days)
    
    def _generate_historical_data(self, days: int) -> pd.DataFrame:
        """Generate simulated historical exchange rate data"""
        dates = [datetime.now() - timedelta(days=i) for i in range(days)]
        dates.reverse()
        
        data = []
        
        for i, date in enumerate(dates):
            row = {'date': date}
            
            for pair, base_rate in self.base_rates.items():
                # Simulate realistic price movements
                daily_change = np.random.normal(0, 0.005)  # 0.5% daily volatility
                trend = np.sin(i / 10) * 0.002  # Long-term trend
                weekend_effect = 0.001 if date.weekday() >= 5 else 0
                
                # Calculate rate for this day
                rate = base_rate * (1 + daily_change + trend + weekend_effect)
                
                # Add some autocorrelation for realism
                if i > 0:
                    prev_rate = data[i-1].get(f'{pair}_rate', base_rate)
                    rate = 0.7 * rate + 0.3 * prev_rate
                
                row[f'{pair}_rate'] = round(rate, 4)
                row[f'{pair}_volatility'] = abs(daily_change)
            
            data.append(row)
        
        return pd.DataFrame(data)
    
    def get_rate_alerts(self, thresholds: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """Check for rate alerts based on thresholds"""
        alerts = []
        current_rates = self.get_current_rates()
        
        for pair, rate in current_rates.items():
            if pair in thresholds:
                threshold_config = thresholds[pair]
                
                if 'high' in threshold_config and rate > threshold_config['high']:
                    alerts.append({
                        'pair': pair,
                        'current_rate': rate,
                        'threshold': threshold_config['high'],
                        'type': 'HIGH',
                        'message': f'{pair} rate {rate} exceeded high threshold {threshold_config["high"]}'
                    })
                
                if 'low' in threshold_config and rate < threshold_config['low']:
                    alerts.append({
                        'pair': pair,
                        'current_rate': rate,
                        'threshold': threshold_config['low'],
                        'type': 'LOW',
                        'message': f'{pair} rate {rate} below low threshold {threshold_config["low"]}'
                    })
        
        return alerts
    
    def get_volatility_analysis(self) -> Dict[str, Any]:
        """Analyze exchange rate volatility"""
        historical_data = self.get_historical_rates(30)
        
        if historical_data.empty:
            return {}
        
        analysis = {}
        
        for pair in self.base_rates.keys():
            rate_col = f'{pair}_rate'
            if rate_col in historical_data.columns:
                rates = historical_data[rate_col].dropna()
                
                if len(rates) > 1:
                    # Calculate volatility metrics
                    returns = rates.pct_change().dropna()
                    
                    analysis[pair] = {
                        'current_rate': rates.iloc[-1],
                        'min_rate': rates.min(),
                        'max_rate': rates.max(),
                        'avg_rate': rates.mean(),
                        'volatility': returns.std() * np.sqrt(252),  # Annualized
                        'daily_change': (rates.iloc[-1] - rates.iloc[-2]) / rates.iloc[-2] if len(rates) > 1 else 0,
                        'weekly_change': (rates.iloc[-1] - rates.iloc[-7]) / rates.iloc[-7] if len(rates) > 7 else 0,
                        'monthly_change': (rates.iloc[-1] - rates.iloc[0]) / rates.iloc[0]
                    }
        
        return analysis
