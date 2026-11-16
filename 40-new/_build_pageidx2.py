# -*- coding: utf-8 -*-
"""按页扫描 middle_json：每页出现过哪些 图X.Y、是否有题注块，生成对照表。"""
import io, json, os, re, glob
from collections import defaultdict

Root = r'D:\Shervon_KnowledgeBase'
path = glob.glob(os.path.join(Root, r'40-new\_pageidx-气液搅拌釜', '*.json'))[0]
doc = json.load(io.open(path, encoding='utf-8'))
pages = doc.get('pages') or []

def btext(b):
    c = b.get('content')
    if isinstance(c, str):
        return c.strip()
    out = []
    for x in (c or []):
        if isinstance(x, dict) and x.get('content'):
            out.append(str(x['content']))
    return ' '.join(s.strip() for s in out if s and s.strip())

FIG = re.compile(r'图\s*(\d+)\s*[.\-－—]\s*(\d+)')
CAPBLOCK = re.compile(r'^\s*图\s*\d+\s*[.\-－—]\s*\d+\s*\S')

page_figs = defaultdict(list)     # fig -> [pages]
caption_pages = defaultdict(list) # fig -> [pages] 题注块所在页
for pg in pages:
    idx = pg.get('page_idx')
    pno = (idx + 1) if idx is not None else None
    for b in pg.get('blocks') or []:
        txt = btext(b)
        if not txt:
            continue
        for m in FIG.finditer(txt):
            fig = '图%s.%s' % (m.group(1), m.group(2))
            if pno not in page_figs[fig]:
                page_figs[fig].append(pno)
        if len(txt) <= 100 and '。' not in txt and CAPBLOCK.match(txt):
            m = FIG.search(txt)
            if m:
                fig = '图%s.%s' % (m.group(1), m.group(2))
                if pno not in caption_pages[fig]:
                    caption_pages[fig].append(pno)

def key(f):
    a, b = re.match(r'图(\d+)\.(\d+)', f).groups()
    return (int(a), int(b))

out = os.path.join(Root, r'40-new\figure-pages-气液搅拌釜.csv')
with io.open(out, 'w', encoding='utf-8-sig', newline='') as f:
    f.write('图号,题注页,首次出现页,全部出现页\n')
    for fig in sorted(page_figs, key=key):
        cap = caption_pages.get(fig, [])
        allp = sorted(p for p in page_figs[fig] if p)
        f.write('%s,%s,%s,%s\n' % (fig, cap[0] if cap else '', allp[0] if allp else '', '/'.join(map(str, allp))))

print('pages=%d figures=%d with_caption=%d' % (len(pages), len(page_figs), len(caption_pages)))
print('csv =', out)
for fig in sorted(page_figs, key=key)[:12]:
    print(' ', fig, 'cap=', caption_pages.get(fig, ['-'])[:2], 'pages=', page_figs[fig][:5])
