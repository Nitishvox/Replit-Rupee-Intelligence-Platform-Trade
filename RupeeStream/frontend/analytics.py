import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

from api.transaction_processor import TransactionProcessor, calculate_tps
from api.exchange_rates import ExchangeRateManager
from utils.fraud_detector import FraudDetector

def show_analytics():
    """Advanced analytics page with interactive visualizations"""
    
    st.title("📊 Advanced Analytics")
    
    # Initialize components
    processor = TransactionProcessor()
    exchange_manager = ExchangeRateManager()
    fraud_detector = FraudDetector()
    
    # Analytics control panel
    show_analytics_controls()
    
    # Main analytics content
    transactions = st.session_state.get('transactions', [])
    
    if not transactions:
        st.warning("No transaction data available for analysis.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Sample Data", use_container_width=True):
                new_transactions = processor.generate_bulk_transactions(50, "Random")
                st.session_state.transactions.extend(new_transactions)
                st.success("Generated 50 sample transactions for analysis!")
                st.rerun()
        with col2:
            if st.button("Load Historical Data", use_container_width=True):
                historical_transactions = processor.generate_bulk_transactions(100, "Random")
                st.session_state.transactions.extend(historical_transactions)
                st.success("Loaded 100 historical transactions!")
                st.rerun()
        return
    
    # Analytics tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Volume Analytics", "Risk Analysis", "Performance Metrics", 
        "Corridor Analysis", "Real-time Monitoring"
    ])
    
    with tab1:
        show_volume_analytics(transactions)
    
    with tab2:
        show_risk_analytics(transactions, fraud_detector)
    
    with tab3:
        show_performance_analytics()
    
    with tab4:
        show_corridor_analytics(transactions, exchange_manager)
    
    with tab5:
        show_realtime_monitoring(transactions)

def show_analytics_controls():
    """Analytics control panel"""
    
    with st.expander("🛠️ Analytics Controls", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            time_range = st.selectbox("Time Range", 
                                    ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
            st.session_state.analytics_time_range = time_range
        
        with col2:
            currency_filter = st.multiselect("Currency Filter", 
                                           ["INR", "USD", "EUR", "GBP", "SGD", "RUB", "AED"],
                                           default=["INR", "USD", "EUR"])
            st.session_state.analytics_currency_filter = currency_filter
        
        with col3:
            risk_threshold = st.slider("Risk Threshold", 0, 100, 50)
            st.session_state.analytics_risk_threshold = risk_threshold
        
        with col4:
            auto_refresh = st.checkbox("Auto Refresh (30s)")
            st.session_state.analytics_auto_refresh = auto_refresh

def show_volume_analytics(transactions: List[Dict[str, Any]]):
    """Volume-based analytics"""
    
    st.subheader("💰 Volume Analytics")
    
    df = pd.DataFrame(transactions)
    
    # Apply filters
    currency_filter = st.session_state.get('analytics_currency_filter', ['INR', 'USD', 'EUR'])
    df_filtered = df[df['currency'].isin(currency_filter)]
    
    # Key volume metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volume = df_filtered['amount'].sum()
        st.metric("Total Volume", f"₹{total_volume:,.0f}")
    
    with col2:
        avg_transaction = df_filtered['amount'].mean()
        st.metric("Avg Transaction", f"₹{avg_transaction:,.0f}")
    
    with col3:
        largest_transaction = df_filtered['amount'].max()
        st.metric("Largest Transaction", f"₹{largest_transaction:,.0f}")
    
    with col4:
        transaction_count = len(df_filtered)
        st.metric("Transaction Count", f"{transaction_count:,}")
    
    # Volume visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Volume by source
        volume_by_source = df_filtered.groupby('source')['amount'].sum().sort_values(ascending=False)
        fig = px.bar(
            x=volume_by_source.index,
            y=volume_by_source.values,
            title="Volume by Transaction Source",
            labels={'x': 'Source', 'y': 'Volume (INR)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Volume distribution by currency
        volume_by_currency = df_filtered.groupby('currency')['amount'].sum()
        fig = px.pie(
            values=volume_by_currency.values,
            names=volume_by_currency.index,
            title="Volume Distribution by Currency"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Time-series volume analysis
    if 'timestamp' in df_filtered.columns:
        st.subheader("📈 Volume Trends")
        
        df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'])
        df_filtered['hour'] = df_filtered['timestamp'].dt.hour
        df_filtered['date'] = df_filtered['timestamp'].dt.date
        
        # Hourly volume pattern
        hourly_volume = df_filtered.groupby('hour')['amount'].agg(['sum', 'count']).reset_index()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Hourly Volume', 'Hourly Transaction Count'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        fig.add_trace(
            go.Bar(x=hourly_volume['hour'], y=hourly_volume['sum'], name='Volume'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(x=hourly_volume['hour'], y=hourly_volume['count'], 
                      mode='lines+markers', name='Count'),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Volume heatmap by corridor and time
    if len(df_filtered) > 10:
        st.subheader("🌡️ Volume Heatmap")
        
        # Create pivot table for heatmap
        df_filtered['hour'] = pd.to_datetime(df_filtered['timestamp']).dt.hour
        heatmap_data = df_filtered.pivot_table(
            values='amount', 
            index='corridor', 
            columns='hour', 
            aggfunc='sum', 
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            title="Volume Heatmap (Corridor vs Hour)",
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_risk_analytics(transactions: List[Dict[str, Any]], fraud_detector: FraudDetector):
    """Risk-focused analytics"""
    
    st.subheader("🔍 Risk Analytics")
    
    df = pd.DataFrame(transactions)
    
    # Risk distribution analysis
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        high_risk_count = len(df[df['risk_score'] > 75])
        st.metric("High Risk Transactions", high_risk_count, 
                 delta=f"{(high_risk_count/len(df)*100):.1f}%" if len(df) > 0 else "0%")
    
    with col2:
        avg_risk = df['risk_score'].mean()
        st.metric("Average Risk Score", f"{avg_risk:.1f}")
    
    with col3:
        max_risk = df['risk_score'].max()
        st.metric("Maximum Risk Score", f"{max_risk:.1f}")
    
    with col4:
        risk_variance = df['risk_score'].var()
        st.metric("Risk Variance", f"{risk_variance:.1f}")
    
    # Risk visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk score distribution
        fig = px.histogram(
            df, x='risk_score', nbins=20,
            title="Risk Score Distribution",
            labels={'risk_score': 'Risk Score', 'count': 'Frequency'}
        )
        fig.add_vline(x=50, line_dash="dash", line_color="orange", 
                     annotation_text="Medium Risk Threshold")
        fig.add_vline(x=75, line_dash="dash", line_color="red", 
                     annotation_text="High Risk Threshold")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Risk by source
        risk_by_source = df.groupby('source')['risk_score'].mean().sort_values(ascending=False)
        fig = px.bar(
            x=risk_by_source.index,
            y=risk_by_source.values,
            title="Average Risk Score by Source",
            color=risk_by_source.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk correlation analysis
    st.subheader("📊 Risk Correlation Analysis")
    
    # Risk vs Amount correlation
    fig = px.scatter(
        df, x='amount', y='risk_score', 
        color='source', size='processing_time',
        title="Risk Score vs Transaction Amount",
        hover_data=['currency', 'corridor']
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Fraud pattern analysis
    st.subheader("🚨 Fraud Pattern Analysis")
    
    # Generate fraud alerts
    fraud_alerts = fraud_detector.generate_fraud_alerts(transactions)
    
    if fraud_alerts:
        alert_df = pd.DataFrame(fraud_alerts)
        
        # Alert severity distribution
        severity_counts = alert_df['severity'].value_counts()
        fig = px.pie(
            values=severity_counts.values,
            names=severity_counts.index,
            title="Fraud Alert Severity Distribution",
            color_discrete_map={'high': 'red', 'medium': 'orange', 'low': 'yellow'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Alert details table
        st.dataframe(alert_df, use_container_width=True)
    else:
        st.success("✅ No fraud patterns detected in current data")

def show_performance_analytics():
    """Performance metrics analytics"""
    
    st.subheader("⚡ Performance Analytics")
    
    # Current performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_tps = calculate_tps()
        st.metric("Current TPS", f"{current_tps:.2f}")
    
    with col2:
        # Average generation time
        perf_log = st.session_state.get('performance_log', {})
        gen_times = perf_log.get('generation_times', [])
        if gen_times:
            avg_gen_time = np.mean([t[1] for t in gen_times[-10:]])
            st.metric("Avg Generation Time", f"{avg_gen_time:.3f}s")
        else:
            st.metric("Avg Generation Time", "0.000s")
    
    with col3:
        # Analytics processing time
        analytics_times = perf_log.get('analytics_times', [])
        if analytics_times:
            avg_analytics_time = np.mean([t[1] for t in analytics_times[-10:]])
            st.metric("Avg Analytics Time", f"{avg_analytics_time:.3f}s")
        else:
            st.metric("Avg Analytics Time", "0.000s")
    
    with col4:
        # Memory usage simulation
        memory_usage = np.random.uniform(40, 80)
        st.metric("Memory Usage", f"{memory_usage:.1f}%")
    
    # Performance trends
    if gen_times:
        st.subheader("📈 Performance Trends")
        
        # Prepare performance data
        timestamps = [t[0] for t in gen_times[-50:]]
        generation_times = [t[1] for t in gen_times[-50:]]
        
        df_perf = pd.DataFrame({
            'timestamp': timestamps,
            'generation_time': generation_times
        })
        
        # Performance over time
        fig = px.line(
            df_perf, x='timestamp', y='generation_time',
            title="Transaction Generation Time Trend",
            labels={'generation_time': 'Generation Time (seconds)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Performance Statistics")
            stats_data = {
                'Metric': ['Min Time', 'Max Time', 'Mean Time', 'Std Dev', 'P95', 'P99'],
                'Value': [
                    f"{min(generation_times):.4f}s",
                    f"{max(generation_times):.4f}s", 
                    f"{np.mean(generation_times):.4f}s",
                    f"{np.std(generation_times):.4f}s",
                    f"{np.percentile(generation_times, 95):.4f}s",
                    f"{np.percentile(generation_times, 99):.4f}s"
                ]
            }
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
        
        with col2:
            # Performance distribution
            fig = px.histogram(
                generation_times, nbins=20,
                title="Generation Time Distribution",
                labels={'value': 'Generation Time (s)', 'count': 'Frequency'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

def show_corridor_analytics(transactions: List[Dict[str, Any]], exchange_manager: ExchangeRateManager):
    """Corridor-specific analytics"""
    
    st.subheader("🌍 Corridor Analytics")
    
    df = pd.DataFrame(transactions)
    
    # Corridor performance metrics
    corridor_stats = df.groupby('corridor').agg({
        'amount': ['sum', 'mean', 'count'],
        'risk_score': 'mean',
        'processing_time': 'mean'
    }).round(2)
    
    corridor_stats.columns = ['Total Volume', 'Avg Amount', 'Transaction Count', 'Avg Risk', 'Avg Processing Time']
    corridor_stats = corridor_stats.reset_index()
    
    st.dataframe(corridor_stats, use_container_width=True)
    
    # Corridor visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Volume by corridor
        volume_by_corridor = df.groupby('corridor')['amount'].sum().sort_values(ascending=False)
        fig = px.bar(
            x=volume_by_corridor.index,
            y=volume_by_corridor.values,
            title="Total Volume by Corridor",
            labels={'x': 'Corridor', 'y': 'Volume (INR)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Average processing time by corridor
        processing_by_corridor = df.groupby('corridor')['processing_time'].mean()
        fig = px.bar(
            x=processing_by_corridor.index,
            y=processing_by_corridor.values,
            title="Average Processing Time by Corridor",
            color=processing_by_corridor.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Exchange rate impact analysis
    st.subheader("💱 Exchange Rate Impact")
    
    current_rates = exchange_manager.get_current_rates()
    historical_rates = exchange_manager.get_historical_rates(7)
    
    if not historical_rates.empty and current_rates:
        # Rate volatility by corridor
        volatility_data = []
        
        for corridor in df['corridor'].unique():
            rate_pair = {
                'IN-US': 'USDINR',
                'IN-EU': 'EURINR',
                'IN-GB': 'GBPINR',
                'IN-SG': 'SGDINR'
            }.get(corridor, 'USDINR')
            
            if f'{rate_pair}_rate' in historical_rates.columns:
                rates = historical_rates[f'{rate_pair}_rate']
                volatility = rates.std() / rates.mean() * 100
                volatility_data.append({
                    'corridor': corridor,
                    'volatility': volatility,
                    'current_rate': current_rates.get(rate_pair, 0)
                })
        
        if volatility_data:
            vol_df = pd.DataFrame(volatility_data)
            
            fig = px.scatter(
                vol_df, x='volatility', y='current_rate',
                color='corridor', size='current_rate',
                title="Exchange Rate Volatility vs Current Rate",
                labels={'volatility': 'Volatility (%)', 'current_rate': 'Current Rate'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def show_realtime_monitoring(transactions: List[Dict[str, Any]]):
    """Real-time monitoring dashboard"""
    
    st.subheader("🔴 Real-time Monitoring")
    
    # Auto-refresh logic
    auto_refresh = st.session_state.get('analytics_auto_refresh', False)
    
    if auto_refresh:
        # Add auto-refresh placeholder
        placeholder = st.empty()
        
        with placeholder.container():
            st.info("🔄 Auto-refresh enabled - Updates every 30 seconds")
    
    # Real-time metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Recent activity (last 5 minutes)
        recent_time = datetime.now() - timedelta(minutes=5)
        df = pd.DataFrame(transactions)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            recent_transactions = df[df['timestamp'] > recent_time]
            st.metric("Recent Activity (5m)", len(recent_transactions))
        else:
            st.metric("Recent Activity (5m)", "0")
    
    with col2:
        # Active alerts
        active_alerts = st.session_state.get('active_alerts', [])
        st.metric("Active Alerts", len(active_alerts))
    
    with col3:
        # System load (simulated)
        system_load = np.random.uniform(20, 90)
        load_color = "normal" if system_load < 70 else "inverse"
        st.metric("System Load", f"{system_load:.1f}%", delta_color=load_color)
    
    # Real-time transaction stream
    st.subheader("📊 Live Transaction Stream")
    
    if transactions:
        # Show last 10 transactions in real-time format
        recent_df = pd.DataFrame(transactions[-10:])
        
        # Format for display
        display_df = recent_df[['id', 'amount', 'currency', 'source', 'status', 'risk_score']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.0f}")
        display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Live metrics chart
        if len(transactions) > 20:
            # Real-time risk trend
            risk_trend = [t.get('risk_score', 0) for t in transactions[-20:]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=risk_trend,
                mode='lines+markers',
                name='Risk Score',
                line=dict(color='red', width=2)
            ))
            
            fig.add_hline(y=75, line_dash="dash", line_color="red", 
                         annotation_text="High Risk Threshold")
            fig.add_hline(y=50, line_dash="dash", line_color="orange", 
                         annotation_text="Medium Risk Threshold")
            
            fig.update_layout(
                title="Real-time Risk Score Trend (Last 20 Transactions)",
                yaxis_title="Risk Score",
                xaxis_title="Transaction Sequence",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction data available for real-time monitoring")
    
    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()
