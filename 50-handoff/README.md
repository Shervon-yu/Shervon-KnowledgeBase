# 50-handoff — 交接包

本目录集中存放「只存在于作者本机 DSH 层」或「体积大、不适合放主目录」的资产，供换机或他人部署时使用。**部署入口是仓库根目录的 [`AGENT-SETUP.md`](../AGENT-SETUP.md)**；本文件只说明包内各件与限制。

## 目录

| 路径 | 内容 | 入 GitHub |
|---|---|---|
| `rules/dsh-AGENTS.md` | DSH 全局行为规则（输出风格、诚实标准、执行边界、权限） | 是 |
| `rules/agents-AGENTS.md` | 文档与公式版式规则（与上者同级） | 是 |
| `index/dsh_library.kb.json` | DSH `kb` 语义库快照：560 文档 / 1896 块 / 256 维，10.6 MB | 是 |
| `installer/Obsidian-1.15.1.exe` | Obsidian Windows x64 安装包，339 MB | **否**（见下） |
| `installer/README.md` | 安装包校验值与官网地址 | 是 |

## 三条限制

1. **安装包不在 GitHub 包里。** GitHub 单文件上限 100 MB，本文件 339 MB，`50-handoff/.gitignore` 已排除 `installer/*.exe`。从 GitHub 下载仓库时 `installer/` 里只有 README，请到 <https://obsidian.md/download> 下载任意 ≥1.5 的 Windows 版。
2. **索引快照是 DSH 私有存储格式（version 1）。** 文档路径写死为 `D:\Shervon_KnowledgeBase\...`；DSH 大版本变化后可能不兼容。不兼容就还原备份、按 [`index/README.md`](index/README.md) 重建，不要手改 JSON。
3. **两份 `AGENTS.md` 是全局规则。** 装到 `%USERPROFILE%\.dsh\` 与 `%USERPROFILE%\.agents\` 后会影响该用户所有项目；已有自己的规则时先备份、合并，不要直接覆盖。

部署时 `AGENT-SETUP.md` §3 会补建 `00-inbox\` 与 `10-source\` 两个空目录；GitHub ZIP 不含空目录，`10-source` 原 PDF 仍不提供。

## 来源与时间

- 导出时间：2026-11-26（Asia/Shanghai）。
- 规则文件：复制作者本机 `C:\Users\shervon\.dsh\AGENTS.md`、`C:\Users\shervon\.agents\AGENTS.md`；仅把 `dsh-AGENTS.md` §0 的两处作者绝对路径换成 `%USERPROFILE%\...`，其余未改。
- 索引快照：从 `C:\Users\shervon\.dsh\storages\dsh_library.json` 过滤 `library == "kb"` 的文档与块，丢弃 `magverify` 库与审计表。
- 安装包：`C:\Users\shervon\Downloads\Obsidian-1.15.1.exe`。

## 校验

```powershell
Get-FileHash "D:\Shervon_KnowledgeBase\50-handoff\installer\Obsidian-1.15.1.exe" -Algorithm SHA256
# 218C7D30ACC065355CE94719DD996D5E2A2347CDE3811EA5DC29380583F02B58
(Get-Item "D:\Shervon_KnowledgeBase\50-handoff\index\dsh_library.kb.json").Length
# 10647827
```
