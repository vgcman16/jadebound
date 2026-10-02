class_name JadeControls
extends RefCounted
## Original remappable single-key profile; mouse destination/cast controls stay explicit.
const PATH="user://jadebound-controls.cfg"
const DEFAULT_KEYS={"move_up":KEY_W,"move_down":KEY_S,"move_left":KEY_A,"move_right":KEY_D,"inventory":KEY_TAB,"interact":KEY_E,"jump":KEY_SPACE,"menu":KEY_F11,"guide":KEY_F12,"cycle_armor":KEY_C,"cycle_head":KEY_V,"cycle_weapon":KEY_B}
const DEFAULT_SLOTS=["slash","jade_arc","threadstrike","sky_vault","flask","gather","","","",""]
const SLOT_CHOICES=["","slash","jade_arc","threadstrike","sky_vault","flask","gather"]
const LABELS={"slash":"Reed Cut","jade_arc":"Jade Arc","threadstrike":"Threadstrike","sky_vault":"Sky Vault","flask":"Flask","gather":"Gather"}
var keys:Dictionary={}
var slots:Array=[]
var wasd_enabled:bool=true
func _init():
	reset(false)
func reset(persist:bool=true):
	keys=DEFAULT_KEYS.duplicate()
	for i in 10:keys["slot_%d"%i]=KEY_F1+i
	slots=DEFAULT_SLOTS.duplicate()
	wasd_enabled=true
	apply()
	if persist:save()
func load_profile():
	var config=ConfigFile.new()
	if config.load(PATH)!=OK:return
	for action in keys:
		var value=config.get_value("keys",action,keys[action])
		if value is int and value>0 and value!=KEY_ESCAPE:keys[action]=value
	for i in 10:
		var value=config.get_value("slots",str(i),slots[i])
		if value is String and value in SLOT_CHOICES:slots[i]=value
	wasd_enabled=bool(config.get_value("profile","wasd_enabled",true))
	apply()
func save():
	var config=ConfigFile.new()
	for action in keys:config.set_value("keys",action,keys[action])
	for i in 10:config.set_value("slots",str(i),slots[i])
	config.set_value("profile","wasd_enabled",wasd_enabled)
	return config.save(PATH)
func apply():
	for action in keys:
		var input_name="jade_"+action
		if not InputMap.has_action(input_name):InputMap.add_action(input_name)
		InputMap.action_erase_events(input_name)
		var event=InputEventKey.new()
		event.physical_keycode=keys[action]
		InputMap.action_add_event(input_name,event)
func bind(action:String,key:int)->bool:
	if not keys.has(action) or key<=0 or key==KEY_ESCAPE:return false
	# Swap conflicting key assignments so one press never triggers two actions.
	var old=keys[action]
	for other in keys:
		if other!=action and keys[other]==key:keys[other]=old
	keys[action]=key
	apply()
	save()
	return true
func key_label(action:String)->String:
	return OS.get_keycode_string(keys.get(action,0))
func pressed(event:InputEvent,action:String)->bool:
	return event.is_action_pressed("jade_"+action) and not event.is_echo()
func movement()->Vector2:
	if not wasd_enabled:return Vector2.ZERO
	var forward=Input.get_action_strength("jade_move_down")-Input.get_action_strength("jade_move_up")
	var side=Input.get_action_strength("jade_move_right")-Input.get_action_strength("jade_move_left")
	return Vector2(forward+side,forward-side).limit_length(1)
func cycle_slot(index:int):
	if index<0 or index>=10:return
	slots[index]=SLOT_CHOICES[(SLOT_CHOICES.find(slots[index])+1)%SLOT_CHOICES.size()]
	save()
