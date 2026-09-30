"""Cache Microsoft's public contracts for local report validation."""
import json, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.schema-cache'
CACHE.mkdir(exist_ok=True)
BASE = 'https://developer.microsoft.com/json-schemas/fabric/item/'
contracts = {
    'visual': 'report/definition/visualContainer/2.1.0/schema.json',
    'page': 'report/definition/page/2.0.0/schema.json',
    'pages': 'report/definition/pagesMetadata/1.0.0/schema.json',
    'report': 'report/definition/report/2.0.0/schema.json',
    'version': 'report/definition/versionMetadata/1.0.0/schema.json',
    'pbir': 'report/definitionProperties/2.0.0/schema.json',
}
for name, path in contracts.items():
    url = BASE + path
    with urllib.request.urlopen(url, timeout=30) as response:
        body = json.load(response)
    (CACHE / (name + '.json')).write_text(json.dumps(body, indent=2), encoding='utf-8')
    print(name, 'required:', body.get('required'), 'properties:', list(body.get('properties', {})))
