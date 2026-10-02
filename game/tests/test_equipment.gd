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
	p.hp=80
	check(world.equip(1,"armor","warden_lamellar"),"owned armor equips")
	check(p.max_hp==145 and p.hp==80,"armor stats change without free healing")
	check(Gear.stats(p).defense==3,"armor defense authoritative")
	check(not world.equip(1,"head","warden_helm"),"equip spam cooldown")
	p.equip_cd=0
	check(world.equip(1,"head","warden_helm"),"headgear independently equips")
	check(Gear.stats(p).defense==4,"head and armor defenses combine")
	p.equip_cd=0
	check(world.equip(1,"weapon","ironwind_glaive"),"weapon independently equips")
	check(Gear.stats(p).attack==22 and is_equal_approx(Gear.stats(p).reach,2.9),"glaive damage and reach match equipped item")
	check(world.players[2].gear==Gear.DEFAULT_GEAR,"one player cannot mutate another loadout")
	p.equip_cd=0
	p.hp=145
	world.equip(1,"armor","wayfarer_coat")
	check(p.max_hp==120 and p.hp==120,"removing armor clamps health")
	p.equip_cd=0
	world.equip(1,"armor","warden_lamellar")
	check(p.hp==120,"repeated swaps do not heal")
	p.dead=2
	p.equip_cd=0
	check(not world.equip(1,"head","topknot"),"dead character cannot equip")
	p.dead=0
	p.quest=1
	p.seals=5
	p.pos=World.ELDER
	world.interact(1)
	check("dawnsteel_saber" in p.owned_equipment and p.gear.weapon=="dawnsteel_saber","quest grants and equips original Super saber")
	check(Gear.item(p,"weapon").effect=="jade_edge","weapon-local quality effect is data-bound")
	var state=world.snapshot()
	state.players[1].gear.weapon="reed_saber"
	check(p.gear.weapon=="dawnsteel_saber","snapshot cannot mutate authority")
	check(Gear.next_owned(p,"weapon")=="reed_saber","owned weapon cycle is bounded")
	if failures==0:print("JADE_EQUIPMENT_TESTS_PASSED ",count)
	quit(0 if failures==0 else 1)
