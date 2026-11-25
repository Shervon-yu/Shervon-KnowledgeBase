# 90-tool\schema.md —— 页面契约（机器可读）

> 版本：v1.3（2026-11-25 P0 落地）｜ 由 `wiki-lint.ps1` 第 0 项读取校验：加字段只改本文件，不改代码
> 权威：`rules.md` §13 与 `AGENTS.wiki.md` §3；三处冲突时以更严的一条为准

## 1. 字段表（行序 = 字段序，不得调序）

必填列取值：`all` 全部页面必填 ｜ `except:openq` 除 `openq` 外必填 ｜ `notes` 仅 `notes\` 必填 ｜ `optional` 选填。
枚举格用 `/` 分隔，不写竖线（竖线会打断表格，本库行内公式同样禁裸竖线）。

| 序 | 字段 | 类型 | 必填 | 枚举或约束 | 说明 |
|:--|:--|:--|:--|:--|:--|
| 1 | type | enum | all | concept/entity/source/comparison/howto/note/openq | 必须与所在目录一致，映射见 §2 |
| 2 | title | text | all | 非空；= 文件名 = 正名 | 正名取自 glossary.md |
| 3 | question | text | all | 以 ？ 或 ? 结尾；全库唯一 | 一个疑问句 |
| 4 | description | text | notes | ≤200 字；不复制标题 | 写「这页回答什么问题、给什么数」；pages 区 P0 起统计覆盖率、P1 补满 |
| 5 | aliases | list | optional | 行内 [a, b] 或 YAML 列表 | 等价写法，检索用 |
| 6 | domain | text | all | 领域名须在 glossary.md 领域表登记 | 领域路由第一跳 |
| 7 | status | enum | all | draft/stable/superseded/open | openq 页固定 open |
| 8 | confidence | enum | except:openq | high/medium/low | low 须正文首段说明为何低 |
| 9 | opened | date | openq | yyyy-mm-dd | openq 页特有，替代 updated |
| 10 | sources | block | all | book/section/lines 三行块 | openq 也须带来源 |
| 11 | related | list | optional | [[页名]] 列表 | 相关页 |
| 12 | supersedes | list | optional | [[页名]]；换代链 ≤3 级 | 旧页保留并标 superseded |
| 13 | updated | date | except:openq | yyyy-mm-dd | notes 超 90 天 → lint 第 11 项告警 |

## 2. type 与目录映射

| type | 目录 | 区 | 说明 |
|:--|:--|:--|:--|
| concept | pages | 资料区 | 概念、机理、公式、参数、适用边界 |
| entity | pages | 资料区 | 设备结构、零件、型式 |
| source | sources | — | 每本书 1 页章节地图 |
| comparison | comparisons | — | 跨书、跨标准同量口径差异 |
| howto | notes | 经验区 | 项目复盘 |
| note | notes | 经验区 | 会话结晶（digest 四字段） |
| openq | openq | — | 冲突与缺口登记 |

## 3. 两区规格

| | pages（资料区） | notes（经验区） |
|:--|:--|:--|
| 知识来源 | 书、规范、论文、权威资料，经 ingest 编译 | 会话问答与项目实操的结论 |
| 有效性 | 永久，无年龄告警 | `updated` 硬必填，超 90 天告警复检 |
| supersedes | 只指向同区新页 | 可指向同区页，也可指向 pages 页（经验被资料转正） |
| confidence 初始 | 按来源权威给 high/medium | 默认 medium；会话推导不超过 medium |
| lint 附加 | — | 第 11 项年龄告警 |

## 4. 非字段硬约束

- 单页 ≤300 行；`index.md`、`index-<领域>.md` 不设上限。
- 每页入链 ≥2。
- 文件名 = `title`；禁用字符 `\ / : * ? " < >` 与竖线。
- 表格单元格内公式用 `$...$`；单元格内不得出现裸竖线，绝对值/条件概率用 `\vert`。
- 新建 `.ps1` 必须带 UTF-8 BOM，含中文的脚本用 `write` 工具落盘。

## 5. lint 项号与依据

| 项 | 判据 | 依据 |
|:--|:--|:--|
| 0 | frontmatter 字段序、必填、枚举与本文件 §1 一致 | 本文件 |
| 1–10 | 死链、孤儿页、无来源、超长页、同义重复、过期断言、index 漂移、图无转述、别名遮蔽、question 不合规 | rules.md §15 |
| 11 | `notes\` 页 `updated` 超 90 天，只告警不计错 | 本文件 §3 |
