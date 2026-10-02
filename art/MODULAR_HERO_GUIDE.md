# Jadebound modular hero: form/pose and construction-atlas study

This is an original, reviewable character study, **not final production art**. It improves the modular checkpoint's proportions, armor construction and supported poses, but still falls below the supplied visual references in face/cloth realism, surface richness and the overall finish. Technical checks do not establish visual parity. Review the actual-engine, effects-off comparison before approving an art direction.

No reference image, copied game asset, downloaded model or third-party texture is packaged. The earlier modular baseline is preserved at repository commit `c16cb4b`.

## Source and output

- Source: `tools/generate_modular_hero.py`
- Editable scene: `art/jadebound_modular_hero.blend`
- Runtime: `game/assets/models/hero_modular.glb`
- Generate: `blender --background --threads 2 --python tools/generate_modular_hero.py -- --output .`
- Add `--render` for five Warden studies: `builds/warden-rebuild-refined/rest.png`, `contact.png`, `apex.png`, `landing.png`, and `clay.png`

The script starts from an empty scene and leaves the previous art library unchanged. It exports the hero before adding authoring lights, camera or contact floor. The editable scene is saved before optional proof renders. The current saved authoring view displays the Warden in its idle pose. The first form study remains in `builds/warden-rebuild/`, and the refined pre-atlas forms remain in `builds/warden-rebuild-refined/` for comparison. Use `--render --proof-mode atlas` for the smaller material-only rest/contact proof set in `builds/warden-atlas-study/`.

## Stable runtime contract

Root: `HeroModular`. Armature: `JadeboundRig`. Shared skinned body: `Body_Base`.

| Independent slot | Option A | Option B |
|---|---|---|
| Armor | `Gear_Wayfarer` | `Gear_Warden` |
| Head | `Head_Topknot` | `Head_Warden` |
| Weapon | `Weapon_Saber` | `Weapon_Glaive` |

Each slot name identifies a single batched skinned mesh. Match its name or prefix if the importer adds a suffix. Show exactly one option per slot, plus `Body_Base`, immediately after loading. All seven meshes share the same 22-joint skeleton and native bind matrices.

`Saber_FX` and `Glaive_FX` are hand-bone markers with `visibility_owner` metadata. They are rig children, not descendants of the skinned weapon meshes, so runtime effects attached there need explicit cleanup on equipment changes. The asset contains no aura, particle system, selection ring or permanent glow. Base weapon materials have zero emission; retain the solid steel blade when adding separately authorized quality effects.

## Scope of the second study

- Shared body: more compact adult head, stronger brow/jaw planes, narrower wrists/ankles, shaped palm/thumb/fingers and fitted instep/toe/sole construction
- Warden: shaped breastplate above two articulated waist lames, asymmetric forged shoulders, a readable side closure, overlapping tassets, shallow knee brows, fitted front greaves, and a designed brow/temple helmet transition
- Cloth: non-circular sleeve sections and localized modeled fold valleys rather than final cylindrical contours
- Pose: asymmetric supported idle, planted-leg stride solving, wide leading-leg attack with lowered/shifted pelvis, and asymmetric airborne tuck/landing compression

The Wayfarer garment and the two existing weapon designs remain the established alternatives. They share the refined body; this pass adds no new equipment family.

Tasset plate edges have been moved outside their cloth backing. Plates and backing now use matching height-dependent hip/coat blends, fixing the triangular intersection patches visible in the first form study.

## Materials and UVs

One original 1024 px construction-atlas set is shared by the three Warden material classes: cloth, forged steel and worn leather. It contains:

- sRGB albedo with explicit constructed recesses, selective worn lips, aligned fold valleys and leather seam bands
- Tangent-space normal detail
- Packed authored cavity, roughness and metalness (ORM)

Named UV islands have different allocations. The main breastplate gets a 448 × 384 px interior, approximately 2.6 times the former equal-cell allocation. Visible plate borders follow the modeled plate-outline UVs. The branching river/reed engraving is an original design used only on the breastplate. It is not a general overlay or a motif tiled across the hero. Small/hidden parts receive less atlas area, and every island has an extruded pixel gutter.

The cavity channel is an authored mask, not a ray-traced AO bake. It is connected to glTF's occlusion input. Cloth fold masks use the existing modeled fold coordinates. Matte aged plate faces and exposed metallic lips have distinct per-pixel roughness/metalness. Existing 256 px maps remain on unchanged material families, including lengthwise blade brushing.

All image data is original, packed into the Blender scene and embedded in GLB. Images use stable `jb_*` names and cleared temporary filepaths, so native texture extraction produces deterministic `hero_modular_jb_*.png` paths. Keep currently referenced extracted textures according to the project's import/export workflow. Do not remove an extracted texture merely because it also exists inside the GLB; confirm imported dependencies first.

The actual embedded construction maps were also extracted for inspection as `builds/warden-atlas-study/jb_warden_construction_albedo.png`, `jb_warden_construction_normal.png`, and `jb_warden_construction_orm.png`.

The atlas-only pass preserved every mesh position, normal, joint, weight and index buffer, and all six animation sample sets exactly. Only UV allocation and surface content changed. The same-light native before/after neutral and albedo-only comparisons are in `builds/material-study/`. They show a real increase in construction readability, while also making the remaining stylized modeling limits clear.

The legacy `--stabilize-image-names` migration was used on the earlier, pre-regional modular checkpoint. The current construction-atlas study already has stable names; do not use that legacy migration option on it.

## Animation

- `idle`: asymmetric supported stance with restrained breathing
- `walk`, `run`: alternating counter-rotation and baked planted-leg trajectories
- `attack`: saber windup, extended diagonal cut and recovery
- `attack_glaive`: two-handed shaft support and a forward-descending cut
- `jump`: launch compression, asymmetric tuck and landing compression

The first three clips loop. Attack and jump clips are one-shots. Gameplay owns horizontal movement and the root jump trajectory; pelvis displacement is local deformation. Attack contact remains at the established authored fraction used by the authoritative runtime and the approximately 0.58 normalized review capture.

Two-handed contact and planted legs are baked to ordinary joint animation, with no runtime IK dependency. Select `attack_glaive` for the glaive and `attack` for the saber. All slot combinations still use the same rig.

## Technical verification and visual limits

Current export: one skin, 22 joints, seven skinned meshes, 28 materials, 21 embedded images and six clips. The active Warden combination is approximately 12,800 triangles.

Verified native export checks:

- Exact slot names, per-primitive UV/joint/weight attributes and inverse bind matrices
- Maximum rest/bind identity error below `1.5e-6`
- Maximum exported weight-sum error below `3e-8`
- Full-support glaive grip error below `2.2e-7 m` at sampled authored poses
- All three Warden material classes share the construction atlas with valid albedo, normal, ORM and occlusion connections
- Stable embedded image names

Native engine tests and effects-off pose captures remain the acceptance route for mixed gear, complete blade framing, collisions/intersections, pose transitions and actual gameplay-scale material readability. The second authoring contact proof extends the blade beyond the studio's left edge; use the wider native capture to assess the complete weapon.

Remaining art-direction limits are intentional review findings, not resolved by these technical checks: the finish is still stylized and smooth, face/cloth forms need a stronger production treatment, and small-scale authored surface richness is below the target references. Do not label this study as production-ready or reference-matched.
