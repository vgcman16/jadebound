# Jadebound original art kit

All geometry and palette materials in this kit are original and generated without external assets. The Blender library keeps every object, material, bevel modifier, character pivot and animation editable.

## Regenerate

`blender --background --threads 2 --python tools/generate_assets.py -- --output .`

This produces `art/jadebound_assets.blend` and ten separate GLBs in `game/assets/models/`. The command does not render or download anything. Run it with Blender 4.3 or newer. Asset regeneration replaces these generated output files.

## Coordinates and size

Blender uses metres, Z up, and characters face -Y. Each exported root is at ground height zero. Standard glTF export maps this to Godot Y up; character front becomes +Z. If a Godot controller uses the common -Z forward convention, rotate its visual model child 180 degrees around Y, or account for +Z when aiming. Do not rotate the physics/controller root solely to fix the visual convention.

- Hero/elder/bandit: stylized approximately 1.8–2.1 m tall including headwear, grounded boots and readable weapon silhouettes
- House: approximately 5 × 4 × 3.9 m, with a projecting front step and entrance canopy
- Gate: approximately 6 × 1.8 × 5.1 m, including raised ridge terminals
- Shrine: approximately 3 × 2.6 × 3.1 m, including raised ridge terminals
- Tree: mature branching cherry, approximately 4.5 m tall with a broad, asymmetric coral-blossom canopy
- Bamboo: three-stalk clump, approximately 3.4 m tall
- Rock: clustered stone and moss, approximately 1.5 m wide
- Lantern: freestanding amber lantern and timber post, approximately 2.3 m tall

These are approximate art bounds rather than collision dimensions. Eaves, canopy clusters, roots, steps, and weapons can project beyond the main body of an asset.

## Revised art direction

The hero is an adult-proportioned wandering swordsman with a fitted dark-teal and ivory robe, long split coat panels, a narrow leather belt, layered shoulder armor, fitted bracers, high boots, and an ink-black topknot. Burnt-orange cloth accents and a belt-mounted scabbard break up the silhouette. The held weapon is a curved steel saber with a restrained jade inset, an aged brass guard, and a wrapped grip. The face uses softened geometry rather than a broad faceted head beneath a large conical hat.

The house, gate, and shrine use slate-blue and charcoal roofs with individually modeled overlapping ceramic tile courses. Curved slopes, upturned eaves, raised hip and ridge tiles, substantial fascia, and a dark soffit cavity provide depth. Gold is limited to aged accents. The house adds warm plaster and clay panels, stone footings, deeper lattice-window surrounds, a carved entrance, timber brackets, and a smaller entrance canopy.

The tree is a mature cherry with a twisting trunk, visible branching and fork structure, irregular dusky-coral blossom clusters, softer highlighted tufts, and scattered fallen petals. Bamboo uses muted natural greens. Stone, timber, metal, leather, and cloth have distinct roughness and color ranges. Beveled hard surfaces coexist with softened faces and foliage, rather than giving every surface the same hard low-poly treatment.

All geometry and palette materials remain procedural source assets with no external textures or downloads.

## Color pipeline

Palette values in `setup_materials()` are perceptual sRGB hex colors. The `material()` helper explicitly converts each channel to linear RGB before assigning Blender's Principled BSDF base color, material display color, and applicable emission color. The glTF exporter therefore receives linear shader values, avoiding the washed-out results caused by treating sRGB palette numbers as linear values.

Judge final colors in an actual Godot scene with its lighting, exposure, and environment settings. The Blender material viewport and the engine's lit output need not look identical. The revised source palette is authored deliberately darker and more restrained; a rendered engine preview is still the visual acceptance check.

## Static export batching

The seven static assets (`house`, `gate`, `shrine`, `tree`, `bamboo`, `rock`, and `lantern`) export as one mesh object per material. The exporter first evaluates each object's geometry, including bevel modifiers, then combines same-material polygons in asset-root-relative coordinates. This reduces many small mesh nodes and draw submissions while preserving their appearance and ground origin. It does not reduce triangle count, and actual frame-rate improvement depends on the scene and renderer.

Batching uses disposable export-only collections. They are removed before the library is saved, so `art/jadebound_assets.blend` retains the original named authoring objects, modifiers, materials, and collections. Static GLB roots use the asset name with an `_optimized` suffix and expose batching counts in exported custom properties. Consumers should not depend on authoring-part node names inside a static GLB.

The hero, elder, and bandit keep their separate meshes and complete animation hierarchy; they are not statically merged. No lights or cameras are exported.

## Character animation

Characters use hierarchical rigid-part pivot animation rather than weighted skinning. The torso, two shoulders and two hips have real keyed transforms grouped into identically named NLA tracks: `idle`, `walk`, and `attack`. The exporter merges matching NLA track names into animation clips. Authored idle is 2 seconds, walk 1 second, and attack 0.75 seconds at 24 fps. Idle and walk return to their starting poses; configure them as looping clips in Godot. Attack is a one-shot. Gameplay may change playback speed independently; the current controller accelerates the authored attack to match its approximately 0.28-second combat window. Exported extra properties also document clip intent.

The file contains all three NLA tracks for each animated pivot. To preview/edit one clip in Blender, solo that track across the character's pivots, or mute the other two tracks. The neutral first frame is shared by all clips. No lights or cameras are exported.

The Blender library arranges assets into an editing gallery after GLB export. These gallery locations do not affect the exported GLB ground-centred origins.
