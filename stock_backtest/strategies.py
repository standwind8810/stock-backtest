"""売買ルール。

どの関数も「その足の終値を見て判断した結果、次の足まで株を持つか」を
1(保有)/ 0(現金)の Series で返す。指標が計算できない期間は NaN。
"""

import pandas as pd

from .indicators import bollinger_bands, rsi, sma


def ma_cross_position(close: pd.Series, short: int = 5, long: int = 25) -> pd.Series:
    """移動平均クロス戦略。短期線が長期線より上なら保有、下なら現金。

    ゴールデンクロスで買い、デッドクロスで売るのと同じ意味になる。
    """
    if short >= long:
        raise ValueError(f"短期({short}日)は長期({long}日)より短くしてください")
    short_ma = sma(close, short)
    long_ma = sma(close, long)
    position = (short_ma > long_ma).astype(float)
    return position.where(long_ma.notna())


def detect_cross(close: pd.Series, short: int = 5, long: int = 25) -> str:
    """最新の足で何が起きたかを返す。

    "golden": ゴールデンクロス(昨日は短期線が下、今日は上)
    "dead":   デッドクロス(昨日は短期線が上、今日は下)
    "up":     上昇トレンド継続(短期線が上のまま)
    "down":   下落トレンド継続(短期線が下のまま)
    """
    position = ma_cross_position(close, short, long).dropna()
    if len(position) < 2:
        raise ValueError(f"判定には少なくとも {long + 1} 本のデータが必要です")
    yesterday, today = position.iloc[-2], position.iloc[-1]
    if yesterday == 0 and today == 1:
        return "golden"
    if yesterday == 1 and today == 0:
        return "dead"
    return "up" if today == 1 else "down"


def rsi_bb_position(
    close: pd.Series,
    rsi_length: int = 14,
    bb_length: int = 20,
    bb_std: float = 2.0,
    entry_rsi: float = 30,
    exit_rsi: float = 70,
    flat_at_day_end: bool = True,
) -> pd.Series:
    """RSI + ボリンジャーバンドの逆張り戦略(デイトレ用)。

    買い: 現金のとき、RSI < entry_rsi かつ 終値 < バンド下限(売られすぎ)
    売り: 保有中のとき、RSI > exit_rsi かつ 終値 > バンド上限(買われすぎ)
    flat_at_day_end=True なら、その日の最後の足で必ず手仕舞いし、翌日に持ち越さない。
    """
    rsi_values = rsi(close, rsi_length)
    bands = bollinger_bands(close, bb_length, bb_std)
    entry = (rsi_values < entry_rsi) & (close < bands["lower"])
    exit_ = (rsi_values > exit_rsi) & (close > bands["upper"])

    dates = close.index.normalize()
    if flat_at_day_end:
        is_last_bar = pd.Series(dates, index=close.index) != pd.Series(dates, index=close.index).shift(-1)
    else:
        is_last_bar = pd.Series(False, index=close.index)

    # 「今持っているか」で判断が変わるので、1本ずつ順番に状態を更新する
    holding = False
    positions = []
    for is_entry, is_exit, last in zip(entry, exit_, is_last_bar):
        if holding and (is_exit or last):
            holding = False
        elif not holding and is_entry and not last:
            holding = True
        positions.append(1.0 if holding else 0.0)

    position = pd.Series(positions, index=close.index)
    ready = rsi_values.notna() & bands["lower"].notna()
    return position.where(ready)
