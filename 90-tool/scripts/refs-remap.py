# -*- coding: utf-8 -*-
"""frontmatter-aware：#L 重映射到重建后的 md。

frontmatter 里按 sources 条目逐个取 book，正文按《书名》顺序跟踪归属。
python refs-remap.py dry|apply
输出 remap5-map.txt / remap5-unresolved.txt / remap5-review.txt
"""
import io, os, re, sys, glob, difflib, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MDROOT = os.path.join(ROOT, "20-md")


def _latest_backup():
    """取 40-new\\_acl\\rebuild-* 里最新的一个，作为旧 md 来源。"""
    cands = sorted(glob.glob(os.path.join(ROOT, "40-new", "_acl", "rebuild-*")))
    if not cands:
        raise SystemExit("找不到旧 md 备份目录（40-new\\_acl\\rebuild-*），无法重映射")
    return cands[-1]


BK = _latest_backup()
PAIRS = {}
for d in sorted(glob.glob(os.path.join(MDROOT, "*"))):
    if not os.path.isdir(d):
        continue
    base = os.path.basename(d)
    new_md = os.path.join(d, base + ".md")
    old_md = os.path.join(BK, base + ".md")
    if os.path.exists(new_md) and os.path.exists(old_md):
        key = base.split("_")[0]
        PAIRS[key] = (old_md, new_md)

TR = str.maketrans({"（": "(", "）": ")", "，": ",", "：": ":", "；": ";", "．": ".", "－": "-", "—": "-", "…": "."})
KEEP = re.compile(r"[^\u3400-\u9fffA-Za-z0-9]+")
MIN_EXPLICIT, MIN_BODY, STRICT, REVIEW = 8, 9, 20, 14


def norm(s):
    return KEEP.sub("", s.translate(TR).replace("$", "").replace("|", "").replace("\\", ""))


def load(p):
    return io.open(p, encoding="utf-8", errors="replace").read().split("\n")


TOCP = re.compile(r"(…{2,}|\.{3,})\s*\d+\s*$")


def is_toc(ln):
    t = ln.strip()
    if not t:
        return False
    if TOCP.search(t):
        return True
    return False


def build_index(lines):
    idx = collections.defaultdict(set)
    for i, ln in enumerate(lines):
        if is_toc(ln):
            continue
        n = norm(ln)
        if len(n) < 8:
            continue
        for k in range(0, max(1, len(n) - 7), 3):
            idx[n[k:k + 8]].add(i + 1)
    return idx


def book_of(name):
    if "化工原理" in name:
        return "化工原理"
    if "气液搅拌釜" in name or "γ-CT" in name:
        return "气液"
    return None


def page_book(raw):
    """页归属：frontmatter domain > 首个 sources book > 《》多数。"""
    head = raw.split("\n---", 1)[0]
    m = re.search(r"^domain:\s*(.+)$", head, re.M)
    if m:
        bk = book_of(m.group(1))
        if bk:
            return bk
    m = re.search(r"^\s*-?\s*book:\s*(.+)$", head, re.M)
    if m:
        bk = book_of(m.group(1))
        if bk:
            return bk
    hits = []
    for mm in re.finditer(r"《([^》]{1,40})》", raw):
        bk = book_of(mm.group(1))
        if bk:
            hits.append(bk)
    return collections.Counter(hits).most_common(1)[0][0] if hits else None


MATHDROP = re.compile(r"[\s\\${}^_()]+")
TAGT = re.compile(r"\\?tag\{[^}]*\}")


def math_norm(s):
    s = TAGT.sub("", s)
    return MATHDROP.sub("", s)


def formula_match(txt, bk):
    mt = math_norm(txt)
    if len(mt) < 8:
        return None
    best = None
    for i, ln in enumerate(NEW[bk]):
        if TOCP.search(ln) or "$" not in ln and "\\" not in ln:
            continue
        mw = math_norm(ln)
        if len(mw) < 8:
            continue
        sz = difflib.SequenceMatcher(None, mt, mw).find_longest_match(0, len(mt), 0, len(mw)).size
        if sz >= 12 and (best is None or sz > best[1]):
            best = (i + 1, sz)
    return (bk, best[0], best[1], txt) if best else None


def best_match(txt, books, strict=False):
    nt = norm(txt)
    if len(nt) < 6:
        return None
    best = None
    for bk in books:
        cands = set()
        for k in range(0, max(1, len(nt) - 7), 3):
            cands |= NIDX[bk].get(nt[k:k + 8], set())
        for c in cands:
            if not (0 < c <= len(NEW[bk])):
                continue
            raw_new = NEW[bk][c - 1]
            if is_toc(raw_new):
                continue
            w = norm(raw_new)
            if len(w) < 6:
                continue
            sz = difflib.SequenceMatcher(None, nt, w).find_longest_match(0, len(nt), 0, len(w)).size
            need = STRICT if strict else MIN_BODY
            if sz >= need and (best is None or sz > best[2]):
                best = (bk, c, sz)
    return best


def anchor_text(bk, n):
    lines = OLD[bk]
    if not (0 < n <= len(lines)):
        return None
    t = lines[n - 1]
    if len(norm(t)) >= 8:
        return t
    for d in (1, -1, 2, -2, 3, -3):
        j = n - 1 + d
        if 0 <= j < len(lines) and len(norm(lines[j])) >= 8:
            return lines[j]
    return t if norm(t) else None


def nearest_heading(lines, n):
    for j in range(n - 1, max(-1, n - 400), -1):
        if lines[j].lstrip().startswith("#"):
            return j + 1, lines[j]
    return None, None


def fallback_local(bk, n, last):
    """全文找与旧行共享片段的候选，按与上一条新行号的距离选最近。"""
    t = anchor_text(bk, n)
    if not t:
        return None
    nt = norm(t)
    if len(nt) < 6:
        return None
    chunks = sorted({nt[k:k + 6] for k in range(0, max(1, len(nt) - 5), 2)}, key=len, reverse=True)[:40]
    cands = set()
    for ch in chunks:
        for i, ln in enumerate(NEW[bk]):
            if ch in ln:
                cands.add(i + 1)
        if len(cands) > 400:
            break
    best = None
    for c in cands:
        raw_new = NEW[bk][c - 1]
        if is_toc(raw_new):
            continue
        w = norm(raw_new)
        if len(w) < 6:
            continue
        sz = difflib.SequenceMatcher(None, nt, w).find_longest_match(0, len(nt), 0, len(w)).size
        if sz < 6:
            continue
        dist = abs(c - last) if last else 0
        key = (sz >= 12, -dist, sz)
        if best is None or key > best[0]:
            best = (key, (bk, c, sz))
    return best[1] if best else None


def fallback(bk, n):
    """节内回退：旧行所在节标题 → 新 md 同名节 → ±100 行内 LCS>=6。"""
    lines_old = OLD[bk]
    t = anchor_text(bk, n)
    if not t:
        return None
    hline, htext = nearest_heading(lines_old, n)
    if not htext:
        return None
    nh = norm(htext)
    if len(nh) < 6:
        return None
    # 在新 md 里找同名标题
    heads = []
    for i, ln in enumerate(NEW[bk]):
        if ln.lstrip().startswith("#") and norm(ln) and len(norm(ln)) >= 6:
            sz = difflib.SequenceMatcher(None, nh, norm(ln)).find_longest_match(0, len(nh), 0, len(norm(ln))).size
            if sz >= max(8, int(len(nh) * 0.7)):
                heads.append(i + 1)
    if not heads:
        return None
    nt = norm(t)
    best = None
    for h in heads:
        for c in range(max(1, h - 6), min(len(NEW[bk]), h + 120)):
            raw_new = NEW[bk][c - 1]
            if is_toc(raw_new):
                continue
            w = norm(raw_new)
            if len(w) < 6:
                continue
            sz = difflib.SequenceMatcher(None, nt, w).find_longest_match(0, len(nt), 0, len(w)).size
            if sz >= 6 and (best is None or sz > best[2]):
                best = (bk, c, sz)
    return best


def main(mode):
    if mode == "apply":
        import subprocess
        st = subprocess.run(["git", "status", "--porcelain", "30-wiki", "kb-blueprint.md"],
                            cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if st:
            raise SystemExit("apply 前工作区必须干净（先 git checkout -- \'30-wiki\' kb-blueprint.md）；当前有未提交改动：\n" + st)
    global OLD, NEW, NIDX
    OLD, NEW, NIDX = {}, {}, {}
    for bk, (o, n) in PAIRS.items():
        OLD[bk], NEW[bk] = load(o), load(n)
        NIDX[bk] = build_index(NEW[bk])
        print("[%s] old=%d new=%d" % (bk, len(OLD[bk]), len(NEW[bk])))

    files = sorted(glob.glob(os.path.join(ROOT, "30-wiki", "**", "*.md"), recursive=True))
    files.append(os.path.join(ROOT, "kb-blueprint.md"))
    stats = collections.Counter()
    maps, unres, review = [], [], []
    pat = re.compile(r"《([^》]{1,40})》|#L(\d+)")
    for p in files:
        rel = os.path.relpath(p, ROOT)
        raw = io.open(p, encoding="utf-8").read()
        lines = raw.split("\n")
        # 定位 frontmatter 结束行
        fm_end = -1
        if lines and lines[0].strip() == "---":
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    fm_end = i
                    break
        # 逐行处理
        body_book = page_book(raw)
        last_new = {}
        fm_book = None
        out = []
        for li, ln in enumerate(lines):
            if 0 <= li <= fm_end:
                mb = re.match(r"\s*-?\s*book:\s*(.+?)\s*$", ln)
                if mb:
                    fm_book = book_of(mb.group(1)) or fm_book
            new_line = []
            pos = 0
            for m in pat.finditer(ln):
                new_line.append(ln[pos:m.start()])
                pos = m.end()
                if m.group(1):
                    bk = book_of(m.group(1))
                    if bk:
                        if li > fm_end:
                            body_book = bk
                    new_line.append(m.group(0))
                    continue
                n = int(m.group(2))
                explicit = 0 <= li <= fm_end
                bk = fm_book if explicit else body_book
                if bk == "气液":
                    new_line.append(m.group(0))
                    stats["气液 skip"] += 1
                    continue
                if bk in PAIRS:
                    t = anchor_text(bk, n)
                    b = best_match(t, [bk]) if t else None
                    b = b if (b and b[2] >= MIN_EXPLICIT) else b
                    if b:
                        b = (b[0], b[1], b[2]) if b[2] >= MIN_EXPLICIT else None
                else:
                    t = None
                    for k in PAIRS:
                        t2 = anchor_text(k, n)
                        b2 = best_match(t2, [k], strict=True) if t2 else None
                        if b2 and (t is None or b2[2] > t[2]):
                            t = b2
                    b = t
                if not b and bk in PAIRS:
                    t0 = anchor_text(bk, n) or ""
                    if "tag{" in t0 or "$" in t0:
                        b = formula_match(t0, bk)
                if not b and bk in PAIRS:
                    b = fallback_local(bk, n, last_new.get(bk))
                if b:
                    last_new[b[0]] = b[1]
                    new_line.append("#L%d" % b[1])
                    stats[b[0] + " ok"] += 1
                    rec = "%s | %s L%d -> L%d (LCS %d) | %s" % (rel, b[0], n, b[1], b[2], (anchor_text(b[0], n) or "")[:50])
                    maps.append(rec)
                    if b[2] < REVIEW:
                        review.append(rec)
                else:
                    new_line.append(m.group(0))
                    stats["miss"] += 1
                    ctx = ln[:m.start()].strip()[-50:]
                    unres.append("%s | %s L%d | %s" % (rel, bk, n, ctx))
            new_line.append(ln[pos:])
            out.append("".join(new_line))
        txt = "\n".join(out)
        if txt != raw:
            stats["files_changed"] += 1
            if mode == "apply":
                io.open(p, "w", encoding="utf-8", newline="\n").write(txt)
    print(dict(stats))
    for name, rows in (("map", maps), ("unresolved", unres), ("review", review)):
        rp = os.path.join(r"C:\Users\shervon\AppData\Local\Temp", "remap5-%s.txt" % name)
        io.open(rp, "w", encoding="utf-8").write("\n".join(rows))
        print(name, len(rows), "->", rp)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dry")
