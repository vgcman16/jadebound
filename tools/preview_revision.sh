#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash tools/art_preview.sh
bash tools/hero_preview.sh
bash tools/capture.sh
