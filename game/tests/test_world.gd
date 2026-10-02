extends SceneTree
const World=preload("res://scripts/world_model.gd")
var assertions=0
var failed=false
func check(condition:bool,label:String):
	assertions+=1
	if not condition:
		push_error("FAIL: "+label)
		failed=true
		return
	print("PASS: "+label)
func _initialize():
	var w=World.new()
	check(w.add_player(1),"player joins")
	check(not w.add_player(1),"duplicate ID denied")
	var p=w.players[1]
	w.input(1,1,Vector2(100,0),Vector2.ZERO,false)
	w.tick(.05)
	check(p.pos.distance_to(World.SPAWN)<=World.SPEED*.05+.001,"speed clamped server side")
	w.input(1,0,Vector2(-1,0),Vector2.ZERO,false)
	check(p.last_seq==1,"replayed input rejected")
	var before=p.pos
	w.input(1,2,Vector2(NAN,0),Vector2.ZERO,false)
	check(p.last_seq==1,"non-finite input rejected")
	p.pos=World.ELDER
	w.action(1,4,World.ELDER)
	check(p.quest==1,"quest accepted through interaction")
	p.pos=Vector2(4,2)
	var hp=w.enemies[1].hp
	w.action(1,1,Vector2(5,2))
	check(w.enemies[1].hp==hp,"windup does not deal damage early")
	w.tick(.25)
	check(w.enemies[1].hp<hp,"melee damage authoritative")
	var after=w.enemies[1].hp
	w.action(1,1,Vector2(5,2))
	check(w.enemies[1].hp==after,"attack cooldown enforced")
	for i in 3:
		p.cooldown=0
		w.action(1,1,Vector2(5,2))
		w.tick(.25)
	check(w.enemies[1].dead>0 and w.drops.size()==1,"enemy defeat creates loot")
	w.action(1,4,p.pos)
	check(p.gold==9 and p.seals==1 and w.drops.is_empty(),"loot collected once")
	w.action(1,4,p.pos)
	check(p.gold==9,"duplicate loot interaction safe")
	p.pos=World.ELDER
	p.seals=5
	w.action(1,4,World.ELDER)
	check(p.quest==2 and p.upgraded and p.gold==109,"quest grants upgrade and reward")
	w.action(1,4,World.ELDER)
	check(p.gold==109,"quest reward cannot repeat")
	p.hp=20
	w.action(1,5,p.pos)
	check(p.hp==85 and p.potions==4,"potion heals and consumes")
	p.stamina=10
	w.action(1,3,Vector2(3,3))
	check(p.jump==0,"insufficient qi blocks jump")
	p.stamina=100
	w.action(1,3,p.pos+Vector2(1,0))
	check(p.jump>0 and p.stamina==78,"jump consumes qi")
	p.dead=.01
	p.hp=0
	w.tick(.05)
	check(p.dead<=0 and p.hp==p.max_hp and p.pos==World.SPAWN,"death returns safely to shrine")
	w.add_player(2)
	w.drops[100]={"owner":1,"ttl":60.,"pos":World.SPAWN,"gold":9,"seals":1}
	w.action(2,4,World.SPAWN)
	check(w.players[2].gold==0,"fresh loot ownership enforced")
	w.drops[100].ttl=40.
	w.action(2,4,World.SPAWN)
	check(w.players[2].gold==9,"abandoned loot unlocks")
	check(w.move_with_collision(Vector2(15,0),Vector2(50,0)).x<=16,"world boundary enforced")
	if not failed:print("JADE_WORLD_TESTS_PASSED ",assertions)
	quit(1 if failed else 0)
