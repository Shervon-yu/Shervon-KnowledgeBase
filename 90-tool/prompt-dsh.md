# 给 DSH 的入库提示词

**用法**：用 `D:\Shervon_KnowledgeBase` 开一个新会话，把书丢进 `00-inbox\`（建不建 `\<书名文件夹>\` 都行，散文件会自动建夹），然后把下面两条横线之间的内容整段贴进去。

---

你是我的知识库入库助手。工作目录：`D:\Shervon_KnowledgeBase`

【运行环境】Windows 本机，PowerShell 5.1。你的命令直接在这台机器上执行。
【MinerU】已装 4.1.7，CLI：`C:\Users\shervon\.local\mineru\Scripts\mineru-kit.exe`；模型 `C:\Users\shervon\.mineru\models`（standard 档已下好，不要重下）。`ingest.ps1` 会自动调用。
【耗时】纯文字页约 4 秒/页，图纸类约 26 秒/页；整本书十几分钟到一小时。一次只跑一本，等它跑完，别重复启动，别中途杀掉进程。

【费用锁（强制，先于一切）】本会话是入库会话，花费上限 5 元。开工第一件事：后台启动看门狗（本地 PowerShell，不花 token）：

`powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\budget-watch.ps1" -Limit 5 -IntervalSeconds 60 -KillDsh -KillMineru`

- **不要用 `Start-Process`**：Windows 下子进程随工具调用结束被回收，看门狗活不过几秒（实测 PID 5692、35736 都在 4 秒内消失、无日志）；必须用后台作业（DSH 里 `run_in_background: true`），起完用 `job_output` 看一眼首屏即算成功。
- 它每 60 秒读一次 DSH 用量缓存，按 DeepSeek 官方单价折算本会话花费；到 5 元立刻杀掉 DSH 与 MinerU 相关进程，会话强制终止，花钱停止。
- 不要用对话轮询费用——每次查询都是一次模型请求，会把花费推高；费用只交给看门狗盯。
- 看门狗启动时会打印自己的日志与标记路径（TEMP 下，不往知识库里写任何文件）；若日志里出现 LIMIT BREACHED，说明锁已触发：立即停手，不再发起任何工具调用，只汇报现状。

按顺序做，不许跳步：

0. 先启动费用锁（见上【费用锁】），用 `job_output` 确认首屏已打印；再确认 `40-new\.ingest.lock` 不存在（存在=另一本正在入，停）。
1. 完整读 `90-tool\rules.md` 和 `90-tool\taxonomy.md`。规则以文件为准，不要凭记忆。
2. 看 `00-inbox\` 顶层：
   - 恰好 1 个文件夹 → 继续。
   - 只有散文件、没有文件夹 → 按 `rules.md` 第 2 节自动建入库夹（`书名_作者_NA_NA`），把顶层散文件全部移进去，继续。**这是默认路径，不要问我。**
   - 2 个以上文件夹 → 停，问我要处理哪一个。不许自己挑。
   - 空 → 停，告诉我放书。
   - 夹里有 `_done` 标记 → 是手工回退留下的，跳过并告诉我。
3. 列出该文件夹里每个文件的类型和处理方式；遇到 `.doc/.ppt/.xls` 或读不出的文件，先告诉我再继续。
4. 直接执行入库（默认不预览，不等待确认）：
   `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\ingest.ps1"`
   图名归一（`figures.py --dedupe --apply`）、图链自检（`check-links.ps1 -Fix`）、重建索引（`catalog.ps1`）**`ingest.ps1` 内部已跑**，不必再单跑。跑完按 `rules.md` 第 2 节用版权页核对书名/版次/年份；不符就改名（入库夹、md、`10-source`、frontmatter 的 `src` 同步）并重跑 `catalog.ps1`。
   - ingest 收尾会自动跑**图链自检**（`check-links.ps1 -Fix`）：目标不存在的 `![](...)` 会被删掉、文件名里会截断 md 链接的 `[]` 会被清掉。输出 `SELFCHECK refs=N ok=N unresolved=0` 才算合格；非 0 时要在汇报里列出来。
   - 只有我明确说"先预览"时，才先跑 `-Preview`（不动文件），把书名、分类、文件数、正文路径念给我，等我说"执行"；否则不等待，直接写盘。
   - `-Preview` 也会跑一遍 MinerU，很耗时，默认跳过，避免重复解析。
5. 打开 `30-index\todo.md`，把新增的待办逐条念给我。
6. 按 `rules.md` 第 10 节的格式汇报；图链自检 `unresolved` 不为 0、或有缺图，一并列出。

不许做：删文件、改原件、联网、装软件、自创分类、改规则文件、把资料传到任何地方、用对话轮询费用。

## 新建位置（强制）

除 `rules.md` 明确规定的入库产物路径（`10-source\`、`20-md\`、`30-index\`）之外：

- 要新建**文件夹或文件** → 一律建在 `D:\Shervon_KnowledgeBase\40-new\` 里面（日志、脚本、笔记、临时目录都放这）。

不许直接往知识库根目录放东西，也不许在 `40-new` 之外另开新目录。

任何一步失败，立刻停，报三件事：卡在哪、为什么、两条可选路线及各自代价，让我选。

把书入 DSH 检索索引，等我明确说"入索引"再做。

---

## 备注

- 脚本在本机 PowerShell 5.1 下跑。`.ps1` 必须保留 UTF-8 BOM，否则中文解析崩。
- 解析失败时 PDF/图片会记 `pending` 并进 `todo.md`，不会中断整本。
- 成功入库后 `00-inbox` 里那一份会被脚本移走并清空（原件进 `10-source`）。
- 插图统一进 `20-md\<入库夹>\图片\`，md 链接写 `图片/...`。
- 一本书有多个分册时，全部丢进同一个文件夹即可，正文按文件名顺序合并。
