extends Node
## Godot GUI-event check on the playable prototype. Screenshots need a native window.
## --event-check-only is an unrendered code-path test, not visual/native-desktop proof.
var app
var directory:String
func _ready():
	directory=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()+"/builds/unequip-input-review"
	DirAccess.make_dir_recursive_absolute(directory)
	await get_tree().create_timer(.5).timeout
	app.controls.reset(false)
	var key=InputEventKey.new();key.physical_keycode=KEY_TAB;key.pressed=true;Input.parse_input_event(key)
	await get_tree().process_frame
	key=key.duplicate();key.pressed=false;Input.parse_input_event(key)
	await get_tree().create_timer(.3).timeout
	assert(app.hud.inventory)
	var player=app.net.model.players[1]
	var owned=player.owned_equipment.duplicate()
	await click_slot("weapon",MOUSE_BUTTON_RIGHT)
	assert(player.gear.weapon=="")
	await click_slot("armor",MOUSE_BUTTON_RIGHT)
	assert(player.gear.armor=="")
	await click_slot("head",MOUSE_BUTTON_RIGHT)
	assert(player.gear.head=="")
	assert(player.owned_equipment==owned)
	app.hud.notice="NATIVE GUI EVENT CHECK · three slots removed · items remain owned"
	await capture("slots-removed")
	await click_slot("armor",MOUSE_BUTTON_LEFT)
	assert(player.gear.armor=="wayfarer_coat")
	await click_slot("head",MOUSE_BUTTON_LEFT)
	assert(player.gear.head=="topknot")
	await click_slot("weapon",MOUSE_BUTTON_LEFT)
	assert(player.gear.weapon=="reed_saber")
	app.hud.notice="NATIVE GUI EVENT CHECK · owned starter gear restored"
	await capture("slots-restored")
	print("JADE_UNEQUIP_GUI_PASSED Tab plus six pointer-event slot transitions; visual_capture=",not "--event-check-only" in OS.get_cmdline_user_args())
	get_tree().quit()
func click_slot(slot:String,button:int):
	var point=app.hud.gear_buttons[slot].get_global_rect().get_center()
	var event=InputEventMouseButton.new();event.position=point;event.global_position=point;event.button_index=button;event.pressed=true
	event.button_mask=MOUSE_BUTTON_MASK_RIGHT if button==MOUSE_BUTTON_RIGHT else MOUSE_BUTTON_MASK_LEFT
	get_viewport().push_input(event,true)
	await get_tree().process_frame
	event=event.duplicate();event.pressed=false;event.button_mask=0;get_viewport().push_input(event,true)
	await get_tree().create_timer(.35).timeout
func capture(name_:String):
	if "--event-check-only" in OS.get_cmdline_user_args():
		print("UNEQUIP_EVENT_CHECKPOINT ",name_);return
	await get_tree().create_timer(.2).timeout
	await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(directory+"/"+name_+".png")==OK)
