# rules/ — DSH 层全局规则

这两份文件不是知识库内容，而是作者本机 DSH 的「底层规则」，决定 agent 怎么说话、怎么引证、怎么写公式。仓库其他位置没有副本。

## 对应关系

| 包内文件 | 目标路径 | 作用 |
|---|---|---|
| `dsh-AGENTS.md` | `%USERPROFILE%\.dsh\AGENTS.md` | 行为：极简输出、诚实标准、执行边界、权限、被质疑时先取证 |
| `agents-AGENTS.md` | `%USERPROFILE%\.agents\AGENTS.md` | 文档：公式「符号式 + 文字式」成对写、Word 用 LaTeX、Markdown 规范 |

DSH 启动时把两份都注入；项目级 `AGENTS.md` 优先于它们。两者同级、不分优先级，同时适用。

> 包内 `dsh-AGENTS.md` 只改了两处（都在 §0）：把作者绝对路径 `C:\Users\shervon\...` 换成 `%USERPROFILE%\...`，语义与条款未变。

## 安装

1. 备份已有文件（若有）：
   ```powershell
   Copy-Item "$env:USERPROFILE\.dsh\AGENTS.md" "$env:USERPROFILE\.dsh\AGENTS.md.bak" -ErrorAction SilentlyContinue
   Copy-Item "$env:USERPROFILE\.agents\AGENTS.md" "$env:USERPROFILE\.agents\AGENTS.md.bak" -ErrorAction SilentlyContinue
   ```
2. 目标不存在 → 直接复制过去。
3. 目标已存在 → **不要覆盖**。把包内内容追加到原文件末尾，一级标题改成 `# 附：……`；冲突条款按「更严的一条」执行（包内 `dsh-AGENTS.md` §7 也是这么规定的）。
4. 重启 DSH 会话生效。

## 非 DSH 用户

没有 `~/.dsh` 自动注入机制。把两份文件作为系统提示词或项目规则交给你的 agent；至少保留：引用必须带书名 + 节号 + `#L`、不确定必须说、不编造、公式成对写。

## 注意

- 这两份规则作用于**所有项目**，不只本知识库。
- 不含任何密钥、路径白名单、MCP 配置；作者的 MCP（`rea` / `windows-mcp`）在 `cordis.patch.yml`，未随包提供，也不需要。
