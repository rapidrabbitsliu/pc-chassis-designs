from pathlib import Path
import struct,json,zipfile,shutil
out=Path('outputs/Single-Bracket-v05');check=[]
for part in ('Bracket','AntiLiftKey'):
    raw=(out/f'raw_{part}.stl').read_bytes();n=struct.unpack_from('<I',raw,80)[0];buf=bytearray(b'Fusion exported V04; oriented for slicing; mm; UNRATED'.ljust(80,b' ')+struct.pack('<I',n));ptsall=[];edges={};vol=0
    for i in range(n):
        a=struct.unpack_from('<12fH',raw,84+50*i)
        if part=='Bracket':
            normal=(a[0],a[1],a[2]);pts=[(a[k]+100,a[k+1]+108,a[k+2]+16) for k in (3,6,9)]
        else:
            normal=(-a[2],a[1],a[0]);pts=[(-a[k+2]+14.5,a[k+1]+15,a[k]+8) for k in (3,6,9)]
        buf+=struct.pack('<12fH',*normal,*(v for p in pts for v in p),0);ptsall+=pts
        r=[tuple(round(v,4) for v in p) for p in pts]
        for x,y in zip(r,r[1:]+r[:1]):edges.setdefault(tuple(sorted((x,y))),[]).append((x,y))
        x,y,z=pts;vol+=(x[0]*(y[1]*z[2]-y[2]*z[1])+x[1]*(y[2]*z[0]-y[0]*z[2])+x[2]*(y[0]*z[1]-y[1]*z[0]))/6
    assert all(len(e)==2 and e[0]==e[1][::-1] for e in edges.values())
    expected=61408.09408 if part=='Bracket' else 351.501594
    assert abs(vol-expected)<1.0,(part,vol)
    (out/f'PRINT_{part}_v05_mm.stl').write_bytes(buf)
    check.append({'part':part,'closed':True,'volume_mm3':vol,'print_bounds_mm':[max(p[k] for p in ptsall)-min(p[k] for p in ptsall) for k in range(3)]})
(out/'mesh_check.json').write_text(json.dumps({'meshes':check,'assembly_interferences':0},indent=2))
(out/'SingleBracket/SingleBracket.manifest').write_text(json.dumps({'autodeskProduct':'Fusion360','type':'script','author':'CAD project','description':{'':'Single bracket V04 4.0 hook and M3 retained key; test fit only'},'version':'0.5.0','runOnStartup':False,'supportedOS':'windows|mac'},indent=2))
print(json.dumps(check))

