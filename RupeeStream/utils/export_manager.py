import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from io import StringIO, BytesIO
import streamlit as st

from utils.db_manager import DatabaseManager
from utils.encryption import decrypt_data
from config import Config

class ExportManager:
    """Manager for RBI-compliant exports and custom reports"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager()
        
        # RBI export schemas
        self.rbi_schemas = {
            'transaction_export': {
                'required_fields': [
                    'transaction_id', 'amount', 'currency', 'timestamp',
                    'source', 'corridor', 'status', 'risk_score'
                ],
                'optional_fields': [
                    'counterparty', 'reference', 'fees', 'processing_time'
                ]
            },
            'settlement_export': {
                'required_fields': [
                    'settlement_id', 'settlement_date', 'total_amount',
                    'status', 'currency_breakdown'
                ],
                'optional_fields': [
                    'transaction_count', 'corridors_involved'
                ]
            }
        }
    
    def generate_rbi_export(self, transactions: List[Dict[str, Any]], 
                           format: str = 'XML',
                           include_encrypted: bool = False,
                           validate_schema: bool = True,
                           date_range: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate RBI-compliant export file"""
        
        try:
            # Filter transactions by date range if provided
            if date_range and len(date_range) == 2:
                start_date = pd.to_datetime(date_range[0])
                end_date = pd.to_datetime(date_range[1])
                
                filtered_transactions = []
                for txn in transactions:
                    txn_date = pd.to_datetime(txn.get('timestamp', datetime.now()))
                    if start_date <= txn_date <= end_date:
                        filtered_transactions.append(txn)
                
                transactions = filtered_transactions
            
            if not transactions:
                return {
                    'success': False,
                    'message': 'No transactions found for the specified criteria'
                }
            
            # Prepare data for export
            export_data = self._prepare_export_data(transactions, include_encrypted)
            
            # Validate schema if required
            if validate_schema:
                validation_result = self._validate_export_schema(export_data, 'transaction_export')
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'message': f'Schema validation failed: {validation_result["message"]}'
                    }
            
            # Generate export based on format
            if format.upper() == 'XML':
                export_content = self._generate_xml_export(export_data)
            elif format.upper() == 'CSV':
                export_content = self._generate_csv_export(export_data)
            elif format.upper() == 'JSON':
                export_content = self._generate_json_export(export_data)
            else:
                return {
                    'success': False,
                    'message': f'Unsupported export format: {format}'
                }
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            return {
                'success': True,
                'data': export_content,
                'timestamp': timestamp,
                'format': format,
                'record_count': len(transactions),
                'message': f'Export generated successfully with {len(transactions)} records'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Export generation failed: {str(e)}'
            }
    
    def _prepare_export_data(self, transactions: List[Dict[str, Any]], 
                           include_encrypted: bool) -> List[Dict[str, Any]]:
        """Prepare transaction data for export"""
        
        export_records = []
        encryption_key = st.session_state.get('encryption_key')
        
        for txn in transactions:
            record = {}
            
            # Copy basic fields
            for field in self.rbi_schemas['transaction_export']['required_fields']:
                if field == 'transaction_id':
                    record[field] = txn.get('id', '')
                else:
                    record[field] = txn.get(field, '')
            
            # Copy optional fields
            for field in self.rbi_schemas['transaction_export']['optional_fields']:
                record[field] = txn.get(field, '')
            
            # Handle encrypted fields
            if include_encrypted and encryption_key:
                # Decrypt sensitive fields for export
                encrypted_counterparty = txn.get('encrypted_counterparty')
                if encrypted_counterparty:
                    decrypted = decrypt_data(encrypted_counterparty, encryption_key)
                    if not decrypted.startswith('Decryption Failed'):
                        record['counterparty'] = decrypted
                
                encrypted_narrative = txn.get('encrypted_narrative')
                if encrypted_narrative:
                    decrypted = decrypt_data(encrypted_narrative, encryption_key)
                    if not decrypted.startswith('Decryption Failed'):
                        record['narrative'] = decrypted
            
            # Format timestamp for RBI compliance
            if 'timestamp' in record:
                timestamp = pd.to_datetime(record['timestamp'])
                record['timestamp'] = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Add compliance fields
            record['export_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            record['rbi_compliance_version'] = '2024.1'
            record['data_classification'] = 'RESTRICTED'
            
            export_records.append(record)
        
        return export_records
    
    def _validate_export_schema(self, data: List[Dict[str, Any]], 
                               schema_name: str) -> Dict[str, Any]:
        """Validate export data against RBI schema"""
        
        if schema_name not in self.rbi_schemas:
            return {'valid': False, 'message': f'Unknown schema: {schema_name}'}
        
        schema = self.rbi_schemas[schema_name]
        required_fields = schema['required_fields']
        
        if not data:
            return {'valid': False, 'message': 'No data to validate'}
        
        # Check required fields in first record
        first_record = data[0]
        missing_fields = []
        
        for field in required_fields:
            mapped_field = 'transaction_id' if field == 'transaction_id' else field
            if mapped_field not in first_record or not first_record[mapped_field]:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                'valid': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }
        
        # Validate data types and formats
        validation_errors = []
        
        for i, record in enumerate(data[:10]):  # Check first 10 records
            # Amount validation
            if 'amount' in record:
                try:
                    amount = float(record['amount'])
                    if amount < 0:
                        validation_errors.append(f'Record {i+1}: Negative amount not allowed')
                except (ValueError, TypeError):
                    validation_errors.append(f'Record {i+1}: Invalid amount format')
            
            # Currency validation
            if 'currency' in record:
                valid_currencies = ['INR', 'USD', 'EUR', 'GBP', 'SGD', 'RUB', 'AED', 'JPY']
                if record['currency'] not in valid_currencies:
                    validation_errors.append(f'Record {i+1}: Invalid currency code')
            
            # Timestamp validation
            if 'timestamp' in record:
                try:
                    pd.to_datetime(record['timestamp'])
                except:
                    validation_errors.append(f'Record {i+1}: Invalid timestamp format')
        
        if validation_errors:
            return {
                'valid': False,
                'message': f'Validation errors: {"; ".join(validation_errors[:5])}'
            }
        
        return {'valid': True, 'message': 'Schema validation passed'}
    
    def _generate_xml_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate XML export file"""
        
        # Create root element
        root = ET.Element('RBI_Transaction_Export')
        root.set('version', '2024.1')
        root.set('generated_at', datetime.now().isoformat())
        root.set('record_count', str(len(data)))
        
        # Add metadata
        metadata = ET.SubElement(root, 'Metadata')
        ET.SubElement(metadata, 'ExportingEntity').text = 'RIPT Platform'
        ET.SubElement(metadata, 'ComplianceVersion').text = 'RBI_FEMA_2024'
        ET.SubElement(metadata, 'DataClassification').text = 'RESTRICTED'
        ET.SubElement(metadata, 'RetentionPeriod').text = '7_YEARS'
        
        # Add transactions
        transactions_elem = ET.SubElement(root, 'Transactions')
        
        for record in data:
            txn_elem = ET.SubElement(transactions_elem, 'Transaction')
            
            for key, value in record.items():
                if value is not None and value != '':
                    elem = ET.SubElement(txn_elem, key)
                    elem.text = str(value)
        
        # Pretty print XML
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _generate_csv_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate CSV export file"""
        
        if not data:
            return ''
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Add export metadata as header comments
        output = StringIO()
        output.write(f"# RBI Transaction Export\n")
        output.write(f"# Generated: {datetime.now().isoformat()}\n")
        output.write(f"# Records: {len(data)}\n")
        output.write(f"# Compliance: RBI_FEMA_2024\n")
        output.write(f"# Classification: RESTRICTED\n")
        output.write(f"#\n")
        
        # Write CSV data
        df.to_csv(output, index=False, quoting=csv.QUOTE_ALL)
        
        return output.getvalue()
    
    def _generate_json_export(self, data: List[Dict[str, Any]]) -> str:
        """Generate JSON export file"""
        
        export_structure = {
            'metadata': {
                'exporting_entity': 'RIPT Platform',
                'generated_at': datetime.now().isoformat(),
                'compliance_version': 'RBI_FEMA_2024',
                'data_classification': 'RESTRICTED',
                'record_count': len(data)
            },
            'transactions': data
        }
        
        return json.dumps(export_structure, indent=2, default=str)
    
    def generate_custom_report(self, transactions: List[Dict[str, Any]], 
                             report_type: str) -> Dict[str, Any]:
        """Generate custom reports"""
        
        try:
            if report_type == "Transaction Summary":
                return self._generate_transaction_summary_report(transactions)
            elif report_type == "Risk Analysis":
                return self._generate_risk_analysis_report(transactions)
            elif report_type == "Volume Analysis":
                return self._generate_volume_analysis_report(transactions)
            elif report_type == "Privacy Compliance":
                return self._generate_privacy_compliance_report(transactions)
            elif report_type == "Performance Metrics":
                return self._generate_performance_metrics_report()
            else:
                return {
                    'success': False,
                    'message': f'Unknown report type: {report_type}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Report generation failed: {str(e)}'
            }
    
    def _generate_transaction_summary_report(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate transaction summary report"""
        
        if not transactions:
            return {
                'success': False,
                'message': 'No transaction data available'
            }
        
        df = pd.DataFrame(transactions)
        
        # Summary statistics
        summary = {
            'total_transactions': len(df),
            'total_volume': df['amount'].sum(),
            'average_amount': df['amount'].mean(),
            'median_amount': df['amount'].median(),
            'max_amount': df['amount'].max(),
            'min_amount': df['amount'].min()
        }
        
        # Breakdown by various dimensions
        breakdown = {
            'by_currency': df['currency'].value_counts().to_dict(),
            'by_source': df['source'].value_counts().to_dict(),
            'by_corridor': df['corridor'].value_counts().to_dict(),
            'by_status': df['status'].value_counts().to_dict()
        }
        
        # Volume analysis
        volume_analysis = {
            'by_currency': df.groupby('currency')['amount'].sum().to_dict(),
            'by_corridor': df.groupby('corridor')['amount'].sum().to_dict(),
            'by_source': df.groupby('source')['amount'].sum().to_dict()
        }
        
        # Generate report content
        report_content = f"""
TRANSACTION SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
========
Total Transactions: {summary['total_transactions']:,}
Total Volume: ₹{summary['total_volume']:,.2f}
Average Amount: ₹{summary['average_amount']:,.2f}
Median Amount: ₹{summary['median_amount']:,.2f}
Largest Transaction: ₹{summary['max_amount']:,.2f}
Smallest Transaction: ₹{summary['min_amount']:,.2f}

BREAKDOWN BY CURRENCY
=====================
"""
        
        for currency, count in breakdown['by_currency'].items():
            volume = volume_analysis['by_currency'].get(currency, 0)
            report_content += f"{currency}: {count:,} transactions, ₹{volume:,.2f}\n"
        
        report_content += f"""
BREAKDOWN BY CORRIDOR
=====================
"""
        
        for corridor, count in breakdown['by_corridor'].items():
            volume = volume_analysis['by_corridor'].get(corridor, 0)
            report_content += f"{corridor}: {count:,} transactions, ₹{volume:,.2f}\n"
        
        return {
            'success': True,
            'data': report_content.encode('utf-8'),
            'preview': report_content[:500] + "..." if len(report_content) > 500 else report_content,
            'summary': summary,
            'breakdown': breakdown
        }
    
    def _generate_risk_analysis_report(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate risk analysis report"""
        
        if not transactions:
            return {
                'success': False,
                'message': 'No transaction data available for risk analysis'
            }
        
        df = pd.DataFrame(transactions)
        
        # Risk statistics
        risk_stats = {
            'avg_risk_score': df['risk_score'].mean(),
            'max_risk_score': df['risk_score'].max(),
            'min_risk_score': df['risk_score'].min(),
            'high_risk_count': len(df[df['risk_score'] > 75]),
            'medium_risk_count': len(df[(df['risk_score'] > 50) & (df['risk_score'] <= 75)]),
            'low_risk_count': len(df[df['risk_score'] <= 50])
        }
        
        # Risk by various dimensions
        risk_by_source = df.groupby('source')['risk_score'].agg(['mean', 'max', 'count']).to_dict()
        risk_by_corridor = df.groupby('corridor')['risk_score'].agg(['mean', 'max', 'count']).to_dict()
        risk_by_amount = df.groupby(pd.cut(df['amount'], bins=5))['risk_score'].mean().to_dict()
        
        # Generate report
        report_content = f"""
RISK ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RISK OVERVIEW
=============
Total Transactions Analyzed: {len(df):,}
Average Risk Score: {risk_stats['avg_risk_score']:.2f}
Maximum Risk Score: {risk_stats['max_risk_score']:.2f}
Minimum Risk Score: {risk_stats['min_risk_score']:.2f}

RISK DISTRIBUTION
=================
High Risk (>75): {risk_stats['high_risk_count']:,} transactions ({risk_stats['high_risk_count']/len(df)*100:.1f}%)
Medium Risk (50-75): {risk_stats['medium_risk_count']:,} transactions ({risk_stats['medium_risk_count']/len(df)*100:.1f}%)
Low Risk (≤50): {risk_stats['low_risk_count']:,} transactions ({risk_stats['low_risk_count']/len(df)*100:.1f}%)

RISK BY SOURCE
==============
"""
        
        for source in df['source'].unique():
            source_data = df[df['source'] == source]
            avg_risk = source_data['risk_score'].mean()
            max_risk = source_data['risk_score'].max()
            count = len(source_data)
            report_content += f"{source}: Avg {avg_risk:.1f}, Max {max_risk:.1f}, Count {count:,}\n"
        
        return {
            'success': True,
            'data': report_content.encode('utf-8'),
            'preview': report_content[:500] + "..." if len(report_content) > 500 else report_content,
            'risk_stats': risk_stats
        }
    
    def _generate_volume_analysis_report(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate volume analysis report"""
        
        if not transactions:
            return {
                'success': False,
                'message': 'No transaction data available for volume analysis'
            }
        
        df = pd.DataFrame(transactions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Volume statistics
        total_volume = df['amount'].sum()
        daily_volume = df.groupby(df['timestamp'].dt.date)['amount'].sum()
        hourly_volume = df.groupby(df['timestamp'].dt.hour)['amount'].sum()
        
        # Generate report
        report_content = f"""
VOLUME ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

VOLUME OVERVIEW
===============
Total Volume: ₹{total_volume:,.2f}
Number of Days: {len(daily_volume)}
Average Daily Volume: ₹{daily_volume.mean():,.2f}
Peak Daily Volume: ₹{daily_volume.max():,.2f}
Peak Hour Volume: ₹{hourly_volume.max():,.2f}

TOP VOLUME CORRIDORS
====================
"""
        
        corridor_volumes = df.groupby('corridor')['amount'].sum().sort_values(ascending=False)
        for corridor, volume in corridor_volumes.head(5).items():
            percentage = (volume / total_volume) * 100
            report_content += f"{corridor}: ₹{volume:,.2f} ({percentage:.1f}%)\n"
        
        return {
            'success': True,
            'data': report_content.encode('utf-8'),
            'preview': report_content[:500] + "..." if len(report_content) > 500 else report_content
        }
    
    def _generate_privacy_compliance_report(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        
        # Get privacy budget status from session state
        from utils.privacy_modules import PrivacyManager
        privacy_manager = PrivacyManager()
        budget_status = privacy_manager.get_privacy_budget_status()
        
        # Analyze encryption status
        encrypted_count = 0
        total_sensitive_fields = 0
        
        for txn in transactions:
            if txn.get('encrypted_counterparty'):
                encrypted_count += 1
            if txn.get('counterparty'):
                total_sensitive_fields += 1
        
        encryption_rate = (encrypted_count / total_sensitive_fields * 100) if total_sensitive_fields > 0 else 0
        
        report_content = f"""
PRIVACY COMPLIANCE REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PRIVACY BUDGET STATUS
=====================
Total Budget: {budget_status['total']:.2f}
Used Budget: {budget_status['used']:.2f}
Remaining Budget: {budget_status['remaining']:.2f}
Usage Percentage: {budget_status['used_percentage']:.1f}%

ENCRYPTION COMPLIANCE
=====================
Total Sensitive Fields: {total_sensitive_fields:,}
Encrypted Fields: {encrypted_count:,}
Encryption Rate: {encryption_rate:.1f}%

COMPLIANCE STATUS
=================
Privacy Budget: {'COMPLIANT' if budget_status['used_percentage'] < 80 else 'WARNING'}
Data Encryption: {'COMPLIANT' if encryption_rate > 90 else 'NEEDS IMPROVEMENT'}
"""
        
        return {
            'success': True,
            'data': report_content.encode('utf-8'),
            'preview': report_content
        }
    
    def _generate_performance_metrics_report(self) -> Dict[str, Any]:
        """Generate performance metrics report"""
        
        # Get performance data from session state
        perf_log = st.session_state.get('performance_log', {})
        
        generation_times = perf_log.get('generation_times', [])
        analytics_times = perf_log.get('analytics_times', [])
        
        report_content = f"""
PERFORMANCE METRICS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TRANSACTION GENERATION PERFORMANCE
===================================
Total Generations: {len(generation_times):,}
"""
        
        if generation_times:
            times = [t[1] for t in generation_times]
            report_content += f"""Average Generation Time: {sum(times)/len(times):.3f} seconds
Fastest Generation: {min(times):.3f} seconds
Slowest Generation: {max(times):.3f} seconds
"""
        
        report_content += f"""
ANALYTICS PERFORMANCE
=====================
Total Analytics Operations: {len(analytics_times):,}
"""
        
        if analytics_times:
            times = [t[1] for t in analytics_times]
            report_content += f"""Average Analytics Time: {sum(times)/len(times):.3f} seconds
Fastest Analytics: {min(times):.3f} seconds
Slowest Analytics: {max(times):.3f} seconds
"""
        
        return {
            'success': True,
            'data': report_content.encode('utf-8'),
            'preview': report_content
        }
    
    def get_audit_logs(self, level: Optional[str] = None, 
                      source: Optional[str] = None,
                      time_range: str = "Last 24 Hours") -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        
        # Map time range to hours
        time_mapping = {
            "Last Hour": 1,
            "Last 24 Hours": 24,
            "Last 7 Days": 168,
            "Last 30 Days": 720
        }
        
        hours_back = time_mapping.get(time_range, 24)
        
        # Get logs from database
        logs = self.db.get_audit_logs(limit=1000, hours_back=hours_back)
        
        # Apply filters
        filtered_logs = []
        for log in logs:
            # Level filter
            if level and level != "All":
                # This would be implemented based on log level field
                # For now, we'll include all logs
                pass
            
            # Source filter
            if source and source != "All":
                if log.get('entity_type', '').lower() != source.lower():
                    continue
            
            filtered_logs.append(log)
        
        return filtered_logs
