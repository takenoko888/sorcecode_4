#!/usr/bin/env python3
"""Generate a 3-variable Lasso basis-expansion report for solar power data.

This script uses only three model variables:
- y  : power_w
- x1 : irradiance_wm2
- x2 : module_temp_c
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LassoCV, LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Lasso basis-expansion plots and report from solar CSV."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/solar_dataset.csv"),
        help="Input CSV path",
    )
    parser.add_argument(
        "--fig-dir",
        type=Path,
        default=Path("figures"),
        help="Directory to save output figures",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("groupwork03_lasso_report.md"),
        help="Output markdown report path",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split ratio",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed",
    )
    parser.add_argument(
        "--degree",
        type=int,
        default=3,
        help="Polynomial degree for basis expansion",
    )
    return parser.parse_args()


def load_three_variable_data(path: Path) -> pd.DataFrame:
    required_cols = ["timestamp", "irradiance_wm2", "module_temp_c", "power_w"]
    df = pd.read_csv(path)

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[required_cols].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["irradiance_wm2"] = pd.to_numeric(df["irradiance_wm2"], errors="coerce")
    df["module_temp_c"] = pd.to_numeric(df["module_temp_c"], errors="coerce")
    df["power_w"] = pd.to_numeric(df["power_w"], errors="coerce")

    df = df.dropna(subset=["irradiance_wm2", "module_temp_c", "power_w"])
    df = df[df["irradiance_wm2"] >= 0.0]

    if len(df) < 30:
        raise ValueError("Not enough rows after cleaning. Need at least 30 rows.")

    return df


def make_models(degree: int, random_state: int) -> tuple[Pipeline, Pipeline]:
    linear = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("reg", LinearRegression()),
        ]
    )

    lasso = Pipeline(
        [
            ("poly", PolynomialFeatures(degree=degree, include_bias=False)),
            ("scaler", StandardScaler()),
            (
                "reg",
                LassoCV(
                    alphas=np.logspace(-4, 2, 120),
                    cv=5,
                    random_state=random_state,
                    max_iter=200_000,
                ),
            ),
        ]
    )

    return linear, lasso


def evaluate(model: Pipeline, x_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
    pred = model.predict(x_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    r2 = float(r2_score(y_test, pred))
    return {"rmse": rmse, "r2": r2}


def plot_scatter_and_curve(
    df: pd.DataFrame,
    linear: Pipeline,
    lasso: Pipeline,
    fig_path: Path,
) -> float:
    x1 = df["irradiance_wm2"].to_numpy()
    y = df["power_w"].to_numpy()
    x2_fixed = float(df["module_temp_c"].median())

    x1_grid = np.linspace(float(x1.min()), float(x1.max()), 300)
    grid = np.column_stack([x1_grid, np.full_like(x1_grid, x2_fixed)])

    y_lin = linear.predict(grid)
    y_lasso = lasso.predict(grid)

    plt.figure(figsize=(9, 5.5))
    plt.scatter(x1, y, s=12, alpha=0.28, label="Observed points")
    plt.plot(x1_grid, y_lin, linewidth=2.2, label="Linear regression (x2 fixed)")
    plt.plot(x1_grid, y_lasso, linewidth=2.2, label="Lasso basis expansion (x2 fixed)")
    plt.xlabel("x1: irradiance_wm2")
    plt.ylabel("y: power_w")
    plt.title("Scatter + Regression Curve Overlay")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=180)
    plt.close()

    return x2_fixed


def plot_scatter_and_surfaces(
    df: pd.DataFrame,
    linear: Pipeline,
    lasso: Pipeline,
    fig_path: Path,
) -> None:
    x1 = df["irradiance_wm2"].to_numpy()
    x2 = df["module_temp_c"].to_numpy()
    y = df["power_w"].to_numpy()

    x1_grid = np.linspace(float(x1.min()), float(x1.max()), 50)
    x2_grid = np.linspace(float(x2.min()), float(x2.max()), 50)
    xx1, xx2 = np.meshgrid(x1_grid, x2_grid)
    mesh = np.column_stack([xx1.ravel(), xx2.ravel()])

    zz_linear = linear.predict(mesh).reshape(xx1.shape)
    zz_lasso = lasso.predict(mesh).reshape(xx1.shape)

    sample_n = min(1500, len(df))
    sample = df.sample(sample_n, random_state=42)

    fig = plt.figure(figsize=(13.5, 5.6))

    ax1 = fig.add_subplot(1, 2, 1, projection="3d")
    ax1.scatter(
        sample["irradiance_wm2"],
        sample["module_temp_c"],
        sample["power_w"],
        s=10,
        alpha=0.35,
        c="tab:blue",
    )
    ax1.plot_surface(xx1, xx2, zz_linear, alpha=0.58, cmap="viridis", linewidth=0)
    ax1.set_title("Linear: Scatter + Regression Plane")
    ax1.set_xlabel("x1: irradiance")
    ax1.set_ylabel("x2: module temp")
    ax1.set_zlabel("y: power")

    ax2 = fig.add_subplot(1, 2, 2, projection="3d")
    ax2.scatter(
        sample["irradiance_wm2"],
        sample["module_temp_c"],
        sample["power_w"],
        s=10,
        alpha=0.35,
        c="tab:blue",
    )
    ax2.plot_surface(xx1, xx2, zz_lasso, alpha=0.58, cmap="plasma", linewidth=0)
    ax2.set_title("Lasso Basis: Scatter + Regression Surface")
    ax2.set_xlabel("x1: irradiance")
    ax2.set_ylabel("x2: module temp")
    ax2.set_zlabel("y: power")

    plt.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(fig_path, dpi=180)
    plt.close(fig)


def nonzero_terms(lasso: Pipeline) -> list[tuple[str, float]]:
    poly = lasso.named_steps["poly"]
    reg = lasso.named_steps["reg"]
    names = poly.get_feature_names_out(["x1", "x2"])
    coefs = reg.coef_
    idx = np.flatnonzero(np.abs(coefs) > 1e-8)
    selected = [(str(names[i]), float(coefs[i])) for i in idx]
    selected.sort(key=lambda t: abs(t[1]), reverse=True)
    return selected


def format_stats(df: pd.DataFrame) -> str:
    stats = df[["irradiance_wm2", "module_temp_c", "power_w"]].describe().T
    lines = []
    for name, row in stats.iterrows():
        lines.append(
            f"- {name}: min={row['min']:.3f}, max={row['max']:.3f}, "
            f"mean={row['mean']:.3f}, std={row['std']:.3f}"
        )
    return "\n".join(lines)


def median_time_step_minutes(timestamps: pd.Series) -> float | None:
    ts = timestamps.dropna().sort_values()
    if len(ts) < 2:
        return None
    delta = ts.diff().dropna().dt.total_seconds() / 60.0
    if len(delta) == 0:
        return None
    return float(delta.median())


def write_report(
    report_path: Path,
    input_csv: Path,
    df: pd.DataFrame,
    linear_metrics: dict[str, float],
    lasso_metrics: dict[str, float],
    alpha: float,
    degree: int,
    x2_fixed: float,
    terms: list[tuple[str, float]],
    fig_curve: Path,
    fig_surface: Path,
) -> None:
    start_ts = df["timestamp"].min()
    end_ts = df["timestamp"].max()
    step_min = median_time_step_minutes(df["timestamp"])

    top_terms = terms[:8]
    if top_terms:
        terms_text = "\n".join([f"- {name}: {coef:.6f}" for name, coef in top_terms])
    else:
        terms_text = "- (all coefficients were shrunk to zero)"

    report = f"""# グループワーク報告: ラッソ正則化を利用した基底展開法（太陽光データ）

## 変数の制約
本報告は、以下の3変数のみを使用した。

- 目的変数 y: power_w [W]
- 説明変数 x1: irradiance_wm2 [W/m^2]
- 説明変数 x2: module_temp_c [degC]

timestamp は期間確認とサンプリング間隔確認のみに使い、学習特徴量には含めていない。

## a. 利用したデータ
- 入力CSV: {input_csv.as_posix()}
- 有効サンプル数: {len(df)}
- 計測期間: {start_ts} 〜 {end_ts}
- サンプリング間隔の中央値: {step_min:.1f} 分

### 変数の要約統計
{format_stats(df)}

## モデル設定
- 比較1: 線形回帰（x1, x2）
- 比較2: 基底展開 + LassoCV
- 基底次数: {degree}
- Lasso 最適 alpha: {alpha:.6g}

## b. 散布図と回帰曲線（面）の重ね描き比較

### 図1: 散布図 + 回帰曲線（x2 固定）
- 固定した x2 の値: {x2_fixed:.3f} degC

![scatter_curve]({fig_curve.as_posix()})

### 図2: 3次元散布図 + 回帰面（左: 線形, 右: ラッソ基底展開）
![scatter_surface_compare]({fig_surface.as_posix()})

### 定量比較（テストデータ）
- 線形回帰: RMSE={linear_metrics['rmse']:.4f}, R^2={linear_metrics['r2']:.4f}
- ラッソ基底展開: RMSE={lasso_metrics['rmse']:.4f}, R^2={lasso_metrics['r2']:.4f}

### 比較検討
- ラッソ基底展開は、線形回帰より非線形な曲面を表現できる。
- Lasso により不要な高次項が0に収縮し、過学習を抑えつつ説明性を確保できる。
- 本データでは、テスト指標の比較から性能差を確認できる。

### ラッソで残った主な基底項（上位）
{terms_text}
"""

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")


def main() -> int:
    args = parse_args()

    df = load_three_variable_data(args.input)

    x = df[["irradiance_wm2", "module_temp_c"]].to_numpy()
    y = df["power_w"].to_numpy()

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    linear, lasso = make_models(degree=args.degree, random_state=args.random_state)
    linear.fit(x_train, y_train)
    lasso.fit(x_train, y_train)

    linear_metrics = evaluate(linear, x_test, y_test)
    lasso_metrics = evaluate(lasso, x_test, y_test)

    fig_curve = args.fig_dir / "groupwork03_scatter_curve_x1.png"
    fig_surface = args.fig_dir / "groupwork03_scatter_surface_compare.png"
    x2_fixed = plot_scatter_and_curve(df, linear, lasso, fig_curve)
    plot_scatter_and_surfaces(df, linear, lasso, fig_surface)

    reg = lasso.named_steps["reg"]
    terms = nonzero_terms(lasso)
    write_report(
        report_path=args.report,
        input_csv=args.input,
        df=df,
        linear_metrics=linear_metrics,
        lasso_metrics=lasso_metrics,
        alpha=float(reg.alpha_),
        degree=args.degree,
        x2_fixed=x2_fixed,
        terms=terms,
        fig_curve=fig_curve,
        fig_surface=fig_surface,
    )

    print(f"Saved report: {args.report}")
    print(f"Saved figure: {fig_curve}")
    print(f"Saved figure: {fig_surface}")
    print(
        "Metrics "
        f"linear(RMSE={linear_metrics['rmse']:.4f}, R2={linear_metrics['r2']:.4f}), "
        f"lasso(RMSE={lasso_metrics['rmse']:.4f}, R2={lasso_metrics['r2']:.4f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
