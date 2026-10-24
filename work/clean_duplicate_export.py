from pathlib import Path
root=Path('D:/personal-files/docs/ChatGPT')
name='\u7535\u8111\u4e0a\u6d1e\u6d1e\u677f'.encode('utf-8').decode('latin1')
wrong=root/name
folder=wrong/'outputs/Single-Bracket-v04'
assert wrong.resolve().parent==root.resolve() and wrong.name==name
allowed={'raw_Bracket.stl','raw_AntiLiftKey.stl','Single_Bracket_v04.f3d','verification.json'}
if folder.is_dir():
    entries=list(folder.iterdir())
    assert all(p.is_file() and p.name in allowed for p in entries)
    for p in entries:p.unlink()
    folder.rmdir()
    for p in (wrong/'outputs',wrong):
        if p.is_dir() and not any(p.iterdir()):p.rmdir()
print('Removed duplicate exports created by path encoding; correct project files preserved.')
