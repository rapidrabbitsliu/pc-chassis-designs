from pathlib import Path
import zipfile,json,xml.etree.ElementTree as E

root=Path(__file__).resolve().parents[1];out=root/'outputs'/'Style2-v07'
project=out/'Style2_V07_A1_PETG_All_Parts_13_Plates.3mf'
with zipfile.ZipFile(project) as z:
    assert z.testzip() is None
    s=json.loads(z.read('Metadata/project_settings.config'))
    cfg=E.fromstring(z.read('Metadata/model_settings.config'))
    assert len(cfg.findall('object'))==19 and len(cfg.findall('plate'))==13
    for obj in cfg.findall('object'):
        md={m.get('key'):m.get('value') for m in obj.findall('metadata')}
        assert not md['name'].startswith('REF_') and md['extruder']=='1' and md['enable_support']=='0'
    for k,v in {'printer_model':'Bambu Lab A1','layer_height':'0.2','wall_loops':'5',
                'sparse_infill_density':'40%','sparse_infill_pattern':'gyroid','enable_prime_tower':'0'}.items():
        assert s[k]==v,(k,s[k])
    assert s['nozzle_diameter']==['0.4']
assert len(list((out/'PRINT_STL').glob('*.stl')))==19
assert len(json.loads((out/'print_plate_checks.json').read_text(encoding='utf-8')))==19
summary={'slicer':'Bambu Studio 02.07.01.62','parts':19,'plates':13,'all_sliced_in_gui':True,
         'filament_g':1103.92,'estimated_total_minutes':3106,'support_g':0,
         'rounded_plate_minutes':[289,263,271,368,207,145,325,323,274,165,205,135,135],
         'print_sent':False,'settings_verified':True,
         'note':'Per-plate rounded minutes sum to one minute less than the UI total. Re-slice after reopen if Bambu requests it.'}
(out/'slice-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
dest=root/'outputs'/'Style2-V07-Dual140-A1-PETG-Print-Package.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for name in [project.name,'Style2_V07_Dual140_Colored.f3d','Style2_V07_Dual140.step',
                 'PRINT_README.txt','print_plate_list.csv','print_plate_checks.json','print_mesh_checks.json',
                 'verification.json','slice-summary.json','Dual140_Front.png']:
        z.write(out/name,'Style2-v07/'+name)
    for f in sorted((out/'PRINT_STL').glob('*.stl')):z.write(f,'Style2-v07/PRINT_STL/'+f.name)
    for name in ['build_style2_v07.py','package_style2_v07_print.py','verify_style2_v07_package.py']:
        z.write(root/'work'/name,'Style2-v07/Sources/'+name)
print(json.dumps({'verified':True,'parts':19,'plates':13,'package':str(dest),'minutes':3106,'grams':1103.92}))
