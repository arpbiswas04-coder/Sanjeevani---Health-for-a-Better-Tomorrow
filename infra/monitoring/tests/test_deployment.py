import sys
from pathlib import Path
import unittest

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path:
    sys.path.insert(0, _infra)

from deployment.ssh_deploy import validate
from deployment.check_release_ci import validate as validate_ci, REQUIRED


class DeploymentTests(unittest.TestCase):
    def test_no_shell_injection_and_explicit_environment(self):
        valid = ['host.example', 'deploy', '/srv/sanjeevani', 'a'*40, 'staging']
        validate(*valid)
        for index, bad in ((0, '-oProxyCommand=x'), (1, 'root;evil'), (2, '/'), (2, '/srv/../etc'), (3, 'main'), (4, 'unknown')):
            values = valid.copy()
            values[index] = bad
            with self.assertRaises(ValueError): validate(*values)

    def test_exact_revision_gate_and_latest_failure(self):
        sha = 'a'*40
        runs = [dict(name=n, head_sha=sha, run_number=1, event='push', conclusion='success', status='completed') for n in REQUIRED]
        validate_ci(runs, sha)
        with self.assertRaises(ValueError): validate_ci(runs, 'b'*40)
        with self.assertRaises(ValueError): validate_ci(runs[:-1], sha)
        failure = {**runs[0], 'run_number': 2, 'conclusion': 'failure'}
        with self.assertRaises(ValueError): validate_ci(runs+[failure], sha)
