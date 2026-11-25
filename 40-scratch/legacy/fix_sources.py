# -*- coding: utf-8 -*-
"""修 6 个新页的 sources 块格式，并补入链。"""
import io, os, re

W = r'D:\Shervon_KnowledgeBase\50-wiki'
spec = {
    'concepts\\气液两相搅拌.md': ('§2.3 气-液两相', '#L2114-#L2330'),
    'concepts\\液液分散.md': ('§2.3 液-液两相', '#L2332-#L2570'),
    'concepts\\固液悬浮.md': ('§2.3 固-液两相', '#L2571-#L2770'),
    'concepts\\气液固三相搅拌.md': ('§2.3 气-液-固三相', '#L2771-#L2925'),
    'concepts\\刮壁式传热.md': ('§3.3 传热', '#L3260-#L3346'),
    'concepts\\搅拌-传质.md': ('§3.4 传质', '#L3347-#L3700'),
}
for rel, (sec, lines) in spec.items():
    p = os.path.join(W, rel)
    t = io.open(p, encoding='utf-8').read()
    t2 = re.sub(r'^sources: \[[^\]]*\]$',
                'sources:\n  - book: 搅拌与混合设备设计选用手册\n    section: %s\n    lines: "%s"' % (sec, lines),
                t, count=1, flags=re.M)
    assert t2 != t, rel
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t2)

def add(rel, anchor, text):
    p = os.path.join(W, rel)
    t = io.open(p, encoding='utf-8').read()
    if text in t:
        return
    t = t.replace(anchor, anchor + text, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

# 入链：传热页 → 刮壁；固液/气液 → 传质；三相/混合设备 → 液液
add('concepts\\搅拌-传热膜系数.md', '## 相关', '\n\n- 高黏与易结垢体系的刮壁强化：[[刮壁式传热]]')
add('concepts\\固液悬浮.md', '## 相关', '\n- 传质计算：[[搅拌-传质]]')
add('concepts\\气液两相搅拌.md', '## 相关', '\n- 气液/液固传质：[[搅拌-传质]]')
add('concepts\\气液固三相搅拌.md', '## 相关', '\n- 液-液分散：[[液液分散]]')
add('concepts\\混合设备-分类与选型.md', '## 相关', '\n- 液-液分散指标：[[液液分散]]')
print('ok')
