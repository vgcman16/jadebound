class_name JadeControlsPanel
extends PanelContainer
signal closed
var profile:JadeControls
var waiting:String=""
var key_buttons:Dictionary={}
var slot_buttons:Array=[]
var prompt:Label
var wasd:CheckBox
func configure(value:JadeControls):
	profile=value
	var style=StyleBoxFlat.new()
	style.bg_color=Color("102524f5")
	style.border_color=Color("857452")
	style.set_border_width_all(1)
	style.set_corner_radius_all(4)
	add_theme_stylebox_override("panel",style)
	position=Vector2(280,58)
	custom_minimum_size=Vector2(720,660)
	var margin=MarginContainer.new()
	for side in ["left","right","top","bottom"]:margin.add_theme_constant_override("margin_"+side,20)
	add_child(margin)
	var stack=VBoxContainer.new()
	stack.add_theme_constant_override("separation",10)
	margin.add_child(stack)
	var title=Label.new()
	title.text="CONTROLS & HOTBAR"
	title.add_theme_font_size_override("font_size",23)
	stack.add_child(title)
	prompt=Label.new()
	prompt.text="Left-click: move / target · Ctrl+click: vault · Right-click: selected skill"
	stack.add_child(prompt)
	wasd=CheckBox.new()
	wasd.text="Enable secondary keyboard movement"
	wasd.button_pressed=profile.wasd_enabled
	wasd.toggled.connect(func(on:bool):profile.wasd_enabled=on;profile.save())
	stack.add_child(wasd)
	var columns=HBoxContainer.new()
	columns.add_theme_constant_override("separation",24)
	stack.add_child(columns)
	var keys_grid=GridContainer.new()
	keys_grid.columns=2
	columns.add_child(keys_grid)
	for action in profile.DEFAULT_KEYS:
		var label=Label.new()
		label.text=String(action).replace("_"," ").capitalize()
		keys_grid.add_child(label)
		var button=Button.new()
		button.custom_minimum_size=Vector2(100,30)
		button.focus_mode=Control.FOCUS_NONE
		button.pressed.connect(func():waiting=action;prompt.text="Press a new key for %s. Esc cancels; conflicts swap."%action)
		keys_grid.add_child(button)
		key_buttons[action]=button
	var slots_grid=GridContainer.new()
	slots_grid.columns=2
	columns.add_child(slots_grid)
	for i in 10:
		var binding=Button.new()
		binding.custom_minimum_size=Vector2(70,30)
		binding.focus_mode=Control.FOCUS_NONE
		binding.pressed.connect(func():waiting="slot_%d"%i;prompt.text="Press a new key for hotbar slot %d. Esc cancels."%(i+1))
		slots_grid.add_child(binding)
		key_buttons["slot_%d"%i]=binding
		var assignment=Button.new()
		assignment.custom_minimum_size=Vector2(145,30)
		assignment.focus_mode=Control.FOCUS_NONE
		assignment.pressed.connect(func():profile.cycle_slot(i);refresh())
		slots_grid.add_child(assignment)
		slot_buttons.append(assignment)
	var note=Label.new()
	note.text="Click an ability to cycle its slot assignment. A skill must be learned to cast.\nSingle physical keys are remappable; mouse bindings use the classic profile."
	note.add_theme_font_size_override("font_size",13)
	stack.add_child(note)
	var row=HBoxContainer.new()
	stack.add_child(row)
	var reset_button=Button.new()
	reset_button.text="Restore defaults"
	reset_button.pressed.connect(func():profile.reset();wasd.button_pressed=true;refresh())
	row.add_child(reset_button)
	var close_button=Button.new()
	close_button.text="Return to game"
	close_button.pressed.connect(close)
	row.add_child(close_button)
	refresh()
	hide()
func refresh():
	for action in key_buttons:key_buttons[action].text=profile.key_label(action)
	for i in slot_buttons.size():slot_buttons[i].text=profile.LABELS.get(profile.slots[i],"Empty")
func close():
	waiting=""
	hide()
	closed.emit()
func _input(event:InputEvent):
	if not visible or not event is InputEventKey or not event.pressed or event.echo:return
	if not waiting.is_empty():
		if event.physical_keycode!=KEY_ESCAPE:profile.bind(waiting,event.physical_keycode)
		waiting=""
		prompt.text="Left-click: move / target · Ctrl+click: vault · Right-click: selected skill"
		refresh()
		get_viewport().set_input_as_handled()
	elif event.physical_keycode==KEY_ESCAPE:
		close()
		get_viewport().set_input_as_handled()
