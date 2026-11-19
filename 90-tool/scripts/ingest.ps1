#requires -Version 5.1
<#
  ingest.ps1  —  知识库入库主脚本 v2.0（规则见 ..\rules.md）

  输入约定：00-inbox 下每个【子文件夹】= 一本书 / 一份资料的入库单元。
            会话开始新建一个文件夹（名字建议 书名_作者_版次_年份），
            把这本书的 PDF / 图片 / docx 全丢进去，然后执行本脚本。

  用法：
    powershell -NoProfile -ExecutionPolicy Bypass -File ingest.ps1 -Preview
    powershell -NoProfile -ExecutionPolicy Bypass -File ingest.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File ingest.ps1 -Layer 机械

  v2.0：默认扁平放 20-md\<入库夹>；20-md 入库夹数 N>=20 时按 rules.md 第 4 节
        自动复用/新建分类夹；N>40 必须分组，可用 -Layer 指定（如 -Layer 机械\泵）。
#>
[CmdletBinding()]
param(
    [switch]$Preview,
    [ValidateSet('flash','standard','basic','advanced')]
    [string]$Tier = 'standard',
    [string]$Layer = ''
)

$ErrorActionPreference = 'Stop'

# ---------- 路径 ----------
$ToolDir  = Split-Path -Parent $PSScriptRoot
$Root     = Split-Path -Parent $ToolDir
$Inbox    = Join-Path $Root '00-inbox'
$LockFile = Join-Path $Root '40-new\.ingest.lock'
if (-not $Preview) {
    if (Test-Path -LiteralPath $LockFile) {
        Write-Host "已有入库任务在跑（$LockFile），本次退出。" -ForegroundColor Red
        exit 1
    }
    New-Item -ItemType File -Path $LockFile -Force | Out-Null
}
$SrcRoot  = Join-Path $Root '10-source'
$MdRoot   = Join-Path $Root '20-md'
$Idx      = Join-Path $Root '30-wiki'
$Quar     = Join-Path $MdRoot '_quarantine'
$NewRoot  = Join-Path $Root '40-new'
$Manifest = Join-Path $Idx 'manifest.csv'
$Issues   = Join-Path $Idx 'issues.log'
$Pending  = Join-Path $Idx 'pending.json'

foreach ($d in @($Inbox, $SrcRoot, $MdRoot, $Idx, $Quar, $NewRoot)) {
    if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

$verFile = Join-Path $ToolDir 'VERSION'
$RulesVer = if (Test-Path -LiteralPath $verFile) { (Get-Content -LiteralPath $verFile -Raw).Trim() } else { '?' }
$modeText = if ($Preview) { '预览模式（不会改动任何文件）' } else { '执行模式' }
Write-Host "规则版本 v$RulesVer  |  解析档位 $Tier  |  $modeText" -ForegroundColor Cyan

# ---------- 层级：v2.0 扁平优先 + 阈值分组（rules.md 第 4 节） ----------
function Get-IngestFolders {
    # 入库夹 = 直接含 <同名>.md 的文件夹
    $res = New-Object System.Collections.ArrayList
    if (-not (Test-Path -LiteralPath $MdRoot)) { return @() }
    foreach ($d in Get-ChildItem -LiteralPath $MdRoot -Directory -Recurse -ErrorAction SilentlyContinue) {
        if ($d.Name -eq '_quarantine') { continue }
        if (Test-Path -LiteralPath (Join-Path $d.FullName ($d.Name + '.md'))) { [void]$res.Add($d) }
    }
    return @($res)
}

function Get-CategoryDirs {
    if (-not (Test-Path -LiteralPath $MdRoot)) { return @() }
    return @(Get-ChildItem -LiteralPath $MdRoot -Directory -ErrorAction SilentlyContinue |
             Where-Object { $_.Name -notlike '_*' -and -not (Test-Path -LiteralPath (Join-Path $_.FullName ($_.Name + '.md'))) })
}

$TopicKw = [ordered]@{
    '机械' = @('机械','传动','齿轮','轴承','联轴器','密封','机构')
    '流体' = @('泵','阀','流体','传热','热工','液压','风机','冷却')
    '材料' = @('材料','钢','合金','热处理','腐蚀','强度')
    '制造' = @('工艺','加工','焊接','铸造','装配','公差')
    '电气' = @('电机','电气','变频','PLC','控制','仪表','传感')
    '数理' = @('数学','力学','有限元','振动','优化','统计')
    '标准' = @('GB','JB','ISO','DIN','ASTM','标准','规范')
    '论文' = @('论文','paper','DOI','学位','期刊')
    '项目' = @('项目','计算书','图纸','报价','方案')
}

function Resolve-Layer([string]$bookName, [string[]]$fileNames, [int]$N) {
    if ($Layer) { return (($Layer -split '[\\/]+' | Where-Object { $_ }) -join '\') }
    $cats = Get-CategoryDirs
    $hay  = $bookName + ' ' + ($fileNames -join ' ')
    foreach ($c in $cats) {
        if ($hay.IndexOf($c.Name, [StringComparison]::OrdinalIgnoreCase) -ge 0) { return $c.Name }
    }
    $best = ''; $bestScore = 0
    foreach ($k in $TopicKw.Keys) {
        $s = 0
        foreach ($w in $TopicKw[$k]) { if ($hay.IndexOf($w, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $s++ } }
        if ($s -gt $bestScore) { $bestScore = $s; $best = $k }
    }
    if ($bestScore -eq 0) { return '' }
    foreach ($c in $cats) { if ($c.Name -eq $best) { return $best } }
    if ($N -ge 20) { return $best }
    return ''
}

# ---------- 小工具 ----------
function Clean-Part([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return 'NA' }
    $s = $s.Trim()
    if ($s -eq 'NA') { return 'NA' }
    $s = $s -replace '[\\/:*?"<>|\r\n\t]', '-'
    $s = $s -replace '\s+', '-'
    $s = $s.Trim('-', '.')
    if ([string]::IsNullOrWhiteSpace($s)) { return 'NA' }
    return $s
}

# 文件名清理：保留中文与图号，去掉 Windows 非法字符与多余空白
function Clean-FileName([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return '未命名' }
    $s = $s -replace '\s*[（(]\s*([a-zA-Z0-9]{1,2})\s*[)）]\s*$', '_$1'
    $s = $s -replace '[（）()]', ' '
    $s = $s -replace '[*?:"<>|\\/\r\n\t]', ' '
    $s = $s -replace '\s+', ' '
    $s = $s.Trim(' ', '.', '-')
    if ($s.Length -gt 60) { $s = $s.Substring(0, 60).Trim() }
    if ([string]::IsNullOrWhiteSpace($s)) { return '未命名' }
    return $s
}

function Esc-Yaml([string]$v) {
    if ($null -eq $v) { return '' }
    return (($v -replace '\\', '\\') -replace '"', '\"')
}

function Get-Hash([string]$p) { return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower() }

function Get-HashFromString([string]$s) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($s)
        $h = $sha.ComputeHash($bytes)
        return (($h | ForEach-Object { $_.ToString('x2') }) -join '')
    } finally { $sha.Dispose() }
}

function Add-Issue([string]$msg) {
    Write-Host "  ! $msg" -ForegroundColor Yellow
    if (-not $Preview) {
        $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg
        Add-Content -LiteralPath $Issues -Value $line -Encoding UTF8
    }
}

function Get-FreePath([string]$dir, [string]$base, [string]$ext) {
    $p = Join-Path $dir ($base + $ext)
    if (-not (Test-Path -LiteralPath $p)) { return $p }
    for ($i = 2; $i -le 99; $i++) {
        $p = Join-Path $dir ("{0}_{1}{2}" -f $base, $i, $ext)
        if (-not (Test-Path -LiteralPath $p)) { return $p }
    }
    throw "同名冲突过多：$base"
}

function Count-Stat([hashtable]$s, [string]$key) { $s[$key] = 1 + [int]$s[$key] }

# ---------- 解析 ----------
function Find-Mineru {
    foreach ($n in @('mineru-kit', 'mineru')) {
        $c = Get-Command $n -ErrorAction SilentlyContinue
        if ($c) { return $c }
    }
    $cands = @(
        'C:\Users\shervon\.local\mineru\Scripts\mineru-kit.exe',
        (Join-Path $env:USERPROFILE '.local\mineru\Scripts\mineru-kit.exe')
    )
    foreach ($p in $cands) {
        if (Test-Path -LiteralPath $p) { return [pscustomobject]@{ Source = $p } }
    }
    return $null
}

function Invoke-Mineru([string]$filePath, [string]$tier) {
    $exe = Find-Mineru
    if (-not $exe) { return [pscustomobject]@{ Ok = $false; Error = '未找到 mineru-kit / mineru，MinerU 未安装'; Text = ''; WorkDir = '' } }
    $tmp = Join-Path $env:TEMP ('kb-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    $err = ''
    $errOut = ''
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $out = & $exe.Source parse $filePath -o $tmp --tier $tier --format zip 2>&1
        if ($LASTEXITCODE -ne 0) { $errOut = (($out | Out-String).Trim()) }
    } catch { $errOut = $_.Exception.Message }
    finally { $ErrorActionPreference = $prevEap }
    $text = ''
    $zip = Get-ChildItem -LiteralPath $tmp -Recurse -File -Filter *.zip -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($zip) {
        $x = Join-Path $tmp 'x'
        try {
            Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
            [IO.Compression.ZipFile]::ExtractToDirectory($zip.FullName, $x)
        } catch { $err = '解压 MinerU 结果失败：' + $_.Exception.Message }
        if (-not $err) {
            $md = Join-Path $x 'markdown.md'
            if (Test-Path -LiteralPath $md) {
                $text = [IO.File]::ReadAllText($md, [Text.Encoding]::UTF8)
                return [pscustomobject]@{ Ok = $true; Error = ''; Text = $text; WorkDir = $tmp; Zip = $zip.FullName }
            }
            $err = '解析未产出 markdown.md'
        }
    } elseif ($errOut) { $err = $errOut } else { $err = '解析未产出 zip' }
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    if ($err.Length -gt 400) { $err = $err.Substring(0, 400) }
    return [pscustomobject]@{ Ok = $false; Error = $err; Text = ''; WorkDir = ''; Zip = '' }
}

function Get-ZipEntryText([string]$zipPath, [string]$entryName) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
    $zip = [IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        $norm = $entryName -replace '\\', '/'
        $e = @($zip.Entries | Where-Object { ($_.FullName -replace '\\', '/') -eq $norm })
        if ($e.Count -eq 0) { return $null }
        $sr = New-Object IO.StreamReader($e[0].Open(), [Text.Encoding]::UTF8)
        try { return $sr.ReadToEnd() } finally { $sr.Dispose() }
    } finally { $zip.Dispose() }
}

function Convert-OfficeToText([string]$inPath) {
    $ext = [IO.Path]::GetExtension($inPath).ToLower()
    try {
        if ($ext -eq '.docx' -or $ext -eq '.docm') {
            $xml = Get-ZipEntryText $inPath 'word/document.xml'
            if (-not $xml) { return $null }
            $xml = $xml -replace '</w:p>', "`r`n"
            $xml = $xml -replace '<w:tab[^>]*/>', "`t"
            $xml = $xml -replace '<w:br[^>]*/>', "`r`n"
            $txt = [regex]::Replace($xml, '<[^>]+>', '')
            $txt = [Net.WebUtility]::HtmlDecode($txt)
            $txt = $txt -replace '(\r?\n){3,}', "`r`n`r`n"
            return $txt.Trim()
        }
        if ($ext -eq '.pptx' -or $ext -eq '.pptm') {
            Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
            $zip = [IO.Compression.ZipFile]::OpenRead($inPath)
            $sb = New-Object System.Text.StringBuilder
            try {
                $entries = @($zip.Entries | Where-Object { ($_.FullName -replace '\\', '/') -match '^ppt/slides/slide[0-9]+\.xml$' })
                $entries = @($entries | Sort-Object { [int]([regex]::Match($_.FullName, 'slide([0-9]+)\.xml').Groups[1].Value) })
                $n = 0
                foreach ($e in $entries) {
                    $n = $n + 1
                    $sr = New-Object IO.StreamReader($e.Open(), [Text.Encoding]::UTF8)
                    $xml = $sr.ReadToEnd()
                    $sr.Dispose()
                    [void]$sb.AppendLine("## 第 $n 页")
                    foreach ($m in [regex]::Matches($xml, '<a:t>(.*?)</a:t>', 'Singleline')) {
                        [void]$sb.AppendLine([Net.WebUtility]::HtmlDecode($m.Groups[1].Value))
                    }
                    [void]$sb.AppendLine('')
                }
            } finally { $zip.Dispose() }
            return $sb.ToString().Trim()
        }
        if ($ext -eq '.xlsx' -or $ext -eq '.xlsm') {
            $xml = Get-ZipEntryText $inPath 'xl/sharedStrings.xml'
            if (-not $xml) { return $null }
            $sb = New-Object System.Text.StringBuilder
            foreach ($m in [regex]::Matches($xml, '<t[^>]*>(.*?)</t>', 'Singleline')) {
                [void]$sb.AppendLine([Net.WebUtility]::HtmlDecode($m.Groups[1].Value))
            }
            return $sb.ToString().Trim()
        }
    } catch { return $null }
    return $null
}

function Get-Quality([string]$text) {
    $len = ($text -replace '\s', '').Length
    $fffd = ([regex]::Matches($text, [string][char]0xFFFD)).Count
    $ratio = if ($text.Length -gt 0) { $fffd / [double]$text.Length } else { 1.0 }
    if ($len -lt 200) { return [pscustomobject]@{ Q = 'quarantine'; Reason = "有效字符数 $len < 200，疑似未解析出来" } }
    if ($ratio -gt 0.02) { return [pscustomobject]@{ Q = 'quarantine'; Reason = ("替换字符占 {0:P1} > 2%" -f $ratio) } }
    if ($len -lt 2000) { return [pscustomobject]@{ Q = 'warn'; Reason = "文本偏少（$len 字），请核对是否完整" } }
    return [pscustomobject]@{ Q = 'ok'; Reason = '' }
}

function Get-KindName([string]$hay) {
    if ($hay -match '\.html?$|网页|抓取') { return 'web' }
    if ($hay -match '标准|规范|GB|JB|ISO|DIN|ASTM') { return 'standard' }
    if ($hay -match '论文|paper|DOI|学位|期刊') { return 'paper' }
    if ($hay -match '项目|计算书|图纸|报价|方案') { return 'project' }
    return 'book'
}

# ---------- 图示处理 ----------
# 在图片所在行前后 3 行内找 "图3.1 说明" / "图3-1 说明" 作文件名；找不到用 未命名图N
function Get-FigureCaption([string[]]$lines, [int]$imgLine) {
    $lo = [Math]::Max(0, $imgLine - 3)
    $hi = [Math]::Min($lines.Count - 1, $imgLine + 3)
    for ($i = $lo; $i -le $hi; $i++) {
        if ($i -eq $imgLine) { continue }
        $m = [regex]::Match($lines[$i], '图\s*\d+[\-\.．]\d+[^\r\n]{0,40}')
        if ($m.Success) { return $m.Value.Trim() }
    }
    $m2 = [regex]::Match($lines[$imgLine], '图\s*\d+[\-\.．]\d+[^\r\n]{0,40}')
    if ($m2.Success) { return $m2.Value.Trim() }
    return $null
}

# 把 md 里的图片复制到 destDir，按图号+说明重命名，并改写链接为相对名
function Import-Figures([string]$mdText, [string]$workDir, [string]$destDir) {
    $pattern = '!\[([^\]]*)\]\(([^)]+)\)'
    $ms = [regex]::Matches($mdText, $pattern)
    if ($ms.Count -eq 0) { return $mdText }
    $lines = $mdText -split "`r?`n"
    $figNo = 0
    $imgDir = Join-Path $destDir '图片'
    if (-not $Preview) { New-Item -ItemType Directory -Force -Path $imgDir | Out-Null }
    foreach ($m in $ms) {
        $raw = $m.Groups[2].Value
        $cand = $null
        $p1 = Join-Path $workDir ($raw -replace '/', '\')
        if (Test-Path -LiteralPath $p1) { $cand = $p1 }
        if (-not $cand) {
            $leaf = Split-Path $raw -Leaf
            $found = Get-ChildItem -LiteralPath $workDir -Recurse -File -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name -eq $leaf } | Select-Object -First 1
            if ($found) { $cand = $found.FullName }
        }
        if (-not $cand) { continue }
        $figNo = $figNo + 1
        $imgLine = 0
        for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i].Contains($m.Value)) { $imgLine = $i; break } }
        $cap = Get-FigureCaption $lines $imgLine
        if (-not $cap) { $cap = "未命名图$figNo" }
        $ext = [IO.Path]::GetExtension($cand)
        $base = Clean-FileName $cap
        $dest = Get-FreePath $imgDir $base $ext
        if (-not $Preview) { Copy-Item -LiteralPath $cand -Destination $dest }
        $newLink = "![$($m.Groups[1].Value)](图片/" + (Split-Path $dest -Leaf) + ")"
        $mdText = $mdText.Replace($m.Value, $newLink)
    }
    return $mdText
}

# ---------- 图示（按 middle_json 的图块 + 图题命名）----------
function Get-FigureList([string]$baseDir) {
    $list = New-Object System.Collections.ArrayList
    $mj = Join-Path $baseDir 'middle_json.json'
    if (-not (Test-Path -LiteralPath $mj)) { return $list }
    try { $doc = Get-Content -LiteralPath $mj -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $list }
    foreach ($pg in @($doc.pages)) {
        foreach ($blk in @($pg.blocks)) {
            if ($blk.type -ne 'image') { continue }
            $imgPath = $null
            $caps = New-Object System.Collections.ArrayList
            foreach ($ch in @($blk.content)) {
                if ($ch.type -eq 'image_body' -and $ch.image_path) { $imgPath = [string]$ch.image_path }
                if ($ch.type -eq 'image_caption') {
                    foreach ($t in @($ch.content)) {
                        if ($t.content) { [void]$caps.Add(([string]$t.content).Trim()) }
                    }
                }
            }
            if ($imgPath) {
                [void]$list.Add([pscustomobject]@{ Path = ($imgPath -replace '/', '\'); Caption = (($caps -join ' ').Trim()) })
            }
        }
    }
    return $list
}

# 文件名 = "图1.1 问题描述"
function Format-FigureName([string]$caption, [int]$index, [string]$ext) {
    $name = [string]$caption
    if ([string]::IsNullOrWhiteSpace($name)) { return ("未命名图{0}{1}" -f $index, $ext) }
    $name = [regex]::Replace($name, '图\s*(\d+)\s*[\-\.．]\s*(\d+)', '图$1.$2')
    $name = $name -replace '\s*[:：]\s*', ' '
    $name = Clean-FileName $name
    if ([string]::IsNullOrWhiteSpace($name)) { return ("未命名图{0}{1}" -f $index, $ext) }
    if ($name.Length -gt 60) { $name = $name.Substring(0, 60).Trim() }
    return ($name + $ext)
}

$script:FigHash = @{}
function Import-FiguresFromJson([string]$mdText, [string]$workDir, [string]$destDir) {
    $base = Join-Path $workDir 'x'
    $figs = Get-FigureList $base
    if ($figs.Count -eq 0) { return (Import-Figures $mdText $workDir $destDir) }
    $imgDir = Join-Path $destDir '图片'
    if (-not $Preview) { New-Item -ItemType Directory -Force -Path $imgDir | Out-Null }
    $i = 0
    foreach ($fg in $figs) {
        $i = $i + 1
        $src = Join-Path $base $fg.Path
        if (-not (Test-Path -LiteralPath $src)) { continue }
        $ext = [IO.Path]::GetExtension($src).ToLower()
        $fh = Get-Hash $src
        if ($script:FigHash.ContainsKey($fh)) {
            # 同字节重复图：不复制，引用直接指向已有文件
            $final = $script:FigHash[$fh]
            $rel0 = $fg.Path -replace '\\', '/'
            $mdText = $mdText.Replace('(' + $rel0 + ')', '(图片/' + $final + ')')
            $mdText = $mdText.Replace('(' + [IO.Path]::GetFileName($rel0) + ')', '(图片/' + $final + ')')
            continue
        }
        $name = Format-FigureName $fg.Caption $i $ext
        $dest = Get-FreePath $imgDir ([IO.Path]::GetFileNameWithoutExtension($name)) $ext
        $final = Split-Path $dest -Leaf
        if (-not $Preview) { Copy-Item -LiteralPath $src -Destination $dest }
        $script:FigHash[$fh] = $final
        $rel = $fg.Path -replace '\\', '/'
        $mdText = $mdText.Replace('(' + $rel + ')', '(图片/' + $final + ')')
        $mdText = $mdText.Replace('(' + [IO.Path]::GetFileName($rel) + ')', '(图片/' + $final + ')')
    }
    return $mdText
}

# ---------- 判重 ----------
$hashSeen = @{}
if (Test-Path -LiteralPath $Manifest) {
    try {
        Import-Csv -LiteralPath $Manifest -Encoding UTF8 | ForEach-Object {
            if ($_.sha256) { $hashSeen[$_.sha256.ToLower()] = $_.id }
        }
    } catch { Write-Host "清单读取失败，按空清单处理: $($_.Exception.Message)" -ForegroundColor Yellow }
}

# ---------- 主循环：一个子文件夹 = 一本书 ----------
$books = @(Get-ChildItem -LiteralPath $Inbox -Directory -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -notlike '.*' -and $_.Name -notlike '_*' -and $_.Name -ne '_quarantine' })
$loose = @(Get-ChildItem -LiteralPath $Inbox -File -ErrorAction SilentlyContinue |
           Where-Object { $_.Name -notlike '.*' -and $_.Name -notlike '~$*' })

foreach ($lf in $loose) {
    Add-Issue ("散文件「{0}」未处理：一本教材请新建一个文件夹，把该书所有文件放进去" -f $lf.Name)
}

Write-Host "`n00-inbox 中待处理：$($books.Count) 个文件夹`n" -ForegroundColor Cyan
if ($books.Count -eq 0) { Write-Host "没有待处理文件夹。" -ForegroundColor Green; return }

$stat = @{ ok = 0; quarantine = 0; duplicate = 0; pending = 0; failed = 0 }
$pendList = New-Object System.Collections.ArrayList
$plan = New-Object System.Collections.ArrayList

foreach ($book in $books) {
    $bookName = $book.Name
    Write-Host ("→ {0}" -f $bookName) -ForegroundColor White

    $files = @(Get-ChildItem -LiteralPath $book.FullName -Recurse -File -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -notlike '.*' -and $_.Name -notlike '~$*' } |
               Sort-Object Name)
    if ($files.Count -eq 0) { Add-Issue "$bookName ：文件夹是空的"; continue }

    # 书级指纹 = 各文件 hash 拼接后的 hash
    $hashes = @($files | ForEach-Object { Get-Hash $_.FullName })
    $bookHash = (Get-HashFromString (($hashes | Sort-Object) -join '|'))
    if ($hashSeen.ContainsKey($bookHash)) {
        Write-Host "  跳过：与已入库文档内容相同（id=$($hashSeen[$bookHash])）" -ForegroundColor DarkGray
        Count-Stat $stat 'duplicate'
        continue
    }

    $parts = $bookName -split '_'
    $title   = Clean-Part $parts[0]
    $author  = if ($parts.Count -ge 2) { Clean-Part $parts[1] } else { 'NA' }
    $edition = if ($parts.Count -ge 3) { Clean-Part $parts[2] } else { 'NA' }
    $year    = if ($parts.Count -ge 4) { Clean-Part $parts[3] } else { 'NA' }
    $missing = @()
    if ($author -eq 'NA')  { $missing += 'authors' }
    if ($edition -eq 'NA') { $missing += 'edition' }
    if ($year -eq 'NA')    { $missing += 'year' }

    $N = (Get-IngestFolders).Count
    $layerRel = Resolve-Layer $bookName @($files | ForEach-Object { $_.Name }) $N
    if ($N -gt 40 -and -not $layerRel) {
        Add-Issue "$bookName ：20-md 已有 $N 个入库夹（>40），按规则必须分组，请用 -Layer 指定分类夹"
    }
    $srcDir = if ($layerRel) { Join-Path (Join-Path $SrcRoot $layerRel) $bookName } else { Join-Path $SrcRoot $bookName }
    $mdDir  = if ($layerRel) { Join-Path (Join-Path $MdRoot  $layerRel) $bookName } else { Join-Path $MdRoot  $bookName }
    $topicVal = if ($layerRel) { ($layerRel -split '\\')[-1] } else { 'NA' }
    $id = $bookHash.Substring(0, [Math]::Min(12, $bookHash.Length))

    # ---- 逐文件取文本 ----
    $textParts = New-Object System.Collections.ArrayList
    $pendingFiles = New-Object System.Collections.ArrayList
    $okFiles = 0

    foreach ($f in $files) {
        $ext = $f.Extension.ToLower()
        Write-Host ("   · {0}" -f $f.Name) -ForegroundColor Gray
        $t = $null

        if ($ext -eq '.md' -or $ext -eq '.txt') {
            $t = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
        }
        elseif ($ext -eq '.html' -or $ext -eq '.htm') {
            $raw = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
            $raw = [regex]::Replace($raw, '(?is)<(script|style)[^>]*>.*?</\1>', ' ')
            $raw = [regex]::Replace($raw, '(?s)<[^>]+>', ' ')
            $t = [Net.WebUtility]::HtmlDecode($raw)
            Add-Issue "$($f.Name)：HTML 为粗提取，可能丢表格结构"
        }
        elseif ($ext -in @('.docx', '.docm', '.pptx', '.pptm', '.xlsx', '.xlsm')) {
            $t = Convert-OfficeToText $f.FullName
            if ([string]::IsNullOrWhiteSpace($t)) {
                Add-Issue "$($f.Name)：Office 文件读不出文本"
                [void]$pendingFiles.Add([pscustomobject]@{ file = $f.FullName; reason = 'Office 读不出文本' })
                continue
            }
        }
        elseif ($ext -in @('.doc', '.ppt', '.xls')) {
            Add-Issue "$($f.Name)：老 Office 格式，请另存为 docx/pptx/xlsx 后重试"
            [void]$pendingFiles.Add([pscustomobject]@{ file = $f.FullName; reason = '老 Office 格式' })
            continue
        }
        elseif ($ext -in @('.pdf', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff')) {
            $r = Invoke-Mineru $f.FullName $Tier
            if (-not $r.Ok) {
                Add-Issue "$($f.Name)：解析失败 —— $($r.Error)"
                [void]$pendingFiles.Add([pscustomobject]@{ file = $f.FullName; reason = $r.Error })
                continue
            }
            $t = $r.Text
            if (-not $Preview -and $r.WorkDir) {
                New-Item -ItemType Directory -Force -Path $mdDir | Out-Null
                $t = Import-FiguresFromJson $t $r.WorkDir $mdDir
                # 暂存 MinerU 产物，供图名归一工序 figures.py 使用
                $stash = Join-Path $NewRoot ('mineru-' + (Clean-FileName $bookName))
                if (Test-Path -LiteralPath (Join-Path $r.WorkDir 'x')) {
                    Copy-Item -LiteralPath (Join-Path $r.WorkDir 'x') -Destination $stash -Recurse -Force
                    $script:Stashed = $stash
                }
            }
            if ($r.Zip -and (Test-Path -LiteralPath $r.Zip)) {
                $parseDir = Join-Path (Join-Path $NewRoot 'parse') (Clean-FileName $bookName)
                New-Item -ItemType Directory -Force -Path $parseDir | Out-Null
                Copy-Item -LiteralPath $r.Zip -Destination (Join-Path $parseDir ([IO.Path]::GetFileName($r.Zip))) -Force
            }
            if ($r.WorkDir) { Remove-Item -LiteralPath $r.WorkDir -Recurse -Force -ErrorAction SilentlyContinue }
        }
        else {
            Add-Issue "$($f.Name)：不支持的类型 $ext"
            continue
        }

        if ([string]::IsNullOrWhiteSpace($t)) { continue }
        if ($files.Count -gt 1) {
            [void]$textParts.Add("# " + [IO.Path]::GetFileNameWithoutExtension($f.Name))
        }
        [void]$textParts.Add($t.Trim())
        $okFiles = $okFiles + 1
    }

    if ($pendingFiles.Count -gt 0) {
        foreach ($p in $pendingFiles) { [void]$pendList.Add($p) }
    }
    if ($okFiles -eq 0) {
        Add-Issue "$bookName ：没解析出可用文本，整本跳过"
        Count-Stat $stat 'pending'
        continue
    }

    $text = ($textParts -join "`r`n`r`n")
    $q = Get-Quality $text
    if ($q.Q -eq 'quarantine') { Add-Issue "$bookName ：质检不合格（$($q.Reason)），已隔离" }
    elseif ($q.Q -eq 'warn')   { Add-Issue "$bookName ：$($q.Reason)" }
    $isQuar = ($q.Q -eq 'quarantine')

    if ($isQuar) {
        $mdPath = Get-FreePath $Quar ('Q-' + (Clean-FileName $bookName)) '.md'
    } else {
        $mdPath = Get-FreePath $mdDir (Clean-FileName $bookName) '.md'
    }
    $srcRel = ($srcDir.Substring($Root.Length + 1)) -replace '\\', '/'

    if ($Preview) {
        [void]$plan.Add([pscustomobject]@{
            Book = $bookName; Layer = $layerRel; N = $N; Files = $files.Count
            Q = $q.Q; Md = ($mdPath.Substring($Root.Length + 1))
        })
        Count-Stat $stat $(if ($isQuar) { 'quarantine' } else { 'ok' })
        # ---- 图链自检（缺图/坏字符，幂等修复）----
    if (-not $isQuar) {
        $lkScript = Join-Path $PSScriptRoot 'check-links.ps1'
        if (Test-Path -LiteralPath $lkScript) {
            Write-Host '   图链自检（check-links.ps1）...' -ForegroundColor DarkCyan
            & powershell -NoProfile -ExecutionPolicy Bypass -File $lkScript -Md $mdPath -Fix
            if ($LASTEXITCODE -ne 0) { Add-Issue "$bookName ：图链自检仍有未解决项" }
        } else {
            Add-Issue "$bookName ：缺 check-links.ps1，未做图链自检"
        }
    }

$anchor
        continue
    }

    # ---- 写 md ----
    New-Item -ItemType Directory -Force -Path $srcDir | Out-Null
    if ($isQuar) { New-Item -ItemType Directory -Force -Path $Quar | Out-Null }
    else { New-Item -ItemType Directory -Force -Path $mdDir | Out-Null }

    $fm = @(
        '---'
        "id: `"$id`""
        "title: `"$(Esc-Yaml $title)`""
        "authors: `"$(Esc-Yaml $author)`""
        "edition: `"$(Esc-Yaml $edition)`""
        "year: `"$(Esc-Yaml $year)`""
        "kind: `"$(Get-KindName ($bookName + ' ' + (($files | ForEach-Object { $_.Name }) -join ' ')))`""
        "topic: `"$topicVal`""
        'pages: ""'
        'ocr: "auto"'
        "quality: `"$($q.Q)`""
        "sha256: `"$bookHash`""
        "src: `"$srcRel`""
        "files: `"$($files.Count)`""
        "added: `"$(Get-Date -Format 'yyyy-MM-dd')`""
        "missing: `"$($missing -join ',')`""
        '---'
        ''
    ) -join "`r`n"
    [IO.File]::WriteAllText($mdPath, $fm + $text + "`r`n", (New-Object Text.UTF8Encoding $false))

    # ---- 移动原件（整个文件夹的内容平铺进 srcDir，保持文件名）----
    foreach ($f in $files) {
        $dest = Get-FreePath $srcDir ([IO.Path]::GetFileNameWithoutExtension($f.Name)) $f.Extension.ToLower()
        Move-Item -LiteralPath $f.FullName -Destination $dest
    }
    if (-not (Get-ChildItem -LiteralPath $book.FullName -Recurse -File -ErrorAction SilentlyContinue)) {
        Remove-Item -LiteralPath $book.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }

    # ---- 图名归一（DSH 工序，幂等）----
    if (-not $isQuar -and $script:Stashed -and (Test-Path -LiteralPath $script:Stashed)) {
        $fgScript = Join-Path $PSScriptRoot 'figures.py'
        $pyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
        if ($pyExe -and (Test-Path -LiteralPath $fgScript)) {
            Write-Host '   图名归一（figures.py）...' -ForegroundColor DarkCyan
            & $pyExe -X utf8 $fgScript --mineru $script:Stashed --book $mdDir --dedupe --apply
            if ($LASTEXITCODE -ne 0) { Add-Issue "$bookName ：figures.py 退出码 $LASTEXITCODE，图名可能未归一" }
        } else {
            Add-Issue "$bookName ：缺 python 或 figures.py，图名未归一（MinerU 产物留在 $script:Stashed）"
        }
        if ($script:Stashed -and (Test-Path -LiteralPath $script:Stashed)) {
            Remove-Item -LiteralPath $script:Stashed -Recurse -Force -ErrorAction SilentlyContinue
        }
        $script:Stashed = $null
    }

    # ---- 图链自检（缺图/坏字符，幂等修复）----
    if (-not $isQuar) {
        $lkScript = Join-Path $PSScriptRoot 'check-links.ps1'
        if (Test-Path -LiteralPath $lkScript) {
            Write-Host '   图链自检（check-links.ps1）...' -ForegroundColor DarkCyan
            & powershell -NoProfile -ExecutionPolicy Bypass -File $lkScript -Md $mdPath -Fix
            if ($LASTEXITCODE -ne 0) { Add-Issue "$bookName ：图链自检仍有未解决项" }
        } else {
            Add-Issue "$bookName ：缺 check-links.ps1，未做图链自检"
        }
    }

            # ---- v3.3: 自动重建带页码锚点的正文（ingest-build.ps1）----
            $bkScript = Join-Path $PSScriptRoot 'ingest-build.ps1'
            if ((Test-Path -LiteralPath $bkScript) -and (Test-Path -LiteralPath $mdPath) -and -not $isQuar) {
                $anchorCount = ([regex]::Matches([IO.File]::ReadAllText($mdPath, [Text.Encoding]::UTF8), '<!-- page: \d+ -->')).Count
                if ($anchorCount -lt 10) {
                    Write-Host '   重建带页码锚点正文（ingest-build.ps1）...' -ForegroundColor DarkCyan
                    & powershell -NoProfile -ExecutionPolicy Bypass -File $bkScript -Book $bookName
                    if ($LASTEXITCODE -ne 0) { Add-Issue "$bookName ：ingest-build 验收未通过（见其上验收表）" }
                }
            }
$anchor
    if ($isQuar) { Count-Stat $stat 'quarantine' } else { Count-Stat $stat 'ok' }
    Write-Host ("   完成 [{0}] {1} 个文件 → {2}" -f $q.Q, $files.Count, $mdPath) -ForegroundColor Green
}

# ---------- 重建索引 ----------
if (-not $Preview) {
    $cat = Join-Path $PSScriptRoot 'catalog.ps1'
    if (Test-Path -LiteralPath $cat) {
        Write-Host "`n重建索引..." -ForegroundColor Cyan
        & powershell -NoProfile -ExecutionPolicy Bypass -File $cat
    }
}

if (-not $Preview -and (Test-Path -LiteralPath $LockFile)) { Remove-Item -LiteralPath $LockFile -Force -ErrorAction SilentlyContinue }
Write-Host ("`n汇总：入库 {0}，隔离 {1}，重复跳过 {2}，待处理 {3}，失败 {4}" -f $stat.ok, $stat.quarantine, $stat.duplicate, $stat.pending, $stat.failed) -ForegroundColor Cyan
