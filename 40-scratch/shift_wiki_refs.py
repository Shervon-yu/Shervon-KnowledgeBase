# -*- coding: utf-8 -*-
"""把本书三页的 #L 引用从 20160 行版平移到 20166 行版（仅这三页，避免误伤其他书的引用）。"""
import io, json, re

mapping = {int(k): v for k, v in json.load(io.open('40-scratch/line-map-20160-to-20166.json', encoding='utf-8')).items()}
files = [
    r'50-wiki\concepts\混合设备-分类与选型.md',
    r'50-wiki\concepts\磁力传动搅拌设备.md',
    r'50-wiki\sources\搅拌与混合设备设计选用手册.md',
]
for f in files:
    t = io.open(f, encoding='utf-8').read()
    hits, miss = [], []

    def sub(m):
        old = int(m.group(1))
        if old in mapping:
            new = mapping[old]
            if new != old:
                hits.append((old, new))
            return '#L%d' % new
        miss.append(old)
        return m.group(0)

    t2 = re.sub(r'#L(\d+)', sub, t)
    io.open(f, 'w', encoding='utf-8', newline='\n').write(t2)
    print(f, 'moved', len(hits), 'unchanged/untouched', len(miss),
          'sample', hits[:5], 'miss', miss[:5])
