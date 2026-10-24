"""Style 1 V15: platform extension 2 mm; insert offset remains 3 mm."""
import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f/'
OUT=ROOT+'outputs/ATX-Desk-v15'

def run(_context: str):
    app=adsk.core.Application.get()
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(ROOT+'outputs/ATX-Desk-v14/ATX_Desk_v14_gpu_fit.f3d'));assert doc
    d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    c=next(o.component for o in root.occurrences if o.component.name=='08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE')
    P=adsk.core.Point3D.create;V=adsk.core.ValueInput.createByString
    pi=c.constructionPlanes.createInput();pi.setByOffset(c.xYConstructionPlane,V('271.99 mm'))
    plane=c.constructionPlanes.add(pi);sk=c.sketches.add(plane);sk.name='V15 shorten front edge by 1 mm'
    coords=[(83.99,241.83),(154.01,241.83),(154.01,242.84),(83.99,242.84)]
    for a,b in zip(coords,coords[1:]+coords[:1]):
        q=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(P(a[0]/10,a[1]/10,27.199)),sk.modelToSketchSpace(P(b[0]/10,b[1]/10,27.199)));q.isFixed=True
    assert sk.profiles.count==1
    ei=c.features.extrudeFeatures.createInput(sk.profiles.item(0),adsk.fusion.FeatureOperations.CutFeatureOperation);ei.participantBodies=[c.bRepBodies.item(0)]
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V('10.02 mm')),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    f=c.features.extrudeFeatures.add(ei);f.name='V15 platform extension 2 mm, holes remain shifted 3 mm';sk.isVisible=False
    d.userParameters.add('v15_platform_extension',V('2 mm'),'mm','User revised platform only; upper insert centres unchanged')
    previous=json.load(open(ROOT+'outputs/ATX-Desk-v14/parts.json'))
    old={p['name']:p for p in previous};parts=[];objects=adsk.core.ObjectCollection.create()
    os.makedirs(OUT+'/Raw_STL',exist_ok=True)
    for o in root.occurrences:
        comp=o.component;n=comp.name
        if n.startswith('REF_'):continue
        assert comp.bRepBodies.count==1;b=comp.bRepBodies.item(0);assert b.isSolid and b.lumps.count==1
        bb=b.preciseBoundingBox
        parts.append({'name':n,'native_size_mm':[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in 'xyz'],'volume_mm3':b.volume*1000})
        opt=d.exportManager.createSTLExportOptions(b,OUT+'/Raw_STL/'+n+'.stl');opt.isBinaryFormat=True;assert d.exportManager.execute(opt)
        objects.add(o)
    changed=[p['name'] for p in parts if abs(p['volume_mm3']-old[p['name']]['volume_mm3'])>.001]
    assert changed==['08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE'],changed
    delta=old[changed[0]]['volume_mm3']-next(p['volume_mm3'] for p in parts if p['name']==changed[0]);assert abs(delta-700)<.001,delta
    bores=[]
    for face in c.bRepBodies.item(0).faces:
        cy=adsk.core.Cylinder.cast(face.geometry)
        if cy and abs(cy.radius*20-4.7)<.01 and abs(cy.axis.z)>.99:bores.append([cy.origin.x*10,cy.origin.y*10])
    assert len(bores)==2 and all(abs(p[1]-246.5)<.001 for p in bores),bores
    inp=d.createInterferenceInput(objects);inp.areCoincidentFacesIncluded=False;result=d.analyzeInterference(inp);assert result.count==0
    bad=[d.timeline.item(i).name for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v15_gpu_fit.f3d'))
    data={'style':1,'version':'V15','platform_extension_mm':2,'platform_front_y_mm':242.84,'hole_offset_y_mm':-3,'hole_centres_xy_mm':bores,'nut_OD5_front_wall_mm':1.16,'unchanged_parts_from_v14':16,'changed_parts_from_v14':changed,'material_removed_mm3':delta,'structure_interferences':0,'timeline_health':'healthy','channel_nominal_mm':8.2,'head_sweep_check_inherited_from_v14':'P12 unchanged; all four continuous 7.5 mm gauge checks remain applicable','simplified_gpu_envelope_overlap_y_mm':1,'physical_retest_required':True}
    open(OUT+'/parts.json','w').write(json.dumps(parts,indent=2));open(OUT+'/verification.json','w').write(json.dumps(data,indent=2))
    vis={o.component.name:o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:o.isLightBulbOn=o.component.name.startswith(('07_','08_'))
    view=app.activeViewport;cam=view.camera;cam.isSmoothTransition=False;cam.eye=P(29,2,32);cam.target=P(12.2,25.5,22);cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType;cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/GPU_Bracket_Front.png',1500,1100)
    for o in root.occurrences:o.isLightBulbOn=vis[o.component.name]
    cam=view.camera;cam.eye=P(48,48,36);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Assembly.png',1500,1150)
    print(json.dumps(data))
