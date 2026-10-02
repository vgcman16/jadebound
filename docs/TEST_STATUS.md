# Local verification status — 2026-10-02

## Passed
- Fresh git-archive checkout of d804312 passed all339 assertions and ten asset contracts at15:02UTC, including regeneration of the import cache
- Godot 4.6.3 headless import/parse check
- 21 world assertions,40 ownership/equip/unequip assertions,230 pure progression assertions,12 authoritative progression/contact-timing integration assertions,19 controls/InputMap assertions,31 reversible body-coverage assertions,39 native skin/slot/effect assertions:392 total
- Ten original world-asset GLB contracts
- Bounded dedicated server + two loopback clients: 118/117 snapshots, two players, client1 removed its weapon while client2 retained its saber; all three processes exited normally
- Actual ten-second native viewport-input movie passed action assertions for click-to-approach/attack/loot, Ctrl-click vault, hotbar selection, right-click skill rejection, under-level armor rejection, eligible visible equip and eligible cast. It explicitly labels the test-only authoritative level1→3 advance; this is not footage of earning those levels
- Actual native control panel: six event-driven transitions passed, including inventory open/close, realm menu, remap to T, Esc dismissal and use of remapped inventory key
- Actual native14-frame equipment matrix: both kits, idle/run/apex/landing/contact/portrait; valid bind continuity and distinct kit silhouettes
- Actual six-second72-frame12fps engine motion movie: run/vault/saber cut, independent armor/head/weapon swap, glaive cut. Reviewed consecutive frames show no gross detached joints/pauldron inversion, and effects now align with contact
- Current frozen playable modular GLB metadata: 21 embedded images, 28 material definitions (15 with base-color textures), 22 joints and six animation clips; this metadata check does not establish final material appearance

- Actual neutral/albedo-only A/B: the same refined rig, geometry and poses show a change attributable to the Warden atlas/material content; these are explicitly labelled renderer studies, not gameplay
- Actual effects-off Warden pose study: new contact stance, clear tasset layering and no gross detachment in selected run/contact/apex/landing frames
- Unrendered `--unequip-review --event-check-only` check: Tab and six slot removal/restoration transitions travelled through Godot GUI handlers. This produced no screenshot/movie and is not native-desktop or pixel evidence

## Separate continuous-body UV master

The isolated human UV master passed a bounded 20.5-second Blender application/export and sequential independent exported-data audits. These results do not change the playable-model test counts above.

- All 168 meshes preserve the oriented geometry/named-weight/body-UV/coverage contract within the recorded comparison tolerances; original body-region source-face total remains 13,378
- All 53 joint rests and inverse binds have zero measured error
- All 528 outfit charts and 36 hair charts have zero measured positive-area triangle overlaps at the unchanged audit tolerance
- Exported minimum chart gutters are 31.999939 pixels on the 2K outfit atlas and 15.999969 pixels on the 512-pixel hair atlas, with float32 rounding
- Verified CC0 skin bytes, original anatomical UVs, hierarchy/extras and hair-flow attributes are preserved
- The maximum shading-normal vector difference from frozen clay remains the disclosed 0.00444001; normals are not claimed byte-identical

Exact asset hashes, current paint coordinates and a standalone reproducible data audit are in [the UV checkpoint](../art/river-warden-uv/README.md). No scene render, texture bake, native capture, live hero replacement or final material acceptance occurred in this stage.

## Pending on this checkpoint
- Native right-click removal/left-click restoration UI check after the latest handler change
- New body/accessory visual fixture is separate from gameplay, with no full-cycle motion or accessory eligibility claim
- Final stylistic acceptance of the Warden/courtyard: the 14:42 UTC native stills resolve overlapping warm lantern wash and stretched stair-side UVs, but paving contrast, cloth/anatomy and overall finish remain below target
- New full-motion capture under the updated environment
- Later human-base/concept work is isolated and not covered by the playable-model test counts
- Standalone Windows/Linux exports: matching export templates are not installed

The movies use automated input and a fixed12fps capture rate; they are behavior evidence, not a measured real-time performance benchmark. Pose screenshots do not establish all-angle/full-cycle clipping quality. No production network/security/load test has been run.
