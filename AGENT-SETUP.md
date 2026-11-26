# 部署提示词：把 Shervon 知识库装到本机

> **给人类**：把本文件从标题到结尾完整交给你的 agent（DeepSeek Harness 最省事；Claude Code / Codex / Cursor 也能完成大部分步骤）。它读完会自己下载、装工具、配 Obsidian、验收，最后按 §11 交报告。
>
> **给 agent**：你是本机部署执行者。先读完 §0–§12 再动手；每一步都用真实命令输出核对，禁止假设成功、禁止编造结果。卡住按 §12 处理。

## 0. 目标与完成判据

把公开仓库 <https://github.com/Shervon-yu/Shervon-KnowledgeBase> 的内容部署到本机 **`D:\Shervon_KnowledgeBase`**，做到：

1. Obsidian 能打开该目录，在 `30-wiki` 中查概念、读页面；
2. `kb-search.ps1` 能检索，命中结果带 `#L行号`；
3. 回答专业问题时，格式为《书名》§节号（`#L行号`），且行号能在 `20-md` 的对应 md 中核对到原文；
4. 仅 DSH 用户：`kb` 语义库可检索（`library_search`）；
5. `wiki-lint.ps1` 跑完，现有页面无新增错误；
6. 根目录存在空目录 `00-inbox`、`10-source`（部署时创建）。

**全部满足才算完成。** 缺任何一项，在报告里写「未完成」并说明原因，不许用「基本完成」糊过去。

不要求：git、GitHub 账号、多机同步、作者的 MCP / 私人软件 / 密钥。

## 1. 这个库是什么（先花 5 分钟认识）

三层结构 + 工具层：

| 路径 | 内容 | 部署后有吗 |
|---|---|---|
| `00-inbox\` | 新书/新材料暂存区，入库前把 PDF 放这里；部署后为空目录 | **有**（空目录，部署时创建） |
| `10-source\` | 原件层（作者本机为 7 本书的 PDF/书子目录：GB/T 150、HG/T 20592、NB/T 47065、化工原理、搅拌与混合设备、γ-CT、混合原理与应用）；部署只建空根目录，PDF 与书子目录都不提供 | **有**（仅空根目录，部署时创建） |
| `20-md\` | 7 本书的 MinerU 解析全文，扁平存放：7 个 `<书名>.md` + 7 个 `<书名>---图片\` + `_quarantine\`，约 137 MB | 有 |
| `30-wiki\` | 560 个概念页（`pages\`）+ `sources\`、`openq\`、`figures\`、`notes\` 五目录；4 个领域；9 个分册索引；`manifest.csv` | 有 |
| `40-scratch\` | 草稿、生成物、临时文件 | 有（少量） |
| `90-tool\` | 规则、schema、taxonomy、18 个脚本、`VERSION`（3.24） | 有（`search-index.json` 除外） |
| `50-handoff\` | 本库的交接包：DSH 全局规则、`kb` 语义库快照、Obsidian 安装包说明 | 有（339 MB 安装包除外） |
| `.obsidian\` | 作者本机的 Obsidian 配置/插件 | **没有**（`.gitignore`） |
| `.git\` | 版本库 | **没有**（下载的 ZIP 本来就不含） |

`30-wiki\pages` 的 560 页按领域分布：搅拌与混合设备 287、化工原理 153、气液搅拌釜γ-CT 68、压力容器标准 62（`index.md` 的统计含 sources/openq，总数 570）。

**先读这五份，再动手：**

- `README.md`：项目速览、目录表、红线。注意其中「542 页 / kb 只有 120 页 / 20-md 嵌套目录 / git 同步」是旧记录，以本提示词和实测为准。
- `90-tool\rules.md`（v3.18）：分层、命名、图示、引用、质检、禁止项，17 节，是硬约束。
- `90-tool\AGENTS.wiki.md`（v1.2）：写者边界、唯一译名、断言必须有来源、页面硬约束、Ingest 六步、Query 六步、Lint 项。
- `90-tool\schema.md` + `taxonomy.md`：页面 frontmatter 字段与领域/类型标签。
- `30-wiki\glossary.md`：术语与唯一译名表；建页、翻译、回答前先查，避免同物异名。

## 2. 硬性前置检查（不满足先停下问）

| 项 | 要求 | 怎么查 |
|---|---|---|
| 操作系统 | Windows 10/11 x64（`.ps1` 依赖 Windows PowerShell；其他系统只能读 `20-md`/`30-wiki`，`.ps1` 不能直接跑，Python 脚本默认路径也是 Windows） | `[Environment]::OSVersion.VersionString` |
| PowerShell | ≥ 5.1 | `$PSVersionTable.PSVersion` |
| Python | ≥ 3.10，脚本只用标准库 | `python --version`；失败用 `py -3 --version` |
| 磁盘 | D: 至少 2 GB 空闲 | `Get-PSDrive D` |
| 安装路径 | **必须是 `D:\Shervon_KnowledgeBase`** | `Test-Path` |

路径为什么不能换：`kb-search.ps1`、`wiki-lint.ps1`、`wiki-index.ps1`、`export.ps1`、`graph.ps1`、`md-anchor.ps1`、`figure-index.py` 的默认值都写死这个路径；换路径要逐个改参数，容易漏。若用户坚持换，先说明代价，再统一改默认值并在报告里列出改了哪些文件。

若 `D:\Shervon_KnowledgeBase` 已存在：**停下问用户**，不要合并、不要覆盖。

## 3. 获取文件（不碰 git）

公开仓库地址：<https://github.com/Shervon-yu/Shervon-KnowledgeBase>（分支 `main`）。

方式 A（推荐，命令行）：

```powershell
$zip = "$env:TEMP\Shervon-KnowledgeBase-main.zip"
$out = "$env:TEMP\kb-extract"
curl.exe -L --fail --retry 3 -o $zip "https://github.com/Shervon-yu/Shervon-KnowledgeBase/archive/refs/heads/main.zip"
Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -LiteralPath $zip -DestinationPath $out -Force
Move-Item "$out\Shervon-KnowledgeBase-main" "D:\Shervon_KnowledgeBase"
```

方式 B：浏览器打开仓库页 → Code → Download ZIP → 解压 → 把解压出的 `Shervon-KnowledgeBase-main` 改名为 `D:\Shervon_KnowledgeBase`。

**不要**：`git clone`、`git init`、注册 GitHub、fork、提 PR；都不需要。下载的 ZIP 里没有 `.git`，正常。

无论用 A 还是 B，落到 `D:\Shervon_KnowledgeBase` 后先补建空目录、再核对（本版应为下列数字；若你拿到的是更新版本，记录实际值并继续，不要伪造）：

```powershell
$root = "D:\Shervon_KnowledgeBase"

# ZIP 不含空目录；部署时补建，后续入库要用
New-Item -ItemType Directory -Force "$root\00-inbox", "$root\10-source" | Out-Null

(Get-ChildItem "$root\30-wiki\pages" -Filter *.md).Count          # 560
(Get-ChildItem "$root\20-md" -Filter *.md).Count                 # 7
(Get-ChildItem "$root\20-md" -Directory -Filter "*---图片").Count # 7
(Get-Content "$root\90-tool\VERSION" -Raw).Trim()                # 3.24
Test-Path "$root\50-handoff\index\dsh_library.kb.json"           # True
Test-Path "$root\00-inbox"                                       # True
Test-Path "$root\10-source"                                      # True
```

任何一项不符：先报告实际值，不要删文件「凑数」。

## 4. 工具清单（装哪些、为什么）

| 工具 | 作者实测版本 | 干什么 | 是否必须 |
|---|---|---|---|
| Obsidian | 1.15.1（安装包在本机 `50-handoff\installer\`；GitHub 包里没有，339 MB 超单文件限制） | 阅读/编辑 `30-wiki`；`#L` 行号跳转靠可选插件 | **必须**（读者） |
| PowerShell | 5.1（Windows 自带） | 跑 `.ps1` 检索/质检/索引 | **必须**（跑脚本） |
| Python | 3.14.6（只用标准库） | `coverage.py`、`figure-index.py`、`md-build.py` 等 | 跑覆盖率/图索引/入库时必需；只读+检索可不装 |
| DeepSeek Harness（DSH） | 作者在用，最新版即可 | 注入全局规则、`library_search` 语义检索、技能/会话 | 推荐，非必须 |
| MinerU | 4.1.7 | 仅新增书籍时解析 PDF | 仅入库需要 |
| Everything / VS Code | 任意 | 可选全文搜索/编辑 | 可选 |

安装方式由你决定（官网、winget、已有安装都可），但**不要**：

- 装到需要管理员权限又改不动脚本的路径；
- 用「绿色版/便携版」替代 Obsidian 后又抱怨 `#L` 跳转不工作；
- 顺手装作者的 MCP（`rea`、`windows-mcp`）、DSH 技能、密钥——都不需要。

版本不必完全一致；装更高版本可以，但必须跑 §7 验收。

## 5. 装 DSH 层资产（仅 DSH 用户；非 DSH 跳到 5.3）

### 5.1 全局规则

把两份文件放到 DSH 的全局指令位置：

```powershell
$dshRule = "$env:USERPROFILE\.dsh\AGENTS.md"
$docRule = "$env:USERPROFILE\.agents\AGENTS.md"
New-Item -ItemType Directory -Force "$env:USERPROFILE\.dsh", "$env:USERPROFILE\.agents" | Out-Null

if (Test-Path $dshRule) {
  Copy-Item $dshRule "$dshRule.bak"
  Write-Host "已存在 $dshRule（已备份），请按 README 追加合并，不要覆盖"
} else {
  Copy-Item "D:\Shervon_KnowledgeBase\50-handoff\rules\dsh-AGENTS.md" $dshRule
}

if (Test-Path $docRule) {
  Copy-Item $docRule "$docRule.bak"
  Write-Host "已存在 $docRule（已备份），请按 README 追加合并，不要覆盖"
} else {
  Copy-Item "D:\Shervon_KnowledgeBase\50-handoff\rules\agents-AGENTS.md" $docRule
}
```

- 目标已存在 → 先备份，再**追加合并**，不要直接覆盖（细节见 `50-handoff\rules\README.md`）。
- 这两份是**全局规则**，会影响该用户所有项目；装完告诉用户一声。
- 重启 DSH 会话生效。

### 5.2 `kb` 语义库快照

快照：`50-handoff\index\dsh_library.kb.json`（560 文档 / 1896 块 / 256 维，10.6 MB，导出 2026-11-26）。

恢复会**整体替换** DSH 的 `dsh_library.json`：

1. 退出 DSH（确认没有后台进程）。
2. 备份 `%USERPROFILE%\.dsh\storages\dsh_library.json`（不存在就跳过）：
   ```powershell
   Copy-Item "$env:USERPROFILE\.dsh\storages\dsh_library.json" "$env:USERPROFILE\.dsh\storages\dsh_library.json.bak" -ErrorAction SilentlyContinue
   ```
3. 用快照覆盖它（快照里的路径必须对应 `D:\Shervon_KnowledgeBase`）：
   ```powershell
   Copy-Item "D:\Shervon_KnowledgeBase\50-handoff\index\dsh_library.kb.json" "$env:USERPROFILE\.dsh\storages\dsh_library.json" -Force
   ```
4. 启动 DSH，让 agent 调 `library_search`（library=`kb`，query=`搅拌功率`）。
5. 有命中 → 完成；报错/空结果 → 还原备份，改为重建。
6. 若本机 DSH 已有别的库（如 `magverify`），替换会一起清掉；先备份，或跳过本节只用 5.3。

重建：让 DSH agent 对 `30-wiki\pages\*.md` 逐个 `library_add`（library=`kb`），560 次；或跳过语义库，只用 5.3 的 BM25。快照是 DSH 存储 `version 1`，DSH 改 schema 后可能不兼容；**不要手改 JSON**。

### 5.3 BM25 索引（所有 agent）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\kb-search.ps1" -Build
```

生成 `90-tool\search-index.json`（约 22 MB，已被 `.gitignore` 排除，通常 1 分钟内）。之后可直接查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\kb-search.ps1" -Q "搅拌功率" -Top 5
```

非 DSH 的 agent：没有 `library_search`，用 BM25 + grep `30-wiki\index*.md`，并明确告诉用户「语义检索不可用，只有关键词检索」。

## 6. 配置 Obsidian

1. 启动 Obsidian → 「Open folder as vault」→ 选 `D:\Shervon_KnowledgeBase`。
2. 首次会问是否信任作者/启用插件：本仓库**不带** `.obsidian`，没有第三方插件，可以正常打开。
3. 设置 → Files and links → **Excluded files**，逐条加入（前 6 条来自作者本机 `app.json`，最后一条是交接包）：
   ```
   10-source/
   20-md/
   40-scratch/
   90-tool/
   00-inbox/
   kb-blueprint.md
   50-handoff/
   ```
   目的：别让 137 MB 的 `20-md`（2102 个文件）拖慢搜索/图谱；阅读层是 `30-wiki`。
4. 可选社区插件（作者装了，但**非必需**，商店搜不到就跳过）：
   - `galaxy-view`：图谱视图；
   - `obsidian-go-to-line`：点击 `#L123` 跳到对应行。
5. 不要启用 Sync/Publish；本部署不需要任何同步。
6. 阅读顺序：`README.md` → `30-wiki\index.md` → 领域分册 → `30-wiki\pages\`。

## 7. 验收（逐条跑，贴真实输出）

```powershell
# 1) 检索：首条应为 [[搅拌功率计算]]，并带 #L 行号
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\kb-search.ps1" -Q "搅拌功率" -Top 3

# 2) 质检：期望「页面 570，错误 0 条，告警 0 条」
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-lint.ps1"

# 3) 链接：期望末行 unresolved=0（refs 数随书不同）
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\check-links.ps1" -Md "D:\Shervon_KnowledgeBase\20-md\化工原理_王志魁_第5版_NA.md"

# 4) 文件数与空目录
(Get-ChildItem "D:\Shervon_KnowledgeBase\30-wiki\pages" -Filter *.md).Count   # 560
Test-Path "D:\Shervon_KnowledgeBase\00-inbox"                                 # True
Test-Path "D:\Shervon_KnowledgeBase\10-source"                                # True
```

5. Obsidian 打开 `30-wiki\index.md`，能看到 4 个领域与分册链接。
6. 仅 DSH：`library_search`（`kb`，`搅拌功率`）有结果。
7. **内容抽检**：问一句「搅拌功率的文字式怎么写？」。合格答案必须带《书名》§节号（`#L行号`）；打开 `20-md\<书名>.md` 跳到该行，确认原文对得上。找不到行号 = 不合格。

`wiki-lint.ps1` 会写 `30-wiki\_lint.md`（已被 `.gitignore` 排除），不用删。

## 8. 使用规则（写内容前必读）

- **Query 六步**（`AGENTS.wiki.md` §6）：拆问题/关键词 → `kb-search.ps1` → 读命中页 → 回 `20-md` 核对 `#L` → 作答（书名 + § + `#L`）→ 标注不确定。
- **Ingest 十二步**（`90-tool\prompt-dsh.md`）：一本书一次；先读 `rules.md`；解析 → `20-md` → wiki 建页/改页 → `wiki-index.ps1` → `wiki-lint.ps1` → `coverage.py --strict`。**跳过**其中的 git 步骤（step 10）和 DSH 专用费用锁。
- **写页硬约束**：frontmatter 11 字段（type/title/question/description/domain/status/confidence/sources/related/supersedes/updated）；正文 `#L` 引用；断言必须有来源；一页一个问题；唯一译名（查 `30-wiki\glossary.md`）。
- **公式版式**：工程/物理计算式按 `50-handoff\rules\agents-AGENTS.md` 的「符号式 + 文字式」三列表格成对写；Word 里符号式用 `{LaTeX}` 源码，不要用 OMML 或纯文本上下标。
- **禁止**：改 `20-md` 原文；删 `10-source`；上传/外传原件；编造书名、节号、行号；自造领域分类；把推测写成事实。
- 改完 wiki 至少跑 `wiki-lint.ps1`；涉及索引/目录再跑 `wiki-index.ps1`、`catalog.ps1`。

## 9. 新增书籍（可选，只有要入库才做）

1. 按 MinerU 官方文档装 4.x（作者实测 4.1.7），模型放本机任意可读目录。
2. 改掉脚本里的作者本机路径（先备份）。查找：
   ```powershell
   Select-String -Path "D:\Shervon_KnowledgeBase\90-tool\scripts\*" -Pattern 'C:\\Users\\shervon' |
     Select-Object Path, LineNumber, Line
   ```
   已知 4 处：
   - `90-tool\scripts\ingest.ps1:174`（`mineru-kit.exe`）
   - `90-tool\scripts\ingest-build.ps1:30`（MinerU 自带 `python.exe`）
   - `90-tool\scripts\md-build.py:675`（临时目录）
   - `90-tool\scripts\refs-remap.py:345`（临时目录）
   `90-tool\prompt-dsh.md` 里的 `C:\Users\shervon\...` 也要替换。
3. `00-inbox` 已由 §3 创建；在它下面建书夹：`New-Item -ItemType Directory -Force "D:\Shervon_KnowledgeBase\00-inbox\<书夹>"`，把 PDF 放进去。
4. 按 `prompt-dsh.md` 执行：`ingest.ps1` → 验收行 `验收通过`、`标题体检：OK`、`SELFCHECK refs=N ok=N unresolved=0` → 覆盖率 `python 90-tool\scripts\coverage.py -Book "<10-source 下的书夹名>" --strict` → `figure-index.py -Book "<同名>"` → `wiki-index.ps1` + `wiki-lint.ps1`。
5. 执行时**跳过** `prompt-dsh.md` 里的 `git add -A; git commit` 步骤；本部署不做版本管理。
6. 费用：本地 MinerU 免费；若用云端 API 由用户付费。作者的 20 元锁 `budget-watch.ps1` 是 DSH 专用，非 DSH 跳过。
7. 版权：只入库用户有权使用的书；不要把 `10-source` 原件上传到任何地方。

## 10. 明确不做（防止「顺手」）

- 不执行 git 命令、不注册 GitHub 账号、不做 fork/PR/commit/push；下载只走 §3 的 ZIP。
- 不做多机同步：不装 Syncthing/OneDrive/iCloud，不配 git remote。
- 不装作者的 MCP（`rea`、`windows-mcp`）、技能、密钥、DSH profile。
- 不重写 `README.md`、不改 `.gitignore`、不批量改脚本；除 §9 的 4 处路径外，要改先问。
- 不删除、不移动 `10-source`/`20-md`/`30-wiki` 原文件；不把生成物写进 `10-source`。
- 不上传任何本地内容（书、页面、索引）。

## 11. 汇报模板

```markdown
## 部署报告

- 环境：Windows <版本> / PowerShell <版本> / Python <版本> / DSH <有或无>
- 安装路径：D:\Shervon_KnowledgeBase
- 仓库获取方式：GitHub ZIP（未使用 git）

| 验收项 | 结果 | 证据 |
|---|---|---|
| 文件数（560/7/7） | 通过/失败 | 实际输出 |
| 空目录 00-inbox / 10-source | 通过/失败 | 两行 Test-Path |
| kb-search 首条 | 通过/失败 | 命中标题 + #L |
| wiki-lint | 通过/失败 | 页面 N，错误 N，告警 N |
| check-links | 通过/失败 | SELFCHECK 行 |
| Obsidian 打开 | 通过/失败 | 截图/描述 |
| DSH library_search | 通过/失败/未装 | 命中数 |
| 内容抽检（书名+§+#L） | 通过/失败 | 引用与核对结果 |

- 偏差与未做项：
- 改过的文件（如有）：
- 下一步建议：
```

## 12. 卡住怎么办

同一问题最多试 2 次；仍不通就停，报告三件事：

1. 卡在哪（命令、报错原文、文件路径）；
2. 为什么（已排查什么、排除了什么）；
3. 可选路线及代价（例如：换安装路径 / 跳过语义库只用 BM25 / 放弃入库只读 wiki）。

不要用「再试一次」「可能是网络」拖时间；不要删数据、不要覆盖用户已有配置来「修复」。下载 404 就报告仓库地址可能变了，向用户要新地址，不要找镜像站。
