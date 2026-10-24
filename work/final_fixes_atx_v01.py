import adsk.core,adsk.fusion,json
def run(_context: str):
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    cs={o.component.name:o.component for o in d.rootComponent.occurrences}
    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    changes=[]
    def cut(c,z,pts,depth,name,circ=False):
        pi=c.constructionPlanes.createInput();pi.setByOffset(c.xYConstructionPlane,V(str(z)+' mm'))
        sk=c.sketches.add(c.constructionPlanes.add(pi))
        if circ:
            x,y,r=pts;sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x/10,y/10,z/10)),r/20)
        else:
            for a,b in zip(pts,pts[1:]+pts[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P(a[0]/10,a[1]/10,z/10)),sk.modelToSketchSpace(P(b[0]/10,b[1]/10,z/10)))
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.participantBodies=[c.bRepBodies.item(0)]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False;changes.append(c.name+': '+name)
    for side,x in [('L',-22),('R',248)]:
        c=cs['01_Side_'+side+'_rear']
        for y in (55,121):
            if c.bRepBodies.item(0).pointContainment(P((x+2)/10,y/10,1.5))==adsk.fusion.PointContainment.PointInsidePointContainment:
                cut(c,14,[(x,y-15),(x+18,y-15),(x+18,y+15),(x,y+15)],6,'PSU seat final '+str(y))
    holes=[(10.16,288.29),(10.16,163.83),(33.02,6.35),(165.1,288.29),(165.1,163.83),(165.1,6.35),(237.49,288.29),(237.49,163.83),(237.49,6.35)]
    for x,y in holes:
        tag='CPU' if y==6.35 else 'MID' if y==163.83 else 'PCI';c=cs['03_BoardBeam_'+tag]
        if c.bRepBodies.item(0).pointContainment(P(x/10,y/10,20.79))==adsk.fusion.PointContainment.PointInsidePointContainment:
            cut(c,203.3,(x,y,4.7),4.7,'Open board insert top',True)
    c=cs['08_GPU_SlidingNut']
    if c.bRepBodies.item(0).pointContainment(P(-.7,17,32.99))==adsk.fusion.PointContainment.PointInsidePointContainment:
        cut(c,325.3,(-7,170,4.7),4.7,'Open nut top',True)
    c=cs['11_INSERT_FIT_FIRST']
    for y,top,depth in [(8,13,4.7),(22,16,8.2)]:
        for n,diam in enumerate((4.6,4.7,4.8)):
            x=297+20*n
            if c.bRepBodies.item(0).pointContainment(P(x/10,y/10,(top-.1)/10))==adsk.fusion.PointContainment.PointInsidePointContainment:
                cut(c,top-depth,(x,y,diam),depth,'Open coupon top',True)
    for tag,y in [('rear',55),('front',121)]:
        c=cs['04_PSU_Shelf_'+tag]
        for x in (17.5,160.5):cut(c,20,[(x,y-8.2),(x+2,y-8.2),(x+2,y+8.2),(x,y+8.2)],6,'Hoop travel clearance in locating stop')
    print(json.dumps({'changes':changes}))
