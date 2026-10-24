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
        if o.component.name.startswith(('04_','05_')):o.deleteMe()
    for o in root.occurrences:
        if o.component.name.startswith(('REF_PSU_','06_')):
            m=o.transform2;m.translation=adsk.core.Vector3D.create(0,6,0);o.transform2=m
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
    frames={o.component.name:o.component for o in root.occurrences}
    c=comp('04_FRONT_PSU_GROUND_BAR_RELOCATED')
    box(c,24.45,89.92,0,282.45,109.92,8,NEW,'Ground bar ahead of downward intake')
    c=comp('05_REARWARD_PSU_OPEN_BOTTOM_CRADLE')
    box(c,73.4,89.92,24,85.4,253.84,30,NEW,'PCI edge runner under PSU chassis')
    box(c,85.4,89.92,24,231.4,101.92,30,JOIN,'Front tie outside PSU intake')
    box(c,219.4,101.92,24,231.4,253.84,30,JOIN,'CPU edge runner under PSU chassis')
    for x in (79.4,225.4):
        box(c,x-5,94.92,8,x+5,104.92,24,JOIN,'Front foot onto ground crossbar')
        box(c,x-5,240.84,16,x+5,250.84,24,JOIN,'Rear foot onto rear frame bottom beam')
    for x in (75,227.8):
        for y in (134,224):box(c,x,y,30,x+2,y+6,36,JOIN,'PSU side locating stop')
    # Rear bracing skirts the full PSU rear envelope, including all its controls.
    for n,x0,x1 in [('12_rear_PCI_SUPPORT_FRAME',52,68),('12_rear_CPU_SUPPORT_FRAME',236.8,252.8)]:
        c=frames[n]
        box(c,x0,237.84,16,x1,253.84,125,JOIN,'Vertical support outside PSU exhaust envelope')
        if x0==52:poly(c,'y',237.84,[(30,16),(42,16),(52,112),(52,125)],16,JOIN,'PCI outer diagonal away from PSU')
        else:poly(c,'y',237.84,[(252.8,16),(264.8,16),(277,112),(277,125)],16,JOIN,'CPU outer diagonal away from PSU')
    # Join the two printed rear halves at top and bottom.
    for tag,z0,z1 in [('TOP',126,138),('BOTTOM',2,14)]:
        c=comp('15_REAR_'+tag+'_SEAM_CONNECTOR')
        box(c,132,253.84,z0,176,256.84,z1,NEW,'Rear seam bridge clear of exhaust opening')
        for x,n in [(140,'12_rear_PCI_SUPPORT_FRAME'),(164,'12_rear_CPU_SUPPORT_FRAME')]:
            circle(c,'y',253.84,x,(z0+z1)/2,3.4,3,CUT,'M3 bridge screw clearance')
            circle(frames[n],'y',247.34,x,(z0+z1)/2,4.6,6.5,CUT,'Trial short M3 insert pocket for seam bridge')
    for o in created:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 frame') if o.component.name.startswith('15_') else d.appearances.itemByName('V03 bracket')
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','PSU_shift_rear_mm':60,'PSU_bounds_mm':[[77.4,111.92,30],[227.4,251.92,116]],'PSU_rear_face_to_frame_outer_face_mm':1.92,'PSU_bottom_gap_mm':30,'rear_clear_opening_x_mm':[68,236.8],'rear_clear_opening_z_mm':[16,125],'rear_seam_bridges':2,'board_bottom_z_mm':158,'GPU_support_retained':True,'floor_width_mm':290,'timeline_health':'healthy','interference_count':rr.count,'actual_plug_and_switch_access':'Not yet checked against physical PSU; full rear body envelope kept open'}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(48,55,32);cam.target=P(15,17,13);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Rear.png',1500,1150)
    cam=view.camera;cam.eye=P(54,-46,39);cam.target=P(15,13,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v08_layout.f3d'))
    print(json.dumps(data))
