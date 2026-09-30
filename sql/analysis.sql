-- SQLite-compatible controls. Currency is GBP, using line-level amounts rounded to cents.
-- This is recorded sales less posted credits, not profit and not matched returns.
SELECT Kind, COUNT(*) AS lines, ROUND(SUM(LineAmount), 2) AS amount_gbp
FROM FactTransactions GROUP BY Kind;

-- Invoice grain has been checked: one customer and country per sale invoice.
SELECT COUNT(*) AS sales_orders, ROUND(AVG(OrderSales), 2) AS aov_gbp
FROM FactOrders;

-- Complete months only: avoid comparing the first nine days of December with full months.
SELECT YearMonth,
       ROUND(SUM(CASE WHEN Kind='Sale' THEN LineAmount ELSE 0 END), 2) AS gross_sales,
       ROUND(-SUM(CASE WHEN Kind='Credit' THEN LineAmount ELSE 0 END), 2) AS recorded_credits,
       ROUND(SUM(LineAmount), 2) AS net_recorded_sales
FROM FactTransactions
WHERE YearMonth <= '2011-11'
GROUP BY YearMonth ORDER BY YearMonth;

-- Repeat-customer share among identifiable purchasing customers in the observed window.
WITH customer_orders AS (
    SELECT CustomerKey, COUNT(*) AS orders
    FROM FactOrders WHERE CustomerKey <> '0' GROUP BY CustomerKey
)
SELECT COUNT(*) AS customers,
       SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       1.0 * SUM(CASE WHEN orders > 1 THEN 1 ELSE 0 END) / COUNT(*) AS repeat_share
FROM customer_orders;

SELECT CountryKey, ROUND(SUM(LineAmount), 2) AS gross_sales
FROM FactTransactions WHERE Kind='Sale'
GROUP BY CountryKey ORDER BY gross_sales DESC;

-- Product figures include only code-pattern merchandise when explicitly requested.
SELECT p.ProductKey, p.Description, ROUND(SUM(t.LineAmount), 2) AS gross_sales
FROM FactTransactions t JOIN DimProduct p USING (ProductKey)
WHERE t.Kind='Sale' AND p.ProductType='Merchandise'
GROUP BY p.ProductKey, p.Description ORDER BY gross_sales DESC LIMIT 15;

SELECT Segment, COUNT(*) AS customers, ROUND(SUM(GrossSales), 2) AS gross_sales
FROM DimCustomer WHERE Orders > 0 GROUP BY Segment;

-- Cohort records contain only fully observed month cells, including zero-activity cells.
SELECT Cohort, Offset, CohortSize, ActiveCustomers,
       1.0 * ActiveCustomers / CohortSize AS repeat_activity
FROM FactCohort ORDER BY Cohort, Offset;
