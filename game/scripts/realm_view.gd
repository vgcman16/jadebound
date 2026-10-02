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
var detailed_courtyard:bool=false

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
	env.ambient_light_color=Color("a7bbcd")
	env.ambient_light_energy=0.38
	env.sky=neutral_reflection_sky()
	env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.fog_enabled=true
	env.fog_light_color=Color("6b8e92")
	env.fog_density=0.0035
	environment.environment=env
	add_child(environment)
	var sun=DirectionalLight3D.new()
	sun.rotation_degrees=Vector3(-38,-36,0)
	sun.light_color=Color("fff0da")
	sun.light_energy=0.82
	sun.shadow_enabled=true
	sun.shadow_opacity=.65
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
	detailed_courtyard=ResourceLoader.exists("res://assets/models/courtyard_detail.glb")
	# Continuous earth/grass variation; no checkerboard or perfect yellow plaza.
	var ground_mesh=PlaneMesh.new()
	ground_mesh.size=Vector2(60,60)
	var ground=mesh_node(ground_mesh,Color.WHITE,Vector3(0,-.075,0))
	var shader=Shader.new()
	shader.code="""shader_type spatial;
render_mode diffuse_burley;
uniform sampler2D meadow_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D earth_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D earth_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D earth_roughness : filter_linear_mipmap_anisotropic, repeat_enable;
uniform bool use_surface_maps = false;
varying vec3 world_pos;
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123); }
float noise(vec2 p) { vec2 i=floor(p); vec2 f=fract(p); vec2 u=f*f*(3.0-2.0*f); return mix(mix(hash(i),hash(i+vec2(1,0)),u.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x),u.y); }
void vertex() { world_pos=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
 vec2 p=world_pos.xz; float broad=noise(p*.31); float medium=noise(p*1.4); float fine=noise(p*23.0);
 vec3 grass=mix(vec3(.058,.086,.035),vec3(.15,.185,.072),broad);
 if(use_surface_maps){vec3 a=texture(meadow_albedo,p*.31).rgb;vec3 b=texture(meadow_albedo,vec2(-p.y,p.x)*.21+vec2(.37,.61)).rgb;grass=mix(a,b,.28+medium*.25);grass=mix(grass,vec3(dot(grass,vec3(.299,.587,.114))),.16)*(.34+broad*.10);}
 grass+=vec3(.016,.019,.007)*(fine-.5);
 float lane=abs(p.y-(1.35+p.x*.42));
 float trail=1.0-smoothstep(.55,1.75+medium*.9,lane);
 float courtyard=1.0-smoothstep(-.05,.80,max(abs(p.x+4.3)-3.8,abs(p.y+1.3)-4.65)+medium*.30);
 float soil_weight=max(courtyard,trail*(.73+medium*.27));
 vec3 earth=use_surface_maps?texture(earth_albedo,p*.31).rgb:vec3(.15,.125,.08);
 earth=mix(earth*.78,earth*1.18,medium);
 ALBEDO=mix(grass,earth,soil_weight);
 ROUGHNESS=use_surface_maps?texture(earth_roughness,p*.31).r:.94;
 if(use_surface_maps){NORMAL_MAP=texture(earth_normal,p*.31).rgb;NORMAL_MAP_DEPTH=.35*soil_weight;}
}
"""
	var ground_mat=ShaderMaterial.new()
	ground_mat.shader=shader
	if detailed_courtyard:
		for channel in ["albedo","normal","roughness"]:ground_mat.set_shader_parameter("earth_"+channel,load("res://assets/textures/courtyard/jb_courtyard_earth_"+channel+".png"))
		ground_mat.set_shader_parameter("meadow_albedo",load("res://assets/textures/courtyard/jb_meadow_albedo.png"))
		ground_mat.set_shader_parameter("use_surface_maps",true)
	ground.material_override=ground_mat
	if detailed_courtyard:
		var bed_mesh=PlaneMesh.new()
		bed_mesh.size=Vector2(8.5,8.9)
		var bed=mesh_node(bed_mesh,Color.WHITE,Vector3(-4.2,-.052,-1.05))
		bed.material_override=ground_mat
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
	if detailed_courtyard:
		model("courtyard_detail",Vector3.ZERO)
	else:batch_boxes(stones)
	model("house",Vector3(-10,0,-7))
	if not detailed_courtyard:model("house",Vector3(-10,0,1),Vector3(.85,.85,.85))
	var house=model("house",Vector3(-3,0,-11))
	house.rotation.y=PI/2
	if not detailed_courtyard:
		model("shrine",Vector3(1,0,-8))
		model("gate",Vector3(1,0,-7),Vector3(.85,.85,.85)).rotation.y=-.3
	model("shrine",Vector3(-13,0,9),Vector3(1.1,1.1,1.1))
	if detailed_courtyard and ResourceLoader.exists("res://assets/models/hero_modular.glb"):
		var keeper=model("hero_modular",Vector3(JadeWorld.ELDER.x,0,JadeWorld.ELDER.y),Vector3.ONE*1.15)
		var appearance={"visual":keeper,"gear_signature":""}
		apply_equipment(appearance,{"gear":Equipment.DEFAULT_GEAR,"dead":0})
		for part in keeper.find_children("*","MeshInstance3D",true,false):
			if String(part.name).begins_with("Weapon_"):part.visible=false
			for i in part.mesh.get_surface_count():
				var original=part.mesh.surface_get_material(i)
				if original is StandardMaterial3D and original.resource_name.to_lower().contains("cloth"):
					var dyed=original.duplicate()
					dyed.albedo_color=Color("93a78f")
					part.set_surface_override_material(i,dyed)
		var animators=keeper.find_children("*","AnimationPlayer",true,false)
		if not animators.is_empty():
			animators[0].get_animation("idle").loop_mode=Animation.LOOP_LINEAR
			animators[0].play("idle")
	else:model("elder",Vector3(JadeWorld.ELDER.x,0,JadeWorld.ELDER.y))
	world_label("KEEPER SURI",Vector3(-5,2.5,-4),Color("d5d4b3"),18)
	world_label("◆",Vector3(-5,3.2,-4),Color("cfb679"),27)
	model("tree",Vector3(-9,0,3.4) if detailed_courtyard else Vector3(-9,0,7),Vector3.ONE*(1.0 if detailed_courtyard else 1.15))
	model("tree",Vector3(5,0,-10),Vector3(.85,.85,.85))
	# Lanterns mark the settlement and adventure boundary.
	for pos in [Vector3(-3,0,-1),Vector3(-7,0,-1),Vector3(2,0,0),Vector3(6,0,3),Vector3(-5,0,-8)]:
		model("lantern",pos)
		var light=OmniLight3D.new()
		light.position=pos+Vector3(0,1.5,0)
		light.light_color=Color("ffc87c")
		light.light_energy=.23
		light.omni_range=2.6
		add_child(light)
	# Tree clusters frame the play area, leaving the central field readable.
	for i in (18 if detailed_courtyard else 62):
		var x=rng.randf_range(-23,23)
		var z=rng.randf_range(-23,23)
		if x>-16 and x<16 and z>-15 and z<16: continue
		var s=rng.randf_range(.7,1.5)
		model("tree",Vector3(x,0,z),Vector3(s,s,s)).rotation.y=rng.randf()*TAU
	if not detailed_courtyard:
		for pos in [Vector3(-15,0,-5),Vector3(-14,0,3),Vector3(-6,0,8),Vector3(1,0,-12),Vector3(13,0,-10),Vector3(14,0,2),Vector3(3,0,15)]:
			model("bamboo",pos,Vector3(1.1,1.1,1.1))
	for i in (14 if detailed_courtyard else 48):
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
	m.inner_radius=radius-.013
	m.outer_radius=radius+.013
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
				var circle=ring(.57,Color("5d8272") if type=="players" else Color("e18565"),root)
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
				var sampled_clip=animation_for(actor,data,force_pose)
				if actor.animator.has_animation(sampled_clip):
					actor.animator.play(sampled_clip)
					actor.animator.seek(actor.animator.get_animation(sampled_clip).length*pose_fraction,true)
					actor.animator.advance(0)
					actor.animator.pause()
				actor.visual.position.y=(1.65 if pose_fraction<.7 else .1) if force_pose=="jump" else 0.0
			elif actor.animator:
				var clip="jump" if jump>0 and actor.animator.has_animation("jump") else ("attack" if data.attack>0 else (("run" if actor.animator.has_animation("run") else "walk") if moving else "idle"))
				if not actor.animator.has_animation(clip) and clip=="walk" and actor.animator.has_animation("run"):clip="run"
				clip=animation_for(actor,data,clip)
				if actor.animator.has_animation(clip):
					var is_attack=clip.begins_with("attack")
					var starts_attack=is_attack and not actor.attack_was
					if starts_attack:
						actor.animator.speed_scale=actor.animator.get_animation(clip).length/maxf(.1,data.attack)
						actor.animator.play(clip,.04)
					elif not is_attack and actor.animator.current_animation!=clip:
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
	if is_instance_valid(actor.get("quality_fx")):
		actor.quality_fx.visible=false
		actor.quality_fx.queue_free()
		actor.quality_fx=null
	var visible_names:Array=[]
	var slot_meshes:Dictionary={}
	for slot in Equipment.SLOTS:
		var mesh=Equipment.item(player,slot).get("mesh","")
		if not mesh.is_empty():
			visible_names.append(mesh)
			slot_meshes[slot]=mesh
	# The prototype topknot is also the base hairstyle when no helmet is equipped.
	if player.get("gear",{}).get("head","").is_empty():visible_names.append("Head_Topknot")
	var weapon=Equipment.item(player,"weapon")
	if weapon.get("effect","")=="jade_edge" and player.dead<=0:
		var anchor=actor.visual.find_child("Saber_FX",true,false)
		if anchor:actor.quality_fx=weapon_glints(anchor)
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
				if original is StandardMaterial3D and (original.resource_name.to_lower().contains("blade") and original.resource_name.to_lower().contains("edge")):
					var glowing=original.duplicate()
					glowing.emission_enabled=true
					glowing.emission=Color(.16,.60,.38)
					glowing.emission_energy_multiplier=1.8
					var gradient=Gradient.new()
					gradient.offsets=PackedFloat32Array([0,.83,.96,1])
					gradient.colors=PackedColorArray([Color.BLACK,Color.BLACK,Color.WHITE,Color.WHITE])
					var edge_mask=GradientTexture2D.new()
					edge_mask.gradient=gradient
					edge_mask.width=128
					edge_mask.height=8
					glowing.emission_texture=edge_mask
					glowing.emission_operator=BaseMaterial3D.EMISSION_OP_MULTIPLY
					node.set_surface_override_material(surface,glowing)

	JadeAppearanceCoverage.apply(actor.visual,slot_meshes)

func animation_for(actor:Dictionary,player:Dictionary,requested:String)->String:
	if requested=="attack" and Equipment.item(player,"weapon").get("mesh","")=="Weapon_Glaive" and actor.animator.has_animation("attack_glaive"):
		return "attack_glaive"
	return requested

func pick_context(point:Vector2,state:Dictionary)->Dictionary:
	var candidates:Array=[]
	for id in state.get("enemies",{}):
		var enemy=state.enemies[id]
		if enemy.dead<=0:candidates.append({"type":"enemy","id":id,"pos":enemy.pos,"height":2.6})
	candidates.append({"type":"npc","id":0,"pos":JadeWorld.ELDER,"height":2.5})
	for id in state.get("drops",{}):candidates.append({"type":"loot","id":id,"pos":state.drops[id].pos,"height":.65})
	var best:Dictionary={}
	var nearest=INF
	for candidate in candidates:
		var base=Vector3(candidate.pos.x,0,candidate.pos.y)
		var feet=camera.unproject_position(base)
		var head=camera.unproject_position(base+Vector3.UP*candidate.height)
		var rect=Rect2(Vector2(minf(feet.x,head.x)-17,minf(feet.y,head.y)-8),Vector2(absf(feet.x-head.x)+34,absf(feet.y-head.y)+16))
		var distance=point.distance_to((feet+head)*.5)
		if rect.has_point(point) and distance<nearest:
			best=candidate
			nearest=distance
	return best

func weapon_glints(anchor:Node3D)->CPUParticles3D:
	var sparks=CPUParticles3D.new()
	sparks.name="EquippedQualityGlints"
	sparks.amount=6
	sparks.lifetime=.5
	sparks.local_coords=true
	sparks.emission_shape=CPUParticles3D.EMISSION_SHAPE_POINTS
	# Rest-space points along the original curved saber, relative to its hand marker.
	sparks.emission_points=PackedVector3Array([Vector3(.11,.28,0),Vector3(.21,.51,0),Vector3(.36,.72,0)])
	sparks.direction=Vector3.UP
	sparks.spread=25
	sparks.initial_velocity_min=.05
	sparks.initial_velocity_max=.16
	sparks.gravity=Vector3(0,.08,0)
	sparks.scale_amount_min=.65
	sparks.scale_amount_max=1.0
	sparks.use_fixed_seed=true
	sparks.seed=41
	var mesh=SphereMesh.new()
	mesh.radius=.012
	mesh.height=.038
	mesh.radial_segments=6
	mesh.rings=3
	sparks.mesh=mesh
	var material=StandardMaterial3D.new()
	material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color=Color("befde0")
	material.emission_enabled=true
	material.emission=Color("7cdbab")
	material.emission_energy_multiplier=1.5
	sparks.material_override=material
	anchor.add_child(sparks)
	return sparks

static func neutral_reflection_sky()->Sky:
	var sky=Sky.new()
	var sky_material=ProceduralSkyMaterial.new()
	sky_material.sky_top_color=Color("647480")
	sky_material.sky_horizon_color=Color("bcc3c7")
	sky_material.ground_bottom_color=Color("26302e")
	sky_material.ground_horizon_color=Color("737d7b")
	sky_material.sky_energy_multiplier=.65
	sky_material.ground_energy_multiplier=.45
	sky_material.sun_angle_max=0.0
	sky.sky_material=sky_material
	sky.radiance_size=Sky.RADIANCE_SIZE_128
	return sky
