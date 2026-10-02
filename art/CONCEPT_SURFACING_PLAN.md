# Human character surfacing

The current editable UV source and public audit are documented in
[River Warden UV master](river-warden-uv/README.md). Body/rig/coverage, UV overlap,
gutters and the verified CC0 skin pass data checks. Surface painting and final
in-game appearance remain pending.

The next original material pass targets medium-scale garment seams and tension
folds, leather construction/wear, restrained metal underlaps/exposed lips and
root-to-tip hair flow. Preserve the accepted adult proportions and independently
removable pieces. Keep the existing body UVs and the 2K outfit / 512-pixel hair
layout. Use sRGB albedo, non-color tangent normals/ORM, and separate material
responses for skin, cloth, leather and metal. Any baked occlusion must respect
independent slots: removing armor must not leave its shadow painted on skin.

All surface changes require texture/data inspection and later actual engine
review. Atlas/mesh counts are not evidence of finished visual quality. The
curated repository contains the usable authoring master rather than rejected
experimental copies; edit it directly in Blender.
