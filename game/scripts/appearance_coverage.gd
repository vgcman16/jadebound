class_name JadeAppearanceCoverage
extends RefCounted
## Reversible covered-body visibility. Equipment state is resolved by the server/model.
## Never destroys body geometry; unknown/missing equipment meshes fail visibly open.
const REGIONS={"Body_Torso":"armor","Body_Arms":"armor","Body_UpperLegs":"armor","Body_Hands":"gloves","Body_LowerLegs":"boots","Body_Feet":"boots"}
const PERMANENT_PREFIXES=["Body_Underwear","Body_Eye","Body_Fingers","Body_Head"]
static func apply(model:Node,selected_meshes:Dictionary)->Dictionary:
	var covered={"armor":false,"head":false,"weapon":false,"boots":false,"gloves":false}
	var meshes=model.find_children("*","MeshInstance3D",true,false)
	# A stat item without an actual visible mesh must never make the body disappear.
	for slot in selected_meshes:
		var prefix=String(selected_meshes[slot])
		if prefix.is_empty():continue
		for mesh in meshes:
			if mesh.visible and (String(mesh.name)==prefix or String(mesh.name).begins_with(prefix+"_")):
				covered[slot]=true
	for mesh in meshes:
		var name_=String(mesh.name)
		if REGIONS.has(name_):mesh.visible=not covered[REGIONS[name_]]
		if name_.begins_with("Body_Hair"):mesh.visible=not covered.head
		for prefix in PERMANENT_PREFIXES:
			if name_.begins_with(prefix):mesh.visible=true
	return covered
