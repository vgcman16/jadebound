#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 120s godot --audio-driver Dummy --path game --fixed-fps 12 --quit-after 72 --write-movie "$PWD/builds/jadebound-super-weapon.avi" -- --super-demo > builds/super-video.log 2>&1
