# -*- coding: utf-8 -*-
"""修正 catalog.ps1 图链体检段（上一次 shell 转义把 \\$ 写进了文件）。"""
import io, re

p = r'D:\Shervon_KnowledgeBase\90-tool\scripts\catalog.ps1'
t = io.open(p, encoding='utf-8-sig').read()

block = r'''# 7 图链体检（md 里指向不存在文件的图片链接）
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

'''

start = t.find('# 7 图链体检')
end = t.find('# 8 规则缺口', start)
if start < 0 or end < 0:
    # 未插入过：找到原 # 7 规则缺口 前插入
    anchor = '# 7 规则缺口'
    if anchor not in t:
        raise SystemExit('anchor missing')
    t = t.replace(anchor, block + '# 8 规则缺口', 1)
else:
    t = t[:start] + block + t[end:]

io.open(p, 'w', encoding='utf-8-sig', newline='').write(t)
print('written', len(t), 'chars')
print('dollar-escape residue:', t.count('\\$'))
