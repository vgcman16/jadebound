#!/usr/bin/env python3
"""Original Jadebound modular skinned hero. Blender 4.3+ authoring source.

Run: blender --background --threads 2 --python tools/generate_modular_hero.py -- --output .
No third-party models/textures. All forms, rig, UVs, material detail and clips are
built here. The six Gear_/Head_/Weapon_ meshes are the runtime visibility contract.
"""
from __future__ import annotations
import argparse
import json
import hashlib
import re
import math
import struct
import tempfile
import zlib
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Euler, Quaternion

SCHEMA = ('Gear_Wayfarer', 'Gear_Warden', 'Head_Topknot', 'Head_Warden',
          'Weapon_Saber', 'Weapon_Glaive')
MATERIALS = {}
BUILDERS = {}
BONES = {}
ROOT = None
RIG = None
PI = math.pi


def srgb(hex_color):
    c = [int(hex_color.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in c)


def mix_weights(a, b, t):
    out = {k: v*(1-t) for k, v in a.items()}
    for k, v in b.items():
        out[k] = out.get(k, 0) + v*t
    return {k: v for k, v in out.items() if v > 1e-7}


def wb(name):
    return {name: 1.0}


class MeshBuilder:
    """One skinned mesh per runtime slot; all sculpted subforms stay batched."""
    def __init__(self, name):
        self.name = name
        self.vertices, self.faces, self.materials, self.weights = [], [], [], []
        self.uvs = []
        self.uv_region=(0,0,1,1)
        self.atlas_region_index=None

    def add(self, vertices, faces, mat, weights, uvs=None):
        offset = len(self.vertices)
        self.vertices.extend(tuple(v) for v in vertices)
        self.faces.extend(tuple(offset+i for i in f) for f in faces)
        self.materials.extend([mat]*len(faces) if isinstance(mat, str) else mat)
        self.weights.extend([weights]*len(vertices) if isinstance(weights, dict) else weights)
        source_uvs=uvs if uvs is not None else [(v[0]*2,v[2]*2) for v in vertices]
        u0,v0,u1,v1=self.uv_region
        if self.atlas_region_index is not None:
            face_materials={mat} if isinstance(mat,str) else set(mat)
            atlas_kind=next((kind for kind,name in ATLAS_MATS.items() if name in face_materials),None)
            if atlas_kind is not None:
                u0,v0,u1,v1=atlas_uv_rect(atlas_kind,self.atlas_region_index)
        self.uvs.extend((u0+u*(u1-u0),v0+v*(v1-v0)) for u,v in source_uvs)

    def finish(self):
        mesh = bpy.data.meshes.new(self.name+' editable surface')
        mesh.from_pydata(self.vertices, [], self.faces)
        mesh.update()
        ob = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(ob)
        ob.parent = RIG
        used = list(dict.fromkeys(self.materials))
        for name in used:
            mesh.materials.append(MATERIALS[name])
        for poly, name in zip(mesh.polygons, self.materials):
            poly.material_index = used.index(name)
            poly.use_smooth = name not in ('Steel', 'Blade edge', 'Steel shadow')
        uv = mesh.uv_layers.new(name='TailoredUV')
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                uv.data[li].uv = self.uvs[mesh.loops[li].vertex_index]
        for bone in BONES:
            group = ob.vertex_groups.new(name=bone)
            for i, weights in enumerate(self.weights):
                if weights.get(bone, 0) > 0:
                    group.add([i], weights[bone], 'REPLACE')
        mod = ob.modifiers.new('Jadebound anatomical skin', 'ARMATURE')
        mod.object = RIG
        mod.use_deform_preserve_volume = False
        ob['original_art'] = True
        ob['slot_contract'] = self.name if self.name in SCHEMA else 'always visible'
        return ob


def loft(builder, rings, mat, weights, n=24, cap=True, phase=0, fold=0):
    """Anatomical z-loft: (z, half-width, half-depth, centre-x, centre-y)."""
    vertices, uvs, vw = [], [], []
    for j, (z, rx, ry, cx, cy) in enumerate(rings):
        for i in range(n):
            a = i*2*PI/n+phase
            # Circumference-shaped tailoring, never a rectangular tube.
            f = 1+fold*math.cos(a*7+j*.43)
            vertices.append((cx+rx*math.cos(a)*f, cy+ry*math.sin(a)*f, z))
            uvs.append((i/n, j/(len(rings)-1)))
            vw.append(weights[j] if isinstance(weights, list) else weights)
    faces = []
    for j in range(len(rings)-1):
        for i in range(n):
            faces.append((j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i))
    if cap:
        faces += [tuple(reversed(range(n))), tuple((len(rings)-1)*n+i for i in range(n))]
    builder.add(vertices, faces, mat, vw, uvs)


def tube(builder, points, widths, depths, mat, weights, n=16):
    """Smooth tapered limb/trim loft along a 3D centreline."""
    verts, uvs, vw = [], [], []
    points = [Vector(p) for p in points]
    for j, p in enumerate(points):
        tangent = (points[min(j+1,len(points)-1)]-points[max(j-1,0)]).normalized()
        reference = Vector((0, 1, 0))
        if abs(tangent.dot(reference)) > .9:
            reference = Vector((1, 0, 0))
        x = tangent.cross(reference).normalized()
        y = tangent.cross(x).normalized()
        for i in range(n):
            a = 2*PI*i/n
            verts.append(p+x*widths[j]*math.cos(a)+y*depths[j]*math.sin(a))
            uvs.append((i/n, j/(len(points)-1)))
            vw.append(weights[j] if isinstance(weights,list) else weights)
    faces=[]
    for j in range(len(points)-1):
        for i in range(n):
            faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces += [tuple(reversed(range(n))),tuple((len(points)-1)*n+i for i in range(n))]
    builder.add(verts,faces,mat,vw,uvs)


def ellipsoid(builder, centre, scale, mat, weights, n=20, rows=12, rotation=None):
    verts, uvs=[] ,[]
    rot=Matrix.Identity(3) if rotation is None else rotation
    for j in range(rows+1):
        lat=-PI/2+PI*j/rows
        for i in range(n):
            a=2*PI*i/n
            local=Vector((scale[0]*math.cos(lat)*math.cos(a),scale[1]*math.cos(lat)*math.sin(a),scale[2]*math.sin(lat)))
            verts.append(Vector(centre)+rot@local)
            uvs.append((i/n,j/rows))
    faces=[]
    for j in range(rows):
        for i in range(n):
            faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    builder.add(verts,faces,mat,weights,uvs)


def ribbon(builder, points, widths, mat, weights, thickness=.004):
    """Swept fabric or metal strip, with a true thickness and shaped centreline."""
    points=[Vector(p) for p in points]
    verts=[]
    for j,p in enumerate(points):
        tangent=(points[min(j+1,len(points)-1)]-points[max(j-1,0)]).normalized()
        side=Vector((tangent.z,0,-tangent.x)).normalized()
        if side.length<.5:
            side=Vector((1,0,0))
        for back in (0,1):
            for sign in (-1,1):
                verts.append(p+side*widths[j]*.5*sign+Vector((0,back*thickness,0)))
    faces=[]
    for j in range(len(points)-1):
        a=j*4;b=a+4
        faces += [(a,b,b+1,a+1),(a+3,b+3,b+2,a+2),(a+2,b+2,b,a),(a+1,b+1,b+3,a+3)]
    faces += [(0,1,3,2),tuple((len(points)-1)*4+i for i in (0,2,3,1))]
    vw=[]
    for j in range(len(points)):
        vw.extend([weights[j] if isinstance(weights,list) else weights]*4)
    builder.add(verts,faces,mat,vw)




def stable_image_name(label):
    label=label.lower().removeprefix('original ')
    label=label.replace('medium-scale tangent normal','normal').replace('medium-scale roughness','roughness')
    return 'jb_'+re.sub(r'[^a-z0-9]+','_',label).strip('_')

def setup_materials():
    palette = {
        'Skin': ('#b88768', 0, .57), 'Skin shadow': ('#91604d',0,.63),
        'Lips': ('#875246',0,.67), 'Eye ivory': ('#c5b8a0',0,.44),
        'Ink': ('#171f25',0,.48), 'Hair': ('#20272b',.02,.43),
        'Hair glint': ('#3d4649',.04,.42),
        'Teal cloth': ('#234e52',0,.86), 'Teal fold': ('#18373d',0,.88),
        'Teal seam': ('#527675',0,.84), 'Ivory cloth': ('#c1b59a',0,.86),
        'Ivory fold': ('#9a927d',0,.89), 'Charcoal cloth': ('#242c34',0,.88),
        'Charcoal leather': ('#303337',0,.63), 'Brown leather': ('#46372d',0,.7),
        'Leather edge': ('#78634a',0,.66), 'Cinnabar': ('#80423a',0,.81),
        'Steel': ('#91a2ab',.82,.28), 'Blade edge': ('#d5dadd',.85,.22),
        'Steel shadow': ('#44535d',.72,.36), 'Armor blue': ('#3d505d',.67,.36),
        'Armor charcoal': ('#35414a',.63,.38), 'Old gold': ('#ae8953',.68,.38),
        'Gold light': ('#c8a873',.70,.31), 'Jade enamel': ('#52867a',.35,.26),
        'Sole': ('#292b2d',0,.8), 'Weapon wood': ('#3c3030',0,.62),
    }
    # Original UV-authored cloth folds, leather wear and brushed metal maps.
    # PNG data is explicitly sRGB for albedo and linear for normal/roughness.
    # Packing real PNG pixels avoids generated-image color-space ambiguity.
    size=256
    categories={}
    def field(kind,u,v):
        micro=math.sin(u*2*PI*121)*math.sin(v*2*PI*113)
        if kind=='cloth':
            folds=math.sin((u*6+.075*math.sin(v*2*PI))*2*PI)
            folds+=.32*math.sin((u*11-v*.23)*2*PI)
            fold_weight=.4+.6*math.sin(v*PI)**2
            edge=min(u,1-u,v,1-v)
            hem=math.exp(-edge*75)
            tonal=1+folds*.065*fold_weight-hem*.13+micro*.011
            height=folds*.0026*fold_weight+micro*.00015
            rough=.83+folds*.035+hem*.045+micro*.014
        elif kind=='leather':
            broad=math.sin(u*2*PI*3+.45*math.sin(v*2*PI*2))*math.cos(v*2*PI*4)
            pores=math.sin(u*2*PI*83+math.sin(v*23))*math.sin(v*2*PI*79)
            edge=min(u,1-u,v,1-v)
            wear=math.exp(-edge*45)
            tonal=.99+broad*.065+wear*.15+pores*.017
            height=broad*.0008+pores*.0002
            rough=.66+broad*.055-wear*.13+pores*.035
        else:
            brush=math.sin(u*2*PI*77+math.sin(v*2*PI)*.8)
            broad=math.sin(u*2*PI*3)*.035+math.cos(v*2*PI*2)*.018
            tonal=1+broad+brush*.027
            height=brush*.00013+math.sin(u*2*PI*7)*.0003
            rough=.28+brush*.035+broad*.7
        return tonal,height,max(.15,min(.96,rough))
    def packed_png(name,pixels,colorspace):
        def chunk(kind,data):
            return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
        rows=b''.join(b'\x00'+pixels[y*size*3:(y+1)*size*3] for y in range(size))
        png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b'')
        with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as f:
            f.write(png);path=Path(f.name)
        im=bpy.data.images.load(str(path),check_existing=False)
        im.name=stable_image_name(name);im.colorspace_settings.name=colorspace;im.pack()
        # The exporter otherwise prefers the random temporary filepath basename.
        # Packed bytes are authoritative; an empty path makes its name deterministic.
        im.filepath_raw=''
        path.unlink()
        return im
    for kind in ('cloth','leather','metal'):
        normal=bytearray();roughness=bytearray();tones=[]
        step=1/size
        for y in range(size):
            v=(y+.5)/size
            for x in range(size):
                u=(x+.5)/size
                tone,height,rough=field(kind,u,v);tones.append(tone)
                dx=(field(kind,u+step,v)[1]-field(kind,u-step,v)[1])/(2*step)
                dy=(field(kind,u,v+step)[1]-field(kind,u,v-step)[1])/(2*step)
                n=Vector((-dx,-dy,1)).normalized()
                normal.extend(round((c*.5+.5)*255) for c in n)
                roughness.extend([round(rough*255)]*3)
        categories[kind]=(tones,packed_png('Original '+kind+' medium-scale tangent normal',bytes(normal),'Non-Color'),
                          packed_png('Original '+kind+' medium-scale roughness',bytes(roughness),'Non-Color'))
    for name,(hexcolor,metal,rough) in palette.items():
        mat = bpy.data.materials.new(name)
        mat.diffuse_color=(*srgb(hexcolor),1)
        mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value=(*srgb(hexcolor),1)
        bsdf.inputs['Metallic'].default_value=metal
        bsdf.inputs['Roughness'].default_value=rough
        kind='metal' if metal>.5 else ('cloth' if 'cloth' in name or 'fold' in name or name=='Cinnabar' else 'leather' if 'leather' in name or name=='Leather edge' else None)
        if kind:
            tones,normal_image,rough_image=categories[kind]
            color=tuple(int(hexcolor.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
            rgb=bytearray()
            for tone in tones:
                # Preserve palette hue and value; variation has legible centimeter scale.
                rgb.extend(round(max(0,min(1,c*tone))*255) for c in color)
            albedo=packed_png('Original '+name+' albedo',bytes(rgb),'sRGB')
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=albedo
            mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
            roughtex=mat.node_tree.nodes.new('ShaderNodeTexImage');roughtex.image=rough_image
            mat.node_tree.links.new(roughtex.outputs['Color'],bsdf.inputs['Roughness'])
            normaltex=mat.node_tree.nodes.new('ShaderNodeTexImage');normaltex.image=normal_image
            normalmap=mat.node_tree.nodes.new('ShaderNodeNormalMap');normalmap.inputs['Strength'].default_value=.65 if kind=='cloth' else .45
            mat.node_tree.links.new(normaltex.outputs['Color'],normalmap.inputs['Color'])
            mat.node_tree.links.new(normalmap.outputs['Normal'],bsdf.inputs['Normal'])
        MATERIALS[name]=mat


def setup_rig():
    global ROOT,RIG
    ROOT=bpy.data.objects.new('HeroModular',None)
    bpy.context.collection.objects.link(ROOT)
    ROOT['license']='Original Jadebound artwork. No external models or textures.'
    ROOT['front_axis']='Blender -Y / glTF +Z; Z-up authoring, metres'
    ROOT['adult_proportions']='1.84m skull height, approximately 7.1 heads'
    data=bpy.data.armatures.new('Jadebound adult anatomical skeleton')
    RIG=bpy.data.objects.new('JadeboundRig',data)
    bpy.context.collection.objects.link(RIG)
    RIG.parent=ROOT
    bpy.context.view_layer.objects.active=RIG
    RIG.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(name,head,tail,parent=None):
        b=data.edit_bones.new(name)
        b.head=head;b.tail=tail;b.roll=0
        if parent: b.parent=data.edit_bones[parent]
        b.use_connect=False
        BONES[name]=(Vector(head),Vector(tail))
    bone('root',(0,0,0),(0,0,.16))
    bone('hips',(0,0,.94),(0,0,1.085),'root')
    bone('spine',(0,0,1.085),(0,0,1.285),'hips')
    bone('chest',(0,0,1.285),(0,0,1.485),'spine')
    bone('neck',(0,0,1.485),(0,0,1.59),'chest')
    bone('head',(0,0,1.59),(0,0,1.825),'neck')
    for sign,side in ((-1,'L'),(1,'R')):
        bone('clavicle.'+side,(sign*.035,0,1.46),(sign*.20,0,1.455),'chest')
        bone('upper_arm.'+side,(sign*.20,0,1.455),(sign*.325,-.006,1.215),'clavicle.'+side)
        bone('forearm.'+side,(sign*.325,-.006,1.215),(sign*.373,-.052,.985),'upper_arm.'+side)
        bone('hand.'+side,(sign*.373,-.052,.985),(sign*.389,-.078,.887),'forearm.'+side)
        bone('thigh.'+side,(sign*.09,0,.94),(sign*.113,-.012,.52),'hips')
        bone('shin.'+side,(sign*.113,-.012,.52),(sign*.113,.01,.125),'thigh.'+side)
        bone('foot.'+side,(sign*.113,.01,.125),(sign*.113,-.175,.075),'shin.'+side)
        bone('coat.'+side,(sign*.125,.065,.99),(sign*.19,.075,.61),'hips')
    bpy.ops.object.mode_set(mode='OBJECT')
    RIG.select_set(False)
    RIG.data.display_type='OCTAHEDRAL'
    RIG.show_in_front=True
    for pb in RIG.pose.bones:
        pb.rotation_mode='QUATERNION'


def torso_weights(z):
    if z<1.045: return wb('hips')
    if z<1.20: return mix_weights(wb('hips'),wb('spine'),min(1,(z-1.045)/.12))
    if z<1.39: return mix_weights(wb('spine'),wb('chest'),min(1,(z-1.20)/.15))
    return wb('chest')


def torso(builder,mat,inflation=0):
    profiles=[(.94,.166,.116,0,.01),(1.015,.166,.109,0,0),
              (1.10,.149,.10,0,0),(1.19,.171,.118,0,0),
              (1.285,.205,.135,0,.002),(1.38,.231,.13,0,.008),
              (1.43,.212,.119,0,.009),(1.472,.114,.083,0,.007),(1.50,.064,.058,0,.003)]
    rings=[(z,rx+inflation,ry+inflation,x,y) for z,rx,ry,x,y in profiles]
    loft(builder,rings,mat,[torso_weights(z) for z,*_ in profiles],n=32,fold=.009)


def arm(builder,side,mat,inflate=0,lower=True):
    sign=-1 if side=='L' else 1
    xs=[.205,.238,.289,.325,.344,.362,.373]
    ys=[0,-.003,-.004,-.006,-.019,-.040,-.052]
    zs=[1.451,1.407,1.31,1.215,1.143,1.053,.985]
    radii=[.083,.084,.073,.058,.067,.052,.039]
    depths=[.083,.081,.070,.057,.063,.047,.037]
    wa=wb('upper_arm.'+side);wf=wb('forearm.'+side)
    weights=[wa,wa,wa,mix_weights(wa,wf,.5),wf,wf,wf]
    count=7 if lower else 4
    ellipsoid(builder,(sign*.226,-.001,1.423),(.089+inflate,.087+inflate,.077+inflate),mat,wa,n=24,rows=12)
    tube(builder,[(sign*x,y,z) for x,y,z in zip(xs[:count],ys[:count],zs[:count])],
         [r+inflate for r in radii[:count]],[r+inflate for r in depths[:count]],mat,weights[:count],n=20)


def make_body():
    b=BUILDERS['Body_Base']=MeshBuilder('Body_Base')
    torso(b,'Charcoal cloth',-.008)
    for side in ('L','R'):
        sign=-1 if side=='L' else 1
        arm(b,side,'Charcoal cloth',-.005)
        thigh=wb('thigh.'+side);shin=wb('shin.'+side);foot=wb('foot.'+side)
        rings=[(.13,.046,.057,sign*.113,.009),(.22,.057,.065,sign*.113,.005),
               (.33,.066,.070,sign*.113,.01),(.435,.068,.064,sign*.113,-.002),
               (.52,.064,.064,sign*.113,-.012),(.61,.080,.083,sign*.11,-.006),
               (.755,.09,.1,sign*.103,.005),(.90,.096,.112,sign*.091,.009),
               (.97,.086,.10,sign*.087,.004)]
        weights=[shin,shin,shin,shin,mix_weights(shin,thigh,.5),thigh,thigh,thigh,wb('hips')]
        loft(b,rings,'Charcoal cloth',weights,n=24,fold=.016)
        # Boots: shaped instep, ankle flare and toe box, not cubes.
        loft(b,[(.08,.060,.095,sign*.113,-.053),(.12,.061,.081,sign*.113,-.02),
                (.17,.058,.073,sign*.113,.005),(.28,.068,.078,sign*.113,.007),
                (.37,.077,.083,sign*.113,.005),(.39,.080,.085,sign*.113,.004)],
             'Brown leather',[foot,foot,shin,shin,shin,shin],n=24)
        loft(b,[(.022,.065,.148,sign*.113,-.063),(.045,.067,.15,sign*.113,-.063),
                (.075,.064,.141,sign*.113,-.065),(.108,.058,.115,sign*.113,-.054),
                (.15,.042,.065,sign*.113,-.019)],'Brown leather',foot,n=28)
        loft(b,[(.017,.067,.15,sign*.113,-.063),(.041,.069,.153,sign*.113,-.063)],'Sole',foot,n=28)
        for z in (.23,.345):
            loft(b,[(z-.009,.082,.087,sign*.113,.005),(z+.009,.082,.087,sign*.113,.005)],'Leather edge',shin,n=20)
        # Hands show wrist, palm and curved finger/knuckle articulation at close range.
        hand=wb('hand.'+side)
        tube(b,[(sign*.373,-.052,1.003),(sign*.381,-.063,.969),(sign*.389,-.074,.931),
                (sign*.393,-.081,.905)], [.039,.047,.046,.036],[.036,.036,.034,.025], 'Skin',hand,n=20)
        for i in range(4):
            x=sign*(.36+i*.019)
            tube(b,[(x,-.087,.938),(x,-.105,.918),(x,-.099,.898)],
                 [.011,.0105,.008],[.012,.012,.009],'Skin',hand,n=10)
        tube(b,[(sign*.345,-.067,.965),(sign*.339,-.101,.946),(sign*.352,-.110,.925)],
             [.018,.017,.013],[.018,.017,.013],'Skin',hand,n=12)
    loft(b,[(1.46,.060,.057,0,.0),(1.515,.057,.053,0,.001),(1.565,.054,.053,0,0),(1.61,.061,.059,0,-.002)],
         'Skin',[wb('chest'),wb('neck'),wb('neck'),wb('head')],n=28)
    make_face(b)


def make_face(b):
    h=wb('head')
    # Adult craniofacial profile with narrow chin, angular jaw and broad cheek planes.
    rings=[(1.577,.029,.040,0,-.023),(1.594,.050,.055,0,-.012),
           (1.617,.074,.064,0,-.006),(1.646,.086,.075,0,-.002),
           (1.679,.097,.083,0,.001),(1.709,.100,.085,0,.005),
           (1.748,.098,.083,0,.012),(1.787,.090,.076,0,.016),
           (1.819,.066,.059,0,.017),(1.834,.021,.025,0,.017)]
    loft(b,rings,'Skin',h,n=32)
    # Individual face planes are integrated-looking convex patches, with restrained eyes.
    for sign in (-1,1):
        ex=sign*.045
        eye=[(ex-.020,-.081,1.699),(ex-.009,-.086,1.704),(ex+.007,-.086,1.703),
             (ex+.020,-.080,1.697),(ex+.006,-.085,1.694),(ex-.010,-.086,1.694)]
        b.add(eye,[(0,1,2,3,4,5)],'Eye ivory',h)
        ellipsoid(b,(ex,-.088,1.699),(.0048,.002,.005),'Ink',h,n=12,rows=6)
        ribbon(b,[(ex-.022,-.082,1.701),(ex,-.09,1.708),(ex+.022,-.081,1.70)],
               [.002,.003,.002],'Skin shadow',h,.001)
        ribbon(b,[(sign*.017,-.090,1.72),(sign*.044,-.088,1.724),(sign*.075,-.073,1.716)],
               [.004,.007,.003],'Hair',h,.002)
        ellipsoid(b,(sign*.100,.003,1.682),(.017,.026,.039),'Skin',h,n=16,rows=10)
        ellipsoid(b,(sign*.111,-.014,1.681),(.005,.011,.023),'Skin shadow',h,n=12,rows=8)
    # Sculpted bridge / alar nose, with a small warm underside instead of black holes.
    b.add([(-.013,-.081,1.722),(.013,-.081,1.722),(-.014,-.105,1.669),(.014,-.105,1.669),
           (0,-.119,1.662),(-.021,-.091,1.654),(.021,-.091,1.654),(0,-.085,1.648)],
          [(0,2,4),(0,4,1),(1,4,3),(2,5,4),(4,6,3),(5,7,6,4)],'Skin',h)
    ribbon(b,[(-.027,-.070,1.632),(-.012,-.080,1.636),(0,-.082,1.633),(.012,-.080,1.636),(.027,-.070,1.632)],
           [.004,.006,.004,.006,.003],'Lips',h,.003)
    ribbon(b,[(-.020,-.071,1.629),(0,-.080,1.626),(.020,-.071,1.629)],
           [.003,.004,.003],'Skin shadow',h,.002)


def cuff(b,side,z0,z1,mat,width=.068):
    sign=-1 if side=='L' else 1
    def centre(z):
        t=(1.215-z)/.23
        return (sign*(.325+.048*t),-.006-.046*t,z)
    tube(b,[centre(z0),centre((z0+z1)/2),centre(z1)],
         [width,width*.96,width*.86],[width*.94,width*.92,width*.84],mat,wb('forearm.'+side),n=20)


def panel(b,sign,mat,hem,front=True,width=.165,flare=.05):
    # Each hanging panel has curved cloth cross-sections and blended hip/coat weights.
    verts=[];weights=[];uv=[]
    for row,z in enumerate((1.02,.925,.79,hem)):
        t=row/3
        centre=sign*(.092+t*flare)
        for i in range(7):
            u=i/6-.5
            y=(-.118 if front else .111)+(t*.007)
            y+=(-1 if front else 1)*(.024*(1-4*u*u)+.008*math.cos(u*4*PI))
            verts.append((centre+u*width*(1+.22*t),y,z+.017*math.cos(u*2*PI)*t))
            weights.append(mix_weights(wb('hips'),wb('coat.'+('L' if sign<0 else 'R')),t*.86))
            uv.append((i/6,t))
    faces=[]
    for j in range(3):
        for i in range(6):
            f=(j*7+i,j*7+i+1,(j+1)*7+i+1,(j+1)*7+i)
            faces.append(f if front else tuple(reversed(f)))
    b.add(verts,faces,mat,weights,uv)
    # Close the edge with a narrow embroidered line rather than solid slab panels.
    for edge in (0,6):
        pts=[verts[j*7+edge] for j in range(4)]
        tube(b,pts,[.006]*4,[.004]*4,'Old gold', [weights[j*7+edge] for j in range(4)],n=6)


def chest_lapel(b,points,widths,mat):
    ribbon(b,points,widths,mat,[torso_weights(p[2]) for p in points],thickness=.008)


def make_wayfarer():
    b=BUILDERS['Gear_Wayfarer']=MeshBuilder('Gear_Wayfarer')
    torso(b,'Teal cloth',.006)
    loft(b,[(1.468,.086,.072,0,.002),(1.501,.072,.065,0,.002),(1.535,.065,.061,0,.003)],'Ivory cloth',wb('chest'),n=28)
    loft(b,[(1.483,.079,.071,0,.003),(1.518,.071,.066,0,.003)],'Teal fold',wb('chest'),n=28)
    for side in ('L','R'):
        arm(b,side,'Teal cloth',.008)
        cuff(b,side,1.205,1.025,'Brown leather',.086)
        cuff(b,side,1.048,1.027,'Old gold',.078)
        cuff(b,side,1.193,1.178,'Steel shadow',.090)
        sign=-1 if side=='L' else 1
        for front in (True,False):
            panel(b,sign,'Teal cloth' if front else 'Teal fold',.605 if front else .66,front=front,width=.17,flare=.07)
        panel(b,sign,'Ivory cloth',.65,front=True,width=.067,flare=.01)
    chest_lapel(b,[(-.07,-.075,1.474),(-.105,-.123,1.407),(-.053,-.144,1.312),(.004,-.138,1.211),(.042,-.109,1.116)],
                [.071,.070,.065,.058,.042],'Ivory cloth')
    chest_lapel(b,[(.073,-.080,1.471),(.071,-.128,1.415),(.043,-.146,1.345),(-.005,-.143,1.26),(-.063,-.111,1.121)],
                [.053,.057,.054,.048,.035],'Teal fold')
    chest_lapel(b,[(.061,-.091,1.475),(.052,-.138,1.41),(.023,-.153,1.34),(-.023,-.150,1.255),(-.079,-.119,1.12)],
                [.008,.009,.009,.008,.007],'Old gold')
    # A curved, asymmetric shoulder shell reads as forged protection, not a block.
    shoulder_shell(b,-1,'Armor blue',large=False)
    # Tailored abdomen folds follow the ribcage/waist transition.
    for sign in (-1,1):
        for i in range(2):
            chest_lapel(b,[(sign*(.12+i*.027),-.113,1.12),(sign*(.155+i*.024),-.114,1.22),
                           (sign*(.169+i*.023),-.108,1.30)], [.005,.008,.003],'Teal seam')
    belt(b,'Brown leather','Old gold')
    ribbon(b,[(-.157,-.112,1.041),(-.202,-.134,.953),(-.22,-.149,.795),(-.27,-.142,.71)],
           [.05,.06,.052,.018],'Cinnabar',[wb('hips'),wb('hips'),wb('coat.L'),wb('coat.L')],.008)
    # Thin lacquered scabbard hangs behind the left hip and cannot cross the saber.
    tube(b,[(-.177,.092,1.04),(-.215,.113,.91),(-.288,.145,.65),(-.318,.154,.55)],
         [.027,.029,.025,.012],[.026,.024,.020,.014],'Teal fold',wb('hips'),n=14)
    for x,y,z in ((-.189,.098,.998),(-.291,.146,.635)):
        tube(b,[(x,y,z+.015),(x-.008,y+.003,z-.014)],[.032,.031],[.029,.029],'Old gold',wb('hips'),n=14)


def belt(b,base,metal):
    loft(b,[(1.016,.179,.124,0,.0),(1.074,.17,.113,0,0)],base,[wb('hips'),torso_weights(1.074)],n=32)
    # Raised octagonal buckle with restrained inset jade.
    ellipsoid(b,(0,-.131,1.046),(.045,.013,.035),metal,wb('hips'),n=8,rows=6)
    ellipsoid(b,(0,-.145,1.048),(.023,.005,.019),'Jade enamel',wb('hips'),n=8,rows=6)


def shoulder_shell(b,sign,mat,large=False):
    side='L' if sign<0 else 'R';w=wb('upper_arm.'+side)
    # Curved elliptical plate segments arch over the deltoid.
    layers=3 if large else 2
    for layer in range(layers):
        # Rigid-looking plate stacks slide with the shoulder without flipping upright.
        if large:
            w=mix_weights(wb('clavicle.'+side),wb('upper_arm.'+side),(.12,.25,.40)[layer])
        cx=sign*(.224+layer*.028)
        z=1.475-layer*.045
        rx=.125 if large else .104
        ry=.125 if large else .108
        verts=[]
        for j in range(4):
            latitude=.18+(j/3)*1.35
            for i in range(13):
                a=2*PI*i/12
                verts.append((cx+rx*math.sin(latitude)*math.cos(a),ry*math.sin(latitude)*math.sin(a),z+.047*math.cos(latitude)))
        faces=[]
        for j in range(3):
            for i in range(12): faces.append((j*13+i,(j+1)*13+i,(j+1)*13+i+1,j*13+i+1))
        faces.append(tuple(range(12)))
        b.add(verts,faces,mat,w)
        rim=verts[-13:]
        tube(b,rim,[.007]*13,[.005]*13,'Old gold',w,n=6)
    if large:
        # A low gold ridge reinforces scale without fantasy spikes.
        ribbon(b,[(sign*.225,-.02,1.53),(sign*.29,-.015,1.487),(sign*.34,-.01,1.412)],
               [.022,.023,.012],'Gold light',[mix_weights(wb('clavicle.'+side),wb('upper_arm.'+side),a) for a in (.12,.25,.40)],.006)


def make_warden():
    b=BUILDERS['Gear_Warden']=MeshBuilder('Gear_Warden')
    torso(b,'Charcoal leather',.012)
    loft(b,[(1.465,.090,.074,0,.003),(1.516,.076,.067,0,.003),(1.535,.071,.064,0,.003)],'Charcoal cloth',wb('chest'),n=28)
    loft(b,[(1.508,.079,.07,0,.003),(1.522,.077,.07,0,.003)],'Old gold',wb('chest'),n=28)
    for side in ('L','R'):
        sign=-1 if side=='L' else 1
        arm(b,side,'Charcoal cloth',.005)
        shoulder_shell(b,sign,'Armor charcoal',large=True)
        cuff(b,side,1.212,1.016,'Armor charcoal',.086)
        for z in (1.18,1.095,1.045):
            cuff(b,side,z+.008,z-.008,'Old gold',.091 if z>1.16 else .081)
        # Steel shin plates continue the warden silhouette below the short war skirt.
        loft(b,[(.145,.066,.082,sign*.113,-.005),(.27,.080,.090,sign*.113,0),
                (.405,.085,.09,sign*.113,-.004),(.445,.073,.081,sign*.113,-.005)],
             'Armor charcoal',wb('shin.'+side),n=20)
        ribbon(b,[(sign*.113,-.091,.16),(sign*.113,-.098,.30),(sign*.113,-.091,.437)],
               [.015,.02,.016],'Old gold',wb('shin.'+side),.003)
        knee=[(sign*.113-.046,-.080,.551),(sign*.113,-.091,.57),(sign*.113+.046,-.080,.551),
              (sign*.113+.063,-.087,.51),(sign*.113+.041,-.088,.473),(sign*.113,-.091,.452),
              (sign*.113-.041,-.088,.473),(sign*.113-.063,-.087,.51),(sign*.113,-.111,.516)]
        b.add(knee,[(i,(i+1)%8,8) for i in range(8)],'Armor blue',mix_weights(wb('thigh.'+side),wb('shin.'+side),.5))
        for front in (True,False):
            panel(b,sign,'Cinnabar',.70,front=front,width=.20,flare=.05)
    # Six rows of individually shaped, overlapping lames follow the torso surface.
    for row in range(6):
        z=1.135+row*.050
        rx=[.184,.194,.212,.230,.244,.255][row]
        ry=[.135,.145,.155,.164,.163,.158][row]
        for col in range(14):
            a=2*PI*col/14
            width=(2*PI/14)*.80
            verts=[]
            for zz in (z-.032,z+.039):
                for aa in (a-width*.5,a,a+width*.5):
                    bulge=.006 if aa==a else 0
                    verts.append(((rx+bulge)*math.cos(aa),(ry+bulge)*math.sin(aa),zz))
            b.add(verts,[(0,1,4,3),(1,2,5,4)],'Armor charcoal' if (row+col)%3 else 'Armor blue',torso_weights(z))
            if col in (8,9,10,11,12):
                # Small paired rivets are geometry; visually subtle at play scale.
                for aa in (a-width*.28,a+width*.28):
                    ellipsoid(b,((rx+.009)*math.cos(aa),(ry+.009)*math.sin(aa),z+.026),
                              (.006,.005,.006),'Old gold',torso_weights(z),n=8,rows=4)
    for sign in (-1,1):
        chest_lapel(b,[(sign*.076,-.080,1.49),(sign*.124,-.121,1.435),(sign*.198,-.100,1.40)],
                    [.032,.037,.020],'Old gold')
    # Four plated tassets flare sideways, unlike the travel coat's long cloth split.
    for sign in (-1,1):
        for front in (True,False):
            for row in range(3):
                z=1.00-row*.077
                y=-.149 if front else .144
                x=sign*(.092+row*.016)
                pts=[(x-sign*.084,y+.023,z),(x,y-.008 if front else y+.008,z-.010),(x+sign*.084,y+.022,z-.006)]
                tube(b,pts,[.041,.045,.037],[.009,.010,.009],'Armor charcoal',wb('coat.'+('L' if sign<0 else 'R')),n=10)
                tube(b,[(p[0],p[1]-.006,p[2]-.029) for p in pts],[.005]*3,[.004]*3,'Old gold',wb('coat.'+('L' if sign<0 else 'R')),n=6)
    belt(b,'Cinnabar','Gold light')


def hair_cap(b,full=True):
    h=wb('head')
    verts=[]
    n=32
    for j in range(9):
        t=j/8
        for i in range(n):
            a=2*PI*i/n
            # Forehead hairline high, back cap naturally lower.
            front=max(0,-math.sin(a))
            boundary_z=1.678+.074*front
            lat_start=math.asin((boundary_z-1.736)/.111)
            lat=lat_start+(PI/2-lat_start)*t
            sweep=.01*math.sin(a)*math.sin(t*PI)
            verts.append((.117*math.cos(lat)*math.cos(a)+sweep,.017+.100*math.cos(lat)*math.sin(a),1.736+.111*math.sin(lat)))
    faces=[]
    for j in range(8):
        for i in range(n): faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    b.add(verts,faces,'Hair',h)
    if full:
        for sign in (-1,1):
            ribbon(b,[(sign*.096,-.009,1.748),(sign*.100,-.026,1.704),(sign*.092,-.021,1.665)],
                   [.023,.019,.010],'Hair',h,.009)


def make_heads():
    b=BUILDERS['Head_Topknot']=MeshBuilder('Head_Topknot')
    hair_cap(b)
    h=wb('head')
    ellipsoid(b,(0,.059,1.88),(.042,.042,.065),'Hair',h,n=24,rows=12)
    loft(b,[(1.855,.046,.04,0,.055),(1.877,.045,.04,0,.057)],'Old gold',h,n=24)
    tube(b,[(-.082,.054,1.875),(.080,.060,1.878)],[.006,.006],[.006,.006],'Jade enamel',h,n=10)
    ribbon(b,[(-.028,.087,1.878),(-.045,.101,1.805),(-.027,.107,1.724)],
           [.022,.021,.009],'Teal fold',h,.004)
    b=BUILDERS['Head_Warden']=MeshBuilder('Head_Warden')
    # Dome, brow visor, cheek guards and short ridged crest change the head silhouette.
    hair_cap(b,False)
    loft(b,[(1.723,.111,.097,0,.015),(1.77,.115,.098,0,.013),
            (1.816,.097,.086,0,.016),(1.849,.061,.059,0,.018),(1.866,.009,.012,0,.021)],
         'Armor charcoal',h,n=32)
    # Open-faced brow, not a face-hiding bucket.
    tube(b,[(-.115,-.001,1.745),(-.087,-.068,1.751),(0,-.089,1.749),(.087,-.068,1.751),(.115,-.001,1.745)],
         [.009,.010,.012,.010,.009],[.007]*5,'Old gold',h,n=8)
    for sign in (-1,1):
        ribbon(b,[(sign*.107,-.018,1.752),(sign*.108,-.035,1.693),(sign*.088,-.025,1.642)],
               [.051,.046,.024],'Armor blue',h,.012)
        tube(b,[(sign*.121,-.035,1.742),(sign*.124,-.046,1.693),(sign*.099,-.032,1.646)],
             [.005]*3,[.004]*3,'Old gold',h,n=6)
    for i in range(5):
        x=(i-2)*.035
        ribbon(b,[(x,.104,1.741),(x,.113,1.679),(x,.100,1.63)],
               [.036,.038,.035],'Armor charcoal',h,.006)
    # Forged swept spine rather than horns or toy plumes.
    ribbon(b,[(0,-.065,1.787),(0,-.026,1.867),(0,.035,1.926),(0,.082,1.871),(0,.096,1.815)],
           [.018,.023,.018,.016,.009],'Gold light',h,.012)


def weapon_transform(point,hand=(.385,-.092,.945),angle=.35):
    # Weapon has its own broadside toward the camera; diagonal outside the body.
    return Vector(hand)+Matrix.Rotation(angle,3,'Y')@Vector(point)


def weapon_tube(b,points,widths,depths,mat,angle=.35,n=16):
    tube(b,[weapon_transform(p,angle=angle) for p in points],widths,depths,mat,wb('hand.R'),n=n)


def blade(b,profiles,mat,angle=.35):
    # Diamond cross-section blade with explicit brighter sharpened edge faces.
    vertices=[]
    for x,z,width,thick in profiles:
        vertices += [weapon_transform((x-width,0,z),angle=angle),weapon_transform((x,-thick,z),angle=angle),
                     weapon_transform((x+width,0,z),angle=angle),weapon_transform((x,thick,z),angle=angle)]
    faces=[];mats=[]
    for j in range(len(profiles)-1):
        for i in range(4):
            faces.append((j*4+i,j*4+(i+1)%4,(j+1)*4+(i+1)%4,(j+1)*4+i))
            mats.append('Blade edge' if i in (1,2) else mat)
    faces += [(0,3,2,1),tuple((len(profiles)-1)*4+i for i in (0,1,2,3))]
    mats += [mat,mat]
    blade_uv=[(u,j/(len(profiles)-1)) for j in range(len(profiles)) for u in (0,.5,1,.5)]
    b.add(vertices,faces,mats,wb('hand.R'),blade_uv)


def make_weapons():
    b=BUILDERS['Weapon_Saber']=MeshBuilder('Weapon_Saber')
    weapon_tube(b,[(0,0,-.105),(0,0,.110)],[.024,.024],[.027,.027],'Brown leather')
    for z in (-.09,-.06,-.03,0,.03,.06,.09):
        weapon_tube(b,[(0,0,z-.005),(0,0,z+.005)],[.026,.026],[.028,.028],'Ivory fold',n=12)
    weapon_tube(b,[(-.114,0,.106),(-.068,0,.133),(0,0,.137),(.07,0,.117),(.113,0,.096)],
                [.012]*5,[.030,.033,.034,.03,.020],'Old gold',n=12)
    blade(b,[(0,.151,.038,.010),(.001,.31,.043,.013),(.014,.50,.046,.013),
             (.046,.68,.042,.012),(.10,.84,.029,.009),(.157,.936,.0,.001)],'Steel')
    weapon_tube(b,[(-.018,-.014,.18),(-.012,-.016,.40),(.014,-.016,.62),(.062,-.012,.78)],
                [.004]*4,[.002]*4,'Steel shadow',n=6)
    weapon_tube(b,[(0,0,-.127),(0,0,-.112)],[.031,.033],[.034,.034],'Old gold',n=12)
    b=BUILDERS['Weapon_Glaive']=MeshBuilder('Weapon_Glaive')
    angle=.25
    weapon_tube(b,[(0,0,-.79),(0,0,.74)],[.018,.022],[.018,.022],'Weapon wood',angle)
    weapon_tube(b,[(0,0,-.80),(0,0,-.70)],[.027,.025],[.027,.025],'Steel',angle)
    for z in (-.12,-.04,.04,.12,.66,.71):
        weapon_tube(b,[(0,0,z-.018),(0,0,z+.018)],[.028,.028],[.028,.028],'Old gold' if z>.5 else 'Charcoal leather',angle)
    blade(b,[(-.002,.73,.053,.018),(.018,.84,.09,.021),(.056,1.015,.100,.019),
             (.094,1.155,.081,.016),(.153,1.32,.0,.002)],'Steel',angle)
    # Hooked heel and pierced-looking inset give the polearm a different silhouette.
    blade(b,[(-.046,.81,.019,.012),(-.132,.895,.043,.014),(-.171,1.00,0,.001)],'Steel shadow',angle)
    weapon_tube(b,[(0,-.02,.73),(.019,-.025,.85),(.046,-.022,.98)],
                [.010,.008,.004],[.004]*3,'Old gold',angle,n=8)
    for sign in (-1,1):
        pts=[weapon_transform((sign*.034,.015,.74),angle=angle),weapon_transform((sign*.078,.027,.64),angle=angle),
             weapon_transform((sign*.093,.04,.49),angle=angle)]
        ribbon(b,pts,[.024,.026,.008],'Cinnabar',wb('hand.R'),.004)


def set_world_rotation(name,angles):
    pb=RIG.pose.bones[name]
    rest=pb.bone.matrix_local.to_quaternion()
    q=Euler(angles,'XYZ').to_quaternion()
    pb.rotation_quaternion=rest.inverted()@q@rest


def set_world_translation(name,xyz):
    pb=RIG.pose.bones[name]
    pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector(xyz)



def orient_hand_world(side,delta):
    bpy.context.view_layer.update()
    hand=RIG.pose.bones['hand.'+side]
    rest=hand.bone.matrix_local.to_quaternion()
    hand.matrix=Matrix.Translation(hand.head)@(delta@rest).to_matrix().to_4x4()
    bpy.context.view_layer.update()


def solve_arm(side,wrist,hand_delta,bend_hint):
    """Analytic two-bone FK bake; no runtime constraint/IK dependency."""
    bpy.context.view_layer.update()
    upper=RIG.pose.bones['upper_arm.'+side]
    fore=RIG.pose.bones['forearm.'+side]
    shoulder=upper.head.copy()
    l1=(BONES[upper.name][1]-BONES[upper.name][0]).length
    l2=(BONES[fore.name][1]-BONES[fore.name][0]).length
    direction=Vector(wrist)-shoulder
    distance=min(direction.length,l1+l2-.001)
    distance=max(distance,abs(l1-l2)+.001)
    axis=direction.normalized()
    wrist=shoulder+axis*distance
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    offset=math.sqrt(max(0,l1*l1-along*along))
    bend=Vector(bend_hint)-axis*Vector(bend_hint).dot(axis)
    bend.normalize()
    elbow=shoulder+axis*along+bend*offset
    for pb,a,b in ((upper,shoulder,elbow),(fore,elbow,wrist)):
        rest_dir=(BONES[pb.name][1]-BONES[pb.name][0]).normalized()
        q=rest_dir.rotation_difference((b-a).normalized())@pb.bone.matrix_local.to_quaternion()
        pb.matrix=Matrix.Translation(a)@q.to_matrix().to_4x4()
        bpy.context.view_layer.update()
    orient_hand_world(side,hand_delta)
    return wrist

def animate():
    scene=bpy.context.scene
    scene.render.fps=24
    RIG.animation_data_create()
    clips=[('idle',48),('walk',32),('run',24),('attack',18),('attack_glaive',18),('jump',34)]
    for clip,length in clips:
        action=bpy.data.actions.new(clip)
        action['clip_name']=clip
        action['loop']=clip in ('idle','walk','run')
        RIG.animation_data.action=action
        grip_errors=[]
        frames=list(range(1,length+2,2))
        if length+1 not in frames:frames.append(length+1)
        for frame in frames:
            t=(frame-1)/length
            p=t*2*PI
            for pb in RIG.pose.bones:
                pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
            if clip=='idle':
                set_world_rotation('spine',(.009*math.sin(p),0,.010*math.sin(p)))
                set_world_rotation('chest',(.012*math.sin(p),0,-.007*math.sin(p)))
                set_world_rotation('head',(0,0,.017*math.sin(p)))
                for sign,side in ((-1,'L'),(1,'R')):
                    set_world_rotation('forearm.'+side,(.04+.012*math.sin(p+sign),0,0))
                    set_world_rotation('coat.'+side,(.017*math.sin(p+sign),0,sign*.012*math.sin(p)))
            elif clip in ('walk','run'):
                running=clip=='run'
                stride=.68 if running else .40
                set_world_translation('hips',(0,0,(.037 if running else .021)*(1-math.cos(2*p))))
                set_world_rotation('hips',(.055 if running else .02,0,.065*math.sin(p)))
                set_world_rotation('spine',(.05 if running else 0,0,-.07*math.sin(p)))
                set_world_rotation('chest',(.045 if running else 0,0,-.05*math.sin(p)))
                for sign,side in ((1,'L'),(-1,'R')):
                    q=p+(0 if sign==1 else PI)
                    set_world_rotation('thigh.'+side,(-stride*math.sin(q),0,0))
                    set_world_rotation('shin.'+side,(max(0,math.sin(q))*(1.0 if running else .63)+.065,0,0))
                    set_world_rotation('foot.'+side,(-max(0,math.sin(q))*.24,0,0))
                    set_world_rotation('upper_arm.'+side,(stride*.56*math.sin(q),0,sign*.035))
                    set_world_rotation('forearm.'+side,(-.20-(.23 if running else .12)*max(0,-math.sin(q)),0,0))
                    set_world_rotation('coat.'+side,(-stride*.75*math.sin(q)-.08,0,sign*.06))
                set_world_rotation('head',(-.045 if running else 0,0,0))
            elif clip in ('attack','attack_glaive'):
                # Anticipation -> decisive outside-to-inside cut -> recover.
                keys=[(0,0),(.23,-.42),(.34,-.5),(.54,.76),(.66,.6),(1,0)]
                def curve(keys):
                    for (ta,va),(tb,vb) in zip(keys,keys[1:]):
                        if ta<=t<=tb:
                            k=(t-ta)/(tb-ta); k=k*k*(3-2*k)
                            return va+(vb-va)*k
                    return keys[-1][1]
                twist=curve(keys)
                arm_x=curve([(0,0),(.26,-.72),(.37,-.88),(.55,-1.34),(.70,-.98),(1,0)])
                arm_y=curve([(0,0),(.30,-.32),(.55,.24),(.7,.30),(1,0)])
                bend=curve([(0,0),(.27,-1.03),(.37,-.94),(.54,-.075),(.70,-.16),(1,0)])
                set_world_rotation('hips',(0,0,twist*.30))
                set_world_rotation('spine',(.025,0,twist*.36))
                set_world_rotation('chest',(0,0,twist*.34))
                set_world_rotation('upper_arm.R',(arm_x,arm_y,0))
                set_world_rotation('forearm.R',(bend,0,0))
                set_world_rotation('hand.R',(0,-twist*.25,0))
                set_world_rotation('upper_arm.L',(-arm_x*.28,-arm_y*.2,0))
                set_world_rotation('forearm.L',(-abs(bend)*.5,0,0))
                set_world_rotation('thigh.L',(-abs(twist)*.24,0,0))
                set_world_rotation('shin.L',(abs(twist)*.32,0,0))
                set_world_rotation('coat.L',(-.04,0,-twist*.22))
                set_world_rotation('coat.R',(-.04,0,-twist*.22))
                def vector_curve(keys):
                    return Vector([curve([(time,value[i]) for time,value in keys]) for i in range(3)])
                if clip=='attack':
                    direction=vector_curve([(0,(.343,0,.939)),(.29,(-.14,.20,.97)),(.38,(-.17,.18,.96)),
                                            (.55,(-.38,-.80,.47)),(.70,(-.62,-.64,.45)),(1,(.343,0,.939))]).normalized()
                    delta=Vector((math.sin(.35),0,math.cos(.35))).rotation_difference(direction)
                    orient_hand_world('R',delta)
                else:
                    # Lead hand genuinely contacts the same rigid shaft, using baked two-bone IK.
                    grip=vector_curve([(0,(.385,-.092,.945)),(.28,(.20,-.16,1.30)),(.36,(.20,-.16,1.30)),
                                       (.55,(.125,-.245,1.295)),(.73,(.20,-.24,1.24)),(1,(.385,-.092,.945))])
                    axis=vector_curve([(0,(.247,0,.969)),(.28,(.10,.10,.99)),(.36,(.10,.10,.99)),
                                       (.55,(-.30,-.87,-.18)),(.73,(.14,-.48,.86)),(1,(.247,0,.969))]).normalized()
                    delta=Vector((math.sin(.25),0,math.cos(.25))).rotation_difference(axis)
                    roll=curve([(0,0),(.30,-.08),(.55,.34),(.73,.16),(1,0)])
                    delta=Quaternion(axis,roll)@delta
                    right_offset=Vector((.012,-.04,-.04))
                    solve_arm('R',grip-delta@right_offset,delta,(1,-.3,-.3))
                    bpy.context.view_layer.update()
                    right_hand=RIG.pose.bones['hand.R']
                    right_rest=right_hand.bone.matrix_local.to_quaternion()
                    actual_delta=right_hand.matrix.to_quaternion()@right_rest.inverted()
                    actual_grip=right_hand.head+actual_delta@right_offset
                    shaft_target=actual_grip+axis*.30
                    support=curve([(0,0),(.12,0),(.27,1),(.64,1),(.90,0),(1,0)])
                    left=RIG.pose.bones['hand.L']
                    left_offset=Vector((-.012,-.04,-.04))
                    left_rest=left.bone.matrix_local.to_quaternion()
                    old_delta=left.matrix.to_quaternion()@left_rest.inverted()
                    left_grip=left.head+old_delta@left_offset
                    support_delta=old_delta.slerp(delta,support)
                    support_target=left_grip.lerp(shaft_target,support)
                    solve_arm('L',support_target-support_delta@left_offset,support_delta,(-1,-.7,-.1))
                    bpy.context.view_layer.update()
                    actual_left=RIG.pose.bones['hand.L']
                    left_grip=actual_left.head+(actual_left.matrix.to_quaternion()@left_rest.inverted())@left_offset
                    if support>.999:grip_errors.append((left_grip-shaft_target).length)
                if t<1e-6 or t>1-1e-6:
                    for pb in RIG.pose.bones:
                        pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
            elif clip=='jump':
                # Root motion remains zero; gameplay owns trajectory. Deformation owns crouch/tuck.
                crouch=max(0,math.sin(min(t/.22,1)*PI))*.32 if t<.22 else max(0,math.sin((t-.77)/.23*PI))*.25 if t>.77 else 0
                tuck=math.sin(max(0,min(1,(t-.20)/.60))*PI)*.75
                set_world_translation('hips',(0,0,-crouch*.20))
                set_world_rotation('spine',(.12*tuck,0,0))
                for sign,side in ((-1,'L'),(1,'R')):
                    set_world_rotation('thigh.'+side,(-crouch-tuck*(.73 if side=='L' else .40),0,sign*.05*tuck))
                    set_world_rotation('shin.'+side,(crouch*1.5+tuck*.85,0,0))
                    set_world_rotation('foot.'+side,(-crouch*.6-.2*tuck,0,0))
                    set_world_rotation('upper_arm.'+side,(-.40*tuck,sign*.17*tuck,0))
                    set_world_rotation('forearm.'+side,(-.23*tuck,0,0))
                    set_world_rotation('coat.'+side,(-.27*tuck,0,sign*.10*tuck))
            mature_pose_adjustment(clip,t)
            for pb in RIG.pose.bones:
                pb.keyframe_insert(data_path='location',frame=frame,group=pb.name)
                pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=pb.name)
                pb.keyframe_insert(data_path='scale',frame=frame,group=pb.name)
        if grip_errors:
            action['maximum_support_grip_error_m']=max(grip_errors)
            print('GLAIVE_SUPPORT_GRIP_ERROR '+str(max(grip_errors)))
            assert max(grip_errors)<.028, 'Glaive supporting hand did not reach shaft'
        for fc in action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
        track=RIG.animation_data.nla_tracks.new()
        track.name=clip
        strip=track.strips.new(clip,1,action)
        strip.name=clip;strip.extrapolation='NOTHING';strip.blend_type='REPLACE'
        track.mute=True
        RIG.animation_data.action=None
    for pb in RIG.pose.bones:
        pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
    ROOT['animation_clips']='idle, walk, run (loop); attack, attack_glaive, jump (one-shot)'


def attachment(name,parent):
    # Proper bone-parent inverse: attachment keeps its authored world rest position.
    ob=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(ob)
    ob.parent=RIG;ob.parent_type='BONE';ob.parent_bone='hand.R'
    bpy.context.view_layer.update()
    ob.matrix_world=Matrix.Translation((.385,-.092,.945))
    ob['visibility_owner']=parent
    ob.empty_display_size=.025
    return ob


def inspect_glb(path):
    raw=path.read_bytes()
    if raw[:4]!=b'glTF':raise RuntimeError('Missing GLB header')
    size,kind=struct.unpack_from('<II',raw,12)
    doc=json.loads(raw[20:20+size])
    names={n.get('name') for n in doc.get('nodes',[])}
    assert set(SCHEMA).issubset(names), 'Export lost a slot node'
    assert 'Body_Base' in names
    assert doc.get('skins'), 'Export lost skin'
    assert len(doc['skins'][0]['joints'])>=20
    assert {a.get('name') for a in doc.get('animations',[])}.issuperset({'idle','walk','run','attack','jump'})
    joints=set(j for s in doc['skins'] for j in s['joints'])
    assert all('inverseBindMatrices' in s for s in doc['skins'])
    for n in doc['nodes']:
        if n.get('name') in SCHEMA or n.get('name')=='Body_Base':
            assert 'skin' in n and 'mesh' in n, 'Mesh is not bound: '+n.get('name','')
            for prim in doc['meshes'][n['mesh']]['primitives']:
                assert 'JOINTS_0' in prim['attributes'] and 'WEIGHTS_0' in prim['attributes']
                assert 'TEXCOORD_0' in prim['attributes']
    # Verify native rest/bind transforms mathematically, not just schema presence.
    parents={child:i for i,node in enumerate(doc['nodes']) for child in node.get('children',[])}
    cache={}
    def global_matrix(i):
        if i in cache:return cache[i]
        n=doc['nodes'][i]
        if 'matrix' in n:
            local=Matrix([n['matrix'][j::4] for j in range(4)])
        else:
            q=n.get('rotation',[0,0,0,1])
            local=Matrix.Translation(n.get('translation',[0,0,0])) @ Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4()
            local=local @ Matrix.Diagonal((*n.get('scale',[1,1,1]),1))
        cache[i]=(global_matrix(parents[i]) if i in parents else Matrix.Identity(4))@local
        return cache[i]
    max_bind_error=0
    binary_start=28+size
    for skin in doc['skins']:
        accessor=doc['accessors'][skin['inverseBindMatrices']]
        view=doc['bufferViews'][accessor['bufferView']]
        start=binary_start+view.get('byteOffset',0)+accessor.get('byteOffset',0)
        for k,joint in enumerate(skin['joints']):
            values=struct.unpack_from('<16f',raw,start+k*64)
            bind=Matrix([values[j::4] for j in range(4)])
            product=global_matrix(joint)@bind
            error=max(abs(product[r][c]-(1 if r==c else 0)) for r in range(4) for c in range(4))
            max_bind_error=max(max_bind_error,error)
    assert max_bind_error<1e-4, 'Invalid native inverse bind matrices: '+str(max_bind_error)
    report={'file':str(path),'skins':len(doc['skins']),'joints':len(joints),
            'max_bind_identity_error':max_bind_error,
            'meshes':len(doc.get('meshes',[])),'materials':len(doc.get('materials',[])),
            'animations':{a['name']:len(a['channels']) for a in doc['animations']},
            'nodes':[n.get('name') for n in doc['nodes'] if n.get('name') in SCHEMA or n.get('name')=='Body_Base'],
            'bytes':len(raw)}
    print('HERO_CONTRACT '+json.dumps(report))
    return report


def preview_setup(objects,output,render=False):
    # Authoring preview only; camera, studio floor and lights are never exported.
    for name,ob in objects.items():
        ob.hide_render=name in ('Gear_Warden','Head_Warden','Weapon_Glaive')
        ob.hide_set(ob.hide_render)
    scene=bpy.context.scene
    scene.world.color=(.16,.16,.16)
    scene.render.engine='CYCLES'
    scene.cycles.samples=16
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.cycles.use_denoising=False  # Distribution build has no OpenImageDenoise
    scene.render.resolution_x=900;scene.render.resolution_y=1000
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    def area(name,loc,power,size):
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.location=loc
        ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
    area('Studio key',(3,-4,5),550,4)
    area('Studio fill',(-3,-2,3),260,3)
    area('Studio rim',(1,3,4),650,3)
    cam_data=bpy.data.cameras.new('Authoring camera');cam=bpy.data.objects.new('Authoring camera',cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location=(3.0,-5.0,3.1);target=Vector((.12,0,1.06))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam_data.type='ORTHO';cam_data.ortho_scale=2.85
    scene.camera=cam
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(output/'builds'/'jadebound-modular-wayfarer.png')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'art/jadebound_modular_hero.blend'))
    if render:
        bpy.ops.render.render(write_still=True)
        def pose_preview(clip,filename):
            RIG.animation_data.action=bpy.data.actions[clip]
            scene.frame_set(11)
            bpy.context.view_layer.update()
            scene.render.filepath=str(output/'builds'/filename)
            bpy.ops.render.render(write_still=True)
            RIG.animation_data.action=None
            for pb in RIG.pose.bones:
                pb.location=(0,0,0);pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
            scene.frame_set(1)
            bpy.context.view_layer.update()
        pose_preview('attack','jadebound-modular-wayfarer-attack.png')
        for name,ob in objects.items():
            ob.hide_render=name in ('Gear_Wayfarer','Head_Topknot','Weapon_Saber')
            ob.hide_set(ob.hide_render)
        scene.render.filepath=str(output/'builds'/'jadebound-modular-warden.png')
        bpy.ops.render.render(write_still=True)
        pose_preview('attack_glaive','jadebound-modular-warden-attack.png')
        for name,ob in objects.items():
            ob.hide_render=name in ('Gear_Warden','Head_Warden','Weapon_Glaive')
            ob.hide_set(ob.hide_render)



def stabilize_saved_image_names(output):
    """Naming-only migration. Never re-export meshes, clips or image pixels."""
    blend=output/'art/jadebound_modular_hero.blend'
    path=output/'game/assets/models/hero_modular.glb'
    raw=path.read_bytes()
    assert raw[:4]==b'glTF'
    size,kind=struct.unpack_from('<II',raw,12)
    assert kind==0x4e4f534a
    doc=json.loads(raw[20:20+size])
    original_doc=json.loads(json.dumps(doc))
    names={}
    def assign(texture_info,label):
        if not texture_info:return
        image_index=doc['textures'][texture_info['index']]['source']
        name=stable_image_name(label)
        assert image_index not in names or names[image_index]==name, 'Shared image has conflicting semantic names'
        names[image_index]=name
    for material in doc['materials']:
        pbr=material.get('pbrMetallicRoughness',{})
        label=material['name']
        kind='metal' if pbr.get('metallicFactor',1)>.5 else ('cloth' if 'cloth' in label or 'fold' in label or label=='Cinnabar' else 'leather')
        assign(pbr.get('baseColorTexture'),label+' albedo')
        assign(material.get('normalTexture'),kind+' normal')
        assign(pbr.get('metallicRoughnessTexture'),kind+' roughness')
    assert len(names)==len(doc['images']), 'Unmapped embedded image'
    for i,image in enumerate(doc['images']):
        assert 'bufferView' in image and 'uri' not in image
        image['name']=names[i]
    comparison=json.loads(json.dumps(doc))
    for image,original in zip(comparison['images'],original_doc['images']):
        image['name']=original['name']
    assert comparison==original_doc, 'Unexpected glTF structural change'
    payload=json.dumps(doc,separators=(',',':')).encode('utf8')
    payload+=b' '*((-len(payload))%4)
    unchanged_binary_chunks=raw[20+size:]
    migrated=struct.pack('<4sII',b'glTF',2,20+len(payload)+len(unchanged_binary_chunks))
    migrated+=struct.pack('<II',len(payload),0x4e4f534a)+payload+unchanged_binary_chunks
    assert migrated[20+len(payload):]==unchanged_binary_chunks
    binary_hash=hashlib.sha256(unchanged_binary_chunks).hexdigest()
    # Apply matching packed-image datablock names without regenerating any scene content.
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    renamed=[]
    for image in bpy.data.images:
        if image.packed_file is None:continue
        before=hashlib.sha256(image.packed_file.data).hexdigest()
        image.name=stable_image_name(image.name) if not image.name.startswith('jb_') else image.name
        image.filepath_raw=''
        assert hashlib.sha256(image.packed_file.data).hexdigest()==before
        renamed.append(image.name)
    assert set(renamed)==set(names.values()), 'Blend/GLB image names disagree'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    path.write_bytes(migrated)
    report=inspect_glb(path)
    print('STABLE_IMAGE_NAMES '+json.dumps({'image_names':sorted(renamed),'unchanged_binary_chunks_sha256':binary_hash,'bytes':len(migrated)}))
# === MATURE WARDEN FORM PASS: original anatomy, construction and regional atlases ===
# Baseline source is preserved at git c16cb4b. Runtime rig and slot names are stable.
ATLAS_SIZE=1024
ATLAS_MATS={'cloth':'Warden tailored cloth','metal':'Warden forged steel','leather':'Warden worn leather'}
FOLD_RECIPES={
    0:[(.22,.38,.27,.045,.21,-.0045),(.73,-.30,.34,.036,.22,-.0038),(.15,-.38,.79,.045,.17,-.004),(.84,.34,.81,.040,.17,-.0045)],
    1:[(.28,.24,.30,.06,.3,-.003),(.69,-.20,.42,.05,.3,-.0035),(.5,.04,.74,.04,.20,.002)],
    2:[(.26,.28,.20,.04,.20,-.004),(.66,-.24,.26,.045,.18,-.004),(.13,.40,.76,.05,.18,-.003)],
    3:[(.31,-.24,.23,.038,.22,-.0045),(.73,.21,.30,.050,.23,-.0032)],
    4:[(.27,.36,.82,.050,.16,-.0045),(.69,-.30,.85,.045,.17,-.0038),(.47,.05,.33,.038,.26,.0018)],
    5:[(.31,-.34,.83,.045,.18,-.0045),(.71,.25,.78,.040,.16,-.0036)],
    6:[(.20,.20,.58,.075,.55,-.005),(.60,-.12,.48,.06,.51,-.004)],
    7:[(.32,-.17,.56,.064,.52,-.0045),(.78,.09,.46,.055,.49,-.005)],
    8:[(.23,.17,.49,.065,.6,-.004),(.67,-.16,.54,.07,.6,-.004)],
    9:[(.37,-.22,.57,.060,.5,-.005),(.74,.07,.40,.05,.55,-.003)],
    10:[(.24,.2,.54,.06,.4,-.003),(.67,-.15,.24,.06,.23,-.0036)],
    11:[(.31,-.17,.51,.06,.4,-.0032),(.73,.13,.25,.065,.22,-.0038)],
}


def region_rect(index):
    col,row=index%4,index//4
    return ((col+.035)/4,(row+.035)/4,(col+.965)/4,(row+.965)/4)


def use_region(builder,index):
    builder.uv_region=region_rect(index)
    builder.atlas_region_index=index


def no_region(builder):
    builder.uv_region=(0,0,1,1)
    builder.atlas_region_index=None


def cloth_depth(u,v,index):
    depth=0.0
    for centre,slope,vc,width,length,amp in FOLD_RECIPES.get(index,[]):
        line=centre+slope*(v-.5)
        g=math.exp(-((u-line)/width)**2-((v-vc)/length)**2)
        ridge=math.exp(-((u-line-width*1.5)/(width*1.2))**2-((v-vc)/length)**2)
        depth+=amp*(g-.44*ridge)
    return depth


def authored_image(name,pixels,space):
    import numpy as np
    # PNG rows run top-to-bottom; authored atlas v runs bottom-to-top.
    data=np.flipud(np.asarray(np.clip(pixels,0,255),dtype=np.uint8))
    height,width,_=data.shape
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    rows=b''.join(b'\x00'+data[y].tobytes() for y in range(height))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,6))+chunk(b'IEND',b'')
    with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as f:
        f.write(png);path=Path(f.name)
    image=bpy.data.images.load(str(path),check_existing=False)
    image.name=stable_image_name(name)
    image.colorspace_settings.name=space
    image.pack();image.filepath_raw='';path.unlink()
    return image


WARDEN_LAYOUT={}
WARDEN_CONTOURS={}
WARDEN_GUTTER=8


def initialize_warden_layout():
    """Purposeful one-atlas allocation: breastplate gets the largest UV island."""
    WARDEN_LAYOUT.clear();WARDEN_CONTOURS.clear()
    sizes={
        ('metal',2):(448,384),('metal',0):(320,72),('metal',1):(320,72),
        ('metal',6):(160,224),('metal',7):(160,224),('metal',4):(160,112),('metal',5):(160,112),
        ('metal',8):(128,144),('metal',9):(96,128),('metal',10):(96,128),
        ('metal',11):(80,96),('metal',12):(80,96),('metal',13):(112,192),('metal',14):(112,192),('metal',15):(192,128),
        ('cloth',0):(128,128),('cloth',2):(128,160),('cloth',3):(128,160),('cloth',4):(96,112),('cloth',5):(96,112),
        ('cloth',6):(96,144),('cloth',7):(96,144),('cloth',8):(80,128),('cloth',9):(80,128),
        ('cloth',10):(96,192),('cloth',11):(96,192),('cloth',14):(128,40),
        ('leather',12):(128,144),('leather',13):(128,144),('leather',14):(96,160),('leather',15):(192,48),
    }
    free=[(0,0,ATLAS_SIZE,ATLAS_SIZE)]
    placed=[]
    for key,(w,h) in sorted(sizes.items(),key=lambda item:(-max(item[1]),-item[1][0]*item[1][1],item[0])):
        rw,rh=w+2*WARDEN_GUTTER,h+2*WARDEN_GUTTER
        choices=[]
        for i,(x,y,fw,fh) in enumerate(free):
            if rw<=fw and rh<=fh:choices.append((min(fw-rw,fh-rh),max(fw-rw,fh-rh),y,x,i))
        assert choices,'Atlas packing failed: '+str(key)
        _,_,_,_,index=min(choices);x,y,_,_=free[index]
        placement=(x,y,rw,rh);new_free=[]
        for fx,fy,fw,fh in free:
            if x>=fx+fw or x+rw<=fx or y>=fy+fh or y+rh<=fy:
                new_free.append((fx,fy,fw,fh));continue
            if x>fx:new_free.append((fx,fy,x-fx,fh))
            if x+rw<fx+fw:new_free.append((x+rw,fy,fx+fw-x-rw,fh))
            if y>fy:new_free.append((fx,fy,fw,y-fy))
            if y+rh<fy+fh:new_free.append((fx,y+rh,fw,fy+fh-y-rh))
        free=[]
        for i,a in enumerate(new_free):
            if any(i!=j and b[0]<=a[0] and b[1]<=a[1] and b[0]+b[2]>=a[0]+a[2] and b[1]+b[3]>=a[1]+a[3]
                   and (b!=a or j<i) for j,b in enumerate(new_free)):continue
            free.append(a)
        for px,py,pw,ph in placed:
            assert x+rw<=px or px+pw<=x or y+rh<=py or py+ph<=y
        placed.append(placement)
        WARDEN_LAYOUT[key]=(x+WARDEN_GUTTER,y+WARDEN_GUTTER,w,h)
    print('WARDEN_ATLAS_LAYOUT '+json.dumps({kind+'_'+str(region):list(rect) for (kind,region),rect in WARDEN_LAYOUT.items()}))


def atlas_uv_rect(kind,index):
    x,y,w,h=WARDEN_LAYOUT[(kind,index)]
    return ((x+.5)/ATLAS_SIZE,(y+.5)/ATLAS_SIZE,(x+w-.5)/ATLAS_SIZE,(y+h-.5)/ATLAS_SIZE)


def register_plate_outline(mat,region,uv):
    if mat==ATLAS_MATS['metal'] and region not in (0,1,2,8,15):
        WARDEN_CONTOURS.setdefault(('metal',region),[(float(u),float(v)) for u,v in uv])


def setup_regional_materials():
    """One construction atlas, painted from the actual named UV islands and outlines."""
    import numpy as np
    size=ATLAS_SIZE
    color=np.zeros((size,size,3),dtype=np.float32);color[:]=(18,25,25)
    normal=np.zeros_like(color);normal[:]=(128,128,255)
    orm=np.zeros_like(color);orm[:]=(255,210,0)
    def segment_distance(u,v,a,b):
        dx,dy=b[0]-a[0],b[1]-a[1]
        f=np.clip(((u-a[0])*dx+(v-a[1])*dy)/max(1e-9,dx*dx+dy*dy),0,1)
        return np.sqrt((u-a[0]-f*dx)**2+(v-a[1]-f*dy)**2)
    def polygon_mask(u,v,points):
        inside=np.zeros_like(u,dtype=bool)
        for a,b in zip(points,points[1:]+points[:1]):
            crossing=((a[1]>v)!=(b[1]>v))&(u<(b[0]-a[0])*(v-a[1])/(b[1]-a[1]+1e-12)+a[0])
            inside^=crossing
        return inside.astype(np.float32)
    def paint(rgb,mask,value):
        mask=np.clip(mask,0,1)[...,None]
        return rgb*(1-mask)+np.asarray(value,dtype=np.float32)*mask
    for (kind,index),(x,y,w,h) in WARDEN_LAYOUT.items():
        u,v=np.meshgrid(np.linspace(0,1,w,dtype=np.float32),np.linspace(0,1,h,dtype=np.float32))
        boundary=WARDEN_CONTOURS.get((kind,index),[(0,0),(1,0),(1,1),(0,1)])
        edge=np.full_like(u,10)
        for a,b in zip(boundary,boundary[1:]+boundary[:1]):edge=np.minimum(edge,segment_distance(u,v,a,b))
        height=np.zeros_like(u)
        if kind=='metal':
            # Matte oxide/lacquered faces reveal albedo; worn lips remain metallic.
            broad=.97+.045*np.sin(u*5.7+index*.37)*np.cos(v*4.1-index*.21)
            rgb=np.stack((broad*132,broad*144,broad*147),axis=-1)
            underlap=np.exp(-(v/.145)**2)
            exposed=np.exp(-(edge/.026)**2)*(.50+.50*np.clip(v+.25,0,1))
            cut=np.exp(-((edge-.067)/.020)**2)
            border_high=np.exp(-((edge-.043)/.010)**2)
            # The long waist bands use a horizontal engraved seam, not a stamped box.
            if index in (0,1):
                cut=np.exp(-((v-.23)/.055)**2)*.75
                border_high=np.exp(-((v-.31)/.030)**2)*.50
                exposed=np.exp(-((1-v)/.09)**2)*.8
            if index==8:cut*=.45;border_high*=.35
            rgb=paint(rgb,underlap*.90,(26,40,43))
            rgb=paint(rgb,cut*.86,(39,57,61))
            rgb=paint(rgb,border_high*.62,(180,186,177))
            rgb=paint(rgb,exposed*.78,(191,202,196))
            # Selective broad burnished edge wear, not all-over glitter/noise.
            wear=exposed*np.clip(np.sin(u*8.3+index)+np.cos(v*5.6-index*.8)-.2,0,1)
            rgb=paint(rgb,wear*.42,(211,206,178))
            height=-.00125*cut-.0015*underlap+.00055*border_high
            ao=np.clip(1-.45*underlap-.28*cut,.22,1)
            rough=np.clip(.55+.13*cut+.13*underlap-.24*exposed,.22,.84)
            metal=np.clip(.40-.21*cut-.22*underlap+.43*exposed,.10,.87)
            if index in (11,12,13,14):
                # A readable directional raised ridge continues the modeled guard plane.
                ridge=np.exp(-((u-.51)/.075)**2)
                rgb=paint(rgb,ridge*.32,(169,185,179));height+=ridge*.0006
            if index==2:
                # Original river/reed engraving, authored only for this breastplate island.
                # It follows the sternum direction and occupies about half the visible face.
                path=[(.44,.18),(.51,.35),(.47,.52),(.55,.72),(.51,.84)]
                distance=np.full_like(u,10)
                for a,b in zip(path,path[1:]):distance=np.minimum(distance,segment_distance(u,v,a,b))
                ink=np.exp(-(distance/.042)**2);stem=np.exp(-(distance/.018)**2)
                leaves=[[(.50,.34),(.30,.43),(.29,.52),(.45,.45)],
                        [(.48,.48),(.68,.58),(.71,.67),(.54,.59)],
                        [(.53,.64),(.37,.73),(.37,.80),(.50,.73)]]
                leaf=np.zeros_like(u)
                for poly in leaves:leaf=np.maximum(leaf,polygon_mask(u,v,poly))
                rgb=paint(rgb,ink*.9,(27,44,47))
                rgb=paint(rgb,np.maximum(stem,leaf)*.92,(164,144,92))
                outline=np.zeros_like(u)
                for poly in leaves:
                    dist=np.full_like(u,10)
                    for a,b in zip(poly,poly[1:]+poly[:1]):dist=np.minimum(dist,segment_distance(u,v,a,b))
                    outline=np.maximum(outline,np.exp(-(dist/.011)**2))
                rgb=paint(rgb,outline*.85,(47,64,61))
                height-=ink*.0010+leaf*.00065
                ao=np.clip(ao-ink*.16-outline*.16,.2,1)
                rough=np.maximum(rough,np.maximum(stem,leaf)*.63)
                metal=metal*(1-np.maximum(stem,leaf))+.57*np.maximum(stem,leaf)
        elif kind=='cloth':
            # Same localized coordinates as the modeled armpit/elbow/waist fold valleys.
            for centre,slope,vc,width,length,amp in FOLD_RECIPES.get(index,[(.31,.13,.46,.07,.49,-.003)]):
                line=centre+slope*(v-.5)
                height+=amp*(np.exp(-((u-line)/width)**2-((v-vc)/length)**2)-.44*np.exp(-((u-line-width*1.5)/(width*1.2))**2-((v-vc)/length)**2))
            valley=np.clip(-height/.0038,0,1);ridge=np.clip(height/.00165,0,1)
            seam=np.exp(-(edge/.055)**2)
            rgb=np.zeros((h,w,3),dtype=np.float32);rgb[:]=(49,69,62)
            rgb=paint(rgb,valley*.93,(9,21,21));rgb=paint(rgb,ridge*.77,(90,108,86))
            rgb=paint(rgb,seam*.64,(17,30,29))
            # A wide muted selvage defines a real sewn cuff/collar/hem at gameplay scale.
            selvage=np.exp(-((v-.925)/.026)**2)
            if index in (4,5,6,7,8,9,14):rgb=paint(rgb,selvage*.50,(97,110,87))
            ao=np.clip(1-.36*valley-.22*seam,.3,1)
            rough=.87+.065*valley-.065*ridge;metal=np.zeros_like(u)
        else:
            rgb=np.zeros((h,w,3),dtype=np.float32);rgb[:]=(103,72,44)
            crease=np.exp(-((v-(.34+.035*math.sin(index))-.07*np.sin(u*3.2+index*.3))/.050)**2)
            seam=np.exp(-((u-.105)/.022)**2)+np.exp(-((u-.895)/.022)**2)
            edge_wear=np.exp(-(edge/.045)**2)
            stitch_centres=.5+.5*np.cos(v*2*PI*(8 if index in (14,15) else 10))
            stitches=seam*stitch_centres**6
            rgb=paint(rgb,crease*.72,(36,29,23));rgb=paint(rgb,seam*.67,(44,33,24))
            rgb=paint(rgb,edge_wear*.65,(156,117,70));rgb=paint(rgb,stitches*.91,(187,151,98))
            # Strap/belt interior stays flatter; boots show the larger flex crease.
            if index in (14,15):rgb=paint(rgb,crease*.25,(83,60,40))
            height=-.0017*crease-.0008*seam+.00065*stitches
            ao=np.clip(1-.32*crease-.29*seam,.3,1)
            rough=np.clip(.69+.13*crease-.18*edge_wear,.4,.86);metal=np.zeros_like(u)
        dy,dx=np.gradient(height,1/max(1,h-1),1/max(1,w-1))
        tangent=np.stack((-dx*2.4,-dy*2.4,np.ones_like(u)),axis=-1)
        tangent/=np.linalg.norm(tangent,axis=-1,keepdims=True)
        packed=np.stack((np.clip(ao,0,1),np.clip(rough,0,1),np.clip(metal,0,1)),axis=-1)*255
        g=WARDEN_GUTTER
        box=(slice(y-g,y+h+g),slice(x-g,x+w+g))
        color[box]=np.pad(rgb,((g,g),(g,g),(0,0)),mode='edge')
        normal[box]=np.pad((tangent*.5+.5)*255,((g,g),(g,g),(0,0)),mode='edge')
        orm[box]=np.pad(packed,((g,g),(g,g),(0,0)),mode='edge')
    images=(authored_image('Warden construction albedo',color,'sRGB'),
            authored_image('Warden construction normal',normal,'Non-Color'),
            authored_image('Warden construction ORM',orm,'Non-Color'))
    group=bpy.data.node_groups.get('glTF Material Output')
    if group is None:
        group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
        group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
        group.nodes.new('NodeGroupInput');group.nodes.new('NodeGroupOutput')
    for kind,name in ATLAS_MATS.items():
        mat=bpy.data.materials.new(name);mat.use_nodes=True
        shader=mat.node_tree.nodes.get('Principled BSDF');nodes=mat.node_tree.nodes;links=mat.node_tree.links
        a=nodes.new('ShaderNodeTexImage');a.image=images[0];links.new(a.outputs['Color'],shader.inputs['Base Color'])
        n=nodes.new('ShaderNodeTexImage');n.image=images[1]
        nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.65
        links.new(n.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],shader.inputs['Normal'])
        ormnode=nodes.new('ShaderNodeTexImage');ormnode.image=images[2]
        sep=nodes.new('ShaderNodeSeparateColor');sep.mode='RGB';links.new(ormnode.outputs['Color'],sep.inputs['Color'])
        links.new(sep.outputs['Green'],shader.inputs['Roughness']);links.new(sep.outputs['Blue'],shader.inputs['Metallic'])
        output=nodes.new('ShaderNodeGroup');output.node_tree=group;links.new(sep.outputs['Red'],output.inputs['Occlusion'])
        MATERIALS[name]=mat
    for name,hexcolor,metal,rough in [('Armor cavity','#1b252c',.28,.65),('Boot seam','#352b25',0,.78),('Skin planar shade','#a16e56',0,.63)]:
        mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=(*srgb(hexcolor),1)
        sh=mat.node_tree.nodes.get('Principled BSDF');sh.inputs['Base Color'].default_value=(*srgb(hexcolor),1)
        sh.inputs['Metallic'].default_value=metal;sh.inputs['Roughness'].default_value=rough;MATERIALS[name]=mat

def profile_surface(builder,rings,mat,weights,region=0,n=28,folds=True,power=.94):
    """Non-circular shaped anatomical surface, with localized modeled fold valleys."""
    use_region(builder,region)
    vertices=[];uv=[];vw=[]
    for j,(z,rx,ry,cx,cy) in enumerate(rings):
        v=j/(len(rings)-1)
        for i in range(n+1):
            u=i/n;a=2*PI*u
            c=math.cos(a);s=math.sin(a)
            bump=cloth_depth(u,v,region) if folds else 0
            x=cx+math.copysign(abs(c)**power,c)*(rx+bump)
            y=cy+math.copysign(abs(s)**power,s)*(ry+bump)
            vertices.append((x,y,z));uv.append((u,v))
            vw.append(weights[j] if isinstance(weights,list) else weights)
    faces=[]
    for j in range(len(rings)-1):
        for i in range(n):faces.append((j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i))
    faces.extend([tuple(reversed(range(n))),tuple((len(rings)-1)*(n+1)+i for i in range(n))])
    builder.add(vertices,faces,mat,vw,uv)


def tailored_torso(builder,mat,extra=0):
    rings=[(.955,.145,.105,0,.006),(1.02,.147,.100,0,0),(1.10,.140,.097,0,-.004),
           (1.185,.162,.108,0,0),(1.28,.195,.123,0,.004),(1.37,.216,.124,0,.007),
           (1.425,.202,.109,0,.007),(1.465,.128,.078,0,.005),(1.508,.062,.057,0,.001)]
    profile_surface(builder,[(z,rx+extra,ry+extra,x,y) for z,rx,ry,x,y in rings],mat,[torso_weights(z) for z,*_ in rings],0,n=40,power=.84)


def tailored_arm(builder,side,mat,extra=0):
    sign=-1 if side=='L' else 1
    wa=wb('upper_arm.'+side);wf=wb('forearm.'+side)
    centres=[(.198,0,1.458),(.227,-.003,1.42),(.251,-.003,1.37),(.282,-.004,1.305),
             (.316,-.005,1.244),(.325,-.006,1.215),(.337,-.02,1.165),(.35,-.033,1.105),(.363,-.047,1.035),(.373,-.052,.985)]
    widths=[.070,.073,.068,.059,.052,.049,.054,.047,.038,.031]
    depths=[.071,.074,.069,.060,.047,.049,.052,.044,.035,.030]
    for start,end,region in ((0,5,2 if sign<0 else 3),(5,9,4 if sign<0 else 5)):
        use_region(builder,region)
        pts=[Vector((sign*x,y,z)) for x,y,z in centres[start:end+1]]
        verts=[];uv=[];weights=[];n=28
        for j,p in enumerate(pts):
            t=j/(len(pts)-1);v=1-t
            tangent=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized()
            x=tangent.cross(Vector((0,1,0))).normalized();y=tangent.cross(x).normalized()
            index=start+j
            for i in range(n+1):
                u=i/n;a=u*2*PI;c=math.cos(a);s=math.sin(a)
                fold=cloth_depth(u,v,region)
                # Flatten the inner elbow; broaden the back of the forearm anatomically.
                rx=widths[index]+extra+fold
                ry=depths[index]+extra+fold
                xx=math.copysign(abs(c)**.87,c)*rx
                yy=math.copysign(abs(s)**1.08,s)*ry
                verts.append(p+x*xx+y*yy);uv.append((u,v))
                blend=max(0,min(1,(index-3.8)/2.2))
                weights.append(mix_weights(wa,wf,blend))
        faces=[]
        for j in range(len(pts)-1):
            for i in range(n):faces.append((j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i))
        builder.add(verts,faces,mat,weights,uv)
    no_region(builder)


def formed_plate(builder,outline,peak,mat,weights,region,thickness=.009):
    """Forged shell: articulated directional planes, beveled lip and dark return faces."""
    use_region(builder,region)
    outer=[Vector(p) for p in outline];centre=Vector(peak);n=len(outer)
    inner=[p.lerp(centre,.11) for p in outer]
    # Centre and inner lip are offset along their authored surface, not a generic sphere.
    surface_normal=sum(((outer[i]-centre).cross(outer[(i+1)%n]-centre) for i in range(n)),Vector((0,0,0))).normalized()
    back=[p-surface_normal*thickness for p in outer]
    verts=outer+inner+[centre]+back
    xs=[p.x for p in outer];ys=[p.y for p in outer];zs=[p.z for p in outer]
    use_y=max(ys)-min(ys)>max(zs)-min(zs)
    second=ys if use_y else zs
    uv=[((p.x-min(xs))/max(.001,max(xs)-min(xs)),((p.y if use_y else p.z)-min(second))/max(.001,max(second)-min(second))) for p in verts]
    faces=[];materials=[]
    for i in range(n):
        nxt=(i+1)%n
        faces.extend([(i,nxt,n+nxt,n+i),(n+i,n+nxt,2*n),(i,2*n+1+i,2*n+1+nxt,nxt)])
        materials.extend([mat,mat,'Armor cavity'])
    faces.append(tuple(2*n+1+i for i in reversed(range(n))));materials.append('Armor cavity')
    register_plate_outline(mat,region,uv[:n])
    builder.add(verts,faces,materials,weights,uv)


def front_band(builder,z0,z1,rx0,rx1,ry0,ry1,region,weights,mat=None,arc=1.38):
    """Contoured overlapping torso/tasset band with physical lower return and cavity."""
    use_region(builder,region)
    mat=mat or ATLAS_MATS['metal']
    vertices=[];uv=[];n=18
    for row,t in enumerate((0,.08,.87,1)):
        for i in range(n+1):
            u=i/n;a=(u*2-1)*arc
            rx=rx0+(rx1-rx0)*t;ry=ry0+(ry1-ry0)*t
            crown=.007*(1-(u*2-1)**2)
            z=z0+(z1-z0)*t+.012*(1-(u*2-1)**2)
            # Trim the outer upper corners, making an intentional plate shape.
            if row==3:z-=.015*abs(u*2-1)**8
            vertices.append((rx*math.sin(a),-(ry+crown)*math.cos(a),z));uv.append((u,t))
    count=len(vertices)
    vertices += [(x,y+.008,z+.003) for x,y,z in vertices]
    uv+=uv.copy()
    faces=[];mats=[]
    for row in range(3):
        for i in range(n):
            a=row*(n+1)+i;b=a+n+1
            faces.append((a,a+1,b+1,b));mats.append(mat)
            faces.append((a+count,b+count,b+1+count,a+1+count));mats.append('Armor cavity')
    for i in range(n):
        faces.append((i,count+i,count+i+1,i+1));mats.append('Armor cavity')
    for row in range(3):
        for edge in (0,n):
            a=row*(n+1)+edge;b=a+n+1
            faces.append((a,b,b+count,a+count));mats.append('Armor cavity')
    builder.add(vertices,faces,mats,weights,uv)

def make_fitted_boot(builder,sign,side):
    foot=wb('foot.'+side);shin=wb('shin.'+side)
    region=12 if sign<0 else 13;use_region(builder,region)
    # Seven deliberately shaped instep/toe sections, with a flat load-bearing sole.
    sections=[(-.213,.012,.058),(-.192,.033,.081),(-.135,.047,.112),(-.070,.045,.157),
              (-.008,.040,.177),(.048,.038,.138),(.072,.022,.081)]
    vertices=[];uv=[]
    for j,(y,w,top) in enumerate(sections):
        profile=[(-w*.84,.029),(-w,.048),(-w*.80,top*.88),(0,top),(w*.80,top*.88),(w,.048),(w*.84,.029)]
        for i,(x,z) in enumerate(profile):
            vertices.append((sign*.113+x,y,z));uv.append((i/6,j/(len(sections)-1)))
    n=7;faces=[]
    for j in range(len(sections)-1):
        for i in range(n):faces.append((j*n+i,(j+1)*n+i,(j+1)*n+(i+1)%n,j*n+(i+1)%n))
    faces.extend([tuple(reversed(range(n))),tuple((len(sections)-1)*n+i for i in range(n))])
    builder.add(vertices,[tuple(reversed(f)) for f in faces[:-2]]+faces[-2:],ATLAS_MATS['leather'],foot,uv)
    # Low, angular outsole follows the foot, rather than a bulbous round toe.
    contour=[(sign*.113-w*.90,y,.018) for y,w,_ in sections]+[(sign*.113+w*.90,y,.018) for y,w,_ in reversed(sections)]
    sole=contour+[(x,y,.033) for x,y,_ in contour];m=len(contour)
    sf=[tuple(reversed(range(m))),tuple(m+i for i in range(m))]
    sf.extend((i,(i+1)%m,(i+1)%m+m,i+m) for i in range(m))
    builder.add(sole,[tuple(reversed(f)) for f in sf],'Sole',foot)
    profile_surface(builder,[(.135,.043,.058,sign*.113,.011),(.18,.041,.052,sign*.113,.014),
                              (.255,.048,.057,sign*.113,.012),(.334,.054,.063,sign*.113,.008),
                              (.348,.055,.064,sign*.113,.008)],ATLAS_MATS['leather'],
                    [foot,shin,shin,shin,shin],region,n=24,folds=False,power=.80)
    no_region(builder)
    # Fine seam follows the ankle, not a thick toy cuff.
    tube(builder,[(sign*.154,-.042,.16),(sign*.155,-.039,.24),(sign*.165,-.036,.337)],
         [.0028]*3,[.0023]*3,'Boot seam',shin,n=6)


def make_hand_mature(builder,sign,side):
    hand=wb('hand.'+side);no_region(builder)
    # Flat dorsal palm / thenar wedge with tapered wrist, not an ellipsoid fist.
    rings=[(.904,.022,.016,sign*.389,-.080),(.923,.033,.023,sign*.385,-.071),
           (.949,.035,.021,sign*.381,-.061),(.977,.026,.024,sign*.374,-.053),
           (.994,.025,.025,sign*.372,-.049)]
    profile_surface(builder,rings,'Skin',hand,15,n=20,folds=False,power=.72)
    no_region(builder)
    for i in range(4):
        x=sign*(.356+i*.017)
        length=(.039,.045,.043,.033)[i]
        tube(builder,[(x,-.087,.938),(x,-.105,.922),(x,-.103,.938-length),
                      (x,-.091,.933-length)], [.0088,.009,.008,.0065],[.009,.009,.008,.0065], 'Skin',hand,n=10)
    # Opposed thumb saddle has a broad root, then a tapered two-joint curl.
    tube(builder,[(sign*.349,-.059,.958),(sign*.342,-.077,.944),(sign*.351,-.105,.936),
                  (sign*.363,-.109,.926)],[.018,.015,.012,.009],[.013,.013,.012,.009],'Skin',hand,n=12)


def make_body_mature():
    b=BUILDERS['Body_Base']=MeshBuilder('Body_Base')
    tailored_torso(b,ATLAS_MATS['cloth'],-.009)
    for sign,side in ((-1,'L'),(1,'R')):
        tailored_arm(b,side,ATLAS_MATS['cloth'],-.006)
        thigh=wb('thigh.'+side);shin=wb('shin.'+side)
        rings=[(.14,.037,.047,sign*.113,.01),(.27,.048,.056,sign*.113,.008),
               (.415,.048,.052,sign*.113,-.007),(.49,.047,.055,sign*.113,-.012),
               (.54,.052,.060,sign*.112,-.011),(.64,.062,.074,sign*.105,-.006),
               (.78,.075,.085,sign*.094,.003),(.92,.079,.092,sign*.089,.006),(.966,.066,.086,sign*.087,.004)]
        weights=[shin,shin,shin,mix_weights(shin,thigh,.28),mix_weights(shin,thigh,.68),thigh,thigh,thigh,wb('hips')]
        profile_surface(b,rings,ATLAS_MATS['cloth'],weights,10 if sign<0 else 11,n=28,power=.86)
        make_fitted_boot(b,sign,side);make_hand_mature(b,sign,side)
    no_region(b)
    loft(b,[(1.475,.054,.05,0,.001),(1.525,.05,.047,0,0),(1.572,.05,.048,0,-.002),(1.608,.054,.051,0,-.002)],
         'Skin',[wb('chest'),wb('neck'),wb('neck'),wb('head')],n=28)
    face_start=len(b.vertices)
    make_face(b)
    for sign in (-1,1):
        brow=[(sign*.013,-.084,1.721),(sign*.042,-.090,1.737),(sign*.081,-.070,1.726),
              (sign*.074,-.080,1.711),(sign*.045,-.098,1.718),(sign*.018,-.092,1.711)]
        brow_faces=[(0,1,4,5),(1,2,3,4)]
        if sign>0:brow_faces=[tuple(reversed(face)) for face in brow_faces]
        b.add(brow,brow_faces,'Skin',wb('head'))
        b.add([brow[5],brow[4],brow[3]],[(0,1,2)],'Skin planar shade',wb('head'))
    # Compact adult cranium; preserve actual inset eyes and facial planes.
    for i in range(face_start,len(b.vertices)):
        x,y,z=b.vertices[i]
        jaw=.0055*math.exp(-((z-1.621)/.026)**2)
        if z<1.614 and y<-.04:y-=.005*math.exp(-((z-1.592)/.025)**2)
        if z<1.6:x*=1.16
        x=x*.94+math.copysign(jaw,x) if abs(x)>.03 else x*.94
        b.vertices[i]=(x,y*.96,1.59+(z-1.59)*.93)


def new_shoulder(builder,sign):
    side='L' if sign<0 else 'R'
    outline=[(.160,-.077,1.488),(.245,-.102,1.484),(.323,-.072,1.438),
             (.344,.016,1.382),(.300,.088,1.402),(.208,.105,1.474)]
    for layer in range(2 if sign<0 else 1):
        shift=.034*layer
        pts=[(sign*(x+layer*.018),y,z-shift) for x,y,z in outline]
        if sign<0:pts.reverse()
        centre=(sign*(.247+layer*.012),-.001,1.493-shift)
        weights=mix_weights(wb('clavicle.'+side),wb('upper_arm.'+side),.23+.20*layer)
        formed_plate(builder,pts,centre,ATLAS_MATS['metal'],weights,4 if sign<0 else 5,thickness=.007)
    # A small asymmetrical anchored strap, rather than gilding every plate edge.
    no_region(builder)
    ribbon(builder,[(sign*.17,-.09,1.455),(sign*.208,-.123,1.413),(sign*.222,-.121,1.352)],
           [.034,.037,.03],'Charcoal leather',wb('clavicle.'+side),.008)


def hanging_tailored_panel(builder,sign,back=False):
    region=(8 if sign<0 else 9) if back else (6 if sign<0 else 7)
    use_region(builder,region)
    vertices=[];uv=[];weights=[]
    side='L' if sign<0 else 'R'
    for j in range(7):
        v=j/6;z=1.026-v*.303
        width=.145+.024*v;centre=sign*(.086+.032*v)
        for i in range(9):
            u=i/8
            x=centre+(u-.5)*width
            fold=cloth_depth(u,1-v,region)
            y=(.111 if back else -.111)+(.032 if back else -.032)*(1-(u*2-1)**2)
            y+=(1 if back else -1)*fold
            vertices.append((x,y,z+.016*math.sin(u*PI)*v));uv.append((u,1-v))
            weights.append(mix_weights(wb('hips'),wb('coat.'+side),v*.92))
    faces=[]
    for j in range(6):
        for i in range(8):
            face=(j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i)
            faces.append(tuple(reversed(face)) if back else face)
    builder.add(vertices,faces,ATLAS_MATS['cloth'],weights,uv)


def tasset_pair(builder,sign):
    side='L' if sign<0 else 'R';weights=wb('coat.'+side)
    for layer in range(2):
        z=1.012-layer*.105
        x=sign*(.093+layer*.010)
        # Six-corner overlapping plate with a real lower return, fitted around the thigh.
        outline=[(x-.060,-.164,z-.104),(x+.052,-.162,z-.097),(x+.070,-.154,z-.027),
                 (x+.058,-.158,z+.004),(x-.051,-.163,z+.01),(x-.070,-.156,z-.025)]
        first=len(builder.vertices)
        formed_plate(builder,outline,(x,-.176,z-.043),ATLAS_MATS['metal'],weights,6 if sign<0 else 7,thickness=.006)
        for i in range(first,len(builder.vertices)):
            factor=max(0,min(1,(1.026-builder.vertices[i][2])/.303))*.92
            builder.weights[i]=mix_weights(wb('hips'),wb('coat.'+side),factor)


def shaped_breastplate(builder):
    """One anatomically shaped cuirass with a sternum ridge, not padded horizontal hoops."""
    use_region(builder,2)
    sections=[(1.234,.158,.131),(1.267,.185,.143),(1.325,.213,.147),(1.390,.216,.139),(1.456,.163,.100)]
    vertices=[];uv=[];weights=[];n=22
    for j,(z,rx,ry) in enumerate(sections):
        v=j/(len(sections)-1)
        for i in range(n+1):
            u=i/n;a=(u*2-1)*1.39
            x=rx*math.sin(a)
            # A directional central fold joins two broad breast planes.
            y=-ry*math.cos(a)-.012*math.exp(-(x/.043)**2)
            zz=z
            if j==len(sections)-1:
                zz-=.012*math.exp(-(x/.035)**2)
                zz-=.010*abs(u*2-1)**6
            vertices.append((x,y,zz));uv.append((u,v));weights.append(torso_weights(zz))
    count=len(vertices)
    vertices += [(x,y+.007,z) for x,y,z in vertices]
    uv+=uv.copy();weights+=weights.copy()
    faces=[];mats=[]
    for j in range(len(sections)-1):
        for i in range(n):
            a=j*(n+1)+i;b=a+n+1
            faces.extend([(a,a+1,b+1,b),(a+count,b+count,b+1+count,a+1+count)])
            mats.extend([ATLAS_MATS['metal'],'Armor cavity'])
    for row in (0,len(sections)-1):
        for i in range(n):
            a=row*(n+1)+i
            faces.append((a,a+count,a+1+count,a+1));mats.append('Armor cavity')
    for edge in (0,n):
        for row in range(len(sections)-1):
            a=row*(n+1)+edge;b=a+n+1
            faces.append((a,b,b+count,a+count));mats.append('Armor cavity')
    builder.add(vertices,faces,mats,weights,uv)


def sewn_side_closure(builder):
    use_region(builder,14)
    points=[Vector((.163,-.071,1.443)),Vector((.211,-.067,1.358)),Vector((.188,-.077,1.264)),Vector((.149,-.081,1.165))]
    vertices=[];uv=[];weights=[]
    for j,p in enumerate(points):
        tangent=(points[min(j+1,3)]-points[max(j-1,0)]).normalized()
        across=Vector((tangent.z,0,-tangent.x)).normalized()
        for side in (-1,1):
            vertices.append(p+across*(.017 if j<3 else .014)*side)
            uv.append(((side+1)/2,j/3));weights.append(torso_weights(p.z))
    builder.add(vertices,[(i*2,i*2+1,(i+1)*2+1,(i+1)*2) for i in range(3)],ATLAS_MATS['leather'],weights,uv)
    no_region(builder)
    # One restrained fastening tab makes the construction legible.
    ribbon(builder,[(.182,-.089,1.286),(.204,-.087,1.313),(.210,-.077,1.337)],
           [.011,.013,.011],'Old gold',torso_weights(1.313),.004)

def make_warden_mature():
    b=BUILDERS['Gear_Warden']=MeshBuilder('Gear_Warden')
    tailored_torso(b,ATLAS_MATS['cloth'],.003)
    for sign,side in ((-1,'L'),(1,'R')):
        tailored_arm(b,side,ATLAS_MATS['cloth'],.003)
        new_shoulder(b,sign)
        hanging_tailored_panel(b,sign,False);hanging_tailored_panel(b,sign,True)
        tasset_pair(b,sign)
        # Shaped front vambrace: thin wrist, broad upper forearm, dark return surfaces.
        x=sign*.354
        outline=[(sign*.373-.025,-.085,1.018),(sign*.373+.025,-.085,1.018),
                 (x+.048,-.065,1.16),(x+.034,-.066,1.194),(x-.037,-.066,1.190),(x-.048,-.063,1.158)]
        formed_plate(b,outline,(x,-.109,1.107),ATLAS_MATS['metal'],wb('forearm.'+side),9 if sign<0 else 10,thickness=.005)
        # Knee is a directional overlapping brow plate rather than a perfect disk.
        cx=sign*.113
        knee=[(cx,-.079,.453),(cx+.047,-.074,.484),(cx+.052,-.069,.533),
              (cx+.025,-.071,.563),(cx-.031,-.071,.557),(cx-.052,-.069,.527),(cx-.043,-.075,.480)]
        formed_plate(b,knee,(cx,-.086,.519),ATLAS_MATS['metal'],mix_weights(wb('thigh.'+side),wb('shin.'+side),.60),11 if sign<0 else 12,thickness=.006)
        shin=[(cx-.025,-.065,.147),(cx+.025,-.065,.147),(cx+.046,-.065,.268),
              (cx+.050,-.049,.405),(cx+.031,-.052,.452),(cx-.035,-.052,.446),
              (cx-.048,-.05,.394),(cx-.045,-.065,.270)]
        formed_plate(b,shin,(cx,-.09,.308),ATLAS_MATS['metal'],wb('shin.'+side),13 if sign<0 else 14,thickness=.006)
        no_region(b)
        for z in (.205,.384):
            profile_surface(b,[(z-.007,.054,.06,cx,.007),(z+.007,.054,.06,cx,.007)],
                            ATLAS_MATS['leather'],wb('shin.'+side),14,n=20,folds=False,power=.86)
    # Shaped breastplate above two articulated waist lames; recessed cloth remains visible at the sides.
    shaped_breastplate(b)
    for row,(z0,z1,rx0,rx1,ry0,ry1) in enumerate([
        (1.088,1.174,.151,.172,.114,.128),(1.157,1.249,.169,.189,.126,.138)]):
        front_band(b,z0,z1,rx0,rx1,ry0,ry1,row,torso_weights((z0+z1)/2))
    sewn_side_closure(b)
    # Two back plates, deliberately leaving a cloth side cavity instead of a full metal tube.
    for z0,z1,rx0,rx1,ry0,ry1 in ((1.09,1.30,.152,.213,.111,.132),(1.284,1.445,.213,.177,.132,.102)):
        start_v=len(b.vertices);start_f=len(b.faces)
        front_band(b,z0,z1,rx0,rx1,ry0,ry1,8,wb('spine'))
        for i in range(start_v,len(b.vertices)):
            x,y,z=b.vertices[i];b.vertices[i]=(x,-y,z);b.weights[i]=torso_weights(z)
        for i in range(start_f,len(b.faces)):b.faces[i]=tuple(reversed(b.faces[i]))
    no_region(b)
    # Fitted cloth collar; a single aged brass accent is enough at the face.
    profile_surface(b,[(1.478,.073,.063,0,.001),(1.519,.061,.054,0,.001),(1.54,.058,.052,0,.001)],
                    ATLAS_MATS['cloth'],wb('chest'),14,n=24,folds=False,power=.9)
    no_region(b)
    tube(b,[(-.055,-.019,1.528),(-.041,-.047,1.532),(0,-.055,1.534),(.041,-.047,1.532),(.055,-.019,1.528)],
         [.0035]*5,[.003]*5,'Old gold',wb('chest'),n=6)
    profile_surface(b,[(1.024,.157,.114,0,0),(1.075,.151,.108,0,0)],ATLAS_MATS['leather'],wb('hips'),15,n=28,folds=False,power=.78)
    no_region(b)
    # Flat, slightly asymmetric sash knot and a small forged clasp.
    ribbon(b,[(-.12,-.107,1.071),(-.015,-.123,1.046),(.129,-.099,1.038)],
           [.035,.047,.031],'Cinnabar',wb('hips'),.006)
    buckle=[(-.029,-.128,1.027),(.031,-.128,1.03),(.037,-.126,1.06),(.026,-.126,1.077),(-.027,-.127,1.072),(-.035,-.129,1.048)]
    formed_plate(b,buckle,(0,-.138,1.051),'Old gold',wb('hips'),15,thickness=.003)
    no_region(b)


def make_heads_mature():
    # Keep the alternative topknot compatible with the more compact shared skull.
    make_heads()
    top=BUILDERS['Head_Topknot']
    for i,(x,y,z) in enumerate(top.vertices):top.vertices[i]=(x*.94,y*.96,1.59+(z-1.59)*.93)
    b=BUILDERS['Head_Warden']=MeshBuilder('Head_Warden');h=wb('head')
    # Directional eight-segment forged crown. Front brow stays open above the eyes.
    rings=[(1.693,.105,.091),(1.751,.106,.091),(1.792,.088,.080),(1.824,.058,.057),(1.839,.019,.019)]
    n=16
    for segment in range(8):
        use_region(b,15)
        vertices=[];uv=[]
        for j,(z,rx,ry) in enumerate(rings):
            for i in range(3):
                a=(segment*2+i)*2*PI/n
                front=max(0,-math.sin(a))
                zz=z+(front*.047 if j==0 else front*.004 if j==1 else 0)
                xx=math.copysign(abs(math.cos(a))**.82,math.cos(a))*rx
                yy=.01+math.copysign(abs(math.sin(a))**.84,math.sin(a))*ry
                vertices.append((xx,yy,zz));uv.append(((segment*2+i)/n,j/(len(rings)-1)))
        faces=[]
        for j in range(len(rings)-1):
            for i in range(2):faces.append((j*3+i,j*3+i+1,(j+1)*3+i+1,(j+1)*3+i))
        b.add(vertices,faces,ATLAS_MATS['metal'],h,uv)
    use_region(b,15)
    crown=[(.019*math.cos(i*2*PI/16),.01+.019*math.sin(i*2*PI/16),1.839) for i in range(16)]
    b.add(crown,[tuple(range(16))],ATLAS_MATS['metal'],h,[(.5+.5*math.cos(i*2*PI/16),.5+.5*math.sin(i*2*PI/16)) for i in range(16)])
    brow=[(-.098,-.043,1.715),(-.067,-.078,1.729),(0,-.092,1.739),(.067,-.078,1.729),(.098,-.043,1.715),
          (.093,-.049,1.753),(.057,-.078,1.774),(0,-.085,1.782),(-.057,-.078,1.774),(-.093,-.049,1.753)]
    formed_plate(b,brow,(0,-.107,1.760),ATLAS_MATS['metal'],h,15,.006)
    no_region(b)
    # Narrow brow return and cheek wings terminate in planes instead of round ear covers.
    tube(b,[(-.101,-.018,1.728),(-.078,-.065,1.739),(0,-.084,1.743),(.078,-.065,1.739),(.101,-.018,1.728)],
         [.0038]*5,[.003]*5,'Steel shadow',h,n=6)
    for sign in (-1,1):
        pts=[(sign*.079,-.025,1.610),(sign*.110,-.032,1.651),(sign*.119,-.026,1.719),
             (sign*.098,.012,1.752),(sign*.094,.031,1.681)]
        if sign<0:pts.reverse()
        formed_plate(b,pts,(sign*.112,-.038,1.687),ATLAS_MATS['metal'],h,15,.005)
    # Low fore-aft reinforcing ridge, with an aged inset instead of a ceremonial spike.
    no_region(b)
    ridge=[(-.008,-.060,1.797),(.008,-.060,1.797),(.010,-.015,1.855),(.008,.045,1.863),
           (-.008,.045,1.863),(-.010,-.015,1.855)]
    b.add(ridge,[(0,1,2,5),(5,2,3,4)],'Steel shadow',h)

def solve_leg_pose(side,ankle,foot_delta):
    """Baked two-bone leg pose with a forward knee and a planted ankle target."""
    bpy.context.view_layer.update()
    thigh=RIG.pose.bones['thigh.'+side];shin=RIG.pose.bones['shin.'+side]
    hip=thigh.head.copy();target=Vector(ankle)
    l1=(BONES[thigh.name][1]-BONES[thigh.name][0]).length
    l2=(BONES[shin.name][1]-BONES[shin.name][0]).length
    axis=(target-hip).normalized();distance=max(abs(l1-l2)+.001,min((target-hip).length,l1+l2-.001))
    target=hip+axis*distance
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    off=math.sqrt(max(0,l1*l1-along*along))
    bend=Vector((0,-1,0));bend=(bend-axis*bend.dot(axis)).normalized()
    knee=hip+axis*along+bend*off
    for pb,a,b in ((thigh,hip,knee),(shin,knee,target)):
        original=(BONES[pb.name][1]-BONES[pb.name][0]).normalized()
        rotation=original.rotation_difference((b-a).normalized())@pb.bone.matrix_local.to_quaternion()
        pb.matrix=Matrix.Translation(a)@rotation.to_matrix().to_4x4()
        bpy.context.view_layer.update()
    foot=RIG.pose.bones['foot.'+side]
    foot.matrix=Matrix.Translation(foot.head)@(foot_delta@foot.bone.matrix_local.to_quaternion()).to_matrix().to_4x4()
    bpy.context.view_layer.update()
    return (target-Vector(ankle)).length


def grounded_feet(lead=0):
    errors=[]
    for sign,side in ((-1,'L'),(1,'R')):
        ankle=(sign*.116,-.038-lead if side=='L' else .043,.125)
        delta=Quaternion((0,0,1),sign*.07)
        errors.append(solve_leg_pose(side,ankle,delta))
    return max(errors)


def mature_pose_adjustment(clip,t):
    """Human weight support while preserving runtime-owned travel and contact timing."""
    if clip=='idle':
        set_world_translation('hips',(.016,0,-.023))
        set_world_rotation('hips',(0,.025,.026))
        set_world_rotation('spine',(.018+.004*math.sin(t*2*PI),-.018,-.018))
        set_world_rotation('chest',(0,-.006,-.018))
        set_world_rotation('upper_arm.L',(-.045,.018,0))
        set_world_rotation('forearm.L',(-.10,0,0))
        set_world_rotation('forearm.R',(-.055,0,.015))
        grounded_feet()
    elif clip in ('walk','run'):
        running=clip=='run'
        stride=.45 if running else .29
        pelvis=-.054+.015*math.sin(t*2*PI)**2 if running else -.032+.004*math.sin(t*2*PI)**2
        set_world_translation('hips',(.009*math.sin(t*2*PI),0,pelvis))
        for sign,side in ((-1,'L'),(1,'R')):
            phase=(t+(0 if side=='L' else .5))%1
            stance=.55 if running else .62
            if phase<stance:
                f=phase/stance
                y=-stride*.5+stride*f
                toe=max(0,(f-.72)/.28)
                z=.125+.031*toe
                pitch=-.12*max(0,1-f/.18)+.19*toe
            else:
                f=(phase-stance)/(1-stance)
                y=stride*.5*math.cos(f*PI)
                z=.125+(.17 if running else .080)*math.sin(f*PI)
                pitch=-.23*math.sin(f*PI)
            delta=Euler((pitch,0,sign*.035),'XYZ').to_quaternion()
            solve_leg_pose(side,(sign*.116,y,z),delta)
            thigh=RIG.pose.bones['thigh.'+side]
            d=thigh.tail-thigh.head
            angle=math.atan2(d.y,-d.z)
            set_world_rotation('coat.'+side,(angle*.52-.035,0,sign*.025))
    elif clip in ('attack','attack_glaive'):
        load=math.sin(PI*t)**2
        keys=[(0,0),(.23,-.42),(.34,-.5),(.54,.76),(.66,.6),(1,0)]
        twist=0.0
        for (ta,va),(tb,vb) in zip(keys,keys[1:]):
            if ta<=t<=tb:
                q=(t-ta)/(tb-ta);q=q*q*(3-2*q);twist=va+(vb-va)*q;break
        set_world_translation('hips',(-.060*load,-.105*load,-.023-.067*load))
        set_world_rotation('hips',(0,0,twist*.38))
        set_world_rotation('spine',(.08*load,0,twist*.28))
        set_world_rotation('chest',(.025*load,0,-twist*.11))
        for sign,side in ((-1,'L'),(1,'R')):
            ankle=((-.116-.075*load) if side=='L' else (.116+.050*load),
                   (-.038-.265*load) if side=='L' else (.043+.16*load),.125)
            solve_leg_pose(side,ankle,Quaternion((0,0,1),sign*(.07+.06*load)))
            thigh=RIG.pose.bones['thigh.'+side];d=thigh.tail-thigh.head
            angle=math.atan2(d.y,-d.z)
            set_world_rotation('coat.'+side,(angle*.55-.02*load,0,sign*.02*load))
    elif clip=='jump':
        if t<.21:
            compression=.125*math.sin(PI*t/.21)
            set_world_translation('hips',(.012,-.014,-.025-compression))
            set_world_rotation('spine',(.19*math.sin(PI*t/.21),0,-.015))
            grounded_feet()
        elif t>.76:
            landing=(t-.76)/.24
            compression=.14*math.sin(PI*landing)
            set_world_translation('hips',(.012,-.018,-.025-compression))
            set_world_rotation('spine',(.17*math.sin(PI*landing),0,-.015))
            grounded_feet()
        else:
            airborne=(t-.21)/.55
            tuck=math.sin(PI*airborne)**.80
            set_world_translation('hips',(0,0,-.008))
            set_world_rotation('hips',(.11*tuck,0,.035*tuck))
            set_world_rotation('spine',(.075*tuck,0,-.025*tuck))
            set_world_rotation('thigh.L',(-.96*tuck,0,-.06*tuck))
            set_world_rotation('shin.L',(1.50*tuck,0,0))
            set_world_rotation('foot.L',(-.37*tuck,0,-.04*tuck))
            set_world_rotation('thigh.R',(-.40*tuck,0,.06*tuck))
            set_world_rotation('shin.R',(1.04*tuck,0,0))
            set_world_rotation('foot.R',(-.14*tuck,0,.04*tuck))
            set_world_rotation('coat.L',(-.53*tuck,0,-.04*tuck))
            set_world_rotation('coat.R',(-.30*tuck,0,.04*tuck))


def preview_mature_warden(objects,output,render,mode="form"):
    """Focused, VFX-free Warden proof. Model export is complete before these views."""
    scene=bpy.context.scene
    for name,ob in objects.items():
        ob.hide_render=name in ('Gear_Wayfarer','Head_Topknot','Weapon_Saber')
        ob.hide_set(ob.hide_render)
    RIG.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)
    # A neutral studio ground gives contact shadows for weight-bearing assessment.
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.006))
    floor=bpy.context.object;floor.name='Authoring contact floor — not exported'
    mat=bpy.data.materials.new('Authoring floor');mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(.09,.105,.11,1);shader.inputs['Roughness'].default_value=.94
    floor.data.materials.append(mat)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'art/jadebound_modular_hero.blend'))
    if not render:return
    proof=output/'builds'/('warden-atlas-study' if mode=='atlas' else 'warden-rebuild-refined');proof.mkdir(parents=True,exist_ok=True)
    proof_poses=[('rest','idle',1),('contact','attack_glaive',11)]
    if mode=='form':proof_poses += [('apex','jump',18),('landing','jump',31)]
    for name,clip,frame in proof_poses:
        RIG.animation_data.action=bpy.data.actions[clip];scene.frame_set(frame);bpy.context.view_layer.update()
        scene.render.filepath=str(proof/(name+'.png'));bpy.ops.render.render(write_still=True)
    if mode=='atlas':return
    clay=bpy.data.materials.new('Authoring untextured clay');clay.use_nodes=True
    sh=clay.node_tree.nodes.get('Principled BSDF');sh.inputs['Base Color'].default_value=(.28,.31,.32,1);sh.inputs['Roughness'].default_value=.8
    RIG.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)
    scene.view_layers[0].material_override=clay
    scene.render.filepath=str(proof/'clay.png');bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override=None

def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='.')
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--proof-mode',choices=('form','atlas'),default='form')
    parser.add_argument('--stabilize-image-names',action='store_true',help='Naming-only migration of saved GLB and packed Blender images; no geometry/texture regeneration')
    opt=parser.parse_args(args)
    output=Path(opt.output).resolve()
    if opt.stabilize_image_names:
        stabilize_saved_image_names(output)
        return
    (output/'art').mkdir(exist_ok=True)
    (output/'game/assets/models').mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    setup_materials();initialize_warden_layout();setup_rig();make_body_mature();make_wayfarer();make_warden_mature();make_heads_mature();make_weapons();setup_regional_materials()
    objects={name:b.finish() for name,b in BUILDERS.items()}
    attachment('Saber_FX','Weapon_Saber');attachment('Glaive_FX','Weapon_Glaive')
    animate()
    scene=bpy.context.scene
    scene.frame_set(1)
    for ob in bpy.context.scene.objects:ob.select_set(True)
    props=bpy.ops.export_scene.gltf.get_rna_type().properties
    options=dict(export_format='GLB',use_selection=True,export_animations=True,export_skins=True,
                 export_yup=True,export_extras=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',
                 export_force_sampling=True,export_frame_range=False,export_animation_mode='ACTIONS',
                 export_nla_strips=False,export_def_bones=True,export_leaf_bone=False,
                 export_anim_single_armature=True,export_optimize_animation_size=False,
                 export_image_format='AUTO')
    options={k:v for k,v in options.items() if k in props and (props[k].type!='ENUM' or v in {item.identifier for item in props[k].enum_items})}
    path=output/'game/assets/models/hero_modular.glb'
    bpy.ops.export_scene.gltf(filepath=str(path),**options)
    inspect_glb(path)
    preview_setup(objects,output,False)
    preview_mature_warden(objects,output,opt.render,opt.proof_mode)
    print('MODULAR_HERO_READY '+str(path))


if __name__ == '__main__':
    main()
