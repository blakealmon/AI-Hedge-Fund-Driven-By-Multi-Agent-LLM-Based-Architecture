from typing import Annotated, Dict
from .reddit_utils import fetch_top_from_category, get_top_reddit_posts_for_ticker
from .yfin_utils import *
from .stockstats_utils import *
from .googlenews_utils import *
from .finnhub_utils import get_data_in_range
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import os
import pandas as pd
from tqdm import tqdm
import yfinance as yf
import requests
from openai import OpenAI
from .config import get_config, set_config, DATA_DIR

def _normalize_ticker_base(ticker: str) -> str:
    """Normalize basic ticker format for cross-provider use.

    - Uppercase
    - Strip leading '$'
    - Trim whitespace
    """
    return str(ticker).strip().upper().lstrip("$")

def get_price_from_csv(
    ticker: str,
    date: str,
) -> float:
    """
    Retrieve the closing price for a given ticker on a given date from local CSV data.
    Args:
        ticker (str): Ticker symbol of the company, e.g. AAPL
        date (str): Date in yyyy-mm-dd format
    Returns:
        float: Closing price for ticker on the given date
    Raises:
        Exception: If price or file not found
    """

    # Path to price data CSV
    price_path = os.path.join(
        os.path.dirname(__file__),
        "../../data/market_data/price_data",
        f"{ticker.upper()}-YFin-data-2015-01-01-2025-07-27.csv",
    )
    if not os.path.exists(price_path):
        # Auto-fetch and cache a baseline file
        start_dt = "2015-01-01"
        end_dt = "2025-07-27"
        hist = yf.Ticker(ticker.upper()).history(start=start_dt, end=end_dt)
        if hist.empty:
            raise Exception(f"Unable to fetch price data for {ticker}")
        hist = hist.reset_index()
        os.makedirs(os.path.dirname(price_path), exist_ok=True)
        hist.to_csv(price_path, index=False)

    df = pd.read_csv(price_path)
    # Normalize date format
    date_str = date.strip()
    # Find row with matching date (ignore time part)
    if "Date" not in df.columns:
        raise Exception(f"Invalid price file (no Date column): {price_path}")
    # Ensure Date as string YYYY-MM-DD
    if not pd.api.types.is_string_dtype(df["Date"]):
        try:
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        except Exception:
            df["Date"] = df["Date"].astype(str).str[:10]
    row = df[df["Date"].str.startswith(date_str)]
    if row.empty:
        # Fetch a small window around the missing date and merge
        try:
            target_dt = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            raise Exception(f"Invalid date format: {date}")
        start = (target_dt - relativedelta(days=45)).strftime("%Y-%m-%d")
        end = (target_dt + relativedelta(days=2)).strftime("%Y-%m-%d")
        fetched = yf.Ticker(ticker.upper()).history(start=start, end=end)
        if not fetched.empty:
            fetched = fetched.reset_index()
            # Normalize fetched Date
            if "Date" in fetched.columns:
                fetched["Date"] = pd.to_datetime(fetched["Date"]).dt.strftime("%Y-%m-%d")
            else:
                # some yfinance versions use index
                fetched.rename(columns={"index": "Date"}, inplace=True)
                fetched["Date"] = pd.to_datetime(fetched["Date"]).dt.strftime("%Y-%m-%d")
            # Merge and de-duplicate by Date
            merged = pd.concat([df, fetched], ignore_index=True)
            merged = merged.drop_duplicates(subset=["Date"]).sort_values("Date")
            merged.to_csv(price_path, index=False)
            df = merged
            row = df[df["Date"].str.startswith(date_str)]
        if row.empty:
            raise Exception(f"No price found for {ticker} on {date}")
    price = float(row.iloc[0]["Close"])
    return price


def get_polygon_close_price(ticker: str, date: str) -> float:
    """
    Fetch the official close from Polygon for a given ticker/date.
    Uses env POLYGON_API_KEY if set; otherwise falls back to provided key.
    """
    key = os.getenv("POLYGON_API_KEY") or "TY7U3esnUP3PvWVVLLKsH_SrlnNFGSnp"
    # Polygon uses dot notation for share classes (e.g., BRK.B)
    poly_ticker = _normalize_ticker_base(ticker).replace("-", ".")
    url = f"https://api.polygon.io/v1/open-close/{poly_ticker}/{date}?adjusted=true&apiKey={key}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        close_px = data.get("close")
        if close_px is None:
            raise Exception("no close in polygon response")
        return float(close_px)
    except Exception as e:
        raise Exception(f"Polygon price fetch failed for {ticker} on {date}: {e}")


def _testing_prices_path() -> Path:
    return (Path.cwd() / "testing" / "stock_prices.csv").resolve()


def get_close_from_testing_csv(ticker: str, date: str) -> float:
    """
    Preferential price resolver that reads testing/stock_prices.csv.

    Supports two formats:
    - Long format: columns include [date, ticker, close] (case-insensitive, underscores/spaces allowed)
    - Wide format: columns include [date, <TICKER>, ...] with each ticker as a column of closes
    """
    csv_path = _testing_prices_path()
    if not csv_path.exists():
        raise FileNotFoundError(str(csv_path))

    df_raw = pd.read_csv(csv_path, low_memory=False)
    # Normalize columns: lower-case, strip, replace spaces with underscores
    norm_cols = {c: str(c).strip().lower().replace(" ", "_") for c in df_raw.columns}
    df = df_raw.rename(columns=norm_cols)

    # Ensure a date-like column exists
    date_col = None
    for cand in ("date", "day", "dt"):  # permissive
        if cand in df.columns:
            date_col = cand
            break
    if date_col is None:
        # try index-based date if provided without header
        if 0 in df.columns:
            date_col = 0  # type: ignore
        else:
            raise ValueError("testing/stock_prices.csv: missing date column")

    # Long format path
    has_ticker = any(c in df.columns for c in ("ticker", "symbol"))
    has_close = any(c in df.columns for c in ("close", "adj_close", "adj_close_", "adjclose"))
    ticker_u = _normalize_ticker_base(ticker)
    date_str = str(date).strip()[:10]

    if has_ticker and has_close:
        tcol = "ticker" if "ticker" in df.columns else "symbol"
        ccol = "close" if "close" in df.columns else ("adj_close" if "adj_close" in df.columns else ("adjclose" if "adjclose" in df.columns else "close"))
        # Normalize values for matching
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
        df[tcol] = df[tcol].astype(str).str.upper().str.strip()
        row = df[(df[tcol] == ticker_u) & (df[date_col] == date_str)]
        if row.empty:
            raise Exception(f"No CSV price for {ticker_u} on {date_str}")
        val = row.iloc[0][ccol]
        if pd.isna(val):
            raise Exception(f"NaN CSV price for {ticker_u} on {date_str}")
        return float(val)

    # Wide format path: one column per ticker
    # Try exact match, then case-insensitive match, then variants replacing dots/hyphens/underscores
    col_candidates = [
        ticker_u,
        ticker_u.replace(".", "_"),
        ticker_u.replace("_", "."),
        ticker_u.replace("-", "_"),
        ticker_u.replace("-", "."),
        ticker_u.replace(".", "-"),
    ]
    # Build mapping from normalized to original column names for case-insensitive access
    lower_to_orig = {str(c).strip().lower(): c for c in df_raw.columns}
    for cand in list(col_candidates):
        lower_key = cand.lower()
        if lower_key in lower_to_orig:
            col_candidates.append(lower_to_orig[lower_key])
    # Ensure date column is normalized to string
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce").dt.strftime("%Y-%m-%d")
    # Find a usable ticker column
    ticker_col = None
    for c in col_candidates:
        if c in df.columns:
            ticker_col = c
            break
    if ticker_col is None:
        # Try original headers exact
        for c in df_raw.columns:
            if str(c).strip().upper() == ticker_u:
                ticker_col = c
                break
    if ticker_col is None:
        raise Exception(f"Ticker column {ticker_u} not found in testing CSV")

    row = df[df[date_col] == date_str]
    if row.empty:
        raise Exception(f"No CSV price for {ticker_u} on {date_str}")
    val = row.iloc[0][ticker_col]
    if pd.isna(val):
        raise Exception(f"NaN CSV price for {ticker_u} on {date_str}")
    return float(val)


def get_close_price(ticker: str, date: str) -> float:
    """
    Unified close-price resolver with preference: testing CSV -> Polygon -> local CSV -> yfinance.
    """
    base = _normalize_ticker_base(ticker)
    # 1) testing/stock_prices.csv (user-provided authoritative data)
    csv_try_order = [base, base.replace(".", "-"), base.replace("-", "."), base.replace(".", "_")]
    for sym in csv_try_order:
        try:
            return get_close_from_testing_csv(sym, date)
        except Exception:
            pass
    # 2) Polygon official close (prefers dot notation)
    polygon_try_order = [base.replace("-", "."), base]
    for sym in polygon_try_order:
        try:
            return get_polygon_close_price(sym, date)
        except Exception:
            pass
    # 3) Local per-ticker YFin CSV cache (Yahoo prefers hyphen)
    csv_cache_try = [base.replace(".", "-"), base]
    for sym in csv_cache_try:
        try:
            return get_price_from_csv(sym, date)
        except Exception:
            pass
    # 4) yfinance fallback (best-effort, use hyphen form)
    try:
        start = datetime.strptime(date, "%Y-%m-%d")
        end = start + relativedelta(days=1)
        yf_sym = base.replace(".", "-")
        hist = yf.Ticker(yf_sym).history(start=start, end=end)
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        pass
    raise Exception(f"No price found for {ticker} on {date}")

def get_finnhub_news(
    ticker: Annotated[
        str,
        "Search query of a company's, e.g. 'AAPL, TSM, etc.",
    ],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"] = 7,
):
    """
    Retrieve news about a company within a time frame

    Args
        ticker (str): ticker for the company you are interested in
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns
        str: dataframe containing the news of the company in the time frame

    """

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    result = get_data_in_range(ticker, before, curr_date, "news_data", DATA_DIR)

    if len(result) == 0:
        # Fallbacks when finnhub data missing: Google News then OpenAI web search
        try:
            alt = get_google_news(ticker, curr_date, look_back_days)
            if alt:
                return alt
        except Exception:
            pass
        try:
            return get_stock_news_openai(ticker, curr_date)
        except Exception:
            return ""

    combined_result = ""
    seen_dicts = []

    config = get_config()
    if config["abmrOffline"]:
        for entry in result:
            if entry not in seen_dicts:
                headline = entry.get('headline', '')
                date = entry.get('date', '')
                summary = entry.get('summary', '')
                combined_result += f"### {headline} ({date}):\n{summary}\n\n"
                seen_dicts.append(entry)
        return f"## {ticker} News, from {before} to {curr_date}:\n" + str(combined_result)

    for day, data in result.items():
        if len(data) == 0:
            continue
        for entry in data:
            if entry not in seen_dicts:
                current_news = (
                    "### " + entry["headline"] + f" ({day})" + "\n" + entry["summary"]
                )
                combined_result += current_news + "\n\n"
                seen_dicts.append(entry)

    return f"## {ticker} News, from {before} to {curr_date}:\n" + str(combined_result)


def get_finnhub_company_insider_sentiment(
    ticker: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[
        str,
        "current date of you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "number of days to look back"] = 7,
):
    """
    Retrieve insider sentiment about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading on, yyyy-mm-dd
    Returns:
        str: a report of the sentiment in the past 15 days starting at curr_date
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_senti", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""
    seen_dicts = []
    config = get_config()
    if config["abmrOffline"]:
        print(data)
        for entry in data["data"]:
            if entry not in seen_dicts:
                result_str += f"### {entry['year']}-{entry['month']}:\nChange: {entry['change']}\nMonthly Share Purchase Ratio: {entry['mspr']}\n\n"
                seen_dicts.append(entry)
        return (
            f"## {ticker} Insider Sentiment Data for {before} to {curr_date}:\n"
            + result_str
            + "The change field refers to the net buying/selling from all insiders' transactions. The mspr field refers to monthly share purchase ratio."
        )
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### {entry['year']}-{entry['month']}:\nChange: {entry['change']}\nMonthly Share Purchase Ratio: {entry['mspr']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} Insider Sentiment Data for {before} to {curr_date}:\n"
        + result_str
        + "The change field refers to the net buying/selling from all insiders' transactions. The mspr field refers to monthly share purchase ratio."
    )


def get_finnhub_company_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[
        str,
        "current date you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    Retrieve insider transcaction information about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading at, yyyy-mm-dd
    Returns:
        str: a report of the company's insider transaction/trading informtaion in the past 15 days
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_trans", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""

    seen_dicts = []

    config = get_config()

    if config["abmrOffline"]:
        if len(data["data"]) == 0:
            return "No insider transactions within the past 7 days."
        for entry in data["data"]:
            if entry not in seen_dicts:
                result_str += f"### Filing Date: {entry['filingDate']}, {entry['name']}:\nChange:{entry['change']}\nShares: {entry['share']}\nTransaction Price: {entry['transactionPrice']}\nTransaction Code: {entry['transactionCode']}\n\n"
                seen_dicts.append(entry)
        return (
            f"## {ticker} insider transactions from {before} to {curr_date}:\n"
            + result_str
            + "The change field reflects the variation in share count—here a negative number indicates a reduction in holdings—while share specifies the total number of shares involved. The transactionPrice denotes the per-share price at which the trade was executed, and transactionDate marks when the transaction occurred. The name field identifies the insider making the trade, and transactionCode (e.g., S for sale) clarifies the nature of the transaction. FilingDate records when the transaction was officially reported, and the unique id links to the specific SEC filing, as indicated by the source. Additionally, the symbol ties the transaction to a particular company, isDerivative flags whether the trade involves derivative securities, and currency notes the currency context of the transaction."
        )

    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### Filing Date: {entry['filingDate']}, {entry['name']}:\nChange:{entry['change']}\nShares: {entry['share']}\nTransaction Price: {entry['transactionPrice']}\nTransaction Code: {entry['transactionCode']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} insider transactions from {before} to {curr_date}:\n"
        + result_str
        + "The change field reflects the variation in share count—here a negative number indicates a reduction in holdings—while share specifies the total number of shares involved. The transactionPrice denotes the per-share price at which the trade was executed, and transactionDate marks when the transaction occurred. The name field identifies the insider making the trade, and transactionCode (e.g., S for sale) clarifies the nature of the transaction. FilingDate records when the transaction was officially reported, and the unique id links to the specific SEC filing, as indicated by the source. Additionally, the symbol ties the transaction to a particular company, isDerivative flags whether the trade involves derivative securities, and currency notes the currency context of the transaction."
    )

def _previous_calendar_quarter_end(curr_date_dt: pd.Timestamp) -> pd.Timestamp:
    """
    Get the most recent completed calendar quarter end strictly before curr_date_dt
    (e.g. if curr_date is 2025-05-15 -> 2025-03-31; if 2025-03-31 -> 2024-12-31).
    """
    year = curr_date_dt.year
    # Define the calendar quarter ends for the current year
    q_ends = [
        pd.Timestamp(year=year, month=3, day=31, tz='UTC'),
        pd.Timestamp(year=year, month=6, day=30, tz='UTC'),
        pd.Timestamp(year=year, month=9, day=30, tz='UTC'),
        pd.Timestamp(year=year, month=12, day=31, tz='UTC'),
    ]
    # Find the last quarter end strictly before curr_date_dt
    prev = None
    for qe in q_ends:
        if qe < curr_date_dt:
            prev = qe
        else:
            break
    if prev is not None:
        return prev
    # If none in this year, return last year's Dec 31
    return pd.Timestamp(year=year - 1, month=12, day=31, tz='UTC')


def _last_fiscal_year_end(curr_date_dt: pd.Timestamp) -> pd.Timestamp:
    """
    Assume fiscal year ends on Dec 31 (no custom fiscal calendars provided).
    Return the most recent Dec 31 strictly before curr_date_dt
    (if curr_date is 2025-01-10 -> 2024-12-31; if 2024-12-31 -> 2023-12-31).
    """
    candidate = pd.Timestamp(year=curr_date_dt.year, month=12, day=31, tz='UTC')
    if curr_date_dt <= candidate:
        # Not yet passed Dec 31 of this year (or exactly on it),
        # so take last year's Dec 31
        return pd.Timestamp(year=curr_date_dt.year - 1, month=12, day=31, tz='UTC')
    return candidate


def get_simfin_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency of the company's financial history: annual / quarterly"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    Retrieve a balance sheet snapshot using ONLY the JSON file for the most recent finished quarter
    (no full directory scans / no loading of all files).

    JSON file naming assumptions (located in DATA_DIR/simfin_data):
      Quarterly files follow one of these patterns (we try both, in this order):
        1. Fiscal-shift style (example provided): {TICKER}_BS_{FISCALYEAR}_Q{FQ}.json
           Mapping from calendar quarter end (QE) month to (FISCALYEAR, FQ):
             Dec (12) -> (year+1, Q1)
             Mar (3)  -> (year,   Q2)
             Jun (6)  -> (year,   Q3)
             Sep (9)  -> (year,   Q4)
        2. Pure calendar style: {TICKER}_BS_{YEAR}_Q{CQ}.json
             Mar (3)->Q1, Jun (6)->Q2, Sep (9)->Q3, Dec (12)->Q4

    Annual (freq starts with 'annual'):
      - Determine last fiscal year end (Dec 31 strictly before curr_date).
      - Use that Dec quarter's file (same quarter-resolution JSON) rather than a separate FY file.
      - Prefer a Q4 (calendar style) or mapped Q1 (fiscal-shift style) corresponding to Dec 31.

    We DO NOT iterate all files. We compute candidate filenames for the target period and attempt them.
    If the target period file is missing / not yet published (Publish Date > curr_date) / Report Date >= curr_date,
    we step back one quarter at a time (up to max_lookback_quarters) repeating the filename inference.

    Returns formatted string or "" if none found.
    """
    base_dir = os.path.join(DATA_DIR, "simfin_data")
    if not os.path.isdir(base_dir):
        print(f"SimFin JSON directory not found: {base_dir}")
        return ""

    curr_dt = pd.to_datetime(curr_date, utc=True).normalize()
    ticker_u = ticker.upper()

    def quarter_filename_candidates(q_end: pd.Timestamp):
        """
        Produce ordered filename candidates (fiscal-shift first, then calendar).
        """
        month = q_end.month
        year = q_end.year

        # Calendar mapping
        cal_q_map = {3: 1, 6: 2, 9: 3, 12: 4}
        cal_q = cal_q_map[month]
        cal_year = year

        # Fiscal-shift mapping (based on example: Q1 FY2019 has Report Date 2018-12-31)
        if month == 12:
            fiscal_year = year + 1
            fiscal_q = 1
        elif month == 3:
            fiscal_year = year
            fiscal_q = 2
        elif month == 6:
            fiscal_year = year
            fiscal_q = 3
        elif month == 9:
            fiscal_year = year
            fiscal_q = 4
        else:
            raise ValueError("Invalid quarter end month")

        fiscal_style = f"{ticker_u}_BS_{fiscal_year}_Q{fiscal_q}.json"
        calendar_style = f"{ticker_u}_BS_{cal_year}_Q{cal_q}.json"

        # Avoid duplicate if they coincidentally match
        if fiscal_style == calendar_style:
            return [fiscal_style]
        return [fiscal_style, calendar_style]

    def load_record_from_file(fname: str):
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                return data[0]  # assume single record per file (as per example)
        except Exception as e:
            print(f"Error reading {path}: {e}")
        return None

    # Determine target quarter end(s)
    if freq.lower().startswith("quarter"):
        target_q_end = _previous_calendar_quarter_end(curr_dt)
    else:  # annual -> use last fiscal year end (Dec 31) and treat that quarter as annual snapshot
        target_q_end = _last_fiscal_year_end(curr_dt)

    max_lookback_quarters = 8  # safety cap
    attempts = 0
    chosen_record = None
    chosen_report_date = None

    q_end = target_q_end
    while attempts < max_lookback_quarters and chosen_record is None:
        for fname in quarter_filename_candidates(q_end):
            rec = load_record_from_file(fname)
            if rec is None:
                continue

            # Parse dates
            try:
                rep_dt = pd.to_datetime(rec.get("Report Date"), utc=True).normalize()
                pub_dt = pd.to_datetime(rec.get("Publish Date"), utc=True).normalize()
            except Exception:
                continue

            # Must represent a finished & published period
            if pd.isna(rep_dt) or pd.isna(pub_dt):
                continue
            if rep_dt >= curr_dt or pub_dt > curr_dt:
                # Not yet finished / published relative to trading date
                continue

            # For annual freq, ensure this is the intended fiscal-year snapshot:
            if freq.lower().startswith("annual"):
                # Prefer FY/Q4 markers if present; if not, still accept (fallback).
                fiscal_period = str(rec.get("Fiscal Period", "")).upper()
                if fiscal_period in ("FY", "Q4") or attempts > 0:
                    chosen_record = rec
                    chosen_report_date = rep_dt
                    break
            else:
                # Quarterly path
                chosen_record = rec
                chosen_report_date = rep_dt
                break

        if chosen_record is None:
            # Step back one quarter: subtract 1 day from current quarter end and recompute
            prev_ref = q_end - pd.Timedelta(days=1)
            q_end = _previous_calendar_quarter_end(prev_ref)
            attempts += 1

    if chosen_record is None:
        print("No suitable balance sheet found within lookback limit.")
        return ""

    # Format output (keep prior style)
    publish_date_str = str(chosen_record.get("Publish Date"))[:10]
    report_date_str = str(chosen_record.get("Report Date"))[:10]

    # Build a pandas Series for pretty printing but exclude helper keys if any
    series = pd.Series({k: v for k, v in chosen_record.items() if not k.startswith("_")})

    return (
        f"## {freq} balance sheet for {ticker} (Report Date {report_date_str}, "
        f"Publish Date {publish_date_str}):\n"
        + series.to_string()
        + "\n\nThis snapshot reflects the latest fully completed fiscal period available before the trading date."
    )

def get_simfin_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    Retrieve a cash flow statement snapshot using ONLY the JSON file for the most recent finished quarter
    (no directory-wide loading).

    JSON file naming assumptions (DATA_DIR/simfin_data):
      Primary patterns attempted (in order) for a quarter ending (QE):
        1. Fiscal-shift style: {TICKER}_CF_{FISCALYEAR}_Q{FQ}.json
           Mapping from calendar quarter end month -> (FiscalYear, FiscalQuarter):
             Dec -> (year+1, Q1)
             Mar -> (year,   Q2)
             Jun -> (year,   Q3)
             Sep -> (year,   Q4)
        2. Pure calendar style: {TICKER}_CF_{YEAR}_Q{CQ}.json
             Mar->Q1, Jun->Q2, Sep->Q3, Dec->Q4

    Annual (freq starts with 'annual'):
      - Determine last fiscal year end (Dec 31 strictly before curr_date).
      - Use that quarter's JSON (no separate FY file).
      - Prefer a record whose Fiscal Period is FY or Q4; otherwise fallback.

    If target file not available or not yet published (Publish Date > curr_date) or Report Date >= curr_date,
    step back one quarter (up to max_lookback_quarters).

    Returns formatted string or "" if none found.
    """
    base_dir = os.path.join(DATA_DIR, "simfin_data")
    if not os.path.isdir(base_dir):
        print(f"SimFin JSON directory not found: {base_dir}")
        return ""

    curr_dt = pd.to_datetime(curr_date, utc=True).normalize()
    ticker_u = ticker.upper()

    def quarter_filename_candidates(q_end: pd.Timestamp):
        month = q_end.month
        year = q_end.year
        cal_q_map = {3: 1, 6: 2, 9: 3, 12: 4}
        cal_q = cal_q_map[month]
        cal_year = year
        # Fiscal-shift mapping
        if month == 12:
            fiscal_year = year + 1
            fiscal_q = 1
        elif month == 3:
            fiscal_year = year
            fiscal_q = 2
        elif month == 6:
            fiscal_year = year
            fiscal_q = 3
        elif month == 9:
            fiscal_year = year
            fiscal_q = 4
        else:
            raise ValueError("Invalid quarter end month")
        fiscal_style = f"{ticker_u}_CF_{fiscal_year}_Q{fiscal_q}.json"
        calendar_style = f"{ticker_u}_CF_{cal_year}_Q{cal_q}.json"
        return [fiscal_style] if fiscal_style == calendar_style else [fiscal_style, calendar_style]

    def load_record_from_file(fname: str):
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                return data[0]
        except Exception as e:
            print(f"Error reading {path}: {e}")
        return None

    # Determine initial target quarter end
    if freq.lower().startswith("quarter"):
        target_q_end = _previous_calendar_quarter_end(curr_dt)
    else:
        target_q_end = _last_fiscal_year_end(curr_dt)

    max_lookback_quarters = 8
    attempts = 0
    chosen_record = None

    q_end = target_q_end
    while attempts < max_lookback_quarters and chosen_record is None:
        for fname in quarter_filename_candidates(q_end):
            rec = load_record_from_file(fname)
            if rec is None:
                continue
            try:
                rep_dt = pd.to_datetime(rec.get("Report Date"), utc=True).normalize()
                pub_dt = pd.to_datetime(rec.get("Publish Date"), utc=True).normalize()
            except Exception:
                continue
            if pd.isna(rep_dt) or pd.isna(pub_dt):
                continue
            if rep_dt >= curr_dt or pub_dt > curr_dt:
                continue
            if freq.lower().startswith("annual"):
                fiscal_period = str(rec.get("Fiscal Period", "")).upper()
                if fiscal_period in ("FY", "Q4") or attempts > 0:
                    chosen_record = rec
                    break
            else:
                chosen_record = rec
                break
        if chosen_record is None:
            prev_ref = q_end - pd.Timedelta(days=1)
            q_end = _previous_calendar_quarter_end(prev_ref)
            attempts += 1

    if chosen_record is None:
        print("No suitable cash flow statement found within lookback limit.")
        return ""

    publish_date_str = str(chosen_record.get("Publish Date"))[:10]
    report_date_str = str(chosen_record.get("Report Date"))[:10]
    series = pd.Series({k: v for k, v in chosen_record.items() if not k.startswith("_")})

    return (
        f"## {freq} cash flow statement for {ticker} (Report Date {report_date_str}, "
        f"Publish Date {publish_date_str}):\n"
        + series.to_string()
        + "\n\nThis includes operating, investing, and financing cash flows for the latest fully completed period before the trading date."
    )

def get_simfin_income_statements(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    """
    Retrieve an income statement snapshot using ONLY the JSON file for the most recent finished quarter
    (no directory-wide scans).

    JSON file naming assumptions (located in DATA_DIR/simfin_data):
      Quarterly files (we try both naming styles, in order):
        1. Fiscal-shift style: {TICKER}_IS_{FISCALYEAR}_Q{FQ}.json
           Mapping calendar quarter end month -> (FiscalYear, FiscalQuarter):
             Dec -> (year+1, Q1)
             Mar -> (year,   Q2)
             Jun -> (year,   Q3)
             Sep -> (year,   Q4)
        2. Pure calendar style: {TICKER}_IS_{YEAR}_Q{CQ}.json
             Mar->Q1, Jun->Q2, Sep->Q3, Dec->Q4

    Annual (freq starts with 'annual'):
      - Determine last fiscal year end (Dec 31 strictly before curr_date).
      - Use that quarter's JSON (no separate FY file).
      - Prefer a record with Fiscal Period FY or Q4; otherwise step back further.

    If the target period file is missing / not yet published (Publish Date > curr_date) /
    Report Date >= curr_date, step back one quarter (up to max_lookback_quarters).

    Returns formatted string or "" if none found.
    """
    base_dir = os.path.join(DATA_DIR, "simfin_data")
    if not os.path.isdir(base_dir):
        print(f"SimFin JSON directory not found: {base_dir}")
        return ""

    curr_dt = pd.to_datetime(curr_date, utc=True).normalize()
    ticker_u = ticker.upper()

    def quarter_filename_candidates(q_end: pd.Timestamp):
        """Produce ordered filename candidates (fiscal-shift first, then calendar)."""
        month = q_end.month
        year = q_end.year
        cal_q_map = {3: 1, 6: 2, 9: 3, 12: 4}
        cal_q = cal_q_map[month]
        cal_year = year
        # Fiscal-shift mapping
        if month == 12:
            fiscal_year = year + 1
            fiscal_q = 1
        elif month == 3:
            fiscal_year = year
            fiscal_q = 2
        elif month == 6:
            fiscal_year = year
            fiscal_q = 3
        elif month == 9:
            fiscal_year = year
            fiscal_q = 4
        else:
            raise ValueError("Invalid quarter end month")

        fiscal_style = f"{ticker_u}_PL_{fiscal_year}_Q{fiscal_q}.json"
        calendar_style = f"{ticker_u}_PL_{cal_year}_Q{cal_q}.json"
        if fiscal_style == calendar_style:
            return [fiscal_style]
        return [fiscal_style, calendar_style]

    def load_record_from_file(fname: str):
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and data:
                return data[0]  # assume single record per file
        except Exception as e:
            print(f"Error reading {path}: {e}")
        return None

    # Determine initial target quarter end
    if freq.lower().startswith("quarter"):
        target_q_end = _previous_calendar_quarter_end(curr_dt)
    else:
        target_q_end = _last_fiscal_year_end(curr_dt)

    max_lookback_quarters = 8
    attempts = 0
    chosen_record = None

    q_end = target_q_end
    while attempts < max_lookback_quarters and chosen_record is None:
        for fname in quarter_filename_candidates(q_end):
            rec = load_record_from_file(fname)
            if rec is None:
                continue

            # Parse dates
            try:
                rep_dt = pd.to_datetime(rec.get("Report Date"), utc=True).normalize()
                pub_dt = pd.to_datetime(rec.get("Publish Date"), utc=True).normalize()
            except Exception:
                continue

            # Validate finished & published before curr_date
            if pd.isna(rep_dt) or pd.isna(pub_dt):
                continue
            if rep_dt >= curr_dt or pub_dt > curr_dt:
                continue

            if freq.lower().startswith("annual"):
                fiscal_period = str(rec.get("Fiscal Period", "")).upper()
                if fiscal_period in ("FY", "Q4") or attempts > 0:
                    chosen_record = rec
                    break
            else:
                chosen_record = rec
                break

        if chosen_record is None:
            prev_ref = q_end - pd.Timedelta(days=1)
            q_end = _previous_calendar_quarter_end(prev_ref)
            attempts += 1

    if chosen_record is None:
        print("No suitable income statement found within lookback limit.")
        return ""

    publish_date_str = str(chosen_record.get("Publish Date"))[:10]
    report_date_str = str(chosen_record.get("Report Date"))[:10]
    series = pd.Series({k: v for k, v in chosen_record.items() if not k.startswith("_")})

    return (
        f"## {freq} income statement for {ticker} (Report Date {report_date_str}, "
        f"Publish Date {publish_date_str}):\n"
        + series.to_string()
        + "\n\nThis includes revenue, cost structure, operating results, non-operating items, taxes, and net income for the latest fully completed period before the trading date."
    )


def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


def get_reddit_global_news(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve pre-fetched macro / global news from a Perplexity JSON dump.

    Change: Instead of iterating Reddit posts, this now loads:
        DATA_DIR/perplexity_macro_news/macro_news_{start_date}.json

    Returns the 'cleanedOutput' field (already formatted text).
    The look_back_days and max_limit_per_day parameters are retained for signature
    compatibility but are not used in this JSON-based retrieval.
    """
    file_name = f"macro_news_{start_date}.json"
    file_path = os.path.join(DATA_DIR, "perplexity_macro_news", file_name)

    if not os.path.exists(file_path):
        print(f"Macro news file not found: {file_path}")
        # Fallback to OpenAI-backed macro news search
        try:
            print("Falling back to get_global_news_openai for macro news...")
            return get_global_news_openai(start_date)
        except Exception:
            return ""

    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        print(f"Error reading macro news file {file_path}: {e}")
        return ""

    cleaned = data.get("cleanedOutput")
    if not cleaned:
        print(f"'cleanedOutput' field missing or empty in {file_path}")
        return ""

    return cleaned

def get_reddit_company_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve recent Reddit posts for a ticker using pre-fetched aggregated JSON.

    Behavior change:
      - Instead of iterating day by day and calling fetch_top_from_category,
        this uses get_top_reddit_posts_for_ticker which already loads the
        single consolidated JSON file for the ticker and filters to the
        last 7 days ending at start_date.
      - The look_back_days parameter is retained for signature compatibility
        and only used to label the output window header (not to drive filtering).

    Args:
        ticker: Ticker symbol.
        start_date: End (anchor) date in yyyy-mm-dd.
        look_back_days: Window label (actual filtering inside helper fixed at 7 days).
        max_limit_per_day: Maximum number of posts to return (passed through).

    Returns:
        Markdown formatted string of top posts or empty string if none.
    """
    ticker_u = ticker.upper()
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        return ""

    end_dt = datetime.strptime(start_date, "%Y-%m-%d")
    before_dt = end_dt - relativedelta(days=look_back_days)
    before_str = before_dt.strftime("%Y-%m-%d")

    posts = get_top_reddit_posts_for_ticker(
        ticker_u,
        start_date,
        max_limit_per_day,
        data_dir=os.path.join(DATA_DIR, "reddit_data"),
    )

    if not posts:
        try:
            print(f"No reddit posts found for {ticker_u}; falling back to get_stock_news_openai...")
            return get_stock_news_openai(ticker_u, start_date)
        except Exception:
            return ""

    news_str = ""
    for post in posts:
        title = post.get("title", "").strip()
        content = (post.get("content") or post.get("selftext") or "").strip()
        url = post.get("url", "").strip()
        score = post.get("score", post.get("upvotes", ""))
        date_str = post.get("posted_date", "")
        meta_line = []
        if date_str:
            meta_line.append(date_str)
        if score != "":
            meta_line.append(f"Score: {score}")
        if url:
            meta_line.append(url)
        meta = " | ".join(meta_line)
        if meta:
            meta = f"\n{meta}"
        if content:
            news_str += f"### {title}{meta}\n\n{content}\n\n"
        else:
            news_str += f"### {title}{meta}\n\n"

    return f"## {ticker_u} News Reddit, from {before_str} to {start_date}:\n\n{news_str}"


def get_stock_stats_indicators_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    # if indicator not in best_ind_params:
    #     raise ValueError(
    #         f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}"
    #     )

    end_date = curr_date
    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date - relativedelta(days=look_back_days)

    if not online:
        # read from YFin data
        data = pd.read_csv(
            os.path.join(
                DATA_DIR,
                f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-07-27.csv",
            )  # type: ignore
        )
        # print("Successfully fetched data")
        data["Date"] = pd.to_datetime(data["Date"], utc=True)
        dates_in_df = data["Date"].astype(str).str[:10]

        ind_string = ""
        while curr_date >= before:
            # only do the trading dates
            if curr_date.strftime("%Y-%m-%d") in dates_in_df.values:
                indicator_value = get_stockstats_indicator(
                    symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
                )

                ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)
    else:
        # online gathering
        ind_string = ""
        while curr_date >= before:
            indicator_value = get_stockstats_indicator(
                symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
            )

            ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)

    result_str = (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {end_date}:\n\n"
        + ind_string
        + "\n\n"
        + best_ind_params.get(indicator, "No description available.")
    )

    return result_str


def get_stockstats_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    curr_date = curr_date.strftime("%Y-%m-%d")

    try:
        indicator_value = StockstatsUtils.get_stock_stats(
            symbol,
            indicator,
            curr_date,
            os.path.join(DATA_DIR, "market_data", "price_data"),
            online=online,
        )
    except Exception as e:
        print(
            f"Error getting stockstats indicator data for indicator {indicator} on {curr_date}: {e}"
        )
        return ""

    return str(indicator_value)


def get_YFin_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # calculate past days
    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    start_date = before.strftime("%Y-%m-%d")

    # read in data
    try:
        data = pd.read_csv(
            os.path.join(
                DATA_DIR,
                f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-07-27.csv",
            )
        )
    except Exception:
        # Fallback to yfinance fetch if local CSV missing
        start_dt = (datetime.strptime(curr_date, "%Y-%m-%d") - relativedelta(days=look_back_days+5)).strftime("%Y-%m-%d")
        end_dt = curr_date
        yf_df = yf.Ticker(symbol.upper()).history(start=start_dt, end=end_dt)
        if yf_df.empty:
            return f"No data found for {symbol} from {start_dt} to {end_dt}"
        yf_df = yf_df.reset_index()
        yf_df.rename(columns={"Date": "Date"}, inplace=True)
        data = yf_df

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= curr_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # Set pandas display options to show the full DataFrame
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = filtered_data.to_string()

    return (
        f"## Raw Market Data for {symbol} from {start_date} to {curr_date}:\n\n"
        + df_string
    )


def get_YFin_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):

    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # Create ticker object
    ticker = yf.Ticker(symbol.upper())

    # Fetch historical data for the specified date range
    data = ticker.history(start=start_date, end=end_date)

    # Check if data is empty
    if data.empty:
        return (
            f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        )

    # Remove timezone info from index for cleaner output
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # Round numerical values to 2 decimal places for cleaner display
    numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
    for col in numeric_columns:
        if col in data.columns:
            data[col] = data[col].round(2)

    # Convert DataFrame to CSV string
    csv_string = data.to_csv()

    # Add header information
    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string

# Dones
def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    # Resolve local price file (remove leading slash bug and allow fallback)
    price_dir = os.path.join(DATA_DIR, "market_data", "price_data")
    target_filename = f"{symbol}-YFin-data-2015-01-01-2025-07-27.csv"
    price_path = os.path.join(price_dir, target_filename)

    if not os.path.exists(price_path):
        # Fallback: pick latest matching file
        import glob
        pattern = os.path.join(price_dir, f"{symbol}-YFin-data-*.csv")
        candidates = sorted(glob.glob(pattern))
        if not candidates:
            raise FileNotFoundError(
                f"No local YFin price data file found for {symbol}. Searched {price_path} and pattern {pattern}"
            )
        price_path = candidates[-1]

    data = pd.read_csv(price_path)
    # Basic range validation based on file’s min/max dates
    if "Date" not in data.columns:
        raise ValueError(f"'Date' column missing in {price_path}")

    data["DateOnly"] = data["Date"].astype(str).str[:10]
    min_file_date = data["DateOnly"].min()
    max_file_date = data["DateOnly"].max()

    if start_date < min_file_date:
        raise Exception(
            f"Get_YFin_Data: {start_date} is outside of the data range of {min_file_date} to {max_file_date}"
        )
    if end_date > max_file_date:
        raise Exception(
            f"Get_YFin_Data: {end_date} is outside of the data range of {min_file_date} to {max_file_date}"
        )

    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= end_date)
    ].drop(columns=["DateOnly"]).reset_index(drop=True)

    return filtered_data
def get_stock_news_openai(ticker, curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Social Media for {ticker} from 7 days before {curr_date} to {curr_date}? Make sure you only get the data posted during that period.",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_global_news_openai(curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search global or macroeconomics news from 7 days before {curr_date} to {curr_date} that would be informative for trading purposes? Make sure you only get the data posted during that period.",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_fundamentals_openai(ticker, curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Fundamental for discussions on {ticker} during of the month before {curr_date} to the month of {curr_date}. Make sure you only get the data posted during that period. List as a table, with PE/PS/Cash flow/ etc",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text
