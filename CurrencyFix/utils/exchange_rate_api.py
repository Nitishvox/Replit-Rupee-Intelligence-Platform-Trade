import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class ExchangeRateAPI:
    """
    Modern Exchange Rate API using free, reliable providers without authentication
    Primary: Fawaz Ahmed's Currency API (via jsDelivr CDN)
    Secondary: ExchangeRate.host
    Tertiary: ExchangeRate-API open access
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        self.last_update = None
        
        # Free API endpoints (no authentication required)
        self.providers = {
            'fawaz': {
                'name': 'Fawaz Ahmed Currency API',
                'base_url': 'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies',
                'active': True,
                'description': 'Free CDN-hosted API with daily updates'
            },
            'exchangerate_host': {
                'name': 'ExchangeRate.host',
                'base_url': 'https://api.exchangerate.host',
                'active': True,
                'description': 'Professional free API with high reliability'
            },
            'exchangerate_api_open': {
                'name': 'ExchangeRate-API Open',
                'base_url': 'https://api.exchangerate-api.com/v4/latest',
                'active': True,
                'description': 'Open access tier, no signup required'
            }
        }
        
        # Supported currencies for SRVA operations
        self.supported_currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY', 
            'RUB', 'SGD', 'HKD', 'KRW', 'THB', 'MYR', 'PHP', 'IDR',
            'VND', 'AED', 'SAR', 'EGP', 'ZAR', 'BRL', 'MXN', 'TRY'
        ]
        
        # Enhanced fallback rates (updated as of August 2025)
        self.fallback_rates = {
            'USD': 83.12, 'EUR': 90.45, 'GBP': 105.78, 'JPY': 0.57,
            'AUD': 54.92, 'CAD': 61.33, 'CHF': 92.67, 'CNY': 11.58,
            'RUB': 0.91, 'SGD': 61.89, 'HKD': 10.62, 'KRW': 0.064,
            'THB': 2.38, 'MYR': 18.82, 'PHP': 1.49, 'IDR': 0.0056,
            'VND': 0.0035, 'AED': 22.62, 'SAR': 22.17, 'EGP': 1.72,
            'ZAR': 4.58, 'BRL': 15.31, 'MXN': 4.89, 'TRY': 2.78
        }

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.last_update:
            return False
        return (datetime.now() - self.last_update).seconds < self.cache_duration

    def _fetch_from_fawaz_api(self) -> Optional[Dict]:
        """Fetch rates from Fawaz Ahmed's Currency API (Primary Provider)"""
        try:
            # Use INR as base currency
            url = f"{self.providers['fawaz']['base_url']}/inr.json"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            inr_rates = data.get('inr', {})
            
            # Convert to standard format (foreign currency per 1 INR)
            rates = {}
            for currency, rate in inr_rates.items():
                currency_upper = currency.upper()
                if currency_upper in self.supported_currencies and rate > 0:
                    rates[currency_upper] = float(rate)
                    
            return rates
            
        except requests.exceptions.Timeout:
            print("Fawaz API timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Fawaz API request error: {str(e)}")
            return None
        except Exception as e:
            print(f"Fawaz API processing error: {str(e)}")
            return None

    def _fetch_from_exchangerate_host(self) -> Optional[Dict]:
        """Fetch rates from ExchangeRate.host (Secondary Provider)"""
        try:
            url = f"{self.providers['exchangerate_host']['base_url']}/latest"
            params = {
                'base': 'INR',
                'symbols': ','.join(self.supported_currencies),
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success', False) and 'rates' in data:
                rates = {}
                for currency, rate in data['rates'].items():
                    if currency in self.supported_currencies and rate > 0:
                        rates[currency] = float(rate)
                return rates
            else:
                return None
                
        except requests.exceptions.Timeout:
            print("ExchangeRate.host timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"ExchangeRate.host request error: {str(e)}")
            return None
        except Exception as e:
            print(f"ExchangeRate.host processing error: {str(e)}")
            return None

    def _fetch_from_exchangerate_api_open(self) -> Optional[Dict]:
        """Fetch rates from ExchangeRate-API open access (Tertiary Provider)"""
        try:
            url = f"{self.providers['exchangerate_api_open']['base_url']}/INR"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'rates' in data:
                rates = {}
                for currency, rate in data['rates'].items():
                    if currency in self.supported_currencies and rate > 0:
                        rates[currency] = float(rate)
                return rates
            else:
                return None
            
        except requests.exceptions.Timeout:
            print("ExchangeRate-API open timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"ExchangeRate-API open request error: {str(e)}")
            return None
        except Exception as e:
            print(f"ExchangeRate-API open processing error: {str(e)}")
            return None

    def get_current_rates(self) -> Dict[str, float]:
        """
        Get current exchange rates with robust fallback system
        Returns rates as foreign currency per 1 INR
        """
        # Return cached data if valid
        if self._is_cache_valid() and self.cache:
            return self.cache
        
        # Try primary provider (Fawaz API)
        print("Fetching rates from Fawaz Ahmed's Currency API...")
        rates = self._fetch_from_fawaz_api()
        if rates and len(rates) >= 5:  # Ensure we got meaningful data
            self.cache = rates
            self.last_update = datetime.now()
            print(f"✅ Successfully fetched {len(rates)} rates from Fawaz API")
            return rates
        
        # Try secondary provider (ExchangeRate.host)
        print("Trying ExchangeRate.host...")
        rates = self._fetch_from_exchangerate_host()
        if rates and len(rates) >= 5:
            self.cache = rates
            self.last_update = datetime.now()
            print(f"✅ Successfully fetched {len(rates)} rates from ExchangeRate.host")
            return rates
        
        # Try tertiary provider (ExchangeRate-API open)
        print("Trying ExchangeRate-API open access...")
        rates = self._fetch_from_exchangerate_api_open()
        if rates and len(rates) >= 5:
            self.cache = rates
            self.last_update = datetime.now()
            print(f"✅ Successfully fetched {len(rates)} rates from ExchangeRate-API")
            return rates
        
        # All providers failed, use fallback rates
        print("⚠️ All exchange rate providers unavailable, using fallback rates")
        self.cache = self.fallback_rates.copy()
        self.last_update = datetime.now()
        return self.fallback_rates

    def get_rate(self, from_currency: str, to_currency: str = 'INR') -> float:
        """Get specific exchange rate between two currencies"""
        rates = self.get_current_rates()
        
        if to_currency == 'INR':
            # Direct conversion from foreign currency to INR
            rate = rates.get(from_currency)
            if rate:
                return 1 / rate  # Convert to INR per foreign currency
            else:
                fallback_rate = self.fallback_rates.get(from_currency, 1.0)
                return fallback_rate
        
        elif from_currency == 'INR':
            # Direct conversion from INR to foreign currency
            return rates.get(to_currency, self.fallback_rates.get(to_currency, 1.0))
        
        else:
            # Cross currency conversion through INR
            from_to_inr_rate = rates.get(from_currency)
            to_to_inr_rate = rates.get(to_currency)
            
            if from_to_inr_rate and to_to_inr_rate:
                # Convert via INR: from -> INR -> to
                return to_to_inr_rate / from_to_inr_rate
            else:
                # Use fallback rates
                from_fallback = self.fallback_rates.get(from_currency, 1.0)
                to_fallback = self.fallback_rates.get(to_currency, 1.0)
                return to_fallback / from_fallback if from_fallback != 0 else 1.0

    def convert_amount(self, amount: float, from_currency: str, to_currency: str = 'INR') -> float:
        """Convert amount between currencies"""
        rate = self.get_rate(from_currency, to_currency)
        return amount * rate

    def get_historical_rates(self, date: datetime, currencies: List[str] = None) -> Dict[str, float]:
        """Get historical rates for a specific date (Fawaz API supports this)"""
        if currencies is None:
            currencies = self.supported_currencies
        
        try:
            date_str = date.strftime('%Y-%m-%d')
            url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date_str}/v1/currencies/inr.json"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            inr_rates = data.get('inr', {})
            
            rates = {}
            for currency in currencies:
                currency_lower = currency.lower()
                if currency_lower in inr_rates:
                    rate = inr_rates[currency_lower]
                    if rate > 0:
                        rates[currency] = float(rate)
            
            return rates
            
        except Exception as e:
            print(f"Historical rates error for {date_str}: {str(e)}")
            # Return current rates as fallback
            current_rates = self.get_current_rates()
            return {curr: current_rates.get(curr, self.fallback_rates.get(curr, 1.0)) for curr in currencies}

    def get_rate_trend(self, currency: str, days: int = 30) -> List[Dict]:
        """Get rate trend for a currency over specified days"""
        trend_data = []
        
        for i in range(min(days, 90)):  # Limit to 90 days for performance
            date = datetime.now() - timedelta(days=i)
            
            try:
                historical_rates = self.get_historical_rates(date, [currency])
                rate = historical_rates.get(currency, self.fallback_rates.get(currency, 1.0))
                
                trend_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'rate': rate,
                    'currency': currency
                })
            except Exception as e:
                # Use fallback rate for missing data
                rate = self.fallback_rates.get(currency, 1.0)
                trend_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'rate': rate,
                    'currency': currency
                })
        
        return list(reversed(trend_data))  # Return chronological order

    def validate_currency(self, currency: str) -> bool:
        """Validate if currency is supported"""
        return currency.upper() in self.supported_currencies

    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        return self.supported_currencies.copy()

    def get_provider_status(self) -> Dict:
        """Get real-time status of all providers"""
        status = {}
        
        for provider_key, provider_info in self.providers.items():
            try:
                start_time = time.time()
                
                if provider_key == 'fawaz':
                    test_result = self._fetch_from_fawaz_api()
                elif provider_key == 'exchangerate_host':
                    test_result = self._fetch_from_exchangerate_host()
                elif provider_key == 'exchangerate_api_open':
                    test_result = self._fetch_from_exchangerate_api_open()
                
                response_time = round((time.time() - start_time) * 1000, 2)  # ms
                
                status[provider_info['name']] = {
                    'status': 'Online' if test_result and len(test_result) >= 5 else 'Limited',
                    'response_time_ms': response_time,
                    'currencies_available': len(test_result) if test_result else 0,
                    'last_check': datetime.now().isoformat(),
                    'description': provider_info['description']
                }
                
            except Exception as e:
                status[provider_info['name']] = {
                    'status': 'Offline',
                    'response_time_ms': None,
                    'currencies_available': 0,
                    'last_check': datetime.now().isoformat(),
                    'error': str(e),
                    'description': provider_info['description']
                }
        
        return status

    def get_api_info(self) -> Dict:
        """Get information about the API configuration"""
        return {
            'providers': len(self.providers),
            'supported_currencies': len(self.supported_currencies),
            'cache_duration_hours': self.cache_duration / 3600,
            'last_successful_update': self.last_update.isoformat() if self.last_update else None,
            'cached_rates_count': len(self.cache),
            'fallback_rates_available': len(self.fallback_rates)
        }

    def clear_cache(self):
        """Clear the cache to force fresh data retrieval"""
        self.cache.clear()
        self.last_update = None
        print("✅ Exchange rate cache cleared")

    def get_cache_info(self) -> Dict:
        """Get cache information"""
        if not self.last_update:
            return {'status': 'empty', 'last_update': None, 'age_minutes': None}
        
        age_minutes = (datetime.now() - self.last_update).total_seconds() / 60
        
        return {
            'status': 'valid' if self._is_cache_valid() else 'expired',
            'last_update': self.last_update.isoformat(),
            'age_minutes': round(age_minutes, 2),
            'cached_currencies': len(self.cache)
        }
