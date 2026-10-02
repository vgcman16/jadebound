#!/usr/bin/env python3
"""Validate original GLB files and animated bind-pose pivots without rendering."""
import json, math, pathlib, struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
MODELS=ROOT/'game/assets/models'
NAMES=['hero','elder','bandit','house','gate','shrine','tree','bamboo','rock','lantern']
def read_glb(path):
    data=path.read_bytes()
    magic,version,length=struct.unpack_from('<III',data)
    assert magic==0x46546C67 and version==2 and length==len(data),path
    size,kind=struct.unpack_from('<II',data,12)
    assert kind==0x4E4F534A,path
    return json.loads(data[20:20+size])
for name in NAMES:
    glb=read_glb(MODELS/f'{name}.glb')
    assert glb.get('meshes') and glb.get('materials'),name
    if name in ['hero','elder','bandit']:
        nodes={n['name']:n for n in glb['nodes'] if 'name' in n}
        clips={a['name'] for a in glb.get('animations',[])}
        assert {'idle','walk','attack'}<=clips,(name,clips)
        expected={f'{name}_torso':(0,1.02 if name=='hero' else .97,0)}
        for suffix,sign in [('L',-1),('R',1)]:
            expected[f'{name}_leg_{suffix}']=(sign*(.126 if name=='hero' else .145),.8 if name=='hero' else .72,0)
            expected[f'{name}_arm_{suffix}']=(sign*(.28 if name=='hero' else .32),.33 if name=='hero' else .30,0)
        for pivot,want in expected.items():
            actual=nodes[pivot].get('translation',[0,0,0])
            assert all(math.isfinite(v) for v in actual),pivot
            assert all(abs(a-b)<.001 for a,b in zip(actual,want)),f'{pivot}: missing/incorrect bind translation {actual}, expected {want}'
    print('PASS GLB',name)
print('JADE_ASSET_CONTRACT_PASSED')
