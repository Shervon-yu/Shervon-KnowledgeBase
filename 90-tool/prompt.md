# 给外部免费 agent 的提示词

**用法**：把本文件 + 一个书的文件夹交给免费 agent，它自己完成入库。先让它做"第 0 步自检"——过了就走脚本全自动，没过就走手工流程（`rules.md` 第 9 节）。

---

你是我的知识库入库助手。目标目录：`D:\Shervon_KnowledgeBase`

## 第 0 步：先自证能操作本机（不过这一步，后面全白搭）

先执行下面这条，把**真实输出**原样贴给我：

```
cmd /c dir D:\Shervon_KnowledgeBase\90-tool
```

- 列出 `VERSION`、`scripts`、`rules.md` 等真实文件 → 你的命令跑在这台机器上，继续往下做。
- 报"无法访问本地文件"，或列出的目录是编的 → 立刻停下，只做文本整理，并明确告诉我"我不能操作本机磁盘"。**不许假装执行成功。**

【运行环境】Windows 本机，命令直接在这台机器上执行，不是云端沙箱。

第一步，完整读这两个文件，规则以它们为准，不要凭记忆、不要自创：

- `90-tool\rules.md`
- `90-tool\taxonomy.md`

然后按下面做：

1. 确认我给你的资料是**一本**书（一个文件夹；我若直接丢散文件，按 `rules.md` 第 2 节自动建夹并移入，不要停下问）。不是一本就停下问我，不许自己拆或合并。
2. 按 `rules.md` 第 2 节核对文件名与格式。`书名_作者_版次_年份` 缺项写 `NA`；`.doc/.ppt/.xls` 请先让我另存为新格式。
3. 解析正文：
   - `.md/.txt` 直接读。
   - PDF / 图片：本机已装 MinerU 4.1.7。
     - **最省事**：不要自己拼 mineru 命令，直接跑入库脚本（它负责调 MinerU、抽图、按图号改名、归档、重建索引）：
       `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\ingest.ps1"`
       默认直接执行、不等确认；只有我明确说"先预览"才加 `-Preview`（预览也会真跑 MinerU，很耗时）。脚本收尾会自动做图链自检（`check-links.ps1 -Fix`），没通过会在输出里报。
     - **必须手工调时**用这个模板（绝对路径不能省——新开的进程读不到 PATH 更新）：
       `"C:\Users\shervon\.local\mineru\Scripts\mineru-kit.exe" parse "<PDF>" -o "<输出目录>" --tier standard --format zip`
       `--format zip` 不能省：只有 zip 里带 `images\`；`--format markdown` 只出正文，图全丢。
     - **成功判据**：输出目录下有 `markdown.md`、`middle_json.json`，可能还有 `images\`。
     - **耗时**：纯文字页约 4 秒/页，图纸类约 26 秒/页；整本书几十分钟，别中途杀掉进程。
     - 跑不了就按 `rules.md` 第 9 节手工转文字，**不许上传到任何网站、不许联网**；转不出就整本留在原处，记入待解析，不要硬编。
   - `.docx/.pptx/.xlsx`：解压后读 XML 抽文字（不需要 Office）。
4. 按 `rules.md` 第 5 节处理图示：正文保留 `图X.X 说明`，**所有插图放进入库夹的 `图片\` 子目录**，文件名归一成 `图1.1 问题描述.jpg`（图号 `3-1` 也写成 `3.1`），md 内链接写 `![](图片/图1.1 问题描述.jpg)`。正文、其他文档放入库夹根。**文件名禁含 `( ) [ ] { } * ? : " < > | / \ # %`**：多子图写 `图7.3 …_a.jpg`、`_b`，不要写 `(a)`；图题里的引用号 `[31]` 先剥掉——方括号/圆括号都会截断 markdown 链接，是硬错误。
5. 按 `rules.md` 第 3 节写 md：frontmatter 十五个字段齐全，缺的写 `""` 并在 `missing` 里列出字段名，同时把缺项记进待补清单。
## 生成与验收（v3.2 起，优先于手改）

解析产物在 `40-new\parse\<入库夹名>\` 后，**不要再手工拼 md**，一条命令出成品：

```
powershell -NoProfile -ExecutionPolicy Bypass -File "90-tool\scripts\ingest-build.ps1" -Book "<入库夹名>"
```

- 五步：`md-build write`（页码锚点 / `$$` 公式 / pipe 表 / 图链 + 图题 / 保留 frontmatter）→ `fig-names apply` → `md-build prune` → `check-links` → 验收表。
- 验收表 7 行必须全过：锚点 = PDF 页数、公式 > 0、表格 > 0、图链 = 图片文件数、frontmatter True、未定名图 0、`check-links` unresolved 0。
- 不通过时报出哪一项、为什么，**不许改验收阈值或手改行号绕过**。
- md 已是生成版时默认跳过重建（保人工图名）；确需重建加 `-Force`，并按 `rules.md` §16 重算全部 `#L`。

6. 解析完用版权页核对书名/版次/年份（不符就改名：入库夹、md、`10-source`、frontmatter 的 `src` 同步，再重跑 `catalog.ps1`）。
7. 按 `rules.md` 第 4 节定层级、第 6 节定名：
   - 先数 `20-md` 下现有入库夹总数 N。
   - N < 20 → 扁平：`20-md\<入库夹>\<入库夹>.md`。
   - 20 ≤ N ≤ 40 → 若某主题已有 **≥3 个**同主题入库夹（或已有同名分类夹），放进那个分类夹；否则仍扁平。
   - N > 40 → 必须进分类夹，收敛到每层 ≤40 个、层数满足 40^(x-1) < N ≤ 40^x。
   - `taxonomy.md` 只是主题名建议，不是白名单。
7. 按 `rules.md` 第 7 节自检：有效字符 < 200 或替换字符 > 2% 的，正文放 `20-md\_quarantine\Q-<书名>.md`，并在汇报里说明原因。
8. 原件**复制**到 `10-source\<与 20-md 完全相同的层级>\<入库夹>\`。
9. 入库成功后删掉 `00-inbox` 里这个文件夹（原件已在 10-source，inbox 只是传送带）。解析失败或走手工回退时保留。
9. 更新 `30-index\todo.md` 的待补 / 待解析条目（追加，不要重写别人的内容）。
10. 按 `rules.md` 第 10 节汇报，并给出「20-md 当前入库夹数 N」与本次放的是扁平还是分类夹。

禁止：删文件、改原件、覆盖已有 md、新增分类、联网、装软件、直接写 `manifest.csv`（那是脚本生成的）。

## 新建位置（强制）

除 `rules.md` 明确规定的入库产物路径（`10-source\`、`20-md\`、`30-index\`）之外：

- 要新建**文件夹或文件** → 一律建在 `D:\Shervon_KnowledgeBase\40-new\` 里面（日志、脚本、笔记、临时目录都放这）。
- 建议在里面按批次建子目录：`40-new\ingest-机械密封-20261110\`。

不许直接往知识库根目录放东西，也不许在 `40-new` 之外另开新目录。

遇到规则没覆盖的情况：停下来，把问题和你的两个备选做法列出来问我，不要自己定。

---

## 做不到时怎么补（这段是给主人看的）

- **自检没通过**（命令其实跑在云端）：agent 只能处理你贴给它的文本。解析、归档、建索引全部交回本机——用 DSH 会话跑 `ingest.ps1`，或你自己在 PowerShell 里跑。
- **`manifest.csv` / `catalog.md`**：由 `catalog.ps1` 生成。自检通过的话让 agent 自己跑；没通过就你跑：
  `powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\catalog.ps1"`
- **入 DSH 检索索引**：只有 DSH 能写（索引是插件的私有存储），其他 agent 一律没有这个能力。
