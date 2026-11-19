# -*- coding: utf-8 -*-
"""按章输出节标题 + 表/图题清单，用于快速摸清全书结构。"""
import io, re, sys

p = r'20-md\搅拌与混合设备设计选用手册_陈志平_第1版_2004\搅拌与混合设备设计选用手册_陈志平_第1版_2004.md'
L = io.open(p, encoding='utf-8').read().split('\n')
lo = int(sys.argv[1]); hi = int(sys.argv[2])
for i in range(lo - 1, min(hi, len(L))):
    s = L[i]
    if re.match(r'^## ', s) or re.match(r'^### ', s):
        print('%5d %s' % (i + 1, s))
    elif re.match(r'^\| 表\s*\d+', s) or re.match(r'^表\s*\d+', s):
        print('%5d   [表] %s' % (i + 1, s[:60]))
    elif re.match(r'^图\s*\d+', s):
        print('%5d   [图] %s' % (i + 1, s[:60]))
