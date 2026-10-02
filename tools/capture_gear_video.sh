#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
# Genuine live scene and live equipment portrait; sequential authoritative slot swaps.
timeout 120s godot --audio-driver Dummy --path game --fixed-fps 12 --quit-after 72 --write-movie "$PWD/builds/jadebound-modular-equipment.avi" -- --gear-demo > builds/gear-video.log 2>&1
