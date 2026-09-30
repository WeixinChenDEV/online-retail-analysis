"""Reproducible UCI Online Retail preparation. Does not modify the source XLSX."""
from pathlib import Path
import hashlib, json, sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'processed'
OUT.mkdir(parents=True, exist_ok=True)
source = ROOT / 'data/raw/Online Retail.xlsx'
cache = ROOT / '.schema-cache/source.pkl'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
hashfile = ROOT / '.schema-cache/source.sha256'
if cache.exists() and hashfile.exists() and hashfile.read_text() == source_hash:
    raw = pd.read_pickle(cache)
else:
    raw = pd.read_excel(source, dtype={'InvoiceNo': str, 'StockCode': str})
    cache.parent.mkdir(exist_ok=True)
    raw.to_pickle(cache)
    hashfile.write_text(source_hash)
df = raw.copy()
df['InvoiceNo'] = df.InvoiceNo.str.strip().str.upper()
df['StockCode'] = df.StockCode.str.strip().str.upper()
df['CustomerKey'] = df.CustomerID.fillna(0).astype('int64').astype(str)
df['Country'] = df.Country.fillna('Unknown').str.strip()
df['Date'] = pd.to_datetime(df.InvoiceDate).dt.normalize()
df['LineAmount'] = (df.Quantity * df.UnitPrice).round(2)
cancel = df.InvoiceNo.str.startswith('C')
eligible = df.UnitPrice.gt(0) & df.Quantity.ne(0) & df.Date.notna()
sales = eligible & df.Quantity.gt(0) & ~cancel
credits = eligible & df.Quantity.lt(0)
df['Kind'] = np.select([sales, credits], ['Sale', 'Credit'], default='Excluded')
fact = df[df.Kind.ne('Excluded')].copy()
fact['LineID'] = fact.index + 1
fact['YearMonth'] = fact.Date.dt.strftime('%Y-%m')
fact['ProductKey'] = fact.StockCode
fact['CountryKey'] = fact.Country
fact['KnownCustomer'] = fact.CustomerKey.ne('0')
fact = fact[['LineID', 'InvoiceNo', 'ProductKey', 'CustomerKey', 'CountryKey',
             'Date', 'Quantity', 'UnitPrice', 'LineAmount', 'Kind', 'KnownCustomer', 'YearMonth']]
sale = fact[fact.Kind.eq('Sale')].copy()
orders = sale.groupby(['InvoiceNo', 'CustomerKey', 'CountryKey'], as_index=False).agg(
    Date=('Date', 'min'), OrderSales=('LineAmount', 'sum'), Units=('Quantity', 'sum'))
orders['OrderKey'] = orders.InvoiceNo + '|' + orders.CustomerKey + '|' + orders.CountryKey
assert not orders.InvoiceNo.duplicated().any(), 'Invoice has inconsistent customer/country; review before counting orders'
known = orders[orders.CustomerKey.ne('0')].copy()
asof = fact.Date.max() + pd.Timedelta(days=1)
customers = known.groupby('CustomerKey', as_index=False).agg(
    FirstObservedPurchase=('Date', 'min'), LastObservedPurchase=('Date', 'max'),
    Orders=('InvoiceNo', 'nunique'), GrossSales=('OrderSales', 'sum'))
customers['RecencyDays'] = (asof - customers.LastObservedPurchase).dt.days
for metric, label, asc in [('RecencyDays', 'RScore', False), ('Orders', 'FScore', True), ('GrossSales', 'MScore', True)]:
    customers[label] = np.ceil(customers[metric].rank(method='average', pct=True, ascending=asc) * 5).clip(1, 5).astype(int)
r, f, m = customers.RScore, customers.FScore, customers.MScore
customers['Segment'] = np.select([
    (r >= 4) & (f >= 4) & (m >= 4), (r <= 2) & (f >= 3), f >= 4,
    (r >= 4) & (f <= 2)], ['Champions', 'At Risk', 'Loyal', 'New / Recent'], default='Developing')
customers['Cohort'] = customers.FirstObservedPurchase.dt.strftime('%Y-%m')
customers['AsOfDate'] = asof
unknown = {c: None for c in customers.columns}
unknown.update(CustomerKey='0', Segment='Unknown customer')
credit_only = sorted(set(fact.CustomerKey) - set(customers.CustomerKey) - {'0'})
credit_rows = [{**unknown, 'CustomerKey': k, 'Segment': 'Credit only', 'Orders': 0, 'GrossSales': 0} for k in credit_only]
dimcustomers = pd.concat([customers, pd.DataFrame([unknown] + credit_rows)], ignore_index=True)
for col in ['FirstObservedPurchase', 'LastObservedPurchase', 'AsOfDate']:
    dimcustomers[col] = pd.to_datetime(dimcustomers[col])
for col in ['Orders', 'RecencyDays', 'RScore', 'FScore', 'MScore']:
    dimcustomers[col] = dimcustomers[col].astype('Int64')
# Product descriptions can change. Use the most frequent nonempty source description.
descriptions = df.dropna(subset=['Description']).copy()
descriptions['Description'] = descriptions.Description.str.strip()
freq = descriptions.groupby(['StockCode', 'Description']).size().reset_index(name='n')
names = freq.sort_values(['StockCode', 'n', 'Description'], ascending=[True, False, True]).drop_duplicates('StockCode')
products = pd.DataFrame({'ProductKey': sorted(fact.ProductKey.unique())}).merge(
    names[['StockCode', 'Description']], how='left', left_on='ProductKey', right_on='StockCode').drop(columns='StockCode')
products.Description = products.Description.fillna(products.ProductKey)
products['ProductLabel'] = products.ProductKey + ' | ' + products.Description
products['ProductType'] = np.where(products.ProductKey.str.match(r'^\d{5}[A-Z]*$'), 'Merchandise', 'Other / charges')
countries = pd.DataFrame({'CountryKey': sorted(fact.CountryKey.unique())})
dates = pd.DataFrame({'Date': pd.date_range(fact.Date.min().replace(month=1, day=1), fact.Date.max().replace(month=12, day=31))})
dates['Year'] = dates.Date.dt.year
dates['Month'] = dates.Date.dt.month
dates['YearMonth'] = dates.Date.dt.strftime('%Y-%m')
dates['YearMonthSort'] = dates.Year * 100 + dates.Month
dates['MonthName'] = dates.Date.dt.strftime('%b')
# Cohort activity: known customers, observed purchases, right-censored end-month cells omitted.
activity = known.merge(customers[['CustomerKey', 'Cohort']], on='CustomerKey')
activity['ActivityMonth'] = activity.Date.dt.to_period('M')
activity['Offset'] = activity.ActivityMonth.astype('int64') - pd.PeriodIndex(activity.Cohort, freq='M').astype('int64')
counts = activity.groupby(['Cohort', 'Offset']).CustomerKey.nunique().to_dict()
sizes = customers.groupby('Cohort').size().to_dict()
last_full = fact.Date.max().to_period('M') - 1  # Dec 2011 is incomplete (ends on the 9th).
cohortrows = []
for cohort, size in sorted(sizes.items()):
    start = pd.Period(cohort, freq='M')
    for offset in range(max(0, last_full.ordinal - start.ordinal + 1)):
        cohortrows.append({'Cohort': cohort, 'Offset': offset, 'CohortSize': size,
                           'ActiveCustomers': counts.get((cohort, offset), 0),
                           'ActivityMonth': str(start + offset)})
cohorts = pd.DataFrame(cohortrows)
tables = {'FactTransactions': fact, 'FactOrders': orders, 'DimCustomer': dimcustomers,
          'DimProduct': products, 'DimCountry': countries, 'DimDate': dates, 'FactCohort': cohorts}
for name, table in tables.items():
    table.to_csv(OUT / f'{name}.csv', index=False, date_format='%Y-%m-%d', encoding='utf-8')
with sqlite3.connect(OUT / 'retail.sqlite') as conn:
    for name, table in tables.items():
        table.to_sql(name, conn, if_exists='replace', index=False)
gross = float(sale.LineAmount.sum())
credit = float(-fact.loc[fact.Kind.eq('Credit'), 'LineAmount'].sum())
monthly = fact.groupby(['YearMonth', 'Kind']).LineAmount.sum().unstack(fill_value=0)
monthly['Net'] = monthly.sum(axis=1)
monthly.to_csv(OUT / 'monthly_reconciliation.csv')
country = sale.groupby('CountryKey').LineAmount.sum().sort_values(ascending=False)
summary = {
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'source_rows': len(raw),
    'exact_duplicate_rows_retained': int(raw.duplicated().sum()),
    'excluded_nonpositive_price_rows': int(df.UnitPrice.le(0).sum()),
    'excluded_positive_cancellation_rows': int((eligible & cancel & df.Quantity.gt(0)).sum()),
    'excluded_rows': int(df.Kind.eq('Excluded').sum()), 'missing_customer_source_rows': int(raw.CustomerID.isna().sum()),
    'sale_rows': len(sale), 'credit_rows': int(fact.Kind.eq('Credit').sum()),
    'gross_sales_gbp': round(gross, 2), 'recorded_credits_gbp': round(credit, 2),
    'net_recorded_sales_gbp': round(gross-credit, 2), 'sales_orders': len(orders),
    'known_purchasing_customers': len(customers), 'average_order_value_gbp': round(gross/len(orders), 2),
    'repeat_customers': int(customers.Orders.gt(1).sum()),
    'repeat_customer_share': round(float(customers.Orders.gt(1).mean()), 6),
    'known_customer_sales_share': round(float(sale.loc[sale.KnownCustomer, 'LineAmount'].sum()/gross), 6),
    'uk_gross_sales_share': round(float(country.get('United Kingdom', 0)/gross), 6),
    'source_start': str(fact.Date.min().date()), 'source_end': str(fact.Date.max().date()),
    'rfm_as_of': str(asof.date()), 'tables': {k: len(v) for k,v in tables.items()},
    'segments': customers.groupby('Segment').agg(Customers=('CustomerKey','size'), GrossSales=('GrossSales','sum')).round(2).to_dict('index'),
}
# Independent SQL controls and relationship integrity.
with sqlite3.connect(OUT / 'retail.sqlite') as conn:
    sqlnet, sqlgross, sqlorders = conn.execute("SELECT SUM(LineAmount), SUM(CASE WHEN Kind='Sale' THEN LineAmount ELSE 0 END), COUNT(DISTINCT CASE WHEN Kind='Sale' THEN InvoiceNo END) FROM FactTransactions").fetchone()
assert abs(sqlnet-(gross-credit)) < .01
assert abs(sqlgross-gross) < .01
assert sqlorders == len(orders)
assert abs(orders.OrderSales.sum()-gross) < .01
for column, dimension in [('CustomerKey', dimcustomers), ('ProductKey', products), ('CountryKey', countries), ('Date', dates)]:
    assert not dimension[column].duplicated().any(), column
    assert fact[column].isin(dimension[column]).all(), column
assert cohorts.ActiveCustomers.le(cohorts.CohortSize).all()
assert cohorts.loc[cohorts.Offset.eq(0),'ActiveCustomers'].equals(cohorts.loc[cohorts.Offset.eq(0),'CohortSize'])
(ROOT/'docs/analysis_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
