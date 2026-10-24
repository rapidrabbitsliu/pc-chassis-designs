from pathlib import Path
s=Path('work/finish_single_v04.py').read_text('utf-8-sig')
s=s.replace('Single-Bracket-v04','Single-Bracket-v05').replace('_v04_','_v05_').replace('56072.09408','61408.09408')
s=s.replace("normal=(-a[0],a[1],-a[2]);pts=[(-a[k]+7,a[k+1]+108,-a[k+2]+16)","normal=(a[0],a[1],a[2]);pts=[(a[k]+100,a[k+1]+108,a[k+2]+16)")
Path('work/finish_single_v05.py').write_text(s,encoding='utf-8')
out=Path('outputs/Single-Bracket-v05')
origin=Path(r'C:\Users\liu\Documents\Codex\2026-10-18\referenced-chatgpt-conversation-this-is-an\outputs\Single-Bracket-v05')
import shutil
for p in origin.iterdir():
    if p.is_file():shutil.copy2(p,out/p.name)
