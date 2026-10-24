"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v05-preview/ATX_Desk_v05_layout.f3d'
OUT=ROOT+'ATX-Desk-v06-preview'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;P=adsk.core.Point3D.create
    for o in root.occurrences:
        n=o.component.name
        if n.startswith(('03_','07_','08_','09_','10_','REF_CASE_FAN_','REF_AIRFLOW_','REF_BOARD_','REF_CPU_','REF_MEMORY_','REF_PRIMARY_','REF_SECOND_','REF_GPU_')):
            m=o.transform2;m.translation=adsk.core.Vector3D.create(0,0,-5);o.transform2=m
    d.snapshots.add()
    os.makedirs(OUT,exist_ok=True)
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad,bad
    objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name
        if not n.startswith('REF_') or n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    with open(OUT+'/interference.json','w') as f:json.dump({'count':rr.count,'interferences':inter},f,indent=2)
    data={'status':'LAYOUT_PREVIEW_NOT_FOR_PRINTING','board_bottom_z_mm':158,'board_lowered_mm':50,'PSU_top_mm':116,'board_to_PSU_gap_mm':42,'lowest_board_beam_z_mm':128,'PSU_retainer_top_mm':125,'front_cover_removed':True,'support_layout':'front and rear frames; open sides with low ties and top rails','floor_width_mm':290,'timeline_health':'healthy','interference_count':rr.count}
    with open(OUT+'/layout.json','w') as f:json.dump(data,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(54,-46,40);cam.target=P(15,12,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Perspective.png',1500,1150)
    cam=view.camera;cam.eye=P(53,48,36);cam.target=P(15,12,13);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Rear.png',1500,1150)
    cam=view.camera;cam.eye=P(54,-46,40);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v06_layout.f3d'))
    print(json.dumps(data))
