import pandas as pd
import yfinance as yf
from stockstats import wrap
from typing import Annotated
import os
from .config import get_config


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the stock data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = True,
    ):
        df = None
        data = None

        if not online:
            try:
                data = pd.read_csv(
                    os.path.join(
                        data_dir,
                        f"{symbol}-YFin-data-2015-01-01-2025-07-27.csv",
                    )
                )
                df = wrap(data)
            except FileNotFoundError:
                # Fallback: fetch via yfinance and save for offline reuse
                start_date = "2015-01-01"
                end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
                fetched = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True,
                )
                fetched = fetched.reset_index()
                os.makedirs(data_dir, exist_ok=True)
                out_file = os.path.join(
                    data_dir,
                    f"{symbol}-YFin-data-2015-01-01-2025-07-27.csv",
                )
                fetched.to_csv(out_file, index=False)
                df = wrap(fetched)
        else:
            # Get today's date as YYYY-mm-dd to add to cache
            today_date = pd.Timestamp.today()
            curr_date = pd.to_datetime(curr_date) # type: ignore

            end_date = today_date
            start_date = today_date - pd.DateOffset(years=15)
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")

            # Get config and ensure cache directory exists
            config = get_config()
            os.makedirs(config["data_cache_dir"], exist_ok=True)

            data_file = os.path.join(
                config["data_cache_dir"],
                f"{symbol}-YFin-data-{start_date}-{end_date}.csv",
            )

            if os.path.exists(data_file):
                data = pd.read_csv(data_file)
                data["Date"] = pd.to_datetime(data["Date"])
            else:
                data = yf.download(
                    symbol,
                    start=start_date,
                    end=end_date,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True,
                )
                data = data.reset_index() # type: ignore
                data.to_csv(data_file, index=False)

            df = wrap(data)
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            curr_date = curr_date.strftime("%Y-%m-%d") # type: ignore

        # attempt to compute indicator; remap problematic names
        try:
            df[indicator]
        except Exception:
            if indicator.lower() in ("dmi", "mdi"):
                # Use ADX as proxy if DMI parsing fails in current stockstats version
                indicator = "adx"
                df[indicator]
            else:
                raise
        matching_rows = df[df["Date"].str.startswith(curr_date)]

        if not matching_rows.empty:
            indicator_value = matching_rows[indicator].values[0]
            return indicator_value
        else:
            return "N/A: Not a trading day (weekend or holiday)"
