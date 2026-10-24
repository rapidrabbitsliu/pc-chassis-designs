from pathlib import Path
import shutil,zipfile
src=Path('outputs/Single-Bracket-v04')
out=Path(r'C:\Users\liu\Documents\Codex\2026-10-18\referenced-chatgpt-conversation-this-is-an\outputs\Single-Bracket-v04')
shutil.copytree(src,out,dirs_exist_ok=True)
with zipfile.ZipFile(out.parent/'Single-Bracket-v04.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in out.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(out.parent))
shutil.copy2(out.parent/'Single-Bracket-v04.zip','outputs/Single-Bracket-v04.zip')
