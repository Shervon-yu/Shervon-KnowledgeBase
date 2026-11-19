# -*- coding: utf-8 -*-
import io
p = r'D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-index.ps1'
t = io.open(p, encoding='utf-8-sig').read()
old = '"| $($g.Name) | $($g.Count) | [[$([IO.Path]::GetFileNameWithoutExtension($fn))]] |"'
new = '"| $($g.Name) | $($g.Count) | $fn |"'
assert old in t, 'row pattern not found'
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8-sig', newline='\n').write(t)
print('ok')
