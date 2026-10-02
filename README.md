# JADEBOUND
### Ashes of Lantern Vale

An original isometric martial-fantasy action RPG prototype, inspired by the broad adventure/loot/control loop of classic online RPGs. All characters, setting, game assets and code are original. It is not affiliated with Conquer Online.

## Play

Install **Godot 4.6.3 standard**, import `game/project.godot`, and press F6/F5. For a fresh command-line checkout, first run `godot --headless --path game --editor --import`, then `godot --path game`. The original models are already included; Blender is needed only to regenerate/edit art.

- WASD or left-click ground: move; mouse wheel: zoom
- Click an enemy: approach and auto-attack; right-click or 1: slash toward cursor
- Q: Jade Arc, a qi-powered radial strike
- R: Threadstrike, a manually aimed piercing line
- Space or Ctrl+click: Sky Vault toward cursor
- E: talk / gather nearby drops; H: healing flask
- Tab: live equipment portrait/satchel; C/V/B: cycle owned armor/headgear/weapon
- F1: realm menu; F2: guide; Esc: close overlay / quit
- F5: save offline progress; F9: restore offline progress at the village

Speak to Keeper Suri, fight the Ashen marauders, collect five ember seals, then return to earn Dawnsteel. Nearby Suri restores vitality. Defeat returns you safely to the shrine.

## Multiplayer prototype

Run `godot --headless --path game -- --server` for a loopback-only server on UDP 27841. Open two clients and use F1 → Join realm, address `127.0.0.1`. The server controls movement, combat, health, loot and quest rewards. No accounts or permanent online progression yet.

An explicit trusted-LAN bind is available through `--server --bind=YOUR_LAN_IP`. This is not hardened for public Internet hosting. Read [architecture and limitations](docs/ARCHITECTURE.md).

## Build and validate

- `bash tools/validate.sh`: bounded import and gameplay-rule tests
- `JADE_NETWORK_TEST=1 bash tools/validate.sh`: additionally test server plus two loopback clients
- `blender --background --threads 2 --python tools/generate_assets.py -- --output .`: regenerate 10 GLBs and the editable Blender library
- [Own-CI instructions](docs/CI.md); no automatic hosted or untrusted-PR jobs

## Status

First playable prototype built on dot's cloud computer with Godot 4.6.3 and Blender 4.3.2. Original low-poly village/field, animated characters, melee/qi skills, jumping, enemies, loot, inventory, quest rewards, levels, death/respawn, offline saves, and staged server-authoritative multiplayer are implemented.

20 world assertions, 20 equipment/ownership/stat assertions and 27 native skin/slot/effect contract assertions pass. Godot import and native scene rendering pass. A first visual revision adds slate-tiled architecture, a tailored topknot hero, layered cherry foliage, natural ground, an irregular stone lane and a compact HUD. The new skinned modular hero supports two independently mixable armor/head/weapon kits and a live in-game equipment portrait. Material painting and stronger attack/landing animation remain work in progress; the current exported hero has three roughness maps, not painted albedo/normal maps. Loopback integration validation and standalone exports are documented separately as they complete. No claim of MMO-scale readiness is made.

See [engine decision](docs/ENGINE_DECISION.md), [art guide](art/ASSET_GUIDE.md), [architecture](docs/ARCHITECTURE.md) and [provenance/licensing](THIRD_PARTY_NOTICES.md).

See [visible equipment](docs/EQUIPMENT.md) and [modular hero source](art/MODULAR_HERO_GUIDE.md). Standalone platform exports are not bundled yet; the native project runs in the installed Godot engine.
