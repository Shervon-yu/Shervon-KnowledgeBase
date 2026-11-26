# installer/ — Obsidian 安装包

| 项 | 值 |
|---|---|
| 文件 | `Obsidian-1.15.1.exe` |
| 平台 | Windows x64 |
| 大小 | 339,406,872 字节（约 324 MiB） |
| SHA256 | `218C7D30ACC065355CE94719DD996D5E2A2347CDE3811EA5DC29380583F02B58` |
| 官方下载 | <https://obsidian.md/download> |

## 为什么 GitHub 包里没有

GitHub 单文件硬上限 100 MB，本文件 339 MB，无法入库；`50-handoff/.gitignore` 已排除 `installer/*.exe`。所以：

- 在本机（作者电脑）交接：直接用这个 exe。
- 从 GitHub 下载仓库：`installer/` 里只有本 README，请到官网下载任意 ≥1.5 的 Windows 版。

## 安装

1. 双击 exe，按默认选项安装（当前用户级，不需要管理员权限）。
2. 首次启动选「Open folder as vault」，指向 `D:\Shervon_KnowledgeBase`。
3. 其余配置见根目录 `AGENT-SETUP.md` §6。

## 校验（可选）

```powershell
Get-FileHash "D:\Shervon_KnowledgeBase\50-handoff\installer\Obsidian-1.15.1.exe" -Algorithm SHA256
```

应与上表一致；从官网新下载的版本号不同则不必比对。
