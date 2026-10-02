#!/usr/bin/env python3
"""Original Jadebound modular skinned hero. Blender 4.3+ authoring source.

Run: blender --background --threads 2 --python tools/generate_modular_hero.py -- --output .
No third-party models/textures. All forms, rig, UVs, material detail and clips are
built here. The six Gear_/Head_/Weapon_ meshes are the runtime visibility contract.
"""
from __future__ import annotations
import argparse
import json
import math
import struct
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

    def add(self, vertices, faces, mat, weights, uvs=None):
        offset = len(self.vertices)
        self.vertices.extend(tuple(v) for v in vertices)
        self.faces.extend(tuple(offset+i for i in f) for f in faces)
        self.materials.extend([mat]*len(faces) if isinstance(mat, str) else mat)
        self.weights.extend([weights]*len(vertices) if isinstance(weights, dict) else weights)
        self.uvs.extend(uvs if uvs is not None else [(v[0]*2, v[2]*2) for v in vertices])

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
    rough_images = {}
    for kind, base in (('cloth',.85),('leather',.66),('metal',.35)):
        image = bpy.data.images.new('Original '+kind+' micrograin roughness',width=64,height=64)
        image.colorspace_settings.name='Non-Color'
        pixels=[]
        for y in range(64):
            for x in range(64):
                grain = (((x*7349+y*9151+x*y*19)%103)/103-.5)
                weave = (.024 if (x//2+y//2)%2 else -.024) if kind=='cloth' else 0
                value = min(.98,max(.05,base+grain*(.095 if kind!='metal' else .055)+weave))
                pixels.extend((value,value,value,1))
        image.pixels.foreach_set(pixels)
        image.pack()
        rough_images[kind] = image
    for name,(hexcolor,metal,rough) in palette.items():
        mat = bpy.data.materials.new(name)
        mat.diffuse_color=(*srgb(hexcolor),1)
        mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value=(*srgb(hexcolor),1)
        bsdf.inputs['Metallic'].default_value=metal
        bsdf.inputs['Roughness'].default_value=rough
        # Packed hand-authored UV roughness gives actual exported cloth/metal detail.
        kind='metal' if metal>.5 else ('cloth' if 'cloth' in name or 'fold' in name else 'leather' if 'leather' in name else None)
        if kind:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex.name='Original woven / hammered surface roughness'
            tex.image=rough_images[kind]
            tex.interpolation='Linear'
            mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Roughness'])
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
               [.022,.023,.012],'Gold light',w,.006)


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
            verts.append((.104*math.cos(lat)*math.cos(a)+sweep,.019+.088*math.cos(lat)*math.sin(a),1.736+.111*math.sin(lat)))
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
    b.add(vertices,faces,mats,wb('hand.R'))


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


def animate():
    scene=bpy.context.scene
    scene.render.fps=24
    RIG.animation_data_create()
    clips=[('idle',48),('walk',32),('run',24),('attack',18),('jump',34)]
    for clip,length in clips:
        action=bpy.data.actions.new(clip)
        action['clip_name']=clip
        action['loop']=clip in ('idle','walk','run')
        RIG.animation_data.action=action
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
            elif clip=='attack':
                # Anticipation -> decisive outside-to-inside cut -> recover.
                keys=[(0,0),(.23,-.42),(.34,-.5),(.54,.76),(.66,.6),(1,0)]
                def curve(keys):
                    for (ta,va),(tb,vb) in zip(keys,keys[1:]):
                        if ta<=t<=tb:
                            k=(t-ta)/(tb-ta); k=k*k*(3-2*k)
                            return va+(vb-va)*k
                    return keys[-1][1]
                twist=curve(keys)
                arm_x=curve([(0,0),(.26,-.94),(.37,-1.08),(.55,.32),(.7,.25),(1,0)])
                arm_y=curve([(0,0),(.30,-.30),(.55,.58),(.7,.36),(1,0)])
                bend=curve([(0,0),(.27,-.75),(.48,-.23),(.68,-.10),(1,0)])
                set_world_rotation('hips',(0,0,twist*.30))
                set_world_rotation('spine',(.025,0,twist*.36))
                set_world_rotation('chest',(0,0,twist*.34))
                set_world_rotation('upper_arm.R',(arm_x,arm_y,0))
                set_world_rotation('forearm.R',(bend,0,0))
                set_world_rotation('hand.R',(0,-twist*.25,0))
                set_world_rotation('upper_arm.L',(-arm_x*.28,-arm_y*.2,0))
                set_world_rotation('forearm.L',(-abs(bend)*.5,0,0))
                set_world_rotation('thigh.L',(-abs(twist)*.12,0,0))
                set_world_rotation('shin.L',(abs(twist)*.16,0,0))
                set_world_rotation('coat.L',(-.04,0,-twist*.22))
                set_world_rotation('coat.R',(-.04,0,-twist*.22))
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
            for pb in RIG.pose.bones:
                pb.keyframe_insert(data_path='location',frame=frame,group=pb.name)
                pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=pb.name)
                pb.keyframe_insert(data_path='scale',frame=frame,group=pb.name)
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
    ROOT['animation_clips']='idle, walk, run (loop); attack, jump (one-shot)'


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
        for name,ob in objects.items():
            ob.hide_render=name in ('Gear_Wayfarer','Head_Topknot','Weapon_Saber')
            ob.hide_set(ob.hide_render)
        scene.render.filepath=str(output/'builds'/'jadebound-modular-warden.png')
        bpy.ops.render.render(write_still=True)
        for name,ob in objects.items():
            ob.hide_render=name in ('Gear_Warden','Head_Warden','Weapon_Glaive')
            ob.hide_set(ob.hide_render)


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='.')
    parser.add_argument('--render',action='store_true')
    opt=parser.parse_args(args)
    output=Path(opt.output).resolve()
    (output/'art').mkdir(exist_ok=True)
    (output/'game/assets/models').mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    setup_materials();setup_rig();make_body();make_wayfarer();make_warden();make_heads();make_weapons()
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
    preview_setup(objects,output,opt.render)
    print('MODULAR_HERO_READY '+str(path))


if __name__ == '__main__':
    main()
