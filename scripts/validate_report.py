"""Validate every authored PBIR JSON against Microsoft's published JSON schemas."""
import hashlib, json, sys, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'.tools'))
from jsonschema import Draft7Validator
from referencing import Registry, Resource
CACHE = ROOT/'.schema-cache'
CACHE.mkdir(exist_ok=True)

def retrieve(uri):
    file = CACHE/(hashlib.sha256(uri.encode()).hexdigest()+'.json')
    if file.exists():
        return json.loads(file.read_text(encoding='utf-8'))
    physical_uri = uri.replace('schema.embedded.json', 'schema-embedded.json')
    with urllib.request.urlopen(physical_uri, timeout=30) as response:
        schema = json.load(response)
    file.write_text(json.dumps(schema), encoding='utf-8')
    return schema

count = 0
for path in sorted((ROOT/'powerbi').rglob('*.json')) + list((ROOT/'powerbi').rglob('*.pbir')):
    body = json.loads(path.read_text(encoding='utf-8'))
    if '$schema' not in body:
        continue
    uri = body['$schema']
    schema = retrieve(uri)
    registry = Registry(retrieve=lambda url: Resource.from_contents(retrieve(url)))
    errors = list(Draft7Validator(schema, registry=registry).iter_errors(body))
    if errors:
        for error in errors:
            print(path.relative_to(ROOT),list(error.path),error.message)
        sys.exit(1)
    count += 1
# Semantic bindings, dimension cardinality and data types are checked separately.
model = json.loads((ROOT/'powerbi/RetailInsights.SemanticModel/model.bim').read_text(encoding='utf-8'))['model']
tables = {t['name']:t for t in model['tables']}
for path in (ROOT/'powerbi').rglob('visual.json'):
    visual = json.loads(path.read_text(encoding='utf-8'))['visual']
    for role in visual['query']['queryState'].values():
        for p in role['projections']:
            kind, expr = next(iter(p['field'].items()))
            table = tables[expr['Expression']['SourceRef']['Entity']]
            props = table['measures' if kind=='Measure' else 'columns']
            assert expr['Property'] in [v['name'] for v in props], p
for rel in model['relationships']:
    for side in ['from','to']:
        assert rel[side+'Column'] in [c['name'] for c in tables[rel[side+'Table']]['columns']]
print('PASS:',count,'official-schema documents; all visual bindings and relationship references resolve.')
status_path = ROOT/'docs/validation.json'
status = json.loads(status_path.read_text()) if status_path.exists() else {}
status.update({'official_schema_documents':count,'bindings':'passed','relationships':'passed'})
status.setdefault('desktop_runtime','pending')
status_path.write_text(json.dumps(status,indent=2))
