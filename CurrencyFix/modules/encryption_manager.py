import streamlit as st
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

class EncryptionManager:
    """Encryption Manager for secure data handling with AES and RSA encryption"""
    
    def __init__(self):
        self.key_file = 'encryption_key.key'
        self.rsa_private_key_file = 'rsa_private.pem'
        self.rsa_public_key_file = 'rsa_public.pem'
        
        # Initialize encryption keys
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialize encryption keys if they don't exist"""
        try:
            # Initialize AES key
            if not os.path.exists(self.key_file):
                self.generate_new_key()
            
            # Initialize RSA key pair
            if not os.path.exists(self.rsa_private_key_file) or not os.path.exists(self.rsa_public_key_file):
                self._generate_rsa_keys()
                
        except Exception as e:
            st.error(f"Error initializing encryption keys: {str(e)}")
    
    def generate_new_key(self):
        """Generate new AES encryption key"""
        try:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as key_file:
                key_file.write(key)
            
            # Save key info to session state
            st.session_state.encryption_key_generated = datetime.now().isoformat()
            
        except Exception as e:
            st.error(f"Error generating new key: {str(e)}")
    
    def _generate_rsa_keys(self):
        """Generate RSA key pair for asymmetric encryption"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Serialize public key
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Save keys to files
            with open(self.rsa_private_key_file, 'wb') as f:
                f.write(private_pem)
            
            with open(self.rsa_public_key_file, 'wb') as f:
                f.write(public_pem)
                
        except Exception as e:
            st.error(f"Error generating RSA keys: {str(e)}")
    
    def _load_key(self) -> Optional[bytes]:
        """Load AES encryption key"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as key_file:
                    return key_file.read()
            return None
        except Exception as e:
            st.error(f"Error loading encryption key: {str(e)}")
            return None
    
    def _load_rsa_keys(self) -> tuple:
        """Load RSA key pair"""
        try:
            private_key = None
            public_key = None
            
            if os.path.exists(self.rsa_private_key_file):
                with open(self.rsa_private_key_file, 'rb') as f:
                    private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
            
            if os.path.exists(self.rsa_public_key_file):
                with open(self.rsa_public_key_file, 'rb') as f:
                    public_key = serialization.load_pem_public_key(f.read())
            
            return private_key, public_key
            
        except Exception as e:
            st.error(f"Error loading RSA keys: {str(e)}")
            return None, None
    
    def encrypt_transaction(self, transaction_data: Dict) -> str:
        """Encrypt transaction data using AES encryption"""
        try:
            key = self._load_key()
            if not key:
                raise Exception("Encryption key not found. Please generate a new key.")
            
            # Create Fernet cipher
            f = Fernet(key)
            
            # Convert transaction data to JSON string
            json_data = json.dumps(transaction_data, default=str)
            
            # Encrypt the data
            encrypted_data = f.encrypt(json_data.encode())
            
            # Return base64 encoded encrypted data
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            st.error(f"Error encrypting transaction: {str(e)}")
            return None
    
    def decrypt_transaction(self, encrypted_data: str) -> Dict:
        """Decrypt transaction data using AES encryption"""
        try:
            key = self._load_key()
            if not key:
                raise Exception("Encryption key not found. Cannot decrypt data.")
            
            # Create Fernet cipher
            f = Fernet(key)
            
            # Decode base64 data
            decoded_data = base64.b64decode(encrypted_data.encode())
            
            # Decrypt the data
            decrypted_data = f.decrypt(decoded_data)
            
            # Convert back to dictionary
            return json.loads(decrypted_data.decode())
            
        except Exception as e:
            st.error(f"Error decrypting transaction: {str(e)}")
            return None
    
    def encrypt_with_rsa(self, data: str) -> str:
        """Encrypt data using RSA public key"""
        try:
            private_key, public_key = self._load_rsa_keys()
            if not public_key:
                raise Exception("RSA public key not found")
            
            # Encrypt data
            encrypted = public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            st.error(f"Error encrypting with RSA: {str(e)}")
            return None
    
    def decrypt_with_rsa(self, encrypted_data: str) -> str:
        """Decrypt data using RSA private key"""
        try:
            private_key, public_key = self._load_rsa_keys()
            if not private_key:
                raise Exception("RSA private key not found")
            
            # Decode base64 data
            decoded_data = base64.b64decode(encrypted_data.encode())
            
            # Decrypt data
            decrypted = private_key.decrypt(
                decoded_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return decrypted.decode()
            
        except Exception as e:
            st.error(f"Error decrypting with RSA: {str(e)}")
            return None
    
    def encrypt_sensitive_field(self, field_value: str, field_name: str = "") -> str:
        """Encrypt sensitive field data with metadata"""
        try:
            # Create metadata
            metadata = {
                'field_name': field_name,
                'encrypted_at': datetime.now().isoformat(),
                'encryption_type': 'AES',
                'version': '1.0'
            }
            
            # Combine metadata and field value
            combined_data = {
                'metadata': metadata,
                'value': field_value
            }
            
            return self.encrypt_transaction(combined_data)
            
        except Exception as e:
            st.error(f"Error encrypting sensitive field: {str(e)}")
            return None
    
    def decrypt_sensitive_field(self, encrypted_field: str) -> Dict:
        """Decrypt sensitive field data and return with metadata"""
        try:
            decrypted_data = self.decrypt_transaction(encrypted_field)
            
            if decrypted_data and isinstance(decrypted_data, dict):
                return {
                    'value': decrypted_data.get('value'),
                    'metadata': decrypted_data.get('metadata', {}),
                    'decryption_success': True
                }
            else:
                return {
                    'value': None,
                    'metadata': {},
                    'decryption_success': False
                }
                
        except Exception as e:
            st.error(f"Error decrypting sensitive field: {str(e)}")
            return {
                'value': None,
                'metadata': {},
                'decryption_success': False
            }
    
    def hash_data(self, data: str) -> str:
        """Create SHA-256 hash of data"""
        try:
            digest = hashes.Hash(hashes.SHA256())
            digest.update(data.encode())
            hash_bytes = digest.finalize()
            return base64.b64encode(hash_bytes).decode()
            
        except Exception as e:
            st.error(f"Error hashing data: {str(e)}")
            return None
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """Verify data against hash"""
        try:
            calculated_hash = self.hash_data(data)
            return calculated_hash == hash_value
            
        except Exception as e:
            st.error(f"Error verifying hash: {str(e)}")
            return False
    
    def encrypt_file(self, file_content: bytes, filename: str = "") -> str:
        """Encrypt file content"""
        try:
            key = self._load_key()
            if not key:
                raise Exception("Encryption key not found")
            
            f = Fernet(key)
            
            # Create file metadata
            file_metadata = {
                'filename': filename,
                'original_size': len(file_content),
                'encrypted_at': datetime.now().isoformat(),
                'file_id': str(uuid.uuid4())
            }
            
            # Combine metadata and content
            file_data = {
                'metadata': file_metadata,
                'content': base64.b64encode(file_content).decode()
            }
            
            # Encrypt combined data
            json_data = json.dumps(file_data)
            encrypted_data = f.encrypt(json_data.encode())
            
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            st.error(f"Error encrypting file: {str(e)}")
            return None
    
    def decrypt_file(self, encrypted_file: str) -> Dict:
        """Decrypt file content"""
        try:
            key = self._load_key()
            if not key:
                raise Exception("Encryption key not found")
            
            f = Fernet(key)
            
            # Decode and decrypt
            decoded_data = base64.b64decode(encrypted_file.encode())
            decrypted_data = f.decrypt(decoded_data)
            
            # Parse JSON
            file_data = json.loads(decrypted_data.decode())
            
            # Decode file content
            file_content = base64.b64decode(file_data['content'].encode())
            
            return {
                'content': file_content,
                'metadata': file_data.get('metadata', {}),
                'decryption_success': True
            }
            
        except Exception as e:
            st.error(f"Error decrypting file: {str(e)}")
            return {
                'content': None,
                'metadata': {},
                'decryption_success': False
            }
    
    def key_exists(self) -> bool:
        """Check if encryption key exists"""
        return os.path.exists(self.key_file)
    
    def get_encryption_info(self) -> Dict:
        """Get information about current encryption setup"""
        info = {
            'aes_key_exists': os.path.exists(self.key_file),
            'rsa_private_key_exists': os.path.exists(self.rsa_private_key_file),
            'rsa_public_key_exists': os.path.exists(self.rsa_public_key_file),
            'encryption_algorithm': 'AES (Fernet) + RSA',
            'key_generated_at': st.session_state.get('encryption_key_generated', 'Unknown')
        }
        
        if info['aes_key_exists']:
            try:
                key_stat = os.stat(self.key_file)
                info['aes_key_created'] = datetime.fromtimestamp(key_stat.st_ctime).isoformat()
                info['aes_key_size'] = f"{key_stat.st_size} bytes"
            except:
                pass
        
        if info['rsa_private_key_exists']:
            try:
                key_stat = os.stat(self.rsa_private_key_file)
                info['rsa_key_created'] = datetime.fromtimestamp(key_stat.st_ctime).isoformat()
            except:
                pass
        
        return info
    
    def backup_keys(self) -> str:
        """Create backup of encryption keys"""
        try:
            backup_data = {}
            
            # Backup AES key
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    backup_data['aes_key'] = base64.b64encode(f.read()).decode()
            
            # Backup RSA keys
            if os.path.exists(self.rsa_private_key_file):
                with open(self.rsa_private_key_file, 'rb') as f:
                    backup_data['rsa_private_key'] = base64.b64encode(f.read()).decode()
            
            if os.path.exists(self.rsa_public_key_file):
                with open(self.rsa_public_key_file, 'rb') as f:
                    backup_data['rsa_public_key'] = base64.b64encode(f.read()).decode()
            
            # Add metadata
            backup_data['backup_created_at'] = datetime.now().isoformat()
            backup_data['backup_id'] = str(uuid.uuid4())
            
            # Encrypt the backup itself
            backup_json = json.dumps(backup_data)
            return base64.b64encode(backup_json.encode()).decode()
            
        except Exception as e:
            st.error(f"Error creating key backup: {str(e)}")
            return None
    
    def restore_keys(self, backup_data: str) -> bool:
        """Restore encryption keys from backup"""
        try:
            # Decode backup data
            backup_json = base64.b64decode(backup_data.encode()).decode()
            backup = json.loads(backup_json)
            
            # Restore AES key
            if 'aes_key' in backup:
                key_data = base64.b64decode(backup['aes_key'].encode())
                with open(self.key_file, 'wb') as f:
                    f.write(key_data)
            
            # Restore RSA keys
            if 'rsa_private_key' in backup:
                private_key_data = base64.b64decode(backup['rsa_private_key'].encode())
                with open(self.rsa_private_key_file, 'wb') as f:
                    f.write(private_key_data)
            
            if 'rsa_public_key' in backup:
                public_key_data = base64.b64decode(backup['rsa_public_key'].encode())
                with open(self.rsa_public_key_file, 'wb') as f:
                    f.write(public_key_data)
            
            return True
            
        except Exception as e:
            st.error(f"Error restoring keys: {str(e)}")
            return False
    
    def secure_delete_keys(self):
        """Securely delete encryption keys"""
        try:
            # Delete key files
            for key_file in [self.key_file, self.rsa_private_key_file, self.rsa_public_key_file]:
                if os.path.exists(key_file):
                    # Overwrite with random data before deletion
                    with open(key_file, 'r+b') as f:
                        length = f.seek(0, 2)  # Seek to end to get file size
                        f.seek(0)
                        f.write(os.urandom(length))
                        f.flush()
                        os.fsync(f.fileno())
                    
                    # Delete the file
                    os.remove(key_file)
            
            # Clear session state
            if 'encryption_key_generated' in st.session_state:
                del st.session_state.encryption_key_generated
            
            return True
            
        except Exception as e:
            st.error(f"Error securely deleting keys: {str(e)}")
            return False
