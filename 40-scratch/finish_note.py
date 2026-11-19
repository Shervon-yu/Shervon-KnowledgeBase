# -*- coding: utf-8 -*-
import io

S = r'D:\Shervon_KnowledgeBase\50-wiki\sources\搅拌与混合设备设计选用手册.md'
t = io.open(S, encoding='utf-8').read()
marker = '## 63 张「有题无图」'
add = """## 63 张「有题无图」

正文里出现了图题（如 `图2-4 聚合物溶液的第二法向应力差`、`图2-5 各种搅拌器的功率曲线`），但该页图像块未被 OCR 抽出，md 中没有对应 `图片/` 链接。
处理：逐条清单在 `40-scratch/figures-report-搅拌与混合设备设计选用手册_陈志平_第1版_2004.json` 的 `missing[]`（含 `line` 与 `caption`）；
成因是原书该页为线条图/小图，MinerU standard 档的版面检测未判为 image 块，不是入库时丢图。
需要这些图时按 `missing[].line` 回查 PDF 对应页，或用图纸档（`--tier 图纸`）重解析该页补齐。

"""
if marker not in t:
    t = t.replace('## 图索引的完整清单', add + '## 图索引的完整清单', 1)
    io.open(S, 'w', encoding='utf-8', newline='\n').write(t)
    print('ok')
else:
    print('skip')

L = r'D:\Shervon_KnowledgeBase\50-wiki\log.md'
lt = io.open(L, encoding='utf-8').read()
entry = ("- 2026-11-18 覆盖率补齐：concepts 由 21 → 40 页，78/78 节全覆盖（coverage.py --strict exit 0），"
         "wiki-lint 0 条（102 页），新增 `90-tool\\scripts\\figure-index.py` 与 `30-index\\figures-…md`（561 行，"
         "整页无题图 222 张已声明「无题非缺图」），v3.7 规则：图索引可机器计数。commit 05f208f。\n")
if entry not in lt:
    io.open(L, 'w', encoding='utf-8', newline='\n').write(lt.rstrip('\n') + '\n' + entry)
    print('log ok')
else:
    print('log skip')
