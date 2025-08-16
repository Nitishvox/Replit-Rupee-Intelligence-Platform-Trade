import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from typing import Optional, Tuple
import streamlit as st

class EncryptionManager:
    """Comprehensive encryption manager for AES and RSA operations"""
    
    def __init__(self):
        self.backend = default_backend()
        
    def generate_aes_key(self) -> bytes:
        """Generate a random AES-256 key"""
        return os.urandom(32)  # 256-bit key
    
    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """Generate RSA key pair"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=self.backend
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def derive_key_from_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode())
        return key, salt

def generate_key() -> bytes:
    """Generate a new AES encryption key"""
    return os.urandom(32)

def encrypt_data(data: str, key: bytes) -> Optional[str]:
    """
    Encrypt data using AES-GCM
    
    Args:
        data: String data to encrypt
        key: 32-byte AES key
    
    Returns:
        Base64-encoded encrypted data or None if failed
    """
    try:
        if not data or not key:
            return None
        
        # Generate random nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        # Encrypt data
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
        
        # Combine nonce + ciphertext + tag
        encrypted_data = nonce + ciphertext + encryptor.tag
        
        # Return as base64 string
        return base64.b64encode(encrypted_data).decode('utf-8')
        
    except Exception as e:
        st.error(f"Encryption failed: {str(e)}")
        return None

def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """
    Decrypt data using AES-GCM
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        key: 32-byte AES key
    
    Returns:
        Decrypted string or error message
    """
    try:
        if not encrypted_data or not key:
            return "N/A"
        
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Extract components
        nonce = encrypted_bytes[:12]
        tag = encrypted_bytes[-16:]
        ciphertext = encrypted_bytes[12:-16]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        
        # Decrypt data
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext.decode('utf-8')
        
    except Exception as e:
        return f"Decryption Failed: {str(e)}"

def encrypt_with_rsa(data: str, public_key_pem: bytes) -> Optional[str]:
    """
    Encrypt data using RSA public key
    
    Args:
        data: String data to encrypt
        public_key_pem: RSA public key in PEM format
    
    Returns:
        Base64-encoded encrypted data or None if failed
    """
    try:
        # Load public key
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        # Encrypt data
        encrypted = public_key.encrypt(
            data.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode('utf-8')
        
    except Exception as e:
        st.error(f"RSA encryption failed: {str(e)}")
        return None

def decrypt_with_rsa(encrypted_data: str, private_key_pem: bytes) -> str:
    """
    Decrypt data using RSA private key
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        private_key_pem: RSA private key in PEM format
    
    Returns:
        Decrypted string or error message
    """
    try:
        # Load private key
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )
        
        # Decode and decrypt
        encrypted_bytes = base64.b64decode(encrypted_data)
        decrypted = private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted.decode('utf-8')
        
    except Exception as e:
        return f"RSA decryption failed: {str(e)}"

def hash_data(data: str, algorithm: str = 'sha256') -> str:
    """
    Hash data using specified algorithm
    
    Args:
        data: String data to hash
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')
    
    Returns:
        Hexadecimal hash string
    """
    try:
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        hash_obj.update(data.encode('utf-8'))
        return hash_obj.hexdigest()
        
    except Exception as e:
        st.error(f"Hashing failed: {str(e)}")
        return ""

def create_pseudonym(identifier: str, salt: str = None) -> str:
    """
    Create a pseudonym for an identifier using salted hash
    
    Args:
        identifier: Original identifier
        salt: Salt for hashing (generated if None)
    
    Returns:
        Pseudonymized identifier
    """
    if salt is None:
        salt = os.urandom(16).hex()
    
    combined = f"{identifier}{salt}"
    hashed = hash_data(combined, 'sha256')
    
    # Return first 12 characters with prefix
    return f"PSEUDO_{hashed[:12].upper()}"

def secure_compare(data1: str, data2: str) -> bool:
    """
    Securely compare two strings to prevent timing attacks
    
    Args:
        data1: First string
        data2: Second string
    
    Returns:
        True if strings are equal, False otherwise
    """
    if len(data1) != len(data2):
        return False
    
    result = 0
    for x, y in zip(data1, data2):
        result |= ord(x) ^ ord(y)
    
    return result == 0

def encrypt_file_data(file_content: bytes, key: bytes) -> Optional[str]:
    """
    Encrypt file content using AES-GCM
    
    Args:
        file_content: Binary file content
        key: 32-byte AES key
    
    Returns:
        Base64-encoded encrypted data or None if failed
    """
    try:
        if not file_content or not key:
            return None
        
        # Generate random nonce
        nonce = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        
        # Encrypt data
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(file_content) + encryptor.finalize()
        
        # Combine nonce + ciphertext + tag
        encrypted_data = nonce + ciphertext + encryptor.tag
        
        # Return as base64 string
        return base64.b64encode(encrypted_data).decode('utf-8')
        
    except Exception as e:
        st.error(f"File encryption failed: {str(e)}")
        return None

def decrypt_file_data(encrypted_data: str, key: bytes) -> Optional[bytes]:
    """
    Decrypt file content using AES-GCM
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        key: 32-byte AES key
    
    Returns:
        Decrypted binary data or None if failed
    """
    try:
        if not encrypted_data or not key:
            return None
        
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Extract components
        nonce = encrypted_bytes[:12]
        tag = encrypted_bytes[-16:]
        ciphertext = encrypted_bytes[12:-16]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        
        # Decrypt data
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext
        
    except Exception as e:
        st.error(f"File decryption failed: {str(e)}")
        return None

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token
    
    Args:
        length: Token length in bytes
    
    Returns:
        Hexadecimal token string
    """
    return os.urandom(length).hex()

def key_derivation_function(password: str, salt: bytes, iterations: int = 100000) -> bytes:
    """
    Derive encryption key from password using PBKDF2
    
    Args:
        password: User password
        salt: Random salt
        iterations: Number of iterations
    
    Returns:
        Derived key bytes
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    
    return kdf.derive(password.encode('utf-8'))

def encrypt_database_field(field_value: str, field_name: str, record_id: str) -> Optional[str]:
    """
    Encrypt database field with additional context
    
    Args:
        field_value: Value to encrypt
        field_name: Name of the database field
        record_id: Unique record identifier
    
    Returns:
        Encrypted field value or None if failed
    """
    try:
        # Get encryption key from session state
        key = st.session_state.get('encryption_key')
        if not key:
            return field_value  # Return as-is if no encryption key
        
        # Add context to encryption
        context = f"{field_name}:{record_id}"
        combined_data = f"{field_value}|{context}"
        
        return encrypt_data(combined_data, key)
        
    except Exception as e:
        st.error(f"Database field encryption failed: {str(e)}")
        return field_value

def decrypt_database_field(encrypted_value: str, field_name: str, record_id: str) -> str:
    """
    Decrypt database field with context validation
    
    Args:
        encrypted_value: Encrypted field value
        field_name: Name of the database field
        record_id: Unique record identifier
    
    Returns:
        Decrypted field value or error message
    """
    try:
        # Get encryption key from session state
        key = st.session_state.get('encryption_key')
        if not key:
            return encrypted_value  # Return as-is if no encryption key
        
        # Decrypt data
        decrypted_combined = decrypt_data(encrypted_value, key)
        
        if decrypted_combined.startswith('Decryption Failed'):
            return decrypted_combined
        
        # Extract value and validate context
        if '|' in decrypted_combined:
            field_value, context = decrypted_combined.rsplit('|', 1)
            expected_context = f"{field_name}:{record_id}"
            
            if context == expected_context:
                return field_value
            else:
                return "Context validation failed"
        else:
            # Fallback for data encrypted without context
            return decrypted_combined
            
    except Exception as e:
        return f"Database field decryption failed: {str(e)}"
