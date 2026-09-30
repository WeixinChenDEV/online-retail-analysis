# Retail Insights — Power BI portfolio case study

A reproducible retail analysis covering trading performance, products and markets,
customer segmentation, and cohort repeat-purchase activity.

**Status:** Data preparation, SQL reconciliations and native PBIR schema checks passed.
Desktop screenshots and the exact scope of runtime checks are recorded in
[validation status](docs/validation.json). This is an independent
historical case study; no affiliation with the retailer or UCI is implied.

![Power BI Desktop — trading overview](assets/screenshots/overview.jpg)

## Business questions

1. How do recorded sales, credits and order values vary over time?
2. Which products and countries contribute to gross sales?
3. Which identifiable customers repeatedly purchase and merit further investigation?
4. How does repeat-purchase activity differ across first-observed-purchase cohorts?

## Results at a glance

| Metric | Observed result |
| --- | ---: |
| Original source rows | 541,909 |
| Gross positive sales | £10,666,684.54 |
| Recorded credits | £896,812.49 |
| Net recorded sales | £9,769,872.05 |
| Positive-sale invoices | 19,960 |
| Identifiable purchasing customers | 4,338 |
| Whole-window repeat customer share | 65.6% |
| Gross sales linked to identifiable customers | 83.5% |

These figures use the policy in [methodology](docs/methodology.md). They are not
profit, a matched return rate, or current-market estimates.

## Power BI deliverable

Open **`powerbi/RetailInsights.pbip`** in standard Power BI Desktop. The report
contains four pages, 28 native visuals, seven tables and 18 DAX measures.
The local working copy also includes `RetailInsights.pbix` with imported data.
That binary is excluded from Git because its refresh metadata contains the local
machine's data path; the public repository contains reproducible PBIP source and CSVs.

| Page | Purpose |
| --- | --- |
| Trading overview | Month/country slicers, financial KPIs, monthly trends and controls |
| Products & markets | Product/country comparisons, merchandise/charges selection, detail |
| Customer snapshot | Fixed RFM segments, customer counts, sales contributions, customer detail |
| Cohort repeat activity | Cohort slicer, month-offset matrix, explicit observed-cell denominators |

The model uses invoice-line and invoice-level facts with shared single-direction
dimensions. The cohort aggregate is separate so its denominators cannot be
silently changed by unrelated slicers. Monetary values use fixed-decimal types.

### Open with the included prepared data

```bash
python scripts/configure_local.py
```

Then open the PBIP and select **Refresh**. `DataFolder` must point to the clone's
`data/processed` folder. The project has no Desktop cache; visuals will populate
only after refresh. Optionally apply `assets/retail-theme.json` through
View → Themes → Browse for themes. The included PBIR report already applies the theme.

Do not commit the personal local path inserted by `configure_local.py`. Regenerate
the data parameter with `python scripts/configure_local.py --portable` to restore the portable placeholder.
See [Chinese opening and validation guide](docs/打开项目.md).

### Reproduce from the original source

Requires Python 3.10+ and the dependencies in `requirements.txt`.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/download_data.py
python scripts/analyze.py
python scripts/build_powerbi.py
python scripts/test_data.py
python scripts/validate_report.py
python scripts/create_previews.py
python scripts/configure_local.py
```

The validator retrieves public Microsoft schemas and requires network access.
PBIR `definition/version.json` uses report format `2.0.0`; setting it to `1.0.0`
can make Desktop load an empty report even when JSON schema validation passes.
Desktop can rewrite schemas to newer versions on save; `build_powerbi.py --report-only`
restores the reproducible report definition without replacing the saved semantic model.
The download script retrieves the original workbook from UCI. Prepared CSVs are
included for opening the report without rerunning preparation; raw data, SQLite
working databases, package folders and Desktop caches are ignored by Git.

## Analytical decisions

- Retain sales without customer IDs in financial totals, but exclude them from
  identifiable-customer RFM and cohort denominators.
- Preserve credit-only customer IDs for referential integrity without counting them as purchasers.
- Keep exact repeated source rows: missing transaction-line identifiers prevent confident deduplication.
- Separate positive-price purchases, negative-quantity credits and excluded entries.
- Omit incomplete December 2011 cohort cells. Blank means unobserved; observed zero stays zero.
- Use tied percentile ranks and documented RFM rules rather than claiming a trained churn model.
- Label customer scores as a fixed snapshot as of 10 December 2011.

![Power BI Desktop — customer snapshot](assets/screenshots/customers.jpg)
![Power BI Desktop — cohort repeat activity](assets/screenshots/cohorts.jpg)

## Inspect the work

- [Analysis and action hypotheses](docs/findings.md)
- [Data contract and limitations](docs/methodology.md)
- [DAX measures](docs/measures.dax)
- [SQL analysis and controls](sql/analysis.sql)
- [Machine-readable analysis summary](docs/analysis_summary.json)
- [Validation status](docs/validation.json)
- [Filter and cohort data tests](docs/data_tests.json)
- [Interview and learning notes (中文)](docs/学习与面试.md)

## Data attribution and license

Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository.
[DOI 10.24432/C5BW33](https://doi.org/10.24432/C5BW33), licensed under CC BY 4.0.
The original observations span 1 December 2010–9 December 2011.
See [data attribution](DATA_LICENSE.md). Project code and authored report definitions
are MIT-licensed; source and derived data retain their attribution requirements.

## Technical references

- [Microsoft: Power BI Desktop projects](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [Microsoft: PBIR report format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)
- [Microsoft: semantic model format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset)
