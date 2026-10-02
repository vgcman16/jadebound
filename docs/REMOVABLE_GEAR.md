# Removable equipment: implementation boundary

## Playable prototype

Armor, headgear and weapon removal use the same sender-bound, server-validated equipment request as equip. Right-click an equipment-panel slot to remove its item; left-click cycles owned items. Removing an item keeps ownership, removes its stat contribution, clamps current health if maximum health falls, and never heals the player. Cooldown, death and active-strike locks apply. Weapon skills require a compatible equipped weapon; vaulting does not. Removing a Super weapon clears its local glow and particles.

The server state now has five independent slot keys: `armor`, `head`, `weapon`, `boots`, `gloves`. The last two remain empty and unavailable in the old playable model. Adding slot names does not make unfinished accessories eligible. The current live UI exposes the three supported visual slots.

The current playable hero's underlying body is the old clothed prototype. Its built-in footwear cannot yet be separately stripped. Do not confuse it with the new art study below.

## Separate continuous-body art study

`art/concept-warden/` uses a CC0-derived adult body with original separate armor/clothing, boot and fingerless-glove meshes on one 53-bone rig. It is not yet the live gameplay hero. Head armor, weapon and gameplay animation are not included in this study.

`Body_Underwear` is permanent base clothing and is never an equipment slot. The full authoring anatomy remains intact. Exported regional body meshes preserve the original face coverage, skin weights and UVs. `appearance_coverage.gd` restores covered regions on unequip; it only hides a region when the corresponding equipment mesh actually exists and is visible. A missing asset must not erase a body part. Headgear removal restores the base hairstyle.

The native visual fixture captures independent armor/boots/gloves removal and restoration. This tests mesh separation and reversible coverage; it does not establish server eligibility for the unintegrated accessories or full-cycle motion clearance. The fixture is labelled in its actual rendered frames.

## Release gates still open

- Finish underwear/garment clearance, material quality and motion review
- Integrate the accepted new body, optimized slot meshes and compatible clips into gameplay
- Add the two actual accessory item definitions with server-owned level/class/stat gates
- Expose five supported live UI slots and verify native equip/unequip input
- Test removal/re-equip during idle, running, vaulting, attack recovery, death and respawn

No client-provided stats, item ownership or level claims are accepted.
