from pathlib import Path
p=Path('work/finish_single_v05.py');s=p.read_text('utf-8');s='\n'.join(x for x in s.splitlines() if not x.startswith("p=out/'SingleBracket/SingleBracket.py'"));s=s.replace("'version':'0.4.0'","'version':'0.5.0'");p.write_text(s,encoding='utf-8')
