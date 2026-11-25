# -*- coding: utf-8 -*-
"""覆盖率门：本书每个 h3 小节是否被至少一条 wiki 引用（#L 行号落在该节区间内）覆盖。"""
import io, os, re, glob, json

ROOT = r'D:\Shervon_KnowledgeBase'
MD = os.path.join(ROOT, r'20-md\搅拌与混合设备设计选用手册_陈志平_第1版_2004\搅拌与混合设备设计选用手册_陈志平_第1版_2004.md')
lines = io.open(MD, encoding='utf-8').read().split('\n')

secs = []
pat_h2 = re.compile(r'^## (.+)$')
pat_h3 = re.compile(r'^### (.+)$')
for i, l in enumerate(lines, 1):
    m2, m3 = pat_h2.match(l), pat_h3.match(l)
    if m2 or m3:
        secs.append({'level': 2 if m2 else 3, 'title': (m2 or m3).group(1).strip(), 'start': i})
for k, s in enumerate(secs):
    s['end'] = secs[k+1]['start'] - 1 if k + 1 < len(secs) else len(lines)
    body = '\n'.join(lines[s['start']-1:s['end']])
    s['tables'] = body.count('|---')
    s['images'] = len(re.findall(r'!\[\]\(图片/', body))
    s['chars'] = len(body)

# 只统计引用本书的 wiki 页
cited = set()
for f in glob.glob(os.path.join(ROOT, '50-wiki', '**', '*.md'), recursive=True):
    if os.path.basename(f) in ('index.md', 'log.md', '_lint.md') or os.path.basename(f).startswith('index-'):
        continue
    t = io.open(f, encoding='utf-8').read()
    if '搅拌与混合设备设计选用手册' not in t:
        continue
    for m in re.finditer(r'#L(\d+)', t):
        cited.add(int(m.group(1)))

h3 = [s for s in secs if s['level'] == 3]
for s in h3:
    s['hits'] = sum(1 for c in cited if s['start'] <= c <= s['end'])
    s['covered'] = s['hits'] > 0

cov = sum(1 for s in h3 if s['covered'])
print('sections=%d covered=%d uncovered=%d' % (len(h3), cov, len(h3)-cov))
print('--- uncovered ---')
for s in h3:
    if not s['covered']:
        print('%s | L%d-%d | p%d | tab=%d img=%d chars=%d' % (s['title'], s['start'], s['end'], (s['start']), s['tables'], s['images'], s['chars']))
json.dump([{k: v for k, v in s.items()} for s in h3], io.open(os.path.join(ROOT, '40-scratch', 'coverage.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
