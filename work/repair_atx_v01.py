import adsk.core, adsk.fusion, os, json
OUT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/ATX-Desk-v01'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    comps={o.component.name:o.component for o in root.occurrences}
    def cut(c,z,pts,depth,name,circle=False):
        pi=c.constructionPlanes.createInput();pi.setByOffset(c.xYConstructionPlane,V(str(z)+' mm'))
        sk=c.sketches.add(c.constructionPlanes.add(pi));sk.name=name+' sketch'
        if circle:
            x,y,r=pts;q=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(P(x/10,y/10,z/10)),r/20);q.isFixed=True
        else:
            for a,b in zip(pts,pts[1:]+pts[:1]):
                q=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P(a[0]/10,a[1]/10,z/10)),sk.modelToSketchSpace(P(b[0]/10,b[1]/10,z/10)));q.isFixed=True
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),CUT)
        inp.participantBodies=[c.bRepBodies.item(0)]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False
    for side,x in [('L',-22),('R',248)]:
        c=comps['01_Side_'+side+'_rear']
        for y in (55,121):
            if side=='L' and y==55:continue
            cut(c,14,[(x,y-15),(x+18,y-15),(x+18,y+15),(x,y+15)],6,'PSU shelf recessed seat')
    holes={'A':(10.16,288.29),'C':(10.16,163.83),'F':(33.02,6.35),'G':(165.1,288.29),'H':(165.1,163.83),'J':(165.1,6.35),'K':(237.49,288.29),'L':(237.49,163.83),'M':(237.49,6.35)}
    for label,(x,y) in holes.items():
        tag='CPU' if y==6.35 else 'MID' if y==163.83 else 'PCI'
        cut(comps['03_BoardBeam_'+tag],203.3,(x,y,4.7),4.7,'Open insert pocket '+label,True)
        cut(comps['03_BoardBeam_'+tag],200,(x,y,3.2),3.5,'Connect tip relief '+label,True)
    cut(comps['08_GPU_SlidingNut'],325.3,(-7,170,4.7),4.7,'Open sliding nut pocket',True)
    for y,top,depth in [(8,13,4.7),(22,16,8.2)]:
        for n,diam in enumerate((4.6,4.7,4.8)):cut(comps['11_INSERT_FIT_FIRST'],top-depth,(297+20*n,y,diam),depth,'Open coupon pocket',True)
    os.makedirs(OUT,exist_ok=True)
    parts=[]
    for occ in root.occurrences:
        c=occ.component
        if c.name.startswith('REF_'):occ.isLightBulbOn=False;continue
        assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid,c.name
        b=c.bRepBodies.item(0);bb=b.boundingBox
        mode='xy';angle=0
        if c.name.startswith(('01_','02_','06_')):mode='yz'
        if c.name.startswith(('05_','07_')) or c.name=='10_GPU_TailSlider':mode='xz'
        if c.name.startswith(('03_','04_')):angle=45
        parts.append(dict(part=c.name,orientation=mode,angle_deg=angle,volume_mm3=b.volume*1000,bounds_mm=[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in ('x','y','z')]))
    unhealthy=[]
    for i in range(d.timeline.count):
        t=d.timeline.item(i)
        if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:unhealthy.append([t.name,t.errorOrWarningMessage])
    assert not unhealthy,unhealthy
    with open(os.path.join(OUT,'geometry.json'),'w',encoding='utf-8') as f:json.dump({'holes_mm':holes,'parts':parts,'timeline_features':d.timeline.count,'timeline_health':'healthy'},f,indent=2)
    print(json.dumps({'parts':len(parts),'healthy':True,'timeline':d.timeline.count,'output':OUT}))
