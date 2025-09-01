import os
import csv
from datetime import datetime, timedelta


import yfinance as yf


PRICE_DIR = os.path.join(os.path.dirname(__file__), 'market_data', 'price_data')

os.makedirs(PRICE_DIR, exist_ok=True)


def create_yfin_csv(symbol: str, end_date: str = None):
    """Fetch historical data via yfinance and write CSV compatible with interface.get_YFin_data.

    If yfinance or network is unavailable, fall back to generating synthetic sample data.

    The file is written with the same name pattern expected by the interface:
    {symbol}-YFin-data-START-END.csv
    """
    # Always use 2015-01-01 as start date
    start_date = "2015-01-01"
    if end_date is None:
        # default end date if not provided
        end_date = "2025-08-22"

    filename = os.path.join(PRICE_DIR, f"{symbol}-YFin-data-{start_date}-{end_date}.csv")

    # Fetch real data via yfinance
    ticker = yf.Ticker(symbol.upper())
    df = ticker.history(start=start_date, end=end_date)
    if not df.empty:
        # Ensure index has no tz info and format Date
        try:
            if getattr(df.index, 'tz', None) is not None:
                df.index = df.index.tz_localize(None)
        except Exception:
            pass

        rows = []
        for idx, row in df.iterrows():
            # include time to match interface expectations
            try:
                date_str = idx.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                date_str = str(idx)
            rows.append({
                'Date': date_str,
                'Open': f"{row['Open']:.2f}",
                'High': f"{row['High']:.2f}",
                'Low': f"{row['Low']:.2f}",
                'Close': f"{row['Close']:.2f}",
                'Adj Close': f"{row.get('Adj Close', row['Close']):.2f}",
                'Volume': str(int(row['Volume'])),
            })

        fieldnames = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        print(f"Wrote YFin CSV from yfinance: {filename}")
        return


if __name__ == '__main__':
    
    ticker_to_company = {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Google",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "NVDA": "Nvidia",
        "TSM": "Taiwan Semiconductor Manufacturing Company OR TSMC",
        "JPM": "JPMorgan Chase OR JP Morgan",
        "JNJ": "Johnson & Johnson OR JNJ",
        "V": "Visa",
        "WMT": "Walmart",
        "META": "Meta OR Facebook",
        "AMD": "AMD",
        "INTC": "Intel",
        "QCOM": "Qualcomm",
        "BABA": "Alibaba",
        "ADBE": "Adobe",
        "NFLX": "Netflix",
        "CRM": "Salesforce",
        "PYPL": "PayPal",
        "PLTR": "Palantir",
        "MU": "Micron",
        "SQ": "Block OR Square",
        "ZM": "Zoom",
        "CSCO": "Cisco",
        "SHOP": "Shopify",
        "ORCL": "Oracle",
        "X": "Twitter OR X",
        "SPOT": "Spotify",
        "AVGO": "Broadcom",
        "ASML": "ASML ",
        "TWLO": "Twilio",
        "SNAP": "Snap Inc.",
        "TEAM": "Atlassian",
        "SQSP": "Squarespace",
        "UBER": "Uber",
        "ROKU": "Roku",
        "PINS": "Pinterest",
    }
    
    for ticker in ticker_to_company.keys():
        print(f"Generating YFin CSV for {ticker} ({ticker_to_company[ticker]})...")
        create_yfin_csv(ticker, '2025-08-22')
