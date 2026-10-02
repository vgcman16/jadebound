# Provenance and third-party notices

Jadebound's game code, fictional setting, procedural geometry, materials, animations and UI were created for this project. No Conquer Online assets, branding, maps, code, audio or screenshots are included as game assets. The design research contains links to official source material only. Jadebound is not affiliated with Conquer Online or its publisher.

Tools used:
- Godot Engine 4.6.3, MIT license: https://godotengine.org/license/
- Blender 4.3.2, GNU GPL: https://www.blender.org/about/license/

The tools' licenses apply to the tools. Blender-created output is not automatically GPL. Godot's license and bundled third-party notices must accompany any distribution of its engine binary. The repository contains a native project and exported original art, not an engine binary.

No open-source license has yet been selected for the original project. Public repository visibility does not grant a license to use the original code or art beyond rights otherwise provided by applicable law or GitHub's platform terms.

## Original generated terrain texture

The courtyard meadow and limestone base albedos were newly generated for Jadebound with the built-in image generation tool. They contain no supplied reference-game pixels. Other courtyard surface maps and courtyard geometry are original procedural Blender/source assets. The separate human-base trial below has its own verified provenance. Exact prompt and asset hash are recorded in `art/texture_sources.json`; source and usage details are in `art/TEXTURE_PROVENANCE.md`. This provenance note does not grant an open-source license.

## Separate human-base authoring trial

`art/human-base-trial/` contains a body/rig derived from verified official MakeHuman core CC0 assets using MPFB 2.0.17. It is not the current runtime hero. See its README, provenance and preserved asset header. MPFB addon source is GPL-3.0-or-later and is kept outside the distributed project; its graphical output is separately covered by the core asset CC0 license. No community asset packs were used. Original Jadebound costume/code licensing remains unchanged.

## Continuous-body costume and UV studies

`art/concept-warden/` develops that same CC0 body/rig with original Jadebound removable clothing and armor. `art/river-warden-uv/` contains the validated editable UV master and its public audit data. These studies are not yet the live gameplay character. The inherited human geometry/rig remains subject to its CC0 provenance; the original costume, code and design do not gain a new license from using it.

The UV master also embeds one unchanged official MakeHuman core skin albedo, explicitly covered by CC0 in its source material header and the [official system-asset list](https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html). Its SHA256 is `e897c4cc1b6ad5d10a7d2b2be92402feda4e772e6582dfaf0a1e8fc4621d8097`. Original asset holders listed for the September 2020 release are Data Collection AB, Joel Palmius and Jonas Hauquier. Exact source entry, descriptor, CRC, hash and credit are retained in `art/river-warden-uv/provenance/`. No community skin packs, proprietary reference images or MPFB addon code are included in this master.
