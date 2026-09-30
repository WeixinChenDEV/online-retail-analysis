# Online Retail Analysis

A data analysis project using Python, SQL and Power BI. It uses the UCI Online
Retail dataset to look at sales, customer segments and repeat purchases.
The data covers December 2010 to December 2011 and contains 541,909 rows.

![Sales overview](assets/screenshots/overview.jpg)

## What the report shows

- Sales, credits and order value by month and country
- Product sales and the difference between merchandise and other charges
- Customer groups based on recency, frequency and monetary value (RFM)
- Monthly purchase activity for customers grouped by their first purchase month

There are four report pages. The customer groups use a fixed snapshot at the
end of the dataset; they do not change with the sales page's date filter.

## A few results

| Metric | Result |
| --- | ---: |
| Gross sales | £10,666,684.54 |
| Recorded credits | £896,812.49 |
| Net recorded sales | £9,769,872.05 |
| Sales orders | 19,960 |
| Customers with a recorded ID and at least one purchase | 4,338 |
| Customers who placed more than one order | 65.6% |

The UK accounts for 84.6% of gross sales. The Champions RFM group has 911
customers and accounts for about 63.8% of sales linked to known customers.
More detail is in [results](docs/results.md).

## Run it

Python 3.10+ is needed for the scripts, and Power BI Desktop is needed for the report.

```bash
python -m pip install -r requirements.txt
python scripts/download_data.py
python scripts/prepare_data.py
python scripts/check_data.py
python scripts/setup_paths.py
```

Open `powerbi/OnlineRetail.pbip` in Power BI Desktop, apply pending query changes
if prompted, then refresh. Prepared CSVs are included, so the download and
preparation steps can be skipped when just opening the report.
See [setup notes (中文)](docs/setup.md) if the first refresh does not work.

The local working folder also has `powerbi/OnlineRetail.pbix`, with data already
loaded. It is not committed because its refresh settings contain a local file path.
Before committing changes, run `python scripts/setup_paths.py --portable` to
restore the source project's placeholder path.

## Files

```text
scripts/       download, clean data, check totals, set local paths
data/          source workbook (not committed) and prepared CSVs
sql/           queries used to check and explore the data
powerbi/       report pages, Power Query and DAX model
tools/         scripts for rebuilding and checking the report files
docs/          analysis notes, results and check records
assets/        report screenshots and theme
```

To rebuild the Power BI source files, run `python tools/build_report.py` before
setting the local paths. `python tools/check_report.py` checks the report JSON
against Microsoft's public schemas. It needs internet access on its first run.
The report has been opened in Desktop; totals and two slicer examples were
checked against SQL. [Check records](docs/checks.json) describe what was tested.

## Things to keep in mind

- Missing customer IDs are kept in sales totals, but excluded from customer analysis.
- Credits are recorded separately. They cannot all be matched to original purchases.
- Exact repeated rows are kept because the source has no unique transaction-line ID.
- December 2011 ends on the 9th. It is excluded from the complete-month cohort comparison.
- The dataset includes wholesale orders. Average order value is not necessarily a typical shopper's basket.

The cleaning rules and RFM definitions are in [analysis notes](docs/notes.md).
AI tools assisted with Python code and report-file generation; the check records
document the verification carried out on the result.

## Data source

Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository.
[Dataset and DOI](https://doi.org/10.24432/C5BW33), CC BY 4.0.
See [data attribution](DATA_LICENSE.md). Project code is MIT licensed.
