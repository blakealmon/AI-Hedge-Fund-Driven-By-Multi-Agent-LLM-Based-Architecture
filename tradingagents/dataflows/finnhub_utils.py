import json
import os
import re


def get_data_in_range(ticker, start_date, end_date, data_type, data_dir, period=None):
    """
    Retrieve a Finnhub data file whose filename's second date matches end_date.
    Filenames look like:
      {TICKER}_{someStartDate}_{end_date}.json
      {TICKER}_{someStartDate}_{end_date}_{period}.json   (when period is annual|quarterly)
    We first try the exact start_date provided; if not found, fall back to any file
    with matching end_date (preferring the one with the latest start date).
    """
    base_dir = os.path.join(data_dir, "finnhub_data", data_type)
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Data directory not found: {base_dir}")

    if period:
        exact_filename = f"{ticker}_{start_date}_{end_date}_{period}.json"
        pattern = rf"^{re.escape(ticker)}_(\d{{4}}-\d{{2}}-\d{{2}})_{re.escape(end_date)}_{re.escape(period)}\.json$"
    else:
        exact_filename = f"{ticker}_{start_date}_{end_date}.json"
        pattern = rf"^{re.escape(ticker)}_(\d{{4}}-\d{{2}}-\d{{2}})_{re.escape(end_date)}\.json$"

    exact_path = os.path.join(base_dir, exact_filename)
    if os.path.isfile(exact_path):
        with open(exact_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    # Fallback: scan for any file whose second date == end_date
    candidates = []
    for fname in os.listdir(base_dir):
        m = re.match(pattern, fname)
        if m:
            start_part = m.group(1)
            candidates.append((start_part, fname))

    if not candidates:
        # Nothing found
        return {}

    # Prefer the candidate whose start date matches requested start_date
    for s, f in candidates:
        if s == start_date:
            with open(os.path.join(base_dir, f), "r", encoding="utf-8") as fh:
                print(fh)
                return json.load(fh)

    # Otherwise pick the one with the latest start date (max)
    candidates.sort(key=lambda x: x[0])  # date strings sort lexicographically (YYYY-MM-DD)
    chosen = candidates[-1][1]
    with open(os.path.join(base_dir, chosen), "r", encoding="utf-8") as fh:
        return json.load(fh)
