# -*- coding: utf-8 -*-
import io

p = r'D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-lint.ps1'
s = io.open(p, encoding='utf-8-sig').read()
old = "Where-Object { $skip -notcontains $_.Name })"
new = "Where-Object { $skip -notcontains $_.Name -and $_.Name -notmatch '^index(-.+)?\\.md$' })"
assert old in s, 'lint pattern not found'
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8-sig', newline='\n').write(s)

p2 = r'D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-index.ps1'
t = io.open(p2, encoding='utf-8-sig').read()
t = t.replace('返回总目录：[[index]]', '返回总目录：index.md')
io.open(p2, 'w', encoding='utf-8-sig', newline='\n').write(t)
print('ok')
