# -*- coding: utf-8 -*-
import io, re

ROOT = r'D:\Shervon_KnowledgeBase'

def rd(p): return io.open(p, encoding='utf-8').read()
def wr(p, t): io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

# ---------- 1. figure-index.py 参数化 ----------
p = ROOT + r'\90-tool\scripts\figure-index.py'
t = rd(p)
t = t.replace(
"""import io, os, re, sys

book = '搅拌与混合设备设计选用手册_陈志平_第1版_2004'
md = os.path.join(r'D:\\Shervon_KnowledgeBase\\20-md', book, book + '.md')""",
"""import io, os, re, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument('-Book', required=True, help='入库夹名')
ap.add_argument('--Root', default=r'D:\\Shervon_KnowledgeBase')
a = ap.parse_args()
book = a.Book
ROOT = a.Root
md = os.path.join(ROOT, '20-md', book, book + '.md')""")
t = t.replace("""dst = os.path.join(r'D:\\Shervon_KnowledgeBase\\30-index', f'figures-{book}.md')""",
              """dst = os.path.join(ROOT, '30-index', f'figures-{book}.md')""")
wr(p, t)
print('figure-index ok')

# ---------- 2. rules.md ----------
p = ROOT + r'\90-tool\rules.md'
t = rd(p)
assert t.startswith('# 入库规则 v3.3')
t = t.replace('# 入库规则 v3.3', '# 入库规则 v3.7', 1)

anchor = "- §16 完成判据升到 v3.6 五条（新增覆盖率门 `coverage.py --strict` 与图索引覆盖）。\n"
add = anchor + (
"- v3.7：图索引改为可机器计数（`figure-index.py -Book` → `30-index\\figures-<入库夹名>.md`）；"
"sources 必须块状三行（`book/section/lines`），行内写法会被 lint 判「无来源」；"
"`.ps1` 必须带 UTF-8 BOM（PS 5.1 按 ANSI 读中文会语法错），含中文的 `.py` 用 `write` 落盘、勿用 here-string；"
"新书禁用 `refs-remap.py`（`book_of()` 只收录机械密封/化工原理/气液搅拌釜三本，其余一律按 §14 手工比对锚点重取行号）。\n")
assert anchor in t
t = t.replace(anchor, add, 1)

t = t.replace("4. 图索引：`python 90-tool\\scripts\\figure-index.py` 生成",
              "4. 图索引：`python 90-tool\\scripts\\figure-index.py -Book \"<入库夹名>\"` 生成", 1)
t = t.replace("**完成判据（v3.6）**", "**完成判据（v3.7）**", 1)

# 守卫段补 refs-remap 禁用于新书
old_gate = "- 重建会换掉全部行号。步骤固定：`git checkout -- '50-wiki' kb-blueprint.md` → `refs-remap.py dry`"
new_gate = ("- 新书（`refs-remap.py` 的 `book_of()` 未收录）**一律不用 refs-remap**，按 §14 用「旧/新 md 逐行比对 + 逐条原文校验」手工重取行号，只改本书专用页。\n"
            "- 重建会换掉全部行号（旧书）。步骤固定：`git checkout -- '50-wiki' kb-blueprint.md` → `refs-remap.py dry`")
assert old_gate in t
t = t.replace(old_gate, new_gate, 1)

# §13 补三条硬约束
old13 = "- 文件名 = `title` = 正名；禁用字符 `\\ / : * ? \" < > |`。"
new13 = (old13 + "\n"
         "- `sources` 必须块状三行写法（`book:` / `section:` / `lines:`）；行内 `sources: [书名]` 会被 `wiki-lint.ps1` 判「无来源」。\n"
         "- 新建 `.ps1` 脚本必须带 UTF-8 BOM（`EF BB BF`），否则 PowerShell 5.1 按 ANSI 读中文会报语法错。\n"
         "- 含中文的脚本一律用 `write` 工具落盘，不要用 `Out-File`/here-string（PS 5.1 会写出乱码）。")
assert old13 in t
t = t.replace(old13, new13, 1)
wr(p, t)
print('rules ok')

# ---------- 3. prompt-dsh.md 步骤 6-10 ----------
p = ROOT + r'\90-tool\prompt-dsh.md'
t = rd(p)
old = """6. 入 wiki（按 `90-tool\\AGENTS.wiki.md` §5 六步）：写 `50-wiki\\sources\\<书名>.md` 章节地图 → 3~8 张 `concepts\\` 概念页（每页必须有本书出处，不许空转述）→ 回改受影响的既有页（openq/comparisons/entities）→ 补 `50-wiki\\index.md` 摘要列（`wiki-index.ps1` 生成表格，人只补摘要）→ 记 `50-wiki\\log.md`。
   - 每页守 `rules.md` §13：frontmatter 字段顺序固定、单页 ≤150 行、入链 ≥2、图引用带 ≥1 句文字转述。
   - 引用一律 `《书名》§节号（#L行号）`，行号取 20-md 正文绝对行号（§14）。
7. 跑 `powershell -NoProfile -ExecutionPolicy Bypass -File "90-tool\\scripts\\wiki-lint.ps1"`，八项全绿为止（死链/孤儿/无来源/超长/同义/过期/index 漂移/图无转述）。
8. `git add -A; git commit -m "wiki(ingest): <书名> touch=N"`（N = 新增+改动页数）。
9. 打开 `30-index\\todo.md`，把新增待办逐条念给我；有未闭合项就写进 `50-wiki\\openq\\`。
10. 按 `rules.md` §10 汇报，并在末尾加三行：
    - 改动文件：<路径清单>
    - wiki：sources 1 / concepts N / 更新 M
    - 验收：ingest-build 七行全过；SELFCHECK unresolved=0；wiki-lint 0 条；commit <短 hash>"""
new = """6. 入 wiki（按 `90-tool\\AGENTS.wiki.md` §5 六步）：写 `50-wiki\\sources\\<书名>.md` 章节地图 → 先写「能独立成页」的概念页（**不设页数上限，按节写，宁多勿少**）→ 回改受影响的既有页（openq/comparisons/entities）→ 记 `50-wiki\\log.md`。
   - 每页守 `rules.md` §13：frontmatter 九字段顺序固定、`sources` 用块状三行、单页 ≤150 行、入链 ≥2、图引用带 ≥1 句文字转述。
   - 引用一律 `《书名》§节号（#L行号）`，行号取 20-md 正文绝对行号（§14）。
7. **覆盖率门（不通过不许往下走）**：`python 90-tool\\scripts\\coverage.py -Book "<入库夹名>" --strict`。
   - 退出码非 0：按打印的 UNCOVERED 小节逐节读 md、成页，回到第 6 步；直到 `uncovered=0`。
   - 判据是「每个 `###` 小节都至少被 wiki 页引用一次」，不是页数指标。
8. 图索引：`python 90-tool\\scripts\\figure-index.py -Book "<入库夹名>"`，核对表体行数 = 20-md 内 `](图片/...)` 链接数；整页/无题图在 sources 页声明「无题非缺图」，有题无图写进 sources「已知缺陷」并指向 `40-new\\figures-report-*.json`。
9. `powershell -NoProfile -ExecutionPolicy Bypass -File "90-tool\\scripts\\wiki-index.ps1"`（页面 >120 行会自动分册）→ `wiki-lint.ps1` 八项全绿（死链/孤儿/无来源/超长/同义/过期/index 漂移/图无转述），有问题就改到 0。
10. `git add -A; git commit -m "wiki(ingest): <书名> touch=N"`（N = 新增+改动页数）。
11. 打开 `30-index\\todo.md`，把新增待办逐条念给我；有未闭合项就写进 `50-wiki\\openq\\`。
12. 按 `rules.md` §10 汇报，并在末尾加四行：
    - 改动文件：<路径清单>
    - wiki：sources 1 / concepts N（其中新增 X）/ 更新 M
    - 覆盖率：sections=N covered=N uncovered=0（coverage.py exit 0）
    - 验收：ingest-build 七行全过；SELFCHECK unresolved=0；lint 0 条；图索引 N 行；commit <短 hash>"""
assert old in t
t = t.replace(old, new, 1)
wr(p, t)
print('prompt-dsh ok')

# ---------- 4. prompt.md 分工说明 ----------
p = ROOT + r'\90-tool\prompt.md'
t = rd(p)
anchor = "- md 已是生成版时默认跳过重建（保人工图名）；确需重建加 `-Force`，并按 `rules.md` §16 重算全部 `#L`。"
add = anchor + "\n- 分工：本提示词只负责到 **raw 层**（`10-source` + `20-md` + 30-index）。`50-wiki` 的 ingest、覆盖率门、`wiki-lint`、`git commit` 由 DSH 会话按 `prompt-dsh.md` 执行，外部 agent 不要写 `50-wiki`。"
assert anchor in t
t = t.replace(anchor, add, 1)
wr(p, t)
print('prompt ok')
