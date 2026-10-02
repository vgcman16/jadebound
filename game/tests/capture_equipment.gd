extends Node
## Automated, reproducible in-engine asset review. Not a claim of manual playtesting.
var app
var records:Array=[]
func _ready():
	await get_tree().create_timer(.6).timeout
	var directory=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()+"/builds/equipment-review"
	DirAccess.make_dir_recursive_absolute(directory)
	var sets={"wayfarer":{"armor":"wayfarer_coat","head":"topknot","weapon":"reed_saber"},"warden":{"armor":"warden_lamellar","head":"warden_helm","weapon":"ironwind_glaive"}}
	var poses=[{"label":"idle","clip":"idle","fraction":.3},{"label":"run-stride","clip":"run","fraction":.25},{"label":"jump-apex","clip":"jump","fraction":.5},{"label":"jump-landing","clip":"jump","fraction":.9},{"label":"attack-contact","clip":"attack","fraction":.58}]
	for set_name in sets:
		var gear:Dictionary=sets[set_name]
		for slot in gear:
			var p=app.net.model.players[1]
			if p.gear[slot]!=gear[slot]:
				if not app.net.model.equip(1,slot,gear[slot]):
					await get_tree().create_timer(.35).timeout
					assert(app.net.model.equip(1,slot,gear[slot]))
				await get_tree().create_timer(.35).timeout
		app.view.force_pose="idle"
		app.view.pose_fraction=.3
		app.view.camera.size=14.5
		app.view.camera_offset=Vector3(17,21,17)
		app.hud.notice="GEAR REVIEW · %s · gameplay scale"%set_name
		await capture(directory,"%s-gameplay-scale"%set_name)
		app.view.camera.size=7
		app.view.camera_offset=Vector3(8,8,12)
		for pose in poses:
			app.view.force_pose=pose.clip
			app.view.pose_fraction=pose.fraction
			app.hud.notice="GEAR POSE REVIEW · %s · %s"%[set_name,pose.label]
			await capture(directory,"%s-%s"%[set_name,pose.label])
		app.view.force_pose="idle"
		app.view.camera.size=14.5
		app.view.camera_offset=Vector3(17,21,17)
		app.hud.inventory=true
		app.hud.notice="LIVE EQUIPMENT PANEL · %s"%set_name
		await capture(directory,"%s-equipment-panel"%set_name)
		app.hud.inventory=false
	var file=FileAccess.open(directory+"/capture-records.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(records,"  "))
	print("JADE_EQUIPMENT_REVIEW_CAPTURED ",records.size()," ",directory)
	get_tree().quit()

func capture(directory:String,label:String):
	await get_tree().create_timer(.22).timeout
	await RenderingServer.frame_post_draw
	var path=directory+"/"+label+".png"
	var result=get_viewport().get_texture().get_image().save_png(path)
	var p=app.net.state.players[1]
	var visible:Array=[]
	var actor=app.view.actors.get("players1",{})
	if not actor.is_empty():
		for node in actor.visual.find_children("*","MeshInstance3D",true,false):
			if node.visible:visible.append(String(node.name))
	records.append({"file":path,"result":result,"gear":p.gear.duplicate(true),"stats":JadeEquipment.stats(p),"visible_meshes":visible,"pose":app.view.force_pose,"fraction":app.view.pose_fraction})
	print("GEAR_FRAME ",label," result=",result," visible=",visible)
