"""株価データの取得。"""

import pandas as pd
import yfinance as yf

# よく使う銘柄の表示名
TICKER_NAMES = {
    "285A.T": "キオクシア",
    "6857.T": "アドバンテスト",
    "8035.T": "東京エレクトロン",
}


def display_name(ticker: str) -> str:
    name = TICKER_NAMES.get(ticker)
    return f"{name}({ticker})" if name else ticker


def fetch_prices(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """Yahoo Finance から株価を取得する。

    period:   取得期間("6mo", "1y", "2y", "max" など)。5分足は直近60日("60d")まで
    interval: 足の間隔("1d" = 日足, "5m" = 5分足 など)
    株式分割の影響を除くため、調整後の価格(auto_adjust=True)を使う。
    """
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if data is None or data.empty:
        raise ValueError(f"{ticker} の株価を取得できませんでした。銘柄コードと期間を確認してください")

    # yfinance は列が (項目, 銘柄) の2段構成(MultiIndex)で返ってくるので1段にする
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # 分足は UTC で返ってくるので日本時間に変換する
    if data.index.tz is not None:
        data.index = data.index.tz_convert("Asia/Tokyo")

    return data.dropna(subset=["Close"])
