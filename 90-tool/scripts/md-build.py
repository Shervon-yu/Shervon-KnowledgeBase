# -*- coding: utf-8 -*-
r"""md-build.py —— 从 MinerU middle_json 按页序重建 20-md（页码锚点 / 公式 / 表格 / 图名候选）。

用法：
  python md-build.py dry  <入库夹名>            # 只出统计与 %TEMP%\preview-*.md
  python md-build.py write <入库夹名>           # 写 md 并拷图
  python md-build.py write <入库夹名> --zipdir <zip 所在目录> --outdir <20-md 入库夹>

入库夹名 = 20-md 下的文件夹名（= md 文件名去掉 .md）。
zip 查找顺序：--zipdir → 40-new\parse\<入库夹名> → %TEMP%\mk-full\<入库夹名>。
"""
import zipfile, os, json, io, re, sys, html, collections, glob, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # D:\Shervon_KnowledgeBase
MDROOT = os.path.join(ROOT, "20-md")
SRC = os.path.join(ROOT, "40-new", "parse")

BOOKS = {}
_ZIP_OVERRIDE = None
_OUT_OVERRIDE = None

BAD = re.compile(r'[\\/:*?"<>|()\[\]{}#%]')
TD = re.compile(r"<td([^>]*)>(.*?)</td>", re.S)
TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TAG = re.compile(r"<[^>]+>")


def flat(node, out):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, list):
        for c in node:
            flat(c, out)
    elif isinstance(node, dict):
        for k in ("content", "text", "html"):
            if k in node:
                flat(node[k], out)


def text_of(node):
    out = []
    flat(node, out)
    return "".join(out).strip()


def inline_md(content):
    """content 数组 → 一行 markdown：文本原样，行内公式包 $...$。"""
    parts = []
    for c in content:
        if not isinstance(c, dict):
            continue
        t = c.get("type")
        if t == "text":
            s = c.get("content") or ""
            if isinstance(s, list):
                s = text_of(s)
            s = re.sub(r"\s*\n\s*", " ", s)
            parts.append(s)
        elif t == "equation_inline":
            s = text_of(c)
            parts.append("$%s$" % s)
    s = "".join(parts)
    s = re.sub(r"[ \t]{2,}", " ", s).strip()
    return s


def cells_of(row_html, spans):
    """把 <tr> 内 <td> 解析成单元格列表，处理 colspan/rowspan（rowspan 用占位）。"""
    cells = []
    for m in TD.finditer(row_html):
        attr, inner = m.group(1), m.group(2)
        txt = html.unescape(TAG.sub(" ", inner))
        txt = re.sub(r"\s+", " ", txt).strip().replace("|", "\\|")
        cs = re.search(r'colspan="(\d+)"', attr)
        rs = re.search(r'rowspan="(\d+)"', attr)
        cspan = int(cs.group(1)) if cs else 1
        rspan = int(rs.group(1)) if rs else 1
        cells.append(txt)
        for _ in range(cspan - 1):
            cells.append("")
        if rspan > 1:
            spans.append((len(cells) - cspan, rspan - 1, txt))
    return cells


def html_table_to_md(h):
    """HTML table → pipe table。rowspan/colspan 退化为重复行内留空。"""
    rows = []
    carry = collections.defaultdict(list)  # col -> 待补的 (文本, 剩余行数)
    for m in TR.finditer(h):
        row_html = m.group(1)
        cells = []
        spans = []
        parsed = cells_of(row_html, spans)
        # 先按列号排布：已被 rowspan 占用的列先填旧值
        col = 0
        it = 0
        out_cells = []
        occupied = sorted(carry.keys())
        total_cols = None
        while it < len(parsed) or col in carry:
            if col in carry and carry[col]:
                txt, left = carry[col].pop(0)
                out_cells.append("")  # 合并单元格后续行留空，保持列数
                if left - 1 > 0:
                    carry[col].insert(0, (txt, left - 1))
                else:
                    del carry[col]
                col += 1
                continue
            if it < len(parsed):
                txt = parsed[it]
                it += 1
                out_cells.append(txt)
                col += 1
            else:
                break
        # rowspan 登记
        for pos, left, txt in spans:
            pass
        rows.append(out_cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def title_level(txt):
    s = txt.strip()
    if re.match(r"^第\s*[一二三四五六七八九十百]+\s*[章篇]", s):
        return 2
    if re.match(r"^第\s*[一二三四五六七八九十百]+\s*节", s):
        return 3
    if re.match(r"^\d+\.\d+\.\d+", s):
        return 4
    if re.match(r"^\d+\.\d+(\s|$)", s):
        return 3
    if re.match(r"^附录", s) or re.match(r"^参考文献", s):
        return 2
    return 2


def clean_name(caption, idx):
    s = caption.replace("\x00", "")
    s = "".join(ch for ch in s if ord(ch) >= 32)
    s = BAD.sub("·", s)
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    if len(s) < 3 or not re.search(r"[\u4e00-\u9fff]", s):
        s = "图_%d" % idx
    return s


def build(book, mode):
    cfg = _resolve(book)
    cfg = BOOKS[book]
    zp = [f for f in os.listdir(cfg["zipdir"]) if f.endswith(".zip")][0]
    zf = zipfile.ZipFile(os.path.join(cfg["zipdir"], zp))
    d = json.loads(zf.read("middle_json.json").decode("utf-8", "replace"))

    lines = []
    stats = collections.Counter()
    names = collections.Counter()
    plan_imgs = []
    title_levels = collections.Counter()

    for pg in d["pages"]:
        printed = None
        for bl in pg["blocks"]:
            if bl.get("type") == "page_number":
                s = text_of(bl.get("content"))
                m = re.search(r"\d+", s)
                if m:
                    printed = int(m.group(0))
        pno = printed if printed else pg["page_idx"] + 1
        lines.append("<!-- page: %d -->" % pno)
        lines.append("")

        blocks = sorted(pg.get("blocks", []), key=lambda b: b.get("index", 0))
        consumed = set()
        CAPRE = r"^图\s*\d+[-.．]\d+"

        def _tocline(s):
            return bool(re.search(r"(?:…{1,}|\.{2,})\s*\d+\s*$", s or ""))

        _tt = [b for b in blocks if b.get("type") == "paragraph_title"]
        _dots = 0
        for b in blocks:
            try:
                _s = text_of(b.get("content")) or inline_md(b.get("content") or [])
            except Exception:
                _s = ""
            if _tocline(_s):
                _dots += 1
        _idx = sum(1 for b in blocks if b.get("type") == "index")
        is_toc = (len(_tt) >= 2 and _idx >= 1) or (len(_tt) >= 5 and _dots >= 4)
        if is_toc:
            stats["toc_page"] = stats.get("toc_page", 0) + 1
        page_caps = []
        for _bi, _b in enumerate(blocks):
            if _b.get("type") == "text":
                _s = inline_md(_b.get("content") or [])
                if re.match(CAPRE, _s) and len(_s) < 100:
                    page_caps.append([_bi, _s])
        for bi, bl in enumerate(blocks):
            t = bl.get("type")
            if bi in consumed:
                continue
            if t in ("header", "page_number"):
                continue
            if t == "paragraph_title":
                txt = text_of(bl.get("content"))
                if txt and is_toc:
                    lines.append("- " + re.sub(r"\s+", " ", txt).strip())
                    lines.append("")
                    stats["toc_title"] = stats.get("toc_title", 0) + 1
                    continue
                if txt:
                    lvl = title_level(txt)
                    title_levels[lvl] += 1
                    lines.append("#" * lvl + " " + txt)
                    lines.append("")
                    stats["title"] += 1
            elif t == "text":
                s = inline_md(bl.get("content") or [])
                if s and is_toc and re.match(r"^[\.…\s\d]+$", s) and lines and lines[-2].startswith("- "):
                    lines[-2] = lines[-2].rstrip() + " " + s.strip()
                    continue
                if s:
                    lines.append(s)
                    lines.append("")
                    stats["text"] += 1
            elif t == "equation":
                raw = bl.get("content")
                if isinstance(raw, list):
                    raw = "".join(text_of(c) for c in raw)
                s = (raw or "").strip()
                if s:
                    lines.append("$$ " + s + " $$")
                    lines.append("")
                    stats["equation"] += 1
            elif t == "ref_text":
                s = text_of(bl.get("content"))
                if s:
                    lines.append(s)
                    lines.append("")
                    stats["ref"] += 1
            elif t == "index":
                items = []
                for c in bl.get("content") or []:
                    s = text_of(c)
                    if s:
                        items.append("- " + re.sub(r"\s+", " ", s).strip())
                if items:
                    lines.extend(items)
                    lines.append("")
                    stats["toc"] += len(items)
            elif t in ("image", "chart"):
                body = None
                cap = None
                note = None
                for c in bl.get("content") or []:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") in ("image_body", "chart_body"):
                        body = c.get("image_path")
                    elif c.get("type") in ("image_caption", "chart_caption"):
                        cap = text_of(c.get("content"))
                    elif c.get("type") == "image_footnote":
                        note = text_of(c.get("content"))
                if not body:
                    continue
                stats["image"] += 1
                CAPRE = r"^图\s*\d+[-.．]\d+"
                if cap and not re.match(CAPRE, cap.strip()):
                    # 被误当图题的往往是图注（1—压盖螺栓;2—压盖），降级为注
                    if not note:
                        note = cap
                    cap = None
                if not cap:
                    # 同页里尚未被用掉的图题，按顺序借一个
                    pick = None
                    for item in page_caps:
                        if item[0] not in consumed:
                            pick = item
                            break
                    if pick is None:
                        for item in page_caps:
                            if item[0] == bi - 1 or item[0] == bi + 1:
                                pick = item
                                break
                    if pick is not None:
                        cap = pick[1]
                        consumed.add(pick[0])
                        stats["cap_borrowed"] += 1
                if cap:
                    base = clean_name(cap, stats["image"])
                    names[base] += 1
                    if names[base] > 1:
                        base = "%s_%d" % (base, names[base])
                    stats["img_caption"] += 1
                else:
                    base = "整页图-p%d_%d" % (pno, stats["image"])
                    stats["img_nocap"] += 1
                plan_imgs.append((body, base))
                lines.append("![](图片/%s.jpg)" % base)
                lines.append("")
                if cap:
                    lines.append(cap)
                    lines.append("")
                if note:
                    lines.append(note)
                    lines.append("")
            elif t == "table":
                cap = body = note = None
                for c in bl.get("content") or []:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "table_caption":
                        cap = text_of(c.get("content"))
                    elif c.get("type") == "table_body":
                        body = c.get("content")
                    elif c.get("type") == "table_footnote":
                        note = text_of(c.get("content"))
                stats["table"] += 1
                if cap:
                    lines.append(cap)
                    lines.append("")
                if body:
                    if isinstance(body, str) and "<tr" in body:
                        md = html_table_to_md(body)
                        if md:
                            lines.append(md)
                            lines.append("")
                            stats["table_pipe"] += 1
                    else:
                        lines.append(body if isinstance(body, str) else "")
                        lines.append("")
                if note:
                    lines.append(note)
                    lines.append("")

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"

    print("[%s] lines=%d chars=%d  %s" % (book, text.count("\n"), len(text), dict(stats)))
    print("  title_levels=%s  unique_img_names=%d" % (dict(title_levels), len(names)))
    if mode == "dry":
        io.open(os.path.join(r"C:\Users\shervon\AppData\Local\Temp", "preview-%s.md" % book), "w", encoding="utf-8").write(text)
        print("  preview -> %%TEMP%%\\preview-%s.md" % book)
        return

    mdpath = os.path.join(cfg["outdir"], cfg["name"])
    # 保留既有 YAML frontmatter（重建正文不重写元数据；catalog.ps1 依赖它）
    fm = ""
    if os.path.exists(mdpath):
        old_txt = io.open(mdpath, encoding="utf-8").read()
        if old_txt.startswith("---"):
            end = old_txt.find("\n---", 3)
            if end > 0:
                fm = old_txt[: end + 4].rstrip("\n") + "\n\n"
    imgdir = os.path.join(cfg["outdir"], "图片")
    if not os.path.isdir(imgdir):
        os.makedirs(imgdir)
    io.open(mdpath, "w", encoding="utf-8", newline="\n").write(fm + text)
    copied = 0
    for body, base in plan_imgs:
        dst = os.path.join(imgdir, base + ".jpg")
        if os.path.exists(dst):
            continue
        data = zf.read(body)
        io.open(dst, "wb").write(data)
        copied += 1
    print("  wrote %s ; images copied=%d" % (mdpath, copied))


def _resolve(key):
    """按入库夹名解析 outdir / md 名 / zip 目录，并登记到 BOOKS。"""
    if key in BOOKS:
        return BOOKS[key]
    outdir = _OUT_OVERRIDE or os.path.join(MDROOT, key)
    if not os.path.isdir(outdir):
        raise SystemExit("找不到入库夹：%s" % outdir)
    mds = [p for p in glob.glob(os.path.join(outdir, "*.md"))]
    if not mds:
        raise SystemExit("入库夹里没有 .md：%s" % outdir)
    name = os.path.basename(mds[0])
    zipdir = _ZIP_OVERRIDE
    if not zipdir:
        cands = [os.path.join(SRC, key), os.path.join(tempfile.gettempdir(), "mk-full", key)]
        # 回退：按书名前缀匹配解析器产物目录（mk-full\机械密封、mk-full\化工原理）
        for root in (SRC, os.path.join(tempfile.gettempdir(), "mk-full")):
            if os.path.isdir(root):
                for d in os.listdir(root):
                    if key.startswith(d):
                        cands.append(os.path.join(root, d))
        for cand in cands:
            if os.path.isdir(cand) and glob.glob(os.path.join(cand, "*.zip")):
                zipdir = cand
                break
    if not zipdir:
        raise SystemExit("找不到解析产物目录（用 --zipdir 指定）：%s" % key)
    BOOKS[key] = dict(zipdir=zipdir, outdir=outdir, name=name)
    return BOOKS[key]


def _build_book(key, mode):
    cfg = _resolve(key)
    build(key, mode)


def _prune(key):
    """把 md 里没有引用的图片移到 40-new\\_acl\\orphan-images\\<入库夹名>\\（可回滚，不删）。"""
    b = _resolve(key)
    md = os.path.join(b["outdir"], b["name"])
    s = io.open(md, encoding="utf-8").read()
    ref = set(re.findall(r"图片/([^)]+?\.jpg)", s))
    imgdir = os.path.join(b["outdir"], "图片")
    files = sorted(f for f in os.listdir(imgdir) if f.lower().endswith(".jpg"))
    orph = [f for f in files if f not in ref]
    print("  [prune] md=%s refs=%d files=%d orph=%d" % (b["name"], len(ref), len(files), len(orph)))
    if not orph:
        print("未引用图片：0")
        return 0
    dest = os.path.join(ROOT, "40-new", "_acl", "orphan-images", key)
    os.makedirs(dest, exist_ok=True)
    for f in orph:
        shutil.move(os.path.join(imgdir, f), os.path.join(dest, f))
    print("未引用图片：%d 张已移入 %s" % (len(orph), dest))
    return len(orph)


def main(argv):
    global _ZIP_OVERRIDE, _OUT_OVERRIDE
    a = [x for x in argv[1:]]
    opts = {}
    i = 0
    while i < len(a):
        if a[i] in ("--zipdir", "--outdir") and i + 1 < len(a):
            opts[a[i]] = a[i + 1]
            i += 2
        else:
            i += 1
    _ZIP_OVERRIDE = opts.get("--zipdir")
    _OUT_OVERRIDE = opts.get("--outdir")
    pos = [x for x in a if not x.startswith("--") and x not in opts.values()]
    if len(pos) < 2:
        raise SystemExit(__doc__)
    mode, key = pos[0], pos[1]
    if mode not in ("dry", "write", "prune"):
        mode, key = key, mode
    if mode == "prune":
        _prune(key)
    else:
        _build_book(key, mode)


if __name__ == "__main__":
    main(sys.argv)
