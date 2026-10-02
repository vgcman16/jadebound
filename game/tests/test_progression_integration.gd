extends SceneTree
const World=preload("res://scripts/world_model.gd")
var assertions=0
var failures=0
func check(ok:bool,label:String):
	assertions+=1
	if ok:print("PASS AUTHORITY: "+label)
	else:failures+=1;push_error("FAIL AUTHORITY: "+label)
func _initialize():
	var w=World.new()
	w.add_player(1)
	var p=w.players[1]
	p.pos=Vector2(4,2)
	w.events.clear()
	w.action(1,2,Vector2(5,2))
	check(p.pending_strike.is_empty() and p.stamina==100,"locked skill cannot spend or queue")
	w.action(1,1,Vector2(5,2))
	check(w.enemies[1].hp==46 and w.events.is_empty(),"damage and effect wait for contact")
	check(not w.equip(1,"head","warden_helm"),"equip cannot change an active strike")
	w.tick(.15)
	check(w.enemies[1].hp==46,"anticipation remains non-damaging")
	w.tick(.10)
	check(w.enemies[1].hp<46 and w.events.any(func(e):return e.type=="skill"),"impact emits damage and effect together")
	check(p.mastery.slash==1 and p.practice.saber==1,"successful hit awards bounded mastery and practice")
	w.tick(.3)
	p.pos=Vector2(-10,10)
	w.action(1,1,p.pos+Vector2(-1,0))
	w.tick(.3)
	check(p.mastery.slash==1,"empty swing cannot farm mastery")
	w.tick(.3)
	p.pos=Vector2(4,2)
	var hp=w.enemies[1].hp
	w.action(1,1,Vector2(5,2))
	p.dead=2
	w.tick(.3)
	check(w.enemies[1].hp==hp and p.pending_strike.is_empty(),"death cancels pending impact")
	p.dead=0
	p.level=3
	p.mastery.slash=3
	w.sync_progression(p)
	check("jade_arc" in p.known_skills and not "threadstrike" in p.known_skills,"authority learns only qualified skills")
	p.level=6
	p.practice.saber=24
	p.mastery.jade_arc=3
	w.sync_progression(p)
	check("threadstrike" in p.known_skills and p.proficiencies.saber==3,"earned practice unlocks veteran skill")
	check(p.attributes.strength==9,"attributes derive from authoritative level")
	var before=p.gear.duplicate(true)
	w.equip(1,"weapon","stormglass_talons")
	check(p.gear==before,"planned catalogue item cannot be equipped")
	if failures==0:print("JADE_PROGRESSION_INTEGRATION_PASSED ",assertions)
	quit(0 if failures==0 else 1)
