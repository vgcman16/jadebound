extends Node
## Finite native event demonstration. Fixture setup is explicit, actions use Input events.
var app
var elapsed=0.0
var stage=0
var cues=[.3,1.7,2.4,3.4,3.7,4.3,4.6,5.5,6.2,6.6,7.2,7.6,8.3,9.5]
var p:Dictionary
func _ready():
	p=app.net.model.players[1]
	p.pos=Vector2(3,2)
	for enemy in app.net.model.enemies.values():enemy.dead=30.0
	app.net.model.enemies[1].dead=0.0
	app.net.model.enemies[1].hp=18
	app.net.model.enemies[1].pos=Vector2(5,2)
	app.controls.reset(false)
	app.view.camera.size=12
	app.view.follow=Vector3(3,0,2)
	app.hud.notice="INPUT QA · level 1 fixture · left-click a foe to approach and attack"
func _process(delta):
	elapsed+=delta
	if stage>=cues.size() or elapsed<cues[stage]:return
	match stage:
		0:click_world(app.net.model.enemies[1].pos,1.2,MOUSE_BUTTON_LEFT)
		1:
			assert(app.net.model.enemies[1].dead>0)
			assert(not app.net.model.drops.is_empty())
			click_world(app.net.model.drops.values()[0].pos,.3,MOUSE_BUTTON_LEFT)
			app.hud.notice="LEFT-CLICK LOOT · approach and gather through normal input"
		2:
			assert(p.gold==9 and app.net.model.drops.is_empty())
			click_world(p.pos+Vector2(-4,-1),0,MOUSE_BUTTON_LEFT,true)
			app.hud.notice="CTRL + LEFT-CLICK · directional vault"
		3:key(KEY_F2);app.hud.notice="F2 selects Jade Arc · right-click attempts the selected skill"
		4:
			click_world(p.pos+Vector2(2,0),0,MOUSE_BUTTON_RIGHT)
		5:
			assert(p.arc_cd==0 and p.notice.contains("level 3"))
			key(KEY_TAB)
			app.hud.notice="LEVEL 1 · Jade Arc rejected · try owned Warden armor"
		6:click_screen(Vector2(392,226),MOUSE_BUTTON_RIGHT)
		7:
			assert(p.gear.armor=="wayfarer_coat")
			app.hud.notice="UNDER-LEVEL GEAR REJECTED · authoritative loadout stays unchanged"
		8:
			# This is a labelled review fixture advance, not earned progression footage.
			p.level=3;p.mastery.slash=3
			app.net.model.sync_progression(p)
			app.net.model.recalculate_stats(p)
			app.hud.notice="QA FIXTURE ADVANCES TO LEVEL 3 · level/stat/practice gates now met"
		9:click_screen(Vector2(392,226),MOUSE_BUTTON_RIGHT)
		10:
			assert(p.gear.armor=="warden_lamellar")
			key(KEY_TAB);key(KEY_F2)
			app.hud.notice="ELIGIBLE ARMOR EQUIPPED · F2 selects newly learned Jade Arc"
		11:click_world(p.pos+Vector2(2,0),0,MOUSE_BUTTON_RIGHT)
		12:
			assert(p.arc_cd>0)
			app.hud.notice="RIGHT-CLICK CAST SUCCEEDED · all tested control actions travelled through native input events"
		13:print("JADE_NATIVE_INPUT_DEMO_PASSED move/attack/loot/vault/hotbar/cast/locked/equip")
	print("INPUT_QA_STAGE ",stage," time=",elapsed," level=",p.level," gear=",p.gear)
	stage+=1
func key(code:int):
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true
	Input.parse_input_event(event)
	var released=event.duplicate();released.pressed=false
	Input.parse_input_event(released)
func click_world(pos:Vector2,height:float,button:int,ctrl:bool=false):
	click_screen(app.view.camera.unproject_position(Vector3(pos.x,height,pos.y)),button,ctrl)
func click_screen(pos:Vector2,button:int,ctrl:bool=false):
	var motion=InputEventMouseMotion.new();motion.position=pos;motion.global_position=pos
	get_viewport().push_input(motion,true)
	var event=InputEventMouseButton.new();event.position=pos;event.global_position=pos;event.button_index=button;event.pressed=true;event.ctrl_pressed=ctrl
	get_viewport().push_input(event,true)
	var released=event.duplicate();released.pressed=false
	get_viewport().push_input(released,true)
