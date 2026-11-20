# AGENTS.wiki.md —— 本库 wiki 层的编辑契约（schema）

> 版本：v1.2（2026-11-19 增「表格与公式」硬约束：单元格内公式必须 `$...$`、裸 `|` 用 `\vert`、禁 `\begin{array}` 伪造合并单元格）
> 变更记录：v0 草稿 → v1.0 定稿，条款未改动，仅去掉「待定稿」标记；v1.1 目录改名 `concepts\`→`pages\`（书内知识唯一承载目录，原名已名不副实），六目录收为五目录，`entities\` 并入 `pages\`；v1.2 增表格公式约束（MinerU 管道表整列丢定界符，Obsidian 显示成源码，2026-11-19 实测 3 本书 1361 行）；此后任何条款变更须人改本文件并在 git 提交信息写明理由。
> 适用对象：只对 `30-wiki\` 层生效的写入者（LLM）。`90-tool\rules.md` 管解析层（10-source / 20-md / 30-wiki），本文件管 wiki 层；两者不互相覆盖，冲突时以更严的一条为准。

## 0. 写者边界

| 目录 | 谁能写 | 谁不能写 |
|:---|:---|:---|
| `00-inbox\` | 人投放 | 脚本、LLM 不得移入移出 |
| `10-source\` | 只增（人放原件） | 任何脚本与 LLM 不得改、不得删 |
| `20-md\` | 仅 `ingest.ps1` 与 `figures.py`、`check-links.ps1` | LLM 不得写；重解析不得波及 `30-wiki` |
| `30-wiki\`（机器区） | 仅 `catalog.ps1`、`wiki-index.ps1`、`wiki-lint.ps1`、`figure-index.py` 等生成脚本 | LLM 不得改成品，只改生成脚本 |
| `40-scratch\` | 任何人放新建物 | 不作为长期存放地 |
| `30-wiki\`（人写区） | 仅 LLM（本契约执行者） | 人在 Obsidian 中只读；改动靠 git 审计发现 |
| `90-tool\` | 人（改规则） | LLM 不得擅自改规则文件 |

- 新增 `30-wiki` 子目录前必须先改本文件，再在提交信息里写明理由。
- 脚本与 LLM 都不得跨层写入：LLM 写 `20-md` 等同于污染原件视图；脚本写 `30-wiki` 等同于绕过查重。

## 1. 唯一译名（对应 `glossary.md`）

- 每个概念只有一个正名，进 `30-wiki\glossary.md` 的「正名」列。
- 同一概念的其他写法进 `aliases`，检索时等价，但页面标题、`title`、文件名只用正名。
- 查重以 `question` 为准（`rules.md` §12.1）：同一问题只留一页；问题不同但结论相同 → 合并；结论不同（口径/适用条件不同）→ 分页或建 `comparisons\`。
- `ingest` 第 0 步先查两处：`glossary.md` 是否有同义行、`pages\` 是否已有等价页。
- 命中即改旧页，不得新建重复页；确属不同概念（口径不同、适用条件不同）时，建 `comparisons\` 页说明差异，不拆成两个同义 `pages` 页。
- 译名分歧（两个中文写法都通行）不擅自二选一：正名取书中出现频率高者，另一写法进 `aliases` 并在 `openq\` 记一条。

## 2. 断言必须有来源

- 任何事实断言必须落在 `sources` 字段的 `[书名, 节号, 行号]` 三元组上，格式见 `rules.md` §14。
- 节号用书中真实章节号（`§1.2.1`），行号用 `20-md` 中的绝对行号，写成 `#L123`。
- 无来源的断言不得进入 wiki 页；只能进 `openq\`，并在页内写明「缺出处，待补」。
- 数值、系数、关联式、材料牌号、工况范围——一律视为事实断言，同样需要来源。
- 由多页来源综合得出的判断，`sources` 必须列全，不得只挂最像的那一本。

## 3. 页面硬约束

- 单页 ≤300 行；超了拆页，原页留一行「→ 已拆至 `[[新页]]`」。例外：`index.md` 与 `index-<领域>.md` 不设行数上限。
- 每页必须被 ≥2 处其他页链接（入链 ≥2），否则合并进上位页或删除。
- 图引用必须附 ≥1 句文字转述；转述不出则走视觉模型流程，并在 `log.md` 记一条。
- **表格与公式（v1.2）**：单元格内公式一律行内 `$...$`；单元格内不得有裸 `|`（绝对值/条件概率用 `\vert`，成对定界用 `\lvert x\rvert`，`\left|`/`\right|` 写成 `\left\vert`/`\right\vert`）；不得用 `\begin{array}` 伪造合并单元格，合并语义改 HTML `rowspan`/`colspan` 或拆行拆列；照此重建不了的表，在 `openq\` 记一条并不写这张表。
- frontmatter 字段顺序固定（`rules.md` §13）：`type`、`title`、`question`、`aliases`、`domain`、`status`、`confidence`、`sources`、`related`、`supersedes`、`updated`。
- `question` 必填：一个疑问句（以 `？`/`?` 结尾），全库唯一；空、非疑问句、重复都判错。
- `type` 只能是：`concept`、`entity`、`source`、`comparison`、`howto`、`openq`；除 `concept`、`entity` 同放 `pages\` 外，其余必须与所在目录一致。
- `status` 只能是：`draft`、`stable`、`superseded`、`open`。
- `confidence` 只能是：`high`、`medium`、`low`；`low` 必须在正文首段说明为何低。
- 文件名 = 正名（不含 `\ / : * ? " < > |`），一页一文件。

页面头部模板（照抄改值，不增删字段）：

```yaml
---
type: concept
title: 搅拌功率-功率准数
question: 搅拌功率怎么计算？
aliases: [功率准数, Np]
domain: 搅拌与混合设备
status: draft
confidence: high
sources:
  - book: 搅拌与混合设备设计选用手册
    section: §1.4
    lines: "#L960-#L1064"
related: ["[[搅拌功率-永田进治关联式]]"]
supersedes: []
updated: 2026-11-16
---
```

正文结构（`concept` 页）：

```markdown
## 定义
一句话 + 出处。

## 判据 / 计算
符号式与文字式成对写（见 `~/.agents/AGENTS.md` 第 1 节）。

## 适用范围与边界
什么条件下成立；什么条件下不成立。

## 相关
- [[另一页]] —— 为什么相关
```

- 无 `sources` 的页只能落在 `openq\`，不得落在 `pages\`。

正文结构（`howto` 页 = 项目复盘，见 `rules.md` §12.2）：

```markdown
## 这次要解决的问题
一句话：当时要交付什么、判定成功的标准。

## 约束
设备/工艺/标准/成本/工期等硬约束，逐条列。

## 用到了库里哪些知识
- [[页名]] —— 用它决定了什么（一句话）
（≥2 条；查到库里没有就写「库里没有」，并在 `openq\` 记一条）

## 怎么做的
关键取舍与计算口径；公式照「符号式/文字式」成对写；标 §节号与 #L。

## 结论与验证
最终选择、验收或回算结果、是否出现返工。

## 暴露的知识缺口
- [[openq 页]] —— 缺什么、下次补哪本书的哪一节
```

- `howto` 页只记「这次怎么用知识解决问题」，不抄书的操作步骤；书里的内容由 `pages\` 承担。
- `howto` 页由用户发起（「这次怎么做的记一下」），LLM 不擅自建。

## 4. 冲突与换代

- 新信息推翻旧断言：旧页 `status: superseded`，`supersedes` 指向新页；旧断言保留，不删行。
- 两源并存矛盾且无法判定谁对：开 `openq\` 页，不擅自二选一，不写成「一般认为」糊过去。
- 矛盾属于口径/参数/适用条件差异时，改开 `comparisons\` 页，四选勾写清差异性质。
- 换代链最长三级；超过三级说明概念本身需要重写，开 `openq\` 讨论。

## 5. Ingest 六步（一次到位，v3.2）

0. 查重：查 `glossary.md` + `pages\` + 全库 `question`，命中则改为改旧页。
1. 解析：`ingest.ps1` 跑 MinerU，产物落 `40-scratch\parse\<入库夹名>\`（`middle_json` 是唯一可信来源）。
2. 生成 + 验收：一条命令
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File "90-tool\scripts\ingest-build.ps1" -Book "<入库夹名>"
   ```
   内部 `md-build write → fig-names apply → md-build prune → check-links → 验收表`。**必须看到「验收通过」**，不许手改行号糊过去。
3. 写 `sources\` 页：元信息表 → 章节地图（带 `#L`）→ 能回答什么/不能回答什么 → 图清单。
4. 建/改概念页：每页带 `sources` 三元组，断言逐条挂出处；每张被引用的图至少一句文字转述。
5. 回改受影响页 + `index.md` + `log.md`（记 token、成本、`touch=N`）。
6. `wiki-lint.ps1` 必过 0 条 + `git commit`。

**验收门（缺一不算完）**：锚点数 = PDF 页数；`$$` 公式数 > 0；图链数 = 图片文件数；未定名图 `图_第NN页_` = 0；frontmatter 存在；`check-links` unresolved = 0。

**重解析代价**：重建会换掉全部行号，必须 `git checkout -- '30-wiki' kb-blueprint.md` → `refs-remap.py dry → apply` 重算 `#L`；同一批文件重复 apply 会二次映射，重试前必须先 checkout。

- 一次 `ingest` 只处理一本书；跨书内容放 `comparisons\`，不塞进单本书页。

## 6. Query 四步

1. `grep` `index.md` 与 `30-wiki\` 全文，取候选页。
2. 读 ≤10 个候选页；超出说明问题太宽，先收窄。
3. 回答带 `§节号` 与 `#L行号`；查不到就说查不到，不用常识补。
4. 判断是否回填：值得沉淀的答案 `crystallize` 成 `howto\` 或 `pages\` 页，并登记 `index.md`。

## 7. Lint 八项（`wiki-lint.ps1` 检查，`_lint.md` 出报告）

| 项 | 判据 |
|:---|:---|
| 死链 | `[[...]]` 与 `](...)` 指向不存在文件 |
| 孤儿页 | 入链 <2 |
| 无来源 | `sources` 为空或与正文断言不匹配 |
| 超长页 | >300 行（不含 index.md、index-*.md） |
| 同义重复 | 两页 `aliases` 交叉命中 |
| 过期断言 | `status: superseded` 仍被其他页当现行引用 |
| index 漂移 | 页存在但 `index.md` 无行，或反之 |
| 图无转述 | 图链接后无文字说明 |
| 别名遮蔽页名 | 某页 `aliases` 命中另一页的文件名 |
| question 不合规 | `question` 空、非疑问句、或全库重复 |

- `_lint.md` 为生成物，不进版本库（`.gitignore` 已排除）。

## 8. 禁止

- 禁止把 wiki 内容写进 `20-md\` 或 `10-source\`。
- 禁止编造来源、编造页码、编造参数、编造书名与章节号。
- 禁止跳过查重直接建页。
- 禁止改 `30-wiki\` 的生成物（改生成脚本，不改成品）。
- 禁止在 `30-wiki\` 内建子目录之外的新层级，除非先改本文件。
- 禁止一次提交里混入两本书的 ingest。
