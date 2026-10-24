from pathlib import Path
import numpy as np
import math,json,struct,zipfile,uuid,copy,csv,collections
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]/'outputs'
SRC=ROOT/'Style2-v06'
DEST=SRC/'Style2_V06_A1_PETG_Arranged.3mf'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
R='http://schemas.openxmlformats.org/package/2006/relationships'
E.register_namespace('',NS);E.register_namespace('p',P)
shared=(ROOT/'arrange_v12_plates.py').read_text(encoding='utf-8')
exec(shared[shared.index('def hull('):shared.index('checks=[]')])

def rz(angle):
    a=math.radians(angle);c=math.cos(a);s=math.sin(a)
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def rotate(part,angle):
    q=part.copy();q['tris']=part['tris']@rz(angle).T
    q['tris']-=q['tris'].min(axis=(0,1));q['size']=q['tris'].max(axis=(0,1));return q

parts={};meshchecks=[]
for meta in json.loads((SRC/'parts.json').read_text(encoding='utf-8')):
    name=meta['name'];data=(SRC/'Raw_STL'/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',data,80)[0]
    ts=np.array([struct.unpack_from('<12fH',data,84+50*i)[3:12] for i in range(n)]).reshape(-1,3,3)
    ratios=np.array(meta['native_size_mm'])/np.ptp(ts,axis=(0,1));scale=10 if abs(np.mean(ratios)-10)<.01 else 1
    assert np.max(abs(ratios-scale))<.01;ts*=scale
    mode='XY face on bed'
    if name.startswith('01_'):
        matrix=np.array([[1,0,0],[0,0,1],[0,-1,0]]);mode='rear Y20 face down; bosses upward'
    elif name.startswith('03_'):
        matrix=np.array([[1,0,0],[0,0,-1],[0,1,0]]);mode='Y20 face down; head wells upward'
    elif name.startswith('05_'):
        if name.endswith('_1'):matrix=np.array([[0,1,0],[0,0,-1],[-1,0,0]])
        else:matrix=np.array([[0,1,0],[0,0,1],[1,0,0]])
        mode='side face flat; screw head wells upward'
    elif name.startswith('06_'):
        matrix=np.diag([1,-1,-1]);mode='top Z22 face down; foot pads upward'
    else:matrix=np.eye(3)
    assert np.linalg.det(matrix)>.99
    ts=ts@matrix.T;ts-=ts.min(axis=(0,1));size=ts.max(axis=(0,1))
    volume=np.sum(ts[:,0]*np.cross(ts[:,1],ts[:,2]))/6
    assert abs(volume-meta['volume_mm3'])/meta['volume_mm3']<.003,(name,volume)
    edges=collections.defaultdict(list)
    for tri in ts:
        ps=[tuple(np.round(p,4)) for p in tri]
        for a,b in zip(ps,ps[1:]+ps[:1]):edges[tuple(sorted((a,b)))].append((a,b))
    assert all(len(e)==2 and e[0]==e[1][::-1] for e in edges.values()),name
    cross=np.cross(ts[:,1]-ts[:,0],ts[:,2]-ts[:,0]);areas=np.linalg.norm(cross,axis=1)/2
    down=(cross[:,2]<-1e-6)&(np.abs(cross[:,2])/np.maximum(areas*2,1e-12)>.99)&(ts[:,:,2].max(axis=1)>.05)
    meshchecks.append({'name':name,'volume_mm3':float(volume),'closed_oriented':True,'orientation':mode,'elevated_horizontal_underside_mm2':float(areas[down].sum())})
    parts[name]=dict(name=name,tris=ts,size=size,brim=3 if name.startswith('02_') else 5,support=False,orientation=mode)

def get(prefix):return next(p for n,p in parts.items() if n.startswith(prefix))
def place(part,x,y):q=part.copy();q['xy']=np.array([x,y]);return q
plates=[]
def plate(name,items):plates.append({'name':name,'items':items})
def single(prefix,label,angle=0):
    q=rotate(get(prefix),angle);plate(label,[place(q,*((256-q['size'][:2])/2))])

def pair(prefix_a,prefix_b,label):
    a=rotate(get(prefix_a),45);b=rotate(get(prefix_b),45)
    ha=hull(a['tris'].reshape(-1,3)[:,:2]);hb=hull(b['tris'].reshape(-1,3)[:,:2]);ac=a['size'][:2]/2;bc=b['size'][:2]/2
    # Long axes remain parallel; SAT conservatively verifies the actual convex outlines.
    normals=[]
    for h in (ha,hb):
        for e in np.roll(h,-1,axis=0)-h:
            v=np.array([-e[1],e[0]]);v/=np.linalg.norm(v)
            if not any(abs(np.dot(v,k))>.99999 for k in normals):normals.append(v)
    normals=np.array(normals);aa=ha@normals.T;bb=hb@normals.T
    best=None
    for along in range(-40,41,2):
        for across in range(-130,131,2):
            shift=ac-bc+np.array([along-across,along+across])/math.sqrt(2)
            proj=shift@normals.T
            sep=np.maximum(bb.min(axis=0)+proj-aa.max(axis=0),aa.min(axis=0)-bb.max(axis=0)-proj)
            if np.max(sep)<a['brim']+b['brim']+2:continue
            lo=np.minimum(-a['brim']-.5+np.zeros(2),shift-b['brim']-.5)
            hi=np.maximum(a['size'][:2]+a['brim']+.5,shift+b['size'][:2]+b['brim']+.5)
            dims=hi-lo
            if max(dims)>254:continue
            score=max(dims)+sum(dims)*.001
            if best is None or score<best[0]:best=(score,shift,lo,hi)
    if best is None:
        single(prefix_a,label+' A',45);single(prefix_b,label+' B',45)
    else:
        _,shift,lo,hi=best;off=(256-(hi-lo))/2-lo
        plate(label,[place(a,*off),place(b,*(off+shift))])

single('01_UPRIGHT_1','01 立柱1_九孔侧_整根斜放',45)
single('01_UPRIGHT_2','02 立柱2_整根斜放',45)
single('01_UPRIGHT_3','03 立柱3_整根斜放',45)
pair('02_FOOT_1','02_FOOT_2','04 两根底脚_整件斜放')
pair('02_FOOT_3','06_GPU_CARRIER','05 第三根底脚_显卡承托梁')
pair('03_LOWER','09_PSU_SADDLE_FRONT','06 下横撑_电源前托条_左右限位')
pair('03_UPPER','09_PSU_SADDLE_REAR','07 上横撑_电源后托条_左右限位')
small=rotate(get('07_'),90)
plate('08 左侧直角框_母槽托盘_显卡托垫',[
    place(get('05_SIDE_RECTANGULAR_FRAME_1'),10,10),place(small,185,15),
    place(get('08_GPU_PAD_LEFT'),185,180),place(get('08_GPU_PAD_RIGHT'),215,180)])
single('05_SIDE_RECTANGULAR_FRAME_3','09 右侧直角框')
for i,pl in enumerate(plates):pl['name']=f'{i+1:02d} '+pl['name'].split(' ',1)[1]

# Reuse the established Bambu 3MF writer, with fresh objects and plate metadata only.
tail=shared[shared.index('checks=[]'):]
tail=tail.replace('==len(parts)==19','==len(parts)==16')
tail=tail.replace("zipfile.ZipFile(ROOT/'ATX-Desk-v12-plate-template.3mf')","zipfile.ZipFile(ROOT/'ATX-Desk-v13/ATX-Desk-v13-All-Parts-9-Plates.3mf')")
tail=tail.replace("('ALREADY_PRINTED_' if pi==0 else '')", "''")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-checks.json'", "SRC/'print_plate_checks.json'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-list.csv'", "SRC/'print_plate_list.csv'")
tail=tail.replace("settings['enable_prime_tower']='0';settings['print_sequence']='by layer'", "settings['enable_prime_tower']='0';settings['print_sequence']='by layer';settings['filament_colour']=['#2378DC']*3;settings['enable_support']='0';settings['support_type']='normal(auto)';settings['support_on_build_plate_only']='1';settings['support_top_z_distance']='0.2';settings['support_bottom_z_distance']='0.2'")
exec(compile(tail,'style2_bambu_writer','exec'))

printdir=SRC/'PRINT_STL';printdir.mkdir(exist_ok=True)
for pl in plates:
    for p in pl['items']:
        data=bytearray(('STYLE2 V06 mm '+p['name']).encode('ascii')[:80].ljust(80,b' ')+struct.pack('<I',len(p['tris'])))
        for t in p['tris']:
            normal=np.cross(t[1]-t[0],t[2]-t[0]);normal/=np.linalg.norm(normal)
            data+=struct.pack('<12fH',*normal,*t.reshape(-1),0)
        (printdir/(p['name']+'.stl')).write_bytes(data)
(SRC/'print_mesh_checks.json').write_text(json.dumps(meshchecks,indent=2),encoding='utf-8')
print(json.dumps({'plates':len(plates),'parts':len(parts),'output':str(DEST),'undersides':[(q['name'],round(q['elevated_horizontal_underside_mm2'],1)) for q in meshchecks]}))
