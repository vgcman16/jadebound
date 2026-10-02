extends SceneTree
## Actual engine rendering of a separate art study; never swaps runtime assets.
var stage:Node3D
var camera:Camera3D
var heading:Label
var note:Label
var out_dir:String
var source_path:String
func _initialize():call_deferred("run_study")
func run_study():
	var project_root=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	source_path=project_root+"/art/concept-warden/river_warden_clay.glb"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--concept-file="):source_path=argument.trim_prefix("--concept-file=")
	if not FileAccess.file_exists(source_path):
		push_error("Concept study file is not generated: "+source_path);quit(2);return
	out_dir=project_root+"/builds/concept-engine-study"
	DirAccess.make_dir_recursive_absolute(out_dir)
	stage=Node3D.new();root.add_child(stage)
	var env=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color("30383a")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("c9ced0");env.ambient_light_energy=.42
	env.sky=RealmView.neutral_reflection_sky();env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	var environment=WorldEnvironment.new();environment.environment=env;stage.add_child(environment)
	var key=DirectionalLight3D.new();key.rotation_degrees=Vector3(-42,-36,0);key.light_energy=.85;key.light_color=Color("f2f1e9");key.shadow_enabled=true;stage.add_child(key)
	var ground=MeshInstance3D.new();var plane=PlaneMesh.new();plane.size=Vector2(60,60);ground.mesh=plane;ground.position.y=0.0
	var ground_mat=StandardMaterial3D.new();ground_mat.albedo_color=Color("444947");ground_mat.roughness=.95;ground.material_override=ground_mat;stage.add_child(ground)
	camera=Camera3D.new();camera.projection=Camera3D.PROJECTION_ORTHOGONAL;stage.add_child(camera)
	var canvas=CanvasLayer.new();root.add_child(canvas)
	heading=Label.new();heading.position=Vector2(28,24);heading.add_theme_font_size_override("font_size",22);canvas.add_child(heading)
	note=Label.new();note.position=Vector2(28,64);note.text="Actual Godot renderer · separate static art study · VFX off · not integrated gameplay";canvas.add_child(note)
	var document=GLTFDocument.new();var state=GLTFState.new()
	if document.append_from_file(source_path,state)!=OK:
		push_error("Could not load concept GLB");quit(3);return
	var hero=document.generate_scene(state)
	if not hero:push_error("Could not instantiate concept GLB");quit(4);return
	stage.add_child(hero)
	set_study_equipment(hero,true,true,true)
	var bones=0
	for skeleton in hero.find_children("*","Skeleton3D",true,false):bones+=skeleton.get_bone_count()
	print("CONCEPT_NATIVE_IMPORT bones=",bones," meshes=",hero.find_children("*","MeshInstance3D",true,false).size())
	if "--import-only" in OS.get_cmdline_user_args():
		print("JADE_CONCEPT_IMPORT_OK");quit();return
	camera.size=3.3;camera.position=Vector3(3.5,2.4,5);camera.look_at(Vector3(0,.96,0))
	if "--layer-movie" in OS.get_cmdline_user_args():
		note.text="Actual Godot art fixture · static poses · accessory gameplay integration pending"
		var steps=[
			[true,true,true,"SEPARATE EQUIPMENT · armor, boots and gloves"],
			[false,true,true,"ARMOR OFF · body and underwear · boots / gloves stay"],
			[false,false,true,"BOOTS OFF · legs and feet restored"],
			[false,false,false,"GLOVES OFF · base body with permanent underwear"],
			[true,true,true,"EQUIPMENT RESTORED · shared body and rig"]]
		for i in steps.size():
			var step=steps[i]
			set_study_equipment(hero,step[0],step[1],step[2]);heading.text=step[3]
			await capture("movie-step-%d.png"%i,1.0)
		print("JADE_CONCEPT_LAYER_MOVIE_CAPTURED 5 static coverage states")
		quit();return
	heading.text="RIVER WARDEN · first clothed form study · three-quarter"
	await capture("front-close.png")
	camera.position=Vector3(-3.5,2.4,-5);camera.look_at(Vector3(0,.96,0));heading.text="RIVER WARDEN · first clothed form study · rear"
	await capture("rear-close.png")
	camera.size=14.5;camera.position=Vector3(17,21,17);camera.look_at(Vector3(0,.8,0));heading.text="RIVER WARDEN · normal gameplay scale · static form study"
	await capture("gameplay-scale.png")
	camera.size=3.3;camera.position=Vector3(3.5,2.4,5);camera.look_at(Vector3(0,.96,0))
	note.text="Actual Godot renderer · visual coverage fixture · accessory game integration pending"
	set_study_equipment(hero,false,true,true)
	heading.text="ARMOR REMOVED · base body / underwear · boots + gloves retained"
	await capture("armor-removed.png")
	set_study_equipment(hero,false,false,true)
	heading.text="BOOTS REMOVED · underlying legs / feet restored · gloves retained"
	await capture("boots-removed.png")
	set_study_equipment(hero,false,false,false)
	heading.text="ALL STUDY GEAR REMOVED · adult base / permanent underwear"
	await capture("base-underwear.png")
	set_study_equipment(hero,true,true,true)
	heading.text="STUDY GEAR RESTORED · independent meshes / reversible coverage"
	await capture("gear-restored.png")
	print("JADE_CONCEPT_ENGINE_STUDY_CAPTURED 7 frames")
	quit()
func capture(file_name:String,hold:float=.6):
	await create_timer(hold).timeout
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(out_dir+"/"+file_name)==OK)

func set_study_equipment(hero:Node,armor:bool,boots:bool,gloves:bool):
	var enabled={"Gear_Warden":armor,"Gear_Boots":boots,"Gear_Gloves":gloves}
	for node in hero.find_children("*","MeshInstance3D",true,false):
		for prefix in enabled:
			if String(node.name).begins_with(prefix):node.visible=enabled[prefix]
	var selected={}
	if armor:selected.armor="Gear_Warden"
	if boots:selected.boots="Gear_Boots"
	if gloves:selected.gloves="Gear_Gloves"
	JadeAppearanceCoverage.apply(hero,selected)
	# This isolated export lifts the rig15mm for its boot sole; bare feet restore ground contact.
	hero.position.y=0.0 if boots else -.015
	assert(hero.find_child("Body_Underwear",true,false).visible)
