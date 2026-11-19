# -*- coding: utf-8 -*-
"""从 MinerU middle_json 生成「图X.Y → PDF 页码 / 是否有导出图」对照表。"""
import io, json, os, re, glob

Root = r'D:\Shervon_KnowledgeBase'
src = glob.glob(os.path.join(Root, r'40-scratch\_pageidx-气液搅拌釜', '*.json'))
assert src, 'no json'
path = src[0]
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

CAP = re.compile(r'图\s*(\d+)\s*[.\-－—]\s*(\d+)\s*(.*)')
rows = []
img_blocks = 0
img_with_file = 0
for pg in pages:
    idx = pg.get('page_idx')
    for b in pg.get('blocks') or []:
        t = b.get('type')
        if t in ('image', 'chart'):
            img_blocks += 1
            for ch in (b.get('content') or []):
                if isinstance(ch, dict) and ch.get('image_path'):
                    img_with_file += 1
        txt = btext(b)
        m = CAP.match(txt.replace(' ', '')) if txt else None
        if m and len(txt) <= 120:
            num = '图%s.%s' % (m.group(1), m.group(2))
            rows.append({'fig': num, 'caption': ' '.join(txt.split()), 'page': (idx + 1) if idx is not None else None})

# 去重：同图号取首次出现页
seen = {}
for r in rows:
    seen.setdefault(r['fig'], r)
ordered = sorted(seen.values(), key=lambda r: (r['page'] or 0))

out = os.path.join(Root, r'40-scratch\figure-pages-气液搅拌釜.csv')
with io.open(out, 'w', encoding='utf-8-sig', newline='') as f:
    f.write('图号,PDF页码,图题\n')
    for r in ordered:
        cap = r['caption'].replace('"', '""')
        f.write('%s,%s,"%s"\n' % (r['fig'], r['page'] if r['page'] else '', cap))

print('json =', path)
print('pages =', len(pages), 'captions =', len(rows), 'unique =', len(ordered))
print('image/chart blocks =', img_blocks, ' with image_path =', img_with_file)
print('csv =', out)
for r in ordered[:8]:
    print(' ', r['fig'], 'p.', r['page'], r['caption'][:40])
