#!/usr/bin/env python3
"""Download only the pinned upstream archive; never accept user-supplied code URLs."""
import fcntl
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from validate import validate

VERSION = '3.8.0'
RELEASE = 'SRBMiner-Multi-3-8-0'
URL = 'https://github.com/doktor83/SRBMiner-Multi/releases/download/3.8.0/SRBMiner-Multi-3-8-0-Linux.tar.gz'
SHA256 = '095c3f75905ee023e8ed85ac905afefc92825cce83a528fa955cf1db456d3dd8'
CACHE = Path('/var/cache/pearl')
MAX_BYTES = 128 * 1024 * 1024


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else stream_digest(f)


def stream_digest(f):
    h = hashlib.sha256()
    for chunk in iter(lambda: f.read(1024 * 1024), b''):
        h.update(chunk)
    return h.hexdigest()


def download(destination):
    with urllib.request.urlopen(URL, timeout=60) as response, destination.open('xb') as out:
        if not response.url.startswith('https://'):
            raise ValueError('Download redirect must use HTTPS')
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError('Archive exceeds size limit')
            out.write(chunk)


def unpack(archive, destination):
    """Reject links, special files, duplicates, traversal and oversized archives."""
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        seen = set()
        total = 0
        for m in members:
            p = PurePosixPath(m.name)
            if (p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != RELEASE
                    or str(p) in seen or not (m.isdir() or m.isfile())):
                raise ValueError('Unsafe archive member: ' + m.name)
            seen.add(str(p))
            total += m.size
            if total > MAX_BYTES or len(seen) > 4096:
                raise ValueError('Expanded archive exceeds limit')
        for m in members:
            target = destination.joinpath(*PurePosixPath(m.name).parts)
            if m.isdir():
                target.mkdir(parents=True, exist_ok=True, mode=0o700)
            else:
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with tar.extractfile(m) as source, target.open('xb') as out:
                    shutil.copyfileobj(source, out)
                target.chmod(0o700 if m.mode & 0o111 else 0o600)
    binary = destination / RELEASE / 'SRBMiner-MULTI'
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError('Release lacks executable SRBMiner-MULTI')
    if not (destination / RELEASE / 'ReadMe.txt').is_file():
        raise ValueError('Release lacks upstream ReadMe/license')
    return binary


def prepare(cache=CACHE, execution_dir=Path('/run/pearl')):
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    if cache.is_symlink():
        raise ValueError('Cache must not be a symlink')
    lock = cache / '.lock'
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX)
        archive = cache / ('srb-' + VERSION + '.tar.gz')
        if archive.is_symlink():
            raise ValueError('Archive cache must not be a symlink')
        if not archive.exists():
            print('Downloading original SRBMiner 3.8.0; verifying pinned SHA256 before execution.', flush=True)
            with tempfile.TemporaryDirectory(prefix='download-', dir=cache) as tmp:
                candidate = Path(tmp) / 'archive'
                download(candidate)
                if digest(candidate) != SHA256:
                    raise ValueError('Downloaded archive SHA256 mismatch; refusing execution')
                candidate.replace(archive)
        if not archive.is_file() or digest(archive) != SHA256:
            raise ValueError('Cached archive SHA256 mismatch; refusing execution. Remove only the dedicated cache volume to retry.')
        # Fresh extraction prevents trusting a previously modified executable or library.
        # /run/pearl is a bounded private executable tmpfs, never a NAS share.
        tmp = Path(tempfile.mkdtemp(prefix='release-', dir=execution_dir))
        try:
            return unpack(archive, tmp)
        except Exception:
            shutil.rmtree(tmp)
            raise


def main():
    if len(sys.argv) != 1:
        raise ValueError('Extra arguments are not supported')
    env = os.environ
    env.setdefault('WORKER', 'pearl01')
    env.setdefault('POOL_HOST', 'prl.kryptex.network')
    env.setdefault('POOL_PORT', '8048')
    validate(env)  # Before all network/filesystem preparation.
    binary = prepare()
    os.chdir(binary.parent)  # Preserve upstream relative-path behavior.
    args = [str(binary), '--disable-cpu', '--disable-msr-tweaks', '--disable-huge-pages',
            '--disable-gpu-amd', '--disable-gpu-intel', '--gpu-disable-oc', '--autotune-no-load',
            '--algorithm', 'pearlhash', '--pool', env['POOL_HOST'] + ':' + env['POOL_PORT'],
            '--tls', 'true', '--wallet', env['PRL_WALLET'] + '.' + env['WORKER'], '--password', 'x']
    os.execv(str(binary), args)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, tarfile.TarError) as e:
        print('Startup refused: ' + str(e), file=sys.stderr)
        sys.exit(64)
