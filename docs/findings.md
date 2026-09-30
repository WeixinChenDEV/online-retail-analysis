# Findings and proposed actions

These are descriptive findings from a historical retailer, not proof of causality
or recommendations for today's market. The raw observation window ends 9 December 2011.

## 1. Customer identification is a material analytical gap

135,080 of 541,909 original rows (24.9%) have no CustomerID. Nevertheless,
83.5% of gross positive sales are attributable to identifiable customers.
Do not treat every anonymous invoice as a separate customer or delete anonymous
sales from financial totals. A useful next step is to investigate which channels,
order types or ingestion stages explain the identification gap; these fields are
not available in this source, so the root cause cannot be established here.

## 2. Repeat purchasing is common in the identifiable population

2,845 of 4,338 identifiable purchasers bought on more than one positive-sale
invoice during the observed window (65.6%). This is a whole-window descriptive
share; a customer entering late has less time to repeat. Cohort repeat activity
provides the more comparable view, while remaining subject to left truncation
of customer history and the incomplete final month.

## 3. A small high-value segment merits attention

The rule-based Champions segment contains 911 customers (21.0% of identifiable
purchasers) and £5.69m of positive sales (about 63.8% of known-customer sales).
This motivates investigating service expectations and concentration exposure.
It does not prove that a loyalty campaign will generate incremental sales.
The At Risk segment contains 765 customers under the fixed recency/frequency
rules; review order cycles and seasonality before interpreting absence as churn.

## 4. The UK dominates the observed sales mix

The UK contributes 84.6% of gross positive sales. Country comparisons should
therefore be shown both as absolute contributions and within-country trends.
There is insufficient information about acquisition costs, margins or market
size to recommend expansion into a particular country.

## 5. Credits and incomplete months require explicit handling

Posted credits total £896,812.49. Their value is approximately 8.4% of gross
positive sales, but this is not a matched return rate. Very large sales and
credit entries need invoice-level review before interpreting them as ordinary
shopping baskets. December 2011 ends on the 9th, so a lower monthly total cannot
be used to claim that the business suddenly declined.

## Decision brief

Prioritise (1) customer-identity coverage investigation, (2) service and concentration
review for major repeat buyers, and (3) invoice-level credit/anomaly review.
To evaluate any intervention, obtain campaign exposure, channel, cost and experiment
data and define outcomes before execution. This project supplies evidence for
investigation, not invented business uplift.
