import yfinance as yf
import matplotlib.pyplot as plt

# ターゲット：キオクシア
ticker = "285A.T"
stock = yf.Ticker(ticker)

# 過去1ヶ月分のデータを取得
data = stock.history(period="1mo")

# 【新機能】5日間の移動平均（Moving Average）を計算
# rolling(window=5) で5日分をまとめ、mean() でその平均を出します
data['MA5'] = data['Close'].rolling(window=5).mean()

# 最新のデータを取り出す
latest_close = data['Close'].iloc[-1]
latest_ma5 = data['MA5'].iloc[-1]

print(f"=== {ticker} AI判定レポート ===")
print(f"最新の終値: {latest_close:.1f}円")
print(f"5日移動平均: {latest_ma5:.1f}円")

# --- AIの判断ロジック ---
if latest_close > latest_ma5:
    diff = latest_close - latest_ma5
    print(f"【判定】買いシグナル：平均より {diff:.1f}円 高いです。上昇トレンド！")
else:
    diff = latest_ma5 - latest_close
    print(f"【判定】待機：平均より {diff:.1f}円 低いです。下落リスクがあります。")

# グラフにも移動平均線を追加
plt.figure(figsize=(10, 5))
plt.plot(data.index, data['Close'], label="Close Price", color="blue")
plt.plot(data.index, data['MA5'], label="5-day MA", color="orange", linestyle="--")

plt.title(f"{ticker} Analysis")
plt.legend()
plt.grid(True)
plt.savefig("stock_analysis.png")
print("分析グラフを stock_analysis.png として保存しました。")