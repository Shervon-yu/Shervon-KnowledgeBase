<#
  budget-watch.ps1 — 会话费用看门狗

  每 N 秒读取 DSH 用量缓存（%USERPROFILE%\.dsh\storages\usage-stats-cache.json），
  取最近活跃会话的输入/缓存命中/输出计数，按 DeepSeek 官方单价折算人民币
  （峰价自动判断，谷价减半）。达到阈值即：写 stop 标记 + 记日志，可选强杀进程。

  用法示例：
    powershell -NoProfile -ExecutionPolicy Bypass -File budget-watch.ps1 -Limit 5
    powershell -NoProfile -ExecutionPolicy Bypass -File budget-watch.ps1 -Limit 5 -KillDsh
    powershell -NoProfile -ExecutionPolicy Bypass -File budget-watch.ps1 -Limit 0.5 -Once   # 自检一次

  参数：
    -Limit <元>          阈值，默认 5
    -IntervalSeconds     轮询秒数，默认 60
    -KillMineru          超阈值时杀掉 MinerU 解析进程（省内存，不省钱）
    -KillDsh             超阈值时强杀 DSH 进程（真断钱，代价：会话被强关）
    -Once                只检查一次后退出
#>
[CmdletBinding()]
param(
    [double]$Limit = 5.0,
    [int]$IntervalSeconds = 60,
    [switch]$KillMineru,
    [switch]$KillDsh,
    [switch]$Once,
    [string]$OutDir = ''
)

$ErrorActionPreference = 'SilentlyContinue'
$Store = Join-Path $env:USERPROFILE '.dsh\storages\usage-stats-cache.json'
$PendingDir = if ($OutDir) { $OutDir } else { Join-Path $env:TEMP 'kb-budget' }
if (-not (Test-Path $PendingDir)) { New-Item -ItemType Directory -Path $PendingDir -Force -ErrorAction SilentlyContinue | Out-Null }
$Flag = Join-Path $PendingDir 'budget-stop.flag'
$Log  = Join-Path $PendingDir 'budget-watch.log'
Write-Host ("watchdog dir: $PendingDir")

function Get-PeakRate {
    $now = Get-Date
    $dow = [int]$now.DayOfWeek
    $t = $now.TimeOfDay
    $workday = ($dow -ge 1 -and $dow -le 5)
    $peak = $workday -and ((($t -ge [TimeSpan]'09:00') -and ($t -lt [TimeSpan]'12:00')) -or
                           (($t -ge [TimeSpan]'14:00') -and ($t -lt [TimeSpan]'18:00')))
    if ($peak) {
        return @{ Peak = $true;  In = 2.0; Hit = 0.04; Out = 8.0 }
    }
    return @{ Peak = $false; In = 1.0; Hit = 0.02; Out = 4.0 }
}

function Get-ActiveSessionCost {
    if (-not (Test-Path $Store)) { return $null }
    $json = (Get-Content $Store -Raw)
    if (-not $json) { return $null }
    $data = $json | ConvertFrom-Json
    $props = @($data.sessions.PSObject.Properties)
    if ($props.Count -eq 0) { return $null }
    $latest = $props | Sort-Object { [long]$_.Value.billing.lastAt } -Descending | Select-Object -First 1
    if (-not $latest) { return $null }

    $miss = [long]0; $hit = [long]0; $out = [long]0
    foreach ($p in $latest.Value.usageSamples.PSObject.Properties) {
        $b = $p.Value.buckets
        if ($null -eq $b) { continue }
        $miss += [long]$b.inputTokens
        $hit  += [long]$b.cacheReadTokens
        $out  += [long]$b.outputTokens
    }

    $rate = Get-PeakRate
    $cost = $miss / 1e6 * $rate.In + $hit / 1e6 * $rate.Hit + $out / 1e6 * $rate.Out

    return [pscustomobject]@{
        Session = $latest.Name
        Miss    = $miss
        Hit     = $hit
        Out     = $out
        Cost    = [math]::Round($cost, 4)
        Peak    = $rate.Peak
        LastAt  = [long]$latest.Value.billing.lastAt
    }
}

function Invoke-Breach {
    param($c)
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $msg = "[$stamp] LIMIT BREACHED  cost=CNY $($c.Cost) >= $Limit  session=$($c.Session)  miss=$($c.Miss) hit=$($c.Hit) out=$($c.Out)"
    Add-Content -Path $Log -Value $msg
    Set-Content -Path $Flag -Value $msg
    Write-Host $msg

    if ($KillMineru) {
        Get-Process -Name 'mineru-kit','mineru' -ErrorAction SilentlyContinue | Stop-Process -Force
        Get-Process -Name 'python' -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match 'mineru' } |
            Stop-Process -Force
    }
    if ($KillDsh) {
        # 只杀 DSH 的 Electron 进程树；用命令行匹配，避免误杀无关 node
        Get-CimInstance Win32_Process |
            Where-Object {
                $_.CommandLine -and
                $_.CommandLine -match '(?i)(deepseek.harness|dsh).*(electron|dsh)' -and
                $_.Name -notmatch '^(powershell|pwsh|conhost|cmd)'
            } |
            ForEach-Object {
                Write-Host ("KILL DSH pid={0} name={1}" -f $_.ProcessId, $_.Name)
                Stop-Process -Id $_.ProcessId -Force
            }
    }
}

$lastLine = ''
while ($true) {
    $c = Get-ActiveSessionCost
    if ($null -ne $c) {
        $stamp = Get-Date -Format 'HH:mm:ss'
        $line = "[$stamp] session=$($c.Session) cost=CNY $($c.Cost) peak=$($c.Peak) miss=$($c.Miss) hit=$($c.Hit) out=$($c.Out)"
        if ($line -ne $lastLine) { Add-Content -Path $Log -Value $line }
        $lastLine = $line
        Write-Host $line

        if ($c.Cost -ge $Limit) {
            Invoke-Breach -c $c
            break
        }
    }
    if ($Once) { break }
    Start-Sleep -Seconds $IntervalSeconds
}
