# -*- coding: utf-8 -*-
r"""md-build.py —— 从 MinerU middle_json 按页序重建 20-md（页码锚点 / 公式 / 表格 / 图名候选）。

用法：
  python md-build.py dry  <入库夹名>            # 只出统计与 %TEMP%\preview-*.md
  python md-build.py write <入库夹名>           # 写 md 并拷图
  python md-build.py write <入库夹名> --zipdir <zip 所在目录> --outdir <20-md 入库夹>
  python md-build.py verify <入库夹名|md 路径>    # v3.16 标题体检：粗体假标题/漏章/孤立层级

入库夹名 = 20-md 下的文件夹名（= md 文件名去掉 .md）。
zip 查找顺序：--zipdir → 40-scratch\parse\<入库夹名> → %TEMP%\mk-full\<入库夹名>。
"""
import zipfile, os, json, io, re, sys, html, collections, glob, tempfile, shutil, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # D:\Shervon_KnowledgeBase
MDROOT = os.path.join(ROOT, "20-md")
SRC = os.path.join(ROOT, "40-scratch", "parse")

BOOKS = {}
_ZIP_OVERRIDE = None
_OUT_OVERRIDE = None
_STRICT = False

BAD = re.compile(r'[\\/:*?"<>|()\[\]{}#%]')
TD = re.compile(r"<td([^>]*)>(.*?)</td>", re.S)
TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
TAG = re.compile(r"<[^>]+>")
BARE_NUM_RE = re.compile(r"^(\d{1,2})\s+[\u4e00-\u9fff]")      # v3.16 GB 式裸数字章标题「1 范围」


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
    """0 = 假标题（转粗体正文），1/2/3/4 = 真标题层级。

    v3.5：MinerU 会把「一、」「1.」「(1)」这类小标题也标成 paragraph_title，
    旧逻辑对未匹配项一律返回 2，导致 624 个 h2（真章只有 17 个）、目录树全乱。
    按 blueprint §2.7 步④「假标题降级 ## (n)→**(n)**」的既定口径：
    只认 第X篇/第X章/第X节/数字多级/附录/参考文献/前置件，其余降级为粗体正文。

    v3.16：补两条 GB 式标题（GB/T 150 全程撞不上旧正则，整本 0 真标题、
    全部降成 **1 范围** 粗体）：
      「第 1 部分:通用要求」→ h1（"部分"是分册不是章，故单列一级）
      「1 范围」「5 钢板」→ h2（数字+空格+汉字，长度 ≤30 才算章标题）
    裸数字条目有误判风险（正文「1 总则 / 2 适用范围」列表也长这样），
    故由 _demote_bare_numbered() 事后守卫：同一分册内编号必须从 1 起、递增、不重号，
    否则成批降回粗体。
    """
    s = txt.strip()
    if re.match(r"^第\s*[一二三四五六七八九十百零\d]+\s*部分", s):
        return 1
    if re.match(r"^第\s*[一二三四五六七八九十百零\d]+\s*[章篇]", s):
        return 2
    if re.match(r"^第\s*[一二三四五六七八九十百零\d]+\s*节", s):
        return 3
    if re.match(r"^\d+\.\d+\.\d+", s):
        return 4
    if re.match(r"^\d+\.\d+(\s|$|[^\d.])", s):
        return 3
    if BARE_NUM_RE.match(s) and len(s) <= 30:
        return 2
    if re.match(r"^(附录|参考文献|前\s*言|序\s*[言一]?|目\s*录|编后记|致\s*谢|内容提要|符号表)", s):
        return 2
    return 0


def clean_name(caption, idx):
    s = caption.replace("\x00", "")
    s = "".join(ch for ch in s if ord(ch) >= 32)
    s = BAD.sub("·", s)
    s = re.sub(r"\s+", " ", s).strip().rstrip(".")
    if len(s) < 3 or not re.search(r"[\u4e00-\u9fff]", s):
        s = "图_%d" % idx
    return s


def _cn2int(s):
    d = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
         "七": 7, "八": 8, "九": 9}
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + d.get(s[1:], 0)
    if "十" in s:
        a, b = s.split("十", 1)
        return d.get(a, 0) * 10 + (d.get(b, 0) if b else 0)
    return d.get(s, 0)


def _inject_missing_chapters(lines):
    """v3.5：MinerU 偶尔漏掉章节标题块（本书漏了第十一章、第十二章），
    只留在目录里。这里按目录顺序把缺失的 `## 第X章 标题` 补回到该章第一个
    `### 第X节` 之前，避免 md 里章节树断链、sources 章节地图对不上。
    """
    toc = []
    for s in lines:
        m = re.match(r"^-\s*(第([一二三四五六七八九十百]+)章)\s*(.*?)[.…\s]*(\d+)\s*$", s)
        if m:
            toc.append((m.group(1), m.group(2), m.group(3).strip()))
    if not toc:
        return lines
    seen, uniq = set(), []
    for t in toc:
        if t[0] not in seen:
            seen.add(t[0])
            uniq.append(t)

    sec_idx = [i for i, l in enumerate(lines) if re.match(r"^###\s*第一节", l)]
    # 章节号 k ↔ 目录第 k 章；缺标题就插在该章「第一节」之前，倒序插入避免下标漂移
    for k in range(min(len(sec_idx), len(uniq)) - 1, -1, -1):
        name, num, title = uniq[k]
        if any(l.startswith("## " + name) for l in lines):
            continue
        i = sec_idx[k]
        lines[i:i] = ["## %s %s" % (name, title), ""]
        print("  [补章标题] %s %s -> 第 %d 行前" % (name, title, i + 1))
    return lines


def _demote_bare_numbered(lines):
    """v3.16 守卫：裸数字 h2（GB 式「1 范围」）误判后成批降回粗体。

    判据——同一 `# ` 分册内，这些编号必须从 1 起、严格递增、不重号。
    GB/T 150.2 真实缺第 3、4 章（1,2,5,6,7,8,9），递增成立，故不会被误杀；
    而正文里的「1 总则 / 2 适用范围 / 3 …」列表往往不递增或不从 1 起，会被降级。
    """
    bad, cur = [], []

    def flush():
        if not cur:
            return
        nums = [n for _, n in cur]
        ok = nums[0] == 1 and nums == sorted(nums) and len(set(nums)) == len(nums)
        if not ok:
            bad.extend(i for i, _ in cur)
        del cur[:]

    for i, l in enumerate(lines):
        if l.startswith("# "):
            flush()
        elif l.startswith("## "):
            m = BARE_NUM_RE.match(l[3:])
            if m:
                cur.append((i, int(m.group(1))))
    flush()
    for i in bad:
        lines[i] = "**" + lines[i][3:] + "**"
    if bad:
        print("  [标题守卫] 裸数字标题不构成章序列，降回粗体 %d 处：%s"
              % (len(bad), ", ".join(str(i + 1) for i in bad[:8])))
    return lines


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
        # v3.4: 锚点一律用物理页序 page_idx+1。
        # 原逻辑优先取页脚印刷页码，但前后置页（封面/版权/目录）使印刷页码与物理页序错位，
        # 同一本书里混用两套编号会产生「锚点数=538 却缺 50 个页号」的假通过，故改为一律物理页序。
        pno = pg["page_idx"] + 1
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
                    if lvl == 0:
                        # v3.5: 假标题降级为粗体正文（同 blueprint §2.7 步④），行数不变
                        lines.append("**" + re.sub(r"\s+", " ", txt).strip() + "**")
                    else:
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

    lines = _inject_missing_chapters(lines)
    lines = _demote_bare_numbered(lines)

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
        old_txt = io.open(mdpath, encoding="utf-8-sig").read()   # utf-8-sig: 容忍旧 md 带 BOM
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
        # 回退：按书名前缀匹配解析器产物目录（mk-full\<书名>、mk-full\化工原理）
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
    """把 md 里没有引用的图片移到 40-scratch\\_acl\\orphan-images\\<入库夹名>\\（可回滚，不删）。"""
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
    dest = os.path.join(ROOT, "40-scratch", "_acl", "orphan-images", key)
    os.makedirs(dest, exist_ok=True)
    for f in orph:
        shutil.move(os.path.join(imgdir, f), os.path.join(dest, f))
    print("未引用图片：%d 张已移入 %s" % (len(orph), dest))
    return len(orph)


def _lab_norm(s):
    """标签归一：全角转半角（NFKC）+ 去空白。"""
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"\s+", "", s)


def _lab_key(lab):
    """标题标签 → 可比较的键：第1章 / 附录A / 1；认不出的返回空串。"""
    s = _lab_norm(lab)
    m = re.match(r"^第([一二三四五六七八九十百零\d]+)([章篇节])", s)
    if m:
        n = m.group(1)
        n = int(n) if n.isdigit() else _cn2int(n)
        return "第%d%s" % (n, m.group(2))
    m = re.match(r"^附录([A-Za-z])", s)
    if m:
        return "附录" + m.group(1).upper()
    m = re.match(r"^(\d{1,2})$", s)
    if m:
        return str(int(m.group(1)))
    return ""


# 目录行：`- 第X章 … 页码` / `- 附录A … 页码` / `- 1 范围 … 页码`
TOC_ENTRY_RE = re.compile(
    r"^-\s*(第\s*[一二三四五六七八九十百零\d]+\s*[章篇]|附录\s*[A-Za-zＡ-Ｚａ-ｚ]|\d{1,2})\s+"
    r"(.+?)\s*\d{1,4}\s*$")
# 假标题残留：**第1部分 …** / **1 范围** / **附录A**
FAKE_BOLD_RE = re.compile(
    r"^\*\*(第\s*[一二三四五六七八九十百零\d]+\s*部分|\d{1,2}\s+[^\s*]|附录\s*[A-Za-z])")


def _toc_labels(lines):
    """从目录块（≥4 行连续 `- `、75% 以上以页码收尾）提取章/附录标签。

    目录跨页会被 `<!-- page: N -->` 与空行打断，二者视为透明；子条目
    （`- 第一节 …`、`- 一、…`、`- 1.1 …`）不算章，只取 第X章 / 附录X / 裸编号。
    """
    runs, cur = [], []
    for l in lines:
        if l.startswith("- "):
            cur.append(l)
        elif not l.strip() or l.startswith("<!-- page:"):
            continue
        else:
            if len(cur) >= 4:
                runs.append(cur)
            cur = []
    if len(cur) >= 4:
        runs.append(cur)
    labels = []
    for run in runs:
        paged = [l for l in run
                 if re.search(r"(?:…+|\.{2,}|·{2,}|\s)\s*\d{1,4}\s*$", l)]
        if len(paged) < 4 or len(paged) * 4 < len(run) * 3:
            continue
        for l in paged:
            m = TOC_ENTRY_RE.match(l)
            if m:
                k = _lab_key(m.group(1))
                if k:
                    labels.append(k)
    return labels


def _h2_labels(text):
    """md 里 h2 的章/附录标签（顺序保留）。"""
    out = []
    for l in text.splitlines():
        if not l.startswith("## "):
            continue
        h = l[3:].strip()
        m = (re.match(r"^(第\s*[一二三四五六七八九十百零\d]+\s*[章篇])", h)
             or re.match(r"^(附录\s*[A-Za-zＡ-Ｚａ-ｚ])", h))
        if m:
            k = _lab_key(m.group(1))
        else:
            m = re.match(r"^(\d{1,2})\s+\S", h)
            k = str(int(m.group(1))) if m else ""
        if k:
            out.append(k)
    return out


def _lab_family(k):
    """标签族：chap（第N章）/ app（附录X）/ num（裸编号）/ ''。"""
    if re.match(r"^第\d+章$", k):
        return "chap"
    if k.startswith("附录"):
        return "app"
    if re.match(r"^\d+$", k):
        return "num"
    return ""


def _md_from_arg(arg):
    """入库夹名 / 夹内 md 路径 / 任意 md 路径 → md 绝对路径。"""
    if os.path.isfile(arg) and arg.lower().endswith(".md"):
        return os.path.abspath(arg)
    p = os.path.join(MDROOT, arg, arg + ".md")
    if os.path.isfile(p):
        return p
    pat = os.path.join(arg if os.path.isabs(arg) else os.path.join(MDROOT, arg), "*.md")
    cands = glob.glob(pat)
    if len(cands) == 1:
        return cands[0]
    raise SystemExit("找不到 md：%s" % arg)


def verify(arg):
    """v3.16 标题体检：生成完/改完之后单读 md 复核标题树，不依赖解析产物。

    硬失败（exit 1）：
      · 残留粗体假标题（**第1部分…** / **1 范围** / **附录A**）——MinerU 直出未规范化
      · 某一族标题「目录有、md 里 0 个」——整族没生成（GB 150 事故形态）
      · 正文引用某附录/某章，但 md 里 0 个该族标题——标题整行丢失
    软警告（--strict 才升级为失败）：
      · 目录有而 h2 部分缺、h2 有而目录无（旧书目录页漏读）
      · 孤立 h4（上级缺 h3 节标题）、孤立 h3（上级缺 h2 章标题）
      · 章号不递增
    无目录块的书只跑结构检查（不报错），避免旧书误杀。
    """
    md = _md_from_arg(arg)
    text = io.open(md, encoding="utf-8-sig").read()
    lines = text.splitlines()
    h = collections.Counter()
    for l in lines:
        m = re.match(r"^(#{1,6})\s", l)
        if m:
            h[len(m.group(1))] += 1

    toc = _toc_labels(lines)
    got = _h2_labels(text)
    c_toc, c_got = collections.Counter(toc), collections.Counter(got)
    miss = list((c_toc - c_got).elements())
    extra = list((c_got - c_toc).elements())
    fam_got = collections.Counter(_lab_family(k) for k in got)
    fam_toc = collections.Counter(_lab_family(k) for k in toc)
    fam_miss = collections.Counter(_lab_family(k) for k in miss)
    fam_extra = collections.Counter(_lab_family(k) for k in extra)

    # 目录块是否可信：同族条目数与 md 的 h2 数相差 ≤30% 才拿来比对；
    # 否则（MinerU 常见：目录只抓回一小截/顺序错乱）只报「跳过」，不制造假警告。
    comparable, skipped = [], []
    for fam, name in (("chap", "第N章"), ("app", "附录X"), ("num", "裸编号章")):
        t, g = fam_toc.get(fam, 0), fam_got.get(fam, 0)
        if not t:
            continue
        if g and g * 10 >= t * 7 and t * 10 >= g * 7:
            comparable.append(fam)
        else:
            skipped.append("%s 目录%d/md%d" % (name, t, g))

    # 正文交叉引用（去掉标题行后统计），用来发现「标题整行丢失、正文还在」
    body = "\n".join(l for l in lines if not l.startswith("#"))
    ref_app = set(re.findall(r"附录\s*([A-H])", body))
    got_app = set(k[-1] for k in got if k.startswith("附录"))
    ref_chap = set()
    for x in re.findall(r"第\s*([0-9]{1,2}|[一二三四五六七八九十百]{1,3})\s*章", body):
        ref_chap.add(int(x) if x.isdigit() else _cn2int(x))
    got_chap = set(int(k[1:-1]) for k in got if re.match(r"^第\d+章$", k))

    fake = [(i + 1, l.strip()) for i, l in enumerate(lines) if FAKE_BOLD_RE.match(l)]

    orphan_h3 = orphan_h4 = 0
    seen_h2 = seen_h3 = False
    seq, seq_bad = [], []
    for l in lines:
        if l.startswith("# "):
            seen_h2 = seen_h3 = False
            seq = []
        elif l.startswith("## "):
            seen_h2, seen_h3 = True, False
            k = _lab_key((re.match(r"^(第\s*[一二三四五六七八九十百零\d]+\s*[章篇])",
                                   l[3:].strip()) or [""])[0])
            if re.match(r"^第\d+章$", k or ""):
                n = int(k[1:-1])
                if seq and n <= seq[-1]:
                    seq_bad.append(k)
                seq.append(n)
        elif l.startswith("### "):
            if not seen_h2:
                orphan_h3 += 1
            seen_h3 = True
        elif l.startswith("#### "):
            if not seen_h3:
                orphan_h4 += 1

    print("[verify] %s" % md)
    print("  标题  h1=%d h2=%d h3=%d h4=%d" % (h[1], h[2], h[3], h[4]))
    if toc:
        print("  目录  条目=%d  比对族=%s  跳过族=%s"
              % (len(toc), ",".join(comparable) or "无", "；".join(skipped) or "无"))
    else:
        print("  目录  未找到目录块（跳过章数/章名比对）")
    print("  标签  第N章=%d 附录X=%d 裸编号=%d"
          % (fam_got.get("chap", 0), fam_got.get("app", 0), fam_got.get("num", 0)))
    print("  假标题 **…** 形态=%d   孤立 h3=%d  h4=%d" % (len(fake), orphan_h3, orphan_h4))

    errs, warns = [], []
    if fake:
        errs.append("残留粗体假标题 %d 处（MinerU 直出未规范化），例：%s"
                    % (len(fake), "；".join("L%d %s" % (i, t) for i, t in fake[:5])))
    for fam, name in (("chap", "第N章"), ("app", "附录X"), ("num", "裸编号章")):
        t, g = fam_toc.get(fam, 0), fam_got.get(fam, 0)
        if not t:
            continue
        if g == 0:
            errs.append("目录有 %d 个%s，md 里 0 个——整族标题没生成" % (t, name))
        elif fam in comparable and fam_miss.get(fam):
            warns.append("%s 目录 %d 个、md %d 个，缺 %d：%s"
                         % (name, t, g, fam_miss[fam],
                            "、".join(k for k in miss if _lab_family(k) == fam)[:200]))
        elif fam in comparable and fam_extra.get(fam):
            warns.append("%s h2 有而目录无 %d 个：%s（目录页可能漏读，人工确认）"
                         % (name, fam_extra[fam],
                            "、".join(k for k in extra if _lab_family(k) == fam)[:200]))
    lack_app = sorted(ref_app - got_app)
    if lack_app:
        (errs if not got_app else warns).append(
            "正文引用附录 %s，但%s" % ("、".join(lack_app),
                                  "md 里一个附录标题都没有" if not got_app else "md 缺该附录标题"))
    if got_chap:
        lack_chap = sorted(ref_chap - got_chap)
        if lack_chap:
            warns.append("正文引用第 %s 章，md 里没有对应 h2"
                         % "、".join(str(n) for n in lack_chap[:10]))
    if orphan_h3:
        warns.append("孤立 h3 %d 处（上级缺 h2 章标题）" % orphan_h3)
    if orphan_h4:
        warns.append("孤立 h4 %d 处（上级缺 h3 节标题）" % orphan_h4)
    if seq_bad:
        warns.append("章号不递增：%s" % "、".join(seq_bad[:12]))

    for m in warns:
        print("  [warn] " + m)
    if _STRICT:
        errs.extend(warns)
    if errs:
        for m in errs:
            print("  ✗ " + m)
        print("TITLE-CHECK FAIL")
        return 1
    print("TITLE-CHECK OK")
    return 0


def main(argv):
    global _ZIP_OVERRIDE, _OUT_OVERRIDE, _STRICT
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
    _STRICT = "--strict" in a
    pos = [x for x in a if not x.startswith("--") and x not in opts.values()]
    if len(pos) < 2:
        raise SystemExit(__doc__)
    mode, key = pos[0], pos[1]
    if mode not in ("dry", "write", "prune", "verify"):
        mode, key = key, mode
    if mode == "prune":
        _prune(key)
    elif mode == "verify":
        return verify(key)
    else:
        _build_book(key, mode)


if __name__ == "__main__":
    sys.exit(main(sys.argv) or 0)
