[CmdletBinding()]
param(
  [string]$WikiDir = 'D:\Shervon_KnowledgeBase\30-wiki'
)
$ErrorActionPreference = 'Stop'
$sections = [ordered]@{
  pages       = @('concept','entity')
  sources     = @('source')
  comparisons = @('comparison')
  howto       = @('howto')
  openq       = @('openq')
}
$titles = @{
  pages       = 'pages —— 知识页'
  sources     = 'sources —— 书页'
  comparisons = 'comparisons —— 对比页'
  howto       = 'howto —— 做法页'
  openq       = 'openq —— 未决页'
}

function Get-FrontMatter([string]$text){
  $r = @{ type=''; title=''; status=''; domain='' }
  if($text -match '(?s)^---\r?\n(.*?)\r?\n---'){ $fm = $Matches[1] } else { return $r }
  foreach($line in ($fm -split "`r?`n")){
    if($line -match '^type:\s*(.+)$')   { $r.type   = $Matches[1].Trim() }
    if($line -match '^title:\s*(.+)$')  { $r.title  = $Matches[1].Trim().Trim('"') }
    if($line -match '^status:\s*(.+)$') { $r.status = $Matches[1].Trim() }
    if($line -match '^domain:\s*(.+)$') { $r.domain = $Matches[1].Trim().Trim('"') }
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

$all = New-Object System.Collections.ArrayList
$files = Get-ChildItem -LiteralPath $WikiDir -Filter *.md -File -Recurse |
  Where-Object { $_.Name -notmatch '^index(-.+)?\.md$' -and $_.Name -notin @('log.md','glossary.md','_lint.md') }
foreach($f in $files){
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $fm   = Get-FrontMatter $text
  $dir  = @($sections.Keys | Where-Object { $sections[$_] -contains $fm.type })
  if($dir.Count -eq 0){ continue }
  $name = if($fm.title -ne ''){ $fm.title } else { $f.BaseName }
  $dom  = if($fm.domain -ne ''){ $fm.domain } else { '未归类' }
  [void]$all.Add([pscustomobject]@{
    dir = $dir[0]; type = $fm.type; domain = $dom
    page = '[[' + $f.BaseName + ']]'
    summary = (Get-Summary $text)
    status = $fm.status
  })
}

function Render-Tables($items){
  $sb = New-Object System.Text.StringBuilder
  foreach($k in $sections.Keys){
    $sub = @($items | Where-Object { $_.dir -eq $k })
    if($sub.Count -eq 0){ continue }
    [void]$sb.AppendLine('## ' + $titles[$k])
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('| 页面 | 摘要 |')
    [void]$sb.AppendLine('|:---|:---|')
    foreach($r in $sub){
      $s = $r.summary
      if($r.status -eq 'superseded'){ $s = '（已过期）' + $s }
      [void]$sb.AppendLine("| $($r.page) | $s |")
    }
    [void]$sb.AppendLine('')
  }
  return $sb.ToString()
}

function Get-LineCount([string]$t){ ([regex]::Matches($t, "`n")).Count }

$enc = New-Object System.Text.UTF8Encoding($false)
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'

# 先估算单文件行数
$head = "# Wiki 索引`n`n> 本文件由 ``90-tool\scripts\wiki-index.ps1`` 生成，人工只补「一句话摘要」列。上限 120 行，超出则按 domain 拆分子索引。`n> 生成时间：$stamp`n`n"
$single = $head + (Render-Tables $all)
$lineCount = Get-LineCount $single

$domains = @($all | Group-Object domain | Sort-Object -Property @{Expression={$_.Count};Descending=$true}, Name)

if($lineCount -le 120){
  # 清理旧子索引
  Get-ChildItem -LiteralPath $WikiDir -Filter 'index-*.md' -File | Remove-Item -Force
  [System.IO.File]::WriteAllText((Join-Path $WikiDir 'index.md'), $single, $enc)
  Write-Host ("index.md 已写：页面 {0} 个，{1} 行" -f $all.Count, $lineCount)
} else {
  # 按 domain 拆分子索引
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.AppendLine('# Wiki 索引（按领域分册）')
  [void]$sb.AppendLine('')
  [void]$sb.AppendLine('> 本文件由 `90-tool\scripts\wiki-index.ps1` 生成。页面数已超过单文件 120 行上限，按 domain 拆分子索引；先读本表，再进对应分册。')
  [void]$sb.AppendLine('> 生成时间：' + $stamp)
  [void]$sb.AppendLine('')
  [void]$sb.AppendLine('| 领域 | 页数 | 分册 |')
  [void]$sb.AppendLine('|:---|---:|:---|')
  $old = @(Get-ChildItem -LiteralPath $WikiDir -Filter 'index-*.md' -File | ForEach-Object { $_.Name })
  $written = @()
  foreach($g in $domains){
    $slug = ($g.Name -replace '[\\/:*?"<>|\s]','-')
    if($slug.Length -gt 40){ $slug = $slug.Substring(0,40) }
    $fn = "index-$slug.md"
    $body = "# 索引：$($g.Name)`n`n> 由 wiki-index.ps1 生成，上限 120 行。返回总目录：index.md`n> 生成时间：$stamp`n`n" + (Render-Tables $g.Group)
    [System.IO.File]::WriteAllText((Join-Path $WikiDir $fn), $body, $enc)
    $written += $fn
    [void]$sb.AppendLine("| $($g.Name) | $($g.Count) | $fn |")
  }
  [void]$sb.AppendLine('')
  [System.IO.File]::WriteAllText((Join-Path $WikiDir 'index.md'), $sb.ToString(), $enc)
  foreach($o in $old){ if($written -notcontains $o){ Remove-Item -LiteralPath (Join-Path $WikiDir $o) -Force } }
  Write-Host ("index.md 已写：页面 {0} 个，按 {1} 个领域拆分" -f $all.Count, $domains.Count)
}
