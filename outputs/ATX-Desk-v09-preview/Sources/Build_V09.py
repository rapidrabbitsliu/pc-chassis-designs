"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
BASE=ROOT+'Sources/Base_v07.f3d'
OUT=ROOT
def run(_context: str):
    app=adsk.core.Application.get();doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    for i in range(root.occurrences.count-1,-1,-1):
        o=root.occurrences.item(i)
        if o.component.name.startswith(('06_','13_','14_')):o.deleteMe()
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
    # Retain only top mounting beam from each rear frame, including GPU mounting holes.
    for n in ('12_rear_PCI_SUPPORT_FRAME','12_rear_CPU_SUPPORT_FRAME'):
        c=cs[n]
        box(c,-10,237,0,310,255,125,CUT,'Remove rear vertical and bottom frame')
    box(cs['12_rear_PCI_SUPPORT_FRAME'],-10,237,124.9,24.45,255,140.1,CUT,'Rear beam butt joint to PCI side')
    box(cs['12_rear_CPU_SUPPORT_FRAME'],282.45,237,124.9,310,255,140.1,CUT,'Rear beam butt joint to CPU side')
    # Left and right load-bearing sides; front frame retained.
    c=comp('16_CPU_VERTICAL_SIDE_SUPPORT')
    box(c,282.45,6,0,298.45,253.84,140,NEW,'CPU side vertical frame')
    box(c,282.3,22,16,298.6,237.84,124,CUT,'CPU side open window')
    poly(c,'x',282.45,[(22,16),(38,16),(237.84,108),(237.84,124)],16,JOIN,'CPU side diagonal')
    c=comp('16_PCI_INSET_SIDE_SUPPORT')
    poly(c,'y',6,[(8.45,0),(24.45,0),(12,140),(-4,140)],247.84,NEW,'PCI side inset 12.45 mm')
    box(c,-4.1,22,16,24.6,237.84,124,CUT,'PCI side open window')
    poly(c,'x',-4,[(22,16),(38,16),(237.84,108),(237.84,124)],28.45,JOIN,'PCI side diagonal before taper trim')
    poly(c,'y',5.9,[(-10,0),(8.45,0),(-4,140),(-10,140)],248.1,CUT,'Trim diagonal to outer tapered face')
    poly(c,'y',5.9,[(24.45,0),(40,0),(40,140),(12,140)],248.1,CUT,'Trim diagonal to inner tapered face')
    c=comp('17_REAR_TOP_BEAM_SEAM_JOINER')
    box(c,132,253.84,126,176,257.84,138,NEW,'Rear top beam seam bridge')
    for x,n in [(140,'12_rear_PCI_SUPPORT_FRAME'),(164,'12_rear_CPU_SUPPORT_FRAME')]:
        circle(c,'y',253.84,x,132,3.4,4,CUT,'M3 seam bridge clearance')
        circle(cs[n],'y',247.34,x,132,4.6,6.5,CUT,'Trial short insert for rear beam bridge')
    # Remove unnecessary CPU-end beam overhang while preserving nine hole centres.
    for n,c in cs.items():
        if n.startswith('03_'):box(c,302.45,-20,0,312,260,220,CUT,'Trim CPU beam end flush with mounting boss tangent')
    for o in created:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 frame') or d.appearances.itemByName('V03 bracket')
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','support_layout':'left right front; rear top beam only','PSU_center_xy_mm':[152.4,121.92],'PSU_bottom_gap_mm':30,'PSU_top_retainers_removed':2,'CPU_beam_end_old_mm':308.8,'CPU_beam_end_new_mm':302.45,'CPU_ground_outer_mm':298.45,'required_CPU_boss_outer_mm':302.45,'nine_hole_centres_preserved':True,'board_bottom_z_mm':158,'floor_width_mm':290,'timeline_health':'healthy','interference_count':rr.count}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,39);cam.target=P(15,12,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    cam=view.camera;cam.eye=P(49,53,34);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Rear.png',1500,1150)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v09_layout.f3d'))
    print(json.dumps(data))
