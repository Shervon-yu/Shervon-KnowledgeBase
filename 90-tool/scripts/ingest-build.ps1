# ingest-build.ps1 —— 一条命令把 MinerU 解析产物变成合格的 20-md（含验收）
#
# 用法：
#   powershell -NoProfile -ExecutionPolicy Bypass -File "90-tool\scripts\ingest-build.ps1" -Book "化工原理_王志魁_第5版_NA"
#   ... -Book <入库夹名> [-ZipDir <解析产物目录>] [-SkipCreate] [-Force]
#
# 做的事（对应 rules.md §16）：
#   1) md-build.py write <入库夹名>   —— 按页序重建 md：<!-- page: N --> 锚点、$$ 公式、pipe 表格、图链与图题、保留 frontmatter
#   2) fig-names.py apply <入库夹名>   —— 无图题图定名：方形小图判二维码、其余挂同页图题
#   3) md-build.py prune            —— 把 md 未引用的历史图移到 40-new\_acl\orphan-images（可回滚，不删）
#   4) check-links.ps1               —— 图链自检必须 unresolved=0
#   5) md-build.py verify            —— 标题体检：粗体假标题 / 整族标题没生成 / 漏章漏附录 / 孤立层级
#   6) 验收打印                      —— 锚点数 / 公式数 / 表格数 / 图链数 / frontmatter / 标题体检
# 任何一步失败即退出非 0；不静默降级。

param(
    [Parameter(Mandatory = $true)][string]$Book,
    [string]$ZipDir = "",
    [switch]$SkipCreate,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
# MinerU 解析出的中文经 python 输出时是 UTF-8，不设这两行控制台会显示乱码
$env:PYTHONIOENCODING = 'utf-8'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$scripts = Split-Path -Parent $PSCommandPath
$root = Split-Path -Parent (Split-Path -Parent $scripts)
$py = 'C:\Users\shervon\.local\mineru\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }
$md = Join-Path $root "20-md\$Book\$Book.md"
$img = Join-Path $root "20-md\$Book\图片"

if (-not (Test-Path $md)) { throw "找不到 md：$md（先用 ingest.ps1 解析并建夹）" }

$zipArgs = @()
if ($ZipDir) { $zipArgs = @('--zipdir', $ZipDir) }
# 守卫：md 已是生成版（有页码锚点且无页码式图名）时，重建会把人工定好的图名打回页码名 → 必须显式 -Force
$skipCreate = $SkipCreate
if (-not $skipCreate -and -not $Force -and (Test-Path $md)) {
    $pre = Get-Content -Raw -Encoding UTF8 $md
    $preAnchors = ([regex]::Matches($pre, '(?m)^<!-- page: \d+ -->')).Count
    $prePageNames = ([regex]::Matches($pre, '图_第\d+页_')).Count
    if ($preAnchors -ge 10 -and $prePageNames -eq 0) {
        Write-Host "== 1/6 跳过重建（md 已是生成版：锚点 $preAnchors、无页码式图名；重建会打回人工图名，确需重建加 -Force）"
        $skipCreate = $true
    }
}
if (-not $skipCreate) {
    Write-Host "== 1/6 重建 md：$Book"
    & $py (Join-Path $scripts 'md-build.py') write $Book @zipArgs
    if ($LASTEXITCODE -ne 0) { throw "md-build 失败（exit $LASTEXITCODE）" }
}

Write-Host "== 2/6 图名定名"
& $py (Join-Path $scripts 'fig-names.py') apply $Book
if ($LASTEXITCODE -ne 0) { throw "fig-names 失败（exit $LASTEXITCODE）" }

Write-Host "== 3/6 归档未引用图片（移到 40-new\_acl\orphan-images）"
& $py (Join-Path $scripts 'md-build.py') prune $Book
if ($LASTEXITCODE -ne 0) { throw "prune 失败（exit $LASTEXITCODE）" }

Write-Host "== 4/6 图链自检"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $scripts 'check-links.ps1') -Md $md
if ($LASTEXITCODE -ne 0) { throw "check-links 未通过（exit $LASTEXITCODE）" }

Write-Host "== 5/6 标题体检"
$titOut = & $py (Join-Path $scripts 'md-build.py') verify $Book 2>&1
$titleOk = ($LASTEXITCODE -eq 0)
$titOut | ForEach-Object { Write-Host $_ }
Write-Host ("   标题体检：" + $(if ($titleOk) { 'OK' } else { 'FAIL' }))

Write-Host "== 6/6 验收"
$text = Get-Content -Raw -Encoding UTF8 $md
$anchors = ([regex]::Matches($text, '(?m)^<!-- page: \d+ -->')).Count
$eqs = ([regex]::Matches($text, '(?m)^\$\$ ')).Count
$tables = ([regex]::Matches($text, '(?m)^\|.*\|$')).Count
$links = ([regex]::Matches($text, '!\[\]\(图片/[^)]+\.jpg\)')).Count
$imgs = (Get-ChildItem $img -File -ErrorAction SilentlyContinue).Count
$hasFm = $text.StartsWith('---')
$pageNames = ([regex]::Matches($text, '图_第\d+页_')).Count

$rows = @(
    [pscustomobject]@{ 项 = '页码锚点 <!-- page: N -->'; 值 = $anchors; 要求 = '= PDF 页数' }
    [pscustomobject]@{ 项 = '独立公式 $$ ... $$'; 值 = $eqs; 要求 = '> 0（教材）' }
    [pscustomobject]@{ 项 = 'pipe 表格行'; 值 = $tables; 要求 = '> 0（有表即需）' }
    [pscustomobject]@{ 项 = '图链'; 值 = $links; 要求 = '= 图片文件数' }
    [pscustomobject]@{ 项 = '图片文件'; 值 = $imgs; 要求 = '= 图链数' }
    [pscustomobject]@{ 项 = 'YAML frontmatter'; 值 = $hasFm; 要求 = 'True' }
    [pscustomobject]@{ 项 = '未定名图（图_第NN页_）'; 值 = $pageNames; 要求 = '0' }
    [pscustomobject]@{ 项 = '标题体检（假标题/漏章）'; 值 = $(if ($titleOk) { 'OK' } else { 'FAIL' }); 要求 = 'OK' }
)
$rows | Format-Table -AutoSize

$bad = @()
if ($links -ne $imgs) { $bad += "图链($links) ≠ 图片($imgs)" }
if (-not $hasFm) { $bad += "缺 frontmatter" }
if ($pageNames -gt 0) { $bad += "还有 $pageNames 张页码式图名（看 fig-names dry 报告，按 rules §16 人工补）" }
if (-not $titleOk) { $bad += "标题体检未通过（见上：粗体假标题/整族标题缺失；按 rules §16 第 7 条补标题后重跑）" }
if ($bad.Count -gt 0) {
    Write-Host ("验收未通过：" + ($bad -join '；')) -ForegroundColor Red
    exit 2
}
Write-Host "验收通过：锚点 $anchors / 公式 $eqs / 图链 $links / 标题 OK" -ForegroundColor Green
exit 0
