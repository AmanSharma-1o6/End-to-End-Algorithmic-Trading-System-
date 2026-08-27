"""Append-only CSV audit trail for the live trader."""

import os
from datetime import datetime
import pandas as pd

LOG_FILE = os.path.join("intraday", "live_trades.csv")

COLUMNS = ["timestamp", "action", "price", "vwap", "dev_bps",
           "position", "equity", "mode"]


def log_trade(action, price, vwap, dev_bps, position, equity=None, mode="PAPER"):
    """Append one row. action: HOLD / BUY / SELL / ERROR / MARKET_CLOSED."""
    row = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "price": round(float(price), 2) if price is not None else None,
        "vwap": round(float(vwap), 2) if vwap is not None else None,
        "dev_bps": round(float(dev_bps), 2) if dev_bps is not None else None,
        "position": position,
        "equity": equity,
        "mode": mode,
    }])

    write_header = not os.path.exists(LOG_FILE)
    row.to_csv(LOG_FILE, mode="a", header=write_header, index=False)


def read_log():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=COLUMNS)
