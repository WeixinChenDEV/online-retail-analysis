"""Independent SQL checks for dashboard filter behaviour and cohort denominators."""
import json, sqlite3
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'data/processed'
fact = pd.read_csv(folder/'FactTransactions.csv', dtype={'CustomerKey':str,'ProductKey':str})
orders = pd.read_csv(folder/'FactOrders.csv', dtype={'CustomerKey':str})
cohort = pd.read_csv(folder/'FactCohort.csv')
summary = json.loads((ROOT/'docs/analysis_summary.json').read_text())
checks = []
with sqlite3.connect(folder/'retail.sqlite') as conn:
    for country in [None, 'United Kingdom', 'Germany', 'France']:
        for month in [None,'2010-12','2011-03','2011-11','2011-12']:
            filtered = fact
            orderfiltered = orders
            where, params = [], []
            if country:
                filtered = filtered[filtered.CountryKey.eq(country)]
                orderfiltered = orderfiltered[orderfiltered.CountryKey.eq(country)]
                where.append('CountryKey = ?'); params.append(country)
            if month:
                filtered = filtered[filtered.YearMonth.eq(month)]
                orderfiltered = orderfiltered[orderfiltered.Date.str.startswith(month)]
                where.append('YearMonth = ?'); params.append(month)
            clause = ' WHERE '+ ' AND '.join(where) if where else ''
            net,gross,credits,purchasers = conn.execute(
                "SELECT SUM(LineAmount), SUM(CASE WHEN Kind='Sale' THEN LineAmount ELSE 0 END), "
                "-SUM(CASE WHEN Kind='Credit' THEN LineAmount ELSE 0 END), "
                "COUNT(DISTINCT CASE WHEN Kind='Sale' AND CustomerKey<>'0' THEN CustomerKey END) "
                'FROM FactTransactions'+clause,params).fetchone()
            sales = filtered[filtered.Kind.eq('Sale')]
            for observed, expected in [(net, filtered.LineAmount.sum()),
                                       (gross,sales.LineAmount.sum()),
                                       (credits,-filtered.loc[filtered.Kind.eq('Credit'),'LineAmount'].sum())]:
                assert abs((observed or 0)-expected)<.01,(country,month,observed,expected)
            assert purchasers == sales.loc[sales.CustomerKey.ne('0'),'CustomerKey'].nunique()
            assert len(orderfiltered) == sales.InvoiceNo.nunique()
            assert abs(orderfiltered.OrderSales.sum()-sales.LineAmount.sum())<.01
            checks.append({'country':country,'month':month,'result':'passed'})
    assert conn.execute("SELECT COUNT(*) FROM DimCustomer WHERE CustomerKey <> '0' AND Orders > 0").fetchone()[0] == summary['known_purchasing_customers']
    for row in cohort.itertuples():
        active = conn.execute("SELECT COUNT(DISTINCT o.CustomerKey) FROM FactOrders o JOIN DimCustomer c USING(CustomerKey) WHERE c.Cohort=? AND substr(o.Date,1,7)=?",[row.Cohort,row.ActivityMonth]).fetchone()[0]
        size = conn.execute("SELECT COUNT(*) FROM DimCustomer WHERE Cohort=?",[row.Cohort]).fetchone()[0]
        assert active == row.ActiveCustomers
        assert size == row.CohortSize
assert cohort.ActivityMonth.le('2011-11').all()
assert not cohort[['Cohort','Offset']].duplicated().any()
result = {'filter_cases':len(checks),'cohort_cells':len(cohort),'financial_tolerance_gbp':0.01,'result':'passed'}
(ROOT/'docs/data_tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
