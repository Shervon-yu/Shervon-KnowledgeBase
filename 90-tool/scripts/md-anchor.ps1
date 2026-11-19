[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$Md,
  [string]$Section = '',
  [string]$OutDir = 'D:\Shervon_KnowledgeBase\40-new'
)
$ErrorActionPreference = 'Stop'
if(-not (Test-Path -LiteralPath $Md)){ throw "找不到 md：$Md" }
$raw   = [System.IO.File]::ReadAllText($Md)
$lines = $raw -split "`r?`n"

$heads = New-Object System.Collections.ArrayList
for($i = 0; $i -lt $lines.Count; $i++){
  $l = $lines[$i]
  if($l -match '^(#{2,4})[ \t]+(.+)$'){
    $text = $Matches[2].Trim()
    if($text -match '^\(\d+\)'){ continue }
    if($text -match '^[①②③④⑤⑥⑦⑧⑨⑩]'){ continue }
    if($text -match '^(目录|前言|序|参考文献|附录|后记)$'){ continue }
    [void]$heads.Add([pscustomobject]@{
      level  = $Matches[1].Length
      line   = $i + 1
      title  = $text
      anchor = '#L' + ($i + 1)
    })
  }
}

if($Section -ne ''){
  $hit = $heads | Where-Object { $_.title -like ("$Section*") } | Select-Object -First 1
  if($null -eq $hit){ Write-Host "未找到 §$Section" -ForegroundColor Yellow; exit 2 }
  $idx = $heads.IndexOf($hit)
  $end = if($idx + 1 -lt $heads.Count){ $heads[$idx + 1].line - 1 } else { $lines.Count }
  Write-Host ("§{0}  {1}  #L{2}-#L{3}" -f $Section, $hit.title, $hit.line, $end)
  exit 0
}

Write-Host ("md={0}" -f (Split-Path -Leaf $Md))
Write-Host ("总行数={0}  章节标题={1}" -f $lines.Count, $heads.Count)
$heads | Format-Table level, line, anchor, title -AutoSize | Out-String -Width 200 | Write-Host

if(-not (Test-Path -LiteralPath $OutDir)){ New-Item -ItemType Directory -Path $OutDir | Out-Null }
$outFile = Join-Path $OutDir ('anchors-' + [System.IO.Path]::GetFileNameWithoutExtension($Md) + '.json')
($heads | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $outFile -Encoding UTF8
Write-Host ("锚点表已写：{0}" -f $outFile)