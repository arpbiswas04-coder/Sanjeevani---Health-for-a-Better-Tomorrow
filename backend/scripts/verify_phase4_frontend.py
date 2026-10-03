"""Run only Phase 4 real HTTP tests; private credentials are passed via environment."""
import json
import os
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[2]
credentials=json.loads((root/'tmp/phase2-auth-account.json').read_text())
manifest=json.loads((root/'tmp/phase4-fixture.json').read_text())
assert manifest['database']=='sanjeevani_dev' and manifest['run'].startswith('DEV-P4-')
env={**os.environ,'MUTATIONS_LIVE_TEST':'1','MUTATIONS_LIVE_FIXTURE':json.dumps(manifest),
     'AUTH_LIVE_USERNAME':credentials['username'],'AUTH_LIVE_PASSWORD':credentials['password']}
command=['npm','test','--','src/test/mutationsLive.integration.test.tsx','--reporter=json','--outputFile=../tmp/phase4-live.json']
if os.name=='nt': command=['cmd.exe','/d','/c',*command]
with (root/'tmp/phase4-live.log').open('w',encoding='utf-8') as log:
    result=subprocess.run(command,cwd=root/'frontend',env=env,stdout=log,stderr=subprocess.STDOUT)
print('Phase 4 live tests exit:',result.returncode,'; results in tmp/phase4-live.json')
sys.exit(result.returncode)
