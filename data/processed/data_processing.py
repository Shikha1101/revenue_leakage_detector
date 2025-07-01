#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Preprocessing Script for Revenue Leakage Detection Project
This script cleans the raw transaction data and computes additional features.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def main():
    print("Starting data preprocessing...")
    
    # Input and output paths
    input_file = '../raw/transactions.csv'
    output_file = 'cleaned_transactions.csv'
    
    # Read the raw data
    df = pd.read_csv(input_file)
    
    print(f"Loaded {len(df)} records from {input_file}")
    
    # Convert date columns to datetime
    date_columns = ['Invoice_Date', 'Due_Date', 'Payment_Date']
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Calculate additional features
    df['Payment_Delay_Days'] = (df['Payment_Date'] - df['Due_Date']).dt.days
    df['Expected_Payment'] = df['Amount_Billed'] - df['Discount']
    df['Payment_Gap'] = df['Expected_Payment'] - df['Amount_Received']
    
    # Fill missing values in Amount_Received for missing payments
    df.loc[df['Payment_Date'].isna(), 'Amount_Received'] = 0
    
    # Calculate payment status
    df['Payment_Status'] = 'Paid in Full'
    df.loc[df['Payment_Gap'] > 0, 'Payment_Status'] = 'Underpaid'
    df.loc[df['Payment_Date'].isna(), 'Payment_Status'] = 'Missing'
    df.loc[df['Payment_Delay_Days'] > 0, 'Payment_Status'] = 'Late'
    
    # Calculate risk score (a simple weighted score based on various factors)
    df['Discount_Percentage'] = (df['Discount'] / df['Amount_Billed'] * 100).fillna(0)
    
    # Risk factors with weights
    df['Risk_Score'] = 0
    # Payment delay risk (0-30)
    df.loc[df['Payment_Delay_Days'] > 0, 'Risk_Score'] += np.minimum(df['Payment_Delay_Days'] / 3, 30)
    # Missing payment risk (50)
    df.loc[df['Payment_Date'].isna(), 'Risk_Score'] += 50
    # Underpayment risk (0-40)
    payment_gap_percentage = df['Payment_Gap'] / df['Expected_Payment'] * 100
    df.loc[df['Payment_Gap'] > 0, 'Risk_Score'] += np.minimum(payment_gap_percentage, 40)
    # High discount risk (0-20)
    df.loc[df['Discount_Percentage'] > 15, 'Risk_Score'] += np.minimum((df['Discount_Percentage'] - 15), 20)
    # Duplicate invoice risk (25)
    df.loc[df['Is_Duplicate'] == 1, 'Risk_Score'] += 25
    
    # Normalize risk score to 0-100
    max_risk = df['Risk_Score'].max()
    if max_risk > 0:
        df['Risk_Score'] = (df['Risk_Score'] / max_risk * 100).round(1)
    
    # Risk category
    df['Risk_Category'] = pd.cut(df['Risk_Score'], 
                               bins=[0, 25, 50, 75, 100],
                               labels=['Low', 'Medium', 'High', 'Critical'])
    
    # Monthly aggregation for time series analysis
    df['Invoice_Month'] = df['Invoice_Date'].dt.to_period('M').astype(str)
    
    # Save the processed data
    df.to_csv(output_file, index=False)
    
    print(f"Data processing complete. Saved to {output_file}")
    print(f"Records with leakage: {df['Is_Leaked'].sum()}")
    print(f"Total leakage amount: {df['Payment_Gap'].sum():.2f}")
    
    # Generate a summary of leakage types
    leakage_summary = df[df['Is_Leaked'] == 1]['Leakage_Type'].value_counts()
    print("\nLeakage Type Summary:")
    for leakage_type, count in leakage_summary.items():
        print(f"  {leakage_type}: {count}")
    
if __name__ == "__main__":
    main() 