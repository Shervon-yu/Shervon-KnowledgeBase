## v3.1 — 2026-11-17

- §5 md 链接规则纠正：写真实文件名、含空格照写、不加 %20（check-links.ps1 按原文判 bad，含 % 一律不过）。

## v3.0 — 2026-11-16

- 新增 **50-wiki 层**（LLM Wiki）：`concepts` / `entities` / `sources` / `comparisons` / `howto` / `openq` 六个子目录 + `index.md` / `log.md` / `glossary.md`。raw（10-source + 20-md）→ wiki（50-wiki）→ schema（AGENTS.wiki.md + rules.md）三层，LLM 只写 50-wiki。
- 新增 `90-tool\AGENTS.wiki.md`：wiki 层编辑契约（写者边界、唯一译名、断言必须有来源、页面硬约束、冲突与换代、ingest/query/lint SOP、禁止项）。
- `rules.md` 追加 §12（50-wiki 层）/ §13（页面契约与 frontmatter）/ §14（书名+节号+行号引用格式）/ §15（ingest / query / lint SOP 与提交信息格式）。
- 版本库接入：`git init` + 本地 P0a 基线快照；`.gitignore` 排除 `10-source\`、`.stfolder\`、`30-index\catalog.md`、`30-index\todo.md`、`50-wiki\_lint.md`、`__pycache__\`、`40-new\_acl\`。
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
- 外部 agent 新建物统一放 `40-new\`（原 `40-newfolder`/`50-newfile` 作废）。
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
- `figures.py`：在 `图片\` 内改名/去重/补链，链接写 `图片/...`；报告路径修正为仓库根下 `40-new\`（原先算错会落回书目录）。
- 现有 2 本书已迁移：机械密封 396 张图、化工原理 340 张图，断链 0（化工另有 86 处 `page_*_chart_*` 图 MinerU 未导出，见 todo）。

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
