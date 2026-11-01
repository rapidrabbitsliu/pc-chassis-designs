from pathlib import Path
import adsk.core,adsk.fusion,json
ROOT=Path('C:/Users/sieme/Documents/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f')
def run(_context: str):
 app=adsk.core.Application.get()
 doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(ROOT/'outputs/ATX-Desk-v23/ATX_Desk_v23_short_fan_screws.f3d')))
 d=adsk.fusion.Design.cast(app.activeProduct);data=[]
 for o in d.rootComponent.occurrences:
  c=o.component
  if c.name.startswith('REF_'):continue
  faces=[]
  for b in c.bRepBodies:
   for f in b.faces:
    cy=adsk.core.Cylinder.cast(f.geometry)
    if cy and 2.9<cy.radius*10<4.5:
     bb=f.boundingBox
     faces.append({'diameter':cy.radius*20,'origin':[v*10 for v in cy.origin.asArray()],'axis':cy.axis.asArray(),'min':[v*10 for v in bb.minPoint.asArray()],'max':[v*10 for v in bb.maxPoint.asArray()]})
  features=[{'name':f.name,'sketch':f.profile.parentSketch.name if f.profile.objectType=='adsk::fusion::Profile' else ''} for f in c.features.extrudeFeatures if any(w in f.name.lower() for w in ['head','well','screw','channel'])]
  data.append({'name':c.name,'cylinders':faces,'features':features})
 (ROOT/'work/v24_head_audit.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 print(json.dumps({'parts':len(data),'head_cylinders':sum(len(x['cylinders']) for x in data)}))
