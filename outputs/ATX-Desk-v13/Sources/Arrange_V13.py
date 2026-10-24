from pathlib import Path
import struct,math,json,zipfile,uuid,copy,csv,collections
import xml.etree.ElementTree as E
import numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'ATX-Desk-v13';DEST=SRC/'ATX-Desk-v13-Arranged.3mf'
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
    name=meta['name'];b=(SRC/'Raw_STL'/(name+'.stl')).read_bytes();count=struct.unpack_from('<I',b,80)[0]
    tris=np.array([struct.unpack_from('<12fH',b,84+i*50)[3:12] for i in range(count)]).reshape(-1,3,3)
    scale=np.array(meta['native_size_mm'])/np.ptp(tris,axis=(0,1));assert np.ptp(scale)<.01
    scale=10 if abs(np.mean(scale)-10)<.01 else 1;tris*=scale
    if name.startswith(('10_','12_','20_','08_')):tris=tris@rot('x',-90).T
    elif name.startswith(('07_','16_')):tris=tris@np.array([[0,1,0],[0,0,1],[1,0,0]]).T
    if name.startswith('16_PCI'):tris=tris@rot('x',math.degrees(math.atan(16.45/140))).T
    if name.startswith(('18_','20_','10_')):tris=tris@rot('x',180).T
    if name.startswith(('04_','18_','20_')):tris=tris@rot('z',45).T
    if name.startswith('19_'):tris=tris@rot('z',90).T
    tris-=tris.min(axis=(0,1));size=tris.max(axis=(0,1))
    cross=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    volume=np.sum(tris[:,0]*np.cross(tris[:,1],tris[:,2]))/6
    assert abs(volume-meta['volume_mm3'])<meta['volume_mm3']*.003,(name,volume)
    edges=collections.defaultdict(list)
    for t in tris:
        ps=[tuple(np.round(p,4)) for p in t]
        for aa,bb in zip(ps,ps[1:]+ps[:1]):edges[tuple(sorted((aa,bb)))].append((aa,bb))
    bad=sum(1 for vv in edges.values() if len(vv)!=2 or vv[0]!=vv[1][::-1]);assert bad==0,(name,bad)
    brim=3 if name.startswith('16_') else 5
    support=name.startswith(('05_','07_','20_','19_MID','08_GPU_LOWER','12_front_CPU'))
    parts[name]=dict(name=name,tris=tris,size=size,brim=brim,support=support)

def get(prefix):return next(p for n,p in parts.items() if n.startswith(prefix))
plates=[]
def plate(name,items):plates.append({'name':name,'items':items})
def place(p,x,y):q=p.copy();q['xy']=np.array([x,y]);return q
def single(prefix,label):
    p=get(prefix);plate(label,[place(p,*((256-p['size'][:2])/2))])
group=[get('16_CPU'),get('19_PCI'),get('19_MID'),get('19_CPU')]
total=sum(p['size'][1]+2*p['brim'] for p in group)+12;y=(256-total)/2;items=[]
for p in group:
    items.append(place(p,(256-p['size'][0])/2,y+p['brim']));y+=p['size'][1]+2*p['brim']+4
plate('01 CPU侧框架_三根主板纵梁',items)
single('16_PCI','02 PCIe侧内斜承重框架')
single('12_front_PCI','03 前侧PCIe承重框架')
single('12_front_CPU','04 前侧CPU承重框架_带连接耳')

# Shared convex-hull/SAT helpers from the previous package writer.
shared=(ROOT/'arrange_v12_plates.py').read_text(encoding='utf-8')
exec(shared[shared.index('def hull('):shared.index('checks=[]')])
# Search the true outlines of both continuous beams; never use diagonal length alone.
a=get('18_');b=get('20_');ha=hull(a['tris'].reshape(-1,3)[:,:2]);hb=hull(b['tris'].reshape(-1,3)[:,:2])
ac=(ha.min(axis=0)+ha.max(axis=0))/2;bc=(hb.min(axis=0)+hb.max(axis=0))/2
best=None
for along in np.arange(-25,25.1,1):
    for across in np.arange(-60,60.1,1):
        shift=ac-bc+np.array([along-across,along+across])/math.sqrt(2)
        if not separated(ha,hb+shift,a['brim']+b['brim']+4.2):continue
        lo=np.minimum(ha.min(axis=0)-a['brim']-.1,(hb+shift).min(axis=0)-b['brim']-.1)
        hi=np.maximum(ha.max(axis=0)+a['brim']+.1,(hb+shift).max(axis=0)+b['brim']+.1)
        dims=hi-lo
        if max(dims)>254:continue
        score=max(dims)+sum(dims)*.001
        if best is None or score<best[0]:best=(score,shift,lo,hi)
if best:
    _,shift,lo,hi=best;offset=(256-(hi-lo))/2-lo
    plate('05 一体后横梁_一体双风扇底梁_斜放',[place(a,*offset),place(b,*(offset+shift))])
else:
    single('18_','05 一体后横梁_斜放');single('20_','06 一体双风扇底梁_斜放')
for side in ('GPU','CPU'):single('10_'+side,f'{len(plates)+1:02d} {side}侧140风扇安装框')
psu=get('05_');tower=get('07_')
plate(f'{len(plates)+1:02d} 电源托架_显卡支架主体',[place(psu,20,36),place(tower,200,47)])
bars=[get('04_front'),get('04_rear')];shift=np.array([-35,35])/math.sqrt(2)
combined=bars[0]['size'][:2]+abs(shift);base=(256-combined)/2+np.array([abs(shift[0]),0])
plate(f'{len(plates)+1:02d} 两根底部横条_整件斜放',[place(bars[0],*base),place(bars[1],*(base+shift))])
# Upper/lower adjustable carriers share the spare area beside the front PCI frame.
for prefix,x,y in [('08_GPU_UPPER',185,28),('08_GPU_LOWER',205,144)]:
    p=get(prefix).copy();ts=p['tris']@rot('z',90).T;ts-=ts.min(axis=(0,1));p['tris']=ts;p['size']=ts.max(axis=(0,1))
    plates[2]['items'].append(place(p,x,y))
# Shift the front PCI frame left to make a full brim gap for the carriers.
plates[2]['items'][0]['xy']=np.array([8,58])

tail=shared[shared.index('checks=[]'):]
tail=tail.replace('==len(parts)==19','==len(parts)==17')
tail=tail.replace("('ALREADY_PRINTED_' if pi==0 else '')", "''")
cols=math.ceil(math.sqrt(len(plates)))
tail=tail.replace('ox=(pi%4)*307.2;oy=-(pi//4)*307.2',f'ox=(pi%{cols})*307.2;oy=-(pi//{cols})*307.2')
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-checks.json'", "SRC/'plate-checks.json'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-list.csv'", "SRC/'plate-list.csv'")
tail=tail.replace("settings['enable_prime_tower']='0';settings['print_sequence']='by layer'", "settings['enable_prime_tower']='0';settings['print_sequence']='by layer'")
exec(compile(tail,'v13_3mf_writer','exec'))

# Export the exact oriented, unscaled meshes used in the 3MF, one STL per assembly part.
printdir=SRC/'PRINT_STL';printdir.mkdir(exist_ok=True)
for pl in plates:
    for p in pl['items']:
        data=bytearray(('V13 mm '+p['name']).encode('ascii')[:80].ljust(80,b' ')+struct.pack('<I',len(p['tris'])))
        for t in p['tris']:
            no=np.cross(t[1]-t[0],t[2]-t[0]);no/=np.linalg.norm(no)
            data+=struct.pack('<12fH',*no,*t.reshape(-1),0)
        (printdir/(p['name']+'.stl')).write_bytes(data)
print(json.dumps({'plates':len(plates),'parts':len(parts),'continuous_beams_share_plate':best is not None,'output':str(DEST)},ensure_ascii=True))
