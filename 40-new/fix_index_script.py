# -*- coding: utf-8 -*-
p = r'D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-index.ps1'
s = open(p, encoding='utf-8-sig').read()
old = 'Sort-Object -Property @{Expression={$_.Count};Descending=$true} -Property Name'
new = 'Sort-Object -Property @{Expression={$_.Count};Descending=$true}, Name'
print('found', old in s)
s = s.replace(old, new)
open(p, 'w', encoding='utf-8-sig', newline='\n').write(s)
