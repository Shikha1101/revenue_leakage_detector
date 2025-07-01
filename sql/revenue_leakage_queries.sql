-- SQL Queries for Revenue Leakage Analysis
-- For use with MySQL/PostgreSQL

-- Create Table Script (if needed)
CREATE TABLE IF NOT EXISTS transactions (
    Invoice_ID VARCHAR(10) PRIMARY KEY,
    Customer_ID VARCHAR(10),
    Invoice_Date DATE,
    Due_Date DATE,
    Payment_Date DATE,
    Amount_Billed DECIMAL(12,2),
    Discount DECIMAL(12,2),
    Amount_Received DECIMAL(12,2),
    Payment_Method VARCHAR(20),
    Salesperson_ID VARCHAR(10),
    Region VARCHAR(10),
    Is_Duplicate BOOLEAN,
    Is_Leaked BOOLEAN,
    Leakage_Type VARCHAR(20)
);

-- Total Revenue Leakage Summary
SELECT 
    SUM(Amount_Billed) AS Total_Billed,
    SUM(Amount_Received) AS Total_Received,
    SUM(Amount_Billed - Amount_Received) AS Total_Leakage,
    (SUM(Amount_Billed - Amount_Received) / SUM(Amount_Billed)) * 100 AS Leakage_Percentage
FROM transactions;

-- Revenue Leakage by Type
SELECT 
    Leakage_Type,
    COUNT(*) AS Count,
    SUM(Amount_Billed - Amount_Received) AS Leakage_Amount,
    (SUM(Amount_Billed - Amount_Received) / 
     (SELECT SUM(Amount_Billed - Amount_Received) FROM transactions WHERE Is_Leaked = 1)) * 100 AS Percentage
FROM transactions
WHERE Is_Leaked = 1
GROUP BY Leakage_Type
ORDER BY Leakage_Amount DESC;

-- Total Leakage Per Invoice
SELECT 
    Invoice_ID,
    Customer_ID,
    Amount_Billed,
    Amount_Received,
    (Amount_Billed - Amount_Received) AS Leakage_Amount,
    CASE
        WHEN Amount_Received < Amount_Billed THEN 'Leaked'
        ELSE 'Paid'
    END AS Payment_Status
FROM transactions
ORDER BY Leakage_Amount DESC;

-- Payment Delay Analysis
SELECT
    Invoice_ID,
    Customer_ID,
    Due_Date,
    Payment_Date,
    DATEDIFF(Payment_Date, Due_Date) AS Delay_Days,
    CASE 
        WHEN Payment_Date IS NULL THEN 'Missing'
        WHEN DATEDIFF(Payment_Date, Due_Date) > 0 THEN 'Delayed'
        ELSE 'On Time'
    END AS Payment_Timeliness
FROM transactions
ORDER BY DATEDIFF(Payment_Date, Due_Date) DESC;

-- Top Customers by Leakage
SELECT 
    Customer_ID,
    COUNT(*) AS Total_Invoices,
    COUNT(CASE WHEN Is_Leaked = 1 THEN 1 END) AS Leaked_Invoices,
    SUM(Amount_Billed) AS Total_Billed,
    SUM(Amount_Received) AS Total_Received,
    SUM(Amount_Billed - Amount_Received) AS Total_Leakage,
    (SUM(Amount_Billed - Amount_Received) / SUM(Amount_Billed)) * 100 AS Leakage_Percentage
FROM transactions
GROUP BY Customer_ID
ORDER BY Total_Leakage DESC
LIMIT 10;

-- Leakage by Salesperson
SELECT 
    Salesperson_ID,
    COUNT(*) AS Total_Invoices,
    COUNT(CASE WHEN Is_Leaked = 1 THEN 1 END) AS Leaked_Invoices,
    SUM(Amount_Billed) AS Total_Billed,
    SUM(Amount_Received) AS Total_Received,
    SUM(Amount_Billed - Amount_Received) AS Total_Leakage,
    (SUM(Amount_Billed - Amount_Received) / SUM(Amount_Billed)) * 100 AS Leakage_Percentage
FROM transactions
GROUP BY Salesperson_ID
ORDER BY Leakage_Percentage DESC;

-- Leakage by Region
SELECT 
    Region,
    COUNT(*) AS Total_Invoices,
    COUNT(CASE WHEN Is_Leaked = 1 THEN 1 END) AS Leaked_Invoices,
    SUM(Amount_Billed) AS Total_Billed,
    SUM(Amount_Received) AS Total_Received,
    SUM(Amount_Billed - Amount_Received) AS Total_Leakage,
    (SUM(Amount_Billed - Amount_Received) / SUM(Amount_Billed)) * 100 AS Leakage_Percentage
FROM transactions
GROUP BY Region
ORDER BY Leakage_Percentage DESC;

-- Leakage by Payment Method
SELECT 
    Payment_Method,
    COUNT(*) AS Total_Invoices,
    COUNT(CASE WHEN Is_Leaked = 1 THEN 1 END) AS Leaked_Invoices,
    SUM(Amount_Billed) AS Total_Billed,
    SUM(Amount_Received) AS Total_Received,
    SUM(Amount_Billed - Amount_Received) AS Total_Leakage,
    (SUM(Amount_Billed - Amount_Received) / SUM(Amount_Billed)) * 100 AS Leakage_Percentage
FROM transactions
WHERE Payment_Method IS NOT NULL
GROUP BY Payment_Method
ORDER BY Leakage_Percentage DESC;

-- Monthly Trend Analysis
SELECT 
    DATE_FORMAT(Invoice_Date, '%Y-%m') AS Month,
    COUNT(*) AS Total_Invoices,
    SUM(Amount_Billed) AS Total_Billed,
    SUM(Amount_Received) AS Total_Received,
    SUM(Amount_Billed - Amount_Received) AS Total_Leakage,
    (SUM(Amount_Billed - Amount_Received) / SUM(Amount_Billed)) * 100 AS Leakage_Percentage
FROM transactions
GROUP BY DATE_FORMAT(Invoice_Date, '%Y-%m')
ORDER BY Month;

-- Duplicate Invoice Detection
SELECT 
    Customer_ID,
    Invoice_Date,
    Amount_Billed,
    COUNT(*) AS Duplicate_Count
FROM transactions
GROUP BY Customer_ID, Invoice_Date, Amount_Billed
HAVING COUNT(*) > 1
ORDER BY Duplicate_Count DESC;

-- Over-Discount Analysis
SELECT 
    Invoice_ID,
    Customer_ID,
    Amount_Billed,
    Discount,
    (Discount / Amount_Billed) * 100 AS Discount_Percentage
FROM transactions
WHERE (Discount / Amount_Billed) * 100 > 15  -- Threshold for suspicious discounts
ORDER BY Discount_Percentage DESC; 