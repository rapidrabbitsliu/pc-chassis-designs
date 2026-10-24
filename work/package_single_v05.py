from pathlib import Path
import shutil,zipfile
out=Path('outputs/Single-Bracket-v05')
s=Path('outputs/Single-Bracket-v04/README.txt').read_text('utf-8')
s=s.replace('V04','V05').replace('v04','v05')
s=s.replace('托面24 mm宽','托面32 mm宽').replace('单片8 mm厚三角筋，留有三角减重窗口','靠单侧的8 mm厚三角筋，留有切去尖角的三角减重窗口').replace('实体体积56.07 cm³','实体体积61.41 cm³')
a=s.index('STL单位mm，PRINT文件已经摆好打印朝向。');b=s.index('插销大平面贴床',a)
s=s[:a]+'''STL单位mm，PRINT文件已经摆好打印朝向。托架三角筋的外侧大平面与背板、托面、前挡边的同侧边缘共面，直接贴打印平台，不再悬空。三角筋本体不需要大面积底部支撑，挂钩和局部孔槽仍需检查支撑。允许局部支撑从模型表面生成；不要误把整个三角减重窗口塞满支撑。
平移三角筋会改变托面的扭转受力，本版托面和前挡边从24 mm加宽至32 mm；这只是装配与打印改进，没有证明与居中筋承载等效。后续左右件需镜像，并复核电源侧面和插头空间。
几何对比：V04离床水平朝下面积约3209 mm²，V05约131 mm²；贴床面积约3841 mm²。此统计只看水平面，不能当作切片支撑体积或打印时间。实际支撑请以逐层预览为准。
''' +s[b:]
s+='''
本轮V05变化摘要：三角筋从宽度中间移到z=-16至-8 mm一侧；托面和前挡边加宽并从z=-16 mm起始，使各部分共面贴床；三角减重窗口尖角改为短边过渡。4.0 mm钩喉、双钩20 mm间距、上下80 mm孔距、防抬起插销及M3孔槽不变。旧V04保留，请勿混用两版主托架。V04插销与V05插销几何相同，已打印的插销可以继续试配。
'''
(out/'README.txt').write_text(s,encoding='utf-8')
export=Path(r'C:\Users\liu\Documents\Codex\2026-10-18\referenced-chatgpt-conversation-this-is-an\outputs\Single-Bracket-v05')
shutil.copytree(out,export,dirs_exist_ok=True)
with zipfile.ZipFile(export.parent/'Single-Bracket-v05.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in export.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(export.parent))
shutil.copy2(export.parent/'Single-Bracket-v05.zip','outputs/Single-Bracket-v05.zip')
print('V05 STL, Fusion archive, script and instructions packaged.')
