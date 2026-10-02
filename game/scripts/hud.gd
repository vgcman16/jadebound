class_name JadeHUD
extends Control
signal equipment_cycle(slot:String)
const Equipment=preload("res://scripts/equipment_data.gd")
var gear_buttons:Dictionary={}
var appearance_source
var preview_container:SubViewportContainer
var preview_viewport:SubViewport
var preview_root:Node3D
var preview_actor:Dictionary={}
var state:Dictionary={}
var local_id:int=1
var mode:String="offline"
var inventory:bool=false
var help:bool=false
var font:Font=ThemeDB.fallback_font
var title_font:SystemFont
var notice:String=""
var demo:bool=false
var last_notice:String=""
var notice_timer:float=0
const INK=Color("122323")
const PAPER=Color("ddd8c5")
const GOLD=Color("c6a568")
const JADE=Color("79b6a2")
func _ready():
	mouse_filter=Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	title_font=SystemFont.new()
	title_font.font_names=PackedStringArray(["Georgia","DejaVu Serif"])
	for i in Equipment.SLOTS.size():
		var slot=Equipment.SLOTS[i]
		var button=Button.new()
		button.position=Vector2(260,207+i*49)
		button.size=Vector2(269,38)
		button.add_theme_font_size_override("font_size",13)
		var style=StyleBoxFlat.new()
		style.bg_color=Color("263d36")
		style.border_color=Color("716b50")
		style.set_border_width_all(1)
		style.set_corner_radius_all(3)
		button.add_theme_stylebox_override("normal",style)
		var hover=style.duplicate()
		hover.bg_color=Color("3d5a4e")
		button.add_theme_stylebox_override("hover",hover)
		button.add_theme_stylebox_override("pressed",hover)
		button.add_theme_color_override("font_color",PAPER)
		button.pressed.connect(func():equipment_cycle.emit(slot))
		button.hide()
		add_child(button)
		gear_buttons[slot]=button
	build_character_preview()
func _process(dt:float):
	var p:Dictionary=state.get("players",{}).get(local_id,{})
	var current=notice if not notice.is_empty() else p.get("notice","")
	if current!=last_notice:
		last_notice=current
		notice_timer=6
	notice_timer=maxf(0,notice_timer-dt)
	if preview_container:
		preview_container.visible=inventory and not help
		preview_viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS if inventory and not help else SubViewport.UPDATE_DISABLED
		preview_root.process_mode=Node.PROCESS_MODE_INHERIT if inventory and not help else Node.PROCESS_MODE_DISABLED
		if inventory and appearance_source and not p.is_empty() and not preview_actor.is_empty():appearance_source.apply_equipment(preview_actor,p)
	for slot in gear_buttons:
		gear_buttons[slot].visible=inventory and not p.is_empty() and not help
		if not p.is_empty():
			var key={"armor":"C","head":"V","weapon":"B"}[slot]
			gear_buttons[slot].text="%s  ·  %s"%[key,Equipment.item(p,slot).get("label",slot)]
func panel(rect:Rect2,color:Color=Color("152525dd")):
	var s=StyleBoxFlat.new()
	s.bg_color=color
	s.border_color=Color("85745299")
	s.set_border_width_all(1)
	s.set_corner_radius_all(3)
	draw_style_box(s,rect)
func text(value:String,pos:Vector2,size:int=18,color:Color=PAPER):
	draw_string(font,pos,value,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)
func _draw():
	var w=size.x
	var h=size.y
	var p:Dictionary=state.get("players",{}).get(local_id,{})
	panel(Rect2(24,24,264,98))
	draw_string(title_font,Vector2(41,58),"JADEBOUND",HORIZONTAL_ALIGNMENT_LEFT,-1,26,GOLD)
	text("ASHES OF LANTERN VALE",Vector2(43,77),10,Color("abb3a6"))
	if not p.is_empty():
		text("Wanderer  ·  Level %d"%p.level,Vector2(43,101),14)
		text("%d c"%p.gold,Vector2(230,101),13,GOLD)
	panel(Rect2(w-189,24,165,156))
	text("LANTERN VALE",Vector2(w-175,46),12,GOLD)
	var map=Rect2(w-175,57,136,106)
	draw_rect(map,Color("273d34"))
	var transform_pos=func(pos:Vector2):return map.position+Vector2((pos.x+20)/40*map.size.x,(pos.y+20)/40*map.size.y)
	draw_line(transform_pos.call(Vector2(-5,-3)),transform_pos.call(Vector2(14,9)),Color("79765a"),2)
	draw_circle(transform_pos.call(JadeWorld.ELDER),3,GOLD)
	for e in state.get("enemies",{}).values():
		if e.dead<=0:draw_circle(transform_pos.call(e.pos),1.8,Color("a66554"))
	for player in state.get("players",{}).values():draw_circle(transform_pos.call(player.pos),3,JADE)
	panel(Rect2(w-253,196,229,105))
	text("THE LAST LANTERNS",Vector2(w-237,220),13,GOLD)
	if not p.is_empty():
		if p.quest==0:
			text("Speak to Keeper Suri",Vector2(w-237,247),14)
			text("E  ·  Interact",Vector2(w-237,276),12,JADE)
		elif p.quest==1:
			text("Ember seals       %d / 5"%p.seals,Vector2(w-237,250),15)
			text("Return to Suri for Dawnsteel",Vector2(w-237,276),11,JADE)
		else:
			text("Dawnsteel earned",Vector2(w-237,250),15,JADE)
			text("The village remembers",Vector2(w-237,276),12)
	var x=w/2-250
	panel(Rect2(x-14,h-116,528,90))
	if not p.is_empty():
		draw_rect(Rect2(x,h-105,244,6),Color("3e3030"))
		draw_rect(Rect2(x,h-105,244*float(p.hp)/p.max_hp,6),Color("ae6255"))
		draw_rect(Rect2(x+257,h-105,243,6),Color("2c3a36"))
		draw_rect(Rect2(x+257,h-105,243*p.stamina/100,6),JADE)
		text("VITALITY  %d / %d"%[p.hp,p.max_hp],Vector2(x,h-84),10)
		text("QI  %d"%p.stamina,Vector2(x+257,h-84),10)
	var keys=["1 / LMB","Q","R","SPACE","H","E"]
	var labels=["Slash","Jade arc","Threadstrike","Sky vault","Flask","Gather"]
	for i in 6:
		var left=x+i*84
		if i>0:draw_line(Vector2(left-5,h-76),Vector2(left-5,h-37),Color("4d5140"),1)
		text(keys[i],Vector2(left+3,h-61),10,GOLD)
		text(labels[i],Vector2(left+3,h-41),11)
		if not p.is_empty():
			var cd=p.arc_cd if i==1 else (p.line_cd if i==2 else 0)
			if cd>0:text("%.1f"%cd,Vector2(left+56,h-61),11,JADE)
	text("WASD / CLICK  ·  TAB satchel  ·  F1 realm  ·  F2 guide",Vector2(x+54,h-9),10,Color("b0b6a5"))
	text("%s  /  %d wanderer%s"%[mode.to_upper(),state.get("players",{}).size(),"" if state.get("players",{}).size()==1 else "s"],Vector2(25,h-29),11,Color("d3ceb5"))
	if demo:text("IN-ENGINE · AUTOMATED INPUT",Vector2(25,h-12),9,GOLD)
	if notice_timer>0 and not last_notice.is_empty():
		var lines=wrap_lines(last_notice,45)
		panel(Rect2(24,h-155,300,32+mini(lines.size(),3)*17),Color("152525dc"))
		for i in mini(lines.size(),3):text(lines[i],Vector2(38,h-132+i*17),12,PAPER)
	if not p.is_empty() and p.dead>0:
		panel(Rect2(w/2-200,h/2-60,400,105),Color("1a2428ed"))
		text("THE SHRINE CALLS YOU HOME",Vector2(w/2-169,h/2-20),20,GOLD)
		text("Return in %.1f seconds"%p.dead,Vector2(w/2-94,h/2+13),16)
	if inventory and not p.is_empty():
		panel(Rect2(24,143,520,453),Color("0b1c20f5"))
		text("THE WANDERER'S SATCHEL",Vector2(43,178),20,GOLD)
		text("VISIBLE EQUIPMENT",Vector2(262,198),10,JADE)
		var stats=Equipment.stats(p)
		text("Attack %d  ·  Guard %d  ·  Vitality %d"%[stats.attack,stats.defense,stats.max_hp],Vector2(262,381),12,GOLD)
		text("%s weapon"%String(Equipment.item(p,"weapon").quality).capitalize(),Vector2(262,409),13,JADE)
		text("Flasks  %d     Ember seals  %d"%[p.potions,p.seals],Vector2(262,449),13)
		text("Copper  %d    XP  %d / %d"%[p.gold,p.xp,p.level*80],Vector2(262,478),12)
		text("Two original preview kits are owned",Vector2(262,520),11)
		text("C armor · V head · B weapon · TAB close",Vector2(43,570),12)
	if help:
		panel(Rect2(w/2-265,160,530,415))
		text("A WANDERER'S GUIDE",Vector2(w/2-240,210),24,GOLD)
		var lines=["WASD moves relative to the camera. Click ground to walk.","Click a marauder to approach and attack automatically.","Q: Jade arc hits all nearby enemies. Costs 32 qi.","R: Threadstrike hits a thin aimed line. Costs 25 qi.","Space or Ctrl+click: vault toward cursor. Costs 22 qi.","E: talk to Suri / collect nearby gold and ember seals.","H: drink a healing flask. Suri also restores vitality.","Gather five seals, return to Suri, earn Dawnsteel.","F1: local / LAN realm. No public servers or accounts yet.","C / V / B: cycle owned armor / headgear / weapons.","F2 closes this guide. Escape quits the game."]
		for i in lines.size():text(lines[i],Vector2(w/2-240,246+i*28),14)
func wrap_lines(value:String,limit:int)->Array[String]:
	var result:Array[String]=[]
	var current=""
	for word in value.split(" "):
		if (current+word).length()>limit:
			result.append(current)
			current=""
		current+=word+" "
	if not current.is_empty():result.append(current)
	return result

func build_character_preview():
	if not ResourceLoader.exists("res://assets/models/hero_modular.glb"):return
	preview_container=SubViewportContainer.new()
	preview_container.position=Vector2(41,205)
	preview_container.size=Vector2(202,328)
	preview_container.stretch=true
	preview_container.mouse_filter=Control.MOUSE_FILTER_IGNORE
	add_child(preview_container)
	preview_viewport=SubViewport.new()
	preview_viewport.size=Vector2i(404,656)
	preview_viewport.own_world_3d=true
	preview_viewport.transparent_bg=true
	preview_viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	preview_container.add_child(preview_viewport)
	preview_root=Node3D.new()
	preview_viewport.add_child(preview_root)
	var environment=WorldEnvironment.new()
	var env=Environment.new()
	env.background_mode=Environment.BG_COLOR
	env.background_color=Color("132622")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color=Color("d6dfdd")
	env.ambient_light_energy=.65
	environment.environment=env
	preview_root.add_child(environment)
	var light=DirectionalLight3D.new()
	light.rotation_degrees=Vector3(-38,-35,0)
	light.light_color=Color("ffe4ba")
	light.light_energy=.9
	preview_root.add_child(light)
	var camera=Camera3D.new()
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=2.65
	preview_root.add_child(camera)
	camera.position=Vector3(3,1.85,5)
	camera.look_at(Vector3(0,1.05,0))
	var character=load("res://assets/models/hero_modular.glb").instantiate()
	preview_root.add_child(character)
	preview_actor={"visual":character,"gear_signature":""}
	var animators=character.find_children("*","AnimationPlayer",true,false)
	if not animators.is_empty() and animators[0].has_animation("idle"):
		animators[0].get_animation("idle").loop_mode=Animation.LOOP_LINEAR
		animators[0].play("idle")
	preview_container.hide()
