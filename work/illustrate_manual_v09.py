from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import json,struct,base64,re,html,zipfile

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/Style2-v09';ASSET=OUT/'Manual_Images';ASSET.mkdir(exist_ok=True)
fontpath='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(fontpath,n)
meta=json.loads((OUT/'parts.json').read_text(encoding='utf-8'))
cn=['左侧立柱','中间立柱','右侧立柱','左侧底脚','中间底脚','右侧底脚','下横撑','上横撑','左侧直角框','右侧直角框','显卡承托梁','PCIe 母槽托盘','左显卡垫座','右显卡垫座','电源前托条','电源后托条','双风扇立梁','下风扇框 · 显卡','上风扇框 · CPU / 内存']
counts=[13,9,17,4,3,4,0,0,0,0,8,0,0,0,0,0,4,0,0]
notes=['带顶部横向短耳；主板侧有 3 个凸台','无顶部短耳，背面仅 4 个横撑孔','外侧另外有 4 个风扇立梁连接孔','电源端带外侧连接凸块','电源端没有直角框连接凸块','电源端带外侧连接凸块，与左侧镜像','两端短斜角向上；装在主板背面下方','两端短斜角向下；装在主板背面上方','装在左立柱外侧，螺钉头凹槽朝外','装在右立柱外侧，螺钉头凹槽朝外','中间大开口，8 个螺母孔朝上','薄框；母槽安装方式仍待实物适配','靠显卡左端，接触壳体可承力位置','靠显卡右端；与左垫座形状相同','较窄的前侧边缘，为立柱与底脚避让','完整宽度托条；装在电源后侧','四条短支脚连接右立柱，4 个接收孔连接风扇框','外形与上框相同，装在下方','外形与下框相同，装在上方']
parts={};info={}
def readstl(p):
 data=p.read_bytes();n=struct.unpack_from('<I',data,80)[0]
 return np.array([struct.unpack_from('<12fH',data,84+i*50)[3:12] for i in range(n)]).reshape(-1,3,3)
for i,m in enumerate(meta):
 t=readstl(OUT/'Raw_STL'/(m['name']+'.stl'));ratio=np.array(m['native_size_mm'])/np.ptp(t,axis=(0,1));scale=10 if np.mean(ratio)>5 else 1;t*=scale
 assert np.max(abs(np.ptp(t,axis=(0,1))-m['native_size_mm']))<.05
 key=f'P{i+1:02d}';parts[m['name']]=t;info[m['name']]=dict(id=key,name=cn[i],nuts=counts[i],note=notes[i])
for p in (OUT/'Manual_Refs').glob('*.stl'):parts[p.stem]=readstl(p)*scale
def render(names,path,title,subtitle='',new=(),eye=(1,-1,.8),labels=False,wh=(1100,850)):
 w,h=wh;im=Image.new('RGB',(w,h),'#f5f8fc');dr=ImageDraw.Draw(im)
 e=np.array(eye,dtype=float);e/=np.linalg.norm(e);u=np.cross([0,0,1],e);u/=np.linalg.norm(u);v=np.cross(e,u);basis=np.array([u,-v,e])
 proj={n:parts[n]@basis.T for n in names};allp=np.concatenate(list(proj.values())).reshape(-1,3);lo=allp[:,:2].min(axis=0);hi=allp[:,:2].max(axis=0)
 s=min((w-160)/max(hi[0]-lo[0],1),(h-215)/max(hi[1]-lo[1],1));off=np.array([w/2,(h+115)/2])-(lo+hi)/2*s
 dr.text((32,22),title,font=font(29),fill='#173354');dr.text((32,67),subtitle,font=font(16),fill='#667b90')
 triangles=[]
 for n in names:
  t=parts[n];p=proj[n];norm=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
  isref=n.startswith('REF_');base=np.array((199,208,217) if isref else ((36,126,226) if n in new else (126,155,184)))
  light=np.array([.4,-.6,1.]);light/=np.linalg.norm(light);shade=.65+.35*np.maximum(0,norm@light)
  for j in range(len(t)):
   if norm[j]@e < -.0001:continue
   color=tuple(np.clip(base*shade[j],0,255).astype(int));triangles.append((p[j,:,2].mean(),p[j,:,:2]*s+off,color))
 for _,p,col in sorted(triangles,key=lambda x:x[0]):dr.polygon([tuple(q) for q in p],fill=col)
 if labels:
  # Numbering on visible projected component extents; full names are in the part cards.
  targets=[]
  for n in names:
   if n not in info or n not in new:continue
   # Anchor on an actual visible triangle, never the empty center of a frame.
   t=parts[n];p=proj[n];normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);visible=normal@e>0
   area=np.abs((p[:,1,0]-p[:,0,0])*(p[:,2,1]-p[:,0,1])-(p[:,1,1]-p[:,0,1])*(p[:,2,0]-p[:,0,0]))
   j=np.argmax(np.where(visible,area,0));c=p[j,:,:2].mean(axis=0)*s+off;targets.append((c[1],c,n))
  left=sorted(targets[::2]);right=sorted(targets[1::2]);
  for side,arr in [(0,left),(1,right)]:
   for j,(_,c,n) in enumerate(arr):
    y=120+(h-240)*j/max(len(arr)-1,1);x=20 if side==0 else w-94;end=x+72 if side==0 else x
    dr.line([tuple(c),(end,y+15)],fill='#566f87',width=2);dr.rounded_rectangle((x,y,x+73,y+31),radius=6,fill='#173b61');dr.text((x+9,y+3),info[n]['id'],font=font(18),fill='white')
 dr.text((32,h-40),'蓝色：本步新增  |  灰蓝：此前已装  |  浅灰：硬件包络示意',font=font(16),fill='#667b90')
 im.save(path)
 return im

for n,m in info.items():render([n],ASSET/(m['id']+'.png'),m['id']+'  '+m['name'],'热熔螺母 '+str(m['nuts'])+' 个 · '+m['note'],new=[n],wh=(900,700))
names=list(info);sets=[names,names[:6],names[:8],names[:10]+names[14:16],names[:16]]
mb=[n for n in parts if n.startswith(('REF_MSI','REF_MOTHERBOARD_IO'))]
psu=[n for n in parts if n.startswith(('REF_ENERMAX','REF_PSU_FAN'))]
gpu=[n for n in parts if n.startswith(('REF_GALAX','REF_RISER','REF_PCIE'))]
fans=[n for n in parts if n.startswith('REF_FAN')]
sets += [sets[-1]+mb,sets[-1]+mb+psu,sets[-1]+mb+psu+gpu,names+mb+psu+gpu+fans,names+mb+psu+gpu+fans]
titles=['01  清点零件','02  立柱与底脚装好','03  上下横撑装好','04  电源托条与外侧框装好','05  显卡承托组件装好','06  主板安装后的示意','07  电源放入后的示意','08  显卡与母槽装入后的示意','09  双风扇安装后的示意','10  最终装配检查示意']
for i,ns in enumerate(sets):
 added=ns if i in (0,1) else [n for n in ns if n not in sets[i-1]]
 if i==0:continue
 render(ns,ASSET/f'step{i+1:02d}.png',titles[i],('仅示硬件包络；散热器、线缆和额外固定件未建模' if i>=5 else '按 P 编号与下方零件卡片对照'),new=added,labels=i<5,eye=(-1,1,.8) if i in (3,6,9) else (1,-1,.8))
# Contact sheet: all 19 parts separately pictured, with IDs printed in each tile.
sheet=Image.new('RGB',(1500,((19+3)//4)*300),'white')
for i,n in enumerate(info):
 tile=Image.open(ASSET/(info[n]['id']+'.png'));tile.thumbnail((375,292));sheet.paste(tile,((i%4)*375,(i//4)*300))
sheet.save(ASSET/'step01.png')
def dataimage(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
def fig(p,caption):return '<figure><img loading="lazy" src="'+dataimage(p)+'" alt="'+html.escape(caption)+'"><figcaption>'+caption+'</figcaption></figure>'
manual=OUT/'Style2_V09_Assembly_Manual.html';text=manual.read_text(encoding='utf-8')
mapping={n:m['id'] for n,m in info.items()}
plate_rows=list(__import__('csv').DictReader(__import__('io').StringIO((OUT/'print_plate_list.csv').read_text(encoding='utf-8-sig'))))
pan={r['零件']:r['盘号'] for r in plate_rows}
cards=[]
for n,m in info.items():
 cards.append('<article class="part-card card" id="'+m['id']+'"><h3><span class="part-tag">'+m['id']+'</span> '+m['name']+'</h3>'+fig(ASSET/(m['id']+'.png'),m['note'])+'<p><strong>第 '+pan[n]+' 盘 · 热熔螺母 '+str(m['nuts'])+' 个</strong></p><code>'+n+'</code></article>')
gallery='<section id="catalog"><h2>零件图册 · 先按编号认零件</h2><p>P01–P19 是本说明书的单件编号，旁边保留 Bambu 文件名与盘号。编号目前显示在说明书中，尚未刻在打印零件上；建议出盘后用纸签或记号笔在非配合面标记。外形相同的零件按安装位置区分，不需要重新打印。</p><div class="part-grid">'+''.join(cards)+'</div></section>'
text=text.replace('<section id="prepare">',gallery+'<section id="prepare">')
text=text.replace('<nav>','<nav><a href="#catalog">19 件零件图册</a>')
# Add stable single-part IDs beside every existing exact file-name reference.
for n in sorted(info,key=len,reverse=True):
 text=text.replace('<small>'+n+'</small>','<small><a href="#'+mapping[n]+'">'+mapping[n]+' · '+n+'</a></small>')
 text=text.replace('<td>'+n+'</td>','<td><a href="#'+mapping[n]+'">'+mapping[n]+' · '+info[n]['name']+'</a><small>'+n+'</small></td>')
used=[list(info),names[:6],names[6:8],names[8:10]+names[14:16],names[10:14],[],[],[],names[16:19],[]]
idx=0
def addstep(match):
 global idx
 i=idx;idx+=1
 chips=''.join('<a class="chip" href="#'+mapping[n]+'">'+mapping[n]+' '+info[n]['name']+'</a>' for n in used[i])
 cap='本步完成状态。'+('螺母和螺丝未画出，位置见孔位图。' if i<5 else '浅灰为硬件包络，未画出线缆、散热器、绑带和显卡挡板额外固定件；这些仍需按文字要求完成。')
 return match.group(0).replace('</article>','<div class="chips">'+chips+'</div>'+fig(ASSET/f'step{i+1:02d}.png',cap)+'</article>')
text=re.sub(r'<article class="step">.*?</article>',addstep,text,flags=re.S);assert idx==10
# Exact explanatory diagrams, embedded as native SVG rather than speculative hardware renders.
detail='''<section id="details"><h2>安装细节 · 容易装反的地方</h2><div class="grid"><div class="card"><h3>A · 螺母先压入接收件</h3><svg viewBox="0 0 600 300" role="img" aria-label="热熔螺母与螺钉连接剖面示意"><defs><marker id="arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0 0L10 4L0 8" fill="#b66a13"/></marker></defs><rect x="200" y="120" width="260" height="125" fill="#a9c3de"/><rect x="292" y="120" width="36" height="80" fill="white"/><rect x="292" y="132" width="36" height="52" fill="#d5a84c"/><path d="M310 45V112" stroke="#b66a13" stroke-width="4" marker-end="url(#arr)"/><text x="200" y="30">4.7 mm 盲孔 → M3 热熔螺母</text><text x="25" y="275">压到与孔口齐平；完全冷却后再拧螺丝</text><text x="18" y="90">压入方向 ↓</text></svg><p>先在 P01–P06、P11、P17 上完成全部热熔。大号螺钉头凹槽不是螺母孔。</p></div><div class="card"><h3>B · 穿过连接件再拧入螺母</h3><svg viewBox="0 0 600 300" role="img" aria-label="螺丝穿过通孔后拧入热熔螺母"><rect x="95" y="130" width="165" height="85" fill="#90b3d9"/><rect x="260" y="130" width="230" height="85" fill="#c4d5e7"/><rect x="90" y="158" width="200" height="28" fill="white"/><rect x="263" y="155" width="65" height="34" fill="#d5a84c"/><path d="M125 172H312" stroke="#52647a" stroke-width="12"/><rect x="103" y="150" width="24" height="44" fill="#52647a"/><text x="28" y="85">螺丝头</text><text x="115" y="255">通孔件</text><text x="310" y="255">已装螺母的接收件</text><text x="80" y="30">局部连接剖面示意 · 不按比例</text></svg><p>连接件贴合后轻拧即可。禁止以拧紧螺丝的方式，把歪斜的热熔螺母强拉到位。</p></div><div class="card"><h3>C · 电源限位与导入方向</h3><svg viewBox="0 0 600 300" role="img" aria-label="电源由斜坡一侧导入，另一侧为直挡边"><rect x="75" y="225" width="450" height="25" fill="#4d93df"/><path d="M75 225V180H100V225M440 225L500 180V225" fill="#4d93df"/><rect x="115" y="80" width="310" height="140" fill="#cbd5df"/><path d="M500 75L430 135" stroke="#b66a13" stroke-width="5" marker-end="url(#arr)"/><text x="130" y="55">电源壳体示意</text><text x="18" y="285">直挡边 / 出风侧</text><text x="330" y="285">斜坡导入 / 线缆侧</text></svg><p>P15、P16 都有左右限位。一侧斜面用于放入时导向；落位后还要用可靠绑带防倾、防脱，不遮挡通风。</p></div><div class="card"><h3>D · 55 mm 间距与风向</h3><svg viewBox="0 0 600 300" role="img" aria-label="显卡与主板基准平面间距55毫米，风扇沿板面吹向接口侧"><rect x="115" y="60" width="20" height="175" fill="#9db9d5"/><rect x="300" y="145" width="60" height="90" fill="#b9c6d4"/><path d="M135 120H300M135 111V129M300 111V129" stroke="#b66a13" stroke-width="3"/><text x="160" y="105">55 mm</text><text x="75" y="275">主板平面</text><text x="292" y="275">显卡背面</text><text x="390" y="105">侧置风扇气流</text><path d="M470 145V235" stroke="#2563eb" stroke-width="5" marker-end="url(#arr)"/><text x="390" y="285">朝主板接口侧</text></svg><p>此图只解释基准距离。显卡穿透风扇可能仍朝主板排热；不能以 55 mm 代替实测温度。按风扇壳体箭头核对两只风扇的真实气流方向。</p></div></div></section>'''
text=text.replace('<section id="check">',detail+'<section id="check">')
text=text.replace('</style>','.part-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.part-tag{display:inline-block;background:#173b61;color:white;border-radius:6px;padding:2px 9px}.part-card img{background:#f5f8fc}.chips{display:flex;flex-wrap:wrap;gap:7px;margin:14px 0}.chip{background:#eaf2fc;border:1px solid #cbdff7;border-radius:7px;padding:5px 9px;font-size:13px;text-decoration:none}.step figure{margin:16px 0}.step{padding-bottom:35px}.part-card:target{outline:3px solid #e1ac42}.part-card code{display:block;font-size:11px}@media(max-width:760px){.part-grid{grid-template-columns:1fr}}@media print{.part-grid{grid-template-columns:1fr 1fr}.step img{max-height:340px;width:auto;max-width:100%;object-fit:contain}.step{break-inside:auto}.part-card{break-inside:avoid}.step h3{break-after:avoid}} </style>')
text=text.replace('先按编号认零件','先按编号认零件（点击步骤中的编号可跳转）')
manual.write_text(text,encoding='utf-8')
(OUT/'manual_part_index.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'part_cards':len(info),'step_images':10,'detail_diagrams':4,'html_bytes':manual.stat().st_size,'assets':str(ASSET)}))
