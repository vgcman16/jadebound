extends SceneTree
const World=preload("res://scripts/world_model.gd")
const Equipment=preload("res://scripts/equipment_data.gd")
const View=preload("res://scripts/realm_view.gd")
var failures=0
var assertions=0
func check(ok:bool,label:String):
	assertions+=1
	if ok:print("PASS VISUAL CONTRACT: "+label)
	else:
		failures+=1
		push_error("FAIL VISUAL CONTRACT: "+label)
func _initialize():call_deferred("run_tests")
func run_tests():
	var scene=load("res://assets/models/hero_modular.glb")
	check(scene is PackedScene,"modular native scene imports")
	var model=scene.instantiate()
	root.add_child(model)
	var skeletons=model.find_children("*","Skeleton3D",true,false)
	check(skeletons.size()==1 and skeletons[0].get_bone_count()>=20,"native articulated skeleton")
	var names=["Body_Base","Gear_Wayfarer","Gear_Warden","Head_Topknot","Head_Warden","Weapon_Saber","Weapon_Glaive"]
	for name_ in names:
		var node=model.find_child(name_,true,false)
		check(node is MeshInstance3D and node.skin!=null,"skinned mesh "+name_)
	var animators=model.find_children("*","AnimationPlayer",true,false)
	check(not animators.is_empty(),"native animation player")
	for clip in ["idle","walk","run","attack","jump"]:check(animators[0].has_animation(clip),"animation "+clip)
	var world=World.new()
	world.add_player(1)
	var p=world.players[1]
	var view=View.new()
	var actor={"visual":model,"gear_signature":""}
	for mask in 8:
		p.gear={"armor":"warden_lamellar" if mask&1 else "wayfarer_coat","head":"warden_helm" if mask&2 else "topknot","weapon":"ironwind_glaive" if mask&4 else "reed_saber"}
		view.apply_equipment(actor,p)
		var selected:Array=[]
		for slot in Equipment.SLOTS:selected.append(Equipment.item(p,slot).mesh)
		var visible:Array=[]
		for name_ in names:
			if name_!="Body_Base" and model.find_child(name_,true,false).visible:visible.append(name_)
		check(visible.size()==3 and selected.all(func(n):return n in visible),"exactly one visible mesh per slot, combination %d"%mask)
	p.gear.weapon="dawnsteel_saber"
	view.apply_equipment(actor,p)
	check(count_glowing(model)>0,"Super blade-local material layer")
	p.gear.weapon="ironwind_glaive"
	view.apply_equipment(actor,p)
	check(count_glowing(model)==0,"swap clears old weapon emission")
	p.gear.weapon="dawnsteel_saber"
	p.dead=1
	view.apply_equipment(actor,p)
	check(count_glowing(model)==0,"death clears weapon emission")
	p.dead=0
	view.apply_equipment(actor,p)
	check(count_glowing(model)>0,"respawn restores only current quality layer")
	view.free()
	model.queue_free()
	if failures==0:print("JADE_MODULAR_VISUAL_CONTRACT_PASSED ",assertions)
	quit(0 if failures==0 else 1)
func count_glowing(model:Node)->int:
	var result=0
	for node in model.find_children("*","MeshInstance3D",true,false):
		for i in node.mesh.get_surface_count():
			var material=node.get_surface_override_material(i)
			if material is StandardMaterial3D and material.emission_enabled:result+=1
	return result
