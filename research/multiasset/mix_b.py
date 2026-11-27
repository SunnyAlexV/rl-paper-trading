"""Backtest of mix B (SPEC_B.md) with the menu simulator. Run from the history working copy."""
import sys; sys.path.insert(0, ".")
exec(open("research/multiasset/menu.py").read().split("grid = [")[0])
rows = []
for name, w in {"mix B: E40 / G20 / US10 / C30": (.4, .2, .1, .3), "mix A: E40 / US10 / C50": (.4, 0, .1, .5),
                "equity sleeve alone": (1, 0, 0, 0)}.items():
    nav = mix(w)
    rows.append(dict(book=name, **{f"full_{k}": v for k, v in stats(nav, "2012-07-02", None).items()},
                     **{f"2020_26_{k}": v for k, v in stats(nav, "2020-01-01", None).items()},
                     years={str(k.year): round(float(v) * 100, 1) for k, v in nav.resample("YE").last().pct_change().dropna().items()}))
    print(rows[-1])
pd.DataFrame(rows).to_csv("research/multiasset/mix_b.csv", index=False)
