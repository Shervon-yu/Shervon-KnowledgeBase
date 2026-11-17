# Shervon 知识库

一个能整个拷走的文件夹：原件 + 可搜索正文 + 一本书目 + 一份待办。

## 目录一眼看懂

| 目录 | 放什么 | 谁动它 |
|---|---|---|
| `00-inbox\` | 待入库：一本书一个文件夹（散文件也行，脚本会建夹） | 人投放，入库后清空 |
| `10-source\` | 原件（PDF / 图片 / docx），只读存档 | 只增不改 |
| `20-md\` | 解析出的正文 `.md` + 每本书的 `图片\` | 脚本生成 |
| `30-index\` | `manifest.csv` / `catalog.md` / `todo.md` | `catalog.ps1` 重建 |
| `40-new\` | 报告、日志、脚本、临时目录 | 只往这里放新建物 |
| `50-wiki\` | LLM Wiki：概念/实体/书页/对比/做法/未决，加 `index.md`、`log.md`、`glossary.md` | 只有 LLM 写；人在 Obsidian 只读 |
| `90-tool\` | 规则（`rules.md`、`AGENTS.wiki.md`）、提示词、脚本 | 改规则时 |

一本书的正文与图：

```
20-md\<书名_作者_版次_年份>\<同名>.md
20-md\<书名_作者_版次_年份>\图片\图2.6 NaI T1 闪烁探测器.jpg
```

`20-md` 入库夹少于 20 个时全部扁平；到 20 个才允许分组，超过 40 个必须分组（见 `rules.md` 第 4 节）。
## 设计文档与 Obsidian

- **设计与实施方案**（P0–P4 施工图、脚本原文、验收判据、成本与规模阈值）：`知识库蓝本.md`，2471 行（含 2026-11-17 并入的使用说明），2026-11-16 由两份调研文档合并。
- **写 wiki 的编辑契约**：`90-tool\AGENTS.wiki.md`（三层写者边界、frontmatter 顺序、页面硬约束）。
- **解析层规则**：`90-tool\rules.md`（v3.0，含 §12–§15）。
- **Obsidian**：本夹直接作 vault 打开。`.obsidian\app.json` 已把 `10-source\`、`20-md\`、`30-index\`、`40-new\`、`90-tool\`、`00-inbox\` 列为排除，星图只显示 `50-wiki` 与根目录文档；改后需重启 Obsidian 才生效。`.obsidian\` 不进版本库（`.gitignore`）。

## 往库里加资料

**一个会话只处理一本书。**

1. 把书丢进 `00-inbox\`：直接放 PDF 最省事（散文件会自动建 `书名_作者_NA_NA` 夹）；想自己指定夹名就建 `书名_作者_版次_年份`，不知道的写 `NA`。
2. 用 `D:\Shervon_KnowledgeBase` 开新会话，贴 `90-tool\prompt-dsh.md` 的内容（免费 agent 用 `90-tool\prompt.md`）。
3. 默认不预览、不等待：`ingest.ps1` 一次跑完 MinerU 解析 → 图名归一 → 图链自检 → 重建索引，账本与缺图都记进 `30-index\todo.md`。
4. 需要补作者/版次/年份时，打开 `todo.md` 照着补对应 md 的 frontmatter；补完重跑 `catalog.ps1` 那一项就消失。

解析后会用版权页核对书名/版次/年份，不符会改名（夹、md、`10-source` 同步）。

入库开销：MinerU 纯文字页约 4 秒/页、图纸页约 26 秒/页；166 页扫描书约 15 分钟，显卡（DirectML/Quadro P6000）会自动用上。

入 DSH 检索索引由我收尾：你说“入索引”才做。

## 查资料

| 场景 | 怎么查 |
|---|---|
| 知道是哪本书 | `30-index\catalog.md`，按书名/类型找 |
| 记得一句话或公式 | 在 `20-md\` 全文搜（Everything / VS Code / Obsidian） |
| 说不清在哪 | 直接问我，要求“书名 + 章节 + 原句/图号” |

图缺失时正文不会留破图占位：`check-links.ps1` 会把指向不存在文件的链接删掉，图注文字保留；缺了哪些记在 `todo.md`。

## 图示约定

图题 `图X.Y 说明`；文件名 `图X.Y 说明.jpg`，子图 `_a/_b`，重号 `_2`；图题里不能出现 `( ) [ ] { } * ? : " < > | / \ # %`（会截断链接），引用号 `[31]` 命名前剥掉。

## 同步到家里

整个 `D:\Shervon_KnowledgeBase` 拷走即可，不需要数据库。别只同步 `20-md`——丢了 `10-source` 就无法重解析。

## 红线

不删原件、不改原件、不联网上传、不装软件、不自创分类。规则没覆盖的写进 `todo.md`，不要自己发明流程。

## 排错

| 现象 | 原因 | 怎么办 |
|---|---|---|
| 提示“禁止运行脚本” | 执行策略 | 用提示词里的完整命令，带 `-ExecutionPolicy Bypass` |
| 中文乱码 / ParserError | `.ps1` 缺 UTF-8 BOM | 存成“UTF-8 带 BOM” |
| PDF 全是 pending | 解析出错 | 看 `30-index\issues.log` 末尾报错；MinerU 在 `C:\Users\shervon\.local\mineru`（4.1.7） |
| md 里“找不到图片” | 图名含 `[]` 或图未导出 | 跑 `check-links.ps1 -Md <md> -Fix` |
| 入库报锁 | `40-new\.ingest.lock` 存在 | 确认没有别的入库会话后删掉它 |
| docx 读不出 | 老 `.doc` 格式 | 另存为 `.docx` |
