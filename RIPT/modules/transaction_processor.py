import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from typing import Dict, List, Optional

class TransactionProcessor:
    """Transaction Processing Module for SRVA trade settlements"""
    
    def __init__(self, db_manager, exchange_api):
        self.db_manager = db_manager
        self.exchange_api = exchange_api
        
        self.transaction_types = [
            "Export Settlement",
            "Import Payment", 
            "Service Export",
            "Service Import",
            "Investment Income",
            "Dividend Payment",
            "Interest Payment",
            "Other Trade Related"
        ]
        
        self.supported_countries = [
            "Russia", "Germany", "United Kingdom", "Singapore", "Malaysia",
            "Thailand", "South Korea", "Japan", "Australia", "New Zealand",
            "UAE", "Saudi Arabia", "Egypt", "South Africa", "Brazil",
            "Mexico", "Turkey", "Bangladesh", "Sri Lanka", "Myanmar"
        ]
    
    def show_interface(self):
        """Display transaction processing interface"""
        st.header("💱 Transaction Processing")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "New Transaction", 
            "Process Pending", 
            "Transaction History", 
            "Batch Processing"
        ])
        
        with tab1:
            self._show_new_transaction()
        
        with tab2:
            self._show_pending_transactions()
        
        with tab3:
            self._show_transaction_history()
        
        with tab4:
            self._show_batch_processing()
    
    def _show_new_transaction(self):
        """Create new transaction interface"""
        st.subheader("Create New Transaction")
        
        # Get SRVA accounts for dropdowns
        accounts_df = self.db_manager.get_srva_accounts(status='active')
        
        if accounts_df.empty:
            st.warning("⚠️ No active SRVA accounts found. Please create SRVA accounts first.")
            return
        
        account_options = accounts_df['account_id'].tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Transaction Details")
            
            transaction_id = st.text_input(
                "Transaction ID", 
                value=f"TXN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}",
                disabled=True
            )
            
            transaction_type = st.selectbox("Transaction Type", self.transaction_types)
            
            from_account = st.selectbox("From Account", account_options, key="from_acc")
            to_account = st.selectbox("To Account", account_options, key="to_acc")
            
            amount = st.number_input("Amount", min_value=0.01, value=1000.0, step=0.01)
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "RUB", "SGD", "AUD", "JPY"])
            
            country = st.selectbox("Trading Country", self.supported_countries)
            
        with col2:
            st.subheader("Settlement Information")
            
            # Get real-time exchange rate
            try:
                current_rate = self.exchange_api.get_rate(currency, 'INR')
                st.info(f"Current Rate: 1 {currency} = {current_rate:.4f} INR")
                
                exchange_rate = st.number_input(
                    f"Exchange Rate ({currency}/INR)", 
                    value=current_rate,
                    step=0.0001,
                    format="%.4f"
                )
                
                inr_amount = amount * exchange_rate
                st.metric("INR Equivalent", f"₹{inr_amount:,.2f}")
                
            except Exception as e:
                st.error(f"Error fetching exchange rate: {e}")
                exchange_rate = st.number_input(f"Exchange Rate ({currency}/INR)", value=83.0)
                inr_amount = amount * exchange_rate
            
            settlement_date = st.date_input("Settlement Date", datetime.now().date())
            
            priority = st.selectbox("Priority", ["Normal", "High", "Urgent"])
            
            description = st.text_area("Description/Reference", placeholder="Invoice number, trade details, etc.")
        
        # Additional details
        st.subheader("Compliance & Documentation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            trade_license = st.text_input("Trade License Number")
            invoice_number = st.text_input("Invoice Number")
            
        with col2:
            regulatory_approval = st.selectbox("Regulatory Approval Required", ["No", "RBI", "FEMA", "DGFT"])
            compliance_officer = st.text_input("Compliance Officer", value="system")
        
        # Risk assessment
        st.subheader("Risk Assessment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            customer_risk = st.selectbox("Customer Risk Level", ["Low", "Medium", "High"])
        
        with col2:
            transaction_risk = st.selectbox("Transaction Risk Level", ["Low", "Medium", "High"])
        
        with col3:
            aml_status = st.selectbox("AML Status", ["Cleared", "Pending", "Review Required"])
        
        # Submit transaction
        if st.button("Create Transaction", type="primary"):
            transaction_data = {
                'transaction_id': transaction_id,
                'from_account': from_account,
                'to_account': to_account,
                'amount': amount,
                'currency': currency,
                'exchange_rate': exchange_rate,
                'inr_amount': inr_amount,
                'transaction_type': transaction_type.lower().replace(' ', '_'),
                'description': description,
                'country': country,
                'settlement_date': settlement_date.isoformat(),
                'priority': priority,
                'trade_license': trade_license,
                'invoice_number': invoice_number,
                'regulatory_approval': regulatory_approval,
                'compliance_officer': compliance_officer,
                'customer_risk': customer_risk,
                'transaction_risk': transaction_risk,
                'aml_status': aml_status,
                'status': 'pending'
            }
            
            if self._validate_transaction(transaction_data):
                success = self.db_manager.insert_transaction(transaction_data)
                
                if success:
                    st.success("✅ Transaction created successfully!")
                    st.balloons()
                    
                    # Show transaction summary
                    st.subheader("Transaction Summary")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.json({
                            'Transaction ID': transaction_id,
                            'Amount': f"{amount} {currency}",
                            'INR Equivalent': f"₹{inr_amount:,.2f}",
                            'Exchange Rate': f"{exchange_rate:.4f}",
                            'Status': 'Pending'
                        })
                    
                    with col2:
                        st.info("**Next Steps:**\n- Compliance review\n- Documentation verification\n- Settlement processing")
                        
                        if st.button("Process Immediately"):
                            # Auto-process if conditions are met
                            if self._auto_process_eligible(transaction_data):
                                self.db_manager.update_transaction_status(transaction_id, 'completed')
                                st.success("Transaction processed automatically!")
                            else:
                                st.info("Transaction requires manual review")
                else:
                    st.error("❌ Failed to create transaction. Please try again.")
            else:
                st.error("❌ Please validate all fields and ensure accounts are different.")
    
    def _show_pending_transactions(self):
        """Process pending transactions interface"""
        st.subheader("Process Pending Transactions")
        
        pending_df = self.db_manager.get_transactions(status='pending')
        
        if not pending_df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Pending Transactions", len(pending_df))
            
            with col2:
                total_amount = pending_df['inr_amount'].sum()
                st.metric("Total Value", f"₹{total_amount:,.0f}")
            
            with col3:
                high_priority = len(pending_df[pending_df.get('priority', 'Normal') == 'High'])
                st.metric("High Priority", high_priority)
            
            with col4:
                urgent_count = len(pending_df[pending_df.get('priority', 'Normal') == 'Urgent'])
                st.metric("Urgent", urgent_count)
            
            st.markdown("---")
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                currency_filter = st.selectbox("Filter by Currency", ["All"] + pending_df['currency'].unique().tolist())
            
            with col2:
                country_filter = st.selectbox("Filter by Country", ["All"] + pending_df['country'].unique().tolist())
            
            # Apply filters
            filtered_df = pending_df.copy()
            if currency_filter != "All":
                filtered_df = filtered_df[filtered_df['currency'] == currency_filter]
            if country_filter != "All":
                filtered_df = filtered_df[filtered_df['country'] == country_filter]
            
            # Display transactions
            st.dataframe(
                filtered_df[['transaction_id', 'from_account', 'to_account', 'amount', 'currency', 'inr_amount', 'country', 'created_date']],
                use_container_width=True
            )
            
            # Process individual transaction
            st.subheader("Process Individual Transaction")
            
            selected_txn = st.selectbox("Select Transaction", filtered_df['transaction_id'].tolist())
            
            if selected_txn:
                txn_details = filtered_df[filtered_df['transaction_id'] == selected_txn].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Transaction Details")
                    st.write(f"**ID:** {txn_details['transaction_id']}")
                    st.write(f"**Amount:** {txn_details['amount']} {txn_details['currency']}")
                    st.write(f"**INR Amount:** ₹{txn_details['inr_amount']:,.2f}")
                    st.write(f"**From:** {txn_details['from_account']}")
                    st.write(f"**To:** {txn_details['to_account']}")
                    st.write(f"**Country:** {txn_details['country']}")
                
                with col2:
                    st.subheader("Process Transaction")
                    
                    action = st.selectbox("Action", ["Approve", "Reject", "Hold", "Request Info"])
                    
                    if action in ["Reject", "Hold", "Request Info"]:
                        reason = st.text_area("Reason/Comments", placeholder="Please provide reason...")
                    
                    if st.button(f"{action} Transaction", type="primary"):
                        if action == "Approve":
                            success = self.db_manager.update_transaction_status(selected_txn, 'completed')
                            if success:
                                st.success("✅ Transaction approved and completed!")
                                st.rerun()
                        elif action == "Reject":
                            success = self.db_manager.update_transaction_status(selected_txn, 'rejected')
                            if success:
                                st.success("Transaction rejected")
                                st.rerun()
                        elif action == "Hold":
                            success = self.db_manager.update_transaction_status(selected_txn, 'on_hold')
                            if success:
                                st.warning("Transaction placed on hold")
                                st.rerun()
        else:
            st.info("📝 No pending transactions found.")
    
    def _show_transaction_history(self):
        """Transaction history interface"""
        st.subheader("Transaction History")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_range = st.date_input(
                "Date Range",
                value=[datetime.now().date() - timedelta(days=30), datetime.now().date()],
                max_value=datetime.now().date()
            )
        
        with col2:
            status_filter = st.selectbox("Status", ["All", "completed", "pending", "rejected", "on_hold"])
        
        with col3:
            limit = st.selectbox("Records to Show", [50, 100, 200, 500])
        
        # Get transactions
        transactions_df = self.db_manager.get_transactions(limit=limit)
        
        if not transactions_df.empty:
            # Apply filters
            if status_filter != "All":
                transactions_df = transactions_df[transactions_df['status'] == status_filter]
            
            if len(date_range) == 2:
                transactions_df['created_date'] = pd.to_datetime(transactions_df['created_date'])
                start_date = pd.to_datetime(date_range[0])
                end_date = pd.to_datetime(date_range[1])
                transactions_df = transactions_df[
                    (transactions_df['created_date'] >= start_date) & 
                    (transactions_df['created_date'] <= end_date)
                ]
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Transactions", len(transactions_df))
            
            with col2:
                completed_count = len(transactions_df[transactions_df['status'] == 'completed'])
                st.metric("Completed", completed_count)
            
            with col3:
                total_volume = transactions_df['inr_amount'].sum()
                st.metric("Total Volume", f"₹{total_volume:,.0f}")
            
            with col4:
                avg_amount = transactions_df['inr_amount'].mean()
                st.metric("Average Amount", f"₹{avg_amount:,.0f}")
            
            st.markdown("---")
            
            # Transaction table
            st.dataframe(
                transactions_df[['transaction_id', 'transaction_type', 'amount', 'currency', 'inr_amount', 'country', 'status', 'created_date']],
                use_container_width=True
            )
            
            # Download data
            if st.button("Download Transaction Data"):
                csv = transactions_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No transactions found for the selected criteria.")
    
    def _show_batch_processing(self):
        """Batch processing interface"""
        st.subheader("Batch Processing")
        
        tab1, tab2 = st.tabs(["Bulk Upload", "Auto Processing"])
        
        with tab1:
            st.subheader("Bulk Transaction Upload")
            
            # Download template
            if st.button("Download Template"):
                template_data = {
                    'from_account': ['SRVA-001', 'SRVA-002'],
                    'to_account': ['SRVA-002', 'SRVA-003'],
                    'amount': [1000.0, 2000.0],
                    'currency': ['USD', 'EUR'],
                    'transaction_type': ['export_settlement', 'import_payment'],
                    'country': ['USA', 'Germany'],
                    'description': ['Export payment', 'Import settlement']
                }
                template_df = pd.DataFrame(template_data)
                csv = template_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV Template",
                    data=csv,
                    file_name="bulk_transactions_template.csv",
                    mime="text/csv"
                )
            
            uploaded_file = st.file_uploader("Upload Transaction CSV", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    if st.button("Process Bulk Upload", type="primary"):
                        success_count = 0
                        for _, row in df.iterrows():
                            transaction_data = self._prepare_bulk_transaction(row)
                            if self.db_manager.insert_transaction(transaction_data):
                                success_count += 1
                        
                        st.success(f"Successfully processed {success_count} out of {len(df)} transactions")
                
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
        
        with tab2:
            st.subheader("Automated Processing Rules")
            
            # Auto-processing criteria
            st.write("**Current Auto-Processing Rules:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("✅ **Eligible for Auto-Processing:**\n- Amount < ₹10 Lakhs\n- Low risk customers\n- Standard currencies\n- Complete documentation")
            
            with col2:
                st.warning("⚠️ **Requires Manual Review:**\n- Amount ≥ ₹10 Lakhs\n- High risk customers\n- Restricted countries\n- Missing documentation")
            
            # Auto-process pending transactions
            if st.button("Run Auto-Processing", type="primary"):
                pending_df = self.db_manager.get_transactions(status='pending')
                
                if not pending_df.empty:
                    auto_processed = 0
                    
                    for _, txn in pending_df.iterrows():
                        if self._auto_process_eligible(txn.to_dict()):
                            success = self.db_manager.update_transaction_status(txn['transaction_id'], 'completed')
                            if success:
                                auto_processed += 1
                    
                    if auto_processed > 0:
                        st.success(f"✅ Auto-processed {auto_processed} transactions")
                    else:
                        st.info("No transactions eligible for auto-processing")
                else:
                    st.info("No pending transactions to process")
    
    def _validate_transaction(self, transaction_data: Dict) -> bool:
        """Validate transaction data"""
        required_fields = ['transaction_id', 'from_account', 'to_account', 'amount', 'currency']
        
        for field in required_fields:
            if not transaction_data.get(field):
                return False
        
        # Ensure from and to accounts are different
        if transaction_data['from_account'] == transaction_data['to_account']:
            return False
        
        # Validate amount
        if transaction_data['amount'] <= 0:
            return False
        
        return True
    
    def _auto_process_eligible(self, transaction_data: Dict) -> bool:
        """Check if transaction is eligible for auto-processing"""
        # Amount threshold (10 Lakhs INR)
        if transaction_data.get('inr_amount', 0) >= 1000000:
            return False
        
        # Risk level check
        if transaction_data.get('customer_risk', 'Low') == 'High':
            return False
        
        if transaction_data.get('transaction_risk', 'Low') == 'High':
            return False
        
        # AML status
        if transaction_data.get('aml_status', 'Cleared') != 'Cleared':
            return False
        
        # Standard currencies
        standard_currencies = ['USD', 'EUR', 'GBP', 'SGD', 'AUD', 'JPY']
        if transaction_data.get('currency') not in standard_currencies:
            return False
        
        return True
    
    def _prepare_bulk_transaction(self, row) -> Dict:
        """Prepare transaction data from CSV row"""
        # Get current exchange rate
        try:
            exchange_rate = self.exchange_api.get_rate(row['currency'], 'INR')
        except:
            exchange_rate = 83.0  # Fallback rate
        
        transaction_id = f"TXN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        return {
            'transaction_id': transaction_id,
            'from_account': row['from_account'],
            'to_account': row['to_account'],
            'amount': float(row['amount']),
            'currency': row['currency'],
            'exchange_rate': exchange_rate,
            'inr_amount': float(row['amount']) * exchange_rate,
            'transaction_type': row['transaction_type'],
            'description': row.get('description', ''),
            'country': row.get('country', ''),
            'status': 'pending'
        }
    
    def get_transaction_summary(self) -> Dict:
        """Get transaction summary statistics"""
        transactions_df = self.db_manager.get_transactions(limit=1000)
        
        if transactions_df.empty:
            return {
                'total_transactions': 0,
                'completed_transactions': 0,
                'pending_transactions': 0,
                'total_volume': 0,
                'average_transaction_size': 0
            }
        
        return {
            'total_transactions': len(transactions_df),
            'completed_transactions': len(transactions_df[transactions_df['status'] == 'completed']),
            'pending_transactions': len(transactions_df[transactions_df['status'] == 'pending']),
            'total_volume': transactions_df['inr_amount'].sum(),
            'average_transaction_size': transactions_df['inr_amount'].mean()
        }
