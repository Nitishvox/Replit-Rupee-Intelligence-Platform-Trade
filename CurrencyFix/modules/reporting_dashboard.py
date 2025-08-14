import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional

class ReportingDashboard:
    """Advanced Reporting and Analytics Dashboard for RIPT system"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        self.report_types = [
            "Executive Summary",
            "Transaction Analytics", 
            "Settlement Performance",
            "Country-wise Analysis",
            "Currency Analysis",
            "Risk Analytics",
            "Compliance Report",
            "Operational Metrics"
        ]
        
        self.time_periods = [
            "Last 7 Days",
            "Last 30 Days", 
            "Last 90 Days",
            "Last 6 Months",
            "Last Year",
            "Year to Date",
            "Custom Range"
        ]
    
    def show_interface(self):
        """Display reporting dashboard interface"""
        st.header("📊 Reporting & Analytics Dashboard")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Executive Dashboard",
            "Detailed Analytics", 
            "Custom Reports",
            "Export & Scheduling"
        ])
        
        with tab1:
            self._show_executive_dashboard()
        
        with tab2:
            self._show_detailed_analytics()
        
        with tab3:
            self._show_custom_reports()
        
        with tab4:
            self._show_export_scheduling()
    
    def _show_executive_dashboard(self):
        """Executive summary dashboard"""
        st.subheader("Executive Summary Dashboard")
        
        # Time period selector
        col1, col2 = st.columns([1, 3])
        
        with col1:
            time_period = st.selectbox("Time Period", self.time_periods, index=1)
        
        with col2:
            if time_period == "Custom Range":
                date_range = st.date_input(
                    "Select Date Range",
                    value=[datetime.now().date() - timedelta(days=30), datetime.now().date()]
                )
        
        # Get filtered data
        transactions_df = self.db_manager.get_transactions(limit=1000)
        accounts_df = self.db_manager.get_srva_accounts()
        
        if not transactions_df.empty:
            # Apply time filter
            transactions_df['created_date'] = pd.to_datetime(transactions_df['created_date'])
            
            if time_period == "Last 7 Days":
                cutoff_date = datetime.now() - timedelta(days=7)
            elif time_period == "Last 30 Days":
                cutoff_date = datetime.now() - timedelta(days=30)
            elif time_period == "Last 90 Days":
                cutoff_date = datetime.now() - timedelta(days=90)
            else:
                cutoff_date = datetime.now() - timedelta(days=30)  # Default
            
            filtered_df = transactions_df[transactions_df['created_date'] >= cutoff_date]
            
            # Key Performance Indicators
            st.subheader("Key Performance Indicators")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_volume = filtered_df['inr_amount'].sum()
                prev_volume = self._get_previous_period_volume(cutoff_date)
                volume_change = ((total_volume - prev_volume) / prev_volume * 100) if prev_volume > 0 else 0
                
                st.metric(
                    "Total Volume", 
                    f"₹{total_volume/1e7:.1f}Cr",
                    delta=f"{volume_change:+.1f}%"
                )
            
            with col2:
                transaction_count = len(filtered_df)
                prev_count = self._get_previous_period_count(cutoff_date)
                count_change = ((transaction_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
                
                st.metric(
                    "Transactions", 
                    f"{transaction_count:,}",
                    delta=f"{count_change:+.1f}%"
                )
            
            with col3:
                avg_transaction = filtered_df['inr_amount'].mean()
                st.metric(
                    "Avg Transaction", 
                    f"₹{avg_transaction/1e5:.1f}L"
                )
            
            with col4:
                success_rate = len(filtered_df[filtered_df['status'] == 'completed']) / len(filtered_df) * 100
                st.metric(
                    "Success Rate", 
                    f"{success_rate:.1f}%"
                )
            
            with col5:
                active_countries = filtered_df['country'].nunique()
                st.metric(
                    "Active Countries", 
                    active_countries
                )
            
            st.markdown("---")
            
            # Charts Section
            col1, col2 = st.columns(2)
            
            with col1:
                # Transaction Volume Trend
                st.subheader("Transaction Volume Trend")
                
                daily_volume = filtered_df.groupby(filtered_df['created_date'].dt.date)['inr_amount'].sum().reset_index()
                daily_volume.columns = ['Date', 'Volume']
                
                fig = px.line(
                    daily_volume, 
                    x='Date', 
                    y='Volume',
                    title="Daily Transaction Volume (₹)",
                    markers=True
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Currency Distribution
                st.subheader("Currency Distribution")
                
                currency_volume = filtered_df.groupby('currency')['inr_amount'].sum().reset_index()
                
                fig = px.pie(
                    currency_volume, 
                    values='inr_amount', 
                    names='currency',
                    title="Volume by Currency"
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            
            # Country Performance
            st.subheader("Top Countries by Volume")
            
            country_stats = filtered_df.groupby('country').agg({
                'inr_amount': ['sum', 'count', 'mean'],
                'status': lambda x: (x == 'completed').sum()
            }).round(2)
            
            country_stats.columns = ['Total Volume', 'Transaction Count', 'Avg Amount', 'Completed']
            country_stats['Success Rate'] = (country_stats['Completed'] / country_stats['Transaction Count'] * 100).round(1)
            country_stats = country_stats.sort_values('Total Volume', ascending=False).head(10)
            
            # Format currency columns
            country_stats['Total Volume'] = country_stats['Total Volume'].apply(lambda x: f"₹{x/1e7:.2f}Cr")
            country_stats['Avg Amount'] = country_stats['Avg Amount'].apply(lambda x: f"₹{x/1e5:.2f}L")
            
            st.dataframe(country_stats, use_container_width=True)
            
            # Settlement Status Overview
            st.subheader("Settlement Status Overview")
            
            status_counts = filtered_df['status'].value_counts()
            
            col1, col2, col3 = st.columns(3)
            
            for i, (status, count) in enumerate(status_counts.items()):
                col = [col1, col2, col3][i % 3]
                percentage = count / len(filtered_df) * 100
                
                with col:
                    if status == 'completed':
                        st.success(f"**{status.title()}**\n{count:,} ({percentage:.1f}%)")
                    elif status == 'pending':
                        st.warning(f"**{status.title()}**\n{count:,} ({percentage:.1f}%)")
                    else:
                        st.info(f"**{status.title()}**\n{count:,} ({percentage:.1f}%)")
        
        else:
            st.info("No transaction data available. Use the Data Generator to create sample data.")
    
    def _show_detailed_analytics(self):
        """Detailed analytics interface"""
        st.subheader("Detailed Analytics")
        
        # Analytics type selector
        analytics_type = st.selectbox("Select Analytics Type", [
            "Transaction Flow Analysis",
            "Settlement Performance",
            "Risk Analytics", 
            "Operational Efficiency",
            "Customer Analytics",
            "Seasonal Trends"
        ])
        
        transactions_df = self.db_manager.get_transactions(limit=2000)
        
        if not transactions_df.empty:
            transactions_df['created_date'] = pd.to_datetime(transactions_df['created_date'])
            
            if analytics_type == "Transaction Flow Analysis":
                self._show_transaction_flow_analysis(transactions_df)
            
            elif analytics_type == "Settlement Performance":
                self._show_settlement_performance(transactions_df)
            
            elif analytics_type == "Risk Analytics":
                self._show_risk_analytics(transactions_df)
            
            elif analytics_type == "Operational Efficiency":
                self._show_operational_efficiency(transactions_df)
            
            elif analytics_type == "Customer Analytics":
                self._show_customer_analytics(transactions_df)
            
            elif analytics_type == "Seasonal Trends":
                self._show_seasonal_trends(transactions_df)
        
        else:
            st.info("No data available for detailed analytics.")
    
    def _show_transaction_flow_analysis(self, df):
        """Transaction flow analysis"""
        st.subheader("Transaction Flow Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Hourly transaction pattern
            df['hour'] = df['created_date'].dt.hour
            hourly_pattern = df.groupby('hour').size()
            
            fig = px.bar(
                x=hourly_pattern.index,
                y=hourly_pattern.values,
                title="Transaction Pattern by Hour of Day",
                labels={'x': 'Hour', 'y': 'Transaction Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Weekly pattern
            df['weekday'] = df['created_date'].dt.day_name()
            weekly_pattern = df.groupby('weekday').size().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ])
            
            fig = px.bar(
                x=weekly_pattern.index,
                y=weekly_pattern.values,
                title="Transaction Pattern by Day of Week",
                labels={'x': 'Day', 'y': 'Transaction Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Transaction size distribution
        st.subheader("Transaction Size Distribution")
        
        # Create size buckets
        df['size_bucket'] = pd.cut(
            df['inr_amount'], 
            bins=[0, 100000, 1000000, 10000000, 100000000, float('inf')],
            labels=['<1L', '1L-10L', '10L-1Cr', '1Cr-10Cr', '>10Cr']
        )
        
        size_dist = df['size_bucket'].value_counts().sort_index()
        
        fig = px.bar(
            x=size_dist.index,
            y=size_dist.values,
            title="Distribution by Transaction Size",
            labels={'x': 'Size Range', 'y': 'Count'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Flow between countries
        st.subheader("Cross-Border Flow Analysis")
        
        flow_data = df.groupby(['from_account', 'to_account'])['inr_amount'].sum().reset_index()
        flow_data = flow_data.sort_values('inr_amount', ascending=False).head(20)
        
        st.dataframe(flow_data, use_container_width=True)
    
    def _show_settlement_performance(self, df):
        """Settlement performance analysis"""
        st.subheader("Settlement Performance Analysis")
        
        # Processing time analysis
        df['processed_date'] = pd.to_datetime(df['processed_date'])
        completed_df = df[df['status'] == 'completed'].copy()
        
        if not completed_df.empty:
            completed_df['processing_time'] = (completed_df['processed_date'] - completed_df['created_date']).dt.total_seconds() / 3600
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Processing time distribution
                fig = px.histogram(
                    completed_df,
                    x='processing_time',
                    title="Processing Time Distribution (Hours)",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Success rate by country
                country_success = df.groupby('country').apply(
                    lambda x: (x['status'] == 'completed').sum() / len(x) * 100
                ).reset_index()
                country_success.columns = ['Country', 'Success Rate']
                
                fig = px.bar(
                    country_success.sort_values('Success Rate', ascending=False).head(10),
                    x='Country',
                    y='Success Rate',
                    title="Success Rate by Country (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Performance metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_processing_time = completed_df['processing_time'].mean()
                st.metric("Avg Processing Time", f"{avg_processing_time:.1f} hrs")
            
            with col2:
                median_processing_time = completed_df['processing_time'].median()
                st.metric("Median Processing Time", f"{median_processing_time:.1f} hrs")
            
            with col3:
                same_day_completion = (completed_df['processing_time'] <= 24).sum() / len(completed_df) * 100
                st.metric("Same Day Completion", f"{same_day_completion:.1f}%")
            
            with col4:
                sla_compliance = (completed_df['processing_time'] <= 48).sum() / len(completed_df) * 100
                st.metric("SLA Compliance (48h)", f"{sla_compliance:.1f}%")
        
        else:
            st.info("No completed transactions available for performance analysis.")
    
    def _show_risk_analytics(self, df):
        """Risk analytics"""
        st.subheader("Risk Analytics")
        
        # High-value transaction analysis
        high_value_threshold = df['inr_amount'].quantile(0.9)
        high_value_df = df[df['inr_amount'] >= high_value_threshold]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("High Value Threshold", f"₹{high_value_threshold/1e7:.1f}Cr")
            st.metric("High Value Transactions", len(high_value_df))
            st.metric("% of Total Volume", f"{high_value_df['inr_amount'].sum() / df['inr_amount'].sum() * 100:.1f}%")
        
        with col2:
            # High-value transactions by country
            high_value_countries = high_value_df['country'].value_counts().head(10)
            
            fig = px.bar(
                x=high_value_countries.values,
                y=high_value_countries.index,
                orientation='h',
                title="High-Value Transactions by Country"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Unusual pattern detection
        st.subheader("Unusual Pattern Detection")
        
        # Transaction frequency by account
        account_frequency = df.groupby('from_account').size().sort_values(ascending=False)
        unusual_frequency = account_frequency[account_frequency > account_frequency.quantile(0.95)]
        
        if not unusual_frequency.empty:
            st.warning(f"Found {len(unusual_frequency)} accounts with unusually high transaction frequency")
            st.dataframe(unusual_frequency.to_frame('Transaction Count'), use_container_width=True)
        
        # Amount anomalies
        amount_mean = df['inr_amount'].mean()
        amount_std = df['inr_amount'].std()
        anomalous_amounts = df[abs(df['inr_amount'] - amount_mean) > 3 * amount_std]
        
        if not anomalous_amounts.empty:
            st.warning(f"Found {len(anomalous_amounts)} transactions with anomalous amounts")
            st.dataframe(
                anomalous_amounts[['transaction_id', 'from_account', 'to_account', 'inr_amount', 'country']],
                use_container_width=True
            )
    
    def _show_operational_efficiency(self, df):
        """Operational efficiency analysis"""
        st.subheader("Operational Efficiency")
        
        # Daily transaction capacity
        daily_stats = df.groupby(df['created_date'].dt.date).agg({
            'transaction_id': 'count',
            'inr_amount': 'sum'
        }).rename(columns={'transaction_id': 'count', 'inr_amount': 'volume'})
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily transaction count trend
            fig = px.line(
                daily_stats.reset_index(),
                x='created_date',
                y='count',
                title="Daily Transaction Count",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Daily volume trend
            fig = px.line(
                daily_stats.reset_index(),
                x='created_date',
                y='volume',
                title="Daily Transaction Volume (₹)",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Efficiency metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_daily_count = daily_stats['count'].mean()
            st.metric("Avg Daily Transactions", f"{avg_daily_count:.0f}")
        
        with col2:
            peak_daily_count = daily_stats['count'].max()
            st.metric("Peak Daily Count", f"{peak_daily_count:.0f}")
        
        with col3:
            capacity_utilization = avg_daily_count / peak_daily_count * 100
            st.metric("Capacity Utilization", f"{capacity_utilization:.1f}%")
        
        with col4:
            processing_efficiency = len(df[df['status'] == 'completed']) / len(df) * 100
            st.metric("Processing Efficiency", f"{processing_efficiency:.1f}%")
    
    def _show_customer_analytics(self, df):
        """Customer analytics"""
        st.subheader("Customer Analytics")
        
        # Account activity analysis
        account_stats = df.groupby('from_account').agg({
            'inr_amount': ['sum', 'mean', 'count'],
            'created_date': ['min', 'max']
        })
        
        account_stats.columns = ['Total Volume', 'Avg Amount', 'Transaction Count', 'First Transaction', 'Last Transaction']
        account_stats['Days Active'] = (account_stats['Last Transaction'] - account_stats['First Transaction']).dt.days
        
        # Top customers by volume
        st.subheader("Top Customers by Volume")
        top_customers = account_stats.sort_values('Total Volume', ascending=False).head(10)
        st.dataframe(top_customers, use_container_width=True)
        
        # Customer segmentation
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume-based segmentation
            volume_segments = pd.cut(
                account_stats['Total Volume'],
                bins=3,
                labels=['Low Volume', 'Medium Volume', 'High Volume']
            ).value_counts()
            
            fig = px.pie(
                values=volume_segments.values,
                names=volume_segments.index,
                title="Customer Segmentation by Volume"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Activity-based segmentation
            frequency_segments = pd.cut(
                account_stats['Transaction Count'],
                bins=3,
                labels=['Low Frequency', 'Medium Frequency', 'High Frequency']
            ).value_counts()
            
            fig = px.pie(
                values=frequency_segments.values,
                names=frequency_segments.index,
                title="Customer Segmentation by Frequency"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_seasonal_trends(self, df):
        """Seasonal trends analysis"""
        st.subheader("Seasonal Trends Analysis")
        
        # Monthly trends
        df['month'] = df['created_date'].dt.to_period('M')
        monthly_stats = df.groupby('month').agg({
            'transaction_id': 'count',
            'inr_amount': 'sum'
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                monthly_stats.reset_index(),
                x='month',
                y='transaction_id',
                title="Monthly Transaction Count Trend"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                monthly_stats.reset_index(),
                x='month',
                y='inr_amount',
                title="Monthly Volume Trend (₹)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Quarterly comparison
        df['quarter'] = df['created_date'].dt.to_period('Q')
        quarterly_stats = df.groupby('quarter')['inr_amount'].sum()
        
        if len(quarterly_stats) > 1:
            st.subheader("Quarterly Growth Analysis")
            quarterly_growth = quarterly_stats.pct_change() * 100
            
            fig = px.bar(
                x=quarterly_growth.index.astype(str),
                y=quarterly_growth.values,
                title="Quarter-over-Quarter Growth (%)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_custom_reports(self):
        """Custom reports interface"""
        st.subheader("Custom Report Builder")
        
        # Report configuration
        col1, col2 = st.columns(2)
        
        with col1:
            report_name = st.text_input("Report Name", "Custom Analysis Report")
            
            metrics = st.multiselect("Select Metrics", [
                "Transaction Count",
                "Total Volume", 
                "Average Amount",
                "Success Rate",
                "Processing Time",
                "Country Distribution",
                "Currency Mix"
            ])
        
        with col2:
            filters = st.multiselect("Apply Filters", [
                "Date Range",
                "Country",
                "Currency", 
                "Amount Range",
                "Transaction Status",
                "Account Type"
            ])
            
            chart_types = st.multiselect("Chart Types", [
                "Line Chart",
                "Bar Chart",
                "Pie Chart",
                "Scatter Plot",
                "Heatmap",
                "Box Plot"
            ])
        
        # Generate custom report
        if st.button("Generate Custom Report", type="primary"):
            if metrics:
                st.success(f"Generated custom report: {report_name}")
                
                # Sample custom report generation
                transactions_df = self.db_manager.get_transactions(limit=1000)
                
                if not transactions_df.empty:
                    st.subheader(f"📋 {report_name}")
                    
                    # Display selected metrics
                    for metric in metrics:
                        if metric == "Transaction Count":
                            st.metric("Total Transactions", len(transactions_df))
                        elif metric == "Total Volume":
                            total_vol = transactions_df['inr_amount'].sum()
                            st.metric("Total Volume", f"₹{total_vol/1e7:.2f}Cr")
                        elif metric == "Average Amount":
                            avg_amt = transactions_df['inr_amount'].mean()
                            st.metric("Average Amount", f"₹{avg_amt/1e5:.2f}L")
                        elif metric == "Success Rate":
                            success_rate = len(transactions_df[transactions_df['status'] == 'completed']) / len(transactions_df) * 100
                            st.metric("Success Rate", f"{success_rate:.1f}%")
                    
                    # Display selected charts
                    for chart_type in chart_types:
                        if chart_type == "Bar Chart" and "Country Distribution" in metrics:
                            country_counts = transactions_df['country'].value_counts().head(10)
                            fig = px.bar(x=country_counts.values, y=country_counts.index, orientation='h',
                                       title="Top Countries by Transaction Count")
                            st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.info("No data available for custom report generation")
            else:
                st.error("Please select at least one metric for the report")
    
    def _show_export_scheduling(self):
        """Export and scheduling interface"""
        st.subheader("Export & Scheduling")
        
        tab1, tab2 = st.tabs(["Export Reports", "Schedule Reports"])
        
        with tab1:
            st.subheader("Export Current Reports")
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox("Export Format", ["Excel", "PDF", "CSV", "JSON"])
                include_charts = st.checkbox("Include Charts", value=True)
                
            with col2:
                report_sections = st.multiselect("Report Sections", [
                    "Executive Summary",
                    "Key Metrics",
                    "Transaction Analysis", 
                    "Country Performance",
                    "Risk Analysis",
                    "Operational Metrics"
                ], default=["Executive Summary", "Key Metrics"])
            
            if st.button("Generate Export", type="primary"):
                # Generate export data
                transactions_df = self.db_manager.get_transactions(limit=1000)
                
                if export_format == "CSV":
                    csv_data = transactions_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV Report",
                        data=csv_data,
                        file_name=f"ript_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "JSON":
                    # Prepare summary data
                    summary_data = {
                        'report_generated': datetime.now().isoformat(),
                        'total_transactions': len(transactions_df),
                        'total_volume': float(transactions_df['inr_amount'].sum()),
                        'success_rate': float(len(transactions_df[transactions_df['status'] == 'completed']) / len(transactions_df) * 100),
                        'top_countries': transactions_df['country'].value_counts().head(5).to_dict(),
                        'currency_distribution': transactions_df['currency'].value_counts().to_dict()
                    }
                    
                    import json
                    json_data = json.dumps(summary_data, indent=2)
                    st.download_button(
                        label="Download JSON Report",
                        data=json_data,
                        file_name=f"ript_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                else:
                    st.info(f"{export_format} export functionality would be implemented here")
        
        with tab2:
            st.subheader("Schedule Automated Reports")
            
            col1, col2 = st.columns(2)
            
            with col1:
                schedule_name = st.text_input("Schedule Name", "Weekly Executive Report")
                report_type = st.selectbox("Report Type", self.report_types)
                frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"])
                
            with col2:
                recipients = st.text_area("Email Recipients", placeholder="email1@company.com, email2@company.com")
                delivery_time = st.time_input("Delivery Time", datetime.now().time())
                
            if st.button("Create Schedule"):
                schedule_data = {
                    'name': schedule_name,
                    'report_type': report_type,
                    'frequency': frequency,
                    'recipients': recipients,
                    'delivery_time': delivery_time.strftime('%H:%M'),
                    'created_date': datetime.now().isoformat(),
                    'status': 'Active'
                }
                
                # Save to session state (in production, would save to database)
                st.session_state.setdefault('scheduled_reports', []).append(schedule_data)
                st.success("Report schedule created successfully!")
            
            # Display existing schedules
            if 'scheduled_reports' in st.session_state and st.session_state.scheduled_reports:
                st.subheader("Existing Schedules")
                
                schedules_df = pd.DataFrame(st.session_state.scheduled_reports)
                st.dataframe(schedules_df, use_container_width=True)
    
    def _get_previous_period_volume(self, cutoff_date):
        """Get volume for the previous period for comparison"""
        # Simplified calculation - in real implementation, would query database
        return 50000000  # Mock previous period volume
    
    def _get_previous_period_count(self, cutoff_date):
        """Get transaction count for the previous period for comparison"""
        # Simplified calculation - in real implementation, would query database
        return 150  # Mock previous period count
    
    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary statistics"""
        transactions_df = self.db_manager.get_transactions(limit=1000)
        
        if transactions_df.empty:
            return {
                'total_volume': 0,
                'transaction_count': 0,
                'success_rate': 0,
                'active_countries': 0
            }
        
        return {
            'total_volume': transactions_df['inr_amount'].sum(),
            'transaction_count': len(transactions_df),
            'success_rate': len(transactions_df[transactions_df['status'] == 'completed']) / len(transactions_df) * 100,
            'active_countries': transactions_df['country'].nunique()
        }
