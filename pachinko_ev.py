#!/usr/bin/env python3
"""パチンコ 台単体の期待値計算（ボーダー理論・マルチレート対応）

モデル:
  P  = 通常時の初当たり確率の分母（例: 319.7）
  E  = 初当たり1回あたりの平均獲得出玉（電サポ中の消費を差し引いた純増, 玉）
  R  = 千円あたりの通常回転数
  L  = 千円あたりの貸玉数（1パチ=1000玉, 4パチ=250玉）
  x  = 換金率（円/玉）
  k  = 持ち玉比率（0〜1）

  1回転あたりの払出期待値(円) = E / P * x
  1回転あたりのコスト(円)      = (1-k) * 1000/R + k * (L/R) * x
  ボーダー R* = ((1-k)*1000 + k*L*x) * P / (E * x)
"""
import argparse

RATES = {
    "1": {"name": "1パチ", "lend": 1000, "default_x": 0.8},
    "4": {"name": "4パチ", "lend": 250, "default_x": 4.0},
}
RATIOS = [("現金100%", 0.0), ("持ち玉50%", 0.5), ("持ち玉100%", 1.0)]
PAYOUT_ADJ = [-0.10, -0.05, 0.0, 0.05, 0.10]


def border(P, E, L, x, k):
    return ((1 - k) * 1000 + k * L * x) * P / (E * x)


def ev_per_spin(P, E, L, x, k, R):
    return E / P * x - ((1 - k) * 1000 / R + k * (L / R) * x)


def exchange_label(rate, x):
    base = 1000 / RATES[rate]["lend"]
    if abs(x - base) < 1e-9:
        return "等価交換"
    return f"{x:g}円交換（{1000 / x:.1f}玉=1,000円）"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rate", choices=["1", "4"], default="1", help="レート（既定: 1パチ）")
    ap.add_argument("--x", type=float, help="換金率 円/玉（既定: 1パチ0.8 / 4パチ4.0）")
    ap.add_argument("--prob", type=float, required=True, help="初当たり確率の分母")
    ap.add_argument("--payout", type=float, required=True, help="初当たり1回あたりの平均純増出玉")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--rpk", type=float, help="千円あたりの回転数")
    g.add_argument("--spins", type=float, help="実践の通常回転数（--invest と併用）")
    ap.add_argument("--invest", type=float, help="実践の投資額（円）")
    ap.add_argument("--sph", type=float, default=180, help="1時間あたり通常回転数（既定180）")
    ap.add_argument("--hours", type=float, default=10, help="1日の稼働時間（既定10）")
    a = ap.parse_args()

    cfg = RATES[a.rate]
    L = cfg["lend"]
    x = a.x if a.x is not None else cfg["default_x"]
    if a.rpk is not None:
        R = a.rpk
    else:
        if not a.invest:
            ap.error("--spins には --invest が必要です")
        R = a.spins / (a.invest / 1000)
    P, E = a.prob, a.payout

    print(f"適用レート: {cfg['name']}・{exchange_label(a.rate, x)}  / 現在の回転率: {R:.2f}回/千円\n")
    print("| 持ち玉比率 | ボーダー | 差 | 1回転EV | 期待時給 | 1日期待収支 |")
    print("|---|---|---|---|---|---|")
    for label, k in RATIOS:
        b = border(P, E, L, x, k)
        ev = ev_per_spin(P, E, L, x, k, R)
        print(f"| {label} | {b:.2f} | {R - b:+.2f} | {ev:+.2f}円 | {ev * a.sph:+,.0f}円 | {ev * a.sph * a.hours:+,.0f}円 |")

    print("\n出玉増減の影響（補正後ボーダー）")
    print("| 出玉補正 | 平均出玉 | " + " | ".join(l for l, _ in RATIOS) + " |")
    print("|---|---|" + "---|" * len(RATIOS))
    for adj in PAYOUT_ADJ:
        e2 = E * (1 + adj)
        cells = " | ".join(f"{border(P, e2, L, x, k):.2f}" for _, k in RATIOS)
        print(f"| {adj:+.0%} | {e2:,.0f}玉 | {cells} |")


if __name__ == "__main__":
    main()
