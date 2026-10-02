extends SceneTree
## Neutral and albedo-only renderer study; explicitly not gameplay footage.
var stage:Node3D
var inspector
var title:Label
func _initialize():call_deferred("run_study")
func run_study():
	stage=Node3D.new();root.add_child(stage)
	var environment=WorldEnvironment.new()
	var env=Environment.new()
	env.background_mode=Environment.BG_COLOR
	env.background_color=Color("293237")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color=Color("c0c5c7")
	env.ambient_light_energy=.42
	env.sky=RealmView.neutral_reflection_sky()
	env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	environment.environment=env;stage.add_child(environment)
	var key=DirectionalLight3D.new();key.rotation_degrees=Vector3(-42,-36,0);key.light_energy=.85;key.light_color=Color("f2f1e9");key.shadow_enabled=true;stage.add_child(key)
	var floor_node=MeshInstance3D.new();var plane=PlaneMesh.new();plane.size=Vector2(15,15);floor_node.mesh=plane;floor_node.position.y=-.052
	var floor_mat=StandardMaterial3D.new();floor_mat.albedo_color=Color("323b38");floor_mat.roughness=.95;floor_node.material_override=floor_mat;stage.add_child(floor_node)
	var slabs=load("res://assets/models/flagstone_samples.glb").instantiate();stage.add_child(slabs)
	inspector=RealmView.new()
	var camera=Camera3D.new();camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=3.9;stage.add_child(camera);camera.position=Vector3(3.6,3.0,5);camera.look_at(Vector3(0,.8,0))
	var canvas=CanvasLayer.new();root.add_child(canvas)
	title=Label.new();title.position=Vector2(28,24);title.add_theme_font_size_override("font_size",22);canvas.add_child(title)
	var caption=Label.new();caption.position=Vector2(28,62);caption.text="Original Warden + four actual slab meshes · diagnostic art study, not gameplay";canvas.add_child(caption)
	var directory=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()+"/builds/material-study"
	DirAccess.make_dir_recursive_absolute(directory)
	var variants={"after":"res://assets/models/hero_modular.glb"}
	if ResourceLoader.exists("res://tests/local_material_before/hero_before.glb"):
		variants={"before":"res://tests/local_material_before/hero_before.glb","after":"res://assets/models/hero_modular.glb"}
	for variant in variants:
		var hero=load(variants[variant]).instantiate();stage.add_child(hero)
		var appearance={"visual":hero,"gear_signature":""}
		inspector.apply_equipment(appearance,{"gear":{"armor":"warden_lamellar","head":"warden_helm","weapon":"ironwind_glaive"},"dead":0})
		var animator=hero.find_children("*","AnimationPlayer",true,false)[0]
		animator.play("idle");animator.seek(.6,true);animator.advance(0);animator.pause()
		title.text="%s ATLAS · NEUTRAL MATERIAL STUDY · quality VFX off"%variant.to_upper()
		await capture(directory+"/"+variant+"-neutral.png")
		var restore:Array=[]
		for node in stage.find_children("*","MeshInstance3D",true,false):
			for i in node.mesh.get_surface_count():
				var override_material=node.get_surface_override_material(i)
				var original=override_material if override_material else node.mesh.surface_get_material(i)
				if original is StandardMaterial3D:
					restore.append([node,i,override_material])
					var unlit=original.duplicate();unlit.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;node.set_surface_override_material(i,unlit)
		title.text="%s ATLAS · ALBEDO-ONLY · textures without lighting"%variant.to_upper()
		await capture(directory+"/"+variant+"-albedo.png")
		for item in restore:item[0].set_surface_override_material(item[1],item[2])
		hero.queue_free()
		await process_frame
	inspector.free()
	print("JADE_MATERIAL_STUDY_CAPTURED neutral and albedo-only frames")
	quit()
func capture(path:String):
	await create_timer(.6).timeout
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(path)==OK)
