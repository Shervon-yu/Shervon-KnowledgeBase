#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figures.py — MinerU 出图名归一工序。

背景：MinerU 4.x 的 image 块通常不带图题（图题是独立文本块），旧流程只能退化成
      「未命名图N / OCR 碎片前缀」，md 引用也跟着对不上。本工序按页面几何把图题
      配回图片，改名成 `图X.Y 说明.jpg`，同步改写 md 引用；并把「有图题没图」的
      位置补上链接。多子图（(a)(b) 并排或上下叠放）按同图题分组、自动加 (a)(b)。

用法：
  python figures.py --book <书目录> [--mineru <MinerU输出目录>] [--md <md>] [--apply] [--dedupe]

  --mineru  指向 MinerU 输出目录（含 middle_json.json 与 images/）；不给则只按 md 内部图题整理
  --apply   真改名/改 md；默认 dry-run 只出报告
  --dedupe  同内容的多份副本只留一份（被引用的一份优先），其余删除并改链

报告：<书目录>\\_figures-report.json
"""
import argparse
import hashlib
import json
import os
import re
import sys

CAP_RE = re.compile(r'^图\s*(\d+)\s*[-－—.．]\s*(\d+)\s*(.*)$')
REF_RE = re.compile(
    r'!\[[^\]]*\]\((?P<a>[^)\n]+?\.(?:jpg|jpeg|png|webp|bmp|tif|tiff))\)'
    r'|<img[^>]*src="(?P<b>[^"\n]+?\.(?:jpg|jpeg|png|webp|bmp|tif|tiff))"', re.I)
EXT_SET = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff')
BAD_CHARS = re.compile(r'[*?:"<>|/\\\[\](){}#%\r\n\t]')
TABLE_IMG = re.compile(r'^page_\d+_table_image_', re.I)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def norm_caption(text):
    """疑似图题 → '图X.Y 说明'；像正文引述句（含句号/以所示起头）返回 None。"""
    if not text:
        return None
    t = ' '.join(str(text).split()).replace('$', '').replace('{', '').replace('}', '')
    t = re.sub(r'\[\d+(?:[,\-\u2013]\d+)*\]', '', t)
    if '。' in t or len(t) > 120:
        return None
    m = CAP_RE.match(t)
    if not m:
        return None
    num = '图%s.%s' % (m.group(1), m.group(2))
    desc = re.sub(r'^[是为即:：,，、\-\s]+', '', m.group(3).strip())
    if re.match(r'^(所示|中|是|为|给出|表明|可见)', desc):
        return None
    desc = ' '.join(BAD_CHARS.sub(' ', desc).split())[:60].strip()
    return (num + ' ' + desc).strip()


def block_text(blk):
    c = blk.get('content')
    if isinstance(c, str):
        return c.strip()
    parts = []
    for x in (c or []):
        if isinstance(x, dict) and x.get('content'):
            parts.append(str(x['content']))
    return ' '.join(p.strip() for p in parts if p and p.strip())


def load_pages(mineru_dir):
    path = os.path.join(mineru_dir, 'middle_json.json')
    if not os.path.isfile(path):
        return []
    with open(path, encoding='utf-8') as fh:
        doc = json.load(fh)
    pages = []
    for pg in doc.get('pages', []):
        blocks = []
        for b in pg.get('blocks') or []:
            t = b.get('type')
            item = {'type': t, 'bbox': b.get('bbox') or [0, 0, 0, 0], 'text': block_text(b)}
            if t in ('image', 'chart'):
                own = []
                for ch in (b.get('content') or []):
                    if not isinstance(ch, dict):
                        continue
                    if ch.get('image_path'):
                        item['image'] = str(ch['image_path']).replace('\\', '/')
                    elif ch.get('content'):
                        c = str(ch['content']).strip()
                        if c:
                            own.append(c)
                item['own_caps'] = own
            blocks.append(item)
        pages.append({'idx': pg.get('page_idx'), 'blocks': blocks})
    return pages


def overlap(a0, a1, b0, b1):
    lo, hi = max(a0, b0), min(a1, b1)
    return max(0.0, hi - lo)


def assign_names(pages):
    """{mineru 图片相对路径: 规范名}。同图题多图 → 图X.Y 说明 (a)/(b)…"""
    out = {}
    for pg in pages:
        caps = []
        for b in pg['blocks']:
            if b['type'] in ('text', 'paragraph_title', 'title') and b.get('text'):
                n = norm_caption(b['text'])
                if n:
                    x0, y0, x1, y1 = b['bbox']
                    caps.append({'name': n, 'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1})
        imgs = [b for b in pg['blocks'] if b.get('image')]
        if not caps or not imgs:
            continue
        buckets = {}
        direct = {}
        for b in imgs:
            own = None
            for c in b.get('own_caps') or []:
                own = norm_caption(c)
                if own:
                    break
            if own:
                direct[b['image']] = own
                continue
            x0, y0, x1, y1 = b['bbox']
            best, best_gap = None, 1e9
            for c in caps:
                ov = overlap(x0, x1, c['x0'], c['x1'])
                if ov < 0.3 * max(1e-6, x1 - x0):
                    continue
                gap = (c['y0'] - y1) if c['y0'] >= y1 else (y0 - c['y1'])
                gap = max(0.0, gap)
                if gap < best_gap:
                    best, best_gap = c, gap
            if best and best_gap < 0.35:
                buckets.setdefault(best['name'], []).append(b)
        out.update(direct)
        for name, arr in buckets.items():
            arr.sort(key=lambda b: (b['bbox'][1], b['bbox'][0]))
            for i, b in enumerate(arr):
                suffix = '' if len(arr) == 1 else ' (%s)' % chr(ord('a') + i)
                out[b['image']] = name if not suffix else name + suffix
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--book', required=True)
    ap.add_argument('--mineru', default=None)
    ap.add_argument('--md', default=None)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dedupe', action='store_true')
    args = ap.parse_args()

    book = os.path.abspath(args.book)
    md_path = args.md
    if not md_path:
        cand = os.path.join(book, os.path.basename(book.rstrip('\\/')) + '.md')
        if not os.path.isfile(cand):
            mds = [f for f in os.listdir(book) if f.lower().endswith('.md')]
            if len(mds) != 1:
                print('ERROR: 找不到唯一 md：%s' % cand)
                return 2
            cand = os.path.join(book, mds[0])
        md_path = cand

    with open(md_path, encoding='utf-8') as fh:
        text = fh.read()

    img_dir = os.path.join(book, '图片')
    if not os.path.isdir(img_dir):
        img_dir = book

    def link(name):
        return ('图片/' + name) if img_dir != book else name

    def relink(text, old, new):
        for pre in ('图片/', ''):
            text = text.replace('](' + pre + old + ')', '](' + link(new) + ')')
            text = text.replace('src="' + pre + old + '"', 'src="' + link(new) + '"')
        return text

    files = [f for f in os.listdir(img_dir) if f.lower().endswith(EXT_SET)]
    hash_of = {f: sha256(os.path.join(img_dir, f)) for f in files}
    by_hash = {}
    for f, h in hash_of.items():
        by_hash.setdefault(h, []).append(f)

    hash_to_name = {}
    if args.mineru:
        pages = load_pages(os.path.abspath(args.mineru))
        names = assign_names(pages)
        for rel, name in names.items():
            p = os.path.join(args.mineru, rel)
            if not os.path.isfile(p):
                continue
            hash_to_name.setdefault(sha256(p), name)

    def current_refs(t):
        out = []
        for m in REF_RE.finditer(t):
            out.append((m.group(1) or m.group(2)).replace('\\', '/').split('/')[-1])
        return out

    def is_canonical(name):
        return bool(re.match(r'^图\d+\.\d+ ', name)) and not name.startswith('未命名')

    def name_rank(name):
        if is_canonical(name):
            return 0
        if name.startswith('未命名图'):
            return 1
        if re.search(r'图\s*\d+\s*[-.．]\s*\d+', name):
            return 2
        return 3

    report = {'md': md_path, 'apply': args.apply, 'renamed': [], 'deduped': [],
              'inserted': [], 'missing': [], 'unreferenced': [], 'ambiguous': []}

    refs = current_refs(text)
    taken = {f.lower() for f in files}
    plan = {}   # old -> new
    drops = []  # (副本, 保留文件)

    for h, locals_ in by_hash.items():
        if len(locals_) < 2:
            continue
        # 保留：被 md 引用的 > 规范名 > 其余
        ranked = sorted(locals_, key=lambda f: (name_rank(f), 0 if f in refs else 1, len(f)))
        keep = ranked[0]
        for extra in ranked[1:]:
            drops.append((extra, keep))
        for f in locals_:
            if f != keep:
                taken.discard(f.lower())

    # 只改「非规范名」且能拿到图题的
    for h, locals_ in by_hash.items():
        canon = hash_to_name.get(h)
        if not canon:
            continue
        keep = min(locals_, key=lambda f: (name_rank(f), 0 if f in refs else 1, len(f)))
        if is_canonical(keep) or keep.lower().startswith('page_'):
            continue
        ext = os.path.splitext(keep)[1].lower()
        dropped_names = {d for d, k in drops if k == keep}
        target = canon + ext
        if target.lower() in taken and target not in (keep,) | dropped_names:
            base, i = canon, 2
            while ('%s_%d%s' % (base, i, ext)).lower() in taken:
                i += 1
            target = '%s_%d%s' % (base, i, ext)
        taken.add(target.lower())
        plan[keep] = target

    for old, new in plan.items():
        report['renamed'].append({'old': old, 'new': new})
        if args.apply:
            text = relink(text, old, new)
            os.replace(os.path.join(img_dir, old), os.path.join(img_dir, new))

    if args.dedupe:
        for old, target in drops:
            if not os.path.isfile(os.path.join(img_dir, old)):
                continue
            target = plan.get(target, target)
            report['deduped'].append({'file': old, 'same_as': target})
            if args.apply:
                text = relink(text, old, target)
                os.remove(os.path.join(img_dir, old))

    # 补链：md 里有图题、但该图题下没有图片引用 → 用同图题文件补
    if args.apply:
        lines = text.split('\n')
    else:
        lines = text.split('\n')
    used = set(current_refs(text))
    name_to_files = {}
    for f, h in hash_of.items():
        n = hash_to_name.get(h)
        if n:
            name_to_files.setdefault(n, []).append(f)
    for f, n in [(k, v) for k, v in plan.items()]:
        pass
    for f in list(name_to_files):
        name_to_files[f] = sorted(set(name_to_files[f]))

    inserts = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        m = CAP_RE.match(s)
        if not m:
            continue
        cap = norm_caption(s)
        if not cap:
            continue
        prev = ' '.join(lines[max(0, i - 2):i])
        if REF_RE.search(prev) or REF_RE.search(s):
            continue
        cand = [f for f in name_to_files.get(cap, []) if f not in used] or \
               [f for f in name_to_files.get(cap, [])]
        if not cand:
            continue
        inserts.append((i, cand[0], s))
        used.add(cand[0])

    for i, f, s in inserts:
        report['inserted'].append({'line': i + 1, 'file': f})
        if args.apply:
            indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            lines.insert(i, indent + '![](' + link(f) + ')')
            lines = [l for l in lines]

    if args.apply and inserts:
        text = '\n'.join(lines)

    if args.apply:
        with open(md_path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text)

    final_files = {f for f in os.listdir(img_dir) if f.lower().endswith(EXT_SET)}
    final_refs = set(current_refs(text))
    report['unreferenced'] = sorted(final_files - final_refs)
    for i, ln in enumerate(lines):
        s = ln.strip()
        if CAP_RE.match(s) and norm_caption(s):
            prev = ' '.join(lines[max(0, i - 2):i])
            if not (REF_RE.search(prev) or REF_RE.search(s)):
                report['missing'].append({'line': i + 1, 'caption': s[:80]})

    # 仓库根 = 最近的名为 20-md 的祖先的上一级；报告统一放 <根>\40-new
    root, cur = None, book
    while True:
        cur = os.path.dirname(cur)
        if not cur or cur == os.path.dirname(cur):
            break
        if os.path.basename(cur) == '20-md':
            root = os.path.dirname(cur)
            break
    scratch = os.path.join(root, '40-new') if root else book
    if not os.path.isdir(scratch):
        scratch = book
    out = os.path.join(scratch, 'figures-report-' + os.path.basename(book) + '.json')
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print('renamed=%d deduped=%d inserted=%d missing=%d unref=%d report=%s'
          % (len(report['renamed']), len(report['deduped']), len(report['inserted']),
             len(report['missing']), len(report['unreferenced']), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
