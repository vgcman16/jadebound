#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 90s godot --audio-driver Dummy --path game -- --controls-review > builds/controls-review.log 2>&1
