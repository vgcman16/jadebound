#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 90s godot --audio-driver Dummy --max-fps 24 --path game -- --hero-closeup --stop-after=7 --screenshot="$PWD/builds/jadebound-hero-closeup.png" > builds/hero-preview.log 2>&1
