"""Publish this project only, using an existing matching Git Credential Manager login.

No tokens are logged, written to disk, included in remote URLs or committed.
Requires explicit authorisation to publish to WeixinChenDEV.
"""
import json, os, subprocess, urllib.request, urllib.error
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OWNER, REPO = 'WeixinChenDEV', 'retail-insights-powerbi'
git = ['git','-c','http.proxy=','-c','https.proxy=','-c','credential.interactive=never',
       '-c','safe.directory='+ROOT.as_posix()]
proc = subprocess.run(git+['credential','fill'], input=f'protocol=https\nhost=github.com\nusername={OWNER}\n\n', text=True,capture_output=True)
if proc.returncode:
    raise SystemExit('Matching GitHub credentials unavailable. Complete Git Credential Manager login first.')
credential = dict(line.split('=',1) for line in proc.stdout.splitlines() if '=' in line)
secret = credential.get('password')
if not secret:
    raise SystemExit('No usable GitHub credential returned.')

def api(path, method='GET', data=None):
    request = urllib.request.Request('https://api.github.com'+path,method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Authorization':'Bearer '+secret,'Accept':'application/vnd.github+json',
                 'X-GitHub-Api-Version':'2022-11-28','User-Agent':'RetailInsights-Portfolio','Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response:
        return json.load(response)

profile = api('/user')
if profile['login'].lower() != OWNER.lower():
    raise SystemExit('Credential identity mismatch. Publication stopped.')
try:
    repo = api(f'/repos/{OWNER}/{REPO}')
except urllib.error.HTTPError as e:
    if e.code != 404:
        raise SystemExit(f'GitHub repository check failed: HTTP {e.code}')
    repo = api('/user/repos','POST',{'name':REPO,'description':'Power BI retail analytics: reproducible Python/SQL, RFM and cohort analysis. Desktop validation pending.','private':False,'auto_init':False})
else:
    # Safe retry after a previous successful create/push; don't overwrite unrelated repositories.
    if not (ROOT/'.git').exists():
        raise SystemExit('Repository already exists; stopped to avoid overwriting unrelated work.')
if not (ROOT/'.git').exists():
    subprocess.run(git+['init','-b','main',str(ROOT)],check=True)
subprocess.run(git+['-C',str(ROOT),'add','.'],check=True)
changes = subprocess.run(git+['-C',str(ROOT),'diff','--cached','--quiet']).returncode
if changes:
    subprocess.run(git+['-C',str(ROOT),'-c','user.name=Weixin Chen','-c','user.email=WeixinChenDEV@users.noreply.github.com',
                        'commit','-m','Add reproducible retail analytics Power BI project'],check=True)
remote = f'https://{OWNER}@github.com/{OWNER}/{REPO}.git'
remotes = subprocess.run(git+['-C',str(ROOT),'remote'],text=True,capture_output=True,check=True).stdout.splitlines()
if 'origin' not in remotes:
    subprocess.run(git+['-C',str(ROOT),'remote','add','origin',remote],check=True)
existing = subprocess.run(git+['-C',str(ROOT),'remote','get-url','origin'],text=True,capture_output=True,check=True).stdout.strip()
if existing != remote:
    raise SystemExit('Unexpected origin URL; publication stopped.')
subprocess.run(git+['-C',str(ROOT),'-c',f'credential.username={OWNER}','push','-u','origin','main'],check=True)
api(f'/repos/{OWNER}/{REPO}/topics','PUT',{'names':['powerbi','data-analysis','retail-analytics','sql','python','rfm','cohort-analysis']})
head = api(f'/repos/{OWNER}/{REPO}/commits/main')['sha']
print('Published:',repo['html_url'])
print('Verified remote commit:',head)
