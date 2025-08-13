import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

class SettlementCalculator:
    """Settlement Calculator for SRVA transactions with real-time exchange rates"""
    
    def __init__(self, exchange_api):
        self.exchange_api = exchange_api
        
        self.settlement_types = [
            "Immediate Settlement",
            "Next Business Day",
            "T+2 Settlement",
            "Forward Settlement",
            "Spot Settlement"
        ]
        
        self.charges_config = {
            'processing_fee': 0.0025,  # 0.25%
            'exchange_margin': 0.005,  # 0.5%
            'swift_charge': 25.0,      # Flat fee
            'regulatory_fee': 0.001,   # 0.1%
            'min_charge': 100.0,       # Minimum charge
            'max_charge': 10000.0      # Maximum charge
        }
    
    def show_interface(self):
        """Display settlement calculator interface"""
        st.header("💰 Settlement Calculator")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Single Settlement", 
            "Bulk Calculator", 
            "Rate Comparison", 
            "Settlement Analytics"
        ])
        
        with tab1:
            self._show_single_settlement()
        
        with tab2:
            self._show_bulk_calculator()
        
        with tab3:
            self._show_rate_comparison()
        
        with tab4:
            self._show_settlement_analytics()
    
    def _show_single_settlement(self):
        """Single settlement calculation interface"""
        st.subheader("Calculate Single Settlement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Transaction Details")
            
            amount = st.number_input("Transaction Amount", min_value=0.01, value=10000.0, step=0.01)
            from_currency = st.selectbox("From Currency", ["USD", "EUR", "GBP", "RUB", "SGD", "AUD", "JPY", "CAD"])
            to_currency = st.selectbox("To Currency", ["INR", "USD", "EUR", "GBP"], index=0)
            
            settlement_type = st.selectbox("Settlement Type", self.settlement_types)
            
            # Get real-time rate
            try:
                current_rate = self.exchange_api.get_rate(from_currency, to_currency)
                st.info(f"Current Market Rate: 1 {from_currency} = {current_rate:.4f} {to_currency}")
                
                use_custom_rate = st.checkbox("Use Custom Exchange Rate")
                
                if use_custom_rate:
                    exchange_rate = st.number_input(
                        f"Custom Rate ({from_currency}/{to_currency})", 
                        value=current_rate,
                        step=0.0001,
                        format="%.4f"
                    )
                else:
                    exchange_rate = current_rate
                    
            except Exception as e:
                st.error(f"Error fetching exchange rate: {e}")
                exchange_rate = st.number_input(f"Exchange Rate ({from_currency}/{to_currency})", value=83.0)
            
            priority = st.selectbox("Priority", ["Standard", "High", "Urgent"])
            
        with col2:
            st.subheader("Settlement Calculation")
            
            # Calculate settlement
            settlement_result = self._calculate_settlement(amount, from_currency, to_currency, exchange_rate, settlement_type, priority)
            
            # Display results
            st.metric("Gross Amount", f"{settlement_result['gross_amount']:.2f} {to_currency}")
            st.metric("Total Charges", f"{settlement_result['total_charges']:.2f} {to_currency}")
            st.metric("Net Settlement", f"{settlement_result['net_amount']:.2f} {to_currency}")
            
            # Exchange rate details
            st.subheader("Rate Details")
            st.metric("Applied Rate", f"{settlement_result['applied_rate']:.4f}")
            st.metric("Market Rate", f"{current_rate:.4f}")
            st.metric("Rate Margin", f"{settlement_result['rate_margin']:.4f}")
            
            # Charges breakdown
            st.subheader("Charges Breakdown")
            charges_df = pd.DataFrame(list(settlement_result['charges_breakdown'].items()), 
                                    columns=['Charge Type', 'Amount'])
            charges_df['Amount'] = charges_df['Amount'].apply(lambda x: f"{x:.2f} {to_currency}")
            st.dataframe(charges_df, hide_index=True)
        
        # Settlement timeline
        st.markdown("---")
        st.subheader("Settlement Timeline")
        
        timeline = self._get_settlement_timeline(settlement_type)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Initiation:** {timeline['initiation']}")
        
        with col2:
            st.info(f"**Processing:** {timeline['processing']}")
        
        with col3:
            st.success(f"**Settlement:** {timeline['settlement']}")
        
        # Save calculation
        if st.button("Save Calculation", type="primary"):
            calculation_data = {
                'amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate,
                'settlement_type': settlement_type,
                'priority': priority,
                'result': settlement_result,
                'timestamp': datetime.now().isoformat()
            }
            
            st.session_state.setdefault('saved_calculations', []).append(calculation_data)
            st.success("✅ Calculation saved successfully!")
    
    def _show_bulk_calculator(self):
        """Bulk settlement calculator interface"""
        st.subheader("Bulk Settlement Calculator")
        
        # Manual entry
        st.subheader("Add Transactions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            bulk_amount = st.number_input("Amount", min_value=0.01, value=1000.0, key="bulk_amount")
        
        with col2:
            bulk_from_currency = st.selectbox("From Currency", ["USD", "EUR", "GBP", "RUB"], key="bulk_from")
        
        with col3:
            bulk_to_currency = st.selectbox("To Currency", ["INR", "USD", "EUR"], index=0, key="bulk_to")
        
        with col4:
            bulk_settlement = st.selectbox("Settlement Type", self.settlement_types, key="bulk_settlement")
        
        if st.button("Add Transaction"):
            if 'bulk_transactions' not in st.session_state:
                st.session_state.bulk_transactions = []
            
            try:
                rate = self.exchange_api.get_rate(bulk_from_currency, bulk_to_currency)
                settlement_result = self._calculate_settlement(
                    bulk_amount, bulk_from_currency, bulk_to_currency, rate, bulk_settlement, "Standard"
                )
                
                transaction = {
                    'amount': bulk_amount,
                    'from_currency': bulk_from_currency,
                    'to_currency': bulk_to_currency,
                    'rate': rate,
                    'settlement_type': bulk_settlement,
                    'net_amount': settlement_result['net_amount'],
                    'total_charges': settlement_result['total_charges']
                }
                
                st.session_state.bulk_transactions.append(transaction)
                st.success("Transaction added!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error adding transaction: {e}")
        
        # CSV Upload
        st.markdown("---")
        st.subheader("Upload Bulk Transactions")
        
        # Download template
        if st.button("Download CSV Template"):
            template_data = {
                'amount': [1000.0, 2000.0, 5000.0],
                'from_currency': ['USD', 'EUR', 'GBP'],
                'to_currency': ['INR', 'INR', 'INR'],
                'settlement_type': ['Immediate Settlement', 'Next Business Day', 'T+2 Settlement']
            }
            template_df = pd.DataFrame(template_data)
            csv = template_df.to_csv(index=False)
            st.download_button(
                label="Download Template",
                data=csv,
                file_name="bulk_settlement_template.csv",
                mime="text/csv"
            )
        
        uploaded_file = st.file_uploader("Upload CSV File", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview:")
                st.dataframe(df.head())
                
                if st.button("Process Bulk Upload"):
                    bulk_results = []
                    
                    for _, row in df.iterrows():
                        try:
                            rate = self.exchange_api.get_rate(row['from_currency'], row['to_currency'])
                            result = self._calculate_settlement(
                                row['amount'], row['from_currency'], row['to_currency'], 
                                rate, row['settlement_type'], "Standard"
                            )
                            
                            bulk_results.append({
                                'amount': row['amount'],
                                'from_currency': row['from_currency'],
                                'to_currency': row['to_currency'],
                                'rate': rate,
                                'settlement_type': row['settlement_type'],
                                'net_amount': result['net_amount'],
                                'total_charges': result['total_charges']
                            })
                        except Exception as e:
                            st.error(f"Error processing row: {e}")
                    
                    st.session_state.bulk_transactions = bulk_results
                    st.success(f"Processed {len(bulk_results)} transactions!")
                    st.rerun()
            
            except Exception as e:
                st.error(f"Error processing file: {e}")
        
        # Display bulk results
        if 'bulk_transactions' in st.session_state and st.session_state.bulk_transactions:
            st.markdown("---")
            st.subheader("Bulk Settlement Results")
            
            bulk_df = pd.DataFrame(st.session_state.bulk_transactions)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Transactions", len(bulk_df))
            
            with col2:
                total_net = bulk_df['net_amount'].sum()
                st.metric("Total Net Amount", f"{total_net:,.2f}")
            
            with col3:
                total_charges = bulk_df['total_charges'].sum()
                st.metric("Total Charges", f"{total_charges:,.2f}")
            
            with col4:
                avg_rate = bulk_df['rate'].mean()
                st.metric("Average Rate", f"{avg_rate:.4f}")
            
            # Display table
            st.dataframe(bulk_df, use_container_width=True)
            
            # Export results
            if st.button("Export Results"):
                csv = bulk_df.to_csv(index=False)
                st.download_button(
                    label="Download Results CSV",
                    data=csv,
                    file_name=f"bulk_settlement_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Clear transactions
            if st.button("Clear All Transactions"):
                del st.session_state.bulk_transactions
                st.rerun()
    
    def _show_rate_comparison(self):
        """Rate comparison interface"""
        st.subheader("Exchange Rate Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            base_currency = st.selectbox("Base Currency", ["INR", "USD", "EUR", "GBP"])
            target_currencies = st.multiselect(
                "Target Currencies", 
                ["USD", "EUR", "GBP", "RUB", "SGD", "AUD", "JPY", "CAD"],
                default=["USD", "EUR", "GBP"]
            )
        
        with col2:
            comparison_period = st.selectbox("Comparison Period", [
                "Current Rates",
                "Last 7 Days",
                "Last 30 Days",
                "Last 90 Days"
            ])
        
        if target_currencies:
            if comparison_period == "Current Rates":
                # Current rates comparison
                rates_data = []
                
                for currency in target_currencies:
                    try:
                        rate = self.exchange_api.get_rate(base_currency, currency)
                        # Calculate settlement cost for standard amount
                        settlement_result = self._calculate_settlement(10000, base_currency, currency, rate, "Immediate Settlement", "Standard")
                        
                        rates_data.append({
                            'Currency': currency,
                            'Exchange Rate': rate,
                            'Settlement Rate': settlement_result['applied_rate'],
                            'Margin': settlement_result['rate_margin'],
                            'Charges (10K)': settlement_result['total_charges'],
                            'Net Amount (10K)': settlement_result['net_amount']
                        })
                    except Exception as e:
                        st.error(f"Error fetching rate for {currency}: {e}")
                
                if rates_data:
                    rates_df = pd.DataFrame(rates_data)
                    st.dataframe(rates_df, use_container_width=True)
                    
                    # Rate visualization
                    fig = px.bar(
                        rates_df, 
                        x='Currency', 
                        y='Exchange Rate',
                        title=f"{base_currency} Exchange Rates Comparison",
                        color='Exchange Rate',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            else:
                # Historical rate trends
                st.subheader(f"Rate Trends - {comparison_period}")
                
                # Get historical data
                days_map = {
                    "Last 7 Days": 7,
                    "Last 30 Days": 30,
                    "Last 90 Days": 90
                }
                
                days = days_map.get(comparison_period, 30)
                
                for currency in target_currencies:
                    try:
                        trend_data = self.exchange_api.get_rate_trend(currency, days)
                        
                        if trend_data:
                            trend_df = pd.DataFrame(trend_data)
                            trend_df['date'] = pd.to_datetime(trend_df['date'])
                            
                            fig = px.line(
                                trend_df,
                                x='date',
                                y='rate',
                                title=f"{base_currency}/{currency} Rate Trend",
                                markers=True
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info(f"No historical data available for {currency}")
                    
                    except Exception as e:
                        st.error(f"Error fetching trend for {currency}: {e}")
    
    def _show_settlement_analytics(self):
        """Settlement analytics interface"""
        st.subheader("Settlement Analytics")
        
        # Analytics for saved calculations
        if 'saved_calculations' in st.session_state and st.session_state.saved_calculations:
            calculations = st.session_state.saved_calculations
            calc_df = pd.DataFrame(calculations)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Calculations", len(calc_df))
            
            with col2:
                total_volume = sum([calc['result']['gross_amount'] for calc in calculations])
                st.metric("Total Volume", f"{total_volume:,.0f}")
            
            with col3:
                total_charges = sum([calc['result']['total_charges'] for calc in calculations])
                st.metric("Total Charges", f"{total_charges:,.0f}")
            
            with col4:
                avg_margin = sum([calc['result']['rate_margin'] for calc in calculations]) / len(calculations)
                st.metric("Avg Rate Margin", f"{avg_margin:.4f}")
            
            # Analytics charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Currency distribution
                currency_counts = {}
                for calc in calculations:
                    from_curr = calc['from_currency']
                    currency_counts[from_curr] = currency_counts.get(from_curr, 0) + 1
                
                if currency_counts:
                    curr_df = pd.DataFrame(list(currency_counts.items()), columns=['Currency', 'Count'])
                    fig = px.pie(curr_df, values='Count', names='Currency', title="Currency Distribution")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Settlement type distribution
                settlement_counts = {}
                for calc in calculations:
                    settlement_type = calc['settlement_type']
                    settlement_counts[settlement_type] = settlement_counts.get(settlement_type, 0) + 1
                
                if settlement_counts:
                    settlement_df = pd.DataFrame(list(settlement_counts.items()), columns=['Settlement Type', 'Count'])
                    fig = px.bar(settlement_df, x='Settlement Type', y='Count', title="Settlement Type Distribution")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Detailed calculations table
            st.subheader("Calculation History")
            
            display_data = []
            for calc in calculations:
                display_data.append({
                    'Timestamp': calc['timestamp'],
                    'Amount': f"{calc['amount']} {calc['from_currency']}",
                    'To Currency': calc['to_currency'],
                    'Exchange Rate': f"{calc['exchange_rate']:.4f}",
                    'Settlement Type': calc['settlement_type'],
                    'Net Amount': f"{calc['result']['net_amount']:.2f}",
                    'Total Charges': f"{calc['result']['total_charges']:.2f}"
                })
            
            display_df = pd.DataFrame(display_data)
            st.dataframe(display_df, use_container_width=True)
            
            # Clear history
            if st.button("Clear Calculation History"):
                del st.session_state.saved_calculations
                st.rerun()
        
        else:
            st.info("No saved calculations available. Perform some calculations to see analytics.")
    
    def _calculate_settlement(self, amount: float, from_currency: str, to_currency: str, 
                            exchange_rate: float, settlement_type: str, priority: str) -> Dict:
        """Calculate settlement with all charges and fees"""
        
        # Gross amount calculation
        gross_amount = amount * exchange_rate
        
        # Apply rate margin based on settlement type and priority
        rate_margin = self._get_rate_margin(settlement_type, priority)
        applied_rate = exchange_rate * (1 + rate_margin)
        
        # Charges calculation
        charges = self._calculate_charges(amount, from_currency, to_currency, settlement_type, priority)
        total_charges = sum(charges.values())
        
        # Net settlement amount
        net_amount = gross_amount - total_charges
        
        return {
            'gross_amount': gross_amount,
            'applied_rate': applied_rate,
            'rate_margin': rate_margin,
            'total_charges': total_charges,
            'net_amount': net_amount,
            'charges_breakdown': charges
        }
    
    def _calculate_charges(self, amount: float, from_currency: str, to_currency: str, 
                         settlement_type: str, priority: str) -> Dict[str, float]:
        """Calculate all applicable charges"""
        charges = {}
        
        # Processing fee (percentage of amount)
        processing_fee = amount * self.charges_config['processing_fee']
        charges['Processing Fee'] = processing_fee
        
        # Exchange margin (percentage of amount)
        exchange_margin = amount * self.charges_config['exchange_margin']
        charges['Exchange Margin'] = exchange_margin
        
        # SWIFT charge (flat fee)
        charges['SWIFT Charge'] = self.charges_config['swift_charge']
        
        # Regulatory fee (percentage of amount)
        regulatory_fee = amount * self.charges_config['regulatory_fee']
        charges['Regulatory Fee'] = regulatory_fee
        
        # Priority charges
        if priority == "High":
            charges['Priority Charge'] = 50.0
        elif priority == "Urgent":
            charges['Urgent Charge'] = 100.0
        
        # Settlement type charges
        if settlement_type == "Immediate Settlement":
            charges['Immediate Settlement Fee'] = 75.0
        elif settlement_type == "Forward Settlement":
            charges['Forward Settlement Fee'] = 25.0
        
        # Apply minimum and maximum charge limits
        total_charges = sum(charges.values())
        
        if total_charges < self.charges_config['min_charge']:
            charges['Minimum Charge Adjustment'] = self.charges_config['min_charge'] - total_charges
        elif total_charges > self.charges_config['max_charge']:
            # Apply proportional reduction
            reduction_factor = self.charges_config['max_charge'] / total_charges
            for key in charges:
                charges[key] *= reduction_factor
            charges['Maximum Charge Cap Applied'] = 0.0
        
        return charges
    
    def _get_rate_margin(self, settlement_type: str, priority: str) -> float:
        """Calculate rate margin based on settlement type and priority"""
        base_margin = 0.005  # 0.5% base margin
        
        # Settlement type adjustments
        if settlement_type == "Immediate Settlement":
            base_margin += 0.002  # Additional 0.2%
        elif settlement_type == "Forward Settlement":
            base_margin += 0.001  # Additional 0.1%
        
        # Priority adjustments
        if priority == "High":
            base_margin += 0.001  # Additional 0.1%
        elif priority == "Urgent":
            base_margin += 0.002  # Additional 0.2%
        
        return base_margin
    
    def _get_settlement_timeline(self, settlement_type: str) -> Dict[str, str]:
        """Get settlement timeline based on type"""
        now = datetime.now()
        
        timelines = {
            "Immediate Settlement": {
                "initiation": "Immediate",
                "processing": "Within 30 minutes",
                "settlement": "Same day"
            },
            "Next Business Day": {
                "initiation": "Same day",
                "processing": "End of day",
                "settlement": "Next business day"
            },
            "T+2 Settlement": {
                "initiation": "Same day",
                "processing": "T+1",
                "settlement": "T+2"
            },
            "Forward Settlement": {
                "initiation": "Contract date",
                "processing": "Value date - 1",
                "settlement": "Value date"
            },
            "Spot Settlement": {
                "initiation": "Trade date",
                "processing": "T+1",
                "settlement": "T+2"
            }
        }
        
        return timelines.get(settlement_type, {
            "initiation": "Same day",
            "processing": "T+1",
            "settlement": "T+2"
        })
    
    def get_settlement_summary(self) -> Dict:
        """Get settlement calculator summary statistics"""
        if 'saved_calculations' not in st.session_state:
            return {
                'total_calculations': 0,
                'total_volume': 0,
                'average_charges': 0,
                'most_used_currency': 'N/A'
            }
        
        calculations = st.session_state.saved_calculations
        
        if not calculations:
            return {
                'total_calculations': 0,
                'total_volume': 0,
                'average_charges': 0,
                'most_used_currency': 'N/A'
            }
        
        total_volume = sum([calc['result']['gross_amount'] for calc in calculations])
        total_charges = sum([calc['result']['total_charges'] for calc in calculations])
        
        # Most used currency
        currency_counts = {}
        for calc in calculations:
            curr = calc['from_currency']
            currency_counts[curr] = currency_counts.get(curr, 0) + 1
        
        most_used = max(currency_counts, key=currency_counts.get) if currency_counts else 'N/A'
        
        return {
            'total_calculations': len(calculations),
            'total_volume': total_volume,
            'average_charges': total_charges / len(calculations),
            'most_used_currency': most_used
        }
