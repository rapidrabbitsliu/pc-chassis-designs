"""Idempotent Style 1 V13 manual, rendered from occurrence meshes exported by Fusion.
No CAD edits, slicing, or printer operations. Units of Manual_Meshes are verified mm.
"""
from pathlib import Path
import base64, csv, html, io, json, re, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/ATX-Desk-v13'
ASSET = OUT / 'Manual_Images'
ASSET.mkdir(exist_ok=True)
FONT = 'C:/Windows/Fonts/msyh.ttc'
def font(n): return ImageFont.truetype(FONT, n)
def esc(s): return html.escape(str(s), quote=True)

# IDs are scoped to Style 1 V13, independent of Style 2's part IDs.
ROWS = [
('P01','16_PCI_INSET_SIDE_16_45mm','左侧内斜框',7,'只有这一侧向内收；上边缘比底边更靠左。'),
('P02','16_CPU_VERTICAL_SIDE_FLUSH_TO_BEAM','右侧垂直框',7,'CPU 侧，外侧保持垂直；不可与左侧框互换。'),
('P03','12_front_PCI_SUPPORT_FRAME','前左框',5,'中缝接收两个连接耳螺丝；上方还有中纵梁和风扇梁接收孔。'),
('P04','12_front_CPU_SUPPORT_FRAME','前右框',2,'中缝上下各带一个一体连接耳；不是独立连接片。'),
('P05','18_ONE_PIECE_REAR_LOAD_BEAM_304_45mm','一体后横梁',4,'304.45 mm 连续整根；中间前伸座承托中纵梁，后侧有显卡塔安装孔。'),
('P06','04_front_GROUND_BAR_290mm_FLAT_PSU','前底横条',2,'实际长 274 mm，两端底搭接薄耳；装在靠风扇一端。'),
('P07','04_rear_GROUND_BAR_290mm_FLAT_PSU','后底横条',2,'实际长 274 mm；与前条几何相同，可互换，本编号按安装位置区分。'),
('P08','05_CENTERED_FLAT_PSU_CRADLE_OPEN_INTAKE','电源开放托架',0,'四脚落在底横条上；中央为向下进风开口，边缘有细扎带槽。'),
('P09','19_PCI_LONGITUDINAL_BOARD_RAIL_243_84mm','左主板纵梁',3,'较宽，承接主板 1、4、7 号孔；安装柱朝上。'),
('P10','19_MID_LONGITUDINAL_BOARD_RAIL_243_84mm','中主板纵梁',3,'底部有连续加强筋；承接主板 2、5、8 号孔。'),
('P11','19_CPU_LONGITUDINAL_BOARD_RAIL_243_84mm','右主板纵梁',3,'较窄，承接主板 3、6、9 号孔；3 号孔前后位置错开。'),
('P12','07_GPU_REINFORCED_REAR_TOWER','显卡固定塔',0,'底座有三个固定孔；竖面有上下滑槽、接口窗口和两侧加强筋。'),
('P13','08_GPU_UPPER_EAR_LEDGE_ADJUSTABLE','显卡上托片',4,'较高的滑片，前伸水平托台承接金属安装耳；两个上耳孔为待实卡核对的预留。'),
('P14','08_GPU_LOWER_TWO_TAB_RECEIVER_ADJUSTABLE','显卡下插脚座',2,'较矮滑片，两个薄插脚槽向下贯通；不能封住下方出口。'),
('P15','20_ONE_PIECE_DUAL_140_FAN_RAIL_284mm','双风扇一体底梁',4,'长 284 mm，四条支臂连接前框；四个小托台接收面板安装耳。'),
('P16','10_GPU_140_FAN_MOUNT','左风扇面板',0,'对应显卡侧；底部两个安装耳。与右面板可按位置区分。'),
('P17','10_CPU_140_FAN_MOUNT','右风扇面板',0,'对应 CPU 与内存侧；风扇外框孔不装热熔螺母。'),
]
META = {r['name']: r for r in json.loads((OUT/'parts.json').read_text())}
PLATES = {r['零件']: r for r in csv.DictReader(io.StringIO((OUT/'plate-list.csv').read_text(encoding='utf-8-sig')))}
INFO = {n: dict(id=i, name=c, nuts=k, note=t, plate=PLATES[n]['盘号']) for i,n,c,k,t in ROWS}
BYID = {v['id']: n for n,v in INFO.items()}
assert len(ROWS)==17 and sum(r[3] for r in ROWS)==48

def readstl(p):
    data = p.read_bytes()
    count = int.from_bytes(data[80:84], 'little')
    dt = np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')])
    a = np.frombuffer(data, dtype=dt, offset=84, count=count)
    assert len(data)==84+50*count
    return a['v'].astype(float)

PARTS = {p.stem: readstl(p) for p in (OUT/'Manual_Meshes').glob('*.stl')}
# Fusion's STL occurrence exporter retained component coordinates in these files.
# Apply the actual occurrence transform (translation is in Fusion centimetres).
for m in json.loads((OUT/'manual_mesh_index.json').read_text()):
    transform=np.array(m['transform']).reshape(4,4)
    PARTS[m['name']]=PARTS[m['name']]@transform[:3,:3].T+transform[:3,3]*10
for n,m in META.items():
    assert np.max(np.abs(np.ptp(PARTS[n], axis=(0,1))-m['native_size_mm']))<.04, n
for m in json.loads((OUT/'manual_mesh_index.json').read_text()):
    a=PARTS[m['name']]
    assert np.max(np.abs(a.min(axis=(0,1))-m['min_mm']))<.04
    assert np.max(np.abs(a.max(axis=(0,1))-m['max_mm']))<.04

def wrapped(dr, s, x, y, maxwidth, size=18, color='#617186'):
    line=''
    for ch in s:
        if dr.textlength(line+ch, font=font(size))>maxwidth and line:
            dr.text((x,y),line,font=font(size),fill=color); y+=size+8; line=''
        line+=ch
    if line: dr.text((x,y),line,font=font(size),fill=color)
    return y+size+8

def render(names, path, title, subtitle='', new=(), eye=(1,-1,.85), marks=(), wh=(1200,900)):
    """Orthographic mesh illustration. Mark targets are exact CAD hole entrances."""
    w,h=wh; im=Image.new('RGB',(w,h),'#f5f8fc'); dr=ImageDraw.Draw(im)
    e=np.array(eye,dtype=float);e/=np.linalg.norm(e)
    u=np.cross([0,0,1],e);u/=np.linalg.norm(u);v=np.cross(e,u);basis=np.array([u,-v,e])
    proj={n:PARTS[n]@basis.T for n in names}
    allp=np.concatenate(list(proj.values())).reshape(-1,3)
    lo=allp[:,:2].min(axis=0);hi=allp[:,:2].max(axis=0)
    s=min((w-170)/max(hi[0]-lo[0],1),(h-260)/max(hi[1]-lo[1],1))
    off=np.array([w/2,(h+125)/2])-(lo+hi)/2*s
    dr.text((32,20),title,font=font(29),fill='#173354')
    wrapped(dr,subtitle,32,68,w-64,17)
    triangles=[];light=np.array([.4,-.6,1.]);light/=np.linalg.norm(light)
    for n in names:
        t=PARTS[n];p=proj[n]
        norm=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
        if n.startswith('REF_'):
            base=np.array((214,222,228) if 'BOARD_' not in n else (187,210,199))
        else: base=np.array((36,126,226) if n in new else (126,155,184))
        shade=.63+.37*np.maximum(0,norm@light)
        for j in np.where(norm@e>=-.0001)[0]:
            col=tuple(np.clip(base*shade[j],0,255).astype(int))
            triangles.append((p[j,:,2].mean(),p[j,:,:2]*s+off,col))
    # Per-pixel depth avoids painter-order artifacts on long rails/open frames.
    pixels=np.array(im); zbuffer=np.full((h,w),-np.inf)
    for n in names:
        t=PARTS[n];p=proj[n]
        normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
        base=np.array((214,222,228) if n.startswith('REF_') else ((36,126,226) if n in new else (126,155,184)))
        if n.startswith('REF_BOARD_'):base=np.array((187,210,199))
        shade=.63+.37*np.maximum(0,normal@light)
        for j in np.where(normal@e>=-.0001)[0]:
            q=p[j,:,:2]*s+off
            x0=max(0,int(np.floor(q[:,0].min())));x1=min(w-1,int(np.ceil(q[:,0].max())))
            y0=max(100,int(np.floor(q[:,1].min())));y1=min(h-65,int(np.ceil(q[:,1].max())))
            if x1<x0 or y1<y0:continue
            a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-9:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            aa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            bb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;cc=1-aa-bb
            zz=aa*p[j,0,2]+bb*p[j,1,2]+cc*p[j,2,2]
            target=zbuffer[y0:y1+1,x0:x1+1]
            mask=(aa>=-1e-6)&(bb>=-1e-6)&(cc>=-1e-6)&(zz>target)
            target[mask]=zz[mask];pixels[y0:y1+1,x0:x1+1][mask]=np.clip(base*shade[j],0,255).astype(np.uint8)
    im=Image.fromarray(pixels);dr=ImageDraw.Draw(im)
    for k,point in enumerate(marks,1):
        q=np.array(point)@basis.T; x,y=q[:2]*s+off
        dr.ellipse((x-8,y-8,x+8,y+8),outline='#b66a13',fill='#ffe4a3',width=3)
        # Number directly beside the actual opening, not a frame bounding-box centre.
        dr.rounded_rectangle((x+11,y-12,x+43,y+15),radius=5,fill='#855319')
        dr.text((x+18,y-10),str(k),font=font(16),fill='white')
    legend='金色编号：本组螺母孔口；请按文字所示方向压入' if marks else ('蓝色：本件  |  真实网格 · 当前装配方向' if len(names)==1 else '蓝色：本步新增打印件  |  灰蓝：此前已装  |  浅灰/浅绿：参考硬件')
    dr.text((32,h-39),legend,font=font(16),fill='#617186')
    im.save(path)
    return im

for n,m in INFO.items():
    eye=(-1,-1,.85) if m['id']=='P01' else (1,-1,.85)
    if m['id'] in ('P13','P14'):eye=(1,-2,1.3)
    if m['id'] in ('P16','P17'):eye=(.35,-2,.7)
    render([n],ASSET/(m['id']+'.png'),m['id']+'  '+m['name'],f"第 {m['plate']} 盘 · 数量 1 · 热熔螺母 {m['nuts']} 个",new=[n],eye=eye,wh=(1000,760))

# Exact assembled-coordinate entrances; arrows below are directions INTO the part.
GROUPS=[]
def group(pid,face,points,direction,coord,eye=(1,-1,2),diam='4.7'):
    GROUPS.append(dict(id=f'N{len(GROUPS)+1:02d}',part=pid,face=face,points=points,
                       direction=direction,coordinate=coord,eye=eye,pilot_mm=diam,count=len(points)))
for pid,xx in [('P01',4),('P02',294)]:
    group(pid,'上表面主板纵梁孔',[(xx,y,140) for y in (20,225)],'从上向下 −Z','X='+str(xx)+'；Y=20 / 225；Z=140')
    pts=[(12.45-16.45*z/140+8 if pid=='P01' else 294.45,6,z) for z in (8,132)]
    group(pid,'前端面前框孔',pts,'从前向后 +Y','前端面 Y=6；孔高 Z=8 / 132',(-.6 if pid=='P01' else .6,-3,.6))
    group(pid,'后端面横梁孔',[(xx,253.84,132)],'从后向前 −Y','Y=253.84；孔高 Z=132',(1,3,.7),'4.6')
    group(pid,'底搭接凹座内孔',[(24.45 if pid=='P01' else 290.45,y,3.2) for y in (39.92,203.92)],'从凹座底面向上 +Z','Y=39.92 / 203.92；入口 Z=3.2',(1,-1,-3))
group('P03','上表面三个孔',[(50,2,140),(110,2,140),(134,3,140)],'从上向下 −Z','风扇梁 X=50 / 110,Y=2；中纵梁 X=134,Y=3')
group('P03','中缝前面两个孔',[(146,-10,z) for z in (8,132)],'从前向后 +Y','X=146，Y=−10；Z=8 / 132',(.6,-3,.6))
group('P04','上表面两个风扇梁孔',[(200,2,140),(265,2,140)],'从上向下 −Z','X=200 / 265；Y=2；Z=140')
group('P05','上表面四个孔',[(134,222.5,140)]+[(x,248.5,140) for x in (80,140,158)],'从上向下 −Z','中梁座 (134,222.5)；塔座 X=80 / 140 / 158,Y=248.5')
for pid,y in [('P06',39.92),('P07',203.92)]:
    group(pid,'上表面两个托架接收孔',[(79.4,y,8),(225.4,y,8)],'从上向下 −Z',f'X=79.4 / 225.4；Y={y:g}；Z=8')
HOLES={1:(16.51,233.68),2:(140.97,233.68),3:(298.45,210.82),4:(16.51,78.74),5:(140.97,78.74),6:(298.45,78.74),7:(16.51,6.35),8:(140.97,6.35),9:(298.45,6.35)}
for pid,nums in [('P09',(1,4,7)),('P10',(2,5,8)),('P11',(3,6,9))]:
    group(pid,'主板安装柱顶孔',[(HOLES[j][0],HOLES[j][1],158) for j in nums],'从安装柱顶向下 −Z','对应主板孔 '+ ' / '.join(map(str,nums))+'；入口 Z=158')
group('P13','背面两个滑块锁紧孔',[(x,260,276) for x in (80,164)],'从背面向前 −Y','背面朝塔；X=80 / 164；Z=276',(1,3,1))
group('P13','托台顶面两个显卡上耳孔',[(100,249.5,282),(120,249.5,282)],'从托台顶向下 −Z','X=100 / 120；Y=249.5；Z=282；待核对实卡',(.6,-1,3),'4.6')
group('P14','背面两个滑块锁紧孔',[(x,260,157) for x in (80,164)],'从背面向前 −Y','背面朝塔；X=80 / 164；Z=157',(1,3,1))
group('P15','四个小托台顶孔',[(x,-14,160) for x in (32.4,132.4,176.4,276.4)],'从上向下 −Z','X=32.4 / 132.4 / 176.4 / 276.4；Y=−14；Z=160')
assert sum(g['count'] for g in GROUPS)==48
for pid,_,_,k,_ in ROWS: assert sum(g['count'] for g in GROUPS if g['part']==pid)==k
for g in GROUPS:
    render([BYID[g['part']]],ASSET/(g['id']+'.png'),f"{g['id']}  {g['part']} · {g['face']}",
           g['direction']+' · 本组 '+str(g['count'])+' 个 · 装配坐标 / mm',new=[BYID[g['part']]],marks=g['points'],eye=g['eye'],wh=(1100,800))

def names(ids): return [BYID[i] for i in ids.split()]
MB=[n for n in PARTS if n.startswith(('REF_BOARD_','REF_CPU_','REF_MEMORY_','REF_PRIMARY_','REF_SECOND_'))]
PSU=[n for n in PARTS if n.startswith('REF_PSU_FLAT')]
GPU=[n for n in PARTS if n.startswith('REF_GPU_FANS')]
FANS=[n for n in PARTS if n.startswith('REF_CASE_FAN_')]
STEPS=[
('清点并完成全部热熔','',0,'核对 17 件及九盘清单，移除 brim 和支撑，尤其清理中纵梁、塔座、前右连接耳和电源托架。按孔位图完成最多 48 个短热熔螺母，冷却后逐孔轻试牙。','不要在 Ø3.4 通孔、Ø6.6 螺丝头井或风扇 Ø4.5 孔中装热熔螺母。P13 上耳两孔先作为待实卡核对的预留。'),
('连接左右框与两根底横条','P01 P02 P06 P07',4,'先把 P06、P07 两端薄搭接耳嵌入 P01、P02 底部对应凹座。螺丝从下面向上穿过薄耳，拧入侧框凹座内的螺母。两条分别在 Y=39.92 和 203.92。','先轻锁四颗。这里没有底部头井，螺丝头会低于模型 Z=0；四角加等高脚垫，净高须大于实测头部突出量，约 4 mm 可作选材起点。此时不得安装电子硬件。'),
('装上前侧两片框架','P03 P04',6,'从风扇一侧看，P03 在左、P04 在右，P04 的两个一体连接耳跨住 P03 中缝。左右各两颗螺丝从前面穿入侧框；中缝另用两颗穿过连接耳拧入 P03。','角部 4 颗，中缝 2 颗。右侧保持垂直，只有左侧向内收。不要用锁紧力弥补接合面错位。'),
('安装连续后横梁','P05',2,'将 P05 横跨左右侧框上沿，前伸的中纵梁座朝主板内部。两端安装耳贴到侧框后端，螺丝从背后向前锁入侧框。','本件整根无中缝，不再添加旧版拼接片。左右端承托面应贴合，校正框架后交替轻锁；电源后排风区域保持开放。'),
('安装电源开放托架','P08',4,'P08 的四只脚对准 P06、P07 上的四个接收孔，从脚上方的深头井放入螺丝向下锁紧。托架边缘承托电源，中央大开口朝下方进风区域。','本步先装托架，不放电源。先把两条宽约 3 mm、足够长度的细扎带穿过边缘槽，暂不收紧；避开进风圆。'),
('安装三根主板纵梁','P09 P10 P11',6,'P09 放左侧框，P11 放 CPU 右侧框，各用两颗从上向下锁紧。P10 的底筋朝下，前端落在 P03，后端落在 P05 的前伸座，两端各一颗。','三根均长 243.84，不沿 304.8 方向横放。九个安装柱顶面应在同一高度；右后 3 号孔本来就与左后两孔错开。'),
('安装显卡塔与两个可调件','P12 P13 P14',7,'P12 底座放在 P05 后部三孔上，用三颗从上向下固定。P13、P14 位于塔的主板一面，托台和插脚口向前；各用两颗从塔背面滑槽穿过，拧入滑块背面的短螺母。','塔 3 颗，上下滑块各 2 颗。滑块先轻夹，留待实卡调高；下插脚槽及塔底、横梁上的对应出口要贯通。'),
('放入并约束电源','',0,'从开放侧在下层放入电源；大风扇朝下，排风面和 AC 插口朝后，与主板 DP、显卡接口同侧。让壳体边缘落在托架上，收紧两条预穿绑带作防脱。','电源 150 × 140 × 86，底面模型高度 Z=30。托架承担电源自重，电源外壳不承担主板或框架载荷。绑带不压进风网、排风网和接线口。'),
('安装主板及板上硬件','',9,'先按原厂方法处理 CPU、内存和散热器背板，再将主板水平放到九个安装柱上。CPU 在右侧，背部接口朝后；用九颗 M3×6 从上面轻锁，不能弯板强行对孔。','主板底面模型 Z=158，右后孔错位是正常布局。真实散热器、内存高度及背面元件尚未建模，应逐处检查；P13、P14 仍可从后面调整。'),
('直插显卡并调好挡板固定','',2,'显卡插靠近 CPU 的第一条长 PCIe，卡扣完全到位；不用 PCIe 延长线。保持显卡自然竖直，调整 P14 让两个金属插脚进入贯通槽，调整 P13 托住上方金属安装耳，再锁紧原有四颗滑块螺丝。','上耳可用 0～2 颗新增 M3×6，取决于实卡孔位。P13 预留 X=100/120、P14 槽中心 X=96/116 未实测。若不自然对位，不硬压显卡或掰插脚，应先完成适配后再通电。'),
('预装双风扇组件','P15 P16 P17',4,'在桌面上将 P16、P17 的四个底部安装耳放在 P15 小托台上，用四颗 M3×6 从上向下固定。两把风扇分别放在面板的前侧，每把用四套匹配的贯穿紧固件安装。','面板 4 颗 M3；风扇另计 8 套，可先备 M4×40、普通 M4 螺母及垫片，核对风扇实物后用。两个风扇均按壳体箭头朝后 +Y 送风，不装反。'),
('把双风扇组件固定到前框','',4,'把预装组件的四条支臂落在 P03、P04 上方：左侧 X=50/110，右侧 X=200/265。四颗螺丝从支臂上方头井向下锁入前框，P16 在左、P17 在右。','本步图片为装到整机后的状态。风扇不能碰内存、显卡及线束；如果真实散热器挡住工具或风扇位置，应先拆下风扇组件再完成适配。'),
('理线和整机检查','',0,'布线避开风扇、热表面和 PCB 锐边；确认电源防脱、显卡挡板固定、主板九孔、四角脚垫均完成。检查真实插头与线缆转弯空间，手转风扇确认无擦碰，再按硬件说明试运行。','框架应在桌面稳定落地，不能由四颗底部螺丝头顶住。首次运行观察温度、异响和塑料变形；几何检查不能代替 PETG 长期承载和温升验证。'),
]
assert sum(x[2] for x in STEPS)==48
# Lower the PSU through the still-open top before rails/tower block tool access.
psu_step=STEPS.pop(7)
STEPS.insert(5,(psu_step[0],psu_step[1],psu_step[2],
    '此时上方仍敞开，从上方将电源轻放到 P08，不必穿过后横梁下面的窄余隙。大风扇朝下，排风面和 AC 插口朝后，与主板 DP、显卡接口同侧。让壳体边缘落在托架上，收紧两条预穿绑带作防脱。',psu_step[4]))
assembled=[]; step_sets=[]; pending_fan=[]
for i,(title,ids,_,_,_) in enumerate(STEPS,1):
    if i==1: ns=list(INFO)
    elif i==11: pending_fan=names('P15 P16 P17')+FANS;ns=pending_fan
    else:
        assembled+=names(ids)
        if i==6:assembled+=PSU
        if i==9:assembled+=MB
        if i==10:assembled+=GPU
        if i==12:assembled+=pending_fan
        ns=assembled.copy()
    step_sets.append(ns)
    if i==1:continue
    fresh=names(ids) if i!=12 else names('P15 P16 P17')
    eye=(-1,1,.85) if i in (4,8,10) else (1,-1,.95)
    render(ns,ASSET/f'step{i:02d}.png',f'{i:02d}  {title}',
           '仅示参考硬件；螺丝、绑带、脚垫、散热器及线缆未画出' if i>=6 else '按编号及孔位图装配；螺丝未画出',new=fresh,eye=eye)
render(names('P12 P13 P14'),ASSET/'gpu-slide-detail.png','显卡塔 · 从主板一侧看','上托台、下插脚座向前；从塔背面穿入螺丝',new=names('P13 P14'),eye=(1,-2,.8))
sheet=Image.new('RGB',(1500,5*300),'white')
for i,(pid,*_) in enumerate(ROWS):
    tile=Image.open(ASSET/(pid+'.png'));tile.thumbnail((375,285));sheet.paste(tile,((i%4)*375,(i//4)*300))
sheet.save(ASSET/'step01.png')

JOINTS=[
('底横条 → 左右侧框','P06 P07','P01 P02',4,'从底面向上；拆装电子硬件前完成'),
('前框角部 → 侧框','P03 P04','P01 P02',4,'从前向后，左右上、下各一'),
('前框中缝连接耳','P04','P03',2,'从前向后，上下各一'),
('后横梁两端 → 侧框','P05','P01 P02',2,'从后向前，两端各一'),
('电源托架 → 底横条','P08','P06 P07',4,'从上向下，四脚各一'),
('左右主板梁 → 侧框','P09 P11','P01 P02',4,'从上向下，每梁前后各一'),
('中主板梁 → 前框和后梁座','P10','P03 P05',2,'从上向下，前后各一'),
('显卡塔 → 后梁','P12','P05',3,'从上向下，底座三孔'),
('塔 → 上下可调滑块','P12','P13 P14',4,'从背后向前，上下各二'),
('风扇底梁 → 前框','P15','P03 P04',4,'从上向下，四支臂'),
('风扇面板 → 风扇底梁','P16 P17','P15',4,'从上向下，每面板二'),
('主板 → 三根主板梁','主板','P09 P10 P11',9,'从上向下，每梁三个'),
('实卡金属上耳 → 上托片','显卡','P13',2,'0～2 颗，实卡对位后确定'),
]
assert sum(j[3] for j in JOINTS)==48

def dataimage(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
def fig(p,caption):return f'<figure><img loading="lazy" src="{dataimage(p)}" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'
def chips(ids):return ''.join(f'<a class="chip" href="#{pid}">{pid} {esc(INFO[BYID[pid]]["name"])}</a>' for pid in ids.split() if pid in BYID)
def table(headers,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in r)+'</tr>' for r in rows)+'</tbody></table></div>'

# Reuse the established manual's layout, without executing its V09 generator.
old=(ROOT/'work/build_manual_v09.py').read_text(encoding='utf-8')
CSS=re.search(r'<style>(.*?)</style>',old,re.S).group(1)
CSS+='''
.part-grid,.hole-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.part-tag{background:#173b61;color:white;border-radius:6px;padding:3px 9px}.chips{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}.chip{background:#eaf2fc;border:1px solid #cbdff7;border-radius:7px;padding:5px 9px;font-size:13px;text-decoration:none}.step figure{margin:18px 0}.step{padding-bottom:38px}.part-card:target{outline:3px solid #e1ac42}.part-card code{display:block;font-size:11px}.hole-card:target{outline:3px solid #e1ac42}.step label{display:block}.lead{font-size:18px}.caption{font-size:13px;color:var(--muted)}
td:nth-child(3){white-space:normal}
@media(max-width:760px){.part-grid,.hole-grid{grid-template-columns:1fr}.card{padding:13px}h2{font-size:23px}}
@media print{.part-grid,.hole-grid{grid-template-columns:1fr 1fr}.part-card,.hole-card{break-inside:avoid}.step{break-inside:auto}.step img{max-height:340px;width:auto;max-width:100%;object-fit:contain}.step h3{break-after:avoid}.notice{break-inside:avoid}img{max-width:100%}}
'''
body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>风格 1 V13 机架安装说明书</title><style>'+CSS+'</style></head><body>',
'<header><span class="badge">STYLE 1 / V13 / 2026.10.23</span><h1>桌面双层开放式机架<br>安装说明书</h1><p class="lead">17 个打印件 · 九盘 · 主板平放 · 下层电源朝下进风 · 前置双 140 风扇</p></header><main class="wrap">',
'<nav><a href="#overview">方向与版本</a><a href="#catalog">零件图册</a><a href="#prepare">材料工具</a><a href="#inserts">热熔孔位</a><a href="#steps">装配步骤</a><a href="#check">完成检查</a><a href="#ledger">连接账</a></nav>',
'<div class="toolbar"><button onclick="window.print()">打印 / 保存为 PDF</button><button id="reset">清空勾选</button><span id="progress" class="muted"></span></div>',
'<section id="overview"><div class="grid"><div><h2>先确认版本和朝向</h2><p>本书仅对应 <strong>风格 1 V13 一体横梁版</strong>，不是风格 2 的竖主板机架。全部零件保持 100% 比例；不要混入旧版后横梁拼接件。</p><div class="triple"><div><div class="metric">17</div>独立打印件</div><div><div class="metric">48</div>热熔螺母预留</div><div><div class="metric">290</div>模型落地宽 / mm</div></div><p>左右以<strong>站在两把前风扇外侧，面向主板</strong>为准：左为 PCIe 侧，右为 CPU 侧；后为主板 DP、显卡显示接口和电源排风一侧。后视图视觉左右会反转，零件身份不变。</p><p>X 向 CPU 右侧，Y 向背部接口，Z 向上。模型桌面为 Z=0，主板左前角投影为 X=0、Y=0；加脚垫后实际离桌面高度随之增加。</p><div class="notice">这是待完整实物验收的原型。显卡挡板上耳、下插脚，真实散热器、内存、线缆及长期承载仍需核对。浅灰硬件只是包络，不能证明已经完成固定。</div></div>'+fig(OUT/'Assembly.png','V13 对应 Fusion 装配图；显示颜色仅用于区分部件。')+'</div></section>',
'<section id="catalog"><h2>01 · 先认零件</h2><p>P01–P17 是风格 1 本说明的固定编号，未刻入模型。出盘后可贴纸签，保留 STL 文件名和盘号；风格 2 的 P 编号不适用于本书。每件数量均为 1。</p><div class="part-grid">']
for pid,n,cn,k,note in ROWS:
    dims=' × '.join(f'{x:.2f}'.rstrip('0').rstrip('.') for x in META[n]['native_size_mm'])
    groups=' '.join(f'<a href="#{g["id"]}">{g["id"]}</a>' for g in GROUPS if g['part']==pid) or '无热熔孔'
    body.append(f'<article class="part-card card" id="{pid}"><h3><span class="part-tag">{pid}</span> {cn}</h3>'+fig(ASSET/(pid+'.png'),note)+f'<p><strong>第 {PLATES[n]["盘号"]} 盘 · 数量 1 · 螺母 {k} 个</strong></p><p>装配轴向包络 {dims} mm；打印方向尺寸见盘号表。</p><p>热熔孔图：{groups}</p><code>{esc(n)}.stl</code></article>')
body.append('</div></section><section id="prepare"><h2>02 · 材料和工具</h2>')
materials=[
('M3 热熔螺母','48 个预留 / 建议备 60','M3 内螺纹 × 高 4.5 × 滚花外径约 5。现有高 8 的螺母不能直接替换短孔。模型底孔有 Ø4.6 和 Ø4.7 两种，先试装。'),
('M3×6 机螺丝','46 颗固定用途 + 实卡上耳 0～2 颗 / 建议备 60','37 颗结构连接、9 颗主板，显卡上耳另最多 2 颗。头径须能进入 Ø6.6 头井，优先普通圆柱头或盘头；头高按实际空间核对，不用沉头、自攻或大手拧头。'),
('140×140×25 风扇','2 只','安装面板四孔距 124.5，孔径 Ø4.5，面板主体厚 6。具体风扇型号未定，先核对孔距、孔径、厚度及引线。'),
('风扇贯穿紧固件','8 套 / 建议备 10 套','可先备 M4×40 螺栓、普通 M4 螺母各 8 及垫片约 16。6 mm 面板加 25 mm 风扇后仍需容纳垫片与螺母，按实物试配；不计入 48 颗 M3。'),
('电源防脱细扎带','2 条，长度按实物','槽约 3.6×2.4，使用宽约 3 的细扎带，可按需要串接。沿电源壳体实边约束，勿挡进排风、开关、AC 插头和模组接口；不把电源外壳当框架承重件。'),
('等高防滑脚垫','至少四个角部支撑点','底部四颗螺丝头未沉入模型。脚垫净高必须大于实测突出量，约 4 mm 可作选材起点；所有支点等高，不能由螺丝头接触桌面。安装脚垫会增加实机高度。'),
('风扇接线材料','按硬件接口选择','必要的 PWM 延长线或集线器。按原厂规格核对两把风扇总电流和主板接口允许电流。'),
('主板、电源、显卡','按硬件基准文档','Z390-A PRO；ENERMAX ERV650G-AHG 140×150×86；影驰 5060 Ti 16GB。本风格不使用 PCIe 延长线。'),
]
body.append(table(['材料','需要量与建议备量','规格和用途'],materials))
body.append('<div class="grid"><div class="card"><h3>热熔工具</h3><ul><li>可调温烙铁、匹配的 M3 热熔压头、烙铁架、耐热垫及镊子。</li><li>PETG 同材料试孔块，直角定位工具或软夹具。</li><li>温度按螺母和材料厂家建议及试块表现调整，不能把喷嘴打印温度当热熔设定。</li></ul></div><div class="card"><h3>装配工具</h3><ul><li>匹配 M3 头型的短柄及正常长度螺丝刀；M4 螺母扳手。</li><li>游标卡尺、直角尺、钢尺、修边刀、小锉及去支撑工具。</li><li>护目镜、清洁平整桌面及硬件要求的防静电条件。</li></ul></div></div></section>')
body.append('<section id="inserts"><h2>03 · 先完成热熔螺母</h2><div class="notice good">在安装主板、电源、显卡之前完成全部热熔。只处理下列金色编号孔：Ø3.4 是通孔，Ø6.6 是螺丝头井，风扇 Ø4.5 是贯穿安装孔，均不装热熔螺母。</div><p>下图由对应 V13 网格绘制，金点对应孔口位置；孔序只属于本组。坐标为装配后的模型坐标，Z 从模型桌面起算，<strong>不是从每个零件底端量</strong>。压入方向单独写明；侧向和底向孔应把零件翻转后操作。</p>')
body.append(table(['零件','螺母数','接收位置'],[(chips(pid),str(k),'；'.join(g['id']+' '+g['face'] for g in GROUPS if g['part']==pid) or '不需要热熔螺母') for pid,_,_,k,_ in ROWS]))
body.append('<ol><li>去掉孔口毛刺，先在同批 PETG 试孔上确认螺母尺寸和压入效果。</li><li>将本组孔口朝上，沿孔轴轻压，热熔到与孔口齐平；不要冷压、顶穿或压歪。</li><li>保持不动至塑料定形，完全冷却后轻试 M3 螺丝。螺母松转、堵牙或塑料开裂须处理后再装。</li><li>优先处理 P01/P02 底搭接凹座和前后端面、P13/P14 朝塔的背面孔；装上框架或滑块后这些孔口会被遮住。</li></ol><div class="hole-grid">')
for g in GROUPS:
    body.append(f'<article class="hole-card card" id="{g["id"]}"><h3>{g["id"]} · {g["part"]} {g["face"]}</h3>'+fig(ASSET/(g['id']+'.png'),g['direction'])+f'<p><strong>{g["count"]} 个 · 底孔 Ø{g["pilot_mm"]} · {g["direction"]}</strong></p><p>{esc(g["coordinate"])}</p></article>')
body.append('</div></section><section id="steps"><h2>04 · 按顺序装配</h2><p>螺丝数量只统计本步新使用的 M3×6；调整已有滑块不重复计数。框架先轻紧、校正后再逐步锁紧，不对 PETG 或主板施加强拧力。</p>')
for i,(title,ids,count,desc,check) in enumerate(STEPS,1):
    if i==1:ids=' '.join(BYID)
    if i==6:ids='P08'
    if i==9:ids='P09 P10 P11'
    if i==10:ids='P12 P13 P14'
    if i==12:ids='P03 P04 P15 P16 P17'
    countlabel='0～2' if i==10 else str(count)
    detail=fig(ASSET/'gpu-slide-detail.png','显卡塔前面细节；两个滑片的热熔孔口在朝塔的背面。') if i==8 else ''
    body.append(f'<article class="step" id="step{i:02d}"><span class="num">{i}</span><h3>{title}</h3><p><strong>本步新用 M3×6：{countlabel} 颗</strong></p><p>{esc(desc)}</p><div class="notice">{esc(check)}</div><div class="chips">{chips(ids)}</div>'+fig(ASSET/f'step{i:02d}.png','清点总览' if i==1 else ('本步完成的桌面子组件；下一步才安装到整机。' if i==11 else '本步完成状态。螺丝、脚垫、绑带、散热器和线缆未画出，仍须按文字完成。'))+detail+f'<label class="check"><input type="checkbox" aria-label="第{i}步已完成">第 {i} 步已完成并检查</label></article>')
CHECKS=[
'17 件编号与 V13 九盘项目对应，旧版拼接件未混入',
'全部短热熔螺母冷却、试牙通过，未将 H8 压入短孔',
'P01 内斜、P02 垂直，框架接合面贴合且无层间开裂',
'底部四颗螺丝头不接触桌面，等高脚垫使机架稳定无晃动',
'电源落在托架边缘并可靠防脱，底部进风、背部排风和 AC 接口通畅',
'三根主板梁柱顶同高，主板九孔自然对位且未接触不应接触的焊点',
'显卡第一长槽直插到位，两个下插脚不顶底，上耳可靠锁紧',
'显卡挡板和实物散热器、内存及线缆空间已适配；不强压不合孔的部件',
'风扇真实气流箭头朝后，全部叶片转动无擦碰，线束固定在叶片之外',
'风扇及显卡供电按原厂要求连接，插头和接口没有受拉或受挤',
'首次试运行已观察振动、异响、温度和塑料变形，长期承载仍持续观察',
]
body.append('</section><section id="check"><h2>05 · 完成检查</h2>'+''.join(f'<label class="check"><input type="checkbox" aria-label="{esc(t)}">{esc(t)}</label>' for t in CHECKS)+'<p class="muted">勾选尝试保存在当前浏览器；换设备不保证同步。单文件内嵌全部图片，正文、图片与打印样式均可离线使用。</p></section>')
body.append('<section id="ledger"><h2>06 · 连接账和盘号</h2><p>共 48 个螺母预留、46 颗固定用途 M3 螺丝，加实卡上耳 0～2 颗。上耳未适配时，不以其他 46 颗已装完代替显卡固定验收。</p>')
body.append(table(['连接','通孔件','螺母接收件','M3×6 数量','锁入方向'],[(a,chips(b) or b,chips(c),str(k),d) for a,b,c,k,d in JOINTS]))
body.append(table(['盘号','说明书编号','STL 文件名','打印方向包络 mm','支撑'],[(PLATES[n]['盘号'],chips(pid),'<code>'+esc(n)+'.stl</code>',PLATES[n]['打印尺寸mm'],PLATES[n]['支撑']) for pid,n,_,_,_ in ROWS]))
body.append('<h3>验证范围与维护入口</h3><p>图解来自 V13 Fusion 装配 occurrence 导出的毫米网格，已逐件核对三轴尺寸与装配坐标。紧固件账按源孔位重算，并从当前 V13 BRep 中独立识别出 48 个 Ø4.6/4.7 圆柱孔面，按零件和孔轴位置复核。已有 CAD 干涉、接触和切片结果可作为几何参考，不能代替真实承重、PETG 蠕变或热性能测试。</p><p>模型：ATX_Desk_v13_one_piece.f3d；打印入口：ATX-Desk-v13-All-Parts-9-Plates.3mf；文档维护源：work/build_manual_style1_v13.py；孔位账：manual_insert_ledger.json；编号表：manual_part_index.json。</p><p>完成静态结构和直接插图检查；浏览器预览进程未能启动，网页的实际桌面/手机排版、打印分页和勾选交互尚未在浏览器验证。</p><p>本次仅生成文档及插图，没有更改 CAD、重切片或发送打印。额外脚垫为装配要求，未画入 CAD。显卡上耳和下插脚的适配、未建模的散热器与线缆均须先完成实物核对。</p></section><footer>风格 1 V13 · 2026年10月23日 · 本书不适用于风格 2；版本变更后需同步更新说明书和打印件。</footer></main>')
body.append('''<script>
const checks=[...document.querySelectorAll('.check input')],key='style1-v13-assembly-checks-v1';
try{const saved=JSON.parse(localStorage.getItem(key)||'[]');checks.forEach((c,i)=>c.checked=!!saved[i]);}catch(e){}
function update(){document.getElementById('progress').textContent='已检查 '+checks.filter(c=>c.checked).length+' / '+checks.length;try{localStorage.setItem(key,JSON.stringify(checks.map(c=>c.checked)));}catch(e){}}
checks.forEach(c=>c.addEventListener('change',update));document.getElementById('reset').addEventListener('click',()=>{checks.forEach(c=>c.checked=false);update();});update();
</script></body></html>''')
manual=OUT/'Style1_V13_Assembly_Manual.html'
manual.write_text('\n'.join(body),encoding='utf-8')
(OUT/'manual_part_index.json').write_text(json.dumps(INFO,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'manual_insert_ledger.json').write_text(json.dumps({'count':48,'groups':GROUPS,'connections':JOINTS,'source_unit':'mm','scope':'Style 1 V13 only'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'html':str(manual),'bytes':manual.stat().st_size,'parts':17,'steps':len(STEPS),'insert_groups':len(GROUPS),'inserts':48,'images':len(list(ASSET.glob('*.png')))},ensure_ascii=False))
