# Original Jadebound progression catalog

`game/scripts/progression_catalog.gd` is a deterministic, side-effect-free `JadeProgression` (`RefCounted`) catalog and eligibility validator. It has no scene, renderer, network, filesystem, or `JadeEquipment` dependency. Its short-session tuning is original: **starter 1 / trained 3 / veteran 6**. These are not Conquer requirements and not a promise of complete progression or class implementations.

## Honest implementation coverage

The catalog contains **12 families / 36 design entries**, of which **7 item IDs are currently available**, using **6 unique runtime mesh identifiers**. The other 29 entries are unavailable production targets. Quality, enhancement, purification and cosmetic combinations are not counted as new items or new models.

| Family | Starter design | Trained design | Veteran design |
|---|---|---|---|
| Paired blades | Reedsteel twins (planned) | Splitmoon blades (planned) | Stormglass talons (planned) |
| Polearm | Ferry spear (planned) | **Ironwind glaive** | Dawnspire lance (planned) |
| Bow | Willow bow (planned) | Crescent recurve (planned) | Starwood warbow (planned) |
| Hammer | Quarry maul (planned) | Bellforge hammer (planned) | Embervault crusher (planned) |
| Focus | Riverwood staff (planned) | Lanternspire rod (planned) | Astral Reed scepter (planned) |
| Saber | **Reedblade saber** | Tideguard saber (planned) | **Dawnsteel saber: reused geometry** |
| Lamellar | **Wayfarer coat** | **Warden lamellar** | Dawnward harness (planned) |
| Light armor | Scout wraps (planned) | Reedshadow leathers (planned) | Galeweave suit (planned) |
| Robe | Novice River robe (planned) | Mistfold vestment (planned) | Celestial Tide robe (planned) |
| Headgear | **Wayfarer topknot** | **Warden helm** | Sunthread crown (planned) |
| Boots | Trail boots (planned) | Ironstep greaves (planned) | Cloudwake sabatons (planned) |
| Shield | Woven guard (planned) | Riverstone buckler (planned) | Dawnmirror shield (planned) |

Dawnsteel is an available item with a veteran gameplay gate, but uses `Weapon_Saber`, the same geometry as Reedblade. It is explicitly `distinct_runtime_form=false`. The six actual mesh names are `Gear_Wayfarer`, `Gear_Warden`, `Head_Topknot`, `Head_Warden`, `Weapon_Saber`, and `Weapon_Glaive`. This module records known availability; it does not inspect asset files at runtime. The focused tests compare each available ID/slot/mesh with `JadeEquipment.ITEMS`.

Only the **blade** class is implemented. **guardian** and **cloud_adept** have data-only profile/design entries. Their requirements never authorize gameplay. Planned boots/offhand slots are not accepted by `can_equip`, and planned skills have `available=false`, `action=0`.

The `animation` and `effect` values are descriptive catalog metadata, not claims that separate animation resources or all future VFX exist. Actual combat handlers remain slash/Jade Arc/Threadstrike. Sky Vault is general movement. Existing runtime stats, qualities, cooldowns, resources, meshes and rendering stay in their existing owning modules; this catalog does not replace them or invent usable stats for unbuilt items.

## Server-owned state and trust boundary

`starter_profile(class_id="blade")` returns a fresh dictionary containing:

- `progression_schema`: 1
- `level`: integer 1
- `class_id`: `blade` by default; an unknown class returns `{}`
- `attributes`: base, unequipped `strength=4`, `agility=4`, `spirit=2`, `vitality=4` for blade
- `proficiencies`: nonnegative integer values for all seven weapon/shield families; blade starts with saber 1 **and polearm 1**, others 0
- `mastery`: nonnegative integer earned points for every catalog skill ID, initially 0
- `known_skills`: `["slash", "sky_vault"]` for blade

The server supplies its existing `gear` and `owned_equipment` fields separately. The module does not grant equipment, mutate learned skills, award practice, change attributes, spend resources, or execute abilities. Starting Polearm 1 is deliberate: the current slice has no starter polearm or trainer route; requiring players to practice an inaccessible family before equipping its first weapon would deadlock progression.

**Always pass the server's canonical player object.** A pure dictionary validator cannot establish a dictionary's provenance or detect a fully forged dictionary supplied in place of canonical state. Never merge client profile, level, mastery, attributes, ownership, quality or rank claims into it. RPCs should accept a bounded action/skill/item ID and target, resolve the authenticated player's canonical state, and pass only that state into validation. Unrelated fields such as `client_payload`, `requested_rank`, `is_admin` and `ignore_requirements` are ignored and cannot relax gates.

Base attributes must exclude the proposed item's own bonuses and any cosmetic/enhancement bonuses. This prevents an item qualifying itself. Proficiency rank and skill mastery points are distinct axes. The authoritative world decides award rates and grants them only from valid resolved actions, never from client requests or client counters. Duplicate action sequences, invalid targets and missed/rejected actions must not award practice.

There is no requested-rank cast API. `mastery` is earned progress; `known_skills` is explicit server learning state. A requirement on another skill demands both its learned flag and its mastery points. A high mastery number cannot substitute for an unlearned prerequisite.

## Public API

Every eligibility result has `{ok: bool, reason: String, code: String}`. Success is `{ok:true, reason:"", code:"ok"}`; failure has a stable machine-readable code and an explanatory sentence.

| Function | Contract |
|---|---|
| `starter_profile(class_id="blade")` | Fresh progression fields only; planned profiles exist for design inspection, not authorization |
| `item_definition(item_id)` | Fresh metadata/requirements dictionary; unknown ID returns `{}` |
| `requirements_for_item(item_id)` | Fresh level/class/proficiency/base-attribute/mastery gates; unknown ID returns `{}` |
| `skill_definition(skill_id)` | Fresh skill metadata; unknown ID returns `{}` |
| `requirements_for_skill(skill_id)` | Fresh static skill requirements; weapon-family list and minimum compatible proficiency are in `skill_definition` |
| `validate_profile(player)` | Checks complete progression field shapes, known class, nonnegative integer values, required keys and unique known skill IDs; does not establish ownership, availability or provenance |
| `can_equip(player,item_id,slot)` | Checks known item, runtime slot, correct slot, available asset, profile, explicit ownership, class availability and every item gate |
| `can_learn(player,skill_id)` | Checks runtime skill, profile, class and progression prerequisites, plus sufficient proficiency in at least one compatible family; learning does not require equipping that family |
| `can_cast(player,skill_id,weapon_id)` | Rechecks learn eligibility, explicit learned state, canonical equipped weapon match, weapon family, ownership and current item gates, then actual equipped-family skill proficiency |
| `skill_for_action(kind)` | 1→slash, 2→jade_arc, 3→sky_vault, 6→threadstrike; interact 4/flask 5/unknown→empty string |
| `available_unlocks(player)` | Fresh `{items:[IDs],skills:[IDs]}` of progression-qualified runtime entries; **does not mean owned, learned, granted or currently equipped**; malformed profile→empty lists |
| `catalog_summary()` | Counts design entries, genuinely available items, unique runtime mesh names and implemented/planned handlers/classes separately |

An empty unknown requirements dictionary is not authorization: always use a validation API for actions. The validator rechecks gear during casts, so forcibly inserting a locked item into the loadout cannot grant its abilities. Sky Vault intentionally has no weapon or ownership dependency, although it still requires valid profile, implemented class, level and a learned movement action.

`validate_profile` checks core profile fields rather than rejecting unrelated simulation fields such as position/health/cooldown. Additional progression-map entries must still have string keys and nonnegative integer values. Known-skill lists and inventory lists must be ordinary Arrays, not strings, dictionaries, or packed arrays. Missing expected skill/proficiency entries are invalid rather than silently zero-filled; save migrations should create a fresh default profile and copy validated server-owned fields explicitly. Do not silently downgrade unknown saved state into a fresh account.

Ownership arrays require unique known IDs. A known but unavailable planned ID can be retained in a server inventory for migration/admin diagnostics, but cannot equip or cast. Unknown inventory IDs invalidate the ownership list rather than being silently ignored.

## Exact current item gates

All current requirements are independent of item quality, enhancement, purification, sockets and appearance. Being `super` does not lower or raise the gate; ownership is separately required.

| ID | Slot | Level | Classes | Weapon proficiency | Base attributes | Learned mastery |
|---|---|---:|---|---|---|---|
| `wayfarer_coat` | armor | 1 | all catalog roles | — | — | — |
| `topknot` | head | 1 | all catalog roles | — | — | — |
| `reed_saber` | weapon | 1 | blade | saber 1 | strength 4 | — |
| `warden_lamellar` | armor | 3 | blade/guardian | — | strength 6, vitality 6 | — |
| `warden_helm` | head | 3 | blade/guardian | — | strength 6, vitality 6 | — |
| `ironwind_glaive` | weapon | 3 | blade/guardian | polearm 1 | strength 6 | — |
| `dawnsteel_saber` | weapon | 6 | blade | saber 3 | strength 9, agility 7 | slash 8 |

A listed planned class is still denied by the implementation-availability check. Glaive does not require saber practice, and the veteran saber does not accept polearm practice. Armor's strength/vitality conditions demonstrate attribute gates independently of weapon proficiency and mastery.

For unavailable designs only, generic original placeholder bands use levels 1/3/6, proficiency 1/2/3 where applicable, and primary base attributes 2/6/9. These are design placeholders, not balanced future content; no future item becomes playable simply by satisfying them.

## Current skills, gates and effect direction

| Skill/action | Unlock | Compatible weapon | Mastery prerequisite | Gameplay/effect distinction |
|---|---|---|---|---|
| Reed Cut / `slash` / 1 | Level 1, strength 4 | saber or polearm, proficiency 1 | none | Basic melee arc; weapon motion/contact accents |
| Jade Arc / `jade_arc` / 2 | Level 3, strength 6 | saber or polearm, proficiency 1 | learned slash with 3 points | Self-centered radial sweep; low ground ring |
| Sky Vault / `sky_vault` / 3 | Level 1 | none | none | General ground-destination movement; landing wisp |
| Threadstrike / `threadstrike` / 6 | Level 6, agility 7 | saber or polearm, proficiency 3 | learned Jade Arc with 3 points | Aimed ground corridor; aligned line accents, not a homing target guarantee |

All combat skills require blade class and explicit membership in `known_skills`. The player may learn Threadstrike through Saber 3 or Polearm 3, but casting it with a Saber 2 while having Polearm 3 is still rejected. The skill's level/attributes/mastery/weapon gates remain true after learning; learning is not a permanent bypass for later invalid state.

Planned guardian concepts are Stone Brace (shield contact/guard pulse) and Bellfall (heavy cone impact). Planned cloud adept concepts are Mending Current (friendly ally/self ribbons) and Mist Lantern (delayed visible countdown area). They have original L3/L6 placeholder gates and no executable action ID. No shield mechanic, healing target implementation, delayed spell, mana model, dual wielding, class promotion, charge mode or mastery-based damage scaling is claimed by this module.

## World integration responsibilities (implemented in this slice)

1. Merge the fresh progression profile into newly created canonical players without replacing the world's gear/inventory.
2. Validate `can_equip` before changing equipment and `can_cast` before spending costs, changing cooldowns or generating attack effects. Use canonical equipped weapon ID, never a client-selected replacement.
3. Keep separate world checks for alive/state, cooldown, stamina/resources, target/range/geometry/line of sight, zone/consent and sequence/replay protection. This catalog intentionally does not validate transient combat state or predict outcomes.
4. Award proficiency/mastery and level attributes on the server after valid resolved actions. This module does not decide rates or automatically increment fields.
5. Use `available_unlocks(player).skills` to discover server-authorized learn opportunities; append only genuinely new IDs according to the world's progression policy. Do not grant every `items` entry: that list means qualification, not ownership.
6. On quest reward, give an item if authorized by the quest, then call `can_equip` before auto-equipping it. A rewarded veteran weapon can remain locked in inventory. Never directly equip it because of quality, reward source or the old shortcut.
7. On load/respec and before attacks, preserve valid state or reject/quarantine impossible saves. Recalculate stats and remove stale attachments/effects atomically when accepted gear changes. A failed cast must not award mastery or grant resources.
8. Keep skill/progression UI explanatory: show locked state and exact reason. Distinguish unlocked, learned, owned and available assets.

## Focused regression tests

Source: `game/tests/test_progression_catalog.gd`.

Run from the repository root when no conflicting Godot session is using the project:

```sh
timeout 25s godot --headless --path game --script res://tests/test_progression_catalog.gd
```

Coverage includes starter positive cases; all 36 unique design IDs; runtime ID/slot/mesh alignment; catalog count honesty; action mapping; unknown IDs/slots; unavailable gear/classes/skills; wrong class/weapon/slot; level, proficiency, each attribute and mastery separately; missing learned prerequisites; explicit ownership and equipped-ID revalidation; malformed scalar/nested types and missing fields; false client claims; enhancement/quality/cosmetic independence; detached return values; no mutation of server state; and separate profiles that cannot mutate each other.

These pure tests do not prove network RPC authorization, gameplay sequencing, persistence, resource/cooldown behavior, mesh existence on disk, animation quality or render integration. Those need world/network/visual acceptance tests owned by the integrating implementation.

## Research boundary

The verified distinctions and caveats are in `research/classes-progression-coverage.md` and `research/equipment-rarity-and-vfx-reference.md`. This catalog adapts their separation of level, class, proficiency, base attributes, learned mastery and presentation layers. It does not import reference-game numbers, copy assets, or claim that 36 planned entries are 36 shipped models.

## Current authoritative award tuning

The world grants one point of skill mastery and weapon practice per attack that actually damages at least one living enemy. Hitting multiple targets does not multiply this award; empty swings grant none. Saber/Polearm begin at rank1 and gain one rank per12successful attacks, capped at10. Each earned character level adds one base attribute point. Qualified skills are learned automatically. These short-session values are original prototype tuning and are subject to playtesting.
