"""V13: continuous rear beam, continuous fan rail, defined M3x6 assembly joints."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/电脑上洞洞板/outputs/'
OUT=ROOT+'ATX-Desk-v13'
BASE=ROOT+'ATX-Desk-v12-print-review/ATX_Desk_v12_print_review.f3d'

def run(_context: str):
    app=adsk.core.Application.get()
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(BASE));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
    CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    for i in range(root.occurrences.count-1,-1,-1):
        if root.occurrences.item(i).component.name.startswith(('18_','20_')):root.occurrences.item(i).deleteMe()
    cs={o.component.name:o.component for o in root.occurrences}
    def comp(name):
        o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name
        cs[name]=o.component;return o.component
    def plane(c,axis,pos):
        inp=c.constructionPlanes.createInput();inp.setByOffset({'x':c.yZConstructionPlane,'y':c.xZConstructionPlane,'z':c.xYConstructionPlane}[axis],V(str(-pos if axis=='y' else pos)+' mm'))
        return c.constructionPlanes.add(inp)
    def point(axis,pos,u,v):return P(*{'z':(u/10,v/10,pos/10),'x':(pos/10,u/10,v/10),'y':(u/10,pos/10,v/10)}[axis])
    def extrude(c,sk,depth,op,name):
        assert sk.profiles.count==1,(name,sk.profiles.count)
        inp=c.features.extrudeFeatures.createInput(sk.profiles.item(0),op)
        if op==CUT:inp.participantBodies=[b for b in c.bRepBodies]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(str(depth)+' mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
        f=c.features.extrudeFeatures.add(inp);f.name=name;sk.isVisible=False;return f
    def poly(c,axis,pos,pts,depth,op,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name+' profile'
        for a,b in zip(pts,pts[1:]+pts[:1]):
            line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(point(axis,pos,*a)),sk.modelToSketchSpace(point(axis,pos,*b)));line.isFixed=True
        return extrude(c,sk,depth,op,name)
    def box(c,x0,y0,z0,x1,y1,z1,op,name):return poly(c,'z',z0,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z1-z0,op,name)
    def circle(c,axis,pos,u,v,diam,depth,op,name):
        sk=c.sketches.add(plane(c,axis,pos));sk.name=name+' profile'
        curve=sk.sketchCurves.sketchCircles.addByCenterRadius(sk.modelToSketchSpace(point(axis,pos,u,v)),diam/20);curve.isFixed=True
        return extrude(c,sk,depth,op,name)
    def slot(c,pos,x,z0,z1,width,depth,name):
        circle(c,'y',pos,x,z0,width,depth,CUT,name+' end A')
        circle(c,'y',pos,x,z1,width,depth,CUT,name+' end B')
        box(c,x-width/2,pos,z0,x+width/2,pos+depth,z1,CUT,name+' middle')
    # A single full-depth extrusion replaces the complementary lap tongues.
    rear=comp('18_ONE_PIECE_REAR_LOAD_BEAM_304_45mm')
    xl=28.45-16.45*128/140
    poly(rear,'y',242.68,[(xl,128),(286.45,128),(286.45,140),(12,140)],23.16,NEW,'Continuous full depth rear beam without centre joint')
    poly(rear,'y',242.68,[(102.4,128),(122.4,120),(182.4,120),(202.4,128)],23.16,JOIN,'Continuous central load spreading rib')
    box(rear,-2,253.84,124,26,261.84,140,JOIN,'Integral PCI end fastening ear')
    box(rear,270,253.84,124,302.45,261.84,140,JOIN,'Integral CPU end fastening ear')
    box(rear,130,218.5,128,152.4,242.68,140,JOIN,'Integral seat for middle motherboard rail')
    box(rear,136.77,218.5,127.9,145.17,237.84,140.1,CUT,'Middle rail rib clearance with 0.2 mm each side')
    circle(rear,'z',133.5,134,222.5,4.7,6.5,CUT,'M3 H4.5 insert for middle rail')
    for x in (80,140,158):circle(rear,'z',133.5,x,248.5,4.7,6.5,CUT,'M3 H4.5 insert for GPU tower')
    for x in (96,116):box(rear,x-7,246.3,119.9,x+7,248.7,140.1,CUT,'GPU lower metal tab exit')
    for x in (4,294):
        circle(rear,'y',253.84,x,132,3.4,8,CUT,'Rear end screw clearance')
        circle(rear,'y',256.84,x,132,6.6,5.01,CUT,'Rear end screw head well leaving 3 mm web')
    # Continuous fan shoe: 284 mm x 31 mm fits diagonally while preserving four seats.
    fan=comp('20_ONE_PIECE_DUAL_140_FAN_RAIL_284mm')
    box(fan,12.4,-25,148,296.4,-19,160,NEW,'One piece dual fan lower mounting rail')
    for xx in (50,110,200,265):
        box(fan,xx-5,-19,140,xx+5,6,154,JOIN,'Frame bearing arm')
        circle(fan,'z',140,xx,2,3.4,14,CUT,'Fan arm M3 clearance')
        circle(fan,'z',143,xx,2,6.6,11.01,CUT,'Fan arm screw well for M3x6 leaving 3 mm web')
    # Counterbores retain three millimetres of material beneath each M3x6 head.
    for tag,xx,yys in [('PCI',4,(20,225)),('CPU',294,(20,225)),('MID',134,(3,222.5))]:
        rail=cs['19_'+tag+'_LONGITUDINAL_BOARD_RAIL_243_84mm']
        for yy in yys:circle(rail,'z',143,xx,yy,6.6,5.01,CUT,'M3x6 rail mounting head well')
    tower=cs['07_GPU_REINFORCED_REAR_TOWER']
    for xx in (80,140,158):circle(tower,'z',143,xx,248.5,6.6,5.01,CUT,'M3x6 tower base screw head well')
    for xx in (80,164):
        slot(tower,263,xx,262,292,6.6,7.01,'Upper sliding screw head channel')
        slot(tower,263,xx,157,165,6.6,7.01,'Lower sliding screw head channel')
    for n,z in [('08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE',276),('08_GPU_LOWER_TWO_TAB_RECEIVER_ADJUSTABLE',157)]:
        for xx in (80,164):circle(cs[n],'y',255.1,xx,z,4.7,4.91,CUT,'Rear entry H4.5 insert for sliding M3x6 clamp')
    # Front-to-side corners: two screws per corner, top and bottom.
    pciside=cs['16_PCI_INSET_SIDE_16_45mm'];cpuside=cs['16_CPU_VERTICAL_SIDE_FLUSH_TO_BEAM']
    for tag,side in [('PCI',pciside),('CPU',cpuside)]:
        front=cs['12_front_'+tag+'_SUPPORT_FRAME']
        for z in (8,132):
            x=12.45-16.45*z/140+8 if tag=='PCI' else 294.45
            circle(front,'y',-10,x,z,3.4,16.01,CUT,'Front corner M3 clearance')
            circle(front,'y',-10,x,z,6.6,13,CUT,'Front corner screw well leaving 3 mm web')
            circle(side,'y',6,x,z,4.7,6.5,CUT,'Front corner H4.5 insert')
    # Integrate small seam bridges into the CPU half; no separate bridge parts.
    frontcpu=cs['12_front_CPU_SUPPORT_FRAME'];frontpci=cs['12_front_PCI_SUPPORT_FRAME']
    for z in (0,124):
        box(frontcpu,140,-13,z,165,-10,z+16,JOIN,'Integral front seam bridge')
        circle(frontcpu,'y',-13,146,z+8,3.4,3.01,CUT,'Front seam M3x6 clearance')
        circle(frontpci,'y',-10,146,z+8,4.7,6.5,CUT,'Front seam H4.5 insert')
    # Floor bars now have bottom-lap end seats with bolts into each side frame.
    cradle=cs['05_CENTERED_FLAT_PSU_CRADLE_OPEN_INTAKE']
    for label,y in [('front',39.92),('rear',203.92)]:
        ground=cs['04_'+label+'_GROUND_BAR_290mm_FLAT_PSU']
        box(ground,20.45,y-10,0,28.45,y+10,3.2,JOIN,'PCI bottom lap end seat')
        box(ground,286.45,y-10,0,294.45,y+10,3.2,JOIN,'CPU bottom lap end seat')
        for side,x0,x1,x in [(pciside,20.3,28.6,24.45),(cpuside,286.3,294.6,290.45)]:
            box(side,x0,y-10.15,-.01,x1,y+10.15,3.2,CUT,'Ground bar seat with lateral print clearance')
            circle(ground,'z',0,x,y,3.4,3.21,CUT,'Bottom lap M3x6 clearance')
            circle(side,'z',3.2,x,y,4.7,6.5,CUT,'Bottom entry H4.5 insert for floor tie')
        for x in (79.4,225.4):
            circle(cradle,'z',8,x,y,3.4,22.01,CUT,'Cradle to crossbar screw clearance')
            circle(cradle,'z',11,x,y,6.6,19.01,CUT,'Cradle screw well leaving 3 mm web')
            circle(ground,'z',1.5,x,y,4.7,6.51,CUT,'Top entry H4.5 insert for cradle foot')
    # Narrow straps run front-to-back at the solid margins, clear of 120 mm intake.
    for x in (88.9,215.9):
        for y in (36.2,207.4):box(cradle,x-1.8,y-1.2,23.99,x+1.8,y+1.2,30.01,CUT,'3 mm strap slot outside PSU fan intake')
    rear.bRepBodies.item(0).appearance=d.appearances.itemByName('V03 frame')
    fan.bRepBodies.item(0).appearance=d.appearances.itemByName('V03 bracket')
    os.makedirs(OUT+'/Raw_STL',exist_ok=True)
    for name,expr in [('v13_rear_overall_length','304.45 mm'),('v13_fan_rail_length','284 mm'),('v13_bed_side','256 mm'),('v13_insert_pilot','4.7 mm'),('v13_screw_clearance','3.4 mm'),('v13_head_well','6.6 mm')]:
        d.userParameters.add(name,V(expr),'mm','V13 manufacturing reference; geometry controlled by named feature sketches')
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad,bad
    parts=[];objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name;c=o.component
        if not n.startswith('REF_'):
            assert c.bRepBodies.count==1,(n,c.bRepBodies.count)
            b=c.bRepBodies.item(0);assert b.isSolid and b.lumps.count==1,(n,b.lumps.count)
            bb=b.preciseBoundingBox;dims=[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in 'xyz']
            parts.append({'name':n,'native_size_mm':dims,'volume_mm3':b.volume*1000})
            op=d.exportManager.createSTLExportOptions(b,OUT+'/Raw_STL/'+n+'.stl');op.isBinaryFormat=True;assert d.exportManager.execute(op)
            objs.add(o)
        elif n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    assert len(parts)==17,len(parts)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    (open(OUT+'/parts.json','w',encoding='utf-8')).write(json.dumps(parts,indent=2))
    (open(OUT+'/interference.json','w',encoding='utf-8')).write(json.dumps({'count':rr.count,'interferences':inter},indent=2))
    assert not inter,inter
    pairs=[('18_ONE_PIECE_REAR_LOAD_BEAM_304_45mm','16_PCI_INSET_SIDE_16_45mm'),('18_ONE_PIECE_REAR_LOAD_BEAM_304_45mm','16_CPU_VERTICAL_SIDE_FLUSH_TO_BEAM'),('18_ONE_PIECE_REAR_LOAD_BEAM_304_45mm','07_GPU_REINFORCED_REAR_TOWER'),('18_ONE_PIECE_REAR_LOAD_BEAM_304_45mm','19_MID_LONGITUDINAL_BOARD_RAIL_243_84mm'),('20_ONE_PIECE_DUAL_140_FAN_RAIL_284mm','12_front_PCI_SUPPORT_FRAME'),('20_ONE_PIECE_DUAL_140_FAN_RAIL_284mm','12_front_CPU_SUPPORT_FRAME')]
    occs={o.component.name:o for o in root.occurrences};contacts=[]
    for a,b in pairs:
        value=app.measureManager.measureMinimumDistance(occs[a],occs[b]).value*10;assert abs(value)<.001,(a,b,value)
        contacts.append({'one':a,'two':b,'distance_mm':value})
    (open(OUT+'/contacts.json','w')).write(json.dumps(contacts,indent=2))
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(48,48,36);cam.target=P(15,12,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Assembly.png',1500,1150)
    vis={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:o.isLightBulbOn=o.component.name==rear.name
    cam=view.camera;cam.eye=P(37,44,29);cam.target=P(15,24,13);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/One-piece-rear-beam.png',1500,800)
    for o in root.occurrences:o.isLightBulbOn=vis[o.component.name]
    cam=view.camera;cam.eye=P(48,48,36);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v13_one_piece.f3d'))
    print(json.dumps({'parts':len(parts),'rear_beam_one_solid':True,'fan_rail_one_solid':True,'interference_count':len(inter),'contact_pairs':len(contacts),'timeline_health':'healthy','output':OUT},ensure_ascii=True))
