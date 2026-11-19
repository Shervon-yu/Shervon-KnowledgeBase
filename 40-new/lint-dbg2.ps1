[CmdletBinding()]
param(
  [string]$WikiDir = 'D:\Shervon_KnowledgeBase\50-wiki',
  [int]$MaxLines = 150,
  [int]$MinInbound = 2
)
$ErrorActionPreference = 'Stop'
$NL = [string][char]10
$skip = @('index.md','log.md','glossary.md','_lint.md')

function Get-Fm([string]$text){
  $o = [ordered]@{ type=''; title=''; status=''; aliases=@(); books=@() }
  if($text -notmatch '(?s)^---\r?\n(.*?)\r?\n---'){ return $o }
  $fm = $Matches[1]
  $lines = $fm -split "`r?`n"
  $inAlias = $false; $inSources = $false
  foreach($line in $lines){
    if($line -match '^type:\s*(.+)$'){ $o.type = $Matches[1].Trim(); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^title:\s*(.+)$'){ $o.title = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^status:\s*(.+)$'){ $o.status = $Matches[1].Trim(); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^aliases:\s*\[(.*)\]\s*$'){
      $inner = $Matches[1].Trim()
      if($inner -ne ''){ $o.aliases = @($inner -split ',' | ForEach-Object { $_.Trim().Trim('"').Trim("'") } | Where-Object { $_ -ne '' }) }
      $inAlias = $false; $inSources=$false; continue
    }
    if($line -match '^aliases:\s*$'){ $inAlias = $true; $inSources=$false; continue }
    if($line -match '^sources:\s*$'){ $inSources = $true; $inAlias=$false; continue }
    if($line -match '^(\w+):'){ $inAlias=$false; $inSources=$false; continue }
    if($inAlias -and $line -match '^\s*-\s*(.+)$'){ $o.aliases += $Matches[1].Trim().Trim('"').Trim("'"); continue }
    if($inSources -and $line -match '^\s*-\s*book:\s*(.+)$'){ $o.books += $Matches[1].Trim(); continue }
    if($inSources -and $line -match '^\s*book:\s*(.+)$'){ $o.books += $Matches[1].Trim(); continue }
  }
  return $o
}

$files = @(Get-ChildItem -LiteralPath $WikiDir -Recurse -Filter *.md -File |
  Where-Object { $skip -notcontains $_.Name -and $_.Name -notmatch '^index(-.+)?\.md$' })
$pages = [ordered]@{}
foreach($f in $files){
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $pages[$f.BaseName] = [pscustomobject]@{
    path = $f.FullName; name = $f.BaseName; text = $text; fm = (Get-Fm $text)
  }
}

# 名称表：页面名 + title + aliases
$nameMap = @{}
foreach($k in $pages.Keys){
  $nameMap[$k] = $k
  if($pages[$k].fm.title){ $nameMap[$pages[$k].fm.title] = $k }
  foreach($a in $pages[$k].fm.aliases){ if($a){ $nameMap[$a] = $k } }
}

$nameMap.GetEnumerator() | Where-Object { $_.Key -match '导流' } | ForEach-Object { Write-Host ("NM " + $_.Key + " -> " + $_.Value) }
$nameMap.GetEnumerator() | Where-Object { $_.Value -eq '导流筒' } | ForEach-Object { Write-Host ("VAL " + $_.Key) }
$deadLink = New-Object System.Collections.ArrayList
$inbound  = @{}; foreach($k in $pages.Keys){ $inbound[$k] = 0 }
$refs     = New-Object System.Collections.ArrayList
$imgNoCap = New-Object System.Collections.ArrayList
$longPage = New-Object System.Collections.ArrayList
$noSrc    = New-Object System.Collections.ArrayList
$dup      = New-Object System.Collections.ArrayList
$supRef   = New-Object System.Collections.ArrayList
$seenTitle = @{}

foreach($k in $pages.Keys){
  $p = $pages[$k]
  $lines = $p.text -split "`r?`n"
  if($lines.Count -gt $MaxLines){ [void]$longPage.Add("$k（$($lines.Count) 行）") }
  if($p.fm.books.Count -eq 0 -and $p.fm.type -ne 'openq'){ [void]$noSrc.Add($k) }
  if($p.fm.title -ne ''){
    if($seenTitle.ContainsKey($p.fm.title)){ [void]$dup.Add("$k / $($seenTitle[$p.fm.title]) → $($p.fm.title)") }
    else { $seenTitle[$p.fm.title] = $k }
  }
  for($i=0; $i -lt $lines.Count; $i++){
    $l = $lines[$i]
    foreach($m in [regex]::Matches($l, '\[\[([^\]|]+)(\|[^\]]*)?\]\]')){
      $target = $m.Groups[1].Value.Trim()
      [void]$refs.Add([pscustomobject]@{ from=$k; to=$target; line=$i+1 })
      if(-not $nameMap.ContainsKey($target)){ [void]$deadLink.Add("$k #L$($i+1) → [[$target]]") }
      elseif($nameMap[$target] -ne $k){ $inbound[$nameMap[$target]] = $inbound[$nameMap[$target]] + 1 }
    }
    if($l -match '!\[[^\]]*\]\(([^)]+)\)'){
      $rel = $Matches[1]
      $relClean = $rel -replace '^<|>$',''
      $relClean = [System.Uri]::UnescapeDataString($relClean)
      if($relClean -notmatch '^[a-zA-Z]+://'){
        $abs = Join-Path (Split-Path $p.path) $relClean
        if(-not (Test-Path -LiteralPath $abs)){ [void]$deadLink.Add("$k #L$($i+1) 图不存在 → $relClean") }
      }
      $cap = ''
      for($j=$i+1; $j -le [Math]::Min($i+2, $lines.Count-1); $j++){
        $t = ($lines[$j] -replace '^\s*[-*>\s]+','').Trim()
        if($t -ne '' -and $t -notmatch '^!?\['){ $cap = $t; break }
      }
      if($cap -eq ''){ [void]$imgNoCap.Add("$k #L$($i+1) $relClean") }
    }
  }
}

$orphan = New-Object System.Collections.ArrayList
foreach($k in $pages.Keys){ if($inbound[$k] -lt $MinInbound){ [void]$orphan.Add("$k（入链 $($inbound[$k])）") } }

foreach($r in $refs){
  if($nameMap.ContainsKey($r.to)){
    $tk = $nameMap[$r.to]
    if($pages[$tk].fm.status -eq 'superseded'){ [void]$supRef.Add("$($r.from) #L$($r.line) → $tk（已 superseded）") }
  }
}

$idxPath = Join-Path $WikiDir 'index.md'
$drift = New-Object System.Collections.ArrayList
if(Test-Path -LiteralPath $idxPath){
  # index.md 可能只是按 domain 分册的目录；把所有 index*.md 合起来判定漂移
  $idx = ''
  foreach($f in (Get-ChildItem -LiteralPath $WikiDir -Filter 'index*.md' -File)){ $idx += [System.IO.File]::ReadAllText($f.FullName) + "`n" }
  foreach($k in $pages.Keys){
    if($idx -notmatch ('\[\[' + [regex]::Escape($k) + '\]\]')){ [void]$drift.Add("$k 不在 index.md") }
  }
  foreach($m in [regex]::Matches($idx, '\[\[([^\]|]+)')){
    $t = $m.Groups[1].Value.Trim()
    if(-not $nameMap.ContainsKey($t)){ [void]$drift.Add("index.md 有行无页：[[$t]]") }
  }
} else { [void]$drift.Add('index.md 不存在') }

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('# wiki lint 报告')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('生成时间：' + (Get-Date -Format 'yyyy-MM-dd HH:mm') + '　页面数：' + $pages.Count)
[void]$sb.AppendLine('')
$orphanKey = '2 孤儿页（入链 <' + $MinInbound + '）'
$longKey   = '4 超长页（>' + $MaxLines + ' 行）'
$blocks = [ordered]@{
  '1 死链'          = $deadLink
  $orphanKey        = $orphan
  '3 无来源'        = $noSrc
  $longKey          = $longPage
  '5 同义重复'      = $dup
  '6 过期断言被引用' = $supRef
  '7 index 漂移'    = $drift
  '8 图无转述'      = $imgNoCap
}
$total = 0
foreach($key in $blocks.Keys){
  $items = @($blocks[$key])
  $total += $items.Count
  [void]$sb.AppendLine('## ' + $key + '：' + $items.Count)
  [void]$sb.AppendLine('')
  if($items.Count -eq 0){ [void]$sb.AppendLine('（无）') }
  else { foreach($it in $items){ [void]$sb.AppendLine('- ' + $it) } }
  [void]$sb.AppendLine('')
}
$out = Join-Path $WikiDir '_lint.md'
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Host ('lint 完成：页面 {0}，问题 {1} 条 → {2}' -f $pages.Count, $total, $out)
if($total -gt 0){ exit 1 }