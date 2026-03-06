import yfinance as yf
import pandas_ta as ta
import pandas as pd

# 1. 5分足データの取得
ticker = "285A.T"
data = yf.download(ticker, period="5d", interval="5m")

# yfinanceの階層構造（MultiIndex）を平坦化
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

# 【追加】タイムゾーンを日本時間（Asia/Tokyo）に変換
data.index = data.index.tz_convert('Asia/Tokyo')

# 2. テクニカル指標の計算
data['RSI'] = ta.rsi(data['Close'], length=14)
bb_data = ta.bbands(data['Close'], length=20, std=2)

# 実際の列名を動的に特定（BBLやBBUが含まれるものを探す）
bbl_name = [c for c in bb_data.columns if 'BBL' in c][0]
bbu_name = [c for c in bb_data.columns if 'BBU' in c][0]

# データを結合
data = pd.concat([data, bb_data], axis=1)

# 3. 短期売買ロジック
# 買い：RSI 30以下 かつ ボリンジャーバンド下限を下回る
data['Entry'] = (data['RSI'] < 30) & (data['Close'] < data[bbl_name])
# 売り：RSI 70以上 かつ ボリンジャーバンド上限を上回る
data['Exit'] = (data['RSI'] > 70) & (data['Close'] > data[bbu_name])

print(f"=== {ticker} デイトレ・シグナル確認 (日本時間) ===")

# シグナルが出た行（Trueの行）を抽出
signals = data[(data['Entry'] == True) | (data['Exit'] == True)]

if not signals.empty:
    # 重要な列だけ選んで、最新15件を表示
    # インデックス（時間）の書式を「2026-03-06 09:05」のような形式に整える
    output = signals[['Close', 'RSI', 'Entry', 'Exit']].copy()
    output.index = output.index.strftime('%Y-%m-%d %H:%M')
    print(output.tail(15))
else:
    print("現在、買い/売りのシグナルは出ていません。")