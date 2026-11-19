# -*- coding: utf-8 -*-
import io
# 1) sources 页各章详页补链接（第十四/十五章）
p = r'D:\Shervon_KnowledgeBase\50-wiki\sources\搅拌与混合设备设计选用手册.md'
t = io.open(p, encoding='utf-8').read()
old = "- 第三章 特殊过程 → [[搅拌-悬浮与分散机理]]"
new = old + """
- 第十四章 容器固定型 → [[固定型混合设备-特殊机型]]
- 第十五章 非回转式 → [[气流搅拌与射流混合]]"""
assert old in t and "固定型混合设备-特殊机型" not in t
io.open(p,'w',encoding='utf-8',newline='\n').write(t.replace(old,new,1))
# 2) 混合设备-分类与选型 页加链接
p2 = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\混合设备-分类与选型.md'
t2 = io.open(p2, encoding='utf-8').read()
old2 = "- [[螺带式混合设备]]"
new2 = "- [[螺带式混合设备]]" + """
- [[固定型混合设备-特殊机型]]：犁刀、瞬间失重、行星锥形、研磨
- [[气流搅拌与射流混合]]：非回转式的两条无运动件路线"""
assert old2 in t2 and "固定型混合设备-特殊机型" not in t2
io.open(p2,'w',encoding='utf-8',newline='\n').write(t2.replace(old2,new2,1))
print('ok')
