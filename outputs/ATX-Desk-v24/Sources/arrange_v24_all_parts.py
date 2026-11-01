from pathlib import Path
import struct,math,json,zipfile,uuid,copy,csv,hashlib
import xml.etree.ElementTree as E
import numpy as np
ROOT=Path(__file__).resolve().parents[1]/'outputs'
SRC=ROOT/'ATX-Desk-v24'
DEST=SRC/'Style1_V24_All_Latest_Parts_9_Plates.3mf'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
R='http://schemas.openxmlformats.org/package/2006/relationships'
E.register_namespace('',NS);E.register_namespace('p',P)
parts={};source_checks=[]
for meta in json.loads((SRC/'parts.json').read_text(encoding='utf-8')):
    n=meta['name'];path=SRC/'PRINT_STL'/(n+'.stl');raw=path.read_bytes()
    cnt=struct.unpack_from('<I',raw,80)[0]
    dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    tris=np.frombuffer(raw,dtype=dt,offset=84,count=cnt)['v'].astype(float)
    volume=np.sum(tris[:,0]*np.cross(tris[:,1],tris[:,2]))/6
    error=abs(volume-meta['volume_mm3'])/meta['volume_mm3']
    assert error<.003,(n,error)
    source_checks.append({'part':n,'source':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'volume_error_percent':error*100})
    tris-=tris.min(axis=(0,1));size=tris.max(axis=(0,1))
    parts[n]=dict(name=n,tris=tris,size=size,brim=3 if n.startswith('16_') else 5,support=n.startswith(('05_','12_front_CPU','19_MID','20_')))
def get(prefix):return next(p for n,p in parts.items() if n.startswith(prefix))
def place(p,x,y):
    q=p.copy();q['xy']=np.array([x,y]);return q
def turn(p):
    q=p.copy();t=p['tris']@np.array([[0,-1,0],[1,0,0],[0,0,1]]).T
    t-=t.min(axis=(0,1));q['tris']=t;q['size']=t.max(axis=(0,1));return q
plates=[]
def single(prefix,label):
    p=get(prefix);plates.append({'name':label,'items':[place(p,*((256-p['size'][:2])/2))]})
single('10_GPU','01 V24 P16 left fan panel - counterbores UP')
single('10_CPU','02 V24 P17 right fan panel - counterbores UP')
single('05_','03 V22 P08 PSU stops - screw access corrected')
front=turn(get('12_front_PCI'));gpu=get('07_')
plates.append({'name':'04 P03 front PCI frame + V20 P12 integrated GPU','items':[place(front,10,(256-front['size'][1])/2),place(gpu,166,64)]})
single('12_front_CPU','05 P04 front CPU frame - support on')
group=[get('16_CPU'),get('19_PCI'),get('19_MID'),get('19_CPU')]
total=sum(p['size'][1]+2*p['brim'] for p in group)+3*4
y=(256-total)/2;items=[]
for p in group:
    items.append(place(p,(256-p['size'][0])/2,y+p['brim']))
    y+=p['size'][1]+2*p['brim']+4
plates.append({'name':'06 P02 CPU side + P09 P10 P11 board rails','items':items})
single('16_PCI','07 P01 PCI inset side - outer face flat')
plates.append({'name':'08 P05 rear beam + P15 dual fan rail - diagonal','items':[place(get('18_'),7.359,27.706),place(get('20_'),39.338,7.359)]})
plates.append({'name':'09 P06 P07 ground bars - diagonal','items':[place(get('04_front'),36.430,11.681),place(get('04_rear'),11.681,36.430)]})
shared=(ROOT/'arrange_v12_plates.py').read_text(encoding='utf-8')
exec(shared[shared.index('def hull('):shared.index('checks=[]')])
tail=shared[shared.index('checks=[]'):]
tail=tail.replace('ox=(pi%4)*307.2;oy=-(pi//4)*307.2','ox=(pi%3)*307.2;oy=-(pi//3)*307.2')
tail=tail.replace('==len(parts)==19','==len(parts)==15').replace("('ALREADY_PRINTED_' if pi==0 else '')","'LATEST_V24_'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-template.3mf'","ROOT/'ATX-Desk-v21/Style1_V21_P08_PSU_Stops_Test_READY.3mf'")
tail=tail.replace("ROOT/'ATX-Desk-v12-plate-checks.json'","SRC/'all-parts-plate-checks.json'").replace("ROOT/'ATX-Desk-v12-plate-list.csv'","SRC/'all-parts-plate-list.csv'")
tail=tail.replace("'support_on_build_plate_only':1","'support_on_build_plate_only':1,'support_top_z_distance':0.2,'support_bottom_z_distance':0.2,'support_interface_top_layers':3,'support_interface_spacing':0.3,'support_threshold_angle':30,'support_object_xy_distance':0.35")
exec(compile(tail,'V24_all_parts_writer','exec'))
(SRC/'all-parts-source-verification.json').write_text(json.dumps(source_checks,indent=2),encoding='utf-8')
with zipfile.ZipFile(DEST) as z:
    assert z.testzip() is None
    cfg=E.fromstring(z.read('Metadata/model_settings.config'))
    assert len(cfg.findall('object'))==15 and len(cfg.findall('plate'))==9
    settings=json.loads(z.read('Metadata/project_settings.config'))
    assert settings['wall_loops']=='5' and settings['layer_height']=='0.2' and settings['sparse_infill_density']=='40%'
    assert settings['sparse_infill_pattern']=='gyroid' and all(x=='PETG' for x in settings['filament_type'])
print(json.dumps({'latest_source_parts':15,'plates':9,'output':str(DEST)}))
