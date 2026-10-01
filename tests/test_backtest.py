import pandas as pd
import pytest

from stock_backtest.backtest import run_backtest
from stock_backtest.metrics import compute_metrics


def daily(values):
    return pd.Series(values, index=pd.date_range("2025-01-01", periods=len(values)), dtype=float)


def test_未来のデータを使わない():
    # 3日目に株価が10%上がり、その日の終値を見てから買うシグナルが出る。
    # 買えるのは3日目の終値なので、この10%の上昇は取れないのが正しい。
    close = daily([100, 100, 110, 110])
    position = daily([0, 0, 1, 1])
    result = run_backtest(close, position, cost_rate=0)
    assert result.equity.iloc[-1] == pytest.approx(1.0)


def test_ずっと保有なら手数料なしでガチホと同じ():
    close = daily([100, 105, 98, 120])
    position = daily([1, 1, 1, 1])
    result = run_backtest(close, position, cost_rate=0)
    assert result.equity.iloc[-1] == pytest.approx(1.2)
    assert result.hold_equity.iloc[-1] == pytest.approx(1.2)


def test_手数料は売買のたびに引かれる():
    # 株価は変わらず、1回買って1回売る → 手数料2回分だけ減る
    close = daily([100, 100, 100, 100])
    position = daily([0, 1, 0, 0])
    result = run_backtest(close, position, cost_rate=0.01)
    assert result.equity.iloc[-1] == pytest.approx(0.99 * 0.99)


def test_ガチホも最初の買いで手数料を払う():
    close = daily([100, 100])
    result = run_backtest(close, daily([1, 1]), cost_rate=0.01)
    assert result.hold_equity.iloc[-1] == pytest.approx(0.99)


def test_指標が計算できない期間は比較から除く():
    close = daily([50, 100, 100, 120])
    position = daily([None, 1, 1, 1])
    result = run_backtest(close, position, cost_rate=0)
    # 2日目からの比較なので、ガチホも 100 → 120 の +20%
    assert result.hold_equity.iloc[-1] == pytest.approx(1.2)
    assert result.equity.index[0] == close.index[1]


def test_取引の一覧と勝率():
    close = daily([100, 110, 121, 121, 110, 99, 99])
    position = daily([1, 1, 0, 1, 1, 0, 0])
    result = run_backtest(close, position, cost_rate=0)
    trades = result.trades
    assert len(trades) == 2
    assert trades["return"].iloc[0] == pytest.approx(0.21)  # 100 → 121
    assert trades["return"].iloc[1] == pytest.approx(99 / 121 - 1)  # 121 → 99
    assert result.metrics["num_trades"] == 2
    assert result.metrics["win_rate"] == pytest.approx(0.5)


def test_保有中の取引は勝率の計算に入れない():
    close = daily([100, 110, 120])
    result = run_backtest(close, daily([1, 1, 1]), cost_rate=0)
    assert result.trades["is_open"].tolist() == [True]
    assert pd.isna(result.metrics["win_rate"])


def test_最大ドローダウン():
    # 1.0 → 1.2 → 0.9 → 1.0: 最大の下落は 1.2 から 0.9 への -25%
    equity = daily([1.2, 0.9, 1.0])
    metrics = compute_metrics(equity)
    assert metrics["max_drawdown"] == pytest.approx(-0.25)
    assert metrics["total_return"] == pytest.approx(0.0)


def test_保有率():
    close = daily([100] * 4)
    result = run_backtest(close, daily([1, 0, 0, 1]), cost_rate=0)
    assert result.metrics["exposure"] == pytest.approx(0.5)
