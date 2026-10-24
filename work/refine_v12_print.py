"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v11-preview/ATX_Desk_v11_layout.f3d'
OUT=ROOT+'ATX-Desk-v12-print-review'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
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
    rear=cs['18_REAR_BEAM_PCI_TAPERED_END_AND_FRONT_LAP'];mid=cs['19_MID_LONGITUDINAL_BOARD_RAIL_243_84mm']
    for c,name in [(mid,'Centre rail rear seat mounting clearance'),(rear,'Trial short M3 insert for centre rail rear anchor')]:
        for i in range(c.features.count-1,-1,-1):
            if c.features.item(i).name==name:c.features.item(i).deleteMe()
    box(rear,136.77,218.5,127.9,145.17,237.84,140.1,CUT,'Clearance channel for continuous middle rail rib')
    circle(rear,'z',133.5,134,222.5,4.7,6.5,CUT,'Trial short M3 insert for centre rail rear anchor')
    box(mid,136.97,218.5,128,144.97,237.84,140,JOIN,'Continue underside rib nearly to rail end')
    poly(mid,'y',218.5,[(136.97,134),(144.97,134),(149.97,140),(131.97,140)],19.34,JOIN,'Continue printable rib transition')
    circle(mid,'z',140,134,222.5,3.4,8,CUT,'Centre rail rear seat mounting clearance')
    os.makedirs(OUT+'/Raw_STL',exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    objs=adsk.core.ObjectCollection.create();parts=[]
    for o in root.occurrences:
        n=o.component.name;c=o.component
        if not n.startswith('REF_'):
            assert c.bRepBodies.count==1,(n,c.bRepBodies.count)
            b=c.bRepBodies.item(0);assert b.isSolid
            bb=b.boundingBox;dims=[(bb.maxPoint.x-bb.minPoint.x)*10,(bb.maxPoint.y-bb.minPoint.y)*10,(bb.maxPoint.z-bb.minPoint.z)*10]
            mode='xy';angle=0;brim=5;note='Check supports in slicer'
            if n.startswith('16_'):mode='yz';brim=3;note='Side frame laid on its side; PCI taper may need local support'
            elif n.startswith(('12_front_','10_','20_','08_')):mode='xz'
            elif n.startswith('07_'):mode='yz';note='Tower on side; inspect local supports around holes and foot'
            elif n.startswith('04_'):angle=45;note='Rotate 45 degrees on bed; no joint needed'
            elif n.startswith('19_'):mode='xy';note='Bosses upward; middle rail uses continuous underside rib; inspect 6 mm end overhangs'
            parts.append({'name':n,'native_size_mm':dims,'volume_mm3':b.volume*1000,'orientation':mode,'angle_deg':angle,'brim_mm':brim,'note':note})
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    with open(OUT+'/parts.json','w') as f:json.dump(parts,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,43);cam.target=P(15,12,15);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    vis={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:
        if o.component.name.startswith('REF_'):o.isLightBulbOn=False
    cam=view.camera;cam.eye=P(48,45,45);cam.target=P(15,12,12);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Structure.png',1500,1150)
    for o in root.occurrences:o.isLightBulbOn=vis[o.component.name]
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v12_print_review.f3d'))
    # Export every printable solid, excluding all hardware reference models.
    for o in root.occurrences:
        if not o.component.name.startswith('REF_'):
            op=d.exportManager.createSTLExportOptions(o.component.bRepBodies.item(0),OUT+'/Raw_STL/'+o.component.name+'.stl');op.isBinaryFormat=True
            assert d.exportManager.execute(op)
            assert os.path.exists(OUT+'/Raw_STL/'+o.component.name+'.stl')
    print(json.dumps({'parts':len(parts),'timeline_health':'healthy','interference_count':rr.count}))
