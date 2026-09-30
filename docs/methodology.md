# Data contract and analytical boundaries

## Source and observation window

UCI Online Retail covers 1 December 2010–9 December 2011. Values are in GBP.
The business includes wholesale customers; average order values must not be
interpreted as typical consumer shopping baskets. December 2011 is incomplete.
The observed customer's first purchase is not necessarily their lifetime first purchase.

## Transaction policy

- `Sale`: positive quantity, positive unit price, invoice not starting with C.
- `Credit`: negative quantity and positive unit price, regardless of invoice prefix.
- `Excluded`: nonpositive price, zero quantity, invalid date, or inconsistent positive cancellation.
- `LineAmount`: quantity × price, rounded per source line to two decimals.
- `Gross Sales`: positive sale amounts, including charges unless the product-type filter is applied.
- `Recorded Credits`: absolute sum of qualifying negative amounts. These are posted credits,
  not evidence that a particular sale was refunded, physically returned or cancelled in the same period.
- `Net Recorded Sales`: gross sales minus recorded credits. Not profit or recognized accounting revenue.
- `Credit Value Share`: credits / gross sales; not a matched return rate.
- Exactly repeated source rows are retained (5,268 rows). Without line IDs,
  deleting them could delete legitimate repeated lines. A removal sensitivity is reported separately.
- Unknown CustomerID maps to key `0`. Sales stay in financial totals; unknown customers are excluded from RFM,
  cohort activity and identifiable purchaser counts. Credit-only customer IDs exist in the dimension
  to preserve relationships but are excluded from the purchasing-customer denominator.
- Product description uses the most frequent nonempty description for each stock code.
  `Merchandise` is a code-pattern heuristic (five digits followed by optional letters), not a curated taxonomy.

## Model

`DimDate`, `DimCountry`, `DimCustomer` filter both `FactTransactions` (invoice-line grain)
and `FactOrders` (one positive-sale invoice). `DimProduct` filters only transactions.
All relationships are many-to-one and single-direction. Product selection therefore does
not redefine order-based KPIs; order KPIs are intentionally confined to the overview page.
`FactCohort` is a separate, preaggregated cohort table with its own cohort slicer;
it does not respond to transaction-country, transaction-date or RFM-segment selection.
This prevents misleading denominators and accidental many-to-many filtering.

## Customer snapshot and RFM

Snapshot as of 10 December 2011. Recency is days since the last observed positive sale;
frequency is distinct positive-sale invoices; monetary value is gross positive sales
for identifiable customers (credits excluded from scoring).
Scores use average percentile ranks and ceiling(percentile × 5). Ties stay together,
so quintile populations are not forced to be equal. Lower recency gets a higher R score.
Rules are evaluated in this order:

1. Champions: R ≥ 4, F ≥ 4, M ≥ 4.
2. At Risk: R ≤ 2, F ≥ 3.
3. Loyal: F ≥ 4.
4. New / Recent: R ≥ 4, F ≤ 2.
5. Developing: everyone else with a positive purchase.

These are transparent business heuristics, not validated churn predictions.
The snapshot does not recompute with report date filters; its page deliberately has no date or country slicer.
Snapshot Repeat Share is the fraction of identifiable customers with more than one
sale invoice in the whole observed window. It is not a 30-day retention measure.

## Cohort repeat activity

Group by the month of first observed positive purchase. Month offset 0 is the cohort month;
subsequent values count customers buying in that calendar month / original cohort size.
Customers need not buy in every intervening month to count. Fully observed zero-activity
cells are retained as zero. Unobserved cells and December 2011 are omitted, not filled with zero.
December 2011's new customers therefore have no cohort cells. No claim of causal
marketing lift, paid conversion, profit or customer lifetime value is made.

## Validation status

The preparation reconciles Python against independent SQL financial and order totals,
checks unique dimension keys and complete relationships, and checks cohort bounds.
Report JSON is validated against Microsoft's public PBIR contracts; visual field references
are checked against the model. Power BI Desktop refresh, DAX execution, rendering and
interaction checks remain pending because Desktop is unavailable in the authoring environment.
Offline preview PNGs are computed from the data, not screenshots from Power BI.
