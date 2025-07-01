import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Revenue Leakage Detector",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define functions for data loading and visualization
@st.cache_data
def load_data():
    """Load and cache the transaction data"""
    try:
        data = pd.read_csv("../data/processed/cleaned_transactions.csv")
        # Convert date columns to datetime
        date_cols = ['Invoice_Date', 'Due_Date', 'Payment_Date']
        for col in date_cols:
            if col in data.columns:
                data[col] = pd.to_datetime(data[col])
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def format_currency(amount):
    """Format numbers as currency"""
    return f"₹{amount:,.2f}"

# Load data
df = load_data()

# App title and description
st.title("💰 Revenue Leakage Detector")
st.markdown("""
This dashboard helps identify and analyze revenue losses in enterprise transactions.
Detect missing payments, payment delays, over-discounts, and other leakage points.
""")

# Sidebar filters
st.sidebar.header("Filters")

if df is not None:
    # Date range filter
    min_date = df['Invoice_Date'].min().date()
    max_date = df['Invoice_Date'].max().date()
    date_range = st.sidebar.date_input(
        "Invoice Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = df[(df['Invoice_Date'].dt.date >= start_date) & 
                        (df['Invoice_Date'].dt.date <= end_date)]
    else:
        filtered_df = df
    
    # Region filter
    regions = ['All'] + sorted(df['Region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Region", regions)
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['Region'] == selected_region]
    
    # Payment method filter
    payment_methods = ['All'] + sorted(df['Payment_Method'].unique().tolist())
    selected_payment_method = st.sidebar.selectbox("Payment Method", payment_methods)
    if selected_payment_method != 'All':
        filtered_df = filtered_df[filtered_df['Payment_Method'] == selected_payment_method]
    
    # Risk category filter
    risk_cats = ['All', 'Critical', 'High', 'Medium', 'Low']
    selected_risk = st.sidebar.selectbox("Risk Category", risk_cats)
    if selected_risk != 'All':
        filtered_df = filtered_df[filtered_df['Risk_Category'] == selected_risk]
    
    # Leakage type filter
    leakage_types = ['All'] + sorted([str(t) for t in df['Leakage_Type'].unique() if pd.notna(t)])
    selected_leakage = st.sidebar.selectbox("Leakage Type", leakage_types)
    if selected_leakage != 'All':
        filtered_df = filtered_df[filtered_df['Leakage_Type'] == selected_leakage]
    
    # Show data summary based on filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtered Data Summary")
    st.sidebar.write(f"Records: {len(filtered_df)}")
    st.sidebar.write(f"Customers: {filtered_df['Customer_ID'].nunique()}")
    st.sidebar.write(f"Total Billed: {format_currency(filtered_df['Amount_Billed'].sum())}")
    st.sidebar.write(f"Total Received: {format_currency(filtered_df['Amount_Received'].sum())}")
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Executive Summary", "Leakage Analysis", "Risk Assessment", "Transaction Details"])
    
    with tab1:
        st.header("Executive Summary")
        
        # Key metrics in a row
        col1, col2, col3, col4 = st.columns(4)
        
        total_billed = filtered_df['Amount_Billed'].sum()
        total_received = filtered_df['Amount_Received'].sum()
        total_leakage = total_billed - total_received
        leakage_percent = (total_leakage / total_billed * 100) if total_billed > 0 else 0
        
        col1.metric("Total Billed", format_currency(total_billed))
        col2.metric("Total Received", format_currency(total_received))
        col3.metric("Total Leakage", format_currency(total_leakage))
        col4.metric("Leakage %", f"{leakage_percent:.2f}%")
        
        # Monthly trend chart
        st.subheader("Monthly Revenue Trend")
        monthly_data = filtered_df.groupby('Invoice_Month').agg({
            'Amount_Billed': 'sum',
            'Amount_Received': 'sum'
        }).reset_index()
        monthly_data['Leakage'] = monthly_data['Amount_Billed'] - monthly_data['Amount_Received']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_data['Invoice_Month'], y=monthly_data['Amount_Billed'], 
                                name='Billed', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=monthly_data['Invoice_Month'], y=monthly_data['Amount_Received'], 
                                name='Received', line=dict(color='green')))
        fig.add_trace(go.Bar(x=monthly_data['Invoice_Month'], y=monthly_data['Leakage'], 
                            name='Leakage', marker_color='red'))
        fig.update_layout(
            title='Monthly Revenue and Leakage',
            xaxis_title='Month',
            yaxis_title='Amount (₹)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Regional distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Leakage by Region")
            region_data = filtered_df.groupby('Region').agg({
                'Amount_Billed': 'sum',
                'Amount_Received': 'sum'
            }).reset_index()
            region_data['Leakage'] = region_data['Amount_Billed'] - region_data['Amount_Received']
            region_data['Leakage_Percent'] = region_data['Leakage'] / region_data['Amount_Billed'] * 100
            
            fig = px.bar(region_data, x='Region', y='Leakage',
                        text_auto='.2s',
                        color='Leakage_Percent',
                        color_continuous_scale='Reds',
                        labels={'Leakage': 'Revenue Leakage (₹)', 'Region': 'Region'})
            fig.update_layout(title='Leakage Amount by Region')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Leakage by Payment Method")
            payment_data = filtered_df.groupby('Payment_Method').agg({
                'Amount_Billed': 'sum',
                'Amount_Received': 'sum'
            }).reset_index()
            payment_data['Leakage'] = payment_data['Amount_Billed'] - payment_data['Amount_Received']
            payment_data['Leakage_Percent'] = payment_data['Leakage'] / payment_data['Amount_Billed'] * 100
            
            fig = px.pie(payment_data, values='Leakage', names='Payment_Method',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(title='Leakage Distribution by Payment Method')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Leakage Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Leakage by Type")
            # Aggregate leakage by type
            leakage_by_type = filtered_df[filtered_df['Is_Leaked'] == 1].groupby('Leakage_Type').agg({
                'Invoice_ID': 'count',
                'Amount_Billed': 'sum',
                'Amount_Received': 'sum'
            }).reset_index()
            leakage_by_type['Leakage_Amount'] = leakage_by_type['Amount_Billed'] - leakage_by_type['Amount_Received']
            leakage_by_type.rename(columns={'Invoice_ID': 'Count'}, inplace=True)
            
            # Create a horizontal bar chart
            fig = px.bar(leakage_by_type, y='Leakage_Type', x='Leakage_Amount',
                        color='Count',
                        color_continuous_scale='Viridis',
                        orientation='h',
                        labels={'Leakage_Amount': 'Leakage Amount (₹)', 
                               'Leakage_Type': 'Type of Leakage',
                               'Count': 'Number of Cases'})
            fig.update_layout(title='Revenue Leakage by Type')
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Top 10 Customers with Leakage")
            # Get top customers by leakage amount
            customer_leakage = filtered_df.groupby('Customer_ID').agg({
                'Invoice_ID': 'count',
                'Amount_Billed': 'sum',
                'Amount_Received': 'sum'
            }).reset_index()
            customer_leakage['Leakage'] = customer_leakage['Amount_Billed'] - customer_leakage['Amount_Received']
            customer_leakage['Leakage_Percent'] = (customer_leakage['Leakage'] / customer_leakage['Amount_Billed'] * 100)
            customer_leakage = customer_leakage.sort_values('Leakage', ascending=False).head(10)
            
            # Create bar chart
            fig = px.bar(customer_leakage, x='Customer_ID', y='Leakage',
                        color='Leakage_Percent',
                        color_continuous_scale='Reds',
                        text_auto='.2s',
                        labels={'Leakage': 'Amount Leaked (₹)', 
                               'Customer_ID': 'Customer', 
                               'Leakage_Percent': 'Leakage %'})
            fig.update_layout(title='Top 10 Customers by Leakage Amount')
            st.plotly_chart(fig, use_container_width=True)
        
        # Payment delay analysis
        st.subheader("Payment Delay Analysis")
        delay_df = filtered_df[filtered_df['Payment_Date'].notna()].copy()
        delay_df['Delay_Category'] = pd.cut(
            delay_df['Payment_Delay_Days'], 
            bins=[-float('inf'), 0, 15, 30, 60, float('inf')],
            labels=['On Time', '1-15 days', '16-30 days', '31-60 days', '60+ days']
        )
        
        delay_summary = delay_df.groupby('Delay_Category').agg({
            'Invoice_ID': 'count',
            'Amount_Billed': 'sum'
        }).reset_index()
        delay_summary.rename(columns={'Invoice_ID': 'Count'}, inplace=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(delay_summary, values='Count', names='Delay_Category',
                        color_discrete_sequence=px.colors.sequential.Plasma_r,
                        hole=0.3)
            fig.update_layout(title='Payment Delay Distribution (Count)')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(delay_summary, values='Amount_Billed', names='Delay_Category',
                        color_discrete_sequence=px.colors.sequential.Plasma_r,
                        hole=0.3)
            fig.update_layout(title='Payment Delay Distribution (Amount)')
            st.plotly_chart(fig, use_container_width=True)
        
        # Salesperson leakage
        st.subheader("Leakage by Salesperson")
        sp_leakage = filtered_df.groupby('Salesperson_ID').agg({
            'Invoice_ID': 'count',
            'Is_Leaked': 'sum',
            'Amount_Billed': 'sum',
            'Amount_Received': 'sum'
        }).reset_index()
        sp_leakage['Leakage'] = sp_leakage['Amount_Billed'] - sp_leakage['Amount_Received']
        sp_leakage['Leakage_Percent'] = (sp_leakage['Leakage'] / sp_leakage['Amount_Billed'] * 100)
        sp_leakage['Leaked_Invoice_Percent'] = (sp_leakage['Is_Leaked'] / sp_leakage['Invoice_ID'] * 100)
        sp_leakage = sp_leakage.sort_values('Leakage', ascending=False)
        
        fig = px.scatter(sp_leakage, x='Leaked_Invoice_Percent', y='Leakage_Percent',
                        size='Amount_Billed', color='Leakage',
                        hover_name='Salesperson_ID',
                        labels={'Leaked_Invoice_Percent': '% of Invoices with Leakage',
                               'Leakage_Percent': '% of Revenue Leaked',
                               'Amount_Billed': 'Total Billed Amount'},
                        color_continuous_scale='Reds')
        fig.update_layout(title='Salesperson Risk Analysis')
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Risk Assessment")
        
        # Risk distribution
        st.subheader("Risk Score Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(filtered_df, x='Risk_Score',
                             color='Risk_Category',
                             color_discrete_map={
                                 'Low': 'green',
                                 'Medium': 'yellow',
                                 'High': 'orange',
                                 'Critical': 'red'
                             },
                             nbins=20,
                             labels={'Risk_Score': 'Risk Score (0-100)'})
            fig.update_layout(title='Distribution of Risk Scores')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            risk_count = filtered_df['Risk_Category'].value_counts().reset_index()
            risk_count.columns = ['Risk_Category', 'Count']
            
            # Ensure all categories are present
            all_cats = pd.DataFrame({'Risk_Category': ['Low', 'Medium', 'High', 'Critical']})
            risk_count = pd.merge(all_cats, risk_count, on='Risk_Category', how='left').fillna(0)
            
            # Create a custom color sequence
            color_map = {'Low': 'green', 'Medium': 'gold', 'High': 'orange', 'Critical': 'red'}
            color_seq = [color_map[cat] for cat in risk_count['Risk_Category']]
            
            fig = px.pie(risk_count, values='Count', names='Risk_Category',
                        color='Risk_Category',
                        color_discrete_map=color_map)
            fig.update_layout(title='Distribution of Risk Categories')
            st.plotly_chart(fig, use_container_width=True)
        
        # High risk invoices
        st.subheader("Critical and High Risk Invoices")
        high_risk_df = filtered_df[filtered_df['Risk_Category'].isin(['Critical', 'High'])].sort_values('Risk_Score', ascending=False)
        if not high_risk_df.empty:
            display_cols = ['Invoice_ID', 'Customer_ID', 'Invoice_Date', 'Due_Date', 'Payment_Date',
                           'Amount_Billed', 'Amount_Received', 'Payment_Gap', 'Payment_Delay_Days',
                           'Leakage_Type', 'Risk_Score', 'Risk_Category']
            st.dataframe(high_risk_df[display_cols], use_container_width=True)
        else:
            st.info("No high-risk invoices found in the selected filters.")
        
        # Risk factors correlation
        st.subheader("Risk Factors Analysis")
        
        # Select numerical columns that might be correlated with risk
        corr_cols = ['Payment_Delay_Days', 'Amount_Billed', 'Discount', 'Payment_Gap', 
                     'Discount_Percentage', 'Risk_Score']
        
        # Calculate correlation matrix for these columns
        corr_matrix = filtered_df[corr_cols].corr()
        
        # Create a heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, cmap='coolwarm', vmax=1, vmin=-1, center=0,
                   annot=True, fmt=".2f", square=True, linewidths=.5, ax=ax)
        plt.title('Correlation Between Risk Factors')
        st.pyplot(fig)
    
    with tab4:
        st.header("Transaction Details")
        
        # Search functionality
        search_col1, search_col2 = st.columns([1, 3])
        with search_col1:
            search_type = st.selectbox("Search by", ["Invoice ID", "Customer ID"])
        
        with search_col2:
            if search_type == "Invoice ID":
                search_term = st.text_input("Enter Invoice ID", "")
                if search_term:
                    search_results = filtered_df[filtered_df['Invoice_ID'].str.contains(search_term, case=False)]
            else:  # Customer ID
                search_term = st.text_input("Enter Customer ID", "")
                if search_term:
                    search_results = filtered_df[filtered_df['Customer_ID'].str.contains(search_term, case=False)]
                    
            if search_term:
                if not search_results.empty:
                    st.write(f"Found {len(search_results)} matching records")
                    st.dataframe(search_results, use_container_width=True)
                else:
                    st.warning("No matching records found.")
        
        # Complete transaction data with pagination
        st.subheader("All Transactions")
        page_size = st.selectbox("Rows per page", [10, 20, 50, 100])
        total_pages = (len(filtered_df) - 1) // page_size + 1
        page_num = st.slider("Page", 1, total_pages, 1)
        
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, len(filtered_df))
        
        st.dataframe(filtered_df.iloc[start_idx:end_idx], use_container_width=True)
        st.write(f"Showing records {start_idx+1} to {end_idx} of {len(filtered_df)}")
        
else:
    st.error("Failed to load transaction data. Please check if the data file exists and is valid.") 