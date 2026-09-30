"""Data-derived offline portfolio previews. These are NOT Power BI screenshots."""
import json
from pathlib import Path
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/previews'
OUT.mkdir(parents=True, exist_ok=True)
summary = json.loads((ROOT/'docs/analysis_summary.json').read_text())
monthly = pd.read_csv(ROOT/'data/processed/monthly_reconciliation.csv')
customers = pd.read_csv(ROOT/'data/processed/DimCustomer.csv')
cohorts = pd.read_csv(ROOT/'data/processed/FactCohort.csv')
WHITE, BG, INK, MUTED, TEAL, ORANGE = '#FFFFFF','#F4F7FA','#15283F','#60738A','#167D9A','#EF9A47'

def font(size, bold=False):
    candidates = [Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    return ImageFont.truetype(str(next(p for p in candidates if p.exists())),size)

def base(title, subtitle):
    im = Image.new('RGB',(1440,940),BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1440,7),fill=TEAL)
    d.text((38,28),'RETAIL INSIGHTS',font=font(14,True),fill=TEAL)
    d.text((38,55),title,font=font(33,True),fill=INK)
    d.text((38,106),subtitle,font=font(16),fill=MUTED)
    d.text((38,895),'OFFLINE DATA PREVIEW | Not a Power BI screenshot | Desktop runtime validation pending',font=font(15,True),fill=MUTED)
    return im,d

def panel(d, box, title):
    d.rounded_rectangle(box,radius=12,fill=WHITE,outline='#DDE5ED')
    d.text((box[0]+20,box[1]+17),title,font=font(19,True),fill=INK)

def card(d, x, label, value, note):
    d.rounded_rectangle((x,153,x+324,285),radius=12,fill=WHITE,outline='#DDE5ED')
    size = 19
    while d.textlength(label,font=font(size,True)) > 284:
        size -= 1
    d.text((x+20,170),label,font=font(size,True),fill=INK)
    d.text((x+20,198),value,font=font(31,True),fill=TEAL)
    size = 13
    while d.textlength(note,font=font(size)) > 284:
        size -= 1
    d.text((x+20,250),note,font=font(size),fill=MUTED)

im,d = base('Trading overview','UCI Online Retail | 1 Dec 2010 - 9 Dec 2011 | Historical case study | GBP')
for x,label,val,note in [
    (38,'Gross sales',f"£{summary['gross_sales_gbp']/1e6:.2f}m",'Positive-price sales; charges included'),
    (385,'Recorded credits',f"£{summary['recorded_credits_gbp']/1e3:.1f}k",'Posted credits, not matched returns'),
    (732,'Net recorded sales',f"£{summary['net_recorded_sales_gbp']/1e6:.2f}m",'Gross sales less posted credits'),
    (1079,'Sales orders',f"{summary['sales_orders']:,}",'Distinct positive-sale invoices')]:
    card(d,x,label,val,note)
panel(d,(38,310,976,685),'Sales trend | complete calendar months')
full = monthly[monthly.YearMonth.le('2011-11')]
maxval = full.Sale.max()*1.15
for j in range(5):
    yy = 620-j*58
    d.line((114,yy,945,yy),fill='#E8EDF2')
    d.text((52,yy-9),f'£{maxval*j/4/1e6:.1f}m',font=font(13),fill=MUTED)
points=[]
for i,row in enumerate(full.itertuples()):
    xx = 118+i*74
    yy = 620-row.Sale/maxval*232
    points.append((xx,yy))
    d.text((xx-20,635),row.YearMonth[2:],font=font(12),fill=MUTED)
d.line(points,fill=TEAL,width=4)
for xx,yy in points:
    d.ellipse((xx-5,yy-5,xx+5,yy+5),fill=TEAL)
panel(d,(998,310,1403,685),'What the data supports')
for y,large,small in [(365,'65.6%','Repeat share of known purchasers'),(459,'84.6%','UK share of gross sales'),(553,'83.5%','Sales linked to an identifiable customer')]:
    d.text((1020,y),large,font=font(34,True),fill=TEAL)
    d.text((1020,y+47),small,font=font(14),fill=MUTED)
panel(d,(38,708,1403,865),'Interpretation before action')
for y,text in [(758,'Prioritise known-customer analysis; 24.9% of source rows have no CustomerID.'),
               (790,'December 2011 ends on the 9th: do not compare it with a full month.'),
               (822,'No cost or web-visit data: profit, conversion and marketing lift cannot be calculated.')]:
    d.text((58,y),text,font=font(17),fill=INK)
im.save(OUT/'overview.png')

im,d = base('Customer snapshot','Fixed RFM as of 10 Dec 2011 | Known purchasing customers only | Whole observed window')
for x,label,val,note in [(38,'Purchasing customers','4,338','Unknown and credit-only customers excluded'),
                         (385,'Repeat customers','2,845','More than one observed positive-sale invoice'),
                         (732,'Champions','911','R >= 4, F >= 4, M >= 4'),
                         (1079,'At-risk segment','765','R <= 2 and F >= 3; heuristic only')]:
    card(d,x,label,val,note)
segments = customers[customers.Orders.gt(0)].groupby('Segment').agg(Customers=('CustomerKey','size'),GrossSales=('GrossSales','sum')).sort_values('GrossSales',ascending=False)
for box,col,title,fmt in [((38,310,707,720),'Customers','Customer distribution',lambda x:f'{int(x):,}'),
                         ((731,310,1403,720),'GrossSales','Gross sales by segment | GBP',lambda x:f'£{x/1e6:.2f}m')]:
    panel(d,box,title)
    for i,(name,row) in enumerate(segments.iterrows()):
        y=box[1]+72+i*61
        d.text((box[0]+20,y),name,font=font(15),fill=INK)
        length = row[col]/segments[col].max()*320
        d.rounded_rectangle((box[0]+167,y,box[0]+167+max(length,2),y+24),radius=4,fill=TEAL)
        d.text((box[0]+180+length,y),fmt(row[col]),font=font(14),fill=MUTED)
panel(d,(38,744,1403,865),'Action hypotheses to test')
d.text((58,792),'Protect service quality for high-value repeat buyers; investigate the 765 at-risk customers before outreach.',font=font(16),fill=INK)
d.text((58,824),'Segments are fixed, descriptive rules. Campaign uplift and churn predictions require additional validation.',font=font(16),fill=MUTED)
im.save(OUT/'customers.png')

im,d = base('Cohort repeat activity','Calendar-month purchases / original cohort size | First observed purchase cohorts | Dec 2011 omitted')
panel(d,(38,153,1403,803),'Right-censoring is visible: unobserved cells stay blank')
cohortlabels = sorted(cohorts.Cohort.unique())
for offset in range(12):
    d.text((220+offset*89,215),f'M{offset}',font=font(15,True),fill=MUTED)
for i,label in enumerate(cohortlabels):
    y=254+i*40
    subset = cohorts[cohorts.Cohort.eq(label)]
    size=int(subset.CohortSize.iloc[0])
    d.text((58,y+7),f'{label} (n={size})',font=font(14),fill=INK)
    for offset in range(12):
        x=207+offset*89
        cell=subset[subset.Offset.eq(offset)]
        if cell.empty:
            d.rounded_rectangle((x,y,x+80,y+32),radius=4,fill='#EDF1F5')
            continue
        ratio=cell.ActiveCustomers.iloc[0]/size
        rgb=tuple(int(a+(b-a)*ratio) for a,b in zip((224,242,246),(22,125,154)))
        d.rounded_rectangle((x,y,x+80,y+32),radius=4,fill=rgb)
        d.text((x+18,y+7),f'{ratio:.0%}',font=font(13,True),fill=WHITE if ratio>.55 else INK)
d.text((38,836),'M0 is 100% by construction. Later months measure repeat purchase, not continuous subscription retention.',font=font(16),fill=MUTED)
im.save(OUT/'cohorts.png')
print('Created 3 labelled offline data previews.')
