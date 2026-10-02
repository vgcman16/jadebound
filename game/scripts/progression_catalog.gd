class_name JadeProgression
extends RefCounted
## Pure original progression data. Call only with the authoritative server player.
## This module never trusts, merges, or awards anything from an action packet.

const SCHEMA_VERSION = 1
const RUNTIME_SLOTS = ["armor", "head", "weapon", "boots", "gloves"]
const ATTRIBUTE_KEYS = ["strength", "agility", "spirit", "vitality"]
const PROFICIENCY_KEYS = ["saber", "polearm", "paired_blades", "bow", "hammer", "focus", "shield"]
const BANDS = ["starter", "trained", "veteran"]
const BAND_LEVELS = [1, 3, 6]
const CLASS_DATA = {
	"blade": {"label": "Reedblade", "available": true, "attributes": {"strength": 4, "agility": 4, "spirit": 2, "vitality": 4}},
	"guardian": {"label": "Stone Guardian", "available": false, "attributes": {"strength": 4, "agility": 2, "spirit": 2, "vitality": 6}},
	"cloud_adept": {"label": "Cloud Adept", "available": false, "attributes": {"strength": 2, "agility": 3, "spirit": 6, "vitality": 3}}
}
# Three authored design targets per family. A target is NOT a shipped mesh.
const FAMILIES = {
	"paired_blades": {"slot": "weapon", "classes": ["blade"], "proficiency": "paired_blades", "ids": ["reedsteel_twins", "splitmoon_blades", "stormglass_talons"], "labels": ["Reedsteel twins", "Splitmoon blades", "Stormglass talons"], "animation": "paired_blades_planned"},
	"polearm": {"slot": "weapon", "classes": ["blade", "guardian"], "proficiency": "polearm", "ids": ["ferry_spear", "ironwind_glaive", "dawnspire_lance"], "labels": ["Ferry spear", "Ironwind glaive", "Dawnspire lance"], "animation": "polearm"},
	"bow": {"slot": "weapon", "classes": ["blade"], "proficiency": "bow", "ids": ["willow_bow", "crescent_recurve", "starwood_warbow"], "labels": ["Willow bow", "Crescent recurve", "Starwood warbow"], "animation": "bow_planned"},
	"hammer": {"slot": "weapon", "classes": ["guardian"], "proficiency": "hammer", "ids": ["quarry_maul", "bellforge_hammer", "embervault_crusher"], "labels": ["Quarry maul", "Bellforge hammer", "Embervault crusher"], "animation": "hammer_planned"},
	"focus": {"slot": "weapon", "classes": ["cloud_adept"], "proficiency": "focus", "ids": ["riverwood_staff", "lanternspire_rod", "astral_reed_scepter"], "labels": ["Riverwood staff", "Lanternspire rod", "Astral Reed scepter"], "animation": "focus_planned"},
	"saber": {"slot": "weapon", "classes": ["blade"], "proficiency": "saber", "ids": ["reed_saber", "tideguard_saber", "dawnsteel_saber"], "labels": ["Reedblade saber", "Tideguard saber", "Dawnsteel saber"], "animation": "saber"},
	"lamellar": {"slot": "armor", "classes": ["blade", "guardian"], "proficiency": "", "ids": ["wayfarer_coat", "warden_lamellar", "dawnward_harness"], "labels": ["Wayfarer coat", "Warden lamellar", "Dawnward harness"], "animation": "humanoid"},
	"light_armor": {"slot": "armor", "classes": ["blade"], "proficiency": "", "ids": ["scout_wraps", "reedshadow_leathers", "galeweave_suit"], "labels": ["Scout wraps", "Reedshadow leathers", "Galeweave suit"], "animation": "humanoid_planned"},
	"robe": {"slot": "armor", "classes": ["cloud_adept"], "proficiency": "", "ids": ["novice_river_robe", "mistfold_vestment", "celestial_tide_robe"], "labels": ["Novice River robe", "Mistfold vestment", "Celestial Tide robe"], "animation": "robe_planned"},
	"headgear": {"slot": "head", "classes": ["blade", "guardian", "cloud_adept"], "proficiency": "", "ids": ["topknot", "warden_helm", "sunthread_crown"], "labels": ["Wayfarer topknot", "Warden helm", "Sunthread crown"], "animation": "humanoid"},
	"boots": {"slot": "boots", "classes": ["blade", "guardian", "cloud_adept"], "proficiency": "", "ids": ["trail_boots", "ironstep_greaves", "cloudwake_sabatons"], "labels": ["Trail boots", "Ironstep greaves", "Cloudwake sabatons"], "animation": "boots_planned"},
	"shield": {"slot": "offhand", "classes": ["guardian"], "proficiency": "shield", "ids": ["woven_guard", "riverstone_buckler", "dawnmirror_shield"], "labels": ["Woven guard", "Riverstone buckler", "Dawnmirror shield"], "animation": "shield_planned"}
}
# Only these item IDs and mesh names exist in the current runtime.
const RUNTIME_MESHES = {
	"wayfarer_coat": "Gear_Wayfarer", "warden_lamellar": "Gear_Warden",
	"topknot": "Head_Topknot", "warden_helm": "Head_Warden",
	"reed_saber": "Weapon_Saber", "ironwind_glaive": "Weapon_Glaive", "dawnsteel_saber": "Weapon_Saber"
}
const ITEM_OVERRIDES = {
	"wayfarer_coat": {"level": 1, "classes": ["blade", "guardian", "cloud_adept"], "proficiencies": {}, "attributes": {}, "mastery": {}},
	"topknot": {"level": 1, "classes": ["blade", "guardian", "cloud_adept"], "proficiencies": {}, "attributes": {}, "mastery": {}},
	"reed_saber": {"level": 1, "classes": ["blade"], "proficiencies": {"saber": 1}, "attributes": {"strength": 4}, "mastery": {}},
	"warden_lamellar": {"level": 3, "classes": ["blade", "guardian"], "proficiencies": {}, "attributes": {"strength": 6, "vitality": 6}, "mastery": {}},
	"warden_helm": {"level": 3, "classes": ["blade", "guardian"], "proficiencies": {}, "attributes": {"strength": 6, "vitality": 6}, "mastery": {}},
	"ironwind_glaive": {"level": 3, "classes": ["blade", "guardian"], "proficiencies": {"polearm": 1}, "attributes": {"strength": 6}, "mastery": {}},
	"dawnsteel_saber": {"level": 6, "classes": ["blade"], "proficiencies": {"saber": 3}, "attributes": {"strength": 9, "agility": 7}, "mastery": {"slash": 8}}
}
const SKILLS = {
	"slash": {"label": "Reed Cut", "available": true, "action": 1, "band": "starter", "kind": "basic", "target": "melee_arc", "effect": "weapon_contact", "weapon_families": ["saber", "polearm"], "weapon_proficiency": 1, "requirements": {"level": 1, "classes": ["blade"], "proficiencies": {}, "attributes": {"strength": 4}, "mastery": {}}},
	"jade_arc": {"label": "Jade Arc", "available": true, "action": 2, "band": "trained", "kind": "active", "target": "self_radial", "effect": "jade_ground_ring", "weapon_families": ["saber", "polearm"], "weapon_proficiency": 1, "requirements": {"level": 3, "classes": ["blade"], "proficiencies": {}, "attributes": {"strength": 6}, "mastery": {"slash": 3}}},
	"sky_vault": {"label": "Sky Vault", "available": true, "action": 3, "band": "starter", "kind": "movement", "target": "ground_destination", "effect": "landing_wisp", "weapon_families": [], "weapon_proficiency": 0, "requirements": {"level": 1, "classes": ["blade", "guardian", "cloud_adept"], "proficiencies": {}, "attributes": {}, "mastery": {}}},
	"threadstrike": {"label": "Threadstrike", "available": true, "action": 6, "band": "veteran", "kind": "active", "target": "aimed_line", "effect": "thread_ground_corridor", "weapon_families": ["saber", "polearm"], "weapon_proficiency": 3, "requirements": {"level": 6, "classes": ["blade"], "proficiencies": {}, "attributes": {"agility": 7}, "mastery": {"jade_arc": 3}}},
	"stone_brace": {"label": "Stone Brace", "available": false, "action": 0, "band": "trained", "kind": "active", "target": "self_guard", "effect": "shield_contact_pulse_planned", "weapon_families": ["shield"], "weapon_proficiency": 1, "requirements": {"level": 3, "classes": ["guardian"], "proficiencies": {"shield": 1}, "attributes": {"vitality": 6}, "mastery": {}}},
	"bellfall": {"label": "Bellfall", "available": false, "action": 0, "band": "veteran", "kind": "active", "target": "ground_cone", "effect": "heavy_impact_fan_planned", "weapon_families": ["hammer"], "weapon_proficiency": 3, "requirements": {"level": 6, "classes": ["guardian"], "proficiencies": {"hammer": 3}, "attributes": {"strength": 9}, "mastery": {"stone_brace": 3}}},
	"mending_current": {"label": "Mending Current", "available": false, "action": 0, "band": "trained", "kind": "support", "target": "ally_or_self", "effect": "friendly_rising_ribbons_planned", "weapon_families": ["focus"], "weapon_proficiency": 1, "requirements": {"level": 3, "classes": ["cloud_adept"], "proficiencies": {"focus": 1}, "attributes": {"spirit": 6}, "mastery": {}}},
	"mist_lantern": {"label": "Mist Lantern", "available": false, "action": 0, "band": "veteran", "kind": "active", "target": "delayed_ground_area", "effect": "countdown_lantern_planned", "weapon_families": ["focus"], "weapon_proficiency": 3, "requirements": {"level": 6, "classes": ["cloud_adept"], "proficiencies": {"focus": 3}, "attributes": {"spirit": 9}, "mastery": {"mending_current": 3}}}
}

static func starter_profile(class_id: String = "blade") -> Dictionary:
	if not CLASS_DATA.has(class_id):
		return {}
	var proficiencies = {}
	for family in PROFICIENCY_KEYS:
		proficiencies[family] = 0
	proficiencies[{"blade": "saber", "guardian": "hammer", "cloud_adept": "focus"}[class_id]] = 1
	if class_id == "blade":
		proficiencies.polearm = 1
	var mastery = {}
	for skill_id in SKILLS:
		mastery[skill_id] = 0
	return {"progression_schema": SCHEMA_VERSION, "level": 1, "class_id": class_id, "attributes": CLASS_DATA[class_id].attributes.duplicate(true), "proficiencies": proficiencies, "mastery": mastery, "known_skills": ["slash", "sky_vault"] if class_id == "blade" else ["sky_vault"]}

static func requirements_for_item(item_id: String) -> Dictionary:
	if ITEM_OVERRIDES.has(item_id):
		return ITEM_OVERRIDES[item_id].duplicate(true)
	for family in FAMILIES:
		var data: Dictionary = FAMILIES[family]
		var band: int = data.ids.find(item_id)
		if band >= 0:
			var proficiencies = {}
			if data.proficiency != "":
				proficiencies[data.proficiency] = [1, 2, 3][band]
			var attributes = {}
			var attribute = "spirit" if family in ["focus", "robe"] else "strength"
			attributes[attribute] = [2, 6, 9][band]
			return {"level": BAND_LEVELS[band], "classes": data.classes.duplicate(), "proficiencies": proficiencies, "attributes": attributes, "mastery": {}}
	return {}

static func item_definition(item_id: String) -> Dictionary:
	for family in FAMILIES:
		var data: Dictionary = FAMILIES[family]
		var band: int = data.ids.find(item_id)
		if band >= 0:
			return {"id": item_id, "label": data.labels[band], "family": family, "slot": data.slot, "band": BANDS[band], "available": RUNTIME_MESHES.has(item_id), "mesh": RUNTIME_MESHES.get(item_id, ""), "animation": data.animation, "requirements": requirements_for_item(item_id), "original_tuning": true, "distinct_runtime_form": RUNTIME_MESHES.has(item_id) and item_id != "dawnsteel_saber", "note": "Reuses Reedblade geometry; veteran stats/finish only." if item_id == "dawnsteel_saber" else ("Current runtime item." if RUNTIME_MESHES.has(item_id) else "Design target only; mesh and gameplay unavailable.")}
	return {}

static func skill_definition(skill_id: String) -> Dictionary:
	return SKILLS.get(skill_id, {}).duplicate(true)

static func requirements_for_skill(skill_id: String) -> Dictionary:
	return SKILLS[skill_id].requirements.duplicate(true) if SKILLS.has(skill_id) else {}

static func skill_for_action(action: int) -> String:
	for skill_id in SKILLS:
		if SKILLS[skill_id].available and SKILLS[skill_id].action == action:
			return skill_id
	return ""

static func can_unequip(player: Dictionary, slot: String) -> Dictionary:
	# Removing gear never creates/destroys ownership and never bypasses a re-equip gate.
	if not slot in RUNTIME_SLOTS:
		return _denied("unsupported_slot", "That equipment slot is not implemented.")
	var validity = validate_profile(player)
	if not validity.ok:return validity
	return _validate_ownership(player)

static func can_equip(player: Dictionary, item_id: String, slot: String) -> Dictionary:
	var definition = item_definition(item_id)
	if definition.is_empty():
		return _denied("unknown_item", "Unknown equipment item.")
	if not slot in RUNTIME_SLOTS:
		return _denied("unsupported_slot", "That equipment slot is not implemented.")
	if definition.slot != slot:
		return _denied("wrong_slot", "This item does not fit that slot.")
	if not definition.available:
		return _denied("unavailable_item", "This gear is planned; its runtime asset is unavailable.")
	var validity = validate_profile(player)
	if not validity.ok:
		return validity
	var ownership = _validate_ownership(player)
	if not ownership.ok:
		return ownership
	if not item_id in player.owned_equipment:
		return _denied("not_owned", "You do not own this item.")
	return _check_requirements(player, definition.requirements)

static func can_learn(player: Dictionary, skill_id: String) -> Dictionary:
	if not SKILLS.has(skill_id):
		return _denied("unknown_skill", "Unknown skill.")
	if not SKILLS[skill_id].available:
		return _denied("unavailable_skill", "This skill is planned and has no runtime handler.")
	var validity = validate_profile(player)
	if not validity.ok:
		return validity
	var requirements = _check_requirements(player, SKILLS[skill_id].requirements)
	if not requirements.ok:
		return requirements
	var skill: Dictionary = SKILLS[skill_id]
	if not skill.weapon_families.is_empty():
		var trained = false
		for family in skill.weapon_families:
			if player.proficiencies[family] >= skill.weapon_proficiency:
				trained = true
		if not trained:
			return _denied("proficiency", "Requires compatible weapon proficiency %d." % skill.weapon_proficiency)
	return _allowed()

static func can_cast(player: Dictionary, skill_id: String, weapon_id: String) -> Dictionary:
	var eligibility = can_learn(player, skill_id)
	if not eligibility.ok:
		return eligibility
	if not skill_id in player.known_skills:
		return _denied("not_learned", "Learn this skill before using it.")
	var skill: Dictionary = SKILLS[skill_id]
	# General movement does not acquire a weapon gate just because it has an action ID.
	if skill.kind == "movement":
		return _allowed()
	if typeof(player.get("gear")) != TYPE_DICTIONARY or typeof(player.gear.get("weapon")) != TYPE_STRING:
		return _denied("invalid_loadout", "The server loadout is missing or malformed.")
	if player.gear.weapon != weapon_id:
		return _denied("weapon_mismatch", "The requested weapon is not the equipped weapon.")
	var weapon = item_definition(weapon_id)
	if weapon.is_empty() or weapon.slot != "weapon":
		return _denied("wrong_weapon", "Equip a compatible weapon for this skill.")
	if not weapon.family in skill.weapon_families:
		return _denied("wrong_weapon", "This weapon family cannot use this skill.")
	var equipment = can_equip(player, weapon_id, "weapon")
	if not equipment.ok:
		return equipment
	if player.proficiencies[weapon.family] < skill.weapon_proficiency:
		return _denied("proficiency", "Requires %s proficiency %d." % [weapon.family, skill.weapon_proficiency])
	return _allowed()

static func validate_profile(player: Dictionary) -> Dictionary:
	if typeof(player.get("level")) != TYPE_INT or player.level < 1:
		return _denied("invalid_profile", "The server level must be a positive integer.")
	if typeof(player.get("class_id")) != TYPE_STRING or not CLASS_DATA.has(player.class_id):
		return _denied("invalid_profile", "The server class is missing or unknown.")
	for field in ["attributes", "proficiencies", "mastery"]:
		if typeof(player.get(field)) != TYPE_DICTIONARY:
			return _denied("invalid_profile", "The server %s are missing or malformed." % field)
		for key in player[field]:
			if typeof(key) != TYPE_STRING or typeof(player[field][key]) != TYPE_INT or player[field][key] < 0:
				return _denied("invalid_profile", "The server %s must contain nonnegative integer values." % field)
	for key in ATTRIBUTE_KEYS:
		if not player.attributes.has(key):
			return _denied("invalid_profile", "The server base attribute %s is missing." % key)
	for key in PROFICIENCY_KEYS:
		if not player.proficiencies.has(key):
			return _denied("invalid_profile", "The server proficiency %s is missing." % key)
	for key in SKILLS:
		if not player.mastery.has(key):
			return _denied("invalid_profile", "The server skill mastery %s is missing." % key)
	if typeof(player.get("known_skills")) != TYPE_ARRAY:
		return _denied("invalid_profile", "The server learned skills must be an array.")
	var seen = {}
	for skill_id in player.known_skills:
		if typeof(skill_id) != TYPE_STRING or not SKILLS.has(skill_id) or seen.has(skill_id):
			return _denied("invalid_profile", "The server learned skills contain an invalid or duplicate entry.")
		seen[skill_id] = true
	return _allowed()

static func _validate_ownership(player: Dictionary) -> Dictionary:
	if typeof(player.get("owned_equipment")) != TYPE_ARRAY:
		return _denied("invalid_ownership", "The server equipment ownership list is missing or malformed.")
	var seen = {}
	for item_id in player.owned_equipment:
		if typeof(item_id) != TYPE_STRING or item_definition(item_id).is_empty() or seen.has(item_id):
			return _denied("invalid_ownership", "The server equipment ownership list contains an invalid or duplicate entry.")
		seen[item_id] = true
	return _allowed()

static func _check_requirements(player: Dictionary, requirements: Dictionary) -> Dictionary:
	if not player.class_id in requirements.classes:
		return _denied("wrong_class", "Requires class: %s." % ", ".join(requirements.classes))
	if not CLASS_DATA[player.class_id].available:
		return _denied("unavailable_class", "This class is data-only and not playable yet.")
	if player.level < requirements.level:
		return _denied("level", "Requires level %d." % requirements.level)
	for family in requirements.proficiencies:
		if player.proficiencies[family] < requirements.proficiencies[family]:
			return _denied("proficiency", "Requires %s proficiency %d." % [family, requirements.proficiencies[family]])
	for attribute in requirements.attributes:
		if player.attributes[attribute] < requirements.attributes[attribute]:
			return _denied("attribute", "Requires base %s %d." % [attribute, requirements.attributes[attribute]])
	for skill_id in requirements.mastery:
		if not skill_id in player.known_skills or player.mastery[skill_id] < requirements.mastery[skill_id]:
			return _denied("mastery", "Requires learned %s mastery %d." % [SKILLS[skill_id].label, requirements.mastery[skill_id]])
	return _allowed()

static func available_unlocks(player: Dictionary) -> Dictionary:
	var result = {"items": [], "skills": []}
	if not validate_profile(player).ok:
		return result
	for item_id in RUNTIME_MESHES:
		if _check_requirements(player, requirements_for_item(item_id)).ok:
			result.items.append(item_id)
	for skill_id in SKILLS:
		if can_learn(player, skill_id).ok:
			result.skills.append(skill_id)
	return result

static func catalog_summary() -> Dictionary:
	var meshes = {}
	for item_id in RUNTIME_MESHES:
		meshes[RUNTIME_MESHES[item_id]] = true
	return {"families": FAMILIES.size(), "design_entries": FAMILIES.size() * 3, "available_items": RUNTIME_MESHES.size(), "runtime_unique_meshes": meshes.size(), "planned_items": FAMILIES.size() * 3 - RUNTIME_MESHES.size(), "implemented_classes": 1, "planned_classes": 2, "combat_skill_handlers": 3, "movement_handlers": 1}

static func _allowed() -> Dictionary:
	return {"ok": true, "reason": "", "code": "ok"}

static func _denied(code: String, reason: String) -> Dictionary:
	return {"ok": false, "reason": reason, "code": code}
