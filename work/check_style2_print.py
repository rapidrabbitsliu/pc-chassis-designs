"""Dependency-free STL print-envelope check, units inferred against CAD dimensions.
Checks per-part geometry plus 5 mm brim on each side; not a slicing/strength test.
"""
import pathlib, struct, math, json, sys
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'/(sys.argv[1] if len(sys.argv)>1 else 'Style2-v02')

def hull(points):
    points=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in points:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(points):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]

results=[]
for part in json.loads((OUT/'parts.json').read_text(encoding='utf-8')):
    name=part['name'];data=(OUT/'Raw_STL'/(name+'.stl')).read_bytes()
    n=struct.unpack_from('<I',data,80)[0];assert len(data)==84+50*n
    verts=[];triangles=[]
    for i in range(n):
        vals=struct.unpack_from('<12fH',data,84+50*i)
        tri=[tuple(vals[j:j+3]) for j in (3,6,9)]
        verts+=tri;triangles.append(tri)
    extents=[max(v[k] for v in verts)-min(v[k] for v in verts) for k in range(3)]
    scale=min((1,10),key=lambda f:sum(abs(extents[k]*f-part['native_size_mm'][k]) for k in range(3)))
    assert max(abs(extents[k]*scale-part['native_size_mm'][k]) for k in range(3))<.1
    edges=Counter()
    for tri in triangles:
        keys=[tuple(round(t,5) for t in v) for v in tri]
        for a,b in zip(keys,keys[1:]+keys[:1]):edges[tuple(sorted((a,b)))]+=1
    assert all(count==2 for count in edges.values()),name
    # Largest deliberate flat face: uprights/crossbars rear; side braces outer face.
    normal=1 if name.startswith(('01_','03_','04_')) else 0 if name.startswith('05_') else 2
    axes=[k for k in range(3) if k!=normal]
    poly=hull([(v[axes[0]]*scale,v[axes[1]]*scale) for v in verts])
    best=None
    for step in range(720):
        angle=step*math.pi/720;c=math.cos(angle);s=math.sin(angle)
        xx=[x*c-y*s for x,y in poly];yy=[x*s+y*c for x,y in poly]
        dims=[max(xx)-min(xx),max(yy)-min(yy)]
        if best is None or max(dims)<max(best[1]):best=(step*.25,dims)
    dims=[v+10 for v in best[1]]
    assert max(dims)<=256,(name,dims)
    results.append({'name':name,'flat_face_normal_axis':'XYZ'[normal],
                    'in_plane_rotation_deg':best[0],
                    'footprint_including_5mm_brim_mm':[round(v,2) for v in dims],
                    'watertight_edge_check':True,'fits_A1_256mm':True})
(OUT/'print_envelope_checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps({'part_count':len(results),'all_fit_with_5mm_brim':True,
                  'largest_footprint_side_mm':max(max(p['footprint_including_5mm_brim_mm']) for p in results)}))
