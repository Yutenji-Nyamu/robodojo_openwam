#!/usr/bin/env bash
set -euo pipefail
gpu=$1
shift
case "$gpu" in 4|5|6|7) ;; *) exit 64 ;; esac
test "${1:-}" = -- && shift
export DOJO_GPU_SCOPE="$gpu"
scope_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export PYTHONPATH="$scope_dir${PYTHONPATH:+:$PYTHONPATH}"
exec "$@"
