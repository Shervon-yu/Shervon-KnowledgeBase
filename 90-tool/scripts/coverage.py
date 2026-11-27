# -*- coding: utf-8 -*-
"""覆盖率门（v3.25）：引用覆盖 + 判定覆盖。

用法：
  python 90-tool/scripts/coverage.py -Book "<入库夹名>"                    # 引用覆盖报告
  python 90-tool/scripts/coverage.py -Book "<入库夹名>" --strict            # 未引用 >0 则 exit 1
  python 90-tool/scripts/coverage.py -Book "<入库夹名>" --judged            # 判定覆盖报告
  python 90-tool/scripts/coverage.py -Book "<入库夹名>" --judged --strict   # 判定有问题则 exit 1

引用覆盖：wiki 页（含该书名的页）里出现的 #L 行号，落在该节 [start,end] 区间内即算覆盖（原逻辑，未改）。

判定覆盖（--judged，rules.md §16 第 8 条，v3.25 起新书强制）：
  1. 本书 md 每个 ### 小节在 sources 页判定表里有记录（区间相交）；
  2. 判定表「材料」行「去向」非空，且指向已存在的页面文件；
  3. 每页 sources.lines 非空、格式 #L起-#L止、起 <= 止、止 <= md 行数。
"""
import io, os, re, sys, glob, json, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAGE_DIRS = ('pages', 'notes', 'comparisons', 'openq')
JUDGE_VALUES = ('材料', '丢弃', '未建页')


def md_lines(book):
    p = os.path.join(ROOT, '20-md', book + '.md')
    if not os.path.exists(p):
        return None
    return io.open(p, encoding='utf-8').read().split('\n')


def sections(lines):
    secs = []
    for i, l in enumerate(lines, 1):
        m2 = re.match(r'^## (.+)$', l)
        m3 = re.match(r'^### (.+)$', l)
        if m2 or m3:
            secs.append({'level': 2 if m2 else 3,
                         'title': (m2 or m3).group(1).strip(),
                         'start': i})
    for k, s in enumerate(secs):
        s['end'] = secs[k + 1]['start'] - 1 if k + 1 < len(secs) else len(lines)
        body = '\n'.join(lines[s['start'] - 1:s['end']])
        s['tables'] = body.count('|---')
        s['images'] = len(re.findall(r'!\[[^\]]*\]\([^)]*图片/', body))
    return secs


def parse_range(text):
    """'L5100-L5140' / '#L5100-#L5140' / 'L5100' -> (a,b)。"""
    m = re.search(r'L(\d+)\s*#?\s*[-\u2014~]\s*#?\s*L(\d+)', text)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return (a, b) if a <= b else (b, a)
    m = re.search(r'L(\d+)', text)
    if m:
        return (int(m.group(1)), int(m.group(1)))
    return None


def find_sources_page(book):
    key = book.split('_')[0]
    for f in glob.glob(os.path.join(ROOT, '30-wiki', 'sources', '*.md')):
        t = io.open(f, encoding='utf-8').read()
        if key in os.path.basename(f) or key in t[:2000]:
            return f, t
    return None, ''


def parse_judge_table(text):
    """解析 sources 页判定表，返回 [[节, 行范围, 判定, 摘要, 去向], ...]。"""
    rows = []
    in_tbl = False
    for l in text.split('\n'):
        s = l.strip()
        if not s.startswith('|'):
            if in_tbl and rows:
                break
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        joined = ' '.join(cells)
        if '行范围' in joined and '判定' in joined:
            in_tbl = True
            continue
        if in_tbl and re.match(r'^[\s|:\-]+$', s):
            continue
        if in_tbl and len(cells) >= 5:
            rows.append(cells[:5])
    return rows


def page_files(book):
    key = book.split('_')[0]
    out = []
    for d in PAGE_DIRS:
        for f in glob.glob(os.path.join(ROOT, '30-wiki', d, '**', '*.md'), recursive=True):
            t = io.open(f, encoding='utf-8').read()
            if key in t or key in os.path.basename(f):
                out.append((f, t))
    return out


def source_entries(fm):
    """把 frontmatter 的 sources 列表拆成条目，每条纹一条。"""
    entries = []
    cur = None
    for line in fm.split('\n'):
        if re.match(r'\s*-\s*book\s*:', line):
            if cur is not None:
                entries.append(cur)
            cur = [line]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        entries.append(cur)
    return entries


def check_judged(book, h3, total):
    issues = []
    sp, st = find_sources_page(book)
    if not sp:
        issues.append('找不到 sources 页（判定表必须写在该页）')
        rows = []
    else:
        rows = parse_judge_table(st)
        if not rows:
            issues.append('%s 没有判定表（格式见 AGENTS.wiki.md §5.1）' % os.path.relpath(sp, ROOT))
    rngs = []
    for r in rows:
        rng = parse_range(r[1])
        if not rng:
            issues.append('判定表行范围非法：%s' % ' | '.join(r))
            continue
        rngs.append(rng)
        if r[2] not in JUDGE_VALUES:
            issues.append('判定值非法（应为 材料/丢弃/未建页）：%s' % ' | '.join(r))
        if r[2] == '材料':
            dest = r[4]
            if not dest or dest in ('—', '-', '–', '?'):
                issues.append('材料行缺去向：%s' % ' | '.join(r))
            else:
                m = re.search(r'\[\[([^\]]+)\]\]', dest)
                if m:
                    name = m.group(1).split('|')[0].split('#')[0].strip()
                    hit = glob.glob(os.path.join(ROOT, '30-wiki', '**', name + '.md'), recursive=True)
                    if not hit:
                        issues.append('去向页不存在：[[%s]]（%s）' % (name, ' | '.join(r)))
    for s in h3:
        s['judged'] = any(a <= s['end'] and b >= s['start'] for a, b in rngs)
    key = book.split('_')[0]
    for f, t in page_files(book):
        rel = os.path.relpath(f, ROOT)
        parts = t.split('---')
        if len(parts) < 3:
            continue
        for entry in source_entries(parts[1]):
            if key not in entry[0]:
                continue
            found = False
            for line in entry[1:]:
                m = re.search(r'lines\s*:\s*(.+)', line)
                if not m:
                    continue
                found = True
                v = m.group(1).strip().strip('"').strip("'")
                if not v or v in ('[]', '~', 'null'):
                    issues.append('%s sources.lines 为空' % rel)
                    continue
                rng = parse_range(v)
                if not rng:
                    issues.append('%s sources.lines 格式非法：%s' % (rel, v))
                    continue
                a, b = rng
                if not (1 <= a <= b <= total):
                    issues.append('%s sources.lines 越界：%s（md 共 %d 行）' % (rel, v, total))
            if not found:
                issues.append('%s 缺 sources.lines（新建页必填，见 rules-page.md §4）' % rel)
    return rows, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-Book', required=True)
    ap.add_argument('--strict', action='store_true')
    ap.add_argument('--judged', action='store_true')
    ap.add_argument('--json', default='')
    a = ap.parse_args()

    book = a.Book
    lines = md_lines(book)
    if lines is None:
        print('md 不存在：' + os.path.join(ROOT, '20-md', book + '.md'))
        return 2
    secs = sections(lines)
    h3 = [s for s in secs if s['level'] == 3]

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

    for s in h3:
        s['hits'] = sum(1 for c in cited if s['start'] <= c <= s['end'])
        s['covered'] = s['hits'] > 0
    cov = sum(1 for s in h3 if s['covered'])
    print('book=%s sections=%d covered=%d uncovered=%d' % (book, len(h3), cov, len(h3) - cov))
    for s in h3:
        if not s['covered']:
            print('  UNCOVERED %s | L%d-%d | tab=%d img=%d' %
                  (s['title'], s['start'], s['end'], s['tables'], s['images']))

    bad = 0
    if a.judged:
        rows, issues = check_judged(book, h3, len(lines))
        unjudged = [s for s in h3 if not s['judged']]
        bad = len(issues)
        print('judged: rows=%d judged_sections=%d unjudged=%d bad=%d' %
              (len(rows), len(h3) - len(unjudged), len(unjudged), bad))
        for s in unjudged:
            print('  UNJUDGED %s | L%d-%d' % (s['title'], s['start'], s['end']))
        for msg in issues:
            print('  BAD ' + msg)

    if a.json:
        json.dump(h3, io.open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    if a.strict:
        if cov < len(h3):
            return 1
        if a.judged and bad:
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
