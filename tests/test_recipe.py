#!/usr/bin/env python3
"""Only executes a locally created argv-printing mock, NEVER a miner."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
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
            GPU_UUID='GPU-11111111-2222-3333-4444-555555555555', WORKER='test01',
            POOL_HOST='pool.test.example.org', POOL_PORT='8048')

class Tests(unittest.TestCase):
    def test_valid(self):
        v.validate(BASE)
    def test_reject_bad_inputs(self):
        bad = {'MINING_ACK':['','yes'], 'PRL_WALLET':['','REPLACE',BASE['PRL_WALLET'][:-1]+'q','seed words here',BASE['PRL_WALLET']+';x'],
               'GPU_UUID':['all','0','GPU-REPLACE',''], 'WORKER':['a;b','$(id)','a b','-x','x'*33],
               'POOL_HOST':['choose-your-pool.invalid','ssl://pool.org','pool.org:8048','a,b.org','-bad.org'],
               'POOL_PORT':['0','65536','8048;id','-1','']}
        for key, values in bad.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    v.validate(dict(BASE, **{key:value}))
    def test_mock_entrypoint(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            mock = d/'mock'
            mock.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
            mock.chmod(0o755)
            entry = d/'entrypoint.sh'
            entry.write_text((ROOT/'entrypoint.sh').read_text().replace('/usr/local/lib/pearl/validate.py',str(ROOT/'validate.py')).replace('/opt/srb/SRBMiner-MULTI',str(mock)))
            env = dict(os.environ, **BASE)
            result = subprocess.run(['sh',str(entry)],env=env,text=True,capture_output=True,check=True)
            args = result.stdout.splitlines()
            self.assertEqual(args[args.index('--algorithm')+1],'pearlhash')
            self.assertEqual(args[args.index('--tls')+1],'true')
            self.assertEqual(args[args.index('--wallet')+1],BASE['PRL_WALLET']+'.test01')
            self.assertIn('--disable-cpu',args)
            self.assertIn('--gpu-disable-oc',args)
            self.assertNotIn('--api-enable',args)
            for extra, changes in [(['--help'],{}),([] ,{'PRL_WALLET':'bad'}),([] ,{'GPU_UUID':'all'})]:
                r = subprocess.run(['sh',str(entry)]+extra,env=dict(env,**changes),text=True,capture_output=True)
                self.assertEqual(r.returncode,64)
                self.assertEqual(r.stdout,'')
    def test_static_safety(self):
        compose = (ROOT/'compose.yaml').read_text()
        for forbidden in ['privileged:', 'network_mode:', 'ports:', 'count:', '/var/run/docker.sock']:
            self.assertNotIn(forbidden,compose)
        for required in ['init: true','restart: "no"','read_only: true','cap_drop: [ALL]','no-new-privileges:true','compute,utility','device_ids:']:
            self.assertIn(required,compose)
        docker = (ROOT/'Dockerfile.private').read_text()
        self.assertIn('sha256sum -c -',docker)
        self.assertIn('md5sum -c -',docker)
        self.assertNotIn('RUN /opt/srb',docker)
        public = (ROOT/'Dockerfile').read_text()
        self.assertNotIn('COPY --from=unpack', public)
        self.assertNotIn('vendor/', public)
        self.assertIn('create_host_path: false', compose)
        self.assertIn('target: /opt/srb', compose)
        self.assertNotIn('/.dockerenv',(ROOT/'entrypoint.sh').read_text())

if __name__ == '__main__':
    unittest.main(verbosity=2)
