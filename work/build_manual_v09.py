from pathlib import Path
import base64, csv, io

root=Path(__file__).resolve().parents[1]
out=root/'outputs/Style2-v09'
rows=[
('立柱 1','01_UPRIGHT_1','1','13','主板侧凸台 3；背面 6；底部侧面 2；外侧上部 2'),
('立柱 2','01_UPRIGHT_2','2','9','主板侧凸台 3；背面 4；底部侧面 2'),
('立柱 3','01_UPRIGHT_3','3','17','主板侧凸台 3；背面 6；底部侧面 2；外侧上部 2；风扇立梁连接 4'),
('底脚 1','02_FOOT_1','4','4','朝上 3；电源侧末端凸块的外侧面 1'),
('底脚 2','02_FOOT_2','4','3','朝上 3'),
('底脚 3','02_FOOT_3','5','4','朝上 3；电源侧末端凸块的外侧面 1'),
('显卡承托梁','06_GPU_CARRIER','6','8','上表面 8：母槽托盘 4，左右显卡垫座各 2'),
('双风扇立梁','10_FAN_MAST_RIGHT_SIDE','11','4','朝风扇框的安装面 4，分为上下两组'),
]
assert sum(int(r[3]) for r in rows)==62
table=''.join('<tr><td>'+r[0]+'<small>'+r[1]+'</small></td><td>'+r[2]+'</td><td><strong>'+r[3]+'</strong></td><td>'+r[4]+'</td></tr>' for r in rows)
plates=list(csv.DictReader(io.StringIO((out/'print_plate_list.csv').read_text(encoding='utf-8-sig'))))
plate_table=''.join('<tr><td>'+r['盘号']+'</td><td>'+r['零件']+'</td></tr>' for r in plates)
photo='data:image/png;base64,'+base64.b64encode((out/'Assembly.png').read_bytes()).decode()

def svg_post(index):
    # Hole positions are generated from V09 geometry, measured from the floor.
    zsets=[([25.51,149.97,307.45],[50,64,94,244,277,291],[20,35,160,184]),
           ([25.51,149.97,307.45],[50,64,277,291],[20,35]),
           ([25.51,149.97,307.45],[50,64,94,244,277,291],[20,35,50,130,160,184,236,290])]
    a,b,c=zsets[index-1]; chunks=[]
    for x,vals,col in [(70,a,'#208561'),(205,b,'#2563eb'),(340,c,'#ba6b14')]:
        chunks.append(f'<rect x="{x-13}" y="35" width="26" height="304" rx="4" fill="#e7edf5"/>')
        for z in vals:
            y=349-z
            chunks.append(f'<circle cx="{x}" cy="{y}" r="4.8" fill="{col}"/><text x="{x+20}" y="{y+4}" font-size="11">{z:g}</text>')
    return '<svg viewBox="0 0 420 380" role="img" aria-label="立柱'+str(index)+'螺母孔位示意，数字为距地面高度毫米"><text x="30" y="20">主板侧凸台</text><text x="180" y="20">背面</text><text x="300" y="20">侧面</text>'+''.join(chunks)+'<path d="M30 349H400" stroke="#8798ad"/><text x="32" y="370">地面基准 Z=0；数字单位 mm，示意不按比例</text></svg>'

html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V09 开放式机架 · 安装说明书</title>
<style>
:root{--blue:#2563eb;--ink:#182a40;--muted:#617186;--bg:#f1f5fa;--line:#dbe4ef}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.75 system-ui,"Microsoft YaHei",sans-serif}header{background:#102942;color:white;padding:48px max(24px,calc((100vw - 1100px)/2))}h1{font-size:38px;line-height:1.25;margin:12px 0}h2{font-size:25px;margin:0 0 18px}h3{margin:18px 0 8px}p{margin:9px 0}header p{color:#c6d8ed}.badge{display:inline-block;background:#254867;border-radius:8px;padding:4px 12px;font-size:13px;letter-spacing:1px}.wrap{max-width:1150px;margin:auto;padding:28px 24px 70px}nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}a{color:var(--blue)}nav a,button{border:1px solid var(--line);border-radius:10px;background:white;padding:8px 14px;text-decoration:none;color:var(--ink);cursor:pointer;font:inherit}section{background:white;padding:28px;border:1px solid var(--line);border-radius:18px;margin:20px 0;scroll-margin-top:20px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.triple{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.card{border:1px solid var(--line);border-radius:12px;padding:18px}.metric{font-size:30px;font-weight:750;color:var(--blue)}small,.muted{color:var(--muted)}small{display:block;font-size:12px;overflow-wrap:anywhere}.notice{border-left:4px solid #d9972e;background:#fff7e8;padding:14px 18px;margin:16px 0}.good{border-left-color:#208561;background:#edf8f2}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:12px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#f4f7fb;white-space:nowrap}td:nth-child(3){white-space:nowrap}.step{position:relative;padding:0 0 25px 48px;border-left:2px solid #dce7f6;margin-left:16px}.num{position:absolute;left:-18px;top:0;background:var(--blue);color:white;width:34px;height:34px;border-radius:50%;text-align:center;line-height:34px;font-weight:700}.step h3{margin-top:0}.check{display:block;padding:10px 0;border-bottom:1px solid #edf1f6}.check input{width:18px;height:18px;vertical-align:middle;margin-right:10px;accent-color:var(--blue)}figure{margin:0}img{width:100%;border-radius:12px}figcaption{font-size:13px;color:var(--muted)}svg{width:100%;height:auto}svg text{font-family:system-ui,"Microsoft YaHei",sans-serif;fill:#34475d}code{background:#eef3f8;padding:2px 5px;border-radius:4px;font-size:13px;overflow-wrap:anywhere}li{margin:5px 0}footer{color:var(--muted);font-size:13px}details{border:1px solid var(--line);padding:14px;border-radius:10px;margin:12px 0}summary{cursor:pointer;font-weight:650}.toolbar{display:flex;gap:10px;flex-wrap:wrap}.printonly{display:none}
@media(max-width:760px){.grid,.triple{grid-template-columns:1fr}h1{font-size:29px}section{padding:20px}.wrap{padding:18px 14px}header{padding:30px 22px}td,th{padding:9px}.step{padding-left:30px}}
@media print{body{background:white;font-size:11px}header{background:white;color:#182a40;padding:10px}header p{color:#617186}h1{font-size:26px}.wrap{max-width:none;padding:0}nav,.toolbar{display:none}section{break-inside:auto;border-radius:0;padding:15px;margin:12px 0}.step,.card,tr,figure{break-inside:avoid}.grid{grid-template-columns:1fr 1fr}.triple{grid-template-columns:repeat(3,1fr)}details{display:block}details>*{display:block}.printonly{display:block}a{color:inherit;text-decoration:none}}
</style></head><body><header><span class="badge">STYLE 2 / V09 / 2026.10.23</span><h1>开放式机架安装说明书</h1><p>先压入热熔螺母，再组装框架，最后安装硬件。适用于 19 件、13 盘的 V09 打印工程。</p></header><main class="wrap">
<nav><a href="#prepare">材料工具</a><a href="#inserts">螺母位置</a><a href="#steps">安装步骤</a><a href="#check">完成检查</a><a href="#parts">零件盘号</a></nav>
<div class="toolbar"><button onclick="window.print()">打印 / 保存为 PDF</button><button id="reset">清空勾选</button><span id="progress" class="muted"></span></div>
<section><div class="grid"><div><h2>这份说明对应哪一版</h2><p>三根竖柱、竖放电源、外侧直角支撑、上下两只 140 mm 风扇；显卡与主板基准平面间距为 <strong>55 mm</strong>。</p><div class="triple"><div><div class="metric">62</div>热熔螺母</div><div><div class="metric">19</div>打印零件</div><div><div class="metric">314</div>总高 / mm</div></div><p class="muted">整体两水平方向为 299.84 × 280 mm。280 mm 对应此前收紧的风扇至电源侧方向，不代表两个方向都小于 290 mm。</p><div class="notice">V09 属于待实物装配验证的原型。PCIe 母槽尺寸、显卡接触位置、CPU 散热器和线缆空间尚未全部确认；55 mm 是图中两平面距离，不是扣除主板元件后的最小距离，也不代表散热已验证。</div></div><figure><img src="PHOTO" alt="V09 蓝色支架与半透明硬件参考装配图"><figcaption>蓝色为打印支架，半透明为硬件示意。以零件编号和孔位图确定方向。</figcaption></figure></div></section>
<section id="prepare"><h2>01 · 先准备材料和工具</h2><div class="scroll"><table><thead><tr><th>材料</th><th>需要 / 建议备量</th><th>购买或使用要点</th></tr></thead><tbody>
<tr><td>M3 黄铜热熔螺母</td><td><strong>62 / 70 个</strong></td><td>长度 H4.5 mm，外径约 5 mm，M3 内螺纹；模型预留孔径 4.7 mm。不同品牌外纹不同，先用试块试装。H8 不可直接代替。</td></tr>
<tr><td>M3 × 6 mm 机螺钉</td><td><strong>62 / 70 颗</strong></td><td>其中框架 53 颗、主板 9 颗。选头径不超过 6.6 mm、头高不超过 3 mm 的圆柱头等合适头型；不选沉头或风扇自攻螺钉。长度从头下计算。</td></tr>
<tr><td>140 × 140 × 25 mm 风扇</td><td>2 只</td><td>当前孔距 124.5 mm，四孔贯穿固定；先核对实际孔距、孔径和厚度。</td></tr>
<tr><td>M4 × 40 mm 贯穿螺栓 + 普通 M4 螺母</td><td>各 8 / 各 10 个</td><td>用于两只风扇，不使用热熔螺母。框 6 mm + 风扇 25 mm 后需容纳螺母及垫片；到货实配，若风扇不允许 M4 穿过则更换相配规格，勿强扩孔。</td></tr>
<tr><td>M4 平垫片</td><td>约 16 个</td><td>螺栓头与螺母侧各一片；可按实际风扇安装面调整。</td></tr>
<tr><td>电源固定带</td><td>2 条</td><td>足够绕过电源和可靠承力位置的可调绑带；约 300–400 mm 长，长度以实物为准。不能遮挡进出风口，不能压电源线出口。模型窄槽不保证适配宽魔术贴。</td></tr>
<tr><td>显卡防倾固定件</td><td>1 套，实配</td><td>目前模型没有完整的金属挡板锁紧座。需补足与挡板配合的机械固定，不能让母槽承担显卡重量，也不能只依靠摩擦夹持。</td></tr>
<tr><td>PCIe 延长线及母槽固定件</td><td>已有延长线；紧固件待测</td><td>托盘当前为临时方案，尚未为实物母槽建立专用安装孔。母槽安装螺丝不包含在 62 颗中；实测后确定。</td></tr>
<tr><td>风扇接线材料</td><td>按接口需要</td><td>PWM 延长线 / 一分二线，或带独立供电的集线器；先查风扇额定电流及主板风扇接口允许电流。</td></tr>
<tr><td>可选辅助材料</td><td>若干</td><td>尼龙扎带与固定座、防滑脚垫、薄软垫。加厚脚垫会增加 314 mm 总高，仍须满足置物空间高度；不得让软垫接触风扇叶片。</td></tr>
</tbody></table></div><div class="grid"><div class="card"><h3>热熔工具</h3><ul><li>可调温电烙铁及 M3 热熔螺母压入头</li><li>稳定烙铁架、耐热垫、镊子</li><li>直角定位夹具或小台钳软夹口</li><li>同材料的 4.7 mm 孔试块，先试装再处理正式零件</li></ul></div><div class="card"><h3>装配工具</h3><ul><li>与所选螺钉匹配的内六角 / 十字螺丝刀</li><li>M4 螺母扳手或小套筒</li><li>游标卡尺、钢尺、直角尺</li><li>去裙边钳、修边工具、小锉刀、护目镜</li><li>防静电操作条件及清洁的装配桌面</li></ul></div></div></section>
<section id="inserts"><h2>02 · 哪些孔先压螺母</h2><div class="notice good"><strong>所有热熔操作都在硬件安装前完成。</strong>螺母装在接收螺丝的 4.7 mm 盲孔里；3.4 mm 通孔只供螺丝穿过，6.6 mm 大孔用于容纳螺丝头，均不装螺母。</div>
<div class="scroll"><table><thead><tr><th>零件 / 文件编号</th><th>盘号</th><th>热熔螺母</th><th>压入位置与朝向</th></tr></thead><tbody>INSERT_TABLE<tr><th colspan="2">合计</th><th>62 个</th><th>立柱 39 + 底脚 11 + 显卡承托梁 8 + 风扇立梁 4</th></tr></tbody></table></div>
<h3>立柱逐面孔位图</h3><p>高度均从装配后的地面 Z=0 起算；立柱底端在 Z=10，因此从零件底端量时需减去 10 mm。绿色为主板凸台孔，蓝色为背面横撑孔，橙色为侧向连接孔。侧面图把两侧孔合并展示，实际朝向见图下说明。</p><div class="triple">POST_DIAGRAMS</div>
<div class="notice">立柱 1 的最上方绿色孔位于伸出的短耳上，其余两个在竖柱上。立柱 3 的四个风扇连接孔高度为 50 / 130 / 236 / 290 mm，不要和背面横撑孔混淆。</div>
<details open><summary>底脚、显卡梁、风扇立梁的定位方法</summary><ul><li><strong>三根底脚：</strong>每根上表面 3 个盲孔，对应显卡梁、电源前托、电源后托。沿显卡方向至电源方向，整机坐标 Y 依次为 −87.4 / 30 / 101 mm；从底脚显卡端的最前端量为 30 / 147.4 / 218.4 mm。底脚 1、3 电源端凸块还各有 1 个外侧横向盲孔。</li><li><strong>显卡承托梁：</strong>上表面的 8 个盲孔全部压入；靠近两端的两对孔给显卡垫座，中间两对孔给母槽托盘。三处固定到底脚的通孔不装螺母。</li><li><strong>风扇立梁：</strong>仅装在朝风扇框一面的 4 个接收孔，高度 68 / 104 / 220 / 256 mm；四条连接主立柱的支脚有深螺丝头孔，不装螺母。</li></ul></details>
<h3>这些零件不需要热熔螺母</h3><p>上下横撑（03）、左右直角框（05）、母槽托盘（07）、两块显卡垫座（08）、电源前后托条（09）、两块风扇框（11）。它们的螺丝穿过去，拧入另一零件中已压好的螺母。</p>
<h3>热熔操作顺序</h3><ol><li>去掉裙边和孔口毛刺，确认零件没有裂纹、层间分离或明显弯曲；不要直接把孔扩到螺母外径。</li><li>在同批 PETG 试块上试装。烙铁温度按螺母厂家及 PETG 的建议调节，以能缓慢压入且不过度软塌为准，不把打印喷嘴温度直接当作热熔设定。</li><li>让安装面朝上、孔轴竖直，烙铁头与孔保持同轴，利用热量轻压到与孔口齐平；不要强行冷压、顶穿或继续压深。</li><li>保持位置至塑料定形，完全冷却后再轻试 M3 螺丝；确认没有歪斜、堵牙、松动或凸起。</li><li>逐件完成上表数量后，再开始装配。若螺母转动、拉脱或孔周围开裂，先返修或重打，不能靠拧得更紧补救。</li></ol></section>
<section id="steps"><h2>03 · 按顺序装配</h2>
STEPS
</section>
<section id="check"><h2>04 · 完成检查清单</h2>CHECKS<p class="muted">本页勾选会尝试保存在当前浏览器；换设备或清除浏览器数据后不保证保留。静态说明离线可用，无外部字体、图片或脚本依赖。</p></section>
<section id="parts"><h2>05 · 零件和盘号对照</h2><p>编号从 03 跳到 05 是沿用设计版本命名，不是漏件。共 19 个打印件，硬件参考模型不参与打印。</p><div class="scroll"><table><thead><tr><th>盘号</th><th>零件文件名</th></tr></thead><tbody>PLATES</tbody></table></div><h3>螺丝去向核对</h3><p>立柱到底脚 6；上下横撑 16；两侧直角框 6；显卡承托梁到底脚 3；电源托条到底脚 6；母槽托盘到显卡梁 4；两块显卡垫座 4；风扇立梁到立柱 4；两块风扇框到立梁 4；主板 9。共 <strong>62 颗 M3 × 6</strong>。风扇的 8 颗 M4 另计。</p></section>
<footer>依据 V09 建模源文件、零件列表及打印工程编写。此说明不包含对实体承载、长期 PETG 蠕变或散热性能的验证结论。版本更新后请同步使用对应模型与说明。</footer></main>
<script>
const checks=[...document.querySelectorAll('.check input')];const key='style2-v09-manual-checks';
try{const saved=JSON.parse(localStorage.getItem(key)||'[]');checks.forEach((c,i)=>c.checked=!!saved[i]);}catch(e){}
function update(){document.getElementById('progress').textContent='准备与检查：'+checks.filter(c=>c.checked).length+' / '+checks.length;try{localStorage.setItem(key,JSON.stringify(checks.map(c=>c.checked)));}catch(e){}}
checks.forEach(c=>c.addEventListener('change',update));document.getElementById('reset').addEventListener('click',()=>{checks.forEach(c=>c.checked=false);update();});update();
</script></body></html>'''

steps=[
('清点与预装检查','先清点 19 个打印件、62 个热熔螺母和紧固件。处理裙边与小孔毛刺，空装确认接合面贴合；主板和显卡先留在防静电包装中。','先完成第 02 节所有热熔螺母，冷却后再继续。'),
('组装三根立柱和底脚','01_UPRIGHT_1/2/3 分别配 02_FOOT_1/2/3。主板凸台朝显卡一侧，底脚带末端凸块的一侧朝电源。每根用 2 颗 M3×6 从底脚侧面穿入，拧入立柱底部侧面螺母。','共 6 颗；先轻拧，让三个底脚平放在同一平面。'),
('安装上下横撑','上下横撑装在立柱背面，也就是电源一侧。每根横撑在每根立柱有 2 颗螺丝，两端短斜角连接各另有 1 颗；每根横撑 8 颗 M3×6。','共 16 颗；下横撑主体孔高度 50/64，上横撑 277/291 mm。校正立柱垂直后逐步交替拧紧，手拧贴合即可。'),
('安装电源托条与外侧直角框','两根电源托条分别对准三根底脚上中间、后方的孔，每条用 3 颗 M3×6。两侧直角框放在最外侧：上端对准立柱侧面 160/184 mm 孔，下端对准底脚末端凸块孔。','托条 6 颗，直角框 6 颗。电源出风侧必须保留通畅，不能被新增绑带或线束遮住。'),
('安装显卡承托梁和小托件','显卡梁装在三根底脚的显卡端固定孔，用 3 颗 M3×6。母槽托盘用 4 颗；左右显卡垫座各用 2 颗。承托梁与托件应一起处于 V09 向外移后的位置。','共 11 颗。母槽托盘的 4 颗只连接托盘与承托梁，并不是将延长线母槽直接锁在托盘上。'),
('安装主板、内存与散热器','先在桌面上按硬件原厂说明安装 CPU、内存和散热器背板。将主板孔与 9 个凸台对齐，主板接口朝电源出风的同一侧；使用 9 颗 M3×6 轻锁固定。','必须全部孔位自然对齐，凸台不能顶住元件或焊点。不要硬弯主板；散热器/内存与显卡空间需按实物确认。主板孔周围只能接触厂家允许的安装环。'),
('放入并固定电源','电源竖放，出风口与主板后接口同向，风扇面朝外。由斜坡限位的一侧导入，落在两条托座上，再用两条可靠绑带固定在承力位置。','不拆电源外壳，不借用外壳散热孔穿金属件，不拧入可能过长的外壳螺丝。托座限位只定位，不能代替防倾/防脱固定。'),
('装入 PCIe 延长线和显卡','先实测母槽并完成适配固定；母槽不能接触裸露导电件，也不能只用胶带承重。延长线按厂家弯折要求接入主板。显卡完全插入并锁扣，壳体边缘落在垫座可承力位置。','必须额外完成显卡挡板的机械锁紧与防倾固定。若母槽孔位、挡板固定或垫座位置尚未适配，停在此步，不通电。不要让热管、风扇、PCB 或元件承担支撑载荷。'),
('安装双风扇组件','风扇立梁先用 4 颗 M3×6 连接到立柱 3 的四个侧孔。两块风扇框各用 2 颗 M3×6 连接到立梁。每只风扇用 4 套 M4 贯穿螺栓、垫片与普通螺母固定到框上。','M3 共 8 颗；M4 共 8 套。上风扇对应 CPU/内存，下风扇对应显卡。按风扇壳体气流箭头，让空气由内存侧吹向主板后接口方向；不要只凭叶片外观判断。'),
('理线、复查后试运行','在接通市电前检查所有机械固定，布线远离叶片与发热部位。核对风扇接口电流、显卡供电连接和延长线插入状态。完成下列检查后，再按硬件原厂说明开机并观察温度与风向。','初次运行先低负载观察；显卡穿透风扇热风仍可能朝主板，需要实测确认。若晃动、异响、局部塑料变形或温度异常，断电检查。')]
step_html=''.join(f'<article class="step"><span class="num">{i}</span><h3>{a}</h3><p>{b}</p><p class="muted">{c}</p></article>' for i,(a,b,c) in enumerate(steps,1))
checktext=['材料规格已核对：M3 / H4.5 / 外径约 5 mm，未混用 H8','所有 62 个热熔螺母已压入、冷却、试牙且没有松动','19 个打印件清点齐全，编号与 V09 一致','框架底部平稳，立柱垂直，各连接贴合，塑料未裂','9 个主板固定孔自然对齐，凸台未碰元件或焊点','主板、散热器与显卡实物之间没有碰撞；55 mm 基准间距已核对','母槽实物已适配并固定；显卡挡板及壳体有可靠承力与防倾固定','电源已用固定带约束，进出风口通畅且电源线出口无挤压','两只风扇方向正确，线缆与叶片之间有余量','风扇电流、供电插头及 PCIe 延长线连接已核对','实际放置空间容纳机架、插头和线缆弯曲，且有进出风余量']
checks=''.join(f'<label class="check"><input type="checkbox" aria-label="{t}">{t}</label>' for t in checktext)
diagrams=''.join(f'<div class="card"><h3>立柱 {i} · {rows[i-1][3]} 个</h3>{svg_post(i)}<small>'+(['底部 20/35：朝左侧；上部 160/184：朝左外侧。','底部 20/35：朝左侧。','底部 20/35：朝左侧；160/184 及风扇孔 50/130/236/290：朝右外侧。'][i-1])+'</small></div>' for i in (1,2,3))
html=html.replace('PHOTO',photo).replace('INSERT_TABLE',table).replace('POST_DIAGRAMS',diagrams).replace('STEPS',step_html).replace('CHECKS',checks).replace('PLATES',plate_table)
(out/'Style2_V09_Assembly_Manual.html').write_text(html,encoding='utf-8')
print('Created manual',len(html),'characters; 62 inserts; 10 assembly stages; 11 checklist items.')
