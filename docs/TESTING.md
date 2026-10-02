# Validation record — prototype work in progress

Environment: Godot 4.6.3, Blender 4.3.2, Linux cloud machine. Native visual capture used Mesa llvmpipe software rendering; this is not a hardware performance benchmark.

Passed:
- Godot editor import and script parsing
- Twenty authoritative simulation assertions: movement clamping, stale/non-finite input rejection, damage/cooldowns, enemy defeat, loot collect-once and ownership, quest reward idempotence, healing/qi, death/respawn and map boundaries
- Dedicated loopback server plus two real client processes: each received 118–119 authoritative snapshots and observed two player identities
- Bounded Deflate snapshot round-trip, no original oversized-packet warning in the two-client run
- Original Blender asset generation and GLB import
- Native scene rendering and screenshot save, including the revised courtyard

Rig export issue identified and fixed: constant animated-node bind translations were omitted from GLBs by the Blender NLA export path. The generator now preserves the authored bind translations deterministically. The asset contract passes for all three characters' torso/arm/leg rest pivots and all ten original GLBs. Corrected motion capture is checked separately before delivery.

Not established: public Internet security, online durable persistence, WAN latency experience, MMO-scale capacity, full 8-player soak, physical Windows/macOS playtests, or polished character animation.

Modular equipment checkpoint:
- 20 additional authority/equip assertions pass, including ownership/slot rejection, matching damage/guard/vitality and no swap-to-heal exploit
- 27 native visual-contract assertions pass: one22-bone skin, seven skinned meshes, five imported clips, all eight mixed equipment combinations and quality-effect reset on swap/death/respawn
- Fourteen actual-engine frames inspect both kits at gameplay/close-up scale, run/jump/attack poses and the live equipment panel
- A finite72-frame six-second recorded slot-swap demo confirms armor, helmet and weapon update separately in both portrait and world, with corresponding stats
- Pose review confirms connected limbs and equipment visibility. Attack contact/landing expressiveness and richer material textures are still being improved; data tests do not certify final art quality
