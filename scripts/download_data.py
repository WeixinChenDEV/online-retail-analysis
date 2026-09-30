"""Download the attributed CC BY 4.0 source dataset from UCI."""
import urllib.request, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'data/raw'
folder.mkdir(parents=True, exist_ok=True)
archive = folder/'online-retail.zip'
urllib.request.urlretrieve('https://archive.ics.uci.edu/static/public/352/online+retail.zip', archive)
with zipfile.ZipFile(archive) as z:
    # Extract only the expected workbook rather than arbitrary archive paths.
    member = next(n for n in z.namelist() if n.split('/')[-1] == 'Online Retail.xlsx')
    (folder/'Online Retail.xlsx').write_bytes(z.read(member))
print('Downloaded Online Retail.xlsx. Source: UCI, DOI 10.24432/C5BW33, CC BY 4.0.')
