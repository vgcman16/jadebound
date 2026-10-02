class_name RealmView
extends Node3D
const Equipment=preload("res://scripts/equipment_data.gd")
var actors:Dictionary={}
var loot_nodes:Dictionary={}
var camera:Camera3D
var elapsed:float=0
var follow:Vector3=Vector3(-3,0,1)
var materials:Dictionary={}
var effect_nodes:Array=[]
var selected:int=-1
var force_pose:String=""
var pose_fraction:float=.3
var camera_offset:Vector3=Vector3(17,21,17)
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
	env.background_color=Color("172d37")
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color=Color("889faf")
	env.ambient_light_energy=0.48
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.fog_enabled=true
	env.fog_light_color=Color("6b8e92")
	env.fog_density=0.0035
	environment.environment=env
	add_child(environment)
	var sun=DirectionalLight3D.new()
	sun.rotation_degrees=Vector3(-38,-36,0)
	sun.light_color=Color("ffcf91")
	sun.light_energy=0.70
	sun.shadow_enabled=true
	sun.shadow_opacity=.72
	sun.directional_shadow_max_distance=70
	add_child(sun)
	camera=Camera3D.new()
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=14.5
	camera.far=160
	add_child(camera)
	camera.position=follow+camera_offset
	camera.look_at(follow)
	build_landscape()

func build_landscape():
	var rng=RandomNumberGenerator.new()
	rng.seed=38140
	# Continuous earth/grass variation; no checkerboard or perfect yellow plaza.
	var ground_mesh=PlaneMesh.new()
	ground_mesh.size=Vector2(60,60)
	var ground=mesh_node(ground_mesh,Color.WHITE,Vector3(0,-.075,0))
	var shader=Shader.new()
	shader.code="""shader_type spatial;
render_mode diffuse_burley;
varying vec3 world_pos;
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123); }
float noise(vec2 p) { vec2 i=floor(p); vec2 f=fract(p); vec2 u=f*f*(3.0-2.0*f); return mix(mix(hash(i),hash(i+vec2(1,0)),u.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x),u.y); }
void vertex() { world_pos=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
 vec2 p=world_pos.xz; float broad=noise(p*.28); float fine=noise(p*9.0);
 vec3 grass=mix(vec3(.105,.155,.098),vec3(.235,.29,.16),broad);
 grass+=vec3(.027,.024,.012)*(fine-.5);
 float trail=1.0-smoothstep(.75,1.8,abs(p.y-(-3.0+(p.x+5.0)*.63)));
 vec3 earth=mix(vec3(.20,.17,.115),vec3(.28,.25,.18),noise(p*.8));
 ALBEDO=mix(grass,earth,trail*.8); ROUGHNESS=.94;
}
"""
	var ground_mat=ShaderMaterial.new()
	ground_mat.shader=shader
	ground.material_override=ground_mat
	# Asymmetric fitted flagstones: three quiet stone colors, recessed seams.
	var stones:Array=[]
	for gx in range(-7,8):
		for gz in range(-6,7):
			var cx=-5+gx*.83+(0.415 if gz%2 else 0.0)
			var cz=-3+gz*.83
			if Vector2(cx+5,cz+3).length()>5.6 or (gx>3 and gz>2):continue
			if Vector2(cx+5,cz+3).length()>4.6 and rng.randf()<.14:continue
			stones.append([Vector3(.79,.10,.79),Vector3(cx,-.04,cz),Color("747969").darkened(rng.randf_range(0,.15))])
	# Embedded flagstones in a broad worn lane, with irregular gaps and margins.
	var tangent=Vector2(15,9.5).normalized()
	var normal=Vector2(-tangent.y,tangent.x)
	var lane_rotation=atan2(tangent.x,tangent.y)
	for i in range(22):
		var t=i/21.0
		var center=Vector2(lerpf(-1,14,t),lerpf(-.5,9,t)+sin(t*6)*.5)
		for col in [-1,0,1]:
			if rng.randf()<(0.30 if col!=0 else .08):continue
			var p=center+normal*(col*.63+rng.randf_range(-.12,.12))+tangent*rng.randf_range(-.16,.16)
			var size_=Vector3(rng.randf_range(.45,.64),.08,rng.randf_range(.54,.77))
			stones.append([size_,Vector3(p.x,-.05,p.y),Color("717665").darkened(rng.randf_range(0,.23)),lane_rotation+rng.randf_range(-.14,.14)])
	batch_boxes(stones)
	model("house",Vector3(-10,0,-7))
	model("house",Vector3(-10,0,1),Vector3(.85,.85,.85))
	var house=model("house",Vector3(-3,0,-11))
	house.rotation.y=PI/2
	model("shrine",Vector3(1,0,-8))
	model("gate",Vector3(1,0,-7),Vector3(.85,.85,.85)).rotation.y=-.3
	model("shrine",Vector3(-13,0,9),Vector3(1.1,1.1,1.1))
	model("elder",Vector3(JadeWorld.ELDER.x,0,JadeWorld.ELDER.y))
	world_label("KEEPER SURI",Vector3(-5,2.5,-4),Color("ffe5a3"),25)
	world_label("◆",Vector3(-5,3.2,-4),Color("ffd978"),44)
	model("tree",Vector3(-9,0,7),Vector3(1.15,1.15,1.15))
	model("tree",Vector3(5,0,-10),Vector3(.85,.85,.85))
	# Lanterns mark the settlement and adventure boundary.
	for pos in [Vector3(-3,0,-1),Vector3(-7,0,-1),Vector3(2,0,0),Vector3(6,0,3),Vector3(-5,0,-8)]:
		model("lantern",pos)
		var light=OmniLight3D.new()
		light.position=pos+Vector3(0,1.5,0)
		light.light_color=Color("ffc87c")
		light.light_energy=1.25
		light.omni_range=5.5
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
	box(Vector3(5,.05,56),Vector3(20,-.045,0),Color("234e5a"))
	for i in 50:
		var z=rng.randf_range(-24,24)
		box(Vector3(rng.randf_range(.3,1.3),.01,.05),Vector3(rng.randf_range(18,22),.005,z),Color("4e888d"))
	var plants:Array=[]
	for i in 60:
		var pos=Vector3(rng.randf_range(-17,16),.01,rng.randf_range(-16,18))
		if pos.distance_to(Vector3(-5,0,-3))<7:continue
		for j in 3:
			plants.append([Vector3(.035,rng.randf_range(.18,.38),.035),pos+Vector3(j*.08,.1,0),Color("778a4e")])
	batch_boxes(plants)
	# Distant silhouette of the Jade Spine.
	for i in 14:
		var peak=CylinderMesh.new()
		peak.top_radius=.25
		peak.bottom_radius=rng.randf_range(5,9)
		peak.height=rng.randf_range(8,16)
		peak.radial_segments=5
		mesh_node(peak,Color("2f4b53"),Vector3(-36+i*6,peak.height/2-2,-29))

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
				var asset="hero_modular" if type=="players" and ResourceLoader.exists("res://assets/models/hero_modular.glb") else ("hero" if type=="players" else "bandit")
				var visual=model(asset,Vector3.ZERO,Vector3.ONE*1.25,root)
				if type=="enemies" and data.elite: visual.scale=Vector3.ONE*1.3
				var animation_players=visual.find_children("*","AnimationPlayer",true,false)
				var animator:AnimationPlayer=animation_players[0] if not animation_players.is_empty() else null
				if animator:
					for clip in animator.get_animation_list():
						if clip.to_lower().contains("idle") or clip.to_lower().contains("walk") or clip.to_lower().contains("run"):animator.get_animation(clip).loop_mode=Animation.LOOP_LINEAR
				var shadow=soft_shadow(root)
				var circle=ring(.57,Color("79e9c9") if type=="players" else Color("e18565"),root)
				var title=data.name if type=="players" else ("ASHEN WARDEN" if data.elite else "Ashen marauder")
				var label=world_label(title,Vector3(0,2.9 if not data.get("elite",false) else 3.3,0),Color("faf0d5") if type=="players" else Color("ffc4a1"),21,root)
				var health=box(Vector3(.9,.07,.045),Vector3(0,2.65,0),Color("db685e"),root)
				actors[key]={"root":root,"visual":visual,"shadow":shadow,"ring":circle,"label":label,"health":health,"prev":root.position,"animator":animator,"gear_signature":"","modular":asset=="hero_modular","attack_was":false}
			var actor=actors[key]
			if type=="players" and actor.modular:apply_equipment(actor,data)
			var pos=Vector3(data.pos.x,0,data.pos.y)
			var moving=actor.root.position.distance_to(pos)>.025
			actor.root.position=actor.root.position.lerp(pos,minf(1,dt*16))
			actor.visual.rotation.y=lerp_angle(actor.visual.rotation.y,data.facing,dt*14)
			actor.root.visible=data.dead<=0
			var jump:float=data.get("jump",0.0)
			actor.visual.position.y=sin(clampf(jump/.7,0,1)*PI)*2.0 if jump>0 else (0.0 if actor.modular else (absf(sin(elapsed*10))*0.07 if moving else sin(elapsed*2)*.015))
			actor.visual.rotation.z=sin(elapsed*10)*.035 if moving and not actor.modular else 0
			if data.attack>0 and not actor.modular: actor.visual.rotation.y+=sin(data.attack/.28*PI)*.5
			
			if actor.animator and not force_pose.is_empty() and type=="players" and id==local_id:
				if actor.animator.has_animation(force_pose):
					actor.animator.play(force_pose)
					actor.animator.seek(actor.animator.get_animation(force_pose).length*pose_fraction,true)
					actor.animator.advance(0)
					actor.animator.pause()
				actor.visual.position.y=(1.65 if pose_fraction<.7 else .1) if force_pose=="jump" else 0.0
			elif actor.animator:
				var clip="jump" if jump>0 and actor.animator.has_animation("jump") else ("attack" if data.attack>0 else (("run" if actor.animator.has_animation("run") else "walk") if moving else "idle"))
				if not actor.animator.has_animation(clip) and clip=="walk" and actor.animator.has_animation("run"):clip="run"
				if actor.animator.has_animation(clip):
					var starts_attack=clip=="attack" and not actor.attack_was
					if starts_attack:
						actor.animator.speed_scale=actor.animator.get_animation(clip).length/maxf(.1,data.attack)
						actor.animator.play(clip,.04)
					elif clip!="attack" and actor.animator.current_animation!=clip:
						actor.animator.speed_scale=actor.animator.get_animation(clip).length/.7 if clip=="jump" else (1.25 if clip=="run" else 1.0)
						actor.animator.play(clip,.08)
				actor.attack_was=data.attack>0
			actor.health.scale.x=maxf(.01,float(data.hp)/data.max_hp)
			actor.health.rotation.y=PI/4
			actor.ring.visible=(type=="players" and id==local_id) or (type=="enemies" and id==selected)
			actor.health.visible=type=="enemies" and data.hp<data.max_hp
			actor.label.visible=(id!=local_id) if type=="players" else (id==selected or data.hp<data.max_hp)
			if type=="players" and id==local_id:
				follow=follow.lerp(pos,dt*5)
				var camera_focus=follow+Vector3(0,.9 if force_pose=="jump" else 0.0,0)
				camera.position=camera_focus+camera_offset
				camera.look_at(camera_focus)
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
		var color=Color(.58,.87,.74,.75)
		root.rotation.y=atan2(event.dir.x,event.dir.y)
		var trail:MeshInstance3D
		if event.kind==6:
			trail=blade_trail(7.0,.26,color,root)
		else:
			trail=crescent(3.0 if event.kind==2 else 1.65,4.6 if event.kind==2 else 2.5,color,root)
			root.rotation.z=.14
		var tween=create_tween().set_parallel(true)
		tween.tween_property(root,"scale",Vector3(1.15,1,1.15),.23)
		tween.tween_property(trail.material_override,"albedo_color:a",0.0,.23)
		tween.chain().tween_callback(root.queue_free)
	else:
		var label=world_label(event.get("text",""),pos+Vector3(0,2.3,0),Color("ff9278") if event.type=="hurt" else Color("ffe5a1"),32)
		var tween=create_tween().set_parallel(true)
		tween.tween_property(label,"position:y",3.7,.8).as_relative()
		tween.tween_property(label,"modulate:a",0.0,.8)
		tween.chain().tween_callback(label.queue_free)

func batch_boxes(items:Array):
	var node=MultiMeshInstance3D.new()
	var multi=MultiMesh.new()
	multi.transform_format=MultiMesh.TRANSFORM_3D
	multi.use_colors=true
	multi.mesh=BoxMesh.new()
	multi.instance_count=items.size()
	for i in items.size():
		var item=items[i]
		var basis=Basis(Vector3.UP,item[3] if item.size()>3 else 0.0).scaled(item[0])
		multi.set_instance_transform(i,Transform3D(basis,item[1]))
		multi.set_instance_color(i,item[2])
	var material=StandardMaterial3D.new()
	material.vertex_color_use_as_albedo=true
	material.vertex_color_is_srgb=true
	material.roughness=.94
	node.multimesh=multi
	node.material_override=material
	add_child(node)

func crescent(radius:float,angle:float,color:Color,parent:Node)->MeshInstance3D:
	var surface=SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in 24:
		var u=float(i)/24
		var v=float(i+1)/24
		var a=-angle/2+u*angle
		var b=-angle/2+v*angle
		var wa=sin(u*PI)*.23
		var wb=sin(v*PI)*.23
		var p1=Vector3(sin(a)*radius,0,cos(a)*radius)
		var p2=Vector3(sin(a)*(radius-wa),0,cos(a)*(radius-wa))
		var p3=Vector3(sin(b)*radius,0,cos(b)*radius)
		var p4=Vector3(sin(b)*(radius-wb),0,cos(b)*(radius-wb))
		for point in [p1,p2,p3,p3,p2,p4]:surface.add_vertex(point)
	surface.generate_normals()
	var node=mesh_node(surface.commit(),color,Vector3.ZERO,parent)
	node.material_override=effect_material(color)
	return node

func blade_trail(length_:float,width:float,color:Color,parent:Node)->MeshInstance3D:
	var surface=SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for point in [Vector3(-width,0,.2),Vector3(width,0,.2),Vector3(0,0,length_)]:surface.add_vertex(point)
	surface.generate_normals()
	var node=mesh_node(surface.commit(),color,Vector3.ZERO,parent)
	node.material_override=effect_material(color)
	return node

func effect_material(color:Color)->StandardMaterial3D:
	var material=StandardMaterial3D.new()
	material.albedo_color=color
	material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode=BaseMaterial3D.CULL_DISABLED
	return material

func soft_shadow(parent:Node)->MeshInstance3D:
	var mesh=PlaneMesh.new()
	mesh.size=Vector2(1.3,1.3)
	var node=mesh_node(mesh,Color.BLACK,Vector3(0,.045,0),parent)
	var shader=Shader.new()
	shader.code="""shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
void fragment() { float d=length(UV-vec2(.5))*2.0; ALBEDO=vec3(.015,.022,.02); ALPHA=(1.0-smoothstep(.1,1.0,d))*.30; }
"""
	var material=ShaderMaterial.new()
	material.shader=shader
	node.material_override=material
	return node

func apply_equipment(actor:Dictionary,player:Dictionary):
	var signature=JSON.stringify(player.get("gear",{}))+str(player.dead>0)
	if signature==actor.gear_signature:return
	actor.gear_signature=signature
	var visible_names:Array=[]
	for slot in Equipment.SLOTS:visible_names.append(Equipment.item(player,slot).get("mesh",""))
	var weapon=Equipment.item(player,"weapon")
	for node in actor.visual.find_children("*","MeshInstance3D",true,false):
		var name_=String(node.name)
		var is_gear=name_.begins_with("Gear_") or name_.begins_with("Head_") or name_.begins_with("Weapon_")
		if is_gear:
			node.visible=false
			for prefix in visible_names:
				if name_==prefix or name_.begins_with(prefix+"_"):node.visible=true
		# Reset the old equipped item's overrides, then apply only the selected blade layer.
		for surface in node.mesh.get_surface_count():
			node.set_surface_override_material(surface,null)
			if node.visible and name_.begins_with(weapon.get("mesh","NONE")) and weapon.get("effect","")=="jade_edge" and player.dead<=0:
				var original=node.mesh.surface_get_material(surface)
				if original is StandardMaterial3D and (original.resource_name.to_lower().contains("steel") or original.resource_name.to_lower().contains("blade")):
					var glowing=original.duplicate()
					glowing.emission_enabled=true
					glowing.emission=Color(.16,.60,.38)
					glowing.emission_energy_multiplier=1.8
					node.set_surface_override_material(surface,glowing)
