#requires -Version 5.1
<#
  catalog.ps1 — 从 20-md 的 frontmatter 重建 30-wiki 下三件套：
                manifest.csv（清单）、catalog.md（书目）、todo.md（待确认）。
  本脚本是这三处的唯一写入者；幂等，可反复跑。
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$ToolDir = Split-Path -Parent $PSScriptRoot
$Root    = Split-Path -Parent $ToolDir
$MdRoot  = Join-Path $Root '20-md'
$Idx     = Join-Path $Root '30-wiki'
$Pending = Join-Path $Idx 'pending.json'
if (-not (Test-Path -LiteralPath $Idx)) { New-Item -ItemType Directory -Force -Path $Idx | Out-Null }

$verFile = Join-Path $ToolDir 'VERSION'
$RulesVer = if (Test-Path -LiteralPath $verFile) { (Get-Content -LiteralPath $verFile -Raw).Trim() } else { '?' }

function Read-FrontMatter([string]$path) {
    $lines = [IO.File]::ReadAllLines($path, [Text.Encoding]::UTF8)
    if ($lines.Count -lt 3) { return $null }
    if ($lines[0].Trim() -ne '---') { return $null }
    $h = @{}
    $i = 1
    while ($i -lt $lines.Count -and $lines[$i].Trim() -ne '---') {
        $l = $lines[$i]
        if ($l -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$') {
            $k = $Matches[1]
            $v = $Matches[2].Trim()
            if ($v.Length -ge 2 -and $v.StartsWith('"') -and $v.EndsWith('"')) {
                $v = $v.Substring(1, $v.Length - 2)
                $v = $v -replace '\\"', '"' -replace '\\\\', '\'
            }
            $h[$k] = $v
        }
        $i++
    }
    return $h
}

$KindOrder = @{ 'book' = 1; 'standard' = 2; 'paper' = 3; 'project' = 4; 'web' = 5; 'other' = 6 }
$KindLabel = @{ 'book' = '教材 / 图书'; 'standard' = '标准规范'; 'paper' = '论文'; 'project' = '项目资料'; 'web' = '网页存档'; 'other' = '其他' }
$LayerLabel = @{ '(扁平)' = '未分组（扁平）'; 'NA' = '未分组（扁平）' }
function Get-Layer([string]$relMd) {
    $p = ($relMd -replace '^20-md/', '') -split '/'
    if ($p.Count -ge 3) { return (($p[0..($p.Count - 2)]) -join '/') }
    return '(扁平)'
}

$docs = New-Object System.Collections.ArrayList
$notes = 0
$bad = New-Object System.Collections.ArrayList

if (Test-Path -LiteralPath $MdRoot) {
    foreach ($f in Get-ChildItem -LiteralPath $MdRoot -Recurse -File -Filter *.md -ErrorAction SilentlyContinue) {
        $fm = Read-FrontMatter $f.FullName
        if (-not $fm) { [void]$bad.Add($f.FullName); continue }
        if ($fm['kind'] -eq 'note') { $notes++; continue }
        $rel = ($f.FullName.Substring($Root.Length + 1)) -replace '\\', '/'
        $layer = Get-Layer $rel
        $q = if ($fm['quality']) { $fm['quality'] } else { 'ok' }
        $st = if ($q -eq 'ok' -or $q -eq 'warn') { 'ok' } else { 'quarantine' }
        [void]$docs.Add([pscustomobject]@{
            id       = $fm['id']
            title    = if ($fm['title']) { $fm['title'] } else { 'NA' }
            authors  = if ($fm['authors']) { $fm['authors'] } else { 'NA' }
            edition  = if ($fm['edition']) { $fm['edition'] } else { 'NA' }
            year     = $fm['year']
            kind     = if ($fm['kind']) { $fm['kind'] } else { 'book' }
            topic    = if ($fm['topic']) { $fm['topic'] } else { 'NA' }
            layer    = $layer
            pages    = $fm['pages']
            ocr      = $fm['ocr']
            quality  = $q
            md       = $rel
            src      = $fm['src']
            sha256   = $fm['sha256']
            added    = $fm['added']
            status   = $st
            missing  = $fm['missing']
            bytes    = $f.Length
        })
    }
}

# ---------- manifest.csv ----------
$cols = @('id','title','authors','edition','year','kind','topic','pages','ocr','quality','md','src','sha256','added','status')
$manifest = Join-Path $Idx 'manifest.csv'
if ($docs.Count -eq 0) {
    ($cols -join ',') | Set-Content -LiteralPath $manifest -Encoding UTF8
} else {
    $docs | Sort-Object @{ Expression = { $KindOrder[$_.kind] } }, title |
        Select-Object $cols | Export-Csv -LiteralPath $manifest -NoTypeInformation -Encoding UTF8
}

# ---------- catalog.md ----------
$live = @($docs | Where-Object { $_.quality -ne 'quarantine' })
$qdoc = @($docs | Where-Object { $_.quality -eq 'quarantine' })
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('# 书目')
[void]$sb.AppendLine('')
[void]$sb.AppendLine(("> 由 catalog.ps1 自动生成，请勿手改；规则 v{0}；更新时间 {1}；可检索 **{2}** 本，隔离 {3} 份，另有 {4} 篇项目笔记未列入。" -f $RulesVer, (Get-Date -Format 'yyyy-MM-dd HH:mm'), $live.Count, $qdoc.Count, $notes))
[void]$sb.AppendLine('')
if ($live.Count -eq 0) {
    [void]$sb.AppendLine('暂无。把文件放进 `00-inbox`，然后双击 `90-tool\run-ingest.bat`。')
} else {
    foreach ($k in @('book','standard','paper','project','web','other')) {
        $group = @($docs | Where-Object { $_.kind -eq $k -and $_.quality -ne 'quarantine' })
        if ($group.Count -eq 0) { continue }
        [void]$sb.AppendLine("## $($KindLabel[$k])（$($group.Count)）")
        [void]$sb.AppendLine('')
        foreach ($t in ($group | Group-Object layer | Sort-Object Name)) {
            $tl = if ($LayerLabel[$t.Name]) { $LayerLabel[$t.Name] } else { $t.Name }
            [void]$sb.AppendLine("### $tl（$($t.Count)）")
            [void]$sb.AppendLine('')
            [void]$sb.AppendLine('| 书名 | 作者 | 版次 | 年份 | 质量 | 文本 |')
            [void]$sb.AppendLine('|:---|:---|:---:|---:|:---|:---|')
            foreach ($d in ($t.Group | Sort-Object title)) {
                $link = "[打开](../{0})" -f $d.md
                $qflag = if ($d.quality -eq 'ok') { 'ok' } elseif ($d.quality -eq 'warn') { '注意' } else { '**隔离**' }
                [void]$sb.AppendLine("| $($d.title) | $($d.authors) | $($d.edition) | $($d.year) | $qflag | $link |")
            }
            [void]$sb.AppendLine('')
        }
    }
}
if ($qdoc.Count -gt 0) {
    [void]$sb.AppendLine("## 隔离区（$($qdoc.Count)）")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('> 质检不合格，不列入上表，也不要交给我入检索索引。修好后重跑 ingest 或手工改 md 里的 `quality:` 字段。')
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('| 书名 | 作者 | 版次 | 年份 | 文本 |')
    [void]$sb.AppendLine('|:---|:---|:---:|---:|:---|')
    foreach ($d in ($qdoc | Sort-Object title)) {
        $link = "[打开](../{0})" -f $d.md
        [void]$sb.AppendLine("| $($d.title) | $($d.authors) | $($d.edition) | $($d.year) | $link |")
    }
    [void]$sb.AppendLine('')
}
[IO.File]::WriteAllText((Join-Path $Idx 'catalog.md'), $sb.ToString(), (New-Object Text.UTF8Encoding $false))

# ---------- todo.md ----------
$tb = New-Object System.Text.StringBuilder
[void]$tb.AppendLine('# 待确认')
[void]$tb.AppendLine('')
[void]$tb.AppendLine(("> 生成时间 {0}。删行无效：本文件每次跑 catalog.ps1 都会按现状重算，只有修掉根因（补元数据/重解析/改图名）那一项才会消失。" -f (Get-Date -Format 'yyyy-MM-dd HH:mm')))
[void]$tb.AppendLine('')

# 1 元数据缺失
$missGroup = @($docs | Where-Object { $_.missing -and $_.missing.Trim() -ne '' })
[void]$tb.AppendLine("## 1. 元数据缺失（$($missGroup.Count)）")
[void]$tb.AppendLine('')
if ($missGroup.Count -eq 0) { [void]$tb.AppendLine('无。') }
else {
    foreach ($d in $missGroup) {
        [void]$tb.AppendLine(("- 《{0}》缺 {1} —— {2}" -f $d.title, $d.missing, $d.md))
    }
    [void]$tb.AppendLine('')
    [void]$tb.AppendLine('> 补法：打开该 md，改顶部 frontmatter 对应字段（缺的写 `NA`，补上真值即可），然后重跑 catalog.ps1；或直接在 `manifest.csv` 里改完另存。')
}
[void]$tb.AppendLine('')

# 2 质量隔离
$quar = @($docs | Where-Object { $_.quality -eq 'quarantine' })
[void]$tb.AppendLine("## 2. 质量隔离（$($quar.Count)）")
[void]$tb.AppendLine('')
if ($quar.Count -eq 0) { [void]$tb.AppendLine('无。') }
else {
    foreach ($d in $quar) {
        [void]$tb.AppendLine(("- 《{0}》 → {1}" -f $d.title, $d.md))
    }
    [void]$tb.AppendLine('')
    [void]$tb.AppendLine('> 多为扫描件无文字层或编码损坏。换 `--tier advanced` 重跑该文件，或先人工 OCR 后再放回 `00-inbox`（会因内容不同视为新文档）。')
}
[void]$tb.AppendLine('')

# 3 待解析
$pend = @()
if (Test-Path -LiteralPath $Pending) {
    try {
        $raw = Get-Content -LiteralPath $Pending -Raw -Encoding UTF8 | ConvertFrom-Json
        $pend = @($raw)
    } catch { $pend = @() }
}
[void]$tb.AppendLine("## 3. 待解析（$($pend.Count)）")
[void]$tb.AppendLine('')
if ($pend.Count -eq 0) { [void]$tb.AppendLine('无。') }
else {
    foreach ($p in $pend) {
        [void]$tb.AppendLine(("- `{0}` —— {1}" -f $p.file, $p.reason))
    }
    [void]$tb.AppendLine('')
    [void]$tb.AppendLine('> 需要 MinerU：`uv venv` 后 `uv pip install -U "mineru>=4.0,<5"`；装好后重跑 ingest.ps1。')
}
[void]$tb.AppendLine('')

# 4 层级体检（v2.0：N<20 扁平；20~40 可分组；>40 必须分组，每层 <=40）
$N = $docs.Count
$depth = 1
while ([math]::Pow(40, $depth) -lt $N) { $depth++ }
$over = @(Get-ChildItem -LiteralPath $MdRoot -Directory -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
    $c = @(Get-ChildItem -LiteralPath $_.FullName -Directory -ErrorAction SilentlyContinue).Count
    if ($c -gt 40) { [pscustomobject]@{ Dir = ($_.FullName.Substring($Root.Length + 1)); Children = $c } }
})
$flat = @($docs | Where-Object { $_.layer -eq '(扁平)' })
[void]$tb.AppendLine("## 4. 层级体检（入库夹 N = $N，所需层数 $depth，单夹上限 40）")
[void]$tb.AppendLine('')
if ($N -lt 20) {
    [void]$tb.AppendLine("- 结论：N < 20，保持扁平，无需分类夹。当前扁平 $($flat.Count) 个。")
} elseif ($N -le 40) {
    [void]$tb.AppendLine("- 结论：20 <= N <= 40，可按主题分组；某主题 >= 3 个入库夹时再建分类夹（当前扁平 $($flat.Count) 个）。")
} else {
    [void]$tb.AppendLine("- 结论：N > 40，**必须分组**，收敛到每层 <= 40、层数 >= $depth。当前扁平 $($flat.Count) 个待归并。")
}
if ($over.Count -gt 0) {
    [void]$tb.AppendLine('')
    [void]$tb.AppendLine('- **超限文件夹（>40 个子文件夹，必须拆）**：')
    foreach ($o in $over) { [void]$tb.AppendLine(("  - {0} —— {1} 个" -f $o.Dir, $o.Children)) }
}
[void]$tb.AppendLine('')
[void]$tb.AppendLine('> 重排归 DSH 做（外部 agent 只决定自己这一本放哪）；挪完文件夹必须重跑 catalog.ps1。')
[void]$tb.AppendLine('')

# 5 体积超限
$big = @($docs | Where-Object { $_.bytes -gt 5242880 })
[void]$tb.AppendLine("## 5. 体积超限（$($big.Count)）")
[void]$tb.AppendLine('')
if ($big.Count -eq 0) { [void]$tb.AppendLine('无。') }
else {
    foreach ($d in $big) {
        [void]$tb.AppendLine(("- 《{0}》 {1:N1} MB —— {2}" -f $d.title, ($d.bytes / 1MB), $d.md))
    }
    [void]$tb.AppendLine('')
    [void]$tb.AppendLine('> 超过 5MiB 无法直接进检索索引，需按篇拆成多个 md。')
}
[void]$tb.AppendLine('')

# 6 无 frontmatter
[void]$tb.AppendLine("## 6. 缺少 frontmatter（$($bad.Count)）")
[void]$tb.AppendLine('')
if ($bad.Count -eq 0) { [void]$tb.AppendLine('无。') }
else {
    foreach ($b in $bad) { [void]$tb.AppendLine(("- {0}" -f ($b.Substring($Root.Length + 1)))) }
}
[void]$tb.AppendLine('')

# 7 图链体检（md 里指向不存在文件的图片链接）
$dead = @()
Get-ChildItem -LiteralPath $MdRoot -Recurse -Filter '*.md' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\_quarantine\\' } | ForEach-Object {
    $t = [IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8)
    $n = 0
    foreach ($m in [regex]::Matches($t, '!\[[^\]]*\]\((图片/[^)]+)\)')) {
        $rel = [Uri]::UnescapeDataString($m.Groups[1].Value)
        if (-not (Test-Path -LiteralPath (Join-Path $_.DirectoryName $rel))) { $n++ }
    }
    if ($n -gt 0) { $dead += [pscustomobject]@{ Book = $_.BaseName; Count = $n } }
}
[void]$tb.AppendLine("## 7. 图链体检（$($dead.Count)）")
[void]$tb.AppendLine('')
if ($dead.Count -eq 0) { [void]$tb.AppendLine('无缺图链接。') }
else {
    foreach ($x in $dead) { [void]$tb.AppendLine(("- 《{0}》 {1} 条死链" -f $x.Book, $x.Count)) }
    [void]$tb.AppendLine('')
    [void]$tb.AppendLine('> 修复：check-links.ps1 -Md <md> -Fix（删死链、清坏字符名）；缺的图按页重解析补齐。')
}
[void]$tb.AppendLine('')

# 8 规则缺口
[void]$tb.AppendLine('## 8. 规则缺口')
[void]$tb.AppendLine('')
[void]$tb.AppendLine('（执行者遇到 `rules.md` 没写到的情况，写在这里；没有就写"无"。）')
[void]$tb.AppendLine('')

[IO.File]::WriteAllText((Join-Path $Idx 'todo.md'), $tb.ToString(), (New-Object Text.UTF8Encoding $false))

Write-Host ("书目已更新：{0} 本 · 笔记 {1} 篇 · 待确认 {2} 项" -f $docs.Count, $notes, ($missGroup.Count + $quar.Count + $pend.Count + $misc.Count + $big.Count + $bad.Count)) -ForegroundColor Green
