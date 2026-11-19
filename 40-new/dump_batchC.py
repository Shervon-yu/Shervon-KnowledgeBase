# -*- coding: utf-8 -*-
import io
md = r'D:\Shervon_KnowledgeBase\20-md\搅拌与混合设备设计选用手册_陈志平_第1版_2004\搅拌与混合设备设计选用手册_陈志平_第1版_2004.md'
L = io.open(md, encoding='utf-8').read().split('\n')
rng = [(8136, 8300), (10310, 10460), (10533, 10680), (11056, 11180),
       (12459, 12620), (12760, 12940), (14072, 14260), (14400, 14600)]
out = []
for a, b in rng:
    out.append('===== %d-%d =====' % (a, b))
    for i in range(a - 1, min(b, len(L))):
        s = L[i]
        if s.startswith('![](') or s.startswith('<!-- page:'):
            continue
        if not s.strip():
            continue
        if s.count('|') > 8:
            s = s[:150] + ' …'
        out.append('%d| %s' % (i + 1, s))
io.open(r'D:\Shervon_KnowledgeBase\40-new\dump-batchC.txt', 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
print(len(out))
