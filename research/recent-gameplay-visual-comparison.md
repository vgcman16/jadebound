# Recent Conquer gameplay reference and Jadebound comparison

Checked 2026-10-02, approximately 14:32–14:41 UTC, in dot's cloud browser. This targeted pass compares actual inspected pixels with `builds/art-redesign-review/warden-gameplay.png` and `builds/material-study/after-neutral.png`. Both local captures were opened and inspected. The neutral material study is explicitly a diagnostic scene, not gameplay.

## Result and video limit

Recent official **in-game** reference is available: three PC HUD screenshots visibly stamped **12/28/2025**, published with the **January 13, 2026** Dune Wanderer release, plus an animated in-game combat demonstration on the December 2025 campaign page. These are stronger evidence than undated image-search thumbnails. The official screenshots may come from a publisher/test capture; they do not establish an ordinary player's precise server settings or default zoom.

Two recent public YouTube videos were found and their upload dates verified through the expanded visible descriptions. **Neither decoded a gameplay frame in this browser.** There are no honest watched gameplay timestamps to report from them:

| Video | Verified metadata | Actual playback result |
|---|---|---|
| [Dune Wanderer gameplay, Conquer Chess TV](https://www.youtube.com/watch?v=PqaI-tBbb74) | Premiered Jan. 17, 2026; duration 2:01 | Black spinner, current time 0, readyState 0 before and after one reload; no decoded frame |
| [Team PK, Turquoise/Hebby/Eagle, AbdulRahman SaskiOchiha](https://www.youtube.com/watch?v=J3YcIoKsbcE) | Uploaded Sept. 16, 2026; title also names that date; duration 3:33 | Black spinner, current time 0, readyState 0; no decoded frame |

The titles identify plausible current gameplay candidates, but cannot verify their visual content, main-PC/server authenticity, movement or skill timing. No CAPTCHA, sign-in requirement or explicit bot block was displayed. The technical cause is unknown. No alternate download service or media extraction was used. The earlier supplied YouTube clip was not retried.

The [publisher-hosted 51.85-second MP4](https://hwimg.99.com/co/images/2025/dunhuang/en/dh-en.mp4), linked in the [official campaign page](https://co.99.com/guide/event/2025/dunhuang/), **did decode and play**. Sampled frames at approximately **0:09 and 0:21** show close cinematic character shots, not an isometric gameplay camera. The end state was observed at 0:51.85. This is not a full-watch claim; the sampled cinematic shots cannot establish live combat responsiveness, jump cadence or world-scale materials.

## Four useful inspected gameplay references

All four below were opened in the public browser and visually inspected. Source images/animations were not downloaded, processed into game assets or added to the repository. Links are reference-only.

| Reference | Provenance and classification | What is actually visible |
|---|---|---|
| [Town and food vendor](https://hw.99.com//uploads/allimg/co3/mainquest2512303.png) | Official [Jan. 13 release gallery](https://co.99.com/news/2026-01-13/the_new_class_dune_wanderer_arrives_in_all_servers__alongside_the_awakening_system.shtml); PC HUD, 1024×768; visible stamp Dec. 28, 2025, 15:19 | Small adult figures beside an earth-toned building; subdued irregular paving fades into dirt; worn plaster, crates, awning, cart wheel, sacks and vegetation create distinct material scales. Costume has fitted upper body and long layered panels; modest localized foot light |
| [Carriage and NPC encounter](https://hw.99.com//uploads/allimg/co3/mainquest2512302.png) | Same official gallery; PC HUD, 1024×768; visible stamp Dec. 28, 2025, 15:18 | Long slim red/white costume, long hair and a separate luminous pale outfit; carriage canopy and wheel details, horse, rough barriers, ledge strata and sparse vegetation. Warm ground stays comparatively quiet around the characters |
| [Elevated desert field](https://hw.99.com//uploads/allimg/co3/mainquest2512307.png) | Same official gallery; PC HUD, 1024×768; visible stamp Dec. 28, 2025, 15:34 | Several separate adult silhouettes among layered rock ledges. Broad terrain shapes have smaller strata/erosion/plant detail. Bright accents mostly identify figures/interaction circles. A dialog obscures the center; this is a quest capture, not proof of uninterrupted battle |
| [Dune combat demonstration](https://hwimg.99.com/co/images/2025/dunhuang/a12.gif) | Actual in-game animation reached through “Skills” → “Click to view game effects” on the [2025 campaign page](https://co.99.com/guide/event/2025/dunhuang/); 862×724 crop, no full HUD or player-session date | Multiple inspected phases show a dark, slim, long-robed fighter turning with a long weapon, the hem flaring into a sweep and returning to a narrower stance. Teal/orange curved ground ribbons and small motifs surround the action, with a stronger translucent circular burst in one phase. The shaded body and weapon core remain visible beneath it |

The combat demonstration is a **campaign skill-appearance preview**, not proof of the unmodified base skill, Super equipment glow or a specific live-server balance state. It has no exposed video timeline, so its samples have **no gameplay timestamps**. Exact animation durations, hit frames and jump trajectories were not measured. The same campaign page reuses some other media whose paths contain 2022; publication on a 2025 page alone would not make those newly captured. Those reused clips are not treated as fresh 2025 gameplay evidence here.

Broad image search also surfaced private-server sites, a Chinese-language undated gallery, mobile/emulator listings and promotional character paintings. They were excluded from the current English PC comparison. The reference set is intentionally small and traceable.

## Direct comparison and highest-value changes

**Hero:** Jadebound's revised Warden has a clearer adult body and coherent colored material groups. The neutral study also reveals the remaining difference: its hip plates, knee caps, shoulder wedges and shin strips read as separate geometric pieces. The reference characters have stronger continuous costume lines, tapered waist/limbs and layered cloth that unifies those parts. Refine plate contours and overlap over a continuous underlayer; vary panel sizes and give cloth folds a clear direction. Keep the original costume and anatomy. This is a visual judgment, not evidence of disconnected joints or a current animation bug.

**Camera:** The current Warden gameplay capture gives the hero and nearby paving a larger share of the frame than the inspected PC quest captures. Test a slightly wider framing alongside the current framing, with identical lighting and output size. Preserve readable gear and target indicators. The publisher screenshots do not prove an exact default camera angle or zoom, so no numeric copy target is prescribed.

**Ground and props:** Jadebound's paving is very bright and has large, repeated dark seams. It dominates the courtyard more than the reference's quieter, weathered ground. Reduce top-surface contrast and repeated streaks, soften the dirt transition, vary wear at several scales and keep occasional damaged edges. The reference gets richness from coherent small material details within larger forms; simply adding uniformly noisy texture or more props will not reproduce that hierarchy. The neutral slab study already shows material work, but its surfaces should be judged again in the full courtyard.

**Combat appearance:** The observed modern Dune demo ties body turn, weapon direction and cloth silhouette together. Its effect has a low ground shape, a brighter event peak and a shaded readable figure. For the original Warden, give each attack a clear body/weapon action first; make the trail follow that path, then add a brief contact accent and a bounded ground response. This is an original implementation recommendation. Still captures of Jadebound cannot establish whether its current timing matches; a local motion capture is needed for that comparison.

**Remaining gap:** actual recent full-session PC footage showing movement, jumping, ordinary melee/ranged loops and gear switching has not been watched successfully. The current evidence supports silhouette/material/VFX layering decisions, not an exact locomotion or combat-timing match. A playable legitimate video source or a directly supplied clip is needed to close that gap.
