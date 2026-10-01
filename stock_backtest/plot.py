"""グラフの作成。どの環境でも文字化けしないよう、グラフ内の文字は英語にしている。"""

import matplotlib

matplotlib.use("Agg")  # 画面のない環境でも画像を保存できるようにする
import matplotlib.pyplot as plt
import pandas as pd

from .backtest import BacktestResult
from .indicators import sma


def plot_price_with_ma(close: pd.Series, short: int, long: int, title: str):
    """終値と2本の移動平均線。ゴールデンクロスを▲、デッドクロスを▼で表示する。"""
    short_ma, long_ma = sma(close, short), sma(close, long)
    above = (short_ma > long_ma).where(long_ma.notna())
    cross = above.astype(float).diff()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(close.index, close, label="Close", color="gray", alpha=0.6)
    ax.plot(close.index, short_ma, label=f"{short}-day MA", color="orange")
    ax.plot(close.index, long_ma, label=f"{long}-day MA", color="red")
    golden, dead = cross == 1, cross == -1
    ax.scatter(close.index[golden], close[golden], marker="^", s=90, color="green", label="Golden cross", zorder=3)
    ax.scatter(close.index[dead], close[dead], marker="v", s=90, color="black", label="Dead cross", zorder=3)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_equity(result: BacktestResult, title: str):
    """戦略とガチホの資産推移(上)と、高値からの下落率(下)。"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(result.hold_equity.index, result.hold_equity, label="Buy & Hold", color="gray")
    ax1.plot(result.equity.index, result.equity, label="Strategy", color="tab:blue")
    ax1.set_yscale("log")  # 何倍にもなる銘柄でも比較しやすいよう対数目盛
    ax1.set_ylabel("Equity (start = 1.0, log scale)")
    ax1.set_title(title)
    ax1.legend()
    ax1.grid(True, alpha=0.3, which="both")

    for equity, label, color in [(result.hold_equity, "Buy & Hold", "gray"), (result.equity, "Strategy", "tab:blue")]:
        drawdown = equity / equity.cummax().clip(lower=1.0) - 1
        ax2.plot(drawdown.index, drawdown * 100, label=label, color=color)
    ax2.set_ylabel("Drawdown (%)")
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_trades(close: pd.Series, trades: pd.DataFrame, title: str):
    """分足の価格と、買い(▲)・売り(▼)の位置。時間の空白(夜間・休日)は詰めて表示する。"""
    fig, ax = plt.subplots(figsize=(12, 5))
    x = range(len(close))
    position_of = {t: i for i, t in enumerate(close.index)}
    ax.plot(x, close.to_numpy(), color="gray", alpha=0.8, label="Close")

    shown = trades[trades["entry_time"].isin(position_of)]
    ax.scatter([position_of[t] for t in shown["entry_time"]], shown["entry_price"], marker="^", s=90, color="green", label="Buy", zorder=3)
    closed = shown[~shown["is_open"] & shown["exit_time"].isin(position_of)]
    ax.scatter([position_of[t] for t in closed["exit_time"]], closed["exit_price"], marker="v", s=90, color="red", label="Sell", zorder=3)

    # 日付の区切りに目盛りを付ける
    day_starts = [i for i, t in enumerate(close.index) if i == 0 or t.date() != close.index[i - 1].date()]
    ax.set_xticks(day_starts)
    ax.set_xticklabels([close.index[i].strftime("%m/%d") for i in day_starts])
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
