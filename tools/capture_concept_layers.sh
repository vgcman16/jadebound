#!/usr/bin/env bash
# Finite actual-engine static gear-layer proof. Not gameplay/animation/FPS evidence.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds
export LP_NUM_THREADS=2
timeout 120s godot --audio-driver Dummy --path game --resolution 960x600 --fixed-fps 12 --write-movie "$PWD/builds/jadebound-body-gear-study.avi" --quit-after 72 --script res://tests/capture_concept_study.gd -- --layer-movie > builds/concept-layers-movie.log 2>&1
