#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
# 120 frames: actual native input handling, with labelled authoritative QA level advance.
timeout 120s godot --audio-driver Dummy --path game --fixed-fps 12 --quit-after 120 --write-movie "$PWD/builds/jadebound-mouse-first-input.avi" -- --input-demo > builds/native-input-demo.log 2>&1
