"""テクニカル指標の計算。

以前は pandas_ta を使っていたが、仕組みを理解するために自前で実装した。
"""

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """単純移動平均(直近 window 本の終値の平均)。"""
    return close.rolling(window=window).mean()


def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    """RSI(相対力指数)。0〜100 の値で、70以上は買われすぎ・30以下は売られすぎの目安。

    上昇幅と下落幅の平均を Wilder の平滑化(alpha = 1/length の指数移動平均)で求め、
    RSI = 100 - 100 / (1 + 平均上昇幅 / 平均下落幅) で計算する。
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()

    result = 100 - 100 / (1 + avg_gain / avg_loss)
    # 下落が一度もない区間は 0 除算になるので 100、値動きが全くない区間は 50 とする
    result = result.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    result = result.mask((avg_loss == 0) & (avg_gain == 0), 50.0)
    return result


def bollinger_bands(close: pd.Series, length: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """ボリンジャーバンド。中心線(移動平均)と、その上下に標準偏差 num_std 個分のバンド。

    標準偏差は Bollinger の定義に合わせて母標準偏差(ddof=0)を使う。
    """
    middle = sma(close, length)
    std = close.rolling(window=length).std(ddof=0)
    return pd.DataFrame(
        {
            "lower": middle - num_std * std,
            "middle": middle,
            "upper": middle + num_std * std,
        }
    )
