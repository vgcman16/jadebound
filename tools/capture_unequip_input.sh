#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 60s godot --audio-driver Dummy --path game -- --unequip-review > builds/unequip-input-review.log 2>&1
