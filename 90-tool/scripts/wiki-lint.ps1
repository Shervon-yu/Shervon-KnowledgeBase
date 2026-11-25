[CmdletBinding()]
param(
  [string]$WikiDir = 'D:\Shervon_KnowledgeBase\30-wiki',
  [int]$MaxLines = 300,
  [int]$MinInbound = 2,
  [int]$NotesMaxAgeDays = 90
)
$ErrorActionPreference = 'Stop'
$NL = [string][char]10
$skip = @('index.md','log.md','glossary.md','_lint.md','catalog.md','todo.md')

function Get-Fm([string]$text){
  $o = [ordered]@{
    type=''; title=''; question=''; description=''; domain=''
    status=''; confidence=''; opened=''; updated=''
    aliases=@(); books=@()
  }
  if($text -notmatch '(?s)^---\r?\n(.*?)\r?\n---'){ return $o }
  $fm = $Matches[1]
  $lines = $fm -split "`r?`n"
  $inAlias = $false; $inSources = $false
  foreach($line in $lines){
    if($line -match '^type:\s*(.+)$'){ $o.type = $Matches[1].Trim(); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^title:\s*(.+)$'){ $o.title = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^question:\s*(.*)$'){ $o.question = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^description:\s*(.*)$'){ $o.description = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^domain:\s*(.+)$'){ $o.domain = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^status:\s*(.+)$'){ $o.status = $Matches[1].Trim(); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^confidence:\s*(.+)$'){ $o.confidence = $Matches[1].Trim(); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^opened:\s*(.+)$'){ $o.opened = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
    if($line -match '^updated:\s*(.+)$'){ $o.updated = $Matches[1].Trim().Trim('"'); $inAlias=$false; $inSources=$false; continue }
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

# ---------- 第 0 项：schema（字段序 / 必填 / 枚举），来源 90-tool\schema.md ----------
$schemaPath = Join-Path (Split-Path $WikiDir -Parent) '90-tool\schema.md'
$schemaOrder = New-Object System.Collections.ArrayList
$schemaReq = @{}
$enums = @{ type=@(); status=@(); confidence=@() }
if(Test-Path -LiteralPath $schemaPath){
  $schemaText = [System.IO.File]::ReadAllText($schemaPath)
  foreach($line in ($schemaText -split "`r?`n")){
    if($line -match '^\|\s*(\d+)\s*\|'){
      $cells = $line -split '\|'
      if($cells.Count -ge 7){
        $name = ($cells[2] -replace '`','').Trim()
        $req  = $cells[4].Trim()
        $enum = $cells[5].Trim()
        if($name -ne ''){
          [void]$schemaOrder.Add($name)
          $schemaReq[$name] = $req
          if($enums.ContainsKey($name) -and $enum -ne ''){
            $enums[$name] = @($enum -split '/' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' -and $_ -notmatch '\s' })
          }
        }
      }
    }
  }
}

$files = @(Get-ChildItem -LiteralPath $WikiDir -Recurse -Filter *.md -File |
  # index.md / index-<领域>.md 为生成的知识点索引，v3.12 起不设行数上限，故不参与第 4 项超长检查
  Where-Object { $skip -notcontains $_.Name -and $_.Name -notmatch '^index(-.+)?\.md$' -and $_.Name -notmatch '^figures-.+\.md$' })
$pages = [ordered]@{}
foreach($f in $files){
  $text = [System.IO.File]::ReadAllText($f.FullName)
  $pages[$f.BaseName] = [pscustomobject]@{
    path = $f.FullName; name = $f.BaseName; text = $text; fm = (Get-Fm $text)
    isNotes = ($f.FullName -match '\\notes\\')
  }
}

$schemaErr = New-Object System.Collections.ArrayList
$ageWarn   = New-Object System.Collections.ArrayList
$descOk = 0; $descMissing = 0; $updMissing = 0
$nameMap = @{}
foreach($k in $pages.Keys){
  $nameMap[$k] = $k
  if($pages[$k].fm.title){ $nameMap[$pages[$k].fm.title] = $k }
  foreach($a in $pages[$k].fm.aliases){ if($a){ $nameMap[$a] = $k } }
}

$aliasShadow = New-Object System.Collections.ArrayList
foreach($k in $pages.Keys){
  foreach($a in $pages[$k].fm.aliases){
    if($a -and $pages.Contains($a) -and $a -ne $k){ [void]$aliasShadow.Add("$k 的别名「$a」遮蔽了同名页") }
  }
}

$deadLink = New-Object System.Collections.ArrayList
$inbound  = @{}; foreach($k in $pages.Keys){ $inbound[$k] = 0 }
$refs     = New-Object System.Collections.ArrayList
$imgNoCap = New-Object System.Collections.ArrayList
$longPage = New-Object System.Collections.ArrayList
$noSrc    = New-Object System.Collections.ArrayList
$dup      = New-Object System.Collections.ArrayList
$supRef   = New-Object System.Collections.ArrayList
$seenTitle = @{}
$seenQ     = @{}
$qBad      = New-Object System.Collections.ArrayList

foreach($k in $pages.Keys){
  $p = $pages[$k]
  $lines = $p.text -split "`r?`n"
  if($lines.Count -gt $MaxLines){ [void]$longPage.Add("$k（$($lines.Count) 行）") }
  if($p.fm.books.Count -eq 0 -and $p.fm.type -ne 'openq'){ [void]$noSrc.Add($k) }
  if($p.fm.title -ne ''){
    if($seenTitle.ContainsKey($p.fm.title)){ [void]$dup.Add("$k / $($seenTitle[$p.fm.title]) → $($p.fm.title)") }
    else { $seenTitle[$p.fm.title] = $k }
  }
  $q = $p.fm.question
  if($q -eq ''){ [void]$qBad.Add("$k（缺 question）") }
  elseif($q -notmatch '[？?]$'){ [void]$qBad.Add("$k（question 非疑问句：$q）") }
  elseif($seenQ.ContainsKey($q)){ [void]$qBad.Add("$k / $($seenQ[$q]) → question 重复：$q") }
  else { $seenQ[$q] = $k }

  # --- 第 0 项：schema 校验 ---
  if($schemaOrder.Count -gt 0){
    $fmBlock = ''
    if($p.text -match '(?s)^---\r?\n(.*?)\r?\n---'){ $fmBlock = $Matches[1] }
    $lastIdx = -1
    foreach($fl in ($fmBlock -split "`r?`n")){
      if($fl -match '^([A-Za-z_][A-Za-z0-9_]*):'){
        $fk = $Matches[1]
        $oi = $schemaOrder.IndexOf($fk)
        if($oi -lt 0){ [void]$schemaErr.Add("$k 有 schema 未定义字段：$fk") }
        elseif($oi -le $lastIdx){ [void]$schemaErr.Add("$k 字段顺序不符：$fk") }
        else { $lastIdx = $oi }
      }
    }
    $vals = @{
      type=$p.fm.type; title=$p.fm.title; question=$p.fm.question
      description=$p.fm.description; domain=$p.fm.domain; status=$p.fm.status
      confidence=$p.fm.confidence; opened=$p.fm.opened; updated=$p.fm.updated
      sources=($p.fm.books.Count -gt 0); aliases=($p.fm.aliases.Count -gt 0)
    }
    foreach($fn in $schemaOrder){
      $need = $schemaReq[$fn]
      $required = $false
      if($need -eq 'all'){ $required = $true }
      elseif($need -eq 'except:openq'){ if($p.fm.type -ne 'openq'){ $required = $true } }
      elseif($need -eq 'notes'){ if($p.isNotes){ $required = $true } }
      if(-not $required){ continue }
      if(-not $vals.ContainsKey($fn)){ continue }
      $v = $vals[$fn]
      if($v -is [bool]){ if(-not $v){ [void]$schemaErr.Add("$k 缺少必填字段：$fn") } }
      elseif([string]::IsNullOrEmpty([string]$v)){ [void]$schemaErr.Add("$k 缺少必填字段：$fn") }
    }
    if($p.fm.type -ne '' -and $enums['type'].Count -gt 0 -and ($enums['type'] -notcontains $p.fm.type)){ [void]$schemaErr.Add("$k type 不在枚举内：$($p.fm.type)") }
    if($p.fm.status -ne '' -and $enums['status'].Count -gt 0 -and ($enums['status'] -notcontains $p.fm.status)){ [void]$schemaErr.Add("$k status 不在枚举内：$($p.fm.status)") }
    if($p.fm.confidence -ne '' -and $enums['confidence'].Count -gt 0 -and ($enums['confidence'] -notcontains $p.fm.confidence)){ [void]$schemaErr.Add("$k confidence 不在枚举内：$($p.fm.confidence)") }
    if($p.fm.description.Length -gt 200){ [void]$schemaErr.Add("$k description 超 200 字（$($p.fm.description.Length) 字）") }
    foreach($df in @('opened','updated')){
      $dv = $vals[$df]
      if(-not [string]::IsNullOrEmpty([string]$dv)){
        try { [void][datetime]::ParseExact([string]$dv, 'yyyy-MM-dd', $null) }
        catch { [void]$schemaErr.Add("$k $df 日期格式不合规：$dv") }
      }
    }
  }
  if($p.fm.description -ne ''){ $descOk++ } else { $descMissing++ }
  if([string]::IsNullOrEmpty($p.fm.updated) -and [string]::IsNullOrEmpty($p.fm.opened)){ $updMissing++ }

  # --- 第 11 项：经验区年龄（只告警）---
  if($p.isNotes -and -not [string]::IsNullOrEmpty($p.fm.updated)){
    try {
      $d = [datetime]::ParseExact($p.fm.updated, 'yyyy-MM-dd', $null)
      $ageDays = [int]((Get-Date).Date - $d.Date).TotalDays
      if($ageDays -gt $NotesMaxAgeDays){ [void]$ageWarn.Add("$k（updated $($p.fm.updated)，已 $ageDays 天）") }
    } catch { }
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
  foreach($f in (Get-ChildItem -LiteralPath $WikiDir -Filter 'index*.md' -File -Recurse)){ $idx += [System.IO.File]::ReadAllText($f.FullName) + "`n" }
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
[void]$sb.AppendLine('生成时间：' + (Get-Date -Format 'yyyy-MM-dd HH:mm') + '　页面数：' + $pages.Count + '　schema 字段：' + $schemaOrder.Count)
[void]$sb.AppendLine('')
$orphanKey = '2 孤儿页（入链 <' + $MinInbound + '）'
$longKey   = '4 超长页（>' + $MaxLines + ' 行）'
$blocks = [ordered]@{
  '0 schema 校验（90-tool\schema.md）' = $schemaErr
  '1 死链'          = $deadLink
  $orphanKey        = $orphan
  '3 无来源'        = $noSrc
  $longKey          = $longPage
  '5 同义重复'      = $dup
  '6 过期断言被引用' = $supRef
  '7 index 漂移'    = $drift
  '8 图无转述'      = $imgNoCap
  '9 别名遮蔽页名'  = $aliasShadow
  '10 question 不合规' = $qBad
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

$warnTotal = 0
$warnBlocks = [ordered]@{
  ('11 notes 年龄（>' + $NotesMaxAgeDays + ' 天，仅告警）') = $ageWarn
}
foreach($key in $warnBlocks.Keys){
  $items = @($warnBlocks[$key])
  $warnTotal += $items.Count
  [void]$sb.AppendLine('## ' + $key + '：' + $items.Count)
  [void]$sb.AppendLine('')
  if($items.Count -eq 0){ [void]$sb.AppendLine('（无）') }
  else { foreach($it in $items){ [void]$sb.AppendLine('- ' + $it) } }
  [void]$sb.AppendLine('')
}

[void]$sb.AppendLine('## 统计')
[void]$sb.AppendLine('')
[void]$sb.AppendLine('- description 覆盖：' + $descOk + ' / ' + $pages.Count + '（缺 ' + $descMissing + '）')
[void]$sb.AppendLine('- updated 与 opened 双缺：' + $updMissing)
[void]$sb.AppendLine('')
$out = Join-Path $WikiDir '_lint.md'
[System.IO.File]::WriteAllText($out, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Host ('lint 完成：页面 {0}，错误 {1} 条，告警 {2} 条 → {3}' -f $pages.Count, $total, $warnTotal, $out)
Write-Host ('description 覆盖 {0}/{1}，updated/opened 双缺 {2}' -f $descOk, $pages.Count, $updMissing)
if($total -gt 0){ exit 1 }
