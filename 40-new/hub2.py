# -*- coding: utf-8 -*-
import io
p = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\气液两相搅拌.md'
t = io.open(p, encoding='utf-8').read()
m = '## 相关'
a = "## 机理\n\n气泡破碎与凝并的机理、以及固液「润湿—打散—悬浮」三段过程，见 [[搅拌-悬浮与分散机理]]。\n\n## 相关"
assert m in t
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(m, a, 1))
print('ok')
