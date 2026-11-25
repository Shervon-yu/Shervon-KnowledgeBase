$ErrorActionPreference = 'Stop'
$root = 'D:\Shervon_KnowledgeBase'
$mdRoot = Join-Path $root '20-md'
$utf8 = New-Object System.Text.UTF8Encoding($false)

foreach ($d in Get-ChildItem -LiteralPath $mdRoot -Directory) {
    if ($d.Name -eq '_quarantine') { continue }
    $book = $d.Name
    $mds = @(Get-ChildItem -LiteralPath $d.FullName -File -Filter *.md)
    $subs = @(Get-ChildItem -LiteralPath $d.FullName -Directory)
    if ($mds.Count -ne 1 -or $subs.Count -ne 1) {
        Write-Output ("SKIP  {0}  md={1} sub={2}" -f $book, $mds.Count, $subs.Count)
        continue
    }
    $md = $mds[0]
    $imgDir = $subs[0]
    $imgName = $imgDir.Name
    $newImg = Join-Path $mdRoot ($book + '---' + $imgName)
    if (Test-Path -LiteralPath $newImg) { Write-Output ("CONFLICT {0}" -f $newImg); continue }

    $txt = [System.IO.File]::ReadAllText($md.FullName)
    $from = '](' + $imgName + '/'
    $to = '](' + $book + '---' + $imgName + '/'
    $refsBefore = ([regex]::Matches($txt, [regex]::Escape($from))).Count
    $newTxt = $txt.Replace($from, $to)
    $refsAfter = ([regex]::Matches($newTxt, [regex]::Escape($to))).Count
    $imgCount = @(Get-ChildItem -LiteralPath $imgDir.FullName -File -Recurse).Count

    $mdNew = Join-Path $mdRoot ($book + '.md')
    [System.IO.File]::WriteAllText($mdNew, $newTxt, $utf8)
    [System.IO.File]::Delete($md.FullName)
    Move-Item -LiteralPath $imgDir.FullName -Destination $newImg
    Remove-Item -LiteralPath $d.FullName -Recurse -Force

    Write-Output ("OK  {0}  refs={1}->{2}  img={3}" -f $book, $refsBefore, $refsAfter, $imgCount)
}
Write-Output '--- done ---'
Get-ChildItem -LiteralPath $mdRoot | ForEach-Object { Write-Output ("{0,-6} {1}" -f $(if ($_.PSIsContainer) { 'DIR' } else { 'FILE' }), $_.Name) }
