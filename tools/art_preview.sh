#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 90s godot --audio-driver Dummy --max-fps 24 --path game -- --stop-after=8 --screenshot="$PWD/builds/jadebound-art-after.png" > builds/art-preview.log 2>&1
