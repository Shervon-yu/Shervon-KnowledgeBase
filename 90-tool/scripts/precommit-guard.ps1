# 提交前守卫：确认暂存区里的删除项都是有意为之
param([switch]$AllowDelete)

$d = git diff --cached --name-status --diff-filter=D 2>$null
if ((-not $AllowDelete) -and $d) {
    Write-Host '暂存区含删除项，已中止：' -ForegroundColor Red
    $d | ForEach-Object { Write-Host "  D  $_" }
    Write-Host '确认无误后改用：precommit-guard.ps1 -AllowDelete' -ForegroundColor Yellow
    exit 1
}
Write-Host 'precommit 守卫通过'
exit 0
