#!/usr/bin/env bash
# Process-local, offline MPFB authoring environment; never edits global preferences.
set -euo pipefail
cd "$(dirname "$0")/.."
export BLENDER_USER_RESOURCES="$PWD/local/mpfb-trial/resources"
export BLENDER_USER_CONFIG="$PWD/local/mpfb-trial/config"
export BLENDER_USER_SCRIPTS="$PWD/local/mpfb-trial/scripts"
export BLENDER_USER_EXTENSIONS="$PWD/local/mpfb-trial/extensions"
export BLENDER_USER_DATAFILES="$PWD/local/mpfb-trial/data"
export XDG_CACHE_HOME="$PWD/local/cache"
exec blender --background --offline-mode --threads 2 --python-exit-code 1 "$@"
