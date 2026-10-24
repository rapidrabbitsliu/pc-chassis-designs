from pathlib import Path
import zipfile,json,xml.etree.ElementTree as E

root=Path(__file__).resolve().parents[1]
out=root/'outputs'/'Style2-v06'
file=out/'Style2_V06_A1_PETG_All_Parts_10_Plates.3mf'
with zipfile.ZipFile(file) as z:
    assert z.testzip() is None
    settings=json.loads(z.read('Metadata/project_settings.config'))
    cfg=E.fromstring(z.read('Metadata/model_settings.config'))
    assert len(cfg.findall('object'))==16 and len(cfg.findall('plate'))==10
    for obj in cfg.findall('object'):
        meta={m.get('key'):m.get('value') for m in obj.findall('metadata')}
        assert not meta['name'].startswith('REF_')
        assert meta['extruder']=='1' and meta['enable_support']=='0'
    expected={'printer_model':'Bambu Lab A1','layer_height':'0.2','wall_loops':'5',
              'sparse_infill_density':'40%','sparse_infill_pattern':'gyroid',
              'top_shell_layers':'6','bottom_shell_layers':'5','print_sequence':'by layer','enable_prime_tower':'0'}
    for key,value in expected.items():assert settings[key]==value,(key,settings[key])
    assert settings['nozzle_diameter']==['0.4']
    assert all(t=='PETG' for t in settings['filament_type'])
checks=json.loads((out/'print_plate_checks.json').read_text(encoding='utf-8'))
assert len(checks)==16
assert len(list((out/'PRINT_STL').glob('*.stl')))==16
summary={'slicer':'Bambu Studio 02.07.01.62','parts':16,'plates':10,'all_sliced_in_gui':True,
         'total_minutes':2627,'total_filament_g':932.24,'support_g':0,
         'plate_minutes':[289,263,268,368,207,145,325,323,274,165],
         'project_settings_verified':expected,'new_print_sent':False,
         'note':'Editable project saved after GUI slicing; Bambu may require reslicing after reopening.'}
assert sum(summary['plate_minutes'])==summary['total_minutes']
(out/'slice-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
with zipfile.ZipFile(root/'outputs'/'Style2-V06-A1-PETG-Print-Package.zip','w',zipfile.ZIP_DEFLATED) as z:
    names=['Style2_V06_A1_PETG_All_Parts_10_Plates.3mf','Style2_V06_Colored.f3d',
           'PRINT_README.txt','print_plate_list.csv','print_plate_checks.json','print_mesh_checks.json',
           'slice-summary.json','Colored_Structure.png','verification.json']
    for name in names:z.write(out/name,'Style2-v06/'+name)
    for f in sorted((out/'PRINT_STL').glob('*.stl')):z.write(f,'Style2-v06/PRINT_STL/'+f.name)
    for name in ['package_style2_print.py','verify_style2_final_package.py','build_style2_v06.py','color_style2_v06.py']:
        z.write(root/'work'/name,'Style2-v06/Sources/'+name)
    z.write(root/'outputs'/'arrange_v12_plates.py','Style2-v06/Sources/Legacy_Package_Writer.py')
print(json.dumps(summary))
