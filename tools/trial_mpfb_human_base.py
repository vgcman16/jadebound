"""Isolated MPFB 2.0.17 core-base experiment; never replaces runtime hero.
Requires the official extension installed in the project-local jadebound_local repo.
The generated base mesh/rig data derive from MakeHuman CC0 assets; addon code is GPL.
"""
import bpy, addon_utils, importlib, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'art/human-base-trial'; OUT.mkdir(parents=True,exist_ok=True)
assert not bpy.app.online_access, 'This trial must run with --offline-mode'
module=addon_utils.enable('bl_ext.jadebound_local.mpfb',default_set=True,persistent=False)
assert module is not None, 'MPFB activation failed'
HumanService=importlib.import_module('bl_ext.jadebound_local.mpfb.services.humanservice').HumanService
TargetService=importlib.import_module('bl_ext.jadebound_local.mpfb.services.targetservice').TargetService
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
macro=TargetService.get_default_macro_info_dict()
macro.update(gender=1.0,age=.43,muscle=.62,weight=.43,proportions=.62,height=.56)
macro['race']={'asian':.78,'caucasian':.15,'african':.07}
body=HumanService.create_human(macro_detail_dict=macro)
body.name='CC0_Human_Base_Editable'
rig=HumanService.add_builtin_rig(body,'game_engine')
rig.name='HumanBase_GameRig'
bpy.context.view_layer.update()
# Keep the original helper/shape-key authoring data; body mask hides helpers.
mat=bpy.data.materials.new('Neutral anatomy clay');mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.29,.25,.21,1);bs.inputs['Roughness'].default_value=.76
body.data.materials.clear();body.data.materials.append(mat)
for face in body.data.polygons:face.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mpfb_adult_base.blend'))
# Evaluate helper mask and shape keys into a separate render/export copy.
for mod in body.modifiers:
 if mod.type=='ARMATURE':mod.show_viewport=False;mod.show_render=False
bpy.context.view_layer.update()
eval_body=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
cleanmesh=bpy.data.meshes.new_from_object(eval_body,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
clean=bpy.data.objects.new('Body_Base_Trial',cleanmesh);bpy.context.collection.objects.link(clean)
clean.matrix_world=body.matrix_world.copy()
for group in body.vertex_groups:clean.vertex_groups.new(name=group.name)
clean.parent=rig
arm=clean.modifiers.new('CC0 game rig deformation','ARMATURE');arm.object=rig
body.hide_render=True;body.hide_set(True)
# Plain fitted shorts are only a modesty material for the anatomy proof, no costume claim.
short=bpy.data.materials.new('Anatomy study shorts');short.diffuse_color=(.04,.048,.045,1);short.use_nodes=True
short.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.04,.048,.045,1)
short.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9
clean.data.materials.append(short)
for face in clean.data.polygons:
 z=sum(clean.data.vertices[i].co.z for i in face.vertices)/len(face.vertices)
 if .69<z<1.01:face.material_index=len(clean.data.materials)-1
bpy.ops.object.select_all(action='DESELECT');clean.hide_set(False);clean.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=clean
bpy.ops.export_scene.gltf(filepath=str(OUT/'mpfb_adult_base.glb'),export_format='GLB',use_selection=True,export_animations=False,export_yup=True,export_apply=False)
record={'tool':'MPFB 2.0.17 official Blender extension','archive_sha256':'4f0a879d64a39bf646fbf5f53601ac678855da329d650617dca5737548239a87','offline':not bpy.app.online_access,'macro_settings':macro,'raw_vertices':len(body.data.vertices),'clean_vertices':len(clean.data.vertices),'clean_polygons':len(clean.data.polygons),'bones':[b.name for b in rig.data.bones],'bounds':list(clean.dimensions),'derived_data_license':'CC0; verified core base.obj header and official MakeHuman licensing','source':'https://extensions.blender.org/add-ons/mpfb/','status':'Unintegrated anatomy trial; no garment/animation quality claim'}
(OUT/'trial_receipt.json').write_text(json.dumps(record,indent=2))
# A finite neutral authoring render for body/face assessment, not gameplay.
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
scene.render.resolution_x=600;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world.color=(.16,.16,.16)
scene.view_settings.view_transform='AgX'
bpy.ops.object.camera_add(location=(3,-6,2.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.96))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.2;scene.camera=cam
for loc,power,size in [((3,-4,5),500,4),((-3,-1,3),300,3),((0,3,4),450,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,1))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));floor=bpy.context.object
m=bpy.data.materials.new('Studio neutral');m.diffuse_color=(.16,.16,.16,1);floor.data.materials.append(m)
scene.render.filepath=str(ROOT/'builds/human-base-trial/clay-base.png');bpy.ops.render.render(write_still=True)
print('HUMAN_BASE_TRIAL_OK',json.dumps(record))
