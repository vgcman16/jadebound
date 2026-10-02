#!/usr/bin/env python3
"""River Warden: continuous-human-base garment/armor clay study.

This is a new, isolated Blender authoring route. It does not import or overwrite
the existing procedural hero generator or game exports. The concept is direction
only; its pixels are never projected onto meshes or packed into this scene.

Production order: evaluated CC0 body -> landmark report -> tailored garment cages
-> independently editable armor -> clay and block-value review -> later surfacing.
The official MPFB trial must already exist. No addon installation/network access.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import math
from pathlib import Path

import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "art/human-base-trial/mpfb_adult_base.blend"
OUT = ROOT / "art/concept-warden"
SLOT_PREFIXES = ("Body", "Gear_Warden", "Gear_Boots", "Gear_Gloves", "Head_Topknot", "Head_Warden", "Weapon_Glaive")


def parse_args():
    import sys
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, default=BASE)
    p.add_argument("--output", type=Path, default=OUT)
    p.add_argument("--render", action="store_true")
    return p.parse_args(args)


def open_cc0_base(path):
    if not path.is_file():
        raise FileNotFoundError(f"The reviewed local CC0 anatomy trial is required: {path}")
    bpy.ops.wm.open_mainfile(filepath=str(path))
    bodies = [o for o in bpy.data.objects if o.type == "MESH" and o.name == "CC0_Human_Base_Editable"]
    rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    if len(bodies) != 1 or len(rigs) != 1:
        raise RuntimeError("Expected one editable MPFB body and one game rig")
    body, rig = bodies[0], rigs[0]
    # Resolve the actual shape keys and helper mask into one continuous cage.
    for mod in body.modifiers:
        if mod.type == "ARMATURE":
            mod.show_viewport = False
            mod.show_render = False
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(body.evaluated_get(graph),
        preserve_all_data_layers=True, depsgraph=graph)
    clean = bpy.data.objects.new("Body_Adult", mesh)
    bpy.context.collection.objects.link(clean)
    clean.matrix_world = body.matrix_world.copy()
    for group in body.vertex_groups:
        clean.vertex_groups.new(name=group.name)
    clean.parent = rig
    arm = clean.modifiers.new("Reviewed human game rig", "ARMATURE")
    arm.object = rig
    body.hide_render = True
    body.hide_set(True)
    body["authoring_only"] = True
    clean["provenance"] = "MakeHuman core CC0 human base; customized through official MPFB 2.0.17"
    return clean, rig, body


def write_landmark_receipt(body, rig, destination):
    """Actual bone positions make fitting assumptions inspectable and reproducible."""
    points = [body.matrix_world @ v.co for v in body.data.vertices]
    bounds = [[min(p[a] for p in points), max(p[a] for p in points)] for a in range(3)]
    bones = {b.name: {"head": list(rig.matrix_world @ b.head_local),
                       "tail": list(rig.matrix_world @ b.tail_local)} for b in rig.data.bones}
    destination.write_text(json.dumps({"base": str(BASE.relative_to(ROOT)),
        "bounds": bounds, "bones": bones, "mesh_vertices": len(points),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "footwear_ground_offset": .015,
        "status": "Bespoke garment clay study, unintegrated; concept is not an in-game image"}, indent=2))


# ---------- Continuous fitting and editable surface tools ----------
MAT = {}
PI = math.pi


def clay_materials():
    colors = {
        'skin': ('#a88870', .72, 0), 'cloth': ('#33473e', .88, 0),
        'lining': ('#652c27', .85, 0), 'sash': ('#c1b697', .86, 0),
        'steel': ('#404944', .48, .50), 'edge': ('#89816a', .44, .58),
        'leather': ('#4e3227', .76, 0), 'sole': ('#292924', .88, 0),
        'hair': ('#211e1b', .65, 0), 'eye': ('#706655', .6, 0),
        'underwear': ('#5b5548', .9, 0),
    }
    for name,(hexcol,rough,metal) in colors.items():
        m=bpy.data.materials.new('Warden clay block '+name);m.use_nodes=True
        rgb=[int(hexcol[i:i+2],16)/255 for i in (1,3,5)]
        linear=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
        bs=m.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(*linear,1)
        bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
        m.diffuse_color=(*linear,1);MAT[name]=m


def mesh_object(name, vertices, faces, material, uv=None):
    mesh=bpy.data.meshes.new(name+' editable cage');mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    mesh.materials.append(MAT[material])
    for p in mesh.polygons:p.use_smooth=True
    if uv is not None:
        layer=mesh.uv_layers.new(name='GarmentPatternUV')
        for p in mesh.polygons:
            for li in p.loop_indices:layer.data[li].uv=uv[mesh.loops[li].vertex_index]
    ob['slot_contract']=next((s for s in SLOT_PREFIXES if name.startswith(s)),'authoring')
    return ob


def shell(ob, thickness=.004, subdiv=1, bevel=0):
    if subdiv:
        mod=ob.modifiers.new('Editable garment subdivision','SUBSURF');mod.levels=subdiv;mod.render_levels=subdiv
    mod=ob.modifiers.new('Constructed fabric or plate thickness','SOLIDIFY');mod.thickness=thickness;mod.offset=0
    if bevel:
        mod=ob.modifiers.new('Forged edge roundover','BEVEL');mod.width=bevel;mod.segments=2


def armature(ob, rig, weights):
    ob.parent=rig
    for name in {k for row in weights for k in row}:
        group=ob.vertex_groups.new(name=name)
        for i,row in enumerate(weights):
            if row.get(name,0)>.00001:group.add([i],row[name],'REPLACE')
    mod=ob.modifiers.new('Human base deformation','ARMATURE');mod.object=rig


def normalize_body(body, rig, height=1.84):
    from mathutils import Matrix
    world=body.matrix_world.copy();rw=rig.matrix_world.copy()
    vertices=[world@v.co for v in body.data.vertices]
    floor=min(v.z for v in vertices);h=max(v.z for v in vertices)-floor
    transform=Matrix.Scale(height/h,4)@Matrix.Translation((0,0,-floor))
    body.data.transform(transform@world)
    rig.data.transform(transform@rw)
    rig.matrix_world=Matrix.Identity(4);body.matrix_world=Matrix.Identity(4)
    body.data.update();bpy.context.view_layer.update()
    return height/h


class FitSurface:
    def __init__(self, body, rig):
        self.body=body;self.rig=rig
        self.points=[v.co.copy() for v in body.data.vertices]
        self.faces=[tuple(p.vertices) for p in body.data.polygons]
        self.tree=BVHTree.FromPolygons(self.points,self.faces,all_triangles=False)
        self.names={g.index:g.name for g in body.vertex_groups}
        self.weights=[{self.names[g.group]:g.weight for g in v.groups if g.group in self.names and g.weight>.0001} for v in body.data.vertices]
    def bone(self,name,tail=False):
        b=self.rig.data.bones[name];return (b.tail_local if tail else b.head_local).copy()
    def weight(self,p):
        hit=self.tree.find_nearest(Vector(p))
        if hit[0] is None:return {'pelvis':1}
        ids=self.faces[hit[2]];near=sorted(ids,key=lambda i:(self.points[i]-Vector(p)).length_squared)[:3]
        coeff=[1/max(.001,(self.points[i]-Vector(p)).length)**2 for i in near];total=sum(coeff)
        result={}
        for i,c in zip(near,coeff):
            for k,w in self.weights[i].items():result[k]=result.get(k,0)+w*c/total
        total=sum(result.values())
        return {k:v/total for k,v in result.items()} if total else {'pelvis':1}
    def front(self,x,z,pad=.012):
        p,n,index,d=self.tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
        return Vector((x,p.y-pad if p else -.12,z))
    def clear(self,p,clearance=.01):
        co,n,_,d=self.tree.find_nearest(Vector(p))
        if co is not None and (Vector(p)-co).dot(n)<clearance:
            return co+n*clearance
        return Vector(p)


def gauss(x,c,w):return math.exp(-((x-c)/w)**2)
def smoothstep(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def bezier(points,t):
    p=[Vector(v) for v in points]
    while len(p)>1:p=[a.lerp(b,t) for a,b in zip(p,p[1:])]
    return p[0]


def patch(name, rows, mat, rig, fit=None, weight=None, nu=20,nv=22, fold=None, thickness=.004,subdiv=1):
    """Tailored quad pattern from explicit cubic seam curves; no circular profile."""
    verts=[];uv=[];weights=[]
    for j in range(nv+1):
        v=j/nv
        for i in range(nu+1):
            u=i/nu;p=bezier([bezier(row,u) for row in rows],v)
            if fold:p+=Vector(fold(u,v,p))
            if fit:p=fit.clear(p,.006)
            verts.append(p);uv.append((u,v))
            weights.append(weight(p,u,v) if weight else fit.weight(p))
    faces=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(nv) for i in range(nu)]
    ob=mesh_object(name,verts,faces,mat,uv);shell(ob,thickness,subdiv);armature(ob,rig,weights)
    ob['construction']='Individually authored seam-bound quad patch with shaped tension folds'
    return ob


def curve_ribbon(name, path, width, material, rig, fit, thickness=.004, envelope=None, back=False):
    verts=[];uv=[];weights=[];count=36
    for i in range(count+1):
        t=i/count;p=bezier(path,t)
        if 'SweptLock' in name:
            co,normal,_,_=fit.tree.find_nearest(p);p=co+normal*.012
        tangent=(bezier(path,min(1,t+.01))-bezier(path,max(0,t-.01))).normalized()
        # Ribbon follows the vertical/diagonal garment surface rather than a round rope.
        side=tangent.cross(Vector((0,-1,0))).normalized()
        if side.length<.1:side=Vector((1,0,0))
        for q in (-1,1):
            v=p+side*width*.5*q
            if envelope:
                hit=envelope.ray_cast(Vector((v.x,1 if back else -1,v.z)),Vector((0,-1 if back else 1,0)),2)
                if hit[0] is not None:v.y=hit[0].y+(.012 if back else -.012)
            verts.append(v);uv.append(((q+1)/2,t));weights.append(fit.weight(v))
    faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(count)]
    ob=mesh_object(name,verts,faces,material,uv);shell(ob,thickness,1);armature(ob,rig,weights)
    return ob


def region_cage(name, fit, select, displace, material, smooth=7,thickness=.004):
    """Body-derived connected garment topology, re-shaped into actual cloth volume."""
    src=fit.body;faces=[];used=set()
    for poly in src.data.polygons:
        centre=sum((src.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
        totals={}
        for i in poly.vertices:
            for k,w in fit.weights[i].items():totals[k]=totals.get(k,0)+w/len(poly.vertices)
        if select(centre,totals):faces.append(tuple(poly.vertices));used.update(poly.vertices)
    ids=sorted(used);remap={v:i for i,v in enumerate(ids)}
    points=[src.data.vertices[i].co.copy() for i in ids]
    faces=[tuple(remap[i] for i in f) for f in faces]
    neighbors=[set() for _ in points];edge_count={}
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            neighbors[a].add(b);neighbors[b].add(a);edge=tuple(sorted((a,b)));edge_count[edge]=edge_count.get(edge,0)+1
    boundary={i for edge,count in edge_count.items() if count==1 for i in edge}
    for _ in range(smooth):
        points=[p.lerp(sum((points[j] for j in neighbors[i]),Vector())/len(neighbors[i]),.42 if i not in boundary else .12) if neighbors[i] else p for i,p in enumerate(points)]
    ob=mesh_object(name,points,faces,material)
    # Smooth cage normals are used after removing the body's muscle definition.
    normals=[v.normal.copy() for v in ob.data.vertices]
    for j,v in enumerate(ob.data.vertices):
        v.co=displace(v.co.copy(),normals[j],fit.weights[ids[j]])
    ob.data.update()
    shell(ob,thickness,1)
    armature(ob,fit.rig,[fit.weights[i] for i in ids])
    ob['construction']='Continuous body-derived sewn cage; smoothed muscle detail, authored cloth ease and compression'
    return ob


def make_underwear(fit):
    # Always-on modest base clothing. Subdivision is fitted and baked in rest space
    # before the final skin modifier, so it cannot shrink back through the body.
    hip=fit.bone('pelvis').z
    ob=region_cage('Body_Underwear',fit,
        lambda p,w:hip-.165<p.z<hip+.078 and abs(p.x)<.27,
        lambda p,n,w:p+n*.008,'underwear',smooth=3,thickness=.002)
    for mod in ob.modifiers:
        if mod.type in ('ARMATURE','SOLIDIFY'):mod.show_viewport=False
    bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
    mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
    ob.data=mesh
    for mod in list(ob.modifiers):ob.modifiers.remove(mod)
    # The reference is the actual evaluated continuous body, not a proxy primitive.
    for v in mesh.vertices:
        point,normal,_,_=fit.tree.find_nearest(v.co);v.co=point+normal*.010
    # Alternate vertex, edge-midpoint and face-centre constraints. Correcting only
    # face centres can pull neighbouring vertices toward another body surface.
    constraints=[(v.index,) for v in mesh.vertices]
    edges={tuple(sorted((a,b))) for p in mesh.polygons for a,b in zip(tuple(p.vertices),tuple(p.vertices)[1:]+tuple(p.vertices)[:1])}
    constraints.extend(sorted(edges));constraints.extend(tuple(p.vertices) for p in mesh.polygons)
    for iteration in range(12):
        changed=0
        for ids in constraints:
            centre=sum((mesh.vertices[i].co for i in ids),Vector())/len(ids)
            point,normal,_,_=fit.tree.find_nearest(centre);distance=(centre-point).dot(normal)
            if distance<.008:
                push=normal*(.008-distance+.0006)
                for i in ids:mesh.vertices[i].co+=push
                changed+=1
        if not changed:break
    mesh.update()
    samples=[sum((mesh.vertices[i].co for i in ids),Vector())/len(ids) for ids in constraints]
    clearances=[]
    for p in samples:
        co,normal,_,_=fit.tree.find_nearest(p);clearances.append((p-co).dot(normal))
    minimum=min(clearances)
    print('UNDERWEAR_CLEARANCE_DIAGNOSTIC',minimum,'point',list(samples[clearances.index(minimum)]),'iterations',iteration+1,flush=True)
    assert minimum>.003,'Underwear rest clearance failed: '+str(minimum)
    shell(ob,.002,subdiv=0)
    arm=ob.modifiers.new('Human base deformation','ARMATURE');arm.object=fit.rig
    ob['covered_by']='always';ob['permanent_modesty']=True
    ob['minimum_rest_clearance_m']=minimum;ob['clearance_samples']=len(samples)
    print('UNDERWEAR_REST_CLEARANCE',minimum,'samples',len(samples),flush=True)


def make_gloves(fit):
    # One removable fingerless pair, independent of sleeves and vambraces.
    for side in ('l','r'):
        names=['hand_'+side]+[f'{finger}_01_{side}' for finger in ('index','middle','ring','pinky','thumb')]
        region_cage('Gear_Gloves_Fingerless_'+side,fit,
            lambda p,w,names=names:sum(w.get(k,0) for k in names)>.58,
            lambda p,n,w:p+n*.0035,'leather',smooth=2,thickness=.0025)


def make_tunic(fit):
    waist=fit.bone('pelvis').z+.09;neck=fit.bone('neck_01').z
    def choose(p,w):
        hand=sum(v for k,v in w.items() if any(k.startswith(n) for n in ('hand','index','middle','ring','pinky','thumb')))
        return p.z>waist and p.z<neck+.024 and hand<.20
    def shape(p,n,w):
        ease=.007
        for side in ('l','r'):
            elbow=fit.bone('lowerarm_'+side);wrist=fit.bone('hand_'+side)
            upper=w.get('upperarm_'+side,0);lower=w.get('lowerarm_'+side,0)
            axis=(wrist-elbow).normalized();dist=(p-elbow).dot(axis)
            radial=p-elbow-axis*dist
            # Full upper sleeve, crushed fan folds at elbow, narrow secured cuff.
            ease+=(upper+lower)*(.009+.008*gauss(dist,-.06,.13))
            bendplane=radial.normalized().dot(Vector((0,-1,0)))
            ease+=(upper+lower)*(.007*gauss(dist,-.036+radial.z*.4,.036)-.004*gauss(dist,.009,.019)+.006*gauss(dist,.052+radial.z*.4,.030))*bendplane
            ease-=(upper+lower)*.007*smoothstep(.15,.23,dist)
        # Diagonal tension from a bound waist, different left and right.
        if abs(p.x)<.22:
            crease=waist+.10+abs(p.x)*.30
            ease+=.012*gauss(p.z,crease,.028)-.007*gauss(p.z,crease+.038,.015)
        return fit.clear(p+n*ease,.009)
    return region_cage('Gear_Warden_TailoredTunic',fit,choose,shape,'cloth',smooth=10)


def make_trousers(fit):
    waist=fit.bone('pelvis').z+.12
    def choose(p,w):return .375<p.z<waist and abs(p.x)<.38
    def shape(p,n,w):
        side='l' if p.x>0 else 'r';knee=fit.bone('calf_'+side);ankle=fit.bone('foot_'+side)
        ease=.018+.020*gauss(p.z,knee.z+.15,.23)
        ease+=.016*gauss(p.z,knee.z+.055+p.x*.13,.028)-.009*gauss(p.z,knee.z+.013,.019)
        ease+=.018*gauss(p.z,.39+abs(p.x)*.12,.026)-.010*gauss(p.z,.356,.015)
        # Cloth bunches just above the high boot, with a fitted lower section.
        ease*=.4+.6*smoothstep(.30,.45,p.z)
        return fit.clear(p+n*ease,.012)
    return region_cage('Gear_Warden_GatheredTrousers',fit,choose,shape,'cloth',smooth=10)


def make_boots(fit):
    # Last-based footwear: an enclosing upper is built independently of the toe anatomy.
    for side,sign in [('l',1),('r',-1)]:
        ankle=fit.bone('foot_'+side);ball=fit.bone('ball_'+side)
        forward=Vector((ball.x-ankle.x,ball.y-ankle.y,0)).normalized()
        across=Vector((-forward.y,forward.x,0))
        def point(x,d,z):return ankle+across*x+forward*d+Vector((0,0,z-ankle.z))
        # Deliberately broader rounded-square toe, curved waist, enclosed heel counter.
        outline=[(-.039,-.068),(-.051,-.032),(-.047,.050),(-.058,.127),(-.048,.208),
                 (-.034,.237),(.022,.240),(.044,.215),(.058,.151),(.048,.069),(.047,-.028),(.035,-.067)]
        vertices=[]
        for row,(z,inset) in enumerate([(-.012,1),(0.006,1.006),(0.010,.98)]):
            vertices.extend(point(x*inset,d,z+(.013*(1-smoothstep(.018,.095,d)) if row==0 else 0)) for x,d in outline)
        n=len(outline);faces=[]
        for row in range(2):faces.extend((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i) for i in range(n))
        faces.extend([tuple(reversed(range(n))),tuple(2*n+i for i in range(n))])
        sole=mesh_object('Gear_Boots_Sole_'+side,vertices,faces,'sole')
        bevel=sole.modifiers.new('Outsole welt roundover','BEVEL');bevel.width=.003;bevel.segments=2
        armature(sole,fit.rig,[{'foot_'+side:1}]*len(vertices))
        # Heel extends to the ground behind the arch, leaving a visible change of profile.
        heel_poly=[(-.034,-.064),(-.044,-.028),(-.039,.021),(.039,.021),(.043,-.028),(.032,-.064)]
        hv=[point(x,d,z) for z in (-.015,.009) for x,d in heel_poly];hn=len(heel_poly)
        hf=[tuple(reversed(range(hn))),tuple(hn+i for i in range(hn))]+[(i,(i+1)%hn,(i+1)%hn+hn,i+hn) for i in range(hn)]
        heel=mesh_object('Gear_Boots_Heel_'+side,hv,hf,'sole');armature(heel,fit.rig,[{'foot_'+side:1}]*len(hv))
        # A sewn seven-section upper cage encloses all toes without reproducing their separations.
        sections=[(-.063,.031,.108),(-.025,.043,.166),(.022,.045,.192),(.075,.050,.139),(.138,.056,.105),(.205,.042,.083),(.230,.023,.061)]
        verts=[];uv=[];num=10
        for j,(d,width,height) in enumerate(sections):
            for i in range(num+1):
                u=i/num;x=-width*math.cos(u*PI)
                z=.010+(height-.010)*math.sin(u*PI)**.62
                # One genuine broad vamp flex crease, not toe-by-toe bumps.
                z-=.009*gauss(d,.080,.022)*math.sin(u*PI)**2
                verts.append(point(x,d,z));uv.append((u,j/(len(sections)-1)))
        faces=[(j*(num+1)+i,(j+1)*(num+1)+i,(j+1)*(num+1)+i+1,j*(num+1)+i+1) for j in range(len(sections)-1) for i in range(num)]
        faces.extend([tuple(range(num+1)),tuple((len(sections)-1)*(num+1)+i for i in reversed(range(num+1)))])
        upper=mesh_object('Gear_Boots_Last_'+side,verts,faces,'leather',uv);shell(upper,.005,1);armature(upper,fit.rig,[{'foot_'+side:1}]*len(verts))
        # The shaft uses the calf anatomy, but excludes the toe/foot region completely.
        def choose(p,w,side=side,sign=sign):return .13<p.z<.405 and p.x*sign>0
        def shape(p,n,w):return fit.clear(p+n*.019,.015)
        region_cage('Gear_Boots_Shaft_'+side,fit,choose,shape,'leather',smooth=9,thickness=.005)
        # Fitted directional shin shell and leather cuff overlap the shaft rather than a raw cutoff.
        knee=fit.bone('calf_'+side);cx=ankle.x
        rows=[]
        for z,width in [(0.168,.038),(.24,.050),(.345,.060),(.424,.055)]:
            tx=cx+(knee.x-cx)*(z-ankle.z)/(knee.z-ankle.z)
            rows.append([(tx+width*u,-.066-.029*(1-u*u),z+.004*(1-u*u)) for u in (-1,-.33,.33,1)])
        sculpted_plate('Gear_Boots_Greave_'+side,rows,fit,{'calf_'+side:1},nu=14,nv=18)
        for j,z in enumerate((.183,.374)):
            tx=cx+(knee.x-cx)*(z-ankle.z)/(knee.z-ankle.z)
            path=[(tx-.057,-.042,z),(tx-.035,-.090,z+.004),(tx+.037,-.089,z+.004),(tx+.059,-.039,z)]
            curve_ribbon('Gear_Boots_Closure_'+side+str(j),path,.016,'leather',fit.rig,fit,.005)


def skirt_follow(z, waist, side, back=False):
    # Front leaves rotate with the thigh below their hip attachment; back tails stay independent.
    t=smoothstep(.012,.14,waist-z)
    fraction=t*(.32 if back else .96)
    return {'pelvis':1-fraction,'thigh_'+side:fraction}


def make_skirts(fit):
    rig=fit.rig;waist=fit.bone('pelvis').z+.10
    for s in (-1,1):
        side='l' if s>0 else 'r'
        # Narrow split-front leaves: front/side/back are different sewn pieces, not one bell.
        hem=.685 if s>0 else .635
        front=[[(s*.048,-.171,waist),(s*.087,-.187,waist+.009),(s*.15,-.163,waist),(s*.185,-.112,waist-.010)],
               [(s*.055,-.191,waist-.13),(s*.10,-.214,waist-.12),(s*.17,-.184,waist-.14),(s*.205,-.111,waist-.14)],
               [(s*.073,-.209,hem+.105),(s*.12,-.228,hem+.075),(s*.19,-.191,hem+.07),(s*.237,-.103,hem+.12)],
               [(s*.083,-.221,hem+.014),(s*.13,-.237,hem-.02),(s*.205,-.192,hem),(s*.25,-.094,hem+.061)]]
        # Long rear tails remain narrower and staggered; their overlap is behind the front leaves.
        rearhem=.49 if s>0 else .445
        rear=[[(s*.010,.159,waist),(s*.07,.182,waist),(s*.145,.152,waist),(s*.191,.085,waist-.012)],
              [(s*.012,.176,waist-.15),(s*.08,.190,waist-.15),(s*.166,.173,waist-.16),(s*.214,.082,waist-.14)],
              [(s*.026,.191,rearhem+.13),(s*.11,.220,rearhem+.11),(s*.212,.162,rearhem+.13),(s*.267,.050,rearhem+.17)],
              [(s*.033,.202,rearhem+.006),(s*.121,.234,rearhem-.022),(s*.227,.163,rearhem+.018),(s*.282,.041,rearhem+.06)]]
        # Cinch the rear attachment onto the actual back-waist surface, closing the floating rim.
        for i,(x,y,z) in enumerate(rear[0]):
            co,normal,_,_=fit.tree.find_nearest(Vector((x,y,z)))
            rear[0][i]=tuple(co+normal*.016)
        # Side gores cover the seam while showing the offset longer rear lining.
        sidehem=.605 if s>0 else .575
        gore=[[(s*.174,-.092,waist),(s*.196,-.040,waist),(s*.202,.015,waist),(s*.184,.095,waist)],
              [(s*.205,-.090,waist-.14),(s*.223,-.037,waist-.14),(s*.229,.025,waist-.15),(s*.212,.096,waist-.15)],
              [(s*.244,-.075,sidehem+.11),(s*.263,-.020,sidehem+.07),(s*.263,.029,sidehem+.075),(s*.243,.092,sidehem+.10)],
              [(s*.259,-.061,sidehem+.035),(s*.275,-.007,sidehem-.012),(s*.276,.036,sidehem),(s*.253,.09,sidehem+.04)]]
        for pattern in (front,gore):
            for i,(x,y,z) in enumerate(pattern[0]):
                co,normal,_,_=fit.tree.find_nearest(Vector((x,y,z)));pattern[0][i]=tuple(co+normal*.016)
        for label,rows,back in [('front',front,False),('side',gore,False),('back',rear,True)]:
            def fold(u,v,p,s=s,back=back,label=label):
                f=(.014*math.sin(u*PI*2.7+.5)+.005*math.sin(u*PI*5))*math.sin(v*PI*.72)
                if back:
                    # Two sewn pleat valleys widen under gravity, then curl at their free hems.
                    c1=.27+.07*v;c2=.70-.08*v
                    f=(.022*gauss(u,c1-.11,.10)-.020*gauss(u,c1,.045+.025*v)+.027*gauss(u,c1+.12,.12)-.024*gauss(u,c2,.046+.034*v))*(.32+.68*v)
                    f+=.018*math.sin(u*PI*2+.7)*v**3
                if label=='side':return (s*f,0,.004*math.sin(u*PI*2)*v)
                return (s*.005*math.sin(v*PI)*math.sin(u*PI*2),(1 if back else -1)*f,.004*math.sin(u*PI*2)*v)
            weights=lambda p,u,v,back=back,side=side:skirt_follow(p.z,waist,side,back)
            patch(f'Gear_Warden_Skirt_{label}_{s}',rows,'cloth',rig,weight=weights,fold=fold,nu=16,nv=24,thickness=.004)
            lining=[[(x,yy+(-.008 if back else .008),z-.014 if back else z+.004) for x,yy,z in row] for row in rows]
            patch(f'Gear_Warden_Lining_{label}_{s}',lining,'lining',rig,weight=weights,fold=fold,nu=14,nv=22,thickness=.002)


def make_scarf_sash(fit):
    rig=fit.rig;neck=fit.bone('neck_01').z;waist=fit.bone('pelvis').z+.12
    # Diagonal folded scarf, low on one clavicle, leaving a visible neck transition.
    rows=[[(-.069,-.073,neck+.026),(-.022,-.107,neck+.006),(.027,-.099,neck-.015),(.065,-.069,neck-.013)],
          [(-.098,-.099,neck+.002),(-.035,-.135,neck-.033),(.035,-.127,neck-.065),(.108,-.082,neck-.050)],
          [(-.137,-.104,neck-.038),(-.045,-.141,neck-.088),(.023,-.144,neck-.126),(.107,-.105,neck-.080)],
          [(-.126,-.093,neck-.055),(-.046,-.132,neck-.123),(.006,-.134,neck-.148),(.057,-.118,neck-.111)]]
    def scarf_fold(u,v,p):
        valley=.29+.28*u
        f=.010*gauss(v,valley-.15,.075)-.010*gauss(v,valley,.045)+.007*gauss(v,valley+.12,.063)
        return (0,-f,.002*math.sin(u*PI))
    patch('Gear_Warden_DrapedScarf',rows,'cloth',rig,fit=fit,fold=scarf_fold,nu=28,nv=22,thickness=.0025)
    for k in range(3):
        # Wrapped cloth band crosses itself, each pass has a different diagonal pull.
        z=waist+.005+k*.025
        path=[(-.178,-.07,z+.006),(-.12,-.153,z-.022),(.09,-.158,z+.015),(.174,-.085,z+.007)]
        curve_ribbon('Gear_Warden_SashWrap'+str(k),path,.037,'sash',rig,fit,.003)
    # Folded tied ends create a long ivory centre accent with an uneven hem.
    rows=[ [(-.035,-.174,waist+.028),(-.008,-.182,waist+.042),(.021,-.181,waist+.015),(.043,-.17,waist)],
           [(-.045,-.179,waist-.055),(-.018,-.188,waist-.07),(.018,-.178,waist-.08),(.034,-.162,waist-.06)],
           [(-.056,-.225,.66),(-.027,-.241,.62),(.001,-.22,.62),(.034,-.202,.66)],
           [(-.074,-.234,.53),(-.03,-.253,.50),(.012,-.236,.53),(.03,-.207,.55)] ]
    patch('Gear_Warden_IvorySashTail',rows,'sash',rig,weight=lambda p,u,v:{'pelvis':1},fold=lambda u,v,p:(0,.007*math.sin(u*PI*3)*v,0),nu=14,nv=28,thickness=.003)


def sculpted_plate(name,rows,fit,weight,nu=16,nv=12):
    return patch(name,rows,'steel',fit.rig,weight=lambda p,u,v:weight,nu=nu,nv=nv,thickness=.012,subdiv=1)


def make_shoulders(fit):
    for s,side in ((1,'l'),(-1,'r')):
        shoulder=fit.bone('upperarm_'+side);sx=abs(shoulder.x);z=shoulder.z
        # Four longitudinal seam curves define a swept shell with crest, lip and rolled down arm.
        for layer in range(3 if side=='l' else 2):
            d=layer*.041
            rows=[[(s*(sx-.037+d*.18),-.087,z+.052-d),(s*(sx+.01+d*.4),-.131,z+.082-d),(s*(sx+.09+d*.5),-.132,z+.058-d),(s*(sx+.146+d*.6),-.075,z+.013-d)],
                  [(s*(sx-.036+d*.2),-.033,z+.063-d),(s*(sx+.025+d*.4),-.031,z+.113-d),(s*(sx+.108+d*.5),-.023,z+.085-d),(s*(sx+.154+d*.6),-.008,z-.005-d)],
                  [(s*(sx-.037+d*.2),.033,z+.051-d),(s*(sx+.023+d*.4),.052,z+.105-d),(s*(sx+.105+d*.5),.066,z+.07-d),(s*(sx+.158+d*.6),.061,z-.008-d)],
                  [(s*(sx-.04+d*.2),.078,z+.025-d),(s*(sx+.026+d*.4),.112,z+.045-d),(s*(sx+.09+d*.5),.116,z+.03-d),(s*(sx+.15+d*.6),.086,z-.015-d)]]
            sculpted_plate(f'Gear_Warden_SweptPauldron_{side}_{layer}',rows,fit,{'clavicle_'+side:.8,'upperarm_'+side:.2})


def make_lamellar(fit):
    rig=fit.rig;z0=fit.bone('pelvis').z+.20;z1=fit.bone('neck_01').z-.13
    # First shape one continuous chest support panel to real torso sections.
    rows=[]
    for v in (0,.33,.67,1):
        z=z1*(1-v)+z0*v
        width=.17*(1-v)+.15*v
        rows.append([tuple(fit.front(x,z,.032)) for x in (-width,-width*.34,width*.34,width)])
    patch('Gear_Warden_LamellarBacking',rows,'leather',rig,fit=fit,nu=24,nv=24,thickness=.005)
    # Overlap follows a shaped chest surface; small repeat units serve construction.
    for row in range(7):
        v=row/6;z=z1-.013-row*(z1-z0)/7
        width=.167*(1-v)+.145*v
        for col in range(9):
            x=-width+(col+.5)*width*2/9;w=width*2/9*.96
            verts=[];uv=[]
            for j,t in enumerate((0,.16,.80,1)):
                zz=z-t*.063
                for k,u in enumerate((0,.17,.83,1)):
                    xx=x+(u-.5)*w;pt=fit.front(xx,zz,.046)
                    pt.y-=.005*math.sin(u*PI)+.007*(1-t)
                    if j==3:pt.z+=.004*(abs(u-.5)*2)**2
                    verts.append(pt);uv.append((u,t))
            faces=[(j*4+i,j*4+i+1,(j+1)*4+i+1,(j+1)*4+i) for j in range(3) for i in range(3)]
            ob=mesh_object(f'Gear_Warden_ChestLamella_{row:02d}_{col:02d}',verts,faces,'steel',uv)
            shell(ob,.005,0,.0015);armature(ob,rig,[fit.weight(p) for p in verts])
    # Tapered hip tassets align with the separate front coat leaves and the same weight field.
    waist=fit.bone('pelvis').z+.10
    for s in (-1,1):
        side='l' if s>0 else 'r'
        for row in range(5):
            z=waist-.025-row*.060
            columns=4 if row<3 else (3 if row==3 else 2)
            for col in range(columns):
                x=s*(.099+col*.030+row*.006);y=-.209+col*.013
                half=.015
                verts=[(x-s*half*.75,y,z),(x+s*half*.75,y+.004,z+.002),
                       (x+s*half,y+.004,z-.012),(x+s*half,y-.005,z-.061),
                       (x+s*half*.65,y-.008,z-.069),(x-s*half*.72,y-.013,z-.072),
                       (x-s*half,y-.012,z-.059),(x-s*half,y-.005,z-.012)]
                ob=mesh_object(f'Gear_Warden_TassetLamella_{s}_{row}_{col}',verts,[tuple(range(8))],'steel',[(.5+(xx-x)/(half*2),max(0,min(1,(z-zz)/.072))) for xx,yy,zz in verts])
                shell(ob,.005,0,.002);armature(ob,rig,[skirt_follow(p[2],waist,side) for p in verts])

def make_bracers(fit):
    for side in ('l','r'):
        elbow=fit.bone('lowerarm_'+side);wrist=fit.bone('hand_'+side)
        axis=(wrist-elbow).normalized();across=axis.cross(Vector((0,-1,0))).normalized()
        rows=[]
        for t in (.20,.40,.73,.96):
            c=elbow.lerp(wrist,t);width=.06*(1-t)+.038*t
            rows.append([tuple(c+across*width*u+Vector((0,-.040-.021*(1-u*u),0))) for u in (-1,-.33,.33,1)])
        sculpted_plate('Gear_Warden_Vambrace_'+side,rows,fit,{'lowerarm_'+side:1},nu=12,nv=16)


def make_harness(fit):
    # Evaluate only torso clothing and chest/shoulder armor into a fitting envelope.
    bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get();verts=[];faces=[]
    names=('Gear_Warden_TailoredTunic','Gear_Warden_ChestLamella','Gear_Warden_LamellarBacking','Gear_Warden_SweptPauldron')
    for ob in list(bpy.context.scene.objects):
        if ob.type!='MESH' or not ob.name.startswith(names):continue
        ev=ob.evaluated_get(graph);mesh=ev.to_mesh();offset=len(verts)
        verts.extend(ev.matrix_world@v.co for v in mesh.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in mesh.polygons);ev.to_mesh_clear()
    envelope=BVHTree.FromPolygons(verts,faces)
    z0=fit.bone('pelvis').z+.20;z1=fit.bone('neck_01').z-.13
    path=[(-.14,-.16,z1+.032),(-.09,-.21,z1-.060),(.082,-.205,z0+.015),(.144,-.155,z0-.027)]
    curve_ribbon('Gear_Warden_FrontLoadStrap',path,.033,'leather',fit.rig,fit,.006,envelope=envelope)
    for sign in (-1,1):
        path=[(sign*.136,.095,z1+.050),(sign*.095,.151,z1-.045),(-sign*.062,.145,z0+.031),(-sign*.144,.098,z0-.025)]
        curve_ribbon('Gear_Warden_BackHarness_'+str(sign),path,.030,'leather',fit.rig,fit,.006,envelope=envelope,back=True)
        # Over-shoulder continuation connects the back harness to front attachment points.
        path=[(sign*.136,-.12,z1+.038),(sign*.129,-.048,z1+.14),(sign*.134,.052,z1+.13),(sign*.136,.105,z1+.053)]
        curve_ribbon('Gear_Warden_ShoulderStrap_'+str(sign),path,.027,'leather',fit.rig,fit,.006)
    waist=fit.bone('pelvis').z+.12;vertices=[];uv=[];weights=[];n=72
    for j,z in enumerate((waist-.012,waist+.022)):
        for i in range(n+1):
            t=i/n*2*PI;direction=Vector((math.cos(t),math.sin(t),0));start=Vector((direction.x*.31,direction.y*.31,z))
            co,normal,_,_=fit.tree.ray_cast(start,-direction,.31)
            q=co+direction*.024 if co is not None else Vector((direction.x*.17,direction.y*.135,z))
            vertices.append(q);uv.append((i/n,j));weights.append(fit.weight(q))
    faces=[(i,i+1,n+2+i,n+1+i) for i in range(n)]
    belt=mesh_object('Gear_Warden_ContinuousWaistBelt',vertices,faces,'leather',uv);shell(belt,.005,1);armature(belt,fit.rig,weights)


def make_hair(fit,eyes):
    head=fit.bone('head');top=max(p.z for p in fit.points);eye_z=sum(p.z for p in eyes.values())/len(eyes)
    # Connected scalp derived from the actual head, with a temple-sensitive hairline.
    def choose(p,w):
        if p.z<head.z+.04:return False
        front_limit=eye_z+.046+.030*smoothstep(.039,.087,abs(p.x))
        frontal=1-smoothstep(-.092,-.028,p.y)
        limit=(eye_z+.003)*(1-frontal)+front_limit*frontal
        return p.z>limit
    hair=region_cage('Body_Hair_Scalp',fit,choose,lambda p,n,w:p+n*(.006+.003*math.cos(p.x*145+p.z*35)),'hair',smooth=2,thickness=.004)
    # Broad swept masses have a shaped crest and taper into the tie instead of rectangular strips.
    for sign in (-1,1):
        for k in range(4):
            x=sign*(.017+k*.021);start_z=eye_z+.049+.030*smoothstep(.039,.087,abs(x))
            start=fit.front(x,start_z,.009)
            path=[start,(x*1.07,-.082,top+.014),(x*.72,.025,top+.021),(sign*.014,.054,top+.009)]
            verts=[];uv=[];count=32;n=6
            for j in range(count+1):
                t=j/count;p=bezier(path,t);co,normal,_,_=fit.tree.find_nearest(p)
                tangent=(bezier(path,min(1,t+.01))-bezier(path,max(0,t-.01))).normalized()
                across=tangent.cross(normal).normalized();width=(.023+.005*math.sin(t*PI))*(1-.70*t)
                for i in range(n+1):
                    u=i/n;q=co+across*(u-.5)*width
                    surf,norm,_,_=fit.tree.find_nearest(q)
                    q=surf+norm*(.006+.005*math.sin(u*PI)*math.sin(min(1,t*3)*PI/2))
                    verts.append(q);uv.append((u,t))
            faces=[(j*(n+1)+i,j*(n+1)+i+1,(j+1)*(n+1)+i+1,(j+1)*(n+1)+i) for j in range(count) for i in range(n)]
            ob=mesh_object(f'Body_Hair_SweptMass_{sign}_{k}',verts,faces,'hair',uv);shell(ob,.003,1);armature(ob,fit.rig,[{'head':1}]*len(verts))
    # Solid, compact tied mass, not a tall hollow loop.
    sections=[((0,.033,top-.005),.029,.020),((0,.043,top+.012),.026,.020),((.003,.061,top+.039),.025,.021),((.006,.085,top+.043),.021,.019),((.006,.102,top+.024),.015,.015)]
    verts=[];uv=[];n=16
    for j,(c,wx,wy) in enumerate(sections):
        for i in range(n):
            a=i*2*PI/n;verts.append((c[0]+wx*math.cos(a),c[1]+wy*math.sin(a),c[2]));uv.append((i/n,j/(len(sections)-1)))
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(sections)-1) for i in range(n)]
    faces.extend([tuple(reversed(range(n))),tuple((len(sections)-1)*n+i for i in range(n))])
    ob=mesh_object('Body_Hair_TiedMass',verts,faces,'hair',uv);sub=ob.modifiers.new('Bound hair mass smooth','SUBSURF');sub.levels=1;armature(ob,fit.rig,[{'head':1}]*len(verts))
    # One tapered tail supplies the recognisable adult martial silhouette.
    rows=[ [(-.025,.05,top+.042),(-.008,.047,top+.052),(.015,.045,top+.05),(.032,.049,top+.035)],
           [(-.030,.13,top+.064),(-.008,.134,top+.085),(.018,.131,top+.075),(.038,.123,top+.05)],
           [(-.042,.168,top+.006),(-.023,.18,top+.016),(.005,.18,top+.01),(.02,.165,top-.012)],
           [(-.059,.156,top-.107),(-.041,.17,top-.112),(-.026,.163,top-.09),(-.021,.16,top-.063)] ]
    patch('Body_Hair_Tail',rows,'hair',fit.rig,weight=lambda p,u,v:{'head':1},nu=12,nv=20,thickness=.012)


def source_eye_centres(source):
    # MPFB core eye joint cubes are stable anatomical helpers, not guessed eyeball positions.
    core=ROOT/'local/mpfb-trial/extensions/jadebound_local/mpfb/data/3dobjs/base.obj'
    groups={};active=None
    for line in core.read_text().splitlines():
        if line.startswith('g '):active=line[2:].strip()
        elif line.startswith('f ') and active in ('joint-l-eye','joint-r-eye'):
            groups.setdefault(active,set()).update(int(x.split('/')[0])-1 for x in line[2:].split())
    saved=[(m,m.show_viewport) for m in source.modifiers]
    for m,_ in saved:
        if m.type in ('MASK','ARMATURE'):m.show_viewport=False
    bpy.context.view_layer.update();ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get())
    centres={name:sum((source.matrix_world@ev.data.vertices[i].co for i in ids),Vector())/len(ids) for name,ids in groups.items()}
    for m,state in saved:m.show_viewport=state
    bpy.context.view_layer.update()
    return centres


def adult_face(body, eyes):
    # Small continuous vertex edits establish jaw/brow planes without adding attached face pieces.
    ez=sum(p.z for p in eyes.values())/len(eyes)
    for vertex in body.data.vertices:
        p=vertex.co
        if p.z<ez-.17 or abs(p.x)>.115:continue
        front=1-smoothstep(-.04,.035,p.y)
        p.x+=math.copysign(.0038*gauss(p.z,ez-.103,.031)*gauss(abs(p.x),.062,.031),p.x)
        p.y-=front*(.004*gauss(p.z,ez+.022,.015)*gauss(abs(p.x),.034,.030)+.0035*gauss(p.z,ez-.127,.019)*gauss(p.x,0,.040))
        p.y+=front*.0025*gauss(p.z,ez-.045,.022)*gauss(abs(p.x),.055,.018)
    body.data.update()


def make_eyes(fit,eyes):
    for name,p in eyes.items():
        # Subdued sclera clay. Eyelids from the continuous base occlude most of each sphere.
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=.0108,location=p)
        eye=bpy.context.object;eye.name='Body_Eye_'+name[-5:];eye.data.materials.append(MAT['eye'])
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        for poly in eye.data.polygons:poly.use_smooth=True
        armature(eye,fit.rig,[{'head':1}]*len(eye.data.vertices))


def supported_knee_pose(rig):
    # Diagnostic only: explicit world-space two-bone solution, both soles remain supported.
    pelvis=rig.pose.bones['pelvis'];mat=pelvis.matrix.copy();mat.translation+=Vector((0,-.035,-.065));pelvis.matrix=mat
    bpy.context.view_layer.update()
    for side in ('l','r'):
        thigh=rig.pose.bones['thigh_'+side];calf=rig.pose.bones['calf_'+side];foot=rig.pose.bones['foot_'+side]
        hip=thigh.head.copy();target=rig.data.bones['foot_'+side].head_local.copy()
        target.y+=-.15 if side=='l' else .06
        a=rig.data.bones[thigh.name].length;b=rig.data.bones[calf.name].length
        axis=(target-hip).normalized();distance=min(a+b-.001,(target-hip).length)
        along=(a*a-b*b+distance*distance)/(2*distance);h=math.sqrt(max(0,a*a-along*along))
        bend=Vector((0,-1,0));bend=(bend-axis*bend.dot(axis)).normalized();knee=hip+axis*along+bend*h
        for pb,start,end in ((thigh,hip,knee),(calf,knee,target)):
            bone=pb.bone;old=(bone.tail_local-bone.head_local).normalized()
            q=old.rotation_difference((end-start).normalized())@bone.matrix_local.to_quaternion()
            pb.matrix=Matrix.Translation(start)@q.to_matrix().to_4x4();bpy.context.view_layer.update()
        foot.matrix=Matrix.Translation(foot.head)@foot.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
        bpy.context.view_layer.update()


def studio():
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=800;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.21,.20,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    scene.view_settings.view_transform='AgX'
    bpy.ops.object.camera_add(location=(3,-6,2.9));camera=bpy.context.object;camera.name='STUDY_Camera';camera.rotation_euler=(Vector((0,0,1.00))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=2.32;scene.camera=camera
    for i,(loc,power,size) in enumerate([((3,-4,5),500,4),((-3,-2,3),250,3),((0,3,4),380,3)]):
        bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.name='STUDY_Light_'+str(i);light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));floor=bpy.context.object;floor.name='STUDY_Floor'
    m=bpy.data.materials.new('Study neutral floor');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.12,.13,.12,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9;floor.data.materials.append(m)
    return scene


def partition_body(fit):
    # Every source face belongs to exactly one reversible runtime region. No anatomy is deleted.
    body=fit.body;groups={};neck=fit.bone('neck_01').z;hip=fit.bone('pelvis').z
    handnames=[f'{name}_{side}' for side in ('l','r') for name in ['hand','index_01','middle_01','ring_01','pinky_01','thumb_01']]
    for poly in body.data.polygons:
        p=sum((body.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
        w={}
        for i in poly.vertices:
            for k,v in fit.weights[i].items():w[k]=w.get(k,0)+v/len(poly.vertices)
        if p.z>neck+.024:region='Body_Head'
        elif sum(w.get(k,0) for k in handnames)>.58:region='Body_Hands'
        elif sum(v for k,v in w.items() if k.startswith(('hand','index','middle','ring','pinky','thumb')))>.20:region='Body_Fingers'
        elif sum(v for k,v in w.items() if k.startswith(('upperarm','lowerarm')))>.30 and abs(p.x)>.15:region='Body_Arms'
        elif sum(v for k,v in w.items() if k.startswith(('foot','ball')))>.50:region='Body_Feet'
        elif p.z<hip+.035 or sum(v for k,v in w.items() if k.startswith(('thigh','calf')))>.45:
            region='Body_LowerLegs' if p.z<.385 else 'Body_UpperLegs'
        else:region='Body_Torso'
        groups.setdefault(region,[]).append(poly.index)
    coverage={'Body_Torso':'armor','Body_Arms':'armor','Body_UpperLegs':'armor',
              'Body_Hands':'gloves','Body_LowerLegs':'boots','Body_Feet':'boots'}
    count=0
    for name,polys in groups.items():
        ids=sorted({i for pi in polys for i in body.data.polygons[pi].vertices});mapping={old:new for new,old in enumerate(ids)}
        faces=[tuple(mapping[i] for i in body.data.polygons[pi].vertices) for pi in polys]
        ob=mesh_object(name,[body.data.vertices[i].co for i in ids],faces,'skin')
        # Per-loop UVs preserve original seams exactly despite shared vertex positions.
        for old_uv in body.data.uv_layers:
            uv=ob.data.uv_layers.new(name=old_uv.name)
            for newpoly,oldpi in zip(ob.data.polygons,polys):
                for newli,oldli in zip(newpoly.loop_indices,body.data.polygons[oldpi].loop_indices):uv.data[newli].uv=old_uv.data[oldli].uv
        if hasattr(ob.data,'normals_split_custom_set_from_vertices'):
            ob.data.normals_split_custom_set_from_vertices([body.data.vertices[i].normal[:] for i in ids])
        armature(ob,fit.rig,[fit.weights[i] for i in ids]);ob['covered_by']=coverage.get(name,'always')
        ob['restore_on_unequip']=True;ob['source_face_count']=len(polys);count+=len(polys)
    assert count==len(body.data.polygons),'Regional body partition lost or duplicated faces'
    body['partition_face_count']=count;body.name='AUTHORING_ContinuousAdult';body.hide_render=True;body.hide_set(True)
    return groups


def export_study(args, body, rig, source):
    args.output.mkdir(parents=True,exist_ok=True)
    write_landmark_receipt(body,rig,args.output/'construction_receipt.json')
    bpy.ops.object.select_all(action='DESELECT')
    for ob in bpy.context.scene.objects:
        if ob.type=='MESH' and any(ob.name.startswith(p) for p in SLOT_PREFIXES):ob.hide_set(False);ob.select_set(True)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.export_scene.gltf(filepath=str(args.output/'river_warden_clay.glb'),export_format='GLB',use_selection=True,export_animations=False,export_apply=True,export_yup=True,export_extras=True)
    scene=studio()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'river_warden_clay.blend'))
    if args.render:
        scene.render.filepath=str(args.output/'clay-block-values.png');bpy.ops.render.render(write_still=True)
        clay=bpy.data.materials.new('Neutral form-only clay');clay.use_nodes=True;bs=clay.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.31,.30,.28,1);bs.inputs['Roughness'].default_value=.85
        scene.view_layers[0].material_override=clay
        camera=scene.camera;front_matrix=camera.matrix_world.copy()
        camera.location=(-3,6,2.7);camera.rotation_euler=(Vector((0,0,1.02))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(args.output/'clay-form-only.png');bpy.ops.render.render(write_still=True)
        camera.matrix_world=front_matrix
        supported_knee_pose(rig)
        scene.render.filepath=str(args.output/'clay-bent-knee.png');bpy.ops.render.render(write_still=True)
        scene.view_layers[0].material_override=None
    print('CONCEPT_WARDEN_CLAY_STUDY_EXPORTED',str(args.output),flush=True)


def main():
    args=parse_args()
    if bpy.app.online_access:print('No network operations are used; run with --offline-mode for enforcement',flush=True)
    body,rig,source=open_cc0_base(args.base)
    eyes=source_eye_centres(source)
    floor=min((body.matrix_world@v.co).z for v in body.data.vertices)
    scale=normalize_body(body,rig)
    eyes={k:Vector((p.x*scale,p.y*scale,(p.z-floor)*scale)) for k,p in eyes.items()}
    adult_face(body,eyes)
    rig.name='ConceptWardenRig'
    clay_materials();body.data.materials.clear();body.data.materials.append(MAT['skin'])
    for p in body.data.polygons:p.material_index=0;p.use_smooth=True
    fit=FitSurface(body,rig)
    make_eyes(fit,eyes);make_underwear(fit);make_gloves(fit)
    make_tunic(fit);make_trousers(fit);make_boots(fit);make_skirts(fit)
    make_scarf_sash(fit);make_shoulders(fit);make_lamellar(fit);make_bracers(fit);make_harness(fit);make_hair(fit,eyes)
    partition_body(fit)
    # Lift the complete rig/skin together to accommodate the genuine sole below the anatomical foot.
    rig.location.z=.015
    bpy.context.view_layer.update()
    # Weapon and alternate helmet are intentionally not modeled in this garment gate.
    export_study(args,body,rig,source)


if __name__=='__main__':main()
