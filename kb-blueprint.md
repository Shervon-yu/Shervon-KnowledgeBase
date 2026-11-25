# 知识库蓝本（KB blueprint）

> **这份文件是本知识库的蓝本**：调研、方案、施工图、使用说明都在这里，没有它就没有这个库。
> - 1. **方案论证**（原 `LLM-Wiki_RAG_GraphRAG_全解与本库改造方案.md`，1420 行）：为何选 LLM Wiki 而非 RAG/GraphRAG，规模阈值与成本。
> - 2. **落地执行**（原 `LLM-Wiki_落地执行方案.md`，584 行）：P0–P4 施工图、脚本原文、验收判据。
> - 3. **维护与升级**（2026-11-23 分出）：换机迁移、四方案复评与升级方向。
> - 4. **使用说明**（2026-11-17 并入，原 `使用说明.md`）：怎么问、怎么加书、坑表。
> 顺序：先讲为什么，再讲怎么做，再讲维护与升级，最后讲怎么用。改动本文档即改动施工依据，改前先看 git log。
> **路径注记（2026-11-19，v3.13）**：本文中出现的 `50-wiki\` 与 `30-index\` 是当时的设计名；两者已合并为单一的 `30-wiki\`（机器区 + 人写区），现行落地口径以 `90-tool\rules.md` §12 为准。文中路径仅作历史记录，不代表当前目录结构。

## 变更记录

| 版本   | 日期         | 改了什么                                                                                            |
| :--- | :--------- | :---------------------------------------------------------------------------------------------- |
| v1.0 | 2026-11-17 | 首版：现状、提问四层、演示脚本、迁移与工具前提、坑表                                                                      |
| v1.1 | 2026-11-17 | 订正 DSH 版本号（0.2.2.0 / 安装包 0.2.2-rc.3）；§4.0 补「另需库索引」；`library_*` 改述为 DSH library 插件提供，并指向 §4.5 退路 |
| v1.2 | 2026-11-23 | 全文三层编号（四部分）；拆出「3. 维护与升级」；删「给老板演示」；使用说明对齐 v3.18 现状（5 本 / 542 页 / 30-wiki / kb 120 页旧路径）          |
| v1.3 | 2026-11-23 | §3.2 增补 3.2.1 白话解读：名词（grep/BM25/向量/RRF）、四方案逐行、本库核心改动（方法/东西/idea）、U1–U6 升级方向，逐条附证据位置             |
| v1.4 | 2026-11-24 | §3.2 增补 3.2.2–3.2.4：GitHub 一手调研的六类「页数增长故障」及解法、LLM Wiki v2 逐模块机制、本库 vs v2 逐项对照与四套升级套餐（供选型）       |
| v1.5 | 2026-11-24 | §3.3 新增升级方案：索引可管理（description / 二级分册 / index-doctor）、检索换二元组 BM25（kb-search + grep 基线 A/B）、回答协议与锚点自检、度量与回滚（供执行） |
| v1.6 | 2026-11-24 | §3.3 推翻重写：按新前提（知识页上万/全领域、资料与经验两类入库分区、不共享单人单写）照 LLM Wiki v2 模块清单重排；旧版的自建 BM25 理由、golden set 度量、回滚原则保留 |

---

# 1. 方案论证：LLM Wiki / RAG / GraphRAG 全解 + 本库改造方案（第三版）

> 版本：**v3.0（2026-11-16）** ｜ 对象：`D:\Shervon_KnowledgeBase`
> 本版预设口径：**按你有 300 本书 + 零散资料设计**（不是按当时 3 本设计；3 本只是起步试点，现已 5 本入库）。
> 标注约定：**【原文】**=一手文献原话 ｜**【文献】**=有出处的研究/项目/价格页 ｜**【实测】**=本机命令结果 ｜**【判断】**=我的推理或经验值 ｜**【估计】**=量级估算，非精确值。
> 价格一律标注来源与日期，**下单前以官网当日价为准**。

---

## 1.0 先给结论（五分钟版）

| 问题             | 结论                                                                                                                                                                 |
| :------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM Wiki 是什么   | 不是软件，是一个**模式**：LLM 在入库时把源文件"编译"成互相链接的 markdown 页面网，而不是等提问时再检索。**知识在入库时被综合一次，之后只做维护。**                                                                              |
| 和 RAG 的根本差别    | RAG 每次提问都从零拼答案（无积累）；LLM Wiki 把答案的原料提前建好（有积累）。差别不在技术栈，在**知识生成的时间点**。                                                                                                |
| 你（300 本书口径）缺什么 | 不缺解析（MinerU 管线已工业级），缺**综合层**（把每本书编译成 ~25 页概念页的网）+ **编辑契约**（AGENTS.wiki.md）+ **版本控制**（git）。                                                                         |
| 改造路径           | 不加解析、不换工具。**加 `30-wiki\` + `git init`（本地 + GitHub 私有仓库）+ 一份 schema，然后一本书一本书编译。**                                                                                   |
| 什么时候上向量检索      | **看 §1.6.4 量化分界线**：md 语料 ≤5 MB 别上；5~50 MB 用全文检索；50 MB 以上（约 50 本）才上混合检索 qmd。300 本书（~240 MB）落在"混合检索"档，仍轮不到 GraphRAG。                                                   |
| 图片喂视觉模型的成本     | 图片便宜到可以忽略：deepseek-flash 下按需喂 30 张图，一本增量 ≈ **¥0.07**；全量 400 张 ≈ ¥0.86/本。**图片不是成本问题，是流程问题。**                                                                        |
| **单本入库到底多少钱**  | 一本《化工原理》编成 wiki：**只文本 ≈ ¥0.44；按需 30 图 ≈ ¥0.51；全量 400 图 ≈ ¥1.31**（deepseek-flash、off-peak、官方价 2026-11-16；peak 翻倍）。详见 §1.8.2。                                          |
| 最重要的一句话        | 你已经有 `catalog`（≈index）、`issues.log`（≈log）、`todo.md`（≈lint 报告）——三操作的骨架早就有了，只是它们服务的是"脚本"，不是"知识"。**这次要做的不是新发明，是补上"编辑"和"版本"两个洞，再借鉴 9 个外部方案（8 仓库 + 1 内置功能）的 idea 做融合。** |

#### 0.1 本版（v3.0）相对 v2.0 改了什么

| # | 变更 | 章节 |
|:--|:---|:---|
| 1 | **第 8 章整章重写**：九个方案逐个读一手 README / gist 原文 / 论文摘要后重写，改为"一手事实 / 借什么 / 不借什么"三列 | 第 8 章 |
| 2 | 新增 **§1.7.0 自查：v2 里被一手文档推翻的 9 处错误**（你让我自己找的"漏洞"） | §1.7.0 |
| 3 | 新增 **§1.7.2 照搬现成方案的三条路线试算**：为什么"直接装 geronimo 引擎 / 直接上 qmd"不如自建融合 | §1.7.2 |
| 4 | **§1.8.2 全部改口径**：改用 DeepSeek 官方 **deepseek-flash**（带 Vision、1M 上下文），只算**单本入库价**，不再扯九万张图 | §1.8.2、§1.3.9、附录 F |
| 5 | 价格表补 **DeepSeek 官方价**（off-peak 输入 $0.15/M、输出 $0.6/M，peak 翻倍）；旧"2/8 元历史锚"降级为对照 | §1.3.9.1 |
| 6 | 事实修正：geronimo 是 **24 个 MCP 工具**（原写 19）、llm-wiki-skills 是 **17 个 skills**（原写 8）、qmd 的 **context 树**、dataview 的 **DQL/DataviewJS** | §1.7.0、§1.3.2、附录 E |
| 7 | A-MEM 加限定：它是 **agent 对话/任务记忆系统**，不是文件型知识库 | §1.1.10、§1.7.1 |
| 8 | 附录 E 补 agent-skills、A-Mem 代码库；附录 F 换算与示例全换 flash 口径 | 附录 E、F |

##### v2.0 相对 v1.0 的 10 条（留档）

| # | 变更 | 章节 |
|:--|:---|:---|
| 1 | 预设口径从"3 本书"改为"300 本书 + 零散资料"，所有规模判断重算 | 全文，尤其 §1.2.6、§1.6 |
| 2 | 新增 **LLM Wiki v2 全解**（作者、时间、四大提升、哪些未验证） | §1.1.9 |
| 3 | 新增**量化分界线**：多少 MB/多少字以下用 LLM Wiki、以上用 RAG，四档表格 + 判据 | §1.6.4、§1.6.5 |
| 4 | 新增**完整成本账**：视觉模型峰/谷价、一本书入库总价、单次提问 token | §1.3.9、§1.8.2、附录 F |
| 5 | 新增**融合方案**专章（10 个项目核心 idea 拆解 + 取舍 + 融合架构） | 第 8 章 |
| 6 | 新增 **Q&A 专章**：你提的全部问题逐条回答 | 第 9 章 |
| 7 | 术语表重写为**小白版全表**（全称 + 中文 + 一句话 + 在哪出现） | §1.1.12、附录 A |
| 8 | 死链成因实测修正：不是图丢了，是 **`%20` URL 编码未解码** | §1.2.3 问题 1 |
| 9 | 新增 **git + GitHub 同步方案**、**Obsidian 星图 + 人机同步方案** | §1.3.11、§1.3.12 |
| 10 | 新增 **MinerU 强制 OCR 的官方答案**（`--method ocr`）与页码锚点方案 | §1.8.7、§1.8.8 |

#### 0.2 你的问题 → 答案索引

| 你的问题 | 答案在哪 |
|:---|:---|
| 向量检索分界线（多少字/MB 为界） | §1.6.4、§1.8.1 |
| 单本入库多少钱（deepseek-flash）、每张图多少钱、单次提问 token | §1.3.9、§1.8.2、附录 F |
| LLM Wiki v2 是谁、什么时候、提升什么 | §1.1.9、§1.8.3 |
| 专业术语全表（gist/git/ingest/lint/MCP/BM25…全称+含义） | §1.1.12、附录 A |
| "无 lint 就腐化"是什么意思 | §1.1.5、§1.1.12、§1.8.4 |
| 预设应为 300 本书 | 已全文改口径，见 §1.0、§1.2.6、§1.8.5 |
| 融合方案（集百家所长、比原方案更高级） | §1.7、§1.8.6 |
| 你让我自己找的"漏洞"（v2 里被一手文档推翻的 9 处） | §1.7.0 |
| MinerU 能不能强制全程 OCR、死链怎么解决 | §1.8.7 |
| 分页标记能不能在解析阶段加 | §1.8.8 |
| git 本地 + GitHub 同步 | §1.3.11、§1.8.9 |
| LLM Wiki 建好是否顺带解决检索不均 | §1.8.10 |
| 目录/文件名怎么命名（Karpathy 还是 GitHub 项目） | §1.3.2、§1.8.11 |
| 50- 前缀为什么、能不能用 a/b/c | §1.3.1、§1.8.12 |
| Obsidian 星图、人机同步、改了要报告 | §1.3.12、§1.8.13 |
| 先看融合方案再决定动不动库 | §1.7 + §1.8.14（**本版没有动你的库，只改了这份文档**） |

---

## 1.1 LLM Wiki

### 1.1.1 出处：一份 gist，不是一个项目

**【原文】** Karpathy 于 2026-04 发布的 [`llm-wiki.md`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)，自述定位：

> "This is an idea file, it is designed to be copy pasted to your own LLM Agent (e.g. OpenAI Codex, Claude Code, OpenCode / Pi, or etc.). Its goal is to communicate the high level idea, but your agent will build out the specifics in collaboration with you."

翻译：**它不是库、不是应用、不是框架，是一份"想法文件"**，让你整段粘进 agent，让 agent 按你的领域现场长出具体形态。所以网上所有 "llm-wiki" 仓库都只是**某个人对这份 gist 的一种落地**，没有权威实现——这恰恰是你能"集百家之长"的前提：**没有正统，只有取舍。**

### 1.1.2 它到底在反对什么

**【原文】** 开篇就点名：

> "Most people's experience with LLMs and documents looks like RAG: you upload a collection of files, the LLM retrieves relevant chunks at query time, and generates an answer. This works, but the LLM is rediscovering knowledge from scratch on every question. There's no accumulation. Ask a subtle question that requires synthesizing five documents, and the LLM has to find and piece together the relevant fragments every time. Nothing is built up."

翻译：普通 RAG 每次提问都在**从零重建**；一个需要综合五份文档的问题，每次都要重新找、重新拼。**没有累积。**

**【原文】** 反方案：

> "the LLM **incrementally builds and maintains a persistent wiki** — a structured, interlinked collection of markdown files that sits between you and the raw sources. When you add a new source, the LLM doesn't just index it for later retrieval. It reads it, extracts the key information, and integrates it into the existing wiki — updating entity pages, revising topic summaries, noting where new data contradicts old claims..."

**注意动词**：不是 `index`（建索引），是 `integrate`（并入）。这是全篇最重要的一处设计意图。

### 1.1.3 为什么它成立：维护成本才是瓶颈

**【原文】** 这是全文最狠的一句：

> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. Updating cross-references, keeping summaries current, noting when new data contradicts old claims, maintaining consistency across dozens of pages. Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass."

**【判断】** 这句话解释了为什么个人 wiki 几乎都死了：不是人不会整理，是**整理的成本随页数超线性增长**（n 页要维护 ~n² 条潜在交叉引用）。LLM 把这个成本压到接近零。

**按 300 本书算这笔账【估计】**：300 本 ≈ 7500 个概念页，潜在交叉引用 ~5000 万条——靠人维护是天文数字，靠脚本只能维护"文件级"关系，**只有 LLM 能维护"知识级"关系**。所以对你而言，LLM Wiki 不是"可选风格"，是"书一多之后唯一能维护得住的知识形态"。

**【原文】** 思想源头：Vannevar Bush 1945 年的 Memex，"a personal, curated knowledge store with associative trails between documents"——Bush 没解决的是"谁来做维护"。LLM 解决了。

### 1.1.4 三层架构（这是唯一必须照抄的部分）

**【原文】**

| 层 | 内容 | 谁写 | 可变性 |
|:---|:---|:---|:---|
| **Raw sources** | 原始文档：文章、论文、图片、数据文件 | 人（采集/剪辑） | **不可变**，LLM 只读不改。"This is your source of truth." |
| **The wiki** | LLM 生成的 markdown：摘要、实体页、概念页、对比、总览、综合 | **LLM 独占** | 持续重写。"You read it; the LLM writes it." |
| **The schema** | 一份文档（`CLAUDE.md` / `AGENTS.md`），规定结构、约定、工作流 | 人 + LLM 共同演化 | 慢变量，改一次要重跑 lint |

**【原文】** 关于 schema 的一句话定义：

> "This is the key configuration file — it's what makes the LLM a disciplined wiki maintainer rather than a generic chatbot."

**没有第三层，前两层必然腐化。** 这是绝大多数模仿者漏掉的地方，也是本方案 §1.3.4 的重点。

### 1.1.5 三个操作（Ingest / Query / Lint）

#### Ingest（入库编译）

**【原文】** 流程：

> "The LLM reads the source, discusses key takeaways with you, writes a summary page in the wiki, updates the index, updates relevant entity and concept pages across the wiki, and appends an entry to the log. A single source might touch 10-15 wiki pages."

**"a single source might touch 10-15 wiki pages"** —— 这是 LLM Wiki 与 RAG 最大的工程差异：RAG 的入库是 **append**（一个 chunk 进向量库，不影响别的 chunk）；LLM Wiki 的入库是 **write fan-out**（一次写 10~15 个文件的散射写）。**这条决定了你的脚本不能是"搬运"，必须是"编辑"。**

#### Query（提问）

**【原文】** 提出问题的关键洞察：

> "**good answers can be filed back into the wiki as new pages.** A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history. This way your explorations compound in the knowledge base just like ingested sources do."

**回填（file back）是 LLM Wiki 独有的机制**：RAG 的问答产物永远死在聊天记录里；LLM Wiki 的问答产物会变成新的 wiki 页。**你的库现在所有问答都死在会话里了。** 这条在 v2 里被发扬成 `crystallize`（§1.1.9）。

#### Lint（体检）

**【原文】** 检查项：`contradictions between pages` / `stale claims that newer sources have superseded` / `orphan pages with no inbound links` / `important concepts mentioned but lacking their own page` / `missing cross-references` / `data gaps that could be filled with a web search`。

**【判断】** Lint 不是可选项，它是**唯一对抗 wiki 腐化的机制**。没有 Lint 的 LLM Wiki 在 20 次 ingest 后一定退化成"另一堆没人看的笔记"。

> 你问的"**无 lint 就腐化**"就是这个意思：wiki 是活体，每次 ingest 都在改 10~15 个文件；没有定期体检（查死链、孤儿页、过期断言、矛盾），错误会**复利式**堆积——错一个链接，后面 10 次编辑都会绕开它，最后整个网没人敢信。**Lint 就是知识的"体检报告"，todo.md 是你文件层的体检，wiki-lint 是知识层的体检。**

### 1.1.6 两个特殊文件

**【原文】**

**`index.md`** —— 内容导向，是 wiki 的**目录**：每页一行，链接 + 一句话摘要 + 可选元数据（日期/来源数），按类别组织（entities / concepts / sources...）。每次 ingest 更新。**查问题时先读 index，定位候选页，再钻进去。**

> "This works surprisingly well at moderate scale (~100 sources, ~hundreds of pages) and avoids the need for embedding-based RAG infrastructure."

**`log.md`** —— 时间导向，**append-only**，记录 ingest / query / lint。格式建议：

```
## [2026-04-02] ingest | Article Title
```

于是 `grep "^## \[" log.md | tail -5` 就能拿到最近 5 条。【判断】固定前缀这一条看似琐碎，实则是让 log 同时服务人和脚本的关键——**正则友好的日志才是可维护的日志**。

### 1.1.7 规模与检索的演进路径

**【原文】** 阶段划分：

| wiki 规模 | 检索手段 | 依据 |
|:---|:---|:---|
| ≤ ~100 sources，数百页 | `index.md` 人工/LLM 遍历 | 原文明确说"surprisingly good" |
| 更大 | 本地混合检索：BM25 + 向量 + LLM 重排 | 原文推荐 [`tobi/qmd`](https://github.com/tobi/qmd)，同时提供 CLI 与 MCP server |

**【判断】** 这个路径的隐含前提：**wiki 页面的摘要质量决定了 index 检索的上限**。如果每页摘要写得含糊，index 就退化成一个文件名列表，那就该上向量检索了。反之，摘要写得好，向量库能推后很久。

→ 你问的"分界线"正解就在这里，§1.6.4 给出量化版；§1.1.12 解释 BM25/向量/重排是什么。

### 1.1.8 原文的实用技巧（可直接抄）

**【原文】**

| 技巧 | 具体做法 | 对你的用处 |
|:---|:---|:---|
| Obsidian Web Clipper | 浏览器扩展，网页转 markdown 进 raw | 收网页资料用 |
| 图片本地化 | 附件目录设为固定路径 + 绑定 "Download attachments for current file" 热键 | **你已经做到了**（`20-md/.../图片/`） |
| 图 graph view | 看谁是枢纽页、谁是孤儿页 | Lint 的可视化入口（→ §1.3.12 Obsidian 星图） |
| Marp | markdown 直接出幻灯片 | 汇报/培训 |
| Dataview | 对 frontmatter 做查询，动态生成表格 | **你最适合这个**：`manifest.csv` 的字段全在 frontmatter 里 |
| git | "The wiki is just a git repo of markdown files" | **你现在没有，这是硬缺口** |

**【原文】** 一个诚实的坑，值得记住：

> "Note that LLMs can't natively read markdown with inline images in one pass — the workaround is to have the LLM read the text first, then view some or all of the referenced images separately"

**【判断】** 这对你尤其重要：你的书有大量工程图，**图里的信息（结构剖面、曲线、参数表）LLM 一次读不进来**。所以 wiki 页里凡是引用图的地方，要么把图的关键信息**用文字转述**（"图2.1 为垫片-法兰-螺栓连接，标注 1—法兰 2—垫片 3—螺栓"），要么单独把图喂给视觉模型（成本见 §1.3.9）。**别指望"链接到图"就等于"知识已入库"。**

### 1.1.9 LLM Wiki v2 全解（你问的"第二个版本"）

**是什么**：【文献】GitHub 用户 `rohitg00`（Rohit Ghumare）的 gist *"LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory"*：[gist 链接](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)。

**时间**：【文献】gist 页面 2026-10-09 访问记录显示 7 个 revision、最近活跃 2026-10-08。**提出时间约 2026-10**（Karpathy 原版 2026-04 之后约半年），仍在变动中。

**它在 LLM Wiki 基础上加了什么**（四大块，按原文归纳）：

| #   | 提升                  | 具体内容                                                                                                                                           |
| :-- | :------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **给知识加生命周期**        | 置信度评分（每条事实挂来源数/最近核验时间/矛盾情况）；supersession（新信息取代旧结论时显式链接、旧版保留标过时）；遗忘/保留策略（按知识类型与访问调整检索优先级，含遗忘曲线思路）；四层记忆整合（working→episodic→semantic→procedural）  |
| 2   | **从页面链接升级为类型化知识图谱** | 实体带类型（people/projects/libraries/concepts），关系带语义（`uses`/`depends on`/`contradicts`/`supersedes`）；查询时沿关系遍历；**图谱是页面导航的补充，不取代可读的 wiki**            |
| 3   | **混合检索与自动化维护**      | BM25 + 向量 + 图遍历三路检索，用 **RRF** 融合；事件钩子（新源进入/会话开始/查询/写入/定时维护时触发抽取与 lint）；质量自纠（查孤儿与断链、提矛盾解决候选）；**crystallization**（把完成的研究/调试/分析固化成可溯源的一等 wiki 资料） |
| 4   | **多代理协作、隐私与输出形态**   | 多代理同步、私有/共享知识范围、入库敏感信息过滤、变更审计、可逆批量操作；呈现可按任务生成对比表/时间线/依赖图，不限于 markdown                                                                          |

**要分清的两件事【判断】**：
- v2 是**扩展**不是替代：它自己写明了 "implementation spectrum"——先有 raw/wiki/schema + 三操作，再**按规模逐项**加生命周期、图、自动化、协作。**它不是让你第一天全上。**
- 其中置信度浮点分数、遗忘曲线、last-write-wins 同步、自动矛盾修复等，v2 原文自己也标注为"待评估选项"——**没有统一基准证明有效**。社区（含我 v1 版）常把"情节/语义记忆分层""睡眠式巩固""置信度衰减"记到 Karpathy 头上，**原文没有**，是 v2 与记忆研究圈的补充。你可以用，但别当官方规范实现。

**v2 对你最有用的三条**（我会融入融合方案第 8 章）：
1. `confidence` + `superseded` 字段 → 工程参数"新旧口径并存、显式换代"直接可用；
2. **事件钩子**（ingest 前必查重、写后必 lint）→ 把"靠自觉"变成"靠流程"；
3. `crystallize` → 你的**计算书、选型过程**就是最该结晶的东西（§1.7.3）。

### 1.1.10 社区延伸与相邻研究（要分清谁说的）

**【文献】** 这条线常被混为一谈，明确切分：

| 名称 | 是什么 | 与原始 gist 的关系 |
|:---|:---|:---|
| **LLM Wiki**（Karpathy, 2026-04） | 三层 + 三操作 + index/log | 原始 |
| **LLM Wiki v2**（rohitg00, ~2026-10） | 生命周期 + 类型化图谱 + 混合检索 + 协作治理（§1.1.9） | 扩展，不是原文 |
| **A-MEM**（[arXiv 2502.12110](https://arxiv.org/abs/2502.12110), NeurIPS 2025） | Zettelkasten 式原子笔记 + 结构化属性（contextual description/keywords/tags）+ 新记忆触发旧记忆"演化" | 最接近的**设计**对应物；原文未引用。**注意【文献，2026-11-16 实读摘要修正】**：它是 **agent 对话/任务历史记忆系统**（代码 A-mem / A-mem-sys），**不是文件型知识库**——可借的是"原子化 + 属性 + 演化"三条设计，不是它的检索算法 |
| **MemGPT / Letta** | 把上下文窗口当虚拟内存，agent 自己决定换入换出 | 相邻，但自持 agent loop，锁定重 |
| **Mem0** | 从对话里被动抽取记忆 | 相邻，轻量，但记忆来自对话而非源文件 |
| **ReadAgent**（DeepMind, 2024） | 长文压缩成摘要树 + 回指指针 | 同源直觉（compile, don't re-retrieve） |
| **Rowboat / 类型化图谱派** | 主张类型化实体图而非摘要页 wiki | 与 v2 第 2 块同路，是 wiki 与 GraphRAG 的交界 |

### 1.1.11 已知的坑（原文没说的部分）

**【判断】** 以下是我认为落地时一定会撞上的，按严重度排：

| # | 坑 | 表现 | 对策 |
|:--|:---|:---|:---|
| 1 | **无 git 就无回滚** | LLM 一次改写 15 个文件，改错了整锅糊 | `git init` + 每次 ingest 一个 commit。**这是硬前提，不是优化项** |
| 2 | **合并幻觉** | 把"传热膜系数"和"总传热系数"混成一页 | 页面必须带 `sources` 字段逐条指向书+章节；无来源断言禁止写入 |
| 3 | **重复建页** | 同一概念三次 ingest 建了三个名字 | `glossary.md` 唯一译名表 + ingest 前先查重（v2 的事件钩子化） |
| 4 | **页面膨胀成第二本流水账** | 一页写到 800 行，等于把书又抄一遍 | 单页硬上限（建议 150 行），超了就拆 |
| 5 | **链接腐烂** | 改名后 `[[旧名]]` 全断 | 每次 ingest 跑死链检查；改名走"先建别名再删"两步 |
| 6 | **无 lint 就腐化** | 20 次 ingest 后没人知道哪页过期 | 固定周期 lint，产出写进 `todo` |
| 7 | **成本不可见** | 一本书 ingest 烧掉多少 token 心里没数 | 每次 ingest 在 log 里记 token/耗时，见 §1.3.9 |

### 1.1.12 专业术语全表（小白版，先扫一遍再读后面）

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

## 1.2 本库现状实测（2026-11-23 复测，库已建成）

> 2026-11-16 复测版记录的是建库前的 5 个问题（P1–P5）与差距清单 G1–G8；库已于 v3.18 建成（5 本书入库、30-wiki 542 页），本版按同一口径复测。结论：**P1/P4 闭环，P2/P3/P5 有残留；G1–G8 全部达标。**

### 1.2.1 目录与职责（命令实测）

```
D:\Shervon_KnowledgeBase\
├─ .obsidian\             Obsidian 金库配置（人机同步入口，§1.3.12）
├─ 00-inbox\              空（传送带）
├─ 10-source\             5 个入库夹，256.6 MB 原件
├─ 20-md\                 5 个 .md（4.25 MB）+ 1858 张图（119.4 MB）；_quarantine\ 空
├─ 30-wiki\               LLM Wiki 成品层（v3.13 起由 50-wiki + 30-index 合并）
│  ├─ pages\               542 页（v1.1 起 concepts/entities 合并于此；对比页也在此）
│  ├─ sources\             5 页书源页
│  ├─ openq\               3 页冲突登记；howto\ 0 页（预留）
│  └─ index.md + 4 分册 + catalog/manifest/todo/_lint/log/glossary
├─ 40-scratch\             一次性脚本、parse\ 中间产物、md 备份（~60 文件）
├─ 90-tool\                rules.md v3.18、AGENTS.wiki.md v1.2、prompt-dsh.md v3.3、VERSION=3.18
│  └─ scripts\              15 个脚本（§1.3.7）
└─ .git\                   6 commits；remote=github.com/Shervon-yu/Shervon-KnowledgeBase.git
```

### 1.2.2 全库 md 总量（"多少字/MB"实测答案）

| 项 | 实测值（2026-11-23） |
|:---|---:|
| 20-md | 5 本、4,453,821 B ≈ **4.25 MB**、2,703,618 字符 ≈ **90.1 万汉字**（按 3 B/汉字折） |
| 20-md 行数 / 页锚点 | 10382/464、8912/398、12527/538、2706/0、6334/459（顺序：GBT/化工原理/搅拌/气液搅拌釜/混合原理） |
| 30-wiki | 563 md、2,386,157 B ≈ **2.27 MB**、1,351,261 字符 ≈ **45.0 万汉字**（pages 542 + sources 5 + openq 3 + 索引类） |
| 图片 | **1858 个 / 125,192,558 B ≈ 119.4 MB**（每本 337/426/561/137/397） |
| 索引 | 4 分册 550 条（化工原理 153、搅拌与混合设备 287、气液搅拌釜γ-CT 68、压力容器标准 42） |
| 质检 | check-links 5 本 unresolved=0；wiki-lint 页面 550、问题 0 |

**300 本书外推【估计】**（按本库实测均量）：md 300 × 0.85 MB ≈ **255 MB ≈ 8,500 万汉字**；图片 300 × 372 张 ≈ **11 万张**、300 × 23.9 MB ≈ **7.2 GB**。结论不变：图必须"按需喂"，20-md 的图不能全进 git（§1.3.11）。

### 1.2.3 五个实测问题（2026-11-16 提出）——复测结论

| # | 问题（2026-11-16） | 复测（2026-11-23） | 状态 |
|:--|:---|:---|:--|
| P1 | 86 条死链（%20 未解码） | check-links 5 本全 `unresolved=0`（refs 337/426/561/137/397） | ✅ 闭环 |
| P2 | 163 个假标题（占 46%） | 全库 `## (n)` 型只剩 **14 条，全在化工原理书**：4112 风压、5367 计算 v、7197 并流逆流传热面积、8262 校核总传热系数、10124 吸收剂再循环、10446 提高吸收塔回收率、10673 塔径计算、12294 芬斯克方程、12501 塔底产品组成、13271 计算塔径、14195 空气消耗量、15578 金属热导率、15593 非金属热导率、15921 无缝钢管 | ⚠️ 残留 14 |
| P3 | 无页码锚点 | 4/5 本有 `<!-- page-N -->`；**气液搅拌釜无锚点**（仅 `<!-- page-appendix -->`，2706 行） | ⚠️ 缺 1 本 |
| P4 | 无任何版本历史 | git 6 commits + GitHub 私有仓库 | ✅ 闭环 |
| P5 | 检索索引只覆盖 1/3 的书 | kb 库 120 页（120/542=22%），且 **119/120 个文档路径仍指向旧 `50-wiki\concepts\`**（索引建于 v3.13 合并与 concepts→pages 改名之前） | ⚠️ 需重导入 |

**残留处理建议**：P2 → 对化工原理重跑标题体检降级（rules §16 口径）；P3 → 气液搅拌釜重跑 md-anchor.ps1 补锚点后重建；P5 → 清空 kb 库、按 `30-wiki\pages` 重导入（或 DSH 重索引），**等用户定夺**。

### 1.2.4 现状 → LLM Wiki 三层映射（复测）

| LLM Wiki 层 | 2026-11-16 判定 | 2026-11-23 复测 |
|:---|:---|:---|
| Raw sources | ✅ 10-source 不动点 | ✅ 5 本 256.6 MB，只增不改 |
| Raw 的派生 | ⚠️ 20-md 属 raw 层、非 wiki 层 | ✅ 由 ingest-build.ps1 生成（rules §16），脚本独占、可删了重跑 |
| Wiki | ❌ 不存在 | ✅ 30-wiki：542 页 + sources 5 + openq 3 + index/log/glossary |
| Schema | ⚠️ rules.md 只规定加工 | ✅ rules.md v3.18（加工）+ AGENTS.wiki.md v1.2（编辑）分工 |

「20-md 不是 wiki 层」的三条理由（生命周期不同 / 形态不同 / 写者不同）与「rules.md 不是编辑 schema」的判断已被建设验证，原文见 git 历史。

### 1.2.5 差距清单 G1–G8（复测）

| ID | 差距 | 验收标准（原） | 复测 |
|:--|:---|:---|:--|
| G1 | 无综合层 | ≥10 概念页、每页 ≥2 入链 | ✅ pages 542 页（lint 判据 MinInbound=2） |
| G2 | 无跨书链接 | ≥3 条跨书引用 | ✅ 跨书页已建（pages\搅拌功率计算、pages\层流域搅拌器混合效率对比 等）；openq 3 条均为跨书冲突 |
| G3 | 无冲突登记 | openq ≥3 条 | ✅ 3 条（微米颗粒传质系数与转速的关系矛盾 / 液液最小临界转速手册式与本书式冲突 / 脂肪油氢化选择性两版解释并存） |
| G4 | 无版本控制 | git log ≥1 | ✅ 6 commits + GitHub 私有仓库 |
| G5 | 无知识级 log | log 有 ingest/query/lint 条目 | ✅ 30-wiki\log.md 105 行 |
| G6 | 引用粒度不足 | 断言落到《书名》§节号 或 #L | ✅ rules §14 强制双轨，lint 0 问题 |
| G7 | 图未转述 | 被引图 ≥1 句转述 | ✅ lint 十项含「图无转述」，实测 0 条 |
| G8 | 无术语唯一表 | glossary ≥30 条 | ✅ 30-wiki\glossary.md 已建（33 行） |

### 1.2.6 以 300 本书为预设的差距重估（v2 新增）

**v1 版按"3 本书"设计，你在第 9 问纠正了我：预设应为 300 本书 + 零散资料。** 哪些设计会因此在 300 本下坏掉？哪些反而更稳？

| 设计                  | 3 本书时     | 300 本书时会怎样                                | 处理                                                                 |
| :------------------ | :-------- | :---------------------------------------- | :----------------------------------------------------------------- |
| `index.md` 单文件      | 50 行，随便读  | 7500 行 ≈ 45 万字符，LLM 一次读不下                 | index 必须**分册**：`index.md` 只放主题分类 + 每类一行，每类再挂 `index-XX.md`（§1.6.4） |
| 每次提问先读 index        | 无感        | 读 45 万字符 = 30 万 token，一问烧几块钱              | 提问先 grep index，再按类读子索引                                             |
| `glossary.md` 单文件   | 30 条      | 术语可能 3000+ 条                              | glossary 按领域拆（`glossary-密封/搅拌/传热…`）或直接由脚本从 frontmatter 生成          |
| 图片全部喂视觉模型           | 无感（876 张） | 9 万张图 × 1.2K token = 1 亿 token，免费档也要排队跑几天 | **按需喂**：ingest 时只喂"被 wiki 页引用且无文字转述"的图（§1.3.5）                     |
| 20-md 全进 git        | 42 MB 无感  | ~70 GB 图片，GitHub 仓库上限 5 GB                | 图不推 GitHub，或用 LFS（§1.3.11）                                         |
| 14 页首批清单            | 够         | 只是第一本书的样板                                 | 每本书"编译"产出 20~25 页；300 本 → ~7500 页，需 lint 自动化（§1.3.7）               |
| `wiki-lint.ps1` 手动跑 | 可以        | 7500 页手动跑不过来                              | lint 挂到 ingest 流程里（v2 事件钩子思想），每次 ingest 自动跑                        |
| Obsidian 单 vault    | 可以        | 7500 页星图会糊成毛球                             | 用 folder 限定视图 + 按领域分 vault 或 bookmark（§1.3.12）                     |

**结论【判断】**：300 本书的规模让"分层、分册、自动化、按需喂图"从"可选优化"变成"必备设计"。v2 方案已全部按此口径重写。

---

## 1.3 改造方案 v2 的落地实况（2026-11-23 复测）

> 本节方案（2026-11-16 起草）已全部执行完毕，库已建成并超出原规模（方案按 3 本试点 → 实际 5 本全部入库、542 页）。保留原小节编号，逐节标注「方案 → 落地」差异；现行规范以 `90-tool\rules.md` v3.18、`AGENTS.wiki.md` v1.2、`prompt-dsh.md` v3.3 为准。

### 1.3.1 目标结构（方案 50-wiki 七目录 → 落地 30-wiki 五目录）

```
30-wiki\                    ← 方案的 50-wiki（v3.13 与 30-index 合并为单一层）
├─ pages\       概念/实体/对比页（方案 concepts+entities+comparisons，v1.1 起合并；542 页）
├─ sources\     书源页（与方案一致；5 本）
├─ howto\       做法页（预留，0 页）
├─ openq\       冲突与未决问题（与方案一致；3 页）
├─ index.md + 4 分册   总目录（方案单文件 → 落地自动分册）
├─ glossary.md  术语唯一表（33 行）
└─ log.md       append-only 时间线（105 行）
```

> 差异：① 50-wiki 与 30-index 合并为 30-wiki（机器区 + 人写区同层，rules §12）；② concepts/entities 并入 pages（v1.1）；③ comparisons 未单独建目录（对比页在 pages 内）。

### 1.3.2 命名对照（落地）

| 位置 | 方案 | 落地 |
|:---|:---|:---|
| 综合层 | 50-wiki\ | 30-wiki\（v3.13） |
| 页面分类 | concepts/entities/sources/comparisons/howto/openq | pages/sources/howto/openq（v1.1） |
| 契约文件 | AGENTS.wiki.md | 同（v1.2） |
| 脚本 | wiki-lint/wiki-index/md-anchor | 15 个（§1.3.7） |

### 1.3.3 rules.md（方案 v2.3→v3.0 加四节；落地 v3.18，§12–§16）

| 方案 | 落地 |
|:---|:---|
| §12 50-wiki 层（写者边界） | §12「30-wiki 层」：五目录 + glossary + log；§12.1 建页判据：一断言簇一页 |
| §13 页面规范 | §13 页面契约：frontmatter 十字段、正文 ≤300 行 |
| §14 引用约定 | §14 引用格式：《书名》+§节号+#L 双轨 |
| §15 三操作 SOP | §15 SOP：lint 十项（死链/孤儿/无来源/超长/同义重复/过期断言/index 漂移/图无转述/别名遮蔽/question）+ query 四步 |
| （方案无） | §16 解析产物生成规范：ingest-build.ps1 的合同（七行验收） |

### 1.3.4 AGENTS.wiki.md（方案八条 → 落地 v1.2，§0–§6）

七节：§0 写者边界（Obsidian 对人只读）/ §1 唯一译名（glossary）/ §2 断言必须有来源 / §3 页面硬约束 / §4 冲突与换代（不删旧断言、标 superseded）/ §5 Ingest 六步（查重是第 0 步）/ §6 Query 四步。

### 1.3.5 三操作 SOP（方案 Ingest 9 步 → 落地 12 步；lint 八项 → 十项）

- **Ingest**：prompt-dsh.md v3.3 十二步入库 SOP；书入库链 ingest.ps1 → MinerU 解析 → ingest-build.ps1（生成+定名+图链自检+七行验收，rules §16）→ check-links → catalog/wiki-index；收尾自动 commit。
- **Query**：AGENTS.wiki.md §6 四步（grep index → 读候选页 → 带引用回答 → 回填判定）。
- **Lint**：wiki-lint.ps1 十项（§1.3.3），2026-11-23 实测：页面 550、问题 0。

### 1.3.6 首批页面清单（方案 7 页 → 全部建成并大幅超出）

- sources 5 页：5 本书全部建成（方案原列 2 本）。
- 首批概念/实体主题均已入库（现属 pages）；跨书页实测存在：pages\搅拌功率计算.md、pages\层流域搅拌器混合效率对比.md。
- 方案第 7 页「搅拌功率关联式对比」的跨书冲突已按规则登记 openq（3 条，见 §1.2.5 G3）。
- 实际规模 542 页（方案预期首批 7 页、每本 20~25 页；粒度更细，一断言簇一页）。

### 1.3.7 脚本层（方案三脚本 → 落地 15 个）

```
90-tool\scripts\
├─ ingest.ps1          入库总入口（32.3 KB）
├─ figures.ps1         MinerU 图归档
├─ ingest-build.ps1    生成 20-md + 七行验收（rules §16）
├─ md-build.ps1        主构建（31.6 KB）
├─ md-anchor.ps1       补页码锚点（方案已有，落地保留）
├─ check-links.ps1     死链自检/修复（-Fix）
├─ catalog.ps1         书目表
├─ wiki-index.ps1      索引生成（自动分册）
├─ wiki-lint.ps1       十项体检
├─ fig-names.ps1 / refs-remap.ps1   图名与引用重映射
├─ figure-index.py / coverage.py    图索引与覆盖报告
├─ precommit-guard.ps1 提交前闸门
└─ budget-watch.ps1    成本看门狗（20 元上限，prompt-dsh.md）
```

### 1.3.8 分阶段执行（P0–P4 全部完成）

| 阶段 | 方案验收 | 落地 |
|:---|:---|:--|
| P0 打地基 | git log ≥1；AGENTS.wiki.md ≥100 行 | ✅ git 6 commits + GitHub 私有仓库；AGENTS.wiki.md v1.2；30-wiki 骨架；rules v3.18 |
| P1 单本试点 | 触及 10~15 页；死链 0 | ✅ 化工原理（首本，153 页）；死链 0 |
| P2 铺开 | 跨书 ≥3；冲突 ≥3 | ✅ 5 本全部入库（超出方案的 3 本）；openq 3 条 |
| P3 闭环 | lint 全过；index 自动生成 | ✅ wiki-lint 0 问题；index 4 分册 550 条 |
| P4 规模 | 常态化 | ✅ 15 脚本 + 看门狗 + 会话开场 git status 审计 |

### 1.3.9 成本账（方案估算 → 实际账单）

- 方案估算表（3.9.1 价格档 deepseek-flash 主推 / 3.9.2 单本 ¥0.44–1.31 / 3.9.3 单问分钱级 / 3.9.4 300 本总账 ¥153–305）为估算口径，原文见 git 历史；现行价格口径见 prompt-dsh.md。
- **实际锚点**：搅拌与混合设备设计选用手册（最大一本，12527 行 / 561 图）谷价入库实耗 **¥5.92**（≈折峰 ¥11.9，prompt-dsh.md 实测记录），高于估算上限 ¥1.31。现预算口径：**20 元上限**（峰价=谷价×2），由 budget-watch.ps1 看门狗强制。

### 1.3.10 风险与回滚（机制全部落地）

方案 7 条风险 → 对应机制已建：git reset 回滚（git 已接）；20-md 脚本独占、ingest 不覆盖已有 md；超长页 lint 拆页；图转述 lint 强制；Obsidian 人改由 git status 暴露并汇报（§1.3.12）。

### 1.3.11 git 本地 + GitHub（方案 → 已落地）

- ✅ git 已接：6 commits，基线 912a7eb「chore: 重建基线—当前成品快照」，最新 6dd94db「docs: 修复…Obsidian 灰链」。
- ✅ remote = https://github.com/Shervon-yu/Shervon-KnowledgeBase.git（私有）。
- ⚠️ 工作区现有 3 个未提交改动：30-wiki\index-化工原理.md、30-wiki\index-搅拌与混合设备.md、30-wiki\pages\搅拌功率计算.md——按 §1.3.12 惯例下次会话开场汇报，吸收或还原由你定。

### 1.3.12 Obsidian 人机同步（方案 → 已落地）

- ✅ .obsidian\ 金库已建；「人对 Obsidian 只读」写入 AGENTS.wiki.md §0。
- ✅ 审计 = 会话开场 `git status --short`：有未提交改动逐文件汇报（当前 3 个待处理项见 §1.3.11）。
- 星图由 Obsidian 客户端按 [[wikilink]] 渲染，MCP 不能代画；vault 指向 D:\Shervon_KnowledgeBase 即可。

---

## 1.4 RAG：检索增强生成

### 1.4.1 出处与一句话定义

**【文献】** RAG 由 Lewis et al. 提出（NeurIPS 2020, *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, Meta AI）。

一句话定义：**提问时才去资料里翻答案片段，塞进上下文让 LLM 生成回答。** 核心等式：

> RAG = 检索（retrieve）+ 生成（generate）

检索解决"LLM 没背过/背不进去"，生成解决"怎么把找到的片段变成人话"。它要解决的问题只有一个：**LLM 的上下文窗口装不下你全部资料，所以只装相关的。**

**和你库的关系【实测】**：你其实已经有一只脚在 RAG 里了——DSH 的 `kb` 向量库（试点书曾 836 chunk，2026-11-18 出库后为空）就是标准的"切块→嵌入→检索"后半段。缺的是另外半只脚：索引陈旧——kb 库 120 页、119/120 路径仍指旧目录（§1.2.3 问题 5）。

### 1.4.2 九段流水线（对照你的库）

| # | 阶段 | 干什么 | 你的库现状 |
|:--|:---|:---|:---|
| 1 | **采集** | 拿到原始文件 | ✅ `10-source\` |
| 2 | **解析** | PDF/网页 → 结构化文本 | ✅ MinerU 管线（ingest.ps1） |
| 3 | **清洗** | 去页眉页脚、乱码、水印 | ⚠️ 半自动（图注残片 `_a.jpg` 未清） |
| 4 | **切块 chunk** | 把长文切成 512~1024 token 的小块 | ⚠️ 试点书切进了 kb 库，但**按假标题切坏了**（§1.2.3 问题 2：163 个假 h2） |
| 5 | **富化** | 每块加元数据：书名/章节/页码/标题层级 | ❌ 无页码锚点（§1.8.8）；标题层级被压平 |
| 6 | **嵌入 embedding** | 每块转成向量 | ✅ kb 库已做（1/3 覆盖） |
| 7 | **索引** | 向量进数据库，建检索结构 | ✅ 同上 |
| 8 | **检索 retrieve** | 问句转向量 → 找最像的 top-k 块 | ✅ 同上 |
| 9 | **生成 generate** | 把 top-k 块 + 问题塞给 LLM 生成答案 | ✅ DSH 注入 |

**【判断】** 九段里你已走通 1/2/6/7/8/9，卡在 3/4/5。而 3/4/5 恰好决定检索质量上限（garbage in, garbage out）。**先修 %20 死链和假标题，比上任何新模型都划算。**

### 1.4.3 关键参数（经验值，非铁律）

| 参数 | 经验值 | 说明 |
|:---|:---|:---|
| chunk 大小 | 512~1024 token（中文 ~800 字~1600 字） | 太小断语义，太大稀释相关性 |
| overlap | 10~20% | 防止关键句正好落在切缝上 |
| top-k 召回 | 召回 20~50，重排后送 5~8 | 召回贪多（便宜），送 LLM 贪精（贵） |
| 稀疏 vs 稠密 | 精确词用 BM25，模糊语义用向量 | 混合最好（下节） |

### 1.4.4 检索策略：从"关键词"到"混合+重排"

| 策略 | 原理 | 优点 | 缺点 |
|:---|:---|:---|:---|
| **BM25（稀疏）** | 按词频+稀有度打分 | 精确术语（"端面比压""pv 值"）一打一个准；免费、可解释 | 换个说法就找不到（"密封环" vs "摩擦副"） |
| **向量（稠密）** | 语义相似度 | 模糊问法也能中 | 专有名词可能漂移；要建库要花钱 |
| **混合** | 两路各召回再融合 | 取长补短，工程事实标准 | 要维护两套索引 |
| **RRF 融合** | 按"两路排名倒数和"合并 | 免调权重的稳健融合 | 有出处：Cormack et al. 2009（k=60 是常用参数） |
| **重排 rerank** | 召回一堆后用更精的模型重排 | **最划算的单点提升** | 多一次模型调用；常用 bge-reranker 系列 |
| **Lost in the Middle** | 位置先验：LLM 对上下文中间部分记得最差 | 把最相关的块放首尾 | 【文献】Liu et al. 2023，U 形注意力曲线 |

**【判断】** 你 300 本书的检索层最终形态就是这一节：BM25 + 向量 + RRF + 重排——这正是 qmd 干的事（§1.6.4 第三档）。

### 1.4.5 RAG 的七条死穴（它为什么回答不了你的问题）

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

### 1.4.6 怎么评估 RAG 好坏：RAGAS 四指标

**【文献】** RAGAS（explodinggradients/ragas）四指标，前三个免金标准，第四个要人工标注：

| 指标 | 问什么 | 说明 |
|:---|:---|:---|
| **faithfulness** 忠实度 | 答案里的每句话是否都能在检索块里找到依据 | 防幻觉 |
| **answer_relevancy** 答案相关性 | 答案是否紧扣问题 | 防跑题 |
| **context_precision** 上下文精度 | 检索块里相关的排得靠不靠前 | 防"对的在第 20 位" |
| **context_recall** 上下文召回 | 该检索到的都检索到了吗 | 需金标准答案 |

### 1.4.7 什么场景不该用 RAG（五条）

1. **要长期维护的知识**：每次从零拼 = 每次重新付检索税，且无累积 → LLM Wiki。
2. **要跨书综合/对比**：死穴 2/4 → 先建对比页再检索。
3. **资料量小**（你的现状 2.4 MB）：grep + LLM 直接读全文，RAG 是杀鸡用牛刀。
4. **有精确出处要求**：死穴 6 → 需要富化元数据。
5. **频繁更新的规范类资料**：向量库更新滞后，检索出旧值 → 规范页用 wiki 页 + superseded 管理。

### 1.4.8 生态速查

| 项目 | 一句话 |
|:---|:---|
| [ragflow](https://github.com/infiniflow/ragflow) | 全家桶带 UI，DeepDoc 解析 |
| [llama_index](https://github.com/run-llama/llama_index) | 框架之王，索引器抽象 |
| [haystack](https://github.com/deepset-ai/haystack) | 企业级管道框架 |
| [ragas](https://github.com/explodinggradients/ragas) | 评估 |
| [dspy](https://github.com/stanfordnlp/dspy) | 把提示词当程序编译优化 |
| 解析器五件套 | MinerU（你已有）/ [docling](https://github.com/docling-project/docling) / [marker](https://github.com/VikParuchuri/marker) / [unstructured](https://github.com/Unstructured-IO/unstructured) / [markitdown](https://github.com/microsoft/markitdown) |

### 1.4.9 RAG 在 300 本书库下的形态与成本（v2 新增）

**【判断】** 300 本书全进向量库 = ~1 万个 chunk（每本 ~35 chunk）→ 嵌入费几百元、索引几个 GB；单问 ¥0.02~0.09（§1.3.9）。技术上完全可行，**但它仍然只有"片段检索"，没有"知识网"**——死穴 1/2/4 一条不少。所以结论不变：

> **RAG 是地基，LLM Wiki 是楼。** 你的库里 RAG 负责"哪本书哪一页"，LLM Wiki 负责"这件事整体是怎么回事"。

---

## 1.5 GraphRAG：给 RAG 补"全局地图"

### 1.5.1 出处

**【文献】** Microsoft Research 2024-02, Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*；开源实现 [microsoft/graphrag](https://github.com/microsoft/graphrag)。

要解决的问题一句话：**RAG 只能答"一个片段里写着的事"，答不了"散落在全书、需要拼起来的事"**——比如"这套标准体系的整体演进""这些实验的共同结论"。GraphRAG 的答案是：**入库时把资料抽成实体关系图，再按社区做全局摘要。**

### 1.5.2 五步索引（入库时发生，这是它贵的原因）

| 步 | 动作 | LLM 调用？ |
|:--|:---|:---|
| 1 | 把文档切成 text units（~600 token） | 否 |
| 2 | 每个 unit 让 LLM 抽实体（人/组织/概念…）和关系 | **是（全量调用）** |
| 3 | 合并全库实体，消歧去重（"泵"与"pump"合一） | 否 |
| 4 | **Leiden 算法**做社区检测，把图切成"话题组团" | 否（【文献】Traag et al. 2019 算法） |
| 5 | 每个社区让 LLM 写一份**社区报告**（摘要+内部关系） | **是（全量调用）** |

查询时（Global 模式）：问题 → 匹配相关社区 → 把多份社区报告 map-reduce 成最终答案。**这就是"全局问答"的来历。**

### 1.5.3 三种查询模式

| 模式 | 回答什么 | 怎么工作 |
|:---|:---|:---|
| **Global** | "总体上…" | 社区报告汇总（map-reduce） |
| **Local** | "某实体相关…" | 从实体出发在图上找邻居 + 关联原始 text unit |
| **DRIFT** | 混合 | 先 Global 找社区，再 Local 钻细节 |

另有 **LazyGraphRAG**（2024-11）：把最贵的"抽取+社区报告"推迟到查询时才做相关部分，索引成本降到接近纯向量检索——是"预算版 GraphRAG"。

### 1.5.4 成本：为什么对你先别上

**【估计】** 你的书（当时 3 本口径）：md 文本 ~60 万 token → 切成 ~1000 个 text units → 全量实体抽取 + 社区报告 ≈ **300~800 万 token 的 LLM 调用**（中文实体抽取尤其费；现已 5 本，同比例约 ×1.7）。**比 LLM Wiki 编译同三本书贵 3~8 倍。**
300 本书：**几千元级**（对比 LLM Wiki 几百元级，§1.3.9）。加上图每 3 本书才约 1000 个社区、300 本书的图规模与社区检测质量在中文语料上尚无基准——**性价比目前对你不成立。**

### 1.5.5 变体与替代品

| 项目 | 特点 | 对你的相关性 |
|:---|:---|:---|
| [LightRAG](https://github.com/HKUDS/LightRAG) | 双级（low/high）检索 + 增量更新；arXiv 2410.05779 | **最现实**：只抽 4 类实体、图谱当"概念路由"用；跨 5 本对比时值得试 |
| [nano-graphrag](https://github.com/gusye1234/nano-graphrag) | 1000 行教学实现 | 学原理用 |
| [graphiti](https://github.com/getzep/graphiti) | bi-temporal（时间双轨）知识图 | 规范更新场景的理论参考 |
| [cognee](https://github.com/topoteretes/cognee) | 会话→图谱记忆 | 相邻 |
| [llm-graph-builder](https://github.com/neo4j-labs/llm-graph-builder) | Neo4j + 可视化 | 想玩图数据库时 |

### 1.5.6 六个坑（社区共识 + 我的判断）

1. **实体消歧难**：同名不同物、同物不同名（"搅拌器"vs"搅拌桨"vs"叶轮"）。
2. **抽取幻觉**：LLM 会编出文档里没有的关系——图谱越密，幻觉越难查。
3. **图更新难**：新书进来要重新消歧、重新社区检测，增量更新是研究级难题（LightRAG 只部分解决）。
4. **社区摘要漂移**：社区报告是 LLM 写的一次性摘要，原始出处锚点被稀释（死穴 6 复现）。
5. **评估难**：没有一个像 RAGAS 那样公认的指标集。
6. **中文弱**：主流图管线的实体识别默认英文，中文工程术语需要换模型+调优。

### 1.5.7 GraphRAG 与 LLM Wiki 的关系

| | LLM Wiki | GraphRAG |
|:---|:---|:---|
| 知识形态 | **人可读的页面网**（`[[链接]]`） | 机器图（节点+边+社区报告） |
| 综合单位 | 概念页（一页一个主题） | 社区报告（一团一个话题） |
| 出处锚点 | 逐句可落 §节号/行号 | 稀释 |
| 维护成本 | 低（每次 ingest 改 10~15 页） | 高（全量重建/增量难） |
| 全局问答 | 靠跨书对比页 + index 导航 | 天生擅长 |

**【判断】** 两者其实是同一个思想的两条技术路线：**都在"入库时综合一次"**。差别在综合的载体是"页面"还是"图"。对你这种**要被人反复翻看、逐条核对出处**的工程库，页面网优先；图是锦上添花（v2 也持此立场：图是导航补充，不取代可读 wiki）。

---

## 1.6 三者对照、决策树与量化分界线

### 1.6.1 三方案一张表

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

### 1.6.2 决策树

```
你的问题是什么类型？
├─ "哪本书哪一页写着 X"（找片段） → 资料小：grep；资料大：RAG
└─ "这件事整体是怎么回事/两本书说法为何不同"（综合）
    └─ 库 ≤ 数百页 → LLM Wiki（index + 页面网）
    └─ 库达万页级、且问题高度全局 → 才考虑 GraphRAG
```

### 1.6.3 可以叠加：三种"记忆"各管一段

| 记忆类型 | 手段 | 管什么 |
|:---|:---|:---|
| **语义记忆**（知识本体） | LLM Wiki | 概念、口径、参数、结论 |
| **检索记忆**（原文索引） | RAG/grep | 片段定位、原文原话 |
| **关系记忆**（结构导航） | 轻量图谱（v2 类型化链接 / LightRAG） | 谁依赖谁、谁取代谁 |

**三者不是竞品，是三层。** 你最终形态 = LLM Wiki 主干 + grep/index 兜底 + （规模到了再加）轻量图谱。

### 1.6.4 量化分界线（你问的第 1 题的正解）

**【实测+估计】** 以"md 语料总字节"为判据（图片不参与检索，只按需喂视觉模型）：

| 档位 | md 语料规模 | 对应你的情况 | 检索手段 |
|:---|:---|:---|:---|
| **A 档** | ≤ 5 MB（≤ ~350 万汉字 ≈ 230 万 token） | **你现在（4.25 MB / 90 万汉字）** | index.md + grep，**不需要任何向量库** |
| **B 档** | 5~50 MB（≤ 50 本） | 几年后的你 | 全文检索（BM25）+ index 分册；向量可选 |
| **C 档** | 50 MB~数 GB（50~300 本） | **300 本书口径的你（~240 MB）** | **混合检索**：BM25+向量+RRF+LLM 重排（qmd） |
| **D 档** | 万页级、跨学科全局问题 | 远超 300 本 | 再加 GraphRAG/LightRAG 类图谱层 |

**判据要点【判断】**：
1. 分界看**可检索文本量**，不是图片量——图片走"按需喂视觉模型"，不进检索索引。
2. A→B 的界是"index 单文件读不动 + grep 命中太多"（index > 数百页）；C 的界是"BM25 召回噪声大、需要语义兜底"；D 的界是"全局聚合问题成为刚需"。
3. **你现在在 A 档，LLM Wiki 就是 A 档的正解**；300 本书落在 C 档，但 C 档的"向量"部分仍然是地基（RAG），"页面网"部分仍然是楼（LLM Wiki）——两者不互斥。
4. 反过来：**md ≤5 MB 时上 RAG 是浪费**——这正是你现在的状态（4.25 MB），所以"当年 kb 只进了 1 本试点书、其余靠 grep"这件事，正确的解法不是把 5 本书都塞进向量库，而是**wiki 已建成（542 页）**（§1.8.10）。

### 1.6.5 升级触发器（到哪一步就升哪一档）

| 触发条件                   | 动作                           |
| :--------------------- | :--------------------------- |
| `index.md` > 300 行     | 按领域分册（脚本自动）                  |
| grep 一次命中 > 200 条      | 上 BM25 全文检索（qmd CLI 即可，不需向量） |
| wiki 页 > 200 且模糊问法开始失手 | 上向量 + RRF + 重排（qmd MCP）      |
| 跨 5 本对比成为高频需求          | 试 LightRAG 只抽 4 类实体          |
| 万页 + 全局科研问题            | 才考虑完整 GraphRAG               |

---

## 1.7 融合方案：九个方案逐份实读 + 十个来源取长（第三版重写）

> 这一版不是"抄 idea"：九个外部方案（八个仓库 + 一个内置功能）的技术文档我逐份读了一遍（2026-11-16，全部是一手 README / gist 原文 / arXiv 摘要页）。顺序是：先自查 v2 说错的地方（§1.7.0），再看每个方案"一手事实 + 借什么 + 不借什么"（§1.7.1），然后试算"照搬现成方案会怎样"（§1.7.2）、取舍总表（§1.7.3）、融合架构（§1.7.4）、比单一方案高级在哪（§1.7.5），最后给落地顺序（§1.7.6）。

### 1.7.0 自查：v2 里被一手文档推翻的 9 处（你让我自己找的"漏洞"）

**这是你留的作业。** 逐份读一手文档后，v2 第 8 章有 9 处事实性错误——不是笔误，是会让选型跑偏的错：

| # | v2 原文（错） | 一手文档事实（2026-11-16 实读） | 为什么要紧 |
|:--|:---|:---|:---|
| **E1** | geronimo-iia/llm-wiki "**19 个 MCP 工具**" | README 首行：**"24 MCP tools. One Rust binary. No LLM inside."** | 低估工具面，就会低估"技能层"的必要性——它自己用 17 个 skill 去驱动这 24 个工具 |
| **E2** | llm-wiki-skills "**8 个 skill**"，名单只有 8 个 | 实为 **17 个**：setup / spaces / config / schema / bootstrap / content / ingest / crystallize / research / lint / graph / frontmatter / configure-hugo / stats / review / export / migrate | 我漏的 7 个（spaces / schema / content / stats / review / export / migrate）恰好是**多空间、schema、导出、评审**——都能等规模化了才需要，但设计时必须预留 |
| **E3** | §1.3.2 说 geronimo 的综合层是 "**content/（大致）**" | **没有 content/ 目录约定**。综合层 = frontmatter 的 `type:` 字段 + `wiki_content_*` 工具组；目录结构由用户自定 | 它把"页面类型"做成 **schema 字段**而不是目录。这比我 v2 的"五类页面五个目录"更灵活——类型可加，目录不重排 |
| **E4** | qmd 只说"BM25 + 向量 + LLM 重排" | 它自称的 **key feature 是 context 树**：`qmd context add qmd://notes "这批笔记讲什么"`，检索命中时把上下文一并发回——原文理由是 "allows LLMs to make much better contextual choices"。另有 **HyDE**、typed query expansion（lex→BM25 / vec→向量）、SQLite 索引、MCP 五工具、HTTP transport | 漏掉 context 树，就漏掉了它对"LLM 需要上下文而非片段"的正面回答。这正是 LLM Wiki 可以**零成本先实现**的部分（把摘要写进 frontmatter） |
| **E5** | dataview 是"**SQL 式**查询" | README 原文：**DQL 是 "pipeline-based, vaguely SQL-looking"**；另三种模式是 Inline Expressions、**DataviewJS**、Inline JS；数据源 = frontmatter YAML + inline fields（`Key:: Value`） | 说"SQL"会被拿去当 SQL 写，一写就报错。DQL 是管道；最强的是 DataviewJS |
| **E6** | A-MEM"最接近的学术对应物" | 它是 **agent 对话/任务历史记忆系统**（Zettelkasten 式原子记忆 + 结构化属性 + 记忆演化），**不是文件型知识库**；代码在 A-mem（评估）与 A-mem-sys | 拿它当"知识库论文"会误判可迁移性。只能借三条设计：原子化、结构化属性、演化触发 |
| **E7** | 价格表里**没有 DeepSeek 官方视觉价** | DeepSeek 官方 `deepseek-flash` **带 Vision ✓**、1M 上下文；off-peak 输入 $0.15/M、输出 $0.6/M（cache-hit 仅 $0.003/M），peak 翻倍 | 这正是你这次点名的口径；也是"一把 key 走完文本+图"的最省事方案。详见 §1.3.9.1、§1.8.2 |
| **E8** | 表里把 "**Obsidian graph view + MCP**" 当成一个"方案/仓库" | graph view 是 **Obsidian 内置功能**，不是仓库。文档在 help.obsidian.md（我 fetch `help.obsidian.md/plugins/graph` 时被 301 到 obsidian.md 且未自动跟随——半个失败，已用 Karpathy 原文佐证其角色） | "十个来源"里它只能算**功能**，不能算**项目**；否则数字虚高 |
| **E9** | qmd 只有一句话 | 实读后它至少值四条：本地 GGUF（node-llama-cpp）**离线**跑嵌入与重排；SQLite 索引；MCP 五工具（query / get / multi_get / status / metadata）；可选**远程度重排**（remote-typesafe，资源界限 2 MiB 请求 / 8 MiB 响应 / 30 s / 64 文档） | 决定"什么时候上 qmd、上它的哪一层"：C 档先 CLI，MCP 留给 agent 直连 |

> **教训**：v2 的错集中在两类——**数量类事实**（19/24、8/17）与**深度类事实**（qmd、dataview、A-MEM 的定位）。写这类文档，凡是"数字 + 声称是它的核心特性"，都必须回一手文档对一遍。

### 1.7.1 九个方案 × 一手事实 × 我借什么

> 口径：1–9 是外部方案（8 个仓库 + 1 个内置功能），10 是你自己的资产。**每个方案只留一条最值钱的 idea，其余明确不借。**

| #   | 来源（一手文档）                                                                                                   | 实读到的最硬事实                                                                                                                                                                                                                                                                                                                                                                                                                                                                | 最值钱的 idea（借）                                                                            | 明确不借                                               |
| :-- | :--------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------- | :------------------------------------------------- |
| 1   | **Karpathy gist**（2026-04，[原文](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)）         | 三层（Raw sources / The wiki / The schema）+ 三操作（Ingest / Query / Lint）；原话 "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase"、"The wiki is just a git repo of markdown files"；Query 输出形态包含 markdown 页、对比表、**Marp 幻灯片**、matplotlib 图、canvas；结尾 Note：一切 modular，目录结构自定                                                                                                                                                                                | 三层 + 三操作 + `index.md`/`log.md` 双索引 + "LLM 独占写 wiki"                                     | 它的"够用就行"没有工程化：无冲突登记、无生命周期、无版本审计——单靠 gist 走不到 300 本 |
| 2   | **rohitg00 LLM Wiki v2**（~2026-10，[原文](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)） | 基于 agentmemory（20K+ stars）；生命周期 = confidence scoring / supersession / Ebbinghaus 遗忘 / 四层记忆（working→episodic→semantic→procedural）；图谱 = 实体抽取 + **6 类关系**（uses / depends on / contradicts / caused / fixed / supersedes），原话 "The graph doesn't replace the wiki pages. It augments them."；检索 = **三路 RRF**（BM25 + vector + graph traversal）；原话 "don't rely on index.md as the LLM's primary search mechanism past ~100 pages"；事件钩子 6 种；"**The schema is the real product**" | 生命周期三字段（status / confidence / supersedes）+ 关系词 + 事件钩子 + crystallize                     | 浮点 confidence 与遗忘曲线（无基准、无法验证）；**单机几百到几千文件不需要图数据库** |
| 3   | **geronimo-iia/llm-wiki**（Rust 引擎，[README](https://github.com/geronimo-iia/llm-wiki)）                      | **24 个 MCP 工具**、单 Rust 二进制、**无内置 LLM**；自称 DKR（Dynamic Knowledge Repository）——"Process sources at ingest time, not query time"；frontmatter 用 **JSON Schema 校验**，`confidence: 0.9` 是浮点，`status: active` 是枚举；从 `sources`/`concepts` 抽 **typed graph edges**（petgraph DiGraph）；tantivy BM25；git2 提交；rmcp（stdio + Streamable HTTP）；还支持 ACP（Zed 编辑器）；`llm-wiki spaces create` + `llm-wiki serve`                                                                              | ① **frontmatter JSON Schema 校验** ② "引擎是哑管道、智能在技能层" ③ git 快照即审计                          | Rust 全家桶（你的管线是 PowerShell + Python）；不引它的二进制，不重写管线  |
| 4   | **geronimo-iia/llm-wiki-skills**（[README](https://github.com/geronimo-iia/llm-wiki-skills)）                | 是 **Claude Code plugin**；**17 个 skills**，SKILL.md 遵 agentskills.io 格式（**技能只是 Markdown，谁都能读**）；原话 "**The engine is a dumb pipe. Skills are the brain.**"；工具按 10 组挂：spaces / config / schema / content / search&index / graph / audit / knowledge / resolve / export / migrate                                                                                                                                                                                            | 技能清单当**工作流命名系统**（只借 6 个核心名写进 AGENTS.wiki.md）                                            | 不装 Claude Code 宿主；不引它的 17 个 skill 文件（6 个自己写）       |
| 5   | **tobi/qmd**（[README](https://github.com/tobi/qmd)）                                                        | npm `@tobilu/qmd`（Node/Bun）；**key feature = context 树**（`qmd context add`，命中附上下文）；typed query expansion（lex→BM25 / vec/hyde→向量）+ 原始 query 双跑 + **RRF** + LLM rerank；本地 node-llama-cpp **GGUF 离线**；SQLite 索引；**MCP 五工具**；可选远程度重排（2 MiB / 8 MiB / 30 s / 64 docs）                                                                                                                                                                                                         | ① **context 树**（我用 frontmatter 的 `summary` + `scope` 做零成本等价物）② 检索接口：CLI 与 MCP 双形态，C 档再接 | 现在不装——4.25 MB 语料上收益≈0（§1.6.4）                      |
| 6   | **blacksmithgu/obsidian-dataview**（[README](https://github.com/blacksmithgu/obsidian-dataview)）            | 四种模式：**DQL**（pipeline-based，类 SQL 但不是 SQL）、Inline Expressions、**DataviewJS**、Inline JS；数据 = frontmatter YAML + `Key:: Value` inline；DataviewJS 能改文件，官方给安全警告                                                                                                                                                                                                                                                                                                             | **"把 frontmatter 当数据库"**：index 表格可由脚本自动生成                                               | 不装插件、不让插件写文件（我自己用 catalog.ps1 出等价表格）               |
| 7   | **marp-team/marp-cli**（[README](https://github.com/marp-team/marp-cli)）                                    | markdown → HTML/CSS/PDF/PPTX/**图片**；npx 即用；PDF/PPTX 需 Chrome / Edge / Firefox；作者 yhatt；MIT                                                                                                                                                                                                                                                                                                                                                                              | wiki 页 → 汇报幻灯片，零二次排版                                                                    | 非汇报场景不装（Karpathy 原文也只把它当输出形态之一）                    |
| 8   | **A-MEM**（[arXiv 2502.12110](https://arxiv.org/abs/2502.12110)，NeurIPS 2025）                               | Zettelkasten 式原子记忆 + 结构化属性（contextual description / keywords / tags）+ **新记忆触发旧记忆"演化"**；代码 A-mem（评估）/ A-mem-sys                                                                                                                                                                                                                                                                                                                                                          | ① 单页原子化（150 行上限）② "ingest 触发相关页更新"                                                      | **它是 agent 对话记忆，不是文件知识库**；不引其检索算法                  |
| 9   | **Obsidian graph view + 双向链接**（内置功能，[文档](https://help.obsidian.md/plugins/graph)）                          | 星图看枢纽/孤儿页；反向链接看"谁引用了我"；**只读文件夹也能看**                                                                                                                                                                                                                                                                                                                                                                                                                                     | 人机共读的可视层 + 孤儿页审计                                                                        | 不占"项目"位；不上它的同步/协作                                  |
| 10  | **你的现有资产**（本机实测）                                                                                           | MinerU 4.1.7 管线（10-source→20-md）；catalog / manifest / todo / issues.log；check-links.ps1；五本中文工程书 4.25 MB / 1858 图；`40-scratch` 里有分页后处理雏形                                                                                                                                                                                                                                                                                                                                 | 解析底座 + 已有三操作骨架 + 真实规模数据                                                                 | —                                                  |

### 1.7.2 照搬现成方案会怎样：三条路线试算

| 路线 | 要装什么 | 能立刻拿到 | 拿不到 / 代价 | 结论 |
|:---|:---|:---|:---|:---|
| **A. 直接装 geronimo 引擎** | Rust 二进制（brew / curl / `irm install.ps1` / cargo）+ 24 个 MCP 工具；17 skills 还要 Claude Code 宿主 | 全文索引、图谱、schema 校验、git 提交、spaces 多空间——开箱即用 | ① 无**中文工程书领域模板**（type 只有通用枚举）② 无成本账、无 `%20` 死链修法、无假标题降级——这三个是你库的特有债 ③ 20-md → 50-wiki 的映射仍要自己写 ④ Windows 要改它的 install 脚本 ⑤ 工具面 24 个，学习成本 > 你现在的需求 | 只借 **schema 校验思路**，不装 |
| **B. 装 qmd + Dataview** | `npm i -g @tobilu/qmd` + Obsidian 插件 | 检索立刻变强；动态表格 | ① 4.25 MB 语料上收益≈0（§1.6.4 A 档）② 完全没有增加"综合知识"——RAG 的老问题（无累积、矛盾不可见）原样保留 | 等 C 档（>50 MB）再上 |
| **C. 自建融合（本方案）** | PowerShell 三脚本 + git + 一份 `AGENTS.wiki.md` | 领域模板、成本账、你的书适配、编辑契约、300 本升级阈值 | 前期要你亲手盯前 14 页 | ✅ **推荐** |

> **一句话**：现成方案解决的是"通用工具"，你的问题一半是"通用工具 + 你的库特有债务（%20 死链、OCR 假标题、中文工程书结构）"。**工具可以借思想，债务只能自己还。**

### 1.7.3 取舍总表：借什么、不借什么、什么时候借

| 来源的 idea                                 | 取舍                       | 理由                                                                           |
| :--------------------------------------- | :----------------------- | :--------------------------------------------------------------------------- |
| 三层 + 三操作 + index/log                     | ✅ **照抄**                 | 唯一被社区反复验证的骨架                                                                 |
| 生命周期字段（v2）                               | ✅ **借字段，不借浮点机制**         | status / confidence / supersedes 三字段解决"新旧口径并存"；遗忘曲线无基准，先不做                   |
| 类型化关系（v2 的 6 类动词）                        | ✅ **借链接语义，不借图数据库**       | 在 wikilink 后写关系词即可（`[[B]]（取代）`）；petgraph/Neo4j 到 D 档再说                       |
| 事件钩子（v2）                                 | ✅ **借**                  | ingest 第 0 步强制查重、写后强制 lint——把"自觉"变"流程"                                       |
| crystallize（v2）                          | ✅ **借**                  | 你的计算书/选型过程就是结晶对象，落 `howto\`                                                  |
| **JSON Schema 校验 frontmatter**（geronimo） | ✅ **借（用 PowerShell 实现）** | wiki-lint.ps1 第 0 项 = 五类页面必填字段校验，失败即拒收                                       |
| git 快照即审计（geronimo）                      | ✅ **借（简化）**              | 一个 ingest 一个 commit，无需工具封装                                                   |
| 17 skills 里的 **6 个核心名**（llm-wiki-skills） | ✅ **借名字**                | setup / ingest / crystallize / lint / graph / research 写进 AGENTS.wiki.md 章节名 |
| Rust 全家桶（geronimo）                       | ❌ **不借**                 | 你的管线是 PowerShell+Python，重写是负资产                                               |
| tantivy 全文索引（geronimo/qmd）               | ⏸ **C 档再借**              | 现在 4.25 MB，grep 够（§1.6.4）                                                      |
| BM25+向量+RRF+重排+**context 树**（qmd）        | ⏸ **C 档接入**              | AGENTS.wiki.md §6 写明"升级到 qmd 时检索流程不变"；context 树先用 frontmatter 摘要替代           |
| Dataview 的"frontmatter 当数据库"             | ✅ **借思想**                | 用 catalog.ps1 读 frontmatter 自动生成 index 表格；不装插件                               |
| marp                                     | ⏸ **需要汇报时再借**            | 零成本，wiki 页本身就能喂 marp                                                         |
| A-MEM 原子化 + 演化                           | ✅ **借两条**                | 单页 150 行上限 + "ingest 触发相关页更新"                                                |
| Obsidian 星图 + 反向链接                       | ✅ **借**                  | 只读 vault + 反向链接审计（§1.3.12）                                                     |

### 1.7.4 融合后的总架构（v3 更新版）

```
【数据流】
10-source(原件) → MinerU解析(+页码锚点 page_idx) → 20-md(全文) → LLM ingest(§1.3.5) → 30-wiki(页面网) → git commit(每书一个)
                    └─ 一次性欠账：%20 死链解码 / 163 个假 h2 降级 / 图注残片清理

【契约层】(三处校验，缺一不可)
frontmatter JSON Schema(借 geronimo 思路，PowerShell 实现)
  ↳ 必填：type/title/status/confidence/sources/summary/scope/updated
lint 八项(Karpathy 7 项 + v2 冲突项 + geronimo schema 项)
git diff 审计(人机只读约定：改动必须能解释)

【检索流】(按 §1.6.4 分档升级，接口不变)
A档(≤5MB，现在)：index.md 分类树 → grep 20-md → 命中页
C档(>50MB≈50本)：index → BM25(qmd CLI) → 向量+RRF+重排(qmd MCP) → 命中页 + context 树
兜底：DSH library 向量库(片段级，kb 库现有 120 页旧路径)

【生命周期】(v2 字段)
status: active|draft|stale|superseded ｜ confidence: high|medium|low ｜ supersedes: [[新页]]
新书推翻旧断言 → 旧页标 superseded 不删 → lint 第 6 项跟踪 → git 留痕

【交付】
人看：Obsidian 星图(只读) + 反向链接 + 脚本生成的 index 表
汇报：marp 幻灯片(按需)
问答：本会话 + DSH 检索注入
```

### 1.7.5 为什么说这个融合"比任何单一方案更高级"

| 被借鉴方案 | 它的短板（实读后确认） | 融合方案怎么补 |
|:---|:---|:---|
| Karpathy gist | 只有思想没有落地：无生命周期、无冲突登记、无版本审计 | + 你的 MinerU 管线落地 + v2 生命周期字段 + git 每书一 commit |
| rohitg00 v2 | 浮点机制无基准；图谱维护成本高；无中文工程书场景 | 图谱降为链接语义；机制不借；+ 中文书实测数据（%20/假标题/909 图） |
| geronimo-iia/llm-wiki | 通用引擎，**无页面内容模板、无领域字段、无成本核算**；24 工具学习成本高；Windows 安装要改脚本 | + 六类页面模板（附录 B）+ 工程书领域字段 + §1.3.9 成本账 + 只用它的 schema 思路 |
| llm-wiki-skills | 17 个技能面向 Claude Code 生态；不含你库的任何领域约定 | 只借 6 个名字；约定自己写进 AGENTS.wiki.md |
| tobi/qmd | 纯检索，无知识网、无累积；4.25 MB 上收益≈0 | + 30-wiki 页面网；qmd 只作 C 档配件；context 树先用 frontmatter 实现 |
| Obsidian + Dataview | 是展示层与查询层，不产生知识 | + 综合层（30-wiki）+ 只读审计 |
| A-MEM | agent 记忆系统，无 schema、无 lint、无版本控制 | + AGENTS.wiki.md + lint 八项 + git |
| 普通 RAG | 无累积、矛盾不可见、引用不可核 | + compile-once、openq 冲突登记、§节号/行号锚点 |
| GraphRAG | 贵 3~8 倍、出处稀释、增量更新难 | 暂不做；预留 LightRAG 升级位（§1.6.5） |

**一句话**：单一方案都只解决"读 / 查 / 记"中的一段；融合方案把 **读（MinerU）、记（30-wiki + v2 生命周期）、查（index→qmd 分级）、核（schema + lint + git）、看（Obsidian）** 串成闭环，且每一步都有"300 本书口径"的成本与升级阈值——**这套东西没有任何一个现成仓库同时提供**。

### 1.7.6 落地：每个阶段拿哪几件零件

| 阶段 | 拿哪些零件（来源） | 产出 | 工时 |
|:---|:---|:---|:---|
| **P0** | 三层+三操作（Karpathy）、6 个技能名（skills 17 里挑）、schema 校验思路（geronimo）、事件钩子（v2） | `git init` + `.gitignore`；`90-tool\AGENTS.wiki.md`（8 节）；`50-wiki\` 骨架；`wiki-lint.ps1` 骨架 | 0.5~1 h |
| **P1** | 六类模板（附录 B）+ 生命周期字段（v2）+ JSON Schema 校验（geronimo 思路） | 试点书一本 → 12 页；lint 八项跑通；log 三字段（action/token/文件） | 1 会话 |
| **P2** | 原子化 150 行 + 演化触发（A-MEM 两条）+ 冲突登记（openq 模板） | 化工原理（先修 %20 + 降假标题）与气液搅拌釜入库；跨书 3 页；glossary 30 条 | 2 会话 |
| **P3** | frontmatter 当数据库（Dataview 思想）+ git 快照（geronimo 简化） | index 自动生成（catalog.ps1 扩展）；lint 全过；每书一 commit | 1 会话 |
| **P4** | context 树 + RRF（qmd），marp（汇报） | index 分册；C 档接 qmd；汇报幻灯片按需 | 规模化后 |

> 读到这里，你可以拍板的三件事（原 §7.2，2026-11-23 已全部完成）：**① git init + GitHub 私有仓库；② 修死链 + 降假标题（残留 14 条见 §1.2.3 P2）；③ 建 30-wiki + AGENTS.wiki.md。** 落地实况见 §1.2 复测与 §1.3。

---

## 1.8 你的问题，逐条回答

### 1.8.1 向量检索分界线：多少字/MB 以下用 LLM Wiki、以上用 RAG

**先纠正一个隐含预设【判断】**：LLM Wiki 和 RAG **不是二选一**。LLM Wiki 解决"综合知识"，RAG/向量解决"片段检索"，规模大了两者共存（§1.6.3）。真正要分界的是**"什么时候需要向量检索"**：

| 判据（实测） | 值 |
|:---|:---|
| 你现在的 md 总量 | **4,350 KB ≈ 4.25 MB ≈ 270 万字符 ≈ 90 万汉字 ≈ 60 万 token**（§1.2.2 实测） |
| 分界线 | **≤ 5 MB：不需要向量检索**（index+grep 足够）；5~50 MB：全文检索（BM25）；> 50 MB（~50 本以上）：上向量+混合检索 |
| 300 本书 | ~240 MB → 落在"混合检索"档 |

**所以对你**：现在 → LLM Wiki + grep，**不要向量库**；300 本 → LLM Wiki + 混合检索（qmd）。详见 §1.6.4。

### 1.8.2 单本入库到底多少钱（deepseek-flash 口径，不扯九万张图）

**直接答**：一本《化工原理》从现成 md 编成 wiki，用 **deepseek-flash**（带 Vision、1M 上下文）：

| 口径 | 一本多少钱（off-peak） | 算法 |
|:---|---:|:---|
| ① 只文本、不喂图 | **≈ ¥0.44** | 35 万 in × ¥1.08/M + 1.5 万 out × ¥4.32/M |
| **② 按需喂 30 张图（推荐）** | **≈ ¥0.51** | ① + 3.6 万 in × 1.08 + 0.6 万 out × 4.32 = +¥0.065 |
| ③ 全量 400 张图（不推荐） | ≈ ¥1.31 | ① + 48 万 in × 1.08 + 8 万 out × 4.32 = +¥0.86 |
| peak 时段（①②③ ×2） | ¥0.89 / ¥1.01 / ¥2.61 | peak = UTC 周一至五 01:00-04:00、06:00-10:00 |

**价格锚**（[DeepSeek 官方](https://api-docs.deepseek.com/quick_start/pricing)，2026-11-16，$1≈¥7.2）：deepseek-flash 输入 cache-miss **$0.15/M**（peak $0.30）、cache-hit $0.003/M、输出 **$0.6/M**（peak $1.2）。**带 Vision ✓**——文本与图共用一把 key，不用第二家。

**为什么 v2 的 ¥0.8~5.2 偏高**：v2 用的是"DeepSeek 系 2 元/M in、8 元/M out"的历史锚，比官方 flash 现价贵约 2 倍（输入）/近 2 倍（输出）。换成官方价后：**单本 off-peak ≈ 五毛，peak ≈ 一块。**

**300 本总账**：文本 300×¥0.44 + 图 300×¥0.065 ≈ **¥150（off-peak）/¥300（peak）**。GraphRAG 同语料索引高 3~8 倍（§1.5.4）。

**单次提问**（§1.3.9）：LLM Wiki ≈ RAG ≈ **¥0.01/问**；GraphRAG Global ≈ **¥0.03~0.06/问**。各方案输入 token 见 §1.3.9 表。

### 1.8.3 LLM Wiki v2 是谁、什么时候、提升什么

- **作者**：Rohit Ghumare（GitHub `rohitg00`），gist 标题 *"LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory"*。
- **时间**：约 **2026-10**（gist 最近活跃 2026-10-08）。
- **四大提升**：① 知识生命周期（confidence/supersession/遗忘/四层记忆）；② 类型化图谱（实体带类型、关系带语义）；③ 混合检索 RRF + 事件钩子 + crystallize；④ 多代理协作、隐私审计、任务化输出。
- **注意**：其中浮点置信度、遗忘曲线等 v2 自己标注为"待评估"；v2 是**扩展不是替代**，主张按规模逐步加装。全文见 §1.1.9。

### 1.8.4 "无 lint 就腐化"和"ingest"到底什么意思

- **ingest = 入库编译**：把一份新资料读进 wiki 的动作。不是"把文件拷进去"，而是"读原文 → 写摘要页 → 更新 10~15 个相关页 → 更新 index → 记 log"（§1.1.5）。
- **无 lint 就腐化**：每次 ingest 都改动十几个文件，没有定期体检（死链/孤儿页/过期断言/矛盾/无来源页），错误会**复利堆积**，20 次入库后没人敢信这个 wiki。lint 就是体检，你的 `todo.md` 是文件层体检，缺的是知识层体检（§1.3.5 lint 八项）。

### 1.8.5 按 300 本书重设预设：哪些设计因此变了

全文已按 300 本口径重写，关键变化（详见 §1.2.6）：index 必须分册；提问先 grep index 再按类读子索引；glossary 按领域拆；**图片一律按需喂**（9 万张全喂排队太慢，不是贵）；20-md 图片不进 GitHub；lint 挂进 ingest 自动跑；Obsidian 星图按领域限定视图。

### 1.8.6 融合方案在哪看

第 8 章整章。三句话版：**骨架照抄 Karpathy（三层+三操作），字段借 v2（status/confidence/supersedes），工程化借 geronimo（JSON Schema 校验+git 快照），检索接口预留 qmd（BM25+向量+重排），可视化借 Obsidian（星图+Dataview），比任何单一方案多的是：你的 MinerU 中文工程书底座 + 五类页面模板 + 成本账 + 300 本升级阈值。**

### 1.8.7 MinerU 能不能一直开 OCR？能不能"不图片"？86 条死链怎么办

- **能强制 OCR**：CLI `--method ocr`（默认 `auto`；API 是 `enable_ocr`；Gradio 勾 `is_ocr`）。但**开关是文档级**，不能按页混合——扫描书和原生文字层书要用不同配置。
- **但强制 OCR 不能让你"不图片"**：MinerU 的图块裁剪来自**版面分析**（识别 figure 区域），与 OCR（识别文字）是两条独立流水线。开 OCR 只会让文字层更干净，图照样被裁出来存进 `图片\`。想少图只能靠按需喂视觉模型（§1.3.5）。
- **86 条死链已查清**：不是图丢了，是 md 内链接带 `%20` 等 URL 编码，磁盘文件名是真空格（`图1.3%20U形管…jpg` vs `图1.3 U形管…jpg`）。**修法 = 链接做 URL 解码**（check-links.ps1 加一行，或批量替换）。另有十余个 `_a.jpg` 图注残片属真垃圾，需重解析对应页或改名（§1.2.3 问题 1）。

### 1.8.8 分页标记（`<!-- page: N -->`）能在解析阶段加吗

- **能，且 MinerU 已经给了原料**：MinerU 输出 `middle.json` 里每个块带 `page_idx`——只是你的 ingest.ps1 没有把它写成锚点。**最佳落点 = ingest.ps1 的后处理**：按 `page_idx` 在行间插入 `<!-- page: N -->`，以后引用 = `#L行号` + `页码` 双轨。
- **不用重解析全库**：MinerU 支持只输出 middle.json（`--output` 选中间产物），你甚至可以只重跑"中间产物"这一步；`40-scratch\` 里已有 `_append_page_appendix.py` 与 figures-report JSON 的雏形，说明这条路你走过一半。
- 详细方案见 §1.3.7 的 `md-anchor.ps1`。**新书从 P1 之后起，解析默认带锚点；三本旧书用脚本补。**

### 1.8.9 git 怎么存，本地和 GitHub 都同步

§1.3.11 完整命令。要点：根目录 `git init`；`.gitignore` 排除 `10-source\`、`.stfolder\`、lint 报告；GitHub 建**私有**仓库（版权材料）；每本书 ingest 一个 commit（message 带 `touch=N`）；图片 3 本时直接推，300 本后切 Git LFS；Syncthing 的 `.stignore` 加 `.git` 防打架；单写者策略（只本机编辑，GitHub 纯备份）。

### 1.8.10 建立 LLM Wiki 是否顺带解决"检索能力不均"

**部分解决，且是正确方向的解决。**
- LLM Wiki 解决的是**知识层不均**：化工原理的概念会变成 wiki 页，不再"只能 grep 原文"。以后问"搅拌功率怎么算"，读的是 wiki 页（跨书综合），不是翻某本书的 chunk。
- 但它**不解决片段级检索不均**：要引用原文原话（"§2.3 公式原文"）仍要 grep 或向量库。正确顺序是：**先建 wiki（现已建成 542 页），规模到 B/C 档再统一上混合检索**——而不是现在就把 5 本书塞进 kb 向量库。因为你现在只有 4.25 MB，A 档的 grep 完全够（§1.6.4）。

### 1.8.11 目录/文件名：用 Karpathy 的还是 GitHub 项目的

**混合**（§1.3.2 全表）：目录层 = 你的数字编号（30-wiki）+ Karpathy 的 `wiki` 语义；文件层 = Karpathy 通用名（`index.md`/`log.md`/`AGENTS.wiki.md`）；技能名从 geronimo 的 17 个里挑 6 个（setup/ingest/crystallize/lint/graph/research）。理由：**Karpathy 的名字是"模式语言"，GitHub 项目名是"实现名字"——模式比实现稳定。** 通用可辨认 = 任何人看到 `50-wiki\index.md + log.md + AGENTS.wiki.md` 立刻知道这是 LLM Wiki 模式落地。

### 1.8.12 `50-` 前缀为什么？能不能用 a/b/c/d
> 现行目录名是 `30-wiki`（v3.13 合并 50-wiki+30-index 改名，见路径注记与 §1.3.1）；本节保留当时的设计问答。

- **是，首要目的就是排序**：00→10→20→30→40→90 是数据流顺序（进料→原件→解析→索引→草稿→工具），wiki 在数据流里排第 6 站，所以用**空号 50** 插进去，不动任何现有路径。
- **数字优于字母**：数字表达"流程顺序"，字母没有语义（a-wiki 排在 z-tool 前会撒谎）。且你的 README/脚本已写死数字约定，改字母要动一串引用。
- **当然可以用任何名字**（`05-wiki`、`wiki` 都行），但建议保留"数字前缀 + wiki"这个组合，理由如上。

### 1.8.13 Obsidian 星图 + 人机同步怎么落地

§1.3.12 完整方案。要点：
- **星图不用 MCP 建**：它是 Obsidian 客户端按 `[[wikilink]]` 渲染的。你只需"打开文件夹为库"指向 `D:\Shervon_KnowledgeBase`（当前 MCP 连的 Obsidian 库只有 4 个文件，不是你的知识库——已实测）。
- **人机同步 = 约定 + git 审计**：AGENTS.wiki.md §0 写"人对 Obsidian 只读"；每次会话开始跑 `git status --short`，有未提交改动就逐文件汇报给你"你改了 X，吸收还是还原？"——这就是你要的"改了要报告"。

### 1.8.14 你同意的"先看融合方案"——方案在 §1.7，这里再给结论

看完 §1.7 如果你认可——原需拍板的三件事（git init + GitHub 私有仓库；修死链+降假标题；建 wiki + AGENTS.wiki.md + 试点书试点）已全部完成，库已按本方案建成（v3.18），落地实况见 §1.2、§1.3。

### 1.8.15 诚实声明：本版（v2）我改了什么、没改什么

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
| graph view | — | 星图 | Obsidian 把 `[[链接]]` 画成节点连线图 |
| ingest | — | 入库编译 | 读新资料→写页→更新 10~15 页→更新 index/log（§1.1.5） |
| JSON Schema | — | JSON 校验规范 | 声明"字段该长什么样"，机器据此验 frontmatter（geronimo 的杀招） |
| Leiden | — | 莱顿算法 | 社区检测算法（Traag et al. 2019），GraphRAG 用它切社区 |
| lint | — | 体检/静态检查 | 定期查 wiki 健康：死链/孤儿/过期/矛盾/无来源（§1.3.5 八项） |
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
  - book: 搅拌与混合设备设计选用手册
    section: "§1.4"
    lines: "L960-L1064"        # 有页码锚点后写页码
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

## 5. Ingest 八步（§1.3.5 为执行标准）
0 查重 → 1 章节地图（降假标题）→ 2 写 source 页 → 3 建/改概念页 → 4 转述图 → 5 回改受影响页（冲突开 openq）→ 6 更新 index → 7 追加 log（记 token 与成本）→ 8 lint 自检 + git commit。

## 6. Query 四步（§1.3.5）
grep index → 读 ≤10 候选页 → 回答带 §节号/行号 → 判断回填（crystallize）并登记 index。

## 7. Lint 八项（§1.3.5 表）
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
| P1 | 试点完成 | 试点书 source 页 + ≥7 概念/实体页；ingest 触及 10~15 页；死链 0 |
| P2 | 三本铺开 | 14 页齐（§1.3.6）；跨书引用 ≥3；openq 冲突 ≥3；glossary ≥30 条 |
| P2 | 死链清零 | check-links 全库 0（%20 已解码） |
| P2 | 假标题降级 | 试点书 163 个假 h2 已降级（脚本报告） |
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

**300 本书总账【估计】**：编译 300 本（文本 + 按需 30 图/本）≈ **¥153（off-peak）/¥305（peak）**；GraphRAG 全量索引同语料 ≈ **几千元**。全部价格以 2026-11-16 公开页为据（§1.3.9.1），下单前以官网当日价为准。

---

> 全文完（v3.0）。本版新增：§1.7.0 自查（v2 里说错的 9 处）、§1.7.2 三条路线试算、§1.8.2 单本入库账（deepseek-flash 口径）。当时的三个拍板（git 私有仓库、死链+假标题清理、建 wiki 并先用试点书试点）均已落地，见 §1.3。

---

# 2. 落地执行方案（P0–P4）

> 状态：**待你确认**。确认前不动库。
> 依据：`LLM-Wiki_RAG_GraphRAG_全解与本库改造方案.md`（v3，1420 行）§1.3 与附录 B/C/D/F，其中 §1.3.1–3.8、§1.3.9、§1.3.11、§1.3.12 为本方案直接引用的原文。
> 版本：v1.0｜2026-11-16｜作者：agent（lead）

---

## 2.1 范围与基线

### 2.1.1 本方案是什么

一句话：**把你现在的"解析 + 索引"流水线，升级成 Karpathy 三层 LLM Wiki（raw → wiki → schema），全部动作拆成 P0–P4 五段，每段有命令、有产出、有验收、有坑与改法，并说清人机分工。**

### 2.1.2 剔除清单（主文档里的内容哪些不进本方案）

| 主文档章节 | 内容 | 本方案处理 |
|:---|:---|:---|
| 第 1 章 | LLM Wiki 是什么、出处、演进（科普） | 剔除，只保留执行所需的字段名/文件名 |
| §1.2 | 现状实测与差距 G1–G8 | 只保留"现状基线表"（§2.1.4），论证过程剔除 |
| 第 4 章 RAG | 九段流水线、参数、RAGAS、生态 | **整章剔除** |
| 第 5 章 GraphRAG | 五步索引、查询模式、变体 | **整章剔除** |
| §1.6 | 三方案对比、决策树、分界线 | 只保留 §1.6.4 升级阈值表（规模演进要用） |
| 第 9 章 Q&A | 15 条问答 | 剔除（答案已在主文档） |
| §1.7 融合方案 | 九个方案的取舍论证 | 只保留 §1.7.6"每个阶段拿哪几件零件"（§2.6 资源映射） |

### 2.1.3 执行红线

1. **本方案确认前**：不改库内任何文件、不建目录、不装软件、不跑 git。现在唯一的库改动就是本文件本身。
2. **每阶段结束即停**：P0 做完等你验收，再进 P1；不连跑。
3. **20-md 的一次性修补**（死链解码、假标题降级）是明确列出的例外，且每处都要先 dry-run 计数、你确认数字后再落盘。
4. **10-source 一字节不改**，任何情况下。

### 2.1.4 现状基线（2026-11-16 本机实测，方案所有步骤以此为准）

| 项 | 实测值 | 对方案的影响 |
|:---|:---|:---|
| git | **未安装**（三个常见路径均不存在） | P0-1 必须先装 |
| 包管理 | winget 可用 | 用它装 git |
| PowerShell | 5.1.26100.6584（**不是 pwsh 7**） | 脚本一律 PS5.1 语法；含中文的 .ps1 存 UTF-8 BOM |
| 根目录 | .stfolder / 00-inbox / 10-source / 20-md / 30-index / 40-scratch / 90-tool / README.md / 主文档 | 无 .git、无 .stignore、无 50-wiki |
| 20-md 三书 | 化工原理 1086836B｜搅拌与混合设备 1362747B｜气液搅拌釜 351311B | 三本 md 均**无页码锚点**（`<!-- page:` 计数=0） |
| 死链 | 化工原理 86 条（`%20` 未解码，图实际存在） | P2-1 解码，不是删链 |
| 假标题 | 试点书 351 个 `## ` 中 163 个 `(n)` 型假标题（46%） | P1-1 降级 |
| 编码矩阵 | 化工原理/气液搅拌釜 md：无BOM+LF；试点书 md：无BOM+**CRLF**；manifest.csv BOM+CRLF；rules.md BOM+LF | git 设 core.autocrlf=false；改文件保持原 BOM/行尾 |
| 30-index | catalog.md（自动生成勿手改）、manifest.csv 15 列、todo.md、issues.log | catalog/todo 是生成物 → 入 .gitignore |
| 40-scratch | **已有**气液搅拌釜的 MinerU middle.json（1.16MB）+ 页码/图页 CSV + 两份 figures-report + links-fix 记录 | P2-2 页码锚点只此一本有原料 |
| DSH kb 库 | 试点书 836 chunk 曾入库（2026-11-18 出库后为空）；另两本未入（README：索引由你发话才做） | 本方案不动 kb；检索不均由 50-wiki + grep 兜底 |
| 成本锚 | deepseek-flash off-peak：输入 ¥1.08/M、输出 ¥4.32/M（peak=北京时间周一至五 9–12 点、14–18 点，翻倍） | 全案报价用 off-peak 口径 |

---

## 2.2 终态架构图（P3 完成后长这样）

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
 │      30-index\（机器索引，自动生成）+ 40-scratch\（草稿与一次性脚本）      │
 └────────────────────────────────────────────────────────────────────┘
            │ git（本地历史 + GitHub 私有仓库，每次 ingest 一个 commit）
            ▼
  三操作闭环（每个会话可复跑）：
  ingest（读 20-md → 写/改 50-wiki 10~15 页）→ query（grep index → 回答带 §节号）→ lint（八项体检）
```

写者边界一句话：**人只放书、只读、只验收；脚本只碰 20-md 和 30-index；LLM 只碰 50-wiki；git 记一切。**

---

## 2.3 文件系统：现在 → 终态

### 2.3.1 现在（改造前）

```
D:\Shervon_KnowledgeBase\
├─ .stfolder\            Syncthing 标记
├─ 00-inbox\             （空）
├─ 10-source\            3 个 PDF 目录（192 MB）
├─ 20-md\
│  ├─ _quarantine\
│  ├─ 化工原理…\          md + 图片
│  ├─ <入库夹>…\          md + 图片
│  └─ 气液搅拌釜…\        md + 图片
├─ 30-index\             catalog.md / manifest.csv / todo.md / issues.log
├─ 40-scratch\               历史补丁脚本 + pageidx/figures 材料
├─ 90-tool\              rules.md v2.3 / prompts / taxonomy / CHANGELOG / VERSION / scripts\（5 个）
└─ README.md
```

### 2.3.2 终态（P3 完成后，只加不改）

```
D:\Shervon_KnowledgeBase\
├─ .git\                 ★新增：版本历史
├─ .gitignore            ★新增
├─ .stfolder\            （不变；Syncthing 侧 .stignore 加 .git/）
├─ 00-inbox\             （不变）
├─ 10-source\            （不变，一字节不改）
├─ 20-md\                （不变结构；三处一次性修补：死链解码/假标题降级/气液搅拌釜页码锚点）
├─ 30-index\             （不变，继续自动生成）
├─ 40-scratch\               （不变，P1-P3 各步报告落这里）
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

## 2.4 分阶段执行：每一步做什么

> 每步格式：【谁做】【命令/动作】【产出】【验收】【坑→改法】。所有命令在执行阶段（你确认后）原样运行，不再改动。

### 2.4.1 打地基（≈0.5 小时，¥0）

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
git add .gitignore 20-md 30-index 40-scratch 90-tool README.md
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
- 坑→改法：这份文件按主文档 §1.3.4 是"唯一必须有、且只能人写"的文件——**我不替你定调**，我出骨架、你拍板，防的是"LLM 给自己定规矩"。

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

### 2.4.2 单本试点（试点书，1 个会话，≈¥0.5）

#### P1-1 假标题降级（163 个）——【我，dry-run 数字先给你看】

```powershell
$md = 'D:\Shervon_KnowledgeBase\20-md\<入库夹>\<入库夹>.md'   # 执行前用 Get-ChildItem 核对真实路径
$raw = [System.IO.File]::ReadAllText($md, [System.Text.Encoding]::UTF8)
$n = ([regex]::Matches($raw, '(?m)^##\s*\(\d+\)')).Count
Write-Host "假标题计数: $n （预期 163，不是这个数就停）"
```

- 若你确认数字无误，再跑替换（脚本全文见附录 C-1）：`## (1)xxx` → `**(1)xxx**`。
- 产出：试点书 md 的 `## ` 标题从 351 个降到 188 个（176 真节 + 12 其他），假标题变成正文加粗行，不再骗过标题树。
- 验收：重跑层级体检，`(n)` 型假 h2 = 0；diff 只有标题行变化。
- 坑→改法：
  1. **dry-run 与替换分两步**，数字对不上（≠163）立刻停，先把真实数字报告给你。
  2. 该文件是 CRLF → 用 `[IO.File]::ReadAllText` 保留 `\r\n`，写回无 BOM UTF-8，**不换行尾**。
  3. PowerShell 里替换串含 `$1` 必须用**单引号** `'**$1**'`，双引号会被 PS 当变量吃掉。
  4. 这是对 20-md 的一次性修补，记入 `40-scratch\` 报告 + CHANGELOG（例外，已在红线里声明）。

#### P1-2 页码锚点：试点书暂缓 ——【结论，先摆这】

- 事实：三本书只有**气液搅拌釜**在 40-scratch 里有 MinerU middle.json；试点书/化工原理的 middle.json 按 rules §11 解析后已清理，重跑 MinerU 才能再拿。
- 决定：P1 试点书的引用一律用 **行号**（`#L117-456`）；锚点等"重解析该 PDF"时由 `md-anchor.ps1` 自动补。不因此卡住试点。
- 坑→改法：这步本来没人意识到"只有一本书有页码原料"，写方案时核对 40-scratch 才发现——所以 P2 的气液搅拌釜锚点与另两本分开列。

#### P1-3 写三个脚本 ——【我】

| 脚本 | 行为规格（全文执行时落盘，先给你过目） |
|:---|:---|
| `wiki-lint.ps1` | 只读 `50-wiki\**`，正则解析 frontmatter（`^---`…`---` 块，字段按模板固定顺序），执行八项体检（§1.3.5 表：死链/孤儿页/无来源/超长页/同义重复/过期断言/index 漂移/图无转述），结果写 `50-wiki\_lint.md`，全过 exit 0 |
| `wiki-index.ps1` | 只读 frontmatter 的 type/title/domain/status，按 domain 分组生成 `index.md` 表格，头注"自动生成勿手改" |
| `md-anchor.ps1` | 只读 20-md + 指定的 MinerU middle.json，按块文本在 md 中定位，插 `<!-- page: N -->`；**匹配失败率 >5% 即停**并报告 |

- 产出：`90-tool\scripts\` 三文件（UTF-8 BOM，PS5.1 语法）。
- 验收：对空 50-wiki 跑 lint 出报告不报错。
- 坑→改法：本机没有 YAML 解析库 → 校验用**固定字段名的正则**，所以 AGENTS.wiki.md §3 强制模板字段顺序，脚本与契约绑死。

#### P1-4 ingest 试点（已完成；试点书 2026-11-18 出库）

> 首轮试点用一本 272 页密封类专著，按本节八步跑通 7 页 + 1 条 log + 1 个 commit，验收死链 0。该书及其全部派生页已于 2026-11-18 按用户要求整体出库，故不再列清单；过程口径（八步、图按需喂、触及页 10~15、`_lint.md` 死链 0）继续有效，见 §1.3.5 与 `rules.md` §15。
- 成本【估计】：文本 ≈32.5 万 in（¥0.35）+ 输出 ¥0.065 + 30 图 ¥0.065 ≈ **¥0.48（off-peak）**。

#### P1-5 你验收试点

- 你：读 7 页；**抽查 3 条断言**回原书核对；看 log.md 与 `_lint.md`。
- 通过 → 进 P2；不通过 → 我改，改完再给你看。——**停，等你验收。**

---

### 2.4.3 三本铺开（2 个会话，≈¥0.7）

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

- 事实：`40-scratch\_pageidx-气液搅拌釜\` 里 MinerU middle.json 的文件名是 **"汽液搅拌釜γ－CT测量、成像与模拟_(刘跃进…).json"**——与 20-md 目录名"气液搅拌釜γ-CT…"存在**汽/气**字与**全角－/半角-**两处差异。
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

### 2.4.4 闭环（1 个会话，≈¥0.1）

| 步 | 做什么 | 谁 |
|:--|:---|:---|
| P3-1 | 回填 3 页 crystallize：把试点期你反复问过的 3 个问题固化成 howto/comparison 页，登记 index | 我 |
| P3-2 | 全量 `wiki-lint.ps1`，八项全过，`_lint.md` 无未决项 | 我 |
| P3-3 | `wiki-index.ps1` 自动生成 index.md（domain 分册表） | 我 |
| P3-4 | 终态验收：附录 D 判据逐项打勾 + 抽 10 条断言核对"10/10 有 §节号或行号"（你抽） | 你 |

**P3 完成 = 本方案主体结束。** 终态即第 1、2 节画的图。

---

### 2.4.5 规模常态化（未来，不是现在做）

| 触发 | 动作 |
|:---|:---|
| 每进 10 本书 | 全量 lint + 分册 index + 死链体检（脚本自动化） |
| 书 >20 本或出现"跨 5 本对比"问题 | 装 LightRAG，只抽实体层做图谱辅助（主文档 §1.6.4 阈值） |
| 全书 >200 页规模的 wiki（约 30 本） | 检索层升级：装 tobi/qmd（BM25+向量+重排+context 树，CLI+MCP），50-wiki 结构不变 |
| 万页级 | 才考虑完整 GraphRAG（本方案不计划，见主文档第 5 章成本结论） |
| 图总量上去（~70 GB） | Git LFS 或图片改走 Syncthing（主文档 §1.3.11 决策表） |

成本总账【估计】：300 本全量编译 ≈ **¥153（off-peak）**，每次 ingest 单本 ¥0.4~0.5；单次提问 ¥0.01。全部用 deepseek-flash 官方价（2026-11-16，见主文档附录 F），下单前以官网当日价为准。

---

## 2.5 挑错清单（写本方案过程中挑出的坑，全部已在对应步骤写进"坑→改法"）

| # | 挑出的坑 | 错法 | 改法（落在哪一步） |
|:--|:---|:---|:---|
| 1 | 本机没装 git | 直接跑 git init 必然失败 | P0-1 winget 装，重开终端验证 |
| 2 | PS5.1 默认 GBK 读 UTF-8 乱码 | Get-Content 不带 -Encoding 会把 catalog.md 读成乱码 | 全案读写走 `[IO.File]::ReadAllText(UTF8)` |
| 3 | 库内 LF/CRLF 混杂 | git 默认 autocrlf 会把全库行尾改写、首次 diff 全红 | P0-3 `core.autocrlf false` |
| 4 | git 不追踪空目录 | 5 个子目录推不上远程 | P0-4 每目录放 `.gitkeep` |
| 5 | catalog.md/todo.md 是脚本生成物 | 版本化后每次重生成都出 diff | P0-3 进 .gitignore（manifest.csv 保留，有手工字段） |
| 6 | 死链根因是 %20 编码，不是图丢了 | todo.md 建议 `check-links.ps1 -Fix` 是删链，链和图都毁 | P2-1 只对链接内部解码，再用干跑验证 |
| 7 | 假标题替换串 `'**$1**'` 用双引号会被 PS 吃变量 | 脚本静默出错 | 附录 C-1 用单引号 |
| 8 | 页码锚点原料只有气液搅拌釜一份 | 原以为三本都能打锚点 | P1-2 试点书用行号引用、锚点挂 todo；P2-2 只做气液搅拌釜 |
| 9 | 40-scratch 里 json 文件名"汽液搅拌釜γ－CT"与目录名"气液搅拌釜γ-CT"不一致 | 直接跑脚本会错位，插错页码=伪造引用 | P2-2 硬步骤"先人工核对映射再跑" |
| 10 | 双机 Syncthing 会把 .git 互传打架 | 两机 git 对象冲突 | P0-3 后你在 Syncthing 的 .stignore 加 `.git/` |
| 11 | Obsidian MCP 当前连的库不是本库 | 星图/backlinks 查到别处 | P0-7 手动"打开文件夹为库" |
| 12 | "只读"没有强制锁 | 以为 Obsidian 有只读模式 | P0-7 约定+每次会话 `git status` 审计兜底 |
| 13 | 无 YAML 解析库 | lint 脚本想解析任意 frontmatter 会写崩 | AGENTS.wiki.md §3 锁定字段顺序，脚本用固定正则 |
| 14 | 首推 235MB 图片会误以为卡死 | 中断重试 | P0-3 注明一次性属正常 |
| 15 | 新书同义页爆发 | ingest 不做查重，同名概念各建一页 | SOP 第 0 步强制查 glossary+concepts |

---

## 2.6 公开资源 → 产物映射（结合哪个资源，生成什么）

| 公开资源 | 我借它什么 | 生成本库什么 |
|:---|:---|:---|
| Karpathy gist（2026-04） | 三层结构、三操作、index/log 命名、commit 节奏 | 50-wiki 目录、§1.3.5 SOP、log.md 格式 |
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

## 2.7 人机分工总表（"我帮你做什么"）

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

## 2.8 规模演进：结构图随书量怎么变

### 2.8.1 三档结构对比

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

### 2.8.2 结构"不变"与"变"各是什么

| | 3 本 | 30 本 | 300 本 |
|:---|:---|:---|:---|
| **不变** | 50-wiki 七子路径、AGENTS.wiki.md 八节、三操作 SOP、写者边界、每书一个 commit | 同左 | 同左 |
| **变** | — | index 分册、glossary 分册、lint 增量模式 | 检索层上 qmd；跨 5 本对比上 LightRAG 实体层；图片切 LFS；10-source 可外置盘 |

设计原则（主文档 §1.3.8/§1.6.4）：**目录与契约是常量，检索层是变量。** 规模涨，换检索层；不换 wiki 结构——这是 Karpathy 原文"everything is modular"的落地。

---

## 2.9 成本与时间总账

| 阶段 | 时间 | 成本（deepseek-flash，off-peak） | 谁主导 |
|:---|:---|:---|:---|
| P0 | 0.5 小时 | ¥0（GitHub 私有仓库免费） | 你装环境，我搭地基 |
| P1 | 1 个会话 | ≈¥0.48 | 我 |
| P2 | 2 个会话 | ≈¥0.7 | 我 |
| P3 | 1 个会话 | ≈¥0.1 | 我 |
| P4 | 常态化 | 每本 ¥0.4~0.5；300 本 ≈¥153 | 我 |
| 单次提问 | — | ≈¥0.01 | — |

---

## 2.10 待你确认的清单（逐项回 Y / N / 改）

1. 本方案整体接受？文件名 `LLM-Wiki_落地执行方案.md` 可以吗？
2. GitHub 仓库名 `Shervon-KnowledgeBase` + **私有**，同意？
3. `.gitignore` 排除项：10-source / .stfolder / catalog.md / todo.md / _lint.md / __pycache__ / 40-scratch\_acl，同意？（图片 3 本时**直推**，不排除）
4. 提交节奏：P0 拆"基线快照 + 地基"两次，此后每本书一个 commit，同意？
5. AGENTS.wiki.md 流程 = 我出骨架、**你定稿**、我落盘，同意？
6. 首批 14 页清单（P1 的 7 页 + P2 的 7 页）同意？
7. 允许对 20-md 的两处一次性修补：假标题降级（163）+ 死链解码（86），同意？
8. P1 试点书没有页码原料 → 引用用行号、锚点挂 todo 延后，接受？
9. P2 气液搅拌釜锚点"先人工核对汽/气映射"由你参与抽验，同意？
10. todo.md 遗留的"化工原理 manifest 缺 year"是否在 P2 顺手补上？（超出本方案范围的只有这一项，需要你点头才做）
11. 执行节奏：**每阶段结束停一次等你验收**，不连跑，同意？

---

## 2.11 附录

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
40-scratch/_acl/
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

**C-1 假标题降级（dry-run 与替换分开跑；路径改为入库夹占位）**

```powershell
# 用法：先跑 dry-run 看计数，确认后再跑 replace
param([switch]$Apply)
$md = 'D:\Shervon_KnowledgeBase\20-md\<入库夹>\<入库夹>.md'
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

# 3. 维护与升级

> 2026-11-23 拆出：§3.1 换机迁移（原使用说明 §5）、§3.2 四方案复评与升级方向（原第一部分 §8.7）。原使用说明的「给老板演示」已删除。

## 3.1 换电脑 / 给别人：前提与迁移

### 3.1.1 三档需求，别多装

| 档 | 你要干什么 | 需要装 |
|:--|:---|:---|
| A 只查询 | 问问题、看 wiki、演示 | DSH（必需）+ 本文件夹（+ 索引） |
| B 加新书 | 把新 PDF 入库 | A + PowerShell 5.1 + Python + MinerU + 模型 |
| C 维护 | 改 wiki、跑体检、改规则 | A + PowerShell（git 可选） |

### 3.1.2 软件清单（本机实测版本）

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

Agent 侧：本机 DSH 已启用 `library_search` / `library_add` / `grep` / `read` / `pwsh`，不需要额外装 CLI（`library_*` 由 DSH 的 library 插件提供；新机若未启用或会话无此工具，按 §4.5 退路走 grep）。MinerU 只由 `ingest.ps1` 调，不要求人会用命令行。

### 3.1.3 迁移六步

1. **整包复制**（不是 git clone）：`10-source\` 与 `30-wiki\catalog.md`、`todo.md` 被 git 排除，clone 会缺原件。建议保持 `D:\Shervon_KnowledgeBase`。
2. 新机装 DSH 0.2.2.0（同一大版本；索引兼容性未跨版本验证，升级前先备份 `dsh_library.json`）。
3. **恢复索引**（三选一，见 §3.1.4）。不恢复也能用，但 `library_search` 会报库不存在。
4. 验证：跑 §4.6.1 四条命令 + 一次检索，对照 §4.6.2 判据。
5. 要 Obsidian：把文件夹当 vault 打开（`.obsidian\app.json` 已排除 `10-source`、`20-md` 等，图谱只显示 `30-wiki`）。
6. 要加书：装 Python + MinerU，把 `models` 目录拷到新机同位置（2.0 GB，可直接拷）。

### 3.1.4 索引怎么恢复（关键：索引不在这个文件夹里）

DSH 的检索索引在 `%USERPROFILE%\.dsh\storages\dsh_library.json`（含文档、分块、256 维向量），**不在 `D:\Shervon_KnowledgeBase` 内**。三种办法：

| 办法 | 怎么做 | 代价 / 风险 |
|:---|:---|:---|
| ① 拷索引文件 | 复制 `dsh_library.json` 到新机同路径 | 最快、零重算；但该文件还含 magverify 库 7 篇，且会覆盖新机已有库；跨 DSH 版本未验证，先备份 |
| ② 重新入库 | 按 `30-wiki\pages` 重导入 kb（542 页，见 §4.6.3） | 干净、只进 kb；要重新切块+嵌入，耗时与费用未测 |
| ③ 不恢复 | 只靠 `grep` + `read` | 能用，但没有语义召回，问法必须带关键词 |

建议：新机没有别的库 → ①；有别的库或换 DSH 大版本 → ②。

### 3.1.5 路径变了怎么办

- 多数脚本从自身位置推根目录，换盘符能自适应。
- 3 个脚本有硬编码默认值，各 1 行，换路径要改（或显式传参）：`90-tool\scripts\md-anchor.ps1`、`wiki-index.ps1`、`wiki-lint.ps1`。
- `90-tool\prompt-dsh.md`、`prompt.md`、`rules.md` 里的示例路径要同步改，否则下次入库会指错地方。
- `30-wiki\manifest.csv` 存相对路径，可搬。

### 3.1.6 给别人时的裁剪（版权）

- `10-source\` 是版权原件，git 已排除。给外人建议只给 `20-md\` + `30-wiki\` + `90-tool\`（约 125 MB）。
- 不带原件的后果：能查、能引用行号、图还在（图在 `20-md`），但不能重解析、不能补图。
- 带原件：约 380 MB，版权自负；别上传任何网盘或公开仓库。

## 3.2 库建成后复评：四方案 vs 本库的差别与升级方向（2026-11-23）

> 库已于 v3.18 建成（5 本书、542 页、lint 0 问题）。本节按 §1.7.1 四个方案的一手文档逐项核对「方案有什么 / 本库有什么」。结论先行：**本库 = Karpathy 三层骨架的工程化落地 + rohitg00 生命周期的字段版 + geronimo 的 schema/git 思想 + skills 的命名法，并自带四方案都没有的三件套（中文工程书解析链、成本账+预算看门狗、双契约）；最该升级的是检索——542 页已过 rohitg00 的 ~100 页 index 阈值，其余按 §1.6.5 分档排队。**

| 方案（一手文档）              | 它提供                                                                                     | 本库现状（2026-11-23）                                                                                                                                                                                           | 差别                                           |
| :-------------------- | :-------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------- |
| **Karpathy gist**     | 三层 / 三操作 / index+log / LLM 独占写 / 多输出形态                                                  | 三层✅（raw=10-source+20-md、wiki=30-wiki、schema=90-tool）；ingest=ingest.ps1 十二步、query=四步、lint=十项；index 4 分册+log.md 105 行；「LLM 独占写」=AGENTS.wiki §0                                                               | gist 只有思想、本库全落地；gist 缺的生命周期/冲突登记/审计本库反而有     |
| **rohitg00 v2**       | 生命周期 / 6 类关系图谱 / 三路 RRF / 事件钩子 / crystallize                                            | 生命周期✅借字段（status+confidence 枚举+supersedes，rules §13）；关系=wikilink 后写关系词（借语义不借图库）；**检索仍为 grep，未上 BM25+RRF——最大缺口**；钩子已上 4 个（ingest 查重第 0 步/写后 lint/precommit-guard/budget-watch）；crystallize=howto 机制已定义、0 页未用 | 生命周期落地；检索待补；缺 session 结晶与 query 回填阈值         |
| **geronimo llm-wiki** | 24 MCP 工具 Rust 引擎 / JSON Schema / typed graph / tantivy BM25 / spaces / export llms.txt | DKR「ingest 时处理、不 query 时重推」✅（本库核心即此）；schema 校验=wiki-lint 十项硬编码实现（无 schema 文件）；无 typed graph、无 BM25、无多空间、无导出                                                                                                | 引擎全不借、校验思想已借；graph/search/export/spaces 四项未上 |
| **llm-wiki-skills**   | 17 skills / 10 工具组 /「引擎是哑管道、技能是大脑」                                                      | 借 6 个核心名写进 AGENTS.wiki（setup/ingest/crystallize/lint/graph/research ↔ §5 Ingest/§6 Query/§7 Lint）；同构：本库脚本是哑管道、rules+AGENTS.wiki+prompt-dsh 是大脑                                                             | 命名体系已借；不装 Claude Code 宿主                     |

**可升级方向（按优先级，与 §1.6.5 分档对齐）**：

| #   | 方向                           | 来源                                        | 触发依据                                                      | 做法                                                       |
| :-- | :--------------------------- | :---------------------------------------- | :-------------------------------------------------------- | :------------------------------------------------------- |
| U1  | 检索上 BM25（最紧迫）                | rohitg00 ~100 页线 + geronimo tantivy + qmd | **本库已 542 页**，index 单分册最大 287 条，超过「index 别当 LLM 主检索机制」的阈值 | C 档上 qmd CLI 或 tantivy；Query 四步只换第 1 步工具（grep→BM25），接口不变 |
| U2  | frontmatter 改 schema 驱动      | geronimo JSON Schema                      | 十一字段现靠 lint 硬编码；type 增多（howto/comparison）时校验要跟着改代码        | 把 rules §13 字段表落成 schema 文件，wiki-lint 第 0 项改为校验它         |
| U3  | 事件钩子补齐                       | rohitg00 六钩子                              | 已有 4 个钩子；缺「session 结束结晶」与「query 回填阈值」                     | 会话收尾把 log.md 登记做成固定步；query 第 4 步回填加质量判据（带 §节号+#L 才准回填）   |
| U4  | typed graph 导出（D 档）          | geronimo wiki_graph + rohitg00 关系词        | related 字段已存关系语义但无图谱视图；542 页星图已开始糊                        | 脚本从 related+supersedes 导出 Mermaid/DOT，不引入图数据库            |
| U5  | llms.txt 导出 + 多空间（E 档/300 本） | geronimo wiki_export/spaces               | 300 本外推 ~7500 页；喂 LLM 需打包出口；单库星图会糊（§1.2.6）                | 加 export 脚本（全页摘要打包）；按领域分册升为分 vault                       |
| U6  | 单页 git 历史                    | geronimo wiki_history                     | 零成本                                                       | `git log --follow -- <页路径>` 即得，写进 Query 手册即可             |

**明确不升级（防追新）**：Rust 引擎重写管线、图数据库（petgraph/Neo4j）、浮点 confidence+遗忘曲线（无基准）、自动 crystallize（howto 必须用户发起，AGENTS.wiki §4 已规定）、Claude Code 插件宿主。

**一句话**：四方案的「通用部分」本库要么已落地（三层/三操作/生命周期/校验思想/命名），要么已判定暂不借（Rust/图库/浮点机制）；本库多出来的是四方案都没有的「中文工程书特有债 + 成本治理」；剩下真正该补的是**检索**——只有它已经被本库自己的规模（542 页）逼过了别人的经验阈值。

### 3.2.1 白话解读（给没读过四方案原文的自己）

> 本节把 §3.2 两张表逐行翻译成白话，每条附证据位置（§号）。补充两个口径：① §1.7.1 实读的是**九个**外部方案，§3.2 只复评其中 4 个「架构级方案」；另外 5 个（qmd / dataview / marp / A-MEM / Obsidian 星图）是工具或功能，取舍已在 §1.7.1、§1.7.3 写清。② 四个方案的一手原文链接都在 §1.7.1 表「来源」列。

#### （0）四个名词，先讲清楚

| 名词   | 白话                                                                                                                                                                     | 本库现状                                                              |
| :--- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------- |
| grep | 一种「按字面关键词搜文本」的**操作方法**（命令）。Agent 拿关键词去 `20-md\*.md` 里找哪几行出现这几个字。优点：快、零成本、能拿精确行号；缺点：只认字面——记错一个字就搜不到；结果不按相关度排序；词太常见时一次命中一大片。                                             | **是。当前全文检索就是它**（§4.2.2 第 1、3 层都用 grep）。§3.2 表里「检索仍为 grep」说的就是这个状态 |
| BM25 | 关键词检索的「聪明版」打分算法：①统计词频；②稀有词加分、大路词减分（「功率准数」比「的」有区分度）；③按文档长度归一。输出是**按相关度排好序的榜单**。它仍然只认字面、不懂语义。geronimo 的 tantivy 库、qmd 都内置它（§1.7.1 #3、#5）                                 | 否。**这就是 §3.2 表标红的「最大缺口」**                                         |
| 向量检索 | 把句子变成一串数字（向量），「意思相近」的句子数字也相近——**记不清原话、只记得大概意思也能命中**。比 BM25 多一层「懂意思」，但要建索引、有成本。                                                                                         | 半有。DSH 的 `kb` 库是向量（§4.2.2 第 2 层），但只有 120 页、路径还是旧的                 |
| RRF  | 「把多个引擎的榜单合成一张总榜」的公式（Reciprocal Rank Fusion）：只按名次倒数相加（第 1 名记 1、第 3 名记 1/3）重排名；因为只吃名次不吃分数，不同算法的分数量纲不同也不碍事。rohitg00 的「三路 RRF」= BM25 + 向量 + 图谱三条路各出一张榜，RRF 合成一张（§1.7.1 #2） | 否。BM25 和向量都没成体系，谈不上「三路合成」                                         |

#### （1）第一张表：四个方案逐行白话

| 方案                | 白话（它是什么、核心 idea）                                                                                                                                                                                                            | 你借了什么 / 没借什么                                                                                                                                                                                                                                        |     |
| :---------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- |
| Karpathy gist     | Karpathy 2026-04 的一篇 gist，**不是软件**：原话「Obsidian 是编辑器、LLM 是程序员、wiki 是代码库」。就三条思想：资料 / wiki / schema 三层；入库 / 提问 / 体检三操作；index+log 双索引；wiki 只许 LLM 写（§1.7.1 #1）。它只有思想、没有工具                                                       | 借：全部骨架。三层 = 你的 `10-source+20-md` / `30-wiki` / `90-tool`；三操作 = ingest.ps1 十二步 / Query 四步 / lint 十项；双索引 = index 4 分册 + log.md（§3.2 表）。不借：无。它的「够用就行」没工程化，光靠它走不到 300 本                                                                                 |     |
| rohitg00 v2       | ~2026-10 一篇 gist，给 Karpathy 骨架补「知识会过期、会冲突」的治理：生命周期（置信度 / 被取代 / 遗忘曲线）、6 类关系动词（uses / depends on / contradicts / caused / fixed / supersedes）、三路 RRF、6 个事件钩子、crystallize；原话「**别把 index.md 当 ~100 页之后的 LLM 主检索机制**」（§1.7.1 #2） | 借：生命周期三字段（status / confidence / supersedes，rules §13）；wikilink 后写关系词（借语义、不借图库）；钩子 4 个（ingest 查重第 0 步 / 写后 lint / precommit-guard / budget-watch）；crystallize = howto 机制（已定义、0 页在用）。不借：浮点置信度 + 遗忘曲线（无基准、无法验证）、图数据库。**它的检索（BM25+RRF）你没上——「最大缺口」就指这个** |     |
| geronimo llm-wiki | 最「产品化」：单个 Rust 二进制 + 24 个 MCP 工具 + JSON Schema 校验 + typed graph + tantivy BM25 + spaces 多空间 + 导出 llms.txt。核心原话「**入库时处理资料，不提问时重推**」（DKR）——这句正是你库的核心思想（§1.7.1 #3）                                                             | 借：DKR 思想；schema 校验思想（你用 wiki-lint 十项硬编码实现，还没有 schema 文件）。不借：Rust 引擎、typed graph、BM25、多空间、导出——五项全未上（§3.2 表）                                                                                                                                          |     |
| llm-wiki-skills   | geronimo 的配套：Claude Code 插件 + 17 个 skill 文件，原话「**引擎是哑管道，技能是大脑**」（§1.7.1 #4）。skill 只是 Markdown，谁都能读                                                                                                                          | 借：命名体系——只借 6 个核心名写进 AGENTS.wiki.md 章节名（setup / ingest / crystallize / lint / graph / research）。同构：你的脚本是哑管道，rules + AGENTS.wiki + prompt-dsh 是大脑。不借：Claude Code 宿主、17 个 skill 文件                                                                     |     |

#### （2）「我的改动」到底改了什么（方法 / 东西 / idea 三问三答）

- **方法**：没发明新方法，是把 Karpathy 骨架**工程化落地**——MinerU 解析 → 图名归一 → 图链自检 → 带页码锚点重建 → 重建索引，十二步串成 ingest.ps1 一条命令（§1.7.4 数据流）。核心方法论就一句：**知识在入库时被综合一次，之后只做维护**（§1.0 表）。
- **东西**：5 本书 → 4.25 MB 带页码锚点正文 + 1858 张图 + 542 页 wiki + 十项 lint + 双契约 + git 6 commits（§4.1 实测表）。四方案都没有的「三件套」：中文工程书解析链（%20 死链、假标题降级）、成本账 + 预算看门狗、双契约（§3.2 结论行）。
- **idea**（借来的四条最值钱的）：三层 + 三操作（Karpathy）、生命周期三字段（rohitg00）、schema 校验 + git 审计（geronimo）、技能命名法（skills）——就是 §3.2 结论行的四句话。取舍原则一句：「**工具可以借思想，债务只能自己还**」（§1.7.2 尾）。

#### （3）第二张表：六个升级方向逐行白话（解决什么问题 → 升级后长什么样）

| #   | 方向                      | 白话：现在哪里难受                                                                                                                | 升级后变成什么样                                               |
| :-- | :---------------------- | :----------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
| U1  | 检索上 BM25（最紧迫）           | grep 只认字面：记错一个字搜不到、命中不排序、命中超阈值时人工翻不动（§1.6.5 触发器：grep 命中 >200 条即该上 BM25）。且 542 页已过 rohitg00 的 ~100 页经验线，index 单分册最大 287 条 | 问法写错字也能命中、结果按相关度排序；Query 四步只换第 1 步工具（grep→BM25），其余流程不变 |
| U2  | frontmatter 改 schema 驱动 | 十一字段规则现在**写死在 lint 代码里**，每加一种页面类型（howto / comparison）就得改脚本                                                               | 字段规则落成一个 schema 文件，lint 第 0 项改成读它；加类型只改文件、不碰代码         |
| U3  | 事件钩子补齐                  | log 登记靠自觉；query 回填没有质量门槛，写坏页没人拦                                                                                          | 会话收尾固定登记 log.md；回填必须带 §节号 + #L 才准写——生命周期闭环             |
| U4  | typed graph 导出          | related 字段已存关系语义，但只有文本没有图；542 页 Obsidian 星图已开始糊（§1.2.6）                                                                  | 脚本从 related + supersedes 导出 Mermaid / DOT 关系图，不引图数据库   |
| U5  | llms.txt 导出 + 多空间       | 300 本 ≈ 7500 页：喂 LLM 没有打包出口；单 vault 星图糊成毛球（§1.2.6 尾行）                                                                    | 加 export 脚本（全页摘要打包）；按领域分册升为分 vault                     |
| U6  | 单页 git 历史               | 想查「这一页谁改过」没有现成入口                                                                                                         | 一条 `git log --follow -- <页路径>` 即得，写进 Query 手册，零成本      |

#### （4）明确不升级（防追新）白话

Rust 引擎重写管线（PowerShell + Python 是资产，推倒重写是负资产）、图数据库（几百到几千文件用不上）、浮点置信度 + 遗忘曲线（无基准、无法验证）、自动 crystallize（必须用户发起，AGENTS.wiki §4）、Claude Code 宿主。五条共同点：要么负资产、要么不可验证、要么违背现有契约（§3.2 尾表）。

### 3.2.2 页数多了会坏在哪：GitHub 上真实报出来的六类故障

名词（grep、BM25、向量、RRF）的白话解释在 §3.2.1（0），四个方案的逐行对照在 §3.2.1（1），这里直接用。表里的外部证据都是 2026-11-24 从一手页面读的；「本库」一列是当天实测。

先给判断：能查到的故障，没有一条是「文件太多存不下」。坏掉的是三样东西——索引还能不能塞进一次对话、模型还能不能记住「已经有什么」、页面上的话还准不准。

| 故障与证据                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | 为什么会这样                          | 别人的解法                                                                                                  | 本库（2026-11-24）                                                                                                                                               |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------ | :----------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1 索引撑爆上下文**。[llmwiki 0.2.1](https://docs.rs/crate/llmwiki/0.2.1) 算过账：500 页时 index ≈8,000 token，加 5 页正文 ≈10,000，合计 18,000，推理还没开始就用掉半个上下文；1,000 页 index 溢出，10,000 页不可用。Karpathy 原文说 index 只在 ~100 sources、几百页内够用（§1.1.7）。                                                                                                                                                                                                                                                                                                                                                                                                                                    | index 每加一页多一行，行数线性涨；每问一次都要重读全表。 | 换搜索引擎（Tantivy BM25 + 向量 + RRF），index 只留给人看；用 frontmatter `description`（<200 字符）当摘要片段；检索的 token 成本变成恒定。 | 已分册：index.md 只列 4 个领域，四个分册最多 307 行（`index-搅拌与混合设备.md`），单文件 token 压住了。检索仍是 grep，命中不排序。                                                                        |
| **2 索引靠 LLM 手写，越写越漂**。[lx-0/llm-wiki 的修复 commit](https://github.com/lx-0/llm-wiki/commit/090d8a2373d38c37f468c11918e7720cb2ba5eb3) 写明线上库漂成 362 条重复行、561 条缺失。                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | ...0                            | 索引改由脚本在编译后对账：表头与散文逐字节不动，行保位，重复行后者覆盖，悬空行删，缺的行补，幂等。                                                      | `wiki-index.ps1` 生成，不让 LLM 手写；lint 第 7 项查「页不在索引」与「索引行没有对应页」→ 这类风险已避开。                                                                                        |
| **3 一个概念两个名字，变成两页、来源拆散**。[atomicstrata/llm-wiki-compiler 的 commit](https://github.com/atomicstrata/llm-wiki-compiler/commit/f7df886ceb68178b8983066d737a323e59012d17)：抽取时把概念写成带别名的 wikilink（`[[Quality-Control\|Quality Control]]`），与纯文本 slug 不同，结果两页并存、来源各归一半。Karpathy gist 评论里也有人贴：不同 run 写成 company、Company、Business、Organization，图就不可靠（[评论](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6206100)）。                                                                                                                                                                                                            | 名字没有唯一约束，模型每次写法不同。              | 正名 + aliases 字段；lint 查同 title 重复、别名遮蔽；术语表定唯一译名。                                                        | 文件名 = title = 正名，rules §13 有 aliases；lint 第 5 项查同 title，第 9 项查别名遮蔽页名；glossary 是唯一译名（rules §1）→ 机制覆盖。                                                         |
| **4 页面过期，读起来跟新的一样**。[nate-b-jones 的对比摘要](https://raw.githubusercontent.com/tim-kaa-py/ai-wiki/3e4cd2e2bdda38d0e7ebe7531eb33a94aaeaa0ad/summaries/2026-04-22_nate-b-jones_karpathy-wiki-vs-open-brain.md)：wiki 一旧就成了主动误导，它会自信地写错，不像数据库缺数据那样露馅；建议每页标 last_updated，超 90 天的当可疑。[Oshayr 的规则](https://raw.githubusercontent.com/Oshayr/LLM-Wiki/main/rules/workflow.md)按内容类型给 TTL（live 15 分钟 … permanent never），过期标 stale。[rohitg00](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) 用 confidence 分数与 supersession 处理新旧答案。                                                                                                                      | 页面上没有时间信号，人和模型都会当真。             | updated 与 TTL、stale 标记、supersedes 链接、定期 drift audit。                                                   | 有 updated、status、confidence、supersedes 字段，lint 第 6 项查「引用已 superseded 的页」；**没有**按 updated 年龄的过期扫描（lint 不读 updated），也没有矛盾登记页 → 半覆盖。                            |
| **5 几百页之后，关键词检索开始漏**。[Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 原话是 at small scale the index file is enough, but as the wiki grows you want proper search，并点名 qmd。[memory-layer 的调研](https://raw.githubusercontent.com/Kinvecta/the-memory-layer/refs/heads/main/Part%204%20-%20Recall%20at%20Scale/research-brief.md) 汇总了上下文变长的代价：Lost in the Middle 里 GPT-3.5 在 20 篇文档中段作答 53.8%，低于闭卷 56.1%；Chroma 2025 测 18 个模型，输入越长越差；NoLiMa 32K 时 10/12 模型掉到短上下文一半以下；Anthropic 的经验是全塞 <200k token（约 500 页）。                                                                                                                     | grep 只认字面，人提问不会正好用页面里的词。        | BM25 管精确词、向量管意思、RRF 合榜、重排；返回片段与上下文，不返回整页。                                                              | grep + kb 向量库（120 页旧路径）。560 页已过 rohitg00 的 ~100 页经验线；§1.6.5 的「grep 命中 >200 条」触发器还没量过——这是下一步该做的实测。                                                            |
| **6 多人多 agent 一起写，体检靠自觉**。[nate-b-jones](https://raw.githubusercontent.com/tim-kaa-py/ai-wiki/3e4cd2e2bdda38d0e7ebe7531eb33a94aaeaa0ad/summaries/2026-04-22_nate-b-jones_karpathy-wiki-vs-open-brain.md) 说多个 agent 并发写同一批 md 会坏、团队共用会裂；[rohitg00](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) 用 mesh 同步（last-write-wins，冲突留时间戳与人工覆盖）、6 个钩子、self-healing lint；[alirezarezvani 的 wiki-lint](https://github.com/alirezarezvani/claude-skills/blob/5909a72e62b5fbb809935fb6a55b58bdbe175074/engineering/llm-wiki/commands/wiki-lint.md) 把检查分成机械项（孤儿页、断链、stale、缺 frontmatter、重名、log 断档）与语义项（矛盾、结构漂移），优先级 contradictions > 断链 > 孤儿 > stale。 | 写者之间没有锁；检查不跑等于没有。               | 单写者或锁、每次操作即 commit、钩子替代自觉。                                                                             | 单写者（AGENTS.wiki §0 LLM 独占写），git 8 个 commit，4 个钩子（ingest 查重第 0 步、写后 lint、precommit-guard、budget-watch）；lint 10 项覆盖机械项。但 lint 要人记得跑（没有会话收尾强制），crystallize 0 页。 |

六条里，1、2、3、6 的修法是同一个动作：把「靠模型自觉」换成「靠脚本确定性」，它们决定库会不会写坏。4 和 5 是内容层面的：4 管还准不准，5 管找不找得到。你的库在 1、2、3、6 上有脚本兜底，所以 §3.2 只把检索列为最大缺口；按这些事故看，还该补一条——页面新鲜度没有机器检查。

数字口径：§3.2 写 542 页是 11-23 的数；今天 `30-wiki\pages` 下 md 实测 560，差 18 页的原因没查。两者都远超 100 页线，不影响判断。

### 3.2.3 LLM Wiki v2 是怎么干的

出处 [rohitg00 的 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)，2026-11-22 最后改（第 7 版），约 1.7k stars。它是设计说明，不是软件：没有代码，没有基准测试，里面的数字是作者经验。主张一句：stop re-deriving, start compiling——同一个结论不要每次提问重新推，编译进 wiki 一次，以后只维护。

| 模块          | 原文怎么做                                                                                                                                                                   | 大白话                                       |
| :---------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------- |
| 记忆生命周期      | confidence scoring（来源数 + 最近核验 + 矛盾，例 0.85）；supersession（新页链旧页，旧页留档标 stale）；forgetting（Ebbinghaus 衰减，访问或强化则重置）；consolidation（working → episodic → semantic → procedural） | 给每条知识记「多可信、有没有被取代、该不该忘」。旧结论不删，标成过时并链到新结论。 |
| 类型化知识图谱     | 抽 people、projects、libraries、concepts、files、decisions；关系固定 6 种：uses、depends on、contradicts、caused、fixed、supersedes；图遍历答影响面（例：升级 Redis 会影响哪些页）                            | 把「谁依赖谁、谁推翻了谁」变成能查的结构，不只是一句 related 文本。    |
| 能扩的检索       | index.md 只在 ~100-200 页内可靠，再长就要真检索；hybrid = BM25 + 向量 + 图遍历，RRF 合榜；index 只当人读的目录                                                                                         | 三张榜单合成一张：精确词靠 BM25，意思靠向量，关系靠图。            |
| 六个事件钩子      | 新来源→自动 ingest；会话开始→载上下文；会话结束→压缩回写；query→质量分过线才回填；写记忆→查矛盾、触发 supersession；定时→lint、consolidation、retention                                                                | 把「记得做」变成「系统在某个时刻自动做」。                     |
| 质量与自愈       | 给一切打分；self-healing lint 自动修孤儿链接、标 stale、修断链；矛盾按来源新旧、权威、支持数给候选，不自动覆盖                                                                                                     | 体检不只报告，还能修低风险项；矛盾只提候选，人来定。                |
| 多 agent 协作  | mesh 同步（last-write-wins，冲突带时间戳与人工覆盖）；shared 与 private 分区；work coordination                                                                                              | 多人多 agent 写同一库时，先约定谁写哪块，冲突有兜底。            |
| 隐私          | ingest 时过滤 API keys、tokens、PII；每操作留 audit trail；批量操作可逆                                                                                                                  | 密钥不进库；做过什么可查；批量改动能回滚。                     |
| crystallize | 把完成的研究、调试、分析蒸馏成一页 digest（question、findings、entities、lessons）                                                                                                            | 干完一件事，把结论沉淀成页，下次不用重查。                     |
| 输出形态        | 不限 markdown：比较表、时间线、依赖图、幻灯片、JSON-CSV、brief                                                                                                                              | 同一份知识按场景换壳。                               |
| schema 是产品  | CLAUDE.md 与 AGENTS.md 写清实体类型、ingest 规则、何时新建还是更新、质量标准、矛盾怎么处理、consolidation 周期、私有还是共享                                                                                     | 真正决定库能不能长的是那份写者契约，不是代码。                   |
| 实施光谱        | minimal → lifecycle → structure → automation → scale（hybrid search、consolidation、quality scoring）→ collaboration                                                        | 可以只抄第一层，后面按规模加。                           |

与页数增长直接相关的只有三块：检索（第 3 行）、新鲜度（第 1 行）、钩子（第 4 行）。图谱（第 2 行）和多 agent（第 6 行）是另外两个方向。作者自己在回帖里把可靠上限说成 200-500 文档（实践者意见，不是测出来的），比 gist 里的 100-200 页宽。别把 gist 里的数字当基准。

### 3.2.4 本库 vs v2：差在哪，升级怎么选

§3.2.1（2）已经答过「方法、东西、idea」，从 v2 的角度再补一句：v2 的 idea 是「把推导编译进库」，你的落地是把这句话变成一条能审计的中文管线（MinerU → md → 页 → 索引 → git）。它有生命周期字段，没有解析链；你有解析链，检索弱。互补的位置就在这里。

| 维度          | v2 的做法                        | 本库现状（2026-11-24 实测）                            | 判定       |
| :---------- | :---------------------------- | :--------------------------------------------- | :------- |
| 写者          | 单写者 + 钩子                      | LLM 独占写（AGENTS.wiki §0），脚本只写机器区                | 同        |
| 知识单元        | 原子页，一实体一页                     | 一断言簇一页（rules §12.1）                            | 同思想，粒度不同 |
| 检索          | BM25 + 向量 + 图，RRF             | grep + kb 向量库（120 页旧路径）                        | 弱        |
| 关系          | 6 类 typed 关系 + 图遍历            | wikilink + related 文本，无图                       | 弱        |
| 生命周期        | 浮点 confidence、遗忘、supersession | status、confidence、supersedes、updated；无 TTL、无遗忘 | 半        |
| 钩子          | 6 个                           | 4 个（缺会话收尾、query 回填门槛）                          | 半        |
| 校验          | JSON Schema 文件                | lint 10 项写在脚本里                                 | 半        |
| 审计          | 每次操作 git                      | 每本书 ingest 后 commit；共 8 个 commit               | 同        |
| 多人          | mesh 同步                       | 单人单写                                           | 不需要      |
| 输出          | 多形态                           | md + 图 + 索引                                    | 够用       |
| 成本          | 未提                            | 成本账 + 预算看门狗                                    | 本库更强     |
| 中文工程书       | 无                             | MinerU 链、假标题降级、%20 修链、页码锚点                     | 本库独有     |
| crystallize | 机制 + 钩子                       | howto 已定义，0 页                                  | 未用       |

一句话区别：v2 面向通用知识工作、多人多 agent、要长期长；你的库面向单一领域、中文工程书、单人维护、要能引用到行。它的强项正好是你的短板（检索、新鲜度），你多出来的是它没有的（中文解析、成本治理、双契约）。所以升级不是照它重做，是把它那两块补进来，已有的解析链不动。

四套可选动作，按「解决什么 → 改完什么样」列：

| 套餐 | 解决什么问题 | 具体改什么 | 改完一次提问什么样 | 代价与风险 |
|:---|:---|:---|:---|:---|
| **A 只换检索第一棒**（BM25） | 记错一个字就搜不到；命中不排序，多了翻不动 | 装 qmd CLI；Query 四步的第 1 步从 grep 换成 `qmd search`（BM25 模式），页面、契约、lint 都不动 | 问「永田进治关联式怎么推」→ 输入带错字也能命中，前 10 条按相关度排；再 read 2-3 页 | 装一个外部程序；排序结果与 grep 不同，要适应几天；可回退（grep 还在） |
| **B 混合检索 + 评估** | 只记得意思、不记得原话；也想知道改了到底有没有用 | qmd MCP（`qmd query`：BM25 + 向量 + RRF + 重排）；先建 20-50 个真实问题的 golden set，量 Recall@5，再决定上线 | 模糊问法也能召回；每次改检索有数字对比 | 向量索引重建（embedding 费用与时间）；MCP 接入；人工标注 20-50 题；风险中 |
| **C 新鲜度与回填治理** | 页面旧了没人知道；回填没门槛；单页历史不好查 | lint 加第 11 项「updated 超过 N 天」；会话收尾固定登记 log.md；query 回填必须带 §节号 + #L；手册加 `git log --follow` | 跑 lint 能看到「90 天没动」的页；答案带更新时间；改坏能追 | 改 lint 脚本与契约文字；每天多一步登记；风险低 |
| **D 规模化**（typed graph、export、多 vault） | 300 本时星图糊、没有打包出口、关系查不了 | 脚本从 related 与 supersedes 导出 Mermaid 或 DOT；export 脚本打包摘要；按领域分 vault | 能查「哪些页依赖这条结论」；能给外部模型一包摘要 | 中高；分 vault 要迁移；等 300 本再做（§1.6.5 E 档） |

选哪个，先回答三个问题：

1. 最烦的是「找不到」还是「怕写错、过期」？前者 A 或 B，后者 C。
2. 愿不愿意在库里多装一个检索程序？qmd 是独立 CLI，要单独装；不愿意就继续 grep，但问法得写准。
3. 要不要「能证明检索变好了」？要就 B（golden set），不要就 A。

我的建议（这段是判断，不是证据）：**C → A → 两周后看数据再定 B → D 等 30 本**。C 一天能做完、零依赖，直接消掉「自信写错」这个隐性风险；A 收益最直接，560 页已经过阈值；B 要先有评估集，没量就上等于花钱买感觉。

升级后这个库长什么样，拿一次提问走一遍：

- 现在：问「搅拌功率准数怎么算」→ grep 搜关键词 → 命中几十行 → 逐页 read → 可能引到旧页，答案里没有时间信息。
- 做完 C + A：问题进 BM25 → 前 10 条按相关度排 → 每页带 updated 与 status → 只 read 2 页 → 答案写「《搅拌与混合设备设计选用手册》§1.4（#L960-#L1064），2026-11-16 更新」；跑 lint 时还会多一行「12 页 90 天没动」。
- 做完 B：模糊问法（只记得「那个算功率的经验式」）也能召回；每次调检索参数有 Recall@5 数字可对。

换检索不影响已有 560 页的写法，这正是 §3.2 表里 U1 的设计：只换第 1 步工具，接口不变。

## 3.3 升级方案：上万页、两类入库，照 LLM Wiki v2 光谱重排（2026-11-24 推翻旧版重写）

> 推翻说明：旧版（2026-11-24 定稿）只解决“索引、检索、回答”三件事，是 560 页规模的补丁。你随后提的三个前提让它的框架失效：**① 知识页会到上万个、覆盖各专业各职业方向；② 入库分两类——资料入库（永久有效）与经验入库（会话/项目结晶），进不同子文件夹；③ 不共享、单人单写，git + GitHub 已就位。** 新版按 §3.2.3 的 v2 模块清单逐项定“做/不做/何时做”：collaboration 整块砍掉，lifecycle 升为主战场，index 从“每次提问的目录”降级为“领域路由表”。旧版经得起推敲的部件保留并注明：自建 BM25 的理由、golden set 度量法、回滚原则。§3.2.4 四套餐的选型结论并入本方案：C→P2、A→P1、D→P3、B→规模触发器（§3.3.5）。

### 3.3.0 三个新前提如何推翻旧版

| 你的前提（2026-11-24）                 | 旧版 §3.3 失效在哪                                                                 | 新版改法                                                              |
| :------------------------------- | :--------------------------------------------------------------------------- | :---------------------------------------------------------------- |
| 知识页上万（不是 300 本的 7500 页，而是全领域上万页） | 二级分册只在 4 个领域里切；“3 万页重建 ≤10 分钟”没有实测路径                                         | 领域路由 + 多级分册 + 预建倒排索引；规模触发器给具体页数（§3.3.4、§3.3.5）                    |
| 资料入库永久有效、经验入库有寿命                 | 旧版 lint 第 11 项对全库一刀切按 `updated` 年龄告警——资料页（如 GB/T 150 的公式）90 天不动是正常的，全库扫描全是噪音 | 两区两规：资料区无 TTL，经验区才做 90 天复检（§3.3.2）                                |
| 不共享、单人单写                         | （旧版没做多人设计，无失效项）                                                              | v2 的 mesh 同步、多空间、shared/private 分区、work coordination 全部不做（§3.3.1） |
| 经验入库要有独立落点                       | 旧版 crystallize 落 howto\，与资料页语义混在一层                                           | 新建 notes\ 经验区；howto\（0 页）并入（§3.3.2）                               |

### 3.3.1 v2 模块清单逐项定夺（本方案主表）

| v2 模块（§3.2.3）                    | 本库动作                                                                                                    | 阶段  |
| :------------------------------- | :------------------------------------------------------------------------------------------------------ | :-- |
| 记忆生命周期                           | **做，分两区**：资料区 permanent、经验区 90 天复检（§3.3.2）。浮点 confidence、Ebbinghaus 遗忘曲线仍不做（无基准，§3.2 已定）                | P2  |
| 类型化知识图谱                          | **半做**：6 类关系词已用（related 字段）；新增 Mermaid/DOT 导出给人看；**不进检索**（v2 三路 RRF 里的 graph traversal 不借——上万页单机维护图库不值） | P3  |
| 能扩的检索                            | **做**：自建 BM25 + 预建索引 + 领域路由；index 不再当 LLM 主检索入口（v2 原话 “don't rely on index.md … past ~100 pages”）       | P1  |
| 六个事件钩子                           | **做**：已有 4 个，补 2 个（会话收尾结晶清单、query 回填门槛）（§3.3.6）                                                         | P2  |
| 质量与自愈                            | **做**：lint 分区扫描 + 锚点自检（旧版 check-anchors 保留）                                                             | P2  |
| crystallize                      | **做**：落 notes\，digest 四字段，**禁止自动结晶**（§3.3.7）                                                            | P2  |
| 多 agent 协作（mesh/last-write-wins） | **不做**：单人单写，git 审计已够                                                                                    | —   |
| 隐私（密钥过滤/audit trail）             | **半做**：ingest 加一条“删 API key/PII”入 rules；audit = 每操作 git commit（已有）                                      | P0  |
| 输出形态                             | **半做**：md + 对比表已够；加图谱导出与 llms.txt 打包出口（P3）                                                              | P3  |
| schema 是产品                       | **做**：十字段 + description 落成 schema 文件，lint 第 0 项读它（旧版 U2 落地）                                             | P0  |
| 实施光谱                             | 本方案即光谱：minimal（已完）→ lifecycle/structure/automation（P0–P2）→ scale（P3–P4）→ collaboration（砍）               | 全阶段 |

### 3.3.2 目标结构：两类知识，两区两规

```
30-wiki\
├─ pages\      资料区（现有 560 页不动）：外部资料编译出的知识页，永久有效
├─ notes\      经验区（新建，0 页起步）：会话结晶 + 项目复盘，有寿命
├─ sources\    每本书/每份资料 1 页章节地图（导航，不算知识页）
├─ openq\      冲突与缺口登记（不算知识页）
├─ index.md    领域树（人看目录 + 检索的领域路由表）
├─ index-<领域>.md  多级分册（单册 ≤300 行，超了下沉一级）
├─ glossary.md 唯一译名表（含领域名登记）
└─ log.md      append-only 时间线
```

迁移动作（P0）：pages\、sources\、openq\ 原样保留；新建 notes\；howto\ 现有 0 页、语义并入 notes\（rules §12 目录清单同步改）。**零文件移动、零重链**。

两区生命周期对照：

|               | pages\（资料区）                        | notes\（经验区）                                |
| :------------ | :--------------------------------- | :----------------------------------------- |
| 知识来源          | 书/规范/论文/权威资料，经 ingest 编译           | 会话问答、项目实操的结论与做法                            |
| 有效性           | **永久**（TTL=permanent）              | 有寿命：`updated` 超 90 天 → lint 告警复检           |
| status 流转     | draft → stable →（被新资料取代）superseded | draft → stable →（过时/被资料页覆盖）superseded      |
| supersedes 方向 | 只指向同区新页                            | 可指向同区页，**也可指向 pages\ 资料页**（经验被资料“转正”）      |
| confidence 初始 | high/medium（按来源权威）                 | 默认 medium；low 必须正文说明                       |
| lint 扫描       | 查 superseded 链、死链、来源格式（现有十项）       | 同上 + 第 11 项按 `updated` 年龄告警（**只扫 notes\**） |

### 3.3.3 生命周期细则

1. **资料区无 TTL**：书里的公式不会因为放 90 天就错，`updated` 只作记录、不触发年龄告警。superseded 只由同区新页发起（新规范取代旧规范），旧页不删、标 superseded 并链新页（现有 rules §4 机制）。
2. **经验区有寿命**：`updated` 硬必填；lint 第 11 项 = notes\ 内 `updated` 超 90 天 → warning（先跑一遍看告警量再定阈值）；告警清单写 log.md。
3. **取代方向**：资料页可以取代经验页（经验被书“转正”）；经验页不能取代资料页（个人经验不能推翻书籍结论——要推翻走 openq 冲突登记）。
4. 冲突仍登记 openq，两区共享（现有机制不变）。

### 3.3.4 领域路由：上万页的第一道闸

上万页 = 几十个领域 × 每领域数百页，任何“全库一次读完”的入口都不成立（旧版已算：3 万页 index ≈ 200 万 token）。所以检索分两步：

1. **定域**：问句 → 模型读 index.md 领域树（几十行）→ 定 1–2 个领域。
2. **域内检索**：只对该领域分册做 BM25（§3.3.5）。跨域问题 = 两个域各搜再合并；真正的全域问题才走全库 BM25。

配套机制：

- index.md 从“页面清单”改成“领域树”：一行一个领域/子领域 + 指向分册；分册才列页。
- 分册多级：单册 >300 行自动下沉一级（旧版二级分册的自然推广，不限深度）。
- 领域名登记进 glossary.md（唯一译名：同一领域不许两个叫法）。
- 新领域 = 入库时 index.md 加一行；lint 第 7 项查漂移（现有）。

### 3.3.5 检索：自建 BM25 + 预建索引

**沿用旧版结论**：自建而不是装 qmd/llmwiki——本机无 Rust；qmd 要下载模型；llmwiki 的 frontmatter 契约与本库冲突（要 `tier` 与数值 `confidence`，`.index/` 目录会与 lint 第 7 项漂移检查打架）。**新增一条规模理由**：上万页必须预建倒排索引，自建才能把索引格式与字段权重握在手里。

`90-tool\scripts\kb-search.ps1`（P1）：

- **构建**：扫描 pages\ 与 notes\ 的 frontmatter + 正文 → 倒排索引 + 文档元数据，落 `90-tool\search-index.json`（或 SQLite）；每次 ingest 收尾重建；lint 校验索引覆盖页数 = 实际页数。
- **取词**：中文字符二元组（不装分词器，`搅拌功率` → 搅拌 / 拌功 / 功率）+ ASCII 词/型号；不依赖词典。
- **打分**：BM25 `k1=1.2`、`b=0.75`；字段权重 `title×3`、`aliases×2`、`description×2`、正文×1。
- **输出**：`[1] pages/搅拌功率准数.md  score=12.4  updated=2026-11-16  domain=搅拌与混合设备`，下行 `title/aliases` + `desc`，再行 `hit: #L960 "功率准数" · #L1002 "Np"`。
- **参数**：`-Q "..."`、`-Top 10`、`-Domain 搅拌`（先定域再打分）。

规模触发器（替代旧版“等页数到再说”，给具体数字）：

| 页数 | 动作 |
|:---|:---|
| ≤ 2,000 | 现在这套（grep + kb-search 并存 A/B） |
| > 2,000 | 实测单次检索延迟；>5 秒 → 索引迁 SQLite（kb-search 只换存储层，接口不变） |
| > 5,000 | golden set 重跑；Recall@5 <85% 或模糊问法失手率 >20% → 评估向量层（§3.2.4 套餐 B 的触发条件兑现） |
| 上万页 ≈ 30–50 MB md（按每页 3–5 KB 估【估计】） | 落在 §1.6.4 B 档上沿 / C 档下沿，与上表触发器自洽 |

### 3.3.6 六个事件钩子（单人版）

| v2 钩子 | 本库现状 | 动作 |
|:---|:---|:---|
| 新来源 → 自动 ingest | 已有：ingest 查重是第 0 步 | 不变 |
| 会话开始 → 载上下文 | 半有：会话开场 git status 审计（§1.3.12） | 加一条：同时读上次 lint 告警清单与 log 尾 5 条 |
| 写记忆 → 查矛盾/触发 supersession | 已有：ingest 第 6 步回改受影响页、冲突开 openq | 不变 |
| query → 质量分过线才回填 | 无 | **补**：回填门槛见 §3.3.7 |
| 会话结束 → 压缩回写 | 无 | **补**：会话收尾固定三件事——log.md 登记一行、“库里没有”汇总给用户、列候选结晶页（1–3 页）由用户挑，**不自动写** |
| 定时 → lint/consolidation | 半有：lint 靠人记得跑 | 固定节奏：每次 ingest 后必跑（已有）+ 每周全量 lint 并在 log 记一行；不建常驻服务 |

### 3.3.7 crystallize：经验区的落地规则

- 落点：`notes\<日期>-<主题>.md`；type 新增枚举 `note`（结晶页），`howto` 沿用（做法页）。
- digest 四字段（v2）：`question`（当时的问题）/ `findings`（结论逐条）/ `entities`（涉及哪些页与实体）/ `lessons`（教训与适用边界）。
- 来源写法：库里查到的 → 照旧双轨《书名》§节号 + #L；会话里自己推的 → 写“本会话推导（日期），依据见 findings 内引用”，confidence ≤ medium。
- 门槛（旧版“回填必须带 §节号+#L”的放宽版）：每条结论要么带库内引用，要么整体标“本会话推导”且 confidence=medium 以下；**两样都没有的不许进 notes\**。
- 禁止自动结晶：必须用户明确说“记下来”才写（AGENTS.wiki §4 已有）。

### 3.3.8 schema 落文件（旧版 U2 落地）

- 现有十字段（type/title/aliases/domain/status/confidence/sources/related/supersedes/updated，rules §13）+ 新增 `description` 字段：≤200 字，写“这页回答什么问题、给什么数”，不许复制标题（旧版 P0 保留项）。
- `type` 枚举加 `note` → 七选一（concept/entity/source/comparison/howto/openq/note）。
- 两区字段子集：notes\ 的 `updated` 是硬必填（资料区缺 updated 只 warning）。
- 落 `90-tool\schema.md`（机器可读表）；wiki-lint.ps1 第 0 项改为校验它，加字段只改文件不改代码。

### 3.3.9 图谱与打包出口（P3，可延后）

- 关系词已用（`[[B]]（取代）` 等）；`graph.ps1` 从 related/supersedes 导出 Mermaid/DOT → Obsidian 星图按领域限定视图（§1.3.12 已有）。
- `export.ps1`：每页 title + description + 领域打包成一份 llms.txt/摘要包（geronimo export 的简化版），喂外部 LLM 或迁移用。
- 明确不做：typed graph 数据库、图谱参与检索。

### 3.3.10 分阶段执行与验收

| 阶段 | 做什么 | 验收（数字） | 工期 |
|:---|:---|:---|:---|
| P0 结构 + schema | 建 notes\；howto 并入；schema.md 落文件；type 加 note；ingest 加隐私一条（删 API key/PII） | notes\ 就位；schema 校验跑通 560 页 0 错；lint 第 0 项换源 | 0.5 天 |
| P1 检索 | kb-search.ps1（构建+查询）；index.md 改领域树、分册多级；补 description（脚本出初稿、人工改） | description 覆盖 560/560；Recall@5 ≥85%（先量 grep 基线）；560 页单次 ≤2 秒；每条带 #L | 2 天 |
| P2 生命周期 + 钩子 | lint 第 11 项（只扫 notes\）；回填门槛写进 AGENTS.wiki；会话收尾三件事落 SOP | 拒答正确率 ≥90%；锚点有效率 100%；notes\ 0 页起步、规则先行 | 2 天 |
| P3 图谱 + 出口 | graph.ps1、export.ps1 | Mermaid 能出、llms.txt 能打包 | 1 天 |
| P4 规模 | 触发器值守（§3.3.5 表） | 页数跨 2,000 / 5,000 时按表动作 | 到点再说 |

P0 先做的理由（同旧版）：结构是后面一切的底座；notes\ 空仓建好，第一批经验才有地方落。

### 3.3.11 度量、顺序与回滚

golden set 从旧版 30 题扩到 **40 题、跨 3 个领域**（现有 5 本书内：化工原理 / 搅拌 / 压力容器各抽），构成：事实定位 12、概念解释 6、跨书对比 8、定位到节 8、库里没有 6。每题记“期望页 + 期望节 + 为什么”，不许只记答案（旧版口径保留）。以后每新入库一个领域补 5–10 题。

| 指标 | 口径 | 现状 | 目标 |
|:---|:---|:---|:---|
| Recall@5 | 40 题里期望页出现在前 5 的比例 | 待量（grep 基线） | ≥85% |
| 拒答正确率 | 6 道“库里没有”题答“没有”的比例 | 待量 | ≥90% |
| 锚点有效率 | 答案 #L 指向真实且相关的行 | 未测 | 100% |
| 领域路由准确率 | 定域正确 / 40 题 | 待量 | ≥90% |
| 索引覆盖 | 最大分册行数 / description 覆盖率 / 漂移数 | 307 / 0 / 待测 | ≤300 / 100% / 0 |
| 单次提问 token | 定域 + 检索 + 读 2–3 页 | 约 3–6k（估） | ≤8k |

顺序：P0 → 量 grep 基线 → P1 → 同题重跑 → P2 → 抽检 → P3 / P4 按触发器；每阶段 log.md 记一行（沿用）。

回滚（沿用旧版原则）：只加一个目录（notes\，空）、两个脚本、一个 schema 文件、一个 frontmatter 字段；不动解析链、不动 pages\ 现有 560 页。回滚 = 删脚本、lint 关两项、notes\ 删空仓。

改前改后一次提问：

- 现在：问“两台叶轮叠加的功率怎么算” → grep 搜“功率” → 命中几十行、跨 3 个分册 → 逐页 read → 可能引到只讲单叶轮的页 → 答案无行号，无法核。
- P1 后：定域“搅拌与混合设备” → `kb-search -Domain 搅拌 -Q "叠加 功率"` → 第 1 条 `pages/搅拌功率准数.md` score 12.4，`hit: #L960` → 只 read 这一页 → 答案“《搅拌与混合设备设计选用手册》§1.4（#L960-#L1064）”。
- P2 后：你追问“我上次项目里 DN800 釜改双层桨的经验” → notes\ 命中一页（若 90 天没动，lint 已提醒复检）→ 答案并列“资料页说法（#L…）”与“经验页结论（日期，medium 置信度）”，冲突则引 openq。
- 库里没有：最高分低于阈值 → 答“库里没有”，log 记缺口 → 周汇总进 openq → 下一批入库选题（旧版机制保留）。

---

# 4. 使用说明（人 + Agent 共用）

> 位置：`D:\Shervon_KnowledgeBase\知识库蓝本.md`（第四部分）｜ 版本 v1.3 ｜ 2026-11-17 并入（2026-11-25 随 §3.3 升级同步）
> 读者：人（你、同事）＋ Agent（DSH 或任何能读文件的模型）
> 一句话：先查 wiki，再查索引，再查原文，最后给「书名 + 节号 + 行号」；查不到就说查不到。
> 本部分编号随全文三层编号（§4.0–§4.8）；原独立文件 `使用说明.md` 已并入本蓝本后删除。「给老板演示」已删除、「换电脑迁移」已拆入第 3 部分（2026-11-23）。

## 4.0 六行速读（人和 Agent 都先看这里）

| #   | 事实                                                                                  |
| :-- | :---------------------------------------------------------------------------------- |
| 1   | 库根目录 `D:\Shervon_KnowledgeBase`，整个文件夹可拷走，不依赖数据库。                                    |
| 2   | 查问题顺序：`30-wiki`（先 `kb-search.ps1` 检索）→ `kb` 语义检索 → `20-md` 全文 → 原件 PDF。                        |
| 3   | 合格答案 = 书名 + 节号 + `#L行号`；没有就写「库里没有」。                                                 |
| 4   | **5 本书都已解析；`30-wiki` 570 页（pages 560 + sources 7 + openq 3，经验区 notes\ 0 页起步）。DSH 检索索引 `kb` 仍是 120 页旧路径**（§4.6.3 待重导入）。 |
| 5   | 只查询：装 DSH 就够（库索引现状见 §3.1.4）。加新书：还要 Python + MinerU + 2.0 GB 模型。                     |
| 6   | 新文件只进 `40-scratch\`；`10-source\`、`20-md\` 不许手改。                                     |

## 4.1 库里有什么（2026-11-23 实测）

| 目录           | 放什么                          | 谁写                          | 人能不能手改         |
| :----------- | :--------------------------- | :-------------------------- | :------------- |
| `00-inbox\`  | 待入库的书，一本书一个文件夹               | 人投放                         | 可以，入库后清空       |
| `10-source\` | 原件 PDF（只读存档）                 | 人放一次                        | 不改、不删          |
| `20-md\`     | 解析出的正文 `.md` + 每本书的 `图片\`    | `ingest.ps1` / `figures.py` | 不改（要改走脚本）      |
| `30-wiki\`   | 结论页（pages 560 / notes 0 / sources 7 / openq 3）、目录、待办（rules §12 机器区+人写区，两区两规） | 机器区脚本；人写区只有 LLM 写 | Obsidian 里只读   |
| `40-scratch\`    | 报告、日志、脚本、临时目录                | 任何人                         | 可以，别当仓库        |
| `90-tool\`   | 规则、提示词、脚本                    | 人改规则                        | 改前看 `rules.md` |

现状数字（2026-11-23 实测）：

| 指标 | 数值 |
|:---|:---|
| 书 | 5 本：化工原理（王志魁 第5版）、气液搅拌釜 γ-CT（刘跃进/韩路长 2014）、搅拌与混合设备设计选用手册、混合原理与应用（永田进治 1984）、GB/T 150.1~150.4-2024 |
| 正文 | 5 份 md，4,453,821 B（4.25 MB）、2,703,618 字符（约 90 万汉字） |
| 图 | 1858 张、125,192,558 B（119.4 MB，`20-md\*\图片\`） |
| wiki | 570 个 md：pages 560 + sources 7 + openq 3（经验区 notes\ 0 页起步，howto 并入） |
| 图链 | 五本全通：337 + 426 + 561 + 137 + 397，`unresolved=0` |
| 体积 | 286.3 MB → 约 380 MB（原件 256.6 + 20-md 123.7 + 30-wiki 2.3） |
| 版本 | git 8 次提交 + GitHub 私有仓库（§3.3 升级改动随本次提交） |
| DSH 索引 | `kb` 库 120 页，119 条路径仍指旧 `50-wiki\concepts\`（建议清空重导入，见 §4.6.3） |
| 描述覆盖 | `description` 560/570 页（pages 全满；sources/openq 不强制，见 `90-tool\schema.md`） |

三层结构：原件（`10-source`）→ 可检索正文（`20-md`）→ 结论页（`30-wiki`）。规则在 `90-tool\rules.md`（解析层）与 `90-tool\AGENTS.wiki.md`（wiki 层）。

## 4.2 人怎么问（核心）

### 4.2.1 一句话模板

> 在 `kb` 库查：**〈问题〉**。要**〈定义/公式/判据/对比/出处〉**，给书名 + 节号 + `#L` 行号；库里没有就说没有。

三个要素缺一不可：**范围**（哪本/跨书）、**要什么**（结论还是原文）、**用途**（写报告/选型/答辩，决定深度）。

### 4.2.2 四层检索（Agent 按这个顺序走）

| 层   | 查什么            | Agent 用什么                      | 命中什么            | 局限              |
| :-- | :------------- | :----------------------------- | :-------------- | :-------------- |
| 1   | `30-wiki` 570 页 / 9 分册 | `kb-search.ps1`（-Q/-Top/-Domain）＋ `read` | 已有结论、跨书对比、已登记缺口，带 score/domain/#L 命中行 | 覆盖 5 本书，细节以原文为准  |
| 2   | `kb` 语义块       | `library_search(library="kb")` | 记不清原话时的相近段落     | 120 页旧路径索引；返回块不带行号 |
| 3   | `20-md` 全文     | `grep` + `read`                | 精确原句、公式、行号      | 得先想到关键词         |
| 4   | `10-source` 原件 | 人打开 PDF                        | 图、版式、印刷页码       | 慢，且要人看          |

判定：第 1 层有现成页就直接用（最省，`kb-search.ps1` 秒级、自带 #L 行）；没有下到第 2、3 层；**第 2 层空/不相关 ≠ 书里没有**，必须回第 3 层 grep 才能说「没有」。

### 4.2.3 六个可复制模板

**① 定位**

```
在 kb 库找「<关键词>」：先 kb-search 查 30-wiki，再 grep 20-md。
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

### 4.2.4 追问四连（拿到第一版答案后）

1. 「给我 `#L` 行号。」
2. 「把那句原文贴出来。」
3. 「这条的适用边界是什么？什么工况不成立？」
4. 「另一本书怎么说？冲突在哪？」

### 4.2.5 合格答案判定（缺一条就打回）

- [ ] 每个事实断言有 书名 + 节号 + `#L行号`
- [ ] 数值带单位、带工况（温度、压力、介质）
- [ ] 公式符号式与文字式成对（按 `~/.agents/AGENTS.md` 第 1 节）
- [ ] 明确分「库中依据」与「我的判断」
- [ ] 查不到写「库里没有」，不拿常识冒充
- [ ] 跨书冲突单列，不合并

### 4.2.6 三个真实样例（已按库核对）

**样例 A：精确引用（grep 兜底）**

问：离心泵最大允许安装高度怎么定？

- 判据：实际安装高度必须低于最大允许安装高度；不汽蚀条件是有效汽蚀余量不小于允许汽蚀余量 ——《化工原理》第2章 六（`#L3787`）
- 计算式：式(2-16)（`#L3783`）；允许汽蚀余量 = 必需汽蚀余量 + 0.3 m 安全余量（`#L3775`–`#L3779`）
- 例题：例 2-4，40 ℃ 清水、Δh = 2 m、吸入管路损失 1 m（`#L3789`）
- 边界：必需汽蚀余量不能计算，只能实验（`#L3765`）

**样例 B：索引内检索（命中后仍要 grep 补行号）**

问：套管换热器的总传热系数怎么算？

- 串联热阻式 1/K：圆筒壁式(4-42)（`#L6907`–`#L6973`）
- 污垢热阻并入 R_d（`#L6977`）、表 4-6 污垢热阻（`#L6983`）
- 平壁/薄壁管简化（`#L7064`–`#L7070`）；K 经验值表 4-7（`#L7078`）
- 出处：《化工原理》§4.4 三、总传热系数（`#L6905`）
- 若 `library_search` 命中，仍要 grep 补行号；若未命中（索引旧），走样例 A。

**样例 C：口径冲突（先查冲突登记，防只按一本书答）**

问：液液分散的最小临界转速怎么定？

- 手册式与本书式冲突，已登记——这是「确认冲突」，不是「没查到」
- 冲突页：`30-wiki\openq\液液最小临界转速手册式与本书式冲突.md`
- 对比页：`30-wiki\pages\层流域搅拌器混合效率对比.md`
- 用法：两条口径都给出处再回答，不擅自二选一；挡「凭常识写公式」。

## 4.3 一本书从 PDF 到可引用：全流程（14 步）

> 泳道：**你**＝人，1 次操作 → **机**＝脚本，¥0 → **我**＝LLM 编译，≈¥0.51/本 → **问**＝下次提问，≈¥0.01/次（§1.3.9、§1.3.9）。每步末尾「出处」指向本文档小节，执行细节以出处原文为准。

```text
① 你   prompt＋新教材 PDF
    │   放进 00-inbox\ 一个文件夹（一本书＝一个入库夹，命名 书名_作者_版次_年份）
    │   工具：拖放即可                出处：rules §2 输入、§1 总则；§1.3.1 目标结构
    ▼
② 我   跑 90-tool\scripts\ingest.ps1 → 调 MinerU（mineru-kit：版面分析＋OCR）
    │   产出 20-md\<入库夹>\：全文 md（多册合并）＋图片\ 裁剪图＋MinerU 中间产物
    │   （middle.json 每块带 page_idx）；原件同步移入 10-source，inbox 清空
    │   出处：rules §3 输出、§2 输入；§1.8.7；§1.8.8
    ▼
③ 机   30-wiki 机器区自动重建（catalog.ps1 → catalog.md / manifest.csv / todo.md）
    │   图名归一 figures.py（caption 化、剥引用号）；质检（rules §7，ingest 内）
    │   出处：rules §7 质检、§11 图名归一；§1.3.1
    ▼
④ 机   一次性修补（每本各跑一次）：假标题降级 ## (n)→**(n)**；%20 死链解码
    │   （check-links.ps1 干跑 0 才过）   出处：P1-1；§1.8.7；P2-1
    ▼
⑤ 机   md-anchor.ps1 读本次解析的 middle.json → 在 20-md 插 <!-- page: N --> 页码锚点
    │   匹配失败率 >5% 即停；旧书已清理 middle.json 的需先重跑 MinerU 中间产物
    │   出处：§1.8.8；§1.3.7；P2-2
    ▼
⑥ 机   git add 20-md → commit（机器层闭环；后面 LLM 写坏可 reset 回滚）
    │   出处：§1.3.11；§1.8.9
    ▼
⑦ 我   Ingest 步0-2：查重（glossary＋pages＋index）→ 提取标题树 →
    │   写 sources\<书>.md（章节地图＋这本书能答/不能答什么）
    │   出处：§1.3.5 Ingest 表；AGENTS.wiki.md §1、§2
    ▼
⑧ 我   Ingest 步3-4：建/改 pages 页（定义/机理/口径/参数/边界/来源）
    │   引用图必有文字转述；转述不出 → 按需喂 deepseek-flash（Vision），钱记 log
    │   出处：§1.3.5 步4；§1.3.9；AGENTS.wiki.md §3
    ▼
⑨ 我   Ingest 步5：回改受影响旧页。两书口径矛盾 → 开 openq（不擅自二选一）；
    │   新断言推翻旧断言 → 旧页标 superseded，supersedes 指向新页，不删
    │   出处：AGENTS.wiki.md §4；§1.3.5 步5
    ▼
⑩ 机   wiki-index.ps1 重生成 index.md（领域树 + 多级分册，单册 >300 行自动下沉）；log.md 追加一条 ingest
    │   （touch=N、in/out token、¥）      出处：§1.3.5 步6、步7；§3.3.4
    ▼
⑪ 机   wiki-lint.ps1 十二项体检 → 30-wiki\_lint.md；kb-search.ps1 -Build 重建检索索引；git commit "ingest: 《书》 touch=N"
    │   出处：§1.3.5 Lint 表；§3.3.3、§3.3.5；§1.3.11
    ▼
⑫ 问   下次提问走 Query 六步：kb-search 定位主题 → 读 ≤10 候选页 →
    │   不够查 glossary 同义词 → 再不够才 grep 20-md 原文（最后手段）
    │   出处：§1.3.5 Query 表；§1.8.10；§3.3.6；§4.5
    ▼
⑬ 问   我回答：每条断言挂《书名》§节号＋#L行号；有锚点的书再附「第 N 页」。
    │   反复被问的点 → 用户说「记下来」才 crystallize 成 notes\（note/howto）或 pages\ 页，不自动写
    │   出处：§1.3.3 §14 引用约定；§1.3.5 Query 步4；§3.3.7
    ▼
⑭ 你   Obsidian 星图只读浏览（星图＝30-wiki 的 [[]] 网，graph.ps1 可导出 Mermaid/DOT）。规模触发器：
    │   ＞2,000 页实测延迟、＞5 秒迁 SQLite；＞5,000 页 golden set 不达标才评估向量层
    │   出处：§1.3.12；§3.3.5 规模表；§3.3.9
```

**工具清单（按出现顺序）**：

| 工具 | 图中步 | 干什么 | 出处 |
|:---|:--:|:---|:---|
| MinerU（mineru-kit CLI） | ② | PDF → md／裁剪图／middle.json（含 page_idx） | §1.8.7、§1.8.8 |
| `ingest.ps1` | ② | 编排解析、搬原件、质检 | rules §3、§7 |
| `figures.py` / `catalog.ps1` | ③ | 图名归一 / 重建 30-wiki 机器区 | rules §11、§3 |
| `check-links.ps1` | ④ | 死链体检 | §1.8.7、P2-1 |
| `md-anchor.ps1` | ⑤ | 页码锚点 `<!-- page: N -->` | §1.3.7、§1.8.8 |
| deepseek-flash（Vision） | ⑧ | 按需喂图拿文字转述 | §1.3.9.1 |
| `wiki-index.ps1` / `wiki-lint.ps1` | ⑩⑪ | 生成 index（多级分册）/ 十二项体检出 `_lint.md` | §1.3.7、§3.3.3 |
| `kb-search.ps1` | ⑪⑫ | 建/查 BM25 倒排索引（-Q/-Top/-Domain，带 #L 行） | §3.3.5 |
| `graph.ps1` / `export.ps1` | ⑭ | 导出 Mermaid/DOT 星图与 llms.txt 摘要包 | §3.3.9 |
| git＋GitHub 私有仓库 | ⑥⑪ | 版本历史、回滚、异地备份 | §1.3.11、§1.8.9 |
| Obsidian | ⑭ | 星图只读视窗（人机同步） | §1.3.12 |
| 我（DSH 会话） | ⑦⑧⑨⑫⑬ | 编译、检索、回答 | 全文 |

**三个口径，避免误读**：

1. **页码不是每本书都有**：4/5 本带锚点；气液搅拌釜γ-CT 无锚点（§1.2.3 P3）。行号取 20-md 绝对行，页码取原书页码，双轨（§1.3.3 §14）。
2. **本图是 §1.3.5 三 SOP 的纵向串联**，横向细节（每步怎么判对错）以出处小节为准，图里不重复。
3. **⑫~⑬ 是"下次提问"路径**，与是否新建向量库无关：先走 wiki 页（kb-search，§1.8.10），grep 原文只是兜底（§4.5）。

## 4.4 要不要先把五本书读一遍

**结论：不要通读。** 2,703,618 字符按 400–500 字/分钟约 90–113 小时（估算），读完也记不住；这个库的价值在「查得到 + 核得回」，不在背下来。

先花 90 分钟建「最小地图」：

| 顺序 | 读什么 | 时间 | 目的 |
|:--|:---|:--|:---|
| 1 | `30-wiki\index.md`＋9 分册 | 10 min | 570 条页名 + `description` 摘要，知道库能回答什么 |
| 2 | `30-wiki\sources\` 7 页 | 15 min | 每本书的重点节与覆盖范围 |
| 3 | `30-wiki\glossary.md` | 10 min | 33 行唯一译名（问问题时用对词） |
| 4 | `30-wiki\openq\` 3 页 | 15 min | 三处跨书口径冲突（comparisons 未单建，对比页在 pages） |
| 5 | `30-wiki\pages\` 挑 5 页 | 30 min | 建立手感（对比页如 `层流域搅拌器混合效率对比.md`） |
| 6 | `30-wiki\notes\`（0 页起步） | 2 min | 经验区：会话结晶与项目复盘，90 天不更新 lint 会提醒复检 |

判断标准：能说出「五本书各管什么、哪几处冲突、哪几个缺口」，就算有印象，够了。之后按需读：算题读《化工原理》第 2 章；选型读《搅拌与混合设备设计选用手册》§2（桨型）、§10（轴封）；承压设计按 GB/T 150.1~150.4。
## 4.5 Agent 怎么调工具

| 任务 | 工具 | 调用要点 |
|:---|:---|:---|
| 库内检索（首选） | `pwsh` 跑 `kb-search.ps1` | `-Q "<问题>" -Top 10 -Domain "<领域>"`；结果带 score/domain/`#L` 行 |
| 语义找段落 | `library_search` | `library="kb"`，`query` 用中文短语，`topK` 4–8 |
| 精确找词/行号 | `grep` | `path` 指到具体 md；返回行号 |
| 读上下文 | `read` | 带 `offset`/`limit`，按 grep 行号前后各读 30 行 |
| 找文件 | `glob` | `20-md\**\*.md` |
| 跑脚本 | `pwsh` | 用完整 `powershell -NoProfile -ExecutionPolicy Bypass -File ...` |
| 图谱 / 打包 | `graph.ps1` / `export.ps1` | 出 Mermaid 星图与 llms.txt（落 `40-scratch\`） |
| 出文档 | `office_docx` / `office_xlsx` | 只在要交付时用；解析 docx 不需要 Office |
| 多步任务 | `todo_write` | 先列步骤再动手 |

**失败退路（新机最容易卡在这）**

| 缺什么 | 表现 | 退路 |
|:---|:---|:---|
| 无 `library_search` / 库不存在 | 工具报错或 library not found | 直接 `grep 20-md`，问法带关键词 |
| 无 Python | `python` 不是内部或外部命令 | 仍可查询；加书前先装 Python 3.10+ |
| 无 MinerU | 入库报「未找到 mineru-kit」 | 只处理 md/txt/docx；PDF 留在 `00-inbox` 记待办 |
| 无 PowerShell | 无法执行 `.ps1` | 按 `rules.md` §9 手工回退，不跑脚本 |
| 盘符变 | `wiki-lint` 找不到 30-wiki | 改 §3.1.5 的 3 个默认值，或显式传参 |
| 索引文件缺 | 检索报库不存在 | 按 §3.1.4 恢复 |

**Agent 硬规则**

1. 不写 `10-source\`、`20-md\`；不删任何文件。
2. 新文件只进 `40-scratch\`。
3. 引用写 `《书名》§节号（#L行号）`；节号用书里真实编号，不猜。
4. 回答分「库中依据 / 我的判断」两段。
5. 不装软件、不联网、不上传资料。
6. 区分「索引里没有」与「书里没有」：前者要 grep 才能下结论。
7. `notes\` 经验页只在用户说「记下来」时建；会话收尾列 1–3 个候选页交用户挑，不自动写。

## 4.6 维护命令与判据

### 4.6.1 五条命令（在库根执行）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\catalog.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-index.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-lint.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\kb-search.ps1" -Build
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\check-links.ps1" -Md "D:\Shervon_KnowledgeBase\20-md\化工原理_王志魁_第5版_NA\化工原理_王志魁_第5版_NA.md"
# 其余四本：-Md 换成对应书的 md 路径，同样要求 unresolved=0
```

### 4.6.2 判据（2026-11-25 基线）

| 命令 | 合格输出 | 不合格怎么办 |
|:---|:---|:---|
| `catalog.ps1` | 5 本（待确认项见 `30-wiki\todo.md`） | 待确认是缺 year 类元数据，不是错误；补 frontmatter 后重跑 |
| `wiki-index.ps1` | 570 条（9 分册，单册 ≤300 行） | 页数对不上 = 有页没进索引，看输出 |
| `wiki-lint.ps1` | 错误 0 条 + 告警 0 条（description 覆盖 560/570） | 按报告逐条修死链/孤儿/无来源；notes 90 天告警是提醒复检，不计错 |
| `kb-search.ps1 -Build` | 索引 560 页（`search-index.json`） | 页数对不上 = 重跑 -Build |
| `check-links.ps1` | 337/426/561/137/397，`unresolved=0` | 跑 `-Fix` 后复查 |

### 4.6.3 检索索引：kb 库 120 页旧路径，建议清空重导入

现状：`kb` 库 120 页，其中 119 条文档路径仍指旧目录 `50-wiki\concepts\`（索引建于 v3.13 目录合并与 concepts→pages 改名之前），只覆盖 120/542 页。建议清空后按 `30-wiki\pages\` 重导入：

```
library_remove(library="kb", documentId="<逐个旧文档 id>")   # 先删旧的
library_add(path="D:\Shervon_KnowledgeBase\30-wiki\pages\<页名>.md", library="kb", name="<页名>")   # 再导新的（542 页）
```

验证：`library_search(library="kb", query="汽蚀余量 允许安装高度")` 应命中对应页；命中后再 grep 补行号。耗时与嵌入计费未实测。**是否执行待你定夺（§1.2.3 P5）。**（kb 索引重导后，日常检索主用 `kb-search.ps1`，kb 库只作语义兜底。）

## 4.7 已知坑

| 现象 | 原因 | 处理 |
|:---|:---|:---|
| kb 检索命中旧路径页 | 索引建于 v3.13 目录合并前（120 页旧 `50-wiki\concepts\`） | 按 §4.6.3 清空重导入 `30-wiki\pages` |
| 检索结果没有行号 | 索引块只存正文 | grep 定位后再引用 |
| 提示「禁止运行脚本」 | 执行策略 | 用带 `-ExecutionPolicy Bypass` 的完整命令 |
| 中文乱码 / ParserError | `.ps1` 缺 UTF-8 BOM | 存成「UTF-8 带 BOM」 |
| 入库报锁 | `40-scratch\.ingest.lock` 存在 | 确认没有别的入库会话后删掉 |
| 图链报错含 `%20` | v3.1 前的旧写法 | 跑 `check-links.ps1 -Fix` |
| Obsidian 图谱只有几个点 | `.obsidian\app.json` 排除了 `10-source`、`20-md` | 正常，图谱只显示 `30-wiki` |
| 页数与 index.md 对不上 | 加了页没重跑索引 | 跑 `wiki-index.ps1` |
| `notes\` 页 90 天没动 | 经验过期风险 | lint 第 11 项告警：复检结论或转正进 `pages\` |
| 工作区有未提交改动 | 3 个文件改动后未 commit（§1.3.11） | 按 §1.3.11 每书一个 commit 提交 |

## 4.8 安装包放哪（换机不卡）

建议在根目录建 `80-setup\`，放这些（版本对应 §3.1.2）：

| 文件 | 用途 |
|:---|:---|
| DSH 0.2.2.0 安装包（0.2.2-rc.3） | 必需 |
| Python 3.12 x64 安装包 | 加书必需（3.10+ 均可） |
| MinerU 4.1.7 安装包 / 离线 wheel | 加书必需 |
| `models\`（2.0 GB，可直接拷） | 加书必需，免重下 |
| Git 2.56.1、Obsidian 1.14.4、7-Zip | 可选 |

两个注意：

1. 你现在的 `rules.md` 禁止在根目录新增层级（新建物一律进 `40-scratch\`）；放 `80-setup\` 属于例外，需在 `rules.md` 补一行「`80-setup\` 仅存安装包，不入库、不进 20-md」，否则下次入库的 Agent 可能按规则拒绝。也可以改放 `40-scratch\setup\`（合规，但 `40-scratch` 定位是临时目录）。
2. 安装包体积大，别进 git：在 `.gitignore` 加 `80-setup/`（要改就说一声）。

