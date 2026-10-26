# Public bootstrap image: contains NO SRBMiner archive or binary.
FROM nvidia/cuda:12.9.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libnuma1 libcurl4 libssl3 ocl-icd-libopencl1 python3 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --uid 10001 --create-home miner
RUN mkdir -p /var/cache/pearl /run/pearl && chown 10001:10001 /var/cache/pearl /run/pearl
COPY bootstrap.py validate.py /usr/local/lib/pearl/
COPY --chmod=0555 entrypoint.sh /usr/local/bin/pearl-entrypoint
ENV HOME=/tmp NVIDIA_DRIVER_CAPABILITIES=compute,utility
USER 10001:10001
WORKDIR /tmp
ENTRYPOINT ["/usr/local/bin/pearl-entrypoint"]
