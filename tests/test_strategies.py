import numpy as np
import pandas as pd
import pytest

from stock_backtest.strategies import detect_cross, ma_cross_position, rsi_bb_position


def daily(values):
    return pd.Series(values, index=pd.date_range("2025-01-01", periods=len(values)), dtype=float)


def test_移動平均クロス_計算できない期間はNaN():
    close = daily(range(1, 11))
    position = ma_cross_position(close, short=2, long=5)
    assert position.iloc[:4].isna().all()
    assert position.iloc[4:].notna().all()


def test_移動平均クロス_短期線が上なら保有():
    close = daily(range(1, 11))  # 上がり続けるので短期線 > 長期線
    position = ma_cross_position(close, short=2, long=5)
    assert (position.dropna() == 1).all()


def test_移動平均クロス_短期線が下なら現金():
    close = daily(range(10, 0, -1))
    position = ma_cross_position(close, short=2, long=5)
    assert (position.dropna() == 0).all()


def test_移動平均クロス_短期が長期以上ならエラー():
    with pytest.raises(ValueError):
        ma_cross_position(daily(range(30)), short=25, long=5)


def test_ゴールデンクロスの検出():
    # 下がってから最終日に急上昇し、短期線が長期線を上抜ける
    close = daily([10, 9, 8, 7, 6, 20])
    assert detect_cross(close, short=2, long=4) == "golden"


def test_デッドクロスの検出():
    close = daily([1, 2, 3, 4, 5, -10])
    assert detect_cross(close, short=2, long=4) == "dead"


def intraday(values_per_day):
    """1日3本の足を複数日分つくる。"""
    index, values = [], []
    for day, day_values in enumerate(values_per_day):
        base = pd.Timestamp("2025-01-06 09:00", tz="Asia/Tokyo") + pd.Timedelta(days=day)
        for i, v in enumerate(day_values):
            index.append(base + pd.Timedelta(minutes=5 * i))
            values.append(v)
    return pd.Series(values, index=pd.DatetimeIndex(index), dtype=float)


def test_RSIBB_持っていないときは売らない():
    rng = np.random.default_rng(0)
    close = daily(1000 + rng.normal(0, 20, 300).cumsum())
    position = rsi_bb_position(close, flat_at_day_end=False).dropna()
    changes = position.diff().dropna()
    # 売り(-1)の直前には必ず買い(+1)がある = 持っていないのに売ることはない
    trades = changes[changes != 0].tolist()
    assert all(a != b for a, b in zip(trades, trades[1:]))
    if trades:
        assert trades[0] == 1


def test_RSIBB_デイトレは大引けで必ず手仕舞い():
    # 毎日、小さく上下したあと急落し(=買いシグナル)、そのまま大引けまで戻らない
    one_day = [100, 101] * 6 + [80, 81, 82]
    close = intraday([one_day] * 3)
    position = rsi_bb_position(close, rsi_length=3, bb_length=10)
    assert position.max() == 1  # 急落で買っている
    last_bars = position.groupby(position.index.date).tail(1)
    assert len(last_bars) == 3
    assert (last_bars.fillna(0) == 0).all()
