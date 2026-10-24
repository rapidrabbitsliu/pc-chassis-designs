from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

out=Path('outputs/board-alignment');out.mkdir(parents=True,exist_ok=True)
im=Image.new('RGB',(1400,1190),'white');d=ImageDraw.Draw(im)
FONT='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(FONT,n)
def text(x,y,s,size=28,fill='#233044',anchor='mm'):
    d.text((x,y),s,font=font(size),fill=fill,anchor=anchor,align='center',spacing=10)
S=3.3;BX=180;BY=190
def p(u,v):return BX+u*S,BY+v*S
def rect(u0,v0,u1,v1,fill,outline='#536375',width=3,r=8):
    d.rounded_rectangle((*p(u0,v0),*p(u1,v1)),radius=r,fill=fill,outline=outline,width=width)
def arrow(a,b,color,width=5):
    import math
    d.line((a,b),fill=color,width=width)
    ang=math.atan2(b[1]-a[1],b[0]-a[0]);L=15
    q=[b,(b[0]-L*math.cos(ang-.5),b[1]-L*math.sin(ang-.5)),(b[0]-L*math.cos(ang+.5),b[1]-L*math.sin(ang+.5))]
    d.polygon(q,fill=color)

text(700,45,'主板位置确认 · 元件面俯视',40)
text(700,84,'后置接口朝上；相对位置示意，不作尺寸或加工依据',25,'#677486')
rect(0,0,304.8,243.84,'#f3f8f4','#344d43',4,18)
# After a clockwise rotation of the user's component-side drawing, I/O is top-right.
rect(146,-10,304.8,-1,'#dce4ed','#536375',3,3)
text(*p(226,-21),'主板后置接口 / DP',27)
arrow(p(226,-12),p(226,-4),'#536375',3)

# CPU and four horizontal DIMM sockets on the right.
rect(185,65,260,135,'#fff0d8','#b37720',4,10)
rect(196,77,249,123,'#fff8ec','#cfaa6e',2,6)
text(*p(222.5,98),'CPU',39,'#845717')
for v in (184,194,204,214):
    rect(150,v-2.6,285,v+2.6,'#e8e0f5','#795b9d',3,2)
    d.line((*p(155,v),*p(280,v)),fill='#aa96c0',width=2)
text(*p(218,225),'内存（4 条）',28,'#684984')

# Two long PCIe sockets. The primary slot receives the GPU.
rect(122.4,42,130.4,147,'#d7ecff','#1676bf',4,3)
rect(124.8,47,128,141,'#7eb3df','#1676bf',2,1)
rect(119.5,142,133.5,150,'#d7ecff','#1676bf',3,3)
rect(56,42,64,147,'#e6e9ee','#7a8492',3,3)
rect(58.4,47,61.6,141,'#bdc5cf','#7a8492',2,1)
rect(53,142,67,150,'#e6e9ee','#7a8492',3,3)
text(*p(60,158),'第二条长 PCIe',25,'#5c6877')
text(*p(120,185),'显卡插槽',29,'#1268a9')
text(*p(120,197),'第一条长 PCIe',22,'#1268a9')
text(*p(71,87),'显卡插这里',27,'#1268a9',anchor='lm')
arrow(p(109,97),p(122,97),'#1676bf',4)
text(*p(126.4,-21),'显卡显示接口侧',25,'#1268a9')
arrow(p(126.4,-12),p(126.4,0),'#1676bf',3)

# Standard hole pattern rotated together with the source drawing. Rear-right is staggered.
holes=[(16.51,10.16),(140.97,10.16),(298.45,33.02),
       (16.51,165.10),(140.97,165.10),(298.45,165.10),
       (16.51,237.49),(140.97,237.49),(298.45,237.49)]
for i,(u,v) in enumerate(holes,1):
    x,y=p(u,v)
    d.ellipse((x-21,y-21,x+21,y+21),fill='white',outline='#d63838',width=5)
    text(x,y-1,str(i),24,'#b92525')

text(700,1053,'红圈 1–9：主板安装孔；右后方 3 号孔与 1、2 号孔不齐平',26,'#a82d2d')
text(700,1110,'主板前缘（与后置接口相对的一边）',27)
text(700,1155,'仅确认方向和相对位置；本次不改 Fusion 模型',23,'#677486')
im.save(out/'motherboard-top-alignment.png')
print(str((out/'motherboard-top-alignment.png').resolve()))
