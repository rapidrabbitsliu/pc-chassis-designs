"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v09-preview/ATX_Desk_v09_layout.f3d'
OUT=ROOT+'ATX-Desk-v10-preview'
def run(_context: str):
    app=adsk.core.Application.get();doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    for i in range(root.occurrences.count-1,-1,-1):
        if root.occurrences.item(i).component.name.startswith('16_'):root.occurrences.item(i).deleteMe()
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
    # Keep the overall ground width 290: both floor extremes move 4 mm to the right.
    poly(cs['12_front_PCI_SUPPORT_FRAME'],'y',-10.1,[(-10,0),(12.45,0),(-4,140),(-10,140)],16.2,CUT,'Increase PCI inward taper to 16.45 mm')
    box(cs['12_front_CPU_SUPPORT_FRAME'],298.45,-10,0,302.45,6,140,JOIN,'CPU front edge aligned with upper beam')
    box(cs['12_rear_CPU_SUPPORT_FRAME'],282.45,237.84,125,286.45,253.84,140,JOIN,'Extend rear beam to relocated CPU side')
    for n,c in cs.items():
        if n.startswith('04_'):
            yc=39.92 if 'front' in n else 203.92
            box(c,24.4,yc-10.1,-.1,28.45,yc+10.1,8.1,CUT,'Floor crossbar shortened for increased PCI taper')
            box(c,282.45,yc-10,0,286.45,yc+10,8,JOIN,'Extend floor crossbar to CPU frame')
    c=comp('16_CPU_VERTICAL_SIDE_FLUSH_TO_BEAM')
    box(c,286.45,6,0,302.45,253.84,140,NEW,'CPU outer face matches beam X302.45')
    box(c,286.3,22,16,302.6,237.84,124,CUT,'CPU side open window')
    poly(c,'x',286.45,[(22,16),(38,16),(237.84,108),(237.84,124)],16,JOIN,'CPU side diagonal')
    c=comp('16_PCI_INSET_SIDE_16_45mm')
    poly(c,'y',6,[(12.45,0),(28.45,0),(12,140),(-4,140)],247.84,NEW,'PCI taper 16.45 over 140 mm height')
    box(c,-4.1,22,16,28.6,237.84,124,CUT,'PCI side open window')
    poly(c,'x',-4,[(22,16),(38,16),(237.84,108),(237.84,124)],32.45,JOIN,'PCI diagonal before taper trim')
    poly(c,'y',5.9,[(-10,0),(12.45,0),(-4,140),(-10,140)],248.1,CUT,'Trim diagonal outer tapered face')
    poly(c,'y',5.9,[(28.45,0),(40,0),(40,140),(12,140)],248.1,CUT,'Trim diagonal inner tapered face')
    for o in created:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 frame') or d.appearances.itemByName('V03 bracket')
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    floor=[];objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_'):
            for b in o.component.bRepBodies:
                for vv in b.vertices:
                    p=o.transform2.copy();q=vv.geometry.copy();q.transformBy(p)
                    if abs(q.z)<1e-5:floor.append(q.x*10)
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    assert abs(min(floor)-12.45)<.01 and abs(max(floor)-302.45)<.01,[min(floor),max(floor)]
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','floor_x_mm':[min(floor),max(floor)],'floor_width_mm':max(floor)-min(floor),'CPU_vertical_face_and_beam_end_x_mm':302.45,'PCI_inward_taper_mm':16.45,'PCI_old_taper_mm':12.45,'board_and_nine_hole_centres_unchanged':True,'PCB_edge_x_mm':304.8,'PCB_overhang_beyond_frame_mm':2.35,'PSU_still_centered_under_board':True,'timeline_health':'healthy','interference_count':rr.count}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,39);cam.target=P(15,12,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    cam=view.camera;cam.eye=P(15,-60,16);cam.target=P(15,12,16);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Front.png',1500,1150)
    cam=view.camera;cam.eye=P(54,-46,39);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v10_layout.f3d'))
    print(json.dumps(data))
