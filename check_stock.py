import yfinance as yf
import matplotlib.pyplot as plt

# ターゲット：キオクシア
ticker = "285A.T"
stock = yf.Ticker(ticker)

# 25日平均を計算するために、少し長めに3ヶ月分（3mo）のデータを取ります
data = stock.history(period="3mo")

# 【学習ポイント】2本の移動平均線を作る
data['MA5'] = data['Close'].rolling(window=5).mean()   # 短期線
data['MA25'] = data['Close'].rolling(window=25).mean() # 長期線

# 最新のデータ（今日）と1日前のデータを取得して「クロス」を判定する
today_ma5 = data['MA5'].iloc[-1]
today_ma25 = data['MA25'].iloc[-1]
yesterday_ma5 = data['MA5'].iloc[-2]
yesterday_ma25 = data['MA25'].iloc[-2]

print(f"=== {ticker} 精密判定レポート ===")
print(f"今日: 5日線={today_ma5:.1f} / 25日線={today_ma25:.1f}")

# --- ゴールデンクロスの判定ロジック ---
# 「昨日は5日線の方が下だったのに、今日は5日線の方が上になった」という条件
if yesterday_ma5 <= yesterday_ma25 and today_ma5 > today_ma25:
    print("【★激アツ★】ゴールデンクロス発生！強力な買いシグナルです。")
elif today_ma5 > today_ma25:
    print("【判定】上昇トレンド継続中。")
elif yesterday_ma5 >= yesterday_ma25 and today_ma5 < today_ma25:
    print("【注意】デッドクロス発生。下落のサイン（売り）です。")
else:
    print("【判定】様子見、または下落トレンドです。")

# グラフに2本の線を描画
plt.figure(figsize=(12, 6))
plt.plot(data.index, data['Close'], label="Close", color="gray", alpha=0.5)
plt.plot(data.index, data['MA5'], label="5-day MA (Short)", color="orange")
plt.plot(data.index, data['MA25'], label="25-day MA (Long)", color="red")

plt.title(f"{ticker} Golden Cross Analysis")
plt.legend()
plt.grid(True)
plt.savefig("golden_cross.png")
print("分析グラフを golden_cross.png として保存しました。")