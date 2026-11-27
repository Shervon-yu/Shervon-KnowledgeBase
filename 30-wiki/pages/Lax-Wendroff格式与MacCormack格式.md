---
type: concept
title: Lax-Wendroff格式与MacCormack格式
question: 显式二阶精度格式怎么构造，Lax-Wendroff 与 MacCormack 各自怎么做，为什么中心差分在激波附近会产生振荡、要靠人工粘性压制？
description: Lax-Wendroff 用时间泰勒展开到二阶、借控制方程替换时间二阶导数；MacCormack 用预测-校正两步达到二阶精度；两者都是显式、受 CFL 限制，且都隐含数值耗散/色散，捕捉激波时常需显式加人工粘性。
aliases: [Lax-Wendroff方法, MacCormack方法, 预测校正, 数值耗散, 数值色散, 人工粘性, 修正方程]
domain: 计算流体力学
status: stable
confidence: high
sources:
  - book: 计算流体力学基础及其应用
    section: §6.2–§6.4、§6.6
    lines: "#L4670-#L5210"
related: ["[[显式隐式方法与稳定性分析]]", "[[有限差分基础与差分方程]]", "[[守恒型方程与迎风格式]]", "[[CFD边界条件与守恒控制方程]]"]
supersedes: []
updated: 2026-11-27
---

# Lax-Wendroff格式与MacCormack格式

## Lax-Wendroff：时间二阶泰勒（§6.2）

显式一阶格式只保留 $\Delta t$ 项；要二阶精度，就把解在时间上展开到 $(\Delta t)^2$（式 6-5～6-8，＃L4700-4718）：

|  |  |  |
|:---|:---:|---:|
| **符号式** | $\rho_{i,j}^{t+\Delta t}=\rho_{i,j}^{t}+\left(\dfrac{\partial\rho}{\partial t}\right)_{i,j}^{t}\Delta t+\left(\dfrac{\partial^2\rho}{\partial t^2}\right)_{i,j}^{t}\dfrac{(\Delta t)^2}{2}+\cdots$ | （6-5） |
| **文字式** | $\text{密度}^{t+\Delta t}=\text{密度}^{t}+\dfrac{\partial\text{密度}}{\partial t}\Delta\text{时间}+\dfrac{\partial^2\text{密度}}{\partial\text{时间}^2}\dfrac{(\Delta\text{时间})^2}{2}+\cdots$ |  |

问题是 $\partial^2\rho/\partial t^2$ 不知道。Lax-Wendroff 的办法：用控制方程本身把时间导数换成空间导数。以连续性方程为例，把（6-1）再对 $t$ 求导（式 6-10，＃L4726），其中 $\partial^2u/\partial x\partial t$ 又用动量方程（6-2）对 $x$ 求导替换（式 6-11，＃L4732），最终得到只含空间导数的二阶时间导数（6-12，＃L4738）。这样每一步只需当前层的空间差分。

- 代价：每个方程要推导、编程量随方程数增长（二维 N-S 有四个方程，手工推导容易出错）。
- 结果：时间、空间都二阶精度，仍是显式，受 CFL 限制（$C\le1$）。

## MacCormack：预测-校正（§6.3）

MacCormack 不推导二阶时间导数，改用两步一阶：

1. **预测**：用前向空间差分估计 $t+\Delta t$ 的中间值（式 6-17、6-18，＃L4796-4804）：

|  |  |  |
|:---|:---:|---:|
| **符号式** | $\left(\bar{\rho}\right)_{i,j}^{t+\Delta t}=\rho_{i,j}^{t}+\left(\dfrac{\partial\rho}{\partial t}\right)_{i,j}^{t}\Delta t$ | （6-18） |
| **文字式** | $\text{中间密度}^{t+\Delta t}=\text{密度}^{t}+\left(\dfrac{\partial\text{密度}}{\partial t}\right)^{t}\Delta\text{时间}$ |  |

2. **校正**：在中间层用后向差分算一次导数（6-21，＃L4822），再与第 $n$ 层导数取平均（6-22，＃L4826）：

|  |  |  |
|:---|:---:|---:|
| **符号式** | $\left(\dfrac{\partial\rho}{\partial t}\right)_{\mathrm{av}}=\dfrac{1}{2}\left[\left(\dfrac{\partial\rho}{\partial t}\right)_{i,j}^{t}+\left(\overline{\dfrac{\partial\rho}{\partial t}}\right)_{i,j}^{t+\Delta t}\right]$ | （6-22） |
| **文字式** | $\text{平均时间导数}=\dfrac{1}{2}\left[\text{第 }n\text{ 层导数}+\text{中间层导数}\right]$ |  |

3. 用平均值推进（6-13，＃L4832）。

预测用前向、校正用后向，两步的截断误差在平均中相消，整体达到二阶精度；编程只需写两遍同样的通量计算，比 Lax-Wendroff 的解析推导简单得多。书里第 7、8、10 章的算例基本都用 MacCormack。

## 推广到 N-S 与空间推进（§6.4）

- 粘性流动在动量、能量方程右端加粘性通量，通量含一阶导数（速度梯度、温度梯度），离散时再对一阶导数做一次中心差分即得二阶导数。
- 定常超声速流动可把流向坐标当推进变量，用与时间推进相同的格式做**空间推进**；此时 CFL 条件换成流向步长限制（第 8 章，＃L8787 起）。

## 数值耗散、色散与人工粘性（§6.6）

以模型方程 $\partial u/\partial t+a\,\partial u/\partial x=0$（6-38，＃L5002）为例，把一阶迎风格式（6-39，＃L5006）的泰勒展开代回，得到它实际求解的**修正方程**（6-43～6-49，＃L5024-5052）：

|  |  |  |
|:---|:---:|---:|
| **符号式** | $\dfrac{\partial u}{\partial t}+a\dfrac{\partial u}{\partial x}=a\dfrac{\Delta x}{2}\dfrac{\partial^2u}{\partial x^2}-\dfrac{a(\Delta x)^2}{6}\dfrac{\partial^3u}{\partial x^3}+\cdots$ | （6-43） |
| **文字式** | 原方程 $=\text{二阶导数项（耗散）}+\text{三阶导数项（色散）}+\cdots$ |  |

- 偶数阶导数项起到粘性作用 → **数值耗散**：抹平解、压制振荡，但降低精度；
- 奇数阶导数项 → **数值色散**：不同波数传播速度不同，激波附近出现波纹状振荡。
- 中心差分没有偶数阶耗散项，所以在激波附近振荡；加**人工粘性**（显式加一个与 $\Delta x$ 成正比的二阶导数项，或 MacCormack 里的 $C_x$ 项）可以压制振荡（#L5118）。

## 适用边界

- Lax-Wendroff 与 MacCormack 都是显式，时间步长受 CFL 限制（$C\le1$，非线性问题只能作指导）。
- 二阶格式在光滑区精度高，但在激波处仍会振荡，必须配人工粘性或改用高分辨率格式（TVD，第 11 章）。
- 人工粘性是双刃剑：加多了抹平激波、加少了振荡甚至发散；书里明确说 $C_x$ 的选取要看问题（#L8181）。
- MacCormack 的预测-校正顺序可以互换（前向-后向或后向-前向），精度不变。

## 判断

Lax-Wendroff 与 MacCormack 的差别是"推导二阶项"与"两步平均"的差别，精度同为二阶，实际选择看编程成本与推广到复杂方程的难易——书里选 MacCormack 做全部算例，理由就是它不需要手工推导二阶导数。数值耗散/色散的概念比格式本身更重要：任何格式都在解一个修正方程，格式的"性格"由修正方程的奇偶阶导数项决定。
