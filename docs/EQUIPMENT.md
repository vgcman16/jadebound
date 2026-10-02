# Visible equipment and authoritative state

Each player has independent `armor`, `head` and `weapon` slots. The authoritative server validates ownership, item identity, compatible slot, character level/class, base attributes, weapon proficiency, skill mastery, alive state and swap/attack cooldown. Clients request an item; they do not send damage, health, defense or a chosen mesh. Snapshots carry the authoritative equipped IDs.

Two original prototype kits are owned initially for this slice; the Warden pieces stay locked until level 3 and their stat/proficiency gates are met:
- Wayfarer: fitted long coat, topknot and Reedblade saber
- Warden: layered lamellar armor, helmet and Ironwind glaive

The quest grants Dawnsteel, a Super-quality saber that requires level 6, Saber3 and Cut mastery. An underqualified character keeps the reward in inventory; the quest never bypasses equip gates. Its modest blade-edge emission and six small weapon-local glints is a separate presentation layer. The original equipment data keeps base mesh, quality, enhancement, purification and cosmetic fields distinct. Only the currently implemented fields affect the prototype. There is no invented universal body halo, gem system, purification service or cosmetic store.

Armor changes vitality, guard and movement speed. The glaive trades a slower strike for more reach and damage. These are original prototype balance values, not a reproduction of another game's combat formulas. Equip never heals the player, including repeated max-health swaps. An unowned item, wrong slot or peer-forged identity is rejected.

Controls: Tab opens the satchel; click a slot or press C (armor), V (head), B (weapon) to cycle owned items. The renderer shows only the selected named mesh per slot and resets old material effects before applying the current equipped weapon's quality layer. Equipment survives local save/load; authoritative online persistence remains future work.

## Visual contract

The modular hero uses a shared skinned body/rig and six separately toggleable skinned meshes. Runtime mesh names: Gear_Wayfarer, Gear_Warden, Head_Topknot, Head_Warden, Weapon_Saber and Weapon_Glaive. The source guide documents bones, UVs/materials and animation. Swapping a slot must visibly change its silhouette, not just its statistics or color.

`tools/capture_equipment.sh` produces matching actual-engine pose review frames for both complete loadouts: normal gameplay scale, close-up idle, running stride, jump apex, landing and attack contact. This automated asset inspection supplements actual gameplay video; it is not a claim of human manual playtesting.

Verification gates: all world/equipment assertions; exact visible slot meshes; native skin/weights/inverse binds; no gaps or outfit clipping across poses; distinguishable materials; no old weapon or effect left behind after swaps. Visual polish is not established by mesh counts or passing data assertions alone.

## Impact timing

The server queues a strike during windup, then resolves damage and emits its effect at 58% of the weapon-specific attack duration. Death cancels pending impact, and equipment swaps are blocked during an attack. A successful damage event grants one mastery/practice point per attack, not per target; empty swings grant none.
