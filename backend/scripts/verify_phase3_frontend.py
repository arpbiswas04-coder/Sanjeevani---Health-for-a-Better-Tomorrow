"""Run opt-in real HTTP frontend tests without placing credentials on the command line.

Requires existing Phase 2 credentials and Phase 3 seed manifest in ignored tmp/.
No mocks, installations, container changes or destructive database setup.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
credentials = json.loads((root / 'tmp/phase2-auth-account.json').read_text())
manifest = json.loads((root / 'tmp/phase3-seed.json').read_text())
assert manifest['database'] == 'sanjeevani_dev'
environment = {
    **os.environ,
    'DATA_LIVE_TEST': '1',
    'AUTH_LIVE_TEST': '1',
    'AUTH_LIVE_USERNAME': credentials['username'],
    'AUTH_LIVE_PASSWORD': credentials['password'],
    'DATA_LIVE_FIXTURE': json.dumps(manifest),
}
command = ['npm', 'test', '--', 'src/test/dataLive.integration.test.tsx',
           'src/test/authLive.integration.test.tsx', '--fileParallelism=false',
           '--reporter=json', '--outputFile=../tmp/phase3-live.json']
if os.name == 'nt':
    command = ['cmd.exe', '/d', '/c', *command]
with (root / 'tmp/phase3-live.log').open('w', encoding='utf-8') as log:
    result = subprocess.run(command, cwd=root / 'frontend', env=environment,
                            stdout=log, stderr=subprocess.STDOUT)
print('Live frontend verification exit code:', result.returncode)
print('Results: tmp/phase3-live.json; log: tmp/phase3-live.log')
sys.exit(result.returncode)
