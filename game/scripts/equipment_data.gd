class_name JadeEquipment
extends RefCounted
## Original gear definitions. Mesh, quality, enhancement and cosmetic layers are separate.
const SLOTS=["armor","head","weapon","boots","gloves"]
# Accessory assets are in the isolated art study, not the live model yet.
const LIVE_VISUAL_SLOTS=["armor","head","weapon"]
const QUALITY_ORDER=["normal","refined","unique","elite","super"]
const DEFAULT_GEAR={"armor":"wayfarer_coat","head":"topknot","weapon":"reed_saber","boots":"","gloves":""}
const STARTER_OWNED=["wayfarer_coat","warden_lamellar","topknot","warden_helm","reed_saber","ironwind_glaive"]
const ITEMS={
	"wayfarer_coat":{"label":"Wayfarer coat","slot":"armor","mesh":"Gear_Wayfarer","quality":"normal","defense":0,"vitality":0,"speed":0.0,"enhancement":0,"purification":"","cosmetic":""},
	"warden_lamellar":{"label":"Warden lamellar","slot":"armor","mesh":"Gear_Warden","quality":"elite","defense":3,"vitality":25,"speed":-0.45,"enhancement":0,"purification":"","cosmetic":""},
	"topknot":{"label":"Wayfarer topknot","slot":"head","mesh":"Head_Topknot","quality":"normal","defense":0,"vitality":0,"speed":0.0,"enhancement":0,"purification":"","cosmetic":""},
	"warden_helm":{"label":"Warden helm","slot":"head","mesh":"Head_Warden","quality":"elite","defense":1,"vitality":0,"speed":0.0,"enhancement":0,"purification":"","cosmetic":""},
	"reed_saber":{"label":"Reedblade saber","slot":"weapon","mesh":"Weapon_Saber","quality":"normal","attack":18,"reach":2.2,"cooldown":0.44,"speed":0.0,"enhancement":0,"effect":"","purification":"","cosmetic":""},
	"ironwind_glaive":{"label":"Ironwind glaive","slot":"weapon","mesh":"Weapon_Glaive","quality":"elite","attack":22,"reach":2.9,"cooldown":0.60,"speed":-0.10,"enhancement":0,"effect":"","purification":"","cosmetic":""},
	"dawnsteel_saber":{"label":"Dawnsteel saber","slot":"weapon","mesh":"Weapon_Saber","quality":"super","attack":26,"reach":2.3,"cooldown":0.44,"speed":0.0,"enhancement":0,"effect":"jade_edge","purification":"","cosmetic":""}
}
static func item(player:Dictionary,slot:String)->Dictionary:
	var equipped:Dictionary=player.get("gear",DEFAULT_GEAR)
	return ITEMS.get(equipped.get(slot,DEFAULT_GEAR.get(slot,"")),{})
static func stats(player:Dictionary)->Dictionary:
	var weapon=item(player,"weapon")
	var result={"attack":0 if weapon.is_empty() else int(weapon.get("attack",0))+maxi(0,int(player.get("level",1))-1)*3,"defense":0,"max_hp":120+maxi(0,int(player.get("level",1))-1)*15,"speed":5.2,"reach":float(weapon.get("reach",0.0)),"cooldown":float(weapon.get("cooldown",.44))}
	for slot in SLOTS:
		var equipped=item(player,slot)
		result.defense+=int(equipped.get("defense",0))
		result.max_hp+=int(equipped.get("vitality",0))
		result.speed+=float(equipped.get("speed",0))
	return result
static func next_owned(player:Dictionary,slot:String)->String:
	var choices:Array=[]
	for id in player.get("owned_equipment",STARTER_OWNED):
		if ITEMS.has(id) and ITEMS[id].slot==slot:choices.append(id)
	if choices.is_empty():return ""
	var current=player.get("gear",DEFAULT_GEAR).get(slot,"")
	return choices[(choices.find(current)+1)%choices.size()]
