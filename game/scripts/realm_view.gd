class_name RealmView
extends Node3D
var actors:Dictionary={}
var loot_nodes:Dictionary={}
var camera:Camera3D
var elapsed:float=0
var follow:Vector3=Vector3(-3,0,1)
var materials:Dictionary={}
var effect_nodes:Array=[]
var selected:int=-1
var asset_cache:Dictionary={}

func mat(color:Color,glow:float=0.0)->StandardMaterial3D:
	var key=str(color)+str(glow)
	if materials.has(key): return materials[key]
	var m=StandardMaterial3D.new()
	m.albedo_color=color
	m.roughness=0.88
	if glow>0:
		m.emission_enabled=true
		m.emission=color
		m.emission_energy_multiplier=glow
	materials[key]=m
	return m

func mesh_node(mesh:Mesh,color:Color,pos:Vector3,parent:Node=self)->MeshInstance3D:
	var node=MeshInstance3D.new()
	node.mesh=mesh
	node.material_override=mat(color)
	node.position=pos
	parent.add_child(node)
	return node

func box(size:Vector3,pos:Vector3,color:Color,parent:Node=self)->MeshInstance3D:
	var mesh=BoxMesh.new()
	mesh.size=size
	return mesh_node(mesh,color,pos,parent)

func disk(radius:float,pos:Vector3,color:Color,parent:Node=self)->MeshInstance3D:
	var mesh=CylinderMesh.new()
	mesh.top_radius=radius
	mesh.bottom_radius=radius
	mesh.height=0.035
	mesh.radial_segments=32
	return mesh_node(mesh,color,pos,parent)

func model(name_:String,pos:Vector3,scale_:Vector3=Vector3.ONE,parent:Node=self)->Node3D:
	if not asset_cache.has(name_):
		var path="res://assets/models/%s.glb"%name_
		asset_cache[name_]=load(path) if ResourceLoader.exists(path) else null
	var node:Node3D
	if asset_cache[name_]: node=asset_cache[name_].instantiate()
	else:
		node=Node3D.new()
		var capsule=CapsuleMesh.new()
		capsule.radius=0.33
		capsule.height=1.8
		mesh_node(capsule,Color("5ad4b5") if name_=="hero" else Color("ac5555"),Vector3(0,0.9,0),node)
	node.position=pos
	node.scale=scale_
	parent.add_child(node)
	return node

func _ready():
	var environment=WorldEnvironment.new()
	var env=Environment.new()
	env.background_mode=Environment.BG_COLOR
	env.background_color=Color("263f46")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color=Color("91b1ae")
	env.ambient_light_energy=0.40
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.fog_enabled=true
	env.fog_light_color=Color("7aaba3")
	env.fog_density=0.002
	environment.environment=env
	add_child(environment)
	var sun=DirectionalLight3D.new()
	sun.rotation_degrees=Vector3(-52,-28,0)
	sun.light_color=Color("ffdea7")
	sun.light_energy=0.75
	sun.shadow_enabled=true
	sun.directional_shadow_max_distance=70
	add_child(sun)
	camera=Camera3D.new()
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=20
	camera.far=160
	add_child(camera)
	camera.position=follow+Vector3(17,21,17)
	camera.look_at(follow)
	build_landscape()

func build_landscape():
	var rng=RandomNumberGenerator.new()
	rng.seed=38140
	# Quiet, hand-colored low-poly terrain. Reproducible per-face color variation.
	var surface=SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for x in range(-25,26):
		for z in range(-25,26):
			var color=Color("718264").lerp(Color("a5ad78"),rng.randf_range(0,0.4))
			if x<1 and z<5: color=Color("7e8972").lerp(Color("a3a783"),rng.randf_range(0,0.25))
			for v in [Vector3(x,-0.05,z),Vector3(x+1,-0.05,z),Vector3(x,-0.05,z+1),Vector3(x+1,-0.05,z),Vector3(x+1,-0.05,z+1),Vector3(x,-0.05,z+1)]:
				surface.set_color(color)
				surface.add_vertex(v)
	surface.generate_normals()
	var land=MeshInstance3D.new()
	land.mesh=surface.commit()
	var land_mat=StandardMaterial3D.new()
	land_mat.vertex_color_use_as_albedo=true
	land_mat.vertex_color_is_srgb=true
	land_mat.roughness=1
	land.material_override=land_mat
	add_child(land)
	# Village plaza and stepping-stone road.
	disk(6.4,Vector3(-5,-0.02,-3),Color("9b9b80"))
	for i in range(26):
		var t=i/25.0
		var path=Vector3(lerpf(-5,14,t),0.02,lerpf(-3,9,t)+sin(t*8)*0.8)
		var p=box(Vector3(rng.randf_range(0.75,1.3),0.06,rng.randf_range(0.7,1.1)),path,Color("b5b29a").darkened(rng.randf_range(0,.12)))
		p.rotation.y=rng.randf_range(-.18,.18)
		var p2=box(Vector3(.8,.05,.85),path+Vector3(-.75,-.006,.65),Color("a4a58c"))
		p2.rotation.y=.1
	model("house",Vector3(-10,0,-7))
	model("house",Vector3(-10,0,1),Vector3(.85,.85,.85))
	var house=model("house",Vector3(-3,0,-11))
	house.rotation.y=PI/2
	model("shrine",Vector3(1,0,-8))
	model("gate",Vector3(0,0,-4),Vector3(.85,.85,.85)).rotation.y=-.8
	model("shrine",Vector3(-13,0,9),Vector3(1.1,1.1,1.1))
	model("elder",Vector3(JadeWorld.ELDER.x,0,JadeWorld.ELDER.y))
	world_label("KEEPER SURI",Vector3(-5,2.5,-4),Color("ffe5a3"),25)
	world_label("◆",Vector3(-5,3.2,-4),Color("ffd978"),44)
	# Lanterns mark the settlement and adventure boundary.
	for pos in [Vector3(-3,0,-1),Vector3(-7,0,-1),Vector3(2,0,0),Vector3(6,0,3),Vector3(-5,0,-8)]:
		model("lantern",pos)
		var light=OmniLight3D.new()
		light.position=pos+Vector3(0,1.5,0)
		light.light_color=Color("ffc87c")
		light.light_energy=.55
		light.omni_range=4
		add_child(light)
	# Tree clusters frame the play area, leaving the central field readable.
	for i in 62:
		var x=rng.randf_range(-23,23)
		var z=rng.randf_range(-23,23)
		if x>-16 and x<16 and z>-15 and z<16: continue
		var s=rng.randf_range(.7,1.5)
		model("tree",Vector3(x,0,z),Vector3(s,s,s)).rotation.y=rng.randf()*TAU
	for pos in [Vector3(-15,0,-5),Vector3(-14,0,3),Vector3(-6,0,8),Vector3(1,0,-12),Vector3(13,0,-10),Vector3(14,0,2),Vector3(3,0,15)]:
		model("bamboo",pos,Vector3(1.1,1.1,1.1))
	for i in 48:
		var pos=Vector3(rng.randf_range(-20,18),0,rng.randf_range(-18,20))
		if pos.distance_to(Vector3(-5,0,-3))<7 or pos.distance_to(Vector3(6,0,5))<7: continue
		model("rock",pos,Vector3.ONE*rng.randf_range(.3,1))
	# River at the east boundary, with small low-poly reeds.
	box(Vector3(5,.05,56),Vector3(20,-.045,0),Color("428c91"))
	for i in 50:
		var z=rng.randf_range(-24,24)
		box(Vector3(rng.randf_range(.3,1.3),.01,.05),Vector3(rng.randf_range(18,22),.005,z),Color("82bfc0"))
	for i in 60:
		var pos=Vector3(rng.randf_range(-17,16),.01,rng.randf_range(-16,18))
		if pos.distance_to(Vector3(-5,0,-3))<7: continue
		for j in 3:
			var grass=box(Vector3(.05,rng.randf_range(.2,.45),.05),pos+Vector3(j*.1,.1,0),Color("b9be83"))
			grass.rotation.z=rng.randf_range(-.3,.3)
	# Distant silhouette of the Jade Spine.
	for i in 14:
		var peak=CylinderMesh.new()
		peak.top_radius=.25
		peak.bottom_radius=rng.randf_range(5,9)
		peak.height=rng.randf_range(8,16)
		peak.radial_segments=5
		mesh_node(peak,Color("496a66"),Vector3(-36+i*6,peak.height/2-2,-29))

func world_label(text:String,pos:Vector3,color:Color,size:int=24,parent:Node=self)->Label3D:
	var label=Label3D.new()
	label.text=text
	label.position=pos
	label.font_size=size
	label.pixel_size=.012
	label.modulate=color
	label.outline_modulate=Color("192c2b")
	label.outline_size=5
	label.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test=true
	parent.add_child(label)
	return label

func ring(radius:float,color:Color,parent:Node)->MeshInstance3D:
	var m=TorusMesh.new()
	m.inner_radius=radius-.025
	m.outer_radius=radius+.025
	m.rings=32
	m.ring_segments=5
	return mesh_node(m,color,Vector3(0,.045,0),parent)

func update_state(state:Dictionary,local_id:int,dt:float):
	if state.is_empty(): return
	elapsed+=dt
	var desired:Dictionary={}
	for type in ["players","enemies"]:
		for id in state[type]:
			var data=state[type][id]
			var key=type+str(id)
			desired[key]=true
			if not actors.has(key):
				var root=Node3D.new()
				add_child(root)
				root.position=Vector3(data.pos.x,0,data.pos.y)
				var visual=model("hero" if type=="players" else "bandit",Vector3.ZERO,Vector3.ONE,root)
				if type=="enemies" and data.elite: visual.scale=Vector3.ONE*1.3
				var animation_players=visual.find_children("*","AnimationPlayer",true,false)
				var animator:AnimationPlayer=animation_players[0] if not animation_players.is_empty() else null
				if animator:
					for clip in animator.get_animation_list():
						if clip.to_lower().contains("idle") or clip.to_lower().contains("walk"):animator.get_animation(clip).loop_mode=Animation.LOOP_LINEAR
				var shadow=disk(.42,Vector3(0,.01,0),Color("445b4f"),root)
				var circle=ring(.57,Color("79e9c9") if type=="players" else Color("e18565"),root)
				var title=data.name if type=="players" else ("ASHEN WARDEN" if data.elite else "Ashen marauder")
				var label=world_label(title,Vector3(0,2.45 if not data.get("elite",false) else 2.9,0),Color("faf0d5") if type=="players" else Color("ffc4a1"),21,root)
				var health=box(Vector3(.9,.07,.045),Vector3(0,2.18,0),Color("db685e"),root)
				actors[key]={"root":root,"visual":visual,"shadow":shadow,"ring":circle,"label":label,"health":health,"prev":root.position,"animator":animator}
			var actor=actors[key]
			var pos=Vector3(data.pos.x,0,data.pos.y)
			var moving=actor.root.position.distance_to(pos)>.025
			actor.root.position=actor.root.position.lerp(pos,minf(1,dt*16))
			actor.visual.rotation.y=lerp_angle(actor.visual.rotation.y,data.facing,dt*14)
			actor.root.visible=data.dead<=0
			var jump:float=data.get("jump",0.0)
			actor.visual.position.y=sin(clampf(jump/.7,0,1)*PI)*2.0 if jump>0 else (absf(sin(elapsed*10))*0.07 if moving else sin(elapsed*2)*.015)
			actor.visual.rotation.z=sin(elapsed*10)*.035 if moving else 0
			if data.attack>0: actor.visual.rotation.y+=sin(data.attack/.28*PI)*.5
			
			if actor.animator:
				var clip="attack" if data.attack>0 else ("walk" if moving else "idle")
				if actor.animator.has_animation(clip) and actor.animator.current_animation!=clip:actor.animator.play(clip,.12)
			actor.health.scale.x=maxf(.01,float(data.hp)/data.max_hp)
			actor.health.rotation.y=PI/4
			actor.ring.visible=(type=="players" and id==local_id) or (type=="enemies" and id==selected)
			actor.health.visible=type=="enemies" and data.hp<data.max_hp
			if type=="players" and id==local_id:
				follow=follow.lerp(pos,dt*5)
				camera.position=follow+Vector3(17,21,17)
				camera.look_at(follow)
	for key in actors.keys():
		if not desired.has(key):
			actors[key].root.queue_free()
			actors.erase(key)
	for id in state.drops:
		var d=state.drops[id]
		if not loot_nodes.has(id):
			var root=Node3D.new()
			add_child(root)
			root.position=Vector3(d.pos.x,.3,d.pos.y)
			var gem=BoxMesh.new()
			gem.size=Vector3(.25,.25,.25)
			var loot=mesh_node(gem,Color("ffd986"),Vector3.ZERO,root)
			loot.material_override=mat(Color("ffd27b"),.8)
			loot.rotation_degrees=Vector3(30,45,30)
			ring(.32,Color("ffd993"),root)
			loot_nodes[id]=root
		loot_nodes[id].rotation.y+=dt
		loot_nodes[id].position.y=.35+sin(elapsed*3+id)*.12
	for id in loot_nodes.keys():
		if not state.drops.has(id):
			loot_nodes[id].queue_free()
			loot_nodes.erase(id)

func screen_to_ground(point:Vector2)->Vector2:
	var origin=camera.project_ray_origin(point)
	var dir=camera.project_ray_normal(point)
	var hit=Plane(Vector3.UP,0).intersects_ray(origin,dir)
	return Vector2(hit.x,hit.z) if hit!=null else Vector2.ZERO

func effect(event:Dictionary):
	var pos=Vector3(event.pos.x,0,event.pos.y)
	if event.type=="skill":
		var root=Node3D.new()
		add_child(root)
		root.position=pos+Vector3(0,.7,0)
		var color=Color("a6f1d7")
		if event.kind==6:
			var strike=box(Vector3(.25,.10,7),Vector3(0,0,3.5),color,root)
			strike.material_override=mat(color,1.2)
			root.rotation.y=atan2(event.dir.x,event.dir.y)
		else:
			var slash=ring(3.2 if event.kind==2 else 1.55,color,root)
			slash.material_override=mat(color,1.1)
			root.rotation.z=.2
		var tween=create_tween()
		tween.tween_property(root,"scale",Vector3(1.25,.05,1.25),.25)
		tween.tween_callback(root.queue_free)
	else:
		var label=world_label(event.get("text",""),pos+Vector3(0,2.3,0),Color("ff9278") if event.type=="hurt" else Color("ffe5a1"),32)
		var tween=create_tween().set_parallel(true)
		tween.tween_property(label,"position:y",3.7,.8).as_relative()
		tween.tween_property(label,"modulate:a",0.0,.8)
		tween.chain().tween_callback(label.queue_free)
