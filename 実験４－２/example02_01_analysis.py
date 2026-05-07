"""
example02_01_analysis.py

Simple time-series analysis script based on the notebooks in 実験４－２.

Usage:
  python 実験４－２/example02_01_analysis.py [--file PATH]

If no file is given, the script attempts to read `data/practice02_01_2026.csv`.
The script computes mean/variance, first differences, ADF test, ACF/PACF,
and saves plots and a summary CSV into the current folder.
"""

from pathlib import Path
import argparse
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.tsa import stattools
from statsmodels.tsa.stattools import adfuller

sns.set_style('whitegrid')


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"データファイルが見つかりません: {path}\ndata フォルダに配置してください。")
    df = pd.read_csv(path)
    return df


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Expect columns: t, y  (if other names exist, try to guess)
    if 'y' in df.columns and 't' in df.columns:
        return df[['t', 'y']].copy()
    # try common alternatives
    for col in ['value', 'y_n', 'level']:
        if col in df.columns:
            return pd.DataFrame({'t': df.index.values, 'y': df[col].values})
    # fallback: use first numeric column as y
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric) >= 1:
        return pd.DataFrame({'t': np.arange(len(df)), 'y': df[numeric[0]].values})
    raise ValueError('時系列データ列が見つかりません。CSV に数値列を用意してください。')


def analyze(df: pd.DataFrame, out_prefix: str = 'example02_01'):
    # prepare
    df = ensure_columns(df)
    y = df['y'].astype(float).reset_index(drop=True)
    t = df['t']

    # statistics
    mu = y.mean()
    var_unbiased = y.var(ddof=1)
    var_mle = y.var(ddof=0)

    # first difference
    y_diff = y.diff().dropna()

    # ADF test on original and diff
    try:
        adf_orig = adfuller(y.dropna())
    except Exception:
        adf_orig = None
    try:
        adf_diff = adfuller(y_diff)
    except Exception:
        adf_diff = None

    # ACF / PACF
    nlags = min(40, int(len(y_diff) // 2))
    acf_vals = stattools.acf(y_diff, nlags=nlags, fft=True)
    pacf_vals = stattools.pacf(y_diff, nlags=nlags)

    # Save summary
    summary = {
        'mean': mu,
        'var_unbiased': var_unbiased,
        'var_mle': var_mle,
        'n_samples': len(y),
        'n_diff_samples': len(y_diff),
    }
    if adf_orig is not None:
        summary.update({
            'adf_stat_orig': float(adf_orig[0]),
            'adf_pvalue_orig': float(adf_orig[1]),
            'adf_usedlag_orig': int(adf_orig[2])
        })
    if adf_diff is not None:
        summary.update({
            'adf_stat_diff': float(adf_diff[0]),
            'adf_pvalue_diff': float(adf_diff[1]),
            'adf_usedlag_diff': int(adf_diff[2])
        })

    Path(f'{out_prefix}_results').mkdir(exist_ok=True)
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(f'{out_prefix}_results/summary.csv', index=False)

    # Plots
    plt.figure(figsize=(12, 3))
    plt.plot(t, y, label='原系列 y')
    plt.title('原系列 y')
    plt.xlabel('t')
    plt.ylabel('y')
    plt.tight_layout()
    plt.savefig(f'{out_prefix}_results/series.png', dpi=150)
    plt.close()

    plt.figure(figsize=(12, 3))
    plt.plot(t.iloc[1:], y_diff, label='階差系列 Δy', color='C1')
    plt.title('階差系列 Δy')
    plt.xlabel('t')
    plt.ylabel('Δy')
    plt.tight_layout()
    plt.savefig(f'{out_prefix}_results/diff_series.png', dpi=150)
    plt.close()

    # histogram
    plt.figure(figsize=(6, 3))
    sns.histplot(y_diff, bins=30, kde=True)
    plt.title('階差系列のヒストグラム')
    plt.tight_layout()
    plt.savefig(f'{out_prefix}_results/diff_hist.png', dpi=150)
    plt.close()

    # ACF / PACF plots
    fig = plt.figure(figsize=(10, 6))
    ax1 = fig.add_subplot(211)
    sm.graphics.tsa.plot_acf(y_diff, lags=nlags, ax=ax1)
    ax2 = fig.add_subplot(212)
    sm.graphics.tsa.plot_pacf(y_diff, lags=nlags, ax=ax2, method='ywm')
    plt.tight_layout()
    fig.savefig(f'{out_prefix}_results/acf_pacf.png', dpi=150)
    plt.close()

    # save acf/pacf arrays
    pd.DataFrame({'lag': np.arange(len(acf_vals)), 'acf': acf_vals}).to_csv(f'{out_prefix}_results/acf.csv', index=False)
    pd.DataFrame({'lag': np.arange(len(pacf_vals)), 'pacf': pacf_vals}).to_csv(f'{out_prefix}_results/pacf.csv', index=False)

    print(f"解析結果を {out_prefix}_results/ に保存しました。summary.csv, series.png, diff_series.png, diff_hist.png, acf_pacf.png を確認してください。")


def main():
    p = argparse.ArgumentParser(description='Time-series analysis for 実験４－２')
    p.add_argument('--file', '-f', type=str, default='data/practice02_01_2026.csv', help='入力CSVファイルのパス')
    p.add_argument('--out', '-o', type=str, default='example02_01', help='出力プレフィックス')
    args = p.parse_args()

    path = Path(args.file)
    df = load_csv(path)
    analyze(df, out_prefix=args.out)


if __name__ == '__main__':
    main()
