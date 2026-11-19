param(
  [Parameter(Mandatory=$true)][string]$Md,
  [switch]$Fix,
  [string]$ReportOut
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Md)) { Write-Host "SELFCHECK md 不存在: $Md"; exit 2 }
$mdPath = (Resolve-Path -LiteralPath $Md).Path
$mdDir  = Split-Path -Parent $mdPath
$text   = [IO.File]::ReadAllText($mdPath, [Text.Encoding]::UTF8)
$badRe  = '[\[\]\(\)\?#%:*"<>\|]'

function Get-Refs([string]$s) {
  $r = New-Object System.Collections.ArrayList
  foreach ($m in [regex]::Matches($s, '!\[[^\]]*\]\(([^)]+)\)')) { [void]$r.Add($m.Groups[1].Value.Trim()) }
  return $r
}
function Test-Link([string]$rel) {
  if ($rel -match '^([a-zA-Z]+:|//)') { return 'skip' }
  $decoded = [Uri]::UnescapeDataString($rel)
  $full = Join-Path $mdDir ($decoded -replace '\\','/')
  if (-not (Test-Path -LiteralPath $full)) { return 'missing' }
  if ($rel -match $badRe) { return 'bad' }
  return 'ok'
}

$refs = Get-Refs $text
$missing = New-Object System.Collections.ArrayList
$bad     = New-Object System.Collections.ArrayList
foreach ($t in $refs) {
  $v = Test-Link $t
  if ($v -eq 'missing') { [void]$missing.Add($t) }
  elseif ($v -eq 'bad') { [void]$bad.Add($t) }
}

$log = New-Object System.Collections.ArrayList
if ($Fix -and ($missing.Count -gt 0 -or $bad.Count -gt 0)) {
  foreach ($rel in $bad) {
    $src = Join-Path $mdDir (($rel -replace '\\','/'))
    $dir = Split-Path -Parent $src
    $name = Split-Path -Leaf $src
    $newName = [regex]::Replace($name, '\[\d+(?:[,\-–]\d+)*\]', '')
    $newName = [regex]::Replace($newName, '[\[\]\(\)\?#%:*"<>\|]', '_')
    $newName = ($newName -replace '\s+', ' ').Trim()
    if ($newName -eq $name) { continue }
    $dst = Join-Path $dir $newName
    if (Test-Path -LiteralPath $dst) { [void]$log.Add("CONFLICT`t$rel`t$newName"); continue }
    Rename-Item -LiteralPath $src -NewName $newName
    $newRel = $rel.Substring(0, $rel.Length - $name.Length) + $newName
    $text = $text.Replace("]($rel)", "]($newRel)")
    [void]$log.Add("RENAME`t$rel`t$newName")
  }
  foreach ($rel in $missing) {
    $pat = '!\[[^\]]*\]\(' + [regex]::Escape($rel) + '\)'
    $n = ([regex]::Matches($text, $pat)).Count
    $text = [regex]::Replace($text, $pat, '')
    [void]$log.Add("DEL_LINK`t$rel`t$n")
  }
  [IO.File]::WriteAllText($mdPath, $text, (New-Object Text.UTF8Encoding $true))
}

$refs2 = Get-Refs ([IO.File]::ReadAllText($mdPath, [Text.Encoding]::UTF8))
$left = 0; $ok = 0
foreach ($t in $refs2) {
  $v = Test-Link $t
  if ($v -eq 'ok' -or $v -eq 'skip') { $ok++ } elseif ($v -eq 'missing' -or $v -eq 'bad') { $left++ }
}
$msg = "SELFCHECK refs=$($refs2.Count) ok=$ok unresolved=$left fixed=$($log.Count)"
Write-Host $msg
foreach ($l in $log) { Write-Host "  $l" }
if ($ReportOut -and $log.Count -gt 0) {
  $log2 = @($msg) + $log
  [IO.File]::WriteAllLines($ReportOut, $log2, (New-Object Text.UTF8Encoding $true))
}
if ($left -gt 0) { exit 1 } else { exit 0 }