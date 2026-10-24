from pathlib import Path
import struct, math, json, collections, zipfile

out=Path('outputs/ATX-Desk-v01')
data=json.loads((out/'geometry.json').read_text('utf-8'))
checks=[]
for entry in data['parts']:
    tag=entry['part']; raw=(out/('raw_'+tag+'.stl')).read_bytes()
    count=struct.unpack_from('<I',raw,80)[0]
    assert len(raw)==84+50*count
    mode=entry['orientation']
    if tag.startswith('01_Side_L'):mode='yz_flip'
    if tag=='09_GPU_TailTower':mode='xy'
    if tag=='10_GPU_TailSlider':mode='xz'
    angle=math.radians(entry.get('angle_deg',0));co=math.cos(angle);si=math.sin(angle)
    def transform(p):
        x,y,z=p
        if mode=='yz':return y,z,x
        if mode=='yz_flip':return y,-z,-x
        if mode=='xz':return x,z,-y
        return co*x-si*y,si*x+co*y,z
    triangles=[];points=[]
    for i in range(count):
        row=struct.unpack_from('<12fH',raw,84+50*i)
        normal=transform(row[:3]);verts=[transform(row[k:k+3]) for k in (3,6,9)]
        triangles.append((normal,verts));points.extend(verts)
    lo=[min(p[k] for p in points) for k in range(3)]
    hi=[max(p[k] for p in points) for k in range(3)]
    size=[hi[k]-lo[k] for k in range(3)]
    assert size[0]<=246 and size[1]<=246,(tag,size) # >=5 mm bed margin each side
    edges=collections.defaultdict(list);vol=0;bedarea=0;downarea=0
    packed=bytearray(('Fusion V01; mm; '+tag).encode('ascii').ljust(80,b' ')+struct.pack('<I',count))
    for normal,verts in triangles:
        verts=[tuple(p[k]-lo[k] for k in range(3)) for p in verts]
        packed+=struct.pack('<12fH',*normal,*(q for p in verts for q in p),0)
        a,b,c=verts
        vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
        rounded=[tuple(round(q,4) for q in p) for p in verts]
        for a,b in zip(rounded,rounded[1:]+rounded[:1]):edges[tuple(sorted((a,b)))].append((a,b))
        if normal[2]<-.999:
            a,b,c=verts;u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
            ar=math.sqrt(sum(q*q for q in (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])))/2
            if max(p[2] for p in verts)<.02:bedarea+=ar
            else:downarea+=ar
    invalid=sum(1 for items in edges.values() if len(items)!=2 or items[0]!=items[1][::-1])
    assert invalid==0,(tag,invalid)
    assert vol>0 and abs(vol-entry['volume_mm3'])<max(1,vol*.002),(tag,vol,entry['volume_mm3']) # <=0.2% tessellation tolerance
    (out/('PRINT_'+tag+'.stl')).write_bytes(packed)
    checks.append(dict(part=tag,triangles=count,closed_manifold=True,consistent_normals=True,volume_mm3=vol,
                       print_bounds_mm=size,bed_contact_mm2=bedarea,elevated_horizontal_down_faces_mm2=downarea,
                       print_orientation=mode,bed_rotation_deg=entry.get('angle_deg',0)))
(out/'mesh_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps({'parts':len(checks),'all_closed_manifold':True,'all_fit_256_bed_with_5mm_margin':True,
                  'solid_volume_cm3':sum(c['volume_mm3'] for c in checks)/1000,
                  'max_print_xy_mm':[max(c['print_bounds_mm'][k] for c in checks) for k in (0,1)]}))
