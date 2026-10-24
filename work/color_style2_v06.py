import adsk.core,adsk.fusion,json

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    out='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/outputs/Style2-v06'
    source=d.appearances.itemByName('Style2 frame');assert source
    palette={}
    for name,rgb in [('PRINT_FRAME_BLUE',(35,120,220)),('REFERENCE_HARDWARE_GRAY',(170,180,190))]:
        a=d.appearances.itemByName(name)
        if not a:a=d.appearances.addByCopy(source,name)
        for key in ('opaque_albedo','surface_albedo'):
            cp=adsk.core.ColorProperty.cast(a.appearanceProperties.itemById(key))
            assert cp;cp.value=adsk.core.Color.create(*rgb,255)
        palette[name]=a
    report=[]
    for o in d.rootComponent.occurrences:
        ref=o.component.name.startswith('REF_');o.isLightBulbOn=True
        for b in o.component.bRepBodies:
            # Assign to the persistent RESULT body, not the source inside the base feature.
            b.appearance=palette['REFERENCE_HARDWARE_GRAY' if ref else 'PRINT_FRAME_BLUE']
            b.opacity=.25 if ref else 1
            report.append({'name':o.component.name,'reference':ref,'opacity':b.opacity,'appearance':b.appearance.name})
    assert sum(not r['reference'] for r in report)==16
    assert all(r['appearance']==('REFERENCE_HARDWARE_GRAY' if r['reference'] else 'PRINT_FRAME_BLUE') for r in report)
    view=app.activeViewport;cam=view.camera;p=adsk.core.Point3D.create
    cam.eye=p(-44,65,42);cam.target=p(12,2,15);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;view.camera=cam;view.refresh()
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'/Style2_V06_Colored.f3d'))
    assert view.saveAsImageFile(out+'/Colored_Structure.png',1600,1400)
    open(out+'/appearance_legend.json','w',encoding='utf-8').write(json.dumps(report,indent=2))
    print(json.dumps({'print_parts_blue':16,'reference_bodies_gray':sum(r['reference'] for r in report),'reference_opacity':.25,'file':'Style2_V06_Colored.f3d'}))
