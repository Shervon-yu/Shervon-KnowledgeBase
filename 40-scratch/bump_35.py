# -*- coding: utf-8 -*-
import io

# VERSION
p = r'D:\Shervon_KnowledgeBase\90-tool\VERSION'
io.open(p, 'w', encoding='utf-8', newline='\n').write('3.5\n')

# CHANGELOG 顶部插入 v3.5
p2 = r'D:\Shervon_KnowledgeBase\90-tool\CHANGELOG.md'
s = io.open(p2, encoding='utf-8-sig').read()
entry = """## v3.5 — 2026-11-18（标题层级、漏章补插、索引分册）

- `md-build.py`：
  - `title_level()` 重写：只有 `第X篇/第X章`→h2、`第X节`→h3、`\\d+\\.\\d+\\.\\d+`→h4、`\\d+\\.\\d+`→h3、`附录/参考文献/前言/序/目录/编后记/致谢/内容提要/符号表`→h2 才成标题，**其余一律降为加粗正文行**（不改行数）。此前未匹配标题一律当 h2，本书实测 h2=624（其中 235 条「一、二、」、287 条「1.」），标题树完全失真；修复后 h2=43、h3=78、降级 584 行。
  - 新增 `_cn2int()` 与 `_inject_missing_chapters()`：从目录行解析 17 章顺序，按「第 k 个 `### 第一节` ↔ 目录第 k 章」定位，MinerU 漏识的章标题（本书第十一、十二、十七章）倒序补插 `## 第X章 标题`。
- `wiki-index.ps1`：页面数使单文件超过 120 行时，自动按 `domain` 拆分为 `index.md`（领域目录）+ `index-<domain>.md`（分册）；未超限时仍写单一 `index.md` 并清理旧分册。此前只打印警告不拆。
- `wiki-lint.ps1`：①`index*.md` 不再计入页面（否则分册文件被当孤儿页/无来源页）；②index 漂移检查改为合并所有 `index*.md` 判定。
- 本书据此重建：行数 20,166、锚点 538、`$$` 444、pipe 表 4944、图 561、`SELFCHECK unresolved=0`、七行验收全过；wiki 行号引用按 `40-scratch\\line-map-20160-to-20166.json`（分段 +2/+4/+6）平移并抽样比对原文。
- 教训：`write` 工具写 `.ps1` 不带 BOM，PowerShell 5.1 按 ANSI 读会因中文变乱码而报语法错；改完必须补 `EF BB BF`。
"""
s = entry + "\n" + s
io.open(p2, 'w', encoding='utf-8-sig', newline='\n').write(s)
print('ok')
