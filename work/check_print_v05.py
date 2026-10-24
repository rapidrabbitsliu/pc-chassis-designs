from pathlib import Path
import struct,math,json
r={}
for version in ('04','05'):
    p=Path(f'outputs/Single-Bracket-v{version}/PRINT_Bracket_v{version}_mm.stl');s=p.read_bytes();n=struct.unpack_from('<I',s,80)[0];area=0;bed=0
    for i in range(n):
        a=struct.unpack_from('<12fH',s,84+i*50)
        if a[2]<-.999:
            p,q,v=a[3:6],a[6:9],a[9:12];u=[q[k]-p[k] for k in range(3)];w=[v[k]-p[k] for k in range(3)]
            cross=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];t=math.sqrt(sum(x*x for x in cross))/2
            if min(p[2],q[2],v[2])>.01:area+=t
            else:bed+=t
    r[version]={'elevated_horizontal_downward_faces_mm2':area,'bed_contact_mm2':bed}
print(json.dumps(r));Path('outputs/Single-Bracket-v05/print_geometry_check.json').write_text(json.dumps(r,indent=2))
