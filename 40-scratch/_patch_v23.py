# -*- coding: utf-8 -*-
"""按审计清单批量修正 rules/prompt/README/脚本（v2.3）。每个替换都断言原文存在。"""
import io, os, sys

ROOT = r'D:\Shervon_KnowledgeBase'
results = []

def read(path):
    with io.open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    return text, bom

def write(path, text, bom):
    data = text.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    with io.open(path, 'wb') as f:
        f.write(data)

def patch(fname, pairs, keep_bom=None):
    path = os.path.join(ROOT, fname) if not os.path.isabs(fname) else fname
    text, bom = read(path)
    for old, new in pairs:
        if old not in text:
            results.append(('MISS', fname, old[:40]))
            continue
        text = text.replace(old, new, 1)
        results.append(('OK', fname, old[:40]))
    write(path, text, bom if keep_bom is None else keep_bom)

# ---------------- rules.md ----------------
patch(r'90-tool\rules.md', [
    ('# 入库规则 v2.2', '# 入库规则 v2.3'),
    ('v2.2 相对 v2.1 的改动：',
     'v2.3 的改动（2026-11-12，按审计清单）：图名禁用字符补 `[ ] { } # %` 并剥引用号 `[31]`；§5 链接空格写 `%20`；§2/§6 夹名以版权页校准并可改名；§11 与 ingest 内部调用对齐；§4.4/§4.5 明确外部 agent 只动自己的夹；§7 增加「图题存图缺」登记；§8 例外与 §2 统一；§9 手工回退留 `_done` 标记；§10 汇报加图链自检与缺图两项；新增 `check-links.ps1`。\n\nv2.2 相对 v2.1 的改动：'),
    ('- 自动建夹的命名：取文件名里的书名与作者，缺项写 `NA`，形如 `书名_作者_NA_NA`；文件名带 `(作者编著)`/`（作者主编）` 的，去掉括号与「编著/主编/著/编」；书名内全角 `－` 归一为半角 `-`。',
     '- 自动建夹的命名：取文件名里的书名与作者，缺项写 `NA`，形如 `书名_作者_NA_NA`；文件名带 `(作者编著)`/`（作者主编）` 的，去掉括号与「编著/主编/著/编」；书名内全角 `－` 归一为半角 `-`。**这只是初值**：解析完必须用正文版权页/CIP 校准书名、版次、年份（例：文件名「汽液」而版权页是「气液」），不符就改名——入库夹、md 文件名、`10-source` 目录、frontmatter 的 `title/src` 同步改，改完重跑 `catalog.ps1`。'),
    ('- **入库成功后，`00-inbox` 里这个文件夹连同原件一并删除**（原件此时已进 `10-source`，inbox 只作传送带，不作仓库）。解析失败或走第 9 节手工回退时**保留**，并在 `todo.md` 留痕。',
     '- **入库成功后，`00-inbox` 里这个文件夹若已空则删除**（原件此时已移进 `10-source`，inbox 只作传送带，不作仓库）。解析失败或走第 9 节手工回退时**保留原文件**，并在 `todo.md` 留痕。'),
    ('`kind` 取值：`book standard paper project web other note`。`topic` 填分类夹名；扁平时填 `NA`。',
     '`kind` 取值：`book spec paper project web other note`（`spec` = 标准/规范，避免与解析档位 `standard` 混淆）。`topic` 填分类夹名；扁平时填 `NA`；分组后手工补或由 `catalog.ps1` 回写。'),
    ('3. 没有合适的，但存在若干个能凑成一类的入库夹 → 新建分类夹，把它们和新夹一起移进去。',
     '3. 没有合适的，但存在若干个能凑成一类的入库夹 → 新建分类夹，**只把本次这一本放进去；别人的入库夹不动**（批量归并见 4.5）。'),
    ('- 全局重排（把散落入库夹归并、拆超限夹）由 **DSH** 负责；',
     '- 全局重排（把散落入库夹归并、拆超限夹）由 **DSH** 负责；外部 agent 建分类夹时可移动本次入库的夹，归并既有夹只有 DSH 能做；'),
    ('- **禁用字符**：`( ) ( ) * ? : " < > | / \\` 一律换成空格或下划线——括号会截断 markdown 的 `![](...)` 链接，是硬错误。',
     '- **禁用字符**：`( ) [ ] { } * ? : " < > | / \\ # %` 一律换成空格或下划线——括号/方括号会截断 markdown 的 `![](...)` 链接，是硬错误；图题里的引用号（`[31]`、`[31-33]`）在命名前先剥掉。'),
    ('- **md 链接**：`![](图片/图1.1 问题描述.jpg)`——带 `图片/` 前缀，不出现绝对路径。',
     '- **md 链接**：`![](图片/图1.1 问题描述.jpg)`——带 `图片/` 前缀，不出现绝对路径；目标含空格时写 `%20` 更稳（`check-links.ps1` 会按解码后的路径校验）。'),
    ('| PDF 解析失败 | — | 原件归档，正文记 `pending`，进 `todo.md` |',
     '| PDF 解析失败 | — | 原件归档，正文记 `pending`，进 `todo.md` |\n| 图题存在但 MinerU 未导出图 | — | `figures.py`/`check-links.ps1` 报缺图数 + 清单，进 `todo.md`（可选：按页重解析补齐） |'),
    ('1. 不删任何文件（原件、md、图片）；例外两条：`figures.py --dedupe` 删**同字节副本**（第 11 节）；`00-inbox` 里已成功入库的原件按第 2 节清空。',
     '1. 不删任何文件（原件、md、图片）；例外三条：`figures.py --dedupe` 删**同字节副本**（第 11 节）；`00-inbox` 里已成功入库且已清空的文件夹（第 2 节）；`check-links.ps1` 只删**指向不存在文件的链接标记**，不删图。'),
    ('5. 汇报里注明"手工完成，未跑脚本"。',
     '5. 汇报里注明"手工完成，未跑脚本"。\n6. 留在 `00-inbox` 的文件夹里放一个空的 `_done` 标记文件；下次会话按第 2 节跳过它，并在 `todo.md` 里记一笔。'),
    ('质检：ok / warn / quarantine\n元数据缺失：edition, year',
     '质检：ok / warn / quarantine\n图链：SELFCHECK refs=N ok=N unresolved=0\n缺图：N 张（清单见 todo.md）\n元数据缺失：edition, year'),
    ('`90-tool\\scripts\\figures.py`：读 MinerU 产物 → 按 bbox 把图题配回图片 → 按 SHA256 去重 → 改名为 `图X.Y 说明[_a].jpg` 并放进 `图片\\` → 改写 md 引用为 `图片/...` → 报告写 `40-scratch\\figures-report-<入库夹>.json`。',
     '`90-tool\\scripts\\figures.py`：读 MinerU 产物 → 按 bbox 把图题配回图片 → 按 SHA256 去重 → 改名为 `图X.Y 说明[_a].jpg` 并放进 `图片\\` → 改写 md 引用为 `图片/...` → 报告写 `40-scratch\\figures-report-<入库夹>.json`。**它由 `ingest.ps1` 内部调用，MinerU 原始产物随后即被删除**——只有另外保留了产物时才可手工重跑（`--mineru` 指向那份产物）。'),
    ('- 跑完必须重新检查：`broken` 应为 0。',
     '- 跑完必须重新检查：`broken` 应为 0。用 `check-links.ps1 -Md <md>`（默认 dry-run，`-Fix` 才修），输出 `unresolved=0` 才算过。'),
])

# ---------------- prompt-dsh.md ----------------
patch(r'90-tool\prompt-dsh.md', [
    ('0. 先启动费用锁（见上【费用锁】），确认看门狗进程起来了，再往下走。',
     '0. 先启动费用锁（见上【费用锁】），用 `job_output` 确认首屏已打印；再确认 `40-scratch\\.ingest.lock` 不存在（存在=另一本正在入，停）。'),
    ('   - 空 → 停，告诉我放书。',
     '   - 空 → 停，告诉我放书。\n   - 夹里有 `_done` 标记 → 是手工回退留下的，跳过并告诉我。'),
    ('   图名归一（`figures.py --dedupe --apply`）和重建索引（`catalog.ps1`）**`ingest.ps1` 内部已跑**，不必再单跑；只有它报出图名未归一时，才按 `rules.md` 第 11 节手工补跑（那时 MinerU 产物已被脚本清掉，`--mineru` 需先保留）。',
     '   图名归一（`figures.py --dedupe --apply`）、图链自检（`check-links.ps1 -Fix`）、重建索引（`catalog.ps1`）**`ingest.ps1` 内部已跑**，不必再单跑。跑完按 `rules.md` 第 2 节用版权页核对书名/版次/年份；不符就改名（入库夹、md、`10-source`、frontmatter 的 `src` 同步）并重跑 `catalog.ps1`。'),
    ('6. 按 `rules.md` 第 10 节的格式汇报。',
     '6. 按 `rules.md` 第 10 节的格式汇报；图链自检 `unresolved` 不为 0、或有缺图，一并列出。'),
])

# ---------------- prompt.md（外部 agent） ----------------
patch(r'90-tool\prompt.md', [
    ('3. 看它给的预览，确认书名和分类没错，再说"执行"。',
     '3. 跑完按 rules 第 2 节用版权页核对书名/版次/年份，不符就改名并重跑 catalog。'),
])

# ---------------- catalog.ps1 ----------------
patch(r'90-tool\scripts\catalog.ps1', [
    ('> 生成时间 {0}。处理完一项就删掉对应行；本文件每次跑 catalog.ps1 会重算，手删的行不会再出现。',
     '> 生成时间 {0}。删行无效：本文件每次跑 catalog.ps1 都会按现状重算，只有修掉根因（补元数据/重解析/改图名）那一项才会消失。'),
])

# ---------------- figures.py ----------------
patch(r'90-tool\scripts\figures.py', [
    ("BAD_CHARS = re.compile(r'[*?:\"<>|/\\\\\\r\\n\\t]')",
     "BAD_CHARS = re.compile(r'[*?:\"<>|/\\\\\\[\\](){}#%\\r\\n\\t]')"),
    ("    t = ' '.join(str(text).split()).replace('$', '').replace('{', '').replace('}', '')",
     "    t = ' '.join(str(text).split()).replace('$', '').replace('{', '').replace('}', '')\n    t = re.sub(r'\\[\\d+(?:[,\\-\\u2013]\\d+)*\\]', '', t)"),
])

# ---------------- check-links.ps1：%20 解码后再判存在 ----------------
patch(r'90-tool\\scripts\\check-links.ps1', [
    ('  $full = Join-Path $mdDir ($rel -replace \'\\\\\',\'/\')',
     '  $decoded = [Uri]::UnescapeDataString($rel)\n  $full = Join-Path $mdDir ($decoded -replace \'\\\\\',\'/\')'),
])

# ---------------- README.md 全量重写 ----------------
readme = u'''# Shervon 知识库

一个能整个拷走的文件夹：原件 + 可搜索正文 + 一本书目 + 一份待办。

## 目录一眼看懂

| 目录 | 放什么 | 谁动它 |
|---|---|---|
| `00-inbox\\` | 待入库：一本书一个文件夹（散文件也行，脚本会建夹） | 人投放，入库后清空 |
| `10-source\\` | 原件（PDF / 图片 / docx），只读存档 | 只增不改 |
| `20-md\\` | 解析出的正文 `.md` + 每本书的 `图片\\` | 脚本生成 |
| `30-index\\` | `manifest.csv` / `catalog.md` / `todo.md` | `catalog.ps1` 重建 |
| `40-scratch\\` | 报告、日志、脚本、临时目录 | 只往这里放新建物 |
| `90-tool\\` | 规则（`rules.md`）、提示词、脚本 | 改规则时 |

一本书的正文与图：

```
20-md\\<书名_作者_版次_年份>\\<同名>.md
20-md\\<书名_作者_版次_年份>\\图片\\图2.6 NaI T1 闪烁探测器.jpg
```

`20-md` 入库夹少于 20 个时全部扁平；到 20 个才允许分组，超过 40 个必须分组（见 `rules.md` 第 4 节）。

## 往库里加资料

**一个会话只处理一本书。**

1. 把书丢进 `00-inbox\\`：直接放 PDF 最省事（散文件会自动建 `书名_作者_NA_NA` 夹）；想自己指定夹名就建 `书名_作者_版次_年份`，不知道的写 `NA`。
2. 用 `D:\\Shervon_KnowledgeBase` 开新会话，贴 `90-tool\\prompt-dsh.md` 的内容（免费 agent 用 `90-tool\\prompt.md`）。
3. 默认不预览、不等待：`ingest.ps1` 一次跑完 MinerU 解析 → 图名归一 → 图链自检 → 重建索引，账本与缺图都记进 `30-index\\todo.md`。
4. 需要补作者/版次/年份时，打开 `todo.md` 照着补对应 md 的 frontmatter；补完重跑 `catalog.ps1` 那一项就消失。

解析后会用版权页核对书名/版次/年份，不符会改名（夹、md、`10-source` 同步）。

入库开销：MinerU 纯文字页约 4 秒/页、图纸页约 26 秒/页；166 页扫描书约 15 分钟，显卡（DirectML/Quadro P6000）会自动用上。

入 DSH 检索索引由我收尾：你说“入索引”才做。

## 查资料

| 场景 | 怎么查 |
|---|---|
| 知道是哪本书 | `30-index\\catalog.md`，按书名/类型找 |
| 记得一句话或公式 | 在 `20-md\\` 全文搜（Everything / VS Code / Obsidian） |
| 说不清在哪 | 直接问我，要求“书名 + 章节 + 原句/图号” |

图缺失时正文不会留破图占位：`check-links.ps1` 会把指向不存在文件的链接删掉，图注文字保留；缺了哪些记在 `todo.md`。

## 图示约定

图题 `图X.Y 说明`；文件名 `图X.Y 说明.jpg`，子图 `_a/_b`，重号 `_2`；图题里不能出现 `( ) [ ] { } * ? : " < > | / \\ # %`（会截断链接），引用号 `[31]` 命名前剥掉。

## 同步到家里

整个 `D:\\Shervon_KnowledgeBase` 拷走即可，不需要数据库。别只同步 `20-md`——丢了 `10-source` 就无法重解析。

## 红线

不删原件、不改原件、不联网上传、不装软件、不自创分类。规则没覆盖的写进 `todo.md`，不要自己发明流程。

## 排错

| 现象 | 原因 | 怎么办 |
|---|---|---|
| 提示“禁止运行脚本” | 执行策略 | 用提示词里的完整命令，带 `-ExecutionPolicy Bypass` |
| 中文乱码 / ParserError | `.ps1` 缺 UTF-8 BOM | 存成“UTF-8 带 BOM” |
| PDF 全是 pending | 解析出错 | 看 `30-index\\issues.log` 末尾报错；MinerU 在 `C:\\Users\\shervon\\.local\\mineru`（4.1.7） |
| md 里“找不到图片” | 图名含 `[]` 或图未导出 | 跑 `check-links.ps1 -Md <md> -Fix` |
| 入库报锁 | `40-scratch\\.ingest.lock` 存在 | 确认没有别的入库会话后删掉它 |
| docx 读不出 | 老 `.doc` 格式 | 另存为 `.docx` |
'''
with io.open(os.path.join(ROOT, 'README.md'), 'wb') as f:
    f.write(readme.encode('utf-8'))
results.append(('OK', 'README.md', 'full rewrite'))

for r in results:
    print('\t'.join(r))
print('MISS count =', sum(1 for r in results if r[0] == 'MISS'))
