# index/ — 语义索引快照与重建

## 这是什么

`dsh_library.kb.json` 是 DeepSeek Harness（DSH）`library_search` 使用的向量库存储文件，从作者本机 `dsh_library.json` 中只保留 `kb` 库：

- 560 个文档（对应 `30-wiki\pages\*.md`）
- 1896 个块，256 维 embedding
- 文档路径：`D:\Shervon_KnowledgeBase\30-wiki\pages\...`
- 导出时间：2026-11-26
- 文件大小：10,647,827 字节

DSH 的库不是仓库文件，正常安装不会自带；没有它，`library_search` 查不到本库内容（BM25 仍可用）。

## 恢复（仅 DSH，且确认可替换）

> 会**整体替换** DSH 现有的 `dsh_library.json`。本机若已有其他库，先备份；不要把两个库直接合并进这个 JSON。

1. 退出 DSH（含托盘/后台进程）。
2. 备份：
   ```powershell
   Copy-Item "$env:USERPROFILE\.dsh\storages\dsh_library.json" "$env:USERPROFILE\.dsh\storages\dsh_library.json.bak" -ErrorAction SilentlyContinue
   ```
3. 复制：
   ```powershell
   Copy-Item "D:\Shervon_KnowledgeBase\50-handoff\index\dsh_library.kb.json" "$env:USERPROFILE\.dsh\storages\dsh_library.json" -Force
   ```
4. 启动 DSH，让 agent 调 `library_search`（library = `kb`，query = `搅拌功率`）。
5. 命中 → 完成；报错或空结果 → 还原 `.bak`，走下面「重建」。

## 重建（版本不一致，或想干净安装）

让 DSH agent 对 `30-wiki\pages\*.md` 逐个调用 `library_add`（library 名 `kb`），共 560 次。DSH 会自动分块并生成 embedding；重建后语义检索能力相当，但 chunk 边界与排序不保证逐字一致，代价是时间与 embedding 费用。

## BM25（所有 agent 可用，不依赖 DSH）

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\kb-search.ps1" -Build
```

生成 `90-tool\search-index.json`（约 22 MB，已被 `.gitignore` 排除）。之后：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Shervon_KnowledgeBase\90-tool\scripts\kb-search.ps1" -Q "搅拌功率" -Top 5
```

## 限制

- 快照是 DSH 存储 `version 1`；DSH 改 schema 后可能读不了。**不要手改 JSON**。
- 文档路径写死 `D:\Shervon_KnowledgeBase`；换盘符后内容仍可能可检索，但路径显示不对。建议按 `AGENT-SETUP.md` §2 固定路径。
- 快照只含 `kb`；不含作者的 `magverify` 库、MCP、会话记录。
- 快照不是「唯一正确索引」：重建后的 chunk 边界可能不同，检索排序略有差异，属正常。
