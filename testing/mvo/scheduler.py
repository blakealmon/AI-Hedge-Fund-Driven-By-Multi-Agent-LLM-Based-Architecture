import datetime as dt
from typing import List


def biweekly_rebalance_days(
    trading_dates: List[str], start_date: str
) -> List[str]:

    fmt = "%Y-%m-%d"
    start = dt.datetime.strptime(start_date, fmt).date()
    selected: List[str] = []
    last_reb: dt.date = None
    for d in trading_dates:
        current = dt.datetime.strptime(d, fmt).date()
        if current < start:
            continue
        if last_reb is None or (current - last_reb).days >= 14:
            selected.append(d)
            last_reb = current
    return selected


