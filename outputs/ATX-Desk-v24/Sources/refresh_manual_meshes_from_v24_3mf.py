"""Rebuild all printed-part illustrations from the exact latest 3MF meshes."""
from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E,math,struct,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/ATX-Desk-v24'
project=OUT/'Style1_V24_All_Latest_Parts_9_Plates.3mf'
N='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
P='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'
expected={m['name']:m for m in json.loads((OUT/'parts.json').read_text())}
index=json.loads((OUT/'manual_mesh_index.json').read_text());old={m['name']:m for m in index}
def rot(axis,angle):
    a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]]) if axis=='x' else np.array([[c,-s,0],[s,c,0],[0,0,1]])
checks=[];updated=[]
with zipfile.ZipFile(project) as z:
    cfg=E.fromstring(z.read('Metadata/model_settings.config'))
    main=E.fromstring(z.read('3D/3dmodel.model'));resources={o.get('id'):o for o in main.find(N+'resources')}
    for obj in cfg.findall('object'):
        md={m.get('key'):m.get('value') for m in obj.findall('metadata') if m.get('key')}
        name=md['name'].removeprefix('LATEST_V24_').removesuffix('.stl');assert name in expected
        component=resources[obj.get('id')].find(N+'components/'+N+'component')
        meshdoc=E.fromstring(z.read(component.get(P+'path').lstrip('/')))
        mesh=meshdoc.find(N+'resources/'+N+'object/'+N+'mesh')
        vertices=np.array([[float(v.get(k)) for k in 'xyz'] for v in mesh.find(N+'vertices')])
        faces=np.array([[int(t.get(k)) for k in ('v1','v2','v3')] for t in mesh.find(N+'triangles')])
        t=vertices[faces]
        if name.startswith('12_front_PCI'):t=t@rot('z',-90).T
        # Undo the documented export orientations from package_atx_v20 and V24.
        if name.startswith(('04_','18_','20_')):t=t@rot('z',-45).T
        if name.startswith('19_'):t=t@rot('z',-90).T
        if name.startswith(('10_','20_')):t=t@rot('x',-90).T
        elif name.startswith('18_'):t=t@rot('x',-180).T
        elif name.startswith(('12_','07_GPU_INTEGRATED_')):t=t@rot('x',90).T
        elif name.startswith('16_'):
            if name.startswith('16_PCI'):t=t@rot('x',-math.degrees(math.atan(16.45/140))).T
            original_to_print=np.array([[0,1,0],[0,0,1],[1,0,0]])
            t=t@original_to_print
        transform=np.array(old[name]['transform']).reshape(4,4)
        t=t@transform[:3,:3].T
        target_min=np.array(old[name]['min_mm']);target_max=np.array(old[name]['max_mm'])
        t+=target_min-t.min(axis=(0,1))
        assert np.allclose(t.max(axis=(0,1)),target_max,atol=.04),(name,t.max(axis=(0,1)),target_max)
        volume=abs(np.sum(t[:,0]*np.cross(t[:,1],t[:,2]))/6)
        error=abs(volume-expected[name]['volume_mm3'])/expected[name]['volume_mm3']
        assert error<.003,(name,error)
        normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
        raw=bytearray(('V24 3MF actual mesh '+name).encode()[:80].ljust(80,b' ')+struct.pack('<I',len(t)))
        for tri,no in zip(t,normals):raw+=struct.pack('<12fH',*no,*tri.reshape(-1),0)
        path=OUT/'Manual_Meshes'/(name+'.stl');path.write_bytes(raw)
        updated.append({'name':name,'transform':np.eye(4).reshape(-1).tolist(),'min_mm':t.min(axis=(0,1)).tolist(),'max_mm':t.max(axis=(0,1)).tolist(),'source':project.name+' / '+component.get(P+'path'),'volume_error_percent':error*100})
        checks.append({'name':name,'triangles':len(t),'volume_error_percent':error*100,'assembled_bounds_verified':True,'illustration_stl_sha256':hashlib.sha256(raw).hexdigest()})
assert len(updated)==15 and {m['name'] for m in updated}==set(expected)
updated+=[m for m in index if m['name'].startswith('REF_')]
(OUT/'manual_mesh_index.json').write_text(json.dumps(updated,indent=2),encoding='utf-8')
(OUT/'manual_from_print_project_verification.json').write_text(json.dumps({'source_project':project.name,'source_project_sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'printed_part_count':15,'historical_printed_mesh_fallback':False,'reference_hardware':'unchanged approximate envelope only','checks':checks},indent=2),encoding='utf-8')
print(json.dumps({'actual_3mf_meshes':15,'all_assembled_bounds_verified':True,'all_volumes_verified':True}))
