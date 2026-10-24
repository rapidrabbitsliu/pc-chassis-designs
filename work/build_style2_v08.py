"""Style 2, independent 315 mm PETG open-frame prototype. Fusion MCP entry point.
All input geometry in mm; reference hardware is never exported as printable parts.
"""
import adsk.core, adsk.fusion, os, json, math

ROOT = 'D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/'
OUT = ROOT + 'outputs/Style2-v08'
PSU_X = -.84  # Exhaust plane flush with the outside face of the left upright.
POSTS = [10.16, 165.10, 237.49]
HOLES = [(16.51,233.68),(140.97,233.68),(298.45,210.82),
         (16.51,78.74),(140.97,78.74),(298.45,78.74),
         (16.51,6.35),(140.97,6.35),(298.45,6.35)]

def run(_context: str):
    app=adsk.core.Application.get()
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name='Style2_V08_DUAL_140_FANS_FLOW_MINUS_X'
    d=adsk.fusion.Design.cast(app.activeProduct)
    d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    root=d.rootComponent
    tm=adsk.fusion.TemporaryBRepManager.get()
    P=lambda x,y,z:adsk.core.Point3D.create(x/10,y/10,z/10)
    V=adsk.core.Vector3D.create
    U=adsk.fusion.BooleanTypes.UnionBooleanType
    D=adsk.fusion.BooleanTypes.DifferenceBooleanType
    def box(x0,y0,z0,x1,y1,z1):
        assert x1>x0 and y1>y0 and z1>z0
        ob=adsk.core.OrientedBoundingBox3D.create(P((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),V(1,0,0),V(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10)
        return tm.createBox(ob)
    def cyl(axis,a,b,u,v,diam):
        coords=lambda t: {'x':(t,u,v),'y':(u,t,v),'z':(u,v,t)}[axis]
        return tm.createCylinderOrCone(P(*coords(a)),diam/20,P(*coords(b)),diam/20)
    def op(a,b,kind):
        assert tm.booleanOperation(a,b,kind),'Boolean failed'
        return a
    def join(a,b):return op(a,b,U)
    def cut(a,b):return op(a,b,D)
    def hole(b,axis,a,e,u,v,diam):return cut(b,cyl(axis,a,e,u,v,diam))
    def beam(a,b,width,thick,normal):
        pa=P(*a);pb=P(*b);direction=pa.vectorTo(pb);length=direction.length
        direction.normalize(); n=V(*normal); n.normalize()
        transverse=n.crossProduct(direction); transverse.normalize()
        center=P(*[(a[i]+b[i])/2 for i in range(3)])
        return tm.createBox(adsk.core.OrientedBoundingBox3D.create(center,direction,transverse,length,width/10,thick/10))
    os.makedirs(OUT+'/Raw_STL',exist_ok=True)
    parts=[]; comps={};refs=[]
    base=app.materialLibraries.item(0).appearances.itemById('Prism-119')
    palette={}
    for key,rgb in [('frame',(63,74,80)),('brace',(91,118,133)),('mount',(190,145,78)),('board',(37,104,70)),('gpu',(66,69,76)),('psu',(100,105,110)),('riser',(190,177,127))]:
        ar=d.appearances.addByCopy(base,'Style2 '+key)
        for prop in ('opaque_albedo','surface_albedo'):
            adsk.core.ColorProperty.cast(ar.appearanceProperties.itemById(prop)).value=adsk.core.Color.create(*rgb,255)
        palette[key]=ar
    def add(name,body,kind='frame',reference=False):
        assert body and body.isSolid and body.lumps.count==1,(name,'not a single solid')
        oc=root.occurrences.addNewComponent(adsk.core.Matrix3D.create());c=oc.component;c.name=name
        bf=c.features.baseFeatures.add();bf.name=name+' source geometry';bf.startEdit()
        c.bRepBodies.add(body,bf);bf.finishEdit();b=c.bRepBodies.item(0);b.name=name;b.appearance=palette['psu' if reference else 'brace'];b.opacity=.25 if reference else 1
        comps[name]=c
        if reference:refs.append(oc)
        else:
            bb=b.preciseBoundingBox
            dims=[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in 'xyz']
            parts.append({'name':name,'native_size_mm':dims,'volume_mm3':b.volume*1000})
        return c
    # Three one-piece uprights, each drilled to the transformed nine-hole pattern.
    for index,x in enumerate(POSTS):
        b=box(x-11,0,10,x+11,20,313.8)
        assigned=[(243.84-yy,9+xx) for xx,yy in HOLES if abs((243.84-yy)-x)<.1]
        if index==0:
            b=join(b,box(x-11,0,299,38.02,20,313.8))
            assigned.append((33.02,307.45))
        for hx,hz in assigned:
            # Raised bearing boss, M3 H4.5 insert from front, no plastic against PCB traces.
            b=join(b,cyl('y',-10.8,0,hx,hz,10))
            b=hole(b,'y',-10.81,-4.3,hx,hz,4.7)
        for z in (50,64,277,291):b=hole(b,'y',13.5,20.01,x,z,4.7)
        if index in (0,2):
            for z in (94,244):b=hole(b,'y',13.5,20.01,x,z,4.7)
        for z in (20,35):b=hole(b,'x',x-11.01,x-4.5,10,z,4.7)
        for zz in (160,184):
            if index==0:b=hole(b,'x',x-11.01,x-4.5,10,zz,4.7)
            if index==2:b=hole(b,'x',x+4.5,x+11.01,10,zz,4.7)
        if index==2:
            for zz in (50,130,236,290):b=hole(b,'x',x+4.5,x+11.01,10,zz,4.7)
        add('01_UPRIGHT_'+str(index+1),b)
    # Feet: open-front U sockets leave motherboard bosses unobstructed.
    for index,x in enumerate(POSTS):
        b=box(x-15,-105,0,x+15,139,10)
        b=cut(b,box(x-15.01,-13,8.5,x+15.01,-10,10.01))
        for a,e in [(x-15,x-11.2),(x+11.2,x+15)]:b=join(b,box(a,-.2,10,e,24,42))
        b=join(b,box(x-15,20.2,10,x+15,24,42))
        for z in (20,35):
            b=hole(b,'x',x-15.01,x-11.19,10,z,3.4)
            b=hole(b,'x',x-15.01,x-14,10,z,6.6)
        for yy in (-75,30,101):b=hole(b,'z',3.5,10.01,x,yy,4.7)
        if index in (0,2):
            if index==0:
                b=join(b,box(x-11,114.5,10,x+15,138,32))
                b=hole(b,'x',x-11.01,x-4.5,126,20,4.7)
            else:
                b=join(b,box(x-15,114.5,10,x+11,138,32))
                b=hole(b,'x',x+4.5,x+11.01,126,20,4.7)
        add('02_FOOT_'+str(index+1),b)
    # Open center: deeper crossmembers, two vertically spaced screws at each post,
    # and short integral corner knees replace the full-height diagonal.
    for label,z in [('LOWER',57),('UPPER',284)]:
        b=box(-.84,20,z-14,248.49,26,z+14)
        knee_z=94 if label=='LOWER' else 244
        bar_z=63 if label=='LOWER' else 278
        for x,tip in [(POSTS[0],50),(POSTS[2],197)]:
            b=join(b,beam((x,23,knee_z),(tip,23,bar_z),16,6,(0,1,0)))
            b=join(b,cyl('y',20,26,x,knee_z,16))
            b=hole(b,'y',19.99,26.01,x,knee_z,3.4)
            b=hole(b,'y',23,26.01,x,knee_z,6.6)
        for x in POSTS:
            for hz in (z-7,z+7):
                b=hole(b,'y',19.99,26.01,x,hz,3.4)
                b=hole(b,'y',23,26.01,x,hz,6.6)
        add('03_'+label+'_CROSSBAR',b,'brace')
    # Compact orthogonal frames follow the PSU top/rear perimeter with 2 mm clearance.
    for index in (0,2):
        x=POSTS[index]
        sign=-1 if index==0 else 1
        cx=x+sign*17; xa=cx-6; xb=cx+6
        b=box(xa,0,174,xb,136,194)
        b=join(b,box(xa,116,20,xb,136,184))
        b=join(b,box(xa,0,148,xb,20,194))
        b=join(b,cyl('x',xa,xb,126,184,26))
        for y,z in [(10,160),(10,184),(126,20)]:
            b=join(b,cyl('x',xa,xb,y,z,20))
            b=hole(b,'x',xa-.01,xb+.01,y,z,3.4)
            if sign<0:b=hole(b,'x',xa-.01,xb-3,y,z,6.6)
            else:b=hole(b,'x',xa+3,xb+.01,y,z,6.6)
        add('05_SIDE_RECTANGULAR_FRAME_'+str(index+1),b,'brace')
    # Front GPU carrier, independent of the riser connector.
    b=box(-.84,-100,14,248.49,-50,22)
    b=cut(b,box(22,-94,13.9,218,-56,22.1))
    for x in POSTS:
        b=join(b,box(x-8,-100,10,x+8,-50,22))
        b=hole(b,'z',9.99,22.01,x,-75,3.4)
        b=hole(b,'z',13,22.01,x,-75,6.6)
    for xx in (25,155):
        for yy in (-97,-53):b=hole(b,'z',15.5,22.01,xx,yy,4.7)
    for xx in (10,230):
        for yy in (-88,-62):b=hole(b,'z',15.5,22.01,xx,yy,4.7)
    # Small riser shelf only supports PCB edge zones; removable while dimensions are provisional.
    add('06_GPU_CARRIER',b)
    b=box(20,-100,22,160,-50,26)
    b=cut(b,box(29,-81,21.99,151,-58,26.01))
    for xx in (25,155):
        for yy in (-97,-53):
            b=hole(b,'z',21.99,26.01,xx,yy,3.4)
            b=hole(b,'z',25,26.01,xx,yy,6.6)
    add('07_RISER_TRAY_PENDING_MEASUREMENT',b,'mount')
    # Shell-edge GPU pads intentionally use conservative placeholder contact faces.
    for tag,x in [('LEFT',10),('RIGHT',230)]:
        b=box(x-7,-99,22,x+7,-51,40)
        for ya,yb in [(-99,-95.5),(-54.5,-51)]:b=join(b,box(x-7,ya,40,x+7,yb,46))
        for yy in (-88,-62):
            b=hole(b,'z',21.99,40.01,x,yy,3.4)
            b=hole(b,'z',25,40.01,x,yy,6.6)
        add('08_GPU_PAD_'+tag+'_FIT_REQUIRED',b,'mount')
    # Upright PSU: exhaust -X; 140 X by 86 Y by 150 Z. No end wall on exhaust side.
    for tag,yy in [('FRONT',30),('REAR',101)]:
        b=box(-.84,yy-10,10,248.49,yy+10,16)
        b=join(b,box(PSU_X,yy-10,16,PSU_X+140,yy+10,22))
        # Corrected axis: stops at X ends, on BOTH supporting crossbars.
        # Exhaust-side straight stop and cable-side 45 degree entry, each 0.5 mm clear.
        b=join(b,box(PSU_X-6.5,yy-10,16,PSU_X+152.5,yy+10,22))
        b=join(b,box(PSU_X-6.5,yy-10,22,PSU_X-.5,yy+10,32))
        ramp=box(PSU_X+140.5,yy-10,22,PSU_X+152.5,yy+10,32)
        ob=adsk.core.OrientedBoundingBox3D.create(
            P(PSU_X+142.5+50/math.sqrt(2),yy,32+50/math.sqrt(2)),
            V(0,1,0),V(-1,0,1),20,20,10)
        ramp=cut(ramp,tm.createBox(ob));b=join(b,ramp)
        for x in POSTS:
            b=hole(b,'z',9.99,22.01,x,yy,3.4)
            b=hole(b,'z',13,22.01,x,yy,6.6)
        # Strap passages are outboard of the PSU shell.
        # Strap passages sit immediately outside the shell ends; the exhaust opening
        # above Z22 stays unobstructed. The first passage is in the front/rear flange.
        for xx in (PSU_X+8,PSU_X+132):
            sy=yy-7 if tag=='FRONT' else yy+7
            b=cut(b,box(xx-2,sy-2,9.99,xx+2,sy+2,16.01))
        if tag=='FRONT': b=cut(b,box(-20,-20,9.9,260,24.2,40))
        add('09_PSU_SADDLE_'+tag,b,'mount')
    # Fan mast stands outside the existing right side frame. Four integral feet
    # land on the right upright at unobstructed heights, with recessed M3x6 joints.
    b=box(262,0,10,274,20,314)
    for zz in (50,130,236,290):
        b=join(b,box(248.49,0,zz-7,274,20,zz+7))
        b=hole(b,'x',248.48,274.01,10,zz,3.4)
        b=hole(b,'x',251.49,274.01,10,zz,6.6)
    for zz in (68,104,220,256):b=hole(b,'x',261.99,268.5,4,zz,4.7)
    add('10_FAN_MAST_RIGHT_SIDE',b,'brace')
    for label,cz in [('GPU',86),('CPU_RAM',238)]:
        b=box(256,-141,cz-76,262,-2,cz+76)
        b=hole(b,'x',255.99,262.01,-71,cz,130)
        for yy in (-133.25,-8.75):
            for zz in (cz-62.25,cz+62.25):b=hole(b,'x',255.99,262.01,yy,zz,4.5)
        for zz in (cz-18,cz+18):
            b=join(b,box(256,-2,zz-7,262,8,zz+7))
            b=hole(b,'x',255.99,262.01,4,zz,3.4)
            b=hole(b,'x',255.99,259,4,zz,6.6)
        add('11_FAN_PANEL_'+label+'_140mm',b,'brace')
        # Purchased fan reference, 140x140x25, 124.5 mm square hole spacing.
        fan=box(262,-141,cz-70,287,-1,cz+70)
        fan=hole(fan,'x',261.99,287.01,-71,cz,130)
        for yy in (-133.25,-8.75):
            for zz in (cz-62.25,cz+62.25):fan=hole(fan,'x',261.99,287.01,yy,zz,4.5)
        for yy,zz in [(-139,cz),(-3,cz),(-71,cz-68),(-71,cz+68)]:
            fan=join(fan,beam((275.5,-71,cz),(275.5,yy,zz),6,3,(1,0,0)))
        fan=join(fan,cyl('x',274,277,-71,cz,40))
        add('REF_FAN_'+label+'_140x140x25_FLOW_MINUS_X',fan,'psu',True)
    # Reference models, transformed from the established hardware coordinate system.
    b=box(0,-12.4,9,243.84,-10.8,313.8)
    for xx,yy in HOLES:b=hole(b,'y',-12.41,-10.79,243.84-yy,9+xx,3.5)
    add('REF_MSI_Z390_A_PRO_304.8x243.84',b,'board',True)
    add('REF_GALAX_GPU_ENVELOPE_235.5x129x40',box(5,-95,40,240.5,-55,169),'gpu',True)
    b=box(PSU_X,28,22,PSU_X+140,114,172)
    # Stylized vent recesses identify direction only, not measured OEM grille geometry.
    for zz in range(36,162,9):b=cut(b,box(PSU_X-.01,35,zz,PSU_X+.8,107,zz+3))
    b=hole(b,'y',113.1,114.01,PSU_X+70,97,120)
    add('REF_ENERMAX_UPRIGHT_EXHAUST_MINUS_X_FAN_PLUS_Y',b,'psu',True)
    add('REF_PSU_FAN_SIDE_DIRECTION_ONLY',cyl('y',113.1,113.8,PSU_X+70,97,118),'gpu',True)
    # Motherboard rear I/O exits -X; simplified blocks show direction, not exact port locations.
    add('REF_MOTHERBOARD_IO_MINUS_X',box(-6,-30,175,0,-12.4,293),'psu',True)
    add('REF_RISER_PCB_PHOTO_ESTIMATE_130x18x1.6',box(22,-78.5,26,152,-60.5,27.6),'riser',True)
    add('REF_PCIE_SOCKET_89x9x11_ESTIMATE',box(48,-74,27.6,137,-65,38.6),'riser',True)
    # Export metadata now; follow-up verification adds print orientations and interference report.
    for item in parts:
        c=comps[item['name']]
        so=d.exportManager.createSTLExportOptions(c,OUT+'/Raw_STL/'+item['name']+'.stl')
        so.isBinaryFormat=True;assert d.exportManager.execute(so)
    open(OUT+'/parts.json','w',encoding='utf-8').write(json.dumps(parts,ensure_ascii=False,indent=2))
    # Final display assignment on persistent bodies.
    color=d.appearances.itemByName('Style2 brace')
    for key in ('opaque_albedo','surface_albedo'):
        adsk.core.ColorProperty.cast(color.appearanceProperties.itemById(key)).value=adsk.core.Color.create(35,120,220,255)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/Style2_V08_Dual140_Colored.f3d'))
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(OUT+'/Style2_V08_Dual140.step'))
    view=app.activeViewport;cam=view.camera;cam.eye=P(480,-650,430);cam.target=P(123,35,150);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Assembly.png',1600,1400)
    print(json.dumps({'parts':len(parts),'height_mm':314,'motherboard_top_mm':313.8,'fan_airflow':'-X','output':OUT}))
