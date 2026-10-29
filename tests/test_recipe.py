#!/usr/bin/env python3
"""Only executes a locally created argv-printing mock, NEVER a miner."""
import importlib.util
import hashlib
import io
import sys
import tarfile
from unittest import mock
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import bootstrap as b
spec = importlib.util.spec_from_file_location('validator', ROOT/'validate.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

# Synthetic witness address: not a user's wallet and never used on a network.
def synthetic_address():
    data = [1] + [0] * 51 + [0]  # 32 zero bytes in 5-bit groups
    values = [3, 3, 3, 0, 16, 18, 12] + data + [0]*6
    polymod = 1
    for value in values:
        b = polymod >> 25
        polymod = ((polymod & 0x1ffffff) << 5) ^ value
        for i, g in enumerate([0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]):
            if b >> i & 1:
                polymod ^= g
    polymod ^= 0x2bc830a3
    return 'prl1' + ''.join(v.CHARSET[d] for d in data + [(polymod >> 5*(5-i)) & 31 for i in range(6)])

BASE = dict(MINING_ACK='I_OWN_OR_AM_AUTHORIZED_TO_USE_THIS_GPU', PRL_WALLET=synthetic_address(),
            NVIDIA_VISIBLE_DEVICES='GPU-11111111-2222-3333-4444-555555555555', GPU_UUID='GPU-11111111-2222-3333-4444-555555555555', WORKER='test01',
            POOL_HOST='pool.test.example.org', POOL_PORT='8048')

class Tests(unittest.TestCase):
    def test_valid(self):
        v.validate(BASE)
    def test_reject_bad_inputs(self):
        bad = {'PRL_WALLET':['','REPLACE',BASE['PRL_WALLET'][:-1]+'q','seed words here',BASE['PRL_WALLET']+';x'],
               'NVIDIA_VISIBLE_DEVICES':['all','','GPU-other'], 'GPU_UUID':['all','0','GPU-REPLACE',''], 'WORKER':['a;b','$(id)','a b','-x','x'*33],
               'POOL_HOST':['choose-your-pool.invalid','ssl://pool.org','pool.org:8048','a,b.org','-bad.org'],
               'POOL_PORT':['0','65536','8048;id','-1','']}
        for key, values in bad.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    v.validate(dict(BASE, **{key:value}))
    def test_mock_entrypoint(self):
        with tempfile.TemporaryDirectory() as d:
            binary = Path(d)/'SRBMiner-MULTI'
            binary.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            binary.chmod(0o700)
            # Replace preparation only in an isolated Python harness. No real miner/network.
            harness = ('import bootstrap as b; from pathlib import Path; '
                       + 'b.prepare=lambda:Path(' + repr(str(binary)) + '); b.main()')
            env = dict(os.environ, **BASE, PYTHONPATH=str(ROOT))
            env.pop('POOL_HOST'); env.pop('POOL_PORT')
            r = subprocess.run([sys.executable,'-c',harness],env=env,text=True,capture_output=True,check=True)
            args = r.stdout.splitlines()
            self.assertEqual(args[args.index('--pool')+1], 'prl.kryptex.network:8048')
            self.assertEqual(args[args.index('--wallet')+1], BASE['PRL_WALLET']+'.test01')
            self.assertIn('--disable-cpu',args)
            self.assertIn('--gpu-disable-oc',args)
            self.assertNotIn('--api-enable',args)
            self.assertNotIn('--gpu-power-tuner',args)
            self.assertNotIn('--gpu-power-tuner-loss',args)

    def archive(self, path, unsafe=None):
        with tarfile.open(path, 'w:gz') as tar:
            for name, content in [('SRBMiner-MULTI',b'#!/bin/sh\nexit 0\n'),('ReadMe.txt',b'mock license')]:
                info = tarfile.TarInfo(b.RELEASE+'/'+name)
                info.mode = 0o755
                info.size = len(content)
                tar.addfile(info,io.BytesIO(content))
            if unsafe:
                info = tarfile.TarInfo(unsafe)
                if 'link' in unsafe:
                    info.type = tarfile.SYMTYPE
                    info.linkname = '/tmp/escape'
                tar.addfile(info)

    def test_download_cache_and_recheck(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); fixture=root/'mock.tar.gz'; self.archive(fixture)
            def fake_download(p): p.write_bytes(fixture.read_bytes())
            with mock.patch.object(b,'SHA256',b.digest(fixture)), mock.patch.object(b,'download',side_effect=fake_download) as dl:
                binary=b.prepare(root/'cache',root)
                self.assertEqual(binary.parent.name,b.RELEASE)
                self.assertEqual(dl.call_count,1)
                binary.write_text('tampered extracted binary')
                other=b.prepare(root/'cache',root)
                self.assertNotEqual(other.read_text(),binary.read_text())
                self.assertEqual(dl.call_count,1)
                (root/'cache'/('srb-' + b.VERSION + '.tar.gz')).write_bytes(b'corrupt')
                with self.assertRaises(ValueError): b.prepare(root/'cache',root)

    def test_bad_download(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(b,'download',side_effect=lambda p:p.write_bytes(b'bad')):
            with self.assertRaises(ValueError): b.prepare(Path(d))
            self.assertFalse((Path(d)/('srb-' + b.VERSION + '.tar.gz')).exists())

    def test_unsafe_archives(self):
        for bad in ['../escape','/tmp/escape',b.RELEASE+'/../escape',b.RELEASE+'/link']:
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as d:
                root=Path(d); fixture=root/'mock.tar.gz'; self.archive(fixture,bad)
                with self.assertRaises(ValueError): b.unpack(fixture,root/'out')

    def test_invalid_config_never_downloads(self):
        with mock.patch.dict(os.environ,{'PRL_WALLET':'bad'},clear=True), mock.patch.object(sys,'argv',['bootstrap.py']), mock.patch.object(b,'prepare') as prep:
            with self.assertRaises(ValueError): b.main()
            prep.assert_not_called()

    def test_static_safety(self):
        compose = (ROOT/'compose.yaml').read_text()
        for forbidden in ['privileged:', 'network_mode:', 'ports:', 'count:', '/var/run/docker.sock']:
            self.assertNotIn(forbidden,compose)
        for required in ['init: true','restart: "no"','read_only: true','cap_drop: [ALL]','no-new-privileges:true','compute,utility','device_ids:']:
            self.assertIn(required,compose)
        public = (ROOT/'Dockerfile').read_text()
        self.assertNotIn('COPY --from=unpack', public)
        self.assertNotIn('vendor/', public)
        self.assertIn('COPY bootstrap.py validate.py /usr/local/lib/pearl/\n', public)
        self.assertIn('miner-cache:/var/cache/pearl', compose)
        self.assertNotIn('build:', compose)
        self.assertNotIn('/.dockerenv',(ROOT/'entrypoint.sh').read_text())

    def test_release_pins_and_publish_tags(self):
        self.assertEqual(b.VERSION, '3.8.1')
        self.assertEqual(b.RELEASE, 'SRBMiner-Multi-3-8-1')
        self.assertEqual(b.URL, 'https://github.com/doktor83/SRBMiner-Multi/releases/download/3.8.1/SRBMiner-Multi-3-8-1-Linux.tar.gz')
        self.assertEqual(b.SHA256, '2f65b3b7f7781def46610c43b8a10a3d38033f6cf4ef6cc968b405ca9b0ce807')
        compose = (ROOT/'compose.yaml').read_text()
        self.assertIn('image: ghcr.io/tourshein/pearl-srb-docker:bootstrap-3.8.1', compose)
        workflow = (ROOT/'.github/workflows/runtime-image.yml').read_text()
        self.assertIn('docker push "$IMAGE:bootstrap-3.8.1"', workflow)
        self.assertNotIn('bootstrap-3.8.0', workflow)
        self.assertNotIn(':latest', workflow)

    def test_upgrade_preserves_rollback_cache(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            cache = root/'cache'
            cache.mkdir()
            old = cache/'srb-3.8.0.tar.gz'
            old.write_bytes(b'previous version cache must remain untouched')
            fixture = root/'mock.tar.gz'
            self.archive(fixture)
            with mock.patch.object(b, 'SHA256', b.digest(fixture)), mock.patch.object(b, 'download', side_effect=lambda p:p.write_bytes(fixture.read_bytes())):
                binary = b.prepare(cache, root)
            self.assertEqual(binary.parent.name, b.RELEASE)
            self.assertEqual(old.read_bytes(), b'previous version cache must remain untouched')
            self.assertTrue((cache/'srb-3.8.1.tar.gz').is_file())

    def test_environment_cannot_override_release(self):
        env = dict(os.environ, VERSION='0.0.0', URL='https://example.org/other', SHA256='0'*64, PYTHONPATH=str(ROOT))
        result = subprocess.run([sys.executable, '-c',
            'import bootstrap as b; print(b.VERSION); print(b.URL); print(b.SHA256)'],
            env=env, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(), [b.VERSION, b.URL, b.SHA256])

if __name__ == '__main__':
    unittest.main(verbosity=2)

