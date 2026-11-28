#!/usr/bin/env bash
# Build storopoli.com via the stdlib-only Python orchestrator.
set -euo pipefail

exec python3 "$(dirname "$0")/build.py" "$@"
