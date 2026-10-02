#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
# Fourteen deterministic in-engine frames, normal exit; one bounded graphics stage.
timeout 120s godot --audio-driver Dummy --max-fps 24 --path game -- --equipment-review > builds/equipment-capture.log 2>&1
