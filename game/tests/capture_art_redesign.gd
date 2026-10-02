extends Node
## Effects-off original art study, rendered by the real game with a qualified QA profile.
var app
func _ready():
	await get_tree().create_timer(.4).timeout
	var directory=ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()+"/builds/art-redesign-review"
	DirAccess.make_dir_recursive_absolute(directory)
	for pair in [["armor","warden_lamellar"],["head","warden_helm"],["weapon","ironwind_glaive"]]:
		assert(app.net.model.equip(1,pair[0],pair[1]))
		await get_tree().create_timer(.3).timeout
	app.net.model.players[1].pos=Vector2(-4.6,-2.1)
	app.view.follow=Vector3(-4.6,0,-2.1)
	app.hud.notice="LIMITED ART STUDY · Warden and one courtyard patch · quality VFX off"
	app.view.force_pose="idle"
	app.view.pose_fraction=.3
	app.view.camera.size=7.8
	app.view.camera_offset=Vector3(6,11,16)
	await capture(directory,"warden-gameplay")
	app.view.camera.size=6.5
	app.view.camera_offset=Vector3(8,8,12)
	for entry in [["idle",.3,"warden-closeup"],["run",.25,"warden-run"],["attack",.58,"warden-contact"],["jump",.5,"warden-apex"],["jump",.9,"warden-landing"]]:
		app.view.force_pose=entry[0]
		app.view.pose_fraction=entry[1]
		await capture(directory,entry[2])
	app.view.force_pose="idle"
	app.view.pose_fraction=.3
	app.view.camera.size=7.8
	app.view.camera_offset=Vector3(6,11,16)
	app.hud.inventory=true
	await capture(directory,"warden-equipment-panel")
	print("JADE_ART_REDESIGN_CAPTURED 7 effects-off native frames")
	get_tree().quit()
func capture(directory:String,label:String):
	await get_tree().create_timer(.25).timeout
	await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(directory+"/"+label+".png")==OK)
	print("ART_FRAME ",label)
