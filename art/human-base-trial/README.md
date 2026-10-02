# Human-base production-method trial

This is a separate authoring experiment, not the currently playable character.

The body, morph targets and game rig derive from the official MakeHuman/MPFB core CC0 assets. The original costume and character concept remain a separate creative layer. The working game still uses the earlier original rig/model.

## Source and licensing

- Official extension: https://extensions.blender.org/add-ons/mpfb/
- Installed version: MPFB 2.0.17, official archive SHA256 `4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87`
- Actual archive: 45,031,536 bytes; 2,384 members; 75,212,589 expanded bytes
- Core asset license: https://static.makehumancommunity.org/about/license.html
- Source/output distinction: https://github.com/makehumancommunity/mpfb2/blob/master/LICENSE.md
- The bundled `data/3dobjs/base.obj` header independently identifies the hm08 base mesh as CC0. See `base-asset-header.txt`.

MPFB program logic is GPL-3.0-or-later. Its addon source and installation are not distributed in this game repository. The official license separately assigns CC0 to base mesh, targets, rigs and other core graphical data, including scripted graphical output. No community packs or unrelated third-party models were used. This does not choose a license for the game's original code or artwork.

## Reproduction

Use Blender 4.3.2 or a compatible version. Install the exact official MPFB archive into a local-only repository named `jadebound_local` using Blender's `extension repo-add` and `extension install-file` commands. All Blender user paths must point beneath this project's ignored `local/mpfb-trial/` directory. `tools/blender_local_mpfb.sh` sets those paths and offline mode for subsequent runs.

Run `timeout 120s bash tools/blender_local_mpfb.sh --python tools/trial_mpfb_human_base.py`.

The master `.blend` keeps the editable shape keys, body mask and 53-bone game rig. The `.glb` is a separate cleaned, skinned export with helper geometry removed and ordinary UVs. The neutral Cycles image is an anatomy proof only. The actual environment lacks OpenImageDenoise, so the finite 12-sample render disables denoising. No global preferences or optional MakeHuman network connection are needed.

## Remaining work

The base is 1.642m high before costume fitting; scale must be explicit. Eyes, hair, skin, original garments/armor and authored motion are unfinished. Imported weights are a starting point and need deformation/clipping review. This trial has not replaced the live gear system, and its topology/rig do not prove final art quality.
