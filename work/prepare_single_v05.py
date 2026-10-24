from pathlib import Path
import ast
out=Path('outputs/Single-Bracket-v05');(out/'SingleBracket').mkdir(parents=True,exist_ok=True)
s=Path('outputs/Single-Bracket-v04/SingleBracket/SingleBracket.py').read_text('utf-8').replace('V04','V05').replace('v04','v05')
s=s.replace("rect(main,-98,0,-6,6,-12,24", "rect(main,-98,0,-6,6,-16,32")
s=s.replace("],-4,8,JOIN,'Central triangular web 8 mm'", "],-16,8,JOIN,'Side flush triangular web 8 mm'")
s=s.replace("],-4,8,CUT,'Web lightening window'", "],-16,8,CUT,'Web lightening window'")
s=s.replace("rect(main,-100,0,-96,12,-12,24", "rect(main,-100,0,-96,12,-16,32")
# Blunt the internal window corners rather than a sharp right-angle cutout.
s=s.replace("[(-14,-77),(-14,-10),(-74,-10)]", "[(-14,-72),(-14,-14),(-18,-10),(-69,-10),(-71,-12),(-16,-74)]")
(out/'SingleBracket/SingleBracket.py').write_text(s,encoding='utf-8')
export=Path(r'C:\Users\liu\Documents\Codex\2026-10-18\referenced-chatgpt-conversation-this-is-an\outputs\Single-Bracket-v05')
s=s.replace('OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))','OUT='+ascii(str(export)))
ast.parse(s)
Path('work/single_v05_execute.py').write_text(s,encoding='utf-8')
