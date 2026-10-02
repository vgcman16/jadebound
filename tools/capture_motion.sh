#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
# 72 actual in-engine frames with ordinary authoritative movement/action/equip inputs.
timeout 120s godot --audio-driver Dummy --path game --fixed-fps 12 --quit-after 72 --write-movie "$PWD/builds/jadebound-modular-motion.avi" -- --motion-demo > builds/modular-motion.log 2>&1
