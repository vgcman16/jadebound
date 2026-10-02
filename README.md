# JADEBOUND
### Ashes of Lantern Vale

An original isometric martial-fantasy action RPG prototype, inspired by the broad adventure/loot/control loop of classic online RPGs. The setting, character concepts, gameplay code and current runtime artwork were created for this project. A separate, unintegrated continuous-body character study uses verified MakeHuman core CC0 assets with explicit provenance and original removable clothing/armor. It is not affiliated with Conquer Online.

## Play

Install **Godot 4.6.3 standard**, import `game/project.godot`, and press F6/F5. For a fresh command-line checkout, first run `godot --headless --path game --editor --import`, then `godot --path game`. The original models are already included; Blender is needed only to regenerate/edit art.

- Left-click ground to move; click foes, drops or Suri to approach and act
- Ctrl+left-click: vault; right-click: cast the selected skill
- F1–F10: configurable skills/items; initial slots are Cut, Arc, Threadstrike, Vault, Flask, Gather
- Optional WASD; Tab live gear; E interact; Space vault; C/V/B cycle owned gear
- F11 realm/save/load/remapping; F12 guide; Esc closes overlays or opens the menu
- In the gear panel: left-click cycles owned gear; right-click removes it
- See [complete controls](docs/CONTROLS.md) and [removable-gear status](docs/REMOVABLE_GEAR.md)

Speak to Keeper Suri, fight the Ashen marauders, collect five ember seals, then return to earn Dawnsteel. Nearby Suri restores vitality. Defeat returns you safely to the shrine.

## Multiplayer prototype

Run `godot --headless --path game -- --server` for a loopback-only server on UDP 27841. Open two clients and use F11 → Join realm, address `127.0.0.1`. The server controls movement, combat, health, loot and quest rewards. No accounts or permanent online progression yet.

An explicit trusted-LAN bind is available through `--server --bind=YOUR_LAN_IP`. This is not hardened for public Internet hosting. Read [architecture and limitations](docs/ARCHITECTURE.md).

## Build and validate

- `bash tools/validate.sh`: bounded import and gameplay-rule tests
- `JADE_NETWORK_TEST=1 bash tools/validate.sh`: additionally test server plus two loopback clients
- `blender --background --threads 2 --python tools/generate_assets.py -- --output .`: regenerate 10 GLBs and the editable Blender library
- [Own-CI instructions](docs/CI.md); no automatic hosted or untrusted-PR jobs

## Status

First playable prototype built on dot's cloud computer with Godot 4.6.3 and Blender 4.3.2. Original low-poly village/field, animated characters, melee/qi skills, jumping, enemies, loot, inventory, quest rewards, levels, death/respawn, offline saves, and staged server-authoritative multiplayer are implemented.

The modular hero has a native 22-bone rig, six clips, two independently mixable armor/head/weapon kits, and a live in-game equipment portrait. The hero uses original UV-authored albedo/normal/roughness maps; Warden now has a construction-aware atlas with plate borders, an original reed motif, cloth folds and leather wear. Two distinct weapon attack clips and clean equipment swaps have been inspected in actual engine movies; contact-timed server damage/effects align with the weapon pose. A connected, original stone courtyard and neutral/material-only inspection scenes are included. Hero materials and stone faces have received a targeted study, but broad plate surfaces, cloth, faces, old enemies and the wider environment still fall short of the intended commercial reference finish. These are limited art studies, not final-production art.

The replacement River Warden study keeps a continuous adult body under separate outfit, boot and glove meshes, with permanent underwear and reversible body-region visibility on a 53-bone rig. Its saved native clay views establish a better proportion and layering direction; they do not establish finished materials or animated removal coverage. The latest underwear clearance correction still needs fresh native visual verification. A separate [validated UV master](art/river-warden-uv/README.md) now passes exported geometry/skin/bind, overlap, padding and hair-flow checks. Outfit/hair surface painting remains the next step. See [the study guide](art/CONCEPT_WARDEN_GUIDE.md) and [surfacing status](art/CONCEPT_SURFACING_PLAN.md). This study is not yet the playable hero, and boots/gloves are not yet eligible live equipment items.

Level/class/base-attribute/weapon-proficiency/skill-mastery gates are server-owned. The catalog separates 36 design targets from seven available item IDs and six distinct gear meshes; unavailable classes/assets fail closed. The compact original slice uses level bands 1/3/6. [Progression details](docs/PROGRESSION_CATALOG.md).

The current local validator passes 392 assertions plus ten original-asset contracts. A dedicated server and two loopback clients passed bounded connectivity/state tests. Actual mouse-first UI verification is recorded separately in [test status](docs/TEST_STATUS.md). These tests do not establish MMO-scale readiness or public-server security.

See [engine decision](docs/ENGINE_DECISION.md), [art guide](art/ASSET_GUIDE.md), [architecture](docs/ARCHITECTURE.md) and [provenance/licensing](THIRD_PARTY_NOTICES.md).

See [visible equipment](docs/EQUIPMENT.md) and [modular hero source](art/MODULAR_HERO_GUIDE.md). Standalone platform exports are not bundled yet; the native project runs in the installed Godot engine.
