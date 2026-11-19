# -*- coding: utf-8 -*-
"""补齐遗漏项：rules §10、prompt.md 版权页核对与图名规则、ingest 锁与 ocr 字段。"""
import io, os

ROOT = r'D:\Shervon_KnowledgeBase'
res = []

def rd(p):
    raw = io.open(p, 'rb').read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')

def wr(p, t, bom):
    data = t.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    io.open(p, 'wb').write(data)

def patch(p, pairs):
    t, bom = rd(p)
    nl = '\r\n' if '\r\n' in t else '\n'
    for old, new in pairs:
        if old not in t:
            res.append(('MISS', os.path.basename(p), old[:36]))
            continue
        t = t.replace(old, new.replace('\n', nl), 1)
        res.append(('OK', os.path.basename(p), old[:36]))
    wr(p, t, bom)

patch(os.path.join(ROOT, r'90-tool\rules.md'), [
    ('质检：ok / warn / quarantine\n元数据缺失：edition, year',
     '质检：ok / warn / quarantine\n图链：SELFCHECK refs=N ok=N unresolved=0\n缺图：N 张（清单见 todo.md）\n元数据缺失：edition, year'),
])

patch(os.path.join(ROOT, r'90-tool\prompt.md'), [
    ('默认直接执行、不等确认；只有我明确说"先预览"才加 `-Preview`（预览也会真跑 MinerU，很耗时）。',
     '默认直接执行、不等确认；只有我明确说"先预览"才加 `-Preview`（预览也会真跑 MinerU，很耗时）。脚本收尾会自动做图链自检（`check-links.ps1 -Fix`），没通过会在输出里报。'),
    ('**文件名禁含括号**：多子图写 `图7.3 …_a.jpg`、`_b`，不要写 `(a)`——括号会截断 markdown 链接。',
     '**文件名禁含 `( ) [ ] { } * ? : " < > | / \\ # %`**：多子图写 `图7.3 …_a.jpg`、`_b`，不要写 `(a)`；图题里的引用号 `[31]` 先剥掉——方括号/圆括号都会截断 markdown 链接，是硬错误。'),
    ('6. 按 `rules.md` 第 4 节定层级、第 6 节定名：',
     '6. 解析完用版权页核对书名/版次/年份（不符就改名：入库夹、md、`10-source`、frontmatter 的 `src` 同步，再重跑 `catalog.ps1`）。\n7. 按 `rules.md` 第 4 节定层级、第 6 节定名：'),
])

patch(os.path.join(ROOT, r'90-tool\scripts\ingest.ps1'), [
    ("$Inbox    = Join-Path $Root '00-inbox'",
     "$Inbox    = Join-Path $Root '00-inbox'\n$LockFile = Join-Path $Root '40-scratch\\.ingest.lock'\nif (-not $Preview) {\n    if (Test-Path -LiteralPath $LockFile) {\n        Write-Host \"已有入库任务在跑（$LockFile），本次退出。\" -ForegroundColor Red\n        exit 1\n    }\n    New-Item -ItemType File -Path $LockFile -Force | Out-Null\n}"),
    ("'ocr: \"unknown\"'", "'ocr: \"auto\"'"),
    ('Write-Host ("`n汇总：入库',
     'if (-not $Preview -and (Test-Path -LiteralPath $LockFile)) { Remove-Item -LiteralPath $LockFile -Force -ErrorAction SilentlyContinue }\nWrite-Host ("`n汇总：入库'),
])

for r in res:
    print('\t'.join(r))
print('MISS =', sum(1 for r in res if r[0] == 'MISS'))
