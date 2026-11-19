# -*- coding: utf-8 -*-
import io

p = r'D:\Shervon_KnowledgeBase\90-tool\rules.md'
t = io.open(p, encoding='utf-8').read()
old = "4. 图索引覆盖：`sources` 页的图索引条数 ≥ 该章主要图题数，`整页图-pNN_n` 类无题图必须逐张说明「原书无题」；"
new = ("4. 图索引：`python 90-tool\\scripts\\figure-index.py` 生成 `30-index\\figures-<入库夹名>.md`，"
       "行数（表体）须等于 20-md 内 `](图片/...)` 链接数；`整页图-pNN_n`、`未命名图N` 类无题图在 sources 页声明「无题非缺图」，"
       "缺图另见 `40-new\\figures-report-*.json`；")
assert old in t
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new, 1))

c = r'D:\Shervon_KnowledgeBase\90-tool\CHANGELOG.md'
t = io.open(c, encoding='utf-8').read()
if '## v3.7' not in t:
    head = """# CHANGELOG

## v3.7（2026-11-18）

- 新增 `90-tool\\scripts\\figure-index.py`：从 20-md 抽全部图片链接，输出 `30-index\\figures-<入库夹名>.md`（行号/图名/所在节/整页/题注）。
- `rules.md` §16 判据 ④ 改为可执行口径：图索引表体行数 = 图片链接数；整页无题图在 sources 页声明「无题非缺图」。
- 动因：v3.6 的 ④ 无法机器校验，且 561 行超过单页 150 行上限，逐页拆分会把 wiki 变成图目录。

"""
    io.open(c, 'w', encoding='utf-8', newline='\n').write(t.replace('# CHANGELOG\n', head, 1))
print('ok')
