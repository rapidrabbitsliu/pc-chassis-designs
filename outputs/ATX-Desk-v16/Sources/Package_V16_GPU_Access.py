from pathlib import Path
import collections,copy,csv,json,math,shutil,struct,uuid,zipfile
import xml.etree.ElementTree as E
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'outputs';SRC=ROOT/'ATX-Desk-v16';DEST=SRC/'Style1_V16_GPU_Replacements_1_Plate_UNSLICED.3mf'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06';R='http://schemas.openxmlformats.org/package/2006/relationships'
E.register_namespace('',NS);E.register_namespace('p',P)
printdir=SRC/'PRINT_STL';printdir.mkdir(exist_ok=True)
replacement=SRC/'REPRINT_STL';replacement.mkdir(exist_ok=True)
def rot(axis,angle):
    a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    if axis=='x':return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])
parts={};allchecks=[]
for meta in json.loads((SRC/'parts.json').read_text()):
    n=meta['name'];data=(SRC/'Raw_STL'/(n+'.stl')).read_bytes();cnt=struct.unpack_from('<I',data,80)[0]
    dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')]);tris=np.frombuffer(data,dtype=dt,offset=84,count=cnt)['v'].astype(float)
    scale=np.array(meta['native_size_mm'])/np.ptp(tris,axis=(0,1));assert np.ptp(scale)<.01
    tris*=10 if abs(np.mean(scale)-10)<.01 else 1
    if n.startswith(('10_','12_','20_','08_')):tris=tris@rot('x',-90).T
    elif n.startswith(('07_','16_')):tris=tris@np.array([[0,1,0],[0,0,1],[1,0,0]]).T
    if n.startswith('16_PCI'):tris=tris@rot('x',math.degrees(math.atan(16.45/140))).T
    if n.startswith(('18_','20_','10_')):tris=tris@rot('x',180).T
    if n.startswith(('04_','18_','20_')):tris=tris@rot('z',45).T
    if n.startswith('19_'):tris=tris@rot('z',90).T
    if n.startswith('08_GPU_UPPER'):tris=tris@rot('z',90).T
    tris-=tris.min(axis=(0,1));size=tris.max(axis=(0,1))
    volume=np.sum(tris[:,0]*np.cross(tris[:,1],tris[:,2]))/6
    assert abs(volume-meta['volume_mm3'])<meta['volume_mm3']*.003,(n,volume)
    edges=collections.defaultdict(list)
    for t in tris:
        pts=[tuple(np.round(p,4)) for p in t]
        for aa,bb in zip(pts,pts[1:]+pts[:1]):edges[tuple(sorted((aa,bb)))].append((aa,bb))
    bad=sum(1 for vals in edges.values() if len(vals)!=2 or vals[0]!=vals[1][::-1]);assert bad==0,(n,bad)
    brim=3 if n.startswith('16_') else 5
    assert max(size[:2]+2*(brim+.1))<=256.01,(n,size)
    normals=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
    output=bytearray((('V16 mm '+n).encode('ascii')[:80]).ljust(80,b' ')+struct.pack('<I',len(tris)))
    for t,no in zip(tris,normals):output+=struct.pack('<12fH',*no,*t.reshape(-1),0)
    (printdir/(n+'.stl')).write_bytes(output)
    allchecks.append({'part':n,'closed_oriented_mesh':True,'print_size_mm':size.round(3).tolist(),'cad_volume_error_pct':abs(volume-meta['volume_mm3'])/meta['volume_mm3']*100})
    if n.startswith(('07_','08_')):
        parts[n]=dict(name=n,tris=tris,size=size,brim=5,support=n.startswith('07_'))
        alias='P12_V16_GPU_Tower.stl' if n.startswith('07_') else ('P13_V16_Upper_Ear_Ledge.stl' if n.startswith('08_GPU_UPPER') else 'P14_V16_Lower_Tab_Receiver.stl')
        shutil.copy2(printdir/(n+'.stl'),replacement/alias)
assert len(parts)==3
items=[]
for n,p in parts.items():
    q=p.copy();q['xy']=np.array((60,47) if n.startswith('07_') else ((140,70) if n.startswith('08_GPU_UPPER') else (132,185)));items.append(q)
plates=[{'name':'V16 P12显卡塔_P13上托片_P14下插脚座补打','items':items}]
shared=(ROOT/'arrange_v12_plates.py').read_text(encoding='utf-8')
exec(shared[shared.index('def hull('):shared.index('checks=[]')])
tail=shared[shared.index('checks=[]'):]
tail=tail.replace('==len(parts)==19','==len(parts)==3').replace("('ALREADY_PRINTED_' if pi==0 else '')", "'V16_'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-template.3mf'", "ROOT/'ATX-Desk-v13/ATX-Desk-v13-All-Parts-9-Plates.3mf'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-checks.json'", "SRC/'replacement-plate-checks.json'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-list.csv'", "SRC/'replacement-plate-list.csv'")
exec(compile(tail,'V16_replacement_3mf_writer','exec'))
(SRC/'mesh_checks.json').write_text(json.dumps(allchecks,indent=2))
old=json.loads((ROOT/'ATX-Desk-v13/parts.json').read_text())
new=json.loads((SRC/'parts.json').read_text())
changed=[p['name'] for p in new if abs(p['volume_mm3']-next(q['volume_mm3'] for q in old if q['name']==p['name']))>.001]
assert set(changed)==set(parts),changed
with zipfile.ZipFile(DEST) as z:
    assert z.testzip() is None
    settings=json.loads(z.read('Metadata/project_settings.config'))
    config=E.fromstring(z.read('Metadata/model_settings.config'))
    assert len(config.findall('plate'))==1 and len(config.findall('object'))==3
    assert settings['wall_loops']=='5' and settings['sparse_infill_density']=='40%'
report={'changed_parts':changed,'unchanged_parts':14,'stl_count':17,'replacement_stl_count':3,'replacement_plates':1,'sliced':False,'supports':'P12 normal auto, build plate only; P13/P14 off','printer_jobs_sent':False}
(SRC/'package_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

source=SRC/"Sources";source.mkdir(exist_ok=True)
shutil.copy2(PROJECT/"work/build_atx_v16_gpu_access.py",source/"Build_V16_GPU_Access.py")
shutil.copy2(Path(__file__),source/"Package_V16_GPU_Access.py")
print(json.dumps(report,ensure_ascii=True))
