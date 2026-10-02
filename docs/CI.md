# Your own CI

The project is intentionally runner-independent and contains **no automatically triggered GitHub Actions workflow**. Public PRs must never execute on trusted personal machines or a privileged self-hosted runner.

For a trusted manual branch/revision:

1. Provision Godot 4.6.3 standard, Blender 4.3.2 or newer, Python 3 and Bash on an isolated Linux runner
2. Review and check out the exact trusted commit, without secrets or host mounts
3. Run `bash tools/validate.sh`
4. If loopback UDP is allowed, run `JADE_NETWORK_TEST=1 bash tools/validate.sh`
5. Optional regeneration: `timeout 120s blender --background --threads 2 --python tools/generate_assets.py -- --output "$PWD"`
6. Optional exports: install matching official Godot export templates, then export through Project → Export (automated export wrapper pending)
7. Retain build logs, checksums and artifacts; tear down the ephemeral workspace

The validator checks import/parse errors explicitly because an editor import can exit zero despite a script parse error. The network runner caps every process and terminates owned children on failure. No server remains behind after tests.

Windows: open `game/project.godot` in Godot 4.6.3 and press F6/F5. A Windows CI port may invoke the same Godot flags and Python runner; the Bash wrapper currently targets Linux. No runner enrollment or credentials are stored in this repository.

## Optional human-asset data audit

With Python 3.11+ and NumPy (tested:2.3.5), run `timeout 120s python3 tools/audit_human_uv.py`. It checks only included assets and writes `builds/human-uv-report.json`; it performs no rendering, networking or public CI dispatch. The authoring master is not yet integrated into the playable character.
