# Official Conquer research: classes, progression, quests, and world structure

Checked 2026-10-02. Bounded research of public English `co.99.com` pages; no game client, code, or asset extraction. The implications below are original design recommendations, not a specification for reproducing Conquer.

## Version boundary that matters

| Evidence set | What the official page actually establishes | How to use it |
|---|---|---|
| [Classic CO announcement, 2009-11-08](https://co.99.com/content/2009-11-08/20091108190213492.shtml) | Liberty was scheduled for Nov. 18, 2009. This was a modified CO 2.0 ruleset: no shopping mall, Battle Power, talismans, Dragon Ball leveling, or equipment bonus quests; Ninja Toxic Fog removed; some socketing restricted; increased gem drops; Twin City allowed PK | Historical named product, not a synonym for every old-school interpretation or today's Origin servers |
| [Legacy class overview](https://co.99.com/guide/classes/) | Describes older class identities, including the Archer's Assassin weapon form and Windwalker's stance switching | Useful for silhouettes; it is not a reliable current roster census |
| [Thunderstriker Q&A, 2019-03-10](https://co.99.com/news/2019-03-11/q_a_on_thunderstriker.shtml) | Confirms a 2019 addition, using Stormhammer and Flashaxe, with physical melee and ranged skills | An explicit later addition missing from the older overview |
| [Dune Wanderer release, 2026-01-13](https://co.99.com/news/2026-01-13/the_new_class_dune_wanderer_arrives_in_all_servers__alongside_the_awakening_system.shtml) | Announces the class across all servers. Its storyline requirements differ between Regular/Furnace and Origin/Silver servers | Modern content cannot be inferred from the legacy overview |
| [Origin baseline](https://co.99.com/guide/event/origin_server_-_unique_gameplay.shtml) and [SkyStep launch, 2026-07-13](https://co.99.com/news/2026-07-13/the_new_us_server_skystep_launches_at_2_00_on__jul__14__2026.shtml) | Baseline Origin copy lists Warrior, Trojan, Archer, Taoist, Ninja. SkyStep's July 14 launch explicitly adds Dune Wanderer as a sixth major class. Origin progressively unlocks several later advancement systems | Treat Origin as server-specific, staged progression, not an exact 2003/2009 preservation |

The live [official homepage](https://co.99.com/index/) links the 2026 Dune Wanderer release. No claim here that the matrix below is an exhaustive playable roster for every server.

## Distinct class/weapon silhouettes

| Official reference | Recognizable combat identity from the source | Original design implication |
|---|---|---|
| [Warrior](https://co.99.com/guide/classes/warrior.shtml) | Heavy armor, shield defense, monster-damage XP burst | Broad stance, readable guard reaction, a brief empowered clear window |
| [Trojan skills](https://co.99.com/guide/skills/m_trojan.shtml) | Dual one-handed weapons; a stamina-costing circular attack; epic weapon line attack | Two weapons should change reach/attack geometry, not merely double a damage number |
| [Archer skills](https://co.99.com/guide/skills/m_archer.shtml) | Bow; sector-shaped Scatter, repeated shots, flight, XP Arrow Rain | Visible cone targeting and projectile travel differentiate ranged play |
| [Archer/Assassin relationship](https://co.99.com/guide/classes/) | Assassin is an Archer weapon transformation after level-40 promotion, using throwing knives | A future alternate weapon stance can expand an existing class without another complete class |
| [Water and Fire Taoists](https://co.99.com/guide/classes/), [2015 weapon update](https://co.99.com/guide/event/2015/taoistascend/) | Water emphasizes healing, cleansing and revival; Fire emphasizes offensive magic; backswords have epic weapon paths | Separate support and damage effects visually; a support ability should have an actual ally interaction |
| [Ninja](https://co.99.com/guide/classes/ninjaindex.shtml) | Light armor, dual katanas, burst, poison/anti-heal and monster-only blink-chain XP skill | A mobile fragile fighter needs a clear engage/disengage tool and fast strike silhouette |
| [Monk](https://co.99.com/guide/skills/m_monk.shtml) | Prayer beads; spinning kick, linear palm attack, cleansing, XP movement/kill reward window | Martial movement and a compact aura/cleanse can distinguish a close fighter from sword classes |
| [Pirate](https://co.99.com/guide/skills/m_pirate.shtml) | Rapier plus pistol; marks interact with shot cooldowns; bomb displacement | A two-step mark/payoff loop gives a hybrid class an immediately teachable rhythm |
| [Dragon Warrior](https://co.99.com/guide/classes/) | Nunchaku, rapid repositioning, chained strikes and stamina support | Animate linked impacts and recovery beats rather than another generic slash |
| [Windwalker](https://co.99.com/guide/classes_-_windwalker.shtml) | Fan; melee Stomper and ranged Chaser modes, area skills and recovery | Stance state should visibly change pose, attack geometry and HUD |
| [Thunderstriker, 2019](https://co.99.com/news/2019-03-11/q_a_on_thunderstriker.shtml) | Stormhammer/Flashaxe physical melee/range hybrid | Heavy arcs, impact pauses, and a charged projectile are a distinct design space |
| [Dune Wanderer skills, linked from 2026 launch](https://co.99.com/guide/quests/dune_wanderer_-_skills.shtml) | Jump-to-dash timing prompt, leap/cone strike, passive parry, delayed line/end-point attack; page expressly says no reborn skill | Movement timing and telegraphed shapes carry identity. Avoid assuming every class shares old rebirth inheritance |

These are reference facts. Use original class names, costume shapes, weapons, VFX, animation timing and skill text in the new game.

## Progression and world coverage

| Area | Source-grounded finding | First-slice implication |
|---|---|---|
| Skill layers | [Skills Intro](https://co.99.com/guide/skills/skillsintro.shtml) separates active, passive and XP skills. Weapon/level/proficiency gates and books teach skills; an XP circle enables a temporary activation opportunity | Provide one basic attack, one deliberate active attack, and one visible charged burst. Keep acquisition and charge feedback legible |
| Promotions | [Warrior guide](https://co.99.com/guide/classes/warrior.shtml) lists advancement milestones at 15, 40, 70, 100, 110 with titles and rewards | Use an early milestone that visibly changes a title, gear or attack; use original thresholds |
| Older first rebirth | [2013 requirements](https://co.99.com/guide/event/2013/rebirth/rebirth-1-1.shtml) list 120 for most classes, 110 for Water Taoist. [2013 quest](https://co.99.com/guide/event/2013/rebirth/rebirth-1-2.shtml) combines seven normal gems and Clean Water into a Celestial Stone and permits a class choice | Rebirth is a long-term replay/build-choice system, not a necessary first-hour mechanic |
| Origin rebirth | [Origin Rebirth Quests](https://co.99.com/guide/quests/origin_server_-_rebirth_quests.shtml) instead lists first rebirth at 90 and second at 110 plus highest class title. First uses a simplified Clean Water hunt; second chains collection, summoning, purification and multi-stage boss trials | Never mix Origin and legacy thresholds. For a future prestige system, a brief authored trial is more meaningful than a reset button |
| Pure/reincarnation | [Reincarnation and Pure Skills](https://co.99.com/guide/pureskills.shtml) connects the last three lives' classes to inherited skills; three matching lives enable pure skills. Reincarnation offers a preview of gained/lost skills | If eventually implemented, preview the exact tradeoff and preserve class-history data |
| Quest structure | [Origin quest list](https://co.99.com/guide/event/origin_server_-_original_server_quests.shtml) starts with NPC introductions, then a hunt-for-plume delivery chain; later quests include gathering, recovery and combat | Keep an always-visible current objective, count or carried quest item, return location and reward |
| World structure | [Atlas](https://co.99.com/guide/atlas/atlas.shtml) organizes distinct city/field regions plus Market, adventure areas and dungeon maps | A central service hub connected to increasingly dangerous fields is enough to communicate an MMO world in the slice |
| Early fields | Legacy [Wind Plain monsters](https://co.99.com/guide/monsters/monsters1.shtml): birds at levels 1–15, then ghosts through 25 and mine creatures. [Maple Forest](https://co.99.com/guide/monsters/monsters2.shtml): snakes/bandits/fire creatures at 27–45, with stronger outliers | Make enemy families and danger bands visible through habitat, scale, behavior and distance from safety |
| Later fields | Legacy [Bird Island](https://co.99.com/guide/monsters/monsters5.shtml) includes birdmen, hawks and bandits at roughly 87–103 | Change biome and enemy behavior as progression advances; these numbers are historical guide values, not tuning targets |

## Concrete original first slice

Build one compact loop: hub contract → weak field enemies → recover a quest item with visible progress → return for a weapon upgrade and first class milestone → use the new attack plus charged burst in a denser camp → defeat a miniboss that opens a second region. A readable melee defender, mobile dual-weapon fighter and ranged caster/bow archetype would expose meaningful contrast; ship only as many as can receive genuinely distinct mechanics and animation.

Completion evidence should be playable: objective acceptance, combat feedback, ground loot collection, inventory/equip change, saved progression, return/reward interaction, ability unlock, miniboss victory and a traversable new exit. Treat this as an original proof of the full loop. Persistence, multiplayer, guilds and rebirth should only be claimed when implemented and verified.

## Source cautions

- The official site's navigation and undated evergreen pages retain outdated class counts and balance text. A recent crawl date does not make the article modern.
- Some skill prose and tables disagree internally, so the report takes combat shapes and roles rather than exact coefficients.
- 2009 Classic, 2013-era general guides, 2024 Origin baseline, and 2026 server-specific announcements are different evidence sets.
- The original game's proper nouns are recorded for source recognition, not proposed asset or naming choices for the new game.
