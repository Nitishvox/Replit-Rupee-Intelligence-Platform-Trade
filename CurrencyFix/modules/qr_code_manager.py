import streamlit as st
import qrcode
import base64
from io import BytesIO
from PIL import Image
import json
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class QRCodeManager:
    """QR Code Manager for secure payment QR generation and scanning"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        self.qr_types = [
            "Payment QR",
            "Account QR",
            "Merchant QR",
            "Transaction QR",
            "Settlement QR"
        ]
        
        # QR Code configuration
        self.qr_config = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 10,
            'border': 4
        }
    
    def generate_payment_qr(self, payment_data: Dict, encrypt: bool = False) -> str:
        """Generate QR code for payment data"""
        try:
            # Prepare QR data
            qr_data = {
                'type': 'payment',
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'data': payment_data
            }
            
            # Encrypt if requested
            if encrypt:
                from modules.encryption_manager import EncryptionManager
                encryption_manager = EncryptionManager()
                qr_content = encryption_manager.encrypt_transaction(qr_data)
            else:
                qr_content = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(**self.qr_config)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for display
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Save QR code record
            self._save_qr_record('payment', payment_data, qr_content, encrypt)
            
            return qr_base64
            
        except Exception as e:
            st.error(f"Error generating payment QR: {str(e)}")
            return None
    
    def generate_account_qr(self, account_data: Dict) -> str:
        """Generate QR code for account information"""
        try:
            qr_data = {
                'type': 'account',
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'data': account_data
            }
            
            qr_content = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(**self.qr_config)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Save QR code record
            self._save_qr_record('account', account_data, qr_content, False)
            
            return qr_base64
            
        except Exception as e:
            st.error(f"Error generating account QR: {str(e)}")
            return None
    
    def generate_merchant_qr(self, merchant_data: Dict) -> str:
        """Generate QR code for merchant information"""
        try:
            qr_data = {
                'type': 'merchant',
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'data': merchant_data
            }
            
            qr_content = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(**self.qr_config)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create QR code image with custom styling for merchant
            qr_image = qr.make_image(fill_color="#1f4e79", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Save QR code record
            self._save_qr_record('merchant', merchant_data, qr_content, False)
            
            return qr_base64
            
        except Exception as e:
            st.error(f"Error generating merchant QR: {str(e)}")
            return None
    
    def scan_qr_code(self, uploaded_file) -> Optional[Dict]:
        """Scan and decode QR code from uploaded image"""
        try:
            # Read uploaded file
            if uploaded_file is not None:
                # Convert uploaded file to image
                file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                
                # Convert to grayscale for better QR detection
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # Initialize QR code detector
                detector = cv2.QRCodeDetector()
                
                # Detect and decode QR code
                data, vertices_array, binary_qrcode = detector.detectAndDecode(gray)
                
                if vertices_array is not None:
                    # QR code detected and decoded
                    if data:
                        try:
                            # Try to parse as JSON
                            decoded_data = json.loads(data)
                            
                            # Check if it's encrypted
                            if isinstance(decoded_data, dict) and 'type' in decoded_data:
                                return decoded_data
                            else:
                                # Might be encrypted data
                                try:
                                    from modules.encryption_manager import EncryptionManager
                                    encryption_manager = EncryptionManager()
                                    decrypted_data = encryption_manager.decrypt_transaction(data)
                                    return decrypted_data
                                except:
                                    # Return raw data if decryption fails
                                    return {'raw_data': data, 'type': 'unknown'}
                        
                        except json.JSONDecodeError:
                            # Return raw text data
                            return {'raw_data': data, 'type': 'text'}
                    
                    else:
                        return {'error': 'QR code detected but no data decoded'}
                
                else:
                    return {'error': 'No QR code detected in the image'}
            
            return None
            
        except Exception as e:
            st.error(f"Error scanning QR code: {str(e)}")
            return None
    
    def generate_dynamic_qr(self, base_data: Dict, expiry_minutes: int = 30) -> str:
        """Generate dynamic QR code with expiry"""
        try:
            # Add expiry timestamp
            expiry_time = datetime.now() + timedelta(minutes=expiry_minutes)
            
            qr_data = {
                'type': 'dynamic',
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'expiry': expiry_time.isoformat(),
                'session_id': str(uuid.uuid4()),
                'data': base_data
            }
            
            qr_content = json.dumps(qr_data)
            
            # Generate QR code
            qr = qrcode.QRCode(**self.qr_config)
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            # Create QR code image with dynamic styling
            qr_image = qr.make_image(fill_color="#d63384", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Save dynamic QR record
            self._save_qr_record('dynamic', qr_data, qr_content, False, expiry_time)
            
            return qr_base64
            
        except Exception as e:
            st.error(f"Error generating dynamic QR: {str(e)}")
            return None
    
    def validate_qr_expiry(self, qr_data: Dict) -> bool:
        """Validate if QR code has expired"""
        try:
            if 'expiry' in qr_data:
                expiry_time = datetime.fromisoformat(qr_data['expiry'])
                return datetime.now() < expiry_time
            return True  # No expiry means always valid
            
        except Exception:
            return False
    
    def generate_batch_qr(self, batch_data: List[Dict], qr_type: str = 'payment') -> List[str]:
        """Generate multiple QR codes in batch"""
        qr_codes = []
        
        for data in batch_data:
            try:
                if qr_type == 'payment':
                    qr_code = self.generate_payment_qr(data)
                elif qr_type == 'account':
                    qr_code = self.generate_account_qr(data)
                elif qr_type == 'merchant':
                    qr_code = self.generate_merchant_qr(data)
                else:
                    qr_code = self.generate_payment_qr(data)  # Default to payment
                
                if qr_code:
                    qr_codes.append(qr_code)
                    
            except Exception as e:
                st.error(f"Error in batch QR generation: {str(e)}")
                continue
        
        return qr_codes
    
    def get_qr_analytics(self) -> Dict:
        """Get QR code usage analytics"""
        try:
            if 'qr_records' in st.session_state:
                records = st.session_state.qr_records
                
                analytics = {
                    'total_generated': len(records),
                    'by_type': {},
                    'encrypted_count': 0,
                    'expired_count': 0,
                    'recent_activity': []
                }
                
                for record in records:
                    # Count by type
                    qr_type = record.get('type', 'unknown')
                    analytics['by_type'][qr_type] = analytics['by_type'].get(qr_type, 0) + 1
                    
                    # Count encrypted
                    if record.get('encrypted', False):
                        analytics['encrypted_count'] += 1
                    
                    # Count expired
                    if record.get('expiry'):
                        try:
                            expiry_time = datetime.fromisoformat(record['expiry'])
                            if datetime.now() > expiry_time:
                                analytics['expired_count'] += 1
                        except:
                            pass
                    
                    # Recent activity (last 24 hours)
                    try:
                        created_time = datetime.fromisoformat(record['created_at'])
                        if datetime.now() - created_time < timedelta(hours=24):
                            analytics['recent_activity'].append(record)
                    except:
                        pass
                
                return analytics
            
            else:
                return {
                    'total_generated': 0,
                    'by_type': {},
                    'encrypted_count': 0,
                    'expired_count': 0,
                    'recent_activity': []
                }
                
        except Exception as e:
            st.error(f"Error getting QR analytics: {str(e)}")
            return {}
    
    def _save_qr_record(self, qr_type: str, data: Dict, content: str, encrypted: bool, expiry: datetime = None):
        """Save QR code generation record"""
        try:
            record = {
                'id': str(uuid.uuid4()),
                'type': qr_type,
                'data': data,
                'content_hash': hash(content),
                'encrypted': encrypted,
                'created_at': datetime.now().isoformat(),
                'expiry': expiry.isoformat() if expiry else None,
                'size': len(content)
            }
            
            # Save to session state (in production, would save to database)
            if 'qr_records' not in st.session_state:
                st.session_state.qr_records = []
            
            st.session_state.qr_records.append(record)
            
        except Exception as e:
            st.error(f"Error saving QR record: {str(e)}")
    
    def get_qr_history(self) -> List[Dict]:
        """Get QR code generation history"""
        return st.session_state.get('qr_records', [])
    
    def clear_expired_qr(self) -> int:
        """Clear expired QR codes and return count"""
        if 'qr_records' not in st.session_state:
            return 0
        
        original_count = len(st.session_state.qr_records)
        current_time = datetime.now()
        
        # Filter out expired QR codes
        st.session_state.qr_records = [
            record for record in st.session_state.qr_records
            if not record.get('expiry') or datetime.fromisoformat(record['expiry']) > current_time
        ]
        
        cleared_count = original_count - len(st.session_state.qr_records)
        return cleared_count
    
    def export_qr_batch(self, qr_codes: List[str], format: str = 'zip') -> bytes:
        """Export batch of QR codes as ZIP file"""
        try:
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, qr_code in enumerate(qr_codes):
                    # Decode base64 QR code
                    qr_data = base64.b64decode(qr_code)
                    
                    # Add to ZIP with sequential filename
                    filename = f"qr_code_{i+1:04d}.png"
                    zip_file.writestr(filename, qr_data)
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            st.error(f"Error exporting QR batch: {str(e)}")
            return None
    
    def create_qr_template(self, template_data: Dict) -> str:
        """Create QR code template for reuse"""
        try:
            template = {
                'id': str(uuid.uuid4()),
                'name': template_data.get('name', 'Unnamed Template'),
                'description': template_data.get('description', ''),
                'template_data': template_data,
                'created_at': datetime.now().isoformat(),
                'usage_count': 0
            }
            
            # Save template
            if 'qr_templates' not in st.session_state:
                st.session_state.qr_templates = []
            
            st.session_state.qr_templates.append(template)
            
            return template['id']
            
        except Exception as e:
            st.error(f"Error creating QR template: {str(e)}")
            return None
    
    def get_qr_templates(self) -> List[Dict]:
        """Get saved QR code templates"""
        return st.session_state.get('qr_templates', [])
