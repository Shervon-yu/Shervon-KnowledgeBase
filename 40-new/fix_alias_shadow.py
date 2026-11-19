# -*- coding: utf-8 -*-
import io

# 1) 去掉遮蔽页名的别名
p = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\搅拌设备-组成与设计流程.md'
t = io.open(p, encoding='utf-8').read()
old = 'aliases: [搅拌设备组成, 搅拌容器, 搅拌机, 搅拌器, 导流筒, 传动装置, 设计步骤, 釜体]'
new = 'aliases: [搅拌设备组成, 搅拌容器, 搅拌机, 搅拌器, 传动装置, 设计步骤, 釜体]'
assert old in t
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new, 1))

# 2) wiki-lint.ps1 增加「别名遮蔽页名」检查
lp = r'D:\Shervon_KnowledgeBase\90-tool\scripts\wiki-lint.ps1'
s = io.open(lp, encoding='utf-8-sig').read()
anchor = '$deadLink = New-Object System.Collections.ArrayList'
add = '''$aliasShadow = New-Object System.Collections.ArrayList
foreach($k in $pages.Keys){
  foreach($a in $pages[$k].fm.aliases){
    if($a -and $pages.Contains($a) -and $a -ne $k){ [void]$aliasShadow.Add("$k 的别名「$a」遮蔽了同名页") }
  }
}

$deadLink = New-Object System.Collections.ArrayList'''
assert anchor in s
s = s.replace(anchor, add, 1)

# 报告里加一节
old_blocks = "  '8 图无转述'      = $imgNoCap"
new_blocks = "  '8 图无转述'      = $imgNoCap\n  '9 别名遮蔽页名'  = $aliasShadow"
assert old_blocks in s
s = s.replace(old_blocks, new_blocks, 1)
io.open(lp, 'w', encoding='utf-8-sig', newline='\n').write(s)
print('ok')
