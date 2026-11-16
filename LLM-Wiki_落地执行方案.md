# LLM Wiki 落地执行方案（P0–P4）

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
- 决定：P1 机械密封的引用一律用 **行号**（`#L123-456`）；锚点等"重解析该 PDF"时由 `md-anchor.ps1` 自动补。不因此卡住试点。
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
| 9 | concepts/流体流动-柏努利方程 | concept | 第 1 章 |
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
