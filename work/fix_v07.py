"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v06-preview/ATX_Desk_v06_layout.f3d'
OUT=ROOT+'ATX-Desk-v07-preview'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    created=[];refcreated=[]
    def comp(name,ref=False):
        o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name
        (refcreated if ref else created).append(o);return o.component
    def plane(c,axis,pos):
        pi=c.constructionPlanes.createInput();base={'z':c.xYConstructionPlane,'x':c.yZConstructionPlane,'y':c.xZConstructionPlane}[axis]
        pi.setByOffset(base,V(str(-pos if axis=='y' else pos)+' mm'));return c.constructionPlanes.add(pi)
    def point(axis,pos,u,v):return P(*{'z':(u/10,v/10,pos/10),'x':(pos/10,u/10,v/10),'y':(u/10,pos/10,v/10)}[axis])
    def profile(c,axis,pos,pts,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name
        for a,b in zip(pts,pts[1:]+pts[:1]):
            q=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(point(axis,pos,*a)),sk.modelToSketchSpace(point(axis,pos,*b)));q.isFixed=True
        assert sk.profiles.count==1,(name,sk.profiles.count)
        return sk
    def ext(c,sk,depth,op,name):
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        if op==CUT:inp.participantBodies=[c.bRepBodies.item(i) for i in range(c.bRepBodies.count)]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False;return f
    def poly(c,axis,pos,pts,depth,op,name):return ext(c,profile(c,axis,pos,pts,name+' sketch'),depth,op,name)
    def box(c,x0,y0,z0,x1,y1,z1,op,name):return poly(c,'z',z0,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z1-z0,op,name)
    def circle(c,axis,pos,u,v,diam,depth,op,name):
        sk=c.sketches.add(plane(c,axis,pos));q=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(point(axis,pos,u,v)),diam/20);q.isFixed=True
        return ext(c,sk,depth,op,name)
    cs={o.component.name:o.component for o in root.occurrences}
    lower=cs['08_GPU_LOWER_TWO_TAB_RECEIVER_ADJUSTABLE'];tower=cs['07_GPU_REINFORCED_REAR_TOWER'];frames=cs
    box(lower,73,244,145.9,171,260.1,148,CUT,'Receiver clearance above structural foot')
    for x in (96,116):
        box(tower,x-7,246.3,139.9,x+7,248.7,148.1,CUT,'Through foot clearance below GPU metal tabs')
        box(frames['12_rear_PCI_SUPPORT_FRAME'],x-7,246.3,124.9,x+7,248.7,140.1,CUT,'Open metal tab exit through rear frame')
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'STRUCTURAL_CONCEPT_PREVIEW_NOT_FOR_PRINTING','board_bottom_z_mm':158,'upper_ear_ledge_z_mm':282,'upper_height_travel_mm':30,'lower_tab_slots_nominal_centres_x_mm':[96,116],'lower_slot_width_y_mm':2.4,'lower_slots_open_bottom':True,'lower_height_travel_mm':8,'tower_wall_mm':10,'tower_foot_mm':8,'insert_pilot_mm':4.6,'insert_pilot_requires_coupon_test':True,'hardware':'M3 screws with washers and rear nuts for carrier clamps; base screws longer than 6mm required','real_GPU_bracket_measurement_required':True,'strength_analysis':'No FEA or load test; geometry and load path revision only','timeline_health':'healthy','interference_count':rr.count}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(53,48,36);cam.target=P(15,12,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Rear.png',1500,1150)
    visible={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:o.isLightBulbOn=o.component.name.startswith(('07_','08_'))
    cam=view.camera;cam.eye=P(34,5,30);cam.target=P(12,25,22);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Bracket_detail.png',1400,1200)
    for o in root.occurrences:o.isLightBulbOn=visible[o.component.name]
    cam=view.camera;cam.eye=P(53,48,36);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v07_layout.f3d'))
    print(json.dumps(data))
