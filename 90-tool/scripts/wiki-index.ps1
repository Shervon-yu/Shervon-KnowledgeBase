[CmdletBinding()]
param(
  [string]$WikiDir = 'D:\Shervon_KnowledgeBase\30-wiki',
  [int]$MaxLines = 300,
  [int]$ChunkRows = 290
)
$ErrorActionPreference = 'Stop'
$sections = [ordered]@{
  pages       = @('concept','entity')
  notes       = @('note','howto')
  sources     = @('source')
  comparisons = @('comparison')
  openq       = @('openq')
}
$titles = @{
  pages       = 'pages —— 知识页'
  notes       = 'notes —— 经验页（note + howto）'
  sources     = 'sources —— 书页'
  comparisons = 'comparisons —— 对比页'
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
  Where-Object { $_.Name -notmatch '^index(-.+)?\.md$' -and $_.Name -notin @('log.md','glossary.md','_lint.md','catalog.md','todo.md') }
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

function Render-Items($items){
  if($items.Count -eq 0){ return '' }
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.AppendLine('| 页面 | 摘要 |')
  [void]$sb.AppendLine('|:---|:---|')
  foreach($r in $items){
    $s = $r.summary
    if($r.status -eq 'superseded'){ $s = '（已过期）' + $s }
    [void]$sb.AppendLine("| $($r.page) | $s |")
  }
  [void]$sb.AppendLine('')
  return $sb.ToString()
}

function Render-Section([string]$sectionKey, $items){
  $sub = @($items | Where-Object { $_.dir -eq $sectionKey })
  if($sub.Count -eq 0){ return $null }
  return ('## ' + $titles[$sectionKey] + "`n`n" + (Render-Items $sub))
}

function Get-LineCount([string]$t){ ([regex]::Matches($t, "`n")).Count }

function Write-Book([string]$fn, [string]$titleLine, [string]$body){
  $txt = "# 索引：$titleLine`n`n> 由 `90-tool\scripts\wiki-index.ps1` 生成，单册上限 $MaxLines 行。返回总目录：index.md`n> 生成时间：$stamp`n`n" + $body
  [System.IO.File]::WriteAllText((Join-Path $WikiDir $fn), $txt, $enc)
}

$enc = New-Object System.Text.UTF8Encoding($false)
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'

$head = "# Wiki 索引`n`n> 本文件由 ``90-tool\scripts\wiki-index.ps1`` 生成，人工只补「一句话摘要」列。单册上限 $MaxLines 行：整库不超则只写本文件；超了按 domain 拆一级分册，单领域分册再超则按 section 拆二级、按条数拆多块。`n> 生成时间：$stamp`n`n"

$singleParts = New-Object System.Collections.ArrayList
foreach($sk in $sections.Keys){
  $s = Render-Section $sk $all
  if($s){ [void]$singleParts.Add($s) }
}
$single = $head + ($singleParts -join '')

$domains = @($all | Group-Object domain | Sort-Object -Property @{Expression={$_.Count};Descending=$true}, Name)

if((Get-LineCount $single) -le $MaxLines){
  Get-ChildItem -LiteralPath $WikiDir -Filter 'index-*.md' -File | Remove-Item -Force
  [System.IO.File]::WriteAllText((Join-Path $WikiDir 'index.md'), $single, $enc)
  Write-Host ("index.md 已写：页面 {0} 个，{1} 行" -f $all.Count, (Get-LineCount $single))
} else {
  $sb = New-Object System.Text.StringBuilder
  [void]$sb.AppendLine('# Wiki 索引（领域树）')
  [void]$sb.AppendLine('')
  [void]$sb.AppendLine('> 本文件由 `90-tool\scripts\wiki-index.ps1` 生成。按领域与 section 两级拆成分册（index-<领域>-<section>.md），单册超 ' + $MaxLines + ' 行再按条数分块。')
  [void]$sb.AppendLine('> 生成时间：' + $stamp)
  [void]$sb.AppendLine('')
  [void]$sb.AppendLine('| 领域 | 页数 | 分册 |')
  [void]$sb.AppendLine('|:---|---:|:---|')
  $old = @(Get-ChildItem -LiteralPath $WikiDir -Filter 'index-*.md' -File | ForEach-Object { $_.Name })
  $written = @()
  foreach($g in $domains){
    $slug = ($g.Name -replace '[\\/:*?"<>|\s]','-')
    if($slug.Length -gt 40){ $slug = $slug.Substring(0,40) }
    $group = @($g.Group)
    $parts = New-Object System.Collections.ArrayList
    foreach($sk in $sections.Keys){
      $sub = @($group | Where-Object { $_.dir -eq $sk })
      if($sub.Count -eq 0){ continue }
      $secHead = '## ' + $titles[$sk] + "`n`n"
      if((Get-LineCount ($secHead + (Render-Items $sub))) -le $MaxLines){
        $fn = "index-$slug-$sk.md"
        Write-Book $fn ($g.Name + ' · ' + $titles[$sk]) ($secHead + (Render-Items $sub))
        [void]$parts.Add($fn)
        $written += $fn
      } else {
        $chunkIdx = 1
        $totalChunks = [Math]::Ceiling($sub.Count / $ChunkRows)
        for($i2=0; $i2 -lt $sub.Count; $i2 += $ChunkRows){
          $chunk = @($sub[$i2..([Math]::Min($i2+$ChunkRows-1, $sub.Count-1))])
          $fn2 = if($chunkIdx -eq 1){ "index-$slug-$sk.md" } else { "index-$slug-$sk-$chunkIdx.md" }
          Write-Book $fn2 ($g.Name + ' · ' + $titles[$sk] + "（第 $chunkIdx / $totalChunks 块）") ($secHead + (Render-Items $chunk))
          [void]$parts.Add($fn2)
          $written += $fn2
          $chunkIdx++
        }
      }
    }
    [void]$sb.AppendLine("| $($g.Name) | $($g.Count) | $(($parts -join ' ')) |")
  }
  [void]$sb.AppendLine('')
  [System.IO.File]::WriteAllText((Join-Path $WikiDir 'index.md'), $sb.ToString(), $enc)
  foreach($o in $old){ if($written -notcontains $o){ Remove-Item -LiteralPath (Join-Path $WikiDir $o) -Force } }
  Write-Host ("index.md 已写：页面 {0} 个，按 {1} 个领域拆分，共 {2} 个分册" -f $all.Count, $domains.Count, $written.Count)
}
