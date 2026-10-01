"""戦略の良し悪しを測る評価指標。"""

import numpy as np
import pandas as pd

# 東証の1年あたりの営業日数(おおよそ)
TRADING_DAYS_PER_YEAR = 245


def compute_metrics(
    equity: pd.Series,
    position: pd.Series | None = None,
    trades: pd.DataFrame | None = None,
) -> dict:
    """資産推移(初期資産 1.0)から評価指標を計算する。

    total_return:  最終的な利益率
    max_drawdown:  途中で資産が最も大きく減った割合(-0.3 なら高値から30%減ったことがある)
    sharpe:        シャープレシオ。リスク(日々の値動きのブレ)1単位あたりのリターン。年率換算
    exposure:      株を持っていた期間の割合
    num_trades:    売買の回数(1回 = 買って売るまで)
    win_rate:      利益が出た取引の割合(決済済みの取引のみ)
    """
    values = np.concatenate([[1.0], equity.to_numpy()])
    peak = np.maximum.accumulate(values)

    # 分足でも日足でも同じ基準で比べられるように、1日ごとのリターンにしてから計算する
    daily_equity = equity.groupby(equity.index.normalize()).last()
    daily_returns = pd.concat([pd.Series([1.0]), daily_equity]).pct_change().dropna()
    std = daily_returns.std()
    sharpe = daily_returns.mean() / std * np.sqrt(TRADING_DAYS_PER_YEAR) if std > 0 else np.nan

    metrics = {
        "start": equity.index[0],
        "end": equity.index[-1],
        "total_return": values[-1] - 1,
        "max_drawdown": (values / peak - 1).min(),
        "sharpe": sharpe,
    }
    if position is not None:
        metrics["exposure"] = position.mean()
    if trades is not None:
        closed = trades[~trades["is_open"]]
        metrics["num_trades"] = len(trades)
        metrics["win_rate"] = (closed["return"] > 0).mean() if len(closed) else np.nan
    return metrics
