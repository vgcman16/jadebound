#!/usr/bin/env python3
"""Standalone, read-only UV/skin/rig audit for the published human authoring master.
Requires Python 3.11+ and NumPy (tested with 2.3.5). No Blender, server, render,
network access, unpublished experimental artifacts or credentials are needed.
"""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib,json,struct,math,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'art/river-warden-uv'
BODY={'Body_Head','Body_Torso','Body_Arms','Body_Hands','Body_Fingers','Body_UpperLegs','Body_LowerLegs','Body_Feet'}
def load_glb(path):
    import numpy as np
    raw=Path(path).read_bytes();length=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+length]);start=20+length;binary=raw[start+8:]
    types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'};sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
    def get(i):
        a=j['accessors'][i];view=j['bufferViews'][a['bufferView']];dtype=np.dtype(types[a['componentType']]);n=sizes[a['type']];stride=view.get('byteStride',dtype.itemsize*n)
        return np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=view.get('byteOffset',0)+a.get('byteOffset',0),strides=(stride,dtype.itemsize)).copy()
    return j,get

def canonical_mesh(node,j,get):
    import numpy as np
    skin=j['skins'][node['skin']];bone_names=[j['nodes'][i]['name'] for i in skin['joints']];records=[];vertex_count=0;bodyuv=[]
    for prim in j['meshes'][node['mesh']]['primitives']:
        at=prim['attributes'];pos=get(at['POSITION']);norm=get(at['NORMAL']);weights=get(at['WEIGHTS_0']);joints=get(at['JOINTS_0']);uv=get(at['TEXCOORD_0']) if 'TEXCOORD_0' in at else None
        tokens=[];uvtokens=[];vertex_count+=len(pos)
        for i in range(len(pos)):
            named=tuple(sorted((bone_names[int(b)],round(float(w),6)) for b,w in zip(joints[i],weights[i]) if w>1e-7))
            token=(tuple(np.rint(pos[i]*1e6).astype('int64')),named)
            tokens.append(token)
            if uv is not None:uvtokens.append((token,tuple(np.rint(uv[i]*1e7).astype('int64'))))
        indices=get(prim['indices']).ravel().reshape(-1,3)
        for tri in indices:
            row=[tokens[int(i)] for i in tri]
            # Cyclic canonicalization retains winding, ignores accessor/index order.
            records.append(min(tuple(row[k:]+row[:k]) for k in range(3)))
            if node['name'] in BODY:
                row=[uvtokens[int(i)] for i in tri];bodyuv.append(min(tuple(row[k:]+row[:k]) for k in range(3)))
    digest=hashlib.sha256(repr(sorted(records)).encode()).hexdigest()
    return {'triangle_hash':digest,'triangles':len(records),'export_vertices':vertex_count,
            'body_uv_triangle_hash':hashlib.sha256(repr(sorted(bodyuv)).encode()).hexdigest() if bodyuv else None}

def cross(a,b):return a[0]*b[1]-a[1]*b[0]

def signed(poly):return sum(cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))/2

def clip_area(a,b):
    subject=[tuple(p) for p in a];clip=[tuple(p) for p in b]
    if signed(clip)<0:clip.reverse()
    for x,y in zip(clip,clip[1:]+clip[:1]):
        output=[]
        if not subject:return 0.
        edge=(y[0]-x[0],y[1]-x[1])
        prev=subject[-1];pd=cross(edge,(prev[0]-x[0],prev[1]-x[1]));pin=pd>=0
        for cur in subject:
            cd=cross(edge,(cur[0]-x[0],cur[1]-x[1]));cin=cd>=0
            if cin != pin:
                t=pd/(pd-cd);output.append((prev[0]+t*(cur[0]-prev[0]),prev[1]+t*(cur[1]-prev[1])))
            if cin:output.append(cur)
            prev,pd,pin=cur,cd,cin
        subject=output
    return abs(signed(subject)) if len(subject)>=3 else 0.

def audit(tris,pixels):
    n=len(tris);bbox_lo=tris.min(axis=1);bbox_hi=tris.max(axis=1);low=bbox_lo.min(axis=0);span=np.maximum(bbox_hi.max(axis=0)-low,1e-9)
    grid=max(1,min(128,int(math.sqrt(n))))
    bins=defaultdict(list)
    for i,(lo,hi) in enumerate(zip(bbox_lo,bbox_hi)):
        l=np.floor((lo-low)/span*grid).astype(int);h=np.minimum(grid-1,np.floor((hi-low)/span*grid).astype(int))
        l=np.minimum(grid-1,l)
        for x in range(l[0],h[0]+1):
            for y in range(l[1],h[1]+1):bins[x,y].append(i)
    pairs=set()
    for ids in bins.values():
        for k,a in enumerate(ids):
            for b in ids[k+1:]:pairs.add((a,b) if a<b else (b,a))
    edgeowners=defaultdict(list)
    for i,tri in enumerate(tris):
        q=[tuple(p) for p in tri]
        for a,b in zip(q,q[1:]+q[:1]):edgeowners[tuple(sorted((a,b)))].append(i)
    shared=set()
    for ids in edgeowners.values():
        for k,a in enumerate(ids):
            for b in ids[k+1:]:shared.add(tuple(sorted((a,b))))
    rows=list(pairs);hits=[];area_sum=0.;maxarea=0.
    for start in range(0,len(rows),12000):
        pair=np.asarray(rows[start:start+12000],dtype=int)
        if not len(pair):continue
        aa=tris[pair[:,0]];bb=tris[pair[:,1]]
        # Positive-area intersection requires strictly overlapping projection intervals.
        edges=np.concatenate((np.roll(aa,-1,axis=1)-aa,np.roll(bb,-1,axis=1)-bb),axis=1)
        axes=edges[:,:,[1,0]].copy();axes[:,:,0]*=-1
        ap=np.einsum('bij,bkj->bik',aa,axes);bp=np.einsum('bij,bkj->bik',bb,axes)
        overlap=np.minimum(ap.max(axis=1),bp.max(axis=1))-np.maximum(ap.min(axis=1),bp.min(axis=1))
        possible=np.all(overlap>1e-10*np.linalg.norm(axes,axis=2),axis=1)
        for a,b in pair[possible]:
            area=clip_area(tris[a],tris[b])
            if area>1e-13:
                hits.append([int(a),int(b),area]);area_sum+=area;maxarea=max(maxarea,area)
    positive_pairs={(r[0],r[1]) for r in hits}
    aa=tris[:,1]-tris[:,0];bb=tris[:,2]-tris[:,0];signedarea=(aa[:,0]*bb[:,1]-aa[:,1]*bb[:,0])/2;total=float(sum(abs(signedarea)))
    return {'triangles':n,'broad_phase_pairs':len(pairs),'positive_area_pairs':len(hits),
       'pairwise_overlap_area_uv2':area_sum,'pairwise_overlap_area_atlas_px2':area_sum*pixels*pixels,
       'pairwise_overlap_fraction_of_triangle_uv_area':area_sum/total if total else 0,
       'largest_intersection_px2':maxarea*pixels*pixels,
       'shared_edge_only_pairs':len(shared-positive_pairs),
       'intersections':hits}

def weighted(values,weights):
 order=np.argsort(values);cw=np.cumsum(weights[order]);return [float(values[order[min(np.searchsorted(cw,cw[-1]*p/100),len(order)-1)]]) for p in (50,90,99)] if len(order) else []

def metrics(p,q,pixels):
 e1=p[:,1]-p[:,0];e2=p[:,2]-p[:,0];da=np.linalg.norm(np.cross(e1,e2),axis=1)
 q1=q[:,1]-q[:,0];q2=q[:,2]-q[:,0];det=q1[:,0]*q2[:,1]-q1[:,1]*q2[:,0]
 valid=(da>1e-12)&(abs(det)>1e-14);length=np.linalg.norm(e1,axis=1);alpha=np.sum(e1*e2,axis=1)/np.maximum(length,1e-20);beta=da/np.maximum(length,1e-20)
 J=np.zeros((len(p),2,2));J[:,:,0]=q1/np.maximum(length[:,None],1e-20);J[:,:,1]=(q2-q1*(alpha/np.maximum(length,1e-20))[:,None])/np.maximum(beta[:,None],1e-20)
 sv=np.linalg.svd(J[valid],compute_uv=False);aniso=sv[:,0]/np.maximum(sv[:,1],1e-20);density=np.sqrt(abs(det[valid])/da[valid])*pixels
 return {'triangles':len(p),'finite_uv':bool(np.isfinite(q).all()),'zero_uv_area_on_nondegenerate_triangles':int(sum((da>1e-12)&(abs(det)<=1e-14))),
  'positive_orientation':int(sum(det>1e-14)),'negative_orientation':int(sum(det< -1e-14)),
  'area_m2':float(sum(da)/2),'uv_area':float(sum(abs(det))/2),'area_weighted_anisotropy_p50_p90_p99':weighted(aniso,da[valid]),
  'density_px_per_m_p10_p50_p90':np.percentile(density,[10,50,90]).tolist() if len(density) else [],
  'mean_area_density_px_per_m':float(np.sqrt(sum(abs(det))/sum(da))*pixels)}

def normals_at(n,j,get):
 out=defaultdict(list)
 for p in j['meshes'][n['mesh']]['primitives']:
  at=p['attributes']
  for xyz,norm in zip(get(at['POSITION']),get(at['NORMAL'])):out[tuple(np.rint(xyz*1e6).astype(int))].append(norm)
 return {k:np.unique(np.array(v),axis=0) for k,v in out.items()}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    started=time.monotonic();manifest=json.loads((ASSET/'asset_manifest.json').read_text())
    for name,record in manifest['assets'].items():
        assert sha(ROOT/name)==record['sha256'],f'Asset hash changed: {name}; update the versioned manifest deliberately'
    a,ag=load_glb(ROOT/'art/concept-warden/river_warden_clay.glb')
    b,bg=load_glb(ASSET/'river_warden_uv_master.glb')
    am={n['name']:n for n in a['nodes'] if 'mesh' in n};bm={n['name']:n for n in b['nodes'] if 'mesh' in n}
    assert set(am)==set(bm) and len(bm)==168
    parents=lambda j:{j['nodes'][c]['name']:n['name'] for n in j['nodes'] for c in n.get('children',[])}
    assert parents(a)==parents(b),'Hierarchy changed'
    normal_delta=0.
    for name,node in bm.items():
        old=canonical_mesh(am[name],a,ag);new=canonical_mesh(node,b,bg)
        assert old['triangle_hash']==new['triangle_hash'],f'Geometry/named weights: {name}'
        assert old['body_uv_triangle_hash']==new['body_uv_triangle_hash'],f'Body UV: {name}'
        assert all(node.get('extras',{}).get(k)==v for k,v in am[name].get('extras',{}).items()),f'Original extras: {name}'
        nn=normals_at(node,b,bg);on=normals_at(am[name],a,ag)
        for key,values in nn.items():
            normal_delta=max(normal_delta,float(np.linalg.norm(values[:,None,:]-on[key][None,:,:],axis=2).min(axis=1).max()))
    assert normal_delta<manifest['limits']['normal_vector_difference_limit']
    aj={a['nodes'][n]['name']:i for i,n in enumerate(a['skins'][0]['joints'])}
    bj={b['nodes'][n]['name']:i for i,n in enumerate(b['skins'][0]['joints'])}
    assert set(aj)==set(bj) and len(bj)==53
    ai=ag(a['skins'][0]['inverseBindMatrices']);bi=bg(b['skins'][0]['inverseBindMatrices']);rest=0.;bind=0.
    for name in aj:
        an=a['nodes'][a['skins'][0]['joints'][aj[name]]];bn=b['nodes'][b['skins'][0]['joints'][bj[name]]]
        for key,default in [('translation',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1]),('matrix',np.eye(4).ravel().tolist())]:
            rest=max(rest,float(np.max(abs(np.asarray(an.get(key,default))-np.asarray(bn.get(key,default))))))
        bind=max(bind,float(np.max(abs(ai[aj[name]]-bi[bj[name]]))))
    assert rest<1e-7 and bind<1e-7
    raw=(ASSET/'river_warden_uv_master.glb').read_bytes();offset=12;binary=None
    while offset<len(raw):
        size=int.from_bytes(raw[offset:offset+4],'little');kind=raw[offset+4:offset+8]
        if kind==b'BIN\0':binary=raw[offset+8:offset+8+size]
        offset+=size+8
    assert binary is not None
    image_hashes=[]
    for image in b.get('images',[]):
        view=b['bufferViews'][image['bufferView']];start=view.get('byteOffset',0)
        image_hashes.append(hashlib.sha256(binary[start:start+view['byteLength']]).hexdigest())
    assert manifest['skin_sha256'] in image_hashes,'Verified CC0 skin changed'
    charts=json.loads((ASSET/'paint_layout.json').read_text())['charts'];byobj=defaultdict(list)
    for c in charts:byobj[c['object']].append(c)
    counts=Counter('hair' if c['group']=='hair' else 'outfit' for c in charts)
    assert counts=={'outfit':528,'hair':36}
    overlap_pairs=0;flow_meshes=0;weight_error=0.;worst_anisotropy=0.;all_metrics={}
    for name,node in bm.items():
        qq=[];pp=[];flow=[]
        for prim in b['meshes'][node['mesh']]['primitives']:
            at=prim['attributes'];q=bg(at['TEXCOORD_0']).astype(float);assert np.isfinite(q).all();q[:,1]=1-q[:,1]
            weights=bg(at['WEIGHTS_0']);weight_error=max(weight_error,float(np.max(abs(weights.sum(axis=1)-1))))
            idx=bg(prim['indices']).ravel().reshape(-1,3);qq.append(q[idx]);pp.append(bg(at['POSITION']).astype(float)[idx])
            if name.startswith('Body_Hair'):
                assert '_HAIR_FLOW_T' in at;flow.extend(bg(at['_HAIR_FLOW_T']).ravel().tolist())
        if flow:
            f=np.asarray(flow);assert np.isfinite(f).all() and f.min()>=-1e-6 and f.max()<=1.000001 and np.ptp(f)>.01
            flow_meshes+=1
        if name not in byobj:continue
        q=np.concatenate(qq);p=np.concatenate(pp);cent=q.mean(axis=1);assigned=np.zeros(len(q),dtype=int)
        for c in byobj[name]:
            x,y,X,Y=c['bounds'];mask=(cent[:,0]>=x-1e-7)&(cent[:,0]<=X+1e-7)&(cent[:,1]>=y-1e-7)&(cent[:,1]<=Y+1e-7);assigned+=mask
            assert mask.any(),c['id'];pixels=512 if c['group']=='hair' else 2048
            mm=metrics(p[mask],q[mask],pixels);assert mm['finite_uv'] and mm['zero_uv_area_on_nondegenerate_triangles']==0
            oo=audit(q[mask],pixels);assert oo['positive_area_pairs']==0,c['id'];overlap_pairs+=oo['positive_area_pairs']
            worst_anisotropy=max(worst_anisotropy,mm['area_weighted_anisotropy_p50_p90_p99'][-1]);all_metrics[c['id']]=mm
        assert (assigned==1).all(),f'Unassigned/multiply assigned triangles: {name}'
    assert flow_meshes==11 and weight_error<1e-6
    spacing={}
    for kind,pixels,required in [('outfit',2048,32),('hair',512,16)]:
        cs=[c for c in charts if (c['group']=='hair')==(kind=='hair')];minimum=float('inf')
        for i,c in enumerate(cs):
            x,y,X,Y=c['bounds']
            for d in cs[i+1:]:
                xx,yy,XX,YY=d['bounds'];minimum=min(minimum,math.hypot(max(x-XX,xx-X,0),max(y-YY,yy-Y,0))*pixels)
        assert minimum>=required-.002;spacing[kind]=minimum
    assert sum(int(bm[n].get('extras',{}).get('source_face_count',0)) for n in BODY)==13378
    gloves={name:len(cs) for name,cs in byobj.items() if name.startswith('Gear_Gloves')};assert all(n<=32 for n in gloves.values())
    result={'passed':True,'scope':'Exported asset data only; no render, motion, runtime integration or material-quality acceptance',
      'meshes':len(bm),'joints':len(bj),'body_source_faces':13378,'charts':dict(counts),'positive_area_overlap_pairs':overlap_pairs,
      'joint_rest_max_error':rest,'inverse_bind_max_error':bind,'normal_vector_max_difference_from_clay':normal_delta,
      'minimum_gutter_px':spacing,'hair_flow_meshes':flow_meshes,'glove_chart_counts':gloves,'maximum_weight_sum_error':weight_error,
      'highest_measured_chart_p99_anisotropy':worst_anisotropy,'geometry_comparison':'Oriented triangle multiset: positions1e-6m, named weights1e-6, body UVs1e-7; accessor order/UV duplication ignored',
      'overlap_method':'Shared boundaries excluded; convex triangle clipping with area>1e-13UV² and projection tolerance1e-10UV',
      'skin_sha256':manifest['skin_sha256'],'master_glb_sha256':sha(ASSET/'river_warden_uv_master.glb'),'elapsed_seconds':time.monotonic()-started}
    output=ROOT/'builds/human-uv-report.json';output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('JADE_HUMAN_UV_AUDIT_PASSED',json.dumps(result,sort_keys=True))

if __name__=='__main__':run()
