# River Warden: editable human UV master

This is an isolated authoring asset, not yet the playable character. Open
`river_warden_uv_master.blend` in Blender 4.3.2 or later to edit the body, separate
outfit/boots/gloves, materials and UVs. `river_warden_uv_master.glb` is its validated
exchange export. No addon is needed merely to open or inspect these files.

The native `.blend` is the editable source for this curated UV asset. It includes
the finalized UV layout, weights, 53-bone rig, body regions and equipment meshes.
Earlier unsuccessful UV experiments and their temporary reproduction pipeline
are intentionally not included. No command here depends on those experiments.
The original costume construction source remains in
`tools/build_concept_warden.py`, with its preceding clay master under
`art/concept-warden/`; regenerating that earlier construction stage is distinct
from editing the finished UV master.

## What is validated

The data checks preserve 168 meshes, the original 13,378 body source faces,
named skin weights, coverage/extras, hierarchy, original anatomical UVs and all
53 joint rest/bind transforms. The outfit has 528 charts in a 2048-pixel atlas;
hair has 36 charts in a 512-pixel atlas. Both have zero measured positive-area
triangle overlaps at the documented tolerance. Actual minimum gutters are
31.999939 pixels for outfit and 15.999969 pixels for hair, including float32
rounding. Shading normals have a known maximum vector difference of 0.00444001
from the preceding clay export; they are not byte-identical.

`paint_layout.json` contains current exported bounds, chart membership and
measured density/distortion. `hair_flow.json` retains root-to-tip anchors.
Several narrow glove opening-rim charts are only about 1.25–1.60 texels wide;
use simple edge color there rather than detailed stitching.

From the repository root, run:

    python3 tools/audit_human_uv.py

The audit uses only the included reference GLB, UV master, manifest and chart
layout. It requires NumPy, has no external service dependency, and writes a
compact report to `builds/human-uv-report.json`. Use a finite CI timeout such as
120 seconds. The main gameplay validator remains `bash tools/validate.sh`.

## Appearance and integration limits

Outfit/hair painting, baked surface detail and final in-game appearance review
are pending. The latest underwear-clearance correction needs fresh visual
verification; static data checks do not prove animated clothing clearance.
This asset has no finished gameplay animation set or new weapon/headgear kit.
The current game still uses its separate 22-bone modular hero. Boots/gloves in
this human study are separate meshes, but they are not yet eligible live items.
Permanent underwear and the reversible body-region coverage contract are kept.

## Provenance

The underlying body/rig and embedded unchanged skin albedo derive from official
MakeHuman core CC0 assets. Exact credit, original asset/material headers and
hashes are in `provenance/` and `asset_manifest.json`. MPFB program code is GPL;
no addon archive/program code is bundled. Original Jadebound costume, code,
concepts and material design remain project-authored, with no open-source
license chosen. See `THIRD_PARTY_NOTICES.md` at the repository root.
