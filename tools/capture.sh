#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
# 72 finite rendered frames: actual gameplay with clearly labelled automated input.
# Normal engine exit finalizes the AVI; timeout is only an outer safety bound.
timeout 90s godot --audio-driver Dummy --path game --fixed-fps 12 --quit-after 72 --write-movie "$PWD/builds/jadebound-visual-revision.avi" -- --demo --quick-demo > builds/capture-revision.log 2>&1
