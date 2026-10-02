#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 120s godot --audio-driver Dummy --path game -- --art-redesign-review > builds/art-redesign-review.log 2>&1
