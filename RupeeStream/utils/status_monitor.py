import psutil
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st
import random
import threading

from utils.db_manager import DatabaseManager
from config import Config

class StatusMonitor:
    """System status monitoring and health checks"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        self.last_check_time = None
        self.cached_status = {}
        self.alerts = []
        
        # Service endpoints to monitor
        self.monitored_services = {
            'database': self._check_database_health,
            'encryption': self._check_encryption_service,
            'api_services': self._check_api_services,
            'exchange_rates': self._check_exchange_rate_service,
            'file_system': self._check_file_system
        }
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 85.0,
            'disk_critical': 95.0,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        
        # Check if we need to refresh status (cache for 30 seconds)
        current_time = datetime.now()
        if (self.last_check_time is None or 
            (current_time - self.last_check_time).seconds > 30):
            
            self.cached_status = self._perform_health_checks()
            self.last_check_time = current_time
        
        return self.cached_status
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform all health checks"""
        
        status = {
            'overall_status': 'healthy',
            'last_updated': datetime.now(),
            'uptime': self._get_uptime(),
            'services': {},
            'alerts': []
        }
        
        # Check each monitored service
        for service_name, check_function in self.monitored_services.items():
            try:
                service_status = check_function()
                status['services'][service_name] = service_status
                
                # Update overall status if any service is down
                if not service_status.get('healthy', False):
                    status['overall_status'] = 'degraded'
                    
                    # Create alert for unhealthy service
                    alert = {
                        'timestamp': datetime.now(),
                        'severity': 'high' if service_status.get('critical', False) else 'medium',
                        'service': service_name,
                        'message': f"{service_name} service is {service_status.get('status', 'unknown')}",
                        'details': service_status.get('error_message', '')
                    }
                    status['alerts'].append(alert)
                    
            except Exception as e:
                status['services'][service_name] = {
                    'healthy': False,
                    'status': 'error',
                    'error_message': str(e),
                    'last_checked': datetime.now()
                }
                status['overall_status'] = 'degraded'
        
        # Store status in database
        self._store_system_status(status)
        
        return status
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        
        start_time = time.time()
        
        try:
            # Test database connection
            conn = self.db.get_connection()
            if not conn:
                return {
                    'healthy': False,
                    'status': 'connection_failed',
                    'error_message': 'Unable to establish database connection',
                    'response_time': None,
                    'last_checked': datetime.now()
                }
            
            # Test database operations
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            response_time = time.time() - start_time
            conn.close()
            
            # Check if response time is within acceptable limits
            is_healthy = response_time < self.thresholds['response_time_critical']
            status = 'healthy' if is_healthy else 'slow'
            
            return {
                'healthy': is_healthy,
                'status': status,
                'response_time': response_time,
                'last_checked': datetime.now(),
                'details': {
                    'connection_successful': True,
                    'query_successful': result is not None
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error_message': str(e),
                'response_time': time.time() - start_time,
                'last_checked': datetime.now()
            }
    
    def _check_encryption_service(self) -> Dict[str, Any]:
        """Check encryption service functionality"""
        
        start_time = time.time()
        
        try:
            from utils.encryption import encrypt_data, decrypt_data, generate_key
            
            # Test encryption/decryption
            test_data = "test_encryption_service"
            test_key = generate_key()
            
            encrypted = encrypt_data(test_data, test_key)
            if not encrypted:
                return {
                    'healthy': False,
                    'status': 'encryption_failed',
                    'error_message': 'Encryption operation failed',
                    'last_checked': datetime.now()
                }
            
            decrypted = decrypt_data(encrypted, test_key)
            if decrypted != test_data:
                return {
                    'healthy': False,
                    'status': 'decryption_failed',
                    'error_message': 'Decryption operation failed',
                    'last_checked': datetime.now()
                }
            
            response_time = time.time() - start_time
            
            return {
                'healthy': True,
                'status': 'operational',
                'response_time': response_time,
                'last_checked': datetime.now(),
                'details': {
                    'encryption_test': 'passed',
                    'decryption_test': 'passed'
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error_message': str(e),
                'response_time': time.time() - start_time,
                'last_checked': datetime.now()
            }
    
    def _check_api_services(self) -> Dict[str, Any]:
        """Check API services health"""
        
        # Since we're using internal services, we'll check core functionality
        start_time = time.time()
        
        try:
            from api.transaction_processor import TransactionProcessor
            from api.srva_manager import SRVAManager
            
            # Test transaction processor
            processor = TransactionProcessor()
            test_transaction = {
                'amount': 1000.0,
                'currency': 'INR',
                'source': 'UPI',
                'corridor': 'IN-US',
                'counterparty': 'test',
                'narrative': 'health check'
            }
            
            # This would normally process, but we'll just validate
            validation = processor._validate_transaction(test_transaction)
            
            if not validation['valid']:
                return {
                    'healthy': False,
                    'status': 'validation_failed',
                    'error_message': validation['message'],
                    'last_checked': datetime.now()
                }
            
            response_time = time.time() - start_time
            
            return {
                'healthy': True,
                'status': 'operational',
                'response_time': response_time,
                'last_checked': datetime.now(),
                'details': {
                    'transaction_processor': 'operational',
                    'srva_manager': 'operational'
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error_message': str(e),
                'response_time': time.time() - start_time,
                'last_checked': datetime.now()
            }
    
    def _check_exchange_rate_service(self) -> Dict[str, Any]:
        """Check exchange rate service"""
        
        start_time = time.time()
        
        try:
            from api.exchange_rates import ExchangeRateManager
            
            rate_manager = ExchangeRateManager()
            current_rates = rate_manager.get_current_rates()
            
            if not current_rates:
                return {
                    'healthy': False,
                    'status': 'no_rates_available',
                    'error_message': 'Unable to fetch exchange rates',
                    'last_checked': datetime.now()
                }
            
            # Check if rates are reasonable (basic sanity check)
            usd_rate = current_rates.get('USDINR', 0)
            if usd_rate < 70 or usd_rate > 100:
                return {
                    'healthy': False,
                    'status': 'unrealistic_rates',
                    'error_message': f'USD/INR rate {usd_rate} seems unrealistic',
                    'last_checked': datetime.now()
                }
            
            response_time = time.time() - start_time
            
            return {
                'healthy': True,
                'status': 'operational',
                'response_time': response_time,
                'last_checked': datetime.now(),
                'details': {
                    'rates_available': len(current_rates),
                    'usd_inr_rate': usd_rate
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error_message': str(e),
                'response_time': time.time() - start_time,
                'last_checked': datetime.now()
            }
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system health"""
        
        try:
            import os
            
            # Check if we can write to the application directory
            test_file = 'health_check_test.tmp'
            
            try:
                with open(test_file, 'w') as f:
                    f.write('health check')
                
                # Read it back
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Clean up
                os.remove(test_file)
                
                if content != 'health check':
                    return {
                        'healthy': False,
                        'status': 'read_write_failed',
                        'error_message': 'File read/write test failed',
                        'last_checked': datetime.now()
                    }
                
            except PermissionError:
                return {
                    'healthy': False,
                    'status': 'permission_denied',
                    'error_message': 'No write permission to application directory',
                    'last_checked': datetime.now()
                }
            
            return {
                'healthy': True,
                'status': 'operational',
                'last_checked': datetime.now(),
                'details': {
                    'read_write_test': 'passed'
                }
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'status': 'error',
                'error_message': str(e),
                'last_checked': datetime.now()
            }
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage"""
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Process information
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'process_memory_mb': process_memory,
                'total_memory_gb': memory.total / 1024 / 1024 / 1024,
                'available_memory_gb': memory.available / 1024 / 1024 / 1024,
                'disk_total_gb': disk.total / 1024 / 1024 / 1024,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            # Return simulated data if psutil fails
            return {
                'cpu_percent': random.uniform(20, 60),
                'memory_percent': random.uniform(40, 80),
                'disk_percent': random.uniform(30, 70),
                'process_memory_mb': random.uniform(100, 500),
                'total_memory_gb': 8.0,
                'available_memory_gb': 4.0,
                'disk_total_gb': 100.0,
                'disk_free_gb': 60.0,
                'last_updated': datetime.now(),
                'simulated': True,
                'error': str(e)
            }
    
    def get_performance_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance history"""
        
        # In a real implementation, this would query historical data
        # For demo purposes, we'll return some sample data
        
        history = []
        current_time = datetime.now()
        
        for i in range(hours):
            timestamp = current_time - timedelta(hours=i)
            
            # Generate realistic performance data
            base_tps = 2.5
            tps_variation = random.uniform(-0.5, 0.5)
            tps = max(0, base_tps + tps_variation)
            
            base_response_time = 0.5
            response_variation = random.uniform(-0.2, 0.3)
            response_time = max(0.1, base_response_time + response_variation)
            
            history.append({
                'timestamp': timestamp,
                'tps': round(tps, 2),
                'avg_response_time': round(response_time, 3),
                'cpu_usage': random.uniform(20, 70),
                'memory_usage': random.uniform(40, 80)
            })
        
        return sorted(history, key=lambda x: x['timestamp'])
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        
        # Get recent alerts from database or session state
        active_alerts = st.session_state.get('active_alerts', [])
        
        # Filter to only recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_alerts = [
            alert for alert in active_alerts
            if alert.get('timestamp', datetime.now()) > cutoff_time
        ]
        
        # Add some system-generated alerts based on current status
        system_status = self.get_system_status()
        resource_usage = self.get_resource_usage()
        
        # Check for resource alerts
        if resource_usage['cpu_percent'] > self.thresholds['cpu_warning']:
            severity = 'high' if resource_usage['cpu_percent'] > self.thresholds['cpu_critical'] else 'medium'
            recent_alerts.append({
                'timestamp': datetime.now(),
                'severity': severity,
                'message': f"High CPU usage: {resource_usage['cpu_percent']:.1f}%",
                'source': 'system_monitor',
                'type': 'resource_alert'
            })
        
        if resource_usage['memory_percent'] > self.thresholds['memory_warning']:
            severity = 'high' if resource_usage['memory_percent'] > self.thresholds['memory_critical'] else 'medium'
            recent_alerts.append({
                'timestamp': datetime.now(),
                'severity': severity,
                'message': f"High memory usage: {resource_usage['memory_percent']:.1f}%",
                'source': 'system_monitor',
                'type': 'resource_alert'
            })
        
        return recent_alerts[-10:]  # Return last 10 alerts
    
    def get_incident_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get incident history"""
        
        # This would typically come from a database
        # For demo purposes, generate some sample incidents
        
        incidents = []
        current_time = datetime.now()
        
        # Sample incidents
        sample_incidents = [
            {
                'type': 'service_outage',
                'severity': 'high',
                'title': 'Database Connection Timeout',
                'description': 'Database service experienced connection timeouts',
                'duration_minutes': 15,
                'resolved': True
            },
            {
                'type': 'performance_degradation',
                'severity': 'medium',
                'title': 'Slow Response Times',
                'description': 'API response times exceeded normal thresholds',
                'duration_minutes': 45,
                'resolved': True
            },
            {
                'type': 'resource_limit',
                'severity': 'low',
                'title': 'High Memory Usage',
                'description': 'Memory usage reached warning threshold',
                'duration_minutes': 120,
                'resolved': True
            }
        ]
        
        for i, incident in enumerate(sample_incidents):
            incident_time = current_time - timedelta(days=i+1, hours=random.randint(1, 23))
            incident['timestamp'] = incident_time
            incident['resolved_at'] = incident_time + timedelta(minutes=incident['duration_minutes'])
            incident['id'] = f"INC-{incident_time.strftime('%Y%m%d')}-{i+1:03d}"
            incidents.append(incident)
        
        return incidents
    
    def create_alert(self, message: str, severity: str = 'medium', 
                    alert_type: str = 'manual') -> bool:
        """Create a new alert"""
        
        try:
            alert = {
                'timestamp': datetime.now(),
                'severity': severity,
                'message': message,
                'source': 'manual',
                'type': alert_type,
                'id': f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Add to session state
            if 'active_alerts' not in st.session_state:
                st.session_state.active_alerts = []
            
            st.session_state.active_alerts.append(alert)
            
            # Store in database
            self.db.insert_audit_log({
                'entity_type': 'ALERT',
                'entity_id': alert['id'],
                'action': 'CREATED',
                'details': f"Alert created: {message}",
                'user_role': st.session_state.get('user_role', 'system')
            })
            
            return True
            
        except Exception as e:
            st.error(f"Failed to create alert: {str(e)}")
            return False
    
    def _get_uptime(self) -> str:
        """Get system uptime"""
        
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return f"{days}d {hours}h {minutes}m"
            
        except:
            # Fallback for systems where psutil doesn't work
            return "Unknown"
    
    def _store_system_status(self, status: Dict[str, Any]):
        """Store system status in database"""
        
        try:
            status_record = {
                'service_name': 'system_overall',
                'status': status['overall_status'],
                'response_time': None,
                'error_message': None,
                'metrics': json.dumps({
                    'services_count': len(status['services']),
                    'healthy_services': sum(1 for s in status['services'].values() if s.get('healthy', False)),
                    'alerts_count': len(status['alerts'])
                })
            }
            
            self.db.insert_system_status(status_record)
            
            # Store individual service statuses
            for service_name, service_status in status['services'].items():
                service_record = {
                    'service_name': service_name,
                    'status': service_status.get('status', 'unknown'),
                    'response_time': service_status.get('response_time'),
                    'error_message': service_status.get('error_message'),
                    'metrics': json.dumps(service_status.get('details', {}))
                }
                
                self.db.insert_system_status(service_record)
                
        except Exception as e:
            # Don't fail the health check if we can't store the status
            pass
    
    def run_background_monitoring(self):
        """Run background monitoring (would be used in production)"""
        
        def monitoring_loop():
            while True:
                try:
                    # Perform health checks
                    self.get_system_status()
                    
                    # Check resource usage
                    resources = self.get_resource_usage()
                    
                    # Generate alerts if thresholds are exceeded
                    if resources['cpu_percent'] > self.thresholds['cpu_critical']:
                        self.create_alert(
                            f"Critical CPU usage: {resources['cpu_percent']:.1f}%",
                            severity='high',
                            alert_type='system_monitor'
                        )
                    
                    if resources['memory_percent'] > self.thresholds['memory_critical']:
                        self.create_alert(
                            f"Critical memory usage: {resources['memory_percent']:.1f}%",
                            severity='high',
                            alert_type='system_monitor'
                        )
                    
                    # Sleep for monitoring interval
                    time.sleep(self.config.HEALTH_CHECK_INTERVAL)
                    
                except Exception as e:
                    st.error(f"Background monitoring error: {str(e)}")
                    time.sleep(60)  # Wait a minute before retrying
        
        # Start monitoring in background thread
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
