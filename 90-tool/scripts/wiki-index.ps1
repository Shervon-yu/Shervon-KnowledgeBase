[CmdletBinding()]
param(
  [string]$WikiDir = 'D:\Shervon_KnowledgeBase\50-wiki'
)
$ErrorActionPreference = 'Stop'
$sections = [ordered]@{
  concept    = 'concepts'
  entity     = 'entities'
  source     = 'sources'
  comparison = 'comparisons'
  howto      = 'howto'
  openq      = 'openq'
}
$titles = @{
  concepts = 'concepts —— 概念页'
  entities = 'entities —— 实体页'
  sources  = 'sources —— 书页'
  comparisons = 'comparisons —— 对比页'
  howto    = 'howto —— 做法页'
  openq    = 'openq —— 未决页'
}

function Get-FrontMatter([string]$text){
  $r = @{ type=''; title=''; status='' }
  if($text -match '(?s)^---\r?\n(.*?)\r?\n---'){ $fm = $Matches[1] } else { return $r }
  foreach($line in ($fm -split "`r?`n")){
    if($line -match '^type:\s*(.+)$')   { $r.type   = $Matches[1].Trim() }
    if($line -match '^title:\s*(.+)$')  { $r.title  = $Matches[1].Trim().Trim('"') }
    if($line -match '^status:\s*(.+)$') { $r.status = $Matches[1].Trim() }
  }
  return $r
}

function Get-Summary([string]$text){
  $body = $text -replace '(?s)^---\r?\n.*?\r?\n---\r?\n?',''
  foreach($line in ($body -split "`r?`n")){
    $t = $line.Trim()
    if($t -eq '' -or $t -match '^#{1,6}\s' -or $t -match '^([-*+]\s|\||>)'){ continue }
    $t = $t -replace '\[\[([^\]|]+)\|?([^\]]*)\]\]','$1'
    $t = $t -replace '!?\[([^\]]*)\]\([^)]*\)','$1'
    $t = $t -replace '[*_`]',''
    if($t.Length -gt 60){ $t = $t.Substring(0,60) + '…' }
    return $t
  }
  return ''
}

$rows = @{}
foreach($k in $sections.Keys){ $rows[$k] = New-Object System.Collections.ArrayList }

$files = Get-ChildItem -LiteralPath $WikiDir -Filter *.md -File -Recurse |
  Where-Object { $_.Name -notin @('index.md','log.md','glossary.md','_lint.md') }
foreach($f in $files){
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $fm   = Get-FrontMatter $text
  $type = $fm.type
  if(-not $sections.Contains($type)){ $type = 'x' ; continue }
  $name = if($fm.title -ne ''){ $fm.title } else { $f.BaseName }
  [void]$rows[$type].Add([pscustomobject]@{
    page = "[[" + $f.BaseName + "]]"
    title = $name
    summary = (Get-Summary $text)
    status = $fm.status
  })
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('# Wiki 索引')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('> 本文件由 `90-tool\scripts\wiki-index.ps1` 生成，人工只补「一句话摘要」列。上限 120 行，超出则按 domain 拆分子索引。')
[void]$sb.AppendLine('> 生成时间：' + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
[void]$sb.AppendLine('')
foreach($k in $sections.Keys){
  $sec = $sections[$k]
  [void]$sb.AppendLine("## " + $titles[$sec])
  [void]$sb.AppendLine('')
  [void]$sb.AppendLine('| 页面 | 摘要 |')
  [void]$sb.AppendLine('|:---|:---|')
  foreach($r in $rows[$k]){
    $s = $r.summary
    if($r.status -eq 'superseded'){ $s = '（已过期）' + $s }
    [void]$sb.AppendLine("| $($r.page) | $s |")
  }
  [void]$sb.AppendLine('')
}

$out = Join-Path $WikiDir 'index.md'
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))

$total = ($rows.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
$lineCount = ([regex]::Matches($sb.ToString(), "`n")).Count
Write-Host ("index.md 已写：页面 {0} 个，{1} 行" -f $total, $lineCount)
if($lineCount -gt 120){ Write-Host '警告：超过 120 行，需要按 domain 拆分子索引' -ForegroundColor Yellow }
