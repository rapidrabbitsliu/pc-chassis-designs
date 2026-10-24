import adsk.core,adsk.fusion,json
def run(_context: str):
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    cs={o.component.name:o.component for o in d.rootComponent.occurrences}
    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    def cut(c,x0,y0,z0,x1,y1,z1,name,circ=False):
        pi=c.constructionPlanes.createInput();pi.setByOffset(c.xYConstructionPlane,V(str(z0)+' mm'))
        sk=c.sketches.add(c.constructionPlanes.add(pi))
        if circ:sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x0/10,y0/10,z0/10)),x1/20)
        else:
            pts=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
            for a,b in zip(pts,pts[1:]+pts[:1]):sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P(a[0]/10,a[1]/10,z0/10)),sk.modelToSketchSpace(P(b[0]/10,b[1]/10,z0/10)))
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation);inp.participantBodies=[c.bRepBodies.item(0)]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(z1-z0)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        c.features.extrudeFeatures.add(inp).name=name;sk.isVisible=False
    for tag,y in [('FRONT',6.35),('MID',78.74),('REAR',233.68)]:
        c=cs['03_'+tag+'_MOTHERBOARD_BEAM']
        for x0,x1 in [(12,14),(290.8,292.8)]:cut(c,x0,y-9,178,x1,y+9,190,'Rib clearance from sloped side frame')
    for side in ('PCI','CPU'):cut(cs['06_'+side+'_PSU_RETAINER'],100,40,178,205,203,179,'PSU retainer clearance below board rib')
    cut(cs['07_GPU_REAR_TOWER'],140.97,233.68,198,9.5,0,206,'Hole 2 standoff clearance',True)
    print('Added rib, PSU retainer and motherboard-standoff clearances.')
