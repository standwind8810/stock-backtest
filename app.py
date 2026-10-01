"""ブラウザで使える Web 版。

    streamlit run app.py
"""

import pandas as pd
import streamlit as st

from stock_backtest.backtest import run_backtest
from stock_backtest.data import TICKER_NAMES, display_name, fetch_prices
from stock_backtest.plot import plot_price_with_ma, plot_trades
from stock_backtest.report import num, pct
from stock_backtest.strategies import ma_cross_position, rsi_bb_position

st.set_page_config(page_title="株の売買ルール検証", layout="wide")
st.title("株の売買ルール検証ツール")
st.caption("売買ルールに従って売買した場合と、最初に買ってずっと持っていた場合(ガチホ)を比較します。投資助言ではありません。")


@st.cache_data(ttl=3600, show_spinner="株価を取得しています…")
def load_close(ticker: str, period: str, interval: str) -> pd.Series:
    return fetch_prices(ticker, period=period, interval=interval)["Close"]


with st.sidebar:
    st.header("設定")
    options = [*TICKER_NAMES, "その他(入力)"]
    choice = st.selectbox("銘柄", options, format_func=lambda t: display_name(t) if t in TICKER_NAMES else t)
    ticker = st.text_input("銘柄コード(例: 7203.T)", "7203.T") if choice == "その他(入力)" else choice

    strategy = st.radio("戦略", ["移動平均クロス(日足)", "RSI + ボリンジャーバンド(5分足デイトレ)"])
    if strategy.startswith("移動平均"):
        period = st.selectbox("期間", ["1y", "2y", "5y", "10y", "max"], index=1)
        short = st.slider("短期移動平均(日)", 2, 50, 5)
        long = st.slider("長期移動平均(日)", 5, 200, 25)
    else:
        period = "60d"
        st.caption("5分足は Yahoo Finance の制限で直近60日分のみ取得できます")
    cost = st.number_input("売買1回あたりのコスト(%)", 0.0, 2.0, 0.1, step=0.05) / 100

try:
    if strategy.startswith("移動平均"):
        if short >= long:
            st.error("短期移動平均は長期移動平均より短くしてください")
            st.stop()
        close = load_close(ticker, period, "1d")
        position = ma_cross_position(close, short, long)
    else:
        close = load_close(ticker, period, "5m")
        position = rsi_bb_position(close)
    result = run_backtest(close, position, cost_rate=cost)
except ValueError as e:
    st.error(str(e))
    st.stop()

m, h = result.metrics, result.hold_metrics
st.subheader(f"{display_name(ticker)}  {m['start']:%Y-%m-%d} 〜 {m['end']:%Y-%m-%d}")

diff = m["total_return"] - h["total_return"]
verdict = "戦略がガチホに勝ちました" if diff > 0 else "戦略はガチホに負けました"
st.markdown(f"**{verdict}**(利益率の差 {pct(diff)})")

cols = st.columns(4)
cols[0].metric("利益率(戦略)", pct(m["total_return"]), f"ガチホ {pct(h['total_return'])}", delta_color="off")
cols[1].metric("最大ドローダウン(戦略)", pct(m["max_drawdown"]), f"ガチホ {pct(h['max_drawdown'])}", delta_color="off")
cols[2].metric("シャープレシオ(戦略)", num(m["sharpe"]), f"ガチホ {num(h['sharpe'])}", delta_color="off")
cols[3].metric("売買回数 / 勝率", f"{m['num_trades']} 回", f"勝率 {pct(m['win_rate'], signed=False)}", delta_color="off")

st.markdown("#### 資産の推移(初期資産 = 1.0)")
st.line_chart(pd.DataFrame({"戦略": result.equity, "ガチホ": result.hold_equity}))

st.markdown("#### 高値からの下落率(%)")
drawdowns = {
    name: (equity / equity.cummax().clip(lower=1.0) - 1) * 100
    for name, equity in [("戦略", result.equity), ("ガチホ", result.hold_equity)]
}
st.line_chart(pd.DataFrame(drawdowns))

if strategy.startswith("移動平均"):
    st.markdown("#### 株価と移動平均線")
    st.pyplot(plot_price_with_ma(close, short, long, f"{ticker} {short}/{long}-day MA"))
else:
    st.markdown("#### 直近5日の売買")
    recent = close[close.index.normalize() >= close.index.normalize().unique()[-5]]
    st.pyplot(plot_trades(recent, result.trades, f"{ticker} RSI + Bollinger (last 5 days)"))

st.markdown("#### 取引の一覧")
trades = result.trades.rename(
    columns={
        "entry_time": "買った日時",
        "entry_price": "買値",
        "exit_time": "売った日時",
        "exit_price": "売値",
        "return": "利益率",
        "is_open": "保有中",
    }
)
st.dataframe(trades.style.format({"利益率": "{:+.2%}", "買値": "{:,.0f}", "売値": "{:,.0f}"}), width="stretch")
