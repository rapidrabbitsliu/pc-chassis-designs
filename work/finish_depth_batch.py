from pathlib import Path
import struct,json,zipfile,shutil
out=Path(r'C:\Users\liu\Documents\Codex\2026-10-18\referenced-chatgpt-conversation-this-is-an\outputs\Hook-Fit-v03')
checks=[];combined=[]
for tag,off in [('4.0',0),('4.2',42)]:
    raw=(out/f'raw_depth_{tag}.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0]
    assert len(raw)==84+50*n
    triangles=[];allpts=[];edges={};vol=0
    for i in range(n):
        vals=struct.unpack_from('<12fH',raw,84+50*i)
        normal=(-vals[2],vals[1],vals[0])
        pts=[(-vals[k+2]+off+16,vals[k+1]-7,vals[k]+3) for k in (3,6,9)]
        allpts+=pts
        triangles.append((normal,pts))
        a,b,c=pts
        vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        q=[tuple(round(x,4) for x in p) for p in pts]
        for a,b in zip(q,q[1:]+q[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append((a,b))
    assert all(len(v)==2 and v[0]==v[1][::-1] for v in edges.values())
    expected=1677.488 if tag=='4.0' else 1684.152
    assert abs(vol-expected)<.05,(vol,expected)
    def write(p,tris):
        with p.open('wb') as f:
            f.write(b'Fusion export; rigid print transform; mm; recessed depth label'.ljust(80,b' '));f.write(struct.pack('<I',len(tris)))
            for normal,pts in tris:f.write(struct.pack('<12fH',*normal,*(x for p in pts for x in p),0))
    write(out/f'PRINT_depth_{tag}mm.stl',triangles)
    # Position on same bed, 10 mm edge-to-edge gap.
    shift=0 if tag=='4.0' else 42
    combined.extend((normal,[(x+shift,y,z) for x,y,z in pts]) for normal,pts in triangles)
    checks.append({'depth_mm':float(tag),'bounds_mm':[max(p[k] for p in allpts)-min(p[k] for p in allpts) for k in range(3)],'volume_mm3':vol,'triangles':n,'closed':True})
write(out/'PRINT_BOTH_4.0_4.2mm.stl',combined)
(out/'mesh_check.json').write_text(json.dumps(checks,indent=2))
(out/'HookDepthBatch/HookDepthBatch.manifest').write_text(json.dumps({'autodeskProduct':'Fusion360','type':'script','author':'CAD project','description':{'':'Two-hook depth coupons, recessed 4.0 and 4.2 labels'},'version':'0.3.0','runOnStartup':False,'supportedOS':'windows|mac'},indent=2))
print(json.dumps(checks))
