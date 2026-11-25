# graph.ps1 —— 从 related / supersedes 导出 Mermaid 或 DOT 关系图（P3）
# 用法：powershell -NoProfile -ExecutionPolicy Bypass -File 90-tool\scripts\graph.ps1 [-Domain 领域名] [-Format Mermaid|DOT] [-OutFile 路径]
# 只读 frontmatter，不改任何 wiki 文件；图谱只给人看，不参与检索。
param(
  [string]$Domain = "",
  [string]$Format = "Mermaid",
  [string]$OutFile = "D:\Shervon_KnowledgeBase\40-scratch\gen\graph.md",
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

function Get-Fm([string]$path) {
  # 取 frontmatter 原文字符串（两个 --- 之间）
  $lines = [System.IO.File]::ReadAllLines($path)
  if ($lines.Count -lt 2 -or $lines[0].Trim() -ne "---") { return $null }
  $sb = New-Object System.Text.StringBuilder
  for ($i = 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -eq "---") { break }
    [void]$sb.AppendLine($lines[$i])
  }
  return $sb.ToString()
}

function Get-FmField([string]$fm, [string]$field) {
  # related: ["[[A]]", "[[B|别名]]"]  → 提取 [[...]] 目标名（| 前为主名）
  $rx = "^$([regex]::Escape($field)):\s*(.*)$"
  $m = [regex]::Match($fm, $rx, [System.Text.RegularExpressions.RegexOptions]::Multiline)
  if (-not $m.Success) { return @() }
  $raw = $m.Groups[1].Value
  if ($field -in @("related", "supersedes")) {
    return [regex]::Matches($raw, "\[\[([^\]]+)\]\]") | ForEach-Object {
      ($_.Groups[1].Value -split "\|")[0].Trim()
    }
  } else {
    return @($raw.Trim().Trim('"').Trim("'"))
  }
}

$nodes = @{}   # 文件名(去 .md) → @{title; domain; section}
$order = @()   # 节点顺序
$edges = @()   # @{from; to; kind}

foreach ($p in $pages) {
  $fm = Get-Fm $p.FullName
  if (-not $fm) { continue }
  $title = (Get-FmField $fm "title")[0]
  if (-not $title) { $title = $p.BaseName }
  $dom  = (Get-FmField $fm "domain")[0]
  $key  = $p.BaseName
  $nodes[$key] = @{ title = $title; domain = $dom; section = $p.Directory.Name }
  $order += $key
  foreach ($rel in (Get-FmField $fm "related"))   { $edges += @{ from = $key; to = $rel; kind = "related" } }
  foreach ($sup in (Get-FmField $fm "supersedes")) { $edges += @{ from = $key; to = $sup; kind = "取代" } }
}

# 只保留两端都在 nodes 里的边；孤立点默认不进图
$valid = @()
foreach ($e in $edges) {
  if ($nodes.ContainsKey($e.from) -and $nodes.ContainsKey($e.to)) { $valid += $e }
}
$linked = @{}
foreach ($e in $valid) { $linked[$e.from] = $true; $linked[$e.to] = $true }
$keep = @($order | Where-Object { $linked.ContainsKey($_) })

if ($Domain -ne "") {
  $keep = @($keep | Where-Object { $nodes[$_].domain -eq $Domain })
}

# 节点 id 用 n0..nN，标签用 title
$idmap = @{}
$i = 0
foreach ($k in $keep) { $idmap[$k] = "n$i"; $i++ }

function Esc([string]$s) {
  return $s.Replace('"', "'").Replace("`r", "").Replace("`n", " ").Trim()
}

$sb = New-Object System.Text.StringBuilder
if ($Format -eq "DOT") {
  [void]$sb.AppendLine("digraph wiki {")
  [void]$sb.AppendLine('  rankdir=LR;')
  foreach ($k in $keep) {
    [void]$sb.AppendLine("  " + $idmap[$k] + " [label=`"" + (Esc $nodes[$k].title) + "`"];")
  }
  foreach ($e in $valid) {
    if ($idmap.ContainsKey($e.from) -and $idmap.ContainsKey($e.to)) {
      $lbl = if ($e.kind -eq "取代") { " [style=dashed,label=`"取代`"]" } else { "" }
      [void]$sb.AppendLine("  " + $idmap[$e.from] + " -> " + $idmap[$e.to] + $lbl + ";")
    }
  }
  [void]$sb.AppendLine("}")
} else {
  [void]$sb.AppendLine('```mermaid')
  [void]$sb.AppendLine("graph LR")
  # 按 domain 分组
  $byDom = $keep | Group-Object { $nodes[$_].domain } | Sort-Object Name
  foreach ($g in $byDom) {
    [void]$sb.AppendLine("  subgraph " + (Esc $g.Name))
    foreach ($k in $g.Group) {
      [void]$sb.AppendLine("    " + $idmap[$k] + "[" + (Esc $nodes[$k].title) + "]")
    }
    [void]$sb.AppendLine("  end")
  }
  foreach ($e in $valid) {
    if ($idmap.ContainsKey($e.from) -and $idmap.ContainsKey($e.to)) {
      $lbl = if ($e.kind -eq "取代") { " -- 取代 --> " } else { " --> " }
      [void]$sb.AppendLine("  " + $idmap[$e.from] + $lbl + $idmap[$e.to])
    }
  }
  [void]$sb.AppendLine('```')
}

[System.IO.File]::WriteAllText($OutFile, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("图谱已导出：节点 {0}、边 {1}（有效页 {2}/{3}）→ {4}" -f $keep.Count, $valid.Count, $keep.Count, $pages.Count, $OutFile)
if ($valid.Count -eq 0) { Write-Output "警告：related/supersedes 一条有效边都没有" }
