"""Style 1 V14: physical-fit correction for P12 tower and P13 ear ledge.
Run through Fusion MCP. Import a copy of V13, never overwrite the baseline.
"""
import adsk.core,adsk.fusion,json,os,math
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/'
OUT=ROOT+'outputs/ATX-Desk-v14'

def run(_context: str):
    app=adsk.core.Application.get()
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(ROOT+'outputs/ATX-Desk-v13/ATX_Desk_v13_one_piece.f3d'))
    assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    cs={o.component.name:o.component for o in root.occurrences}
    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    CUT=adsk.fusion.FeatureOperations.CutFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
    def plane(c,axis,pos):
        inp=c.constructionPlanes.createInput()
        inp.setByOffset({'y':c.xZConstructionPlane,'z':c.xYConstructionPlane}[axis],V(str(-pos if axis=='y' else pos)+' mm'))
        return c.constructionPlanes.add(inp)
    def point(axis,pos,u,v):return P(*((u/10,v/10,pos/10) if axis=='z' else (u/10,pos/10,v/10)))
    def ext(c,sk,depth,op,name):
        assert sk.profiles.count==1,(name,sk.profiles.count)
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        if op==CUT:inp.participantBodies=[b for b in c.bRepBodies]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False
        return f
    def poly(c,axis,pos,pts,depth,op,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name+' profile'
        for a,b in zip(pts,pts[1:]+pts[:1]):
            line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(point(axis,pos,*a)),sk.modelToSketchSpace(point(axis,pos,*b)));line.isFixed=True
        return ext(c,sk,depth,op,name)
    def circle(c,axis,pos,u,v,diam,depth,op,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name+' profile'
        curve=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(point(axis,pos,u,v)),diam/20);curve.isFixed=True
        return ext(c,sk,depth,op,name)
    def box(c,x0,y0,z0,x1,y1,z1,op,name):return poly(c,'z',z0,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z1-z0,op,name)
    def slot(c,x,z0,z1,width):
        for z in (z0,z1):circle(c,'y',263,x,z,width,24,CUT,'V14 accessible mushroom head channel end')
        box(c,x-width/2,263,z0,x+width/2,287,z1,CUT,'V14 accessible mushroom head channel web')
    tower=cs['07_GPU_REINFORCED_REAR_TOWER'];upper=cs['08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE']
    manager=adsk.fusion.TemporaryBRepManager.get()
    def swept_gauge(body,diameter,zs):
        checks=[]
        for x in (80,164):
            for z0,z1 in ((157,165),(262,292)):
                tool=manager.createCylinderOrCone(P(x/10,26.301,z0/10),diameter/20,P(x/10,30,z0/10),diameter/20)
                end=manager.createCylinderOrCone(P(x/10,26.301,z1/10),diameter/20,P(x/10,30,z1/10),diameter/20)
                bounds=adsk.core.OrientedBoundingBox3D.create(P(x/10,(26.301+30)/2,(z0+z1)/20),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),diameter/10,30-26.301,(z1-z0)/10)
                middle=manager.createBox(bounds)
                assert manager.booleanOperation(tool,middle,adsk.fusion.BooleanTypes.UnionBooleanType)
                assert manager.booleanOperation(tool,end,adsk.fusion.BooleanTypes.UnionBooleanType)
                target=manager.copy(body)
                assert manager.booleanOperation(target,tool,adsk.fusion.BooleanTypes.IntersectionBooleanType)
                checks.append({'x_mm':x,'z_range_mm':[z0,z1],'continuous_sweep':True,'interference_mm3':target.volume*1000})
        return checks
    tests_z=[157+i for i in range(9)]+[262+i for i in range(31)]
    before=swept_gauge(tower.bRepBodies.item(0),7.5,tests_z)
    # Width compensation from user: V13 CAD 6.6 printed about 6; target >=7.5.
    # Retain the 260..263 mm, 3 mm shank-bearing web for M3x6 engagement.
    for x in (80,164):
        slot(tower,x,262,292,8.2)
        slot(tower,x,157,165,8.2)
    for x in (80,140,158):circle(tower,'z',143,x,248.5,8.2,5.01,CUT,'V14 8.2 mm tower base mushroom head well')
    after=swept_gauge(tower.bRepBodies.item(0),7.5,tests_z)
    assert max(c['interference_mm3'] for c in after)<.0001,after
    # Remove the old two pockets cleanly, then move their centres -Y by 3 mm.
    removed=0
    for i in range(upper.features.count-1,-1,-1):
        f=upper.features.item(i)
        if f.name.startswith('Trial M3 short insert for graphics card ear'):f.deleteMe();removed+=1
    assert removed==2,removed
    box(upper,84,241.84,272,154,244.85,282,JOIN,'V14 extend ear platform 3 mm towards GPU')
    for x in (100,120):circle(upper,'z',275.5,x,246.5,4.7,6.5,CUT,'V14 ear insert relocated 3 mm towards GPU')
    d.userParameters.add('v14_gpu_head_channel',V('8.2 mm'),'mm','Nominal; compensate observed 0.6 mm undersize; physical retest required')
    d.userParameters.add('v14_gpu_ear_offset',V('3 mm'),'mm','Upper holes and platform front extended towards minus Y')
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad,bad
    os.makedirs(OUT+'/Raw_STL',exist_ok=True);os.makedirs(OUT+'/Manual_Meshes',exist_ok=True)
    parts=[];assembly=[];refs=[]
    for o in root.occurrences:
        c=o.component;n=c.name
        if not n.startswith('REF_'):
            assert c.bRepBodies.count==1
            b=c.bRepBodies.item(0);assert b.isSolid and b.lumps.count==1
            bb=b.preciseBoundingBox
            parts.append({'name':n,'native_size_mm':[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in 'xyz'],'volume_mm3':b.volume*1000})
            opts=d.exportManager.createSTLExportOptions(b,OUT+'/Raw_STL/'+n+'.stl');opts.isBinaryFormat=True;assert d.exportManager.execute(opts)
            assembly.append(o)
        elif n in ('REF_GPU_FANS_TO_MINUS_X','REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):refs.append(o)
    assert len(parts)==17
    def interferences(objects):
        obs=adsk.core.ObjectCollection.create()
        for o in objects:obs.add(o)
        inp=d.createInterferenceInput(obs);inp.areCoincidentFacesIncluded=False;result=d.analyzeInterference(inp)
        return [{'one':result.item(i).entityOne.parentComponent.name,'two':result.item(i).entityTwo.parentComponent.name,'volume_mm3':result.item(i).interferenceBody.volume*1000} for i in range(result.count)]
    structural=interferences(assembly);assert not structural,structural
    hardware=interferences(assembly+refs)
    archive=OUT+'/ATX_Desk_v14_gpu_fit.f3d'
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(archive))
    data={'style':1,'version':'V14','parts':parts,'replacements':['07_GPU_REINFORCED_REAR_TOWER','08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE'],
          'nominal_channel_mm':8.2,'v13_printed_channel_report_mm':6,'print_target_clear_mm':7.5,'wall_web_retained_mm':3,
          'ear_offset_y_mm':-3,'new_ear_centres_mm':[[100,246.5,282],[120,246.5,282]],'platform_front_y_mm':241.84,'platform_extension_mm':3,
          'nut_OD5_front_edge_material_mm':2.16,'before_head_access':before,'after_head_access':after,'gauge_diameter_mm':7.5,
          'structural_interferences':structural,'reference_envelope_interferences':hardware,'timeline_health':'healthy','physical_retest_required':True,
          'note':'GPU reference is a simplified rectangular envelope; report any overlap explicitly, do not erase it to claim fit.'}
    open(OUT+'/parts.json','w').write(json.dumps(parts,indent=2))
    open(OUT+'/verification.json','w').write(json.dumps(data,indent=2))
    vis={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:o.isLightBulbOn=o.component.name.startswith(('07_','08_'))
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(30,55,28);cam.target=P(12.2,26,22);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/GPU_Bracket_Rear.png',1500,1100)
    cam=view.camera;cam.eye=P(29,2,32);cam.target=P(12.2,25.5,22);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/GPU_Bracket_Front.png',1500,1100)
    for o in root.occurrences:o.isLightBulbOn=vis[o.component.name]
    cam=view.camera;cam.eye=P(48,48,36);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Assembly.png',1500,1150)
    print(json.dumps({'archive':archive,'head_path_checks':len(after),'max_after_collision_mm3':max(c['interference_mm3'] for c in after),'before_blocked_count':sum(c['interference_mm3']>.0001 for c in before),'structural_interferences':structural,'hardware_interferences':hardware,'parts':len(parts)}))
