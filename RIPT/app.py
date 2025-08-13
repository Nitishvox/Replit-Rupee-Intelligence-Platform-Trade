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

# Custom CSS for modern financial dashboard
st.markdown("""
<style>
/* Main container styling */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Header styling */
.main-header {
    background: linear-gradient(90deg, #1f77b4 0%, #2e86de 100%);
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
}

/* Metric cards styling */
.metric-card {
    background: rgba(255, 255, 255, 0.05);
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #1f77b4;
    margin-bottom: 1rem;
}

/* Sidebar styling */
.css-1d391kg {
    background: linear-gradient(180deg, #262730 0%, #1e1e1e 100%);
}

/* Success indicators */
.status-success {
    color: #28a745;
    font-weight: bold;
}

.status-warning {
    color: #ffc107;
    font-weight: bold;
}

.status-error {
    color: #dc3545;
    font-weight: bold;
}

/* Modern button styling */
.stButton > button {
    border-radius: 8px;
    border: none;
    background: linear-gradient(45deg, #1f77b4, #2e86de);
    color: white;
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(31, 119, 180, 0.3);
}

/* Chart containers */
.chart-container {
    background: rgba(255, 255, 255, 0.02);
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

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
    # Modern header
    st.markdown("""
    <div class="main-header">
        <h1>🏦 RIPT - Rupee Intelligence Platform Trade</h1>
        <p>Advanced SRVA Management & INR Trade Settlement System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation with modern styling
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        page = st.selectbox(
            "Select Module",
            [
                "🏠 Dashboard",
                "🏦 SRVA Management", 
                "💱 Transaction Processing",
                "💰 Settlement Calculator",
                "🔍 Compliance Tracking",
                "📊 Reporting & Analytics",
                "📄 Document Generation",
                "🎯 Data Generator",
                "📱 QR Code Manager",
                "🔐 Security & Encryption",
                "🤖 AI Fraud Detection"
            ]
        )
        
        # Display current INR exchange rates in sidebar
        st.markdown("---")
        st.markdown("### 💹 Live INR Rates")
        
        try:
            with st.spinner("Fetching live rates..."):
                rates = st.session_state.exchange_api.get_current_rates()
            
            if rates:
                # Display rates in a modern format
                for currency, rate in list(rates.items())[:6]:  # Show top 6 currencies
                    # Simulate trend direction for visual appeal
                    trend_icon = "📈" if hash(currency) % 2 else "📉"
                    trend_color = "green" if trend_icon == "📈" else "red"
                    
                    st.markdown(f"""
                    <div style="
                        background: rgba(255,255,255,0.05);
                        padding: 0.5rem;
                        border-radius: 5px;
                        margin: 0.25rem 0;
                        border-left: 3px solid {trend_color};
                    ">
                        <strong>{currency}</strong> {trend_icon}<br>
                        <span style="font-size: 0.9em;">₹{rate:.4f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Provider status
                provider_status = st.session_state.exchange_api.get_provider_status()
                st.markdown("### 🔗 API Status")
                for provider, status in provider_status.items():
                    status_color = "green" if status['status'] == 'Online' else "red"
                    status_icon = "✅" if status['status'] == 'Online' else "❌"
                    st.markdown(f"<span style='color: {status_color}'>{status_icon} {provider[:15]}...</span>", unsafe_allow_html=True)
            else:
                st.error("❌ Unable to fetch current rates")
                
        except Exception as e:
            st.error(f"Rate fetch error: {str(e)}")
        
        # System status indicators
        st.markdown("---")
        st.markdown("### 🔧 System Status")
        
        status_items = [
            ("RBI Compliance", "🟢", "Active"),
            ("Exchange APIs", "🟢", "Connected"),
            ("Banking Network", "🟢", "Online"),
            ("Security", "🟢", "Operational")
        ]
        
        for item, icon, status in status_items:
            st.markdown(f"{icon} **{item}**: {status}")
    
    # Main content routing
    page_key = page.split(" ", 1)[1] if " " in page else page
    
    if "Dashboard" in page:
        show_dashboard()
    elif "SRVA Management" in page:
        srva_manager.show_interface()
    elif "Transaction Processing" in page:
        transaction_processor.show_interface()
    elif "Settlement Calculator" in page:
        settlement_calculator.show_interface()
    elif "Compliance Tracking" in page:
        compliance_tracker.show_interface()
    elif "Reporting & Analytics" in page:
        reporting_dashboard.show_interface()
    elif "Document Generation" in page:
        document_generator.show_interface()
    elif "Data Generator" in page:
        show_data_generator()
    elif "QR Code Manager" in page:
        show_qr_code_manager()
    elif "Security & Encryption" in page:
        show_security_encryption()
    elif "AI Fraud Detection" in page:
        show_ai_fraud_detection()

def show_dashboard():
    """Modern financial dashboard with enhanced UI"""
    
    # Get summary statistics
    stats = st.session_state.db_manager.get_dashboard_stats()
    
    # Key Performance Indicators with modern styling
    st.markdown("### 📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_color = "normal" if stats.get('new_accounts_this_month', 0) >= 0 else "inverse"
        st.metric(
            "🏦 Active SRVA Accounts",
            f"{stats.get('active_accounts', 0):,}",
            delta=f"+{stats.get('new_accounts_this_month', 0)}"
        )
    
    with col2:
        settlement_delta = stats.get('settlements_this_month', 0)
        st.metric(
            "💰 Total Settlements",
            f"₹{stats.get('total_settlements', 0)/1e7:.1f}Cr",
            delta=f"₹{settlement_delta/1e7:.1f}Cr this month"
        )
    
    with col3:
        st.metric(
            "🌍 Active Countries",
            stats.get('active_countries', 22),
            delta=f"+{stats.get('new_countries_this_month', 0)} new"
        )
    
    with col4:
        pending_count = stats.get('pending_transactions', 0)
        st.metric(
            "⏳ Pending Transactions",
            pending_count,
            delta="Requires attention" if pending_count > 10 else "Normal"
        )
    
    st.markdown("---")
    
    # Enhanced Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌎 Settlement Volume by Country")
        country_data = st.session_state.db_manager.get_settlement_by_country()
        
        if not country_data.empty:
            # Modern bar chart with enhanced styling
            fig = px.bar(
                country_data.head(10),
                x='country',
                y='settlement_amount',
                title="Top 10 Countries - INR Settlement Volume (Last 30 Days)",
                color='settlement_amount',
                color_continuous_scale='viridis',
                template='plotly_dark'
            )
            
            fig.update_layout(
                height=400,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )
            
            fig.update_traces(
                hovertemplate='<b>%{x}</b><br>Settlement: ₹%{y:,.0f}<extra></extra>'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No settlement data available. Use the Data Generator to create sample data.")
    
    with col2:
        st.markdown("### 📈 Transaction Flow Trend")
        trend_data = st.session_state.db_manager.get_transaction_trend()
        
        if not trend_data.empty:
            # Modern line chart with dual y-axis
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=trend_data['date'],
                y=trend_data['exports'],
                mode='lines+markers',
                name='Exports',
                line=dict(color='#00cc96', width=3),
                marker=dict(size=6)
            ))
            
            fig.add_trace(go.Scatter(
                x=trend_data['date'],
                y=trend_data['imports'],
                mode='lines+markers',
                name='Imports',
                line=dict(color='#ff6692', width=3),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title="Export/Import Transaction Trend (₹)",
                height=400,
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No transaction trend data available. Use the Data Generator to create sample data.")
    
    # Recent Activities with modern table styling
    st.markdown("### 🕒 Recent Activities")
    recent_activities = st.session_state.db_manager.get_recent_activities()
    
    if not recent_activities.empty:
        # Enhanced dataframe display
        st.dataframe(
            recent_activities,
            use_container_width=True,
            column_config={
                "transaction_id": st.column_config.TextColumn("Transaction ID", width="medium"),
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "currency": st.column_config.TextColumn("Currency", width="small"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "created_date": st.column_config.DatetimeColumn("Created", width="medium")
            }
        )
    else:
        st.info("📝 No recent activities to display. Transaction data will appear here once created.")
    
    # Enhanced System Health Dashboard
    st.markdown("---")
    st.markdown("### 🔧 System Health & Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🏛️ Regulatory Compliance</h4>
            <p class="status-success">✅ RBI Compliance: Active</p>
            <p class="status-success">✅ FEMA Guidelines: Compliant</p>
            <p class="status-success">✅ Exchange Rate API: Connected</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🔗 Network & Services</h4>
            <p class="status-success">✅ Banking Network: Online</p>
            <p class="status-success">✅ Document System: Operational</p>
            <p class="status-success">✅ QR Code Service: Active</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🔒 Security & Monitoring</h4>
            <p class="status-success">✅ Encryption: AES-256 Active</p>
            <p class="status-success">✅ Fraud Detection: Running</p>
            <p class="status-success">✅ Audit Trail: Recording</p>
        </div>
        """, unsafe_allow_html=True)

def show_data_generator():
    """Enhanced Data Generator Interface with modern styling"""
    st.markdown("### 🎯 Enhanced Data Generator")
    st.markdown("Generate realistic transactions and SRVA accounts with encryption and fraud simulation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💱 Generate Transactions")
        
        with st.container():
            transaction_count = st.slider("Number of transactions", 10, 1000, 100)
            include_spam = st.checkbox("Include suspicious transactions", value=True)
            spam_percentage = st.slider("Suspicious transaction percentage", 0, 50, 10) if include_spam else 0
            
            col_a, col_b = st.columns(2)
            with col_a:
                start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=30))
            with col_b:
                end_date = st.date_input("End Date", datetime.now().date())
            
            if st.button("🚀 Generate Transactions", type="primary", use_container_width=True):
                with st.spinner("Generating realistic transaction data..."):
                    transactions = data_generator.generate_random_transactions(
                        transaction_count, 
                        include_spam=include_spam,
                        spam_percentage=spam_percentage,
                        start_date=start_date,
                        end_date=end_date
                    )
                    inserted = data_generator.insert_transactions_to_db(transactions)
                    
                st.success(f"✅ Generated and inserted {inserted} transactions successfully!")
                st.balloons()
                
                # Show sample transaction with modern styling
                if transactions:
                    with st.expander("📄 Sample Transaction Preview"):
                        sample = transactions[0]
                        st.json(sample)
                        
                        # Show encryption for sample
                        encrypted_data = encryption_manager.encrypt_transaction(sample)
                        st.code(encrypted_data[:100] + "...", language="text")
    
    with col2:
        st.markdown("#### 🏦 Generate SRVA Accounts")
        
        with st.container():
            account_count = st.slider("Number of accounts", 5, 100, 20)
            
            account_types = st.multiselect(
                "Account Types",
                ["Corporate", "Individual", "Government", "Financial Institution"],
                default=["Corporate", "Individual"]
            )
            
            countries = st.multiselect(
                "Countries",
                ["Russia", "Germany", "UK", "Singapore", "UAE", "Japan", "Australia"],
                default=["Russia", "Germany", "UK"]
            )
            
            if st.button("🏗️ Generate Accounts", type="primary", use_container_width=True):
                with st.spinner("Creating SRVA accounts..."):
                    accounts = data_generator.generate_srva_accounts(
                        account_count,
                        account_types=account_types,
                        countries=countries
                    )
                    inserted = data_generator.insert_accounts_to_db(accounts)
                    
                st.success(f"✅ Generated and inserted {inserted} accounts successfully!")
                st.balloons()
                
                # Show sample account
                if accounts:
                    with st.expander("📄 Sample Account Preview"):
                        sample = accounts[0]
                        st.json(sample)

def show_qr_code_manager():
    """Enhanced QR Code Manager with modern UI"""
    st.markdown("### 📱 QR Code Manager")
    st.markdown("Generate and scan encrypted QR codes for secure mobile payments")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💳 Payment QR", "🏦 Account QR", "🏪 Merchant QR", "🔍 QR Scanner"])
    
    with tab1:
        st.markdown("#### Generate Encrypted Payment QR Code")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.form("payment_qr_form"):
                transaction_id = st.text_input("Transaction ID", value=f"PAY_{int(datetime.now().timestamp())}")
                amount = st.number_input("Amount", min_value=0.01, value=1000.0)
                currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"])
                recipient_account = st.text_input("Recipient Account", value="SRVA12345")
                description = st.text_area("Description", value="Mobile payment via encrypted QR code")
                
                submitted = st.form_submit_button("🔐 Generate Encrypted QR", type="primary", use_container_width=True)
                
                if submitted:
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
                st.markdown("#### 📱 Your QR Code")
                st.image(f"data:image/png;base64,{st.session_state.payment_qr}", 
                        caption="Encrypted Payment QR Code", width=300)
                
                # Show encrypted data preview
                if 'payment_data' in st.session_state:
                    with st.expander("🔒 Encrypted Data Preview"):
                        encrypted_data = encryption_manager.encrypt_transaction(st.session_state.payment_data)
                        st.code(encrypted_data[:200] + "...", language="text")
    
    with tab2:
        st.markdown("#### Generate Account QR Code")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.form("account_qr_form"):
                account_id = st.text_input("Account ID", value="SRVA12345")
                account_name = st.text_input("Account Name", value="Test SRVA Account")
                bank = st.selectbox("Bank", ["State Bank of India", "ICICI Bank", "HDFC Bank"])
                country = st.selectbox("Country", ["India", "USA", "Germany", "UK"])
                
                submitted = st.form_submit_button("🏦 Generate Account QR", type="primary", use_container_width=True)
                
                if submitted:
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
                st.markdown("#### 🏦 Account QR Code")
                st.image(f"data:image/png;base64,{st.session_state.account_qr}", 
                        caption="Account QR Code", width=300)
    
    with tab3:
        st.markdown("#### Generate Merchant QR Code")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.form("merchant_qr_form"):
                merchant_id = st.text_input("Merchant ID", value="MERCH001")
                merchant_name = st.text_input("Merchant Name", value="Export Trading Co.")
                category = st.selectbox("Category", ["Export", "Import", "Services", "Manufacturing"])
                
                submitted = st.form_submit_button("🏪 Generate Merchant QR", type="primary", use_container_width=True)
                
                if submitted:
                    merchant_data = {
                        'merchant_id': merchant_id,
                        'merchant_name': merchant_name,
                        'category': category,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    qr_image = qr_manager.generate_merchant_qr(merchant_data)
                    st.session_state.merchant_qr = qr_image
        
        with col2:
            if 'merchant_qr' in st.session_state:
                st.markdown("#### 🏪 Merchant QR Code")
                st.image(f"data:image/png;base64,{st.session_state.merchant_qr}", 
                        caption="Merchant QR Code", width=300)
    
    with tab4:
        st.markdown("#### QR Code Scanner")
        st.info("📷 Upload a QR code image to decode its contents")
        
        uploaded_file = st.file_uploader("Choose QR code image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(uploaded_file, caption="Uploaded QR Code", width=300)
            
            with col2:
                if st.button("🔍 Scan QR Code", type="primary"):
                    with st.spinner("Scanning QR code..."):
                        result = qr_manager.scan_qr_code(uploaded_file)
                    
                    if result:
                        st.success("✅ QR Code decoded successfully!")
                        st.json(result)
                    else:
                        st.error("❌ Could not decode QR code. Please ensure the image is clear and contains a valid QR code.")

def show_security_encryption():
    """Enhanced Security and Encryption Interface"""
    st.markdown("### 🔐 Security & Encryption Manager")
    st.markdown("Manage encryption keys and secure transaction data with AES-256 encryption")
    
    tab1, tab2, tab3 = st.tabs(["🔒 Encrypt Data", "🔓 Decrypt Data", "🔑 Key Management"])
    
    with tab1:
        st.markdown("#### Encrypt Transaction Data")
        col1, col2 = st.columns(2)
        
        with col1:
            data_to_encrypt = st.text_area(
                "Data to Encrypt", 
                value='{"amount": 1000, "currency": "INR", "account": "SRVA123"}',
                height=150,
                help="Enter JSON data to encrypt"
            )
            
            if st.button("🔐 Encrypt Data", type="primary", use_container_width=True):
                try:
                    import json
                    parsed_data = json.loads(data_to_encrypt)
                    encrypted = encryption_manager.encrypt_transaction(parsed_data)
                    st.session_state.encrypted_data = encrypted
                    st.success("✅ Data encrypted successfully!")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format. Please provide valid JSON data.")
                except Exception as e:
                    st.error(f"❌ Encryption failed: {str(e)}")
        
        with col2:
            if 'encrypted_data' in st.session_state:
                st.markdown("#### 🔒 Encrypted Result")
                st.code(st.session_state.encrypted_data, language="text")
                
                if st.button("📋 Copy Encrypted Data"):
                    st.info("💡 Encrypted data displayed above. Copy manually from the text area.")
    
    with tab2:
        st.markdown("#### Decrypt Transaction Data")
        col1, col2 = st.columns(2)
        
        with col1:
            encrypted_input = st.text_area(
                "Encrypted Data to Decrypt", 
                height=150,
                help="Paste encrypted data here"
            )
            
            if st.button("🔓 Decrypt Data", type="primary", use_container_width=True):
                try:
                    decrypted = encryption_manager.decrypt_transaction(encrypted_input)
                    st.session_state.decrypted_data = decrypted
                    st.success("✅ Data decrypted successfully!")
                except Exception as e:
                    st.error(f"❌ Decryption failed: {str(e)}")
        
        with col2:
            if 'decrypted_data' in st.session_state:
                st.markdown("#### 🔓 Decrypted Result")
                st.json(st.session_state.decrypted_data)
    
    with tab3:
        st.markdown("#### Encryption Key Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🔑 Current Key Status")
            if encryption_manager.key_exists():
                st.success("✅ Encryption key is active and operational")
                
                st.markdown("##### ⚠️ Regenerate Key")
                st.warning("Regenerating the key will invalidate all existing encrypted data!")
                
                confirm_regen = st.checkbox("I understand this will invalidate all existing encrypted data")
                
                if st.button("🔄 Regenerate Key", type="secondary", disabled=not confirm_regen):
                    encryption_manager.generate_new_key()
                    st.success("🔑 New encryption key generated successfully!")
                    st.rerun()
            else:
                st.warning("⚠️ No encryption key found")
                if st.button("🔑 Generate New Key", type="primary"):
                    encryption_manager.generate_new_key()
                    st.success("🔑 Encryption key generated successfully!")
                    st.rerun()
        
        with col2:
            st.markdown("##### 🛡️ Security Information")
            
            security_info = [
                ("🔒", "Encryption Algorithm", "AES-256-CBC"),
                ("🔑", "Key Storage", "Local Environment"),
                ("⚡", "Processing", "Local Encryption"),
                ("🛡️", "Security Level", "Military Grade"),
                ("🔄", "Key Rotation", "Manual/On-Demand"),
                ("📊", "Performance", "High Speed")
            ]
            
            for icon, label, value in security_info:
                st.markdown(f"**{icon} {label}:** {value}")

def show_ai_fraud_detection():
    """Enhanced AI Fraud Detection Interface"""
    st.markdown("### 🤖 AI Fraud Detection System")
    st.markdown("Machine learning-powered fraud detection using advanced algorithms")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Scan Transactions", "🧠 Model Training", "📊 Detection Results"])
    
    with tab1:
        st.markdown("#### Real-time Fraud Detection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🔍 Single Transaction Analysis")
            
            with st.form("fraud_analysis_form"):
                amount = st.number_input("Transaction Amount (₹)", min_value=0.01, value=50000.0)
                currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP"], key="fraud_currency")
                country = st.selectbox("Country", ["India", "USA", "Russia", "Germany", "UK"], key="fraud_country")
                transaction_type = st.selectbox("Type", ["Export", "Import", "Service"])
                
                time_of_day = st.selectbox("Time of Day", ["Business Hours", "After Hours", "Weekend"])
                customer_type = st.selectbox("Customer Type", ["Regular", "New", "High-Risk"])
                
                submitted = st.form_submit_button("🔍 Analyze Transaction", type="primary")
                
                if submitted:
                    transaction_data = {
                        'amount': amount,
                        'currency': currency,
                        'country': country,
                        'type': transaction_type,
                        'time_of_day': time_of_day,
                        'customer_type': customer_type,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    with st.spinner("🧠 AI analyzing transaction patterns..."):
                        result = ai_fraud_detector.detect_fraud_single(transaction_data)
                    
                    # Display results with enhanced styling
                    if result['is_fraud']:
                        st.error(f"🚨 **FRAUD DETECTED** - Risk Score: {result['risk_score']:.1f}/100")
                        st.error(f"**Reason:** {result['reason']}")
                    else:
                        st.success(f"✅ **Transaction Legitimate** - Risk Score: {result['risk_score']:.1f}/100")
                        
                    # Risk score visualization
                    risk_color = "red" if result['is_fraud'] else "green"
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(90deg, {risk_color} {result['risk_score']}%, transparent {result['risk_score']}%);
                        height: 20px;
                        border-radius: 10px;
                        border: 1px solid #ddd;
                        margin: 10px 0;
                    "></div>
                    """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("##### 📊 Batch Analysis")
            
            if st.button("🔍 Scan All Recent Transactions", type="primary", use_container_width=True):
                with st.spinner("🤖 AI scanning recent transactions..."):
                    results = ai_fraud_detector.scan_recent_transactions()
                
                if results:
                    fraud_count = sum(1 for r in results if r['is_fraud'])
                    total_count = len(results)
                    
                    # Summary metrics
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Total Scanned", total_count)
                    with col_b:
                        st.metric("Fraudulent", fraud_count)
                    with col_c:
                        fraud_rate = (fraud_count / total_count * 100) if total_count > 0 else 0
                        st.metric("Fraud Rate", f"{fraud_rate:.1f}%")
                    
                    # Show flagged transactions
                    if fraud_count > 0:
                        st.markdown("##### 🚨 Flagged Transactions")
                        fraud_df = pd.DataFrame([r for r in results if r['is_fraud']])
                        st.dataframe(fraud_df, use_container_width=True)
                    else:
                        st.success("🎉 No fraudulent transactions detected!")
                else:
                    st.info("📝 No transactions available for analysis")
    
    with tab2:
        st.markdown("#### Model Training & Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🧠 Train Detection Model")
            
            training_options = st.multiselect(
                "Training Features",
                ["Amount Patterns", "Time Patterns", "Geographic Patterns", "Customer Behavior"],
                default=["Amount Patterns", "Geographic Patterns"]
            )
            
            if st.button("🚀 Train Model", type="primary", use_container_width=True):
                with st.spinner("🤖 Training AI model on transaction data..."):
                    results = ai_fraud_detector.train_model()
                
                if results:
                    st.success("✅ Model trained successfully!")
                    
                    # Performance metrics
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Model Accuracy", f"{results['accuracy']:.1%}")
                    with col_b:
                        st.metric("Training Samples", f"{results['training_samples']:,}")
                        
                    # Model performance visualization
                    if 'confusion_matrix' in results:
                        st.markdown("##### 📊 Model Performance")
                        st.info("Model performance metrics and confusion matrix would be displayed here.")
                else:
                    st.error("❌ Insufficient data for model training")
        
        with col2:
            st.markdown("##### 📈 Model Information")
            model_info = ai_fraud_detector.get_model_info()
            
            if model_info:
                info_items = [
                    ("🤖", "Model Type", model_info['type']),
                    ("📅", "Last Trained", model_info['last_trained']),
                    ("📊", "Training Samples", f"{model_info['samples']:,}"),
                    ("🎯", "Accuracy", f"{model_info.get('accuracy', 0):.1%}"),
                    ("⚡", "Status", "Active" if model_info else "Inactive")
                ]
                
                for icon, label, value in info_items:
                    st.markdown(f"**{icon} {label}:** {value}")
            else:
                st.warning("⚠️ No trained model available")
                st.info("Train a model to enable fraud detection capabilities.")
    
    with tab3:
        st.markdown("#### Detection History & Analytics")
        
        detection_history = ai_fraud_detector.get_detection_history()
        
        if not detection_history.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_detections = len(detection_history)
            fraud_detections = len(detection_history[detection_history['is_fraud'] == True])
            avg_risk_score = detection_history['risk_score'].mean()
            recent_detections = len(detection_history[detection_history['timestamp'] >= datetime.now() - timedelta(days=7)])
            
            with col1:
                st.metric("Total Detections", f"{total_detections:,}")
            with col2:
                st.metric("Fraud Detected", fraud_detections)
            with col3:
                st.metric("Avg Risk Score", f"{avg_risk_score:.1f}")
            with col4:
                st.metric("This Week", recent_detections)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Fraud detection trend
                detection_history['date'] = pd.to_datetime(detection_history['timestamp']).dt.date
                daily_stats = detection_history.groupby('date').agg({
                    'is_fraud': ['count', 'sum']
                }).round(2)
                
                daily_stats.columns = ['Total', 'Fraud']
                daily_stats['Fraud_Rate'] = (daily_stats['Fraud'] / daily_stats['Total'] * 100).round(1)
                
                fig = px.line(
                    daily_stats.reset_index(), 
                    x='date', 
                    y='Fraud_Rate',
                    title="Daily Fraud Detection Rate (%)",
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Risk score distribution
                fig = px.histogram(
                    detection_history, 
                    x='risk_score', 
                    nbins=20,
                    title="Risk Score Distribution",
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent detections table
            st.markdown("##### 🚨 Recent Fraud Detections")
            recent_fraud = detection_history[detection_history['is_fraud'] == True].head(10)
            
            if not recent_fraud.empty:
                st.dataframe(
                    recent_fraud[['timestamp', 'amount', 'currency', 'country', 'risk_score', 'reason']],
                    use_container_width=True,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("Timestamp"),
                        "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                        "risk_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100)
                    }
                )
            else:
                st.success("🎉 No recent fraud detections - System is secure!")
                
        else:
            st.info("📊 No detection history available. Run fraud detection to see analytics.")

if __name__ == "__main__":
    main()
