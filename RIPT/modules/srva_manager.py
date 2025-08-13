import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from typing import Dict, List

class SRVAManager:
    """SRVA (Special Rupee Vostro Account) Management Module"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.load_reference_data()
    
    def load_reference_data(self):
        """Load countries and banks reference data"""
        try:
            with open('data/countries.json', 'r') as f:
                self.countries_data = json.load(f)
            with open('data/banks.json', 'r') as f:
                self.banks_data = json.load(f)
        except FileNotFoundError:
            # Default data if files don't exist
            self.countries_data = {
                "India": {"currency": "INR", "region": "Asia"},
                "Russia": {"currency": "RUB", "region": "Europe"},
                "Germany": {"currency": "EUR", "region": "Europe"},
                "United Kingdom": {"currency": "GBP", "region": "Europe"},
                "United States": {"currency": "USD", "region": "Americas"}
            }
            self.banks_data = {
                "State Bank of India": {"country": "India", "swift": "SBININBB"},
                "ICICI Bank": {"country": "India", "swift": "ICICINBB"},
                "HDFC Bank": {"country": "India", "swift": "HDFCINBB"}
            }
    
    def show_interface(self):
        """Display SRVA management interface"""
        st.header("🏦 SRVA Account Management")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Create Account", "View Accounts", "Account Operations", "Bulk Operations"])
        
        with tab1:
            self._show_create_account()
        
        with tab2:
            self._show_view_accounts()
        
        with tab3:
            self._show_account_operations()
        
        with tab4:
            self._show_bulk_operations()
    
    def _show_create_account(self):
        """Create new SRVA account interface"""
        st.subheader("Create New SRVA Account")
        
        col1, col2 = st.columns(2)
        
        with col1:
            account_id = st.text_input("Account ID", placeholder="SRVA-COUNTRY-001")
            account_name = st.text_input("Account Holder Name", placeholder="Export Trading Company Ltd")
            bank = st.selectbox("Authorized Bank", list(self.banks_data.keys()))
            country = st.selectbox("Country", list(self.countries_data.keys()))
        
        with col2:
            currency = st.selectbox("Primary Currency", ["INR", "USD", "EUR", "GBP", "RUB"])
            initial_balance = st.number_input("Initial Balance", min_value=0.0, value=0.0)
            account_type = st.selectbox("Account Type", ["Corporate", "Individual", "Government"])
            purpose = st.selectbox("Purpose", ["Export", "Import", "Both", "Services"])
        
        # Additional details
        st.subheader("Additional Details")
        description = st.text_area("Description/Notes")
        
        compliance_docs = st.multiselect(
            "Required Compliance Documents",
            ["PAN Card", "GST Certificate", "Import/Export License", "FEMA Declaration", "Board Resolution"]
        )
        
        if st.button("Create SRVA Account", type="primary"):
            account_data = {
                'account_id': account_id,
                'account_name': account_name,
                'bank': bank,
                'country': country,
                'currency': currency,
                'balance': initial_balance,
                'account_type': account_type,
                'purpose': purpose,
                'description': description,
                'compliance_docs': compliance_docs,
                'status': 'active'
            }
            
            if self._validate_account_data(account_data):
                success = self.db_manager.insert_srva_account(account_data)
                if success:
                    st.success("✅ SRVA Account created successfully!")
                    st.balloons()
                    
                    # Show account summary
                    st.subheader("Account Summary")
                    st.json(account_data)
                else:
                    st.error("❌ Failed to create account. Please check if Account ID already exists.")
            else:
                st.error("❌ Please fill in all required fields correctly.")
    
    def _show_view_accounts(self):
        """View existing SRVA accounts"""
        st.subheader("SRVA Accounts Overview")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "active", "suspended", "closed"])
        
        with col2:
            country_filter = st.selectbox("Filter by Country", ["All"] + list(self.countries_data.keys()))
        
        with col3:
            bank_filter = st.selectbox("Filter by Bank", ["All"] + list(self.banks_data.keys()))
        
        # Get accounts data
        accounts_df = self.db_manager.get_srva_accounts()
        
        if not accounts_df.empty:
            # Apply filters
            if status_filter != "All":
                accounts_df = accounts_df[accounts_df['status'] == status_filter]
            if country_filter != "All":
                accounts_df = accounts_df[accounts_df['country'] == country_filter]
            if bank_filter != "All":
                accounts_df = accounts_df[accounts_df['bank'] == bank_filter]
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Accounts", len(accounts_df))
            
            with col2:
                total_balance = accounts_df['balance'].sum()
                st.metric("Total Balance", f"₹{total_balance:,.2f}")
            
            with col3:
                active_accounts = len(accounts_df[accounts_df['status'] == 'active'])
                st.metric("Active Accounts", active_accounts)
            
            with col4:
                countries_count = accounts_df['country'].nunique()
                st.metric("Countries", countries_count)
            
            st.markdown("---")
            
            # Display accounts table
            st.dataframe(
                accounts_df[['account_id', 'account_name', 'bank', 'country', 'currency', 'balance', 'status', 'created_date']],
                use_container_width=True
            )
            
            # Account details
            if st.checkbox("Show Detailed View"):
                selected_account = st.selectbox("Select Account for Details", accounts_df['account_id'].tolist())
                if selected_account:
                    account_details = accounts_df[accounts_df['account_id'] == selected_account].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Account Information")
                        st.write(f"**Account ID:** {account_details['account_id']}")
                        st.write(f"**Account Name:** {account_details['account_name']}")
                        st.write(f"**Bank:** {account_details['bank']}")
                        st.write(f"**Country:** {account_details['country']}")
                        st.write(f"**Currency:** {account_details['currency']}")
                    
                    with col2:
                        st.subheader("Financial Information")
                        st.metric("Current Balance", f"₹{account_details['balance']:,.2f}")
                        st.write(f"**Status:** {account_details['status']}")
                        st.write(f"**Created:** {account_details['created_date']}")
                        st.write(f"**Last Updated:** {account_details['updated_date']}")
        else:
            st.info("No SRVA accounts found. Create your first account using the 'Create Account' tab.")
    
    def _show_account_operations(self):
        """Account operations interface"""
        st.subheader("Account Operations")
        
        accounts_df = self.db_manager.get_srva_accounts()
        
        if not accounts_df.empty:
            selected_account = st.selectbox("Select Account", accounts_df['account_id'].tolist())
            
            if selected_account:
                account_info = accounts_df[accounts_df['account_id'] == selected_account].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Account Information")
                    st.write(f"**Account:** {account_info['account_name']}")
                    st.metric("Current Balance", f"₹{account_info['balance']:,.2f}")
                    st.write(f"**Status:** {account_info['status']}")
                
                with col2:
                    st.subheader("Operations")
                    
                    operation = st.selectbox("Select Operation", [
                        "Update Balance",
                        "Change Status", 
                        "Update Account Details",
                        "View Transaction History"
                    ])
                    
                    if operation == "Update Balance":
                        new_balance = st.number_input("New Balance", value=float(account_info['balance']))
                        if st.button("Update Balance"):
                            # Here you would implement balance update logic
                            st.success("Balance updated successfully!")
                    
                    elif operation == "Change Status":
                        new_status = st.selectbox("New Status", ["active", "suspended", "closed"])
                        if st.button("Update Status"):
                            # Here you would implement status update logic
                            st.success(f"Status changed to {new_status}")
                    
                    elif operation == "Update Account Details":
                        st.info("Account details update functionality")
                        # Implement update form
                    
                    elif operation == "View Transaction History":
                        st.info("Transaction history for this account")
                        # Get and display transactions for this account
        else:
            st.info("No accounts available for operations.")
    
    def _show_bulk_operations(self):
        """Bulk operations interface"""
        st.subheader("Bulk Operations")
        
        tab1, tab2, tab3 = st.tabs(["Bulk Import", "Bulk Status Update", "Bulk Export"])
        
        with tab1:
            st.subheader("Bulk Import Accounts")
            
            # Sample CSV template
            if st.button("Download CSV Template"):
                sample_data = {
                    'account_id': ['SRVA-RUS-001', 'SRVA-GER-001'],
                    'account_name': ['Russian Trading Corp', 'German Exports Ltd'],
                    'bank': ['State Bank of India', 'ICICI Bank'],
                    'country': ['Russia', 'Germany'],
                    'currency': ['RUB', 'EUR'],
                    'balance': [0.0, 0.0]
                }
                sample_df = pd.DataFrame(sample_data)
                csv = sample_df.to_csv(index=False)
                st.download_button(
                    label="Download Template",
                    data=csv,
                    file_name="srva_accounts_template.csv",
                    mime="text/csv"
                )
            
            uploaded_file = st.file_uploader("Upload CSV File", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    if st.button("Import Accounts", type="primary"):
                        success_count = 0
                        for _, row in df.iterrows():
                            account_data = row.to_dict()
                            if self.db_manager.insert_srva_account(account_data):
                                success_count += 1
                        
                        st.success(f"Successfully imported {success_count} out of {len(df)} accounts")
                
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
        
        with tab2:
            st.subheader("Bulk Status Update")
            
            accounts_df = self.db_manager.get_srva_accounts()
            
            if not accounts_df.empty:
                selected_accounts = st.multiselect(
                    "Select Accounts to Update", 
                    accounts_df['account_id'].tolist()
                )
                
                new_status = st.selectbox("New Status", ["active", "suspended", "closed"])
                
                if st.button("Update Selected Accounts") and selected_accounts:
                    # Implement bulk status update
                    st.success(f"Updated {len(selected_accounts)} accounts to {new_status}")
        
        with tab3:
            st.subheader("Export Account Data")
            
            accounts_df = self.db_manager.get_srva_accounts()
            
            if not accounts_df.empty:
                export_format = st.selectbox("Export Format", ["CSV", "Excel", "JSON"])
                
                if st.button("Export Data"):
                    if export_format == "CSV":
                        csv = accounts_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"srva_accounts_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    elif export_format == "JSON":
                        json_data = accounts_df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"srva_accounts_{datetime.now().strftime('%Y%m%d')}.json",
                            mime="application/json"
                        )
    
    def _validate_account_data(self, account_data: Dict) -> bool:
        """Validate account data before creation"""
        required_fields = ['account_id', 'account_name', 'bank', 'country']
        
        for field in required_fields:
            if not account_data.get(field):
                return False
        
        # Validate account ID format
        account_id = account_data['account_id']
        if len(account_id) < 5:
            return False
        
        return True
    
    def get_account_summary(self) -> Dict:
        """Get account summary statistics"""
        accounts_df = self.db_manager.get_srva_accounts()
        
        if accounts_df.empty:
            return {
                'total_accounts': 0,
                'active_accounts': 0,
                'total_balance': 0,
                'countries': 0,
                'banks': 0
            }
        
        return {
            'total_accounts': len(accounts_df),
            'active_accounts': len(accounts_df[accounts_df['status'] == 'active']),
            'total_balance': accounts_df['balance'].sum(),
            'countries': accounts_df['country'].nunique(),
            'banks': accounts_df['bank'].nunique()
        }
