import re
import datetime as dt
from typing import Dict, List, Tuple


def read_prices_csv(csv_path: str) -> Tuple[List[str], Dict[str, Dict[str, float]]]:

    dates: List[str] = []
    date_to_prices: Dict[str, Dict[str, float]] = {}

    with open(csv_path, "r") as f:
        lines = [ln.rstrip("\n") for ln in f]

    # Build header across wrapped lines until first date line
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}")
    header_parts: List[str] = []
    i = 0
    while i < len(lines) and not date_re.match(lines[i]):
        part = lines[i].strip()
        if part:
            header_parts.append(part)
        i += 1
    header_line = "".join(header_parts)
    header_cols = [c.strip() for c in header_line.split(",") if c.strip()]
    if len(header_cols) == 0 or header_cols[0].lower() != "date":
        raise ValueError("CSV header must start with Date")
    tickers = header_cols[1:]

    # Now iterate blocks: each data row may be wrapped over multiple lines until next date line or EOF
    while i < len(lines):
        # line starting a new row
        if not date_re.match(lines[i]):
            i += 1
            continue
        block = [lines[i].strip()]
        i += 1
        while i < len(lines) and not date_re.match(lines[i]):
            if lines[i].strip():
                block.append(lines[i].strip())
            i += 1
        row_joined = "".join(block)
        cols = [c.strip() for c in row_joined.split(",")]
        if len(cols) < 2:
            continue
        date_str = cols[0]
        prices: Dict[str, float] = {}
        for idx, ticker in enumerate(tickers, start=1):
            if idx >= len(cols):
                break
            cell = cols[idx]
            if cell == "":
                continue
            try:
                prices[ticker] = float(cell)
            except ValueError:
                continue
        dates.append(date_str)
        date_to_prices[date_str] = prices

    return dates, date_to_prices


def previous_trading_day(dates: List[str], date_str: str) -> str:

    if date_str in dates:
        idx = dates.index(date_str)
    else:
        # insert position
        idx = 0
        for i, d in enumerate(dates):
            if d > date_str:
                idx = i
                break
        else:
            idx = len(dates)
    if idx == 0:
        raise ValueError("No previous trading day available")
    return dates[idx - 1]


def parse_date(date_str: str) -> dt.date:
    return dt.datetime.strptime(date_str, "%Y-%m-%d").date()


