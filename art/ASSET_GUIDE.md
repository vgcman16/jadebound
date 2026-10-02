# Jadebound original art kit

All geometry and palette materials in this kit are original and generated without external assets. The Blender library keeps every object, material, bevel modifier, character pivot and animation editable.

## Regenerate

`blender --background --threads 2 --python tools/generate_assets.py -- --output .`

This produces `art/jadebound_assets.blend` and ten separate GLBs in `game/assets/models/`. The command does not render or download anything. Run it with Blender 4.3 or newer. Asset regeneration replaces these generated output files.

## Coordinates and size

Blender uses metres, Z up, and characters face -Y. Each exported root is at ground height zero. Standard glTF export maps this to Godot Y up; character front becomes +Z. If a Godot controller uses the common -Z forward convention, rotate its visual model child 180 degrees around Y, or account for +Z when aiming. Do not rotate the physics/controller root solely to fix the visual convention.

- Hero/elder/bandit: stylized approximately 1.8–2.1 m tall including headwear, grounded boots and readable weapon silhouettes
- House: approximately 5 × 4 × 3.8 m, with a projecting front step
- Gate: approximately 6 × 1.8 × 4.9 m
- Shrine: approximately 3 × 2.6 × 2.8 m
- Tree: evergreen jade pine, approximately 3.6 m tall
- Bamboo: three-stalk clump, approximately 3.4 m tall
- Rock: clustered stone and moss, approximately 1.5 m wide
- Lantern: freestanding amber lantern and timber post, approximately 2.3 m tall

The house, gate and shrine use dark jade hipped roofs, raised tile seams, gold ridge/corner details, and warm timber. Most forms are deliberately flat-shaded with one-segment bevels. Simple PBR materials keep the kit usable without textures.

## Character animation

Characters use hierarchical rigid-part pivot animation rather than weighted skinning. The torso, two shoulders and two hips have real keyed transforms grouped into identically named NLA tracks: `idle`, `walk`, and `attack`. The exporter merges matching NLA track names into animation clips. Idle is 2 seconds, walk 1 second, and attack 0.75 seconds at 24 fps. Idle and walk return to their starting poses; configure them as looping clips in Godot. Attack is a one-shot. Exported extra properties also document intent.

The file contains all three NLA tracks for each animated pivot. To preview/edit one clip in Blender, solo that track across the character's pivots, or mute the other two tracks. The neutral first frame is shared by all clips. No lights or cameras are exported.

The Blender library arranges assets into an editing gallery after GLB export. These gallery locations do not affect the exported GLB ground-centred origins.
