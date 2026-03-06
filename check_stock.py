import yfinance as yf

# ターゲットを修正：285A: キオクシア, 6857: アドバンテスト, 8035: 東京エレクトロン
targets = ["285A.T", "6857.T", "8035.T"]

print("=== 半導体関連 銘柄一括チェック開始 ===")

for ticker in targets:
    stock = yf.Ticker(ticker)
    data = stock.history(period='2d') # 今日と昨日のデータを取得
    
    # データが2日分以上（今日と昨日）あるか確認
    if not data.empty and len(data) >= 2:
        latest = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        diff = latest - prev
        
        # 値上がりの場合は▲、それ以外は▼を表示
        status = "▲" if diff > 0 else "▼"
        
        # 見やすくフォーマットして表示
        # {latest:8.1f} は「合計8桁、小数点以下1桁」という意味です
        print(f"[{ticker}] {latest:8.1f}円 ({status} {diff:+6.1f}円)")
    else:
        print(f"[{ticker}] データの取得に失敗しました。市場が閉まっているか上場直後の可能性があります。")

print("======================================")