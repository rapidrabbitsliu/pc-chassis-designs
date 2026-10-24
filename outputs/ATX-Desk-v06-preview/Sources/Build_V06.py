"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
BASE=ROOT+'Sources/Base_v05.f3d'
OUT=ROOT
def run(_context: str):
    app=adsk.core.Application.get();doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    for i in range(root.occurrences.count-1,-1,-1):
        o=root.occurrences.item(i);n=o.component.name
        if n.startswith(('01_','02_','11_')):o.deleteMe()
    for o in root.occurrences:
        n=o.component.name
        if n.startswith(('03_','07_','08_','09_','10_','REF_CASE_FAN_','REF_AIRFLOW_','REF_BOARD_','REF_CPU_','REF_MEMORY_','REF_PRIMARY_','REF_SECOND_','REF_GPU_')):
            m=o.transform2;m.translation=adsk.core.Vector3D.create(0,0,-5);o.transform2=m
    d.snapshots.add()
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
    for tag,y in [('front',-10),('rear',237.84)]:
        for side,x0,x1 in [('PCI',8.45,152.1),('CPU',152.7,298.45)]:
            c=comp('12_'+tag+'_'+side+'_SUPPORT_FRAME')
            topx=-4 if side=='PCI' else x0
            poly(c,'y',y,[(x0,0),(x1,0),(x1,140),(topx,140)],16,NEW,'Front rear load frame')
            if tag=='front':
                lo,hi=(30,134) if side=='PCI' else (171,277)
                box(c,lo,y-1,16,hi,y+17,124,CUT,'Open front frame window')
                # Diagonal brace within each front opening.
                poly(c,'y',y,[(lo,16),(lo+12,16),(hi,112),(hi,124)],16,JOIN,'Front diagonal brace')
            else:
                box(c,30,y-1,16,277,y+17,125,CUT,'Wide rear exhaust opening')
    for side,x0,x1 in [('PCI',8.45,24.45),('CPU',282.45,298.45)]:
        c=comp('13_'+side+'_LOW_FLOOR_RUNNER')
        box(c,x0,6,0,x1,237.84,8,NEW,'Low floor tie between front and rear')
        c=comp('14_'+side+'_TOP_LONGITUDINAL_RAIL')
        a,b=(-4,12) if side=='PCI' else (282.45,298.45)
        box(c,a,6,128,b,237.84,140,NEW,'Top rail carries three motherboard beams')
    for o in root.occurrences:
        if o.component.name.startswith('04_'):
            c=o.component
            box(c,8,20,-.1,24.45,220,8.1,CUT,'Butt joint to PCI floor runner')
            box(c,282.45,20,-.1,299,220,8.1,CUT,'Butt joint to CPU floor runner')
    for o in root.occurrences:
        if o.component.name.startswith('12_'):
            c=o.component
            if '_front_' in c.name:box(c,14,-2.65,128,281.45,6.01,140.01,CUT,'Seat for front motherboard beam rib')
            else:box(c,14,237.83,128,281.45,242.68,140.01,CUT,'Seat for rear motherboard beam rib')
    for o in created:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 frame') or d.appearances.itemByName('V03 bracket')
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad,bad
    objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','board_bottom_z_mm':158,'board_lowered_mm':50,'PSU_top_mm':116,'board_to_PSU_gap_mm':42,'lowest_board_beam_z_mm':128,'PSU_retainer_top_mm':125,'front_cover_removed':True,'support_layout':'front and rear frames; open sides with low ties and top rails','floor_width_mm':290,'timeline_health':'healthy','interference_count':rr.count}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,40);cam.target=P(15,12,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    cam=view.camera;cam.eye=P(53,48,36);cam.target=P(15,12,13);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Rear.png',1500,1150)
    cam=view.camera;cam.eye=P(54,-46,40);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v06_layout.f3d'))
    print(json.dumps(data))
