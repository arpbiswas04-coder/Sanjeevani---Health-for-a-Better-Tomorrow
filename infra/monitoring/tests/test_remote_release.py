import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

_infra = str(Path(__file__).resolve().parents[2])
if _infra not in sys.path:
    sys.path.insert(0, _infra)

from deployment.remote_release import deploy


@unittest.skipIf(os.name == 'nt', 'Linux host filesystem contract; exercised in Linux CI/container')
class RemoteReleaseTests(unittest.TestCase):
    def prepare(self, root, sha):
        shared=root/'shared'; shared.mkdir()
        (shared/'federated-secrets/local-dev').mkdir(parents=True)
        (shared/'federated-secrets/local-dev/manifest.json').write_text('{}')
        for name in ('outputs','checkpoints','tls'): (shared/name).mkdir()
        (shared/'nginx.conf').write_text('provisioned')
        env=shared/'.env'
        env.write_text('PUBLIC_HTTPS_ORIGIN=https://demo.example\nCORS_ALLOWED_ORIGINS=["https://demo.example"]\n'
                       f'NGINX_TLS_DIRECTORY={shared}/tls\nNGINX_CONFIG={shared}/nginx.conf\n')
        env.chmod(0o600)
        incoming=root/'incoming';incoming.mkdir()
        with tarfile.open(incoming/f'{sha}.tar','w') as archive:
            for directory in ('infra','infra/federated'):
                item=tarfile.TarInfo(directory);item.type=tarfile.DIRTYPE;archive.addfile(item)

    def test_success_preserves_data_and_commits_pointer(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sha='a'*40;self.prepare(root,sha)
            with patch('deployment.remote_release.subprocess.run') as run, patch('deployment.remote_release.urlopen') as fetch:
                fetch.return_value.__enter__.return_value=io.StringIO(json.dumps({'status':'ok'}))
                result=deploy(root,sha,'staging')
            self.assertTrue(result['health_verified'])
            self.assertEqual((root/'current-release').read_text(),sha)
            self.assertEqual((root/'releases'/sha/'infra/federated/checkpoints').resolve(),root/'shared/checkpoints')
            self.assertEqual(run.call_count,2)

    def test_failed_health_rolls_back_without_advancing_pointer(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sha='b'*40;prior='a'*40;self.prepare(root,sha)
            (root/'current-release').write_text(prior)
            with patch('deployment.remote_release.subprocess.run') as run, patch('deployment.remote_release.urlopen',side_effect=OSError('offline')):
                with self.assertRaises(OSError): deploy(root,sha,'production')
            self.assertEqual((root/'current-release').read_text(),prior)
            self.assertEqual(run.call_count,4)
            self.assertIn(str(root/'releases'/prior/'infra/compose.yaml'),run.call_args_list[-1].args[0])
