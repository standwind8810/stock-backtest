"""売買ルールを過去の株価で検証する(バックテスト)。"""

from dataclasses import dataclass

import pandas as pd

from .metrics import compute_metrics


@dataclass
class BacktestResult:
    equity: pd.Series  # 戦略の資産推移(初期資産 1.0)
    hold_equity: pd.Series  # 最初に買ってずっと持っていた場合(ガチホ)の資産推移
    position: pd.Series  # 各足の終値時点で決めたポジション(1: 保有, 0: 現金)
    trades: pd.DataFrame  # 取引の一覧
    metrics: dict  # 戦略の評価指標
    hold_metrics: dict  # ガチホの評価指標


def run_backtest(close: pd.Series, position: pd.Series, cost_rate: float = 0.001) -> BacktestResult:
    """戦略とガチホを、同じ期間・同じ手数料で比較する。

    - position[t] は「t の終値を見て決め、t の終値で売買した結果、次の足まで持つか」。
      t の値上がりは t-1 のポジションにだけ反映する(shift(1))ので、未来のデータは使わない。
    - cost_rate は売買1回あたりのコスト(手数料 + スプレッドなど)。0.001 なら 0.1%。
    - 指標が計算できない期間(position が NaN)は、戦略もガチホも比較から除く。
    """
    position = position.dropna()
    if position.empty:
        raise ValueError("データが少なすぎて指標を計算できません。期間を長くしてください")
    close = close.loc[position.index]
    position = position.astype(int)

    returns = close.pct_change().fillna(0.0)
    held = position.shift(1).fillna(0)
    # ポジションが変わった足で売買が発生する(最初の足で保有なら、そこで買う)
    turnover = position.diff().abs().fillna(position.iloc[0])
    strategy_returns = held * returns - cost_rate * turnover
    equity = (1 + strategy_returns).cumprod()

    hold_returns = returns.copy()
    hold_returns.iloc[0] = -cost_rate  # 最初に1回だけ買う
    hold_equity = (1 + hold_returns).cumprod()

    trades = extract_trades(close, position, equity)
    return BacktestResult(
        equity=equity,
        hold_equity=hold_equity,
        position=position,
        trades=trades,
        metrics=compute_metrics(equity, position, trades),
        hold_metrics=compute_metrics(hold_equity),
    )


def extract_trades(close: pd.Series, position: pd.Series, equity: pd.Series) -> pd.DataFrame:
    """ポジションの変化から、1回ごとの取引(買い → 売り)を取り出す。

    取引の利益率は手数料込みの資産の増減で計算する。最後まで持っている取引は is_open=True。
    """
    changes = position.diff().fillna(position.iloc[0])
    entries = position.index[changes == 1]
    exits = position.index[changes == -1]
    equity_before = equity.shift(1).fillna(1.0)

    rows = []
    for i, entry in enumerate(entries):
        is_open = i >= len(exits)
        exit_ = position.index[-1] if is_open else exits[i]
        rows.append(
            {
                "entry_time": entry,
                "entry_price": close[entry],
                "exit_time": exit_,
                "exit_price": close[exit_],
                "return": equity[exit_] / equity_before[entry] - 1,
                "is_open": is_open,
            }
        )
    columns = ["entry_time", "entry_price", "exit_time", "exit_price", "return", "is_open"]
    return pd.DataFrame(rows, columns=columns)
