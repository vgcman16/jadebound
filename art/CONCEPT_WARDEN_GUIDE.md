# River Warden: continuous body and removable equipment

The isolated 53-bone human study is separate from the playable 22-bone hero.
The latest editable UV source is documented in
[River Warden UV master](river-warden-uv/README.md). Outfit/hair painting and
final in-game material review are pending. The generated character concept is
art direction, not an in-game screenshot.

## Editable source

- Original construction code: `tools/build_concept_warden.py`
- Verified CC0 anatomical input: `art/human-base-trial/mpfb_adult_base.blend`
- Pre-UV clay master/reference: `art/concept-warden/river_warden_clay.blend` and `.glb`
- Current authoring master: `art/river-warden-uv/river_warden_uv_master.blend`
- Current exchange export: `art/river-warden-uv/river_warden_uv_master.glb`

The native Blender files are editable source assets. Open a copy to work on
materials or geometry. The optional construction generator can recreate the
preceding clay stage; it is not the final UV-authoring step. Earlier rejected
experiments and temporary logs are excluded from the public source tree.

The adult body is normalized to 1.84m. Body-derived torso/sleeve/trouser cages
retain the shared rig's weights. The scarf, split front/side/back coat panels,
shoulder shells, lamellae, leather harness and enclosing boot lasts are original
Jadebound construction. These are subdivision authoring surfaces, not final
retopology or draw-call batching. No finished animation set is included here.

## Separate pieces and coverage

- `Gear_Warden*`: armor and outfit
- `Gear_Boots*`: independent boots, greaves and closures
- `Gear_Gloves*`: independent fingerless gloves
- `Body_Hair*`: base hairstyle
- `Body_Underwear`: permanent base clothing; never an equipment slot
- `Head_Warden*` and `Weapon_Glaive*`: reserved names; these new pieces are not yet modeled

The continuous source remains in Blender as `AUTHORING_ContinuousAdult`.
Eight exported body regions partition all 13,378 source faces exactly once;
anatomy is not deleted to conceal clipping. Torso/arms/upper legs are provisionally
covered by armor, lower legs/feet by boots, and hands by gloves. Fingers and head
remain visible. Original `covered_by`, `restore_on_unequip`, `source_face_count`
and permanent-underwear properties are preserved.

The rig is raised15mm to accommodate soles. A barefoot integration must account
for that offset. The newest underwear fit has an8.051mm minimum sampled rest
clearance over8,087 samples, exceeding its3mm guard. This is a sampled rest-space
check, not proof of full-cycle or all-angle clipping. Fresh visual verification
of that correction and animated removal/restoration remains pending.

The live game currently supports its original armor/head/weapon visuals and
server-owned removal. The new human boots/gloves are separate authoring meshes,
not yet eligible live items. Keep that distinction when testing or demonstrating.

## Provenance

The underlying body/rig is from official MakeHuman core CC0 assets through
MPFB2.0.17. The costume, fitting code, hair forms and design are original project
work. The embedded skin has separate verified core CC0 provenance in the UV
master folder. No Conquer assets, user-reference screenshots or addon archives
are included. See the root `THIRD_PARTY_NOTICES.md`.
