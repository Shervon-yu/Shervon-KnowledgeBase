# -*- coding: utf-8 -*-
"""给本书 md 末尾追加「章节/图号 → PDF 页码」附录（幂等，章节按章号去重）。"""
import io, json, os, re, glob

Root = r'D:\Shervon_KnowledgeBase'
book = '气液搅拌釜γ-CT测量、成像与模拟_刘跃进、韩路长_第1版_2014'
md = os.path.join(Root, r'20-md', book, book + '.md')
js = glob.glob(os.path.join(Root, r'40-new\_pageidx-气液搅拌釜', '*.json'))
assert js, 'middle json missing'

doc = json.load(io.open(js[0], encoding='utf-8'))
pages = doc.get('pages') or []

def btext(b):
    c = b.get('content')
    if isinstance(c, str):
        return c.strip()
    return ' '.join(str(x.get('content')).strip() for x in (c or []) if isinstance(x, dict) and x.get('content'))

CHAP = re.compile(r'^第\s*(\d+)\s*章\s*(.*)$')
SEC = re.compile(r'^(\d+(?:\.\d+)*)\s+(\S.*)$')
FIG = re.compile(r'图\s*(\d+)\s*[.\-－—]\s*(\d+)')

chapters = {}  # 章号 -> (页码, 标题)
sections = {}  # '2.6.1 闪烁体' -> 页码
fig_pages = {}

for pg in pages:
    pno = (pg.get('page_idx') or 0) + 1
    if pno < 11:
        continue
    for b in pg.get('blocks') or []:
        txt = btext(b)
        if not txt:
            continue
        h = ' '.join(txt.split())
        if len(h) <= 60 and '。' not in h:
            m = CHAP.match(h)
            if m:
                n = int(m.group(1))
                title = re.sub(r'\s+', ' ', m.group(2)).strip()
                if n not in chapters or pno < chapters[n][0]:
                    if title or n not in chapters:
                        chapters[n] = (pno, title or chapters.get(n, (pno, ''))[1])
                continue
            m = SEC.match(h)
            if m and len(h) <= 45:
                key = re.sub(r'\s+', ' ', h)
                if key not in sections or pno < sections[key]:
                    sections[key] = pno
        for m in FIG.finditer(txt):
            f = '图%s.%s' % (m.group(1), m.group(2))
            if f not in fig_pages or pno < fig_pages[f]:
                fig_pages[f] = pno

def sec_key(s):
    m = re.match(r'^(\d+(?:\.\d+)*)', s)
    parts = [int(x) for x in m.group(1).split('.')]
    return (parts + [0] * 4)[:4]

def fig_key(f):
    m = re.match(r'图(\d+)\.(\d+)', f)
    return (int(m.group(1)), int(m.group(2)))

lines = ['', '<!-- page-appendix -->', '## 附录 A 页码对照（PDF 页码）', '',
         '> 由 MinerU `middle_json` 的逐页文本反查生成；页码为 PDF 阅读器物理页（非书印刷页码）。章节取正文首次出现页（跳过前 10 页封面/目录），图取首次出现页。', '',
         '### A.1 章节', '', '| 章节 | PDF 页 |', '|:---|:---:|']
for n in sorted(chapters):
    p, title = chapters[n]
    label = ('第%d章 %s' % (n, title)).strip()
    lines.append('| %s | %d |' % (label.replace('|', '\\|'), p))
for k in sorted(sections, key=sec_key):
    lines.append('| %s | %d |' % (k.replace('|', '\\|'), sections[k]))
lines += ['', '### A.2 图', '', '| 图号 | PDF 页 |', '|:---|:---:|']
for f in sorted(fig_pages, key=fig_key):
    lines.append('| %s | %d |' % (f, fig_pages[f]))
lines.append('')
block = '\n'.join(lines)

text = io.open(md, encoding='utf-8').read()
if '<!-- page-appendix -->' in text:
    text = text[:text.index('<!-- page-appendix -->')].rstrip() + '\n'
text = text.rstrip() + '\n' + block
io.open(md, 'w', encoding='utf-8', newline='').write(text)
print('chapters=%d sections=%d figs=%d chars=%d' % (len(chapters), len(sections), len(fig_pages), len(text)))
print(' 第3章 =', chapters.get(3), ' 2.6.1 =', sections.get('2.6.1 闪烁体'))
