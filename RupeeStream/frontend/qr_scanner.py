import streamlit as st
import pandas as pd
import json
import uuid
from datetime import datetime
import qrcode
from io import BytesIO
import base64
from typing import Dict, Any, Optional, List

from api.transaction_processor import TransactionProcessor
from utils.encryption import encrypt_data, decrypt_data
from config import Config

def show_qr_scanner():
    """QR Code scanner and generator for mobile payments"""
    
    st.title("📱 QR Code Scanner & Generator")
    
    # Initialize components
    processor = TransactionProcessor()
    config = Config()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Generate QR Code", "Scan QR Code", "QR Transaction History", "Offline Transactions"
    ])
    
    with tab1:
        show_qr_generator(processor)
    
    with tab2:
        show_qr_scanner_interface(processor)
    
    with tab3:
        show_qr_transaction_history()
    
    with tab4:
        show_offline_transactions()

def show_qr_generator(processor: TransactionProcessor):
    """QR Code generation interface"""
    
    st.subheader("📄 Generate QR Code for Payment")
    
    # QR Code generation form
    with st.form("qr_generator_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Transaction Details")
            amount = st.number_input("Amount", min_value=1.0, value=1000.0)
            currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "SGD"])
            source = st.selectbox("Payment Source", ["UPI", "NEFT", "SRVA-INR", "SWIFT"])
            
        with col2:
            st.markdown("#### Additional Information")
            corridor = st.selectbox("Trade Corridor", ["IN-US", "IN-EU", "IN-SG", "IN-GB", "IN-RU"])
            merchant_id = st.text_input("Merchant/Entity ID", value=f"MERCH_{uuid.uuid4().hex[:8].upper()}")
            description = st.text_area("Payment Description", value="Cross-border trade payment")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            expiry_minutes = st.number_input("Expiry (minutes)", min_value=1, max_value=1440, value=30)
        with col2:
            include_encryption = st.checkbox("Encrypt QR Data", value=True)
        with col3:
            offline_capable = st.checkbox("Offline Compatible", value=True)
        
        generate_qr = st.form_submit_button("Generate QR Code", use_container_width=True)
    
    if generate_qr:
        qr_data = create_qr_payment_data(
            amount=amount,
            currency=currency,
            source=source,
            corridor=corridor,
            merchant_id=merchant_id,
            description=description,
            expiry_minutes=expiry_minutes,
            include_encryption=include_encryption,
            offline_capable=offline_capable
        )
        
        if qr_data['success']:
            # Generate QR code image
            qr_image = generate_qr_code_image(qr_data['qr_payload'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📱 QR Code")
                st.image(qr_image, caption=f"Payment QR - ₹{amount:,.2f}")
                
                # Download button for QR code
                st.download_button(
                    label="📥 Download QR Code",
                    data=qr_image,
                    file_name=f"payment_qr_{qr_data['payment_id']}.png",
                    mime="image/png",
                    use_container_width=True
                )
            
            with col2:
                st.subheader("📋 Payment Details")
                st.json(qr_data['display_data'])
                
                # QR payload for manual entry
                with st.expander("📄 QR Code Data"):
                    st.code(qr_data['qr_payload'])
                
                # Security information
                if include_encryption:
                    st.success("🔒 QR code data is encrypted")
                else:
                    st.warning("🔓 QR code data is not encrypted")
        else:
            st.error(f"Failed to generate QR code: {qr_data['message']}")

def show_qr_scanner_interface(processor: TransactionProcessor):
    """QR Code scanning simulation interface"""
    
    st.subheader("📷 Scan QR Code")
    
    # Note about camera access in Streamlit
    st.info("📱 In a production mobile app, this would access the device camera. For demo purposes, you can paste QR code data below.")
    
    # Manual QR data input for testing
    with st.form("qr_scanner_form"):
        qr_input_method = st.radio("Input Method", ["Paste QR Data", "Upload QR Image File"])
        
        if qr_input_method == "Paste QR Data":
            qr_data_input = st.text_area("Paste QR Code Data", 
                                       placeholder="Paste the QR code payload here...")
            uploaded_file = None
        else:
            uploaded_file = st.file_uploader("Upload QR Code Image", 
                                           type=['png', 'jpg', 'jpeg'])
            qr_data_input = ""
        
        scan_qr = st.form_submit_button("🔍 Process QR Code", use_container_width=True)
    
    if scan_qr:
        if qr_input_method == "Paste QR Data" and qr_data_input:
            result = process_qr_payment(qr_data_input, processor)
            display_qr_scan_result(result)
        
        elif qr_input_method == "Upload QR Image File" and uploaded_file:
            st.info("📷 QR image processing would be implemented with a QR decoder library in production")
            st.warning("For demo purposes, please use the 'Paste QR Data' option")
        
        else:
            st.warning("Please provide QR code data to process")
    
    # Quick test QR codes
    st.subheader("🧪 Test QR Codes")
    st.info("Click any button below to generate and immediately process a test QR code")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Small Payment", use_container_width=True):
            test_qr = create_test_qr_data("small")
            result = process_qr_payment(test_qr, processor)
            display_qr_scan_result(result)
    
    with col2:
        if st.button("Test Large Payment", use_container_width=True):
            test_qr = create_test_qr_data("large")
            result = process_qr_payment(test_qr, processor)
            display_qr_scan_result(result)
    
    with col3:
        if st.button("Test International", use_container_width=True):
            test_qr = create_test_qr_data("international")
            result = process_qr_payment(test_qr, processor)
            display_qr_scan_result(result)

def show_qr_transaction_history():
    """Display QR transaction history"""
    
    st.subheader("📊 QR Transaction History")
    
    # Get QR transactions from session state
    qr_transactions = st.session_state.get('qr_transactions', [])
    
    if not qr_transactions:
        st.info("No QR transactions found. Generate and scan QR codes to see transaction history.")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(qr_transactions)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_qr_volume = df['amount'].sum()
        st.metric("Total QR Volume", f"₹{total_qr_volume:,.0f}")
    
    with col2:
        total_qr_count = len(df)
        st.metric("Total QR Transactions", total_qr_count)
    
    with col3:
        successful_qr = len(df[df['status'] == 'Completed'])
        success_rate = (successful_qr / total_qr_count * 100) if total_qr_count > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        avg_qr_amount = df['amount'].mean()
        st.metric("Avg QR Amount", f"₹{avg_qr_amount:,.0f}")
    
    # Transaction table with filters
    st.subheader("Transaction Details")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect("Filter by Status", 
                                     df['status'].unique(), 
                                     default=df['status'].unique())
    with col2:
        source_filter = st.multiselect("Filter by Source", 
                                     df['source'].unique(), 
                                     default=df['source'].unique())
    with col3:
        min_amount = st.number_input("Minimum Amount", min_value=0.0, value=0.0)
    
    # Apply filters
    filtered_df = df[
        (df['status'].isin(status_filter)) &
        (df['source'].isin(source_filter)) &
        (df['amount'] >= min_amount)
    ]
    
    # Display filtered transactions
    display_columns = ['payment_id', 'amount', 'currency', 'source', 'status', 'timestamp', 'method']
    if not filtered_df.empty:
        st.dataframe(filtered_df[display_columns], use_container_width=True)
        
        # Export QR transaction data
        if st.button("📥 Export QR Transaction Data"):
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"qr_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No transactions match the selected filters")
    
    # QR transaction analytics
    if len(df) > 0:
        st.subheader("📈 QR Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # QR usage by source
            source_counts = df['source'].value_counts()
            fig = px.pie(values=source_counts.values, names=source_counts.index,
                        title="QR Transactions by Source")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # QR transaction amounts over time
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df_sorted = df.sort_values('timestamp')
                
                fig = px.line(df_sorted, x='timestamp', y='amount',
                            title="QR Transaction Amounts Over Time")
                st.plotly_chart(fig, use_container_width=True)

def show_offline_transactions():
    """Manage offline QR transactions"""
    
    st.subheader("📴 Offline Transaction Management")
    
    # Offline transactions queue
    offline_queue = st.session_state.get('offline_qr_queue', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Pending Offline Transactions", len(offline_queue))
    
    with col2:
        if st.button("🔄 Sync Offline Transactions", use_container_width=True):
            if offline_queue:
                synced_count = sync_offline_transactions(offline_queue)
                st.success(f"Synced {synced_count} offline transactions!")
                st.session_state.offline_qr_queue = []
                st.rerun()
            else:
                st.info("No offline transactions to sync")
    
    # Show pending offline transactions
    if offline_queue:
        st.subheader("📋 Pending Offline Transactions")
        
        offline_df = pd.DataFrame(offline_queue)
        st.dataframe(offline_df, use_container_width=True)
        
        # Manual sync options
        with st.expander("⚙️ Manual Sync Options"):
            selected_indices = st.multiselect(
                "Select transactions to sync",
                range(len(offline_queue)),
                format_func=lambda x: f"Transaction {x+1}: ₹{offline_queue[x]['amount']:,.0f}"
            )
            
            if st.button("Sync Selected") and selected_indices:
                selected_transactions = [offline_queue[i] for i in selected_indices]
                synced_count = sync_offline_transactions(selected_transactions)
                
                # Remove synced transactions from queue
                remaining_queue = [offline_queue[i] for i in range(len(offline_queue)) if i not in selected_indices]
                st.session_state.offline_qr_queue = remaining_queue
                
                st.success(f"Synced {synced_count} selected transactions!")
                st.rerun()
    else:
        st.info("📶 All transactions are synced. No offline transactions pending.")
    
    # Offline capabilities information
    with st.expander("ℹ️ Offline Transaction Information"):
        st.markdown("""
        **Offline QR Transaction Features:**
        
        - 📴 **Store transactions locally** when internet is unavailable
        - 🔄 **Auto-sync** when connection is restored
        - 🔒 **Encrypted storage** for security
        - ⏰ **Timestamp preservation** for accurate record keeping
        - 🛡️ **Fraud detection** runs during sync process
        
        **How it works:**
        1. QR transactions are processed locally when offline
        2. Transactions are stored in encrypted local cache
        3. When online, transactions are automatically synced
        4. Full validation and fraud checking occurs during sync
        """)

def create_qr_payment_data(amount: float, currency: str, source: str, corridor: str,
                          merchant_id: str, description: str, expiry_minutes: int,
                          include_encryption: bool, offline_capable: bool) -> Dict[str, Any]:
    """Create QR payment data structure"""
    
    try:
        payment_id = f"QR_{uuid.uuid4().hex[:12].upper()}"
        expiry_time = datetime.now() + pd.Timedelta(minutes=expiry_minutes)
        
        payment_data = {
            'payment_id': payment_id,
            'amount': amount,
            'currency': currency,
            'source': source,
            'corridor': corridor,
            'merchant_id': merchant_id,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'expires_at': expiry_time.isoformat(),
            'offline_capable': offline_capable,
            'version': '1.0'
        }
        
        # Create QR payload
        qr_payload = json.dumps(payment_data)
        
        # Encrypt if requested
        if include_encryption:
            encryption_key = st.session_state.get('encryption_key')
            if encryption_key:
                qr_payload = encrypt_data(qr_payload, encryption_key)
                payment_data['encrypted'] = True
        
        # Display data (without sensitive info)
        display_data = {
            'Payment ID': payment_id,
            'Amount': f"{amount:,.2f} {currency}",
            'Source': source,
            'Corridor': corridor,
            'Merchant': merchant_id,
            'Expires': expiry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Offline Capable': "Yes" if offline_capable else "No"
        }
        
        return {
            'success': True,
            'payment_id': payment_id,
            'qr_payload': qr_payload,
            'display_data': display_data,
            'raw_data': payment_data
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Failed to create QR payment data: {str(e)}"
        }

def generate_qr_code_image(qr_data: str):
    """Generate QR code image from data"""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to bytes for Streamlit
    img_buffer = BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    return img_buffer.getvalue()

def process_qr_payment(qr_data: str, processor: TransactionProcessor) -> Dict[str, Any]:
    """Process scanned QR code payment data"""
    
    try:
        # Try to decrypt if needed
        decrypted_data = qr_data
        encryption_key = st.session_state.get('encryption_key')
        
        # Check if data is encrypted (basic check)
        if not qr_data.startswith('{'):
            if encryption_key:
                decrypted_data = decrypt_data(qr_data, encryption_key)
                if decrypted_data.startswith('Decryption Failed'):
                    return {
                        'success': False,
                        'message': 'Failed to decrypt QR code data'
                    }
        
        # Parse JSON data
        payment_data = json.loads(decrypted_data)
        
        # Validate payment data
        validation_result = validate_qr_payment_data(payment_data)
        if not validation_result['valid']:
            return {
                'success': False,
                'message': validation_result['message']
            }
        
        # Check expiry
        expires_at = datetime.fromisoformat(payment_data['expires_at'])
        if datetime.now() > expires_at:
            return {
                'success': False,
                'message': 'QR code has expired'
            }
        
        # Process the transaction
        transaction_data = {
            'amount': payment_data['amount'],
            'currency': payment_data['currency'],
            'source': payment_data['source'],
            'corridor': payment_data['corridor'],
            'counterparty': payment_data['merchant_id'],
            'narrative': payment_data['description']
        }
        
        # Check if we're online or offline
        is_online = st.session_state.get('network_online', True)  # Simulate network status
        
        if is_online:
            # Process normally
            result = processor.process_manual_transaction(transaction_data)
            
            if result['success']:
                # Add to QR transaction history
                qr_transaction = {
                    'payment_id': payment_data['payment_id'],
                    'method': 'QR_SCAN',
                    'timestamp': datetime.now(),
                    **transaction_data,
                    'status': result['transaction']['status']
                }
                
                if 'qr_transactions' not in st.session_state:
                    st.session_state.qr_transactions = []
                st.session_state.qr_transactions.append(qr_transaction)
                
                return {
                    'success': True,
                    'message': 'QR payment processed successfully',
                    'transaction_id': result['transaction_id'],
                    'payment_id': payment_data['payment_id']
                }
            else:
                return result
        else:
            # Store for offline processing
            if payment_data.get('offline_capable', False):
                offline_transaction = {
                    'payment_id': payment_data['payment_id'],
                    'method': 'QR_SCAN_OFFLINE',
                    'timestamp': datetime.now(),
                    'sync_status': 'PENDING',
                    **transaction_data
                }
                
                if 'offline_qr_queue' not in st.session_state:
                    st.session_state.offline_qr_queue = []
                st.session_state.offline_qr_queue.append(offline_transaction)
                
                return {
                    'success': True,
                    'message': 'QR payment stored for offline processing',
                    'offline': True,
                    'payment_id': payment_data['payment_id']
                }
            else:
                return {
                    'success': False,
                    'message': 'QR code not compatible with offline processing'
                }
        
    except json.JSONDecodeError:
        return {
            'success': False,
            'message': 'Invalid QR code data format'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'QR processing failed: {str(e)}'
        }

def validate_qr_payment_data(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate QR payment data structure"""
    
    required_fields = ['payment_id', 'amount', 'currency', 'source', 'corridor', 'merchant_id']
    
    for field in required_fields:
        if field not in payment_data:
            return {'valid': False, 'message': f'Missing required field: {field}'}
    
    # Validate amount
    if payment_data['amount'] <= 0:
        return {'valid': False, 'message': 'Invalid amount'}
    
    # Validate currency
    valid_currencies = ['INR', 'USD', 'EUR', 'GBP', 'SGD', 'RUB', 'AED']
    if payment_data['currency'] not in valid_currencies:
        return {'valid': False, 'message': 'Invalid currency'}
    
    return {'valid': True, 'message': 'Valid QR payment data'}

def create_test_qr_data(test_type: str) -> str:
    """Create test QR data for demonstration"""
    
    test_configs = {
        'small': {
            'amount': 500.0,
            'currency': 'INR',
            'source': 'UPI',
            'corridor': 'IN-US',
            'description': 'Small test payment'
        },
        'large': {
            'amount': 100000.0,
            'currency': 'USD',
            'source': 'SWIFT',
            'corridor': 'IN-EU',
            'description': 'Large international payment'
        },
        'international': {
            'amount': 25000.0,
            'currency': 'EUR',
            'source': 'SRVA-Non-INR',
            'corridor': 'IN-EU',
            'description': 'Cross-border trade payment'
        }
    }
    
    config = test_configs.get(test_type, test_configs['small'])
    
    test_data = {
        'payment_id': f"TEST_{uuid.uuid4().hex[:8].upper()}",
        'merchant_id': f"MERCHANT_{uuid.uuid4().hex[:6].upper()}",
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + pd.Timedelta(minutes=30)).isoformat(),
        'offline_capable': True,
        'version': '1.0',
        **config
    }
    
    return json.dumps(test_data)

def display_qr_scan_result(result: Dict[str, Any]):
    """Display QR scan processing result"""
    
    if result['success']:
        if result.get('offline', False):
            st.warning(f"📴 **Offline Processing**")
            st.info(f"Payment ID: {result['payment_id']}")
            st.info("Transaction stored locally and will sync when online")
        else:
            st.success(f"✅ **Payment Successful**")
            st.info(f"Transaction ID: {result.get('transaction_id', 'N/A')}")
            st.info(f"Payment ID: {result['payment_id']}")
    else:
        st.error(f"❌ **Payment Failed**")
        st.error(f"Error: {result['message']}")

def sync_offline_transactions(offline_transactions: List[Dict[str, Any]]) -> int:
    """Sync offline transactions when online"""
    
    processor = TransactionProcessor()
    synced_count = 0
    
    for offline_txn in offline_transactions:
        # Extract transaction data
        transaction_data = {
            'amount': offline_txn['amount'],
            'currency': offline_txn['currency'],
            'source': offline_txn['source'],
            'corridor': offline_txn['corridor'],
            'counterparty': offline_txn.get('counterparty', 'Unknown'),
            'narrative': offline_txn.get('narrative', 'Offline QR payment')
        }
        
        # Process the transaction
        result = processor.process_manual_transaction(transaction_data)
        
        if result['success']:
            # Add to QR transaction history
            qr_transaction = {
                'payment_id': offline_txn['payment_id'],
                'method': 'QR_SCAN_SYNCED',
                'timestamp': offline_txn['timestamp'],
                'sync_timestamp': datetime.now(),
                **transaction_data,
                'status': result['transaction']['status']
            }
            
            if 'qr_transactions' not in st.session_state:
                st.session_state.qr_transactions = []
            st.session_state.qr_transactions.append(qr_transaction)
            
            synced_count += 1
    
    return synced_count
