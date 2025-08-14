import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json

# Import custom modules
from modules.srva_manager import SRVAManager
from modules.transaction_processor import TransactionProcessor
from modules.settlement_calculator import SettlementCalculator
from modules.compliance_tracker import ComplianceTracker
from modules.reporting_dashboard import ReportingDashboard
from modules.document_generator import DocumentGenerator
from modules.data_generator import DataGenerator
from modules.qr_code_manager import QRCodeManager
from modules.encryption_manager import EncryptionManager
from modules.ai_fraud_detector import AIFraudDetector
from utils.exchange_rate_api import ExchangeRateAPI
from utils.database_manager import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="RIPT - Rupee Intelligence Platform Trade",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'exchange_api' not in st.session_state:
    st.session_state.exchange_api = ExchangeRateAPI()

# Initialize modules
srva_manager = SRVAManager(st.session_state.db_manager)
transaction_processor = TransactionProcessor(st.session_state.db_manager, st.session_state.exchange_api)
settlement_calculator = SettlementCalculator(st.session_state.exchange_api)
compliance_tracker = ComplianceTracker(st.session_state.db_manager)
reporting_dashboard = ReportingDashboard(st.session_state.db_manager)
document_generator = DocumentGenerator()
data_generator = DataGenerator(st.session_state.db_manager)
qr_manager = QRCodeManager(st.session_state.db_manager)
encryption_manager = EncryptionManager()
ai_fraud_detector = AIFraudDetector(st.session_state.db_manager)

def main():
    # Header
    st.title("🏦 RIPT - Rupee Intelligence Platform Trade")
    st.markdown("**Advanced SRVA Management & INR Trade Settlement System**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Module",
        [
            "Dashboard",
            "SRVA Management", 
            "Transaction Processing",
            "Settlement Calculator",
            "Compliance Tracking",
            "Reporting & Analytics",
            "Document Generation",
            "Data Generator",
            "QR Code Manager",
            "Security & Encryption",
            "AI Fraud Detection"
        ]
    )
    
    # Display current INR exchange rates in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Current INR Rates")
    
    try:
        rates = st.session_state.exchange_api.get_current_rates()
        if rates:
            for currency, rate in rates.items():
                st.sidebar.metric(f"INR/{currency}", f"{rate:.4f}")
    except Exception as e:
        st.sidebar.error("Unable to fetch current rates")
    
    # Main content based on selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "SRVA Management":
        srva_manager.show_interface()
    elif page == "Transaction Processing":
        transaction_processor.show_interface()
    elif page == "Settlement Calculator":
        settlement_calculator.show_interface()
    elif page == "Compliance Tracking":
        compliance_tracker.show_interface()
    elif page == "Reporting & Analytics":
        reporting_dashboard.show_interface()
    elif page == "Document Generation":
        document_generator.show_interface()
    elif page == "Data Generator":
        show_data_generator()
    elif page == "QR Code Manager":
        show_qr_code_manager()
    elif page == "Security & Encryption":
        show_security_encryption()
    elif page == "AI Fraud Detection":
        show_ai_fraud_detection()

def show_dashboard():
    """Main dashboard with system overview"""
    st.header("System Overview Dashboard")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Get summary statistics
    stats = st.session_state.db_manager.get_dashboard_stats()
    
    with col1:
        st.metric(
            "Active SRVA Accounts",
            stats.get('active_accounts', 0),
            delta=stats.get('new_accounts_this_month', 0)
        )
    
    with col2:
        st.metric(
            "Total Settlements (₹)",
            f"{stats.get('total_settlements', 0):,.0f}",
            delta=f"{stats.get('settlements_this_month', 0):,.0f}"
        )
    
    with col3:
        st.metric(
            "Active Countries",
            stats.get('active_countries', 22),
            delta=stats.get('new_countries_this_month', 0)
        )
    
    with col4:
        st.metric(
            "Pending Transactions",
            stats.get('pending_transactions', 0)
        )
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Settlement Volume by Country")
        country_data = st.session_state.db_manager.get_settlement_by_country()
        if not country_data.empty:
            fig = px.bar(
                country_data,
                x='country',
                y='settlement_amount',
                title="INR Settlement Volume by Country (Last 30 Days)",
                color='settlement_amount',
                color_continuous_scale='viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No settlement data available")
    
    with col2:
        st.subheader("Transaction Flow Trend")
        trend_data = st.session_state.db_manager.get_transaction_trend()
        if not trend_data.empty:
            fig = px.line(
                trend_data,
                x='date',
                y=['exports', 'imports'],
                title="Export/Import Transaction Trend (₹)",
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction trend data available")
    
    # Recent activities
    st.subheader("Recent Activities")
    recent_activities = st.session_state.db_manager.get_recent_activities()
    if not recent_activities.empty:
        st.dataframe(recent_activities, use_container_width=True)
    else:
        st.info("No recent activities to display")
    
    # System status
    st.markdown("---")
    st.subheader("System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("✅ RBI Compliance: Active")
        st.success("✅ Exchange Rate API: Connected")
    
    with col2:
        st.success("✅ Banking Network: Online")
        st.success("✅ Document System: Operational")
    
    with col3:
        st.success("✅ Audit Trail: Recording")
        st.success("✅ Backup System: Active")

def show_data_generator():
    """Enhanced Data Generator Interface"""
    st.header("🎯 Enhanced Data Generator")
    st.markdown("Generate random transactions and SRVA accounts with encryption and spam simulation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Generate Transactions")
        transaction_count = st.slider("Number of transactions", 10, 1000, 100)
        include_spam = st.checkbox("Include spam transactions", value=True)
        spam_percentage = st.slider("Spam percentage", 0, 50, 10) if include_spam else 0
        
        if st.button("Generate Transactions", type="primary"):
            with st.spinner("Generating transactions..."):
                transactions = data_generator.generate_random_transactions(
                    transaction_count, 
                    include_spam=include_spam,
                    spam_percentage=spam_percentage
                )
                inserted = data_generator.insert_transactions_to_db(transactions)
                
            st.success(f"✅ Generated and inserted {inserted} transactions successfully!")
            
            # Show sample transaction
            if transactions:
                st.subheader("Sample Transaction")
                sample = transactions[0]
                st.json(sample)
                
                # Show encryption for sample
                encrypted_data = encryption_manager.encrypt_transaction(sample)
                st.subheader("Encrypted Sample")
                st.code(encrypted_data[:100] + "...")
    
    with col2:
        st.subheader("Generate SRVA Accounts")
        account_count = st.slider("Number of accounts", 5, 100, 20)
        
        if st.button("Generate Accounts", type="primary"):
            with st.spinner("Generating accounts..."):
                accounts = data_generator.generate_srva_accounts(account_count)
                inserted = data_generator.insert_accounts_to_db(accounts)
                
            st.success(f"✅ Generated and inserted {inserted} accounts successfully!")
            
            # Show sample account
            if accounts:
                st.subheader("Sample Account")
                sample = accounts[0]
                st.json(sample)

def show_qr_code_manager():
    """Enhanced QR Code Manager Interface"""
    st.header("📱 QR Code Manager with Encryption")
    st.markdown("Generate and scan encrypted QR codes for secure payments")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Payment QR", "Account QR", "Merchant QR", "QR Scanner"])
    
    with tab1:
        st.subheader("Generate Encrypted Payment QR Code")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            transaction_id = st.text_input("Transaction ID", value=f"PAY_{int(datetime.now().timestamp())}")
            amount = st.number_input("Amount", min_value=0.01, value=1000.0)
            currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"])
            recipient_account = st.text_input("Recipient Account", value="SRVA12345")
            description = st.text_area("Description", value="Mobile payment via encrypted QR code")
            
            if st.button("Generate Encrypted Payment QR", type="primary"):
                payment_data = {
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'currency': currency,
                    'recipient_account': recipient_account,
                    'description': description,
                    'timestamp': datetime.now().isoformat()
                }
                
                qr_image = qr_manager.generate_payment_qr(payment_data, encrypt=True)
                st.session_state.payment_qr = qr_image
                st.session_state.payment_data = payment_data
        
        with col2:
            if 'payment_qr' in st.session_state:
                st.image(f"data:image/png;base64,{st.session_state.payment_qr}", 
                        caption="Encrypted Payment QR Code", width=300)
                
                # Show raw encrypted data
                if 'payment_data' in st.session_state:
                    encrypted_data = encryption_manager.encrypt_transaction(st.session_state.payment_data)
                    st.text_area("Encrypted QR Data", encrypted_data[:200] + "...", height=100)
    
    with tab2:
        st.subheader("Generate Account QR Code")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            account_id = st.text_input("Account ID", value="SRVA12345")
            account_name = st.text_input("Account Name", value="Test SRVA Account")
            bank = st.selectbox("Bank", ["State Bank of India", "ICICI Bank", "HDFC Bank"])
            country = st.selectbox("Country", ["India", "USA", "Germany", "UK"])
            
            if st.button("Generate Account QR", type="primary"):
                account_data = {
                    'account_id': account_id,
                    'account_name': account_name,
                    'bank': bank,
                    'country': country,
                    'currency': 'INR'
                }
                
                qr_image = qr_manager.generate_account_qr(account_data)
                st.session_state.account_qr = qr_image
        
        with col2:
            if 'account_qr' in st.session_state:
                st.image(f"data:image/png;base64,{st.session_state.account_qr}", 
                        caption="Account QR Code", width=300)
    
    with tab3:
        st.subheader("Generate Merchant QR Code")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            merchant_name = st.text_input("Merchant Name", value="RIPT Merchant")
            merchant_account = st.text_input("Merchant Account", value="SRVA54321")
            min_amount = st.number_input("Minimum Amount", value=1.0)
            max_amount = st.number_input("Maximum Amount", value=100000.0)
            
            if st.button("Generate Merchant QR", type="primary"):
                merchant_data = {
                    'merchant_name': merchant_name,
                    'account_id': merchant_account,
                    'min_amount': min_amount,
                    'max_amount': max_amount
                }
                
                qr_image = qr_manager.generate_merchant_qr(merchant_data)
                st.session_state.merchant_qr = qr_image
        
        with col2:
            if 'merchant_qr' in st.session_state:
                st.image(f"data:image/png;base64,{st.session_state.merchant_qr}", 
                        caption="Merchant QR Code", width=300)
    
    with tab4:
        st.subheader("QR Code Scanner & Fraud Detection")
        
        # File upload for QR scanning
        uploaded_file = st.file_uploader("Upload QR Code Image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file is not None:
            # Process uploaded QR code
            qr_data = qr_manager.scan_qr_code(uploaded_file)
            
            if qr_data:
                st.success("QR Code successfully scanned!")
                
                # Try to decrypt if it's encrypted
                try:
                    decrypted_data = encryption_manager.decrypt_transaction(qr_data)
                    st.subheader("Decrypted Transaction Data")
                    st.json(decrypted_data)
                    
                    # Run fraud detection (ensure decrypted_data is a dict)
                    if isinstance(decrypted_data, dict):
                        fraud_result = ai_fraud_detector.detect_fraud(decrypted_data)
                    else:
                        # Try to parse as JSON if it's a string
                        transaction_dict = json.loads(decrypted_data) if isinstance(decrypted_data, str) else decrypted_data
                        fraud_result = ai_fraud_detector.detect_fraud(transaction_dict)
                    
                    if fraud_result['is_fraud']:
                        st.error(f"⚠️ FRAUD DETECTED: {fraud_result['reason']}")
                        st.error(f"Confidence: {fraud_result['confidence']:.2%}")
                    else:
                        st.success("✅ Transaction appears legitimate")
                        st.info(f"Confidence: {fraud_result['confidence']:.2%}")
                        
                except Exception as e:
                    st.warning("Could not decrypt QR data - showing raw content")
                    st.code(qr_data)
            else:
                st.error("No valid QR code found in image")

def show_security_encryption():
    """Security & Encryption Interface"""
    st.header("🔐 Security & Encryption Manager")
    st.markdown("Encrypt/decrypt transaction data and manage security keys")
    
    tab1, tab2, tab3 = st.tabs(["Encrypt Data", "Decrypt Data", "Key Management"])
    
    with tab1:
        st.subheader("Encrypt Transaction Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Manual data entry
            transaction_data = st.text_area(
                "Transaction Data (JSON)",
                value='{"transaction_id": "TXN123", "amount": 1000, "sender": "ACC001", "receiver": "ACC002"}',
                height=200
            )
            
            encryption_method = st.selectbox("Encryption Method", ["AES", "RSA", "Hybrid"])
            
            if st.button("Encrypt Data", type="primary"):
                try:
                    data_dict = json.loads(transaction_data)
                    
                    if encryption_method == "AES":
                        encrypted_data = encryption_manager.encrypt_transaction(data_dict)
                    elif encryption_method == "RSA":
                        encrypted_data = encryption_manager.rsa_encrypt(transaction_data)
                    else:  # Hybrid
                        encrypted_data = encryption_manager.hybrid_encrypt(transaction_data)
                    
                    st.session_state.encrypted_result = encrypted_data
                    st.success("Data encrypted successfully!")
                    
                except json.JSONDecodeError:
                    st.error("Invalid JSON format")
                except Exception as e:
                    st.error(f"Encryption failed: {str(e)}")
        
        with col2:
            if 'encrypted_result' in st.session_state:
                st.subheader("Encrypted Result")
                st.text_area("Encrypted Data", st.session_state.encrypted_result, height=200)
                
                # Show hash
                hash_value = encryption_manager.hash_transaction(st.session_state.encrypted_result)
                st.text_input("SHA-256 Hash", hash_value)
    
    with tab2:
        st.subheader("Decrypt Transaction Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            encrypted_input = st.text_area("Encrypted Data", height=200)
            decryption_method = st.selectbox("Decryption Method", ["AES", "RSA", "Hybrid"])
            
            if st.button("Decrypt Data", type="primary"):
                try:
                    if decryption_method == "AES":
                        decrypted_data = encryption_manager.decrypt_transaction(encrypted_input)
                    elif decryption_method == "RSA":
                        decrypted_data = encryption_manager.rsa_decrypt(encrypted_input)
                    else:  # Hybrid
                        decrypted_data = encryption_manager.hybrid_decrypt(encrypted_input)
                    
                    st.session_state.decrypted_result = decrypted_data
                    st.success("Data decrypted successfully!")
                    
                except Exception as e:
                    st.error(f"Decryption failed: {str(e)}")
        
        with col2:
            if 'decrypted_result' in st.session_state:
                st.subheader("Decrypted Result")
                if isinstance(st.session_state.decrypted_result, dict):
                    st.json(st.session_state.decrypted_result)
                else:
                    st.text_area("Decrypted Data", str(st.session_state.decrypted_result), height=200)
    
    with tab3:
        st.subheader("Key Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Generate New Keys**")
            
            if st.button("Generate AES Key"):
                key = encryption_manager.generate_aes_key()
                st.code(f"AES Key: {key}")
            
            if st.button("Generate RSA Key Pair"):
                private_key, public_key = encryption_manager.generate_rsa_keys()
                st.text_area("Private Key", private_key, height=100)
                st.text_area("Public Key", public_key, height=100)
        
        with col2:
            st.markdown("**Key Information**")
            st.info("🔑 AES keys are 256-bit for symmetric encryption")
            st.info("🔑 RSA keys are 2048-bit for asymmetric encryption")
            st.info("🔑 Hybrid encryption combines both methods")
            st.warning("⚠️ Keep private keys secure and never share them")

def show_ai_fraud_detection():
    """AI Fraud Detection Interface"""
    st.header("🤖 AI Fraud Detection System")
    st.markdown("Machine learning-based spam and fraud detection for transactions")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Single Transaction", "Batch Analysis", "Model Training", "Statistics"])
    
    with tab1:
        st.subheader("Analyze Single Transaction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Transaction input
            transaction_id = st.text_input("Transaction ID", value=f"TXN_{int(datetime.now().timestamp())}")
            amount = st.number_input("Amount", min_value=0.01, value=1000.0)
            sender = st.text_input("Sender", value="ACC001")
            receiver = st.text_input("Receiver", value="ACC002")
            timestamp = st.date_input("Date", value=datetime.now().date())
            status = st.selectbox("Status", ["pending", "completed", "failed"])
            description = st.text_area("Description", value="Standard transaction")
            
            if st.button("Analyze Transaction", type="primary"):
                transaction_data = {
                    'transaction_id': transaction_id,
                    'amount': amount,
                    'sender': sender,
                    'receiver': receiver,
                    'timestamp': timestamp.isoformat(),
                    'status': status,
                    'description': description
                }
                
                # Run fraud detection
                result = ai_fraud_detector.detect_fraud(transaction_data)
                st.session_state.fraud_result = result
                st.session_state.analyzed_transaction = transaction_data
        
        with col2:
            if 'fraud_result' in st.session_state:
                result = st.session_state.fraud_result
                
                if result['is_fraud']:
                    st.error("⚠️ POTENTIAL FRAUD DETECTED")
                    st.error(f"**Reason**: {result['reason']}")
                    st.error(f"**Confidence**: {result['confidence']:.2%}")
                    st.error(f"**Risk Score**: {result['risk_score']:.2f}/10")
                else:
                    st.success("✅ Transaction appears legitimate")
                    st.success(f"**Confidence**: {result['confidence']:.2%}")
                    st.info(f"**Risk Score**: {result['risk_score']:.2f}/10")
                
                # Show detailed analysis
                st.subheader("Detailed Analysis")
                for feature, value in result.get('features', {}).items():
                    st.metric(feature.replace('_', ' ').title(), f"{value:.2f}")
    
    with tab2:
        st.subheader("Batch Transaction Analysis")
        
        # Get recent transactions for analysis
        if st.button("Analyze Recent Transactions"):
            recent_transactions = st.session_state.db_manager.get_recent_transactions(limit=50)
            
            if not recent_transactions.empty:
                fraud_results = []
                
                progress_bar = st.progress(0)
                for i, (_, transaction) in enumerate(recent_transactions.iterrows()):
                    result = ai_fraud_detector.detect_fraud(transaction.to_dict())
                    fraud_results.append({
                        'transaction_id': transaction['transaction_id'],
                        'amount': transaction['amount'],
                        'is_fraud': result['is_fraud'],
                        'confidence': result['confidence'],
                        'risk_score': result['risk_score'],
                        'reason': result['reason']
                    })
                    progress_bar.progress((i + 1) / len(recent_transactions))
                
                fraud_df = pd.DataFrame(fraud_results)
                st.session_state.batch_results = fraud_df
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Analyzed", len(fraud_df))
                with col2:
                    fraud_count = fraud_df['is_fraud'].sum()
                    st.metric("Fraud Detected", fraud_count)
                with col3:
                    fraud_rate = (fraud_count / len(fraud_df)) * 100 if len(fraud_df) > 0 else 0
                    st.metric("Fraud Rate", f"{fraud_rate:.1f}%")
                
                # Show results table
                st.subheader("Analysis Results")
                st.dataframe(fraud_df, use_container_width=True)
                
                # Visualization
                fig = px.scatter(
                    fraud_df, 
                    x='amount', 
                    y='risk_score',
                    color='is_fraud',
                    title="Transaction Risk Analysis",
                    labels={'amount': 'Transaction Amount', 'risk_score': 'Risk Score'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recent transactions found for analysis")
    
    with tab3:
        st.subheader("Model Training & Tuning")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Training Parameters**")
            n_estimators = st.slider("Number of Estimators", 10, 200, 100)
            contamination = st.slider("Contamination Rate", 0.01, 0.5, 0.1)
            
            if st.button("Retrain Model"):
                with st.spinner("Training model..."):
                    # Get training data
                    training_data = st.session_state.db_manager.get_transactions_for_training()
                    
                    if not training_data.empty:
                        # Retrain the model
                        ai_fraud_detector.retrain_model(
                            training_data, 
                            n_estimators=n_estimators,
                            contamination=contamination
                        )
                        st.success("Model retrained successfully!")
                    else:
                        st.error("No training data available")
        
        with col2:
            st.markdown("**Model Information**")
            model_info = ai_fraud_detector.get_model_info()
            
            st.info(f"**Algorithm**: {model_info['algorithm']}")
            st.info(f"**Features Used**: {model_info['n_features']}")
            st.info(f"**Last Trained**: {model_info['last_trained']}")
            st.info(f"**Training Samples**: {model_info['training_samples']}")
    
    with tab4:
        st.subheader("Fraud Detection Statistics")
        
        # Get fraud statistics
        stats = ai_fraud_detector.get_fraud_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Scanned", stats.get('total_scanned', 0))
        with col2:
            st.metric("Fraud Detected", stats.get('fraud_detected', 0))
        with col3:
            fraud_rate = (stats.get('fraud_detected', 0) / max(stats.get('total_scanned', 1), 1)) * 100
            st.metric("Detection Rate", f"{fraud_rate:.2f}%")
        with col4:
            st.metric("Avg Risk Score", f"{stats.get('avg_risk_score', 0):.2f}")
        
        # Fraud trend over time
        fraud_trend = ai_fraud_detector.get_fraud_trend()
        if not fraud_trend.empty:
            fig = px.line(
                fraud_trend,
                x='date',
                y='fraud_count',
                title="Fraud Detection Trend",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Common fraud patterns
        st.subheader("Common Fraud Patterns")
        fraud_patterns = ai_fraud_detector.get_fraud_patterns()
        if fraud_patterns:
            for pattern, count in fraud_patterns.items():
                st.write(f"**{pattern}**: {count} occurrences")

if __name__ == "__main__":
    main()
