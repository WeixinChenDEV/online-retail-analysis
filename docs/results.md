# Results

## Sales and markets

Gross sales are £10.67m and recorded credits are £896.81k. Net recorded sales
are £9.77m. These are transaction amounts, not profit: the dataset has no cost data.
The UK contributes 84.6% of gross sales, so the country chart is dominated by it.
Monthly trends within each country give a more useful comparison than totals alone.

## Repeat purchases

2,845 of 4,338 known purchasing customers placed more than one order (65.6%).
This figure uses the whole observation window. Customers who first appear near
the end have less time to place another order, which is why the report also has
a cohort page. First observed purchase is not necessarily a customer's first-ever purchase.

## RFM groups

The Champions group has 911 customers and £5.69m in gross sales, around 63.8%
of known-customer sales. This shows a concentration in high-value repeat buyers.
The At Risk group has 765 customers. That label comes from the RFM rules; it
does not establish that these customers have actually churned.

![Customer groups](../assets/screenshots/customers.jpg)

## Data gaps

135,080 original rows have no customer ID (24.9%). They still count towards
sales, but cannot be used to identify repeat customers. December 2011 includes
only nine days, so its lower sales should not be interpreted as a sudden decline.

## What could be added

With more data, useful next steps would be to check why IDs are missing, match
credits to original invoices, and look at buying intervals within customer groups.
Campaign and cost data would be needed to evaluate a marketing action or profit.

![Cohort activity](../assets/screenshots/cohorts.jpg)
