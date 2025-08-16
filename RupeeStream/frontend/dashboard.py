import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

from api.transaction_processor import TransactionProcessor, calculate_tps
from api.exchange_rates import ExchangeRateManager
from api.srva_manager import SRVAManager
from utils.fraud_detector import FraudDetector
from utils.status_monitor import StatusMonitor

def show_dashboard():
    """Main dashboard view with key metrics and visualizations"""
    
    st.title("🏠 RIPT Dashboard")
    
    # Initialize managers
    transaction_processor = TransactionProcessor()
    exchange_manager = ExchangeRateManager()
    srva_manager = SRVAManager()
    fraud_detector = FraudDetector()
    status_monitor = StatusMonitor()
    
    # Role-based content
    user_role = st.session_state.get('user_role', 'trader')
    
    # Quick actions bar
    show_quick_actions(transaction_processor)
    
    # Key metrics row
    show_key_metrics(exchange_manager, srva_manager)
    
    # Main dashboard content based on role
    if user_role == 'admin':
        show_admin_dashboard(transaction_processor, exchange_manager, srva_manager, status_monitor)
    elif user_role == 'auditor':
        show_auditor_dashboard(transaction_processor, fraud_detector)
    else:  # trader
        show_trader_dashboard(transaction_processor, exchange_manager)

def show_quick_actions(processor: TransactionProcessor):
    """Quick action buttons"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Generate 5 Transactions", use_container_width=True):
            new_txns = processor.generate_bulk_transactions(5)
            st.session_state.transactions.extend(new_txns)
            st.success(f"Generated 5 transactions!")
            st.rerun()
    
    with col2:
        if st.button("📊 Refresh Rates", use_container_width=True):
            st.cache_data.clear()
            st.success("Exchange rates refreshed!")
            st.rerun()
    
    with col3:
        if st.button("🔍 Risk Scan", use_container_width=True):
            if st.session_state.transactions:
                high_risk = [t for t in st.session_state.transactions if t.get('risk_score', 0) > 75]
                st.info(f"Found {len(high_risk)} high-risk transactions")
            else:
                st.info("No transactions to scan")
    
    with col4:
        if st.button("📈 Live Analytics", use_container_width=True):
            st.session_state.current_page = 'Analytics'
            st.rerun()

def show_key_metrics(exchange_manager: ExchangeRateManager, srva_manager: SRVAManager):
    """Display key performance metrics"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Transaction metrics
    transactions = st.session_state.get('transactions', [])
    with col1:
        total_volume = sum(t.get('amount', 0) for t in transactions)
        st.metric("Total Volume", f"₹{total_volume:,.0f}", 
                 delta=f"+{len(transactions)} txns")
    
    # TPS metric
    with col2:
        current_tps = calculate_tps()
        st.metric("Current TPS", f"{current_tps:.2f}", 
                 delta="+0.1" if current_tps > 0 else "0")
    
    # Risk metrics
    with col3:
        if transactions:
            avg_risk = np.mean([t.get('risk_score', 0) for t in transactions])
            risk_delta = "High" if avg_risk > 75 else "Medium" if avg_risk > 50 else "Low"
            st.metric("Avg Risk Score", f"{avg_risk:.1f}", delta=risk_delta)
        else:
            st.metric("Avg Risk Score", "0.0", delta="No data")
    
    # Exchange rate
    with col4:
        rates = exchange_manager.get_current_rates()
        usd_rate = rates.get('USDINR', 83.5)
        st.metric("USD/INR", f"₹{usd_rate:.2f}", delta="+0.15")
    
    # SRVA accounts
    with col5:
        account_stats = srva_manager.get_account_statistics()
        total_accounts = account_stats.get('total_accounts', 0)
        st.metric("SRVA Accounts", str(total_accounts), delta="+2")

def show_trader_dashboard(processor: TransactionProcessor, exchange_manager: ExchangeRateManager):
    """Dashboard view for traders"""
    
    st.markdown("### 💱 Exchange Rates")
    show_exchange_rate_widget(exchange_manager)
    
    st.markdown("### 📊 Transaction Overview")
    show_transaction_overview()
    
    st.markdown("### 🎯 Quick Transaction")
    show_quick_transaction_form(processor)

def show_auditor_dashboard(processor: TransactionProcessor, fraud_detector: FraudDetector):
    """Dashboard view for auditors"""
    
    st.markdown("### 🔍 Risk Analysis")
    show_risk_analysis()
    
    st.markdown("### 📋 Audit Trail")
    show_audit_trail()
    
    st.markdown("### 🚨 Fraud Alerts")
    show_fraud_alerts(fraud_detector)

def show_admin_dashboard(processor: TransactionProcessor, exchange_manager: ExchangeRateManager, 
                        srva_manager: SRVAManager, status_monitor: StatusMonitor):
    """Dashboard view for administrators"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ System Status")
        show_system_status_widget(status_monitor)
        
        st.markdown("### 🏦 SRVA Overview")
        show_srva_overview(srva_manager)
    
    with col2:
        st.markdown("### 📈 Performance Metrics")
        show_performance_metrics()
        
        st.markdown("### 🌍 Global Activity")
        show_global_activity_map()

def show_exchange_rate_widget(exchange_manager: ExchangeRateManager):
    """Real-time exchange rate widget"""
    
    rates = exchange_manager.get_current_rates()
    
    if rates:
        # Create rate display grid
        rate_cols = st.columns(3)
        rate_pairs = list(rates.items())
        
        for i, (pair, rate) in enumerate(rate_pairs[:6]):  # Show top 6 pairs
            col_idx = i % 3
            with rate_cols[col_idx]:
                # Simulate rate change for demo
                change = np.random.uniform(-0.5, 0.5)
                change_color = "🔴" if change < 0 else "🟢"
                
                st.metric(
                    label=pair,
                    value=f"₹{rate:.4f}",
                    delta=f"{change_color} {change:+.3f}"
                )
        
        # Rate trend chart
        if st.checkbox("Show Rate Trends"):
            historical_data = exchange_manager.get_historical_rates(7)  # Last 7 days
            if not historical_data.empty:
                fig = px.line(historical_data, x='date', 
                             y=[col for col in historical_data.columns if col.endswith('_rate')],
                             title="7-Day Exchange Rate Trends")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Unable to fetch current exchange rates")

def show_transaction_overview():
    """Transaction overview widget"""
    
    transactions = st.session_state.get('transactions', [])
    
    if not transactions:
        st.info("No transactions available. Generate some using the quick actions above.")
        return
    
    # Create dataframe for analysis
    df = pd.DataFrame(transactions)
    
    # Transaction distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        # By source
        source_dist = df['source'].value_counts()
        fig = px.pie(values=source_dist.values, names=source_dist.index,
                    title="Transactions by Source")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # By status
        status_dist = df['status'].value_counts()
        fig = px.bar(x=status_dist.index, y=status_dist.values,
                    title="Transactions by Status")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent transactions table
    st.markdown("#### Recent Transactions")
    recent_df = df.tail(10)[['id', 'amount', 'currency', 'source', 'status', 'risk_score']]
    st.dataframe(recent_df, use_container_width=True)

def show_quick_transaction_form(processor: TransactionProcessor):
    """Quick transaction creation form"""
    
    with st.form("quick_transaction", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            amount = st.number_input("Amount", min_value=1.0, value=10000.0)
            currency = st.selectbox("Currency", ["INR", "USD", "EUR", "GBP", "SGD"])
        
        with col2:
            source = st.selectbox("Source", ["UPI", "NEFT", "RTGS", "SRVA-INR", "SWIFT"])
            corridor = st.selectbox("Corridor", ["IN-US", "IN-EU", "IN-SG", "IN-GB"])
        
        with col3:
            counterparty = st.text_input("Counterparty", value="Entity_1234")
            submit = st.form_submit_button("Create Transaction", use_container_width=True)
        
        if submit:
            txn_data = {
                'amount': amount,
                'currency': currency,
                'source': source,
                'corridor': corridor,
                'counterparty': counterparty
            }
            
            result = processor.process_manual_transaction(txn_data)
            if result['success']:
                st.success(f"Transaction created! ID: {result['transaction_id']}")
                st.session_state.transactions.append(result['transaction'])
                st.rerun()
            else:
                st.error(f"Failed: {result['message']}")

def show_risk_analysis():
    """Risk analysis widget for auditors"""
    
    transactions = st.session_state.get('transactions', [])
    if not transactions:
        st.info("No transactions for risk analysis")
        return
    
    df = pd.DataFrame(transactions)
    
    # Risk distribution
    risk_bins = pd.cut(df['risk_score'], bins=[0, 25, 50, 75, 100], 
                      labels=['Low', 'Medium', 'High', 'Critical'])
    risk_dist = risk_bins.value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk distribution pie chart
        fig = px.pie(values=risk_dist.values, names=risk_dist.index,
                    title="Risk Distribution", color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # High risk transactions
        high_risk_txns = df[df['risk_score'] > 75]
        st.metric("High Risk Transactions", len(high_risk_txns))
        st.metric("Avg High Risk Score", f"{high_risk_txns['risk_score'].mean():.1f}" if len(high_risk_txns) > 0 else "0")
        st.metric("Max Risk Score", f"{df['risk_score'].max():.1f}")
    
    # Risk over time
    if 'timestamp' in df.columns:
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        hourly_risk = df.groupby('hour')['risk_score'].mean()
        
        fig = px.line(x=hourly_risk.index, y=hourly_risk.values,
                     title="Average Risk Score by Hour")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

def show_audit_trail():
    """Audit trail widget"""
    
    st.info("Audit trail functionality - showing transaction history and user actions")
    
    # Mock audit data for demonstration
    audit_data = [
        {"timestamp": datetime.now() - timedelta(minutes=5), "user": "trader_001", "action": "CREATE_TRANSACTION", "details": "Manual transaction ₹50,000"},
        {"timestamp": datetime.now() - timedelta(minutes=15), "user": "admin", "action": "BULK_GENERATE", "details": "Generated 10 transactions"},
        {"timestamp": datetime.now() - timedelta(hours=1), "user": "auditor_002", "action": "RISK_REVIEW", "details": "Reviewed high-risk transactions"},
        {"timestamp": datetime.now() - timedelta(hours=2), "user": "trader_003", "action": "RATE_CHECK", "details": "Checked USD/INR rates"},
    ]
    
    audit_df = pd.DataFrame(audit_data)
    st.dataframe(audit_df, use_container_width=True)

def show_fraud_alerts(fraud_detector: FraudDetector):
    """Fraud alerts widget"""
    
    transactions = st.session_state.get('transactions', [])
    
    if transactions:
        # Analyze for fraud patterns
        alerts = fraud_detector.generate_fraud_alerts(transactions)
        
        if alerts:
            for alert in alerts:
                severity = alert.get('severity', 'medium')
                if severity == 'high':
                    st.error(f"🚨 {alert['message']}")
                elif severity == 'medium':
                    st.warning(f"⚠️ {alert['message']}")
                else:
                    st.info(f"ℹ️ {alert['message']}")
        else:
            st.success("✅ No fraud alerts detected")
    else:
        st.info("No transaction data for fraud analysis")

def show_system_status_widget(status_monitor: StatusMonitor):
    """System status widget for admins"""
    
    status = status_monitor.get_system_status()
    
    # Status indicators
    indicators = [
        ("Database", status.get('database', True)),
        ("API Services", status.get('api_services', True)),
        ("Encryption", status.get('encryption', True)),
    ]
    
    for service, is_up in indicators:
        status_icon = "🟢" if is_up else "🔴"
        status_text = "Online" if is_up else "Offline"
        st.metric(service, f"{status_icon} {status_text}")

def show_srva_overview(srva_manager: SRVAManager):
    """SRVA accounts overview widget"""
    
    stats = srva_manager.get_account_statistics()
    
    if stats:
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Accounts", stats.get('total_accounts', 0))
            st.metric("Total Balance", f"₹{stats.get('total_balance', 0):,.0f}")
        
        with col2:
            # Country distribution
            country_dist = stats.get('by_country', {})
            if country_dist:
                fig = px.bar(x=list(country_dist.keys()), y=list(country_dist.values()),
                           title="Accounts by Country")
                fig.update_layout(height=200)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No SRVA account data available")

def show_performance_metrics():
    """Performance metrics widget"""
    
    # Get performance data from session state
    perf_log = st.session_state.get('performance_log', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        # TPS metric
        current_tps = calculate_tps()
        st.metric("Current TPS", f"{current_tps:.2f}")
        
        # Generation times
        gen_times = perf_log.get('generation_times', [])
        if gen_times:
            avg_gen_time = np.mean([t[1] for t in gen_times[-10:]])
            st.metric("Avg Gen Time", f"{avg_gen_time:.3f}s")
    
    with col2:
        # Analytics times  
        analytics_times = perf_log.get('analytics_times', [])
        if analytics_times:
            avg_analytics_time = np.mean([t[1] for t in analytics_times[-10:]])
            st.metric("Avg Analytics Time", f"{avg_analytics_time:.3f}s")
        
        # Memory usage (simulated)
        memory_usage = np.random.uniform(40, 80)
        st.metric("Memory Usage", f"{memory_usage:.1f}%")

def show_global_activity_map():
    """Global trading activity map"""
    
    # Simulate global activity data
    countries = ['United States', 'Germany', 'United Kingdom', 'Singapore', 'Russia']
    activity_data = {
        'country': countries,
        'lat': [39.8283, 51.1657, 55.3781, 1.3521, 61.5240],
        'lon': [-98.5795, 10.4515, -3.4360, 103.8198, 105.3188],
        'volume': np.random.randint(1000000, 50000000, len(countries)),
        'transactions': np.random.randint(10, 500, len(countries))
    }
    
    df = pd.DataFrame(activity_data)
    
    fig = px.scatter_geo(df, lat='lat', lon='lon', 
                        size='volume', hover_name='country',
                        hover_data=['transactions'], 
                        title="Global Trading Activity")
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
