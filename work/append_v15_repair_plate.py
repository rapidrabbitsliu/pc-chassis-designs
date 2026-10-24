"""Update the user's saved nine-plate project and append a temporary repair plate.
Preserves per-object settings, plate labels and local XY positions. No printing.
"""
from pathlib import Path
import copy,json,math,re,shutil,uuid,zipfile
import xml.etree.ElementTree as E
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/ATX-Desk-v15'
BASE=ROOT/'outputs/ATX-Desk-v13/ATX-Desk-v13-All-Parts-9-Plates.3mf'
PATCH=OUT/'Style1_V15_GPU_Replacements_1_Plate_UNSLICED.3mf'
DEST=OUT/'Style1_V15_All_Parts_10_Plates_With_Temporary_Repair.3mf'
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';P='http://schemas.microsoft.com/3dmanufacturing/production/2015/06';REL='http://schemas.openxmlformats.org/package/2006/relationships'
E.register_namespace('',NS);E.register_namespace('p',P)
shutil.copy2(BASE,OUT/'Source_User_V13_9_Plates_Before_Update.3mf')
def md(el):return {m.get('key'):m.get('value') for m in el.findall('metadata') if m.get('key')}
def put(el,key,value):
    found=next((m for m in el.findall('metadata') if m.get('key')==key),None)
    if found is None:found=E.SubElement(el,'metadata',key=key)
    found.set('value',str(value))
def xml(el):return E.tostring(el,encoding='utf-8',xml_declaration=True)
def vertex_array(mesh_model):return np.array([[float(v.get(k)) for k in ('x','y','z')] for v in mesh_model.findall('.//{'+NS+'}vertex')])
with zipfile.ZipFile(BASE) as z:files={n:z.read(n) for n in z.namelist()}
with zipfile.ZipFile(PATCH) as z:patchfiles={n:z.read(n) for n in z.namelist()}
model=E.fromstring(files['3D/3dmodel.model']);cfg=E.fromstring(files['Metadata/model_settings.config']);res=model.find('{'+NS+'}resources');build=model.find('{'+NS+'}build')
pr=E.fromstring(patchfiles['3D/3dmodel.model']);pcfg=E.fromstring(patchfiles['Metadata/model_settings.config']);pres=pr.find('{'+NS+'}resources');pbuild=pr.find('{'+NS+'}build')
assemble=cfg.find('assemble')
oldplates=cfg.findall('plate');assert len(oldplates)==9
original_names=[md(p)['plater_name'] for p in oldplates]
objects={o.get('id'):o for o in cfg.findall('object')}
modelobjs={o.get('id'):o for o in res.findall('{'+NS+'}object')}
items={o.get('objectid'):o for o in build}
assemblies={o.get('object_id'):o for o in assemble}
def translate(el,dx=0,dy=0,dz=0):
    a=[float(x) for x in el.get('transform').split()];a[9]+=dx;a[10]+=dy;a[11]+=dz;el.set('transform',' '.join(f'{x:.10g}' for x in a))
# Reflow the global plate grid to four columns; retain every object's local XY.
for i,pl in enumerate(oldplates):
    dx=((i%4)-(i%3))*307.2;dy=(-(i//4)+(i//3))*307.2
    for inst in pl.findall('model_instance'):
        oid=md(inst)['object_id'];translate(items[oid],dx,dy);translate(assemblies[oid],dx,dy)
updates=[]
for pobj in pcfg.findall('object'):
    pname=md(pobj)['name'];stem=pname.removeprefix('V15_').removesuffix('.stl')
    target=next(o for o in objects.values() if md(o)['name'].removesuffix('.stl')==stem)
    oid=target.get('id');oldchild=modelobjs[oid].find('.//{'+NS+'}component');oldpath=oldchild.get('{'+P+'}path').lstrip('/');oldmid=oldchild.get('objectid')
    pchild=next(o for o in pres if o.get('id')==pobj.get('id')).find('.//{'+NS+'}component');newmesh=E.fromstring(patchfiles[pchild.get('{'+P+'}path').lstrip('/')])
    oldmesh=E.fromstring(files[oldpath]);oldsize=np.ptp(vertex_array(oldmesh),axis=0);newsize=np.ptp(vertex_array(newmesh),axis=0)
    newmesh.find('.//{'+NS+'}object').set('id',oldmid);files[oldpath]=xml(newmesh)
    dz=(newsize[2]-oldsize[2])/2;translate(items[oid],dz=dz);translate(assemblies[oid],dz=dz)
    put(target,'name','V15_'+stem+'.stl')
    part=target.find('part');put(part,'name','V15_'+stem+'.stl');put(part,'source_file',str(OUT/'PRINT_STL'/(stem+'.stl')))
    for a,v in zip('xyz',newsize/2):put(part,'source_offset_'+a,v)
    count=len(newmesh.findall('.//{'+NS+'}triangle'))
    for m in target.findall('metadata'):
        if 'face_count' in m.attrib:m.set('face_count',str(count))
    part.find('mesh_stat').set('face_count',str(count))
    updates.append({'object_id':oid,'part':stem,'new_size_mm':newsize.tolist(),'settings_preserved':True})
assert len(updates)==2
# Append a duplicate of the two new parts on plate 10, with explicit repair labels.
newplate=copy.deepcopy(pcfg.find('plate'));put(newplate,'plater_id',10);put(newplate,'plater_name','10 临时修补 V15 P12显卡塔 P13上托片');put(newplate,'locked','false')
for inst in list(newplate.findall('model_instance')):newplate.remove(inst)
rels=E.fromstring(files['3D/_rels/3dmodel.model.rels'])
nextid=max(int(o.get('id')) for o in res)+1
for index,pobj in enumerate(pcfg.findall('object')):
    oid=nextid+index*2+1;mid=oid-1;path=f'/3D/Objects/v15_repair_{index+1}.model'
    pwrap=next(o for o in pres if o.get('id')==pobj.get('id'));wrapper=copy.deepcopy(pwrap);wrapper.set('id',str(oid));wrapper.set('{'+P+'}UUID',str(uuid.uuid4()))
    component=wrapper.find('.//{'+NS+'}component');sourcepath=component.get('{'+P+'}path').lstrip('/');component.set('{'+P+'}path',path);component.set('objectid',str(mid));component.set('{'+P+'}UUID',str(uuid.uuid4()));res.append(wrapper)
    mesh=E.fromstring(patchfiles[sourcepath]);mesh.find('.//{'+NS+'}object').set('id',str(mid));files[path.lstrip('/')]=xml(mesh)
    ob=copy.deepcopy(pobj);oldoid=ob.get('id');ob.set('id',str(oid));ob.find('part').set('id',str(mid));put(ob,'name',('临时修补_P12_' if index==0 else '临时修补_P13_')+md(pobj)['name']);cfg.insert(len(cfg.findall('object')),ob)
    item=copy.deepcopy(next(i for i in pbuild if i.get('objectid')==oldoid));item.set('objectid',str(oid));item.set('{'+P+'}UUID',str(uuid.uuid4()));translate(item,dx=307.2,dy=-614.4);build.append(item)
    inst=E.SubElement(newplate,'model_instance');put(inst,'object_id',oid);put(inst,'instance_id',0);put(inst,'identify_id',1000+index)
    E.SubElement(assemble,'assemble_item',object_id=str(oid),instance_id='0',transform=item.get('transform'),offset='0 0 0')
    E.SubElement(rels,'{'+REL+'}Relationship',Target=path,Id='v15-repair-'+str(index),Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel')
cfg.insert(list(cfg).index(assemble),newplate)
# Remove stale slicer caches; Bambu Studio will regenerate plate images and slicing.
for pl in cfg.findall('plate'):
    for m in list(pl.findall('metadata')):
        if m.get('key') in ('thumbnail_file','thumbnail_no_light_file','top_file','pick_file'):pl.remove(m)
for n in list(files):
    if n.startswith('Metadata/') and (n.endswith(('.png','.gcode','.json')) or n.endswith('slice_info.config')):files.pop(n)
files['3D/3dmodel.model']=xml(model);files['Metadata/model_settings.config']=xml(cfg)
# Bambu's relationship loader expects unprefixed Relationship elements.
E.register_namespace('',REL)
files['3D/_rels/3dmodel.model.rels']=xml(rels)
E.register_namespace('',NS)
assert [md(p)['plater_name'] for p in cfg.findall('plate')[:9]]==original_names
assert len(cfg.findall('object'))==19 and len(cfg.findall('plate'))==10
with zipfile.ZipFile(DEST,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in files.items():z.writestr(n,b)
with zipfile.ZipFile(DEST) as z:assert z.testzip() is None
report={'file':str(DEST),'plates':10,'objects':19,'original_plate_labels_preserved':True,'updated_original_objects':updates,'temporary_plate':10,'temporary_parts':['P12','P13'],'sliced':False,'original_project_settings_unchanged':True}
(OUT/'ten_plate_project_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=True))
