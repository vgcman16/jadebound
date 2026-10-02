extends Node3D
const Network=preload("res://scripts/network.gd")
const View=preload("res://scripts/realm_view.gd")
const Equipment=preload("res://scripts/equipment_data.gd")
const HUD=preload("res://scripts/hud.gd")
var net:JadeNetwork
var view:RealmView
var hud:JadeHUD
var realm_panel:PanelContainer
var ip:LineEdit
var goal:Vector2=JadeWorld.SPAWN
var use_goal:bool=false
var selected:int=-1
var input_timer:float=0
var auto_timer:float=0
var elapsed:float=0
var demo:bool=false
var no_render:bool=false
var capture_path:String=""
var stop_after:float=0
var demo_stage:int=0
var quick_demo:bool=false
var gear_demo:bool=false

func _ready():
	var args=OS.get_cmdline_user_args()
	no_render="--server" in args or "--network-probe" in args
	gear_demo="--gear-demo" in args
	demo="--demo" in args or gear_demo
	quick_demo="--quick-demo" in args
	for arg in args:
		if arg.begins_with("--stop-after="):stop_after=float(arg.split("=")[1])
		if arg.begins_with("--screenshot="):capture_path=arg.trim_prefix("--screenshot=")
	net=Network.new()
	net.name="Realm"
	add_child(net)
	if "--server" in args:
		var bind="127.0.0.1"
		for arg in args:
			if arg.begins_with("--bind="):bind=arg.trim_prefix("--bind=")
		var err=net.host(bind,true)
		print("JADE_SERVER_READY error=",err," bind=",bind)
		if err!=OK:get_tree().quit(2)
	for arg in args:
		if arg.begins_with("--connect="):
			var err=net.join(arg.trim_prefix("--connect="))
			if err!=OK:get_tree().quit(2)
	if no_render:
		print("JADE_HEADLESS_READY")
		return
	view=View.new()
	add_child(view)
	if "--hero-closeup" in args:
		view.camera.size=7
		view.follow=Vector3(-3,0,1)
	var canvas=CanvasLayer.new()
	add_child(canvas)
	hud=HUD.new()
	canvas.add_child(hud)
	hud.demo=demo
	hud.appearance_source=view
	hud.equipment_cycle.connect(cycle_equipment)
	if gear_demo:
		hud.inventory=true
		hud.notice="AUTOMATED EQUIPMENT DEMO · armor, headgear and weapon update through the authoritative model"
	build_realm_panel(canvas)
	net.effects_received.connect(func(effects:Array):
		for event in effects:view.effect(event))
	net.connection_note.connect(func(note:String):hud.notice=note)
	if demo:
		# Capture runs ordinary input through the same authoritative simulation.
		net.model.players[1].notice="Lantern Vale · original Godot + Blender gameplay prototype"
	if "--equipment-review" in args:
		var reviewer=load("res://tests/capture_equipment.gd").new()
		reviewer.app=self
		add_child(reviewer)
	print("JADE_PLAYABLE_READY")

func _process(delta:float):
	elapsed+=delta
	if stop_after>0 and elapsed>=stop_after:
		if no_render and net.mode=="client":
			var valid=net.snapshot_count>5 and net.max_seen_players>=2 and net.state.get("players",{}).has(net.local_id)
			print("JADE_NETWORK_PROBE snapshots=",net.snapshot_count," own_player=",valid," max_players=",net.max_seen_players)
			get_tree().quit(0 if valid else 3)
		else:get_tree().quit()
		return
	if no_render:
		input_timer+=delta
		if net.mode=="client" and input_timer>=.05:
			input_timer-=.05
			net.send_input(Vector2(1,0),Vector2.ZERO,false)
		return
	view.selected=selected
	view.update_state(net.state,net.local_id,delta)
	hud.state=net.state
	hud.local_id=net.local_id
	hud.mode=net.mode
	hud.queue_redraw()
	if demo:
		demo_input(delta)
	else:
		input_timer+=delta
		if input_timer>=.05 and not realm_panel.visible:
			input_timer=0
			var move=Vector2.ZERO
			if Input.is_physical_key_pressed(KEY_W):move+=Vector2(-1,-1)
			if Input.is_physical_key_pressed(KEY_S):move+=Vector2(1,1)
			if Input.is_physical_key_pressed(KEY_A):move+=Vector2(-1,1)
			if Input.is_physical_key_pressed(KEY_D):move+=Vector2(1,-1)
			if move.length()>0:
				use_goal=false
				selected=-1
			if selected>=0 and net.state.get("enemies",{}).has(selected):
				var enemy=net.state.enemies[selected]
				if enemy.dead>0:selected=-1
				else:
					goal=enemy.pos
					use_goal=true
					var p=net.state.get("players",{}).get(net.local_id,{})
					if not p.is_empty() and p.pos.distance_to(goal)<1.9:
						use_goal=false
						net.send_action(1,goal)
			net.send_input(move.normalized(),goal,use_goal)
	if not capture_path.is_empty() and elapsed>4:
		await RenderingServer.frame_post_draw
		var result=get_viewport().get_texture().get_image().save_png(capture_path)
		print("JADE_SCREENSHOT ",result," ",capture_path)
		capture_path=""

func _unhandled_input(event:InputEvent):
	if no_render:return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode==KEY_ESCAPE:
			if realm_panel.visible:realm_panel.hide()
			elif hud.help:hud.help=false
			else:get_tree().quit()
		if event.physical_keycode==KEY_F1:realm_panel.visible=not realm_panel.visible
		if realm_panel.visible:return
		match event.physical_keycode:
			KEY_TAB:hud.inventory=not hud.inventory
			KEY_F2:hud.help=not hud.help
			KEY_1:attack(1)
			KEY_Q:attack(2)
			KEY_R:attack(6)
			KEY_SPACE:attack(3)
			KEY_E:attack(4)
			KEY_H:attack(5)
			KEY_C:cycle_equipment("armor")
			KEY_V:cycle_equipment("head")
			KEY_B:cycle_equipment("weapon")
			KEY_F5:save_progress()
			KEY_F9:load_progress()
	if event is InputEventMouseButton and event.pressed and not realm_panel.visible:
		if event.button_index==MOUSE_BUTTON_WHEEL_UP:view.camera.size=maxf(12,view.camera.size-1)
		if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:view.camera.size=minf(28,view.camera.size+1)
		if event.button_index==MOUSE_BUTTON_LEFT:
			goal=view.screen_to_ground(event.position)
			use_goal=true
			selected=-1
			if event.ctrl_pressed:
				net.send_action(3,goal)
				use_goal=false
			else:
				for id in net.state.get("enemies",{}):
					var e=net.state.enemies[id]
					if e.dead<=0 and e.pos.distance_to(goal)<1.1:selected=id
		if event.button_index==MOUSE_BUTTON_RIGHT:attack(1)

func cycle_equipment(slot:String):
	var p:Dictionary=net.state.get("players",{}).get(net.local_id,{})
	if p.is_empty():return
	var item=Equipment.next_owned(p,slot)
	if not item.is_empty():net.send_equip(slot,item)

func attack(kind:int):
	if kind in [2,3,6]:selected=-1
	net.send_action(kind,view.screen_to_ground(get_viewport().get_mouse_position()))

func build_realm_panel(canvas:CanvasLayer):
	realm_panel=PanelContainer.new()
	realm_panel.position=Vector2(420,220)
	realm_panel.custom_minimum_size=Vector2(440,340)
	canvas.add_child(realm_panel)
	var margin=MarginContainer.new()
	for side in ["left","right","top","bottom"]:margin.add_theme_constant_override("margin_"+side,24)
	realm_panel.add_child(margin)
	var col=VBoxContainer.new()
	col.add_theme_constant_override("separation",12)
	margin.add_child(col)
	var title=Label.new()
	title.text="CHOOSE YOUR REALM"
	title.add_theme_font_size_override("font_size",24)
	col.add_child(title)
	var note=Label.new()
	note.text="Prototype sessions · maximum 8 wanderers\nNo account or permanent online progression yet"
	col.add_child(note)
	ip=LineEdit.new()
	ip.text="127.0.0.1"
	ip.placeholder_text="Trusted host address"
	col.add_child(ip)
	for item in [["Join realm",func():
		var err=net.join(ip.text.strip_edges())
		hud.notice="Connecting…" if err==OK else "Could not create connection: %s"%error_string(err)
		realm_panel.hide()], ["Host local realm (loopback)",func():
		var err=net.host()
		hud.notice="Local realm open on 127.0.0.1:27841" if err==OK else "Host failed: %s"%error_string(err)
		realm_panel.hide()], ["New offline session",func():
		net.start_offline()
		hud.notice=""
		selected=-1
		use_goal=false
		realm_panel.hide()], ["Return to game",func():realm_panel.hide()]]:
		var button=Button.new()
		button.text=item[0]
		button.pressed.connect(item[1])
		col.add_child(button)
	realm_panel.hide()

func save_progress():
	if net.mode!="offline":
		hud.notice="Online persistence is not enabled in this prototype."
		return
	var p=net.model.players[1]
	var data={"schema":1}
	for key in ["hp","max_hp","stamina","gold","seals","potions","xp","level","quest","kills","upgraded"]:data[key]=p[key]
	var file=FileAccess.open("user://jadebound-save.json",FileAccess.WRITE)
	if file:
		data.gear=p.gear.duplicate(true)
		file.store_string(JSON.stringify(data))
		hud.notice="Offline progress saved. F9 restores it at the village."
	else:hud.notice="Could not write the offline save."

func load_progress():
	if net.mode!="offline" or not FileAccess.file_exists("user://jadebound-save.json"):return
	var data=JSON.parse_string(FileAccess.get_file_as_string("user://jadebound-save.json"))
	if not data is Dictionary or data.get("schema",0)!=1:return
	var p=net.model.players[1]
	for key in ["hp","max_hp","stamina","gold","seals","potions","xp","level","quest","kills"]:
		if data.get(key) is float or data.get(key) is int:p[key]=clamp(int(data[key]),0,99999)
	p.level=clampi(p.level,1,99)
	p.max_hp=120+(p.level-1)*15
	p.hp=p.max_hp
	p.stamina=100.0
	p.quest=clampi(p.quest,0,2)
	p.upgraded=p.quest==2
	if p.upgraded and not "dawnsteel_saber" in p.owned_equipment:p.owned_equipment.append("dawnsteel_saber")
	var saved_gear=data.get("gear",{})
	if saved_gear is Dictionary:
		for slot in Equipment.SLOTS:
			var item=saved_gear.get(slot,"")
			if item in p.owned_equipment and Equipment.ITEMS.has(item) and Equipment.ITEMS[item].slot==slot:p.gear[slot]=item
	net.model.recalculate_stats(p)
	p.hp=p.max_hp
	p.pos=JadeWorld.SPAWN
	p.dead=0.0
	p.go=false
	use_goal=false
	selected=-1
	hud.notice="Offline progress restored. Welcome home."

func demo_input(delta:float):
	if not net.model:return
	var p=net.model.players[1]
	input_timer+=delta
	if input_timer<.05:return
	input_timer=0
	if gear_demo:
		net.send_input(Vector2.ZERO,p.pos,false)
		if elapsed>1.5 and demo_stage==0:
			net.send_equip("armor","warden_lamellar")
			demo_stage=1
		elif elapsed>2.5 and demo_stage==1:
			net.send_equip("head","warden_helm")
			demo_stage=2
		elif elapsed>3.5 and demo_stage==2:
			net.send_equip("weapon","ironwind_glaive")
			demo_stage=3
		return
	if quick_demo:
		if elapsed<.75:
			net.send_input(Vector2.ZERO,p.pos,false)
		elif elapsed<1.7:
			if demo_stage==0:
				net.send_action(3,Vector2(5,2))
				demo_stage=1
			net.send_input(Vector2.ZERO,p.pos,false)
		else:
			var target:Dictionary={}
			var distance=100.0
			for e in net.model.enemies.values():
				if e.dead<=0 and p.pos.distance_to(e.pos)<distance:
					distance=p.pos.distance_to(e.pos)
					target=e
			if not target.is_empty():
				net.send_input(Vector2.ZERO,target.pos,distance>1.8)
				if p.arc_cd<=0 and distance<3.5:net.send_action(2,target.pos)
				elif p.line_cd<=0:net.send_action(6,target.pos)
				elif distance<2:net.send_action(1,target.pos)
		return
	if elapsed<3:
		net.send_input(Vector2.ZERO,JadeWorld.ELDER,true)
	elif elapsed<4:
		if p.quest==0:net.send_action(4,JadeWorld.ELDER)
		net.send_input(Vector2.ZERO,Vector2(4,2),true)
	elif elapsed<7:
		if elapsed>4.4 and demo_stage==0:
			net.send_action(3,Vector2(5,2))
			demo_stage=1
		net.send_input(Vector2.ZERO,Vector2(5,2),true)
	elif elapsed<20:
		var nearest=-1
		var distance=100.0
		for id in net.model.enemies:
			var e=net.model.enemies[id]
			if e.dead<=0 and p.pos.distance_to(e.pos)<distance:
				distance=p.pos.distance_to(e.pos)
				nearest=id
		if nearest>=0:
			var e=net.model.enemies[nearest]
			net.send_input(Vector2.ZERO,e.pos,distance>1.8)
			if p.line_cd<=0:net.send_action(6,e.pos)
			elif p.arc_cd<=0 and distance<3.5:net.send_action(2,e.pos)
			elif distance<2:net.send_action(1,e.pos)
			if p.hp<65:net.send_action(5,e.pos)
			for d in net.model.drops.values():
				if p.pos.distance_to(d.pos)<2.5:
					net.send_action(4,d.pos)
					break
	else:
		net.send_input(Vector2.ZERO,Vector2(-3,1),true)
