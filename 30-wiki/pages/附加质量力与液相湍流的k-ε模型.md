---
type: concept
title: 附加质量力与液相湍流的k-ε模型
question: 附加质量力系数为什么取 0.5？k-ε 模型的常数取哪些值？
description: 气泡加速的附加质量力系数取0.5且与曳力同量级不可忽略，液相湍流用标准k-ε模型并附各常数取值
aliases: [虚拟质量力, k-ε模型常数, 液相湍动模型]
domain: 气液搅拌釜γ-CT
status: stable
confidence: high
sources:
  - book: 气液搅拌釜γ-CT测量、成像与模拟
    section: 第7章 7.3.2–7.3.3
    lines: "#L3155-#L3191"
related: ["[[相间作用力与曳力的湍流修正]]", "[[双流体模型的基本方程]]"]
supersedes: []
updated: 2026-11-19
---

# 附加质量力与液相湍流的k-ε模型

## 附加质量力（7.11，`#L3157-#L3163`）

气泡在液体中加速，必须同时带动周围液体加速，故受到一个"额外惯性力"：

$$\mathbf{F}_{VM}=-\alpha_g\alpha_l C_{VM}\frac{D}{Dt}(\mathbf{u}_b-\mathbf{u}_l)\tag{7.11}$$

- $C_{VM}$ **取 0.5**（球形颗粒在无界理想流体中的理论值）：气泡密度远小于液体时，附加质量力与曳力同量级，**不能忽略**；
- 符号：与相对加速度方向相反，起"延缓气泡加速"的作用。

## 液相湍流模型（7.12~7.15，`#L3167-#L3189`）

通用输运式（7.12，变量 $\phi$ 可为 $v_i$、$k$、$\varepsilon$）：

$$\frac{\partial(\rho\phi)}{\partial t}+\nabla\cdot(\rho\mathbf{u}\phi)=\nabla\cdot(\Gamma\nabla\phi)+S_0$$

$k$ 方程与 $\varepsilon$ 方程（7.13、7.14）：

$$\frac{\partial(\rho k)}{\partial t}+\nabla\cdot(\rho\mathbf{u}k)=\nabla\cdot\left[\left(\mu+\frac{\mu_t}{\sigma_k}\right)\nabla k\right]+G_k+G_b-\rho\varepsilon-Y_M$$

$$\frac{\partial(\rho\varepsilon)}{\partial t}+\nabla\cdot(\rho\mathbf{u}\varepsilon)=\nabla\cdot\left[\left(\mu+\frac{\mu_t}{\sigma_\varepsilon}\right)\nabla\varepsilon\right]+C_{1\varepsilon}\frac{\varepsilon}{k}(G_k+C_{3\varepsilon}G_b)-C_{2\varepsilon}\rho\frac{\varepsilon^2}{k}$$

湍流黏度（7.15，`#L3189`）：

$$\mu_t=\rho C_\mu\frac{k^2}{\varepsilon}$$

| 常数 | 值 | 含义 |
|:--|:--|:--|
| $C_{1\varepsilon}$ | 1.44 | $\varepsilon$ 方程生成项系数 |
| $C_{2\varepsilon}$ | 1.92 | $\varepsilon$ 方程耗散项系数 |
| $C_\mu$ | 0.09 | 湍流黏度系数 |
| $\sigma_k$ | 1.0 | $k$ 的湍流普朗特数 |
| $\sigma_\varepsilon$ | 1.3 | $\varepsilon$ 的湍流普朗特数 |

- $G_k$ 平均速度梯度产生的湍动能、$G_b$ 浮力产生的湍动能、$Y_M$ 可压缩湍流中波动扩张对总耗散的贡献（不可压时忽略）。

## 判断

- $C_{VM}=0.5$ 是**势流理论值**，对变形大气泡偏高；但搅拌釜中气泡多为 1~4 mm，接近球形，用 0.5 合理；
- 标准 $k$-$\varepsilon$ 在强旋流（搅拌釜的切向流）下会高估湍流黏度，本书仍用它，是因为**网格 30 万 + 滑动交界面**下，RNG 或 Realizable 的收敛性不稳定；
- 常数是 Launder-Spalding 标准值，**不要改**；要改的是 $C_1$/$C_7$（见曳力修正页），那才是本书标定的对象。
