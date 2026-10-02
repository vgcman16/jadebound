extends Node
var app
var directory:String
func _ready():
	directory=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()+"/builds/controls-review"
	DirAccess.make_dir_recursive_absolute(directory)
	await get_tree().create_timer(.5).timeout
	app.controls.reset(false)
	await capture("mouse-first-gameplay")
	await key(KEY_TAB)
	assert(app.hud.inventory)
	await capture("starter-equipment-locked")
	var before=app.net.model.players[1].gear.duplicate(true)
	app.cycle_equipment("armor")
	assert(app.net.model.players[1].gear==before)
	await key(KEY_TAB)
	await key(KEY_F11)
	assert(app.realm_panel.visible)
	await capture("realm-menu")
	app.realm_panel.hide()
	app.controls_panel.show()
	await capture("remappable-controls")
	app.controls_panel.waiting="inventory"
	await key(KEY_T)
	assert(app.controls.keys.inventory==KEY_T)
	await capture("remapped-inventory")
	await key(KEY_ESCAPE)
	assert(not app.controls_panel.visible)
	await key(KEY_T)
	assert(app.hud.inventory)
	await key(KEY_T)
	app.controls.reset()
	print("JADE_CONTROLS_UI_PASSED 6 event-driven transitions and 5 screenshots")
	get_tree().quit()
func key(code:int):
	var event=InputEventKey.new()
	event.physical_keycode=code
	event.pressed=true
	Input.parse_input_event(event)
	await get_tree().process_frame
	event=event.duplicate()
	event.pressed=false
	Input.parse_input_event(event)
	await get_tree().process_frame
func capture(label:String):
	await get_tree().create_timer(.15).timeout
	await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(directory+"/"+label+".png")==OK)
