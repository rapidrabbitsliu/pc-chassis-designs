"""Fusion MCP build: Z390-A PRO / GM650 / GALAX compact 5060 Ti.
Dimensions in mm. V01 fit prototype; regenerate into a NEW document.
X: rear I/O to front. Y: CPU end to PCI end. Z: upwards.
"""
import adsk.core, adsk.fusion, math, os, json

OUT = 'D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/ATX-Desk-v01'
CONFIG = dict(frame_height=190, insert_bore=4.7, short_pocket=4.7,
              long_pocket=8.2, board_gap=10, frame_width=288,
              psu_x=20, psu_y=45, psu_z=20, gpu_slot_y=155)
HOLES = {'A':(10.16,288.29),'C':(10.16,163.83),'F':(33.02,6.35),
         'G':(165.10,288.29),'H':(165.10,163.83),'J':(165.10,6.35),
         'K':(237.49,288.29),'L':(237.49,163.83),'M':(237.49,6.35)}

def run(_context: str):
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
    printable=[]; refs=[]; meta=[]
    os.makedirs(OUT,exist_ok=True)
    for name,value in CONFIG.items():
        d.userParameters.add(name,V(str(value)+' mm'),'mm','Regeneration configuration; fixed sketch positions also require script regeneration')
    def comp(tag,orientation='xy',angle=0,reference=False):
        occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c=occ.component;c.name=tag
        (refs if reference else printable).append(occ)
        if not reference:meta.append(dict(part=tag,orientation=orientation,angle_deg=angle))
        return c
    def plane(c,axis,offset):
        basis={'z':c.xYConstructionPlane,'x':c.yZConstructionPlane,'y':c.xZConstructionPlane}[axis]
        # XZ normal is -Y.
        val=-offset if axis=='y' else offset
        inp=c.constructionPlanes.createInput();inp.setByOffset(basis,V(str(val)+' mm'))
        return c.constructionPlanes.add(inp)
    def point(axis,pos,u,v):
        return P(*({'z':(u/10,v/10,pos/10),'x':(pos/10,u/10,v/10),'y':(u/10,pos/10,v/10)}[axis]))
    def profile(c,axis,pos,pts,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name
        for a,b in zip(pts,pts[1:]+pts[:1]):
            line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(point(axis,pos,*a)),sk.modelToSketchSpace(point(axis,pos,*b)))
            line.isFixed=True
        assert sk.profiles.count==1,(name,sk.profiles.count)
        return sk
    def extrude(c,sk,axis,depth,op,name):
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        if op==CUT:inp.participantBodies=[c.bRepBodies.item(i) for i in range(c.bRepBodies.count)]
        direction=adsk.fusion.ExtentDirections.PositiveExtentDirection
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),direction)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False
        return f
    def poly(c,axis,pos,pts,depth,op,name):
        return extrude(c,profile(c,axis,pos,pts,name+' sketch'),axis,depth,op,name)
    def box(c,x0,y0,z0,x1,y1,z1,op,name):
        return poly(c,'z',z0,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z1-z0,op,name)
    def circle(c,axis,pos,u,v,diam,depth,op,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name+' sketch'
        q=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(point(axis,pos,u,v)),diam/20);q.isFixed=True
        return extrude(c,sk,axis,depth,op,name)
    def bore(c,axis,pos,u,v,diam,depth,name):return circle(c,axis,pos,u,v,diam,depth,CUT,name)
    def slot(c,axis,pos,u,v0,v1,diam,depth,name):
        # Two round ends and their connecting rectangle. All three cuts overlap.
        bore(c,axis,pos,u,v0,diam,depth,name+' end 1')
        bore(c,axis,pos,u,v1,diam,depth,name+' end 2')
        poly(c,axis,pos,[(u-diam/2,v0),(u+diam/2,v0),(u+diam/2,v1),(u-diam/2,v1)],depth,CUT,name+' bridge')
    def zinsert(c,x,y,top,depth=4.7,diam=None):
        bore(c,'z',top-depth,x,y,diam or CONFIG['insert_bore'],depth,'M3 heat insert pocket')
    def xinsert(c,face,y,z,sign=1,depth=8.2):
        start=face if sign>0 else face-depth
        bore(c,'x',start,y,z,CONFIG['insert_bore'],depth,'M3 long insert side pocket')
    # Four flat-print triangulated side panels. 0.4 mm butt gap is intentional.
    panels={}
    for side,x0 in [('L',-22),('R',248)]:
        for section,a,b in [('rear',-10,146),('front',146.4,310)]:
            c=comp('01_Side_'+side+'_'+section,'yz')
            box(c,x0,a,0,x0+18,b,190,NEW,'18 mm triangulated side panel')
            poly(c,'x',x0,[(a+14,36),(a+14,176),(b-36,176)],18,CUT,'Upper lightening window')
            poly(c,'x',x0,[(a+36,16),(b-14,16),(b-14,154)],18,CUT,'Lower lightening window')
            for yy in (6.35,163.83,288.29):
                if a<yy<b:zinsert(c,x0+9,yy,190)
            if section=='rear':
                for yy in (55,121):
                    box(c,x0,yy-15,14,x0+18,yy+15,20,CUT,'PSU shelf recessed end seat')
                    zinsert(c,x0+9,yy,14)
            face=x0 if side=='L' else x0+18
            sy=136 if section=='rear' else 156
            for zz in (25,35,167.5,177.5):xinsert(c,face,sy,zz,1 if side=='L' else -1)
            panels[side,section]=c
    # Splice plates across each side-panel seam, two separated elevations.
    for side,x in [('L',-26),('R',266)]:
        for tag,z in [('low',16),('high',158.5)]:
            c=comp('02_Splice_'+side+'_'+tag,'yz')
            poly(c,'x',x,[(121,z+3),(124,z),(168,z),(171,z+3),(171,z+25),(168,z+28),(124,z+28),(121,z+25)],4,NEW,'Chamfered splice plate')
            for yy in (136,156):
                for zz in (z+9,z+19):bore(c,'x',x,yy,zz,3.4,4,'M3x12 splice screw clearance')
    # Three ribbed motherboard crossmembers. Each fits a 256 bed at 45 degrees.
    beams={}
    for tag,y in [('CPU',6.35),('MID',163.83),('PCI',288.29)]:
        c=comp('03_BoardBeam_'+tag,'xy',45)
        box(c,-22,y-10,190,266,y+10,198,NEW,'8 mm top flange')
        box(c,-4,y-4,178,248,y+4,190,JOIN,'12 mm underside stiffening rib')
        poly(c,'x',-4,[(y-4,184),(y+4,184),(y+10,190),(y-10,190)],252,JOIN,'45 degree flange support transitions')
        for xx in (-13,257):bore(c,'z',190,xx,y,3.4,8,'M3x12 to side frame')
        for label,(xx,yy) in HOLES.items():
            if abs(yy-y)<.01:
                circle(c,'z',198,xx,yy,8,10,JOIN,'10 mm motherboard standoff '+label)
                zinsert(c,xx,yy,208,4.9)
                bore(c,'z',200,xx,yy,3.2,3.5,'Screw tip relief '+label)
        if tag=='MID':
            for xx in (-13,257):
                for yy in (y-6,y+6):zinsert(c,xx,yy,198)
        beams[tag]=c
    # Power-supply support rails and independent removable retention hoops.
    # PSU actual envelope: X20..160, Y45..131, Z20..170. Fan faces +Y.
    for tag,y in [('rear',55),('front',121)]:
        c=comp('04_PSU_Shelf_'+tag,'xy',45)
        box(c,-22,y-15,14,266,y+15,20,NEW,'PSU bottom support rail')
        for xx in (-13,257):bore(c,'z',14,xx,y,3.4,6,'M3x10 shelf to frame')
        for xx in (14,166):slot(c,'z',14,xx,y-4,y+4,3.4,6,'Hoop position adjustment')
        for xx in (17.5,160.5):
            box(c,xx,y-15,20,xx+2,y-8.2,26,JOIN,'PSU locating stop first half')
            box(c,xx,y+8.2,20,xx+2,y+15,26,JOIN,'PSU locating stop second half')
        if tag=='rear':box(c,19.5,42.5,20,160.5,44.5,26,JOIN,'PSU side locating lip')
        else:box(c,19.5,131.5,20,160.5,133.5,26,JOIN,'PSU fan-side lower-edge lip')
        h=comp('05_PSU_Hoop_'+tag,'xz')
        poly(h,'y',y-4,[(10,20),(18,20),(18,171),(162,171),(162,20),(170,20),(170,179),(10,179)],8,NEW,'Removable PSU retaining hoop')
        for xx in (14,166):bore(h,'z',20,xx,y,4.7,8.2,'M3 long insert from underside')
    # Rear GPU bracket: adjustable in height, long Y slot for the metal bracket screw.
    c=comp('06_GPU_RearTower','yz')
    box(c,-38,130,198,-5,226,204,NEW,'GPU tower foot')
    box(c,-38,130,204,-30,226,350,JOIN,'GPU rear frame')
    poly(c,'x',-38,[(144,214),(146,212),(210,212),(212,214),(212,308),(210,310),(146,310),(144,308)],8,CUT,'Open display connector access')
    for yy in (157.83,169.83):bore(c,'z',198,-13,yy,3.4,6,'M3x10 tower foot screw')
    bore(c,'z',198,-13,163.83,7,3,'Access clearance above crossbeam screw head')
    for yy in (136,220):slot(c,'x',-38,yy,316,344,3.4,8,'GPU bracket height slot')
    s=comp('07_GPU_RearSlider','xz')
    box(s,-30,130,316,-20,226,346,NEW,'GPU sliding carrier')
    box(s,-20,130,330,-1,226,336,JOIN,'GPU metal bracket screw ledge')
    for yy in (136,220):xinsert(s,-30,yy,332,1)
    slot(s,'z',330,-7,142,214,3.4,6,'GPU mounting screw Y adjustment')
    # Keep the center clear for display plugs, including the carrier lower portion.
    box(s,-30,145,316,-20,211,329,CUT,'Carrier display plug opening')
    p=comp('08_GPU_SlidingNut','xy')
    box(p,-12,165,324,-2,175,330,NEW,'M3 captive sliding insert block')
    zinsert(p,-7,170,330,4.9)
    # GPU tail support approaches from beyond the front motherboard edge.
    c=comp('09_GPU_TailTower','yz')
    box(c,248,153.83,198,266,212,204,NEW,'Tail support foot outside motherboard')
    box(c,250,176,204,258,212,250,JOIN,'Tail support external upright')
    for yy in (157.83,169.83):bore(c,'z',198,257,yy,3.4,6,'M3x10 tail support foot screw')
    bore(c,'z',198,257,163.83,7,3,'Crossbeam screw head clearance')
    for yy in (184,204):slot(c,'x',250,yy,214,238,3.4,8,'Tail pad height slot')
    s=comp('10_GPU_TailSlider','yz')
    box(s,240,180,212,250,208,240,NEW,'Tail pad sliding upright')
    box(s,210,180,213,240,208,219,JOIN,'Tail support cantilever above motherboard')
    for yy in (184,204):xinsert(s,250,yy,226,-1)
    # Small fit coupon: left-to-right bores 4.6,4.7,4.8; near row short, far row long.
    c=comp('11_INSERT_FIT_FIRST','xy')
    box(c,285,0,0,349,30,3,NEW,'Insert fit coupon base')
    for row,y,top,depth in [('short',8,13,4.9),('long',22,16,8.4)]:
        for n,diam in enumerate((4.6,4.7,4.8)):
            xx=297+20*n
            circle(c,'z',3,xx,y,8,top-3,JOIN,row+' test boss '+str(diam))
            zinsert(c,xx,y,top,depth,diam)
    # Reference bodies are deliberately excluded from all print exports.
    b=comp('REF_MSI_Z390_A_PRO_304.8x243.84','xy',reference=True)
    box(b,0,0,208,243.84,304.8,209.6,NEW,'Motherboard envelope ONLY')
    for label,(xx,yy) in HOLES.items():bore(b,'z',208,xx,yy,3.96,1.6,'ATX '+label)
    b.opacity=.22
    ps=comp('REF_ENERMAX_ERV650G_AHG_140x86x150_FAN_PLUS_Y','xy',reference=True)
    box(ps,20,45,20,160,131,170,NEW,'PSU envelope ONLY')
    ps.opacity=.32
    gp=comp('REF_GPU_BODY_223x40x114_APPROX_SLOT','xy',reference=True)
    box(gp,0,155,219,223,195,333,NEW,'GPU body envelope ONLY - slot offset approximate')
    gp.opacity=.25
    # Add a thin reference on the fan face so orientation is visible.
    fan=comp('REF_PSU_FAN_FACE_PLUS_Y','xy',reference=True)
    circle(fan,'y',131,90,95,120,.3,NEW,'PSU intake direction marker ONLY')
    fan.opacity=.25
    # Reference graphics are hidden during manufacturing and interference validation.
    for occ in refs:occ.isLightBulbOn=False
    result=[]
    for occ,entry in zip(printable,meta):
        c=occ.component
        assert c.bRepBodies.count==1,(c.name,c.bRepBodies.count)
        body=c.bRepBodies.item(0);assert body.isSolid,c.name
        bb=body.boundingBox
        entry.update(volume_mm3=body.volume*1000,bounds_mm=[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in ('x','y','z')])
        opt=d.exportManager.createSTLExportOptions(c,os.path.join(OUT,'raw_'+c.name+'.stl'))
        opt.sendToPrintUtility=False
        opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert d.exportManager.execute(opt),c.name
        result.append(entry)
    unhealthy=[]
    for i in range(d.timeline.count):
        t=d.timeline.item(i)
        if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:unhealthy.append([t.name,t.errorOrWarningMessage])
    assert not unhealthy,unhealthy
    with open(os.path.join(OUT,'geometry.json'),'w',encoding='utf-8') as f:json.dump({'config_mm':CONFIG,'holes_mm':HOLES,'parts':result,'timeline_features':d.timeline.count,'timeline_health':'healthy'},f,indent=2)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(os.path.join(OUT,'ATX_Desk_v01.f3d')))
    # Show the fitted assembly, excluding the fit coupon.
    printable[-1].isLightBulbOn=False
    for occ in refs:occ.isLightBulbOn=True
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False
    cam.eye=P(55,65,50);cam.target=P(10,14,17);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True
    view.camera=cam;view.refresh()
    print(json.dumps({'parts':len(result),'timeline_features':d.timeline.count,'healthy':True,'output':OUT,'holes_mm':HOLES}))
