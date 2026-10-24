from pathlib import Path
src=Path('work/build_atx_v02_preview.py').read_text('utf-8')
src=src.replace('V02','V03').replace('v02','v03').replace('ATX-Desk-v03-preview','ATX-Desk-v03-preview')
src=src.replace("('footprint_width',286)","('footprint_width',290)")
src=src.replace("[('PCI',10.45,-4),('CPU',280.45,292.8)]","[('PCI',8.45,-4),('CPU',282.45,282.45)]")
src=src.replace("[('PCI',10.45,-4,-1),('CPU',280.45,292.8,1)]","[('PCI',8.45,-4,-1),('CPU',282.45,282.45,1)]")
src=src.replace("c=comp('01_'+side+'_'+section+'_INSET_SIDE')","c=comp('01_'+side+'_'+section+('_INSET_SIDE' if side=='PCI' else '_VERTICAL_SIDE'))")
src=src.replace('box(c,14,y-4,178,290.8,y+4,190','box(c,14,y-4,178,281.45,y+4,190')
src=src.replace("],276.8,JOIN,'Printable rib transition'","],267.45,JOIN,'Printable rib transition'")
src=src.replace('GROUND_BAR_286mm','GROUND_BAR_290mm').replace('box(c,10.45,y-10,0,296.45,y+10,8','box(c,8.45,y-10,0,298.45,y+10,8').replace('286 mm floor crossbar','290 mm floor crossbar')
src=src.replace('footprint[0]-286','footprint[0]-290').replace("'ground_width_mm':286","'ground_width_mm':290")
src=src.replace("'tail_support_removed':True","'tail_support_removed':True,'CPU_side_vertical':True,'PCI_side_tapered_only':True,'case_fans':{'count':2,'size_mm':[140,140,25],'hole_pitch_mm':124.5,'airflow':'+Y front to rear','model':'unconfirmed'},'added_front_extent_mm':50")
fans='''    # Two 140x140x25 front intake fans. They add fore-aft space, not lateral width.
    c=comp('09_FRONT_DUAL_FAN_CARRIER')
    box(c,12.4,-25,198,296.4,-19,210,NEW,'Common 284 mm wide fan carrier')
    for x in (50,154.4,265):
        box(c,x-5,-19,198,x+5,14,204,JOIN,'Fan carrier arm onto front beam')
        poly(c,'x',x-5,[(-25,198),(-19,184),(-2.65,198)],10,JOIN,'Fan carrier arm gusset')
    for tag,x0 in [('GPU',12.4),('CPU',156.4)]:
        c=comp('10_'+tag+'_140_FAN_MOUNT')
        poly(c,'y',-25,[(x0,210),(x0+140,210),(x0+140,350),(x0,350)],6,NEW,'140 mm removable fan mounting frame')
        bore(c,'y',-25,x0+70,280,130,6,'Open airflow aperture')
        for xx in (x0+7.75,x0+132.25):
            for zz in (217.75,342.25):bore(c,'y',-25,xx,zz,4.5,6,'124.5 mm pitch fan fixing clearance')
    for tag,x0 in [('GPU',12.4),('CPU',156.4)]:
        c=comp('REF_CASE_FAN_'+tag+'_140x140x25',True)
        poly(c,'y',-50,[(x0,210),(x0+140,210),(x0+140,350),(x0,350)],25,NEW,'140x140x25 fan envelope')
        bore(c,'y',-50,x0+70,280,130,25,'Rotor opening reference')
        box(c,x0+5,-38,278,x0+135,-36,282,JOIN,'Rotor reference spoke horizontal')
        box(c,x0+68,-38,215,x0+72,-36,345,JOIN,'Rotor reference spoke vertical')
        circle(c,'y',-38,x0+70,280,32,2,JOIN,'Fan hub reference')
        for xx in (x0+7.75,x0+132.25):
            for zz in (217.75,342.25):bore(c,'y',-50,xx,zz,4.5,25,'Reference fan mounting bore')
        a=comp('REF_AIRFLOW_'+tag+'_FRONT_TO_REAR',True)
        poly(a,'z',279,[(x0+65,-75),(x0+75,-75),(x0+75,-64),(x0+82,-64),(x0+70,-53),(x0+58,-64),(x0+65,-64)],2,NEW,'Front intake direction +Y')
'''
src=src.replace('    # Hardware references, not printable components.',fans+'    # Hardware references, not printable components.')
src=src.replace("('04_','05_','06_','07_','08_')","('04_','05_','06_','07_','08_','09_','10_')")
src=src.replace("elif n.startswith('REF_GPU'):k='GPU';c.opacity=.4","elif n.startswith('REF_GPU'):k='GPU';c.opacity=.4\n        elif n.startswith('REF_CASE_FAN'):k='slot';c.opacity=.8\n        elif n.startswith('REF_AIRFLOW'):k='slot'")
Path('work/build_atx_v03_preview.py').write_text(src,encoding='utf-8')
import ast
ast.parse(src)
print('Prepared V03: CPU side vertical, PCI side tapered, floor width 290, dual 140 mm front fans.')
