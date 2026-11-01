from pathlib import Path
import adsk.core,adsk.fusion,json
ROOT=Path('C:/Users/sieme/Documents/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f')
OUT=ROOT/'outputs/ATX-Desk-v24'
def run(_context: str):
 app=adsk.core.Application.get()
 doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(ROOT/'outputs/ATX-Desk-v23/ATX_Desk_v23_short_fan_screws.f3d')))
 d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
 P=adsk.core.Point3D.create;V=adsk.core.ValueInput.createByString;m=adsk.fusion.TemporaryBRepManager.get()
 audit=json.loads((ROOT/'work/v24_head_audit.json').read_text(encoding='utf-8'))
 cs={o.component.name:o.component for o in root.occurrences}
 checks=[];changed=[]
 def cylinder(row,diam,expand=0):
  ax=row['axis'];idx=max(range(3),key=lambda k:abs(ax[k]));a=row['origin'][:];b=a[:]
  a[idx]=row['min'][idx]-expand;b[idx]=row['max'][idx]+expand
  return m.createCylinderOrCone(P(*[v/10 for v in a]),diam/20,P(*[v/10 for v in b]),diam/20)
 def intersection(body,tool):
  q=m.copy(body);assert m.booleanOperation(q,tool,adsk.fusion.BooleanTypes.IntersectionBooleanType);return q.volume*1000
 for rec in audit:
  rows=[];seen=set()
  for row in rec['cylinders']:
   if abs(row['diameter']-6.6)>.01:continue
   key=tuple(round(v,4) for v in row['origin'])
   if key not in seen:rows.append(row);seen.add(key)
  if not rows:continue
  c=cs[rec['name']];before=m.copy(c.bRepBodies.item(0));tools=[]
  for row in rows:
   axis='z' if row['axis'][2]>.9 else 'y';idx=2 if axis=='z' else 1
   pos=row['min'][idx];depth=row['max'][idx]-pos
   # Match the existing XZ construction plane cut direction (+Y).
   start=pos
   pi=c.constructionPlanes.createInput();pi.setByOffset(c.xZConstructionPlane if axis=='y' else c.xYConstructionPlane,V(f'{-start if axis=="y" else start} mm'))
   sk=c.sketches.add(c.constructionPlanes.add(pi));sk.name='V24 D8.2 M3 D7 head access'
   centre=row['origin'][:];centre[idx]=start
   curve=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(*[v/10 for v in centre])),.41);curve.isFixed=True
   ei=c.features.extrudeFeatures.createInput(sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation)
   ei.participantBodies=[c.bRepBodies.item(0)];ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(f'{depth+.02} mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
   c.features.extrudeFeatures.add(ei).name='V24 M3x6 D7 head well D8.2 compensated';sk.isVisible=False
   tools.append(cylinder(row,8.2,.021))
   checks.append({'part':c.name,'centre_mm':row['origin'],'axis':axis,'old_CAD_diameter_mm':6.6,'new_CAD_diameter_mm':8.2,'depth_mm':depth,'nominal_bearing_web_mm':3,'gauge_D7_6_overlap_mm3':intersection(c.bRepBodies.item(0),cylinder(row,7.6,-.001))})
  b=c.bRepBodies.item(0);assert c.bRepBodies.count==1 and b.isSolid and b.lumps.count==1,c.name
  removed=m.copy(before);assert m.booleanOperation(removed,b,adsk.fusion.BooleanTypes.DifferenceBooleanType)
  for tool in tools:assert m.booleanOperation(removed,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
  assert removed.volume*1000<.0001,(c.name,removed.volume*1000)
  changed.append(c.name)
 assert len(checks)==20 and len(changed)==8,(len(checks),changed)
 assert all(r['gauge_D7_6_overlap_mm3']<.0001 for r in checks),checks
 retained=[]
 for rec in audit:
  for row in rec['cylinders']:
   if abs(row['diameter']-8.2)<.01:
    vol=intersection(cs[rec['name']].bRepBodies.item(0),cylinder(row,7.6,-.001));assert vol<.0001
    retained.append({'part':rec['name'],'centre_mm':row['origin'],'diameter_mm':8.2,'gauge_overlap_mm3':vol})
 OUT.mkdir(exist_ok=True);(OUT/'Raw_STL').mkdir(exist_ok=True)
 parts=[];occs=[]
 for o in root.occurrences:
  if o.component.name.startswith('REF_'):continue
  c=o.component;b=c.bRepBodies.item(0);assert b.isSolid and b.lumps.count==1
  bb=b.preciseBoundingBox;parts.append({'name':c.name,'native_size_mm':[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in 'xyz'],'volume_mm3':b.volume*1000})
  opt=d.exportManager.createSTLExportOptions(b,str(OUT/'Raw_STL'/(c.name+'.stl')));opt.isBinaryFormat=True;assert d.exportManager.execute(opt)
  occs.append(o)
 assert len(parts)==15
 objects=adsk.core.ObjectCollection.create()
 for o in occs:objects.add(o)
 ii=d.createInterferenceInput(objects);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii);assert rr.count==0,rr.count
 bad=[d.timeline.item(i).name for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
 d.userParameters.add('v24_M3_D7_head_well',V('8.2 mm'),'mm','D7 head; nominal print shrink 0.3 to 0.6; target physical clear >=7.5 mm, verify test')
 report={'version':'V24','changed_parts':changed,'changed_head_wells':20,'retained_D8_2_head_wells':retained,'checks':checks,'head_diameter_mm':7,'screw_thread':'M3','thread_length_mm':6,'new_CAD_head_well_mm':8.2,'measured_previous_CAD_and_print_mm':[6.6,6.3],'expected_print_range_mm':[7.6,7.9],'physical_fit_test_required':True,'bearing_web_nominal_mm':3,'non_head_geometry_unchanged':True,'printed_parts':15,'interferences':0,'timeline':'healthy','sent_to_printer':False}
 (OUT/'parts.json').write_text(json.dumps(parts,indent=2),encoding='utf-8');(OUT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(OUT/'ATX_Desk_v24_M3_D7_head_clearance.f3d')))
 app.activeViewport.fit();app.activeViewport.refresh();app.activeViewport.saveAsImageFile(str(OUT/'Assembly.png'),1500,1100)
 print(json.dumps({'version':'V24','changed_parts':8,'enlarged_head_wells':20,'retained_D8_2_wells':len(retained),'interferences':0}))

