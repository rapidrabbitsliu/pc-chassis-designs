"""Style 1 V16: physical GPU insertion and base screw access, through Fusion MCP."""
from pathlib import Path
import adsk.core, adsk.fusion, json

ROOT = Path('D:/personal-files/docs/ChatGPT/\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f')
OUT = ROOT / 'outputs/ATX-Desk-v16'


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(
        str(ROOT / 'outputs/ATX-Desk-v15/ATX_Desk_v15_gpu_fit.f3d')))
    assert doc
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    components = {o.component.name: o.component for o in root.occurrences}
    P = adsk.core.Point3D.create
    V = adsk.core.ValueInput.createByString
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

    def box(component, low, high, name):
        x0, y0, z0 = low
        x1, y1, z1 = high
        plane_input = component.constructionPlanes.createInput()
        plane_input.setByOffset(component.xYConstructionPlane, V(f'{z0} mm'))
        sketch = component.sketches.add(component.constructionPlanes.add(plane_input))
        sketch.name = name + ' profile'
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            line = sketch.sketchCurves.sketchLines.addByTwoPoints(
                sketch.modelToSketchSpace(P(a[0]/10, a[1]/10, z0/10)),
                sketch.modelToSketchSpace(P(b[0]/10, b[1]/10, z0/10)))
            line.isFixed = True
        assert sketch.profiles.count == 1
        extrude = component.features.extrudeFeatures.createInput(sketch.profiles.item(0), CUT)
        extrude.participantBodies = [component.bRepBodies.item(0)]
        extrude.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(f'{z1-z0} mm')),
                                adsk.fusion.ExtentDirections.PositiveExtentDirection)
        feature = component.features.extrudeFeatures.add(extrude)
        feature.name = name
        sketch.isVisible = False

    def insert_hole(component, x):
        plane_input = component.constructionPlanes.createInput()
        plane_input.setByOffset(component.xYConstructionPlane, V('275.5 mm'))
        sketch = component.sketches.add(component.constructionPlanes.add(plane_input))
        sketch.name = 'V16 upper insert centre moved rearward 1.5 mm from V13'
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
            sketch.modelToSketchSpace(P(x/10, 25.1, 27.55)), 0.235)
        circle.isFixed = True
        inp = component.features.extrudeFeatures.createInput(sketch.profiles.item(0), CUT)
        inp.participantBodies = [component.bRepBodies.item(0)]
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V('6.5 mm')),
                             adsk.fusion.ExtentDirections.PositiveExtentDirection)
        component.features.extrudeFeatures.add(inp).name = 'V16 ear M3 short insert Y251'
        sketch.isVisible = False

    tower = components['07_GPU_REINFORCED_REAR_TOWER']
    upper = components['08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE']
    lower = components['08_GPU_LOWER_TWO_TAB_RECEIVER_ADJUSTABLE']
    removed = []
    for i in range(upper.features.count-1, -1, -1):
        feature = upper.features.item(i)
        if feature.name.startswith(('V14 ', 'V15 ')):
            removed.append(feature.name)
            assert feature.deleteMe()
    assert len(removed) == 4, removed
    # Original front Y244.84 -> Y246.84. Keep the original 10 mm vertical thickness.
    box(upper, (83.99, 244.83, 261.99), (154.01, 246.84, 282.01),
        'V16 retract original ear platform front 2 mm including projecting gussets')
    for x in (100, 120):
        insert_hole(upper, x)
    # The inaccessible first base screw is X158, directly below the audio socket.
    # Remove only its forward foot, keeping both rear tower posts and gusset roots supported.
    box(tower, (150, 243.99, 139.99), (174.01, 254, 148.001),
        'V16 shorten CPU-side forward foot 24 mm and remove inaccessible X158 screw')
    # User red line: shorten guide from X140 to X132; both tab slots still end at X123.
    box(lower, (132, 244.83, 147.99), (140.01, 254, 158.01),
        'V16 shorten lower tab guide to X132 for second base screw access')
    box(lower, (83.99, 244.83, 147.99), (85, 254, 158.01),
        'V16 clear opposite base screw head entry at X80')
    for name, value, comment in [
        ('v16_ear_front_retraction', 2, 'From original V13 front; vertical thickness remains 10 mm'),
        ('v16_ear_hole_rear_offset', 1.5, 'From original V13 hole centres, towards tower'),
        ('v16_lower_guide_right_x', 132, 'Expose X140 base screw; preserve both GPU metal tab slots'),
        ('v16_forward_foot_right_x', 150, 'First X158 base screw omitted; tower rear supports retained')]:
        design.userParameters.add(name, V(f'{value} mm'), 'mm', comment)

    manager = adsk.fusion.TemporaryBRepManager.get()

    def overlap(body, tool):
        target = manager.copy(body)
        assert manager.booleanOperation(target, tool, adsk.fusion.BooleanTypes.IntersectionBooleanType)
        return target.volume * 1000

    access = []
    for x in (80, 140):
        tool = manager.createCylinderOrCone(P(x/10, 24.85, 14.801), .5,
                                           P(x/10, 24.85, 31), .5)
        row = {'x_mm': x, 'y_mm': 248.5, 'driver_gauge_diameter_mm': 10,
               'z_range_mm': [148.01, 310],
               'tower_overlap_mm3': overlap(tower.bRepBodies.item(0), tool),
               'lower_receiver_overlap_mm3': overlap(lower.bRepBodies.item(0), tool),
               'assembly_sequence': 'Fasten tower base before fitting upper ear ledge and GPU'}
        assert max(row['tower_overlap_mm3'], row['lower_receiver_overlap_mm3']) < .0001, row
        access.append(row)
    bores = []
    for face in upper.bRepBodies.item(0).faces:
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if cylinder and abs(cylinder.radius*20-4.7) < .001 and abs(cylinder.axis.z) > .99:
            bores.append([cylinder.origin.x*10, cylinder.origin.y*10])
    assert len(bores) == 2 and all(abs(point[1]-251) < .0001 for point in bores), bores
    base_holes = []
    for face in tower.bRepBodies.item(0).faces:
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if cylinder and abs(cylinder.radius*20-3.4) < .001 and abs(cylinder.axis.z) > .99:
            base_holes.append([cylinder.origin.x*10, cylinder.origin.y*10])
    assert sorted(round(p[0], 4) for p in base_holes) == [80, 140], base_holes

    OUT.mkdir(exist_ok=True)
    (OUT/'Raw_STL').mkdir(exist_ok=True)
    old = {p['name']: p for p in json.loads((ROOT/'outputs/ATX-Desk-v15/parts.json').read_text())}
    parts = []
    objects = adsk.core.ObjectCollection.create()
    reference_objects = adsk.core.ObjectCollection.create()
    for occurrence in root.occurrences:
        component = occurrence.component
        name = component.name
        if name.startswith('REF_'):
            if name in ('REF_GPU_FANS_TO_MINUS_X', 'REF_BOARD_304.8x243.84_NUMBERED_HOLES',
                        'REF_PSU_FLAT_CENTERED_150x140x86') or name.startswith('REF_CASE_FAN_'):
                reference_objects.add(occurrence)
            continue
        assert component.bRepBodies.count == 1
        body = component.bRepBodies.item(0)
        assert body.isSolid and body.lumps.count == 1, name
        bb = body.preciseBoundingBox
        parts.append({'name': name, 'native_size_mm': [
            (getattr(bb.maxPoint, k)-getattr(bb.minPoint, k))*10 for k in 'xyz'],
            'volume_mm3': body.volume*1000})
        options = design.exportManager.createSTLExportOptions(body, str(OUT/'Raw_STL'/(name+'.stl')))
        options.isBinaryFormat = True
        assert design.exportManager.execute(options)
        objects.add(occurrence)
        reference_objects.add(occurrence)
    assert len(parts) == 17
    changed = [p['name'] for p in parts if abs(p['volume_mm3']-old[p['name']]['volume_mm3']) > .001]
    assert set(changed) == {tower.name, upper.name, lower.name}, changed
    inp = design.createInterferenceInput(objects)
    inp.areCoincidentFacesIncluded = False
    structural = design.analyzeInterference(inp)
    assert structural.count == 0, structural.count
    inp = design.createInterferenceInput(reference_objects)
    inp.areCoincidentFacesIncluded = False
    hardware = design.analyzeInterference(inp)
    overlaps = [{'one': hardware.item(i).entityOne.parentComponent.name,
                 'two': hardware.item(i).entityTwo.parentComponent.name,
                 'volume_mm3': hardware.item(i).interferenceBody.volume*1000}
                for i in range(hardware.count)]
    bad = [(design.timeline.item(i).name, design.timeline.item(i).errorOrWarningMessage)
           for i in range(design.timeline.count)
           if design.timeline.item(i).healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not bad, bad
    data = {'style': 1, 'version': 'V16', 'changed_parts': changed,
            'unchanged_from_v15': 14, 'upper_platform_front_y_mm': 246.84,
            'upper_platform_retraction_from_v13_mm': 2, 'platform_vertical_thickness_mm': 10,
            'upper_hole_offset_from_v13_towards_tower_mm': 1.5, 'hole_centres_xy_mm': bores,
            'nut_OD5_front_wall_mm': 1.66, 'base_holes_xy_mm': base_holes,
            'omitted_base_hole_xy_mm': [158, 248.5], 'forward_foot_x_range_mm': [70, 150],
            'tower_overall_width_unchanged_mm': 104, 'lower_guide_x_range_mm': [85, 132],
            'metal_tab_slot_centres_x_mm_unchanged': [96, 116], 'nominal_head_channel_mm': 8.2,
            'driver_access': access, 'structural_interferences': 0,
            'hardware_reference_interferences': overlaps, 'timeline_health': 'healthy',
            'physical_retest_required': True,
            'note': 'Audio jack has no detailed CAD solid. Physical socket clearance remains to be tested. '
                    'Fasten both base screws before installing upper ledge and GPU. Existing unused '
                    'X158 insert in rear load beam can remain; do not reprint rear beam.'}
    (OUT/'parts.json').write_text(json.dumps(parts, indent=2), encoding='utf-8')
    (OUT/'verification.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    visibility = {o.component.name: o.isLightBulbOn for o in root.occurrences}
    for o in root.occurrences:
        o.isLightBulbOn = o.component.name.startswith(('07_', '08_'))
    viewport = app.activeViewport
    camera = viewport.camera
    camera.isSmoothTransition = False
    camera.eye = P(31, 2, 32)
    camera.target = P(12.2, 25.5, 22)
    camera.upVector = adsk.core.Vector3D.create(0, 0, 1)
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    assert viewport.saveAsImageFile(str(OUT/'GPU_Bracket_Front.png'), 1500, 1100)
    for o in root.occurrences:
        o.isLightBulbOn = visibility[o.component.name]
    camera = viewport.camera
    camera.eye = P(48, 48, 36)
    camera.target = P(15, 12, 14)
    camera.isFitView = True
    viewport.camera = camera
    viewport.refresh()
    assert viewport.saveAsImageFile(str(OUT/'Assembly.png'), 1500, 1150)
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(
        str(OUT/'ATX_Desk_v16_gpu_access.f3d')))
    print(json.dumps(data))
