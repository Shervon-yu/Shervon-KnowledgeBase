# -*- coding: utf-8 -*-
"""比对「git 里的旧 md」与「重建后的新 md」，输出逐行映射 old->new（1 基）。"""
import subprocess, io, difflib, json, sys

p = '20-md/搅拌与混合设备设计选用手册_陈志平_第1版_2004/搅拌与混合设备设计选用手册_陈志平_第1版_2004.md'
old = subprocess.check_output(['git', 'show', '7c6f97c:' + p]).decode('utf-8').split('\n')
new = io.open(p, encoding='utf-8').read().split('\n')
print('old lines', len(old), 'new lines', len(new))
sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
mapping = {}
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1):
            mapping[i1 + k + 1] = j1 + k + 1
    else:
        print(tag, 'old', i1 + 1, i2, 'new', j1 + 1, j2,
              '| old:', (old[i1][:44] if i1 < len(old) else ''),
              '| new:', (new[j1][:44] if j1 < len(new) else ''))
        # 非等长块：仅当长度相同可按位移映射
        if (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                mapping[i1 + k + 1] = j1 + k + 1
json.dump(mapping, io.open('40-new/line-map-20160-to-20166.json', 'w', encoding='utf-8'))
ident = sum(1 for k, v in mapping.items() if k == v)
print('mapped', len(mapping), 'identity', ident)
for probe in (1012, 1484, 17178, 1518, 14944, 15228, 19166):
    print(probe, '->', mapping.get(probe))
