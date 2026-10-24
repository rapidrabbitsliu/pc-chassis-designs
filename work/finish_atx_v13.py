import adsk.core,adsk.fusion,json,os
ROOT='D:/personal-files/docs/ChatGPT/电脑上洞洞板/'

def run(_context: str):
    # Reuse the same documented sketch/extrude helpers, without rebuilding the design.
    source=open(ROOT+'work/build_atx_v13.py',encoding='utf-8').read()
    helpers=source[source.index('    def plane('):source.index('    # A single full-depth extrusion')]
    scope={'adsk':adsk,'json':json,'os':os,'ROOT':ROOT}
    code='def finish():\n'
    code+='    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent\n'
    code+='    V=adsk.core.ValueInput.createByString;P=adsk.core.Point3D.create\n'
    code+='    NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation;JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation;CUT=adsk.fusion.FeatureOperations.CutFeatureOperation\n'
    code+='    cs={o.component.name:o.component for o in root.occurrences}\n'
    code+=helpers
    code+='''    fan=cs['20_ONE_PIECE_DUAL_140_FAN_RAIL_284mm']
    for tag,x0 in [('GPU',12.4),('CPU',156.4)]:
        panel=cs['10_'+tag+'_140_FAN_MOUNT']
        for x in (x0+20,x0+120):
            # Panel component carries a -50 mm assembly offset inherited from V06.
            box(panel,x-6,-19,210,x+6,-9,213,JOIN,'Integral 3 mm fan panel fastening tab')
            circle(panel,'z',210,x,-14,3.4,3.01,CUT,'M3x6 fan panel tab clearance')
            box(fan,x-6,-19,148,x+6,-9,160,JOIN,'Integral fan panel tab support pad')
            circle(fan,'z',153.5,x,-14,4.7,6.51,CUT,'H4.5 insert for fan panel M3x6 fastening')
    OUT=ROOT+'outputs/ATX-Desk-v13'
    parts=[];objs=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        n=o.component.name;c=o.component
        if not n.startswith('REF_'):
            assert c.bRepBodies.count==1,(n,c.bRepBodies.count)
            b=c.bRepBodies.item(0);assert b.isSolid and b.lumps.count==1
            bb=b.preciseBoundingBox;dims=[(getattr(bb.maxPoint,k)-getattr(bb.minPoint,k))*10 for k in 'xyz']
            parts.append({'name':n,'native_size_mm':dims,'volume_mm3':b.volume*1000})
            if n.startswith(('10_','20_')):
                op=d.exportManager.createSTLExportOptions(b,OUT+'/Raw_STL/'+n+'.stl');op.isBinaryFormat=True;assert d.exportManager.execute(op)
            objs.add(o)
        elif n in ('REF_BOARD_304.8x243.84_NUMBERED_HOLES','REF_GPU_FANS_TO_MINUS_X','REF_PSU_FLAT_CENTERED_150x140x86') or n.startswith('REF_CASE_FAN_'):objs.add(o)
    ii=d.createInterferenceInput(objs);ii.areCoincidentFacesIncluded=False;rr=d.analyzeInterference(ii)
    inter=[{'one':rr.item(i).entityOne.parentComponent.name,'two':rr.item(i).entityTwo.parentComponent.name,'volume_mm3':rr.item(i).interferenceBody.volume*1000} for i in range(rr.count)]
    assert not inter,inter
    bad=[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
    open(OUT+'/parts.json','w').write(json.dumps(parts,indent=2))
    open(OUT+'/interference.json','w').write(json.dumps({'count':0,'interferences':[]},indent=2))
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(OUT+'/ATX_Desk_v13_one_piece.f3d'))
    view=app.activeViewport;cam=view.camera;cam.eye=P(48,48,36);cam.target=P(15,12,14);cam.isFitView=True;view.camera=cam;view.refresh()
    assert view.saveAsImageFile(OUT+'/Assembly.png',1500,1150)
    print(json.dumps({'parts':len(parts),'panel_fastening_tabs':4,'interferences':len(inter),'timeline_health':'healthy'}))
'''
    exec(compile(code,'V13_finish','exec'),scope);scope['finish']()
