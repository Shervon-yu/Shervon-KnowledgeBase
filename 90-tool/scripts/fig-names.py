# -*- coding: utf-8 -*-
r"""fig-names.py —— 给「无图题图」定名（二维码识别 + 挂同页图题）。

背景：MinerU 常把一个图拆成多块，只给其中一块图题；也可能把书里的二维码当成图导出。
本脚本按确定性规则处理，绝不编造图号。

规则（按顺序）：
  1) 方形小图（宽高差 ≤15% 且长边 ≤200px）判定为二维码 → `二维码-第NN页.jpg`
  2) 否则挂同页图题：优先取该图之后最近的图题（子图在前、总题在后），
     超过 MAXDIST 行再取之前最近的；命名 `<图题>_a.jpg`、`_b` …
  3) 都找不到 → 保留原名 `图_第NN页_n.jpg`，在报告里列出，留人工。

用法：
  python fig-names.py dry   <入库夹名> [--maxdist 25]
  python fig-names.py apply <入库夹名> [--maxdist 25]

入库夹名 = 20-md 下的文件夹名。只改 md 与 图片\，不动正文其他内容。
"""
import io, os, re, sys, glob, argparse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
MDROOT = os.path.join(ROOT, "20-md")

IMGCAP = re.compile(r"^!\[.*?\]\(图片/(图\s*\d{1,2}[-.．]\d{1,2}[^)]*\.jpg)\)")
UNCAP = re.compile(r"^!\[.*?\]\(图片/((?:图_第|整页图-p)(\d+)页?_?\d*\.jpg)\)")
UNCAP2 = re.compile(r"^!\[.*?\]\(图片/(图_第(\d+)页_(\d+)\.jpg)\)")
PAGE = re.compile(r"^<!-- page: (\d+) -->")
TRY_PIL = True
try:
    from PIL import Image
except Exception:
    TRY_PIL = False


def is_qr(path):
    if not TRY_PIL or not os.path.exists(path):
        return False
    try:
        w, h = Image.open(path).size
    except Exception:
        return False
    if max(w, h) > 200:
        return False
    return abs(w - h) <= 0.15 * max(w, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["dry", "apply"])
    ap.add_argument("book")
    ap.add_argument("--maxdist", type=int, default=25)
    a = ap.parse_args()

    folder = os.path.join(MDROOT, a.book)
    mds = glob.glob(os.path.join(folder, "*.md"))
    if not mds:
        raise SystemExit("找不到 md：%s" % folder)
    path = mds[0]
    imgdir = os.path.join(folder, "图片")
    L = io.open(path, encoding="utf-8").read().split("\n")

    page_of, cp = [], "1"
    for ln in L:
        m = PAGE.match(ln.strip())
        if m:
            cp = m.group(1)
        page_of.append(cp)

    caps = defaultdict(list)
    for i, ln in enumerate(L):
        m = IMGCAP.match(ln)
        if m:
            caps[page_of[i]].append((i, os.path.splitext(m.group(1))[0]))

    plan, skip = [], []
    for i, ln in enumerate(L):
        m = UNCAP2.match(ln)
        if not m:
            continue
        old, pg = m.group(1), m.group(2)
        src = os.path.join(imgdir, old)
        if is_qr(src):
            plan.append((i, old, "二维码-第%s页" % pg, "qr"))
            continue
        c = caps.get(page_of[i], [])
        after = sorted((ci - i, ci, nm) for ci, nm in c if ci > i)
        before = sorted((i - ci, ci, nm) for ci, nm in c if ci < i)
        pick = None
        if after and after[0][0] <= a.maxdist:
            pick = after[0][2]
        elif before and before[0][0] <= a.maxdist:
            pick = before[0][2]
        if pick:
            plan.append((i, old, pick, "caption"))
        else:
            skip.append((i, old, "no caption within %d lines" % a.maxdist))

    qr = sum(1 for p in plan if p[3] == "qr")
    cap = sum(1 for p in plan if p[3] == "caption")
    print("[%s] mode=%s  待定名=%d（二维码 %d / 挂图题 %d）  留人工=%d"
          % (a.book, a.mode, len(plan), qr, cap, len(skip)))
    for r in plan[:8]:
        print("   plan", r)
    for r in skip[:8]:
        print("   skip", r)

    if a.mode != "apply" or not plan:
        return
    used = set(os.listdir(imgdir)) if os.path.isdir(imgdir) else set()
    for i, old, base, why in plan:
        suffix = "" if why == "qr" else "_a"
        cand = base + suffix
        k = 1
        while cand + ".jpg" in used:
            k += 1
            cand = "%s_%s" % (base, chr(96 + k)) if why != "qr" else "%s-%d" % (base, k)
        new = cand + ".jpg"
        used.add(new)
        src = os.path.join(imgdir, old)
        if os.path.exists(src):
            os.replace(src, os.path.join(imgdir, new))
        L[i] = L[i].replace(old, new)
    io.open(path, "w", encoding="utf-8", newline="\n").write("\n".join(L))
    print("   applied %d renames" % len(plan))


if __name__ == "__main__":
    main()
