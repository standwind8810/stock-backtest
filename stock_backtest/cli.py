"""コマンドラインから使うための入口。

    python -m stock_backtest check 285A.T 6857.T 8035.T
    python -m stock_backtest backtest 285A.T --short 5 --long 25
    python -m stock_backtest compare 285A.T 6857.T 8035.T
    python -m stock_backtest daytrade 285A.T
"""

import argparse
from pathlib import Path

from .backtest import run_backtest
from .data import display_name, fetch_prices
from .plot import plot_equity, plot_price_with_ma, plot_trades
from .report import compare_table, period_text, result_table
from .strategies import detect_cross, ma_cross_position, rsi_bb_position

CROSS_MESSAGES = {
    "golden": "ゴールデンクロス発生(短期線が長期線を上抜け): 買いシグナル",
    "dead": "デッドクロス発生(短期線が長期線を下抜け): 売りシグナル",
    "up": "上昇トレンド継続中(短期線 > 長期線)",
    "down": "下落トレンド継続中(短期線 < 長期線)",
}


def save(fig, out_dir: Path, filename: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    fig.savefig(path, dpi=110)
    return path


def file_stem(ticker: str) -> str:
    return ticker.replace(".", "_")


def cmd_check(args):
    for ticker in args.tickers:
        close = fetch_prices(ticker, period="6mo")["Close"]
        short_ma = close.rolling(args.short).mean().iloc[-1]
        long_ma = close.rolling(args.long).mean().iloc[-1]
        print(f"=== {display_name(ticker)} {close.index[-1]:%Y-%m-%d} ===")
        print(f"終値={close.iloc[-1]:,.1f} / {args.short}日線={short_ma:,.1f} / {args.long}日線={long_ma:,.1f}")
        print(CROSS_MESSAGES[detect_cross(close, args.short, args.long)])
        fig = plot_price_with_ma(close, args.short, args.long, f"{ticker} {args.short}/{args.long}-day MA")
        print(f"グラフ: {save(fig, args.out, f'{file_stem(ticker)}_ma.png')}\n")


def backtest_ma(ticker: str, args):
    close = fetch_prices(ticker, period=args.period)["Close"]
    position = ma_cross_position(close, args.short, args.long)
    return run_backtest(close, position, cost_rate=args.cost)


def cmd_backtest(args):
    result = backtest_ma(args.ticker, args)
    print(f"=== {display_name(args.ticker)} 移動平均クロス({args.short}日/{args.long}日)===")
    print(f"期間: {period_text(result)} / 手数料: 片道 {args.cost:.2%}\n")
    print(result_table(result))
    title = f"{args.ticker} MA cross ({args.short}/{args.long}) vs Buy & Hold"
    print(f"\nグラフ: {save(plot_equity(result, title), args.out, f'{file_stem(args.ticker)}_backtest.png')}")


def cmd_compare(args):
    results = {}
    for ticker in args.tickers:
        result = backtest_ma(ticker, args)
        results[display_name(ticker)] = result
        title = f"{ticker} MA cross ({args.short}/{args.long}) vs Buy & Hold"
        save(plot_equity(result, title), args.out, f"{file_stem(ticker)}_backtest.png")

    header = f"移動平均クロス({args.short}日/{args.long}日)とガチホの比較 / 手数料: 片道 {args.cost:.2%}"
    lines = [header, ""]
    for name, r in results.items():
        lines.append(f"- {name}: {period_text(r)}")
    table = compare_table(results)
    text = "\n".join(lines) + "\n\n" + table + "\n"
    print(text)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "compare.md").write_text(text, encoding="utf-8")
    print(f"表とグラフを {args.out} に保存しました")


def cmd_daytrade(args):
    close = fetch_prices(args.ticker, period=args.period, interval=args.interval)["Close"]
    position = rsi_bb_position(close)
    result = run_backtest(close, position, cost_rate=args.cost)

    print(f"=== {display_name(args.ticker)} デイトレ戦略(RSI + ボリンジャーバンド, {args.interval}足)===")
    print(f"期間: {period_text(result)} / 手数料: 片道 {args.cost:.2%}")
    print("ルール: RSI<30 かつ バンド下限割れで買い、RSI>70 かつ バンド上限超えで売り、大引けで必ず手仕舞い\n")
    print(result_table(result))

    trades = result.trades
    if trades.empty:
        print("\nこの期間に売買はありませんでした")
    else:
        print(f"\n直近の取引(最大{args.recent}件):")
        for t in trades.tail(args.recent).to_dict("records"):
            exit_text = "保有中" if t["is_open"] else f"{t['exit_time']:%m/%d %H:%M} 売り {t['exit_price']:,.0f}"
            print(f"  {t['entry_time']:%m/%d %H:%M} 買い {t['entry_price']:,.0f} → {exit_text}  ({t['return']:+.2%})")

    recent = close[close.index.normalize() >= close.index.normalize().unique()[-5]]
    fig = plot_trades(recent, trades, f"{args.ticker} RSI + Bollinger day trade (last 5 days)")
    print(f"\nグラフ: {save(fig, args.out, f'{file_stem(args.ticker)}_daytrade.png')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m stock_backtest", description="売買ルールを過去の株価で検証するツール")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p):
        p.add_argument("--out", type=Path, default=Path("output"), help="グラフなどの保存先(デフォルト: output)")

    def add_ma(p):
        p.add_argument("--short", type=int, default=5, help="短期移動平均の日数(デフォルト: 5)")
        p.add_argument("--long", type=int, default=25, help="長期移動平均の日数(デフォルト: 25)")

    def add_cost(p):
        p.add_argument("--cost", type=float, default=0.001, help="売買1回あたりのコスト率(デフォルト: 0.001 = 0.1%%)")

    p = sub.add_parser("check", help="最新のゴールデンクロス/デッドクロスを判定する")
    p.add_argument("tickers", nargs="+", help="銘柄コード(例: 285A.T)")
    add_ma(p)
    add_common(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("backtest", help="移動平均クロス戦略をガチホと比較する")
    p.add_argument("ticker", help="銘柄コード(例: 285A.T)")
    p.add_argument("--period", default="2y", help="検証期間(例: 1y, 2y, 5y, max。デフォルト: 2y)")
    add_ma(p)
    add_cost(p)
    add_common(p)
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("compare", help="複数銘柄でまとめて比較する")
    p.add_argument("tickers", nargs="+", help="銘柄コード(例: 285A.T 6857.T 8035.T)")
    p.add_argument("--period", default="2y", help="検証期間(デフォルト: 2y)")
    add_ma(p)
    add_cost(p)
    add_common(p)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("daytrade", help="RSI + ボリンジャーバンドのデイトレ戦略を検証する")
    p.add_argument("ticker", help="銘柄コード(例: 285A.T)")
    p.add_argument("--period", default="60d", help="検証期間(5分足は最大60日。デフォルト: 60d)")
    p.add_argument("--interval", default="5m", help="足の間隔(デフォルト: 5m)")
    p.add_argument("--recent", type=int, default=10, help="表示する直近の取引数(デフォルト: 10)")
    add_cost(p)
    add_common(p)
    p.set_defaults(func=cmd_daytrade)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        raise SystemExit(f"エラー: {e}")
