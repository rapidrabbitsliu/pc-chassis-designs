"""V05 preview: horizontal centered PSU, intake down, rear exhaust unchanged."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/'
BASE=ROOT+'ATX-Desk-v10-preview/ATX_Desk_v10_layout.f3d'
OUT=ROOT+'ATX-Desk-v11-preview'
def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent;P=adsk.core.Point3D.create
    os.makedirs(OUT,exist_ok=True)
    cs={o.component.name:o for o in root.occurrences}
    pairs=[('18_REAR_BEAM_PCI_TAPERED_END_AND_FRONT_LAP','16_PCI_INSET_SIDE_16_45mm'),('18_REAR_BEAM_CPU_END_AND_REAR_LAP','16_CPU_VERTICAL_SIDE_FLUSH_TO_BEAM'),('18_REAR_BEAM_PCI_TAPERED_END_AND_FRONT_LAP','18_REAR_BEAM_CPU_END_AND_REAR_LAP'),('18_REAR_BEAM_PCI_TAPERED_END_AND_FRONT_LAP','07_GPU_REINFORCED_REAR_TOWER')]
    contacts=[]
    for a,b in pairs:
        m=app.measureManager.measureMinimumDistance(cs[a],cs[b]);contacts.append({'one':a,'two':b,'minimum_distance_mm':m.value*10});assert abs(m.value)<1e-5,(a,b,m.value)
    with open(OUT+'/contacts.json','w') as f:json.dump(contacts,f,indent=2)
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(45,60,31);cam.target=P(15,16,14);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Rear.png',1500,1150)
    visible={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:o.isLightBulbOn=o.component.name.startswith('18_')
    cam=view.camera;cam.eye=P(37,48,30);cam.target=P(15,25,13);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Joint_detail.png',1500,1000)
    for o in root.occurrences:o.isLightBulbOn=visible[o.component.name]
    cam=view.camera;cam.eye=P(45,60,31);cam.target=P(15,16,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v11_layout.f3d'))
    print(json.dumps(contacts))
