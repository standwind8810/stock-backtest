import numpy as np
import pandas as pd
import pytest

from stock_backtest.indicators import bollinger_bands, rsi, sma


def make_series(values):
    return pd.Series(values, index=pd.date_range("2025-01-01", periods=len(values)), dtype=float)


def test_sma_は直近n日の平均():
    close = make_series([1, 2, 3, 4, 5])
    result = sma(close, 3)
    assert result.isna().sum() == 2  # 最初の2日は計算できない
    assert result.iloc[-1] == pytest.approx(4.0)  # (3+4+5)/3


def test_rsi_上がり続けると100():
    close = make_series(range(1, 31))
    result = rsi(close, 14)
    assert result.iloc[:14].isna().all()
    assert (result.iloc[14:] == 100).all()


def test_rsi_下がり続けると0():
    close = make_series(range(30, 0, -1))
    result = rsi(close, 14)
    assert (result.iloc[14:] == 0).all()


def test_rsi_は0から100の範囲():
    rng = np.random.default_rng(0)
    close = make_series(100 + rng.normal(0, 1, 200).cumsum())
    result = rsi(close, 14).dropna()
    assert result.between(0, 100).all()


def test_ボリンジャーバンド_値動きがなければ3本が一致():
    close = make_series([100] * 25)
    bands = bollinger_bands(close, 20, 2)
    last = bands.iloc[-1]
    assert last["lower"] == last["middle"] == last["upper"] == 100


def test_ボリンジャーバンド_上限と下限は中心から標準偏差の2倍():
    close = make_series([1, 2, 3, 4, 5])
    bands = bollinger_bands(close, 5, 2)
    std = np.std([1, 2, 3, 4, 5])  # 母標準偏差(ddof=0)
    assert bands["upper"].iloc[-1] == pytest.approx(3 + 2 * std)
    assert bands["lower"].iloc[-1] == pytest.approx(3 - 2 * std)
