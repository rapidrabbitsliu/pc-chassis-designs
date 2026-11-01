from pathlib import Path
import numpy as np,json,struct,collections,math,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/ATX-Desk-v24'
(OUT/'PRINT_STL').mkdir(exist_ok=True);(OUT/'REPRINT_STL').mkdir(exist_ok=True)
def rot(axis,angle):
 a=math.radians(angle);c,s=math.cos(a),math.sin(a)
 return np.array([[1,0,0],[0,c,-s],[0,s,c]]) if axis=='x' else np.array([[c,-s,0],[s,c,0],[0,0,1]])
changed=json.loads((OUT/'verification.json').read_text())['changed_parts'];checks=[]
for meta in json.loads((OUT/'parts.json').read_text()):
 n=meta['name'];raw=(OUT/'Raw_STL'/(n+'.stl')).read_bytes();cnt=struct.unpack_from('<I',raw,80)[0]
 dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')]);t=np.frombuffer(raw,dtype=dt,offset=84,count=cnt)['v'].astype(float)
 scale=np.array(meta['native_size_mm'])/np.ptp(t,axis=(0,1));assert np.ptp(scale)<.01;t*=np.mean(scale)
 if n.startswith(('10_','12_','20_','07_GPU_INTEGRATED_')):t=t@rot('x',-90).T
 elif n.startswith('16_'):t=t@np.array([[0,1,0],[0,0,1],[1,0,0]]).T
 if n.startswith('16_PCI'):t=t@rot('x',math.degrees(math.atan(16.45/140))).T
 if n.startswith(('18_','20_','10_')):t=t@rot('x',180).T
 if n.startswith(('04_','18_','20_')):t=t@rot('z',45).T
 if n.startswith('19_'):t=t@rot('z',90).T
 t-=t.min(axis=(0,1));size=t.max(axis=(0,1));vol=np.sum(t[:,0]*np.cross(t[:,1],t[:,2]))/6
 assert abs(vol-meta['volume_mm3'])/meta['volume_mm3']<.003
 edges=collections.Counter()
 for tri in t:
  p=[tuple(np.round(v,4)) for v in tri]
  for a,b in zip(p,p[1:]+p[:1]):edges[tuple(sorted((a,b)))]+=1
 assert all(x==2 for x in edges.values()),n
 normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normals/=np.linalg.norm(normals,axis=1)[:,None]
 data=bytearray(('V24 mm '+n).encode()[:80].ljust(80,b' ')+struct.pack('<I',cnt))
 for tri,no in zip(t,normals):data+=struct.pack('<12fH',*no,*tri.reshape(-1),0)
 (OUT/'PRINT_STL'/(n+'.stl')).write_bytes(data)
 if n in changed:(OUT/'REPRINT_STL'/(n+'.stl')).write_bytes(data)
 checks.append({'part':n,'closed_mesh':True,'print_size_mm':size.tolist(),'volume_error_pct':abs(vol-meta['volume_mm3'])/meta['volume_mm3']*100})
(OUT/'mesh_checks.json').write_text(json.dumps(checks,indent=2))
s=(ROOT/'work/arrange_v23_all_parts.py').read_text(encoding='utf-8').replace('v23','v24').replace('V23','V24')
(ROOT/'work/arrange_v24_all_parts.py').write_text(s,encoding='utf-8')
print(json.dumps({'mesh_count':len(checks),'reprint_count':len(changed)}))
