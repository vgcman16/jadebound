# Original weathered courtyard study

Scope: one compact stone approach and entrance, not a claim that the full world is finished.

Authoring source: `tools/generate_courtyard_detail.py`. Editable output: `art/jadebound_courtyard_detail.blend`. Runtime: `game/assets/models/courtyard_detail.glb` plus original terrain PNGs in `game/assets/textures/courtyard/`.

The Blender file retains separate authoring parts. The GLB batches them into material-batched meshes: mixed-size chipped/recessed stone paving, layered masonry and shallow doorstep, fitted timber doorway/lattice with a deep cavity, plaster returns, slate canopy, irregular shaped rocks and grouped grass blades. The central action lane stays clear. Runtime obstacles account for the new solid entrance and removed foreground house.

The fitted paving has four face-specific UV islands with original mineral imagery, authored worn lips, under-edge cavities and restrained surface/roughness treatment. Wood, plaster, earth and background rock use original non-periodic fields. Blanket runtime tinting is removed; judge each material under the neutral reflection sky. The meadow and limestone base colors are original generated imagery; see `TEXTURE_PROVENANCE.md`. No copied reference art is shipped. Godot texture imports generate mipmaps to avoid distant grass sparkle. Judge maps under the final engine light, not by texture count.

Regenerate with Blender4.3+ using:
`timeout 120s blender --background --threads 2 --python tools/generate_courtyard_detail.py -- --output .`

This is still an art-direction study. The shared hero/keeper rig and original old enemy assets coexist; enemy production art, environment-wide replacement, navigation and full combat animation polish remain separate future work. Do not mistake posed effects-off review frames for manual playtesting.
