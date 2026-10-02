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

## Focused control research and Jadebound defaults

Expanded 2026-10-02 after the explicit requests for many gear items, researched skills/effects, level-dependent progression and controls closer to Conquer. The following distinguishes documented legacy PC behavior from current class-specific behavior. No full 2026 default-keybinding export was available, so this is not a claim that every historic binding is unchanged.

| Action | Verified official behavior | Jadebound adaptation |
|---|---|---|
| Walk/run | Left-click destination; UI toggles walk/run. [Getting Started](https://co.99.com/guide/guides/gettingstartednew.shtml) | Primary destination movement with immediate marker and path response. Optional WASD is secondary |
| Jump | Hold Ctrl and left-click ground. Same onboarding source | Ctrl+left-click leap with a visible landing point; validate destination, collision and range |
| Basic attack | Click monsters to fight in onboarding; an [official 2009 event walkthrough](https://co.99.com/guide/quests/valentinequest.shtml) explicitly says left-click to defeat enemies | Left-click hostile selects and requests basic attack; movement should bring the player into valid range, with explicit cancellation |
| Active skill | Open skill panel/select skill, then right-click target; summons use blank ground. [FAQ skill section](https://co.99.com/guide/faqs.shtml) | Right-click casts the selected active skill toward the pointer, valid entity or ground location according to its target type |
| Skill selection | [Skills Intro](https://co.99.com/guide/skills/skillsintro.shtml) describes selecting an active skill in the panel with the correct weapon equipped | Hotbar clearly shows selected skill and its valid target shape; changing weapons updates compatibility immediately |
| Item pickup | Dedicated [Item Usage Guide](https://co.99.com/guide/items/guide.shtml) explicitly says left-click ground item | Left-click visible item/label to approach and collect when permitted |
| Equip/use | Right-click inventory item, or drag to equipment slot; double-click equipped item to unequip. [Status](https://co.99.com/guide/guides/statusint.shtml) | Contextual right-click equip/use and drag equip; expose a clear unequip action and every failed requirement |
| Hotbar | Drag items/skills onto F1-F10 slots. [Getting Started](https://co.99.com/guide/guides/gettingstartednew.shtml) | F1-F10 as a reference-style preset. Skills select for right-click aim by default; consumables/self-actions can activate immediately |
| Custom shortcuts | [Options](https://co.99.com/guide/guides/setupint.shtml) supports skills/items/actions; [Action interface](https://co.99.com/guide/guides/actionint.shtml) documents Alt/Ctrl/Shift plus a chosen key | Rebindable actions; show actual current bindings. Number-key or direct-cast presets are optional adaptations, not claimed original defaults |
| Equipment sets | Main/alternate switch can be put on shortcut bar; empty alternate slots fall back to main. [Alternative Equipment](https://co.99.com/guide/guides/alternativeequipment.shtml) | Explicit loadout action, assignable to hotbar; define fallback and atomically refresh meshes, stats, skills and effects. No universal fixed swap key verified |
| Chat/send | Enter sends typed text. Shift+left-click player, Alt+click message, typed name or chat-list entry selects recipient. [Chat interface](https://co.99.com/guide/guides/chatint.shtml) | Enter enters/sends chat; Shift+click a player can prepare a whisper. Text focus must suppress movement, attacks and hotbar actions |
| Combat target cycling | No universal Tab-to-target rule verified in the official sources inspected | Pointer targeting first. Any target-cycle binding is a clearly labelled optional original convenience |
| Mounted movement | Alt+left-click charge; Ctrl+left-click jump. [Mounted Combat](https://co.99.com/guide/guides/mountedcombatsystem.shtml) | Defer until mounts exist; do not give the same modifier conflicting actions in one state |
| Current class-specific input | [Dune Wanderer skill page](https://co.99.com/guide/quests/dune_wanderer_-_skills.shtml) uses a left-button dash prompt after a qualifying leap and right-click destination leap attacks | Ability states can temporarily reinterpret input, but must visibly explain the state and preserve predictable cancellation |

**Control caveats:** older onboarding says right-click a dropped coin, while the dedicated item guide explicitly says left-click pickup; the Fire skill page also mentions double-click book pickup. The chosen Jadebound default is left-click context interaction, a deliberate resolution of inconsistent archival documentation. Enter-to-open chat, Escape-to-cancel and direct hotbar casting are sensible original UX decisions, not verified universal Conquer defaults. Do not claim holding either mouse button auto-repeats at a specific rate without runtime evidence.

### Input behavior that matters more than a key list

Resolve UI clicks before world actions. Resolve Ctrl+left-click as jump before ordinary movement. A left-click should identify whether the pointer means loot, NPC, hostile or terrain; the cursor and highlight must agree. Right-click should use the selected skill's target rule: aimed line/cone, point-area, unit, ally, self or corpse. An aimed ground strike must not silently become guaranteed homing damage. Chat focus, menus and drag operations consume input. Show a concise reason for no target, wrong weapon, insufficient resource, low level or cooldown.

## Skill progression and effect families

The official [Skill interface](https://co.99.com/guide/guides/skillint.shtml) exposes skill rank and progress earned by using that skill. This is separate from character level, weapon proficiency and the XP-skill charge opportunity. [Skills Intro](https://co.99.com/guide/skills/skillsintro.shtml) connects learning to class, weapon, proficiency and level, through books or trainers; XP skills have class/level requirements. The [Training Ground guide](https://co.99.com/guide/guides/trainingground.shtml) provides a historical level-20+ proficiency-training route. These are distinct progression axes.

The table samples documented mechanics to cover distinct gameplay/VFX needs. Numbers belong to the linked reference pages, not proposed Jadebound balance. Paces, range and distance are source units, not meters or Godot units. Omitted cooldowns are unknown, not zero. “Fixed” is the terminal entry in those tables, not proof that any arbitrary skill cannot improve.

| Reference skill family | Documented gates and progression | Cost, target shape and timing evidence | Original animation/VFX requirement |
|---|---|---|---|
| Blade/sword aimed strike | [Weapon skills](https://co.99.com/guide/skills/m_weaponsk.shtml): initial character 40; ranks gated at 50/60/70 plus skill experience | 20 stamina; separate range/distance columns; straight-line behavior confirmed in 2019 preview below | Directed weapon release, thin ground corridor, aligned repeated impact accents; actual intersection decides hits |
| Shield Block | Same weapon guide: character 40 initially, rank gates 50/70/90/110 | 50 stamina; documented buff lasts 30-60 seconds by rank | Guard pose, shield-face emphasis and brief contact flash; defensive state icon |
| Weapon passive | Same guide: sword Phoenix begins at character 30, chance rises with rank | Automatically triggers during attacks; source lists proc chance and skill XP | Brief exceptional hit motif subordinate to the basic attack; no extra active button |
| Dual-weapon radial sweep | [Trojan](https://co.99.com/guide/skills/m_trojan.shtml): two one-handed weapons; initial character 40, later 70/80/90/100 | Hercules costs 30 stamina and hits around caster; radius changes with rank | Torso-led spin, low radial arc, readable feet and recovery |
| Epic paired-weapon line | Same Trojan guide: two Epic weapons; initial character 40 | Fatal Cross costs 25 stamina; directional path affects targets within 3 paces along it | Separate emitted projectile/path effect from ordinary blade trail; gear gate is functional |
| Speed XP mode | Same Trojan guide: charged XP skill | Super Cyclone documented 40-second duration, faster movement/attacks and halved stamina costs; XP cannot recover during it | Temporary motion accent and clear duration; remove on expiry and death |
| Bow cone | [Archer](https://co.99.com/guide/skills/m_archer.shtml): Scatter starts character 23, later gates 32/48/54/66/72 | Sector attack; arrow cost changes with rank | Bow draw/release, separated fan projectiles and target impacts |
| Bow flight and burst | Same Archer page: XP flight at 15; Arrow Rain at 70; ordinary flight at 70/100 | XP Arrow Rain is a sector; ordinary flight lists 40/60-second durations | Flight is a combat state with shadow/height clarity; do not implement cosmetic wings as automatic flight |
| Early magic and heal | [Water Tao](https://co.99.com/guide/skills/m_watertao.shtml): Thunder and Cure start at character 1 with further rank gates | Initial Thunder 1 MP; Cure 10 MP. Healing Rain starts 40/150 MP; Pray revival 70/1000 MP | Distinguish hostile bolt, ally healing pulse, team heal and corpse revival; target rules must be explicit |
| Spell prerequisite chain | [Fire Tao](https://co.99.com/guide/skills/m_firetao.shtml): Fire requires character 40 plus Thunder rank 4; Tornado requires character 90 plus Fire rank 3 | Initial costs 21 MP and 32 MP respectively; separate mastery XP in table | New spell silhouette and cast gesture at milestones, not just larger damage text |
| Delayed caster burst | Same Fire guide: Flame Lotus is Epic-weapon-exclusive; initial level 50 | 8-second countdown,90-second cooldown; interruption changes result | Visible charging object/zone, countdown and interrupt response; avoid copying the lotus texture/design |
| Martial spin and line | [Monk](https://co.99.com/guide/skills/m_monk.shtml): prayer beads; Whirlwind Kick 15, Radiant Palm 40 | Both 20 stamina; kick cooldown 1.5 s; palm strikes targets in a row | Full-body kick plus outward swirl versus a sharply directed palm wave |
| Cleanse and aura | Same Monk guide: Tranquility 70; one aura type active at once | 25 stamina + 100 MP; 3-second cooldown, removed with two Epic weapons | Readable cleanse cue and persistent state icon; bounded team aura, separate from gear rarity |
| Mark and shot loop | [Pirate](https://co.99.com/guide/skills/m_pirate.shtml): pistol for Eagle Eye; rapier for Blade Tempest | Eagle Eye 20-second cooldown; marks can reset it. Tempest 20 stamina | Distinct shot/rapier gestures, visible target mark and cooldown-ready feedback |
| Bomb displacement and XP area | Same Pirate page: bomb skill and Cannon Barrage XP family | Bomb 20 stamina/20-second cooldown; XP area pulses every 2 seconds | Point-area explosive burst/displacement cue versus repeated timed pulses |
| Modern movement state | [Dune Wanderer](https://co.99.com/guide/quests/dune_wanderer_-_skills.shtml): Moonward Leap ranks 0-9 | Qualifying jump over 4 paces exposes left-click dash prompt; state 10 s/up to 4 triggers; cooldown 20→10 s | Visible input window and destination accent; do not infer permanent jump invulnerability |
| Modern leap and delayed line | Same Dune page: Swallow Dive and Cliff Crusher | Dive right-clicks into a 6-pace frontal cone; 30 s cooldown. Crusher 12×3 forward rectangle, endpoint burst after 1 s; 5 s cooldown | Cone landing accent versus long ground corridor plus separately telegraphed endpoint burst |

**XP modes:** the charge opportunity is not character experience spent as currency. Official legacy instructions expose a short selection window once full, then right-click activation. The old FAQ's approximate 5-10-minute recharge is not a verified modern universal timer. Individual XP modes may change movement, damage, targets or kill rewards. Jadebound should expose a charge meter, ready state, selected burst and duration, without forcing the historical recharge length.

**Quest and equipment gates:** trainers/books are not the only unlock sources. [Pure skills](https://co.99.com/guide/pureskills.shtml) depend on class-life history; Epic skills depend on specific gear/quests; the 2026 Dune page explicitly says that class has no reborn skill. Keep prerequisites data-driven and inspectable. Do not assume all classes inherit every legacy rule.

### Source conflicts that must remain visible

The Monk page gives different table/prose acquisition levels for Serenity and Tyrant Aura. The Pirate page conflicts on several learn levels, target counts and damage percentages. The Dune page describes a Sky Step state lasting 2 seconds yet triggering a surrounding attack every 5 seconds. These contradictions prevent treating the pages as authoritative executable balance data. The matrix uses unambiguous examples and labels reference mechanics; uncertain values require in-game verification for that exact version. No source in this pass establishes animation startup/recovery frames or a universal attack cadence.

## Actually observed skill visuals

The [June 2019 official Trojan skill preview](https://co.99.com/news/2019-06-13/first_look_at_trojan-inspired_skills_coming_with_the_new_expansion.shtml) contains two 292×192 animated demonstrations. Both were visually inspected in the public cloud browser at multiple sampled phases:

- The directional strike displays cyan-white blade/light spikes aligned along a ground corridor, with taller bright streaks and individual hit numbers over practice targets
- The radial strike displays a low orange-gold ellipse around the caster, luminous ribbons and a strong central flash; another sampled phase exposes the body inside a clearer ring

These observations distinguish attack geometry and effect layering. They do not measure cast duration, cancel windows, particle rate or hit timing. The preview itself warns that release details may change. The effect is a skill demonstration, not evidence of Super-quality equipment VFX. Older official video links point to legacy Flash/MediaWrap pages and did not provide usable modern playback in this pass. The user's separate YouTube clip remains unobserved.

Use original procedural geometry/materials: narrow attack strips with fade, short ground ripples, actual weapon trails, hit sparks, impact dust and bounded color accents. Synchronize each effect's start, hit and finish to the authoritative action. Do not extract effect textures or turn public reference animations into shipped assets.

## Server-enforced progression and original starter skill plan

This is the recommended Jadebound contract, not a description of Conquer's server implementation or a claim that Jadebound already enforces it.

On learn/upgrade, validate character level, class/promotion, prerequisite skill rank, quest completion, weapon proficiency, cost and unlocked source. On equip and loadout switch, validate item ownership/location, slot compatibility, required level/class/proficiency/stats and paired/two-hand rules. On cast, revalidate currently equipped compatible weapons, learned rank, alive/state status, cooldown, resource, range, target type, line of sight/collision, zone/consent and action sequence.

The server selects damage/procs/rewards and advances mastery from valid resolved actions. Clients request an action ID and target, not a level, damage amount, reward or mastery increment. Use one equipment revision for a swap so neither old bonuses nor an incompatible old skill can remain active. Eligibility must not bootstrap itself from the very item being equipped. Define respec, unequip, death, rebirth and save migration behavior rather than leaving over-level gear silently valid.

Keep original starter tuning simple and explicit:

| Original action | Proposed unlock | Purpose and target | Progression distinction |
|---|---|---|---|
| Reed Cut | Level 1, compatible melee weapon | Basic selected-target strike | Weapon handling/proficiency grows from valid hits |
| Threading Arc | Level 5 plus first training task | Aimed line; stamina | Rank 2 at 15 plus mastery threshold; rank 3 at 30 plus mastery |
| Circle Step | Level 10 plus camp contract | Caster-centered sweep; stamina | Improved reliability/reach can be a milestone, with separate tuning |
| Brace | Level 5 with shield | Temporary guarded state; stamina | Shield-specific pose and block response; cannot cast without shield |
| Reed Volley | Level 5 with bow plus training task | Aimed cone | Projectile/arrow policy must be explicit; mastery is separate from bow quality |
| Mending Current | Level 5 with caster implement | Ally/self heal; mana | Target rules, amount and mastery separate from cosmetic aura |
| Clear Current | Level 15 plus elite-contract reward | Charged temporary combat mode | Charge is not level XP; duration and recharge are original playtest values |

Names and thresholds are proposals. Preserve existing project naming where appropriate. Do not advertise future class actions as playable before they have distinct animation, feedback and verified gameplay. Gear breadth and a clear level-dependent progression are detailed in the [equipment catalogue extension](equipment-rarity-and-vfx-reference.md).

Minimum meaningful checks: below-level and wrong-class equip rejected; valid-level/insufficient-proficiency rejected; locked skill cannot cast; lower rank cannot request higher-rank result; low resources/cooldown/out-of-range/invalid target rejected; swap removes incompatible ability and stale effects; duplicate input does not grant extra mastery; reload preserves rank/gates; UI and chat clicks do not fire world actions.

## Focused class-art requirements for the current redesign

Added 2026-10-02. This is a compact visual implementation brief for the current hero, with bow/caster contrast reserved for later. It does not expand the promised playable roster. **Observed** means pixels actually inspected; **documented** means official text; **recommendation** means an original Jadebound design choice. Pose descriptions from stills do not establish animation sequences, handedness rules, frame timing or weapon-grip biomechanics across all versions.

### Three distinct visual profiles

| Profile | Evidence and boundary | Original art/animation requirements |
|---|---|---|
| First melee hero: paired weapons | **Observed:** the [2010 paired-weapon still](https://hw.99.com/uploads/co/ind/conew/100414_co_artifact4.jpg) shows an adult-sized head, narrow waist, separated long legs, layered shoulder/forearm/greave pieces and two slim blades. Its action pose has bent elbows, turned torso, a raised knee and crossing weapon diagonals. **Documented:** [Trojan skills](https://co.99.com/guide/skills/m_trojan.shtml) separate a surrounding sweep from an Epic-weapon directional path. The [2019 preview](https://co.99.com/news/2019-06-13/first_look_at_trojan-inspired_skills_coming_with_the_new_expansion.shtml) visually confirms a low radial ring versus a cyan-white line corridor. Neither source proves exact startup or recovery timing | Build a continuous adult body under fitted lamellar plates and a split cloth skirt. Keep a visible grip and guard in each hand, clearance between blade and forearm, and different leading/supporting arm poses. Animate weight transfer through feet, hips, torso and shoulders; follow with elbows and wrists. Give the basic slash, aimed release and radial sweep different silhouettes. Trails follow actual blade paths; hit accents occur at resolved contact. A jump has an airborne pose and a grounded landing recovery |
| Future bow user | **Observed:** the [2010 bow still](https://hw.99.com/uploads/co/ind/conew/100414_co_artifact2.jpg) retains curved limbs, a compact armored torso and separate legs under its emissions. It does **not** clearly demonstrate a complete nock/draw/release cycle. **Documented:** the [Archer class guide](https://co.99.com/guide/classes/archer.shtml) describes light armor and mobile ranged combat; [skill tables](https://co.99.com/guide/skills/m_archer.shtml) distinguish sector attacks and concentrated repeated shots | Use a torso-facing/aiming offset, stable bow hand, visible draw-hand travel and arrow alignment. Release a projectile from the nock position when the release pose occurs. Slim shoulder pieces and short split panels leave the draw arm and stride clear. Keep the bow's negative space and string readable. Cone volleys show several diverging paths; a focused shot shows one dominant path. These are original handling requirements, not measured reference animation |
| Future caster | **Observed:** the [2010 caster still](https://hw.99.com/uploads/co/ind/conew/100414_co_artifact3.jpg) shows a fitted upper torso, layered long blue/purple robe panels, broad decorated hems, bent arms and a weapon extended across the body in one pose. **Documented:** [Water Taoist](https://co.99.com/guide/classes/watertao.shtml) uses robes/backswords and support magic; the [2015 update](https://co.99.com/guide/event/2015/taoistascend/) adds Epic backswords and a Hossu implement. A generic two-handed wizard staff is not the sole reference loadout | Give the casting hand a readable gather/aim/release gesture and keep the implement anchored to a real grip. Overlapping sleeves/hem panels follow the turn while preserving leg or foot contact cues. Offensive magic has a directed launch and impact; healing emphasizes the selected ally; revival emphasizes the valid corpse and completion. A staff remains a permissible original Jadebound choice, but should be labelled an adaptation |

The stills come from the publisher's [April 2010 artifact preview](https://co.99.com/content/2010-04-14/20100414022125268.shtml), not a controlled base-equipment comparison. Their ornate shoulders and effects should not override the class guide's relative armor weight. Exact bow-string travel, finger placement, footwork sequences and current caster animations remain unobserved.

### Promotion and visible equipment are separate decisions

The legacy [Trojan class page](https://co.99.com/guide/classes/trojan.shtml) explicitly gates dual wielding at level 40. The [Water guide](https://co.99.com/guide/classes/watertao.shtml) places the Fire/Water choice at 40, while the [class overview](https://co.99.com/guide/classes/) links the Archer's throwing-knife form to a level-40 promotion. These are historical gates, not universal current server rules. The later [Improved Job Promotion](https://co.99.com/guide/event/improved_job_promotion.shtml) page describes requirement/attribute/prestige progression and has differing titles and branch labels. Do not merge those tables into one exact chronology.

Promotion rewards may provide weapon/headgear/armor, but the inspected sources do not establish a mandatory body or costume transformation at every promotion. For Jadebound, make an earned milestone grant a concrete visible gear option or a new action, then show its equipped result. Preserve the same adult anatomy. Quality glow, item-level silhouette, class promotion and cosmetic override remain separate. A garment can hide base armor, and a weapon accessory can override weapon appearance; inspect UI should reveal the underlying item. See the [equipment/VFX matrix](equipment-rarity-and-vfx-reference.md).

### Immediate acceptance bar

Finish the current melee hero before producing contrasting roles. Review both existing kits in neutral light with VFX disabled: front/side/back stance, stride, jump, basic strike, aimed skill and radial sweep. Require connected joints, stable grips, purposeful foot support, visible waist/knees and armor that bends or separates plausibly. The kit swap must change weapon and armor geometry, not just tint. Restore weapon-local glow only after those checks; preserve body shading and ground contact. At gameplay zoom, the silhouette and action direction should remain legible without labels or a large aura. This is a visual review plan, not a claim that these animation states or fixes are already implemented.

## Source cautions

- The official site's navigation and undated evergreen pages retain outdated class counts and balance text. A recent crawl date does not make the article modern.
- Some skill prose and tables disagree internally, so the report takes combat shapes and roles rather than exact coefficients.
- 2009 Classic, 2013-era general guides, 2024 Origin baseline, and 2026 server-specific announcements are different evidence sets.
- The original game's proper nouns are recorded for source recognition, not proposed asset or naming choices for the new game.
