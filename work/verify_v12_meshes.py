from pathlib import Path
import struct,math,json,collections,csv
out=Path('outputs/ATX-Desk-v12-print-review');dest=out/'PRINT_STL';dest.mkdir(exist_ok=True)
parts=json.loads((out/'parts.json').read_text(encoding='utf-8'));checks=[]
for e in parts:
    tag=e['name'];raw=(out/'Raw_STL'/(tag+'.stl')).read_bytes();n=struct.unpack_from('<I',raw,80)[0];assert len(raw)==84+50*n
    tris=[];rawpts=[]
    for i in range(n):
        a=struct.unpack_from('<12fH',raw,84+i*50);vs=[a[k:k+3] for k in (3,6,9)];tris.append((a[:3],vs));rawpts.extend(vs)
    sz=[max(q[k] for q in rawpts)-min(q[k] for q in rawpts) for k in range(3)]
    ratio=[e['native_size_mm'][k]/sz[k] for k in range(3)];scale=sum(ratio)/3
    assert max(abs(r-scale) for r in ratio)<.01,(tag,ratio)
    assert min(abs(scale-1),abs(scale-10))<.01,(tag,scale)
    scale=1 if abs(scale-1)<.01 else 10
    a=math.radians(e['angle_deg']);co=math.cos(a);si=math.sin(a)
    def rot(p):
        x,y,z=p
        if e['orientation']=='xz':x,y,z=x,z,-y
        elif e['orientation']=='yz':x,y,z=y,z,x
        return co*x-si*y,si*x+co*y,z
    transformed=[(rot(no),[tuple(t*scale for t in rot(v)) for v in vs]) for no,vs in tris]
    pts=[p for no,vs in transformed for p in vs];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)];size=[hi[k]-lo[k] for k in range(3)]
    assert size[0]+2*e['brim_mm']<=256.001 and size[1]+2*e['brim_mm']<=256.001,(tag,size,e['brim_mm'])
    packed=bytearray(('V12 PRINT FIT TRIAL mm '+tag).encode('ascii')[:80].ljust(80,b' ')+struct.pack('<I',n));vol=0;edges=collections.defaultdict(list);bedarea=0;downarea=0
    for normal,vs in transformed:
        vs=[tuple(p[k]-lo[k] for k in range(3)) for p in vs];packed+=struct.pack('<12fH',*normal,*(t for p in vs for t in p),0)
        A,B,C=vs;vol+=(A[0]*(B[1]*C[2]-B[2]*C[1])+A[1]*(B[2]*C[0]-B[0]*C[2])+A[2]*(B[0]*C[1]-B[1]*C[0]))/6
        points=[tuple(round(t,4) for t in p) for p in vs]
        for aa,bb in zip(points,points[1:]+points[:1]):edges[tuple(sorted((aa,bb)))].append((aa,bb))
        if normal[2]<-.99:
            u=[B[k]-A[k] for k in range(3)];v=[C[k]-A[k] for k in range(3)];area=math.sqrt(sum(t*t for t in (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])))/2
            if max(p[2] for p in vs)<.02:bedarea+=area
            else:downarea+=area
    bad=sum(1 for x in edges.values() if len(x)!=2 or x[0]!=x[1][::-1]);assert bad==0,(tag,bad)
    assert vol>0 and abs(vol-e['volume_mm3'])<max(1,e['volume_mm3']*.003),(tag,vol,e['volume_mm3'])
    (dest/(tag+'.stl')).write_bytes(packed)
    checks.append(dict(name=tag,print_xyz_mm=[round(x,3) for x in size],brim_mm=e['brim_mm'],bed_with_brim_mm=[round(size[k]+2*e['brim_mm'],3) for k in (0,1)],closed_manifold=True,volume_mm3=round(vol,2),bed_contact_mm2=round(bedarea,2),elevated_downward_horizontal_area_mm2=round(downarea,2),orientation=e['orientation'],angle_deg=e['angle_deg'],note=e['note']))
(out/'print_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
with (out/'print_parts.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['part','print_X_mm','print_Y_mm','print_Z_mm','brim_mm','bed_with_brim_X_mm','bed_with_brim_Y_mm','note'])
    for e in checks:w.writerow([e['name'],*e['print_xyz_mm'],e['brim_mm'],*e['bed_with_brim_mm'],e['note']])
print(json.dumps({'parts':len(checks),'all_fit_with_brim':True,'all_closed_manifold':True,'max_bed_footprint_with_brim_mm':[max(e['bed_with_brim_mm'][k] for e in checks) for k in (0,1)],'parts_requiring_support_review':[e['name'] for e in checks if e['elevated_downward_horizontal_area_mm2']>10]}))
