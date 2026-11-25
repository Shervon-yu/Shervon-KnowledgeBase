# -*- coding: utf-8 -*-
import io

p = r'D:\Shervon_KnowledgeBase\50-wiki\sources\搅拌与混合设备设计选用手册.md'
t = io.open(p, encoding='utf-8').read()
old = "- 第十七章 采购与交付 → [[搅拌设备-采购与交付]]"
new = """- 第十七章 采购与交付 → [[搅拌设备-采购与交付]]
- 第五章 搅拌器 → [[搅拌器-分类]]、[[搅拌器-技术要求与验收]]、[[搅拌器-应用实例]]、[[搅拌器-新型桨]]
- 第八章 搅拌附件 → [[挡板]]、[[导流筒]]"""
assert old in t
t = t.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(t)

# 选型准则页补导航
p2 = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\搅拌器-选型准则.md'
t2 = io.open(p2, encoding='utf-8').read()
mark = '## 相关'
add = """## 延伸

- 分类三口径与结构对应见 [[搅拌器-分类]]；制造公差与平衡验收见 [[搅拌器-技术要求与验收]]。
- 已运行工况样本见 [[搅拌器-应用实例]]；覆盖率换低功率的新型桨见 [[搅拌器-新型桨]]。

## 相关"""
assert mark in t2
t2 = t2.replace(mark, add, 1)
io.open(p2, 'w', encoding='utf-8', newline='\n').write(t2)

# 挡板页补导流筒互链
p3 = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\挡板.md'
t3 = io.open(p3, encoding='utf-8').read()
mark3 = '## 相关'
add3 = """## 相关附件

- 导流筒限定循环路径、与挡板配合消除短路，见 [[导流筒]]。
- 指形挡板、底挡板、轻液挡板的具体尺寸见 §8.1。

## 相关"""
assert mark3 in t3
t3 = t3.replace(mark3, add3, 1)
io.open(p3, 'w', encoding='utf-8', newline='\n').write(t3)
print('ok')
