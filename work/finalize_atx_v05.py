"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v04-preview/ATX_Desk_v04_layout.f3d'
OUT=ROOT+'ATX-Desk-v05-preview'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
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
    for o in root.occurrences:
        if o.component.name.startswith('06_') and o.component.name.endswith('_LOW_PSU_RETAINER'):
            box(o.component,60,50,29.9,240,190,36.2,CUT,'Clearance above cradle locating stops')
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
    vis={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:
        if o.component.name.startswith('11_LOWER_FRONT_COVER_'):o.isLightBulbOn=False
    view.refresh()
    assert view.saveAsImageFile(OUT+'/Internal.png',1500,1150)
    for o in root.occurrences:o.isLightBulbOn=vis[o.component.name]
    view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v05_layout.f3d'))
    print(json.dumps(data))
