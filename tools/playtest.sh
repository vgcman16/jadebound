#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")/.."
exec timeout 90s godot --path game -- --stop-after=30 --screenshot="$PWD/builds/jadebound-town.png" > builds/visual-test.log 2>&1
