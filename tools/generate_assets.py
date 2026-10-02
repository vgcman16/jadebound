#!/usr/bin/env python3
"""Original Jadebound art kit. Run with Blender 4.3+, never regular Python.

blender --background --threads 2 --python tools/generate_assets.py -- --output .
No downloads, textures, simulation, rendering, or optional add-ons are needed.
The library stays fully editable; exports use evaluated bevel modifiers.
"""
import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

RNG = random.Random(72419)
MATS = {}
ASSETS = []
COLLECTION = None
ROOT = None


def material(name, color, metallic=0.0, roughness=0.7, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*color, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission
    MATS[name] = mat
    return mat


def setup_materials():
    material('Jade deep', (0.025, 0.22, 0.20))
    material('Jade bright', (0.08, 0.62, 0.45), 0.18, 0.36)
    material('Jade pale', (0.29, 0.84, 0.64), 0.2, 0.32)
    material('Ink teal', (0.018, 0.073, 0.085))
    material('Ivory silk', (0.88, 0.81, 0.59))
    material('Parchment', (0.66, 0.59, 0.40))
    material('Warm plaster', (0.82, 0.70, 0.46))
    material('Orange silk', (0.93, 0.26, 0.067))
    material('Lantern paper', (1.0, 0.44, 0.12), roughness=0.5, emission=1.25)
    material('Old gold', (0.63, 0.39, 0.10), 0.65, 0.38)
    material('Gold edge', (0.93, 0.65, 0.22), 0.55, 0.32)
    material('Timber', (0.20, 0.083, 0.042))
    material('Timber edge', (0.35, 0.16, 0.061))
    material('Ash stone', (0.22, 0.30, 0.29))
    material('Stone light', (0.43, 0.49, 0.40))
    material('Corruption', (0.39, 0.036, 0.08))
    material('Crimson edge', (0.75, 0.095, 0.14))
    material('Pink blossom', (0.89, 0.32, 0.32))
    material('Dark leather', (0.082, 0.050, 0.035))
    material('Skin warm', (0.61, 0.37, 0.23))
    material('Hair ink', (0.022, 0.025, 0.027))
    material('Steel', (0.44, 0.57, 0.57), 0.8, 0.28)


def own(obj, name, mat=None, parent=None):
    obj.name = name
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    COLLECTION.objects.link(obj)
    obj.parent = parent if parent is not None else ROOT
    if mat:
        obj.data.materials.append(MATS[mat])
    return obj


def empty(name, loc=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    COLLECTION.objects.link(obj)
    obj.parent = parent if parent is not None else ROOT
    obj.location = loc
    obj.empty_display_size = 0.13
    return obj


def bevel(obj, amount=0.025):
    if amount:
        mod = obj.modifiers.new('Hand cut softened edges', 'BEVEL')
        mod.width = amount
        mod.segments = 1
        mod.affect = 'EDGES'
    return obj


def box(name, loc, size, mat, parent=None, edge=0.025, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = own(bpy.context.object, name, mat, parent)
    # Bake dimensions directly into the vertices to keep clean animation scale.
    for v in obj.data.vertices:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    obj.location = loc
    if rot:
        obj.rotation_euler = rot
    return bevel(obj, edge)


def cone(name, loc, r1, r2, depth, mat, parent=None, vertices=8, rot=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1,
                                    radius2=r2, depth=depth)
    obj = own(bpy.context.object, name, mat, parent)
    obj.location = loc
    if rot:
        obj.rotation_euler = rot
    return obj


def orb(name, loc, scale, mat, parent=None, subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1)
    obj = own(bpy.context.object, name, mat, parent)
    for v in obj.data.vertices:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    obj.location = loc
    return obj


def beam(name, a, b, radius, mat, parent=None, vertices=6, end_radius=None):
    a, b = Vector(a), Vector(b)
    obj = cone(name, (a+b)*0.5, radius,
               radius if end_radius is None else end_radius,
               (b-a).length, mat, parent, vertices)
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return obj


def mesh(name, vertices, faces, mat, parent=None, edge=0):
    data = bpy.data.meshes.new(name + ' mesh')
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    own(obj, name, mat, parent)
    return bevel(obj, edge)


def frustum(name, zbottom, ztop, bottom, top, mat, parent=None, offset=(0, 0)):
    bx, by = bottom[0]*0.5, bottom[1]*0.5
    tx, ty = top[0]*0.5, top[1]*0.5
    x, y = offset
    verts = [(x-bx,y-by,zbottom), (x+bx,y-by,zbottom),
             (x+bx,y+by,zbottom), (x-bx,y+by,zbottom),
             (x-tx,y-ty,ztop), (x+tx,y-ty,ztop),
             (x+tx,y+ty,ztop), (x-tx,y+ty,ztop)]
    return mesh(name, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                              (1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, parent, 0.018)


def begin_asset(name):
    global COLLECTION, ROOT
    COLLECTION = bpy.data.collections.new(name.upper() + ' • original Jadebound asset')
    bpy.context.scene.collection.children.link(COLLECTION)
    ROOT = None
    ROOT = empty(name)
    ROOT['asset_name'] = name
    ROOT['authoring_axes'] = 'Blender Z up; front -Y; metres; ground origin'
    ROOT['license'] = 'Original project artwork; no third party assets'
    ASSETS.append((name, COLLECTION, ROOT))
    return ROOT


def make_lantern(parent, x=0, y=0, z=0, scale=1):
    s = scale
    cone('Amber lantern paper', (x,y,z+0.28*s), .18*s, .18*s,
         .38*s, 'Lantern paper', parent, 8)
    for dz in (.08,.48):
        cone('Lantern octagonal brass cap', (x,y,z+dz*s), .21*s,.18*s,
             .065*s,'Old gold',parent,8)
    for angle in range(0,360,90):
        a=math.radians(angle)
        beam('Lantern ribs', (x+.177*s*math.cos(a),y+.177*s*math.sin(a),z+.11*s),
             (x+.177*s*math.cos(a),y+.177*s*math.sin(a),z+.46*s),.012*s,'Timber',parent)
    beam('Lantern hanging cord',(x,y,z+.5*s),(x,y,z+.67*s),.016*s,'Timber',parent)
    cone('Lantern silk tassel',(x,y,z+.015*s),.018*s,.035*s,.11*s,'Orange silk',parent)


def sword(parent, corrupted=False):
    mat = 'Steel' if corrupted else 'Jade pale'
    # Weapon rises above the hand; thin diamond-section blade with original jade inlay.
    box('Sword leather grip', (0,0,-.32),(.055,.055,.20),'Dark leather',parent, .007)
    box('Sword gold crossguard', (0,0,-.20),(.29,.075,.06),'Old gold',parent,.012)
    mesh('Jadeblade tapered steel', [(-.065,0,-.18),(.065,0,-.18),(0,-.032,-.18),
          (0,.032,-.18),(-.048,0,.39),(.048,0,.39),(0,-.024,.39),
          (0,.024,.39),(0,0,.58)],
         [(0,2,6,4),(2,1,5,6),(1,3,7,5),(3,0,4,7),
          (4,6,8),(6,5,8),(5,7,8),(7,4,8),(0,3,1,2)],mat,parent)
    box('Jadeblade central enamel',(0,-.034,.13),(.022,.006,.46),
        'Crimson edge' if corrupted else 'Jade bright',parent,.002)
    orb('Sword pommel',(0,0,-.44),(.055,.055,.05),'Gold edge',parent)


def character(name):
    begin_asset(name)
    elder, enemy = name=='elder', name=='bandit'
    primary = 'Corruption' if enemy else ('Ivory silk' if elder else 'Jade deep')
    secondary = 'Crimson edge' if enemy else ('Old gold' if elder else 'Ivory silk')
    body = empty(name+'_torso',(0,0,.97))
    frustum('Layered robe tunic',-.13,.42,(.47,.31),(.56,.30),primary,body)
    frustum('Layered flared robe skirt',-.56,-.14,(.65,.40),(.43,.29),primary,body)
    # Panels and sash make the silhouette legible at a small isometric scale.
    box('Ivory inner robe panel',(0,-.17,.15),(.23,.035,.48),secondary,body,.009)
    box('Crossed left lapel',(-.075,-.205,.26),(.055,.025,.33),primary,body,.006, (0,-.34,0))
    box('Crossed right lapel',(.072,-.209,.27),(.045,.025,.31),'Gold edge',body,.005,(0,.34,0))
    box('Wide dark waist sash',(0,-.01,-.05),(.49,.36,.115),'Dark leather',body,.012)
    box('Jade belt clasp',(0,-.204,-.052),(.12,.035,.09),
        'Crimson edge' if enemy else 'Jade bright',body,.012)
    for x in (-.14,.14):
        box('Robe split lower facing',(x,-.20,-.33),(.16,.035,.40),secondary,body,.008,(0,x*.3,0))
    cone('Neck',(0,0,.48),.073,.075,.16,'Skin warm',body)
    orb('Faceted head',(0,-.008,.64),(.165,.145,.20),'Skin warm',body,2)
    orb('Hair cap',(0,.033,.72),(.17,.14,.15),'Hair ink',body,1)
    for x in (-.065,.065):
        box('Eyes',(x,-.142,.66),(.036,.019,.017),
            'Crimson edge' if enemy else 'Hair ink',body,.002)
    box('Nose',(0,-.153,.607),(.035,.035,.05),'Skin warm',body,.005)
    if elder:
        cone('Elder ivory beard',(0,-.128,.47),.012,.10,.27,'Ivory silk',body,6)
        cone('Elder topknot',(0,.025,.94),.078,.047,.20,'Ivory silk',body,8)
        cone('Elder topknot gold binding',(0,.025,.9),.083,.083,.06,'Old gold',body)
        box('Elder head ribbon',(0,-.04,.78),(.34,.25,.046),'Old gold',body,.005)
    elif enemy:
        box('Bandit face mask',(0,-.146,.56),(.26,.05,.115),'Ink teal',body,.018)
        cone('Bandit wrapped crown',(0,.015,.8),.185,.135,.14,'Corruption',body,8)
        for x in (-.15,.15):
            beam('Ash crown spikes',(x,.02,.80),(x*1.3,.04,.99),.058,'Ash stone',body,4,0)
    else:
        cone('Travel hat wide brim',(0,0,.85),.39,.30,.055,'Parchment',body,12)
        cone('Travel hat woven crown',(0,0,.97),.32,.055,.22,'Ivory silk',body,12)
        cone('Travel hat teal crown tip',(0,0,1.085),.066,.04,.055,'Jade deep',body,8)
        for a in (0, math.pi/2, math.pi, math.pi*1.5):
            beam('Hat gold stitch',(math.cos(a)*.035,math.sin(a)*.035,1.088),
                 (math.cos(a)*.35,math.sin(a)*.35,.868),.009,'Old gold',body,4)
        box('Orange neck scarf',(0,-.01,.43),(.29,.30,.10),'Orange silk',body,.01)
        box('Scarf trailing strip',(-.20,.17,.26),(.11,.06,.42),
            'Orange silk',body,.008,(0,-.38,.20))
        box('Scarf gold stitch',(-.285,.174,.09),(.10,.068,.035),'Gold edge',body,.004)
    limbs={}
    for sign, side in ((-1,'L'),(1,'R')):
        arm = empty(name+'_arm_'+side,(sign*.32,0,.30),body)
        cone('Structured shoulder sleeve',(sign*.02,0,-.13),.105,.15,.29,primary,arm,6,
             (0,sign*-.20,0))
        beam('Forearm bracer',(sign*.05,0,-.24),(sign*.06,-.045,-.43),.085,
             'Ash stone' if enemy else 'Timber',arm)
        cone('Gold wrist band',(sign*.06,-.045,-.42),.09,.09,.06,'Old gold',arm,8)
        orb('Hand',(sign*.065,-.04,-.485),(.073,.070,.082),'Skin warm',arm)
        leg = empty(name+'_leg_'+side,(sign*.145,0,.72))
        beam('Trouser leg',(0,0,-.02),(0,0,-.44),.092,'Ink teal',leg)
        box('Leather travel boot',(0,-.07,-.60),(.17,.29,.18),'Dark leather',leg,.025)
        box('Boot warm toe cap',(0,-.17,-.57),(.16,.10,.09),'Timber edge',leg,.015)
        for zz in (-.33,-.39,-.45):
            box('Ivory shin wraps',(0,-.078,zz),(.14,.042,.029),secondary,leg,.004)
        limbs['arm_'+side]=arm
        limbs['leg_'+side]=leg
    if elder:
        staff = empty('Elder ceremonial staff',(-.03,-.06,-.47),limbs['arm_R'])
        beam('Old cedar walking staff',(0,0,-.62),(0,0,.95),.028,'Timber',staff)
        cone('Staff jade crystal',(0,0,.94),.09,0,.24,'Jade pale',staff,6)
        cone('Staff brass socket',(0,0,.83),.065,.065,.12,'Old gold',staff,6)
    else:
        weapon=empty('Held sword mount',(.09,-.10,-.15),limbs['arm_R'])
        weapon.rotation_euler=(math.radians(-12),math.radians(8),0)
        sword(weapon,enemy)
    if enemy:
        for sign in (-1,1):
            orb('Bandit shoulder plate',(sign*.34,0,.35),(.20,.19,.13),'Ash stone',body)
            beam('Bandit shoulder spike',(sign*.43,0,.38),(sign*.59,0,.51),.065,'Crimson edge',body,4,0)
    make_character_animations(name, body, limbs)


def make_character_animations(name, body, limbs):
    """Rigid-piece animation, editable pivot rigs; NLA names merge across objects."""
    actors=[body]+list(limbs.values())
    neutral={ob.name:(ob.location.copy(),ob.rotation_euler.copy()) for ob in actors}
    for clip, end in (('idle',48),('walk',24),('attack',18)):
        frames = [1, end//4+1, end//2+1, end*3//4+1, end+1]
        for ob in actors:
            ob.animation_data_create()
            action=bpy.data.actions.new(name+'_'+ob.name+'_'+clip)
            ob.animation_data.action=action
            action['clip']=clip
            action['loop']=clip!='attack'
            base_loc,base_rot=neutral[ob.name]
            for i, frame in enumerate(frames):
                ob.location=base_loc
                ob.rotation_euler=base_rot
                phase=i*math.pi*.5
                if clip=='idle':
                    if ob==body:
                        ob.location.z+=math.sin(phase)*.013
                        ob.rotation_euler.z+=math.sin(phase)*.022
                    elif 'arm' in ob.name:
                        ob.rotation_euler.x+=math.sin(phase)*.028
                elif clip=='walk':
                    if ob==body:
                        ob.location.z+=abs(math.sin(phase))*.035
                        ob.rotation_euler.z+=math.sin(phase)*.045
                    else:
                        sign=1 if ob.name.endswith('L') else -1
                        ob.rotation_euler.x+=math.sin(phase)*(.38 if 'leg' in ob.name else -.25)*sign
                else:
                    twist=[0,-.42,.72,.21,0][i]
                    if ob==body:
                        ob.rotation_euler.z+=twist
                        ob.location.y+=[0,.035,-.10,-.02,0][i]
                    elif ob==limbs['arm_R']:
                        ob.rotation_euler.x+=[0,-1.8,-.7,-.25,0][i]
                        ob.rotation_euler.y+=[0,-.4,.65,.12,0][i]
                    elif ob==limbs['arm_L']:
                        ob.rotation_euler.x+=[0,-.4,.3,.1,0][i]
                ob.keyframe_insert(data_path='location',frame=frame,group='Transform')
                ob.keyframe_insert(data_path='rotation_euler',frame=frame,group='Transform')
            track=ob.animation_data.nla_tracks.new()
            track.name=clip
            strip=track.strips.new(clip,1,action)
            strip.name=clip
            strip.extrapolation='NOTHING'
            strip.blend_type='REPLACE'
            # Keep all authored clips. glTF NLA export gathers tracks by matching names.
            ob.animation_data.action=None
            ob.location=base_loc
            ob.rotation_euler=base_rot
    ROOT['animation_clips']='idle (loop), walk (loop), attack (one shot)'
    ROOT['rig_type']='hierarchical rigid-part transform rig; no skinning required'


def pagoda_roof(name, z, width, depth, height, parent=None):
    # Three overlapping hipped tiers and gold upturned corner spars.
    frustum(name+' roof lower eave',z,z+.15,(width,depth),(width-.28,depth-.28),'Jade deep',parent)
    frustum(name+' roof lower slope',z+.13,z+height*.50,(width-.14,depth-.14),(width*.62,depth*.62),'Jade deep',parent)
    frustum(name+' roof upper slope',z+height*.47,z+height,(width*.68,depth*.68),(width*.12,depth*.16),'Ink teal',parent)
    for sx in (-1,1):
        for sy in (-1,1):
            beam(name+' turned corner gold spar',(sx*width*.16,sy*depth*.16,z+height*.84),
                 (sx*width*.48,sy*depth*.48,z+.08),.035,'Old gold',parent)
            beam(name+' rising corner tip',(sx*width*.46,sy*depth*.46,z+.09),
                 (sx*(width*.5+.08),sy*(depth*.5+.08),z+.30),.045,'Old gold',parent)
    # Raised teal ribs are visible from the game camera without texture maps.
    for i in range(-3,4):
        t=i/4
        beam(name+' front jade tile seam',(t*width*.44,-depth*.46,z+.19),
             (t*width*.25,-depth*.29,z+height*.51),.016,'Jade bright',parent,4)
    beam(name+' gold ridge',(-width*.1,0,z+height+.02),(width*.1,0,z+height+.02),.065,'Old gold',parent)


def house():
    begin_asset('house')
    box('Stone foundation',(0,0,.14),(4.7,3.7,.28),'Ash stone',edge=.09)
    box('Raised timber floor',(0,0,.33),(4.42,3.42,.15),'Timber edge',edge=.035)
    box('Cream plaster walls',(0,0,1.43),(4.05,3.05,2.12),'Warm plaster',edge=.05)
    for x in (-2.10,0,2.10):
        for y in (-1.60,1.60):
            box('House carved timber post',(x,y,1.50),(.18,.18,2.42),'Timber',edge=.025)
            box('House stone post shoe',(x,y,.48),(.25,.25,.26),'Stone light',edge=.025)
    for z in (.58,2.40):
        box('House long timber beam',(0,-1.61,z),(4.38,.16,.14),'Timber',edge=.025)
        box('House back timber beam',(0,1.61,z),(4.38,.16,.14),'Timber',edge=.025)
    box('Door shadow',(0,-1.55,1.24),(.83,.08,1.61),'Ink teal',edge=.01)
    box('Door teak panel',(0,-1.603,1.22),(.70,.055,1.5),'Timber',edge=.009)
    for x in (-.24,0,.24):
        box('Door vertical slats',(x,-1.64,1.24),(.025,.025,1.49),'Old gold',edge=.005)
    orb('Door brass handle',(.23,-1.69,1.1),(.045,.04,.045),'Gold edge')
    for x in (-1.35,1.35):
        box('Window dark inset',(x,-1.553,1.58),(.78,.06,.82),'Ink teal',edge=.015)
        box('Window glowing paper',(x,-1.592,1.58),(.69,.025,.73),'Parchment',edge=.01)
        for k in (-1,0,1):
            box('Window vertical lattice',(x+k*.21,-1.619,1.58),(.038,.035,.77),'Timber',edge=.004)
            box('Window horizontal lattice',(x,-1.623,1.58+k*.21),(.77,.04,.038),'Timber',edge=.004)
    for y,z,w in ((-1.93,.20,1.55),(-2.16,.10,1.85)):
        box('House welcome step',(0,y,z),(w,.48,.20),'Stone light',edge=.035)
    pagoda_roof('Lantern Vale dwelling',2.61,5.0,4.0,1.16)
    for x in (-1.00,1.00):
        make_lantern(ROOT,x,-1.85,1.77,.85)
    box('Jade house name plaque',(0,-1.77,2.35),(1.04,.10,.28),'Jade deep',edge=.018)
    for x in (-.25,0,.25):
        box('Original plaque gold lozenges',(x,-1.828,2.35),(.085,.012,.085),'Gold edge',edge=.005,rot=(0,math.pi/4,0))


def gate():
    begin_asset('gate')
    for x in (-2.15,2.15):
        box('Gate stone foot',(x,0,.21),(.75,.87,.42),'Ash stone',edge=.07)
        box('Gate pillar',(x,0,2.08),(.33,.39,3.76),'Corruption',edge=.035)
        for z in (.54,3.31):
            box('Gate brass collar',(x,0,z),(.39,.45,.15),'Old gold',edge=.015)
        beam('Gate diagonal brace',(x,0,2.77),(x-math.copysign(.76,x),0,3.65),.11,'Timber',vertices=4)
    box('Gate lower crossbeam',(0,0,3.28),(5.15,.41,.26),'Timber',edge=.025)
    box('Gate upper crossbeam',(0,0,3.73),(5.36,.48,.28),'Corruption',edge=.03)
    pagoda_roof('Spirit crossing gate',3.99,6.0,1.75,.86)
    box('Gate hanging plaque',(0,-.30,3.40),(1.02,.12,.65),'Jade deep',edge=.05)
    for x in (-.27,0,.27):
        box('Gate engraved jade seals',(x,-.37,3.4),(.12,.025,.21),'Gold edge',edge=.015)
    for x in (-1.59,1.59):
        make_lantern(ROOT,x,-.2,2.34,1.30)


def shrine():
    begin_asset('shrine')
    box('Shrine stone plinth',(0,0,.13),(2.72,2.38,.26),'Ash stone',edge=.09)
    box('Shrine upper step',(0,0,.31),(2.34,2.08,.16),'Stone light',edge=.045)
    for x in (-.95,.95):
        for y in (-.75,.75):
            box('Shrine cedar post',(x,y,1.18),(.14,.14,1.66),'Timber',edge=.02)
    box('Shrine back screen',(0,.74,1.17),(1.77,.12,1.45),'Jade deep',edge=.025)
    box('Stone altar',(0,.12,.66),(1.17,.95,.46),'Ash stone',edge=.08)
    cone('Jade flame pedestal',(0,.10,1.0),.32,.24,.24,'Old gold',vertices=8)
    cone('Jade shrine crystal',(0,.1,1.47),.24,0,.70,'Jade pale',vertices=5)
    cone('Jade shrine crystal lower',(0,.1,1.08),0,.24,.16,'Jade bright',vertices=5)
    for x in (-.61,.61):
        cone('Altar candle bowl',(x,-.25,.99),.10,.14,.10,'Old gold',vertices=8)
        cone('Amber candle flame',(x,-.25,1.11),.059,0,.16,'Lantern paper',vertices=5)
    pagoda_roof('Jade flame shrine',2.03,2.98,2.56,.77)
    make_lantern(ROOT,-.89,-.83,1.24,.75)
    make_lantern(ROOT,.89,-.83,1.24,.75)


def tree():
    begin_asset('tree')
    beam('Pine trunk lower',(0,0,0),(.07,.03,1.95),.20,'Timber',vertices=7,end_radius=.13)
    beam('Pine trunk leaning crown',(.07,.03,1.85),(-.15,.04,3.34),.12,'Timber edge',end_radius=.035)
    for a in range(0,360,90):
        rad=math.radians(a)
        beam('Pine ground roots',(math.cos(rad)*.51,math.sin(rad)*.43,.02),
             (.01,0,.47),.05,'Timber',end_radius=.13)
    for i,(x,y,z,s) in enumerate(((-.52,.03,1.67,.9),(.50,.09,2.12,1.02),
                                  (-.37,-.08,2.64,.94),(.06,.02,3.16,.76))):
        beam('Pine angular branch',(.04,0,z-.3),(x,y,z),.075,'Timber',end_radius=.035)
        cone('Pine sculpted bough '+str(i),(x,y,z),s,.10,s*.63,'Jade deep',vertices=7)
        cone('Pine sunlit bough cap '+str(i),(x,y,z+.13),s*.82,.07,s*.54,'Jade bright',vertices=7)
    for x,y,z in ((.39,-.10,1.95),(-.5,-.23,1.60),(-.28,.14,2.57)):
        orb('Amber pine cone',(x,y,z),(.09,.075,.16),'Old gold')


def bamboo():
    begin_asset('bamboo')
    for n,(x,y,h) in enumerate(((-.27,.09,2.75),(.05,-.05,3.34),(.31,.17,2.38))):
        r=.046 if n!=1 else .057
        cone('Bamboo green culm',(x,y,h*.5),r,r*.75,h,'Jade deep',vertices=7)
        for k in range(1,int(h/.4)):
            cone('Bamboo ivory joint',(x,y,k*.4),r*1.15,r*1.15,.025,'Jade pale',vertices=7)
        for k in range(3):
            z=h*.53+k*.35
            sign=-1 if (n+k)%2 else 1
            end=(x+sign*.50,y+.06,z+.20)
            beam('Bamboo fine branch',(x,y,z),end,.013,'Jade deep',vertices=4)
            for j in range(3):
                px=x+sign*(.18+j*.12)
                py=y+.035*j
                pz=z+.06+j*.05
                mesh('Bamboo lance leaf',[(px,py,pz),(px+sign*.12,py-.06,pz+.07),
                      (px+sign*.35,py-.1,pz-.13),(px+sign*.14,py+.026,pz-.04)],
                     [(0,1,2),(0,2,3)],'Jade bright')


def rock():
    begin_asset('rock')
    for loc,scale,mat in (((-.15,0,.50),(.83,.65,.60),'Ash stone'),
                           ((.48,.1,.25),(.44,.42,.32),'Stone light'),
                           ((-.49,-.33,.17),(.34,.30,.20),'Stone light')):
        obj=orb('Weathered low polygon stone',loc,scale,mat,subdivisions=1)
        for vert in obj.data.vertices:
            vert.co *= RNG.uniform(.9,1.1)
            # Keep every vertex above the world ground plane.
            vert.co.z=max(vert.co.z,-loc[2])
    for x,y,z in ((-.12,-.22,1.0),(.22,.05,.85),(-.49,.05,.85)):
        orb('Jade moss patch',(x,y,z),(.22,.19,.037),'Jade deep',subdivisions=1)


def lantern():
    begin_asset('lantern')
    box('Lantern post stone socket',(0,0,.15),(.42,.42,.30),'Ash stone',edge=.055)
    beam('Lantern cedar upright',(0,0,.27),(0,0,2.16),.058,'Timber',vertices=6)
    beam('Lantern hanging arm',(0,0,2.13),(.56,0,2.13),.058,'Timber',vertices=6)
    beam('Lantern arm angled brace',(0,0,1.86),(.30,0,2.13),.032,'Timber edge',vertices=6)
    make_lantern(ROOT,.48,0,1.40,1.04)
    cone('Lantern post jade cap',(0,0,2.20),.10,0,.15,'Jade bright',vertices=6)


def supported_export_options():
    """Only pass options exposed by the installed glTF exporter (4.3 baseline)."""
    props=bpy.ops.export_scene.gltf.get_rna_type().properties
    desired={
        'export_format':'GLB', 'use_selection':True,
        'export_yup':True, 'export_apply':True,
        'export_animations':True, 'export_frame_range':False,
        'export_force_sampling':True, 'export_cameras':False,
        'export_lights':False, 'export_extras':True,
        'export_materials':'EXPORT', 'export_nla_strips':True,
        'export_animation_mode':'NLA_TRACKS',
    }
    out={}
    for key,value in desired.items():
        if key not in props:
            continue
        prop=props[key]
        if prop.type=='ENUM' and value not in {item.identifier for item in prop.enum_items}:
            continue
        out[key]=value
    return out


def export_all(output):
    model_dir=output/'game'/'assets'/'models'
    art_dir=output/'art'
    model_dir.mkdir(parents=True,exist_ok=True)
    art_dir.mkdir(parents=True,exist_ok=True)
    options=supported_export_options()
    for name,collection,root in ASSETS:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.all_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active=root
        bpy.context.scene.frame_set(1)
        bpy.ops.export_scene.gltf(filepath=str(model_dir/(name+'.glb')),**options)
        print('JADEBOUND_EXPORTED',name,flush=True)
    # Editing gallery layout only. GLBs above have exact ground-centred origins.
    placements={'hero':(-5,-5,0),'elder':(-3.6,-5,0),'bandit':(-2.1,-5,0),
                'house':(-4,1,0),'gate':(3,2,0),'shrine':(3,-3,0),
                'tree':(-7,0,0),'bamboo':(-7,-4,0),'rock':(0,-5,0),
                'lantern':(5,-5,0)}
    for name,collection,root in ASSETS:
        root.location=placements[name]
    bpy.context.scene.frame_start=1
    bpy.context.scene.frame_end=49
    bpy.context.scene.render.fps=24
    bpy.context.scene.world.color=(.11,.15,.18)
    bpy.context.scene['project']='Jadebound: Ashes of Lantern Vale'
    bpy.context.scene['asset_notes']='Original editable geometry. Every asset has a named collection and root. No external dependencies. Materials are vertex-friendly flat PBR palettes.'
    bpy.context.scene['animation_notes']='Character pivot tracks named idle, walk, attack. Mute NLA tracks when editing a single clip. Idle/walk loop in engine; attack plays once.'
    bpy.ops.object.select_all(action='DESELECT')
    # A useful solid/material viewport on first opening, with no render dependencies.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.shading.type='MATERIAL'
                area.spaces.active.region_3d.view_distance=18
                area.spaces.active.region_3d.view_location=(0,0,1)
    bpy.ops.wm.save_as_mainfile(filepath=str(art_dir/'jadebound_assets.blend'))
    print('JADEBOUND_COMPLETE',str(art_dir/'jadebound_assets.blend'),flush=True)


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path.cwd())
    options=parser.parse_args(args)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for old in list(bpy.data.collections):
        if old.users==0 or old.name=='Collection':
            bpy.data.collections.remove(old)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.render.fps=24
    setup_materials()
    for name in ('hero','elder','bandit'):
        character(name)
    for builder in (shrine,house,gate,tree,bamboo,rock,lantern):
        builder()
    export_all(options.output.resolve())


if __name__=='__main__':
    main()
