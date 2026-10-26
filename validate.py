#!/usr/bin/env python3
"""Offline input validation only; no network and no miner execution."""
import os
import re
import sys

CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'

def valid_wallet(s):
    if not s.startswith('prl1') or s != s.lower() or not 14 <= len(s) <= 90:
        return False
    try:
        data = [CHARSET.index(c) for c in s[4:]]
    except ValueError:
        return False
    chk = 1
    for v in [ord(c) >> 5 for c in 'prl'] + [0] + [ord(c) & 31 for c in 'prl'] + data:
        top = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i, g in enumerate((0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)):
            if (top >> i) & 1:
                chk ^= g
    if not data or data[0] > 16 or chk != (1 if data[0] == 0 else 0x2bc830a3):
        return False
    acc = bits = 0
    decoded = []
    for v in data[1:-6]:
        acc = (acc << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            decoded.append((acc >> bits) & 255)
    return (bits < 5 and ((acc << (8-bits)) & 255) == 0
            and 2 <= len(decoded) <= 40
            and (data[0] != 0 or len(decoded) in (20, 32)))

def validate(env):
    if env.get('MINING_ACK') != 'I_OWN_OR_AM_AUTHORIZED_TO_USE_THIS_GPU':
        raise ValueError('MINING_ACK: explicit hardware authorization acknowledgment required')
    if not valid_wallet(env.get('PRL_WALLET', '')):
        raise ValueError('PRL_WALLET: valid lowercase prl1 public receive address required; never use a seed/private key')
    if not re.fullmatch(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', env.get('GPU_UUID', '')):
        raise ValueError('GPU_UUID: one full GPU UUID required (not all/index/placeholder)')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,31}', env.get('WORKER', '')):
        raise ValueError('WORKER: 1-32 letters/digits/underscore/hyphen required')
    host = env.get('POOL_HOST', '')
    if (len(host) > 253 or '.' not in host or host.endswith(('.invalid', '.example', '.test'))
        or any(not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', p) for p in host.split('.'))):
        raise ValueError('POOL_HOST: real DNS hostname required, no scheme/port/options')
    port = env.get('POOL_PORT', '')
    if not re.fullmatch(r'[1-9][0-9]{0,4}', port) or int(port) > 65535:
        raise ValueError('POOL_PORT: 1-65535 required; confirm the pool TLS port')

if __name__ == '__main__':
    try:
        validate(os.environ)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(64)
