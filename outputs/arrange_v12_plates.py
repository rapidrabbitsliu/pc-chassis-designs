from pathlib import Path
import struct, math, json, zipfile, uuid, copy, csv
import xml.etree.ElementTree as E
import numpy as np

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'ATX-Desk-v12-print-review'
DEST=ROOT/'ATX-Desk-v12-MultiPlate.3mf'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
R='http://schemas.openxmlformats.org/package/2006/relationships'
E.register_namespace('',NS);E.register_namespace('p',P)
parts={}
def rot(axis,angle):
    a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    if axis=='x':return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])
for meta in json.loads((SRC/'parts.json').read_text(encoding='utf-8')):
    name=meta['name']; b=(SRC/'PRINT_STL'/(name+'.stl')).read_bytes()
    count=struct.unpack_from('<I',b,80)[0]
    tris=np.array([struct.unpack_from('<12fH',b,84+i*50)[3:12] for i in range(count)]).reshape(-1,3,3)
    if name.startswith('16_PCI'):tris=tris@rot('x',math.degrees(math.atan(16.45/140))).T
    if name.startswith('18_') or name.startswith('20_'):tris=tris@rot('x',180).T
    if name.startswith('19_') and not name.startswith('19_CPU'):tris=tris@rot('z',90).T
    tris-=tris.min(axis=(0,1));size=tris.max(axis=(0,1))
    support=name.startswith(('05_','07_','20_','19_MID','08_GPU_LOWER'))
    parts[name]=dict(name=name,tris=tris,size=size,brim=meta['brim_mm'],support=support)

def get(prefix):return next(p for n,p in parts.items() if n.startswith(prefix))
plates=[]
def plate(name,items):
    plates.append({'name':name,'items':items})
def place(p,x,y):
    q=p.copy();q['xy']=np.array([x,y]);return q
def single(prefix,label):
    p=get(prefix);plate(label,[place(p,*((256-p['size'][:2])/2))])
single('19_CPU','01 已打印_CPU侧主板纵梁')
group=[get('16_CPU'),get('19_PCI'),get('19_MID')]
total=sum(p['size'][1]+2*p['brim'] for p in group)+12
y=(256-total)/2
items=[]
for p in group:
    items.append(place(p,(256-p['size'][0])/2,y+p['brim']))
    y+=p['size'][1]+2*p['brim']+6
plate('02 CPU侧框架_其余两根主板纵梁',items)
single('16_PCI','03 PCIe侧内斜框架_已贴平')
single('12_front_PCI','04 前侧PCIe承重框架')
single('12_front_CPU','05 前侧CPU承重框架')
for side,beam in [('GPU','18_REAR_BEAM_CPU'),('CPU','18_REAR_BEAM_PCI')]:
    group=[get('10_'+side),get('20_'+side),get(beam)]
    total=sum(p['size'][1]+2*p['brim'] for p in group)+12
    assert total<256,total
    y=(256-total)/2;items=[]
    for p in group:
        items.append(place(p,(256-p['size'][0])/2,y+p['brim']))
        y+=p['size'][1]+2*p['brim']+6
    plate(f'{len(plates)+1:02d} {side}风扇框_底座_后横梁',items)
single('05_','08 电源托架_局部支撑')
group=[get('07_'),get('08_GPU_UPPER'),get('08_GPU_LOWER')]
plate('09 显卡接口固定组件_先试装',[
    place(group[0],30,47),place(group[1],100,70),place(group[2],100,135)])
group=[get('04_front'),get('04_rear')]
shift=np.array([-35,35])/math.sqrt(2)
combined=group[0]['size'][:2]+abs(shift)
base=(256-combined)/2+np.array([abs(shift[0]),0])
plate('10 两根落地横条_斜放整件',[
    place(group[0],*base),place(group[1],*(base+shift))])

# Convex-hull SAT checks conservatively include the outer projection of every model.
def hull(points):
    ps=sorted(set(map(tuple,points)))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    halves=[]
    for seq in [ps,ps[::-1]]:
        h=[]
        for p in seq:
            while len(h)>=2 and cross(h[-2],h[-1],p)<=1e-7:h.pop()
            h.append(p)
        halves.append(h[:-1])
    return np.array(halves[0]+halves[1])
def separated(a,b,clearance):
    for h in [a,b]:
        for d in np.roll(h,-1,axis=0)-h:
            n=np.array([-d[1],d[0]]);n/=np.linalg.norm(n)
            aa=a@n;bb=b@n
            if max(bb.min()-aa.max(),aa.min()-bb.max())>=clearance-1e-4:return True
    return False
checks=[]
for ix,pl in enumerate(plates):
    for j,p in enumerate(pl['items']):
        lo=p['xy']-p['brim']-.1;hi=p['xy']+p['size'][:2]+p['brim']+.1
        assert min(lo)>=0 and max(hi)<=256,(ix,p['name'],lo,hi)
        assert p['size'][2]<=256
        hp=hull(p['tris'].reshape(-1,3)[:,:2]+p['xy'])
        for q in pl['items'][:j]:
            hq=hull(q['tris'].reshape(-1,3)[:,:2]+q['xy'])
            assert separated(hp,hq,p['brim']+q['brim']+1),(ix,p['name'],q['name'])
        # Require a genuine plane touching the bed, including the inclined side frame.
        ts=p['tris'];cross=np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0])
        onbed=ts[:,:,2].max(axis=1)<.02
        area=np.linalg.norm(cross[onbed],axis=1).sum()/2
        assert area>100,(p['name'],area)
        checks.append({'plate':ix+1,'plate_name':pl['name'],'part':p['name'],
            'print_xyz_mm':p['size'].round(3).tolist(),'xy_mm':p['xy'].round(3).tolist(),
            'brim_mm':p['brim'],'support':p['support'],'bed_contact_mm2':round(area,2)})
assert len(checks)==len(parts)==19

template=zipfile.ZipFile(ROOT/'ATX-Desk-v12-plate-template.3mf')
model=E.fromstring(template.read('3D/3dmodel.model'))
resources=model.find('{'+NS+'}resources');resources.clear()
build=model.find('{'+NS+'}build');build.clear();build.set('{'+P+'}UUID',str(uuid.uuid4()))
cfg=E.Element('config');rels=E.Element('Relationships',xmlns=R)
identity='1 0 0 0 1 0 0 0 1'
def md(parent,key,value):E.SubElement(parent,'metadata',key=key,value=str(value))
def xml(el):return E.tostring(el,encoding='utf-8',xml_declaration=True)
files={}
identifier=0
assemble=E.Element('assemble')
for pi,pl in enumerate(plates):
    pc=E.Element('plate')
    for k,v in {'plater_id':pi+1,'plater_name':pl['name'],'locked':'false',
        'filament_map_mode':'Auto For Flush','filament_maps':'1 1 1','filament_volume_maps':'0 0 0'}.items():md(pc,k,v)
    ox=(pi%4)*307.2;oy=-(pi//4)*307.2
    for part in pl['items']:
        identifier+=1;mid=identifier*2-1;oid=identifier*2
        centered=part['tris']-part['size']/2
        verts,inds=np.unique(centered.reshape(-1,3),axis=0,return_inverse=True)
        mm=E.Element('{'+NS+'}model',unit='millimeter')
        rs=E.SubElement(mm,'{'+NS+'}resources')
        ob=E.SubElement(rs,'{'+NS+'}object',id=str(mid),type='model')
        mesh=E.SubElement(ob,'{'+NS+'}mesh');ve=E.SubElement(mesh,'{'+NS+'}vertices');tr=E.SubElement(mesh,'{'+NS+'}triangles')
        for v in verts:E.SubElement(ve,'{'+NS+'}vertex',**{k:f'{t:.8f}' for k,t in zip('xyz',v)})
        for v in inds.reshape(-1,3):E.SubElement(tr,'{'+NS+'}triangle',**{k:str(t) for k,t in zip(['v1','v2','v3'],v)})
        path=f'/3D/Objects/object_{identifier}.model';files[path[1:]]=xml(mm)
        obj=E.SubElement(resources,'{'+NS+'}object',id=str(oid),type='model',attrib={'{'+P+'}UUID':str(uuid.uuid4())})
        comps=E.SubElement(obj,'{'+NS+'}components')
        E.SubElement(comps,'{'+NS+'}component',objectid=str(mid),transform=identity+' 0 0 0',attrib={'{'+P+'}path':path,'{'+P+'}UUID':str(uuid.uuid4())})
        xyz=[ox+part['xy'][0]+part['size'][0]/2,oy+part['xy'][1]+part['size'][1]/2,part['size'][2]/2]
        transform=identity+' '+' '.join(f'{v:.8f}' for v in xyz)
        E.SubElement(build,'{'+NS+'}item',objectid=str(oid),transform=transform,printable='1',attrib={'{'+P+'}UUID':str(uuid.uuid4())})
        E.SubElement(rels,'Relationship',Target=path,Id=f'rel-{identifier}',Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
        oc=E.SubElement(cfg,'object',id=str(oid))
        label=('ALREADY_PRINTED_' if pi==0 else '')+part['name']+'.stl'
        for k,v in {'name':label,'extruder':1,'brim_type':'outer_only','brim_width':part['brim'],
            'enable_support':int(part['support']),**({'support_type':'normal(auto)','support_on_build_plate_only':1} if part['support'] else {})}.items():md(oc,k,v)
        E.SubElement(oc,'metadata',face_count=str(len(part['tris'])))
        partcfg=E.SubElement(oc,'part',id=str(mid),subtype='normal_part')
        for k,v in {'name':label,'matrix':'1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1','source_file':str(SRC/'PRINT_STL'/(part['name']+'.stl')),'source_object_id':0,'source_volume_id':0,
            **{f'source_offset_{a}':part['size'][j]/2 for j,a in enumerate('xyz')}}.items():md(partcfg,k,v)
        E.SubElement(partcfg,'mesh_stat',face_count=str(len(part['tris'])),edges_fixed='0',degenerate_facets='0',facets_removed='0',facets_reversed='0',backwards_edges='0')
        ins=E.SubElement(pc,'model_instance')
        for k,v in {'object_id':oid,'instance_id':0,'identify_id':100+identifier}.items():md(ins,k,v)
        E.SubElement(assemble,'assemble_item',object_id=str(oid),instance_id='0',transform=transform,offset='0 0 0')
    cfg.append(pc)
cfg.append(assemble)
settings=json.loads(template.read('Metadata/project_settings.config'))
settings['enable_prime_tower']='0';settings['print_sequence']='by layer'
files.update({'3D/3dmodel.model':xml(model),'3D/_rels/3dmodel.model.rels':xml(rels),
    'Metadata/project_settings.config':json.dumps(settings,ensure_ascii=False,indent=2).encode('utf-8'),
    'Metadata/model_settings.config':xml(cfg),'[Content_Types].xml':template.read('[Content_Types].xml'),
    '_rels/.rels':template.read('_rels/.rels')})
with zipfile.ZipFile(DEST,'w',zipfile.ZIP_DEFLATED) as z:
    for path,b in files.items():z.writestr(path,b)
(ROOT/'ATX-Desk-v12-plate-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'ATX-Desk-v12-plate-list.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['盘号','分组','零件','打印尺寸mm','支撑','brim宽度mm'])
    for p in checks:w.writerow([p['plate'],p['plate_name'],p['part'],' x '.join(map(str,p['print_xyz_mm'])),'自动普通支撑_仅热床' if p['support'] else '无',p['brim_mm']])
print(json.dumps({'output':str(DEST),'plates':len(plates),'objects':len(checks),'all_fit_with_brim':True,'bed_contact':True},ensure_ascii=False))
