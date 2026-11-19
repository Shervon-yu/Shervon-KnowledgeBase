# -*- coding: utf-8 -*-
import io

io.open(r'D:\Shervon_KnowledgeBase\90-tool\VERSION', 'w', encoding='utf-8', newline='\n').write('3.7\n')

c = r'D:\Shervon_KnowledgeBase\90-tool\CHANGELOG.md'
t = io.open(c, encoding='utf-8').read()
assert '## v3.7' not in t
sec = """## v3.7 — 2026-11-18（图索引可机器计数）

- 新增 `90-tool\\scripts\\figure-index.py`：从 20-md 抽全部 `](图片/...)` 链接，输出 `30-index\\figures-<入库夹名>.md`（行号/图名/所在节/是否整页/有无题注）。
- `rules.md` §16 判据 ④ 改为可执行口径：图索引表体行数 = 图片链接数；`整页图-pNN_n`、`未命名图N` 类无题图在 sources 页声明「无题非缺图」，缺图另见 `40-scratch\\figures-report-*.json`。
- 动机：v3.6 的 ④（561 图逐张说明）无法机器校验，且 561 行超过单页 150 行上限，逐页拆分会把 wiki 变成图目录。

"""
assert '## v3.6' in t
io.open(c, 'w', encoding='utf-8', newline='\n').write(t.replace('## v3.6', sec + '## v3.6', 1))
print('ok')
