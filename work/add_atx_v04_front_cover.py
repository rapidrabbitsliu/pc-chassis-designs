"""V04: removable two-piece lower front cable cover; V03 imported into a new document."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v03-preview/ATX_Desk_v03_layout.f3d'
OUT=ROOT+'ATX-Desk-v04-preview'
def run(_context: str):
    app=adsk.core.Application.get();doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    cs={o.component.name:o.component for o in root.occurrences}
    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    def comp(name):
        c=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component;c.name=name;return c
    def sketch(c,y):
        pi=c.constructionPlanes.createInput();pi.setByOffset(c.xZConstructionPlane,V(str(-y)+' mm'))
        return c.sketches.add(c.constructionPlanes.add(pi))
    def extrude(c,sk,depth,op,name):
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        if op==CUT:inp.participantBodies=[c.bRepBodies.item(0)]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False;return f
    def poly(c,y,pts,depth,op,name):
        sk=sketch(c,y)
        for a,b in zip(pts,pts[1:]+pts[:1]):
            q=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P(a[0]/10,y/10,a[1]/10)),sk.modelToSketchSpace(P(b[0]/10,y/10,b[1]/10)));q.isFixed=True
        return extrude(c,sk,depth,op,name)
    def circle(c,y,x,z,diam,depth,op,name):
        sk=sketch(c,y);q=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x/10,y/10,z/10)),diam/20);q.isFixed=True
        return extrude(c,sk,depth,op,name)
    left=comp('11_LOWER_FRONT_COVER_PCI_HALF')
    low=8.45-12.45*8/190;high=8.45-12.45*182/190
    poly(left,-14.4,[(low,8),(152.1,8),(152.1,182),(high,182)],3,NEW,'3 mm PETG lower front cover - follows PCI side taper')
    right=comp('11_LOWER_FRONT_COVER_CPU_HALF')
    poly(right,-14.4,[(152.7,8),(298.45,8),(298.45,182),(152.7,182)],3,NEW,'3 mm PETG lower front cover - straight CPU edge')
    for c,x in [(left,25),(right,286)]:
        poly(c,-14.4,[(x-7,180),(x+7,180),(x+7,196),(x-7,196)],3,JOIN,'Upper removable mounting tab')
        circle(c,-11.4,x,192.5,8,8.75,JOIN,'Upper mounting stand-off')
        circle(c,-14.4,x,192.5,3.4,11.75,CUT,'Upper M3x16 screw clearance')
        circle(cs['03_FRONT_MOTHERBOARD_BEAM'],-2.65,x,192.5,4.7,4.7,CUT,'M3 short heat insert for removable front cover')
    circle(cs['01_CPU_front_VERTICAL_SIDE'],-10,286,192.5,8.4,7.35,CUT,'Upper cover stand-off clearance')
    for c,x,frame in [(left,17.5,'01_PCI_front_INSET_SIDE'),(right,290.45,'01_CPU_front_VERTICAL_SIDE')]:
        circle(c,-11.4,x,20,8,1.4,JOIN,'Lower mounting spacer')
        circle(c,-14.4,x,20,3.4,4.4,CUT,'Lower M3x8 screw clearance')
        circle(cs[frame],-10,x,20,4.7,4.7,CUT,'M3 short heat insert for removable front cover')
    for z in (45,150):
        poly(left,-11.4,[(148,z-8),(162,z-8),(162,z+8),(148,z+8)],6,JOIN,'Hidden center seam joining lug')
        circle(left,-11.4,157.5,z,4.7,4.7,CUT,'M3 short heat insert in seam lug')
        circle(right,-14.4,157.5,z,3.4,3,CUT,'M3x6 center seam screw clearance')
    appc=d.appearances.itemByName('V03 frame')
    assert appc
    for c in (left,right):
        assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
        c.bRepBodies.item(0).appearance=appc
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad,bad
    objects=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_CENTER_152.4_121.92') or n.startswith('REF_CASE_FAN_'):objects.add(o)
    inp=d.createInterferenceInput(objects);inp.areCoincidentFacesIncluded=False;result=d.analyzeInterference(inp)
    interferences=[{'one':result.item(i).entityOne.parentComponent.name,'two':result.item(i).entityTwo.parentComponent.name,'volume_mm3':result.item(i).interferenceBody.volume*1000} for i in range(result.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':result.count,'interferences':interferences},f,indent=2)
    parts=[]
    for c in (left,right):
        b=c.bRepBodies.item(0);bb=b.boundingBox
        parts.append({'name':c.name,'volume_mm3':b.volume*1000,'bounds_xyz_mm':[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in ('x','y','z')]})
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','cover_thickness_mm':3,'main_cover_z_mm':[8,182],'bottom_gap_mm':8,'upper_gap_to_main_beam_mm':8,'center_seam_mm':.6,'front_cover_y_mm':[-14.4,-11.4],
          'screw_plan':{'M3x16':2,'M3x8':2,'M3x6':2,'short_M3_insert_OD5_H4.5':6},'parts':parts,'timeline_features':d.timeline.count,'timeline_health':'healthy','interference_count':result.count,
          'PSU_side_intake_open':True,'PSU_rear_exhaust_open':True,'ground_width_mm':290}
    with open(OUT+'/cover.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,48);cam.target=P(15,12,17);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v04_layout.f3d'))
    print(json.dumps(data))
