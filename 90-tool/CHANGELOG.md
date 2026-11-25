## v3.24 — 2026-11-25（未引用图归档改为「验收过即清」；prune 不再依赖 MinerU 产物）

- 起因：v3.23 删掉 MinerU 产物后，`40-scratch\_acl\`（419 张未引用图）也一并删除——用户判定图片都已在 20-md，其中 68 张属 HGT 20569-2013（该书无 md、无原件），用户明确会重新入库，故不再保留。
- 规则：`rules.md` §11 改为「prune 暂存 → 验收（check-links + 标题体检）全过后自动清空该书归档；验收未过则保留供回滚」。§16 补一句：产物只服务 `md-build.py write`（重建），`fig-names`/`prune`/`check-links`/`verify` 只读 md 与图夹，缺产物也能跑。
- 脚本：`ingest-build.ps1` 验收通过后新增归档清理段——删 `40-scratch\_acl\orphan-images\<入库夹名>\`，父目录空了再删 `orphan-images\` 与 `_acl\`。`md-build.py` 新增 `_resolve_md()`，`_prune()` 改用它——原先 `_prune()` 走 `_resolve()`，缺产物直接 `SystemExit("找不到解析产物目录")`，删掉 parse 后 prune 必然失败，属 v3.23 遗留缺陷，本次修掉。
- 验证：`混合原理与应用` 冒烟（`-SkipCreate`）全绿——锚点 459 / 公式 904 / 表格 525 / 图链 397 = 图 397 / frontmatter True / 未定名图 0 / 标题 OK；手工造 1 张假归档后重跑，验收通过即自动删除该书目录与空的 `_acl\`；`20-md` 零改动（`git status` 干净）。
- 已删：`40-scratch\_acl\`（419 张 / 22.2 MB）。`40-scratch` 余 `backup\` 2.7 MB、`desc\` 0.1 MB、`gen\` 0.2 MB、`legacy\` 0.6 MB、`_tmp\` 提交信息。

## v3.23 — 2026-11-25（取消 MinerU 产物永久保留：用完即删，溯源改为重跑解析）

- 起因：用户判定 7 本 md 定稿、不再重排重抽图，`40-scratch\parse\` 的 3 个 zip（270 MB / 1370 文件）只剩「误删后重建」这一点价值。核实后确认 md 自带 `<!-- page: N -->` 页码锚点，行号锚点由 `md-anchor.ps1` 从 md 标题算出（不读产物），故产物不再是锚点的唯一来源。
- 删除：`40-scratch\parse\` 整目录（270 MB，实测删前 1370 个文件）。
- 规则：`rules.md` §3 改为「MinerU 产物用完即删」，并写清删除前提——md 必须已承载正文、公式、pipe 表格、图题与图链，且带 `<!-- page: N -->` 页码锚点；图块 bbox 不入 md，随产物一并消失；需要溯源就从 `10-source\<书>.pdf` 重跑一次 `mineru-kit parse`（只耗本机算力，不耗 token）。§11 figures.py 说明、§16 命令前置条件与 v3.3 保留说明同步改。
- 脚本：`ingest.ps1` 删除「复制 zip 到 `40-scratch\parse\`」的代码块；`md-build.py` 模块注释的 zip 查找顺序加注「产物不再常驻，一般不存在」。
- `.gitignore`：删掉 `40-scratch/parse/` 忽略行；整份重写为干净 UTF-8（此前追加 `90-tool/search-index.json` 时把该文件写成了非 UTF-8，`read` 报 invalid UTF-8）。
- 溯源链路：`10-source\` 7 个 PDF 原件（284.4 MB）仍在，是重跑解析的入口。
- 验证：`ingest.ps1`、`ingest-build.ps1` 经 PowerShell Parser 校验 PARSE OK；`md-build.py` 经 `ast.parse` 通过。
- 未动：`40-scratch\_acl\`（419 张未引用图）。其中 68 张属 HGT 20569-2013，该书无 md、无原件、无产物，去留等用户决定。

## v3.22 — 2026-11-25（结构迁移：20-md 平铺 + 图夹后缀、30-wiki 分册收纳、40-scratch 归档）

- 起因：用户指出 `30-wiki` 根下 `index-*` / `figures-*` 会越积越多、`20-md` 每本书一个目录不便定位、`40-scratch` 散着 490+ 文件。
- `20-md`：每本书的 `<书>.md` 移到 `20-md\` 根；原 `<书>\图片\` 更名为 `<书>---图片\`；md 内图链前缀改为 `<书>---图片/`（7 本共 2095 条，`check-links` 全部 `unresolved=0`）。脚本同步：`md-build.py`（md/图目录与图链前缀、prune 正则、`_resolve` 只认 20-md 根的 md）、`ingest.ps1`（`$mdDir` 改指图夹、新增 `$imgSub`/`$linkPre`、md 落 20-md 根、分层只作用于图夹）、`ingest-build.ps1`、`fig-names.py`、`figures.py`（支持 `--book <书>---图片`，报告落 `40-scratch\gen\`）、`coverage.py`、`catalog.ps1`、`figure-index.py`。
- `30-wiki`：新增 `index\`（9 个分册）与 `figures\`（7 个图索引），总表 `index.md` 留根；`wiki-index.ps1` 写 `index\` 并在拆册时清旧册，`figure-index.py` 写 `figures\`，`wiki-lint.ps1` 漂移检查改递归。
- `40-scratch`：按用途分 `gen\`（生成物）、`desc\`（描述中间数据）、`backup\`（历史快照）、`legacy\`（一次性补丁脚本与 dump）、`parse\`（MinerU 原始 zip）、`_acl\`（未引用图）、`_tmp\`（临时）。体积大的 `parse\`（227 MB）与 `_acl\` 仍由 `.gitignore` 排除；其余子目录合计几 MB，继续入库以便回溯。
- 规则：`rules.md` §3 输出表改新布局、§4 阈值改按图夹计数、§12 机器区路径、§16 生成规范；**新增 §17 规模触发器**（P4 值守：≤2000 现行 / >2000 实测延迟、>5 秒迁 SQLite / >5000 重跑 golden set 再评估向量层）。
- 文档：`kb-blueprint.md` §4.1 目录表与现状数字（7 本、2095 图、595 文件）、§4.3 泳道产出、§4.5 工具表输出路径、§4.6 检查命令同步。
- 验证：`wiki-index` 570 页 / 4 领域 / 9 分册（最大 290 行）；lint 570 页 0 错 0 告警，`description` 560/570；`catalog` 7 本；`export` 570 页；`graph` 570 节点 1977 边。
- 未做：`kb` 索引库仍 120 页旧路径（重导需逐页调用库工具，本轮未执行）。

## v3.21 — 2026-11-25（§3.3 升级执行：两区 + schema + description + 自建检索 + 分册下沉 + 图谱出口）

- 起因：kb-blueprint.md §3.3「升级方案」定稿，用户批准执行（P0–P4）。
- 结构（P0）：新建 `30-wiki\notes\` 经验区（0 页起步）；删除空目录 `30-wiki\howto\`（howto 类型并入 notes）；`type` 枚举加 `note` 成七选一；frontmatter 新增 `description` 字段（≤200 字，notes 必填、pages 全区补满）。
- 规则（P0/P2）：新建 `90-tool\schema.md`（13 字段机器口径，lint 第 0 项改读它）；`rules.md` v3.19（五目录职责改两区、ingest 加删 API key/PII 一条）；`AGENTS.wiki.md` v1.4（Query 四步扩六步：会话开场读 lint 告警+log 尾 5 行、收尾三件事）；`prompt-dsh.md` v3.4（同步两钩子）。
- 检索（P1）：新建 `90-tool\scripts\kb-search.ps1`——扫 pages\+notes\ 建 BM25 倒排索引（中文二元组，k1=1.2 b=0.75，字段权重 title×3/aliases×2/description×2/正文×1），落 `90-tool\search-index.json`；查询带 score/domain/`#L` 命中行，参数 -Q/-Top/-Domain。实测 560 页索引、查询秒回。
- 索引（P1）：重写 `wiki-index.ps1`——领域树 index.md + 多级分册，单册 >300 行自动下沉；实测 570 页 4 领域 9 分册，最大 290 行。
- 描述（P1）：7 个并行子代理为 pages 560 页各写一句 description 并插入 frontmatter（question 行后），lint 校验 0 错，覆盖 560/570（sources/openq 不强制）。
- 出口（P3）：新建 `graph.ps1`（related/supersedes → Mermaid/DOT，实测 570 节点 1977 边）与 `export.ps1`（llms.txt 摘要包，570 页）。
- 坑：graph.ps1 双引号内三反引号被 PS 当转义、字符串永不闭合（ParserError 链）；改单引号解决。其余同 v3.20 BOM 教训。
- 文档：kb-blueprint.md §4 使用说明随升级同步（页数/分册/lint 项/工具表/触发器口径）；本条目与 VERSION 同步。
- 触发：用户 2026-11-24 定稿 §3.3、2026-11-25 批准执行；规则文件可改（用户已授权）。

## v3.20 — 2026-11-23（合订本标准：分标准 h1 注入 + 表格扁平化）

- 起因：HG/T 20592~20635-2009 为 19 个分标准合订本，分标准封面编号行多数被 MinerU 丢失，全书无 h1 分界 → 标题守卫把 141 个裸数字标题全部降级，TITLE-CHECK FAIL（假标题 141）。
- `md-build.py` 新函数 `_fix_std_covers()`：① 从全书目录页「标准名称对照表」（`| 71 | HG/T 20592—2009 | 钢制管法兰(PN 系列) |` 式 pipe 表）解析 19 个分标准号+名称，在每个分标准目次前注入 `# HG/T 2xxxx—2009 名称` h1，首个第N章前与末目次后首个第N章前注入 `# 编制说明`；② 分册内编号回跳的伪章行（`2 标记示例:`、`1 外观和尺寸检查。` 等 MinerU 误升的图例/列表行）降 `### `，防止一个坏行使整段降级；③ 表扁平化修复：build() 把表格存为整段多行字符串，逐元素正则不匹配导致前述函数早退——函数入口先按行展开（保留空行段落分隔）。
- BOM 教训：write/edit 工具落盘会剥掉 .ps1 的 UTF-8 BOM，PowerShell 5.1 按 GBK 读中文脚本直接解析崩溃（本次 ingest.ps1 首跑 exit 1）；已重补 BOM（EF BB BF），**改完 .ps1 必须重验 BOM**。
- 实测：注入 19+2 后 TITLE-CHECK OK、验收 8 行全过；残留 3 类 warn（第N章 目录6/md7、正文引用第 5、7、9、10、11、12、13、14 章无 h2、孤立 h4 32 处）不属三类硬伤，接受并汇报注明。
- 触发：HG/T 20592~20635 入库 TITLE-CHECK FAIL；用户授权规则文件可改。

## v3.19 — 2026-11-23（分册标准标题修补 + 行业标准 kind 映射）

- 起因：NB/T 47065.1~.5—2018《容器支座》五个分册标题带书名前缀（`容器支座 第1部分:鞍式支座`），`md-build.py` 原 h1 白名单不认 → 全分册 h1=0 → 守卫把 66 个裸数字标题全部降级，TITLE-CHECK FAIL（假标题 66）。
- `md-build.py` 四处补丁：① title_level h1 兼容 `^(?:容器支座\s*)?第\s*[一二三四五六七八九十百零\d]+\s*部分`（兼容「第 4 部分」带空格）；② 新增行业标准编制说明 h2（`NB/T|GB/T|GB|JB/T|JB|HG/T|HG|SH/T|DL/T|SY/T …《…》编制说明`）与 `^\d{1,2}\s+[A-Z]` 条目规则；③ 前置件补 `目\s*次`；④ 新函数 `_fix_part_heads()`：裸/粗体「附录X」行转 `## 附录X`、孤儿「（资料性附录）」行与分册内首个 `X.N` 内容行前注入附录标题（先预扫全分册防重复）、编制说明区（裸编号重启）条目降 `### ` 并按全书目录行补编制说明标题，注入点降序插入防漂移。守卫下标为 lines 数组下标而非文件行号（既有显示怪癖，非 bug）。
- `ingest.ps1` kind 映射补 `NB|HG`：NB/T、HG/T 行业标准自动得 kind=standard（原只认 标准|规范|GB|JB|ISO|DIN|ASTM）。
- 触发：本次 NB/T 47065.1~.5 入库时 TITLE-CHECK FAIL；用户授权规则文件可改（AGENTS.md 授权条款）。

## v3.18 — 2026-11-19（建页粒度补下限、附录按内容分流）

- 背景：用户问「压力容器标准 21 页为什么这么少」。审查 GB/T 150 分册发现 20 个 concept 页 frontmatter `lines:` 合并只覆盖源 md 2,912 / 17,877 行（≈16%），其中 150.4 十三章 1,434 行正文（`#L15617` 起）被压进 1 页（`sections: 第4部分 4`）。覆盖率门仍报 132/132——它只按 h3 统计「有无引用」，看不见「一页装多少」。
- `rules.md` §12.1 增**粒度下限**：一章内含多个独立判据的须各自成页；一类校核、一个公式体系算一个独立判据。把整章压成一页即违反本条。
- `rules.md` §12.1 **附录按内容分流**：载有公式/判据/参数取值的附录按断言簇正常建页（150.3 附录 A 非圆形截面容器、E 低温容器、F 防低温脆断校核、G 夹套容器；150.4 附录 A 锻焊、B 套合、C 多层包扎、E 低温脆断容器制造附加要求）；纯查表附录（许用应力表、高温性能表、牌号对照表）与文书表（提案表）不建页。原条文一律禁止「为附录建页」，与同条「能解决具体工程问题才建页」自相矛盾。
- `rules.md` 显式禁止条与「非知识条目」条同步删去「附录」二字，改由上面两条分流判定。
- `md` 源缺陷修复：`20-md\GBT 150.1～150.4-2024 压力容器…\…md` 的 `#L2518` `- 3 术语和定义`、`#L2522` `- 4 总体要求` 两条列表项伪标题改回 `## `（全库仅此两处，行数未变故 `#L` 引用无需重映射）。150.2 第 4 章 4.1~4.27 为无小节标题的平铺条款，`coverage.py` 只认 h3，故该章 27 条仍不在覆盖率统计内——指标盲区，留待后续决定是否扩到 level-2。
- 触发：2026-11-19 用户指出 21 页过少并要求「凭借规则来说哪里还需要添加」；17:15 批准两条改法并回「执行吧」。

## v3.17 — 2026-11-19（表格公式定界符：规则 + 20-md 修补）

- 背景：Obsidian 只把 `$...$` 当即时公式渲染；MinerU 转出的 pipe 表格常整列丢定界符，单元格显示成反斜杠源码。2026-11-19 实测 20-md 共 9986 行表格，1361 行含裸 LaTeX（3 本书：压力容器 502 行、搅拌手册 688 行、化工原理 171 行）。
- `20-md` 修补（提交 `b5c3097`）：纯公式单元格整体包 `$...$`；中文句内公式按数学片段分别包裹；顿号分隔的多公式逐个包裹；`\left|`/`\right|` → `\left\vert`/`\right\vert`，其余裸 `|` → `\vert`；跳过代码块、分隔行、已含 `$` 的单元格。补后复核：表格行中裸 LaTeX = 0。
- 残留：`化工原理` 7106/7107/11120 四处 `\begin{array}` 伪造合并单元格未动，需对 PDF 原表重建（或 HTML rowspan）。
- `rules.md`：头部 v3.16 → v3.17；§13 页面契约加「表格与公式」条；§16 硬性产出 7 条 → 8 条（新增第 8 条表格公式定界符与后处理说明）；完成判据 6 条 → 7 条（新增「表格内无未包裹 LaTeX」）。
- `AGENTS.wiki.md` v1.1 → v1.2：§3 加同名硬约束（行内 `$...$`、裸 `|` 用 `\vert`、禁 `\begin{array}` 伪造合并单元格）。
- 未脚本化：本次补丁为一次性人工后处理（脚本经 stdin 运行、未入库），重解析重建 md 后须重做；要长期生效需并进 `ingest-build.ps1` 后处理步骤（未做）。
- 触发：2026-11-19 16:23 用户问「MinerU 识别的表格里有公式，输入的管道表，在 obsidian 里就是一串乱码，是我的 obsidian 设置的错误……」；16:45 批准「现在修改吧」，16:45 批准「帮我把刚刚的改动写进规则里」。

## v3.16 — 2026-11-19（md 生成后加标题体检）

- 起因：MinerU 直出的 `paragraph_title` 不可信，而验收链里**从来没有标题项**。2026-11-19 修 GB/T 150 时统计出：全书 **0 个真标题**（章标题形如 `1 范围`、`第 1 部分:通用要求`，撞不上 `title_level()` 原白名单，全部被降成 `**…**` 粗体）、**18 个附录标题整行丢失**（正文「见附录 A」全悬空）。两次抢救都靠一次性脚本（`1ca9ab1`、`55d005f`），脚本未落盘，无法复现。
- `md-build.py`
  - `title_level()` 增两条：`^第\s*[一二三四五六七八九十百零\d]+\s*部分` → `#`（分册级 h1）；裸数字章 `^(\d{1,2})\s+[一-龥]` 且正文 ≤30 字 → `##`。
  - 增守卫 `_demote_bare_numbered()`（`_inject_missing_chapters()` 之后）：以 `# ` 分册切段，段内裸数字 h2 必须从 1 起、递增、不重号，否则整段降回 `**…**` 并打印 `[标题守卫]`。动机：`1 范围` 之外，正文段落也可能以「1 xxx」开头，靠书级校验兜住。
  - 增 `verify` 子命令（`python md-build.py verify <入库夹名|md 路径> [--strict]`）：`_toc_labels()` 抓目录条目（≥4 行连续 `- `、≥75% 以页码收尾才认），`_h2_labels()` 抓 `## ` 标题，按族（`第N章`/`附录X`/裸编号）做多重集比对。硬失败：`FAKE_BOLD_RE` 命中粗体假标题、某族目录有 md 一个都没有、正文引用附录而 md 无附录标题；软警告：可比族（数量差 ≤30%）内部缺项、孤立 h3/h4、章号跳号、正文引用第N章而 md 无对应 h2（`--strict` 升级为失败）。输出 `TITLE-CHECK OK|FAIL`，退出码 0/1。
  - 修 bug：`_h2_labels()` 的裸数字分支原用 `group(0)`，把 `\S` 吃进标签，导致压力容器 34 个裸编号章全被判缺失；改用捕获组取数字。
- `ingest-build.ps1` 五步 → 六步：插 `md-build.py verify` 为第 5 步，验收表七行 → 八行（新行「标题体检（假标题/漏章）」要求 `OK`），不通过进 `$bad` 后 `exit 2`；脚本加 `$env:PYTHONIOENCODING='utf-8'` 与控制台 UTF-8，否则 python 的中文体检报告在控制台乱码。
- `rules.md`：头部 v3.13 → v3.16（v3.14/v3.15 只记在本文件、没回写 rules.md 头，故跳号）；§16 内部五步 → 六步、六条硬性产出 → 七条（新增第 7 条「标题体检」及其三类硬伤）、完成判据第 1 条改「验收表八行全过（含标题体检）」。
- `prompt-dsh.md` 第 4 步链补 verify，验收口径由「必须看到两行」改为「三样：`验收通过` + `标题体检：OK` + `SELFCHECK unresolved=0`」。
- 实测：4 本书 `verify` 全 exit 0（压力容器 第N章0/附录X24/裸编号34、假标题0；化工原理 目录仅1条→跳过族；搅拌手册 目录20条 第N章17+附录X3 全匹配；气液搅拌釜 1 条章号跳号警告）。合成 md 单测：`**附录A**`+`**5 钢板**`+「见附录A」→ 2 条硬失败 + exit 1。
- 触发：2026-11-19 16:27 用户问「我忘了我有没有在入库规则里，添加一条命令就是，一本书已经把 pdf 转换成 md 了，再检查一下标题，因为 MinerU 直出的文档标题是乱的」（答：没有），16:38 批准「好的，写入吧」。

## v3.15 — 2026-11-19（concepts → pages，六目录收为五目录）

- `30-wiki\concepts\` 改名为 `30-wiki\pages\`（484 页整体 `git mv`，`[[wikilink]]` 按文件名解析，不断链）。理由：v3.14 把 `howto\` 重定义为「项目复盘」后，`concepts\` 事实上成了书内知识的唯一承载目录（488 页里 484 页），内含设备结构、测量方法、设计步骤、放大实例与 `*-总览` 导航页，按 §12.2 字面定义（「机理性知识」）已名不副实；改叫 `pages`（知识页）与内容一致。
- 六个类型值不动：`concept` / `entity` / `source` / `comparison` / `howto` / `openq`；空目录 `entities\` 并入 `pages\`，一致性规则改为「除 `concept`、`entity` 同放 `pages\` 外，其余必须与所在目录一致」。
- `rules.md` §12 六目录改五目录、§12.2 标题与职责、§12.1 总览页路径、§13 type 一致性、§15 ingest 查重路径、howto 条「书里的东西由 pages 承担」共 6 处。
- `AGENTS.wiki.md` v1.0 → v1.1：6 处 `concepts\` 改 `pages\`，§3 type 一致性同步，版本行注明理由。
- `wiki-index.ps1` 的 `$sections` 由「type→目录名」改为「目录→type 数组」并对 `entity` 同归 `pages`，`Render-Tables` 按目录分组，避免两个类型各出一节同名标题；重跑后 index 仍 488 页、4 领域分册，lint 0 条。
- `glossary.md` 路径列 12 处、`prompt-dsh.md` 第 56 行汇报格式同步为 `pages`。
- 未改：`kb-blueprint.md` 历史路径（开头已有路径注记）、`CHANGELOG` 旧条目、`wiki-lint.ps1`（不硬编码目录名，按 type 校验）。
- 触发：2026-11-19 16:05 用户问「现在叫 concepts 文件夹，是不是就有点不太合适了」，16:08 批准「行，你看着改一下吧」。

## v3.14 — 2026-11-19（howto = 项目复盘）

- `rules.md` 新增 **§12.2 六目录职责**：逐个写明 `concepts` / `entities` / `sources` / `comparisons` / `openq` / `howto` 各自承担什么，避免再次出现「四目录长期为空、不知该往里放什么」。
- `howto\` 定义为**项目复盘**：用户用库内知识解决了一个具体工程难题之后，把那次事件提炼成一页存入库中——问题、约束、用到库里哪些页、怎么选/怎么算、结论与事后验证、暴露的知识缺口；目的是留下「知识 → 用法」的证据链，不是复述知识。
- `AGENTS.wiki.md` §3 增 `howto` 页正文结构模板（六小节）；写明只记「这次怎么用知识」、不抄书，由用户发起、LLM 不擅自建，所用知识页必须链回，缺口同步进 `openq\`。
- 未新建 howto 页：规则生效，等第一次真实复盘按此落页。
- 触发：2026-11-19 15:32 用户指出 `comparisons`/`entities`/`howto`/`openq` 为空，并定义 howto 用途为「当我使用了库里的知识完成了一个工程难题的时候，想用把那次事件怎么完成的、用了哪些知识，提炼一下高价值信息存入库中」。

## v3.13 — 2026-11-19（目录合并：30-index + 50-wiki → 30-wiki）

- 原 `30-index`（机器生成物：catalog.md、manifest.csv、todo.md、issues.log、figures-*.md）与原 `50-wiki`（六子目录 + index + log + glossary + _lint）合并为单一 `30-wiki`；`30-index` 目录消失。
- 删除四个过期 `30-index\派生页-<书名>.md`：引用的是已删旧 119 页页名（如 `[[搅拌功率关联式对比]]`、`[[传热-总传热系数]]`），功能由 `30-wiki\sources\<书名>.md` 与 `30-wiki\index-<领域>.md` 覆盖。
- 路径改 30-wiki：`wiki-index.ps1`、`wiki-lint.ps1`（$WikiDir）、`catalog.ps1`、`ingest.ps1`（$Idx）、`coverage.py`、`refs-remap.py`、`figure-index.py`；文档 `AGENTS.wiki.md`、`prompt-dsh.md`、`prompt.md`、`README.md`；配置 `.gitignore`、`.obsidian\app.json`（移除 "30-index/" 忽略项）。
- `rules.md` §12 改写写者边界：分「机器区」（脚本写，人不手改）与「人写区」（六子目录 + glossary + log，只有 LLM 写）；同时修复 v3.10 写入时损坏的版本历史段（第 10 行字面 `n-`、第 27~33 行混入 PowerShell 片段）与本文件 v3.11 行的乱码前缀。
- 触发：2026-11-19 15:16 用户要求「把现在的 30-index、50wiki 改成 30-wiki，合并两个文件夹里的文件，同功能合并、冗余删除」，15:17 补充「配套修改 90-tool」。

## v3.12 — 2026-11-19

- 索引页豁免单页行数上限：index.md、index-<领域>.md 不再受 ≤300 行约束，lint 第 4 项（超长页）只查知识页。
- 触发：用户 2026-11-19 13:51 要求「各书的知识点 index 都不设置行数上限」；当时 index-搅拌与混合设备.md 已 261 行。

## v3.11 - 2026-11-19（单页上限 150 → 300 行）

- 
- rules.md §13 单页行数上限由 150 行改为 300 行；wiki-lint.ps1 默认 -MaxLines 同步改为 300，第 4 项标题随之为「超长页（>300 行）」。
- 同步 AGENTS.wiki.md §3 硬约束与 §7 lint 表、prompt-dsh.md 执行口径、VERSION 3.11。
- 触发：2026-11-19 12:58 本会话用户要求「把150行上限改成300行上限」。

## v3.10 — 2026-11-19（建页判据：以知识点为单位）

- 新增 `rules.md` §12.1 **建页判据**：页单位 = 一断言簇（同一结论的定义/公式判据/参数/边界/出处合为一页，不同结论分页）；建页前提是能解决具体工程问题；**禁止按书的目录或章节建页、禁止预设每书页数**；非知识条目（思考题/参考文献/符号说明/附录/索引）不建页，在该书 sources 页标注。
- `rules.md` §13 与 `AGENTS.wiki.md` §3 增 `question` 字段（一个疑问句，全库唯一），frontmatter 由九字段变十字段；`wiki-lint.ps1` 增第 10 项「question 不合规」（缺失/非疑问句/重复）。
- `rules.md` §15 ingest 八步改十步（新增「提炼断言簇、列 question 清单」与「建/改页」）；lint 八项改十项（补上原有的「别名遮蔽页名」与新的 question 项）。
- 覆盖率门 `coverage.py --strict` 保留为**底线**（每节至少被引用一次，防整节漏读），不再意味着一节一页；页数不设上限。
- `rules.md` §16 完成判据五条改六条（第 5 条为 question 非空/疑问句/唯一）。
- 触发：2026-11-19 用户定「知识为核心，一个知识点或能解决一个工程难题的几个知识点搭配算一页，一定不是按书的目录分哪几页，也不能按预设一本书多少页往里塞东西」，并要求四本书全部推倒重建、先做《搅拌与混合设备设计选用手册》。

## v3.8 — 2026-11-18（费用锁上限 5 → 20 元）

- `prompt-dsh.md` 【费用锁】由 5 元改 20 元（`-Limit 20`），并写明由来：峰价单价是谷价 2 倍，上一本谷价实耗 5.92 元（折峰价约 11.9 元），5 元峰价必然在 wiki 阶段被强杀。
- 触发：2026-11-18 15:07 本会话入库《GBT 150.1～150.4-2024 压力容器》时，用户在会话中明确要求「上限提到 20 元，一条龙做完，并且以后入库步骤的看门狗上限都提到 20 元」。
- 未改 `budget-watch.ps1`：脚本默认 `-Limit 5.0` 仍作为裸跑兜底，入库会话一律显式传 `-Limit 20`。

## v3.7 — 2026-11-18（图索引可机器计数）

- 新增 `90-tool\scripts\figure-index.py`：从 20-md 抽全部 `](图片/...)` 链接，输出 `30-index\figures-<入库夹名>.md`（行号/图名/所在节/是否整页/有无题注）。
- `rules.md` §16 判据 ④ 改为可执行口径：图索引表体行数 = 图片链接数；`整页图-pNN_n`、`未命名图N` 类无题图在 sources 页声明「无题非缺图」，缺图另见 `40-scratch\figures-report-*.json`。
- 动机：v3.6 的 ④（561 图逐张说明）无法机器校验，且 561 行超过单页 150 行上限，逐页拆分会把 wiki 变成图目录。

## v3.6 — 2026-11-18（覆盖率门：把「读没读完」变成退出码）

- 新增 `90-tool\scripts\coverage.py`：解析 20-md 的 `##`/`###` 标题成节区间，统计 wiki 页里 `#L` 引用落在哪些节，输出 `sections/covered/uncovered`；`--strict` 时 uncovered>0 退出码 1。
- `rules.md` §16 完成判据由 4 条升到 5 条：验收表 + `SELFCHECK=0`、`wiki-lint` 0 条、**覆盖率门 exit 0**、图索引覆盖（无题整页图逐张说明）、已 commit。
- `prompt-dsh.md` 入库收尾新增覆盖率门一步，明确「有 UNCOVERED 就继续读那一节、成页」。
- 动机：v3.3~v3.5 的判据止于「lint 0 + commit」，机器无法判断书的内容是否被覆盖，于是可以交 8 页 wiki 就宣布完成。覆盖率门把这件事变成可计算、可复跑、可卡人的退出码。

## v3.5 — 2026-11-18（标题层级、漏章补插、索引分册）

- `md-build.py`：
  - `title_level()` 重写：只有 `第X篇/第X章`→h2、`第X节`→h3、`\d+\.\d+\.\d+`→h4、`\d+\.\d+`→h3、`附录/参考文献/前言/序/目录/编后记/致谢/内容提要/符号表`→h2 才成标题，**其余一律降为加粗正文行**（不改行数）。此前未匹配标题一律当 h2，本书实测 h2=624（其中 235 条「一、二、」、287 条「1.」），标题树完全失真；修复后 h2=43、h3=78、降级 584 行。
  - 新增 `_cn2int()` 与 `_inject_missing_chapters()`：从目录行解析 17 章顺序，按「第 k 个 `### 第一节` ↔ 目录第 k 章」定位，MinerU 漏识的章标题（本书第十一、十二、十七章）倒序补插 `## 第X章 标题`。
- `wiki-index.ps1`：页面数使单文件超过 120 行时，自动按 `domain` 拆分为 `index.md`（领域目录）+ `index-<domain>.md`（分册）；未超限时仍写单一 `index.md` 并清理旧分册。此前只打印警告不拆。
- `wiki-lint.ps1`：①`index*.md` 不再计入页面（否则分册文件被当孤儿页/无来源页）；②index 漂移检查改为合并所有 `index*.md` 判定。
- 本书据此重建：行数 20,166、锚点 538、`$$` 444、pipe 表 4944、图 561、`SELFCHECK unresolved=0`、七行验收全过；wiki 行号引用按 `40-scratch\line-map-20160-to-20166.json`（分段 +2/+4/+6）平移并抽样比对原文。
- 教训：`write` 工具写 `.ps1` 不带 BOM，PowerShell 5.1 按 ANSI 读会因中文变乱码而报语法错；改完必须补 `EF BB BF`。

## v3.4 — 2026-11-17（页码锚点改用物理页序）

- `md-build.py`：页码锚点由「优先页脚印刷页码、缺失才退 `page_idx+1`」改为**一律 `page_idx+1`**。原因：前后置页（封面/版权/目录/附录）使印刷页码与物理页序错位，同一本书混用两套编号时，锚点数会「刚好等于 PDF 页数」但页号缺一半（本书实测 537 个锚点、缺 50 个页号、另有 49 个锚点号 >538），属假通过。
- `rules.md` §16 第 1 条与 §14 行号漂移说明同步改写：锚点=物理页序、1..N 连续无缺；行号平移只来自首页 frontmatter 分隔行（本次实测 +2），按锚点比对即可校正。
- 本书据此 `-Force` 重建：锚点 538/538 连续、行数 20,160、`SELFCHECK refs=561 ok=561 unresolved=0`，wiki 全部 `#L` 引用按 +2 平移并逐条比对原文校验。
- 教训：验收只看「锚点数=PDF 页数」不够，必须同时要求页号 1..N 连续；锚点号是否单调递增可比数少一个更早暴露错位。

## v3.3 — 2026-11-17（一条龙收尾）

- `ingest.ps1`：①`Invoke-Mineru` 返回 zip 路径；②解析产物 zip 复制到 `40-scratch\parse\<入库夹名>\` 永久保留（以前解析完即删，导致无法重建页码锚点）；③收尾在 md 锚点 <10 时自动调用 `ingest-build.ps1 -Book "<入库夹名>"`，一条命令跑到「七行验收表 + SELFCHECK」。
- `check-links.ps1`：修 RENAME 分支丢目录前缀 bug（`Split-Path -Leaf` → 保留 `图片/` 前缀），此前会生成 `](图14.12…jpg)` 死链并把 `unresolved` 卡在 1。
- `rules.md` v3.3：§2 改名后必须把 `missing` 改成剩余缺项并清旧 issues；§10 汇报模板加 `wiki`/`验收` 两行、收尾口径禁止「只列未完成」；§16 增「完成判据」四项；版本头加 v3.3 变更段。
- `prompt-dsh.md` 重写：步骤 4 一条命令含 build+验收；新增 6~10 步 wiki 入库、`wiki-lint` 0 条、commit、汇报加三行；「规则文件」由禁改改为「可改但必须汇报并同步 VERSION/CHANGELOG」。
- 教训：`Get-Content` 默认编码会把无 BOM 的 UTF-8 中文读成乱码，读 md/rules/CHANGELOG 一律显式 `-Encoding UTF8`。
## v3.2 — 2026-11-17

- 新增四个脚本（`90-tool\scripts\`）：`md-build.py`（middle_json → 20-md：页码锚点 / `$$` 公式 / pipe 表 / 图链图题 / 保留 frontmatter / 目录页转列表 / 未引用图归档）、`fig-names.py`（挂同页图题 + 二维码判定）、`refs-remap.py`（重建后 `#L` 重算，apply 前强制工作区干净）、`ingest-build.ps1`（一条命令五步 + 七行验收，不达标 exit 2）。
- `rules.md` 新增 §16（生成规范六条 + 守卫 + 重解析顺序）；`AGENTS.wiki.md` §5 由「Ingest 八步」改为「Ingest 六步（一次到位）」；`prompt.md` 第 6 步前插入「生成与验收（v3.2 起，优先于手改）」；`kb-blueprint.md` §3.5 与 §2.7 注明 ②–⑤ 已收拢成一条命令。
- 三条教训：①`.ps1` 必须 UTF-8 BOM，否则 PowerShell 5.1 按 ANSI 读中文报语法错；②图片名含空格时计数正则要用 `图片/([^)]+?\.jpg)`，`[^)]+` 会截断；③重建 md 会打回人工图名，故 `ingest-build.ps1` 对已生成版默认跳过重建，需 `-Force`。

## v3.1 — 2026-11-17

- §5 md 链接规则纠正：写真实文件名、含空格照写、不加 %20（check-links.ps1 按原文判 bad，含 % 一律不过）。

## v3.0 — 2026-11-16

- 新增 **50-wiki 层**（LLM Wiki）：`concepts` / `entities` / `sources` / `comparisons` / `howto` / `openq` 六个子目录 + `index.md` / `log.md` / `glossary.md`。raw（10-source + 20-md）→ wiki（50-wiki）→ schema（AGENTS.wiki.md + rules.md）三层，LLM 只写 50-wiki。
- 新增 `90-tool\AGENTS.wiki.md`：wiki 层编辑契约（写者边界、唯一译名、断言必须有来源、页面硬约束、冲突与换代、ingest/query/lint SOP、禁止项）。
- `rules.md` 追加 §12（50-wiki 层）/ §13（页面契约与 frontmatter）/ §14（书名+节号+行号引用格式）/ §15（ingest / query / lint SOP 与提交信息格式）。
- 版本库接入：`git init` + 本地 P0a 基线快照；`.gitignore` 排除 `10-source\`、`.stfolder\`、`30-index\catalog.md`、`30-index\todo.md`、`50-wiki\_lint.md`、`__pycache__\`、`40-scratch\_acl\`。
- 解析层（10-source / 20-md / 30-index）规则不变，v3.0 只加不改。

## v2.3 — 2026-11-12

- 图名规则补全：禁用字符加 [ ] { } # %，命名前剥图题引用号 [31]（igures.py 已改）；含空格的 md 链接建议写 %20。
- 夹名以版权页校准：解析完用 CIP 核对书名/版次/年份，不符改名（夹、md、10-source、src），再重跑 catalog；README 同步改写为 v2.3 现状。
- check-links.ps1 正式列入流程：ingest 收尾自动跑（-Fix 修坏字符名与死链），§10 汇报加「图链 / 缺图」两项。
- 规则澄清：§4.4/§4.5 外部 agent 只动自己的夹；§7 增「图题存但未导出图」登记；§8 例外与 §2 统一；§9 手工回退留 _done 标记；ingest 增加 .ingest.lock 并发锁，frontmatter ocr 由 unknown 改为 auto。

## v2.2 — 2026-11-12

- `00-inbox` 顶层只有**散文件**时不报错、不停下询问：自动建入库夹 `书名_作者_NA_NA` 并把顶层散文件全部移入，继续入库；只有「2 个以上文件夹」和「空」两种情况才停。`rules.md` 第 1、2 节与 `prompt-dsh.md`、`prompt.md` 同步。
- 修正 `prompt-dsh.md` 第 4 步：`figures.py` 与 `catalog.ps1` 已由 `ingest.ps1` 内部执行（且 MinerU 暂存目录入库后即删），不再要求手工重复跑。

## v2.0 — 2026-11-10

- 目录改为**扁平入库夹**：默认 `20-md\<入库夹>\<入库夹>.md`，`10-source` 同构镜像。
- 新增第 4 节分层规则：单夹 ≤40；N<20 扁平、20≤N≤40 可分组（同主题 ≥3 个）、N>40 必须分组（40^(x-1)<N≤40^x，允许分类夹与入库夹混层）。
- `taxonomy.md` 改为**建议清单**，不再是白名单；`01-books`/`02-standards` 类型层取消。
- 外部 agent 新建物统一放 `40-scratch\`（原 `40-scratchfolder`/`50-newfile` 作废）。
- 图名规则更新：禁用括号，多子图用 `_a`/`_b`（括号会截断 markdown 链接）。
- `ingest.ps1` v2.0：`-Layer` 参数、按 N 自动选层、文件名括号归一、图 byte 级去重、入库后自动跑 `figures.py`。
- `catalog.ps1`：书目按层级分组；`todo.md` 第 4 节改为「层级体检」（N、所需层数、超限夹）。
- 新增 `scripts\figures.py`：按 MinerU `middle_json.json` 的 bbox 配回图题、哈希去重、改名并回链，幂等。

# 变更记录

## v2.1 — 2026-11-10

- 入库夹内部结构定死：**插图全部进 `图片\` 子目录**，正文与其他文档放夹根；md 链接写 `图片/...`。
- `00-inbox` 改为传送带：**入库成功后清空**该文件夹（原件进 `10-source`）；解析失败/手工回退时保留。
- 新增 4.4「重排时机」：**每新增一个入库夹就重排一次**——按现有分类夹内实际入库夹判断归属，合适就进，必要时合并新建或改名分类夹，重排后必须重跑 `catalog.ps1`。
- `ingest.ps1`：图目录改为 `<入库夹>\图片`，md 引用加 `图片/` 前缀。
- `figures.py`：在 `图片\` 内改名/去重/补链，链接写 `图片/...`；报告路径修正为仓库根下 `40-scratch\`（原先算错会落回书目录）。
- 现有 2 本书已迁移：试点书 396 张图、化工原理 340 张图，断链 0（化工另有 86 处 `page_*_chart_*` 图 MinerU 未导出，见 todo）。

## v1.2 — 2026-11-09

- **接入 MinerU 4.1.7**（`C:\Users\shervon\.local\mineru`，模型在 `C:\Users\shervon\.mineru\models`，默认档 `standard`）。PDF/图片由脚本自动解析，不再记 pending。
- 解析改用 `--format zip`：zip 内含 `markdown.md` + `middle_json.json` + `images/`。实测纯文字页约 4 秒/页，图纸类约 26 秒/页。
- **图示自动导出并改名**：读 `middle_json` 的 `image_caption` 取图题，按 `图1.1 问题描述.jpg` 命名（图号 `图 3-1`/`图3．1` 归一为 `图3.1`），无图题记 `未命名图N.jpg`；md 内链接同步改成相对文件名。
- `ingest.ps1` 结尾自动调 `catalog.ps1` 重建索引，并打印汇总行。
- 修：PowerShell 把 MinerU 的 stderr 当错误导致误判解析失败 → 改看 zip 产物判断成败。
- 三份文档补执行方式 `powershell -NoProfile -ExecutionPolicy Bypass -File ...`（本机执行策略禁止直接跑 .ps1）。

## v1.1 — 2026-11-09

- **一个会话 = 一本书 = `00-inbox` 下一个文件夹**；一个文件夹内多文件按名排序合并成一份正文。散文件只告警，不处理。
- 新增**图示规则**：`图X.X 说明` 作为图片文件名，图片与 md 同目录，md 内链接改相对路径；无图号记 `未命名图N`；同号重复加 `_2`。
- **删除 `90-tool\run-ingest.bat`**：上传由 DSH 会话或外部免费 agent 执行，人不再双击。
- 提示词拆两份：`prompt-dsh.md`（DSH 会话用）、`prompt.md`（外部免费 agent 用，含手工回退）。
- `.docx/.pptx/.xlsx` 改为直接读 OOXML 抽文本，不再依赖 Office COM（该路线在本机挂死，已废弃）。
- 质检阈值：有效字符 < 200 隔离；200–2000 警告；U+FFFD > 2% 隔离。
- 正文改为 `20-md\<类>\<学科>\<书名>\<书名>.md`，与图片同目录。

## v1.0 — 2026-11-09

- 初始骨架：`00-inbox` / `10-source` / `20-md` / `30-index` / `90-tool`。
- 两个脚本：`ingest.ps1`（-Preview 预览）、`catalog.ps1`（重建三件索引）。
- 分类表 `taxonomy.md`（6 类 × 8 学科），规则 `rules.md`，说明 `README.md`。
