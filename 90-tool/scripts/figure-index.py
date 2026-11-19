# -*- coding: utf-8 -*-
"""生成图索引：30-wiki/figures-<入库夹名>.md
每条：行号 | 图名 | 所在节 | 是否整页图 | 是否有题
"""
import io, os, re, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument('-Book', required=True, help='入库夹名')
ap.add_argument('--Root', default=r'D:\Shervon_KnowledgeBase')
a = ap.parse_args()
book = a.Book
ROOT = a.Root
md = os.path.join(ROOT, '20-md', book, book + '.md')
L = io.open(md, encoding='utf-8').read().split('\n')

sec = ''
rows = []
for i, s in enumerate(L, 1):
    if s.startswith('## ') or s.startswith('### '):
        sec = re.sub(r'#+\s*', '', s).strip()
    for m in re.finditer(r'!\[\]\(图片/([^)]+)\)', s):
        name = m.group(1)
        wholepage = bool(re.match(r'整页图-p\d+_\d+', name))
        noCap = wholepage or name.startswith('未命名图') or re.match(r'^[a-z] ', name) is not None
        rows.append((i, name, sec, '整页' if wholepage else '', '无题' if noCap else '有题'))

out = [f'# 图索引：{book}', '',
       f'- 图片总数：{len(rows)}',
       f'- 有题图：{sum(1 for r in rows if r[4] == "有题")}',
       f'- 无题图（含整页图）：{sum(1 for r in rows if r[4] == "无题")}',
       f'- 整页图：{sum(1 for r in rows if r[3] == "整页")}',
       '- 说明：无题图是 OCR 未识别到图题（多为整页扫描图或子图拆散），非缺图；缺图清单见 40-new/figures-report-*.json',
       '',
       '| 行号 | 图名 | 所在节 | 类型 | 题注 |',
       '|---|---|---|---|---|']
for i, name, sec, whole, cap in rows:
    out.append(f'| {i} | {name} | {sec} | {whole} | {cap} |')

dst = os.path.join(ROOT, '30-wiki', f'figures-{book}.md')
io.open(dst, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print(f'rows={len(rows)} whole={sum(1 for r in rows if r[3]=="整页")} nocap={sum(1 for r in rows if r[4]=="无题")}')
print(dst)
