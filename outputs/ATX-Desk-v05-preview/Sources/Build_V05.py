"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
BASE=ROOT+'Sources/Base_v04.f3d'
OUT=ROOT
def run(_context: str):
    app=adsk.core.Application.get();doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    remove={'04_front_GROUND_BAR_290mm','04_rear_GROUND_BAR_290mm','05_CENTERED_PSU_CRADLE','06_PCI_PSU_RETAINER','06_CPU_PSU_RETAINER','REF_PSU_CENTER_152.4_121.92','REF_PSU_INTAKE_PLUS_X_CPU_SIDE'}
    for i in range(root.occurrences.count-1,-1,-1):
        o=root.occurrences.item(i)
        if o.component.name in remove:o.deleteMe()
    cs={o.component.name:o.component for o in root.occurrences}
    for n,c in cs.items():
        if n.startswith('01_'):
            for i in range(c.features.count-1,-1,-1):
                if c.features.item(i).name=='Recess for bottom crossbar':c.features.item(i).deleteMe()
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
    # Relocate both ground bars beyond the simplified downward-facing fan projection.
    for n,c in cs.items():
        if n.startswith('01_'):
            y=39.92 if '_front_' in n else 203.92
            box(c,-10,y-10,0,320,y+10,8,CUT,'Recess for relocated crossbar outside PSU intake')
    for tag,y in [('front',39.92),('rear',203.92)]:
        c=comp('04_'+tag+'_GROUND_BAR_290mm_FLAT_PSU')
        box(c,8.45,y-10,0,298.45,y+10,8,NEW,'290 mm ground bar clear of intake circle')
    # PSU bottom at z30. Rails only touch the outer solid chassis edges.
    c=comp('05_CENTERED_FLAT_PSU_CRADLE_OPEN_INTAKE')
    box(c,73.4,29.92,24,85.4,213.92,30,NEW,'PCI side edge-bearing runner')
    box(c,85.4,29.92,24,231.4,41.92,30,JOIN,'Front tie outside intake projection')
    box(c,219.4,41.92,24,231.4,213.92,30,JOIN,'CPU side edge-bearing runner')
    box(c,85.4,201.92,24,219.4,213.92,30,JOIN,'Rear tie outside intake projection')
    for x in (79.4,225.4):
        for y in (39.92,203.92):box(c,x-5,y-5,8,x+5,y+5,24,JOIN,'Short load foot to ground crossbar')
    for x in (75,227.8):
        for y in (74,164):box(c,x,y,30,x+2,y+6,36,JOIN,'PSU chassis edge locating stop')
    for tag,y in [('front',65.92),('rear',177.92)]:
        c=comp('06_'+tag+'_LOW_PSU_RETAINER')
        poly(c,'y',y-4,[(69.4,36.2),(77,36.2),(77,117),(227.8,117),(227.8,36.2),(235.4,36.2),(235.4,125),(69.4,125)],8,NEW,'Low removable PSU retainer')
    c=comp('REF_PSU_FLAT_CENTERED_150x140x86',True)
    box(c,77.4,51.92,30,227.4,191.92,116,NEW,'Horizontal PSU 150 wide x140 deep x86 high')
    c.opacity=.45
    fan=comp('REF_PSU_INTAKE_DOWN_MINUS_Z',True)
    circle(fan,'z',29.7,152.4,121.92,120,.3,NEW,'Downward-facing 120 mm intake marker - approximate')
    fan.opacity=.6
    exhaust=comp('REF_PSU_REAR_EXHAUST_PLUS_Y',True)
    poly(exhaust,'y',191.92,[(77.4,30),(227.4,30),(227.4,116),(77.4,116)],.3,NEW,'Rear exhaust face direction marker')
    exhaust.opacity=.4
    for o in created:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 bracket')
    for o in refcreated:
        for b in o.component.bRepBodies:b.appearance=d.appearances.itemByName('V03 PSU') if o.component.name.startswith('REF_PSU_FLAT') else d.appearances.itemByName('V03 slot')
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    # Body contact width remains 290 mm; downward intake marker is reference only.
    floor=[]
    objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_'):
            for b in o.component.bRepBodies:
                assert b.isSolid
                for vv in b.vertices:
                    if abs(vv.geometry.z)<1e-5:floor.append(vv.geometry.x*10)
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    assert abs(max(floor)-min(floor)-290)<.01,[min(floor),max(floor)]
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','PSU_bounds_mm':[[77.4,51.92,30],[227.4,191.92,116]],'PSU_center_xy_mm':[152.4,121.92],
          'PSU_intake_face':'-Z downward','PSU_exhaust_face':'+Y toward GPU display ports','nominal_floor_to_PSU_bottom_mm':30,
          'PSU_body_height_mm':86,'old_PSU_top_mm':170,'new_PSU_top_mm':116,'old_PSU_geometric_center_z_mm':95,'new_PSU_geometric_center_z_mm':73,
          'center_drop_mm':22,'ground_crossbar_y_mm':[39.92,203.92],'intake_marker_diameter_mm':120,'fan_marker_is_approximate':True,
          'ground_width_mm':290,'board_bottom_z_mm':208,'front_cover_retained':True,'timeline_features':d.timeline.count,'timeline_health':'healthy','interference_count':rr.count}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,48);cam.target=P(15,12,17);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v05_layout.f3d'))
    print(json.dumps(data))
