"""Single-side V05 bracket and anti-lift key prototype. UNRATED.
Units mm. Edit config then regenerate in a NEW Fusion document.
"""
import adsk.core, adsk.fusion, os, json, math
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(_context):
    app=adsk.core.Application.get()
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d=adsk.fusion.Design.cast(app.activeProduct)
    d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    root=d.rootComponent
    V=adsk.core.ValueInput.createByString
    P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    def comp(name):
        obj=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
        obj.name=name;return obj
    def plane(obj,z):
        inp=obj.constructionPlanes.createInput();inp.setByOffset(obj.xYConstructionPlane,V(str(z)+' mm'))
        return obj.constructionPlanes.add(inp)
    def poly(obj,pts,z,length,op,name):
        s=obj.sketches.add(plane(obj,z));s.name=name+' profile'
        for a,b in zip(pts,pts[1:]+pts[:1]):
            q=s.sketchCurves.sketchLines.addByTwoPoints(P(a[0]/10,a[1]/10,0),P(b[0]/10,b[1]/10,0));q.isFixed=True
        assert s.profiles.count==1
        inp=obj.features.extrudeFeatures.createInput(s.profiles.item(0),op)
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(length)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=obj.features.extrudeFeatures.add(inp);f.name=name;s.isVisible=False
        return f
    def rect(obj,x0,y0,x1,y1,z,length,op,name):
        return poly(obj,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z,length,op,name)
    def xshape(obj,x,points,depth,op,name):
        i=obj.constructionPlanes.createInput();i.setByOffset(obj.yZConstructionPlane,V(str(x)+' mm'))
        sk=obj.sketches.add(obj.constructionPlanes.add(i))
        for a,b in zip(points,points[1:]+points[:1]):
            pa=sk.modelToSketchSpace(P(x/10,a[0]/10,a[1]/10));pb=sk.modelToSketchSpace(P(x/10,b[0]/10,b[1]/10))
            q=sk.sketchCurves.sketchLines.addByTwoPoints(pa,pb);q.isFixed=True
        inp=obj.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=obj.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False
    def xhole(obj,x,y,z,diam,depth,name):
        i=obj.constructionPlanes.createInput();i.setByOffset(obj.yZConstructionPlane,V(str(x)+' mm'))
        sk=obj.sketches.add(obj.constructionPlanes.add(i))
        circle=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x/10,y/10,z/10)),diam/20);circle.isFixed=True
        inp=obj.features.extrudeFeatures.createInput(sk.profiles.item(0),CUT)
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        obj.features.extrudeFeatures.add(inp).name=name;sk.isVisible=False
    main=comp('Single bracket V05 - THROAT 4.0 - UNRATED')
    rect(main,-6,-108,0,6,-16,32,NEW,'Backplate 6 mm')
    rect(main,-98,0,-6,6,-16,32,JOIN,'Shelf 92 mm')
    poly(main,[(-6,-100),(-6,0),(-96,0)],-16,8,JOIN,'Side flush triangular web 8 mm')
    poly(main,[(-14,-72),(-14,-14),(-18,-10),(-69,-10),(-71,-12),(-16,-74)],-16,8,CUT,'Web lightening window')
    rect(main,-100,0,-96,12,-16,32,JOIN,'Front stop 6 mm above shelf')
    # Upper slot centers y=-16, lower centers=-96. Same-column gap80.
    for z in (-10,10):
        y=-23.5
        poly(main,[(0,y),(4,y),(4,y-3),(7,y-3),(7,y+3.5),(0,y+3.5)],z-1.9,3.8,JOIN,'Upper hook throat 4.0')
        rect(main,0,-103.5,4,-100,z-1.9,3.8,JOIN,'Lower locating tab')
    # Separate key inserted from the front AFTER lowering bracket onto slots.
    rect(main,-6,-14,0,-9.4,8.1,3.8,CUT,'Key guide opening')
    xhole(main,-6,-5,10,3.4,6,'M3 screw clearance')
    radius=5.7/math.sqrt(3)
    hexagon=[(-5+radius*math.cos(k*math.pi/3),10+radius*math.sin(k*math.pi/3)) for k in range(6)]
    xshape(main,-2.6,hexagon,2.6,CUT,'Rear captive M3 nut pocket AF5.7 depth2.6')
    key=comp('Removable anti-lift key - M3 retained - TEST FIT')
    rect(key,-8,-15,-6,-2,5.5,9,NEW,'Key flange 2 mm')
    rect(key,-6,-13.8,3.5,-9.6,8.3,3.4,JOIN,'Key tongue')
    xhole(key,-8,-5,10,3.4,2,'M3 key retainer clearance')
    # PSU only an envelope. X negative points toward room; Y up; Z width.
    psu=comp('PSU reference only - NOT FOR PRINT')
    rect(psu,-94,6,-8,156,-70,140,NEW,'PSU 140 x 150 x 86')
    psu.opacity=.22
    mgr=d.exportManager;os.makedirs(OUT,exist_ok=True)
    result=[]
    for obj,tag in [(main,'Bracket'),(key,'AntiLiftKey')]:
        assert obj.bRepBodies.count==1
        body=obj.bRepBodies.item(0);assert body.isSolid
        opt=mgr.createSTLExportOptions(obj,os.path.join(OUT,'raw_'+tag+'.stl'));opt.sendToPrintUtility=False;assert mgr.execute(opt)
        box=body.boundingBox
        result.append({'part':tag,'volume_mm3':body.volume*1000,'bounds_mm':[(getattr(box.maxPoint,k)-getattr(box.minPoint,k))*10 for k in ('x','y','z')],'solid':True})
    for i in range(d.timeline.count):
        item=d.timeline.item(i)
        assert item.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,(item.name,item.errorOrWarningMessage)
    assert mgr.execute(mgr.createFusionArchiveExportOptions(os.path.join(OUT,'Single_Bracket_v05.f3d')))
    psu.isBodiesFolderLightBulbOn=False
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False
    cam.eye=P(-18,8,14);cam.target=P(-3,-4,0);cam.upVector=adsk.core.Vector3D.create(0,1,0);cam.isFitView=True
    view.camera=cam;view.refresh()
    with open(os.path.join(OUT,'verification.json'),'w') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
