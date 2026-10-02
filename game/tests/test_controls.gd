extends SceneTree
const Controls=preload("res://scripts/controls.gd")
var n=0
var failures=0
func check(ok:bool,label:String):
	n+=1
	if ok:print("PASS CONTROLS: "+label)
	else:failures+=1;push_error(label)
func _initialize():
	var c=Controls.new()
	check(c.slots.size()==10,"ten assignable hotbar slots")
	for i in 10:check(c.keys["slot_%d"%i]==KEY_F1+i,"function key slot %d"%i)
	check(c.keys.menu==KEY_F11 and c.keys.guide==KEY_F12,"menu and guide do not take hotbar keys")
	var old=c.keys.inventory
	check(c.bind("inventory",KEY_E),"single-key remap accepted")
	check(c.keys.interact==old,"conflicting key assignments swap")
	check(not c.bind("inventory",KEY_ESCAPE),"escape safety key remains reserved")
	var event=InputEventKey.new()
	event.physical_keycode=KEY_E
	event.pressed=true
	check(c.pressed(event,"inventory"),"remap updates native InputMap")
	c.cycle_slot(0)
	check(c.slots[0]=="jade_arc","slot assignment cycles independently of key")
	c.wasd_enabled=false
	check(c.movement()==Vector2.ZERO,"optional keyboard movement can be disabled")
	c.reset(false)
	check(c.keys.inventory==KEY_TAB and c.slots==Controls.DEFAULT_SLOTS,"restore defaults is deterministic")
	if failures==0:print("JADE_CONTROLS_TESTS_PASSED ",n)
	quit(0 if failures==0 else 1)
