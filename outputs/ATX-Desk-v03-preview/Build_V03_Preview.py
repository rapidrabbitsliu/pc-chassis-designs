"""V03 layout review, not released for printing.
Top view: +X toward CPU/right, +Y toward rear I/O/top, +Z up.
"""
import adsk.core, adsk.fusion, os, json
OUT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/ATX-Desk-v03-preview'
HOLES={1:(16.51,233.68),2:(140.97,233.68),3:(298.45,210.82),
       4:(16.51,78.74),5:(140.97,78.74),6:(298.45,78.74),
       7:(16.51,6.35),8:(140.97,6.35),9:(298.45,6.35)}
def run(_context: str):
    app=adsk.core.Application.get();doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d=adsk.fusion.Design.cast(app.activeProduct);d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    root=d.rootComponent;V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create
    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
    parts=[];refs=[]
    os.makedirs(OUT,exist_ok=True)
    for n,v in [('desk_limit',290),('footprint_width',290),('board_width',304.8),('board_depth',243.84),('board_bottom_height',208),('approx_slot_x',126.4)]:
        d.userParameters.add(n,V(str(v)+' mm'),'mm','V03 layout review; fixed profiles require regeneration')
    def comp(name,ref=False):
        o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());o.component.name=name
        (refs if ref else parts).append(o);return o.component
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
    def bore(c,axis,pos,u,v,diam,depth,name):return circle(c,axis,pos,u,v,diam,depth,CUT,name)
    def slot(c,axis,pos,u,v0,v1,diam,depth,name):
        bore(c,axis,pos,u,v0,diam,depth,name+' end1');bore(c,axis,pos,u,v1,diam,depth,name+' end2')
        poly(c,axis,pos,[(u-diam/2,v0),(u+diam/2,v0),(u+diam/2,v1),(u-diam/2,v1)],depth,CUT,name+' middle')
    def loftpanel(c,x0,x1,y0,y1,z0,z1,width,name):
        sk0=profile(c,'z',z0,[(x0,y0),(x0+width,y0),(x0+width,y1),(x0,y1)],name+' lower')
        sk1=profile(c,'z',z1,[(x1,y0),(x1+width,y0),(x1+width,y1),(x1,y1)],name+' upper')
        inp=c.features.loftFeatures.createInput(NEW);inp.isSolid=True
        inp.loftSections.add(sk0.profiles.item(0));inp.loftSections.add(sk1.profiles.item(0))
        f=c.features.loftFeatures.add(inp);f.name=name;sk0.isVisible=False;sk1.isVisible=False
    sidepanels=[]
    for side,xb,xt in [('PCI',8.45,-4),('CPU',282.45,282.45)]:
        for section,a,b in [('front',-10,121.72),('rear',122.12,253.84)]:
            c=comp('01_'+side+'_'+section+('_INSET_SIDE' if side=='PCI' else '_VERTICAL_SIDE'))
            loftpanel(c,xb,xt,a,b,0,190,16,'Inward taper side frame')
            poly(c,'x',-10,[(a+14,36),(a+14,176),(b-34,176)],340,CUT,'Upper triangular opening')
            poly(c,'x',-10,[(a+34,16),(b-14,16),(b-14,154)],340,CUT,'Lower triangular opening')
            # Low crossbars sit in these notches, preserving continuous floor support elsewhere.
            y=65.92 if section=='front' else 177.92
            box(c,-10,y-10,0,320,y+10,8,CUT,'Recess for bottom crossbar')
            sidepanels.append(c)
    for side,xb,xt,sgn in [('PCI',8.45,-4,-1),('CPU',282.45,282.45,1)]:
        def edge(z):return xb+(xt-xb)*z/190+(0 if sgn==-1 else 16)
        for tag,z in [('low',22),('high',158)]:
            c=comp('02_'+side+'_'+tag+'_SEAM_PLATE')
            x0=edge(z)-4 if sgn==-1 else edge(z);x1=edge(z+28)-4 if sgn==-1 else edge(z+28)
            loftpanel(c,x0,x1,101.92,141.92,z,z+28,4,'Taper matching seam plate - screw detail pending')
    # Three ribbed crossmembers. The rear member includes the staggered hole 3 pad.
    for tag,y,nums in [('FRONT',6.35,(7,8,9)),('MID',78.74,(4,5,6)),('REAR',233.68,(1,2,3))]:
        c=comp('03_'+tag+'_MOTHERBOARD_BEAM')
        box(c,-4,y-9,190,308.8,y+9,198,NEW,'Upper beam flange')
        box(c,14,y-4,178,281.45,y+4,190,JOIN,'Underside rib')
        poly(c,'x',14,[(y-4,184),(y+4,184),(y+9,190),(y-9,190)],267.45,JOIN,'Printable rib transition')
        if tag=='REAR':box(c,286,201.82,190,308.8,233.68,198,JOIN,'Staggered hole 3 pad')
        for num in nums:
            x,yy=HOLES[num];circle(c,'z',198,x,yy,8,10,JOIN,'Motherboard mount '+str(num))
            bore(c,'z',203.1,x,yy,4.7,4.9,'M3 insert pocket '+str(num))
    # Full-width bottom contact is 290 mm wide, ending at the hole 9 X line.
    for tag,y in [('front',65.92),('rear',177.92)]:
        c=comp('04_'+tag+'_GROUND_BAR_290mm')
        box(c,8.45,y-10,0,298.45,y+10,8,NEW,'290 mm floor crossbar')
    # Independent load path from centered PSU to the bottom crossbars.
    c=comp('05_CENTERED_PSU_CRADLE')
    box(c,104.4,42.92,14,112.4,200.92,20,NEW,'Left cradle runner')
    box(c,112.4,51.92,14,200.4,67.92,20,JOIN,'Front PSU bearing rail')
    box(c,192.4,42.92,14,200.4,200.92,20,JOIN,'Right cradle runner')
    box(c,112.4,175.92,14,192.4,191.92,20,JOIN,'Rear PSU bearing rail')
    for x in (108.4,196.4):
        for y in (65.92,177.92):box(c,x-4,y-5,8,x+4,y+5,14,JOIN,'Cradle load foot')
    # Small lower-edge stops; large fan face remains open above the edge.
    for x in (107.4,195.4):
        for y in (53.92,185.92):box(c,x,y,20,x+2,y+4,26,JOIN,'PSU bottom-edge stop')
    for tag,x in [('PCI',108.4),('CPU',196.4)]:
        c=comp('06_'+tag+'_PSU_RETAINER')
        poly(c,'x',x-4,[(42.92,20),(50.92,20),(50.92,171),(192.92,171),(192.92,20),(200.92,20),(200.92,178),(42.92,178)],8,NEW,'Removable retainer outside intake face')
    # GPU bracket at rear, shifted to the agreed first slot. No tail support exists in V03.
    c=comp('07_GPU_REAR_TOWER')
    box(c,74,224.68,198,170,268,206,NEW,'Rear tower foot - fasteners pending')
    bore(c,'z',198,140.97,233.68,9.5,8,'Hole 2 standoff clearance')
    box(c,74,260,206,170,268,350,JOIN,'Rear display connector frame')
    poly(c,'y',260,[(88,214),(90,212),(154,212),(156,214),(156,308),(154,310),(90,310),(88,308)],8,CUT,'Display connector window')
    for x in (80,164):slot(c,'y',260,x,316,344,3.4,8,'Bracket height adjustment')
    c=comp('08_GPU_REAR_SLIDER')
    box(c,74,250,316,170,260,346,NEW,'GPU rear sliding carrier')
    box(c,74,244.84,330,170,250,336,JOIN,'GPU screw ledge')
    box(c,89,250,316,155,260,329,CUT,'Keep display plug path open')
    # Slot across X for the bracket screw; all coordinates remain outside the motherboard rear edge.
    bore(c,'z',330,90,247.5,3.4,6,'GPU screw slot first end')
    bore(c,'z',330,154,247.5,3.4,6,'GPU screw slot second end')
    box(c,90,245.8,330,154,249.2,336,CUT,'GPU screw transverse slot')
    # Two 140x140x25 front intake fans. They add fore-aft space, not lateral width.
    c=comp('09_FRONT_DUAL_FAN_CARRIER')
    box(c,12.4,-25,198,296.4,-19,210,NEW,'Common 284 mm wide fan carrier')
    for x in (50,154.4,265):
        box(c,x-5,-19,198,x+5,14,204,JOIN,'Fan carrier arm onto front beam')
        poly(c,'x',x-5,[(-25,198),(-19,184),(-2.65,198)],10,JOIN,'Fan carrier arm gusset')
    for tag,x0 in [('GPU',12.4),('CPU',156.4)]:
        c=comp('10_'+tag+'_140_FAN_MOUNT')
        poly(c,'y',-25,[(x0,210),(x0+140,210),(x0+140,350),(x0,350)],6,NEW,'140 mm removable fan mounting frame')
        bore(c,'y',-25,x0+70,280,130,6,'Open airflow aperture')
        for xx in (x0+7.75,x0+132.25):
            for zz in (217.75,342.25):bore(c,'y',-25,xx,zz,4.5,6,'124.5 mm pitch fan fixing clearance')
    for tag,x0 in [('GPU',12.4),('CPU',156.4)]:
        c=comp('REF_CASE_FAN_'+tag+'_140x140x25',True)
        poly(c,'y',-50,[(x0,210),(x0+140,210),(x0+140,350),(x0,350)],25,NEW,'140x140x25 fan envelope')
        bore(c,'y',-50,x0+70,280,130,25,'Rotor opening reference')
        box(c,x0+3,-38,278,x0+137,-36,282,JOIN,'Rotor reference spoke horizontal')
        box(c,x0+68,-38,213,x0+72,-36,347,JOIN,'Rotor reference spoke vertical')
        circle(c,'y',-38,x0+70,280,32,2,JOIN,'Fan hub reference')
        for xx in (x0+7.75,x0+132.25):
            for zz in (217.75,342.25):bore(c,'y',-50,xx,zz,4.5,25,'Reference fan mounting bore')
        a=comp('REF_AIRFLOW_'+tag+'_FRONT_TO_REAR',True)
        poly(a,'z',279,[(x0+65,-75),(x0+75,-75),(x0+75,-64),(x0+82,-64),(x0+70,-53),(x0+58,-64),(x0+65,-64)],2,NEW,'Front intake direction +Y')
    # Hardware references, not printable components.
    c=comp('REF_BOARD_304.8x243.84_NUMBERED_HOLES',True)
    box(c,0,0,208,304.8,243.84,209.6,NEW,'Motherboard component-side reference')
    for num,(x,y) in HOLES.items():bore(c,'z',208,x,y,3.96,1.6,'Board hole '+str(num))
    c=comp('REF_CPU_RIGHT',True);box(c,185,108.84,209.6,260,178.84,214.6,NEW,'CPU position reference only')
    c=comp('REF_MEMORY_RIGHT_FRONT',True)
    for v in (184,194,204,214):box(c,150,243.84-v-2.6,209.6,285,243.84-v+2.6,222,NEW,'DIMM position reference')
    c=comp('REF_PRIMARY_PCIE_X126.4_APPROX',True);box(c,122.4,96.84,209.6,130.4,201.84,219.6,NEW,'Primary GPU slot approximate')
    c=comp('REF_SECOND_LONG_PCIE_X60_APPROX',True);box(c,56,96.84,209.6,64,201.84,219.6,NEW,'Second long PCIe approximate')
    c=comp('REF_GPU_FANS_TO_MINUS_X',True);box(c,88.4,20.84,221,128.4,243.84,335,NEW,'GPU body 40 x 223 x 114')
    c=comp('REF_PSU_CENTER_152.4_121.92',True);box(c,109.4,51.92,20,195.4,191.92,170,NEW,'PSU 86 x 140 x 150')
    c=comp('REF_PSU_INTAKE_PLUS_X_CPU_SIDE',True);circle(c,'x',195.4,121.92,95,120,.3,NEW,'Large PSU intake fan faces CPU side')
    c=comp('REF_GPU_FAN_MARKERS_MINUS_X',True)
    for y in (75,180):circle(c,'x',88.1,y,278,92,.3,NEW,'GPU fan faces away from PSU fan')
    # Colors match the top-view alignment illustration.
    base=app.materialLibraries.item(0).appearances.itemById('Prism-119');pal={}
    for name,rgb in [('frame',(105,155,205)),('beam',(175,205,225)),('bracket',(235,155,65)),('board',(65,155,95)),('CPU',(232,173,80)),('RAM',(148,116,185)),('slot',(65,145,220)),('PSU',(105,120,145)),('GPU',(215,130,60))]:
        a=d.appearances.addByCopy(base,'V03 '+name)
        for prop in ('opaque_albedo','surface_albedo'):adsk.core.ColorProperty.cast(a.appearanceProperties.itemById(prop)).value=adsk.core.Color.create(*rgb,255)
        adsk.core.FloatProperty.cast(a.appearanceProperties.itemById('surface_roughness')).value=.5;pal[name]=a
    for o in parts+refs:
        c=o.component;n=c.name;k='frame'
        if n.startswith('03_'):k='beam'
        elif n.startswith(('04_','05_','06_','07_','08_','09_','10_')):k='bracket'
        elif n.startswith('REF_BOARD'):k='board';c.opacity=.25
        elif n.startswith('REF_CPU'):k='CPU';c.opacity=.8
        elif n.startswith('REF_MEMORY'):k='RAM'
        elif n.startswith(('REF_PRIMARY','REF_SECOND')):k='slot'
        elif n.startswith('REF_PSU'):k='PSU';c.opacity=.55
        elif n.startswith('REF_GPU'):k='GPU';c.opacity=.4
        elif n.startswith('REF_CASE_FAN'):k='slot';c.opacity=.8
        elif n.startswith('REF_AIRFLOW'):k='slot'
        for b in c.bRepBodies:b.appearance=pal[k]
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad,bad
    # Check actual foot contact width from all printable bodies crossing z=0.
    floor=[]
    for o in parts:
        for b in o.component.bRepBodies:
            assert b.isSolid
            for vert in b.vertices:
                if abs(vert.geometry.z)<1e-5:floor.append(vert.geometry.x*10)
    footprint=[min(floor),max(floor)];assert abs(footprint[1]-footprint[0]-290)<.01,footprint
    info={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','holes_mm':HOLES,'ground_contact_x_mm':footprint,'ground_width_mm':290,
          'desk_range_x_mm':[8.45,298.45],'PSU_bounds_mm':[[109.4,51.92,20],[195.4,191.92,170]],
          'PSU_center_xy_mm':[152.4,121.92],'PSU_fan':'+X toward CPU','GPU_fans':'-X toward second PCIe',
          'approx_primary_slot_x_mm':126.4,'tail_support_removed':True,'CPU_side_vertical':True,'PCI_side_tapered_only':True,'case_fans':{'count':2,'size_mm':[140,140,25],'hole_pitch_mm':124.5,'airflow':'+Y front to rear','model':'unconfirmed'},'added_front_extent_mm':50,'timeline_features':d.timeline.count,
          'timeline_health':'healthy','printable_candidate_parts':[o.component.name for o in parts]}
    with open(OUT+'/layout.json','w') as f:json.dump(info,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False
    cam.eye=P(54,-46,48);cam.target=P(15,12,17);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True
    view.camera=cam;view.refresh();assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v03_layout.f3d'))
    print(json.dumps(info))
