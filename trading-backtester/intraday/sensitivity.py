"""How does net performance decay as costs rise? The HFT lesson in one chart."""

import pandas as pd


def cost_sensitivity(df, positions_fn, backtest_fn,
                     entry_bps=10, cost_range=None):
    """
    Sweep cost-per-side (in bps) and return a DataFrame of net results.
    positions_fn(df, entry_bps) -> position series
    backtest_fn(df, pos, cost)  -> net returns series
    """
    if cost_range is None:
        cost_range = [0, 1, 2, 5, 10]   # bps per side

    pos = positions_fn(df, entry_bps=entry_bps)
    n_entries = int((pos.diff() == 1).sum())

    rows = []
    for bps in cost_range:
        net = backtest_fn(df, pos, cost_per_side=bps / 10000)
        total = (1 + net).prod() - 1
        rows.append({"cost_bps_per_side": bps,
                     "round_trip_bps": 2 * bps,
                     "net_return_pct": round(total * 100, 3),
                     "entries": n_entries})
    return pd.DataFrame(rows)
