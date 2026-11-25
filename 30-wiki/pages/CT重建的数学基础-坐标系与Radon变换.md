---
type: concept
title: CT重建的数学基础：坐标系与Radon变换
question: Radon 变换为什么能"用线积分反解出截面图像"，逆变换公式里的奇异积分怎么理解？
description: 推导 Radon 变换与逆变换，逆变换含奇异积分难以数值实现，故工程上改用 FBP 或迭代法重建。
aliases: [Radon变换, 坐标系转换, 逆变换, 线积分]
domain: 气液搅拌釜γ-CT
status: draft
confidence: high
sources:
  - book: 气液搅拌釜γ-CT测量、成像与模拟
    section: 第4章 4.1.1-4.1.2
    lines: "#L1885-#L1923"
related: ["[[傅里叶切片定理]]", "[[CT重建算法的两类与比较]]", "[[射线CT的测量原理]]"]
supersedes: []
updated: 2026-11-19
---

# CT重建的数学基础：坐标系与Radon变换

## 两条历史线索（`#L1887`）

CT 重建思想可追溯到 1917 年 Radon 的线积分反演；他证明的 Radon 变换与 Fourier 切片定理共同构成图像重建的数学基础。

## 坐标转换（`#L1891-#L1900`）

直角坐标与极坐标：

$$\begin{cases}x=r\cos\theta\\ y=r\sin\theta\end{cases}\tag{4.1}$$

另定义与射线方向对齐的旋转坐标 $(x_r,y_r)$，原点重合、$y_r$ 沿射线方向、$x_r$ 垂直射线（图4.1）。投影角 $\phi$ 下：

$$\begin{pmatrix}x_r\\ y_r\end{pmatrix}=\begin{pmatrix}\cos\phi&\sin\phi\\ -\sin\phi&\cos\phi\end{pmatrix}\begin{pmatrix}x\\ y\end{pmatrix}\tag{4.2}$$

变换矩阵行列式为 1，故面积元不变（$dx_rdy_r=dxdy$）——这是后面傅里叶切片定理推导的关键一步。

## Radon 变换（`#L1905-#L1915`）

探测器测到的强度信号，本质是射线路径上吸收系数的**线积分**；反求吸收系数分布即求 Radon 逆变换。二维 Radon 变换：

$$p(\rho,\beta)=\int_l f(x,y)\,\mathrm{d}l=\iint f(x,y)\,\delta(x\cos\beta+y\sin\beta-\rho)\,\mathrm{d}x\mathrm{d}y\tag{4.3}$$

$\delta$ 为采样函数（只在射线上取非零），$f$ 为灰度（吸收系数），$\beta$ 为旋转角。

## Radon 逆变换（`#L1915-#L1922`）

$$f(x,y)=\frac{1}{2\pi^2}\int_0^\pi\int_{-\infty}^{+\infty}\frac{1}{r\cos(\theta-\beta)-\rho}\cdot\frac{\partial p}{\partial\rho}\,\mathrm{d}\rho\,\mathrm{d}\beta\tag{4.4}$$

$$x=r\cos\theta,\quad y=r\sin\theta,\quad r=\sqrt{x^2+y^2},\quad \rho=x\cos\theta+y\sin\theta\tag{4.5}$$

## 判断

- 4.4 式的被积函数在 $r\cos(\theta-\beta)=\rho$（即积分路径恰好经过该点）时发散，属**奇异积分**；直接数值求积会不稳定，这正是工程上不用 Radon 逆变换而用 FBP/迭代法的原因。
- 4.3 式的物理含义很朴素：投影 = 沿射线的加权和。CT 重建的一切方法（解析或迭代）都是在解这个"和等于测量值"的方程组，区别只在用什么策略反解。
- 4.2 式的旋转坐标是"跟着射线走"的坐标，后面推切片定理时要把 $\phi$ 与频域角对应起来，全靠它。

## 相关

- 频域定理 → [[傅里叶切片定理]]
