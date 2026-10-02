class_name JadeWorld
extends RefCounted
## Pure authoritative simulation. No scene, render or client ownership dependencies.
const Gear=preload("res://scripts/equipment_data.gd")
const SPAWN = Vector2(-3, 1)
const ELDER = Vector2(-5, -4)
const MAX_PLAYERS = 8
const SPEED = 5.2
const OBSTACLES = [Vector3(-10,-7,2.6), Vector3(-10,1,2.3), Vector3(-3,-11,2.5), Vector3(-13,9,2.2), Vector3(1,-8,1.6)]
var players: Dictionary = {}
var enemies: Dictionary = {}
var drops: Dictionary = {}
var events: Array = []
var clock: float = 0.0
var next_drop: int = 1
var kills: int = 0

func _init():
	var points = [Vector2(5,2),Vector2(9,-2),Vector2(11,5),Vector2(4,9),Vector2(10,11),Vector2(0,12),Vector2(13,12)]
	for i in points.size():
		var elite = i == points.size()-1
		enemies[i+1] = {"id":i+1,"pos":points[i],"home":points[i],"hp":110 if elite else 46,"max_hp":110 if elite else 46,"cooldown":0.0,"dead":0.0,"facing":0.0,"elite":elite,"attack":0.0}

func add_player(id: int, title: String = "Wanderer") -> bool:
	if players.has(id) or players.size() >= MAX_PLAYERS: return false
	players[id] = {"id":id,"name":title.left(20),"pos":SPAWN+Vector2((players.size()%3)*1.2,0),"hp":120,"max_hp":120,"stamina":100.0,"gold":0,"seals":0,"potions":3,"xp":0,"level":1,"quest":0,"kills":0,"cooldown":0.0,"arc_cd":0.0,"line_cd":0.0,"jump":0.0,"jump_dir":Vector2.ZERO,"dead":0.0,"facing":0.0,"attack":0.0,"attack_kind":0,"move":Vector2.ZERO,"goal":SPAWN,"go":false,"last_seq":-1,"last_input":0.0,"upgraded":false,"notice":"Welcome to Lantern Vale. Speak to Keeper Suri [E]."}
	players[id].gear=Gear.DEFAULT_GEAR.duplicate(true)
	players[id].owned_equipment=Gear.STARTER_OWNED.duplicate()
	players[id].equip_cd=0.0
	return true

func input(id: int, seq: int, movement: Vector2, target: Vector2, use_target: bool):
	if not players.has(id) or not movement.is_finite() or not target.is_finite(): return
	var p = players[id]
	if seq <= p.last_seq: return
	p.last_seq = seq
	p.move = movement.limit_length(1.0)
	p.goal = Vector2(clampf(target.x,-18,16),clampf(target.y,-17,18))
	p.go = use_target
	p.last_input = clock

func action(id: int, kind: int, aim: Vector2):
	if not players.has(id) or not aim.is_finite(): return
	var p = players[id]
	if p.dead > 0: return
	var dir: Vector2 = (aim-p.pos).normalized()
	if dir.length_squared() < 0.1: dir=Vector2(sin(p.facing),cos(p.facing))
	if kind == 4:
		interact(id)
		return
	if kind == 5:
		if p.potions > 0 and p.hp < p.max_hp:
			p.potions -= 1
			p.hp = mini(p.max_hp,p.hp+65)
			p.notice = "Cloudleaf flask restores 65 vitality."
			events.append({"type":"heal","pos":p.pos,"text":"+65"})
		return
	if kind == 3:
		if p.jump <= 0 and p.stamina >= 22:
			p.stamina -= 22
			p.jump = 0.7
			p.jump_dir = dir
			p.go = false
			p.facing = atan2(dir.x,dir.y)
		return
	if p.cooldown > 0: return
	if kind == 2 and (p.arc_cd > 0 or p.stamina < 32): return
	if kind == 6 and (p.line_cd > 0 or p.stamina < 25): return
	if not kind in [1,2,6]: return
	p.cooldown = float(Gear.stats(p).cooldown)
	p.facing = atan2(dir.x,dir.y)
	p.attack = 0.28
	p.attack_kind = kind
	var gear_stats=Gear.stats(p)
	var damage: int = int(gear_stats.attack)
	if kind == 2:
		p.arc_cd = 4.0
		p.stamina -= 32
		damage = int(gear_stats.attack)+15+(p.level-1)
	if kind == 6:
		p.line_cd = 2.5
		p.stamina -= 25
		damage = int(gear_stats.attack)+10+(p.level-1)
	events.append({"type":"skill","pos":p.pos,"kind":kind,"dir":dir})
	for eid in enemies:
		var e = enemies[eid]
		if e.dead > 0: continue
		var offset: Vector2 = e.pos-p.pos
		var hit: bool = offset.length() <= float(gear_stats.reach) and offset.normalized().dot(dir)>-0.1
		if kind == 2: hit=offset.length()<=3.8
		if kind == 6: hit=offset.dot(dir)>0 and offset.dot(dir)<8 and absf(offset.cross(dir))<0.85
		if hit:
			e.hp-=damage
			events.append({"type":"damage","pos":e.pos,"text":str(damage)})
			if e.hp<=0: defeat_enemy(id,eid)

func defeat_enemy(id: int,eid: int):
	var p=players[id]
	var e=enemies[eid]
	e.dead=20.0
	e.hp=0
	p.xp+=25 if not e.elite else 70
	p.kills+=1
	kills+=1
	drops[next_drop]={"id":next_drop,"pos":e.pos,"owner":id,"gold":9 if not e.elite else 35,"seals":1 if not e.elite else 2,"ttl":60.0}
	next_drop+=1
	if p.xp>=p.level*80:
		p.xp-=p.level*80
		p.level+=1
		p.max_hp+=15
		p.hp=p.max_hp
		p.notice="Attunement deepens. Level %d!"%p.level
		events.append({"type":"level","pos":p.pos,"text":"LEVEL %d"%p.level})

func interact(id: int):
	var p=players[id]
	if p.pos.distance_to(ELDER)<3.0:
		p.hp=p.max_hp
		if p.quest==0:
			p.quest=1
			p.notice="Suri: Recover 5 ember seals from the Ashen in the eastern field. Bring them home."
		elif p.quest==1 and p.seals>=5:
			p.seals-=5
			p.quest=2
			p.gold+=100
			p.upgraded=true
			if not "dawnsteel_saber" in p.owned_equipment:p.owned_equipment.append("dawnsteel_saber")
			p.gear.weapon="dawnsteel_saber"
			recalculate_stats(p)
			p.potions+=2
			p.notice="QUEST COMPLETE · Dawnsteel blade, 100 copper, 2 flasks. Lantern Vale remembers."
			events.append({"type":"level","pos":p.pos,"text":"DAWNSTEEL EARNED"})
		elif p.quest==1:
			p.notice="Suri: You carry %d / 5 ember seals. Rest here, then return to the field."%p.seals
		else:
			p.notice="Suri: The lanterns shine again. Rest, wanderer."
		return
	var found=false
	for did in drops.keys():
		var d=drops[did]
		if p.pos.distance_to(d.pos)<3.0 and (d.owner==id or d.ttl<45):
			p.gold+=d.gold
			p.seals+=d.seals
			drops.erase(did)
			found=true
	if found: p.notice="Gathered copper and ember seals."
	else: p.notice="Move closer to a glowing drop or Keeper Suri."

func tick(dt:float):
	clock+=dt
	for id in players:
		var p=players[id]
		for key in ["cooldown","arc_cd","line_cd","attack","equip_cd"]: p[key]=maxf(0,p[key]-dt)
		p.stamina=minf(100,p.stamina+18*dt)
		if p.dead>0:
			p.dead-=dt
			if p.dead<=0:
				p.pos=SPAWN
				p.hp=p.max_hp
				p.go=false
				p.notice="The shrine calls you home. Your belongings are safe."
			continue
		var direction:Vector2=p.move
		if clock-p.last_input>0.5: direction=Vector2.ZERO
		if p.go:
			var delta:Vector2=p.goal-p.pos
			if delta.length()<0.2: p.go=false
			else: direction=delta.normalized()
		var speed=float(Gear.stats(p).speed)
		if p.jump>0:
			p.jump=maxf(0,p.jump-dt)
			direction=p.jump_dir
			speed=10.5
		if direction.length_squared()>0.01:
			p.pos=move_with_collision(p.pos,direction*speed*dt)
			p.facing=atan2(direction.x,direction.y)
		if p.pos.distance_to(ELDER)<3.0: p.hp=minf(p.max_hp,p.hp+dt*14)
	for eid in enemies:
		var e=enemies[eid]
		e.attack=maxf(0,e.attack-dt)
		e.cooldown=maxf(0,e.cooldown-dt)
		if e.dead>0:
			e.dead-=dt
			if e.dead<=0:
				e.hp=e.max_hp
				e.pos=e.home
			continue
		var target:Dictionary={}
		var near=7.5
		for id in players:
			var p=players[id]
			var dist:float=p.pos.distance_to(e.pos)
			if p.dead<=0 and p.pos.x>-1.5 and dist<near:
				near=dist
				target=p
		if not target.is_empty():
			var delta:Vector2=target.pos-e.pos
			e.facing=atan2(delta.x,delta.y)
			if near>1.35: e.pos=move_with_collision(e.pos,delta.normalized()*dt*(2.7 if not e.elite else 2.3))
			elif e.cooldown<=0:
				e.cooldown=1.2 if not e.elite else 1.5
				e.attack=0.3
				if target.jump<0.12:
					var incoming=maxi(1,(10 if not e.elite else 19)-int(Gear.stats(target).defense))
					target.hp-=incoming
					events.append({"type":"hurt","pos":target.pos,"text":"-%d"%incoming})
					if target.hp<=0:
						target.hp=0
						target.dead=3.5
						target.notice="Fallen · returning to Lantern Vale…"
		elif e.pos.distance_to(e.home)>0.1: e.pos=e.pos.move_toward(e.home,dt*1.5)
	for did in drops.keys():
		drops[did].ttl-=dt
		if drops[did].ttl<=0: drops.erase(did)
	if events.size()>80: events=events.slice(events.size()-80)

func move_with_collision(pos:Vector2, delta:Vector2)->Vector2:
	var result=pos+delta
	result.x=clampf(result.x,-18,16)
	result.y=clampf(result.y,-17,18)
	for o in OBSTACLES:
		var center=Vector2(o.x,o.y)
		var away=result-center
		if away.length()<o.z+0.35: result=center+away.normalized()*(o.z+0.35)
	return result

func snapshot()->Dictionary:
	return {"players":players.duplicate(true),"enemies":enemies.duplicate(true),"drops":drops.duplicate(true),"time":clock}

func recalculate_stats(player:Dictionary):
	var current=Gear.stats(player)
	player.max_hp=int(current.max_hp)
	player.hp=minf(player.hp,player.max_hp)

func equip(id:int,slot:String,item_id:String)->bool:
	if not players.has(id) or not slot in Gear.SLOTS or not Gear.ITEMS.has(item_id):return false
	var p=players[id]
	if p.dead>0 or p.equip_cd>0:return false
	if not item_id in p.owned_equipment or Gear.ITEMS[item_id].slot!=slot:return false
	if p.gear.get(slot)==item_id:return false
	p.gear[slot]=item_id
	p.equip_cd=.25
	recalculate_stats(p)
	p.notice="Equipped %s · %s"%[Gear.ITEMS[item_id].label,String(Gear.ITEMS[item_id].quality).capitalize()]
	return true
