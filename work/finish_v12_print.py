"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v11-preview/ATX_Desk_v11_layout.f3d'
OUT=ROOT+'ATX-Desk-v12-print-review'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;P=adsk.core.Point3D.create
    for o in root.occurrences:
        if o.component.name=='19_MID_LONGITUDINAL_BOARD_RAIL_243_84mm':
            c=o.component
            for i in range(c.features.count-1,-1,-1):
                if c.features.item(i).name=='Continue printable rib transition':c.features.item(i).deleteMe()
    os.makedirs(OUT+'/Raw_STL',exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    objs=adsk.core.ObjectCollection.create();parts=[]
    for o in root.occurrences:
        n=o.component.name;c=o.component
        if not n.startswith('REF_'):
            assert c.bRepBodies.count==1,(n,c.bRepBodies.count)
            b=c.bRepBodies.item(0);assert b.isSolid
            bb=b.boundingBox;dims=[(bb.maxPoint.x-bb.minPoint.x)*10,(bb.maxPoint.y-bb.minPoint.y)*10,(bb.maxPoint.z-bb.minPoint.z)*10]
            mode='xy';angle=0;brim=5;note='Check supports in slicer'
            if n.startswith('16_'):mode='yz';brim=3;note='Side frame laid on its side; PCI taper may need local support'
            elif n.startswith(('12_front_','10_','20_','08_')):mode='xz'
            elif n.startswith('07_'):mode='yz';note='Tower on side; inspect local supports around holes and foot'
            elif n.startswith('04_'):angle=45;note='Rotate 45 degrees on bed; no joint needed'
            elif n.startswith('19_'):mode='xy';note='Bosses upward; middle rail uses continuous underside rib; inspect 6 mm end overhangs'
            parts.append({'name':n,'native_size_mm':dims,'volume_mm3':b.volume*1000,'orientation':mode,'angle_deg':angle,'brim_mm':brim,'note':note})
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    with open(OUT+'/parts.json','w') as f:json.dump(parts,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,43);cam.target=P(15,12,15);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    vis={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:
        if o.component.name.startswith('REF_'):o.isLightBulbOn=False
    cam=view.camera;cam.eye=P(48,45,45);cam.target=P(15,12,12);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Structure.png',1500,1150)
    for o in root.occurrences:o.isLightBulbOn=vis[o.component.name]
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v12_print_review.f3d'))
    # Export every printable solid, excluding all hardware reference models.
    for o in root.occurrences:
        if not o.component.name.startswith('REF_'):
            op=d.exportManager.createSTLExportOptions(o.component.bRepBodies.item(0),OUT+'/Raw_STL/'+o.component.name+'.stl');op.isBinaryFormat=True
            assert d.exportManager.execute(op)
            assert os.path.exists(OUT+'/Raw_STL/'+o.component.name+'.stl')
    print(json.dumps({'parts':len(parts),'timeline_health':'healthy','interference_count':rr.count}))
