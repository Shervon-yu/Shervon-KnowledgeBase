# -*- coding: utf-8 -*-
import io

# 1) rules.md §16 完成判据扩为「五合一」
p = r'D:\Shervon_KnowledgeBase\90-tool\rules.md'
s = io.open(p, encoding='utf-8-sig').read()
old = '**完成判据（v3.3）**：验收表七行全过 + `SELFCHECK unresolved=0` + `wiki-lint` 0 条 + 已 `git commit`，四者缺一不算入库完成；未过不许进 `50-wiki`，也不许在汇报里把它写成「已入库」。'
new = ('**完成判据（v3.6）**：五条全过才算入库完成，缺一不许写成「已入库」——\n'
       '1. `ingest-build.ps1` 验收表七行全过 + `SELFCHECK unresolved=0`；\n'
       '2. `wiki-lint.ps1` 0 条；\n'
       '3. **覆盖率门** `coverage.py -Book "<入库夹名>" --strict` 退出码 0（本书 md 的每个 `###` 小节都至少被 wiki 引用一次；未被覆盖的节必须当场成页，不能留到汇报里）；\n'
       '4. 图索引覆盖：`sources` 页的图索引条数 ≥ 该章主要图题数，`整页图-pNN_n` 类无题图必须逐张说明「原书无题」；\n'
       '5. 已 `git commit`。\n\n'
       '> 教训（v3.6）：v3.3~v3.5 的判据只到「lint 0 + commit」，于是入库可以交出一个 8 页的 wiki 就宣布完成——判据里没有「书的内容被覆盖」这一项，机器又不会自己发现。覆盖率门就是补这个洞：它把「读没读完」变成可计算的退出码。')
assert old in s, 'rules completion line not found'
s = s.replace(old, new, 1)

# 2) rules 变更段加 v3.6 一行
old2 = '- §16 增「完成判据」：验收表七行全过'
new2 = ('- §16 完成判据升到 v3.6 五条（新增覆盖率门 `coverage.py --strict` 与图索引覆盖）。\n- §16 增「完成判据」：验收表七行全过')
if old2 in s:
    s = s.replace(old2, new2, 1)
io.open(p, 'w', encoding='utf-8-sig', newline='\n').write(s)

# 3) prompt-dsh.md 步骤：入库收尾加覆盖率门
q = r'D:\Shervon_KnowledgeBase\90-tool\prompt-dsh.md'
t = io.open(q, encoding='utf-8-sig').read()
old3 = '8. `git commit -m "wiki(ingest): <书名> touch=N"`'
new3 = ('8. **覆盖率门**：`python 90-tool\\scripts\\coverage.py -Book "<入库夹名>" --strict`，必须 exit 0；\n'
        '   有 UNCOVERED 就继续读那一节、成页，直到 uncovered=0（这是「通读」的机器判据，不是自觉）。\n'
        '9. `git commit -m "wiki(ingest): <书名> touch=N"`')
if old3 in t:
    t = t.replace(old3, new3, 1)
io.open(q, 'w', encoding='utf-8-sig', newline='\n').write(t)

# 4) VERSION / CHANGELOG
io.open(r'D:\Shervon_KnowledgeBase\90-tool\VERSION', 'w', encoding='utf-8', newline='\n').write('3.6\n')
c = r'D:\Shervon_KnowledgeBase\90-tool\CHANGELOG.md'
cs = io.open(c, encoding='utf-8-sig').read()
entry = """## v3.6 — 2026-11-18（覆盖率门：把「读没读完」变成退出码）

- 新增 `90-tool\\scripts\\coverage.py`：解析 20-md 的 `##`/`###` 标题成节区间，统计 wiki 页里 `#L` 引用落在哪些节，输出 `sections/covered/uncovered`；`--strict` 时 uncovered>0 退出码 1。
- `rules.md` §16 完成判据由 4 条升到 5 条：验收表 + `SELFCHECK=0`、`wiki-lint` 0 条、**覆盖率门 exit 0**、图索引覆盖（无题整页图逐张说明）、已 commit。
- `prompt-dsh.md` 入库收尾新增覆盖率门一步，明确「有 UNCOVERED 就继续读那一节、成页」。
- 动机：v3.3~v3.5 的判据止于「lint 0 + commit」，机器无法判断书的内容是否被覆盖，于是可以交 8 页 wiki 就宣布完成。覆盖率门把这件事变成可计算、可复跑、可卡人的退出码。
"""
cs = entry + "\n" + cs
io.open(c, 'w', encoding='utf-8-sig', newline='\n').write(cs)
print('ok')
