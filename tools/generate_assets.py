#!/usr/bin/env python3
"""Original Jadebound art kit. Run with Blender 4.3+, never regular Python.

blender --background --threads 2 --python tools/generate_assets.py -- --output .
No downloads, textures, simulation, rendering, or optional add-ons are needed.
The library stays fully editable; exports use evaluated bevel modifiers.
"""
import argparse
import json
import struct
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
    # Palette hex values are perceptual sRGB. Blender/glTF shader inputs are linear.
    if isinstance(color, str):
        srgb=tuple(int(color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
        color=tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in srgb)
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
    material('Jade deep', '#234949')
    material('Jade bright', '#3b806a', 0.18, 0.46)
    material('Jade pale', '#83bea4', 0.2, 0.38)
    material('Ink teal', '#18272b')
    material('Ivory silk', '#b8a47e')
    material('Parchment', '#b4a17e')
    material('Warm plaster', '#a48c6c')
    material('Orange silk', '#bc582f')
    material('Lantern paper', '#ffc66d', roughness=0.5, emission=0.7)
    material('Old gold', '#b18a53', 0.65, 0.38)
    material('Gold edge', '#d4ab69', 0.55, 0.32)
    material('Timber', '#493428')
    material('Timber edge', '#795438')
    material('Ash stone', '#55625f')
    material('Stone light', '#889089')
    material('Corruption', '#692d37')
    material('Crimson edge', '#a7494a')
    material('Pink blossom', '#c2847b')
    material('Dark leather', '#392d27')
    material('Skin warm', '#b78360')
    material('Hair ink', '#24282a')
    material('Steel', '#9babaf', 0.8, 0.28)
    material('Roof slate', '#2d4352', .05, .81)
    material('Roof weathered', '#405768', .05, .78)
    material('Roof shadow', '#172831', .02, .86)
    material('Clay panels', '#8c674e')
    material('Bamboo leaf', '#526e40')
    material('Bamboo stalk', '#728454')
    material('Bamboo node', '#8d906b')
    material('Blossom shade', '#633e4b')
    material('Blossom coral', '#a65d70')
    material('Blossom light', '#be8290')
    material('Hero cloth shadow', '#192e34')
    material('Hero armor', '#53626b', .48, .43)


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
    if subdivisions >= 2:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
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


def curved_saber(parent):
    """A distinct forward-curving, single-edged travel saber with jade fuller."""
    box('Saber cord grip',(0,0,-.055),(.048,.064,.20),'Dark leather',parent,.009)
    for z in (-.12,-.075,-.03,.015):
        box('Saber grip binding',(0,-.035,z),(.051,.012,.012),'Ivory silk',parent,.002)
    box('Saber swept brass guard',(0,0,.06),(.24,.081,.043),'Old gold',parent,.016,
        (0,-.12,0))
    profile=[(0,.095,.063),(.004,.31,.069),(.026,.54,.061),(.080,.73,.050),(.16,.88,0)]
    vertices=[]
    for x,z,w in profile:
        vertices.extend([(x-w,0,z),(x,-.027,z),(x+w,0,z),(x,.021,z)])
    faces=[]
    for i in range(len(profile)-1):
        for side in range(4):
            faces.append((i*4+side,i*4+(side+1)%4,(i+1)*4+(side+1)%4,(i+1)*4+side))
    faces.extend([(3,2,1,0),(16,17,18,19)])
    mesh('Curved steel dao blade',vertices,faces,'Steel',parent)
    for a,b in zip(profile[:-2],profile[1:-1]):
        beam('Saber jade fuller',(a[0]-.008,-.029,a[1]+.018),
             (b[0]-.008,-.029,b[1]),.008,'Jade pale',parent,4)
    orb('Saber jade pommel',(0,0,-.17),(.043,.052,.043),'Jade bright',parent)
    beam('Saber orange knot',(0,0,-.19),(.052,.018,-.32),.014,'Orange silk',parent,5)


def hero():
    """Adult, layered wandering swordsman; a readable asymmetrical silhouette."""
    begin_asset('hero')
    body=empty('hero_torso',(0,0,1.02))
    frustum('Fitted dark teal underrobe',-.17,.40,(.38,.27),(.50,.29),'Jade deep',body)
    frustum('Long split robe rear',-.55,-.12,(.57,.32),(.39,.26),'Hero cloth shadow',body)
    for sign in (-1,1):
        panel=empty('Layered split robe panel',(sign*.13,-.135,-.15),body)
        panel.rotation_euler.y=sign*-.09
        frustum('Ivory linen inner pleat',-.43,.08,(.19,.045),(.15,.035),'Ivory silk',panel)
        frustum('Teal outer coat skirt',-.40,.08,(.17,.062),(.13,.052),'Jade deep',panel,
                offset=(sign*.065,-.017))
        beam('Coat skirt narrow embroidered edge',(sign*.15,-.050,-.39),
             (sign*.12,-.052,.05),.010,'Old gold',panel,4)
    box('Diagonal ivory lapel',(-.058,-.164,.21),(.11,.045,.40),'Ivory silk',body,.012,
        (0,-.39,0))
    box('Overlapping dark teal lapel',(.070,-.18,.23),(.09,.045,.43),'Jade deep',body,.012,
        (0,.39,0))
    beam('Fine collar gold piping',(-.015,-.207,.40),(.148,-.207,.08),.011,'Old gold',body,4)
    for x in (-.17,-.095,.145):
        beam('Subtle fabric fold',(x,-.151,-.045),(x*.82,-.155,.23),.011,'Hero cloth shadow',body,4)
    box('Wide leather sword belt',(0,-.01,-.065),(.425,.315,.095),'Dark leather',body,.021)
    box('Worn brass belt buckle',(.05,-.177,-.06),(.107,.030,.087),'Old gold',body,.014)
    box('Buckle dark inset',(.05,-.195,-.06),(.065,.013,.047),'Hero armor',body,.004)
    box('Russet sash knot',(-.19,-.115,-.055),(.11,.075,.13),'Orange silk',body,.015,
        (0,.18,-.15))
    box('Long russet sash tail',(-.26,-.16,-.29),(.089,.039,.39),'Orange silk',body,.008,
        (0,.22,.12))
    # A diagonal sheathed off-hand blade balances the raised saber silhouette.
    scabbard=empty('Belt scabbard mount',(-.26,.075,-.04),body)
    scabbard.rotation_euler=(.15,-.41,-.08)
    frustum('Lacquered travel scabbard',-.66,.06,(.08,.055),(.11,.068),'Hero cloth shadow',scabbard)
    for z in (-.58,-.16,.04):
        box('Scabbard brass furniture',(0,0,z),(.116,.078,.045),'Old gold',scabbard,.009)
    box('Sheathed secondary sword grip',(0,0,.15),(.064,.07,.17),'Dark leather',scabbard,.011)
    cone('Hero neck',(0,0,.455),.063,.066,.14,'Skin warm',body,10)
    orb('Adult angular face',(0,-.012,.643),(.133,.115,.169),'Skin warm',body,2)
    orb('Swept ink hair',(0,.025,.725),(.140,.114,.102),'Hair ink',body,2)
    for sign in (-1,1):
        orb('Ear',(sign*.132,-.005,.635),(.024,.020,.044),'Skin warm',body,1)
        box('Expressive dark brow',(sign*.052,-.112,.68),(.064,.017,.012),'Hair ink',body,.003,
            (0,sign*.12,0))
        box('Hero narrow eye',(sign*.052,-.116,.655),(.037,.010,.010),'Hair ink',body,.002)
        box('Temple hair lock',(sign*.117,.006,.701),(.024,.044,.106),'Hair ink',body,.008,
            (0,sign*-.17,0))
    mesh('Sculpted hero nose',[(-.022,-.109,.66),(.022,-.109,.66),(0,-.151,.605),
         (-.023,-.114,.596),(.023,-.114,.596)],[(0,1,2),(0,2,3),(1,4,2),(3,2,4)],'Skin warm',body)
    box('Quiet determined mouth',(0,-.116,.573),(.044,.011,.007),'Timber',body,.002)
    orb('Swordsman topknot',(0,.049,.866),(.069,.071,.098),'Hair ink',body,2)
    cone('Topknot jade band',(0,.045,.822),.069,.067,.042,'Jade bright',body,10)
    beam('Topknot brass hairpin',(-.13,.046,.847),(.15,.046,.854),.010,'Old gold',body,6)
    # Short scarf at the collar, not a broad cartoon bib.
    box('Burnt orange collar scarf',(0,.01,.404),(.285,.257,.052),'Orange silk',body,.017)
    box('Scarf trailing shoulder fold',(-.21,.134,.25),(.075,.04,.32),'Orange silk',body,.010,
        (0,-.35,-.14))
    limbs={}
    for sign,side in ((-1,'L'),(1,'R')):
        arm=empty('hero_arm_'+side,(sign*.28,0,.33),body)
        frustum('Tailored upper sleeve',-.28,.025,(.17,.18),(.20,.23),'Jade deep',arm,
                offset=(sign*.026,0))
        frustum('Layered shoulder cuirass',-.075,.065,(.25,.28),(.19,.24),'Hero armor',arm,
                offset=(sign*.04,.012))
        box('Shoulder armor gold rim',(sign*.105,-.12,-.025),(.075,.022,.083),'Old gold',arm,.009,
            (0,sign*-.26,0))
        frustum('Fitted forearm vambrace',-.48,-.27,(.12,.13),(.16,.16),'Dark leather',arm,
                offset=(sign*.043,-.027))
        for z in (-.30,-.42):
            box('Vambrace layered metal bands',(sign*.045,-.031,z),(.17,.17,.043),
                'Hero armor',arm,.010)
        orb('Gloved sword hand',(sign*.042,-.038,-.51),(.062,.066,.073),'Dark leather',arm,2)
        orb('Exposed knuckles',(sign*.042,-.090,-.504),(.054,.022,.037),'Skin warm',arm,1)
        leg=empty('hero_leg_'+side,(sign*.126,0,.80))
        frustum('Tailored dark trousers',-.46,.06,(.14,.15),(.18,.20),'Hero cloth shadow',leg)
        frustum('High leather boot shaft',-.66,-.39,(.135,.16),(.15,.16),'Dark leather',leg)
        box('Adult shaped travel boot',(0,-.078,-.708),(.164,.292,.14),'Dark leather',leg,.035)
        box('Boot heavy sole',(0,-.080,-.765),(.178,.30,.041),'Hero armor',leg,.014)
        for z in (-.45,-.54):
            box('Boot buckled straps',(0,-.002,z),(.163,.175,.031),'Timber edge',leg,.009)
            box('Boot small brass buckle',(.055,-.094,z),(.029,.018,.034),'Old gold',leg,.004)
        limbs['arm_'+side]=arm
        limbs['leg_'+side]=leg
    weapon=empty('Held curved saber',(.066,-.068,-.50),limbs['arm_R'])
    weapon.rotation_euler=(math.radians(-22),math.radians(23),math.radians(-8))
    curved_saber(weapon)
    make_character_animations('hero',body,limbs)


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
    """Overlapping slate tile rows on a curved hip roof; one editable tile mesh."""
    # Broad dark cavity and two substantial fascia levels make the eave read.
    frustum(name+' deep roof soffit',z-.16,z+.035,
            (width*.88,depth*.88),(width*.98,depth*.98),'Roof shadow',parent)
    for sy in (-1,1):
        box(name+' long carved eave fascia',(0,sy*depth*.465,z-.065),
            (width*.93,.10,.16),'Timber',parent,.025)
    for sx in (-1,1):
        box(name+' end carved eave fascia',(sx*width*.465,0,z-.065),
            (.10,depth*.93,.16),'Timber',parent,.025)
    # More shallow at the eave and steeper near the ridge. Corners turn upward.
    profile=[(1.0,.085),(.91,.025),(.80,.145),(.68,.31),
             (.56,.48),(.44,.66),(.31,.84),(.16,1.0)]
    vertices=[]
    faces=[]
    shades=[]
    def surface(side,u,ring):
        factor,rise=profile[ring]
        corner=(abs(u)**8)*.15*(factor**3)
        if side==0:
            x,y=u*width*.5*factor,-depth*.5*factor
        elif side==1:
            x,y=width*.5*factor,u*depth*.5*factor
        elif side==2:
            x,y=-u*width*.5*factor,depth*.5*factor
        else:
            x,y=-width*.5*factor,-u*depth*.5*factor
        return Vector((x,y,z+rise*height+corner))
    for side in range(4):
        count=max(5,round((width if side%2==0 else depth)/.28))
        for row in range(len(profile)-1):
            for col in range(count):
                u0=-1+2*col/count+.008
                u1=-1+2*(col+1)/count-.008
                um=(u0+u1)*.5
                # The centre of each broad ceramic tile is slightly barrelled.
                top=[surface(side,u0,row),surface(side,um,row),surface(side,u1,row),
                     surface(side,u0,row+1),surface(side,um,row+1),surface(side,u1,row+1)]
                top[1].z+=.022
                top[4].z+=.022
                for v in top:
                    v.z+=row*.007
                top.extend([top[0]-Vector((0,0,.035)),top[2]-Vector((0,0,.035))])
                base=len(vertices)
                vertices.extend(tuple(v) for v in top)
                tile_faces=[(0,1,4,3),(1,2,5,4),(0,6,7,2)]
                for face in tile_faces:
                    indices=tuple(base+i for i in face)
                    faces.append(indices)
                    shades.append(1 if (row*3+col+side)%7 in (0,1) else 0)
    tiles=mesh(name+' overlapping ceramic tile courses',vertices,faces,'Roof slate',parent)
    tiles.data.materials.append(MATS['Roof weathered'])
    for face,index in zip(tiles.data.polygons,shades):
        face.material_index=index
    # Raised charcoal hip tiles unify the roof; restrained aged metal at tips.
    for sx in (-1,1):
        for sy in (-1,1):
            for ring in range(len(profile)-1):
                f0,h0=profile[ring]
                f1,h1=profile[ring+1]
                beam(name+' rounded hip ridge',
                     (sx*width*.5*f0,sy*depth*.5*f0,z+h0*height+.15*f0**3+.035),
                     (sx*width*.5*f1,sy*depth*.5*f1,z+h1*height+.15*f1**3+.035),
                     .057,'Roof weathered',parent,8)
            beam(name+' upturned eave end',
                 (sx*width*.45,sy*depth*.45,z+.08),
                 (sx*(width*.5+.065),sy*(depth*.5+.065),z+.32),
                 .064,'Roof slate',parent,8)
            orb(name+' aged eave cap',(sx*(width*.5+.065),sy*(depth*.5+.065),z+.32),
                (.073,.073,.063),'Old gold',parent,1)
    box(name+' layered ridge base',(0,0,z+height+.015),
        (width*.39,depth*.17,.13),'Roof shadow',parent,.032)
    beam(name+' heavy ceramic roof ridge',(-width*.22,0,z+height+.11),
         (width*.22,0,z+height+.11),.095,'Roof weathered',parent,10)
    for sx in (-1,1):
        beam(name+' turned ridge terminal',(sx*width*.18,0,z+height+.10),
             (sx*width*.245,0,z+height+.27),.075,'Roof slate',parent,8)


def house():
    begin_asset('house')
    box('Stone foundation',(0,0,.14),(4.7,3.7,.28),'Ash stone',edge=.09)
    box('Raised timber floor',(0,0,.33),(4.42,3.42,.15),'Timber edge',edge=.035)
    box('Cream plaster walls',(0,0,1.43),(4.05,3.05,2.12),'Warm plaster',edge=.05)
    for x in (-2.10,2.10):
        for y in (-1.60,1.60):
            box('House carved timber post',(x,y,1.50),(.18,.18,2.42),'Timber',edge=.025)
            box('House stone post shoe',(x,y,.48),(.25,.25,.26),'Stone light',edge=.025)
    for z in (.58,2.40):
        box('House long timber beam',(0,-1.61,z),(4.38,.16,.14),'Timber',edge=.025)
        box('House back timber beam',(0,1.61,z),(4.38,.16,.14),'Timber',edge=.025)
    for x in (-1.52,-.5,.5,1.52):
        box('Front warm clay dado panels',(x,-1.542,.79),(.88,.068,.53),'Clay panels',edge=.025)
    for y in (-.92,0,.92):
        for x in (-2.035,2.035):
            box('Side plaster panel frame',(x,y,1.45),(.065,.09,1.83),'Timber',edge=.014)
            box('Side clay lower wall panels',(x,y,.76),(.045,.81,.48),'Clay panels',edge=.022)
    for x in (-1.9,-1.3,-.7,-.1,.5,1.1,1.7):
        box('Separate worn foundation stones',(x,-1.81,.15),(.54,.085,.20),
            'Stone light' if x<-.6 else 'Ash stone',edge=.039)
    box('Door dark recess',(0,-1.57,1.26),(1.02,.10,1.77),'Roof shadow',edge=.025)
    box('Door teak panel',(0,-1.62,1.22),(.79,.075,1.6),'Timber',edge=.016)
    for x in (-.50,.50):
        box('Carved entrance jamb',(x,-1.64,1.23),(.13,.23,1.81),'Timber edge',edge=.018)
        box('Entrance stone threshold foot',(x,-1.67,.50),(.21,.27,.26),'Stone light',edge=.027)
    box('Heavy carved door lintel',(0,-1.65,2.11),(1.22,.28,.18),'Timber edge',edge=.025)
    for x in (-.24,0,.24):
        box('Door vertical slats',(x,-1.64,1.24),(.025,.025,1.49),'Old gold',edge=.005)
    orb('Door brass handle',(.23,-1.69,1.1),(.045,.04,.045),'Gold edge')
    for x in (-1.35,1.35):
        box('Window dark inset',(x,-1.553,1.58),(.78,.06,.82),'Ink teal',edge=.015)
        box('Window deep paper pane',(x,-1.592,1.58),(.69,.025,.73),'Parchment',edge=.01)
        for sign in (-1,1):
            box('Window carved raised surround',(x+sign*.414,-1.66,1.58),(.066,.13,.90),'Timber edge',edge=.012)
            box('Window carved sill and header',(x,-1.66,1.58+sign*.44),(.89,.15,.077),'Timber edge',edge=.012)
        for k in (-1,0,1):
            box('Window vertical lattice',(x+k*.21,-1.619,1.58),(.038,.035,.77),'Timber',edge=.004)
            box('Window horizontal lattice',(x,-1.623,1.58+k*.21),(.77,.04,.038),'Timber',edge=.004)
    for y,z,w in ((-1.93,.20,1.55),(-2.16,.10,1.85)):
        box('House welcome step',(0,y,z),(w,.48,.20),'Stone light',edge=.035)
    # Substantial joinery sits in the cavity under the roof, not on the plaster.
    for x in (-1.94,-1.24,1.24,1.94):
        for y in (-1.62,1.62):
            box('Stepped timber eave bracket',(x,y,2.39),(.23,.40,.17),'Timber edge',edge=.020)
            box('Bracket lower cantilever',(x,y*1.06,2.48),(.35,.50,.11),'Timber',edge=.018)
    pagoda_roof('Lantern Vale dwelling',2.65,5.0,4.0,1.0)
    # Asymmetrical porch wing gives the dwelling a stronger silhouette.
    box('Entry porch canopy shadow',(0,-1.98,2.17),(1.55,.87,.10),'Timber',edge=.025)
    for x in (-.65,.65):
        beam('Porch canopy carved diagonal bracket',(x,-1.66,1.89),(x,-2.20,2.15),.065,'Timber edge',vertices=6)
    pagoda_roof('Entry porch canopy',2.25,1.75,1.22,.27)
    for x in (-1.00,1.00):
        make_lantern(ROOT,x,-1.85,1.77,.85)
    box('Jade house name plaque',(0,-1.77,2.35),(1.04,.10,.28),'Jade deep',edge=.018)
    for x in (-.25,0,.25):
        box('Original plaque gold lozenges',(x,-1.828,2.35),(.085,.012,.085),'Gold edge',edge=.005,rot=(0,math.pi/4,0))


def gate():
    begin_asset('gate')
    for x in (-2.15,2.15):
        box('Gate stone foot',(x,0,.21),(.75,.87,.42),'Ash stone',edge=.07)
        box('Gate pillar',(x,0,2.08),(.37,.43,3.76),'Timber',edge=.045)
        for z in (.54,3.31):
            box('Gate brass collar',(x,0,z),(.39,.45,.15),'Old gold',edge=.015)
        beam('Gate diagonal brace',(x,0,2.77),(x-math.copysign(.76,x),0,3.65),.11,'Timber',vertices=4)
    box('Gate lower crossbeam',(0,0,3.28),(5.15,.41,.26),'Timber',edge=.025)
    box('Gate upper crossbeam',(0,0,3.73),(5.36,.48,.28),'Timber edge',edge=.03)
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
    """Mature wind-shaped cherry tree, with visible branching and dusky coral mass."""
    begin_asset('tree')
    trunk=[(0,0,.02),(.12,.035,.80),(.04,.07,1.54),(-.21,.055,2.24),(-.34,.09,2.89)]
    for i,(a,b) in enumerate(zip(trunk[:-1],trunk[1:])):
        beam('Cherry twisting mature trunk',a,b,.27-i*.044,'Timber',vertices=10,
             end_radius=.225-i*.040)
        if i:
            orb('Cherry worn trunk joint',a,(.235-i*.035,.21-i*.031,.24),'Timber',subdivisions=2)
    for i in range(5):
        a=i*math.tau/5+.2
        beam('Cherry flared ground roots',(.67*math.cos(a),.53*math.sin(a),.035),
             (.03,0,.42),.041,'Timber',vertices=8,end_radius=.18)
    branches=[
        ((.07,.04,1.39),(.74,.10,2.13),(1.48,.25,2.82)),
        ((-.11,.04,1.96),(-.95,-.10,2.45),(-1.67,-.14,3.06)),
        ((-.25,.08,2.31),(-.15,.78,2.88),(.32,1.25,3.25)),
        ((-.12,.03,1.77),(.39,-.72,2.39),(.85,-1.13,2.86)),
        ((-.32,.09,2.73),(-.45,.14,3.20),(-.08,.23,3.73)),
        ((.70,.10,2.14),(1.20,-.15,2.72),(1.77,-.48,3.16)),
    ]
    for i,(a,b,c) in enumerate(branches):
        beam('Cherry sweeping bough',a,b,.135,'Timber',vertices=9,end_radius=.086)
        beam('Cherry ascending twig structure',b,c,.086,'Timber edge',vertices=8,end_radius=.026)
        orb('Cherry branch union',b,(.105,.11,.12),'Timber',subdivisions=2)
        mid=Vector(b).lerp(Vector(c),.43)
        fork=mid+Vector(((-1 if i%2 else 1)*.38,.18,.33))
        beam('Cherry visible fork',mid,fork,.047,'Timber edge',vertices=7,end_radius=.014)
    # Nine broad, flattened bough pads give a composed crown silhouette.
    # Their irregular edges break into individual petals without balloon lobes.
    clusters=[
        (-1.31,-.05,3.13,.93,.64,.12),(-.61,-.12,3.44,.78,.61,.12),
        (-.10,.19,3.81,.78,.62,.15),(.71,.27,3.54,.84,.62,.12),
        (1.51,-.27,3.17,.84,.62,.13),(.78,-.97,2.97,.80,.59,.12),
        (-.53,-.76,3.15,.88,.56,.12),(-.44,.91,3.29,.80,.60,.11),
        (.50,1.05,3.40,.82,.60,.12),
    ]
    # No closed canopy shells: each crown is an open collection of small,
    # folded petal sprays. Gaps, visible twigs and jagged edges read as foliage.
    for i,(x,y,z,sx,sy,sz) in enumerate(clusters):
        centre=Vector((x,y,z))
        nearest=min((Vector(branch[2]) for branch in branches),
                    key=lambda tip:(tip-centre).length)
        twigbase=nearest.lerp(centre,.35)
        beam('Cherry fine canopy branch',nearest,centre,.022,'Timber edge',
             vertices=5,end_radius=.007)
        for sign in (-1,1):
            beam('Cherry exposed blossom twig',twigbase,
                 centre+Vector((sign*sx*.52,sy*.13,sz*.30)),
                 .015,'Timber edge',vertices=5,end_radius=.004)
        vertices=[]
        faces=[]
        shades=[]
        # A fixed local generator keeps this foliage reproducible independently
        # of edits to any other asset or the number of source trunk objects.
        petals=random.Random(9107+i*173)
        for spray in range(60):
            # Dense, overlapping fan sprays form flattened branch pads, not
            # scattered points. A scalloped edge breaks the broad silhouette.
            theta=spray*2.399963229728653+petals.uniform(-.26,.26)
            radius=math.sqrt((spray+.45)/60)
            radius*=1+.13*math.sin(theta*3+i)+.08*math.sin(theta*7-i)
            p=centre+Vector((math.cos(theta)*sx*radius,
                             math.sin(theta)*sy*radius,
                             petals.uniform(-.60,.60)*sz+radius*radius*.04))
            orient=petals.uniform(0,math.tau)
            for petal in range(3):
                angle=orient+petal*math.tau/3+petals.uniform(-.38,.38)
                length=petals.uniform(.15,.245)
                width=length*petals.uniform(.38,.54)
                direction=Vector((math.cos(angle),math.sin(angle),
                                  petals.uniform(-.20,.34))).normalized()
                sideways=direction.cross(Vector((0,0,1))).normalized()
                normal=sideways.cross(direction).normalized()
                # Five points form a folded diamond petal, not an oval bump.
                pts=[p,
                     p+direction*length*.43+sideways*width,
                     p+direction*length,
                     p+direction*length*.43-sideways*width,
                     p+direction*length*.43+normal*length*.20]
                base=len(vertices)
                vertices.extend(tuple(v) for v in pts)
                # Only a few upper sprays receive restrained rose highlights.
                chance=petals.random()
                shade=2 if p.z>z and chance<.13 else (1 if chance<.32 else 0)
                for face in ((0,1,4),(1,2,4),(2,3,4),(3,0,4)):
                    faces.append(tuple(base+k for k in face))
                    shades.append(shade)
        foliage=mesh('Cherry open angular blossom sprays '+str(i),vertices,faces,
                     'Blossom coral')
        foliage.data.materials.append(MATS['Blossom shade'])
        foliage.data.materials.append(MATS['Blossom light'])
        for polygon,shade in zip(foliage.data.polygons,shades):
            polygon.material_index=shade
    # Few fallen petals anchor the tree naturally, without a flat base disk.
    for i in range(12):
        angle=RNG.uniform(0,math.tau)
        radius=RNG.uniform(.55,1.70)
        orb('Fallen coral petals',(math.cos(angle)*radius,math.sin(angle)*radius,.018),
            (.065,.044,.012),'Blossom coral',subdivisions=1)


def bamboo():
    begin_asset('bamboo')
    for n,(x,y,h) in enumerate(((-.27,.09,2.75),(.05,-.05,3.34),(.31,.17,2.38))):
        r=.046 if n!=1 else .057
        cone('Bamboo green culm',(x,y,h*.5),r,r*.75,h,'Bamboo stalk',vertices=7)
        for k in range(1,int(h/.4)):
            cone('Bamboo ivory joint',(x,y,k*.4),r*1.15,r*1.15,.025,'Bamboo node',vertices=7)
        for k in range(3):
            z=h*.53+k*.35
            sign=-1 if (n+k)%2 else 1
            end=(x+sign*.50,y+.06,z+.20)
            beam('Bamboo fine branch',(x,y,z),end,.013,'Bamboo stalk',vertices=4)
            for j in range(3):
                px=x+sign*(.18+j*.12)
                py=y+.035*j
                pz=z+.06+j*.05
                mesh('Bamboo lance leaf',[(px,py,pz),(px+sign*.12,py-.06,pz+.07),
                      (px+sign*.35,py-.1,pz-.13),(px+sign*.14,py+.026,pz-.04)],
                     [(0,1,2),(0,2,3)],'Bamboo leaf')


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


def make_static_export_copy(name, source_collection, source_root):
    """Bake an export-only mesh per material without touching authoring objects.

    Evaluating first preserves bevel geometry. Root-relative vertex transforms
    preserve the same ground origin, scale, placement and flat-shaded appearance.
    Grouping by material replaces scores of tiny runtime draws with a handful.
    """
    bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    root_inverse=source_root.matrix_world.inverted_safe()
    groups={}
    source_count=0
    for original in source_collection.all_objects:
        if original.type!='MESH':
            continue
        source_count+=1
        evaluated=original.evaluated_get(depsgraph)
        evaluated_mesh=evaluated.to_mesh()
        try:
            transform=root_inverse @ evaluated.matrix_world
            # Remapping independently for each source/material avoids retaining
            # unused vertices when an author later adds multi-material meshes.
            remaps={}
            for polygon in evaluated_mesh.polygons:
                slot=polygon.material_index
                mat=(evaluated_mesh.materials[slot]
                     if slot<len(evaluated_mesh.materials) else None)
                if mat is None:
                    mat=MATS['Ash stone']
                group=groups.setdefault(mat.name,{
                    'material':mat,'vertices':[],'faces':[],'smooth':[]})
                remap=remaps.setdefault(mat.name,{})
                face=[]
                for vertex_index in polygon.vertices:
                    if vertex_index not in remap:
                        remap[vertex_index]=len(group['vertices'])
                        group['vertices'].append(tuple(
                            transform @ evaluated_mesh.vertices[vertex_index].co))
                    face.append(remap[vertex_index])
                group['faces'].append(face)
                group['smooth'].append(polygon.use_smooth)
        finally:
            evaluated.to_mesh_clear()
    temporary=bpy.data.collections.new('__EXPORT_ONLY_'+name)
    bpy.context.scene.collection.children.link(temporary)
    export_root=bpy.data.objects.new(name+'_optimized',None)
    temporary.objects.link(export_root)
    export_root.matrix_world=source_root.matrix_world.copy()
    for key in source_root.keys():
        export_root[key]=source_root[key]
    export_root['static_mesh_batching']='One evaluated mesh per material'
    export_root['authoring_mesh_count']=source_count
    export_root['exported_mesh_count']=len(groups)
    for mat_name,group in sorted(groups.items()):
        data=bpy.data.meshes.new(name+' • '+mat_name+' • batched')
        data.from_pydata(group['vertices'],[],group['faces'])
        data.materials.append(group['material'])
        for polygon,smooth in zip(data.polygons,group['smooth']):
            polygon.use_smooth=smooth
        data.update()
        obj=bpy.data.objects.new(name+'_'+mat_name.replace(' ','_'),data)
        temporary.objects.link(obj)
        obj.parent=export_root
    print('JADEBOUND_STATIC_BATCH',name,source_count,'->',len(groups),'meshes',flush=True)
    return temporary,export_root


def remove_static_export_copy(collection):
    """Remove transient export data before saving the editable asset library."""
    for obj in list(collection.objects):
        data=obj.data if obj.type=='MESH' else None
        bpy.data.objects.remove(obj,do_unlink=True)
        if data is not None and data.users==0:
            bpy.data.meshes.remove(data)
    bpy.data.collections.remove(collection)


def restore_character_bind_translations(path, character_name):
    """Preserve authored constant pivot locations omitted by Blender NLA optimization.

    The Blender 4.3 glTF exporter can omit constant translation channels while
    emitting identity rest nodes for transform-animated objects. Restore only
    the known authored pivot locations, converted from Blender Z-up to glTF Y-up.
    Animation samples remain absolute local transforms, so this does not add
    another offset to animated torso positions.
    """
    raw=path.read_bytes()
    magic,version,total=struct.unpack_from('<III',raw)
    if magic!=0x46546C67 or version!=2 or total!=len(raw):
        raise RuntimeError('Invalid generated GLB header: '+str(path))
    json_size,json_kind=struct.unpack_from('<II',raw,12)
    if json_kind!=0x4E4F534A:
        raise RuntimeError('Expected GLB JSON chunk')
    document=json.loads(raw[20:20+json_size])
    h=character_name=='hero'
    bind={character_name+'_torso':[0,1.02 if h else .97,0]}
    for suffix,sign in [('L',-1),('R',1)]:
        bind[character_name+'_leg_'+suffix]=[sign*(.126 if h else .145),.80 if h else .72,0]
        bind[character_name+'_arm_'+suffix]=[sign*(.28 if h else .32),.33 if h else .30,0]
    seen=set()
    for node in document['nodes']:
        name=node.get('name')
        if name in bind:
            if 'matrix' in node:
                raise RuntimeError('Unexpected matrix on animated bind pivot: '+name)
            node['translation']=bind[name]
            seen.add(name)
    if seen!=set(bind):
        raise RuntimeError('Missing generated rig pivots: '+str(set(bind)-seen))
    encoded=json.dumps(document,separators=(',',':'),ensure_ascii=False).encode('utf8')
    encoded+=b' '*((-len(encoded))%4)
    tail=raw[20+json_size:]
    payload=struct.pack('<III',magic,version,20+len(encoded)+len(tail))
    payload+=struct.pack('<II',len(encoded),json_kind)+encoded+tail
    path.write_bytes(payload)
    print('JADEBOUND_BIND_PRESERVED',character_name,len(seen),flush=True)


def export_all(output):
    model_dir=output/'game'/'assets'/'models'
    art_dir=output/'art'
    model_dir.mkdir(parents=True,exist_ok=True)
    art_dir.mkdir(parents=True,exist_ok=True)
    options=supported_export_options()
    for name,collection,root in ASSETS:
        bpy.context.scene.frame_set(1)
        temporary=None
        export_collection,export_root=collection,root
        asset_options=dict(options)
        try:
            # Animated characters retain their exact hierarchy and NLA tracks.
            # Static props use disposable, material-batched evaluated geometry.
            if name not in ('hero','elder','bandit'):
                temporary,export_root=make_static_export_copy(name,collection,root)
                export_collection=temporary
                asset_options['export_animations']=False
            bpy.ops.object.select_all(action='DESELECT')
            for obj in export_collection.all_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active=export_root
            bpy.ops.export_scene.gltf(filepath=str(model_dir/(name+'.glb')),**asset_options)
        finally:
            if temporary is not None:
                remove_static_export_copy(temporary)
        if name in ('hero','elder','bandit'):
            restore_character_bind_translations(model_dir/(name+'.glb'),name)
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
    hero()
    for name in ('elder','bandit'):
        character(name)
    for builder in (shrine,house,gate,tree,bamboo,rock,lantern):
        builder()
    export_all(options.output.resolve())


if __name__=='__main__':
    main()
