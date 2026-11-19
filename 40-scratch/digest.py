# -*- coding: utf-8 -*-
"""输出全书每节标题 + 该节首句（跳过空行/图表/公式），供快速建页。"""
import io, re

p = r'20-md\搅拌与混合设备设计选用手册_陈志平_第1版_2004\搅拌与混合设备设计选用手册_陈志平_第1版_2004.md'
L = io.open(p, encoding='utf-8').read().split('\n')
out = []
i = 0
while i < len(L):
    s = L[i]
    if re.match(r'^#{2,3} ', s):
        out.append('%d\t%s' % (i + 1, s))
        j = i + 1
        n = 0
        while j < len(L) and n < 1:
            t = L[j].strip()
            if (t and not t.startswith('<!--') and not t.startswith('|') and not t.startswith('$$')
                    and not t.startswith('!') and not t.startswith('**') and t != s.lstrip('# ')):
                out.append('    ' + t[:110])
                n += 1
            j += 1
    i += 1
io.open('40-scratch/outline-digest.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('lines', len(out))
