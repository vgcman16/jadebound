#!/usr/bin/env python3
"""Original weathered approach: modeled chipped stone, clustered vegetation and timber.
Blender 4.3+: --background --threads 2 --python tools/generate_courtyard_detail.py -- --output .
No reference pixels, downloaded textures, add-ons or rendering are used.
"""
import argparse, math, random, struct, sys, zlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
R=random.Random(98451)
M={}; OBJECTS=[]

def png(path,rgb):
    rgb=np.uint8(np.clip(rgb,0,1)*255);h,w,_=rgb.shape
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    rows=b''.join(b'\0'+rgb[y].tobytes() for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows,7))+chunk(b'IEND',b''))

def texture_set(kind,out):
    n=512;y,x=np.mgrid[0:n,0:n]/n
    rng=np.random.default_rng(810+len(kind));grain=rng.random((n,n))-.5
    def field(nx,ny):
        values=rng.random((ny+1,nx+1));values[-1]=values[0];values[:,-1]=values[:,0]
        px=x*nx;py=y*ny;ix=np.floor(px).astype(int);iy=np.floor(py).astype(int)
        fx=px-ix;fy=py-iy;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
        return ((values[iy,ix]*(1-fx)+values[iy,ix+1]*fx)*(1-fy)+(values[iy+1,ix]*(1-fx)+values[iy+1,ix+1]*fx)*fy)-.5
    broad=field(5,5)*1.6+field(13,13)*.65
    medium=field(37,37)
    fine=field(117,117)
    if kind=='stone':
        pits=np.maximum(0,fine-.20)
        h=.11*broad+.025*medium-.018*pits
        tone=.285+.115*broad+.035*medium-.055*pits+.012*grain
        rgb=np.stack((tone*.98,tone,tone*1.015),-1);rough=.83+.10*broad+.035*grain
    elif kind=='wood':
        long_grain=field(79,4);grooves=np.maximum(0,long_grain+.03)
        knots=np.exp(-((x-.31)**2/.006+(y-.62)**2/.020))
        h=.020*long_grain-.025*grooves-.012*knots
        tone=.205+.030*broad-.11*grooves-.025*knots+.012*grain
        rgb=np.stack((tone*1.20,tone,tone*.81),-1);rough=.72+.15*grooves+.025*grain
    elif kind=='plaster':
        pits=np.maximum(0,fine-.29)
        h=.035*broad+.009*medium-.014*pits
        tone=.39+.055*broad+.025*medium-.13*pits
        rgb=np.stack((tone*1.04,tone*1.015,tone*.94),-1);rough=.93+.025*grain
    else:
        grit=np.maximum(0,fine-.23)
        h=.045*broad+.019*medium+.01*fine
        tone=.205+.07*broad+.030*medium-.055*grit+.018*grain
        rgb=np.stack((tone*1.15,tone,tone*.77),-1);rough=.94+.025*grain
    dy,dx=np.gradient(h);normal=np.stack((-dx*70,-dy*70,np.ones_like(h)),-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    maps={}
    for name,data,space in [('albedo',rgb,'sRGB'),('normal',normal*.5+.5,'Non-Color'),('roughness',np.stack([rough]*3,-1),'Non-Color')]:
        path=out/f'jb_courtyard_{kind}_{name}.png';png(path,data)
        image=bpy.data.images.load(str(path),check_existing=False);image.name=path.stem;image.colorspace_settings.name=space;image.pack();image.filepath_raw=''
        maps[name]=image
    return maps

def fitted_stone_atlas(out):
    """Four slab-face UV islands. Wear follows real slab boundaries, not world noise."""
    source=out/'jb_limestone_source.png'
    if not source.exists():raise RuntimeError('Original limestone source texture missing')
    im=bpy.data.images.load(str(source),check_existing=False)
    im.colorspace_settings.name='Non-Color'
    sw,sh=im.size
    pixels=np.empty(sw*sh*4,dtype=np.float32);im.pixels.foreach_get(pixels)
    base=pixels.reshape(sh,sw,4)[:,:,:3].copy()
    bpy.data.images.remove(im)
    n=1024;cell=512
    albedo=np.zeros((n,n,3),dtype=np.float32);height=np.zeros((n,n),dtype=np.float32);rough=np.zeros((n,n),dtype=np.float32)
    vv,uu=np.mgrid[0:cell,0:cell]/(cell-1)
    edge=np.minimum.reduce([uu,vv,1-uu,1-vv])
    rim=np.exp(-((edge-.043)/.018)**2)
    underlap=np.clip((.029-edge)/.029,0,1)
    # A restrained moss/dirt crescent is restricted to one physical slab edge.
    for tile in range(4):
        x0=(tile%2)*cell;y0=(tile//2)*cell
        sx=((uu*.49+(tile%2)*.43+.025)* (sw-1)).astype(int)
        sy=((vv*.49+(tile//2)*.43+.025)*(sh-1)).astype(int)
        patch=base[sy,sx].copy()
        if tile%2:patch=patch[:,::-1]
        if tile==2:patch=patch[::-1]
        luminance=patch@np.array([.299,.587,.114])
        blur=sum(np.roll(np.roll(luminance,dy,0),dx,1) for dx,dy in [(0,0),(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,2),(-2,2),(2,-2)])/9
        pores=np.clip((blur-luminance)*2.5,0,.20)
        joint_soil=np.clip((.10-vv)/.10,0,1)*(0.35+0.65*uu) if tile in (1,3) else underlap*.35
        paint=patch*(1-underlap[:,:,None]*.42)
        paint=paint*(1-joint_soil[:,:,None]*.18)
        paint+=rim[:,:,None]*np.array([.075,.074,.063])
        # Low-level mineral structure comes from original albedo; authored edge masks supply cavity/arris relief.
        h=(luminance-blur)*.003-pores*.004-underlap*.012+rim*.003
        albedo[y0:y0+cell,x0:x0+cell]=paint
        height[y0:y0+cell,x0:x0+cell]=h
        rough[y0:y0+cell,x0:x0+cell]=np.clip(.83+pores*.4+joint_soil*.08-rim*.11,.65,.98)
    dy,dx=np.gradient(height);normal=np.stack((-dx*160,-dy*160,np.ones_like(height)),-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    maps={}
    for channel,data,space in [('albedo',albedo,'sRGB'),('normal',normal*.5+.5,'Non-Color'),('roughness',np.stack([rough]*3,-1),'Non-Color')]:
        path=out/f'jb_fitted_flagstone_{channel}.png';png(path,np.flipud(data))
        image=bpy.data.images.load(str(path),check_existing=False);image.name=path.stem;image.colorspace_settings.name=space;image.pack();image.filepath_raw='';maps[channel]=image
    return maps

def material(name,kind,tint=(1,1,1),metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*tint,1);bs.inputs['Roughness'].default_value=.8;bs.inputs['Metallic'].default_value=metal
    if kind:
        for channel in ['albedo','roughness','normal']:
            t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=TEXTURES[kind][channel]
            if channel=='normal':
                node=m.node_tree.nodes.new('ShaderNodeNormalMap');node.inputs['Strength'].default_value=.32
                m.node_tree.links.new(t.outputs['Color'],node.inputs['Color']);m.node_tree.links.new(node.outputs['Normal'],bs.inputs['Normal'])
            else:m.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color' if channel=='albedo' else 'Roughness'])
    m.diffuse_color=(*tint,1);M[name]=m;return m

def pos(x,z,h):return (x,-z,h)
def own(ob,name,mat):
    ob.name=name;ob.data.materials.append(M[mat]);OBJECTS.append(ob);return ob

def uv_project(ob,scale=.7):
    uv=ob.data.uv_layers.new(name='OriginalSurfaceUV') if not ob.data.uv_layers else ob.data.uv_layers[0]
    for face in ob.data.polygons:
        axis=max(range(3),key=lambda a:abs(face.normal[a]))
        for li in face.loop_indices:
            v=ob.data.vertices[ob.data.loops[li].vertex_index].co+ob.location
            pair=(v.x,v.y) if axis==2 else ((v.x,v.z) if axis==1 else (v.y,v.z))
            uv.data[li].uv=(pair[0]*scale,pair[1]*scale)

def mesh(name,verts,faces,mat,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);own(ob,name,mat)
    for p in me.polygons:p.use_smooth=smooth
    uv_project(ob);return ob

def box(name,center,size,mat,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos(*center));ob=own(bpy.context.object,name,mat)
    # size uses world X/Z/up, then is baked into Blender X/Y/Z vertices.
    for v in ob.data.vertices:v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
    ob.data.update();uv_project(ob)
    if bevel:
        mod=ob.modifiers.new('Rounded worn arris','BEVEL');mod.width=bevel;mod.segments=2
        bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=ob.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL');mod.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=mod.name)
    return ob

def slab(name,x,z,w,d,top=0,thickness=.15):
    c=[R.uniform(.008,.035) for _ in range(4)]
    if R.random()<.23:c[R.randrange(4)]=R.uniform(.045,.09)
    pts=[(-w/2+c[0],-d/2),(w/2-c[1],-d/2),(w/2,-d/2+c[1]),(w/2,d/2-c[2]),(w/2-c[2],d/2),(-w/2+c[3],d/2),(-w/2,d/2-c[3]),(-w/2,-d/2+c[0])]
    a=R.uniform(-.035,.035);ca,sa=math.cos(a),math.sin(a)
    pts=[(u*ca-v*sa+R.uniform(-.016,.016),u*sa+v*ca+R.uniform(-.016,.016)) for u,v in pts]
    verts=[]
    for ring in range(3):
        inset=.025 if ring==2 else 0
        for u,v in pts:
            factor=1-inset/max(w,d)
            verts.append(pos(x+u*factor,z+v*factor,top+(-thickness if ring==0 else (-.025 if ring==1 else R.uniform(-.006,.004)))))
    verts.append(pos(x,z,top-.002));faces=[]
    for ring in range(2):
        for i in range(8):faces.append((ring*8+i,ring*8+(i+1)%8,(ring+1)*8+(i+1)%8,(ring+1)*8+i))
    for i in range(8):faces.append((16+i,16+(i+1)%8,24))
    ob=mesh(name,verts,[tuple(reversed(f)) for f in faces],'fitted flagstone')
    tile=zlib.crc32(('%s/%.3f/%.3f'%(name,x,z)).encode())%4
    uv=ob.data.uv_layers[0]
    ob.data.materials.append(M['weathered stone'])
    for poly in ob.data.polygons:
        top_face=poly.normal.z>.9
        if not top_face:poly.material_index=1
        for li in poly.loop_indices:
            co=ob.data.vertices[ob.data.loops[li].vertex_index].co
            if top_face:
                dx=co.x-x;dz=-co.y-z
                u=np.clip((dx*ca+dz*sa)/w+.5,0,1);v=np.clip((-dx*sa+dz*ca)/d+.5,0,1)
                uv.data[li].uv=((tile%2+.012+u*.976)/2,(tile//2+.012+v*.976)/2)
            else:
                along=co.y if abs(poly.normal.x)>abs(poly.normal.y) else co.x
                uv.data[li].uv=(along*.7,co.z*.7)
    return ob

def rock(name,x,z,scale):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);ob=own(bpy.context.object,name,'weathered stone')
    phase=R.uniform(0,6)
    for v in ob.data.vertices:
        p=v.co;ridge=1+.14*math.sin(p.x*5+p.z*3+phase)+.09*math.cos(p.y*7-p.z*4)
        p.x*=scale[0]*ridge;p.y*=scale[1]*ridge;p.z=max(-.18*scale[2],p.z*scale[2]*(1+.1*math.cos(p.x*8)))
    ob.location=pos(x,z,scale[2]*.20-.035);ob.rotation_euler.z=R.uniform(0,math.tau)
    for p in ob.data.polygons:p.use_smooth=True
    ob.data.update();uv_project(ob,.55)
    return ob

def grass_cluster(x,z,radius=.25,amount=13):
    verts=[];faces=[]
    for i in range(amount):
        theta=R.uniform(0,math.tau);r=radius*math.sqrt(R.random());cx=x+math.cos(theta)*r;cz=z+math.sin(theta)*r
        height=R.uniform(.17,.41);width=R.uniform(.015,.030);lean=R.uniform(.07,.17);direction=R.uniform(0,math.tau)
        vx=math.cos(direction)*width;vz=math.sin(direction)*width;lx=math.cos(theta)*lean;lz=math.sin(theta)*lean;k=len(verts)
        verts.extend([pos(cx-vx,cz-vz,-.022),pos(cx+vx,cz+vz,-.022),pos(cx+lx*.35-vx*.5,cz+lz*.35-vz*.5,height*.55),pos(cx+lx*.35+vx*.5,cz+lz*.35+vz*.5,height*.55),pos(cx+lx,cz+lz,height)])
        faces.extend([(k,k+1,k+3,k+2),(k+2,k+3,k+4)])
    ob=mesh('Clustered reed grass',verts,faces,R.choice(['grass olive','grass dry','grass shadow']))
    return ob

def scene_patch():
    # Fitted stonework uses mixed runs and widths, missing edge stones and sunk arrises.
    index=0
    z=-5.2;row=0
    while z<3.0:
        depth=R.choice([.57,.64,.78]);x=-7.9-(.45 if row%2 else 0)
        while x<-.45:
            width=R.choice([.82,1.10,1.42])
            edge=x<-7.45 or x+width>-.8 or z>2.4
            if x+width>-7.8 and (not edge or R.random()>.24):
                slab('Laid bonded flagstone %03d'%index,x+width*.5,z+depth*.5,width-.034,depth-.033,top=R.uniform(-.047,-.032));index+=1
            x+=width
        z+=depth;row+=1
    # A worn continuation is broken into sparse groups rather than a stepping-stone zipper.
    for i in range(25):
        t=R.random();x=.4+t*9;z=1.4+t*3.4+R.uniform(-.7,.7)
        slab('Embedded approach stone',x,z,R.uniform(.45,.82),R.uniform(.4,.7),top=-.04)
    # Boundary stones and two very shallow entry steps, outside the open action lane.
    for row in range(3):
        for x in [-8.3,-7.3,-6.3,-2.7,-1.7,-.7]:
            box('Layered boundary masonry',(x+(row%2)*.1,-6.15,row*.27+.11),(.92,.47,.24),'weathered stone',.035)
    for x in [-8.4,-7.35,-6.3,-2.7,-1.65,-.6]:box('Boundary cap',(x,-6.15,.88),(1.05,.58,.13),'weathered stone',.035)
    slab('Broad first entry tread',-4.5,-5.0,3.4,.60,top=.06,thickness=.17)
    slab('Broad second entry tread',-4.5,-5.48,3.2,.61,top=.15,thickness=.23)
    slab('Raised threshold landing',-4.5,-6.02,3.0,.90,top=.26,thickness=.34)
    # L-shaped connected boundary gives the approach a near/mid/far spatial frame.
    for z in [-5.4,-4.35,-3.3,-2.25,-1.2,-.15,.9,1.95]:
        for row in range(2):box('Returning low courtyard wall',(-8.12,z+(row%2)*.05,row*.28+.12),(.46,1.0,.25),'weathered stone',.028)
        box('Returning wall coping',(-8.12,z,.65),(.59,1.07,.12),'weathered stone',.025)
    # One deep, closed timber entrance with split panels and inset lattice cavities.
    for x in [-5.72,-3.28]:
        box('Stone column footing',(x,-6.64,.28),(.51,.64,.55),'weathered stone',.05)
        box('Worn entrance upright',(x,-6.65,1.6),(.24,.32,2.8),'weathered timber',.026)
        box('Column collar',(x,-6.65,2.88),(.38,.45,.20),'weathered timber',.025)
    box('Entrance lintel',(-4.5,-6.64,3.05),(3.12,.39,.30),'weathered timber',.035)
    box('Door cavity',(-4.5,-6.88,1.6),(2.15,.16,2.72),'deep cavity',.015)
    for i in range(10):
        x=-5.51+i*.225
        box('Fitted door board',(x,-6.75,1.15),(.215,.095,1.72),'weathered timber',.014)
    for side in [-1,1]:
        cx=-4.5+side*.56
        box('Door cross brace',(cx,-6.66,1.83),(1.0,.07,.09),'weathered timber',.008)
        box('Door cross brace',(cx,-6.66,.49),(1.0,.07,.09),'weathered timber',.008)
        for i in range(5):box('Recessed lattice vertical',(cx-.39+i*.195,-6.70,2.37),(.035,.06,.67),'weathered timber',.007)
        for i in range(4):box('Recessed lattice horizontal',(cx,-6.66,2.07+i*.19),(.84,.055,.032),'weathered timber',.006)
        box('Aged iron handle',(cx-side*.32,-6.58,1.30),(.045,.055,.21),'dark iron',.009)
    # Worn plaster returns have separate footings and framing, not a single flat plane.
    for x in [-7.15,-1.85]:
        box('Recessed lime plaster',(x,-6.98,1.72),(2.0,.24,2.6),'worn lime plaster',.065)
        box('Plaster sill',(x,-6.80,.52),(2.0,.34,.19),'weathered stone',.04)
        box('Timber wall eave',(x,-6.90,3.04),(2.18,.48,.21),'weathered timber',.025)
    # Thin overlapping canopy courses, two slopes, shaped by real tile strips.
    for side in [-1,1]:
        for row in range(5):
            t=row/4;z=-6.85+side*t*.83;h=3.59-.42*t+.08*t*t
            for col in range(16):
                ob=box('Canopy slate tile',(-6.24+col*.232,z,h),(.226,.26,.045),'roof slate',.014)
                ob.rotation_euler.x=side*.40
    box('Canopy ridge',(-4.5,-6.85,3.64),(3.84,.14,.16),'roof slate',.025)
    # Purposeful edge ecologies: rocks, tuft groups and little chips at structural bases.
    centers=[(-8.9,2.7),(-8.8,-3.7),(-7.6,3.5),(-1.1,-4.8),(.7,-2.1),(1.3,3.5),(6.8,2.4),(9.4,6.0)]
    for i,(x,z) in enumerate(centers):
        rock('Weathered shoulder boulder',x,z,(R.uniform(.38,.72),R.uniform(.30,.58),R.uniform(.35,.60)))
        for j in range(4):
            a=R.random()*math.tau;r=R.uniform(.45,.9);px=x+math.cos(a)*r;pz=z+math.sin(a)*r
            rock('Ground-set stone chip',px,pz,(R.uniform(.08,.23),R.uniform(.08,.19),R.uniform(.08,.17)))
        for j in range(12):
            a=R.random()*math.tau;r=R.uniform(.4,1.1);grass_cluster(x+math.cos(a)*r,z+math.sin(a)*r,R.uniform(.12,.25),R.randint(8,15))
    # Thick visible roots connect the framing tree, low wall and earth shoulder.
    for side in [-1,0,1]:
        verts=[];faces=[]
        for j in range(12):
            t=j/11;x=-9.0+t*(1.15+side*.25);z=3.4-t*(1.2+side*.40)
            height=.045+.13*(1-t);radius=.16*(1-t)+.023
            for k in range(10):
                ang=k*math.tau/10
                verts.append(pos(x+math.cos(ang)*radius,z+math.sin(ang)*radius*.75,height+math.sin(ang)*radius*.45))
        for j in range(11):
            for k in range(10):faces.append((j*10+k,j*10+(k+1)%10,(j+1)*10+(k+1)%10,(j+1)*10+k))
        mesh('Tree root into courtyard shoulder',verts,faces,'weathered timber',True)
    for i in range(18):grass_cluster(R.uniform(-8.7,-7.8),R.uniform(-5.7,2.6),.12,8)

def export_material_samples(path):
    originals=[o for o in OBJECTS if o.name.startswith('Laid bonded flagstone')][:4]
    copies=[]
    bpy.ops.object.select_all(action='DESELECT')
    for i,original in enumerate(originals):
        ob=original.copy();ob.data=original.data.copy();bpy.context.collection.objects.link(ob)
        xs=[v.co.x for v in ob.data.vertices];ys=[v.co.y for v in ob.data.vertices]
        cx=(min(xs)+max(xs))*.5;cy=(min(ys)+max(ys))*.5
        w=max(xs)-min(xs);d=max(ys)-min(ys)
        targetx=(-w*.5-.02 if i%2==0 else w*.5+.02);targety=(-d*.5-.02 if i//2==0 else d*.5+.02)
        for vertex in ob.data.vertices:vertex.co.x+=targetx-cx;vertex.co.y+=targety-cy
        ob.name='Actual slab sample %d'%i;ob.select_set(True);copies.append(ob)
    bpy.context.view_layer.objects.active=copies[0]
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_animations=False)
    for ob in copies:bpy.data.objects.remove(ob,do_unlink=True)

def batch_export(path):
    # Retain editable authored parts in .blend; material-batch a disposable export copy.
    copies=[]
    for material_ in M.values():
        group=[o for o in OBJECTS if o.type=='MESH' and o.data.materials[0]==material_]
        if not group:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in group:
            clone=o.copy();clone.data=o.data.copy();bpy.context.collection.objects.link(clone);clone.select_set(True)
            last=clone
        bpy.context.view_layer.objects.active=last;bpy.ops.object.join();joined=bpy.context.object;joined.name='Courtyard '+material_.name
        copies.append(joined)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in copies:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_animations=False,export_extras=True)
    for ob in list(copies):
        if ob.name in bpy.data.objects:bpy.data.objects.remove(ob,do_unlink=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='.');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    output=Path(args.output).resolve();tex=output/'game/assets/textures/courtyard';tex.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    TEXTURES={kind:texture_set(kind,tex) for kind in ['stone','wood','plaster','earth']}
    TEXTURES['flagstone']=fitted_stone_atlas(tex)
    material('fitted flagstone','flagstone');material('weathered stone','stone');material('weathered timber','wood');material('worn lime plaster','plaster')
    material('deep cavity',None,(.018,.026,.025));material('dark iron',None,(.055,.064,.063),.65)
    material('roof slate',None,(.052,.074,.088));material('grass olive',None,(.082,.108,.032));material('grass dry',None,(.16,.17,.066));material('grass shadow',None,(.041,.065,.026))
    scene_patch()
    path=output/'game/assets/models/courtyard_detail.glb';path.parent.mkdir(parents=True,exist_ok=True)
    export_material_samples(output/'game/assets/models/flagstone_samples.glb')
    batch_export(path)
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'art/jadebound_courtyard_detail.blend'))
    print('JADE_COURTYARD_DETAIL_COMPLETE',len(OBJECTS),'authored pieces',path)
