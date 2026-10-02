# Jadebound modular hero

Original authored geometry, surface textures, skeleton and animation. No reference image, game asset, copied model or downloaded texture is packaged.

## Source and export

- Editable source: `tools/generate_modular_hero.py`
- Editable Blender scene: `art/jadebound_modular_hero.blend`
- Runtime: `game/assets/models/hero_modular.glb`
- Generate with Blender 4.3+: `blender --background --threads 2 --python tools/generate_modular_hero.py -- --output .`
- Optional `--render` creates two neutral-studio authoring previews in `builds/`

The script starts from an empty scene. It does not modify the previous art library or previous hero. Export occurs before preview-only lights/camera are added. UVs and packed original micrograin roughness textures are embedded in GLB and Blender. Palette hex colors are converted from sRGB to linear before shader assignment. Cloth, leather, enamel and forged metal use separate materials and roughness.

## Runtime contract

Root is `HeroModular`; armature object is `JadeboundRig`. The always-visible shared skinned mesh is `Body_Base`. Each following name is a single batched skinned mesh, not an empty visibility container. Match the mesh name or prefix if Godot adds import suffixes.

| Slot | Option A | Option B |
|---|---|---|
| Armor | `Gear_Wayfarer` | `Gear_Warden` |
| Head | `Head_Topknot` | `Head_Warden` |
| Weapon | `Weapon_Saber` | `Weapon_Glaive` |

Set exactly one mesh visible for each independent slot. All combinations share the same adult body and bind skeleton. Export includes every option. The saved Blender scene shows wayfarer/topknot/saber by default for authoring; runtime must set visibility from authoritative equipment immediately on load.

`Saber_FX` and `Glaive_FX` are bone-parented marker nodes at the held weapon grip, with custom `visibility_owner` properties naming the corresponding weapon. They are siblings under the rig rather than descendants of the skinned slot mesh; runtime must explicitly hide optional attached effects on swap. There are no particle systems, glows, auras, rings or persistent effect meshes in this asset.

For later weapon-quality effects, only materials with `Steel` or `Blade` in the name identify forged blade surfaces. `Old gold`, grip/leather, ribbons and wood are separate. The base weapons have zero emission. Keep armor/head/weapon visibility independent from any cosmetic/purification systems.

## Anatomy and skinning

Adult skull height is 1.834 m; approximately 7.1 head lengths. Topknot and helmet crest extend above that. The body has shaped ribcage, waist and pelvis; articulated upper/lower arms and legs; tapered wrists/ankles; shaped boot toe/instep; modeled nose, lips, ears and brows. The jacket and armor follow the torso rather than forming a box. Wayfarer has split long teal cloth, ivory lapels and asymmetric shoulder protection. Warden has short red-lined tassets, charcoal overlapping lamellar, broad curved shoulder lames and plated shins.

All seven batched meshes use armature modifiers and normalized vertex groups. No limb relies on an animated empty pivot. Vertices are authored in world-rest coordinates with identity mesh transforms; inverse bind matrices come from the native glTF skin exporter. Cloth skirt panels have two supplementary coat bones and smoothly blended hip/coat weights. Wrist/head props are fully weighted to their owning hand/head bone.

## Animation

- `idle`: grounded breath and restrained joint motion; loop
- `walk`: alternating hip and shoulder rotation, bent knees/elbows and coat response; loop
- `run`: larger stride and knee recovery; loop
- `attack`: windup, contact and recovery; one-shot
- `jump`: crouch, tuck and landing articulation; one-shot

All animation is in place. Gameplay owns horizontal travel and the jump arc. The tiny hip crouch/bob is deformation, not sustained root travel. Match clip names without requiring a rig-name prefix. Runtime may retime attack to its authoritative state duration.

## Validation

The generator checks GLB header, all exact slot node names, the always-visible body, exported skins/joints, inverse bind matrices, per-primitive UV/JOINTS/WEIGHTS attributes and the five named clips. This contract check is necessary but does not replace visual inspection of each gear combination and animation in Godot. Inspect rest pose, max-stride run, attack contact and airborne tuck, especially split coat, scabbard and both weapon silhouettes.
