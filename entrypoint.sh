#!/bin/sh
set -eu
[ "$#" -eq 0 ] || { echo 'Extra arguments are not supported.' >&2; exit 64; }
python3 /usr/local/lib/pearl/validate.py
[ -x /opt/srb/SRBMiner-MULTI ] || { echo "Missing official SRBMiner-MULTI: mount your verified release read-only at /opt/srb." >&2; exit 66; }
# No eval, sourced user files, arbitrary miner arguments, API, clock or power writes.
exec /opt/srb/SRBMiner-MULTI \
  --disable-cpu --disable-msr-tweaks --disable-huge-pages \
  --disable-gpu-amd --disable-gpu-intel --gpu-disable-oc \
  --autotune-no-load --algorithm pearlhash \
  --pool "${POOL_HOST}:${POOL_PORT}" --tls true \
  --wallet "${PRL_WALLET}.${WORKER}" --password x
