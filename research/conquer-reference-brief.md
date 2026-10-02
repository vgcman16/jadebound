# Conquer Online reference brief for an original isometric MMORPG

Research date: 2026-10-02 UTC. Purpose: inform an original playable game, not reproduce Conquer Online's assets, maps, branding, UI, characters, or exact balance. Sources are public official publisher pages unless identified otherwise. No game clients, asset archives, private-server code, or executables were acquired.

## The recommendation in one paragraph

Build the first slice around **responsive click movement, frequent readable leaps, aimed melee lines, small clusters of enemies, visible loot, and a short return-to-town upgrade loop**. This combination is more distinctive than simply using an isometric camera and fantasy swords. Give the environment restrained color and the combat generous visual clarity. Demonstrate one genuinely enjoyable combat role before adding a class catalogue. A server-authoritative combat core and durable item identity must precede competitive PvP, item loss, trading, and a persistent economy.

## 1. What the reference establishes, and what it does not

- The publisher describes Conquer Online as a 2.5D fantasy MMORPG with an ancient-Chinese setting, originating in 2003. Treat that as genre context, not an instruction to copy its fictional world. [S1]
- Historical official onboarding specifies left-click walking/running and Ctrl+click jumping. The weapon guide distinguishes manually activated stamina-based weapon skills from mana-based magic. [S2, S3]
- A January 2010 publisher retrospective says its Classic edition removed Battle Power and talismans, emphasizing player control, role cooperation, and hunting for equipment. This is evidence about that historical edition, not proof that all later servers have those rules. [S4]
- The official returning-player guide records an October 17, 2017 graphics revision and describes faster progression, epic weapons, and additional systems. Its ten-class count is archival, not a verified 2026 census. [S5]
- The official Origin-server page describes five starting class families and staged unlocks of later systems. Thus even an official product labelled nostalgic is not necessarily a pristine 2003 ruleset. [S6]

**Source reliability caveat:** official pages retain old copy inside updated navigation. Counts, event schedules, damage tables, and even PvP descriptions differ between pages. Live browser inspection of the Guild War page showed Sunday while the search-indexed copy showed Saturday. This brief deliberately does not prescribe those schedules or claim an exact current class roster. No timings were measured from the running game, and no game executable was used. Numerical tuning below is proposed for the new game.

## 2. Art, camera, silhouettes, and the original-art translation

### Directly observed reference

Two official legacy Guild War images were visually inspected in dot's cloud browser, through the publisher's linked gallery. They show an elevated fixed oblique scene, diagonal stone paving, muted grey/olive ground, a relatively small standing character, large architecture, dark ground shadows, and brighter character coloration. One image has a stone objective in a spacious paved court; another shows a tall wall and roofed gate. These observations concern the game image, not the ornamental website frame. [V1, V2]

### Proposed original direction

- Use an orthographic/high-oblique camera. Start near a 45-degree azimuth and 35-degree elevation as an original tuning baseline, then choose the angle for legibility. Do not claim these are Conquer's measured angles.
- Prioritize the navigable ground. A field should have readable open travel lanes and enemy clusters, with larger silhouette landmarks at its boundary.
- Ground palette: slate, moss, warm earth, desaturated foliage. Accents: warm lanterns, one player-team color, one hostile telegraph color, and distinct rarity cues. Keep broad skill effects short enough to reveal feet and enemies again.
- Characters should read by weapon shape and posture: two separated weapons; a broad shield; a curved bow; a staff or long casting implement. Distinguish roles in silhouette before surface detail.
- A leap needs a clear ground shadow, rise/apex/landing pose, and a brief landing accent. Visual height is separate from the ground-plane position; do not let the airborne sprite obscure the authoritative landing location.
- Prefer original Blender-made modular geometry or procedural art: beveled masonry, roof segments, posts, planters, rock families, three foliage masses, cloth banners, simple weapon meshes. Keep a limited material palette and consistent texel/detail density.
- Design a different town plan, gateway, objective, UI arrangement, faction symbols, NPC names, enemy species, and weapon ornamentation. Inspiration is the relationship between mobility, readability, and social space.

### Asset provenance

The primary recommendation is original geometry/materials authored for this project. Public Conquer imagery is **reference-only**; availability on a website is not a reuse license. Do not extract models, sprites, sounds, fonts, animations, maps, icons, or UI textures from its client or redistribute the reference screenshots as game content.

Optional fallback, only if external art is wanted: **Kenney Nature Kit**, original creator Kenney, official asset page explicitly lists CC0. Kenney's support page expressly permits commercial use and says attribution is optional. Keep the downloaded license with the asset manifest and still record source, creator, license, download date, and any modifications. This is a stylized foliage/rock source, not Conquer art, and was not downloaded in this research. [A1, A2]

## 3. Movement and combat feel

### Evidence

The official weapon table includes active line-oriented sword/blade attacks with stamina cost. A 2008 player-authored weapon guide hosted by the publisher explicitly discusses timing and aim; treat it as historical player testimony, not an engine specification. Official skill documentation describes active skills, automatic passive effects, and an independently charged XP-skill opportunity. These XP skills are distinct from the character-level experience reward. [S3, S7, S8]

### Proposed implementation target

1. **Walk and leap immediately.** Clicking terrain creates a readable destination; a modifier-click or an accessible alternate binding leaps toward it. Support keyboard movement if desired, but retain destination-based motion as a first-class path.
2. **Make travel feel light.** Begin with a 0.38–0.55-second leap covering roughly 2–3 normal movement seconds, then tune by playtesting. These are original proposed values, not documented Conquer timings.
3. **Separate selection from skill aim.** Basic melee may chase a selected enemy into reach. The signature line strike should use a ground direction and actual intersection, not silently become a guaranteed target hit.
4. **Make errors informative.** An out-of-range target, blocked landing, insufficient resource, or cooldown gives immediate restrained feedback. Clicking UI must never launch a ground attack.
5. **Readable attack cycle.** As an initial baseline, try a 0.1–0.18-second anticipation and a short recovery for the line strike. Tune hit testing, animation impact, sound, and damage display to the same event. Avoid long animation lock in ordinary hunting.
6. **Resource rhythm.** One clearly visible stamina bar can govern the line strike and radial skill; use regeneration rules that create choices without frequent forced waiting. Add mana only when a distinct caster role exists.
7. **Burst punctuation.** A charged temporary flourish can recreate the appeal of periodic XP-skill power spikes without copying their name, icon, or exact formula. It is optional after ordinary combat already feels good.

Do not assume jumping grants invulnerability, arbitrary wall traversal, or a particular ability-cancel window. Those details were not verified. Choose explicit original rules, expose the landing clearly, and validate movement on the server if multiplayer is active.

## 4. Roles and weapons

The official class overview presents a dual-weapon aggressive melee role (Trojan), a shield/armored role (Warrior), a bow/multi-target ranged role (Archer), and offensive versus restorative Taoist branches; later additions include Ninja, Monk, Pirate, and stance-switching Windwalker. The exact current roster is outside this brief. [S9]

Translate their complementary functions into original roles rather than copying the catalogue:

- **First playable role:** mobile paired-weapon or spear fighter, with basic attack, directional line strike, short radial sweep, and recovery item
- **Second role, only after the first works:** bow user with an aimed shot and controlled cone; this tests projectiles and kiting
- **Third role:** protective caster with shield/heal utility; valuable only once cooperation is real
- Make weapons visible equipment with attack rhythm and silhouette differences. Avoid adding ten classes that share the same effective behavior

Retain a skill-definition/data boundary so new actions can later add range shape, resource cost, valid targets, cast/recovery, and effects without duplicating combat code.

## 5. Town, field, monsters, and the first 15 minutes

The historical onboarding connects zone quests, monster hunting, equipment rewards, class promotion, storage, parties, and return visits. It names distinct regional environments as players progress. [S2] A publisher-hosted 2009 player guide describes an early town exit with weak creatures to hunt. [S10]

### Original first-slice loop

**Arrive → learn leap → leave settlement → defeat a small pack → pick up a drop → equip an upgrade → defeat a stronger encounter → return for a reward.**

Suggested compact content, without expanding the game's existing plan unnecessarily:

- One safe settlement edge containing a trainer/quest NPC, vendor, and clear route into the field
- One field with three recognizably different enemy behaviors: a slow contact attacker, a mobile flanker, and a ranged telegrapher
- One elite using a readable area warning and stronger loot; make it optional until basic controls are understood
- One short hunt objective, one return objective, and visible progress
- A handful of equipment drops with inspect/equip feedback; one earned upgrade changes either appearance or handling
- Defeat/respawn that preserves the player's ability to continue testing; never block the slice behind an unimplemented resource requirement

The goal is not prolonged grinding. The initial slice should demonstrate a satisfying encounter cadence and give a tangible upgrade in minutes. Expand biomes and spawn tiers only after that loop survives repeated play.

## 6. Loot, equipment, and progression

Official guides describe separate equipment level and quality improvements, a five-step quality hierarchy, repair, sockets, gems, and later accumulated enhancements. Rebirth restarts a developed character with additional benefits and class-related possibilities. These are long-term attachment systems, not requirements for first play. [S11, S12]

For the original game:

- Start with three readable rarity bands, a few slots, and deterministic item definitions
- Make ground loot readable by silhouette plus label/icon, with color as an additional cue
- Give each actual item instance a unique identity; separate item definition, rolled attributes, owner, and location
- Make comparisons concise: relevant attack/defense/resource change and weapon role
- Prefer understandable earned upgrades before sockets, random enhancement risk, complex crafting, or prestige resets
- If the first slice saves locally, label that as local prototype progress. Never present local storage as secure cross-device MMO persistence

Rebirth, multi-axis stat systems, epic equipment trees, daily reward ladders, cash-shop power, and randomized enhancement sinks can wait. The historical material supports the value of a compact understandable combat ecosystem; it does not require recreating its monetization.

## 7. Social, PvP, guilds, and trade

Official guides show small teams, friend/enemy relationships, local and directed chat, two-party trade confirmation, and player stalls in a market. [S13, S14] Guild War centers on a capturable objective with different roles contributing damage, defense, and revival. [S15] Open-world PK documentation uses attack modes, criminal-name states, and equipment consequences; exact penalties differ by era and page. [S16]

The design lesson is **visible interdependence**: a town where people can gather; a field where help matters; objective fights where roles differ; a market that makes found equipment useful to others.

First slice: genuine connected-player presence if supported, readable nameplates, and perhaps a consensual duel/training zone. If no networking exists yet, use ordinary NPCs and explicitly call it a single-player prototype. Do not populate fake player names or fabricate a live population count.

Delay: unrestricted PK, stolen/dropped player equipment, guild treasuries, public auction houses, persistent stalls, inter-player currency exchange, territory rewards, and ranked competition. Those features magnify duplication exploits, authority bugs, cheating, and moderation demands.

## 8. Foundation gates before an MMO economy or competitive play

These are project recommendations, not descriptions of Conquer's implementation. Current official authoritative-server documentation illustrates the core pattern: clients submit inputs, the server validates and changes central state, and validated changes are broadcast. It does not make secure game rules automatic. [T1]

1. **Combat authority:** server owns position bounds, collision/landing validation, cooldowns, resources, target validity, damage, death, monster AI, RNG, rewards, and pickup eligibility. The client may predict presentation but cannot award itself results.
2. **Identity and protocol:** authenticated sessions; schema validation; bounded payloads and action rates; sequence/order handling; reconnect behavior. Reject impossible speed, repeated reward requests, and unknown action/item IDs.
3. **Persistence:** versioned character/item schema, atomic ownership changes, durable transaction IDs, backups, and recovery testing. A crash between removing and granting an item must not lose or duplicate it.
4. **Trade safety:** offer versioning, server escrow/locking, both parties confirming the exact current contents, automatic confirmation reset on any change, atomic commit, audit record, and disconnect cancellation.
5. **PvP fairness:** explicit safe zones/consent, tested prediction and reconciliation under latency, clear hit/landing rules, abuse reports, and combat logs. Avoid irreversible losses until these pass.
6. **Scale evidence:** test actual concurrent sessions, interest filtering, tick-time budget, memory, reconnection, and spawn density. Do not infer MMO scale from a two-client demo.

Minimum adversarial checks before persistent rewards: double pickup, duplicated reward request, simultaneous item transfer, death during pickup, disconnect during trade, stale trade confirmation, impossible leap, resource underflow, reconnect replay, and save/load migration.

## 9. Evidence and acceptance priorities

**Highest priority:** movement/leap response, directional hit consistency, reliable kill/loot/equip loop, readable collision and occlusion, stable camera, repeatable respawn.

**Then:** a second distinct combat role, cooperative encounter, real connected sessions, durable character progress.

**Later:** trading, guild ownership, criminal systems, prestige loops, and large-scale competition after the corresponding foundation gates are demonstrated.

The first deliverable should state exactly what is playable, what is genuinely networked, what is stored and where, which tests were run, and which assets are original or licensed.

## Source register

### Publisher descriptions and gameplay guides

- **S1 — Official introduction:** https://co.99.com/guide/info/introduction_t.shtml (archival introduction; genre and 2003 origin)
- **S2 — Official historical onboarding:** https://co.99.com/index/new.shtml (controls, field/quest progression, services; page includes 2014-era news)
- **S3 — Official weapon skills:** https://co.99.com/guide/skills/m_weaponsk.shtml (active skills, stamina/mana distinction)
- **S4 — Official Classic retrospective, January 22, 2010:** https://co.99.com/content/2010-01-22/20100122015921993.shtml
- **S5 — Official returning-player guide:** https://co.99.com/guide/event/co%20basics.shtml (2017 graphics date, later systems; archival copy)
- **S6 — Official Origin-server feature description:** https://co.99.com/guide/event/origin_server_-_unique_gameplay.shtml (staged feature scope)
- **S7 — Publisher-hosted player-authored weapon guide, March 31, 2008:** https://co.99.com/content/2008-03-31/20080331184628394.shtml (historical player testimony about aim/timing)
- **S8 — Official skill introduction:** https://co.99.com/guide/skills/skillsintro.shtml (active, passive, XP abilities)
- **S9 — Official class overview:** https://co.99.com/guide/classes/ (role/weapon contrasts, not a guaranteed current census)
- **S10 — Publisher-hosted player guide, March 24, 2009:** https://co.99.com/content/2009-03-24/20090326231511508%2C1.shtml (early hunting-loop testimony)
- **S11 — Official equipment improvement:** https://co.99.com/guide/guides/improve.shtml (quality, level, repair)
- **S12 — Official rebirth introduction:** https://co.99.com/guide/reborn.shtml
- **S13 — Official team interface:** https://co.99.com/guide/guides/teamint.shtml
- **S14 — Official trade FAQ:** https://co.99.com/guide/faq/trade.shtml (bilateral trade and player booths)
- **S15 — Official weekly Guild War:** https://co.99.com/guide/quests/guildwar.shtml (objective and roles; do not reuse indexed schedule as a current fact)
- **S16 — Official PK overview:** https://co.99.com/guide/guides/aboutpk.shtml (modes, notoriety, equipment consequence example; era-sensitive)

### Inspected visual references (reference-only)

- **V1 — Official legacy objective-court screenshot:** https://co.99.com/templates/0812_simpic.shtml?url=https://hw.99.com/uploads/conquer91e/images/guides/quests/images/guild1.jpg
- **V2 — Official legacy fortress-gate screenshot:** https://co.99.com/templates/0812_simpic.shtml?url=https://hw.99.com/uploads/conquer91e/images/guides/quests/images/guild2.jpg

### Optional licensed art and technical reference

- **A1 — Kenney Nature Kit, original asset page, CC0:** https://kenney.nl/assets/nature-kit
- **A2 — Kenney commercial-use/attribution statement:** https://kenney.nl/support
- **T1 — Heroic Labs authoritative multiplayer documentation:** https://heroiclabs.com/docs/nakama/concepts/multiplayer/authoritative/ (architectural reference, not a mandatory backend choice)
