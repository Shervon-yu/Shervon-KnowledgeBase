# -*- coding: utf-8 -*-
"""覆盖率门：一本书的每个 h3 小节是否被 wiki 页至少引用一次。

用法：
  python 90-tool/scripts/coverage.py -Book "<入库夹名>"           # 报告
  python 90-tool/scripts/coverage.py -Book "<入库夹名>" --strict   # 未覆盖 >0 则 exit 1

判定：wiki 页（含该书名的页）里出现的 #L 行号，落在该节 [start,end] 区间内即算覆盖。
"""
import io, os, re, sys, glob, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-Book', required=True)
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--json', default='')
    a = ap.parse_args()

    book = a.Book
    md = os.path.join(ROOT, '20-md', book, book + '.md')
    if not os.path.exists(md):
        print('md 不存在：' + md)
        return 2
    lines = io.open(md, encoding='utf-8').read().split('\n')

    secs = []
    for i, l in enumerate(lines, 1):
        m2 = re.match(r'^## (.+)$', l)
        m3 = re.match(r'^### (.+)$', l)
        if m2 or m3:
            secs.append({'level': 2 if m2 else 3, 'title': (m2 or m3).group(1).strip(), 'start': i})
    for k, s in enumerate(secs):
        s['end'] = secs[k + 1]['start'] - 1 if k + 1 < len(secs) else len(lines)
        body = '\n'.join(lines[s['start'] - 1:s['end']])
        s['tables'] = body.count('|---')
        s['images'] = len(re.findall(r'!\[\]\(图片/', body))

    cited = set()
    for f in glob.glob(os.path.join(ROOT, '30-wiki', '**', '*.md'), recursive=True):
        name = os.path.basename(f)
        if name in ('index.md', 'log.md', '_lint.md', 'glossary.md') or name.startswith('index-'):
            continue
        t = io.open(f, encoding='utf-8').read()
        if book.split('_')[0] not in t:
            continue
        for m in re.finditer(r'#L(\d+)', t):
            cited.add(int(m.group(1)))

    h3 = [s for s in secs if s['level'] == 3]
    for s in h3:
        s['hits'] = sum(1 for c in cited if s['start'] <= c <= s['end'])
        s['covered'] = s['hits'] > 0
    cov = sum(1 for s in h3 if s['covered'])
    print('book=%s sections=%d covered=%d uncovered=%d' % (book, len(h3), cov, len(h3) - cov))
    for s in h3:
        if not s['covered']:
            print('  UNCOVERED %s | L%d-%d | tab=%d img=%d' % (s['title'], s['start'], s['end'], s['tables'], s['images']))
    if a.json:
        json.dump(h3, io.open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if a.strict and cov < len(h3):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
