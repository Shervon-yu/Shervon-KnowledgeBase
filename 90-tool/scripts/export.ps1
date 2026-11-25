# export.ps1 —— 打包 llms.txt 摘要出口（P3，geronimo export 简化版）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File 90-tool\scripts\export.ps1 [-OutFile 路径]
# 输出：每页一行 `- title｜domain｜路径｜description`，按领域分组；喂外部 LLM 或迁移用。
param(
  [string]$OutFile = "D:\Shervon_KnowledgeBase\40-scratch\gen\llms.txt",
  [string]$WikiDir = "D:\Shervon_KnowledgeBase\30-wiki"
)

$ErrorActionPreference = "Stop"
$sections = @("pages", "notes", "sources", "comparisons", "openq")
$pages = @()
foreach ($s in $sections) {
  $dir = Join-Path $WikiDir $s
  if (Test-Path $dir) {
    $pages += Get-ChildItem $dir -Filter *.md -File
  }
}

function Get-FmField([string]$path, [string]$field) {
  $lines = [System.IO.File]::ReadAllLines($path)
  if ($lines.Count -lt 2 -or $lines[0].Trim() -ne "---") { return "" }
  $val = ""
  for ($i = 1; $i -lt $lines.Count; $i++) {
    $ln = $lines[$i]
    if ($ln.Trim() -eq "---") { break }
    if ($ln -match ("^" + [regex]::Escape($field) + ":\s*(.*)$")) {
      $val = $Matches[1].Trim().Trim('"').Trim("'")
      break
    }
  }
  return $val
}

$rows = @()
foreach ($p in $pages) {
  $title = Get-FmField $p.FullName "title"
  $dom   = Get-FmField $p.FullName "domain"
  $desc  = Get-FmField $p.FullName "description"
  if (-not $title) { $title = $p.BaseName }
  $rows += [pscustomobject]@{ title = $title; domain = $dom; rel = $p.FullName.Substring($WikiDir.Length + 1); desc = $desc }
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("# Shervon KnowledgeBase llms.txt 导出")
[void]$sb.AppendLine(("# 生成时间：{0}；页面 {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), $rows.Count))
[void]$sb.AppendLine("")
foreach ($g in ($rows | Group-Object domain | Sort-Object Name)) {
  [void]$sb.AppendLine("## " + $g.Name)
  foreach ($r in ($g.Group | Sort-Object title)) {
    [void]$sb.AppendLine(("- {0}｜{1}｜{2}｜{3}" -f $r.title, $r.domain, $r.rel, $r.desc))
  }
  [void]$sb.AppendLine("")
}

[System.IO.File]::WriteAllText($OutFile, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("llms.txt 已导出：{0} 页 → {1}" -f $rows.Count, $OutFile)
