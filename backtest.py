import yfinance as yf
import pandas as pd

# ターゲット：キオクシア（285A.T）
ticker = "285A.T"
# 過去2年分くらいのデータを取って検証します
data = yf.download(ticker, period="2y")

# 移動平均線の計算
data['MA5'] = data['Close'].rolling(window=5).mean()
data['MA25'] = data['Close'].rolling(window=25).mean()

# 売買シグナルの作成 (1: 買い, -1: 売り, 0: 待機)
data['Signal'] = 0
# ゴールデンクロス（5日線 > 25日線）のときに1
data.loc[data['MA5'] > data['MA25'], 'Signal'] = 1

# 前日からのシグナルの変化（売買タイミング）を特定
data['Action'] = data['Signal'].diff()

# 利益の計算（単純なホールド時の利益と比較）
data['Return'] = data['Close'].pct_change() # 1日ごとの騰落率
data['Strategy_Return'] = data['Return'] * data['Signal'].shift(1) # 戦略に従った利益

# 累積利益（資産がどう増えたか）
cumulative_return = (1 + data['Strategy_Return'].fillna(0)).cumprod()

print(f"=== {ticker} バックテスト結果 ===")
final_profit = (cumulative_return.iloc[-1] - 1) * 100
print(f"この1年間の合計利益率: {final_profit:.2f} %")

# 資産推移を保存
import matplotlib.pyplot as plt
cumulative_return.plot(figsize=(10, 6), title=f"{ticker} Backtest Strategy")
plt.savefig("backtest_result.png")