"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
BASE=ROOT+'Sources/Base_v11.f3d'
OUT=ROOT
def run(_context: str):
    app=adsk.core.Application.get();doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    for i in range(root.occurrences.count-1,-1,-1):
        if root.occurrences.item(i).component.name.startswith(('03_','09_')):root.occurrences.item(i).deleteMe()
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
    for n in ('12_front_PCI_SUPPORT_FRAME','12_front_CPU_SUPPORT_FRAME'):
        c=cs[n]
        for i in range(c.features.count-1,-1,-1):
            if c.features.item(i).name=='Seat for front motherboard beam rib':c.features.item(i).deleteMe()
    holes={1:(16.51,233.68),2:(140.97,233.68),3:(298.45,210.82),4:(16.51,78.74),5:(140.97,78.74),6:(298.45,78.74),7:(16.51,6.35),8:(140.97,6.35),9:(298.45,6.35)}
    # Integral seat on the rear beam supports the middle longitudinal rail.
    rear=cs['18_REAR_BEAM_PCI_TAPERED_END_AND_FRONT_LAP']
    box(rear,130,218.5,128,152.4,242.68,140,JOIN,'Integral front projecting seat for middle longitudinal rail')
    box(rear,136.77,218.5,127.9,145.17,237.84,140.1,CUT,'Clearance channel for continuous middle rail rib')
    circle(rear,'z',133.5,134,222.5,4.7,6.5,CUT,'Trial short M3 insert for centre rail rear anchor')
    rails=[]
    for tag,x0,x1,nums in [('PCI',-4,25.51,(1,4,7)),('MID',131.97,149.97,(2,5,8)),('CPU',286.45,302.45,(3,6,9))]:
        c=comp('19_'+tag+'_LONGITUDINAL_BOARD_RAIL_243_84mm');rails.append(c)
        box(c,x0,0,140,x1,243.84,148,NEW,'One piece rail fits bed with 5 mm brim')
        if tag=='MID':
            box(c,136.97,6,128,144.97,237.84,140,JOIN,'Middle rail underside rib')
            poly(c,'y',6,[(136.97,134),(144.97,134),(149.97,140),(131.97,140)],212.5,JOIN,'45 degree printable rib transition')
        for num in nums:
            x,y=holes[num];circle(c,'z',148,x,y,8,10,JOIN,'Board hole '+str(num)+' unchanged')
            circle(c,'z',153.1,x,y,4.7,4.9,CUT,'Trial M3 H4.5 OD5 board insert '+str(num))
        if tag in ('PCI','CPU'):
            xx=4 if tag=='PCI' else 294
            frame=cs['16_PCI_INSET_SIDE_16_45mm'] if tag=='PCI' else cs['16_CPU_VERTICAL_SIDE_FLUSH_TO_BEAM']
            for yy in (20,225):
                circle(c,'z',140,xx,yy,3.4,8,CUT,'M3 side rail mounting clearance')
                circle(frame,'z',133.5,xx,yy,4.7,6.5,CUT,'Trial short insert for side rail anchor')
        else:
            circle(c,'z',140,134,3,3.4,8,CUT,'Centre rail front mounting clearance')
            circle(cs['12_front_PCI_SUPPORT_FRAME'],'z',133.5,134,3,4.7,6.5,CUT,'Trial short insert for middle rail front anchor')
            circle(c,'z',140,134,222.5,3.4,8,CUT,'Centre rail rear seat mounting clearance')
    # Two independently mounted fan shoes replace the 284 mm common carrier.
    for tag,x0,x1,anchors in [('GPU',12.4,152.4,(50,110)),('CPU',156.4,296.4,(200,265))]:
        c=comp('20_'+tag+'_INDEPENDENT_FAN_SHOE_140mm')
        box(c,x0,-25,148,x1,-19,160,NEW,'140 mm fan shoe')
        frame=cs['12_front_PCI_SUPPORT_FRAME'] if tag=='GPU' else cs['12_front_CPU_SUPPORT_FRAME']
        for xx in anchors:
            box(c,xx-5,-19,140,xx+5,6,154,JOIN,'Deep short arm bears on front frame')
            circle(c,'z',140,xx,2,3.4,14,CUT,'M3 shoe mounting screw clearance')
            circle(frame,'z',133.5,xx,2,4.7,6.5,CUT,'Trial short insert for fan shoe anchor')
    for o in created:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 bracket') if o.component.name.startswith('20_') else d.appearances.itemByName('V03 frame')
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
