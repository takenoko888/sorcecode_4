# 予習内容への回答

## (1) 任意の2組データを用いた推定（逆行列）
任意の2組として、データ番号1と2を選んだ。

- \((I_1, V_1) = (0.614,\ 22.308)\)
- \((I_2, V_2) = (0.007,\ 23.603)\)

電源モデル \(V = E - rI\) より、

\[
\begin{bmatrix}
E \\
r
\end{bmatrix}
=
\begin{bmatrix}
1 & -I_1 \\
1 & -I_2
\end{bmatrix}^{-1}
\begin{bmatrix}
V_1 \\
V_2
\end{bmatrix}
\]

に代入して計算した結果、

- 電源電圧: \(E = 23.618\ \mathrm{V}\)
- 内部抵抗: \(r = 2.133\ \Omega\)

となった。

## (2) 全8組データを用いた推定（ムーア・ペンローズ擬似逆行列）
全8組データに対して、

\[
\mathbf{X}=
\begin{bmatrix}
1 & -I_1 \\
1 & -I_2 \\
\vdots & \vdots \\
1 & -I_8
\end{bmatrix},
\quad
\mathbf{y}=
\begin{bmatrix}
V_1 \\
V_2 \\
\vdots \\
V_8
\end{bmatrix}
\]

として、

\[
\begin{bmatrix}
\hat{E} \\
\hat{r}
\end{bmatrix}
= \mathbf{X}^{+}\mathbf{y}
\]

で推定した。

ノートブック実行結果は次のとおりである。

- 電源電圧の推定値: \(\hat{E} = 23.429\ \mathrm{V}\)
- 内部抵抗の推定値: \(\hat{r} = 1.475\ \Omega\)

したがって、推定直線は

\[
\hat{V} = 23.429 - 1.475I
\]

となる。