"""Author a native PBIP/PBIR report and import semantic model from prepared CSVs."""
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / 'powerbi'
REPORT = PBI / 'RetailInsights.Report'
MODEL = PBI / 'RetailInsights.SemanticModel'
BASE = 'https://developer.microsoft.com/json-schemas/fabric/item/report/'

def write(path, data):
    if '--report-only' in sys.argv and path.name in ('model.bim', 'definition.pbism'):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

write(PBI/'RetailInsights.pbip', {'version':'1.0','artifacts':[{'report':{'path':'RetailInsights.Report'}}], 'settings':{'enableAutoRecovery':True}})
write(REPORT/'definition.pbir', {'$schema':BASE+'definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../RetailInsights.SemanticModel'}}})
write(MODEL/'definition.pbism', {'version':'1.0','settings':{}})

currency = '£#,0.00;(£#,0.00);£0.00'
measures = {
    'Gross Sales': ('CALCULATE(SUM(FactTransactions[LineAmount]), FactTransactions[Kind] = "Sale")', currency),
    'Recorded Credits': ('-CALCULATE(SUM(FactTransactions[LineAmount]), FactTransactions[Kind] = "Credit")', currency),
    'Net Recorded Sales': ('SUM(FactTransactions[LineAmount])', currency),
    'Sales Orders': ('COUNTROWS(FactOrders)', '#,0'),
    'Average Order Value': ('DIVIDE([Gross Sales], [Sales Orders])', currency),
    'Purchasing Customers': ('CALCULATE(DISTINCTCOUNT(FactOrders[CustomerKey]), FactOrders[CustomerKey] <> "0")', '#,0'),
    'Units Sold': ('CALCULATE(SUM(FactTransactions[Quantity]), FactTransactions[Kind] = "Sale")', '#,0'),
    'Credit Value Share': ('DIVIDE([Recorded Credits], [Gross Sales])', '0.0%'),
    'Known Customer Sales Share': ('DIVIDE(CALCULATE([Gross Sales], FactTransactions[CustomerKey] <> "0"), [Gross Sales])', '0.0%'),
    'Selected Period Repeat Customers': ('COUNTROWS(FILTER(VALUES(DimCustomer[CustomerKey]), DimCustomer[CustomerKey] <> "0" && CALCULATE([Sales Orders]) > 1))', '#,0'),
    'Selected Period Repeat Share': ('DIVIDE([Selected Period Repeat Customers], [Purchasing Customers])', '0.0%'),
    'Snapshot Customers': ('CALCULATE(COUNTROWS(DimCustomer), DimCustomer[CustomerKey] <> "0", DimCustomer[Orders] > 0)', '#,0'),
    'Snapshot Gross Sales': ('SUM(DimCustomer[GrossSales])', currency),
    'Snapshot Repeat Customers': ('CALCULATE(COUNTROWS(DimCustomer), DimCustomer[CustomerKey] <> "0", DimCustomer[Orders] > 1)', '#,0'),
    'Snapshot Repeat Share': ('DIVIDE([Snapshot Repeat Customers], [Snapshot Customers])', '0.0%'),
    'Cohort Active Customers': ('SUM(FactCohort[ActiveCustomers])', '#,0'),
    'Cohort Repeat Activity': ('IF(HASONEVALUE(FactCohort[Cohort]) && HASONEVALUE(FactCohort[Offset]), DIVIDE(SUM(FactCohort[ActiveCustomers]), SUM(FactCohort[CohortSize])))', '0.0%'),
    'Merchandise Gross Sales': ('CALCULATE([Gross Sales], DimProduct[ProductType] = "Merchandise")', currency),
}
types = {
    'Date':'dateTime','FirstObservedPurchase':'dateTime','LastObservedPurchase':'dateTime','AsOfDate':'dateTime',
    'LineID':'int64','Quantity':'int64','Orders':'int64','Units':'int64','RecencyDays':'int64',
    'RScore':'int64','FScore':'int64','MScore':'int64','Year':'int64','Month':'int64','YearMonthSort':'int64',
    'Offset':'int64','CohortSize':'int64','ActiveCustomers':'int64','KnownCustomer':'boolean',
    'UnitPrice':'double','LineAmount':'decimal','OrderSales':'decimal','GrossSales':'decimal',
}
mt = {'dateTime':'type date','int64':'Int64.Type','boolean':'type logical','double':'type number','decimal':'Currency.Type','string':'type text'}
tables = []
for path in sorted((ROOT/'data/processed').glob('*.csv')):
    if path.stem == 'monthly_reconciliation':
        continue
    names = list(pd.read_csv(path, nrows=0).columns)
    cols = []
    for name in names:
        datatype = types.get(name, 'string')
        col = {'name':name,'dataType':datatype,'sourceColumn':name,'summarizeBy':'none'}
        if datatype == 'dateTime':
            col['formatString'] = 'yyyy-MM-dd'
        if name == 'YearMonth':
            col['sortByColumn'] = 'YearMonthSort' if path.stem == 'DimDate' else None
            if col['sortByColumn'] is None:
                del col['sortByColumn']
        if name == 'MonthName':
            col['sortByColumn'] = 'Month'
        if (name.endswith('Key') and path.stem != 'DimCountry') or name == 'LineID':
            col['isHidden'] = True
        cols.append(col)
    conversions = ', '.join('{"'+n+'", '+mt[types.get(n,'string')]+'}' for n in names)
    expression = '\n'.join([
        'let',
        f'    Source = Csv.Document(File.Contents(DataFolder & "\\{path.name}"), [Delimiter=",", Columns={len(names)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
        '    Typed = Table.TransformColumnTypes(Headers, {'+conversions+'}, "en-GB")',
        'in', '    Typed'])
    table = {'name':path.stem, 'columns':cols,'partitions':[{'name':path.stem,'mode':'import','source':{'type':'m','expression':expression.splitlines()}}]}
    if path.stem == 'FactTransactions':
        table['measures'] = [{'name':n,'expression':ex,'formatString':fmt,'displayFolder':'Retail KPIs'} for n,(ex,fmt) in measures.items()]
    tables.append(table)
relationships = []
for fact in ['FactTransactions','FactOrders']:
    for dim,key in [('DimDate','Date'),('DimCustomer','CustomerKey'),('DimCountry','CountryKey')]:
        relationships.append({'name':fact+'_'+dim,'fromTable':fact,'fromColumn':key,'toTable':dim,'toColumn':key,'crossFilteringBehavior':'oneDirection'})
relationships.append({'name':'Transactions_Product','fromTable':'FactTransactions','fromColumn':'ProductKey','toTable':'DimProduct','toColumn':'ProductKey','crossFilteringBehavior':'oneDirection'})
write(MODEL/'model.bim', {'name':'RetailInsights','compatibilityLevel':1601,'model':{
    'culture':'en-GB','defaultPowerBIDataSourceVersion':'powerBI_V3',
    'sourceQueryCulture':'en-GB','tables':tables,'relationships':relationships,
    'expressions':[{'name':'DataFolder','kind':'m','expression':'"C:\\RETAIL_INSIGHTS\\data\\processed" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
    'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(['DataFolder']+[t['name'] for t in tables])}]}})
(ROOT/'docs/measures.dax').write_text('\n\n'.join(n+' =\n'+ex for n,(ex,_) in measures.items())+'\n', encoding='utf-8')

def literal(value):
    val = "'"+value.replace("'","''")+"'" if isinstance(value,str) else ('true' if value is True else 'false' if value is False else str(value))
    return {'expr':{'Literal':{'Value':val}}}

def color(value):
    return {'solid':{'color':literal(value)}}

def field(table, prop, measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':prop}}

def projection(table, prop, measure=False):
    return {'field':field(table,prop,measure),'queryRef':table+'.'+prop,'nativeQueryRef':prop}

def plot(page, name, vtype, title, x, y, w, h, roles, sort=None):
    visual = {'visualType':vtype,'query':{'queryState':{r:{'projections':[projection(*p) for p in ps]} for r,ps in roles.items()}},
              'visualContainerObjects':{
                  'title':[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(12),'fontColor':color('#15283F'),'bold':literal(True)}}],
                  'background':[{'properties':{'show':literal(True),'color':color('#FFFFFF'),'transparency':literal(0)}}],
                  'border':[{'properties':{'show':literal(True),'color':color('#DCE4EC'),'radius':literal(8)}}]},
              'drillFilterOtherVisuals':True}
    if vtype == 'slicer':
        visual['objects'] = {'data':[{'properties':{'mode':literal('Dropdown')}}]}
    elif vtype == 'card':
        visual['objects'] = {'labels':[{'properties':{'fontSize':literal(24),'displayUnits':literal(0),'precision':literal(2 if 'Sales' in title or 'Credits' in title or 'Value' in title else 0)}}], 'categoryLabels':[{'properties':{'show':literal(False)}}]}
    elif vtype in ('tableEx','pivotTable'):
        visual['objects'] = {'grid':[{'properties':{'textSize':literal(11)}}]}
        if vtype == 'pivotTable':
            visual['objects']['subTotals'] = [{'properties':{'rowSubtotals':literal(False),'columnSubtotals':literal(False),'rowGrandTotal':literal(False),'columnGrandTotal':literal(False)}}]
    if sort:
        visual['query']['sortDefinition'] = {'sort':[{'field':field(*sort[:3]),'direction':sort[3]}],'isDefaultSort':False}
    write(REPORT/f'definition/pages/{page}/visuals/{name}/visual.json', {
        '$schema':BASE+'definition/visualContainer/2.1.0/schema.json','name':name,
        'position':{'x':x,'y':y,'z':0,'height':h,'width':w,'tabOrder':0}, 'visual':visual})

M = lambda n: ('FactTransactions',n,True)
C = lambda t,n: (t,n,False)
page_order = ['Overview','Products','Customers','Cohorts']
write(REPORT/'definition/version.json',{'$schema':BASE+'definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
write(REPORT/'definition/report.json',{'$schema':BASE+'definition/report/2.0.0/schema.json','themeCollection':{'customTheme':{'name':'RetailTheme','reportVersionAtImport':'5.37','type':'RegisteredResources'}},'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'RetailTheme','path':'RetailTheme.json','type':'CustomTheme'}]}],'settings':{'useStylableVisualContainerHeader':True}})
write(REPORT/'definition/pages/pages.json',{'$schema':BASE+'definition/pagesMetadata/1.0.0/schema.json','pageOrder':page_order,'activePageName':'Overview'})
labels = {'Overview':'01 | Trading overview','Products':'02 | Products & markets','Customers':'03 | Customer snapshot','Cohorts':'04 | Cohort repeat activity'}
for page in page_order:
    page_body = {'$schema':BASE+'definition/page/2.0.0/schema.json','name':page,'displayName':labels[page],'displayOption':'FitToPage','width':1280,'height':800,'objects':{'background':[{'properties':{'color':color('#F5F7FB'),'transparency':literal(0)}}]}}
    if page == 'Customers':
        page_body['filterConfig'] = {'filters':[{'name':'PurchasingCustomerSnapshot','field':field('DimCustomer','Orders'),'type':'Advanced','filter':{'Version':2,'From':[{'Name':'c','Entity':'DimCustomer','Type':0}],'Where':[{'Condition':{'Comparison':{'ComparisonKind':1,'Left':{'Column':{'Expression':{'SourceRef':{'Source':'c'}},'Property':'Orders'}},'Right':{'Literal':{'Value':'0L'}}}}}]}}]}
    write(REPORT/f'definition/pages/{page}/page.json',page_body)
for page in ['Overview','Products']:
    plot(page,'MonthFilter','slicer','Reporting month · Dec 2011 is partial',24,16,602,80, {'Values':[C('DimDate','YearMonth')]})
    plot(page,'CountryFilter','slicer','Country',646,16,610,80, {'Values':[C('DimCountry','CountryKey')]})
for i,n in enumerate(['Gross Sales','Recorded Credits','Net Recorded Sales','Sales Orders']):
    plot('Overview','KPI'+str(i),'card',n,24+i*314,112,290,108,{'Values':[M(n)]})
plot('Overview','MonthlyTrend','lineChart','Gross sales & recorded credits | GBP',24,238,800,322,{'Category':[C('DimDate','YearMonth')],'Y':[M('Gross Sales'),M('Recorded Credits')]}, ('DimDate','YearMonth',False,'Ascending'))
for i,n in enumerate(['Average Order Value','Purchasing Customers','Known Customer Sales Share','Credit Value Share']):
    plot('Overview','Operating'+str(i),'card',n,844+(i%2)*214,238+(i//2)*170,198,152,{'Values':[M(n)]})
plot('Overview','MonthlyControls','tableEx','Monthly controls | Dec 2011 ends on the 9th',24,578,1232,196, {'Values':[C('DimDate','YearMonth')]+[M(n) for n in ['Gross Sales','Recorded Credits','Net Recorded Sales','Sales Orders','Average Order Value']]}, ('DimDate','YearMonth',False,'Ascending'))
plot('Products','CountrySales','barChart','Gross sales by country | GBP',24,112,602,310, {'Category':[C('DimCountry','CountryKey')],'Y':[M('Gross Sales')]}, ('FactTransactions','Gross Sales',True,'Descending'))
plot('Products','ProductSales','barChart','Products & charges | GBP · scroll for more',646,112,610,310, {'Category':[C('DimProduct','ProductLabel')],'Y':[M('Gross Sales')]}, ('FactTransactions','Gross Sales',True,'Descending'))
plot('Products','ProductTypeFilter','slicer','Merchandise or other / charges',24,438,300,90, {'Values':[C('DimProduct','ProductType')]})
plot('Products','ProductDetail','tableEx','Product detail | posted credits are not matched refunds',344,438,912,336, {'Values':[C('DimProduct','ProductLabel')]+[M(n) for n in ['Gross Sales','Recorded Credits','Units Sold']]}, ('FactTransactions','Gross Sales',True,'Descending'))
for i,n in enumerate(['Snapshot Customers','Snapshot Repeat Customers','Snapshot Repeat Share']):
    plot('Customers','Snapshot'+str(i),'card',n+' | as of 10 Dec 2011',24+i*420,24,392,112,{'Values':[M(n)]})
plot('Customers','SegmentFilter','slicer','RFM segment | fixed full-period snapshot',24,154,1232,80, {'Values':[C('DimCustomer','Segment')]})
plot('Customers','SegmentCount','barChart','Customers by RFM segment',24,252,602,280, {'Category':[C('DimCustomer','Segment')],'Y':[M('Snapshot Customers')]})
plot('Customers','SegmentSales','barChart','Known-customer gross sales by segment | GBP',646,252,610,280, {'Category':[C('DimCustomer','Segment')],'Y':[M('Snapshot Gross Sales')]})
plot('Customers','CustomerTable','tableEx','Customer snapshot | anonymous customers excluded from RFM',24,550,1232,224, {'Values':[C('DimCustomer',n) for n in ['CustomerKey','Segment','RecencyDays','Orders','GrossSales','RScore','FScore','MScore']]})
plot('Cohorts','CohortFilter','slicer','First observed purchase cohort',24,24,1232,80, {'Values':[C('FactCohort','Cohort')]})
plot('Cohorts','RetentionMatrix','pivotTable','Monthly repeat-purchase activity | incomplete Dec 2011 omitted',24,124,1232,440, {'Rows':[C('FactCohort','Cohort')],'Columns':[C('FactCohort','Offset')],'Values':[M('Cohort Repeat Activity')]})
plot('Cohorts','CohortDetail','tableEx','Observed cells only | counts and denominators',24,584,1232,190, {'Values':[C('FactCohort',n) for n in ['Cohort','Offset','CohortSize','ActiveCustomers','ActivityMonth']]})
write(ROOT/'assets/retail-theme.json', {'name':'Retail Insights','dataColors':['#167D9A','#EF9A47','#385B8D','#81B29A','#A86F98'],'background':'#F5F7FB','foreground':'#15283F','tableAccent':'#167D9A'})
write(REPORT/'StaticResources/RegisteredResources/RetailTheme.json',json.loads((ROOT/'assets/retail-theme.json').read_text()))
print('Built native PBIP with', len(tables), 'tables,',len(measures),'measures and',len(list(REPORT.glob('definition/pages/*/visuals/*/visual.json'))),'visuals')
