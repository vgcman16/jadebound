extends SceneTree
const World=preload("res://scripts/world_model.gd")
const Gear=preload("res://scripts/equipment_data.gd")
var failures:int=0
var count:int=0
func check(ok:bool,label:String):
	count+=1
	if not ok:
		failures+=1
		push_error("FAIL GEAR: "+label)
	else:print("PASS GEAR: "+label)
func _initialize():
	var world=World.new()
	world.add_player(1)
	world.add_player(2)
	var p=world.players[1]
	check(p.gear==Gear.DEFAULT_GEAR,"default modular slots")
	check(not world.equip(1,"weapon","dawnsteel_saber"),"unowned Super item denied")
	check(not world.equip(1,"weapon","warden_helm"),"wrong-slot item denied")
	check(not world.equip(1,"armor","forged_by_client"),"unknown item denied")
	check(not world.equip(1,"armor","warden_lamellar"),"owned but underleveled armor denied")
	p.level=3
	world.sync_progression(p)
	world.recalculate_stats(p)
	p.hp=80
	check(world.equip(1,"armor","warden_lamellar"),"owned armor equips")
	check(p.max_hp==175 and p.hp==80,"armor stats change without free healing")
	check(Gear.stats(p).defense==3,"armor defense authoritative")
	check(not world.equip(1,"head","warden_helm"),"equip spam cooldown")
	p.equip_cd=0
	check(world.equip(1,"head","warden_helm"),"headgear independently equips")
	check(Gear.stats(p).defense==4,"head and armor defenses combine")
	p.equip_cd=0
	check(world.equip(1,"weapon","ironwind_glaive"),"weapon independently equips")
	check(Gear.stats(p).attack==28 and is_equal_approx(Gear.stats(p).reach,2.9),"glaive damage and reach match equipped item")
	check(world.players[2].gear==Gear.DEFAULT_GEAR,"one player cannot mutate another loadout")
	p.equip_cd=0
	p.hp=175
	world.equip(1,"armor","wayfarer_coat")
	check(p.max_hp==150 and p.hp==150,"removing armor clamps health")
	p.equip_cd=0
	world.equip(1,"armor","warden_lamellar")
	check(p.hp==150,"repeated swaps do not heal")
	p.dead=2
	p.equip_cd=0
	check(not world.equip(1,"head","topknot"),"dead character cannot equip")
	p.dead=0
	p.quest=1
	p.seals=5
	p.pos=World.ELDER
	world.interact(1)
	check("dawnsteel_saber" in p.owned_equipment and p.gear.weapon=="ironwind_glaive","quest stores locked Super reward without bypassing gates")
	p.level=6
	p.practice.saber=24
	p.mastery.slash=8
	world.sync_progression(p)
	p.equip_cd=0
	check(world.equip(1,"weapon","dawnsteel_saber"),"earned level and practice allow Super equip")
	check(Gear.item(p,"weapon").effect=="jade_edge","weapon-local quality effect is data-bound")
	var state=world.snapshot()
	state.players[1].gear.weapon="reed_saber"
	check(p.gear.weapon=="dawnsteel_saber","snapshot cannot mutate authority")
	check(Gear.next_owned(p,"weapon")=="reed_saber","owned weapon cycle is bounded")
	var old_owned=p.owned_equipment.duplicate()
	p.equip_cd=0
	check(world.equip(1,"weapon",""),"server accepts explicit weapon unequip")
	check(p.gear.weapon=="" and Gear.stats(p).attack==0 and Gear.stats(p).reach==0,"unequip clears weapon-derived stats")
	check(p.owned_equipment==old_owned,"unequip preserves item ownership")
	check(not world.equip(1,"armor",""),"unequip obeys shared equip cooldown")
	p.equip_cd=0
	check(not world.equip(1,"weapon",""),"repeated empty request has no effect")
	check(not JadeProgression.can_cast(p,"slash","").ok,"weapon skill fails closed while unarmed")
	check(JadeProgression.can_cast(p,"sky_vault","").ok,"movement remains available while unarmed")
	check(not world.equip(1,"underwear",""),"permanent base underwear is not an equipment slot")
	p.dead=2
	check(not world.equip(1,"armor",""),"dead character cannot remove equipment")
	p.dead=0
	check(not world.equip(999,"armor",""),"unknown sender cannot unequip anyone")
	check(world.equip(1,"weapon","reed_saber"),"owned eligible weapon re-equips after removal")
	p.equip_cd=0
	p.attack=.3
	check(not world.equip(1,"weapon",""),"cannot change weapon during contact sequence")
	p.attack=0
	check(world.equip(1,"armor",""),"armor independently unequips")
	check(p.gear.armor=="" and p.gear.head=="warden_helm" and p.gear.weapon=="reed_saber","armor removal preserves other slots")
	check(Gear.stats(p).defense==1,"armor defense disappears while helmet remains")
	check(Gear.SLOTS.has("boots") and Gear.SLOTS.has("gloves") and p.gear.boots=="" and p.gear.gloves=="","five-slot state reserves empty independent accessories")
	p.equip_cd=0
	check(not world.equip(1,"boots","trail_boots"),"unfinished accessory item is not made live by slot schema")
	check(world.players[2].gear==Gear.DEFAULT_GEAR,"unequip cannot alter another player's equipment")
	if failures==0:print("JADE_EQUIPMENT_TESTS_PASSED ",count)
	quit(0 if failures==0 else 1)
