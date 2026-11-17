# 知识库蓝本（KB blueprint）

> **这份文件是本知识库的蓝本**：调研、方案、施工图、使用说明都在这里，没有它就没有这个库。
> - 第一部分 **方案论证**（原 `LLM-Wiki_RAG_GraphRAG_全解与本库改造方案.md`，1420 行）：为何选 LLM Wiki 而非 RAG/GraphRAG，规模阈值与成本。
> - 第二部分 **落地执行**（原 `LLM-Wiki_落地执行方案.md`，584 行）：P0–P4 施工图、脚本原文、验收判据。
> - 第三部分 **使用说明**（2026-11-17 并入，原 `使用说明.md`）：怎么问、怎么加书、怎么迁移、怎么演示、坑表。
> 顺序：先讲为什么，再讲怎么做，最后讲怎么用。改动本文档即改动施工依据，改前先看 git log。

---
# 第一部分 方案论证：LLM Wiki / RAG / GraphRAG 全解 + 本库改造方案（第三版）

> 版本：**v3.0（2026-11-16）** ｜ 对象：`D:\Shervon_KnowledgeBase`
> 本版预设口径：**按你有 300 本书 + 零散资料设计**（不是按现在 3 本设计；3 本只是起步试点）。
> 标注约定：**【原文】**=一手文献原话 ｜**【文献】**=有出处的研究/项目/价格页 ｜**【实测】**=本机命令结果 ｜**【判断】**=我的推理或经验值 ｜**【估计】**=量级估算，非精确值。
> 价格一律标注来源与日期，**下单前以官网当日价为准**。

---

## 0. 先给结论（五分钟版）

| 问题             | 结论                                                                                                                                                                 |
| :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM Wiki 是什么   | 不是软件，是一个**模式**：LLM 在入库时把源文件"编译"成互相链接的 markdown 页面网，而不是等提问时再检索。**知识在入库时被综合一次，之后只做维护。**                                                                              |
| 和 RAG 的根本差别    | RAG 每次提问都从零拼答案（无积累）；LLM Wiki 把答案的原料提前建好（有积累）。差别不在技术栈，在**知识生成的时间点**。                                                                                                |
| 你（300 本书口径）缺什么 | 不缺解析（MinerU 管线已工业级），缺**综合层**（把每本书编译成 ~25 页概念页的网）+ **编辑契约**（AGENTS.wiki.md）+ **版本控制**（git）。                                                                         |
| 改造路径           | 不加解析、不换工具。**加 `50-wiki\` + `git init`（本地 + GitHub 私有仓库）+ 一份 schema，然后一本书一本书编译。**                                                                                   |
| 什么时候上向量检索      | **看 §6.4 量化分界线**：md 语料 ≤5 MB 别上；5~50 MB 用全文检索；50 MB 以上（约 50 本）才上混合检索 qmd。300 本书（~240 MB）落在"混合检索"档，仍轮不到 GraphRAG。                                                   |
| 图片喂视觉模型的成本     | 图片便宜到可以忽略：deepseek-flash 下按需喂 30 张图，一本增量 ≈ **¥0.07**；全量 400 张 ≈ ¥0.86/本。**图片不是成本问题，是流程问题。**                                                                        |
| **单本入库到底多少钱**  | 一本《化工原理》编成 wiki：**只文本 ≈ ¥0.44；按需 30 图 ≈ ¥0.51；全量 400 图 ≈ ¥1.31**（deepseek-flash、off-peak、官方价 2026-11-16；peak 翻倍）。详见 §9.2。                                          |
| 最重要的一句话        | 你已经有 `catalog`（≈index）、`issues.log`（≈log）、`todo.md`（≈lint 报告）——三操作的骨架早就有了，只是它们服务的是"脚本"，不是"知识"。**这次要做的不是新发明，是补上"编辑"和"版本"两个洞，再借鉴 9 个外部方案（8 仓库 + 1 内置功能）的 idea 做融合。** |

#### 0.1 本版（v3.0）相对 v2.0 改了什么

| # | 变更 | 章节 |
|:--|:---|:---|
| 1 | **第 8 章整章重写**：九个方案逐个读一手 README / gist 原文 / 论文摘要后重写，改为"一手事实 / 借什么 / 不借什么"三列 | 第 8 章 |
| 2 | 新增 **§8.0 自查：v2 里被一手文档推翻的 9 处错误**（你让我自己找的"漏洞"） | §8.0 |
| 3 | 新增 **§8.2 照搬现成方案的三条路线试算**：为什么"直接装 geronimo 引擎 / 直接上 qmd"不如自建融合 | §8.2 |
| 4 | **§9.2 全部改口径**：改用 DeepSeek 官方 **deepseek-flash**（带 Vision、1M 上下文），只算**单本入库价**，不再扯九万张图 | §9.2、§3.9、附录 F |
| 5 | 价格表补 **DeepSeek 官方价**（off-peak 输入 $0.15/M、输出 $0.6/M，peak 翻倍）；旧"2/8 元历史锚"降级为对照 | §3.9.1 |
| 6 | 事实修正：geronimo 是 **24 个 MCP 工具**（原写 19）、llm-wiki-skills 是 **17 个 skills**（原写 8）、qmd 的 **context 树**、dataview 的 **DQL/DataviewJS** | §8.0、§3.2、附录 E |
| 7 | A-MEM 加限定：它是 **agent 对话/任务记忆系统**，不是文件型知识库 | §1.10、§8.1 |
| 8 | 附录 E 补 agent-skills、A-Mem 代码库；附录 F 换算与示例全换 flash 口径 | 附录 E、F |

##### v2.0 相对 v1.0 的 10 条（留档）

| # | 变更 | 章节 |
|:--|:---|:---|
| 1 | 预设口径从"3 本书"改为"300 本书 + 零散资料"，所有规模判断重算 | 全文，尤其 §2.6、§6 |
| 2 | 新增 **LLM Wiki v2 全解**（作者、时间、四大提升、哪些未验证） | §1.9 |
| 3 | 新增**量化分界线**：多少 MB/多少字以下用 LLM Wiki、以上用 RAG，四档表格 + 判据 | §6.4、§6.5 |
| 4 | 新增**完整成本账**：视觉模型峰/谷价、一本书入库总价、单次提问 token | §3.9、§9.2、附录 F |
| 5 | 新增**融合方案**专章（10 个项目核心 idea 拆解 + 取舍 + 融合架构） | 第 8 章 |
| 6 | 新增 **Q&A 专章**：你提的全部问题逐条回答 | 第 9 章 |
| 7 | 术语表重写为**小白版全表**（全称 + 中文 + 一句话 + 在哪出现） | §1.12、附录 A |
| 8 | 死链成因实测修正：不是图丢了，是 **`%20` URL 编码未解码** | §2.3 问题 1 |
| 9 | 新增 **git + GitHub 同步方案**、**Obsidian 星图 + 人机同步方案** | §3.11、§3.12 |
| 10 | 新增 **MinerU 强制 OCR 的官方答案**（`--method ocr`）与页码锚点方案 | §9.7、§9.8 |

#### 0.2 你的问题 → 答案索引

| 你的问题 | 答案在哪 |
|:---|:---|
| 向量检索分界线（多少字/MB 为界） | §6.4、§9.1 |
| 单本入库多少钱（deepseek-flash）、每张图多少钱、单次提问 token | §3.9、§9.2、附录 F |
| LLM Wiki v2 是谁、什么时候、提升什么 | §1.9、§9.3 |
| 专业术语全表（gist/git/ingest/lint/MCP/BM25…全称+含义） | §1.12、附录 A |
| "无 lint 就腐化"是什么意思 | §1.5、§1.12、§9.4 |
| 预设应为 300 本书 | 已全文改口径，见 §0、§2.6、§9.5 |
| 融合方案（集百家所长、比原方案更高级） | 第 8 章、§9.6 |
| 你让我自己找的"漏洞"（v2 里被一手文档推翻的 9 处） | §8.0 |
| MinerU 能不能强制全程 OCR、死链怎么解决 | §9.7 |
| 分页标记能不能在解析阶段加 | §9.8 |
| git 本地 + GitHub 同步 | §3.11、§9.9 |
| LLM Wiki 建好是否顺带解决检索不均 | §9.10 |
| 目录/文件名怎么命名（Karpathy 还是 GitHub 项目） | §3.2、§9.11 |
| 50- 前缀为什么、能不能用 a/b/c | §3.1、§9.12 |
| Obsidian 星图、人机同步、改了要报告 | §3.12、§9.13 |
| 先看融合方案再决定动不动库 | 第 8 章 + §9.14（**本版没有动你的库，只改了这份文档**） |

---

## 1. LLM Wiki

### 1.1 出处：一份 gist，不是一个项目

**【原文】** Karpathy 于 2026-04 发布的 [`llm-wiki.md`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)，自述定位：

> "This is an idea file, it is designed to be copy pasted to your own LLM Agent (e.g. OpenAI Codex, Claude Code, OpenCode / Pi, or etc.). Its goal is to communicate the high level idea, but your agent will build out the specifics in collaboration with you."

翻译：**它不是库、不是应用、不是框架，是一份"想法文件"**，让你整段粘进 agent，让 agent 按你的领域现场长出具体形态。所以网上所有 "llm-wiki" 仓库都只是**某个人对这份 gist 的一种落地**，没有权威实现——这恰恰是你能"集百家之长"的前提：**没有正统，只有取舍。**

### 1.2 它到底在反对什么

**【原文】** 开篇就点名：

> "Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up."

翻译：普通 RAG 每次提问都在**从零重建**；一个需要综合五份文档的问题，每次都要重新找、重新拼。**没有累积。**

**【原文】** 反方案：

> "the LLM **incrementally builds and maintains a persistent wiki** — a structured, interlinked collection of markdown files that sits between you and the raw sources. When you add a new source, the LLM doesn't just index it for later retrieval. It reads it, extracts the key information, and integrates it into the existing wiki — updating entity pages, revising topic summaries, noting where new data contradicts old claims..."

**注意动词**：不是 `index`（建索引），是 `integrate`（并入）。这是全篇最重要的一处设计意图。

### 1.3 为什么它成立：维护成本才是瓶颈

**【原文】** 这是全文最狠的一句：

> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. Updating cross-references, keeping summaries current, noting when new data contradicts old claims, maintaining consistency across dozens of pages. Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass."

**【判断】** 这句话解释了为什么个人 wiki 几乎都死了：不是人不会整理，是**整理的成本随页数超线性增长**（n 页要维护 ~n² 条潜在交叉引用）。LLM 把这个成本压到接近零。

**按 300 本书算这笔账【估计】**：300 本 ≈ 7500 个概念页，潜在交叉引用 ~5000 万条——靠人维护是天文数字，靠脚本只能维护"文件级"关系，**只有 LLM 能维护"知识级"关系**。所以对你而言，LLM Wiki 不是"可选风格"，是"书一多之后唯一能维护得住的知识形态"。

**【原文】** 思想源头：Vannevar Bush 1945 年的 Memex，"a personal, curated knowledge store with associative trails between documents"——Bush 没解决的是"谁来做维护"。LLM 解决了。

### 1.4 三层架构（这是唯一必须照抄的部分）

**【原文】**

| 层 | 内容 | 谁写 | 可变性 |
|:---|:---|:---|:---|
| **Raw sources** | 原始文档：文章、论文、图片、数据文件 | 人（采集/剪辑） | **不可变**，LLM 只读不改。"This is your source of truth." |
| **The wiki** | LLM 生成的 markdown：摘要、实体页、概念页、对比、总览、综合 | **LLM 独占** | 持续重写。"You read it; the LLM writes it." |
| **The schema** | 一份文档（`CLAUDE.md` / `AGENTS.md`），规定结构、约定、工作流 | 人 + LLM 共同演化 | 慢变量，改一次要重跑 lint |

**【原文】** 关于 schema 的一句话定义：

> "This is the key configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot."

**没有第三层，前两层必然腐化。** 这是绝大多数模仿者漏掉的地方，也是本方案 §3.4 的重点。

### 1.5 三个操作（Ingest / Query / Lint）

#### Ingest（入库编译）

**【原文】** 流程：

> "The LLM reads the source, discusses key takeaways with you, writes a summary page in the wiki, updates the index, updates relevant entity and concept pages across the wiki, and appends an entry to the log. A single source might touch 10-15 wiki pages."

**"a single source might touch 10-15 wiki pages"** —— 这是 LLM Wiki 与 RAG 最大的工程差异：RAG 的入库是 **append**（一个 chunk 进向量库，不影响别的 chunk）；LLM Wiki 的入库是 **write fan-out**（一次写 10~15 个文件的散射写）。**这条决定了你的脚本不能是"搬运"，必须是"编辑"。**

#### Query（提问）

**【原文】** 提出问题的关键洞察：

> "**good answers can be filed back into the wiki as new pages.** A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history. This way your explorations compound in the knowledge base just like ingested sources do."

**回填（file back）是 LLM Wiki 独有的机制**：RAG 的问答产物永远死在聊天记录里；LLM Wiki 的问答产物会变成新的 wiki 页。**你的库现在所有问答都死在会话里了。** 这条在 v2 里被发扬成 `crystallize`（§1.9）。

#### Lint（体检）

**【原文】** 检查项：`contradictions between pages` / `stale claims that newer sources have superseded` / `orphan pages with no inbound links` / `important concepts mentioned but lacking their own page` / `missing cross-references` / `data gaps that could be filled with a web search`。

**【判断】** Lint 不是可选项，它是**唯一对抗 wiki 腐化的机制**。没有 Lint 的 LLM Wiki 在 20 次 ingest 后一定退化成"另一堆没人看的笔记"。

> 你问的"**无 lint 就腐化**"就是这个意思：wiki 是活体，每次 ingest 都在改 10~15 个文件；没有定期体检（查死链、孤儿页、过期断言、矛盾），错误会**复利式**堆积——错一个链接，后面 10 次编辑都会绕开它，最后整个网没人敢信。**Lint 就是知识的"体检报告"，todo.md 是你文件层的体检，wiki-lint 是知识层的体检。**

### 1.6 两个特殊文件

**【原文】**

**`index.md`** —— 内容导向，是 wiki 的**目录**：每页一行，链接 + 一句话摘要 + 可选元数据（日期/来源数），按类别组织（entities / concepts / sources...）。每次 ingest 更新。**查问题时先读 index，定位候选页，再钻进去。**

> "This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure."

**`log.md`** —— 时间导向，**append-only**，记录 ingest / query / lint。格式建议：

```
## [2026-04-02] ingest | Article Title
```

于是 `grep "^## \[" log.md | tail -5` 就能拿到最近 5 条。【判断】固定前缀这一条看似琐碎，实则是让 log 同时服务人和脚本的关键——**正则友好的日志才是可维护的日志**。

### 1.7 规模与检索的演进路径

**【原文】** 阶段划分：

| wiki 规模 | 检索手段 | 依据 |
|:---|:---|:---|
| ≤ ~100 sources，数百页 | `index.md` 人工/LLM 遍历 | 原文明确说"surprisingly good" |
| 更大 | 本地混合检索：BM25 + 向量 + LLM 重排 | 原文推荐 [`tobi/qmd`](https://github.com/tobi/qmd)，同时提供 CLI 与 MCP server |

**【判断】** 这个路径的隐含前提：**wiki 页面的摘要质量决定了 index 检索的上限**。如果每页摘要写得含糊，index 就退化成一个文件名列表，那就该上向量检索了。反之，摘要写得好，向量库能推后很久。

→ 你问的"分界线"正解就在这里，§6.4 给出量化版；§1.12 解释 BM25/向量/重排是什么。

### 1.8 原文的实用技巧（可直接抄）

**【原文】**

| 技巧 | 具体做法 | 对你的用处 |
|:---|:---|:---|
| Obsidian Web Clipper | 浏览器扩展，网页转 markdown 进 raw | 收网页资料用 |
| 图片本地化 | 附件目录设为固定路径 + 绑定 "Download attachments for current file" 热键 | **你已经做到了**（`20-md/.../图片/`） |
| 图 graph view | 看谁是枢纽页、谁是孤儿页 | Lint 的可视化入口（→ §3.12 Obsidian 星图） |
| Marp | markdown 直接出幻灯片 | 汇报/培训 |
| Dataview | 对 frontmatter 做查询，动态生成表格 | **你最适合这个**：`manifest.csv` 的字段全在 frontmatter 里 |
| git | "The wiki is just a git repo of markdown files" | **你现在没有，这是硬缺口** |

**【原文】** 一个诚实的坑，值得记住：

> "Note that LLMs can't natively read markdown with inline images in one pass — the workaround is to have the LLM read the text first, then view some or all of the referenced images separately"

**【判断】** 这对你尤其重要：你的书有大量工程图，**图里的信息（结构剖面、曲线、参数表）LLM 一次读不进来**。所以 wiki 页里凡是引用图的地方，要么把图的关键信息**用文字转述**（"图2.1 为垫片-法兰-螺栓连接，标注 1—法兰 2—垫片 3—螺栓"），要么单独把图喂给视觉模型（成本见 §3.9）。**别指望"链接到图"就等于"知识已入库"。**

### 1.9 LLM Wiki v2 全解（你问的"第二个版本"）

**是什么**：【文献】GitHub 用户 `rohitg00`（Rohit Ghumare）的 gist *"LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory"*：[gist 链接](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)。

**时间**：【文献】gist 页面 2026-10-09 访问记录显示 7 个 revision、最近活跃 2026-10-08。**提出时间约 2026-10**（Karpathy 原版 2026-04 之后约半年），仍在变动中。

**它在 LLM Wiki 基础上加了什么**（四大块，按原文归纳）：

| # | 提升 | 具体内容 |
|:--|:---|:---|
| 1 | **给知识加生命周期** | 置信度评分（每条事实挂来源数/最近核验时间/矛盾情况）；supersession（新信息取代旧结论时显式链接、旧版保留标过时）；遗忘/保留策略（按知识类型与访问调整检索优先级，含遗忘曲线思路）；四层记忆整合（working→episodic→semantic→procedural） |
| 2 | **从页面链接升级为类型化知识图谱** | 实体带类型（people/projects/libraries/concepts），关系带语义（`uses`/`depends on`/`contradicts`/`supersedes`）；查询时沿关系遍历；**图谱是页面导航的补充，不取代可读的 wiki** |
| 3 | **混合检索与自动化维护** | BM25 + 向量 + 图遍历三路检索，用 **RRF** 融合；事件钩子（新源进入/会话开始/查询/写入/定时维护时触发抽取与 lint）；质量自纠（查孤儿与断链、提矛盾解决候选）；**crystallization**（把完成的研究/调试/分析固化成可溯源的一等 wiki 资料） |
| 4 | **多代理协作、隐私与输出形态** | 多代理同步、私有/共享知识范围、入库敏感信息过滤、变更审计、可逆批量操作；呈现可按任务生成对比表/时间线/依赖图，不限于 markdown |

**要分清的两件事【判断】**：
- v2 是**扩展**不是替代：它自己写明了 "implementation spectrum"——先有 raw/wiki/schema + 三操作，再**按规模逐项**加生命周期、图、自动化、协作。**它不是让你第一天全上。**
- 其中置信度浮点分数、遗忘曲线、last-write-wins 同步、自动矛盾修复等，v2 原文自己也标注为"待评估选项"——**没有统一基准证明有效**。社区（含我 v1 版）常把"情节/语义记忆分层""睡眠式巩固""置信度衰减"记到 Karpathy 头上，**原文没有**，是 v2 与记忆研究圈的补充。你可以用，但别当官方规范实现。

**v2 对你最有用的三条**（我会融入融合方案第 8 章）：
1. `confidence` + `superseded` 字段 → 工程参数"新旧口径并存、显式换代"直接可用；
2. **事件钩子**（ingest 前必查重、写后必 lint）→ 把"靠自觉"变成"靠流程"；
3. `crystallize` → 你的**计算书、选型过程**就是最该结晶的东西（§8.3）。

### 1.10 社区延伸与相邻研究（要分清谁说的）

**【文献】** 这条线常被混为一谈，明确切分：

| 名称 | 是什么 | 与原始 gist 的关系 |
|:---|:---|:---|
| **LLM Wiki**（Karpathy, 2026-04） | 三层 + 三操作 + index/log | 原始 |
| **LLM Wiki v2**（rohitg00, ~2026-10） | 生命周期 + 类型化图谱 + 混合检索 + 协作治理（§1.9） | 扩展，不是原文 |
| **A-MEM**（[arXiv 2502.12110](https://arxiv.org/abs/2502.12110), NeurIPS 2025） | Zettelkasten 式原子笔记 + 结构化属性（contextual description/keywords/tags）+ 新记忆触发旧记忆"演化" | 最接近的**设计**对应物；原文未引用。**注意【文献，2026-11-16 实读摘要修正】**：它是 **agent 对话/任务历史记忆系统**（代码 A-mem / A-mem-sys），**不是文件型知识库**——可借的是"原子化 + 属性 + 演化"三条设计，不是它的检索算法 |
| **MemGPT / Letta** | 把上下文窗口当虚拟内存，agent 自己决定换入换出 | 相邻，但自持 agent loop，锁定重 |
| **Mem0** | 从对话里被动抽取记忆 | 相邻，轻量，但记忆来自对话而非源文件 |
| **ReadAgent**（DeepMind, 2024） | 长文压缩成摘要树 + 回指指针 | 同源直觉（compile, don't re-retrieve） |
| **Rowboat / 类型化图谱派** | 主张类型化实体图而非摘要页 wiki | 与 v2 第 2 块同路，是 wiki 与 GraphRAG 的交界 |

### 1.11 已知的坑（原文没说的部分）

**【判断】** 以下是我认为落地时一定会撞上的，按严重度排：

| # | 坑 | 表现 | 对策 |
|:--|:---|:---|:---|
| 1 | **无 git 就无回滚** | LLM 一次改写 15 个文件，改错了整锅糊 | `git init` + 每次 ingest 一个 commit。**这是硬前提，不是优化项** |
| 2 | **合并幻觉** | 把"机械密封端面比压 0.3~0.6 MPa"和"填料密封压盖比压"混成一页 | 页面必须带 `sources` 字段逐条指向书+章节；无来源断言禁止写入 |
| 3 | **重复建页** | 同一概念三次 ingest 建了三个名字 | `glossary.md` 唯一译名表 + ingest 前先查重（v2 的事件钩子化） |
| 4 | **页面膨胀成第二本流水账** | 一页写到 800 行，等于把书又抄一遍 | 单页硬上限（建议 150 行），超了就拆 |
| 5 | **链接腐烂** | 改名后 `[[旧名]]` 全断 | 每次 ingest 跑死链检查；改名走"先建别名再删"两步 |
| 6 | **无 lint 就腐化** | 20 次 ingest 后没人知道哪页过期 | 固定周期 lint，产出写进 `todo` |
| 7 | **成本不可见** | 一本书 ingest 烧掉多少 token 心里没数 | 每次 ingest 在 log 里记 token/耗时，见 §3.9 |

### 1.12 专业术语全表（小白版，先扫一遍再读后面）

**用法**：全表在附录 A。这里先给文档里最高频的 12 个，读完这节你就能看懂后面所有章节。

| 术语               | 全称                            | 中文        | 一句话（小白口径）                                                     |
| :--------------- | :---------------------------- | :-------- | :------------------------------------------------------------ |
| **gist**         | GitHub Gist                   | —         | GitHub 的"单文件分享页"，贴代码/想法用的；Karpathy 和 v2 都发在这。**不是仓库，是个网页文件。** |
| **git / repo**   | — / repository                | 仓库        | 版本控制工具/仓库：记录每次改动，能回滚到任意历史版本。                                  |
| **token**        | —                             | 词元        | LLM 计费与计量的最小单位；中文约 1 字 ≈ 0.67 token（即 1.5 字 = 1 token）。       |
| **MCP**          | Model Context Protocol        | 模型上下文协议   | 给 agent 插"工具"的标准接口；Obsidian、qmd、llm-wiki 都靠它接进你的 agent。       |
| **ingest**       | —                             | 入库编译      | 把一份新源读进 wiki：写摘要页 + 更新 10~15 个相关页 + 更新 index/log。             |
| **lint**         | —                             | 体检        | 定期自动检查 wiki 健康：死链/孤儿页/过期断言/矛盾。                                |
| **frontmatter**  | —                             | 文件头元数据    | md 文件开头 `---` 包起来的 YAML 字段块（type/title/sources…），机器可解析。       |
| **OCR**          | Optical Character Recognition | 光学字符识别    | 把图片里的文字"认"出来变成文本；扫描版 PDF 全靠它。                                 |
| **raw / schema** | —                             | 原件层 / 契约层 | raw=不可改的原件；schema=教 LLM 怎么维护 wiki 的规则文件（AGENTS.md）。           |
| **BM25**         | Best Matching 25              | 关键词检索算法   | 按"词出现频率 + 稀有度"打分的关键词检索，擅长精确词，不花钱不调模型。                         |
| **embedding**    | —                             | 嵌入/向量     | 把文字变成一串数字（向量），让"意思相近"的文字距离也近，用于语义检索。                          |
| **rerank**       | —                             | 重排        | 召回一堆候选后，用更精的模型重新排序，通常是最划算的单点提升。                               |
|                  |                               |           |                                                               |

---

## 2. 本库现状实测（2026-11-16 复测）

### 2.1 目录与职责（命令实测，非推测）

```
D:\Shervon_KnowledgeBase\
├─ .stfolder\           ← Syncthing 同步标记（同步器建的，不是你的设计）
├─ 00-inbox\            空（传送带）
├─ 10-source\           3 个入库夹，192.3 MB 原件
├─ 20-md\               909 个图片 + 3 个 .md（2.4 MB 文本），235.8 MB 图
├─ 30-index\            catalog.md / manifest.csv / todo.md / issues.log
├─ 40-new\              12 个脚本与报告（含 figures-report JSON、_append_page_appendix.py）
├─ 90-tool\             rules.md / prompt*.md / taxonomy.md / CHANGELOG / VERSION=2.3
│  └─ scripts\          ingest.ps1(31KB) / catalog.ps1(13KB) / check-links.ps1 / figures.py / budget-watch.ps1
└─ README.md            71 行，入口说明
```

#### 2.2 全库 md 总量（你问"多少字/MB"的实测答案）

| 项 | 实测值 |
|:---|---:|
| md 文件数 | **12 个**（3 本书 + 30-index 2 个 + 90-tool 5 个 + 根目录 2 个） |
| md 总字节 | **2,544,009 B ≈ 2.43 MB** |
| md 总字符 | **1,601,942 字符 ≈ 53.4 万汉字**（按 3 B/汉字折） |
| 折合 token【估计】 | **~35 万 text token**（1.5 字/token） |
| 图片 | **909 个文件 / 235.84 MB** |
| 三本书 | 化工原理 623 KB / 16221 行 / 426 图链；机械密封 438 KB / 10530 行 / 319 图链；气液搅拌釜 343 KB / 4410 行 / 137 图链（两本为 2026-11-17 新解析重建版，含 `<!-- page: N -->` 页码锚点） |

**300 本书的外推【估计】**：300 × 0.8 MB ≈ **240 MB md ≈ 8 千万汉字 ≈ 5,300 万 text token**；图片 300 × 300 张 ≈ **9 万张图 ≈ 70 GB**。这个量级决定了两件事：(a) 图不可能全部喂视觉模型（成本还行但时间太长），必须"按需喂"；(b) 20-md 的图不能全进 git（§3.11）。

### 2.3 五个实测问题（带证据，含 v2 修正）

**问题 1：86 条死链——根因已查清，不是图丢了。**
【实测 v2】化工原理：md 内图链引用 **426** 条，磁盘实际图文件 **340** 个，差 86 条。
死链样例（md 内的链接原文）：
```
图片/图1.3%20U形管液柱压差计.jpg        ← 带 %20（URL 编码）
```
磁盘实际存在：`图1.3 U形管液柱压差计.jpg`（真空格）。
→ **结论：86 条死链 = 链接里的 URL 编码（%20 等）没被解码成空格**，文件名本身存在。修法极简单：`check-links.ps1` 比较前先对链接做一次 URL 解码（或一次性把 md 里的 `%20` 批量替换为空格）。**这不是 MinerU 的锅，也不是图丢了。**
【实测】另有一类真垃圾：`_a.jpg`、`a _2.jpg`、`a _6.jpg` 这类图注残片命名（图注被拆成 a/b 字符），属于 MinerU 版面切分问题，共约十余个，需重解析对应页或人工改名。

**问题 2：OCR 标题层级被压平，破坏可引用性。**
【实测】机械密封那本书的标题序列：

```
# 第1章概述
## 1.1 密封的作用
## 1.1.1 泄漏与密封
## (1)尽量减少密封部位      ← 本是三级标题下的列表项，被提升为 h2
## (2)堵塞或隔离泄漏通道
## 1.2 密封的分类及选型
```

【实测】量化后果：全书 `## ` 级标题共 **351** 个，其中 `(n)` 型假标题 **163** 个（占 46%），真节标题 `## X.Y` 仅 **176** 个。
→ 后果：**按标题切块会多切出 163 个假的"节"**，章节地图、锚点、引用编号全部失真。凡是要"按 §节号 引用"的方案，第一步必须先把这 163 个降级成正文列表项。

**问题 3：书内没有可分页的锚点。**
【实测】3 个 md 都是单文件 6k~17k 行，无 `<!-- page: N -->` 之类分页标记。
→ 只能按**行号**或**标题文本**引用，不能按"第 137 页"引用。而工程书里"第 137 页图 6-3"是最自然的引用单位。
→ 好消息：【实测】你的 `40-new\` 里已经有 `_append_page_appendix.py`（名字显示它做过"追加页码附录"的尝试）与 figures-report JSON——**页码锚点的雏形你已经自己做过一次**。完整方案见 §9.8。

**问题 4：没有任何版本历史。**
【实测】根目录无 `.git`；有 `.stfolder`（Syncthing 标记）。
→ 后果：靠"文件同步"而不是"版本控制"。同步≠历史：改错了只能靠 `.stversions`（如果开了），没有语义化 diff、没有分支、没有 commit message。**这是必须第一个补的洞**（§3.11）。

**问题 5：DSH 检索索引只覆盖了 1/3 的书。**
【实测】`library_list`：`kb` 库只有机械密封（836 chunk）；化工原理、气液搅拌釜没进任何索引。→ 现状是"问机械密封能走向量库，问化工原理只能走 grep"。**LLM Wiki 建好之后是否顺带解决：见 §9.10（答案是：部分解决，原理在那节）。**

### 2.4 现状 → LLM Wiki 三层映射

| LLM Wiki 层 | 你已有的对应物 | 判定 |
|:---|:---|:---|
| **Raw sources** | `10-source\`（原件，只增不改） | ✅ 完全合规，是不动点 |
| Raw 的派生 | `20-md\`（解析全文 + 图） | ⚠️ 属于 raw 层，不是 wiki 层 |
| **Wiki** | **不存在** | ❌ 核心缺口 |
| **Schema** | `90-tool\rules.md` + `taxonomy.md` | ⚠️ 存在但目标错位 |

**为什么 `20-md` 不是 wiki 层【判断】**（三条，任一条都成立）：
1. **生命周期不同**：`20-md` 是 `ingest.ps1` 的产物，可以随时删了重跑；wiki 页删了就没了。混在一起，一次重解析会覆盖掉综合成果。
2. **形态不同**：`20-md` 是线性全文（书的投影），wiki 是网状综合。线性文件表达不了"五本书都讲了搅拌功率但口径不同"。
3. **写者不同**：`20-md` 由脚本写，wiki 由 LLM 写。同一目录两种写者 = 迟早互相覆盖。

**为什么 `rules.md` 不是合格的 schema【判断】**：它规定的是**脚本怎么把 PDF 搬成 md**（加工规范）；Karpathy 的 schema 规定的是**LLM 怎么维护知识**（编辑规范）。两者不重叠。你需要一份新的 `AGENTS.wiki.md`，不是改 `rules.md`（§3.4）。

**但你已经有了三操作的骨架**（这是最值钱的发现）：

| Karpathy 的操作 | 你的对应物 | 差距 |
|:---|:---|:---|
| `index.md`（内容目录） | `catalog.md`（书目表） | 只索引到"书"，没索引到"知识" |
| `log.md`（时间线） | `issues.log` | 只记错误，不记 ingest/query/lint |
| `Lint`（体检报告） | `todo.md`（8 节检查） | 检查文件完整性，不检查知识一致性 |

### 2.5 差距清单（带验收标准）

| ID | 差距 | 验收标准（可判真假） |
|:---|:---|:---|
| **G1** | 无综合层 | `50-wiki\` 下出现 ≥10 个概念/实体页，且每个页被 ≥2 处其他页链接 |
| **G2** | 无跨书链接 | 至少 3 条跨书引用，形如"《化工原理》§2.3 ↔《气液搅拌釜》§4.1 口径不同" |
| **G3** | 无冲突登记 | `50-wiki\openq\` ≥3 条实质冲突，每条指明两处出处 |
| **G4** | 无版本控制 | `git log --oneline` ≥1；每次 ingest 一个 commit |
| **G5** | 无知识级 log | `50-wiki\log.md` 有 ingest/query/lint 三类条目 |
| **G6** | 引用粒度不足 | 每条断言落到 `《书名》§节号` 或 `#L行号`，抽查 10 条全中 |
| **G7** | 图未转述 | 每张被引用的图有 ≥1 句文字转述 |
| **G8** | 无术语唯一表 | `50-wiki\glossary.md` ≥30 条，每个概念只用一个译名 |

### 2.6 以 300 本书为预设的差距重估（v2 新增）

**v1 版按"3 本书"设计，你在第 9 问纠正了我：预设应为 300 本书 + 零散资料。** 哪些设计会因此在 300 本下坏掉？哪些反而更稳？

| 设计 | 3 本书时 | 300 本书时会怎样 | 处理 |
|:---|:---|:---|:---|
| `index.md` 单文件 | 50 行，随便读 | 7500 行 ≈ 45 万字符，LLM 一次读不下 | index 必须**分册**：`index.md` 只放主题分类 + 每类一行，每类再挂 `index-XX.md`（§6.4） |
| 每次提问先读 index | 无感 | 读 45 万字符 = 30 万 token，一问烧几块钱 | 提问先 grep index，再按类读子索引 |
| `glossary.md` 单文件 | 30 条 | 术语可能 3000+ 条 | glossary 按领域拆（`glossary-密封/搅拌/传热…`）或直接由脚本从 frontmatter 生成 |
| 图片全部喂视觉模型 | 无感（876 张） | 9 万张图 × 1.2K token = 1 亿 token，免费档也要排队跑几天 | **按需喂**：ingest 时只喂"被 wiki 页引用且无文字转述"的图（§3.5） |
| 20-md 全进 git | 42 MB 无感 | ~70 GB 图片，GitHub 仓库上限 5 GB | 图不推 GitHub，或用 LFS（§3.11） |
| 14 页首批清单 | 够 | 只是第一本书的样板 | 每本书"编译"产出 20~25 页；300 本 → ~7500 页，需 lint 自动化（§3.7） |
| `wiki-lint.ps1` 手动跑 | 可以 | 7500 页手动跑不过来 | lint 挂到 ingest 流程里（v2 事件钩子思想），每次 ingest 自动跑 |
| Obsidian 单 vault | 可以 | 7500 页星图会糊成毛球 | 用 folder 限定视图 + 按领域分 vault 或 bookmark（§3.12） |

**结论【判断】**：300 本书的规模让"分层、分册、自动化、按需喂图"从"可选优化"变成"必备设计"。v2 方案已全部按此口径重写。

---

## 3. 改造方案 v2：从"书籍仓库"到"知识库"

### 3.1 目标结构

```
D:\Shervon_KnowledgeBase\
├─ 00-inbox\            （不变）
├─ 10-source\           【raw】原件，一字节不改
├─ 20-md\               【raw 派生】解析全文 + 图，脚本独占
├─ 30-index\            【机器索引】catalog / todo / manifest（不变，继续自动生成）
├─ 40-new\              【草稿】报告、一次性脚本
├─ 50-wiki\             ★【新增：LLM 独占的综合层】
│  ├─ index.md          总目录（按主题分类，每类一行，指向子索引）
│  ├─ log.md            append-only 时间线
│  ├─ glossary.md       术语唯一译名表（大了按领域拆）
│  ├─ concepts\         概念页（机理性、可复用）——主力，占 60%
│  ├─ entities\         实体页（设备/零件/标准/材料）
│  ├─ sources\          单本页（这本书能回答什么）
│  ├─ comparisons\      对比页（跨书/跨型号）
│  ├─ howto\            做法页（选型/校核步骤，crystallize 的落点）
│  └─ openq\            未决问题与冲突
├─ 90-tool\             【schema】rules.md（加工）+ AGENTS.wiki.md（编辑，新增）
└─ README.md
```

**为什么用 `50-` 前缀（你问的第 12 条）**：
- 是，**编号的首要作用是排序**——Windows 资源管理器按名称排序，00/10/20/30/40/90 的顺序就是你数据流的顺序（进料 → 原件 → 解析 → 索引 → 草稿 → 综合 → 工具）。
- 为什么不用 a/b/c/d：**数字天然表达"流程顺序"，字母没有语义**。a-wiki 排在 z-tool 前面，但 wiki 在数据流里是第 6 站，字母序会撒谎。且你的规则、README、脚本里已写死数字约定，改字母要动一堆引用。
- 用 50 而不是 60/70/80：**50 是现有序列里的空号**（00→10→20→30→40→90 中唯一连续空位是 50），插进去不改任何现有路径。**也可以用任何你喜欢的名字（比如 05-wiki、wiki），但数字前缀比纯字母好，理由如上。**

**为什么不放 `20-md\_wiki\`**：见 §2.4 三条理由，最硬的是"两种写者混目录"。

### 3.2 命名：用 Karpathy 的还是 GitHub 项目的（你问的第 11 条）

**【判断】** 结论：**目录层保持你的数字编号 + Karpathy 的语义名；文件层用 Karpathy 的通用名；技能名从 geronimo-iia 的 17 个 skill 里挑 6 个核心名（setup / ingest / crystallize / lint / graph / research）。** 三者不冲突，对照如下：

| 位置 | Karpathy 原名 | geronimo-iia 名 | 本库采用 | 理由 |
|:---|:---|:---|:---|:---|
| 综合层 | `wiki/` | `content/`（大致） | `50-wiki\` | 保留你的数字前缀（排序语义），后接 Karpathy 的 `wiki`（一看就知道这是 LLM Wiki 模式） |
| 总目录 | `index.md` | — | `index.md` | 名字已是通用事实标准 |
| 时间线 | `log.md` | — | `log.md` | 同上 |
| 契约文件 | `CLAUDE.md` / `AGENTS.md` | `AGENTS.md` | `AGENTS.wiki.md` | 你已在用 AGENTS 命名；加 `.wiki` 后缀区分"编辑契约"与"全局行为" |
| 页面分类 | entities/concepts | 有类似分类 | concepts/entities/sources/comparisons/howto/openq | Karpathy 词 + 工程场景补两类 |
| 脚本 | — | 24 个 MCP 工具名 | wiki-lint.ps1 / wiki-index.ps1 / md-anchor.ps1 | 你已有 .ps1 惯例 |
| 会话技能 | — | setup / ingest / crystallize / lint / graph / research | 从 17 个 skill 名里挑 6 个写进 AGENTS.wiki.md 的章节 | 见 §8.3，通用可辨认 |

**通用性原则**：外人（或未来的 agent）看到 `50-wiki\index.md` + `log.md` + `AGENTS.wiki.md`，立刻知道"这是 Karpathy LLM Wiki 模式的一个落地"；看到数字前缀，立刻知道你库的数据流。**两者叠加比单一抄任何一方都更可辨认。**

### 3.3 需要改的规则（增量，不重写）

`rules.md` 从 v2.3 → **v3.0**，只加四节，不动原有 11 节：

| 新增节 | 内容 | 为什么独立成节 |
|:---|:---|:---|
| §12 `50-wiki` 层 | 该层由 LLM 独占写；脚本只读；`20-md` 重解析不得波及该层 | 明确写者边界，防覆盖 |
| §13 页面规范 | 五类页面的 frontmatter、行数上限、命名、链接语法、confidence/status 字段 | schema 的实体部分（v2 字段） |
| §14 引用约定 | `《书名》§节号` + `#L行号` 双轨；图必须文字转述；新书必带页码锚点 | 解决 G6/G7 + 你问的分页 |
| §15 三操作 SOP | ingest / query / lint 的步骤与产出（含 git commit、事件钩子） | 附录 C 的调用方 |

**同步动作**：`VERSION` → `3.0`，`CHANGELOG.md` 加一节，`README.md` 的目录表加 `50-wiki\` 一行。

### 3.4 新增 schema：`90-tool\AGENTS.wiki.md`

**这是整个改造里唯一"必须有、且只能人写"的文件。** 骨架见附录 C（v2 版）。要点八条：

1. **写者声明**：`50-wiki\` 只由 LLM 写；`10-source`/`20-md` 只读；`30-index` 只由脚本写；**人在 Obsidian 里只读**（§3.12）。
2. **断言规则**：任何一句事实断言必须挂 `sources`。没来源的不许进概念页，只能进 `openq`。
3. **合并优先**：ingest 前必须先查 `glossary.md` + `concepts\` 是否有同义页；**有则改，无则建**（v2 事件钩子化：查重是 ingest 第 0 步，不许跳过）。
4. **单页上限 150 行**，超了拆页并留一行 `→ 已拆至 [[X]]`。
5. **每次 ingest 必须做六件事**：查重、写/改页、更新 index、追加 log、死链自检、git commit（含 touch=N）。
6. **图规则**：引用图必须文字转述；转述不出（图太复杂）→ 喂视觉模型拿转述（§3.5），成本记 log。
7. **生命周期字段**（v2）：每页 frontmatter 必带 `status: active|draft|stale|superseded` 与 `confidence: high|medium|low`；新信息推翻旧断言 → 旧页标 `superseded` 并 `supersedes:` 指向新页，**不删旧断言**。
8. **禁止自创目录**：只能往 7 个子目录写；要加新目录先改本文件。

### 3.5 三操作 SOP v2（可直接当提示词用）

#### Ingest —— 一本书一次编译

| 步 | 动作 | 产出 | 300 本书口径的注意点 |
|---:|:---|:---|:---|
| 0 | 前置检查：`todo.md` 无该书未决项；死链已修（**化工原理先解码 %20**） | — | 死链修复是一次性脚本活，与 LLM 无关 |
| 1 | 提取标题树（`^#{1,3} ` + 行号），标注假标题并降级 | 章节地图 | 先跑 `md-anchor.ps1` 补页码锚点（§9.8） |
| 2 | 写 `sources\<书>.md` | 1 页 | 300 本 → 300 个 source 页，是"这本书能答什么"的闸门 |
| 3 | 列 10~20 个候选概念 → 查重（glossary + concepts + index）→ 建/改 | 8~15 页 | 书多了以后 80% 的 ingest 是**改旧页**不是建新页 |
| 4 | 每页写：定义/机理/口径/参数/边界/图转述/来源 | 见模板 | 图按需喂视觉模型（见下） |
| 5 | 回改受影响页：冲突 → 开 openq；换代 → 标 superseded | diff | 不删旧断言，只标记 |
| 6 | 更新 `index.md`（按主题，非按书；大了写子索引） | 1 文件 | 300 本后 index.md 只放分类树 |
| 7 | 追加 `log.md`：`## [日期] ingest | 《书名》 touch=N in=…k out=…k ¥=…` | 1 条 | **记 token 与钱**，成本才可见 |
| 8 | 死链自检 + `git commit -m "ingest: 《书名》 touch=N"` | commit | 每本书一个 commit |

**验收**：触及页数 10~15。远低于 10 说明在抄书，远高于 20 说明拆太碎。

**按需喂图规则（300 本书的省钱关键）**：ingest 时**不是**把 400 张图全喂视觉模型，而是只喂两类：①被 wiki 页引用且文字转述不出的图；②你点名要精读的图（如关键结构剖面）。估量：每本书实际喂 20~50 张，成本 ¥0.01~¥0.06（免费档为 0）。

#### Query —— 先读索引，再回填

| 步 | 动作 |
|---:|:---|
| 1 | **grep `index.md`** 定位主题 → 读 ≤10 个候选页（300 本后不许整读 index） |
| 2 | 页不够 → 查 `glossary.md` 同义词 → 再 grep `20-md`（最后手段） |
| 3 | 回答必须带 `《书名》§节号` 或 `#L行号` 引用 |
| 4 | **判断是否回填**：会被再问一次 → 写成 `comparisons\`/`howto\` 页（= v2 的 crystallize）并登记 index；否则只记 log |

#### Lint —— 七项体检（ingest 后自动跑，周期全量跑）

| # | 检查 | 判据 | 修法 |
|:---|:---|:---|:---|
| 1 | 死链 | `[[X]]` 无对应文件 | 建页或改链 |
| 2 | 孤儿页 | 入链 = 0 且不在 index | 加链接或删 |
| 3 | 无来源页 | frontmatter 缺 `sources` | 补来源或降级 openq |
| 4 | 超长页 | > 150 行 | 拆页 + 留指针 |
| 5 | 同义重复 | glossary 里两个译名各有一页 | 合并 + redirect |
| 6 | 过期断言 | `status: stale` 未被处理 | 重读来源，改或升 superseded |
| 7 | index 漂移 | index 页数与磁盘页数不符 | 重生成 index |
| 8 | 图引用无转述 | 引用图但无文字转述且无 vision 记录 | 补转述或喂图 |

> 全流程 14 步图（你 → 机 → 我 → 问）见 **第三部分 §2.7**，本节只留 SOP 表格。

> **v3.2 起**：图中 ②③④⑤ 四步已收拢成一条命令 `90-tool\scripts\ingest-build.ps1 -Book "<入库夹名>"`（生成 + 定名 + 归档未引用图 + 图链自检 + 七行验收）。手写 md 的做法作废，见 `rules.md` §16。

### 3.6 首批页面清单（P1 试点仍按一本书跑，但流程按 300 本设计）

| # | 路径 | 类型 | 来自 |
|---:|:---|:---|:---|
| 1 | `sources/机械密封结构图例及应用.md` | source | 机械密封（272 页） |
| 2 | `concepts/泄漏与密封判据.md` | concept | 机械密封 §1.1 |
| 3 | `concepts/端面比压与pv值.md` | concept | 机械密封 §1.2 + 化工原理（**跨书**） |
| 4 | `concepts/摩擦副材料配对.md` | concept | 机械密封 §1.3 |
| 5 | `concepts/静密封与动密封分类.md` | concept | 机械密封 §1.2.1 |
| 6 | `entities/机械密封-结构型式.md` | entity | 机械密封 第2~4 章 |
| 7 | `entities/密封辅助件.md` | entity | 机械密封 |
| 8 | `sources/化工原理.md` | source | 化工原理（**先修 %20 死链**） |
| 9 | `concepts/流体流动-伯努利方程.md` | concept | 化工原理 第1章 |
| 10 | `concepts/传热-总传热系数.md` | concept | 化工原理 第4章 |
| 11 | `sources/气液搅拌釜γ-CT.md` | source | 气液搅拌釜 |
| 12 | `concepts/气液分散-搅拌功率.md` | concept | 气液搅拌釜 + 化工原理（**跨书**） |
| 13 | `entities/搅拌桨型谱.md` | entity | 气液搅拌釜 |
| 14 | `comparisons/搅拌功率关联式对比.md` | comparison | 第 12 页派生，**跨书冲突第一个落点** |

第 3、12、14 页是全批的价值锚点：必须跨书，否则只是"抄书加链接"。

### 3.7 脚本层要加什么（最小集，三个）

| 脚本 | 干什么 | 300 本书口径 |
|:---|:---|:---|
| `wiki-lint.ps1` | 八项体检（§3.5），输出写 `50-wiki\_lint.md` | 支持目录递归 + 增量模式（只查最近改的页） |
| `wiki-index.ps1` | 扫 frontmatter 生成 index 表格 + 按领域分册 | 自动分册，防单文件爆炸 |
| `md-anchor.ps1` | 给 `20-md` 补 `<!-- page: N -->` 锚点（用 MinerU middle.json 的 page_idx） | 解析后自动跑，成为 ingest.ps1 的一步 |

**红线**：三个脚本只读 `20-md`，只写 `50-wiki`。`.ps1` 存 **UTF-8 带 BOM**（你 README 已记过这个坑）。

### 3.8 分阶段执行计划（300 本书口径）

| 阶段 | 内容 | 耗时【估计】 | 验收 |
|:---|:---|:---|:---|
| **P0 打地基** | git init + .gitignore + GitHub 私有仓库 + 建 `50-wiki\` 7 子目录 + `AGENTS.wiki.md` + rules 升 v3.0 + **Obsidian 只读 vault** | 0.5 小时 | git log ≥1；AGENTS.wiki.md ≥100 行 |
| **P1 单本试点** | 机械密封 7 页 + 完整 ingest + lint | 1 会话（~30 万 in） | 触及 10~15 页；死链 0 |
| **P2 三本铺开** | 化工原理（先修 %20）+ 气液搅拌釜；glossary 30 条 | 2 会话 | 14 页齐；跨书 ≥3；冲突 ≥3 |
| **P3 闭环** | 回填 3 页；lint 全过；index 自动生成 | 1 会话 | lint 八项全过 |
| **P4 规模** | 每进 10 本书跑一次全量 lint + 分册 index | 常态化 | §6.4 阈值触发时升级检索层 |

### 3.9 成本账（你问的第 2 条；附录 F 有完整计算器）

#### 3.9.1 价格档（2026-11-16 核对的公开价）

**主推口径：DeepSeek 官方 `deepseek-flash`**（DeepSeek-V4.1-Flash-1017；旧名 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 已退休但仍接受，按 flash 计费）。一个模型同时干文本 + 视觉（**Vision ✓**）、1M 上下文，最省事；v4-pro **没有 Vision**。

| 档位 | 模型 | 输入 元/M token | 输出 元/M token | 来源 |
|:---|:---|:---|---:|:---|
| **主推（off-peak）** | **deepseek-flash**（带 Vision） | **1.08**（cache-miss；cache-hit 仅 0.022） | **4.32** | [DeepSeek 官方定价](https://api-docs.deepseek.com/quick_start/pricing)：$0.15 / $0.6 per M × 7.2 汇率 |
| 主推（peak） | 同上 | 2.16 | 8.64 | peak = UTC 周一至五 01:00-04:00、06:00-10:00（中国节假日除外），价翻倍 |
| 谷价（免费） | GLM-4V-Flash（智谱） | **0** | **0** | [ai-tokens.cn 核验](https://ai-tokens.cn/model/276.html)：官方标价 0，16K 上下文，有速率/并发限制 |
| 低价付费 | qwen-vl-ocr（阿里云百炼） | 0.3 | 0.5 | [阿里云开发者社区定价表](https://developer.aliyun.com/article/1733271)（2026-05-08 文，含官方价格截图） |
| 中档 | qwen-vl-plus | 0.8 | 2 | 同上 |
| **峰价（强）** | qwen-vl-max | 1.6 | 4 | 同上 |
| 峰价（更强，阶梯） | qwen3-vl-plus | 1 / 1.5 / 3（按 32K/128K/256K 阶梯） | 10 / 15 / 30 | 同上 |

**【判断】选型**：**统一用 deepseek-flash**。理由：一把 key 覆盖文本+图（不用第二家）；1M 上下文，35 万 token 的书塞得下，不必切块重读到吐；off-peak 比 v4-pro 便宜 4 倍多。GLM-4V-Flash 免费但 16K 上下文 + 速率限制，只适合少量图应急。

#### 3.9.2 以《化工原理》为例算一本书（deepseek-flash，off-peak 口径）

假设：426 图链（实际图 ~400 张）；每张图 1200 视觉 token；图转述输出 200 token/图；文本按"分块重读 ×1.5"计。

| 项 | 算法 | 结果（off-peak） |
|:---|:---|---:|
| 文本 input | 1082 KB ≈ 35 万汉字 ≈ 23 万 token；×1.5 | **~35 万 in ≈ ¥0.378** |
| 文本 output | 12 页 × 1.2K | **~1.5 万 out ≈ ¥0.065** |
| 图 input（按需 30 张） | 30 × 1200 = 3.6 万 | **≈ ¥0.039** |
| 图 output（转述） | 30 × 200 = 6K | **≈ ¥0.026** |
| **① 只文本、不喂图** | 0.378 + 0.065 | **≈ ¥0.44/本** |
| **② 按需 30 图（推荐）** | ① + 0.039 + 0.026 | **≈ ¥0.51/本** |
| ③ 全量 400 图（不推荐） | 48 万 in + 8 万 out | **≈ ¥1.31/本** |
| peak 时段 | ①②③ ×2 | **¥0.89 / ¥1.01 / ¥2.61** |

**结论【判断】**：**图不是成本问题。** 按需喂 30 张图，一本教材只多花 **7 分钱**；全量 400 张也才多 8 毛 6。真正的账是文本编译（¥0.44/本），真正的瓶颈是**时间与速率**（9 万张图排队太慢）——所以规则是"按需喂图"，不是"为了省钱"。

#### 3.9.3 单次提问多少钱（你问的"库建成了，单次提问各方案花多少 token"）

| 方案 | 一次提问的输入 | 一次输出 | off-peak（flash） | peak（flash） |
|:---|:---|---:|---:|---:|
| **LLM Wiki** | 读 index 片段 ~1K + 3~5 页 wiki ~4K ≈ **5K in** | ~1K out | **≈ ¥0.01** | ≈ ¥0.02 |
| **向量 RAG** | top-5~8 chunk ~5K in | ~1K out | **≈ ¥0.01** | ≈ ¥0.02 |
| **grep 全文** | 命中片段 ~2K in | ~1K out | ≈ ¥0.006 | ≈ ¥0.012 |
| **GraphRAG Global** | 20~50 份社区报告 map-reduce ~**2~5 万 in** | ~1K out | **≈ ¥0.03~0.06** | ≈ ¥0.06~0.12 |
| **GraphRAG Local** | 子图 + 关联 chunk ~8K in | ~1K out | ≈ ¥0.013 | ≈ ¥0.026 |

**结论【判断】**：单问成本 LLM Wiki ≈ RAG ≈ grep（都是分钱级），**GraphRAG Global 贵 3~6 倍**。三者的真正差别不在单问价格，在**回答质量和累积性**（§6.1）。

#### 3.9.4 300 本书的总账【估计】

| 项 | 结果 |
|:---|---:|
| 全量编译 300 本（文本 + 按需 30 图/本） | 文本 300×35 万 = 1.05 亿 in / 450 万 out ≈ **¥133**；图 9000 张 = 1080 万 in / 180 万 out ≈ **¥20**；合计 **≈ ¥153（off-peak）/ ¥305（peak）** |
| 对比 GraphRAG 全量索引同语料 | 索引阶段 300~800% 的 LLM 调用 → **几千元级别**（§5.4） |
| 结论 | **300 本书的 LLM Wiki 编译，总成本约等于几顿外卖；GraphRAG 约等于一台新电脑。** 这也是选型的重要论据。 |

### 3.10 风险与回滚

| 风险 | 触发条件 | 回滚 |
|:---|:---|:---|
| LLM 批量写坏 | 一次 ingest 改了 15 页 | `git reset --hard HEAD~1`（P0 必须先做 git） |
| `20-md` 被误覆盖 | wiki 内容写进 20-md 后重跑 ingest | 规则层禁止；ingest.ps1 已"不覆盖已有 md" |
| 目录约定打架 | 新目录和 rules.md §4 冲突 | `50-wiki` 是根级新层，§12 显式豁免 |
| 概念页越写越像抄书 | 单页 > 150 行 | lint 第 4 项强制拆页 |
| 图片信息进不来 | 只链图不转述 | lint 第 8 项强制 |
| GitHub 仓库超限 | 图全推上去（70 GB > 5 GB） | 图排除或 LFS（§3.11） |
| Obsidian 里人改坏了 | 人违背只读约定 | git diff 暴露 + log 汇报（§3.12） |

### 3.11 git 本地 + GitHub 同步方案（你问的第 10 条）

**目标**：本地版本历史 + GitHub 异地备份 + 每次 ingest 一个 commit。

```
# 本地（P0 第一步，先装好 git 再执行）
git init
# .gitignore 写：
#   10-source/          ← 192 MB 原件不版本化（外部可重取）
#   .stfolder/          ← Syncthing 标记不入库
#   50-wiki/_lint.md    ← 自动生成的报告不入库（可重算）
#   *__pycache__*

# GitHub：建一个 **私有（private）** 仓库 —— 你的书是版权材料，绝对不能 public
git remote add origin https://github.com/<你>/Shervon-KnowledgeBase.git
git add 20-md 30-index 40-new 50-wiki 90-tool README.md AGENTS.md
git commit -m "P0: LLM Wiki 地基"
git push -u origin main
```

| 决策点 | 建议 | 理由 |
|:---|:---|:---|
| 仓库可见性 | **私有** | 版权书内容 |
| `10-source` PDF | **排除** | 192 MB，外部可重取；版本控制保护"不可重建的东西"（你的 wiki） |
| `20-md` 图片（235 MB） | **3 本书时直接推**；300 本（~70 GB）后 | 要么用 **Git LFS**，要么把 `20-md/*/图片` 排除、图片走 Syncthing 继续同步。**P0 先直接推，到 P4 再切 LFS。** |
| Syncthing 与 git 共存 | `.stignore` 加 `.git` | 防止 git 对象文件被同步打架 |
| 提交节奏 | 每本书 ingest 一个 commit；lint/修图各一个 | message 带 `touch=N`，历史即审计（v2 的"变更审计"免费实现） |
| 冲突（多端） | 只在本机编辑，GitHub 只做备份 | 单写者策略，不搞多人协作合并 |

### 3.12 Obsidian 星图 + "人机同步"方案（你问的第 13 条）

**能不能用 MCP 建星图**：星图（graph view）是 **Obsidian 客户端的渲染功能**，不是数据。MCP（我手上的 obsidian_* 工具）能读写/搜索/查反向链接，但**不能替你画出星图**。星图 = 你的 vault + `[[wikilinks]]`，由 Obsidian 自己渲染。所以方案是：

| 步骤 | 做什么 | 谁做 |
|:---|:---|:---|
| 1 | 在 Obsidian 里 **"打开文件夹为库（Open folder as vault）"** 选择 `D:\Shervon_KnowledgeBase`（或把该文件夹加入已有库为子库） | 你手动一次 |
| 2 | 确保 wiki 页用标准 `[[wikilink]]`（AGENTS.wiki.md §3 已强制） | LLM |
| 3 | 打开 Graph view → 星图自动出现：`50-wiki` 是网络核心，`20-md` 的 3 个大节点是孤岛 | 你 |
| 4 | 用我手上的 `obsidian_backlinks` 在每次 lint 时抽查反向链接是否与 git 里一致 | LLM（MCP） |

**【实测 v2】** 当前 MCP 连接的 Obsidian 库只有 4 个文件（欢迎/未命名/技术手册/2026-11-12），**不是你的知识库**。所以要么新建库指向知识库，要么把知识库设为子库。

**"不准人为改动，改了要报告"怎么落地**：
1. **写入契约**：`AGENTS.wiki.md` §0 写明"Obsidian 对人只读"。
2. **检测手段 = git**：每次会话开始（或 lint）跑 `git status --short`，有未提交改动 → 说明有人动过（Obsidian 是唯一人工入口），逐文件汇报给你："你改了 X，是否要我把改动吸收进 wiki？" —— 这就是你要的"改了要告诉你"。
3. **吸收流程**：人改的内容如果是对的 → LLM 走 ingest 流程把它"正规化"（补来源、建链接、进 index）后 commit；如果是误改 → 建议 `git checkout` 还原。
4. 技术边界：Obsidian 没有原生只读锁，**"只读"是约定 + git 审计**，不是强制的文件权限——但对你够用，因为只有你一个人。

---

## 4. RAG：检索增强生成

### 4.1 出处与一句话定义

**【文献】** RAG 由 Lewis et al. 提出（NeurIPS 2020, *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, Meta AI）。

一句话定义：**提问时才去资料里翻答案片段，塞进上下文让 LLM 生成回答。** 核心等式：

> RAG = 检索（retrieve）+ 生成（generate）

检索解决"LLM 没背过/背不进去"，生成解决"怎么把找到的片段变成人话"。它要解决的问题只有一个：**LLM 的上下文窗口装不下你全部资料，所以只装相关的。**

**和你库的关系【实测】**：你其实已经有一只脚在 RAG 里了——DSH 的 `kb` 向量库（机械密封 836 chunk）就是标准的"切块→嵌入→检索"后半段。缺的是另外半只脚：另外两本书没入库（§2.3 问题 5）。

### 4.2 九段流水线（对照你的库）

| # | 阶段 | 干什么 | 你的库现状 |
|:--|:---|:---|:---|
| 1 | **采集** | 拿到原始文件 | ✅ `10-source\` |
| 2 | **解析** | PDF/网页 → 结构化文本 | ✅ MinerU 管线（ingest.ps1） |
| 3 | **清洗** | 去页眉页脚、乱码、水印 | ⚠️ 半自动（图注残片 `_a.jpg` 未清） |
| 4 | **切块 chunk** | 把长文切成 512~1024 token 的小块 | ⚠️ 机械密封切进了 kb 库，但**按假标题切坏了**（§2.3 问题 2：163 个假 h2） |
| 5 | **富化** | 每块加元数据：书名/章节/页码/标题层级 | ❌ 无页码锚点（§9.8）；标题层级被压平 |
| 6 | **嵌入 embedding** | 每块转成向量 | ✅ kb 库已做（1/3 覆盖） |
| 7 | **索引** | 向量进数据库，建检索结构 | ✅ 同上 |
| 8 | **检索 retrieve** | 问句转向量 → 找最像的 top-k 块 | ✅ 同上 |
| 9 | **生成 generate** | 把 top-k 块 + 问题塞给 LLM 生成答案 | ✅ DSH 注入 |

**【判断】** 九段里你已走通 1/2/6/7/8/9，卡在 3/4/5。而 3/4/5 恰好决定检索质量上限（garbage in, garbage out）。**先修 %20 死链和假标题，比上任何新模型都划算。**

### 4.3 关键参数（经验值，非铁律）

| 参数 | 经验值 | 说明 |
|:---|:---|:---|
| chunk 大小 | 512~1024 token（中文 ~800 字~1600 字） | 太小断语义，太大稀释相关性 |
| overlap | 10~20% | 防止关键句正好落在切缝上 |
| top-k 召回 | 召回 20~50，重排后送 5~8 | 召回贪多（便宜），送 LLM 贪精（贵） |
| 稀疏 vs 稠密 | 精确词用 BM25，模糊语义用向量 | 混合最好（下节） |

### 4.4 检索策略：从"关键词"到"混合+重排"

| 策略 | 原理 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **BM25（稀疏）** | 按词频+稀有度打分 | 精确术语（"端面比压""pv 值"）一打一个准；免费、可解释 | 换个说法就找不到（"密封环" vs "摩擦副"） |
| **向量（稠密）** | 语义相似度 | 模糊问法也能中 | 专有名词可能漂移；要建库要花钱 |
| **混合** | 两路各召回再融合 | 取长补短，工程事实标准 | 要维护两套索引 |
| **RRF 融合** | 按"两路排名倒数和"合并 | 免调权重的稳健融合 | 有出处：Cormack et al. 2009（k=60 是常用参数） |
| **重排 rerank** | 召回一堆后用更精的模型重排 | **最划算的单点提升** | 多一次模型调用；常用 bge-reranker 系列 |
| **Lost in the Middle** | 位置先验：LLM 对上下文中间部分记得最差 | 把最相关的块放首尾 | 【文献】Liu et al. 2023，U 形注意力曲线 |

**【判断】** 你 300 本书的检索层最终形态就是这一节：BM25 + 向量 + RRF + 重排——这正是 qmd 干的事（§6.4 第三档）。

### 4.5 RAG 的七条死穴（它为什么回答不了你的问题）

| # | 死穴 | 表现 | 你的场景示例 |
|:--|:---|:---|:---|
| 1 | **无累积** | 每次提问从零拼答案 | 上次问过的"pv 值极限"下次重新翻书 |
| 2 | **全局聚合弱** | "这本书总体讲了什么"无从答起 | 需要 20 个 chunk 才够，top-8 只给你 8 个 |
| 3 | **多跳推理断** | "A 依赖 B，B 依赖 C"跨块断链 | "pv 值→材料配对→辅助冲洗"三步推理 |
| 4 | **矛盾不可见** | 两本书口径打架，各自被检索出来，LLM 随机选一个 | 搅拌功率关联式跨书差异 |
| 5 | **表格公式差** | 表格被切碎、公式变乱码 | 你的书全是参数表、计算式 |
| 6 | **引用不可核** | 答案没有出处锚点 | 没法落"《化工原理》§2.3 #L1157" |
| 7 | **时效/版本盲** | 新版书和旧版书混在一起 | 规范更新后旧参数仍然被检索出来 |

**【判断】** 七条里 1/2/4/6 是 LLM Wiki 明确解决的（compile-once、跨书页、冲突登记、引用锚点）；3/5 需要切块质量与富化；7 需要 status/confidence 字段（v2）。

### 4.6 怎么评估 RAG 好坏：RAGAS 四指标

**【文献】** RAGAS（explodinggradients/ragas）四指标，前三个免金标准，第四个要人工标注：

| 指标 | 问什么 | 说明 |
|:---|:---|:---|
| **faithfulness** 忠实度 | 答案里的每句话是否都能在检索块里找到依据 | 防幻觉 |
| **answer_relevancy** 答案相关性 | 答案是否紧扣问题 | 防跑题 |
| **context_precision** 上下文精度 | 检索块里相关的排得靠不靠前 | 防"对的在第 20 位" |
| **context_recall** 上下文召回 | 该检索到的都检索到了吗 | 需金标准答案 |

### 4.7 什么场景不该用 RAG（五条）

1. **要长期维护的知识**：每次从零拼 = 每次重新付检索税，且无累积 → LLM Wiki。
2. **要跨书综合/对比**：死穴 2/4 → 先建对比页再检索。
3. **资料量小**（你的现状 2.4 MB）：grep + LLM 直接读全文，RAG 是杀鸡用牛刀。
4. **有精确出处要求**：死穴 6 → 需要富化元数据。
5. **频繁更新的规范类资料**：向量库更新滞后，检索出旧值 → 规范页用 wiki 页 + superseded 管理。

### 4.8 生态速查

| 项目 | 一句话 |
|:---|:---|
| [ragflow](https://github.com/infiniflow/ragflow) | 全家桶带 UI，DeepDoc 解析 |
| [llama_index](https://github.com/run-llama/llama_index) | 框架之王，索引器抽象 |
| [haystack](https://github.com/deepset-ai/haystack) | 企业级管道框架 |
| [ragas](https://github.com/explodinggradients/ragas) | 评估 |
| [dspy](https://github.com/stanfordnlp/dspy) | 把提示词当程序编译优化 |
| 解析器五件套 | MinerU（你已有）/ [docling](https://github.com/docling-project/docling) / [marker](https://github.com/VikParuchuri/marker) / [unstructured](https://github.com/Unstructured-IO/unstructured) / [markitdown](https://github.com/microsoft/markitdown) |

### 4.9 RAG 在 300 本书库下的形态与成本（v2 新增）

**【判断】** 300 本书全进向量库 = ~1 万个 chunk（每本 ~35 chunk）→ 嵌入费几百元、索引几个 GB；单问 ¥0.02~0.09（§3.9.3）。技术上完全可行，**但它仍然只有"片段检索"，没有"知识网"**——死穴 1/2/4 一条不少。所以结论不变：

> **RAG 是地基，LLM Wiki 是楼。** 你的库里 RAG 负责"哪本书哪一页"，LLM Wiki 负责"这件事整体是怎么回事"。

---

## 5. GraphRAG：给 RAG 补"全局地图"

### 5.1 出处

**【文献】** Microsoft Research 2024-02, Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*；开源实现 [microsoft/graphrag](https://github.com/microsoft/graphrag)。

要解决的问题一句话：**RAG 只能答"一个片段里写着的事"，答不了"散落在全书、需要拼起来的事"**——比如"这套标准体系的整体演进""这些实验的共同结论"。GraphRAG 的答案是：**入库时把资料抽成实体关系图，再按社区做全局摘要。**

### 5.2 五步索引（入库时发生，这是它贵的原因）

| 步 | 动作 | LLM 调用？ |
|:--|:---|:---|
| 1 | 把文档切成 text units（~600 token） | 否 |
| 2 | 每个 unit 让 LLM 抽实体（人/组织/概念…）和关系 | **是（全量调用）** |
| 3 | 合并全库实体，消歧去重（"泵"与"pump"合一） | 否 |
| 4 | **Leiden 算法**做社区检测，把图切成"话题组团" | 否（【文献】Traag et al. 2019 算法） |
| 5 | 每个社区让 LLM 写一份**社区报告**（摘要+内部关系） | **是（全量调用）** |

查询时（Global 模式）：问题 → 匹配相关社区 → 把多份社区报告 map-reduce 成最终答案。**这就是"全局问答"的来历。**

### 5.3 三种查询模式

| 模式 | 回答什么 | 怎么工作 |
|:---|:---|:---|
| **Global** | "总体上…" | 社区报告汇总（map-reduce） |
| **Local** | "某实体相关…" | 从实体出发在图上找邻居 + 关联原始 text unit |
| **DRIFT** | 混合 | 先 Global 找社区，再 Local 钻细节 |

另有 **LazyGraphRAG**（2024-11）：把最贵的"抽取+社区报告"推迟到查询时才做相关部分，索引成本降到接近纯向量检索——是"预算版 GraphRAG"。

### 5.4 成本：为什么对你先别上

**【估计】** 你的 3 本书：md 文本 ~60 万 token → 切成 ~1000 个 text units → 全量实体抽取 + 社区报告 ≈ **300~800 万 token 的 LLM 调用**（中文实体抽取尤其费）。**比 LLM Wiki 编译同三本书贵 3~8 倍。**
300 本书：**几千元级**（对比 LLM Wiki 几百元级，§3.9.4）。加上图每 3 本书才约 1000 个社区、300 本书的图规模与社区检测质量在中文语料上尚无基准——**性价比目前对你不成立。**

### 5.5 变体与替代品

| 项目 | 特点 | 对你的相关性 |
|:---|:---|:---|
| [LightRAG](https://github.com/HKUDS/LightRAG) | 双级（low/high）检索 + 增量更新；arXiv 2410.05779 | **最现实**：只抽 4 类实体、图谱当"概念路由"用；跨 5 本对比时值得试 |
| [nano-graphrag](https://github.com/gusye1234/nano-graphrag) | 1000 行教学实现 | 学原理用 |
| [graphiti](https://github.com/getzep/graphiti) | bi-temporal（时间双轨）知识图 | 规范更新场景的理论参考 |
| [cognee](https://github.com/topoteretes/cognee) | 会话→图谱记忆 | 相邻 |
| [llm-graph-builder](https://github.com/neo4j-labs/llm-graph-builder) | Neo4j + 可视化 | 想玩图数据库时 |

### 5.6 六个坑（社区共识 + 我的判断）

1. **实体消歧难**：同名不同物、同物不同名（"机械密封"vs"端面密封"vs"机械端面密封"）。
2. **抽取幻觉**：LLM 会编出文档里没有的关系——图谱越密，幻觉越难查。
3. **图更新难**：新书进来要重新消歧、重新社区检测，增量更新是研究级难题（LightRAG 只部分解决）。
4. **社区摘要漂移**：社区报告是 LLM 写的一次性摘要，原始出处锚点被稀释（死穴 6 复现）。
5. **评估难**：没有一个像 RAGAS 那样公认的指标集。
6. **中文弱**：主流图管线的实体识别默认英文，中文工程术语需要换模型+调优。

### 5.7 GraphRAG 与 LLM Wiki 的关系

| | LLM Wiki | GraphRAG |
|:---|:---|:---|
| 知识形态 | **人可读的页面网**（[[链接]]） | 机器图（节点+边+社区报告） |
| 综合单位 | 概念页（一页一个主题） | 社区报告（一团一个话题） |
| 出处锚点 | 逐句可落 §节号/行号 | 稀释 |
| 维护成本 | 低（每次 ingest 改 10~15 页） | 高（全量重建/增量难） |
| 全局问答 | 靠跨书对比页 + index 导航 | 天生擅长 |

**【判断】** 两者其实是同一个思想的两条技术路线：**都在"入库时综合一次"**。差别在综合的载体是"页面"还是"图"。对你这种**要被人反复翻看、逐条核对出处**的工程库，页面网优先；图是锦上添花（v2 也持此立场：图是导航补充，不取代可读 wiki）。

---

## 6. 三者对照、决策树与量化分界线

### 6.1 三方案一张表

| 维度 | grep/全文 | RAG | LLM Wiki | GraphRAG |
|:---|:---|:---|:---|:---|
| 知识生成时间点 | 提问时 | 提问时 | **入库时** | 入库时 |
| 累积性 | 无 | 无 | **有（页面网）** | 有（图+报告） |
| 综合/跨书问题 | 弱 | 弱 | **强（对比页/冲突登记）** | 强（社区报告） |
| 出处可核性 | 强 | 中 | **强** | 弱 |
| 维护成本 | 无 | 低 | 中（靠 LLM 自动） | **高** |
| 建库成本 | 0 | 低 | 中 | **极高** |
| 单问成本 | ¥0.01 | ¥0.02 | ¥0.02 | ¥0.05~0.5 |
| 适合规模 | ≤5 MB | 5~240 MB 片段检索 | **≤240 MB 综合** | 万页级/全局科研问题 |

### 6.2 决策树

```
你的问题是什么类型？
├─ "哪本书哪一页写着 X"（找片段） → 资料小：grep；资料大：RAG
└─ "这件事整体是怎么回事/两本书说法为何不同"（综合）
    └─ 库 ≤ 数百页 → LLM Wiki（index + 页面网）
    └─ 库达万页级、且问题高度全局 → 才考虑 GraphRAG
```

### 6.3 可以叠加：三种"记忆"各管一段

| 记忆类型 | 手段 | 管什么 |
|:---|:---|:---|
| **语义记忆**（知识本体） | LLM Wiki | 概念、口径、参数、结论 |
| **检索记忆**（原文索引） | RAG/grep | 片段定位、原文原话 |
| **关系记忆**（结构导航） | 轻量图谱（v2 类型化链接 / LightRAG） | 谁依赖谁、谁取代谁 |

**三者不是竞品，是三层。** 你最终形态 = LLM Wiki 主干 + grep/index 兜底 + （规模到了再加）轻量图谱。

### 6.4 量化分界线（你问的第 1 题的正解）

**【实测+估计】** 以"md 语料总字节"为判据（图片不参与检索，只按需喂视觉模型）：

| 档位 | md 语料规模 | 对应你的情况 | 检索手段 |
|:---|:---|:---|:---|
| **A 档** | ≤ 5 MB（≤ ~350 万汉字 ≈ 230 万 token） | **你现在（2.43 MB / 53.4 万汉字）** | index.md + grep，**不需要任何向量库** |
| **B 档** | 5~50 MB（≤ 50 本） | 几年后的你 | 全文检索（BM25）+ index 分册；向量可选 |
| **C 档** | 50 MB~数 GB（50~300 本） | **300 本书口径的你（~240 MB）** | **混合检索**：BM25+向量+RRF+LLM 重排（qmd） |
| **D 档** | 万页级、跨学科全局问题 | 远超 300 本 | 再加 GraphRAG/LightRAG 类图谱层 |

**判据要点【判断】**：
1. 分界看**可检索文本量**，不是图片量——图片走"按需喂视觉模型"，不进检索索引。
2. A→B 的界是"index 单文件读不动 + grep 命中太多"（index > 数百页）；C 的界是"BM25 召回噪声大、需要语义兜底"；D 的界是"全局聚合问题成为刚需"。
3. **你现在在 A 档，LLM Wiki 就是 A 档的正解**；300 本书落在 C 档，但 C 档的"向量"部分仍然是地基（RAG），"页面网"部分仍然是楼（LLM Wiki）——两者不互斥。
4. 反过来：**md ≤5 MB 时上 RAG 是浪费**——这正是你现在的状态（2.43 MB），所以"机械密封进了向量库、另外两本没进"这件事，正确的解法不是把两本也塞进向量库，而是**先建 wiki 页**（§9.10）。

### 6.5 升级触发器（到哪一步就升哪一档）

| 触发条件 | 动作 |
|:---|:---|
| `index.md` > 300 行 | 按领域分册（脚本自动） |
| grep 一次命中 > 200 条 | 上 BM25 全文检索（qmd CLI 即可，不需向量） |
| wiki 页 > 200 且模糊问法开始失手 | 上向量 + RRF + 重排（qmd MCP） |
| 跨 5 本对比成为高频需求 | 试 LightRAG 只抽 4 类实体 |
| 万页 + 全局科研问题 | 才考虑完整 GraphRAG |

---

## 7. 最终建议（v3 版：等批准，未动库）

### 7.1 推荐架构一句话

> **LLM Wiki 主干（50-wiki + AGENTS.wiki.md + git）+ grep/index 兜底（现有）+ 轻量图谱链接（v2 字段，不装图数据库）+ 规模到了再上混合检索（qmd）。GraphRAG 暂缓。** 只新增一个"东西"：git。

### 7.2 批准后立刻做三件事（对应 v1 的"三个现在就做"，v2 加了"先等你看完"）

1. **`git init` + GitHub 私有仓库**（§3.11）：一切改动从此可回滚、可审计。没有 git 的 LLM Wiki 是裸奔。
2. **修 86 条死链 + 降级 163 个假标题**（§2.3）：死链修法是 `%20` 解码；假标题降级是脚本活。这两个都是"一次性、机械性"的，**不花 LLM 钱**。
3. **建 `50-wiki\` 七个子目录 + 写 `AGENTS.wiki.md`（附录 C）+ rules.md 升 v3.0**：然后只拿《机械密封》跑 P1 试点（§3.8）。

### 7.3 先别做三件事

1. **别批量造页**：300 本书 × 25 页 = 7500 页，一天造完也是死页。一本书一本书 ingest，让链接自然长出来。
2. **别上向量库**：你现在 A 档（2.43 MB），grep + index 足够（§6.4）。等 `index.md` 分册都撑不住再上 qmd。
3. **别动 rules.md 原有 11 节**：只追加 §12~§15，加工规范继续由 ingest.ps1 族履行；编辑规范交给 AGENTS.wiki.md。

### 7.4 一句话总结

> **你的库是一台很好的印刷机（MinerU 管线），缺的是编辑部（wiki 层 + schema + git）。** 300 本书的目标下，这个编辑部必须现在建——书越多，没有编辑部的问题越疼。

---

## 8. 融合方案：九个方案逐份实读 + 十个来源取长（第三版重写）

> 这一版不是"抄 idea"：九个外部方案（八个仓库 + 一个内置功能）的技术文档我逐份读了一遍（2026-11-16，全部是一手 README / gist 原文 / arXiv 摘要页）。顺序是：先自查 v2 说错的地方（§8.0），再看每个方案"一手事实 + 借什么 + 不借什么"（§8.1），然后试算"照搬现成方案会怎样"（§8.2）、取舍总表（§8.3）、融合架构（§8.4）、比单一方案高级在哪（§8.5），最后给落地顺序（§8.6）。

### 8.0 自查：v2 里被一手文档推翻的 9 处（你让我自己找的"漏洞"）

**这是你留的作业。** 逐份读一手文档后，v2 第 8 章有 9 处事实性错误——不是笔误，是会让选型跑偏的错：

| # | v2 原文（错） | 一手文档事实（2026-11-16 实读） | 为什么要紧 |
|:--|:---|:---|:---|
| **E1** | geronimo-iia/llm-wiki "**19 个 MCP 工具**" | README 首行：**"24 MCP tools. One Rust binary. No LLM inside."** | 低估工具面，就会低估"技能层"的必要性——它自己用 17 个 skill 去驱动这 24 个工具 |
| **E2** | llm-wiki-skills "**8 个 skill**"，名单只有 8 个 | 实为 **17 个**：setup / spaces / config / schema / bootstrap / content / ingest / crystallize / research / lint / graph / frontmatter / configure-hugo / stats / review / export / migrate | 我漏的 7 个（spaces / schema / content / stats / review / export / migrate）恰好是**多空间、schema、导出、评审**——都能等规模化了才需要，但设计时必须预留 |
| **E3** | §3.2 说 geronimo 的综合层是 "**content/（大致）**" | **没有 content/ 目录约定**。综合层 = frontmatter 的 `type:` 字段 + `wiki_content_*` 工具组；目录结构由用户自定 | 它把"页面类型"做成 **schema 字段**而不是目录。这比我 v2 的"五类页面五个目录"更灵活——类型可加，目录不重排 |
| **E4** | qmd 只说"BM25 + 向量 + LLM 重排" | 它自称的 **key feature 是 context 树**：`qmd context add qmd://notes "这批笔记讲什么"`，检索命中时把上下文一并发回——原文理由是 "allows LLMs to make much better contextual choices"。另有 **HyDE**、typed query expansion（lex→BM25 / vec→向量）、SQLite 索引、MCP 五工具、HTTP transport | 漏掉 context 树，就漏掉了它对"LLM 需要上下文而非片段"的正面回答。这正是 LLM Wiki 可以**零成本先实现**的部分（把摘要写进 frontmatter） |
| **E5** | dataview 是"**SQL 式**查询" | README 原文：**DQL 是 "pipeline-based, vaguely SQL-looking"**；另三种模式是 Inline Expressions、**DataviewJS**、Inline JS；数据源 = frontmatter YAML + inline fields（`Key:: Value`） | 说"SQL"会被拿去当 SQL 写，一写就报错。DQL 是管道；最强的是 DataviewJS |
| **E6** | A-MEM"最接近的学术对应物" | 它是 **agent 对话/任务历史记忆系统**（Zettelkasten 式原子记忆 + 结构化属性 + 记忆演化），**不是文件型知识库**；代码在 A-mem（评估）与 A-mem-sys | 拿它当"知识库论文"会误判可迁移性。只能借三条设计：原子化、结构化属性、演化触发 |
| **E7** | 价格表里**没有 DeepSeek 官方视觉价** | DeepSeek 官方 `deepseek-flash` **带 Vision ✓**、1M 上下文；off-peak 输入 $0.15/M、输出 $0.6/M（cache-hit 仅 $0.003/M），peak 翻倍 | 这正是你这次点名的口径；也是"一把 key 走完文本+图"的最省事方案。详见 §3.9.1、§9.2 |
| **E8** | 表里把 "**Obsidian graph view + MCP**" 当成一个"方案/仓库" | graph view 是 **Obsidian 内置功能**，不是仓库。文档在 help.obsidian.md（我 fetch `help.obsidian.md/plugins/graph` 时被 301 到 obsidian.md 且未自动跟随——半个失败，已用 Karpathy 原文佐证其角色） | "十个来源"里它只能算**功能**，不能算**项目**；否则数字虚高 |
| **E9** | qmd 只有一句话 | 实读后它至少值四条：本地 GGUF（node-llama-cpp）**离线**跑嵌入与重排；SQLite 索引；MCP 五工具（query / get / multi_get / status / metadata）；可选**远程度重排**（remote-typesafe，资源界限 2 MiB 请求 / 8 MiB 响应 / 30 s / 64 文档） | 决定"什么时候上 qmd、上它的哪一层"：C 档先 CLI，MCP 留给 agent 直连 |

> **教训**：v2 的错集中在两类——**数量类事实**（19/24、8/17）与**深度类事实**（qmd、dataview、A-MEM 的定位）。写这类文档，凡是"数字 + 声称是它的核心特性"，都必须回一手文档对一遍。

### 8.1 九个方案 × 一手事实 × 我借什么

> 口径：1–9 是外部方案（8 个仓库 + 1 个内置功能），10 是你自己的资产。**每个方案只留一条最值钱的 idea，其余明确不借。**

| # | 来源（一手文档） | 实读到的最硬事实 | 最值钱的 idea（借） | 明确不借 |
|:--|:---|:---|:---|:---|
| 1 | **Karpathy gist**（2026-04，[原文](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)） | 三层（Raw sources / The wiki / The schema）+ 三操作（Ingest / Query / Lint）；原话 "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase"、"The wiki is just a git repo of markdown files"；Query 输出形态包含 markdown 页、对比表、**Marp 幻灯片**、matplotlib 图、canvas；结尾 Note：一切 modular，目录结构自定 | 三层 + 三操作 + `index.md`/`log.md` 双索引 + "LLM 独占写 wiki" | 它的"够用就行"没有工程化：无冲突登记、无生命周期、无版本审计——单靠 gist 走不到 300 本 |
| 2 | **rohitg00 LLM Wiki v2**（~2026-10，[原文](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)） | 基于 agentmemory（20K+ stars）；生命周期 = confidence scoring / supersession / Ebbinghaus 遗忘 / 四层记忆（working→episodic→semantic→procedural）；图谱 = 实体抽取 + **6 类关系**（uses / depends on / contradicts / caused / fixed / supersedes），原话 "The graph doesn't replace the wiki pages. It augments them."；检索 = **三路 RRF**（BM25 + vector + graph traversal）；原话 "don't rely on index.md as the LLM's primary search mechanism past ~100 pages"；事件钩子 6 种；"**The schema is the real product**" | 生命周期三字段（status / confidence / supersedes）+ 关系词 + 事件钩子 + crystallize | 浮点 confidence 与遗忘曲线（无基准、无法验证）；**单机几百到几千文件不需要图数据库** |
| 3 | **geronimo-iia/llm-wiki**（Rust 引擎，[README](https://github.com/geronimo-iia/llm-wiki)） | **24 个 MCP 工具**、单 Rust 二进制、**无内置 LLM**；自称 DKR（Dynamic Knowledge Repository）——"Process sources at ingest time, not query time"；frontmatter 用 **JSON Schema 校验**，`confidence: 0.9` 是浮点，`status: active` 是枚举；从 `sources`/`concepts` 抽 **typed graph edges**（petgraph DiGraph）；tantivy BM25；git2 提交；rmcp（stdio + Streamable HTTP）；还支持 ACP（Zed 编辑器）；`llm-wiki spaces create` + `llm-wiki serve` | ① **frontmatter JSON Schema 校验** ② "引擎是哑管道、智能在技能层" ③ git 快照即审计 | Rust 全家桶（你的管线是 PowerShell + Python）；不引它的二进制，不重写管线 |
| 4 | **geronimo-iia/llm-wiki-skills**（[README](https://github.com/geronimo-iia/llm-wiki-skills)） | 是 **Claude Code plugin**；**17 个 skills**，SKILL.md 遵 agentskills.io 格式（**技能只是 Markdown，谁都能读**）；原话 "**The engine is a dumb pipe. Skills are the brain.**"；工具按 10 组挂：spaces / config / schema / content / search&index / graph / audit / knowledge / resolve / export / migrate | 技能清单当**工作流命名系统**（只借 6 个核心名写进 AGENTS.wiki.md） | 不装 Claude Code 宿主；不引它的 17 个 skill 文件（6 个自己写） |
| 5 | **tobi/qmd**（[README](https://github.com/tobi/qmd)） | npm `@tobilu/qmd`（Node/Bun）；**key feature = context 树**（`qmd context add`，命中附上下文）；typed query expansion（lex→BM25 / vec/hyde→向量）+ 原始 query 双跑 + **RRF** + LLM rerank；本地 node-llama-cpp **GGUF 离线**；SQLite 索引；**MCP 五工具**；可选远程度重排（2 MiB / 8 MiB / 30 s / 64 docs） | ① **context 树**（我用 frontmatter 的 `summary` + `scope` 做零成本等价物）② 检索接口：CLI 与 MCP 双形态，C 档再接 | 现在不装——2.43 MB 语料上收益≈0（§6.4） |
| 6 | **blacksmithgu/obsidian-dataview**（[README](https://github.com/blacksmithgu/obsidian-dataview)） | 四种模式：**DQL**（pipeline-based，类 SQL 但不是 SQL）、Inline Expressions、**DataviewJS**、Inline JS；数据 = frontmatter YAML + `Key:: Value` inline；DataviewJS 能改文件，官方给安全警告 | **"把 frontmatter 当数据库"**：index 表格可由脚本自动生成 | 不装插件、不让插件写文件（我自己用 catalog.ps1 出等价表格） |
| 7 | **marp-team/marp-cli**（[README](https://github.com/marp-team/marp-cli)） | markdown → HTML/CSS/PDF/PPTX/**图片**；npx 即用；PDF/PPTX 需 Chrome / Edge / Firefox；作者 yhatt；MIT | wiki 页 → 汇报幻灯片，零二次排版 | 非汇报场景不装（Karpathy 原文也只把它当输出形态之一） |
| 8 | **A-MEM**（[arXiv 2502.12110](https://arxiv.org/abs/2502.12110)，NeurIPS 2025） | Zettelkasten 式原子记忆 + 结构化属性（contextual description / keywords / tags）+ **新记忆触发旧记忆"演化"**；代码 A-mem（评估）/ A-mem-sys | ① 单页原子化（150 行上限）② "ingest 触发相关页更新" | **它是 agent 对话记忆，不是文件知识库**；不引其检索算法 |
| 9 | **Obsidian graph view + 双向链接**（内置功能，[文档](https://help.obsidian.md/plugins/graph)） | 星图看枢纽/孤儿页；反向链接看"谁引用了我"；**只读文件夹也能看** | 人机共读的可视层 + 孤儿页审计 | 不占"项目"位；不上它的同步/协作 |
| 10 | **你的现有资产**（本机实测） | MinerU 4.1.7 管线（10-source→20-md）；catalog / manifest / todo / issues.log；check-links.ps1；三本中文工程书 2.43 MB / 909 图；`40-new` 里有分页后处理雏形 | 解析底座 + 已有三操作骨架 + 真实规模数据 | — |

### 8.2 照搬现成方案会怎样：三条路线试算

| 路线 | 要装什么 | 能立刻拿到 | 拿不到 / 代价 | 结论 |
|:---|:---|:---|:---|:---|
| **A. 直接装 geronimo 引擎** | Rust 二进制（brew / curl / `irm install.ps1` / cargo）+ 24 个 MCP 工具；17 skills 还要 Claude Code 宿主 | 全文索引、图谱、schema 校验、git 提交、spaces 多空间——开箱即用 | ① 无**中文工程书领域模板**（type 只有通用枚举）② 无成本账、无 `%20` 死链修法、无假标题降级——这三个是你库的特有债 ③ 20-md → 50-wiki 的映射仍要自己写 ④ Windows 要改它的 install 脚本 ⑤ 工具面 24 个，学习成本 > 你现在的需求 | 只借 **schema 校验思路**，不装 |
| **B. 装 qmd + Dataview** | `npm i -g @tobilu/qmd` + Obsidian 插件 | 检索立刻变强；动态表格 | ① 2.43 MB 语料上收益≈0（§6.4 A 档）② 完全没有增加"综合知识"——RAG 的老问题（无累积、矛盾不可见）原样保留 | 等 C 档（>50 MB）再上 |
| **C. 自建融合（本方案）** | PowerShell 三脚本 + git + 一份 `AGENTS.wiki.md` | 领域模板、成本账、你的书适配、编辑契约、300 本升级阈值 | 前期要你亲手盯前 14 页 | ✅ **推荐** |

> **一句话**：现成方案解决的是"通用工具"，你的问题一半是"通用工具 + 你的库特有债务（%20 死链、OCR 假标题、中文工程书结构）"。**工具可以借思想，债务只能自己还。**

### 8.3 取舍总表：借什么、不借什么、什么时候借

| 来源的 idea | 取舍 | 理由 |
|:---|:---|:---|
| 三层 + 三操作 + index/log | ✅ **照抄** | 唯一被社区反复验证的骨架 |
| 生命周期字段（v2） | ✅ **借字段，不借浮点机制** | status / confidence / supersedes 三字段解决"新旧口径并存"；遗忘曲线无基准，先不做 |
| 类型化关系（v2 的 6 类动词） | ✅ **借链接语义，不借图数据库** | 在 wikilink 后写关系词即可（`[[B]]（取代）`）；petgraph/Neo4j 到 D 档再说 |
| 事件钩子（v2） | ✅ **借** | ingest 第 0 步强制查重、写后强制 lint——把"自觉"变"流程" |
| crystallize（v2） | ✅ **借** | 你的计算书/选型过程就是结晶对象，落 `howto\` |
| **JSON Schema 校验 frontmatter**（geronimo） | ✅ **借（用 PowerShell 实现）** | wiki-lint.ps1 第 0 项 = 五类页面必填字段校验，失败即拒收 |
| git 快照即审计（geronimo） | ✅ **借（简化）** | 一个 ingest 一个 commit，无需工具封装 |
| 17 skills 里的 **6 个核心名**（llm-wiki-skills） | ✅ **借名字** | setup / ingest / crystallize / lint / graph / research 写进 AGENTS.wiki.md 章节名 |
| Rust 全家桶（geronimo） | ❌ **不借** | 你的管线是 PowerShell+Python，重写是负资产 |
| tantivy 全文索引（geronimo/qmd） | ⏸ **C 档再借** | 现在 2.43 MB，grep 够（§6.4） |
| BM25+向量+RRF+重排+**context 树**（qmd） | ⏸ **C 档接入** | AGENTS.wiki.md §6 写明"升级到 qmd 时检索流程不变"；context 树先用 frontmatter 摘要替代 |
| Dataview 的"frontmatter 当数据库" | ✅ **借思想** | 用 catalog.ps1 读 frontmatter 自动生成 index 表格；不装插件 |
| marp | ⏸ **需要汇报时再借** | 零成本，wiki 页本身就能喂 marp |
| A-MEM 原子化 + 演化 | ✅ **借两条** | 单页 150 行上限 + "ingest 触发相关页更新" |
| Obsidian 星图 + 反向链接 | ✅ **借** | 只读 vault + 反向链接审计（§3.12） |

### 8.4 融合后的总架构（v3 更新版）

```
【数据流】
10-source(原件) → MinerU解析(+页码锚点 page_idx) → 20-md(全文) → LLM ingest(8步,§3.5) → 50-wiki(页面网) → git commit(每书一个)
                    └─ 一次性欠账：%20 死链解码 / 163 个假 h2 降级 / 图注残片清理

【契约层】(三处校验，缺一不可)
frontmatter JSON Schema(借 geronimo 思路，PowerShell 实现)
  ↳ 必填：type/title/status/confidence/sources/summary/scope/updated
lint 八项(Karpathy 7 项 + v2 冲突项 + geronimo schema 项)
git diff 审计(人机只读约定：改动必须能解释)

【检索流】(按 §6.4 分档升级，接口不变)
A档(≤5MB，现在)：index.md 分类树 → grep 20-md → 命中页
C档(>50MB≈50本)：index → BM25(qmd CLI) → 向量+RRF+重排(qmd MCP) → 命中页 + context 树
兜底：DSH library 向量库(片段级，仅 kb 库现有 836 chunk)

【生命周期】(v2 字段)
status: active|draft|stale|superseded ｜ confidence: high|medium|low ｜ supersedes: [[新页]]
新书推翻旧断言 → 旧页标 superseded 不删 → lint 第 6 项跟踪 → git 留痕

【交付】
人看：Obsidian 星图(只读) + 反向链接 + 脚本生成的 index 表
汇报：marp 幻灯片(按需)
问答：本会话 + DSH 检索注入
```

### 8.5 为什么说这个融合"比任何单一方案更高级"

| 被借鉴方案 | 它的短板（实读后确认） | 融合方案怎么补 |
|:---|:---|:---|
| Karpathy gist | 只有思想没有落地：无生命周期、无冲突登记、无版本审计 | + 你的 MinerU 管线落地 + v2 生命周期字段 + git 每书一 commit |
| rohitg00 v2 | 浮点机制无基准；图谱维护成本高；无中文工程书场景 | 图谱降为链接语义；机制不借；+ 中文书实测数据（%20/假标题/909 图） |
| geronimo-iia/llm-wiki | 通用引擎，**无页面内容模板、无领域字段、无成本核算**；24 工具学习成本高；Windows 安装要改脚本 | + 六类页面模板（附录 B）+ 工程书领域字段 + §3.9 成本账 + 只用它的 schema 思路 |
| llm-wiki-skills | 17 个技能面向 Claude Code 生态；不含你库的任何领域约定 | 只借 6 个名字；约定自己写进 AGENTS.wiki.md |
| tobi/qmd | 纯检索，无知识网、无累积；2.43 MB 上收益≈0 | + 50-wiki 页面网；qmd 只作 C 档配件；context 树先用 frontmatter 实现 |
| Obsidian + Dataview | 是展示层与查询层，不产生知识 | + 综合层（50-wiki）+ 只读审计 |
| A-MEM | agent 记忆系统，无 schema、无 lint、无版本控制 | + AGENTS.wiki.md + lint 八项 + git |
| 普通 RAG | 无累积、矛盾不可见、引用不可核 | + compile-once、openq 冲突登记、§节号/行号锚点 |
| GraphRAG | 贵 3~8 倍、出处稀释、增量更新难 | 暂不做；预留 LightRAG 升级位（§6.5） |

**一句话**：单一方案都只解决"读 / 查 / 记"中的一段；融合方案把 **读（MinerU）、记（50-wiki + v2 生命周期）、查（index→qmd 分级）、核（schema + lint + git）、看（Obsidian）** 串成闭环，且每一步都有"300 本书口径"的成本与升级阈值——**这套东西没有任何一个现成仓库同时提供**。

### 8.6 落地：每个阶段拿哪几件零件

| 阶段 | 拿哪些零件（来源） | 产出 | 工时 |
|:---|:---|:---|:---|
| **P0** | 三层+三操作（Karpathy）、6 个技能名（skills 17 里挑）、schema 校验思路（geronimo）、事件钩子（v2） | `git init` + `.gitignore`；`90-tool\AGENTS.wiki.md`（8 节）；`50-wiki\` 骨架；`wiki-lint.ps1` 骨架 | 0.5~1 h |
| **P1** | 六类模板（附录 B）+ 生命周期字段（v2）+ JSON Schema 校验（geronimo 思路） | 机械密封一本 → 12 页；lint 八项跑通；log 三字段（action/token/文件） | 1 会话 |
| **P2** | 原子化 150 行 + 演化触发（A-MEM 两条）+ 冲突登记（openq 模板） | 化工原理（先修 %20 + 降假标题）与气液搅拌釜入库；跨书 3 页；glossary 30 条 | 2 会话 |
| **P3** | frontmatter 当数据库（Dataview 思想）+ git 快照（geronimo 简化） | index 自动生成（catalog.ps1 扩展）；lint 全过；每书一 commit | 1 会话 |
| **P4** | context 树 + RRF（qmd），marp（汇报） | index 分册；C 档接 qmd；汇报幻灯片按需 | 规模化后 |

> 读到这里，你可以拍板的三件事（§7.2 同）：**① `git init` + GitHub 私有仓库；② 修 86 条死链 + 降 163 个假标题；③ 建 `50-wiki\` + `AGENTS.wiki.md`，先用机械密封试点。** 这三件之外，本版没有动你库里任何文件。

---

## 9. 你的问题，逐条回答

### 9.1 向量检索分界线：多少字/MB 以下用 LLM Wiki、以上用 RAG

**先纠正一个隐含预设【判断】**：LLM Wiki 和 RAG **不是二选一**。LLM Wiki 解决"综合知识"，RAG/向量解决"片段检索"，规模大了两者共存（§6.3）。真正要分界的是**"什么时候需要向量检索"**：

| 判据（实测） | 值 |
|:---|:---|
| 你现在的 md 总量 | **2,430 KB ≈ 2.43 MB ≈ 160 万字符 ≈ 53.4 万汉字 ≈ 35 万 token**（§2.2 实测） |
| 分界线 | **≤ 5 MB：不需要向量检索**（index+grep 足够）；5~50 MB：全文检索（BM25）；> 50 MB（~50 本以上）：上向量+混合检索 |
| 300 本书 | ~240 MB → 落在"混合检索"档 |

**所以对你**：现在 → LLM Wiki + grep，**不要向量库**；300 本 → LLM Wiki + 混合检索（qmd）。详见 §6.4。

### 9.2 单本入库到底多少钱（deepseek-flash 口径，不扯九万张图）

**直接答**：一本《化工原理》从现成 md 编成 wiki，用 **deepseek-flash**（带 Vision、1M 上下文）：

| 口径 | 一本多少钱（off-peak） | 算法 |
|:---|---:|:---|
| ① 只文本、不喂图 | **≈ ¥0.44** | 35 万 in × ¥1.08/M + 1.5 万 out × ¥4.32/M |
| **② 按需喂 30 张图（推荐）** | **≈ ¥0.51** | ① + 3.6 万 in × 1.08 + 0.6 万 out × 4.32 = +¥0.065 |
| ③ 全量 400 张图（不推荐） | ≈ ¥1.31 | ① + 48 万 in × 1.08 + 8 万 out × 4.32 = +¥0.86 |
| peak 时段（①②③ ×2） | ¥0.89 / ¥1.01 / ¥2.61 | peak = UTC 周一至五 01:00-04:00、06:00-10:00 |

**价格锚**（[DeepSeek 官方](https://api-docs.deepseek.com/quick_start/pricing)，2026-11-16，$1≈¥7.2）：deepseek-flash 输入 cache-miss **$0.15/M**（peak $0.30）、cache-hit $0.003/M、输出 **$0.6/M**（peak $1.2）。**带 Vision ✓**——文本与图共用一把 key，不用第二家。

**为什么 v2 的 ¥0.8~5.2 偏高**：v2 用的是"DeepSeek 系 2 元/M in、8 元/M out"的历史锚，比官方 flash 现价贵约 2 倍（输入）/近 2 倍（输出）。换成官方价后：**单本 off-peak ≈ 五毛，peak ≈ 一块。**

**300 本总账**：文本 300×¥0.44 + 图 300×¥0.065 ≈ **¥150（off-peak）/¥300（peak）**。GraphRAG 同语料索引高 3~8 倍（§5.4）。

**单次提问**（§3.9.3）：LLM Wiki ≈ RAG ≈ **¥0.01/问**；GraphRAG Global ≈ **¥0.03~0.06/问**。各方案输入 token 见 §3.9.3 表。

### 9.3 LLM Wiki v2 是谁、什么时候、提升什么

- **作者**：Rohit Ghumare（GitHub `rohitg00`），gist 标题 *"LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory"*。
- **时间**：约 **2026-10**（gist 最近活跃 2026-10-08）。
- **四大提升**：① 知识生命周期（confidence/supersession/遗忘/四层记忆）；② 类型化图谱（实体带类型、关系带语义）；③ 混合检索 RRF + 事件钩子 + crystallize；④ 多代理协作、隐私审计、任务化输出。
- **注意**：其中浮点置信度、遗忘曲线等 v2 自己标注为"待评估"；v2 是**扩展不是替代**，主张按规模逐步加装。全文见 §1.9。

### 9.4 "无 lint 就腐化"和"ingest"到底什么意思

- **ingest = 入库编译**：把一份新资料读进 wiki 的动作。不是"把文件拷进去"，而是"读原文 → 写摘要页 → 更新 10~15 个相关页 → 更新 index → 记 log"（§1.5）。
- **无 lint 就腐化**：每次 ingest 都改动十几个文件，没有定期体检（死链/孤儿页/过期断言/矛盾/无来源页），错误会**复利堆积**，20 次入库后没人敢信这个 wiki。lint 就是体检，你的 `todo.md` 是文件层体检，缺的是知识层体检（§3.5 lint 八项）。

### 9.5 按 300 本书重设预设：哪些设计因此变了

全文已按 300 本口径重写，关键变化（详见 §2.6）：index 必须分册；提问先 grep index 再按类读子索引；glossary 按领域拆；**图片一律按需喂**（9 万张全喂排队太慢，不是贵）；20-md 图片不进 GitHub；lint 挂进 ingest 自动跑；Obsidian 星图按领域限定视图。

### 9.6 融合方案在哪看

第 8 章整章。三句话版：**骨架照抄 Karpathy（三层+三操作），字段借 v2（status/confidence/supersedes），工程化借 geronimo（JSON Schema 校验+git 快照），检索接口预留 qmd（BM25+向量+重排），可视化借 Obsidian（星图+Dataview），比任何单一方案多的是：你的 MinerU 中文工程书底座 + 五类页面模板 + 成本账 + 300 本升级阈值。**

### 9.7 MinerU 能不能一直开 OCR？能不能"不图片"？86 条死链怎么办

- **能强制 OCR**：CLI `--method ocr`（默认 `auto`；API 是 `enable_ocr`；Gradio 勾 `is_ocr`）。但**开关是文档级**，不能按页混合——扫描书和原生文字层书要用不同配置。
- **但强制 OCR 不能让你"不图片"**：MinerU 的图块裁剪来自**版面分析**（识别 figure 区域），与 OCR（识别文字）是两条独立流水线。开 OCR 只会让文字层更干净，图照样被裁出来存进 `图片\`。想少图只能靠按需喂视觉模型（§3.5）。
- **86 条死链已查清**：不是图丢了，是 md 内链接带 `%20` 等 URL 编码，磁盘文件名是真空格（`图1.3%20U形管…jpg` vs `图1.3 U形管…jpg`）。**修法 = 链接做 URL 解码**（check-links.ps1 加一行，或批量替换）。另有十余个 `_a.jpg` 图注残片属真垃圾，需重解析对应页或改名（§2.3 问题 1）。

### 9.8 分页标记（`<!-- page: N -->`）能在解析阶段加吗

- **能，且 MinerU 已经给了原料**：MinerU 输出 `middle.json` 里每个块带 `page_idx`——只是你的 ingest.ps1 没有把它写成锚点。**最佳落点 = ingest.ps1 的后处理**：按 `page_idx` 在行间插入 `<!-- page: N -->`，以后引用 = `#L行号` + `页码` 双轨。
- **不用重解析全库**：MinerU 支持只输出 middle.json（`--output` 选中间产物），你甚至可以只重跑"中间产物"这一步；`40-new\` 里已有 `_append_page_appendix.py` 与 figures-report JSON 的雏形，说明这条路你走过一半。
- 详细方案见 §3.7 的 `md-anchor.ps1`。**新书从 P1 之后起，解析默认带锚点；三本旧书用脚本补。**

### 9.9 git 怎么存，本地和 GitHub 都同步

§3.11 完整命令。要点：根目录 `git init`；`.gitignore` 排除 `10-source\`、`.stfolder\`、lint 报告；GitHub 建**私有**仓库（版权材料）；每本书 ingest 一个 commit（message 带 `touch=N`）；图片 3 本时直接推，300 本后切 Git LFS；Syncthing 的 `.stignore` 加 `.git` 防打架；单写者策略（只本机编辑，GitHub 纯备份）。

### 9.10 建立 LLM Wiki 是否顺带解决"检索能力不均"

**部分解决，且是正确方向的解决。**
- LLM Wiki 解决的是**知识层不均**：化工原理的概念会变成 wiki 页，不再"只能 grep 原文"。以后问"搅拌功率怎么算"，读的是 wiki 页（跨书综合），不是翻某本书的 chunk。
- 但它**不解决片段级检索不均**：要引用原文原话（"§2.3 公式原文"）仍要 grep 或向量库。正确顺序是：**先建 wiki（现在），规模到 B/C 档再统一上混合检索**——而不是现在就把两本书塞进 kb 向量库。因为你现在只有 2.43 MB，A 档的 grep 完全够（§6.4）。

### 9.11 目录/文件名：用 Karpathy 的还是 GitHub 项目的

**混合**（§3.2 全表）：目录层 = 你的数字编号（50-wiki）+ Karpathy 的 `wiki` 语义；文件层 = Karpathy 通用名（`index.md`/`log.md`/`AGENTS.wiki.md`）；技能名从 geronimo 的 17 个里挑 6 个（setup/ingest/crystallize/lint/graph/research）。理由：**Karpathy 的名字是"模式语言"，GitHub 项目名是"实现名字"——模式比实现稳定。** 通用可辨认 = 任何人看到 `50-wiki\index.md + log.md + AGENTS.wiki.md` 立刻知道这是 LLM Wiki 模式落地。

### 9.12 `50-` 前缀为什么？能不能用 a/b/c/d

- **是，首要目的就是排序**：00→10→20→30→40→90 是数据流顺序（进料→原件→解析→索引→草稿→工具），wiki 在数据流里排第 6 站，所以用**空号 50** 插进去，不动任何现有路径。
- **数字优于字母**：数字表达"流程顺序"，字母没有语义（a-wiki 排在 z-tool 前会撒谎）。且你的 README/脚本已写死数字约定，改字母要动一串引用。
- **当然可以用任何名字**（`05-wiki`、`wiki` 都行），但建议保留"数字前缀 + wiki"这个组合，理由如上。

### 9.13 Obsidian 星图 + 人机同步怎么落地

§3.12 完整方案。要点：
- **星图不用 MCP 建**：它是 Obsidian 客户端按 `[[wikilink]]` 渲染的。你只需"打开文件夹为库"指向 `D:\Shervon_KnowledgeBase`（当前 MCP 连的 Obsidian 库只有 4 个文件，不是你的知识库——已实测）。
- **人机同步 = 约定 + git 审计**：AGENTS.wiki.md §0 写"人对 Obsidian 只读"；每次会话开始跑 `git status --short`，有未提交改动就逐文件汇报给你"你改了 X，吸收还是还原？"——这就是你要的"改了要报告"。

### 9.14 你同意的"先看融合方案"——方案在第 8 章，这里再给结论

看完第 8 章如果你认可，需要你拍板的只有三件事（§7.2）：**git init + GitHub 私有仓库；修死链+降假标题；建 50-wiki + AGENTS.wiki.md + 机械密封试点。** 拍板后我再动，不拍板就一直停在"文档状态"。

### 9.15 诚实声明：本版（v2）我改了什么、没改什么

| 项 | 状态 |
|:---|:---|
| 这份 `.md` 文档 | ✅ 唯一改动：从 v1（1131 行）重写为 v2 全文 |
| 知识库其他任何文件/目录 | ❌ **未动一字节**（按你的要求） |
| git init / GitHub 仓库 | ❌ 未执行 |
| 建 `50-wiki\` / 改 rules.md / README / VERSION | ❌ 未执行 |
| 修 86 条死链 / 降级假标题 | ❌ 未执行 |
| 安装任何工具 | ❌ 未安装 |
| 文档内数字 | 【实测】标实测（本机命令）；【文献】标来源+日期；价格是 2026-11-16 公开页核对，**下单前以官网当日价为准** |

---

## 附录 A：专业术语全表（小白版，按字母排）

| 术语 | 全称 | 中文 | 一句话 |
|:---|:---|:---|:---|
| agent | — | 智能体 | 能自己调用工具完成多步任务的 AI 程序；本方案里的"LLM"多指它 |
| API | Application Programming Interface | 应用编程接口 | 程序之间对接的"插座"；MinerU 有 CLI 也有 API |
| append-only | — | 只追加 | 日志只许往后加、不许改旧行；log.md 的规则 |
| backlink | — | 反向链接 | "谁链向了我"；Obsidian 查反向链接能发现孤儿页 |
| BM25 | Best Matching 25 | 关键词检索算法 | 按词频+稀有度打分，找"词面相符"；免费、可解释 |
| chunk | — | 文本块 | 长文切成的 512~1024 token 小段，RAG 的检索单位 |
| CLI | Command Line Interface | 命令行接口 | 在终端敲命令用程序，如 `mineru --method ocr` |
| commit | — | 提交 | git 的一次存档，带说明（message）；回滚的最小单位 |
| community detection | — | 社区检测 | 把图切成"联系更紧密的组团"；GraphRAG 用 Leiden 算法 |
| confidence | — | 置信度 | 页面/断言的可信等级 high/medium/low（v2 字段） |
| context window | — | 上下文窗口 | LLM 一次能"看见"的最大 token 量；中文 1 字≈0.67 token |
| crystallize | — | 结晶 | 把一次有价值的问答/分析固化成 wiki 页（v2 概念） |
| Dataview | — | Obsidian 插件 | 把 frontmatter 当数据库查询，自动生成表格 |
| embedding | — | 嵌入/向量化 | 把文字变成一串数字（向量），语义近的数字也近 |
| entity | — | 实体 | 图里的节点：设备/零件/标准/材料/概念 |
| frontmatter | — | 文件头元数据 | md 开头 `---` 包住的字段块（type/title/sources…），机器可解析 |
| gist | GitHub Gist | — | GitHub 的单文件分享页；Karpathy 和 v2 的"论文"都发在这，**不是仓库** |
| git | — | — | 版本控制工具：记录每次改动、可回滚到任意历史 |
| graph view | — | 星图 | Obsidian 把 [[链接]] 画成节点连线图 |
| ingest | — | 入库编译 | 读新资料→写页→更新 10~15 页→更新 index/log（§1.5） |
| JSON Schema | — | JSON 校验规范 | 声明"字段该长什么样"，机器据此验 frontmatter（geronimo 的杀招） |
| Leiden | — | 莱顿算法 | 社区检测算法（Traag et al. 2019），GraphRAG 用它切社区 |
| lint | — | 体检/静态检查 | 定期查 wiki 健康：死链/孤儿/过期/矛盾/无来源（§3.5 八项） |
| LLM | Large Language Model | 大语言模型 | ChatGPT/DeepSeek 这类模型本身 |
| log.md | — | 时间线文件 | append-only 记录，前缀 `## [日期] 动作 | 标题` |
| map-reduce | — | 映射-归约 | 把大任务拆小分别处理再汇总；GraphRAG Global 的问答方式 |
| marp | — | — | markdown 直接出幻灯片的工具 |
| MCP | Model Context Protocol | 模型上下文协议 | agent 插工具的标准接口；Obsidian/qmd/llm-wiki 都靠它接进 agent |
| middle.json | — | MinerU 中间产物 | 含每个块的 page_idx（页码），页码锚点的原料 |
| OCR | Optical Character Recognition | 光学字符识别 | 把图片里的文字认成文本；扫描版 PDF 全靠它 |
| orphan page | — | 孤儿页 | 没有任何页面链向它的页；lint 第 2 项 |
| page anchor | — | 页码锚点 | `<!-- page: N -->` 标记，让引用能落到"第几页" |
| page_idx | — | 页索引 | middle.json 里每个块所属的 PDF 页码 |
| petgraph | — | Rust 图库 | geronimo 用来存图谱的库；我们暂不借 |
| raw | — | 原件层 | 不可变的第一层（你的 10-source） |
| repo | repository | 仓库 | 一个 git 项目（本地文件夹 + 可选 GitHub 云端） |
| rerank | — | 重排 | 召回一堆候选后用更精的模型重排，最划算的单点提升 |
| RRF | Reciprocal Rank Fusion | 倒数排名融合 | 把多路检索按"排名倒数和"合并（Cormack 2009，常用 k=60） |
| schema | — | 契约层 | 教 LLM 怎么维护 wiki 的规则文件（AGENTS.wiki.md） |
| status | — | 页面状态 | active/draft/stale/superseded（v2 字段） |
| supersedes | — | 取代关系 | "新页取代旧页"；旧页保留标过时，不删 |
| tantivy | — | Rust 全文检索库 | geronimo/qmd 的 BM25 引擎；我们 B/C 档才借 |
| text unit | — | 文本单元 | GraphRAG 的切块单位（~600 token） |
| token | — | 词元 | LLM 计费单位；中文 1.5 字≈1 token |
| vault | — | Obsidian 库 | 一个 Obsidian 文件夹，打开就能当笔记库用 |
| wikilink | — | 双链 | `[[页面名]]` 语法，星图和反向链接都靠它 |
| YAML | YAML Ain't Markup Language | 数据序列化格式 | frontmatter 用的格式，`key: value` 写法 |

---

## 附录 B：五类页面模板（含 300 本口径的前置字段）

**所有页共用的 frontmatter**（geronimo 式 JSON Schema 校验的就是它）：

```yaml
---
type: concept | entity | source | comparison | howto | openq
title: 页面名（唯一，进 glossary）
aliases: [别名1, 别名2]      # 唯一译名的"曾用名"
domain: 密封 | 搅拌 | 传热 | …   # 领域，分册 index 用
status: active | draft | stale | superseded
confidence: high | medium | low
sources:                      # 断言来源，G6 验收
  - book: 机械密封结构图例及应用
    section: "§1.2"
    lines: "123-456"          # 有页码锚点后写页码
  - book: 化工原理
    section: "§2.3"
    lines: "L890-912"
related: [[相关页1]], [[相关页2]]
supersedes: [[被取代的旧页]]   # 有才写
updated: 2026-11-16
---
```

**1. concept（概念页，主力 60%）** 小节顺序：定义 → 机理 → 计算与口径 → 参数范围 → 适用边界 → 图（每图一句转述）→ 争议与未决（有冲突就开 openq）。
**2. entity（实体页）** 小节：型号谱系 → 结构与零件 → 参数表 → 适用工况 → 失效模式 → 选型要点。
**3. source（单本书页）** 小节：元信息（表）→ 章节地图（真标题+行号）→ **这本书能回答什么/不能回答什么** → 图清单（链接+一句转述）。
**4. comparison（对比页）** 开头放四选勾：☐ 口径不同 ☐ 参数不同 ☐ 结论相反 ☐ 适用条件不同；中间放对比表；结尾放处理建议（指向 howto/openq）。
**5. howto（做法页，crystallize 落点）** 小节：适用条件 → 步骤（每步标依据页）→ 算例 → 已知坑。
**6. openq（未决页）** 小节：现象 → 出处 A / 出处 B（各带 §节号）→ 差异性质（勾选）→ 处理建议 → status。

---

## 附录 C：`90-tool\AGENTS.wiki.md` 骨架（8 节，人写的契约）

```markdown
# AGENTS.wiki.md —— 本库 wiki 层的编辑契约（schema）

## 0. 写者边界
- 10-source、20-md：只读。20-md 由 ingest.ps1 独占，重解析不得波及 50-wiki。
- 50-wiki：仅 LLM（本契约执行者）可写；人在 Obsidian 中只读（改动以 git 审计发现）。
- 30-index：仅脚本可写。
- 新增 50-wiki 子目录前必须先改本文件。

## 1. 唯一译名（对应 glossary.md）
- 每个概念只有一个正名；ingest 第 0 步先查 glossary 与 concepts 是否已有同义页。
- 有则改，无则建；别名进 aliases。

## 2. 断言必须有来源
- 任何事实断言必须落在 sources[book, section, lines]。
- 无来源的断言不得进入 wiki 页，只能进 openq。

## 3. 页面硬约束
- 单页 ≤150 行，超了拆页并留"→ 已拆至 [[X]]"。
- 每页必须被 ≥2 处其他页链接，否则合并或删除。
- 图引用必须附 ≥1 句文字转述；转述不出则走视觉模型流程并记 log。

## 4. 冲突与换代
- 新信息推翻旧断言：旧页标 status: superseded、supersedes 指向新页，不删旧断言。
- 两源并存矛盾：开 openq 页，不擅自二选一。

## 5. Ingest 八步（§3.5 为执行标准）
0 查重 → 1 章节地图（降假标题）→ 2 写 source 页 → 3 建/改概念页 → 4 转述图 → 5 回改受影响页（冲突开 openq）→ 6 更新 index → 7 追加 log（记 token 与成本）→ 8 lint 自检 + git commit。

## 6. Query 四步（§3.5）
grep index → 读 ≤10 候选页 → 回答带 §节号/行号 → 判断回填（crystallize）并登记 index。

## 7. Lint 八项（§3.5 表）
死链 / 孤儿页 / 无来源 / 超长页 / 同义重复 / 过期断言 / index 漂移 / 图无转述。

## 8. 禁止
- 禁止把 wiki 内容写进 20-md 或 10-source。
- 禁止编造来源、编造页码、编造参数。
- 禁止跳过查重直接建页。
- 禁止改 30-index 的生成物（改生成脚本，不改成品）。
```

---

## 附录 D：验收清单（P0–P4）

| 阶段 | 验收项 | 判据 |
|:---|:---|:---|
| P0 | git 就绪 | `git log --oneline` ≥1；`.gitignore` 含 10-source、.stfolder |
| P0 | GitHub 同步 | 远程私有仓库有首个 push |
| P0 | schema 就绪 | AGENTS.wiki.md ≥100 行；rules.md 有 §12~§15 且 VERSION=3.0 |
| P0 | 目录就绪 | 50-wiki 七个子路径存在 |
| P1 | 试点完成 | 机械密封 source 页 + ≥7 概念/实体页；ingest 触及 10~15 页；死链 0 |
| P2 | 三本铺开 | 14 页齐（§3.6）；跨书引用 ≥3；openq 冲突 ≥3；glossary ≥30 条 |
| P2 | 死链清零 | check-links 全库 0（%20 已解码） |
| P2 | 假标题降级 | 机械密封 163 个假 h2 已降级（脚本报告） |
| P3 | lint 全过 | 八项检查全过（`50-wiki\_lint.md` 无未决项） |
| P3 | 引用可核 | 抽 10 条断言，10/10 有 §节号或行号 |
| P4 | 规模自动化 | lint 随 ingest 自动跑；index 自动分册；10 本书一次全量体检 |

---

## 附录 E：资源清单（按用途分组，GitHub 链接，2026-11 检索）

**1. LLM Wiki 思想与实现**
- Karpathy 原始 gist（2026-04）：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- LLM Wiki v2（rohitg00，~2026-10）：https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
- geronimo-iia/llm-wiki（Rust 引擎，**24 个 MCP 工具**，无内置 LLM，MIT OR Apache-2.0）：https://github.com/geronimo-iia/llm-wiki
- geronimo-iia/llm-wiki-skills（**17 个 skills**，Claude Code plugin）：https://github.com/geronimo-iia/llm-wiki-skills
- geronimo-iia/agent-skills（扩展技能：wiki-ingest-pdf / research-paper / kb-conventions）：https://github.com/geronimo-iia/agent-skills
- geronimo-iia/llm-wiki-hugo-cms（网站化）：https://github.com/geronimo-iia/llm-wiki-hugo-cms
- lucasastorian/llmwiki：https://github.com/lucasastorian/llmwiki
- basicmachines-co/basic-memory（Markdown 知识库 MCP）：https://github.com/basicmachines-co/basic-memory
- A-MEM（arXiv 2502.12110，NeurIPS 2025；**agent 记忆系统，非文件知识库**）：https://arxiv.org/abs/2502.12110 ｜ 代码：https://github.com/WujiangXu/A-mem ｜ https://github.com/WujiangXu/A-mem-sys
- Obsidian graph view（**内置功能，不是仓库**）：https://help.obsidian.md/plugins/graph

**2. 检索与可视化**
- tobi/qmd（BM25+向量+重排，CLI+MCP）：https://github.com/tobi/qmd
- blacksmithgu/obsidian-dataview：https://github.com/blacksmithgu/obsidian-dataview
- marp-team/marp-cli：https://github.com/marp-team/marp-cli
- logseq/logseq：https://github.com/logseq/logseq
- silverbulletmd/silverbullet：https://github.com/silverbulletmd/silverbullet

**3. 文档解析（你的 MinerU 已在本地 C:\Users\shervon\.local\mineru，4.1.7）**
- opendatalab/MinerU：https://github.com/opendatalab/MinerU
- docling-project/docling：https://github.com/docling-project/docling
- VikParuchuri/marker：https://github.com/VikParuchuri/marker
- Unstructured-IO/unstructured：https://github.com/Unstructured-IO/unstructured
- microsoft/markitdown：https://github.com/microsoft/markitdown

**4. RAG 框架与评估**
- infiniflow/ragflow：https://github.com/infiniflow/ragflow
- run-llama/llama_index：https://github.com/run-llama/llama_index
- deepset-ai/haystack：https://github.com/deepset-ai/haystack
- explodinggradients/ragas：https://github.com/explodinggradients/ragas
- stanfordnlp/dspy：https://github.com/stanfordnlp/dspy

**5. GraphRAG 与图谱**
- microsoft/graphrag：https://github.com/microsoft/graphrag
- HKUDS/LightRAG（arXiv 2410.05779）：https://github.com/HKUDS/LightRAG
- gusye1234/nano-graphrag：https://github.com/gusye1234/nano-graphrag
- getzep/graphiti：https://github.com/getzep/graphiti
- topoteretes/cognee：https://github.com/topoteretes/cognee
- neo4j-labs/llm-graph-builder：https://github.com/neo4j-labs/llm-graph-builder

**6. Agent 记忆（相邻参考）**
- letta-ai/letta：https://github.com/letta-ai/letta
- mem0ai/mem0：https://github.com/mem0ai/mem0
- khoj-ai/khoj：https://github.com/khoj-ai/khoj

---

## 附录 F：价格与成本计算器（口径 + 示例）

**通用换算【估计】**
- 中文文本：1 字 ≈ 0.67 token（1.5 字 = 1 token）；1 汉字 ≈ 3 字节。
- 一张图 ≈ 1200 视觉 token；图转述输出 ≈ 200 token/图。
- 一本 400 页工程书 ≈ 800 KB md ≈ 27 万汉字 ≈ 18 万 token；分块重读 ×1.5 ≈ 27 万 in。

**入库成本公式**

```
一本书入库费 = 文本in × 文本价 + 文本out × 文本价 + 喂图数 × (1200 × 视觉in价 + 200 × 视觉out价)
```

**价目常量（deepseek-flash，官方价 2026-11-16，$1≈¥7.2）**
- off-peak：输入 cache-miss **¥1.08/M**（$0.15）、cache-hit ¥0.022/M、输出 **¥4.32/M**（$0.6）。
- peak（UTC 周一至五 01:00-04:00、06:00-10:00）：输入 ¥2.16/M、输出 ¥8.64/M。
- 带 Vision ✓：图与文本同价目，无需第二家模型。

**入库成本公式**

```
一本书入库费 = 文本in × 输入价 + 文本out × 输出价
              + 喂图数 × (1200 × 输入价 + 200 × 输出价) / 10^6
```

**示例：化工原理（文本 35 万 in / 1.5 万 out；每张图 1200 in / 200 out）**

| 口径 | 图费 | 文本费 | 合计（off-peak） | peak |
|:---|:---|---:|---:|---:|
| 只文本 | ¥0 | ¥0.443 | **¥0.44** | ¥0.89 |
| 按需 30 图（推荐） | ¥0.065 | ¥0.443 | **¥0.51** | ¥1.01 |
| 全量 400 图 | ¥0.864 | ¥0.443 | **¥1.31** | ¥2.62 |

**单次提问成本公式**

```
单问费 = 输入token × 输入价 + 输出token × 输出价
```

| 方案 | 输入 | 输出 | off-peak | peak |
|:---|---:|---:|---:|---:|
| grep | 2K | 1K | ¥0.006 | ¥0.012 |
| LLM Wiki / RAG | 5K | 1K | ¥0.010 | ¥0.020 |
| GraphRAG Local | 8K | 1K | ¥0.013 | ¥0.026 |
| GraphRAG Global | 2~5 万 | 1K | ¥0.025~0.06 | ¥0.05~0.12 |

**300 本书总账【估计】**：编译 300 本（文本 + 按需 30 图/本）≈ **¥153（off-peak）/¥305（peak）**；GraphRAG 全量索引同语料 ≈ **几千元**。全部价格以 2026-11-16 公开页为据（§3.9.1），下单前以官网当日价为准。

---

> 全文完（v3.0）。本版新增：§8.0 自查（v2 里说错的 9 处）、§8.2 三条路线试算、§9.2 单本入库账（deepseek-flash 口径）。下一步等你的三个拍板：git 私有仓库、死链+假标题清理、建 `50-wiki\` 并先用机械密封试点。

---

# 第二部分 落地执行方案（P0–P4）

> 状态：**待你确认**。确认前不动库。
> 依据：`LLM-Wiki_RAG_GraphRAG_全解与本库改造方案.md`（v3，1420 行）第 3 章与附录 B/C/D/F，其中 §3.1–3.8、§3.9、§3.11、§3.12 为本方案直接引用的原文。
> 版本：v1.0｜2026-11-16｜作者：agent（lead）

---

## 0. 范围与基线

### 0.1 本方案是什么

一句话：**把你现在的"解析 + 索引"流水线，升级成 Karpathy 三层 LLM Wiki（raw → wiki → schema），全部动作拆成 P0–P4 五段，每段有命令、有产出、有验收、有坑与改法，并说清人机分工。**

### 0.2 剔除清单（主文档里的内容哪些不进本方案）

| 主文档章节 | 内容 | 本方案处理 |
|:---|:---|:---|
| 第 1 章 | LLM Wiki 是什么、出处、演进（科普） | 剔除，只保留执行所需的字段名/文件名 |
| 第 2 章 | 现状实测与差距 G1–G8 | 只保留"现状基线表"（§0.4），论证过程剔除 |
| 第 4 章 RAG | 九段流水线、参数、RAGAS、生态 | **整章剔除** |
| 第 5 章 GraphRAG | 五步索引、查询模式、变体 | **整章剔除** |
| 第 6 章 | 三方案对比、决策树、分界线 | 只保留 §6.4 升级阈值表（规模演进要用） |
| 第 9 章 Q&A | 15 条问答 | 剔除（答案已在主文档） |
| 第 8 章融合方案 | 九个方案的取舍论证 | 只保留 §8.6"每个阶段拿哪几件零件"（§5 资源映射） |

### 0.3 执行红线

1. **本方案确认前**：不改库内任何文件、不建目录、不装软件、不跑 git。现在唯一的库改动就是本文件本身。
2. **每阶段结束即停**：P0 做完等你验收，再进 P1；不连跑。
3. **20-md 的一次性修补**（死链解码、假标题降级）是明确列出的例外，且每处都要先 dry-run 计数、你确认数字后再落盘。
4. **10-source 一字节不改**，任何情况下。

### 0.4 现状基线（2026-11-16 本机实测，方案所有步骤以此为准）

| 项 | 实测值 | 对方案的影响 |
|:---|:---|:---|
| git | **未安装**（三个常见路径均不存在） | P0-1 必须先装 |
| 包管理 | winget 可用 | 用它装 git |
| PowerShell | 5.1.26100.6584（**不是 pwsh 7**） | 脚本一律 PS5.1 语法；含中文的 .ps1 存 UTF-8 BOM |
| 根目录 | .stfolder / 00-inbox / 10-source / 20-md / 30-index / 40-new / 90-tool / README.md / 主文档 | 无 .git、无 .stignore、无 50-wiki |
| 20-md 三书 | 化工原理 1108425B｜机械密封 974661B｜气液搅拌釜 351303B | 三本 md 均**无页码锚点**（`<!-- page:` 计数=0） |
| 死链 | 化工原理 86 条（`%20` 未解码，图实际存在） | P2-1 解码，不是删链 |
| 假标题 | 机械密封 351 个 `## ` 中 163 个 `(n)` 型假标题（46%） | P1-1 降级 |
| 编码矩阵 | 化工原理/气液搅拌釜 md：无BOM+LF；机械密封 md：无BOM+**CRLF**；manifest.csv BOM+CRLF；rules.md BOM+LF | git 设 core.autocrlf=false；改文件保持原 BOM/行尾 |
| 30-index | catalog.md（自动生成勿手改）、manifest.csv 15 列、todo.md、issues.log | catalog/todo 是生成物 → 入 .gitignore |
| 40-new | **已有**气液搅拌釜的 MinerU middle.json（1.16MB）+ 页码/图页 CSV + 两份 figures-report + links-fix 记录 | P2-2 页码锚点只此一本有原料 |
| DSH kb 库 | 仅机械密封 836 chunk 入库；另两本未入（README：索引由你发话才做） | 本方案不动 kb；检索不均由 50-wiki + grep 兜底 |
| 成本锚 | deepseek-flash off-peak：输入 ¥1.08/M、输出 ¥4.32/M（peak=北京时间周一至五 9–12 点、14–18 点，翻倍） | 全案报价用 off-peak 口径 |

---

## 1. 终态架构图（P3 完成后长这样）

```
                        ┌─────────────────────────────────────────────┐
                        │  你（人）：只读 + 验收 + 供书 + 拍板           │
                        └───────────────┬─────────────────────────────┘
                                        │ Obsidian（只读视窗，星图靠它渲染）
                                        ▼
 D:\Shervon_KnowledgeBase\
 ┌────────────────────────────────────────────────────────────────────┐
 │ 10-source\  【raw】PDF 原件，一字节不改                （人）放书     │
 │      │  ingest.ps1（MinerU 管线，已有，不动）                        │
 │      ▼                                                              │
 │ 20-md\      【raw 派生】全文 md + 图，脚本独占        （脚本）       │
 │      │  一次性修补：%20 解码 / 假标题降级 / 页码锚点（气液搅拌釜）     │
 │      ▼                                                              │
 │ 50-wiki\    ★【wiki】LLM 独占写，git 版本化          （LLM=我）      │
 │   index.md · log.md · glossary.md                                   │
 │   concepts\ entities\ sources\ comparisons\ howto\ openq\           │
 │      ▲                                                              │
 │ 90-tool\    【schema】rules.md（加工，v3.0）+ AGENTS.wiki.md（编辑）  │
 │      30-index\（机器索引，自动生成）+ 40-new\（草稿与一次性脚本）      │
 └────────────────────────────────────────────────────────────────────┘
            │ git（本地历史 + GitHub 私有仓库，每次 ingest 一个 commit）
            ▼
  三操作闭环（每个会话可复跑）：
  ingest（读 20-md → 写/改 50-wiki 10~15 页）→ query（grep index → 回答带 §节号）→ lint（八项体检）
```

写者边界一句话：**人只放书、只读、只验收；脚本只碰 20-md 和 30-index；LLM 只碰 50-wiki；git 记一切。**

---

## 2. 文件系统：现在 → 终态

### 2.1 现在（改造前）

```
D:\Shervon_KnowledgeBase\
├─ .stfolder\            Syncthing 标记
├─ 00-inbox\             （空）
├─ 10-source\            3 个 PDF 目录（192 MB）
├─ 20-md\
│  ├─ _quarantine\
│  ├─ 化工原理…\          md + 图片
│  ├─ 机械密封…\          md + 图片
│  └─ 气液搅拌釜…\        md + 图片
├─ 30-index\             catalog.md / manifest.csv / todo.md / issues.log
├─ 40-new\               历史补丁脚本 + pageidx/figures 材料
├─ 90-tool\              rules.md v2.3 / prompts / taxonomy / CHANGELOG / VERSION / scripts\（5 个）
└─ README.md
```

### 2.2 终态（P3 完成后，只加不改）

```
D:\Shervon_KnowledgeBase\
├─ .git\                 ★新增：版本历史
├─ .gitignore            ★新增
├─ .stfolder\            （不变；Syncthing 侧 .stignore 加 .git/）
├─ 00-inbox\             （不变）
├─ 10-source\            （不变，一字节不改）
├─ 20-md\                （不变结构；三处一次性修补：死链解码/假标题降级/气液搅拌釜页码锚点）
├─ 30-index\             （不变，继续自动生成）
├─ 40-new\               （不变，P1-P3 各步报告落这里）
├─ 50-wiki\              ★新增：LLM 独占综合层
│  ├─ index.md           总目录（P3 起由 wiki-index.ps1 自动生成）
│  ├─ log.md             append-only 时间线（每本书一条 ingest 记录）
│  ├─ glossary.md        术语唯一译名表（P2 末 ≥30 条）
│  ├─ concepts\          ★新增 概念页（主力，~60%）
│  ├─ entities\          ★新增 实体页
│  ├─ sources\           ★新增 单本页（每本书一页）
│  ├─ comparisons\       ★新增 对比页（跨书冲突落点）
│  ├─ howto\             ★新增 做法页（crystallize 落点）
│  ├─ openq\             ★新增 未决与冲突
│  └─ _lint.md           体检报告（自动生成，不入 git）
├─ 90-tool\
│  ├─ rules.md           v2.3 → v3.0（追加 §12–§15，原 11 节不动）
│  ├─ AGENTS.wiki.md     ★新增：编辑契约（8 节，人定稿）
│  ├─ scripts\
│  │  ├─ wiki-lint.ps1   ★新增
│  │  ├─ wiki-index.ps1  ★新增
│  │  └─ md-anchor.ps1   ★新增
│  └─ …（其余不变）
├─ VERSION               2.3 → 3.0
└─ README.md             目录表加一行 50-wiki
```

---

## 3. 分阶段执行：每一步做什么

> 每步格式：【谁做】【命令/动作】【产出】【验收】【坑→改法】。所有命令在执行阶段（你确认后）原样运行，不再改动。

### P0 打地基（≈0.5 小时，¥0）

#### P0-1 装 git ——【你】

```powershell
winget install --id Git.Git -e --source winget
```

- 产出：git 可用。
- 验收：**新开一个终端**跑 `git --version` 出 `git version 2.xx`。
- 坑→改法：
  1. 装完当前终端 PATH 不刷新 → **必须重开终端**再验证。
  2. winget 源不通或公司策略拦 → 备选：官网 https://git-scm.com/download/win 下载安装包，一路默认。
  3. 首次用要配身份（否则 commit 被拒）→ 我会在 P0-3 前让你跑：
     ```powershell
     git config --global user.name "你的GitHub用户名"
     git config --global user.email "你的GitHub邮箱"
     ```

#### P0-2 建 GitHub 私有仓库 ——【你】

- 动作：github.com → New repository → 名字建议 `Shervon-KnowledgeBase` → **Private（必须，书是版权材料）** → **不要勾** README / .gitignore / LICENSE（要空仓库，避免首次 push 冲突）。
- 产出：一个空私有仓库 + 它的 HTTPS 地址（形如 `https://github.com/<你>/Shervon-KnowledgeBase.git`）。
- 坑→改法：勾了 README 的话本地 push 会被拒 → 空仓库就没有这问题；真勾了就告诉我，我改用"先 pull 再 push"的走法。

#### P0-3 基线快照 + 首推 ——【我，需你提供 P0-2 的仓库地址】

```powershell
cd D:\Shervon_KnowledgeBase
git init -b main
git config core.autocrlf false        # 坑：库内 LF/CRLF 混杂，autocrlf 默认开会把全库行尾改写、污染 diff
git config core.quotepath false       # 中文路径在 git 输出里不乱码
```

写入 `.gitignore`（全文见附录 A）后：

```powershell
git add .gitignore 20-md 30-index 40-new 90-tool README.md
git status --short                     # 人工核对：绝不能出现 10-source/ 任何文件
git commit -m "P0a: 基线快照（改造前，3 本书）"
git remote add origin https://github.com/<你>/Shervon-KnowledgeBase.git
git push -u origin main
```

- 产出：本地仓库 + 远程私有仓库首个提交（含 20-md 全部图片 ≈235 MB，首推一次性慢，属正常）。
- 验收：`git log --oneline` ≥1；GitHub 网页能看见文件树。
- 坑→改法：
  1. **提交前必看 `git status`**：发现 10-source 被 add 就 `git reset` 重来，绝不能推上去。
  2. 分两次提交（P0a 基线 / P0b 地基）是刻意设计：回滚能精确回到"改造前"。
  3. push 弹 GitHub 登录 → 用 Git Credential Manager 浏览器登录一次即可。

#### P0-4 建 50-wiki 骨架 ——【我】

```powershell
mkdir 50-wiki\concepts, 50-wiki\entities, 50-wiki\sources, 50-wiki\comparisons, 50-wiki\howto, 50-wiki\openq
```

- 产出：目录 + 三份骨架文件：
  - `50-wiki\index.md`：头注"自动生成，勿手改"（P3 前先手写分类树骨架）；
  - `50-wiki\log.md`：头注 append-only 规则 + 示例行 `## [2026-11-16] init | 建层`；
  - `50-wiki\glossary.md`：头注 + "正名 / 曾用名 / 领域 / 定义来源"表头。
- 验收：`tree 50-wiki` 见 6 目录 3 文件。
- 坑→改法：**git 不追踪空目录** → 5 个子目录各放一个 `.gitkeep`（0 字节占位），否则下次 clone 目录会丢。

#### P0-5 AGENTS.wiki.md（编辑契约）——【我起草 → 你定稿 → 我落盘】

- 动作：我把主文档**附录 C 的 8 节骨架**（主文档第 1256–1298 行）原样呈给你，你逐条确认或改字；你的定稿我写入 `90-tool\AGENTS.wiki.md`。
- 产出：唯一一份"编辑契约"。八节：0 写者边界 / 1 唯一译名 / 2 断言必须有来源 / 3 页面硬约束（≤150 行、≥2 入链、图必有转述）/ 4 冲突与换代（superseded 不删旧）/ 5 Ingest 八步 / 6 Query 四步 / 7 Lint 八项 / 8 禁止四项。
- 验收：文件 ≥100 行；你逐节点头。
- 坑→改法：这份文件按主文档 §3.4 是"唯一必须有、且只能人写"的文件——**我不替你定调**，我出骨架、你拍板，防的是"LLM 给自己定规矩"。

#### P0-6 rules.md 升 v3.0 + 版本号 + README ——【我】

- 动作：rules.md **只追加** §12–§15（全文见附录 B），不动原 11 节；`VERSION` 内容改 `3.0`；`CHANGELOG.md` 加一节；`README.md` 目录表加 `50-wiki\` 一行。
- 验收：rules.md 首行版本号变 v3.0；原 11 节一字未动（diff 里只见追加）。
- 坑→改法：
  1. rules.md 是 **BOM+LF** → 追加时用 `[IO.File]::ReadAllText(UTF8)` 读完再 `WriteAllText(UTF8Encoding($true))`，保 BOM 保行尾。
  2. VERSION 是 4 字节纯文本 → 覆盖写 `3.0` 即可，别带换行。
  3. README 改动只加一行目录项，其余不动（超出授权范围的事不做）。

#### P0-7 Obsidian 只读视窗 ——【你】

- 动作：Obsidian →「打开文件夹作为库」选 `D:\Shervon_KnowledgeBase` → 打开 Graph view。
- 产出：星图自动出现；P3 后 `50-wiki` 是网络核心、`20-md` 三大节点是孤岛（预期，不是 bug）。
- 验收：星图能看到 50-wiki 的链接网。
- 坑→改法：
  1. 当前 MCP 连的 Obsidian 库只有 4 个文件、**不是本库** → 必须新建/切换 vault。
  2. Obsidian 会生成 `.obsidian\` 配置夹（新目录）→ 默认保留并入 git 同步（多端配置一致），不想同步就告诉我加进 .gitignore。
  3. "只读"是约定 + git 审计，不是文件锁 → 每次会话开始我会跑 `git status --short`，有未提交改动就逐条问你"你改了 X，吸收还是还原？"。

**P0 完成标准**：git log 有 P0a+P0b 两次提交；远程仓库有文件；AGENTS.wiki.md ≥100 行；rules.md v3.0；50-wiki 六目录三文件；Obsidian 星图能开。——**停，等你验收。**

---

### P1 单本试点（机械密封，1 个会话，≈¥0.5）

#### P1-1 假标题降级（163 个）——【我，dry-run 数字先给你看】

```powershell
$md = 'D:\Shervon_KnowledgeBase\20-md\机械密封…\机械密封….md'   # 执行前用 Get-ChildItem 核对真实路径
$raw = [System.IO.File]::ReadAllText($md, [System.Text.Encoding]::UTF8)
$n = ([regex]::Matches($raw, '(?m)^##\s*\(\d+\)')).Count
Write-Host "假标题计数: $n （预期 163，不是这个数就停）"
```

- 若你确认数字无误，再跑替换（脚本全文见附录 C-1）：`## (1)xxx` → `**(1)xxx**`。
- 产出：机械密封 md 的 `## ` 标题从 351 个降到 188 个（176 真节 + 12 其他），假标题变成正文加粗行，不再骗过标题树。
- 验收：重跑层级体检，`(n)` 型假 h2 = 0；diff 只有标题行变化。
- 坑→改法：
  1. **dry-run 与替换分两步**，数字对不上（≠163）立刻停，先把真实数字报告给你。
  2. 该文件是 CRLF → 用 `[IO.File]::ReadAllText` 保留 `\r\n`，写回无 BOM UTF-8，**不换行尾**。
  3. PowerShell 里替换串含 `$1` 必须用**单引号** `'**$1**'`，双引号会被 PS 当变量吃掉。
  4. 这是对 20-md 的一次性修补，记入 `40-new\` 报告 + CHANGELOG（例外，已在红线里声明）。

#### P1-2 页码锚点：机械密封暂缓 ——【结论，先摆这】

- 事实：三本书只有**气液搅拌釜**在 40-new 里有 MinerU middle.json；机械密封/化工原理的 middle.json 按 rules §11 解析后已清理，重跑 MinerU 才能再拿。
- 决定：P1 机械密封的引用一律用 **行号**（`#L117-456`）；锚点等"重解析该 PDF"时由 `md-anchor.ps1` 自动补。不因此卡住试点。
- 坑→改法：这步本来没人意识到"只有一本书有页码原料"，写方案时核对 40-new 才发现——所以 P2 的气液搅拌釜锚点与另两本分开列。

#### P1-3 写三个脚本 ——【我】

| 脚本 | 行为规格（全文执行时落盘，先给你过目） |
|:---|:---|
| `wiki-lint.ps1` | 只读 `50-wiki\**`，正则解析 frontmatter（`^---`…`---` 块，字段按模板固定顺序），执行八项体检（§3.5 表：死链/孤儿页/无来源/超长页/同义重复/过期断言/index 漂移/图无转述），结果写 `50-wiki\_lint.md`，全过 exit 0 |
| `wiki-index.ps1` | 只读 frontmatter 的 type/title/domain/status，按 domain 分组生成 `index.md` 表格，头注"自动生成勿手改" |
| `md-anchor.ps1` | 只读 20-md + 指定的 MinerU middle.json，按块文本在 md 中定位，插 `<!-- page: N -->`；**匹配失败率 >5% 即停**并报告 |

- 产出：`90-tool\scripts\` 三文件（UTF-8 BOM，PS5.1 语法）。
- 验收：对空 50-wiki 跑 lint 出报告不报错。
- 坑→改法：本机没有 YAML 解析库 → 校验用**固定字段名的正则**，所以 AGENTS.wiki.md §3 强制模板字段顺序，脚本与契约绑死。

#### P1-4 ingest 试点（7 页，我执行主文档 §3.5 八步 SOP）

| # | 页面 | 类型 | 来源 |
|:--|:---|:---|:---|
| 1 | sources/机械密封结构图例及应用 | source | 全书 272 页 |
| 2 | concepts/泄漏与密封判据 | concept | §1.1 |
| 3 | concepts/端面比压与pv值 | concept | §1.2（预留化工原理跨书位） |
| 4 | concepts/摩擦副材料配对 | concept | §1.3 |
| 5 | concepts/静密封与动密封分类 | concept | §1.2.1 |
| 6 | entities/机械密封-结构型式 | entity | 第 2~4 章 |
| 7 | entities/密封辅助件 | entity | 全书 |

- 动作：按 §3.5 Ingest 八步（0 查重 → 1 标题树 → 2 source 页 → 3 概念页 → 4 图转述 → 5 回改 → 6 更新 index → 7 记 log（token+¥）→ 8 lint+commit `ingest: 机械密封 touch=N`）。
- 图规则：按需喂（预估 20~30 张），每张一句文字转述；喂图的 cost 记 log。
- 产出：7 页（frontmatter 照附录 B 模板）+ log 1 条 + 1 个 commit。
- 验收：触及页 10~15（不是只写 7 页新页就算完，回改旧页也算）；`_lint.md` 死链 0。
- 成本【估计】：文本 ≈32.5 万 in（¥0.35）+ 输出 ¥0.065 + 30 图 ¥0.065 ≈ **¥0.48（off-peak）**。

#### P1-5 你验收试点

- 你：读 7 页；**抽查 3 条断言**回原书核对；看 log.md 与 `_lint.md`。
- 通过 → 进 P2；不通过 → 我改，改完再给你看。——**停，等你验收。**

---

### P2 三本铺开（2 个会话，≈¥0.7）

#### P2-1 修化工原理 86 条死链（%20 解码，不是删）——【我，先 dry-run】

```powershell
$md = 'D:\Shervon_KnowledgeBase\20-md\化工原理…\化工原理….md'   # 真实路径先核对
$raw = [System.IO.File]::ReadAllText($md, [System.Text.Encoding]::UTF8)
# dry-run：只统计链接里带 % 的条数，不改文件
$hits = [regex]::Matches($raw, '(?<=\]\(图片/)[^)]*%[0-9A-Fa-f]{2}[^)]*')
Write-Host "带%编码的图片链接: $($hits.Count) 条（预期 86 附近，对不上就停）"
```

确认后替换（脚本全文见附录 C-2）：只对 `](图片/...)` 链接内部做 `UnescapeDataString`，再跑 `check-links.ps1 -Md <md>`（不带 -Fix）验证 0 死链。

- 产出：86 条死链清零；图从"有链找不到"变"链图对应"。
- 验收：check-links 干跑输出 0。
- 坑→改法：
  1. **todo.md 原建议 `check-links.ps1 -Fix` 是"删链"**——图实际存在，删链是错修法；本方案改为解码链接，链和图都保住。
  2. 不能全文替换 `%xx`（会误伤正文里合法的百分号文字）→ 正则限定 `(?<=\]\(图片/)` 只碰链接内部。
  3. 若死链前缀不是 `图片/`（比如个别链接写的是别的前缀）→ dry-run 数字对不上时先抽样看真实前缀，改正则再跑，不硬套。

#### P2-2 气液搅拌釜页码锚点（唯一有原料的一本）——【我，先核对映射】

- 事实：`40-new\_pageidx-气液搅拌釜\` 里 MinerU middle.json 的文件名是 **"汽液搅拌釜γ－CT测量、成像与模拟_(刘跃进…).json"**——与 20-md 目录名"气液搅拌釜γ-CT…"存在**汽/气**字与**全角－/半角-**两处差异。
- 动作：先把 json ↔ md ↔ PDF 三者的对应关系核对清楚（以 20-md 内 md 的实际内容与 json 内容抽样比对为准），再跑 `md-anchor.ps1`（带 -Json 参数显式指定路径）。
- 产出：气液搅拌釜 md 出现 `<!-- page: N -->` 锚点（覆盖标题与图行）。
- 验收：**你抽 5 处锚点翻 PDF 核对页码**；我核对匹配失败率报告 <5%。
- 坑→改法：这步是本方案挑出的一个真坑——**文件名不一致的原料比没有原料更危险**（插错页码等于伪造引用，违反 AGENTS.wiki.md §8 禁令），所以"先人工核对映射"是硬步骤，不许跳过。

#### P2-3 ingest 化工原理 + 气液搅拌釜（完成 14 页清单）——【我】

剩余 7 页：

| # | 页面 | 类型 | 说明 |
|:--|:---|:---|:---|
| 8 | sources/化工原理 | source | 死链修完后才入 |
| 9 | concepts/流体流动-伯努利方程 | concept | 第 1 章 |
| 10 | concepts/传热-总传热系数 | concept | 第 4 章 |
| 11 | sources/气液搅拌釜γ-CT | source | 锚点做完后入 |
| 12 | concepts/气液分散-搅拌功率 | concept | **跨书**（+化工原理） |
| 13 | entities/搅拌桨型谱 | entity | 气液搅拌釜 |
| 14 | comparisons/搅拌功率关联式对比 | comparison | **跨书冲突第一个落点**（第 12 页派生） |

- 同批动作：glossary 补到 ≥30 条；遇到两书矛盾 → 开 openq ≥3 条（不擅自二选一）。
- 产出：14 页齐 + glossary + openq + 2 个 commit（每本书一个）。
- 验收（附录 D P2 行）：跨书引用 ≥3；openq ≥3；glossary ≥30；死链全库 0。
- 成本【估计】：化工原理 ≈¥0.51 + 气液搅拌釜 ≈¥0.2 ≈ **¥0.7（off-peak）**。

#### P2-4 你验收铺开成果

重点看第 3、12、14 页是否真跨书（这三页是价值锚点，不是"抄书加链接"）。——**停，等你验收。**

---

### P3 闭环（1 个会话，≈¥0.1）

| 步 | 做什么 | 谁 |
|:--|:---|:---|
| P3-1 | 回填 3 页 crystallize：把试点期你反复问过的 3 个问题固化成 howto/comparison 页，登记 index | 我 |
| P3-2 | 全量 `wiki-lint.ps1`，八项全过，`_lint.md` 无未决项 | 我 |
| P3-3 | `wiki-index.ps1` 自动生成 index.md（domain 分册表） | 我 |
| P3-4 | 终态验收：附录 D 判据逐项打勾 + 抽 10 条断言核对"10/10 有 §节号或行号"（你抽） | 你 |

**P3 完成 = 本方案主体结束。** 终态即第 1、2 节画的图。

---

### P4 规模常态化（未来，不是现在做）

| 触发 | 动作 |
|:---|:---|
| 每进 10 本书 | 全量 lint + 分册 index + 死链体检（脚本自动化） |
| 书 >20 本或出现"跨 5 本对比"问题 | 装 LightRAG，只抽实体层做图谱辅助（主文档 §6.4 阈值） |
| 全书 >200 页规模的 wiki（约 30 本） | 检索层升级：装 tobi/qmd（BM25+向量+重排+context 树，CLI+MCP），50-wiki 结构不变 |
| 万页级 | 才考虑完整 GraphRAG（本方案不计划，见主文档第 5 章成本结论） |
| 图总量上去（~70 GB） | Git LFS 或图片改走 Syncthing（主文档 §3.11 决策表） |

成本总账【估计】：300 本全量编译 ≈ **¥153（off-peak）**，每次 ingest 单本 ¥0.4~0.5；单次提问 ¥0.01。全部用 deepseek-flash 官方价（2026-11-16，见主文档附录 F），下单前以官网当日价为准。

---

## 4. 挑错清单（写本方案过程中挑出的坑，全部已在对应步骤写进"坑→改法"）

| # | 挑出的坑 | 错法 | 改法（落在哪一步） |
|:--|:---|:---|:---|
| 1 | 本机没装 git | 直接跑 git init 必然失败 | P0-1 winget 装，重开终端验证 |
| 2 | PS5.1 默认 GBK 读 UTF-8 乱码 | Get-Content 不带 -Encoding 会把 catalog.md 读成乱码 | 全案读写走 `[IO.File]::ReadAllText(UTF8)` |
| 3 | 库内 LF/CRLF 混杂 | git 默认 autocrlf 会把全库行尾改写、首次 diff 全红 | P0-3 `core.autocrlf false` |
| 4 | git 不追踪空目录 | 5 个子目录推不上远程 | P0-4 每目录放 `.gitkeep` |
| 5 | catalog.md/todo.md 是脚本生成物 | 版本化后每次重生成都出 diff | P0-3 进 .gitignore（manifest.csv 保留，有手工字段） |
| 6 | 死链根因是 %20 编码，不是图丢了 | todo.md 建议 `check-links.ps1 -Fix` 是删链，链和图都毁 | P2-1 只对链接内部解码，再用干跑验证 |
| 7 | 假标题替换串 `'**$1**'` 用双引号会被 PS 吃变量 | 脚本静默出错 | 附录 C-1 用单引号 |
| 8 | 页码锚点原料只有气液搅拌釜一份 | 原以为三本都能打锚点 | P1-2 机械密封用行号引用、锚点挂 todo；P2-2 只做气液搅拌釜 |
| 9 | 40-new 里 json 文件名"汽液搅拌釜γ－CT"与目录名"气液搅拌釜γ-CT"不一致 | 直接跑脚本会错位，插错页码=伪造引用 | P2-2 硬步骤"先人工核对映射再跑" |
| 10 | 双机 Syncthing 会把 .git 互传打架 | 两机 git 对象冲突 | P0-3 后你在 Syncthing 的 .stignore 加 `.git/` |
| 11 | Obsidian MCP 当前连的库不是本库 | 星图/backlinks 查到别处 | P0-7 手动"打开文件夹为库" |
| 12 | "只读"没有强制锁 | 以为 Obsidian 有只读模式 | P0-7 约定+每次会话 `git status` 审计兜底 |
| 13 | 无 YAML 解析库 | lint 脚本想解析任意 frontmatter 会写崩 | AGENTS.wiki.md §3 锁定字段顺序，脚本用固定正则 |
| 14 | 首推 235MB 图片会误以为卡死 | 中断重试 | P0-3 注明一次性属正常 |
| 15 | 新书同义页爆发 | ingest 不做查重，同名概念各建一页 | SOP 第 0 步强制查 glossary+concepts |

---

## 5. 公开资源 → 产物映射（结合哪个资源，生成什么）

| 公开资源 | 我借它什么 | 生成本库什么 |
|:---|:---|:---|
| Karpathy gist（2026-04） | 三层结构、三操作、index/log 命名、commit 节奏 | 50-wiki 目录、§3.5 SOP、log.md 格式 |
| rohitg00 v2 gist（~2026-10） | status/confidence/supersedes 生命周期、事件钩子（"每次 ingest 六件事"）、"schema 才是产品" | frontmatter 字段、AGENTS.wiki.md §4/§7 |
| geronimo-iia/llm-wiki（Rust，24 MCP 工具） | JSON Schema 校验思想、frontmatter 字段命名、lint/suggest 检查清单 | 本阶段**不装**（自写 3 个 .ps1 够用）；当 wiki >200 页时它是引擎候选 |
| geronimo-iia/llm-wiki-skills（17 skills） | 只借 6 个核心名：setup/ingest/crystallize/lint/graph/research | AGENTS.wiki.md 的章节名 |
| tobi/qmd | context 树 + BM25+向量+RRF 混合检索 | P4 阈值触发才装（C 档检索层） |
| obsidian-dataview | "frontmatter 当数据库查询"思想 | wiki-index.ps1 的生成逻辑 |
| marp-cli | md 直出幻灯片 | 可选：你用 wiki 页汇报时我生成 slide deck |
| Obsidian graph view | 星图渲染（内置功能） | P0-7 只读视窗 |
| A-MEM（NeurIPS 2025） | 记忆演化："新记忆更新旧记忆属性" | AGENTS.wiki.md §4 冲突与换代（旧页改属性不删断言） |
| 你自己的 rules.md + ingest.ps1 + MinerU 管线 | 数字编号、质检、图名归一 | 全部保留，只做增量 |

---

## 6. 人机分工总表（"我帮你做什么"）

| 环节 | 你 | 我（agent） |
|:---|:---|:---|
| 环境 | 装 git（P0-1）、建 GitHub 私有仓库（P0-2）、Obsidian 开 vault（P0-7）、Syncthing 加 .git/ | 验证安装、配 git 身份、remote+push |
| 契约 | **AGENTS.wiki.md 定稿**（骨架我出、字你定）、rules.md 增量过目 | 起草骨架、按定稿落盘、rules §12–15 追加 |
| 修补 | 确认 dry-run 数字（163 假标题、86 死链）、抽 5 处锚点翻 PDF 核对 | 跑 dry-run、替换、复验 |
| ingest | 供书（放 00-inbox 或指路径）、每批验收、抽查断言 | 八步 SOP 全部执行、喂图转述、写 log、commit |
| 巡检 | 看报告、拍板冲突（openq 的裁决权） | 每会话 git status、全量 lint、星图 backlinks 抽查 |
| 查询 | 提问 | grep index → 回答带 §节号；反复问的回填成页 |

一句话：**动手的都是我；拍板的都是你。**

---

## 7. 规模演进：结构图随书量怎么变

### 7.1 三档结构对比

```
【3 本 = P3 终态】                         【30 本】                                  【300 本】
50-wiki\                                   50-wiki\                                  50-wiki\          （结构不变形）
 ├ index.md ←单表够用                        ├ index.md ←只剩分类树                    ├ index.md ←分类树
 ├ log.md（3 条 ingest）                     ├ log.md（30 条）                          ├ log.md（300 条）
 ├ glossary.md（30 条）                      ├ glossary\（按领域分册）                   ├ glossary\（分册）
 ├ concepts\（~40 页）                       ├ concepts\密封\ concepts\搅拌\ …（~500 页） ├ concepts\**（~7000 页，子目录加深）
 └ …5 子目录平铺                             └ 子目录开始按 domain 分册                  └ 同左 + openq 常态化
检索：grep index + 直接读页                  检索：分册 index + 增量 lint                  检索：+qmd（BM25+向量+重排+context 树）
git：图片直推（235MB）                       git：图片>2GB 切 LFS                        git：图片走 LFS/Syncthing
成本：¥1.2（已花）                           成本：+¥13.5                                 成本：累计 ≈¥153（off-peak）
```

### 7.2 结构"不变"与"变"各是什么

| | 3 本 | 30 本 | 300 本 |
|:---|:---|:---|:---|
| **不变** | 50-wiki 七子路径、AGENTS.wiki.md 八节、三操作 SOP、写者边界、每书一个 commit | 同左 | 同左 |
| **变** | — | index 分册、glossary 分册、lint 增量模式 | 检索层上 qmd；跨 5 本对比上 LightRAG 实体层；图片切 LFS；10-source 可外置盘 |

设计原则（主文档 §3.8/§6.4）：**目录与契约是常量，检索层是变量。** 规模涨，换检索层；不换 wiki 结构——这是 Karpathy 原文"everything is modular"的落地。

---

## 8. 成本与时间总账

| 阶段 | 时间 | 成本（deepseek-flash，off-peak） | 谁主导 |
|:---|:---|:---|:---|
| P0 | 0.5 小时 | ¥0（GitHub 私有仓库免费） | 你装环境，我搭地基 |
| P1 | 1 个会话 | ≈¥0.48 | 我 |
| P2 | 2 个会话 | ≈¥0.7 | 我 |
| P3 | 1 个会话 | ≈¥0.1 | 我 |
| P4 | 常态化 | 每本 ¥0.4~0.5；300 本 ≈¥153 | 我 |
| 单次提问 | — | ≈¥0.01 | — |

---

## 9. 待你确认的清单（逐项回 Y / N / 改）

1. 本方案整体接受？文件名 `LLM-Wiki_落地执行方案.md` 可以吗？
2. GitHub 仓库名 `Shervon-KnowledgeBase` + **私有**，同意？
3. `.gitignore` 排除项：10-source / .stfolder / catalog.md / todo.md / _lint.md / __pycache__ / 40-new\_acl，同意？（图片 3 本时**直推**，不排除）
4. 提交节奏：P0 拆"基线快照 + 地基"两次，此后每本书一个 commit，同意？
5. AGENTS.wiki.md 流程 = 我出骨架、**你定稿**、我落盘，同意？
6. 首批 14 页清单（P1 的 7 页 + P2 的 7 页）同意？
7. 允许对 20-md 的两处一次性修补：假标题降级（163）+ 死链解码（86），同意？
8. P1 机械密封没有页码原料 → 引用用行号、锚点挂 todo 延后，接受？
9. P2 气液搅拌釜锚点"先人工核对汽/气映射"由你参与抽验，同意？
10. todo.md 遗留的"化工原理 manifest 缺 year"是否在 P2 顺手补上？（超出本方案范围的只有这一项，需要你点头才做）
11. 执行节奏：**每阶段结束停一次等你验收**，不连跑，同意？

---

## 10. 附录

### 附录 A：`.gitignore` 全文（P0-3 落盘用）

```
# 原件：版权材料，外部可重取，永不版本化
10-source/
# Syncthing 标记
.stfolder/
# 机器生成物：可重算，不入库
30-index/catalog.md
30-index/todo.md
50-wiki/_lint.md
# Python 缓存
__pycache__/
# 一次性草稿与临时目录
40-new/_acl/
```

### 附录 B：rules.md 追加稿（§12–§15，P0-6 落盘用，原 11 节不动）

```markdown
## 12. 50-wiki 层（v3.0 新增）
- 50-wiki 是 LLM 独占的综合层；脚本只读，不写。
- 20-md 重解析不得波及 50-wiki；50-wiki 内容不得回写 20-md、10-source。
- 30-index 仍只由脚本生成；人工/LLM 改生成脚本，不改成品。

## 13. wiki 页面规范
- frontmatter 字段与顺序按 90-tool\AGENTS.wiki.md 附录模板执行（type/title/aliases/domain/status/confidence/sources/related/supersedes/updated）。
- 单页 ≤150 行；每页须被 ≥2 处链接；文件名即页面正名。
- 链接一律 [[wikilink]]；confidence 与 status 枚举值不得自造。

## 14. 引用约定
- 事实断言一律双轨引用：《书名》§节号 + #L行号（有页码锚点后改页码）。
- 引用图必须附文字转述；转述不出走视觉模型，成本记 log.md。
- 新书入库前必须先具备章节地图（真标题+行号）。

## 15. 三操作 SOP
- ingest / query / lint 的标准动作与产出以 AGENTS.wiki.md §5–§7 为准。
- 每次 ingest 以一个 git commit 收尾，message 带 touch=N。
```

### 附录 C：两个修补脚本全文

**C-1 假标题降级（机械密封，dry-run 与替换分开跑）**

```powershell
# 用法：先跑 dry-run 看计数，确认后再跑 replace
param([switch]$Apply)
$md = 'D:\Shervon_KnowledgeBase\20-md\机械密封结构图例及应用_孙开元、郝振洁_第1版_2017\机械密封结构图例及应用_孙开元、郝振洁_第1版_2017.md'
$raw = [System.IO.File]::ReadAllText($md, [System.Text.Encoding]::UTF8)
$n = ([regex]::Matches($raw, '(?m)^##\s*\(\d+\)')).Count
Write-Host "假标题计数: $n"
if (-not $Apply) { exit }
if ($n -eq 0) { Write-Host '无可替换项'; exit }
$fixed = [regex]::Replace($raw, '(?m)^##(\s*\(\d+\))', '**$1**')   # 注意单引号
[System.IO.File]::WriteAllText($md, $fixed, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "已替换 $n 处"
```

**C-2 死链解码（化工原理，只碰图片链接内部）**

```powershell
# 用法：先跑 dry-run 看计数，确认后再跑 replace
param([switch]$Apply)
$md = 'D:\Shervon_KnowledgeBase\20-md\化工原理_王志魁_第5版_NA\化工原理_王志魁_第5版_NA.md'
$raw = [System.IO.File]::ReadAllText($md, [System.Text.Encoding]::UTF8)
$hits = [regex]::Matches($raw, '(?<=\]\(图片/)[^)]*%[0-9A-Fa-f]{2}[^)]*')
Write-Host "带%编码的图片链接: $($hits.Count)"
if (-not $Apply) { exit }
$fixed = [regex]::Replace($raw, '(?<=\]\(图片/)[^)]*', { param($m) [System.Uri]::UnescapeDataString($m.Value) })
[System.IO.File]::WriteAllText($md, $fixed, (New-Object System.Text.UTF8Encoding($false)))
Write-Host '已解码，请随后跑 check-links.ps1 -Md <md> 验证 0 死链'
```

> 两个脚本落盘前都会先给你看 dry-run 数字；实际路径执行当天用 `Get-ChildItem` 核对后写入，不凭记忆硬填。

### 附录 D：命令速查（你只需会用这几条）

```powershell
git log --oneline                 # 看历史（每本书一条）
git status --short                # 看有没有人动过库
git diff --stat                   # 看动了什么
winget install --id Git.Git -e    # 装 git（P0-1）
```

---

*本方案到第 9 章为止。你确认清单后，P0 由你开始（装 git、建仓库），其余按阶段推进，每段停一次。*

---

# 第三部分 使用说明（人 + Agent 共用）

> 位置：`D:\Shervon_KnowledgeBase\知识库蓝本.md`（第三部分）｜ 版本 v1.0 ｜ 2026-11-17 并入
> 读者：人（你、同事、老板演示）＋ Agent（DSH 或任何能读文件的模型）
> 一句话：先查 wiki，再查索引，再查原文，最后给「书名 + 节号 + 行号」；查不到就说查不到。
> 本节自成编号（0–10），与上文第 1–10 章并列；原独立文件 `使用说明.md` 已并入本蓝本后删除。

## 0. 六行速读（人和 Agent 都先看这里）

| # | 事实 |
|:--|:---|
| 1 | 库根目录 `D:\Shervon_KnowledgeBase`，整个文件夹可拷走，不依赖数据库。 |
| 2 | 查问题顺序：`50-wiki` → `kb` 语义检索 → `20-md` 全文 → 原件 PDF。 |
| 3 | 合格答案 = 书名 + 节号 + `#L行号`；没有就写「库里没有」。 |
| 4 | **3 本书都已解析，但 DSH 检索索引 `kb` 只进了 1 本**（机械密封）；另两本目前只能 grep（截至 2026-11-17）。 |
| 5 | 只查询：装 DSH 就够（另需库索引，见 §5.4）。加新书：还要 Python + MinerU + 2.0 GB 模型。 |
| 6 | 新文件只进 `40-new\`；`10-source\`、`20-md\` 不许手改。 |

## 1. 库里有什么（2026-11-17 实测）

| 目录 | 放什么 | 谁写 | 人能不能手改 |
|:---|:---|:---|:---|
| `00-inbox\` | 待入库的书，一本书一个文件夹 | 人投放 | 可以，入库后清空 |
| `10-source\` | 原件 PDF（只读存档） | 人放一次 | 不改、不删 |
| `20-md\` | 解析出的正文 `.md` + 每本书的 `图片\` | `ingest.ps1` / `figures.py` | 不改（要改走脚本） |
| `30-index\` | 书目、待办、清单 | `catalog.ps1` | 只改生成脚本 |
| `40-new\` | 报告、日志、脚本、临时目录 | 任何人 | 可以，别当仓库 |
| `50-wiki\` | 56 页结构化笔记（概念/实体/书页/对比/做法/未决） | 只有 LLM 写 | Obsidian 里只读 |
| `90-tool\` | 规则、提示词、脚本 | 人改规则 | 改前看 `rules.md` |

现状数字：

| 指标 | 数值 |
|:---|:---|
| 书 | 3 本：化工原理（王志魁 第5版）、机械密封结构图例及应用（孙开元/郝振洁 2017）、气液搅拌釜 γ-CT（刘跃进/韩路长 2014） |
| 正文 | 3 份 md，合计 1,528,505 字符 |
| 图 | 959 张（`20-md\*\图片\`） |
| wiki | 56 页 = 41 概念 + 3 实体 + 3 书页 + 3 对比 + 3 做法 + 3 未决 |
| 图链 | 883 条全通（426 + 320 + 137），缺图 0 |
| 体积 | 286.3 MB（其中原件 PDF 约 192 MB） |
| 版本 | git 5 次提交；`50-wiki\index.md` 有 1 处未提交改动 |
| DSH 索引 | `kb` 库 1 本 / 836 块 / 652,047 字符 |
| 待确认 | 1 项：化工原理缺 year（见 `30-index\todo.md`） |

三层结构：原件（`10-source`）→ 可检索正文（`20-md`）→ 结论页（`50-wiki`）。规则在 `90-tool\rules.md`（解析层）与 `90-tool\AGENTS.wiki.md`（wiki 层）。

## 2. 人怎么问（核心）

### 2.1 一句话模板

> 在 `kb` 库查：**〈问题〉**。要**〈定义/公式/判据/对比/出处〉**，给书名 + 节号 + `#L` 行号；库里没有就说没有。

三个要素缺一不可：**范围**（哪本/跨书）、**要什么**（结论还是原文）、**用途**（写报告/选型/答辩，决定深度）。

### 2.2 四层检索（Agent 按这个顺序走）

| 层 | 查什么 | Agent 用什么 | 命中什么 | 局限 |
|:--|:---|:---|:---|:---|
| 1 | `50-wiki` 56 页 | `grep` / `read` | 已有结论、跨书对比、已登记缺口 | 只有 37 页，细节覆盖不到 |
| 2 | `kb` 语义块 | `library_search(library="kb")` | 记不清原话时的相近段落 | 只索引 1 本；返回块不带行号 |
| 3 | `20-md` 全文 | `grep` + `read` | 精确原句、公式、行号 | 得先想到关键词 |
| 4 | `10-source` 原件 | 人打开 PDF | 图、版式、印刷页码 | 慢，且要人看 |

判定：第 1 层有现成页就直接用（最省）；没有下到第 2、3 层；**第 2 层空/不相关 ≠ 书里没有**，必须回第 3 层 grep 才能说「没有」。

### 2.3 六个可复制模板

**① 定位**

```
在 kb 库找「<关键词>」：先查 50-wiki，再 grep 20-md。
输出：书名 + 节号 + #L 行号 + 一句原文，最多 5 条；没有就写「库里没有」。
```

**② 定义 / 公式**

```
用 kb 库回答「<概念> 的定义与计算式」。
分两段：① 库中依据（书名+节号+#L+原文）② 我的判断。
公式按符号式+文字式成对写；给适用条件、单位、符号含义。
```

**③ 跨书对比**

```
对比《<书A>》与《<书B>》对「<主题>」的口径：共同点、冲突点、各自适用条件。
逐条挂出处，冲突不要合并成一条。
```

**④ 计算**

```
用库里式子算 <工况>：列出用了哪条式（#L）、代入了哪些数（带单位）、假设是什么。
缺数据就列缺什么，不要用常识补。
```

**⑤ 查缺口**

```
库里有没有「<主题>」的定量内容？
没有就说明缺什么、哪本书可能补、现在能回答到什么程度。
```

**⑥ 入库一本书**

```
按 90-tool\prompt-dsh.md 把 00-inbox 里这本书入库。
```

### 2.4 追问四连（拿到第一版答案后）

1. 「给我 `#L` 行号。」
2. 「把那句原文贴出来。」
3. 「这条的适用边界是什么？什么工况不成立？」
4. 「另一本书怎么说？冲突在哪？」

### 2.5 合格答案判定（缺一条就打回）

- [ ] 每个事实断言有 书名 + 节号 + `#L行号`
- [ ] 数值带单位、带工况（温度、压力、介质）
- [ ] 公式符号式与文字式成对（按 `~/.agents/AGENTS.md` 第 1 节）
- [ ] 明确分「库中依据」与「我的判断」
- [ ] 查不到写「库里没有」，不拿常识冒充
- [ ] 跨书冲突单列，不合并

### 2.6 三个真实样例（已按库核对）

**样例 A：精确引用（该书未入索引，走 grep）**

问：离心泵最大允许安装高度怎么定？

- 判据：实际安装高度必须低于最大允许安装高度；不汽蚀条件是有效汽蚀余量不小于允许汽蚀余量 ——《化工原理》第2章 六（`#L3787`）
- 计算式：式(2-16)（`#L3783`）；允许汽蚀余量 = 必需汽蚀余量 + 0.3 m 安全余量（`#L3775`–`#L3779`）
- 例题：例 2-4，40 ℃ 清水、Δh = 2 m、吸入管路损失 1 m（`#L3789`）
- 边界：必需汽蚀余量不能计算，只能实验（`#L3765`）

**样例 B：索引内检索（该书已入 kb）**

问：机械密封端面摩擦功率怎么算？

- 端面摩擦功率式(6-3)（`#L4627`），符号释义（`#L4629`）
- 端面摩擦扭矩式(6-1)（`#L4619`）
- 出处：《机械密封结构图例及应用》§6.1.1（`#L9087`）
- 这条 `library_search` 能直接命中；命中后仍要 grep 补行号。

**样例 C：确认缺口（防编造）**

问：搅拌功率关联式有吗？

- 三本书都没有定量关联式；只有 F₁、F_r 两个无量纲数定义（`#L2944`）和 3 个实验点（表 5.1，`#L2569`）
- 结论页：`50-wiki\openq\搅拌功率关联式缺口.md`
- 这是「确认没有」，不是「没查到」；用途是挡住「凭常识写公式」。

### 2.7 一本书从 PDF 到可引用：全流程（14 步）

> 泳道：**你**＝人，1 次操作 → **机**＝脚本，¥0 → **我**＝LLM 编译，≈¥0.51/本 → **问**＝下次提问，≈¥0.01/次（§3.9.2、§3.9.3）。每步末尾「出处」指向本文档小节，执行细节以出处原文为准。

```text
① 你   prompt＋新教材 PDF
    │   放进 00-inbox\ 一个文件夹（一本书＝一个入库夹，命名 书名_作者_版次_年份）
    │   工具：拖放即可                出处：rules §2 输入、§1 总则；§3.1 目标结构
    ▼
② 我   跑 90-tool\scripts\ingest.ps1 → 调 MinerU（mineru-kit：版面分析＋OCR）
    │   产出 20-md\<入库夹>\：全文 md（多册合并）＋图片\ 裁剪图＋MinerU 中间产物
    │   （middle.json 每块带 page_idx）；原件同步移入 10-source，inbox 清空
    │   出处：rules §3 输出、§2 输入；§9.7；§9.8
    ▼
③ 机   30-index 自动重建（catalog.ps1 → catalog.md / manifest.csv / todo.md）
    │   图名归一 figures.py（caption 化、剥引用号）；质检（rules §7，ingest 内）
    │   出处：rules §7 质检、§11 图名归一；§3.1
    ▼
④ 机   一次性修补（每本各跑一次）：假标题降级 ## (n)→**(n)**；%20 死链解码
    │   （check-links.ps1 干跑 0 才过）   出处：P1-1；§9.7；P2-1
    ▼
⑤ 机   md-anchor.ps1 读本次解析的 middle.json → 在 20-md 插 <!-- page: N --> 页码锚点
    │   匹配失败率 >5% 即停；旧书已清理 middle.json 的需先重跑 MinerU 中间产物
    │   出处：§9.8；§3.7；P2-2
    ▼
⑥ 机   git add 20-md → commit（机器层闭环；后面 LLM 写坏可 reset 回滚）
    │   出处：§3.11；§9.9
    ▼
⑦ 我   Ingest 步0-2：查重（glossary＋concepts＋index）→ 提取标题树 →
    │   写 sources\<书>.md（章节地图＋这本书能答/不能答什么）
    │   出处：§3.5 Ingest 表；AGENTS.wiki.md §1、§2
    ▼
⑧ 我   Ingest 步3-4：建/改 concepts、entities 页（定义/机理/口径/参数/边界/来源）
    │   引用图必有文字转述；转述不出 → 按需喂 deepseek-flash（Vision），钱记 log
    │   出处：§3.5 步4；§3.9.2；AGENTS.wiki.md §3
    ▼
⑨ 我   Ingest 步5：回改受影响旧页。两书口径矛盾 → 开 openq（不擅自二选一）；
    │   新断言推翻旧断言 → 旧页标 superseded，supersedes 指向新页，不删
    │   出处：AGENTS.wiki.md §4；§3.5 步5
    ▼
⑩ 机   wiki-index.ps1 重生成 index.md；log.md 追加一条 ingest
    │   （touch=N、in/out token、¥）      出处：§3.5 步6、步7
    ▼
⑪ 机   wiki-lint.ps1 八项体检 → 50-wiki\_lint.md；git commit "ingest: 《书》 touch=N"
    │   出处：§3.5 Lint 表；§3.11
    ▼
⑫ 问   下次提问走 Query 四步：grep index.md 定位主题 → 读 ≤10 候选页 →
    │   不够查 glossary 同义词 → 再不够才 grep 20-md 原文（最后手段）
    │   出处：§3.5 Query 表；§9.10；§6.4
    ▼
⑬ 问   我回答：每条断言挂《书名》§节号＋#L行号；有锚点的书再附「第 N 页」。
    │   反复被问的点 → crystallize 成 howto/comparison 页并登记 index（回填）
    │   出处：§3.3 §14 引用约定；§3.5 Query 步4
    ▼
⑭ 你   Obsidian 星图只读浏览（星图＝50-wiki 的 [[]] 网）。规模升级触发器：
    │   ＞20 本 → LightRAG 实体图；＞30 本 → tobi/qmd 混合检索；图膨胀 → Git LFS
    │   出处：§3.12；§6.5；P4
```

**工具清单（按出现顺序）**：

| 工具 | 图中步 | 干什么 | 出处 |
|:---|:--:|:---|:---|
| MinerU（mineru-kit CLI） | ② | PDF → md／裁剪图／middle.json（含 page_idx） | §9.7、§9.8 |
| `ingest.ps1` | ② | 编排解析、搬原件、质检 | rules §3、§7 |
| `figures.py` / `catalog.ps1` | ③ | 图名归一 / 重建 30-index | rules §11、§3 |
| `check-links.ps1` | ④ | 死链体检 | §9.7、P2-1 |
| `md-anchor.ps1` | ⑤ | 页码锚点 `<!-- page: N -->` | §3.7、§9.8 |
| deepseek-flash（Vision） | ⑧ | 按需喂图拿文字转述 | §3.9.1 |
| `wiki-index.ps1` / `wiki-lint.ps1` | ⑩⑪ | 生成 index / 八项体检出 `_lint.md` | §3.7 |
| git＋GitHub 私有仓库 | ⑥⑪ | 版本历史、回滚、异地备份 | §3.11、§9.9 |
| Obsidian | ⑭ | 星图只读视窗（人机同步） | §3.12 |
| 我（DSH 会话） | ⑦⑧⑨⑫⑬ | 编译、检索、回答 | 全文 |

**三个口径，避免误读**：

1. **页码不是每本书都有**：新书从 P1 之后解析默认带锚点（§9.8）；机械密封试点暂以行号引用（P1-2）。行号取 20-md 绝对行，页码取原书页码，双轨（§3.3 §14）。
2. **本图是 §3.5 三 SOP 的纵向串联**，横向细节（每步怎么判对错）以出处小节为准，图里不重复。
3. **⑫~⑬ 是"下次提问"路径**，与是否新建向量库无关：先走 wiki 页（§9.10），grep 原文只是兜底（§6.4）。

## 3. 要不要先把三本书读一遍

**结论：不要通读。** 1,528,505 字符按 400–500 字/分钟约 51–64 小时（估算），读完也记不住；这个库的价值在「查得到 + 核得回」，不在背下来。

先花 90 分钟建「最小地图」：

| 顺序 | 读什么 | 时间 | 目的 |
|:--|:---|:--|:---|
| 1 | `50-wiki\index.md` | 10 min | 56 页页名 + 一句摘要，知道库能回答什么 |
| 2 | `50-wiki\sources\` 3 页 | 15 min | 每本书的重点节与覆盖范围 |
| 3 | `50-wiki\glossary.md` | 10 min | 30 条唯一译名（问问题时用对词） |
| 4 | `50-wiki\comparisons\` 3 页 | 15 min | 三处跨书口径冲突 |
| 5 | `50-wiki\openq\` 3 页 | 10 min | 三个已确认缺口 |
| 6 | 挑 5 个与你工作最近的 `concepts\` | 30 min | 建立手感 |

判断标准：能说出「三本书各管什么、哪三处冲突、哪三个缺口」，就算有印象，够了。之后按需读：算题读《化工原理》第 2 章；选型读《机械密封》§4、§6。

## 4. 给老板演示（8 分钟脚本）

### 4.1 演示前 10 分钟准备

1. 确认 `kb` 里有 3 本（当前只有 1 本，补齐见 §7.3）；不补也能演，但第 2 步会退化成 grep。
2. 资源管理器打开 `D:\Shervon_KnowledgeBase`；Obsidian 打开 `50-wiki\index.md`。
3. 开一个 DSH 会话，工作目录选库根。
4. 手边一页数字：3 本 / 1.30 M 字符 / 56 页 / 959 图 / 883 图链全通。

### 4.2 六步

| 步 | 你说/做什么 | 屏幕上应出现 | 说明什么 |
|:--|:---|:---|:---|
| 1（30 s） | 打开根目录与 `30-index\catalog.md`、`50-wiki\index.md` | 三本书目 + 37 页索引 | 这不是网盘，是编过目的库 |
| 2（60 s） | 问「机械密封端面摩擦功率怎么算？给行号」 | 式(6-3) + §6.1.1 + `#L9101` | 回答带出处，不是聊天 |
| 3（60 s） | 问「离心泵最大允许安装高度怎么定？」 | 式(2-16) + `#L6723` + 例 2-4 + 边界 | 能落到计算，不只是概念 |
| 4（30 s） | 问「搅拌功率关联式有吗？」 | 明确「库里没有」+ 缺口页 + 现有 3 个实验点 | 不会的地方直接说不会 |
| 5（30 s） | 让 Agent 给出 `#L6723`，你在 md 里跳过去 | 原文与答案逐字对得上 | 可核对，防幻觉 |
| 6（60 s） | 「把 2、3、4 整理成一页对比，带出处，存 docx」 | `40-new\` 里出现文件 | 能出交付物，不只是问答 |

### 4.3 预期结果与判定

| 判定项 | 合格线 |
|:---|:---|
| 出处 | 每条都有书名 + 节号 + `#L`，能点回原文 |
| 缺口 | 问库里没有的，答案第一句就是「没有」 |
| 一致性 | 屏幕上的行号与 md 原文一致（现场抽查 1 条） |
| 速度 | 单问 10–30 秒；出文档 1–2 分钟 |
| 边界 | 答案里写明工况/单位/适用条件 |

### 4.4 给老板的一页纸（可直接念）

- **是什么**：3 本专业书 → 可检索、可引用、可核对的工作底稿。
- **能答**：定义、公式、判据、跨书对比、明确缺口。
- **不能答**：库里没有的，会直接说没有，并指出缺哪类资料。
- **硬数字**：3 本 / 1.30 M 字符 / 56 页 / 959 图 / 883 图链全通 / 引用精确到行。
- **怎么复核**：打开 `20-md` 对应 md，按 `#L` 跳行，逐字对。

## 5. 换电脑 / 给别人：前提与迁移

### 5.1 三档需求，别多装

| 档 | 你要干什么 | 需要装 |
|:--|:---|:---|
| A 只查询 | 问问题、看 wiki、演示 | DSH（必需）+ 本文件夹（+ 索引） |
| B 加新书 | 把新 PDF 入库 | A + PowerShell 5.1 + Python + MinerU + 模型 |
| C 维护 | 改 wiki、跑体检、改规则 | A + PowerShell（git 可选） |

### 5.2 软件清单（本机实测版本）

| 软件 | 本机版本 / 位置 | 干什么 | A 查询 | B 加书 |
|:---|:---|:---|:---:|:---:|
| DeepSeek Harness | 0.2.2.0（安装包 0.2.2-rc.3；`C:\local installation directory\DeepSeek Harness`） | 会话、检索、写 wiki | 必需 | 必需 |
| PowerShell | 5.1.26100（系统自带） | 跑 `90-tool\scripts\*.ps1` | 可选 | 必需 |
| Python | 系统 3.14.6；MinerU venv 3.12.14 | `figures.py`（只用标准库） | 否 | 必需 |
| MinerU | 4.1.7（`C:\Users\shervon\.local\mineru\Scripts\mineru-kit.exe`） | PDF/图片 → md | 否 | 必需 |
| MinerU 模型 | standard 档约 2.0 GB（`C:\Users\shervon\.mineru\models`） | 解析模型，勿重下 | 否 | 必需 |
| Git | 2.56.1 | 提交、回滚、审计 | 否 | 可选 |
| Obsidian | 1.14.4 | 读 wiki、看链接 | 否 | 可选 |
| Everything / VS Code | — | 全文搜 | 可选 | 可选 |
| 7-Zip | — | 打包迁移 | 可选 | 可选 |

Agent 侧：本机 DSH 已启用 `library_search` / `library_add` / `grep` / `read` / `pwsh`，不需要额外装 CLI（`library_*` 由 DSH 的 library 插件提供；新机若未启用或会话无此工具，按 §6 退路走 grep）。MinerU 只由 `ingest.ps1` 调，不要求人会用命令行。

### 5.3 迁移六步

1. **整包复制**（不是 git clone）：`10-source\` 与 `30-index\catalog.md`、`todo.md` 被 git 排除，clone 会缺原件。建议保持 `D:\Shervon_KnowledgeBase`。
2. 新机装 DSH 0.2.2.0（同一大版本；索引兼容性未跨版本验证，升级前先备份 `dsh_library.json`）。
3. **恢复索引**（三选一，见 §5.4）。不恢复也能用，但 `library_search` 会报库不存在。
4. 验证：跑 §7.1 四条命令 + 一次检索，对照 §7.2 判据。
5. 要 Obsidian：把文件夹当 vault 打开（`.obsidian\app.json` 已排除 `10-source`、`20-md` 等，图谱只显示 `50-wiki`）。
6. 要加书：装 Python + MinerU，把 `models` 目录拷到新机同位置（2.0 GB，可直接拷）。

### 5.4 索引怎么恢复（关键：索引不在这个文件夹里）

DSH 的检索索引在 `%USERPROFILE%\.dsh\storages\dsh_library.json`（本机 11 MB，含文档、分块、256 维向量），**不在 `D:\Shervon_KnowledgeBase` 内**。三种办法：

| 办法 | 怎么做 | 代价 / 风险 |
|:---|:---|:---|
| ① 拷索引文件 | 复制 `dsh_library.json` 到新机同路径 | 最快、零重算；但该文件还含 magverify 8 篇，且会覆盖新机已有库；跨 DSH 版本未验证，先备份 |
| ② 重新入库 | 对 3 份 md 各跑一次 `library_add`（见 §7.3） | 干净、只进 kb；要重新切块+嵌入，耗时与费用未测 |
| ③ 不恢复 | 只靠 `grep` + `read` | 能用，但没有语义召回，问法必须带关键词 |

建议：新机没有别的库 → ①；有别的库或换 DSH 大版本 → ②。

### 5.5 路径变了怎么办

- 多数脚本从自身位置推根目录，换盘符能自适应。
- 3 个脚本有硬编码默认值，各 1 行，换路径要改（或显式传参）：`90-tool\scripts\md-anchor.ps1`、`wiki-index.ps1`、`wiki-lint.ps1`。
- `90-tool\prompt-dsh.md`、`prompt.md`、`rules.md` 里的示例路径要同步改，否则下次入库会指错地方。
- `30-index\manifest.csv` 存相对路径，可搬。

### 5.6 给别人时的裁剪（版权）

- `10-source\` 是版权原件，git 已排除。给外人建议只给 `20-md\` + `50-wiki\` + `90-tool\` + `30-index\`（约 90 MB）。
- 不带原件的后果：能查、能引用行号、图还在（图在 `20-md`），但不能重解析、不能补图。
- 带原件：286 MB，版权自负；别上传任何网盘或公开仓库。

## 6. Agent 怎么调工具

| 任务 | 工具 | 调用要点 |
|:---|:---|:---|
| 语义找段落 | `library_search` | `library="kb"`，`query` 用中文短语，`topK` 4–8 |
| 精确找词/行号 | `grep` | `path` 指到具体 md；返回行号 |
| 读上下文 | `read` | 带 `offset`/`limit`，按 grep 行号前后各读 30 行 |
| 找文件 | `glob` | `20-md\**\*.md` |
| 跑脚本 | `pwsh` | 用完整 `powershell -NoProfile -ExecutionPolicy Bypass -File ...` |
| 出文档 | `office_docx` / `office_xlsx` | 只在要交付时用；解析 docx 不需要 Office |
| 多步任务 | `todo_write` | 先列步骤再动手 |

**失败退路（新机最容易卡在这）**

| 缺什么 | 表现 | 退路 |
|:---|:---|:---|
| 无 `library_search` / 库不存在 | 工具报错或 library not found | 直接 `grep 20-md`，问法带关键词 |
| 无 Python | `python` 不是内部或外部命令 | 仍可查询；加书前先装 Python 3.10+ |
| 无 MinerU | 入库报「未找到 mineru-kit」 | 只处理 md/txt/docx；PDF 留在 `00-inbox` 记待办 |
| 无 PowerShell | 无法执行 `.ps1` | 按 `rules.md` §9 手工回退，不跑脚本 |
| 盘符变 | `wiki-lint` 找不到 50-wiki | 改 §5.5 的 3 个默认值，或显式传参 |
| 索引文件缺 | 检索报库不存在 | 按 §5.4 恢复 |

**Agent 硬规则**

1. 不写 `10-source\`、`20-md\`；不删任何文件。
2. 新文件只进 `40-new\`。
3. 引用写 `《书名》§节号（#L行号）`；节号用书里真实编号，不猜。
4. 回答分「库中依据 / 我的判断」两段。
5. 不装软件、不联网、不上传资料。
6. 区分「索引里没有」与「书里没有」：前者要 grep 才能下结论。

## 7. 维护命令与判据

### 7.1 四条命令（在库根执行）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\catalog.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-index.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-lint.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\check-links.ps1" -Md "D:\Shervon_KnowledgeBase\20-md\化工原理_王志魁_第5版_NA\化工原理_王志魁_第5版_NA.md"
```

### 7.2 判据（2026-11-17 基线）

| 命令 | 合格输出 | 不合格怎么办 |
|:---|:---|:---|
| `catalog.ps1` | 3 本 / 待确认 1 项 | 待确认是缺 year，不是错误；补 frontmatter 后重跑 |
| `wiki-index.ps1` | 37 页 | 页数对不上 = 有页没进索引，看输出 |
| `wiki-lint.ps1` | 问题 0 条 | 按报告逐条修死链/孤儿/无来源 |
| `check-links.ps1` | 426/320/137，`unresolved=0` | 跑 `-Fix` 后复查 |

### 7.3 补齐检索索引（当前只有 1 本，建议做）

对两份未入库的 md 各跑一次（Agent 用 `library_add`）：

```
library_add(path="D:\Shervon_KnowledgeBase\20-md\化工原理_王志魁_第5版_NA\化工原理_王志魁_第5版_NA.md", library="kb", name="化工原理_王志魁_第5版_NA")
library_add(path="D:\Shervon_KnowledgeBase\20-md\气液搅拌釜γ-CT测量、成像与模拟_刘跃进、韩路长_第1版_2014\气液搅拌釜γ-CT测量、成像与模拟_刘跃进、韩路长_第1版_2014.md", library="kb", name="气液搅拌釜γ-CT测量、成像与模拟_刘跃进、韩路长_第1版_2014")
```

验证：`library_search(library="kb", query="汽蚀余量 允许安装高度")` 应命中《化工原理》段落；命中后再 grep 补行号。耗时与嵌入计费未实测，先确认再跑。

## 8. 已知坑

| 现象 | 原因 | 处理 |
|:---|:---|:---|
| 问《化工原理》却返回机械密封段落 | 该书没进索引，语义检索不报空 | 先 grep；或按 §7.3 补索引 |
| 检索结果没有行号 | 索引块只存正文 | grep 定位后再引用 |
| 提示「禁止运行脚本」 | 执行策略 | 用带 `-ExecutionPolicy Bypass` 的完整命令 |
| 中文乱码 / ParserError | `.ps1` 缺 UTF-8 BOM | 存成「UTF-8 带 BOM」 |
| 入库报锁 | `40-new\.ingest.lock` 存在 | 确认没有别的入库会话后删掉 |
| 图链报错含 `%20` | v3.1 前的旧写法 | 跑 `check-links.ps1 -Fix` |
| Obsidian 图谱只有几个点 | 只显示未排除目录 | 正常，见 `50-wiki\howto\Obsidian图谱为什么只显示部分页面.md` |
| 页数与 index.md 对不上 | 加了页没重跑索引 | 跑 `wiki-index.ps1` |
| git push 失败 | 本机 DNS 解析失败（2026-11-17） | 本地 commit 已在，稍后重试 |

## 9. 安装包放哪（换机不卡）

建议在根目录建 `80-setup\`，放这些（版本对应 §5.2）：

| 文件 | 用途 |
|:---|:---|
| DSH 0.2.2.0 安装包（0.2.2-rc.3） | 必需 |
| Python 3.12 x64 安装包 | 加书必需（3.10+ 均可） |
| MinerU 4.1.7 安装包 / 离线 wheel | 加书必需 |
| `models\`（2.0 GB，可直接拷） | 加书必需，免重下 |
| Git 2.56.1、Obsidian 1.14.4、7-Zip | 可选 |

两个注意：

1. 你现在的 `rules.md` 第 8 节禁止在根目录新增层级；放 `80-setup\` 属于例外，需在 `rules.md` 补一行「`80-setup\` 仅存安装包，不入库、不进 20-md」，否则下次入库的 Agent 可能按规则拒绝。也可以改放 `40-new\setup\`（合规，但 `40-new` 定位是临时目录）。
2. 安装包体积大，别进 git：在 `.gitignore` 加 `80-setup/`（要改就说一声）。

## 10. 变更记录

| 版本 | 日期 | 改了什么 |
|:---|:---|:---|
| v1.0 | 2026-11-17 | 首版：现状、提问四层、演示脚本、迁移与工具前提、坑表 |
| v1.1 | 2026-11-17 | 订正 DSH 版本号（0.2.2.0 / 安装包 0.2.2-rc.3）；§0 补「另需库索引」；`library_*` 改述为 DSH library 插件提供，并指向 §6 退路 |
