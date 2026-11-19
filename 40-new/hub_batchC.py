# -*- coding: utf-8 -*-
import io

def patch(path, old, new, marker):
    t = io.open(path, encoding='utf-8').read()
    if marker in t:
        print('skip', path)
        return
    assert old in t, path
    io.open(path, 'w', encoding='utf-8', newline='\n').write(t.replace(old, new, 1))
    print('ok', path)

S = r'D:\Shervon_KnowledgeBase\50-wiki\sources\搅拌与混合设备设计选用手册.md'
patch(S, "- 第三章 特殊过程 → [[搅拌-悬浮与分散机理]]",
      "- 第三章 特殊过程 → [[搅拌-悬浮与分散机理]]\n"
      "- 第九章 传动装置 → [[搅拌传动装置-部件选用]]\n"
      "- 第十章 轴封 → [[轴封-填料密封]]\n"
      "- 第十一章 磁力传动 → [[磁力联轴器-结构与磁钢材料]]",
      "磁力联轴器-结构与磁钢材料")

C = r'D:\Shervon_KnowledgeBase\50-wiki\concepts'
patch(C + '\\搅拌传动装置-选用.md', "## 相关",
      "## 部件选型\n\n- 见 [[搅拌传动装置-部件选用]]。\n\n## 相关",
      "搅拌传动装置-部件选用")
patch(C + '\\轴封-类型与功率损耗.md', "## 相关",
      "## 填料密封\n\n- 见 [[轴封-填料密封]]。\n\n## 相关",
      "轴封-填料密封")
patch(C + '\\磁力传动搅拌设备.md', "## 相关",
      "## 原理与磁钢材料\n\n- 见 [[磁力联轴器-结构与磁钢材料]]。\n\n## 相关",
      "磁力联轴器-结构与磁钢材料")
