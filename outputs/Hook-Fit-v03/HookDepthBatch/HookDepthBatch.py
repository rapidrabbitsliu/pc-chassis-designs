"""Four-slot coupon ONLY. No load rating; NOT a PSU support.
Units mm. Edit config then regenerate in a NEW Fusion document.
"""
import adsk.core, adsk.fusion, os, json
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG=dict(horizontal_pitch=20.0,vertical_pitch=40.0,slot_width=5.2,
            slot_height=15.0,empirical_tight_fit_depth=4.2,rear_gap_estimated=10.0,
            plate_thickness=3.0,hook_width=3.8,throat=4.4,toe_drop=3.0,
            toe_thickness=3.0,insertion_lift=5.0)

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
    c=CONFIG
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
    results=[]
    for t,offset in [(4.0,0),(4.2,42)]:
        tag=f'{t:.1f}'
        coupon=comp('DEPTH '+tag+' mm - FIT ONLY')
        rect(coupon,-3,7,0,22,offset-16,32,NEW,'Compact plate 32 x 15 x 3')
        for z in (offset-10,offset+10):
            poly(coupon,[(0,12.5),(t,12.5),(t,9.5),(t+3,9.5),(t+3,16),(0,16)],z-1.9,3.8,JOIN,'Upper hook '+tag)

        before=coupon.bRepBodies.item(0).volume
        # Seven-segment recessed numerals on FRONT face. 0.6 mm deep,
        # >=0.8 mm stroke; no dependency on fonts installed in Fusion.
        segs={'a':(0,7.2,4.4,8),'b':(3.6,4,4.4,7.2),
              'c':(3.6,.8,4.4,4),'d':(0,0,4.4,.8),
              'e':(0,.8,.8,4),'f':(0,4,.8,7.2),'g':(0,3.6,4.4,4.4)}
        digits={'4':'fgbc','0':'abcdef','2':'abged'}
        for ch,start in [('4',-8),('.',-1.8),(tag[-1],1)]:
            marks=[(0,0,1,1)] if ch=='.' else [segs[k] for k in digits[ch]]
            for x0,y0,x1,y1 in marks:
                rect(coupon,-3,y0+9,-2.4,y1+9,offset+start+x0,x1-x0,CUT,'Engrave '+tag)
        assert coupon.bRepBodies.count==1 and coupon.bRepBodies.item(0).isSolid
        body=coupon.bRepBodies.item(0);assert body.volume<before
        body.name='DEPTH '+tag+' mm ENGRAVED - NO LOAD'
        mgr=d.exportManager
        os.makedirs(OUT,exist_ok=True)
        opt=mgr.createSTLExportOptions(coupon,os.path.join(OUT,'raw_depth_'+tag+'.stl'))
        opt.sendToPrintUtility=False;assert mgr.execute(opt)
        results.append({'depth_mm':t,'engraving_mm':.6,'volume_mm3':body.volume*1000,'offset_z_mm':offset,'solid':True})
    for i in range(d.timeline.count):
        item=d.timeline.item(i)
        assert item.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,(item.name,item.errorOrWarningMessage)
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(os.path.join(OUT,'HookDepth_4.0_4.2_v03.f3d')))
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False
    cam.eye=P(-15,4,15);cam.target=P(0,0,2);cam.upVector=adsk.core.Vector3D.create(0,1,0)
    cam.isFitView=True;view.camera=cam;view.refresh()
    with open(os.path.join(OUT,'verification.json'),'w') as f:json.dump(results,f,indent=2)
    print(json.dumps(results))
