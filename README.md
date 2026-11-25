# Shervon 知识库

LLM Wiki 落地库（v3.18，2026-11-23）：原件只读 + 解析全文 + 542 页 Wiki + 双契约 + 15 脚本质检链 + git/GitHub 审计。

> 三分钟速读：目录干什么看下表；加书贴 `90-tool\prompt-dsh.md`；查资料走 Query 四步（`90-tool\AGENTS.wiki.md` §6）；红线在文末；设计全案在 `kb-blueprint.md`。

## 目录一眼看懂

| 目录 | 放什么 | 谁动它 |
|---|---|---|
| `00-inbox\` | 待入库：一本书一个文件夹（散文件也行） | 人投放，入库后清空 |
| `10-source\` | 原件（PDF），只读存档，256.6 MB | 只增不改 |
| `20-md\` | 解析出的正文 `.md` + 1858 张图（119.4 MB） | 脚本生成（`ingest.ps1` → MinerU → `ingest-build.ps1`） |
| `30-wiki\` 机器区 | `manifest.csv` / `catalog.md` / `todo.md` / `issues.log` / `figures-*.md` / `index*.md` / `_lint.md` | 脚本重建（`catalog.ps1`、`wiki-index.ps1`、`wiki-lint.ps1`、`figure-index.py`） |
| `30-wiki\` 人写区 | `pages\` 542 页（概念/实体/总览）、`sources\` 5 页书源、`openq\` 3 页冲突、`howto\` 0 页（项目复盘预留，rules §12.2 五目录之四，comparisons 未单建、对比页暂放 pages）；`glossary.md`、`log.md` | 只有 LLM 写；人在 Obsidian 只读 |
| `40-scratch\` | 一次性脚本、parse 中间产物、备份 | 只往这里放新建物 |
| `90-tool\` | `rules.md` v3.18、`AGENTS.wiki.md` v1.2、`prompt-dsh.md` v3.3、`prompt.md`、`taxonomy.md`、`VERSION`、`scripts\` 15 个 | 改规则时 |

一本书的正文与图：

```
20-md\<书名_作者_版次_年份>\<同名>.md
20-md\<书名_作者_版次_年份>\图片\图2.6 NaI T1 闪烁探测器.jpg
```

`20-md` 入库夹少于 20 个时全部扁平；到 20 个才允许分组，超过 40 个必须分组（`rules.md` 第 4 节）。

## 功能一览（v3.18 实测）

| 功能 | 实现 | 现状 |
|---|---|---|
| 入库 | `ingest.ps1`：MinerU 解析 → 图名归一 → 图链自检 → `ingest-build.ps1` 七行验收 → 重建索引 | 5 本书入库（GBT150 / 化工原理 / 搅拌与混合设备 / 气液搅拌釜γ-CT / 混合原理） |
| Wiki 页 | 一断言簇一页（rules §12.1）；frontmatter 十一字段（rules §13）；正文 ≤300 行 | 542 页；索引 4 分册 550 条 |
| 质检 | `check-links.ps1` 死链、`wiki-lint.ps1` 十项、`precommit-guard.ps1` 提交闸门、`md-anchor.ps1` 页码锚点 | 死链 0；lint 550 页 0 问题 |
| 索引 | `wiki-index.ps1` 自动分册、`catalog.ps1`、`figure-index.py` / `coverage.py` | 4 分册 550 条 |
| 成本闸门 | `budget-watch.ps1`：20 元上限，超限杀 DSH+MinerU | 会话内常驻运行 |
| 版本审计 | git 每书一 commit；GitHub 私有仓库 shervon-yu/Shervon-KnowledgeBase | 6 commits |
| 人机同步 | Obsidian 只读 vault；开场 `git status` 审计 | 3 个未提交改动待处理 |
| DSH 检索 | kb 库向量索引 | ⚠️ 仅 120 页且路径指向旧 `50-wiki\concepts\`，重导入前别当主检索通道 |

## 设计文档

- **设计与实施方案**：`kb-blueprint.md`，2262 行（2026-11-23 复测更新 §2/§3、删除过时 §7、新增 §8.7 四方案复评）。
- **写 wiki 的编辑契约**：`90-tool\AGENTS.wiki.md` v1.2（写者边界、页面契约、Ingest 六步、Query 四步、Lint 十项、禁止）。
- **解析层规则**：`90-tool\rules.md` v3.18（§12 30-wiki 层、§13 页面契约、§14 引用格式、§15 SOP、§16 生成规范）。
- **入库 SOP**：`90-tool\prompt-dsh.md` v3.3（十二步、20 元上限口径）。
- **Obsidian**：本夹直接作 vault 打开；`.obsidian\app.json` 已排除 `10-source\`、`20-md\`、`40-scratch\`、`90-tool\`、`00-inbox\`；`.obsidian\` 不进版本库（`.gitignore`）。

## 往库里加资料

**一个会话只处理一本书。**

1. 把书丢进 `00-inbox\`：直接放 PDF 最省事；想自己指定夹名就建 `书名_作者_版次_年份`，不知道的写 `NA`。
2. 用 `D:\Shervon_KnowledgeBase` 开新会话，贴 `90-tool\prompt-dsh.md` 的内容（免费 agent 用 `90-tool\prompt.md`）。
3. 默认不预览、不等待：`ingest.ps1` 一次跑完 MinerU 解析 → 图名归一 → 图链自检 → 重建索引，账本与缺图记进 `30-wiki\todo.md`。
4. 需要补作者/版次/年份时，打开 `todo.md` 照补 frontmatter，补完重跑 `catalog.ps1`。

解析后按版权页核对书名/版次/年份，不符会改名（夹、md、`10-source` 同步）。

入库开销：MinerU 纯文字页约 4 秒/页、图纸页约 26 秒/页；显卡（DirectML/Quadro P6000）自动用上。成本口径：预算 20 元上限（峰价=谷价×2），`budget-watch.ps1` 强制；实测最大一本（12527 行/561 图）谷价 ¥5.92。

## 查资料（Query 四步，AGENTS.wiki.md §6）

| 步 | 动作 |
|---|---|
| 1 | `grep` `30-wiki\index*.md` 与 `30-wiki\` 全文，取候选页 |
| 2 | 读 ≤10 个候选页；超出说明问题太宽，先收窄 |
| 3 | 回答带《书名》§节号（#L行号）；查不到就说查不到 |
| 4 | 判断是否回填：值得沉淀的答案进 `howto\` / `pages\` 并登记 index（howto 须用户发起） |

| 场景 | 怎么查 |
|---|---|
| 知道是哪本书 | `30-wiki\catalog.md` |
| 记得一句话或公式 | `20-md\` 全文搜（Everything / VS Code / Obsidian） |
| 说不清在哪 | 直接问 Agent，要求「书名 + 章节 + 原句/图号」 |

图缺失时正文不留破图占位：`check-links.ps1` 删坏链、图注文字保留，缺的记 `todo.md`。

## 图示约定

图题 `图X.Y 说明`；文件名 `图X.Y 说明.jpg`，子图 `_a/_b`，重号 `_2`；图题里不能出现 `( ) [ ] { } * ? : " < > | / \ # %`（会截断链接），引用号 `[31]` 命名前剥掉。

## 同步与版本

整个 `D:\Shervon_KnowledgeBase` 拷走即可，不需要数据库。已接 git + GitHub 私有仓库：`git push/pull` 同步；每本书 ingest 一个 commit；改库前先 `git status --short`，未提交改动先吸收或还原。别只同步 `20-md`——丢了 `10-source` 就无法重解析。

## 红线

不删原件、不改原件、不联网上传、不装软件、不自创分类。规则没覆盖的写进 `todo.md`，不要自己发明流程。

## 排错

| 现象 | 原因 | 怎么办 |
|---|---|---|
| 提示「禁止运行脚本」 | 执行策略 | 用提示词里的完整命令，带 `-ExecutionPolicy Bypass` |
| 中文乱码 / ParserError | `.ps1` 缺 UTF-8 BOM | 存成「UTF-8 带 BOM」 |
| PDF 全是 pending | 解析出错 | 看 `30-wiki\issues.log` 末尾报错；MinerU 在 `C:\Users\shervon\.local\mineru`（4.1.7） |
| md 里「找不到图片」 | 图名含 `[]` 或图未导出 | 跑 `check-links.ps1 -Md <md> -Fix` |
| 入库报锁 | `40-scratch\.ingest.lock` 存在 | 确认没有别的入库会话后删掉它 |
| docx 读不出 | 老 `.doc` 格式 | 另存为 `.docx` |
