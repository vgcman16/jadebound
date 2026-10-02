extends SceneTree
const Coverage=preload("res://scripts/appearance_coverage.gd")
var count=0
var failures=0
func check(ok:bool,message:String):
	count+=1
	if not ok:failures+=1;push_error("FAIL COVERAGE: "+message)
	else:print("PASS COVERAGE: "+message)
func _initialize():
	var model=Node3D.new();root.add_child(model)
	for name_ in ["Body_Torso","Body_Arms","Body_UpperLegs","Body_Hands","Body_Fingers","Body_LowerLegs","Body_Feet","Body_Head","Body_Eye_L","Body_Hair_Scalp","Body_Underwear","Gear_Warden_Coat","Gear_Boots_Shell","Gear_Gloves_Wrap","Head_Warden_Helm"]:
		var node=MeshInstance3D.new();node.name=name_;model.add_child(node)
	var all={"armor":"Gear_Warden","boots":"Gear_Boots","gloves":"Gear_Gloves","head":"Head_Warden"}
	Coverage.apply(model,all)
	for region in Coverage.REGIONS:check(not model.get_node(region).visible,"covered region hidden: "+region)
	for name_ in ["Body_Underwear","Body_Head","Body_Fingers","Body_Eye_L"]:check(model.get_node(name_).visible,"permanent base remains: "+name_)
	check(not model.get_node("Body_Hair_Scalp").visible,"helmet hides only base hair")
	for pair in [["armor","Gear_Warden_Coat","Body_Torso"],["boots","Gear_Boots_Shell","Body_Feet"],["gloves","Gear_Gloves_Wrap","Body_Hands"],["head","Head_Warden_Helm","Body_Hair_Scalp"]]:
		model.get_node(pair[1]).visible=false
		Coverage.apply(model,all)
		check(model.get_node(pair[2]).visible,"removal restores underlying "+pair[0])
		check(model.get_node("Body_Underwear").visible,"underwear survives "+pair[0]+" removal")
		model.get_node(pair[1]).visible=true
		Coverage.apply(model,all)
		check(not model.get_node(pair[2]).visible,"re-equip restores only coverage for "+pair[0])
	Coverage.apply(model,{})
	for region in Coverage.REGIONS:check(model.get_node(region).visible,"empty state restores: "+region)
	Coverage.apply(model,{"armor":"Missing_Armor"})
	check(model.get_node("Body_Torso").visible,"missing asset cannot erase body")
	check(model.get_node("Body_Underwear").visible,"underwear cannot be removed through coverage")
	model.free()
	if failures==0:print("JADE_COVERAGE_TESTS_PASSED ",count)
	quit(0 if failures==0 else 1)
