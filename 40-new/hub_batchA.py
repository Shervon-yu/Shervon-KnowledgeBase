# -*- coding: utf-8 -*-
import io

p = r'D:\Shervon_KnowledgeBase\50-wiki\sources\搅拌与混合设备设计选用手册.md'
t = io.open(p, encoding='utf-8').read()
old = "- 第五章 搅拌器 → [[搅拌器-分类]]、[[搅拌器-技术要求与验收]]、[[搅拌器-应用实例]]、[[搅拌器-新型桨]]"
new = old + """
- 第三章 特殊过程 → [[搅拌-悬浮与分散机理]]
- 第四章 放大 → [[搅拌设备-放大准则与实例]]
- 第六章 容器 → [[立式搅拌容器-型式与参数]]、[[搅拌容器-传热元件]]"""
assert old in t
io.open(p, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new, 1))

# 搅拌容器-容积 页加入链
p2 = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\搅拌容器-容积与装液高径比.md'
t2 = io.open(p2, encoding='utf-8').read()
mark = '## 相关'
add = """## 标准组合与传热面

- 立式钢制容器的标准组合（GB 9845、表 6-2/6-3）见 [[立式搅拌容器-型式与参数]]。
- 夹套与内盘管的选型见 [[搅拌容器-传热元件]]。

## 相关"""
assert mark in t2
io.open(p2, 'w', encoding='utf-8', newline='\n').write(t2.replace(mark, add, 1))

# 组成与设计流程 页加放大入口
p3 = r'D:\Shervon_KnowledgeBase\50-wiki\concepts\搅拌设备-组成与设计流程.md'
t3 = io.open(p3, encoding='utf-8').read()
mark3 = '## 相关'
add3 = """## 放大与标准组合

- 九步流程里「特性计算」之后的放大判断见 [[搅拌设备-放大准则与实例]]。
- 容器尺寸落标准组合见 [[立式搅拌容器-型式与参数]]。

## 相关"""
assert mark3 in t3
io.open(p3, 'w', encoding='utf-8', newline='\n').write(t3.replace(mark3, add3, 1))
print('ok')
