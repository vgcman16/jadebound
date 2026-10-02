#!/usr/bin/env bash
# Run on a trusted runner with Godot 4.6.3; no credentials or online service needed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p builds local/{cache,data,config}
export XDG_CACHE_HOME="$PWD/local/cache" XDG_DATA_HOME="$PWD/local/data" XDG_CONFIG_HOME="$PWD/local/config"
timeout 90s godot --headless --path game --editor --import > builds/import.log 2>&1
if grep -E 'SCRIPT ERROR|ERROR:' builds/import.log; then exit 1; fi
timeout 30s godot --headless --path game --script res://tests/test_world.gd | tee builds/world-test.log
grep -q 'JADE_WORLD_TESTS_PASSED' builds/world-test.log
timeout 30s godot --headless --path game --script res://tests/test_equipment.gd | tee builds/equipment-test.log
grep -q 'JADE_EQUIPMENT_TESTS_PASSED' builds/equipment-test.log
for test in progression_catalog progression_integration controls appearance_coverage; do
  timeout 30s godot --headless --path game --script "res://tests/test_${test}.gd" | tee "builds/${test}-test.log"
  if grep -E "SCRIPT ERROR|FAIL" "builds/${test}-test.log"; then exit 1; fi
  grep -q "PASSED" "builds/${test}-test.log"
done
python3 -m py_compile tools/generate_assets.py tools/generate_modular_hero.py tools/test_network.py tools/test_asset_contract.py
python3 tools/test_asset_contract.py
if [[ -f game/assets/models/hero_modular.glb ]]; then
  timeout 30s godot --headless --path game --script res://tests/test_modular_visuals.gd | tee builds/modular-contract.log
  grep -q "JADE_MODULAR_VISUAL_CONTRACT_PASSED" builds/modular-contract.log
fi
# Explicit opt-in for loopback sockets in locked-down CI.
if [[ "${JADE_NETWORK_TEST:-0}" == 1 ]]; then timeout 30s python3 tools/test_network.py; fi
