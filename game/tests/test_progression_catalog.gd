extends SceneTree
const Progression = preload("res://scripts/progression_catalog.gd")
const Gear = preload("res://scripts/equipment_data.gd")
var failures: int = 0
var count: int = 0

func check(ok: bool, label: String):
	count += 1
	if not ok:
		failures += 1
		push_error("FAIL PROGRESSION: " + label)
	else:
		print("PASS PROGRESSION: " + label)

func denied(result: Dictionary, code: String, label: String):
	check(not result.ok and result.code == code and result.reason != "", label)

func player_fixture() -> Dictionary:
	var player = Progression.starter_profile()
	player.gear = Gear.DEFAULT_GEAR.duplicate(true)
	player.owned_equipment = Gear.STARTER_OWNED.duplicate()
	return player

func veteran_fixture() -> Dictionary:
	var player = player_fixture()
	player.level = 6
	player.attributes = {"strength": 9, "agility": 7, "spirit": 2, "vitality": 9}
	player.proficiencies.saber = 3
	player.proficiencies.polearm = 3
	player.mastery.slash = 8
	player.mastery.jade_arc = 3
	player.known_skills.append("jade_arc")
	player.known_skills.append("threadstrike")
	player.owned_equipment.append("dawnsteel_saber")
	return player

func _initialize():
	_test_starter_and_catalog()
	_test_equipment_gates()
	_test_skill_gates()
	_test_malformed_profiles()
	_test_bypass_and_purity()
	if failures == 0:
		print("JADE_PROGRESSION_TESTS_PASSED ", count)
	quit(0 if failures == 0 else 1)

func _test_starter_and_catalog():
	var p = player_fixture()
	check(Progression.validate_profile(p).ok, "starter profile is valid")
	check(p.proficiencies.saber == 1 and p.proficiencies.polearm == 1, "starter knows both runtime weapon families without a training deadlock")
	check(not Progression.starter_profile().has("gear") and not Progression.starter_profile().has("owned_equipment"), "profile leaves inventory and loadout ownership to World")
	check(Progression.starter_profile("unknown").is_empty(), "unknown class has no starter profile")
	check(Progression.can_equip(p, "reed_saber", "weapon").ok, "starter may equip owned starter saber")
	check(Progression.can_equip(p, "wayfarer_coat", "armor").ok, "starter may equip starter armor")
	check(Progression.can_cast(p, "slash", "reed_saber").ok, "starter may perform learned basic attack")
	check(Progression.can_cast(p, "sky_vault", "").ok, "general movement is independent of weapon")
	for pair in [[1, "slash"], [2, "jade_arc"], [3, "sky_vault"], [6, "threadstrike"], [4, ""], [5, ""], [0, ""], [99, ""]]:
		check(Progression.skill_for_action(pair[0]) == pair[1], "action mapping %d" % pair[0])
	var summary = Progression.catalog_summary()
	check(summary.families == 12 and summary.design_entries == 36 and summary.planned_items == 29, "catalog separates 36 targets from 29 planned-only entries")
	check(summary.available_items == 7 and summary.runtime_unique_meshes == 6, "seven actual item IDs reuse only six meshes")
	check(summary.combat_skill_handlers == 3 and summary.movement_handlers == 1 and summary.implemented_classes == 1, "runtime coverage is reported without planned class inflation")
	var all_ids = {}
	for family in Progression.FAMILIES:
		for item_id in Progression.FAMILIES[family].ids:
			check(not all_ids.has(item_id), "unique catalog ID " + item_id)
			all_ids[item_id] = true
			var definition = Progression.item_definition(item_id)
			check(definition.family == family and not definition.requirements.is_empty(), "complete family/gates for " + item_id)
			if definition.available:
				check(Gear.ITEMS.has(item_id) and definition.mesh == Gear.ITEMS[item_id].mesh and definition.slot == Gear.ITEMS[item_id].slot, "real runtime mesh and slot for " + item_id)
			else:
				check(definition.mesh == "", "planned item cannot claim a mesh: " + item_id)
	check(not Progression.item_definition("dawnsteel_saber").distinct_runtime_form, "Dawnsteel is not counted as a new physical form")
	check(Progression.requirements_for_item("missing").is_empty(), "unknown item has no invented requirements")
	check(Progression.requirements_for_skill("missing").is_empty(), "unknown skill has no invented requirements")

func _test_equipment_gates():
	var p = player_fixture()
	denied(Progression.can_equip(p, "made_up", "weapon"), "unknown_item", "unknown item fails closed")
	denied(Progression.can_equip(p, "reed_saber", "ring"), "unsupported_slot", "unknown slot fails closed")
	denied(Progression.can_equip(p, "warden_helm", "weapon"), "wrong_slot", "cross-slot equip fails")
	denied(Progression.can_equip(p, "tideguard_saber", "weapon"), "unavailable_item", "planned same-family model cannot equip")
	denied(Progression.can_equip(p, "trail_boots", "boots"), "unavailable_item", "accessory slot exists but unintegrated asset stays unavailable")
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "not_owned", "unowned item denied before character gates")
	denied(Progression.can_equip(p, "warden_lamellar", "armor"), "level", "level gate cannot be bypassed by ownership")
	p.level = 3
	denied(Progression.can_equip(p, "warden_lamellar", "armor"), "attribute", "level alone does not satisfy armor attributes")
	p.attributes.strength = 6
	denied(Progression.can_equip(p, "warden_lamellar", "armor"), "attribute", "each independent armor attribute is required")
	p.attributes.vitality = 6
	check(Progression.can_equip(p, "warden_lamellar", "armor").ok and Progression.can_equip(p, "warden_helm", "head").ok, "trained Warden pieces qualify after both attributes")
	p.proficiencies.polearm = 0
	denied(Progression.can_equip(p, "ironwind_glaive", "weapon"), "proficiency", "glaive checks its own proficiency")
	p.proficiencies.saber = 50
	denied(Progression.can_equip(p, "ironwind_glaive", "weapon"), "proficiency", "saber practice cannot replace polearm handling")
	p.proficiencies.polearm = 1
	check(Progression.can_equip(p, "ironwind_glaive", "weapon").ok, "trained glaive passes actual independent gates")
	p = veteran_fixture()
	p.class_id = "cloud_adept"
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "wrong_class", "high level wrong class remains ineligible")
	p.class_id = "guardian"
	denied(Progression.can_equip(p, "warden_lamellar", "armor"), "unavailable_class", "even matching planned class cannot be played")
	p = veteran_fixture()
	p.level = 5
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "level", "veteran needs level six")
	p.level = 6
	p.proficiencies.saber = 2
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "proficiency", "veteran needs saber three")
	p.proficiencies.saber = 3
	p.attributes.agility = 6
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "attribute", "veteran needs agility independently")
	p.attributes.agility = 7
	p.mastery.slash = 7
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "mastery", "veteran needs earned Slash mastery")
	p.mastery.slash = 8
	p.known_skills.erase("slash")
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "mastery", "mastery points cannot substitute an unlearned prerequisite")
	p.known_skills.append("slash")
	check(Progression.can_equip(p, "dawnsteel_saber", "weapon").ok, "all independent veteran gates pass")

func _test_skill_gates():
	var p = player_fixture()
	denied(Progression.can_cast(p, "forged_skill", "reed_saber"), "unknown_skill", "unknown skill fails closed")
	denied(Progression.can_cast(p, "stone_brace", "reed_saber"), "unavailable_skill", "planned skill never authorizes a runtime cast")
	denied(Progression.can_cast(p, "slash", "ironwind_glaive"), "weapon_mismatch", "client weapon claim must match server loadout")
	denied(Progression.can_cast(p, "jade_arc", "reed_saber"), "level", "trained skill is locked at level one")
	p.level = 3
	p.attributes.strength = 6
	denied(Progression.can_learn(p, "jade_arc"), "mastery", "learning checks prior actual skill mastery")
	p.mastery.slash = 3
	check(Progression.can_learn(p, "jade_arc").ok, "trained skill can be learned after progression gates")
	denied(Progression.can_cast(p, "jade_arc", "reed_saber"), "not_learned", "qualifying does not automatically grant a learned skill")
	p.known_skills.append("jade_arc")
	check(Progression.can_cast(p, "jade_arc", "reed_saber").ok, "learned trained skill casts with eligible saber")
	p.gear.weapon = "ironwind_glaive"
	check(Progression.can_cast(p, "jade_arc", "ironwind_glaive").ok, "trained radial skill supports current polearm")
	p = veteran_fixture()
	p.proficiencies.saber = 2
	p.proficiencies.polearm = 2
	denied(Progression.can_learn(p, "threadstrike"), "proficiency", "learning veteran strike needs a practiced compatible family")
	p.proficiencies.polearm = 3
	check(Progression.can_learn(p, "threadstrike").ok, "learning accepts one qualified weapon family")
	denied(Progression.can_cast(p, "threadstrike", "reed_saber"), "proficiency", "casting uses equipped family proficiency not another family")
	p.proficiencies.saber = 3
	p.mastery.jade_arc = 2
	denied(Progression.can_cast(p, "threadstrike", "reed_saber"), "mastery", "known skill cannot bypass lost prerequisite mastery")
	p.mastery.jade_arc = 3
	check(Progression.can_cast(p, "threadstrike", "reed_saber").ok, "veteran line skill passes all gates")
	p.gear.weapon = "willow_bow"
	p.owned_equipment.append("willow_bow")
	denied(Progression.can_cast(p, "threadstrike", "willow_bow"), "wrong_weapon", "incompatible bow cannot cast a melee line skill")
	p.gear.weapon = "tideguard_saber"
	p.owned_equipment.append("tideguard_saber")
	denied(Progression.can_cast(p, "slash", "tideguard_saber"), "unavailable_item", "forging planned same-family ownership cannot activate an unavailable mesh")
	p.gear.weapon = "dawnsteel_saber"
	p.mastery.slash = 0
	denied(Progression.can_cast(p, "slash", "dawnsteel_saber"), "mastery", "cast rechecks previously equipped item's current requirements")
	p = veteran_fixture()
	p.owned_equipment.erase("reed_saber")
	denied(Progression.can_cast(p, "slash", "reed_saber"), "not_owned", "cast rechecks current weapon ownership")
	p = player_fixture()
	p.erase("gear")
	denied(Progression.can_cast(p, "slash", "reed_saber"), "invalid_loadout", "missing gear cannot authorize combat")

func _test_malformed_profiles():
	for field in ["level", "class_id", "attributes", "proficiencies", "mastery", "known_skills"]:
		var p = player_fixture()
		p.erase(field)
		denied(Progression.can_equip(p, "reed_saber", "weapon"), "invalid_profile", "missing authoritative field " + field)
	for pair in [["level", "6"], ["level", 6.0], ["level", true], ["level", 0], ["class_id", 1], ["class_id", "forged"], ["attributes", []], ["proficiencies", []], ["mastery", 999], ["known_skills", {}]]:
		var p = player_fixture()
		p[pair[0]] = pair[1]
		denied(Progression.can_cast(p, "slash", "reed_saber"), "invalid_profile", "malformed %s %s" % [pair[0], str(pair[1])])
	for pair in [["attributes", "strength", "99"], ["attributes", "strength", -1], ["proficiencies", "saber", true], ["proficiencies", "polearm", 1.0], ["mastery", "slash", -1], ["mastery", "jade_arc", "8"]]:
		var p = player_fixture()
		p[pair[0]][pair[1]] = pair[2]
		denied(Progression.can_equip(p, "reed_saber", "weapon"), "invalid_profile", "malformed nested %s.%s" % [pair[0], pair[1]])
	for pair in [["attributes", "spirit"], ["proficiencies", "saber"], ["mastery", "slash"]]:
		var p = player_fixture()
		p[pair[0]].erase(pair[1])
		denied(Progression.can_equip(p, "reed_saber", "weapon"), "invalid_profile", "missing nested %s.%s" % [pair[0], pair[1]])
	for learned in [["slash", "slash"], ["slash", 1], ["slash", "made_up"]]:
		var p = player_fixture()
		p.known_skills = learned
		denied(Progression.can_cast(p, "slash", "reed_saber"), "invalid_profile", "invalid learned skill list " + str(learned))
	for owned in [null, {}, ["reed_saber", "reed_saber"], ["reed_saber", 1], ["forged_item"]]:
		var p = player_fixture()
		p.owned_equipment = owned
		denied(Progression.can_equip(p, "reed_saber", "weapon"), "invalid_ownership", "invalid ownership list " + str(owned))
	var missing_owner = player_fixture()
	missing_owner.erase("owned_equipment")
	denied(Progression.can_equip(missing_owner, "reed_saber", "weapon"), "invalid_ownership", "ownership never defaults to starter inventory")
	for gear in [null, [], {}, {"weapon": 1}]:
		var p = player_fixture()
		p.gear = gear
		denied(Progression.can_cast(p, "slash", "reed_saber"), "invalid_loadout", "invalid equipped weapon state " + str(gear))

func _test_bypass_and_purity():
	var p = player_fixture()
	p.owned_equipment.append("dawnsteel_saber")
	p.client_payload = {"level": 999, "class_id": "blade", "mastery": {"slash": 999}, "known_skills": ["jade_arc", "threadstrike"], "ignore_requirements": true}
	p.requested_rank = 999
	p.is_admin = true
	p.ignore_requirements = true
	denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "level", "extra client claims never override authoritative profile")
	denied(Progression.can_cast(p, "threadstrike", "reed_saber"), "level", "client requested skill rank cannot authorize a cast")
	var expected = Progression.requirements_for_item("dawnsteel_saber")
	for quality in ["normal", "refined", "unique", "elite", "super"]:
		p.quality = quality
		p.enhancement = 99
		p.purification = "prestige"
		p.cosmetic = "veteran"
		p.gear_quality = {"weapon": quality}
		check(Progression.requirements_for_item("dawnsteel_saber") == expected, "requirements remain independent of " + quality)
		denied(Progression.can_equip(p, "dawnsteel_saber", "weapon"), "level", "presentation layers cannot bypass gates: " + quality)
	var requirements_copy = Progression.requirements_for_item("dawnsteel_saber")
	requirements_copy.level = 1
	requirements_copy.mastery.clear()
	check(Progression.requirements_for_item("dawnsteel_saber") == expected, "returned requirement dictionary cannot mutate catalog")
	var item_copy = Progression.item_definition("dawnsteel_saber")
	item_copy.requirements.level = 1
	check(Progression.requirements_for_item("dawnsteel_saber") == expected, "item definition requirements are detached")
	var skill_copy = Progression.skill_definition("threadstrike")
	skill_copy.available = false
	skill_copy.requirements.level = 1
	check(Progression.skill_definition("threadstrike").available and Progression.requirements_for_skill("threadstrike").level == 6, "skill definitions are detached")
	var before = p.duplicate(true)
	Progression.can_equip(p, "dawnsteel_saber", "weapon")
	Progression.can_cast(p, "slash", "reed_saber")
	var unlocks = Progression.available_unlocks(p)
	check(p == before, "all validation and unlock queries leave server state unchanged")
	check(unlocks.skills == ["slash", "sky_vault"], "starter unlock report does not pretend veteran skills are available")
	check(not "dawnsteel_saber" in unlocks.items, "owned locked gear is not reported eligible")
	var veteran = veteran_fixture()
	veteran.owned_equipment.erase("dawnsteel_saber")
	check("dawnsteel_saber" in Progression.available_unlocks(veteran).items, "unlock report means qualified, not owned or awarded")
	check("threadstrike" in Progression.available_unlocks(veteran).skills, "veteran skill unlock is discoverable")
	check(Progression.available_unlocks({}) == {"items": [], "skills": []}, "malformed profile yields no available unlocks")
	var other = player_fixture()
	p.attributes.strength = 99
	p.mastery.slash = 99
	check(other.attributes.strength == 4 and other.mastery.slash == 0, "starter profiles do not share nested mutable state")
