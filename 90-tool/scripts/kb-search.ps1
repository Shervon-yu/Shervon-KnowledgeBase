[CmdletBinding()]
param(
  [string]$WikiDir = 'D:\Shervon_KnowledgeBase\30-wiki',
  [string]$IndexPath = 'D:\Shervon_KnowledgeBase\90-tool\search-index.json',
  [string]$Q = '',
  [int]$Top = 10,
  [string]$Domain = '',
  [switch]$Build
)
$ErrorActionPreference = 'Stop'
$k1 = 1.2
$b  = 0.75
$weights = @{ title = 3; aliases = 2; desc = 2; body = 1 }
$skipNames = @('log.md','glossary.md','_lint.md','catalog.md','todo.md')

function Get-Fm([string]$text){
  $o = [ordered]@{ type=''; title=''; question=''; description=''; domain=''; status=''; updated=''; aliases=@() }
  if($text -notmatch '(?s)^---\r?\n(.*?)\r?\n---'){ return $o }
  $fm = $Matches[1]
  $lines = $fm -split "`r?`n"
  $inAlias = $false
  foreach($line in $lines){
    if($line -match '^type:\s*(.+)$'){ $o.type = $Matches[1].Trim(); $inAlias=$false; continue }
    if($line -match '^title:\s*(.+)$'){ $o.title = $Matches[1].Trim().Trim('"'); $inAlias=$false; continue }
    if($line -match '^question:\s*(.*)$'){ $o.question = $Matches[1].Trim().Trim('"'); $inAlias=$false; continue }
    if($line -match '^description:\s*(.*)$'){ $o.description = $Matches[1].Trim().Trim('"'); $inAlias=$false; continue }
    if($line -match '^domain:\s*(.+)$'){ $o.domain = $Matches[1].Trim().Trim('"'); $inAlias=$false; continue }
    if($line -match '^status:\s*(.+)$'){ $o.status = $Matches[1].Trim(); $inAlias=$false; continue }
    if($line -match '^updated:\s*(.+)$'){ $o.updated = $Matches[1].Trim().Trim('"'); $inAlias=$false; continue }
    if($line -match '^aliases:\s*\[(.*)\]\s*$'){
      $inner = $Matches[1].Trim()
      if($inner -ne ''){ $o.aliases = @($inner -split ',' | ForEach-Object { $_.Trim().Trim('"').Trim("'") } | Where-Object { $_ -ne '' }) }
      $inAlias = $false; continue
    }
    if($line -match '^aliases:\s*$'){ $inAlias = $true; continue }
    if($line -match '^(\w+):'){ $inAlias=$false; continue }
    if($inAlias -and $line -match '^\s*-\s*(.+)$'){ $o.aliases += $Matches[1].Trim().Trim('"').Trim("'"); continue }
  }
  return $o
}

function Get-Tokens([string]$s){
  $out = New-Object System.Collections.ArrayList
  if([string]::IsNullOrEmpty($s)){ return @() }
  $cjk = New-Object System.Collections.ArrayList
  $lat = New-Object System.Text.StringBuilder
  function Flush-Cjk([System.Collections.ArrayList]$arr){ if($arr.Count -gt 0){ $run = -join $arr; for($i=0; $i -lt $run.Length-1; $i++){ [void]$out.Add($run.Substring($i,2)) }; $arr.Clear() } }
  function Flush-Lat([System.Text.StringBuilder]$sb){ if($sb.Length -gt 0){ $w = $sb.ToString().ToLowerInvariant(); if($w.Length -ge 2){ [void]$out.Add($w) }; [void]$sb.Clear() } }
  foreach($ch in $s.ToCharArray()){
    $code = [int]$ch
    $isCjk = ($code -ge 0x4E00 -and $code -le 0x9FFF) -or ($code -ge 0x3400 -and $code -le 0x4DBF) -or ($code -ge 0xF900 -and $code -le 0xFAFF)
    if($isCjk){
      Flush-Lat $lat
      [void]$cjk.Add($ch)
    } else {
      Flush-Cjk $cjk
      if([char]::IsLetterOrDigit($ch)){ [void]$lat.Append($ch) } else { Flush-Lat $lat }
    }
  }
  Flush-Cjk $cjk
  Flush-Lat $lat
  return @($out)
}

function New-Tf([string[]]$toks){
  $h = @{}
  foreach($t in $toks){ if($h.ContainsKey($t)){ $h[$t]++ } else { $h[$t] = 1 } }
  return $h
}

function Build-Index {
  $docs = [ordered]@{}
  $df = @{ title = @{}; aliases = @{}; desc = @{}; body = @{} }
  $sumLen = @{ title = 0; aliases = 0; desc = 0; body = 0 }
  $n = 0
  $dirs = @('pages','notes')
  foreach($d in $dirs){
    $p = Join-Path $WikiDir $d
    if(-not (Test-Path -LiteralPath $p)){ continue }
    $files = @(Get-ChildItem -LiteralPath $p -Filter *.md -File | Where-Object { $skipNames -notcontains $_.Name -and $_.Name -notmatch '^index(-.+)?\.md$' -and $_.Name -notmatch '^figures-.+\.md$' })
    foreach($f in $files){
      $text = [System.IO.File]::ReadAllText($f.FullName)
      $fm = Get-Fm $text
      $body = $text -replace '(?s)^---\r?\n.*?\r?\n---\r?\n?',''
      $fields = @{
        title   = [string]$fm.title
        aliases = (($fm.aliases | Where-Object { $_ }) -join ' ')
        desc    = [string]$fm.description
        body    = $body
      }
      $tf = @{}; $len = @{}
      foreach($fn in $fields.Keys){
        $toks = @(Get-Tokens ([string]$fields[$fn]))
        $tf[$fn] = New-Tf $toks
        $len[$fn] = $toks.Count
        $sumLen[$fn] += $toks.Count
        foreach($t in $tf[$fn].Keys){ if($df[$fn].ContainsKey($t)){ $df[$fn][$t]++ } else { $df[$fn][$t] = 1 } }
      }
      $docs[$f.BaseName] = [ordered]@{
        path = $f.FullName
        type = $fm.type; domain = $fm.domain; status = $fm.status; updated = $fm.updated
        tf = $tf; len = $len
      }
      $n++
    }
  }
  $avgdl = @{}
  foreach($fn in $sumLen.Keys){ $avgdl[$fn] = if($n -gt 0){ [double]$sumLen[$fn] / $n } else { 0 } }
  $idx = [ordered]@{ built = (Get-Date -Format 'yyyy-MM-dd HH:mm'); N = $n; avgdl = $avgdl; df = $df; docs = $docs }
  [System.IO.File]::WriteAllText($IndexPath, ($idx | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding($false)))
  Write-Host ("索引已建：{0} 页 → {1}" -f $n, $IndexPath)
}

function Test-NeedBuild {
  if($Build){ return $true }
  if(-not (Test-Path -LiteralPath $IndexPath)){ return $true }
  $idxTime = (Get-Item -LiteralPath $IndexPath).LastWriteTime
  foreach($d in @('pages','notes')){
    $p = Join-Path $WikiDir $d
    if(-not (Test-Path -LiteralPath $p)){ continue }
    $latest = Get-ChildItem -LiteralPath $p -Filter *.md -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if($latest -and $latest.LastWriteTime -gt $idxTime){ return $true }
  }
  return $false
}

function Get-Idf($dfField, [int]$N, [string]$t){
  if($dfField.PSObject.Properties.Name -notcontains $t){ return 0 }
  $d = [double]$dfField.$t
  return [Math]::Log(1 + ($N - $d + 0.5) / ($d + 0.5))
}

if(Test-NeedBuild){ Build-Index }

if([string]::IsNullOrEmpty($Q)){
  Write-Host '用法：kb-search.ps1 -Q "<查询>" [-Top 10] [-Domain "<领域关键词>"] [-Build]'
  Write-Host '不带 -Q 且索引存在时只打印本行。索引：' + $IndexPath
  return
}

$idx = Get-Content -LiteralPath $IndexPath -Raw -Encoding UTF8 | ConvertFrom-Json
$qtoks = @(Get-Tokens $Q)
if($qtoks.Count -eq 0){ Write-Host '查询无法分词（需要至少一个汉字或两个字母的词）'; return }

$results = New-Object System.Collections.ArrayList
foreach($name in $idx.docs.PSObject.Properties.Name){
  $doc = $idx.docs.$name
  if($Domain -ne '' -and $doc.domain -notlike ('*' + $Domain + '*')){ continue }
  $score = 0.0
  foreach($fn in $weights.Keys){
    $w = [double]$weights[$fn]
    $avg = [double]$idx.avgdl.$fn
    $len = [double]$doc.len.$fn
    $norm = $k1 * (1 - $b + $b * $(if($avg -gt 0){ $len / $avg } else { 1 }))
    foreach($t in $qtoks){
      $idf = Get-Idf $idx.df.$fn $idx.N $t
      if($idf -le 0){ continue }
      $tfd = 0
      if($doc.tf.$fn.PSObject.Properties.Name -contains $t){ $tfd = [double]$doc.tf.$fn.$t }
      $score += $w * $idf * ($tfd * ($k1 + 1)) / ($tfd + $norm)
    }
  }
  if($score -gt 0){ [void]$results.Add([pscustomobject]@{ name = $name; score = $score; doc = $doc }) }
}
$results = @($results | Sort-Object score -Descending | Select-Object -First $Top)

if($results.Count -eq 0){ Write-Host '无命中。可先 kb-search.ps1 -Build 重建索引。'; return }

$i = 0
foreach($r in $results){
  $i++
  $d = $r.doc
  Write-Host ('[{0}] {1:N4}　[[{2}]]　({3} / {4} / updated {5})' -f $i, $r.score, $r.name, $d.domain, $d.status, $d.updated)
  if(Test-Path -LiteralPath $d.path){
    $text = [System.IO.File]::ReadAllText($d.path)
    $lines = $text -split "`r?`n"
    $bodyStart = 0
    $dashes = 0
    for($i2=0; $i2 -lt $lines.Count -and $dashes -lt 2; $i2++){ if($lines[$i2].Trim() -eq '---'){ $dashes++; if($dashes -eq 2){ $bodyStart = $i2 + 1 } } }
    $shown = 0
    for($ln=$bodyStart; $ln -lt $lines.Count -and $shown -lt 3; $ln++){
      $line = $lines[$ln]
      $hitLine = $false
      foreach($t in $qtoks){ if($line.Contains($t)){ $hitLine = $true; break } }
      if($hitLine){
        $disp = $line.Trim()
        if($disp.Length -gt 80){ $disp = $disp.Substring(0,80) + '…' }
        Write-Host ('    #L{0}　{1}' -f ($ln+1), $disp)
        $shown++
      }
    }
  }
}
