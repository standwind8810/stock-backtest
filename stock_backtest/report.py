"""結果を表(Markdown 形式)にする。README にそのまま貼れる。"""

import math

from .backtest import BacktestResult


def pct(value: float, signed: bool = True) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value * 100:+,.1f}%" if signed else f"{value * 100:,.1f}%"


def num(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value:.2f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def period_text(result: BacktestResult) -> str:
    start, end = result.metrics["start"], result.metrics["end"]
    return f"{start:%Y-%m-%d} 〜 {end:%Y-%m-%d}"


def result_table(result: BacktestResult) -> str:
    """1銘柄の結果を、戦略とガチホで並べた表。"""
    m, h = result.metrics, result.hold_metrics
    rows = [
        ["利益率", pct(m["total_return"]), pct(h["total_return"])],
        ["最大ドローダウン", pct(m["max_drawdown"]), pct(h["max_drawdown"])],
        ["シャープレシオ", num(m["sharpe"]), num(h["sharpe"])],
        ["保有率", pct(m["exposure"], signed=False), "100.0%"],
        ["売買回数", str(m["num_trades"]), "1"],
        ["勝率", pct(m["win_rate"], signed=False), "-"],
    ]
    return markdown_table(["指標", "戦略", "ガチホ"], rows)


def compare_table(results: dict[str, BacktestResult]) -> str:
    """複数銘柄の結果を1つの表にまとめる。"""
    rows = []
    for name, r in results.items():
        m, h = r.metrics, r.hold_metrics
        rows.append(
            [
                name,
                pct(m["total_return"]),
                pct(h["total_return"]),
                pct(m["max_drawdown"]),
                pct(h["max_drawdown"]),
                num(m["sharpe"]),
                num(h["sharpe"]),
                str(m["num_trades"]),
                pct(m["win_rate"], signed=False),
            ]
        )
    headers = ["銘柄", "戦略 利益率", "ガチホ 利益率", "戦略 最大DD", "ガチホ 最大DD", "戦略 シャープ", "ガチホ シャープ", "売買回数", "勝率"]
    return markdown_table(headers, rows)
