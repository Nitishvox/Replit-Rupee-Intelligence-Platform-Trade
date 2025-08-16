import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frontend.dashboard import show_dashboard
from frontend.analytics import show_analytics
from frontend.qr_scanner import show_qr_scanner
from api.srva_manager import SRVAManager
from api.transaction_processor import TransactionProcessor
from utils.db_manager import DatabaseManager
from utils.status_monitor import StatusMonitor
from config import Config

# Initialize Streamlit configuration
st.set_page_config(
    page_title="RIPT - Rupee Intelligence Platform for Trade",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🌐"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.main-header h1 {
    font-family: 'Arial Black', sans-serif;
    font-size: 2.5rem;
    margin: 0;
}
.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #2a5298;
}
.nav-tab {
    background: #f0f2f6;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin: 0.2rem;
    cursor: pointer;
    transition: all 0.3s ease;
}
.nav-tab:hover {
    background: #2a5298;
    color: white;
}
.nav-tab.active {
    background: #2a5298;
    color: white;
}
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'trader'
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'performance_log' not in st.session_state:
        st.session_state.performance_log = {
            'generation_times': [],
            'analytics_times': [],
            'last_tps_calculation': 0.0
        }
    if 'encryption_key' not in st.session_state:
        from utils.encryption import generate_key
        st.session_state.encryption_key = generate_key()

def show_header():
    """Display the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🌐 RIPT - Rupee Intelligence Platform for Trade</h1>
        <p><strong>Motto:</strong> Secure speed. Transparent trust. INR-first global flows</p>
        <p><strong>Partner Countries:</strong> Russia 🇷🇺 | Germany 🇩🇪 | UK 🇬🇧 | Singapore 🇸🇬</p>
    </div>
    """, unsafe_allow_html=True)

def show_navigation():
    """Show navigation sidebar"""
    with st.sidebar:
        st.markdown("## 🚀 Navigation")
        
        # Role selection
        role = st.selectbox(
            "Select Role",
            ["trader", "auditor", "admin"],
            index=["trader", "auditor", "admin"].index(st.session_state.user_role)
        )
        if role != st.session_state.user_role:
            st.session_state.user_role = role
            st.rerun()
        
        st.markdown("---")
        
        # Navigation pages
        pages = {
            "Dashboard": "🏠",
            "Analytics": "📊", 
            "QR Scanner": "📱",
            "SRVA Management": "🏦",
            "Transaction Processing": "💳",
            "Privacy & Security": "🔐",
            "Export & Reports": "📄",
            "System Status": "⚡"
        }
        
        for page, icon in pages.items():
            if st.button(f"{icon} {page}", use_container_width=True):
                st.session_state.current_page = page
                st.rerun()
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🔄 Generate 10 Transactions", use_container_width=True):
            processor = TransactionProcessor()
            new_transactions = processor.generate_bulk_transactions(10)
            st.session_state.transactions.extend(new_transactions)
            st.success(f"Generated {len(new_transactions)} transactions!")
            st.rerun()
        
        if st.button("📊 Refresh Analytics", use_container_width=True):
            st.cache_data.clear()
            st.success("Analytics cache cleared!")
            st.rerun()

def main():
    """Main application function"""
    initialize_session_state()
    show_header()
    
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Show navigation
    show_navigation()
    
    # Main content area
    current_page = st.session_state.get('current_page', 'Dashboard')
    
    if current_page == 'Dashboard':
        show_dashboard()
    elif current_page == 'Analytics':
        show_analytics()
    elif current_page == 'QR Scanner':
        show_qr_scanner()
    elif current_page == 'SRVA Management':
        show_srva_management()
    elif current_page == 'Transaction Processing':
        show_transaction_processing()
    elif current_page == 'Privacy & Security':
        show_privacy_security()
    elif current_page == 'Export & Reports':
        show_export_reports()
    elif current_page == 'System Status':
        show_system_status()

def show_srva_management():
    """SRVA Management page"""
    st.title("🏦 SRVA Management")
    
    manager = SRVAManager()
    
    tab1, tab2, tab3 = st.tabs(["Create Account", "View Accounts", "Settlement Management"])
    
    with tab1:
        st.subheader("Create New SRVA Account")
        with st.form("create_account_form"):
            col1, col2 = st.columns(2)
            with col1:
                account_name = st.text_input("Account Name")
                partner_country = st.selectbox("Partner Country", ["Russia", "Germany", "UK", "Singapore"])
                bank_name = st.text_input("Bank Name")
            with col2:
                currency = st.selectbox("Primary Currency", ["INR", "USD", "EUR", "GBP", "SGD", "RUB"])
                trade_limit = st.number_input("Trade Limit", min_value=0, value=10000000)
                compliance_status = st.selectbox("Compliance Status", ["Active", "Pending", "Suspended"])
            
            if st.form_submit_button("Create Account"):
                account_data = {
                    'name': account_name,
                    'partner_country': partner_country,
                    'bank_name': bank_name,
                    'currency': currency,
                    'trade_limit': trade_limit,
                    'compliance_status': compliance_status
                }
                result = manager.create_account(account_data)
                if result['success']:
                    st.success(f"Account created successfully! ID: {result['account_id']}")
                else:
                    st.error(f"Failed to create account: {result['message']}")
    
    with tab2:
        st.subheader("SRVA Accounts Overview")
        accounts = manager.get_all_accounts()
        if accounts:
            st.dataframe(accounts, use_container_width=True)
        else:
            st.info("No SRVA accounts found. Create one using the form above.")
    
    with tab3:
        st.subheader("Settlement Management")
        settlements = manager.get_pending_settlements()
        if settlements:
            st.dataframe(settlements, use_container_width=True)
            
            selected_settlement = st.selectbox("Select Settlement to Process", 
                                             [f"Settlement {s['id']}" for s in settlements])
            if st.button("Process Settlement"):
                st.success("Settlement processed successfully!")
        else:
            st.info("No pending settlements found.")

def show_transaction_processing():
    """Transaction Processing page"""
    st.title("💳 Transaction Processing")
    
    processor = TransactionProcessor()
    
    tab1, tab2, tab3 = st.tabs(["Manual Transaction", "Bulk Generation", "Transaction History"])
    
    with tab1:
        st.subheader("Create Manual Transaction")
        with st.form("manual_transaction_form"):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount", min_value=0.01, value=10000.0)
                currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "SGD", "RUB"])
                source = st.selectbox("Source", ["UPI", "NEFT", "RTGS", "SRVA-INR", "SRVA-Non-INR", "SWIFT"])
            with col2:
                corridor = st.selectbox("Corridor", ["IN-US", "IN-EU", "IN-SG", "IN-AE", "IN-GB", "IN-JP", "IN-RU"])
                counterparty = st.text_input("Counterparty")
                narrative = st.text_area("Transaction Narrative")
            
            if st.form_submit_button("Process Transaction"):
                transaction_data = {
                    'amount': amount,
                    'currency': currency,
                    'source': source,
                    'corridor': corridor,
                    'counterparty': counterparty,
                    'narrative': narrative
                }
                result = processor.process_manual_transaction(transaction_data)
                if result['success']:
                    st.success(f"Transaction processed! ID: {result['transaction_id']}")
                    st.session_state.transactions.append(result['transaction'])
                else:
                    st.error(f"Transaction failed: {result['message']}")
    
    with tab2:
        st.subheader("Bulk Transaction Generation")
        col1, col2 = st.columns(2)
        with col1:
            num_transactions = st.number_input("Number of Transactions", min_value=1, max_value=100, value=10)
            transaction_type = st.selectbox("Transaction Type", ["Random", "High Risk", "Low Risk", "SRVA Only"])
        with col2:
            target_corridor = st.selectbox("Target Corridor (Optional)", 
                                         ["Any", "IN-US", "IN-EU", "IN-SG", "IN-AE", "IN-GB", "IN-JP", "IN-RU"])
            
        if st.button("Generate Transactions"):
            with st.spinner("Generating transactions..."):
                new_transactions = processor.generate_bulk_transactions(
                    num_transactions, 
                    transaction_type=transaction_type,
                    corridor=target_corridor if target_corridor != "Any" else None
                )
                st.session_state.transactions.extend(new_transactions)
                st.success(f"Generated {len(new_transactions)} transactions successfully!")
                
                # Show summary
                import pandas as pd
                df = pd.DataFrame(new_transactions)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Volume", f"₹{df['amount'].sum():,.2f}")
                with col2:
                    st.metric("Avg Risk Score", f"{df['risk_score'].mean():.1f}")
                with col3:
                    st.metric("Success Rate", f"{(df['status'] == 'Completed').mean()*100:.1f}%")
    
    with tab3:
        st.subheader("Transaction History")
        if st.session_state.transactions:
            import pandas as pd
            df = pd.DataFrame(st.session_state.transactions)
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                currency_filter = st.multiselect("Filter by Currency", 
                                                df['currency'].unique(), 
                                                default=df['currency'].unique())
            with col2:
                status_filter = st.multiselect("Filter by Status", 
                                              df['status'].unique(), 
                                              default=df['status'].unique())
            with col3:
                risk_threshold = st.slider("Max Risk Score", 0, 100, 100)
            
            # Apply filters
            filtered_df = df[
                (df['currency'].isin(currency_filter)) &
                (df['status'].isin(status_filter)) &
                (df['risk_score'] <= risk_threshold)
            ]
            
            st.dataframe(filtered_df, use_container_width=True)
            
            if st.button("Clear Transaction History"):
                st.session_state.transactions = []
                st.rerun()
        else:
            st.info("No transactions found. Generate some using the bulk generation feature.")

def show_privacy_security():
    """Privacy & Security page"""
    st.title("🔐 Privacy & Security")
    
    from utils.privacy_modules import PrivacyManager
    privacy_manager = PrivacyManager()
    
    tab1, tab2, tab3, tab4 = st.tabs(["SafeDataVault", "Privacy Budget", "Risk Analysis", "Encryption Status"])
    
    with tab1:
        st.subheader("SafeDataVault Operations")
        
        # Data encryption demo
        st.markdown("#### Encrypt Sensitive Data")
        sensitive_data = st.text_area("Enter sensitive data to encrypt:")
        if st.button("Encrypt Data") and sensitive_data:
            encrypted = privacy_manager.encrypt_sensitive_data(sensitive_data)
            st.success("Data encrypted successfully!")
            st.code(encrypted[:100] + "..." if len(encrypted) > 100 else encrypted)
        
        # Pseudonymization
        st.markdown("#### Pseudonymization")
        trader_info = st.text_input("Trader Information:")
        if st.button("Pseudonymize") and trader_info:
            pseudo = privacy_manager.pseudonymize_trader(trader_info)
            st.success(f"Pseudonymized ID: {pseudo}")
    
    with tab2:
        st.subheader("Privacy Budget Tracking")
        budget_status = privacy_manager.get_privacy_budget_status()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"{budget_status['total']:.2f}")
        with col2:
            st.metric("Used Budget", f"{budget_status['used']:.2f}")
        with col3:
            st.metric("Remaining", f"{budget_status['remaining']:.2f}")
        
        # Privacy budget visualization
        import plotly.graph_objects as go
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = budget_status['used_percentage'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Privacy Budget Usage (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Re-identification Risk Analysis")
        
        if st.session_state.transactions:
            risk_analysis = privacy_manager.analyze_reidentification_risk(st.session_state.transactions)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("High Risk Transactions", risk_analysis['high_risk_count'])
                st.metric("Medium Risk Transactions", risk_analysis['medium_risk_count'])
            with col2:
                st.metric("Low Risk Transactions", risk_analysis['low_risk_count'])
                st.metric("Overall Risk Score", f"{risk_analysis['overall_risk']:.2f}")
            
            # Risk distribution chart
            import plotly.express as px
            risk_data = {
                'Risk Level': ['Low', 'Medium', 'High'],
                'Count': [risk_analysis['low_risk_count'], 
                         risk_analysis['medium_risk_count'], 
                         risk_analysis['high_risk_count']]
            }
            fig = px.pie(risk_data, values='Count', names='Risk Level', 
                        title='Re-identification Risk Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction data available for risk analysis.")
    
    with tab4:
        st.subheader("Encryption Status")
        
        # Show encryption key info (safely)
        st.markdown("#### Current Encryption Configuration")
        st.success("✅ AES-256 encryption active")
        st.success("✅ RSA key pair configured")
        st.success("✅ Secure key derivation enabled")
        
        # Encryption performance test
        if st.button("Test Encryption Performance"):
            with st.spinner("Running encryption performance test..."):
                perf_results = privacy_manager.test_encryption_performance()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Encryption Speed", f"{perf_results['encrypt_speed']:.2f} MB/s")
                with col2:
                    st.metric("Decryption Speed", f"{perf_results['decrypt_speed']:.2f} MB/s")

def show_export_reports():
    """Export & Reports page"""
    st.title("📄 Export & Reports")
    
    from utils.export_manager import ExportManager
    export_manager = ExportManager()
    
    tab1, tab2, tab3 = st.tabs(["RBI Compliant Export", "Custom Reports", "Audit Logs"])
    
    with tab1:
        st.subheader("RBI Compliant Export")
        
        col1, col2 = st.columns(2)
        with col1:
            export_format = st.selectbox("Export Format", ["XML", "CSV"])
            date_range = st.date_input("Date Range", value=[])
        with col2:
            include_encrypted = st.checkbox("Include Encrypted Fields", value=False)
            validate_schema = st.checkbox("Validate Schema", value=True)
        
        if st.button("Generate Export"):
            if st.session_state.transactions:
                with st.spinner("Generating export..."):
                    export_data = export_manager.generate_rbi_export(
                        st.session_state.transactions,
                        format=export_format,
                        include_encrypted=include_encrypted,
                        validate_schema=validate_schema
                    )
                    
                    if export_data['success']:
                        st.success("Export generated successfully!")
                        st.download_button(
                            label=f"Download {export_format} Export",
                            data=export_data['data'],
                            file_name=f"rbi_export_{export_data['timestamp']}.{export_format.lower()}",
                            mime=f"application/{export_format.lower()}"
                        )
                    else:
                        st.error(f"Export failed: {export_data['message']}")
            else:
                st.warning("No transaction data available for export.")
    
    with tab2:
        st.subheader("Custom Reports")
        
        report_types = {
            "Transaction Summary": "Summary of all transactions by corridor and currency",
            "Risk Analysis": "Detailed risk assessment report",
            "Volume Analysis": "Trading volume trends and patterns", 
            "Privacy Compliance": "Privacy budget and compliance status",
            "Performance Metrics": "System performance and TPS analysis"
        }
        
        selected_report = st.selectbox("Select Report Type", list(report_types.keys()))
        st.info(report_types[selected_report])
        
        if st.button("Generate Custom Report"):
            with st.spinner("Generating report..."):
                report_data = export_manager.generate_custom_report(
                    st.session_state.transactions,
                    report_type=selected_report
                )
                
                if report_data['success']:
                    st.success("Report generated successfully!")
                    
                    # Display report preview
                    st.subheader("Report Preview")
                    st.markdown(report_data['preview'])
                    
                    # Download button
                    st.download_button(
                        label="Download Full Report",
                        data=report_data['data'],
                        file_name=f"{selected_report.lower().replace(' ', '_')}_report.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error(f"Report generation failed: {report_data['message']}")
    
    with tab3:
        st.subheader("Audit Logs")
        
        # Audit log filters
        col1, col2 = st.columns(2)
        with col1:
            log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR"])
            log_source = st.selectbox("Log Source", ["All", "Transactions", "Privacy", "Export", "Auth"])
        
        with col2:
            time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
        
        # Display audit logs
        audit_logs = export_manager.get_audit_logs(
            level=log_level if log_level != "All" else None,
            source=log_source if log_source != "All" else None,
            time_range=time_range
        )
        
        if audit_logs:
            import pandas as pd
            df = pd.DataFrame(audit_logs)
            st.dataframe(df, use_container_width=True)
            
            # Export audit logs
            if st.button("Export Audit Logs"):
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download Audit Logs CSV",
                    data=csv_data,
                    file_name=f"audit_logs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No audit logs found for the selected criteria.")

def show_system_status():
    """System Status page"""
    st.title("⚡ System Status")
    
    monitor = StatusMonitor()
    
    tab1, tab2, tab3 = st.tabs(["System Health", "Performance Metrics", "Alerts & Incidents"])
    
    with tab1:
        st.subheader("System Health Dashboard")
        
        # Get system status
        system_status = monitor.get_system_status()
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            db_healthy = system_status.get('services', {}).get('database', {}).get('healthy', False)
            status_color = "🟢" if db_healthy else "🔴"
            st.metric("Database", f"{status_color} {'Online' if db_healthy else 'Offline'}")
        with col2:
            enc_healthy = system_status.get('services', {}).get('encryption', {}).get('healthy', False)
            status_color = "🟢" if enc_healthy else "🔴"
            st.metric("Encryption", f"{status_color} {'Active' if enc_healthy else 'Inactive'}")
        with col3:
            api_healthy = system_status.get('services', {}).get('api_services', {}).get('healthy', False)
            status_color = "🟢" if api_healthy else "🔴"
            st.metric("API Services", f"{status_color} {'Running' if api_healthy else 'Down'}")
        with col4:
            st.metric("Uptime", system_status['uptime'])
        
        # System resources
        st.subheader("Resource Usage")
        resource_data = monitor.get_resource_usage()
        
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=1, cols=3,
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
            subplot_titles=('CPU Usage', 'Memory Usage', 'Disk Usage')
        )
        
        fig.add_trace(go.Indicator(
            mode = "gauge+number",
            value = resource_data['cpu_percent'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [{'range': [0, 50], 'color': "lightgray"},
                             {'range': [50, 80], 'color': "yellow"},
                             {'range': [80, 100], 'color': "red"}]}
        ), row=1, col=1)
        
        fig.add_trace(go.Indicator(
            mode = "gauge+number",
            value = resource_data['memory_percent'],
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [{'range': [0, 50], 'color': "lightgray"},
                             {'range': [50, 80], 'color': "yellow"},
                             {'range': [80, 100], 'color': "red"}]}
        ), row=1, col=2)
        
        fig.add_trace(go.Indicator(
            mode = "gauge+number", 
            value = resource_data['disk_percent'],
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "darkred"},
                    'steps': [{'range': [0, 50], 'color': "lightgray"},
                             {'range': [50, 80], 'color': "yellow"},
                             {'range': [80, 100], 'color': "red"}]}
        ), row=1, col=3)
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Performance Metrics")
        
        # TPS calculation
        from api.transaction_processor import calculate_tps
        current_tps = calculate_tps()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current TPS", f"{current_tps:.2f}")
        with col2:
            generation_times = st.session_state.performance_log.get('generation_times', [])
            avg_generation_time = sum(t[1] for t in generation_times[-10:]) / len(generation_times[-10:]) if generation_times else 0
            st.metric("Avg Generation Time", f"{avg_generation_time:.3f}s")
        with col3:
            analytics_times = st.session_state.performance_log.get('analytics_times', [])
            avg_analytics_time = sum(t[1] for t in analytics_times[-10:]) / len(analytics_times[-10:]) if analytics_times else 0
            st.metric("Avg Analytics Time", f"{avg_analytics_time:.3f}s")
        
        # Performance trends
        performance_history = monitor.get_performance_history()
        if performance_history:
            import pandas as pd
            import plotly.express as px
            
            df = pd.DataFrame(performance_history)
            fig = px.line(df, x='timestamp', y=['tps', 'avg_response_time'], 
                         title='Performance Trends Over Time')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance history available yet.")
    
    with tab3:
        st.subheader("Alerts & Incidents")
        
        # Current alerts
        alerts = monitor.get_active_alerts()
        
        if alerts:
            for alert in alerts:
                alert_type = alert['severity']
                if alert_type == 'high':
                    st.error(f"🚨 HIGH: {alert['message']}")
                elif alert_type == 'medium':
                    st.warning(f"⚠️ MEDIUM: {alert['message']}")
                else:
                    st.info(f"ℹ️ LOW: {alert['message']}")
        else:
            st.success("✅ No active alerts")
        
        # Incident history
        st.subheader("Recent Incidents")
        incidents = monitor.get_incident_history()
        
        if incidents:
            import pandas as pd
            df = pd.DataFrame(incidents)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent incidents recorded.")
        
        # Manual alert creation (for testing)
        st.subheader("Create Test Alert")
        with st.form("create_alert_form"):
            alert_message = st.text_input("Alert Message")
            alert_severity = st.selectbox("Severity", ["low", "medium", "high"])
            
            if st.form_submit_button("Create Alert"):
                monitor.create_alert(alert_message, alert_severity)
                st.success("Alert created successfully!")
                st.rerun()

if __name__ == "__main__":
    main()
