# -*- coding: utf-8 -*-
import io
p = r'D:\Shervon_KnowledgeBase\50-wiki\sources\搅拌与混合设备设计选用手册.md'
t = io.open(p, encoding='utf-8').read()
old = """## 63 张「有题无图」

正文里出现了图题（如 `图2-4 聚合物溶液的第二法向应力差`、`图2-5 各种搅拌器的功率曲线`），但该页图像块未被 OCR 抽出，md 中没有对应 `图片/` 链接。
处理：逐条清单在 `40-scratch/figures-report-搅拌与混合设备设计选用手册_陈志平_第1版_2004.json` 的 `missing[]`（含 `line` 与 `caption`）；
成因是原书该页为线条图/小图，MinerU standard 档的版面检测未判为 image 块，不是入库时丢图。
需要这些图时按 `missing[].line` 回查 PDF 对应页，或用图纸档（`--tier 图纸`）重解析该页补齐。

"""
new = """## 63 张「有题无图」

正文有图题、但 OCR 未抽出图像块（线条图/小图，standard 档未判为 image），md 里没有对应 `图片/` 链接。逐条见 `40-scratch/figures-report-…json` 的 `missing[]`（`line` + `caption`）；需要时按行号回查 PDF，或用图纸档重解析该页。

"""
assert old in t
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new, 1))
print('ok')
