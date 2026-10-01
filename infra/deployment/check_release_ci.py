"""Fail closed unless required workflow runs passed for the exact deployment SHA."""
import json
import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode

REQUIRED = {'Member 4 checks', 'Backend CI', 'Frontend CI', 'Project Integrity & Security Check'}


def validate(runs, sha):
    latest = {}
    for run in sorted(runs, key=lambda row: (row['run_number'], row.get('run_attempt', 1)), reverse=True):
        if run['head_sha'] == sha and run.get('event') in ('push', 'workflow_dispatch'):
            latest.setdefault(run['name'], run)
    if any(name not in latest or latest[name]['conclusion'] != 'success' or latest[name]['status'] != 'completed' for name in REQUIRED):
        raise ValueError('Required checks missing, unfinished or failed for this exact revision')


if __name__ == '__main__':
    if os.environ['DEPLOY_ENVIRONMENT'] == 'production' and os.environ['GITHUB_REF'] != 'refs/heads/main':
        raise ValueError('Production manual deployment requires main and environment approval')
    sha = os.environ['DEPLOY_SHA']
    repository = os.environ['GITHUB_REPOSITORY']
    request = Request(f'https://api.github.com/repos/{repository}/actions/runs?'+urlencode({'head_sha': sha, 'per_page': 100}),
        headers={'Authorization': 'Bearer '+os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json'})
    with urlopen(request, timeout=15) as response:
        validate(json.load(response)['workflow_runs'], sha)
    print('Exact-revision workflow gates passed')
