from pathlib import Path
import base64, collections, json, subprocess, sys, zipfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/ATX-Desk-v13'
ledger=json.loads((OUT/'manual_insert_ledger.json').read_text(encoding='utf-8'))
parts=json.loads((OUT/'manual_part_index.json').read_text(encoding='utf-8'))
byid={v['id']:n for n,v in parts.items()}
actual=json.loads((OUT/'manual_cylinder_audit.json').read_text())
assert len(actual)==48
used=set()
for group in ledger['groups']:
    for point in group['points']:
        matches=[]
        for i,c in enumerate(actual):
            if c['part']!=byid[group['part']] or abs(c['diameter']-float(group['pilot_mm']))>.01:continue
            p=np.array(point);origin=np.array(c['origin']);axis=np.array(c['axis'])
            perpendicular=(p-origin)-np.dot(p-origin,axis)*axis
            if np.linalg.norm(perpendicular)<.02 and np.all(p>=np.array(c['min'])-.02) and np.all(p<=np.array(c['max'])+.02):matches.append(i)
        assert len(matches)==1,(group['id'],point,matches)
        assert matches[0] not in used
        used.add(matches[0])
assert len(used)==48
validator=Path('C:/Users/liu/.codex/skills/chassis-assembly-manual/scripts/validate_manual.py')
run=subprocess.run([sys.executable,str(validator),str(OUT/'Style1_V13_Assembly_Manual.html'),'--parts','17','--steps','13'],capture_output=True,text=True,encoding='utf-8',check=True)
structure=json.loads(run.stdout)
from html.parser import HTMLParser
class Images(HTMLParser):
    def __init__(self):super().__init__();self.images=[]
    def handle_starttag(self,tag,attrs):
        if tag=='img':self.images.append(dict(attrs)['src'])
parser=Images();parser.feed((OUT/'Style1_V13_Assembly_Manual.html').read_text(encoding='utf-8'))
import io
for src in parser.images:
    payload=base64.b64decode(src.split(',',1)[1],validate=True)
    im=Image.open(io.BytesIO(payload));im.verify()
report=dict(version='Style 1 V13',date='2026-10-23',structure=structure,
    actual_insert_bore_faces=48,ledger_positions_matched_to_brep=48,embedded_pngs_decoded=len(parser.images),
    mesh_assembly_bounds_verified=True,insert_groups=21,part_ids=17,steps=13,
    browser_preview='Not completed: sandboxed Edge process exited during launch. No alternate browser or service used.',
    visual_review='Direct PNG inspection; no browser layout, print pagination, or checkbox interaction verification.',
    physical_fit='GPU bracket, cooler, RAM, cables and complete physical assembly pending.',
    cad_modified=False,printer_jobs_sent=False)
(OUT/'manual_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
maintenance=[OUT/'Style1_V13_Assembly_Manual.html',OUT/'Assembly.png',OUT/'README.txt',OUT/'parts.json',OUT/'plate-list.csv',
    OUT/'manual_part_index.json',OUT/'manual_insert_ledger.json',OUT/'manual_cylinder_audit.json',OUT/'manual_mesh_index.json',OUT/'manual_verification.json',
    ROOT/'work/build_manual_style1_v13.py',ROOT/'work/build_manual_v09.py',ROOT/'work/verify_package_manual_style1_v13.py',ROOT/'work/check_manual_style1_v13.cjs',
    ROOT/'docs/风格1 桌面双层开放式机箱.md',ROOT/'docs/硬件尺寸与通用设计基准.md',ROOT/'outputs/board-alignment/motherboard-top-alignment.png']
maintenance+=list((OUT/'Manual_Images').glob('*.png'))+list((OUT/'Manual_Meshes').glob('*.stl'))
manualzip=OUT/'Style1_V13_Illustrated_Manual.zip'
with zipfile.ZipFile(manualzip,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('START_HERE.txt','风格1 V13安装说明书：解压后打开 outputs/ATX-Desk-v13/Style1_V13_Assembly_Manual.html。\nHTML全部插图已内嵌，可单独复制使用。其余路径保留项目结构用于维护；不含CAD和打印工程。\n')
    for p in maintenance:z.write(p,p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(manualzip) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
# Update the existing complete package without losing its CAD and printing data.
complete=ROOT/'outputs/ATX-Desk-v13-complete.zip'
replacement={p.relative_to(OUT).as_posix():p for p in maintenance if p.is_relative_to(OUT)}
replacement['Style1_V13_Illustrated_Manual.zip']=manualzip
replacement['Sources/Build_Assembly_Manual_V13.py']=ROOT/'work/build_manual_style1_v13.py'
replacement['Sources/Verify_Assembly_Manual_V13.py']=ROOT/'work/verify_package_manual_style1_v13.py'
temporary=complete.with_suffix('.manual-update.zip')
with zipfile.ZipFile(complete) as old,zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as new:
    original_names=old.namelist()
    # Complete package uses a single ATX-Desk-v13/ prefix.
    prefix='ATX-Desk-v13/' if any(n.startswith('ATX-Desk-v13/') for n in original_names) else ''
    targets={prefix+n:p for n,p in replacement.items()}
    for item in old.infolist():
        if item.filename not in targets:new.writestr(item,old.read(item.filename))
    for n,p in targets.items():new.write(p,n)
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(set(z.namelist()))
temporary.replace(complete)
print(json.dumps({'structure':structure,'brep_hole_matches':len(used),'images':len(parser.images),
                  'manual_zip':str(manualzip),'complete_package_updated':True},ensure_ascii=False))
