from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import numpy as np
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows import interface
import json
import yfinance as yf


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)
            
    

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """
        
        global_news_result = interface.get_reddit_global_news(curr_date, 7, 5)

        return global_news_result

    @staticmethod
    @tool
    def get_finnhub_news(
        ticker: Annotated[
            str,
            "Search query of a company, e.g. 'AAPL, TSM, etc.",
        ],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock from Finnhub within a date range
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing news about the company within the date range from start_date to end_date
        """

        end_date_str = end_date

        end_date = datetime.strptime(end_date, "%Y-%m-%d")  # type: ignore
        start_date = datetime.strptime(start_date, "%Y-%m-%d")  # type: ignore
        look_back_days = (end_date - start_date).days # type: ignore

        finnhub_news_result = interface.get_finnhub_news(
            ticker, end_date_str, look_back_days
        )

        return finnhub_news_result

    @staticmethod
    @tool
    def get_reddit_stock_info(
        ticker: Annotated[
            str,
            "Ticker of a company. e.g. AAPL, TSM",
        ],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given stock from Reddit, given the current date.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted dataframe containing the latest news about the company on the given date
        """

        stock_news_results = interface.get_reddit_company_news(ticker, curr_date, 7, 5)

        return stock_news_results

    @staticmethod
    @tool
    def get_YFin_data(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_YFin_data_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve the stock price data for a given ticker symbol from Yahoo Finance.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the stock price data for the specified ticker symbol in the specified date range.
        """

        result_data = interface.get_YFin_data_online(symbol, start_date, end_date)

        return result_data

    @staticmethod
    @tool
    def get_stockstats_indicators_report(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, False
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_stockstats_indicators_report_online(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = interface.get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, True
        )

        return result_stockstats

    @staticmethod
    @tool
    def get_finnhub_company_insider_sentiment(
        ticker: Annotated[str, "ticker symbol for the company"],
        curr_date: Annotated[
            str,
            "current date of you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider sentiment information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the sentiment in the past 30 days starting at curr_date
        """

        data_sentiment = interface.get_finnhub_company_insider_sentiment(
            ticker, curr_date, 30
        )

        return data_sentiment

    @staticmethod
    @tool
    def get_finnhub_company_insider_transactions(
        ticker: Annotated[str, "ticker symbol"],
        curr_date: Annotated[
            str,
            "current date you are trading at, yyyy-mm-dd",
        ],
    ):
        """
        Retrieve insider transaction information about a company (retrieved from public SEC information) for the past 30 days
        Args:
            ticker (str): ticker symbol of the company
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's insider transactions/trading information in the past 30 days
        """

        data_trans = interface.get_finnhub_company_insider_transactions(
            ticker, curr_date, 30
        )

        return data_trans

    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = interface.get_google_news(query, curr_date, 7)

        return google_news_results

    @staticmethod
    @tool
    def get_stock_news_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the company on the given date.
        """

        openai_news_results = interface.get_stock_news_openai(ticker, curr_date)

        return openai_news_results

    @staticmethod
    @tool
    def get_global_news_openai(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news on a given date using OpenAI's macroeconomics news API.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """

        openai_news_results = interface.get_global_news_openai(curr_date)

        return openai_news_results

    @staticmethod
    @tool
    def get_fundamentals_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest fundamental information about a given stock on a given date by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest fundamental information about the company on the given date.
        """

        openai_fundamentals_results = interface.get_fundamentals_openai(
            ticker, curr_date
        )

        return openai_fundamentals_results

    @staticmethod
    @tool
    def get_portfolio(ticker: Annotated[str, "Ticker of the company to get portfolio info for"], date: Annotated[str, "Date in yyyy-mm-dd format"]):
        """Retrieve current portfolio information for a given ticker."""
        portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
        if not os.path.exists(portfolio_path):
            return f"No portfolio exists."
        portfolio = json.load(open(portfolio_path, "r"))
        stockportfolio = portfolio.get(ticker, {})
        if not stockportfolio:
            return f"No holdings for {ticker} in portfolio."

        max_shares = round(stockportfolio.get('liquid', 0) / interface.get_close_price(ticker, date), 2)

        returned = f"""
# Portfolio
#### Current Liquidity: {stockportfolio.get('liquid', 0)}
#### {ticker} Holdings: {stockportfolio.get('totalAmount', 0)} shares
#### Max Shares Available to Purchase: {max_shares} shares
"""
        return returned
    
    @staticmethod
    @tool
    def get_price(ticker: Annotated[str, "Ticker of the company to get price for"], date: Annotated[str, "Date in yyyy-mm-dd format"]):
        """Retrieve the price for a given ticker on a given date from local CSV data."""
        try:
            price = interface.get_close_price(ticker, date)
            return f"Price for {ticker} on {date} is ${price:.2f}."
        except Exception as e:
            return f"Error retrieving price for {ticker} on {date}: {str(e)}"

    @staticmethod
    @tool
    def buy(ticker, date: Annotated[str, "Date of the purchase in yyyy-mm-dd format"], quantity = 1):
        """Tool wrapper for buying shares of a ticker on a specific date."""
        if not ticker or not date:
            return "Ticker and date must be provided for buying shares. Please provide both and try again."
        # Delegate to implementation
        return Toolkit.buy_impl(ticker, date, quantity)

    @staticmethod
    def buy_impl(ticker, date: Annotated[str, "Date of the purchase in yyyy-mm-dd format"], quantity = 1) -> str:
        """Implementation to buy shares and persist to portfolio.json (positions only, no trade log)"""
        portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
        if not os.path.exists(portfolio_path):
            with open(portfolio_path, "w") as f:
                json.dump({"portfolio": {}, "liquid": 1000000}, f)
        data = json.load(open(portfolio_path, "r"))
        if "portfolio" not in data or not isinstance(data["portfolio"], dict):
            data["portfolio"] = {}
        holdings = data["portfolio"].get(ticker, {"totalAmount": 0})
        # Fetch current price via Polygon-backed resolver (with internal fallbacks)
        try:
            current_price = float(interface.get_close_price(ticker, date))
        except Exception:
            current_price = 0.0
        # Update liquidity if present
        if "liquid" not in data:
            data["liquid"] = 1000000
        cost = quantity * current_price
        if data["liquid"] < cost and current_price > 0:
            quantity = int(data["liquid"] // current_price)
            cost = quantity * current_price
            if quantity == 0:
                return f"Insufficient liquidity to buy {ticker}."
        prev_qty = int(holdings.get("totalAmount", 0))
        buy_qty = int(quantity)
        new_qty = prev_qty + buy_qty
        holdings["totalAmount"] = new_qty
        holdings["last_price"] = current_price
        # Entry price logic: VWAP for adds on the same side; reset when side flips
        try:
            prev_entry = float(holdings.get("entry_price", 0.0) or 0.0)
            if current_price > 0 and buy_qty > 0:
                if prev_qty >= 0 and new_qty > 0:
                    if prev_qty > 0 and prev_entry > 0:
                        holdings["entry_price"] = ((prev_entry * prev_qty) + (current_price * buy_qty)) / max(new_qty, 1)
                    else:
                        holdings["entry_price"] = current_price
                else:
                    # Crossing from short to long -> new long entry
                    holdings["entry_price"] = current_price
        except Exception:
            holdings["entry_price"] = current_price
        data["portfolio"][ticker] = holdings
        data["liquid"] = max(0, data.get("liquid", 0) - cost)
        with open(portfolio_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ BUY EXECUTED: {quantity} shares of {ticker} at ${current_price:.2f} for ${cost:.2f}")
        print(f"💰 Remaining liquid cash: ${data['liquid']:.2f}")

        return f"Bought {quantity} shares of {ticker} at ${current_price:.2f} per share. Total cost: ${cost:.2f}"

    @staticmethod
    @tool
    def hold(ticker, date: Annotated[str, "Date of the hold in yyyy-mm-dd format"], note: Annotated[str, "Optional note"] = ""):
        """Tool wrapper for recording a HOLD decision for a ticker/date."""
        if not ticker or not date:
            return "Ticker and date must be provided for holding."
        return Toolkit.hold_impl(ticker, date, note)

    @staticmethod
    def hold_impl(ticker: str, date: str, note: str = "") -> str:
        """Persist a HOLD decision (positions-only schema); updates last_price when possible."""
        portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
        if not os.path.exists(portfolio_path):
            with open(portfolio_path, "w") as f:
                json.dump({"portfolio": {}, "liquid": 1000000}, f)
        data = json.load(open(portfolio_path, "r"))
        if "portfolio" not in data or not isinstance(data["portfolio"], dict):
            data["portfolio"] = {}
        holdings = data["portfolio"].get(ticker, {"totalAmount": 0})
        # Update last_price using Polygon-backed resolver
        try:
            current_price = float(interface.get_close_price(ticker, date))
            holdings["last_price"] = current_price
        except Exception:
            pass
        data["portfolio"][ticker] = holdings
        with open(portfolio_path, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"✅ HOLD EXECUTED: {ticker} - {note if note else 'No action taken'}")
        
        return f"Recorded HOLD for {ticker}. {('Note: ' + note) if note else ''}"

    @staticmethod
    @tool
    def sell(ticker, date: Annotated[str, "Date of the sale in yyyy-mm-dd format"], quantity = 1):
        """Tool wrapper for selling shares of a ticker on a specific date."""
        if not ticker or not date:
            return "Ticker and date must be provided for selling shares. Please provide both and try again."
        # Delegate to implementation
        if quantity <= 0:
            return "Quantity must be greater than 0 for selling shares. Please provide a valid quantity and try again."
        return Toolkit.sell_impl(ticker, date, quantity)

    @staticmethod
    def sell_impl(ticker: str, date: str, quantity: int = 1) -> str:
        """Implementation to sell shares and persist to portfolio.json (positions only, no trade log)"""
        portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
        if not os.path.exists(portfolio_path):
            return f"No portfolio exists to sell {ticker}."
        data = json.load(open(portfolio_path, "r"))
        if "portfolio" not in data or ticker not in data["portfolio"]:
            return f"No holdings for {ticker}."
        holdings = data["portfolio"][ticker]
        current_shares = holdings.get("totalAmount", 0)
        if current_shares <= 0:
            return f"No shares of {ticker} to sell."
        if quantity <= 0:
            return "Quantity must be positive."
        sell_qty = min(quantity, current_shares)
        # Get price via Polygon-backed resolver
        try:
            current_price = float(interface.get_close_price(ticker, date))
        except Exception:
            current_price = 0.0
        remaining = int(current_shares - sell_qty)
        prev_qty = int(current_shares)
        holdings["totalAmount"] = remaining
        holdings["last_price"] = current_price
        # Entry price rules: VWAP on same-side adds; reset on side flip; clear when flat
        prev_entry = float(holdings.get("entry_price", 0.0) or 0.0)
        if prev_qty >= 0 and remaining < 0:
            # New short entry
            holdings["entry_price"] = current_price
        elif prev_qty < 0 and remaining < 0:
            # Increasing short size -> weighted average by absolute shares
            prev_abs = abs(prev_qty)
            new_abs = abs(remaining)
            add_abs = abs(sell_qty)
            if prev_abs > 0 and prev_entry > 0:
                holdings["entry_price"] = ((prev_entry * prev_abs) + (current_price * add_abs)) / max(new_abs, 1)
            else:
                holdings["entry_price"] = current_price
        elif remaining > 0 and prev_qty < 0:
            # Crossed from short to long
            holdings["entry_price"] = current_price
        elif remaining == 0:
            holdings["entry_price"] = 0.0
        data["portfolio"][ticker] = holdings
        data["liquid"] = data.get("liquid", 0) + sell_qty * current_price
        with open(portfolio_path, "w") as f:
            json.dump(data, f, indent=2)
        
        sale_proceeds = sell_qty * current_price

        print(f"✅ SELL EXECUTED: {sell_qty} shares of {ticker} at ${current_price:.2f} for ${sale_proceeds:.2f}")
        print(f"💰 Remaining liquid cash: ${data['liquid']:.2f}")

        return f"Sold {sell_qty} shares of {ticker} at ${current_price:.2f} per share. Total proceeds: ${sale_proceeds:.2f}"

    @staticmethod
    @tool
    def get_portfolio_kelly_criterion(
        ticker: Annotated[str, "Ticker symbol of the company"],
    ) -> dict:
        """
        Calculate the Kelly Criterion for optimal bet sizing based on historical trades.
        Args:
            ticker (str): Ticker symbol of the company
        Returns:
            dict: Kelly Criterion results for all trades and specific ticker
        """
        
        portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
        try:
            with open(portfolio_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            return {"error": "Portfolio file not found", "all_trades_kelly": 0.0, "ticker_kelly": 0.0}
        portfolio_data = data.get("portfolio", {})
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")["Close"].iloc[-1]
        except Exception:
            return {"error": f"Could not fetch current price for {ticker}", "all_trades_kelly": 0.0, "ticker_kelly": 0.0}

        def calculate_kelly(trades_data, current_price):
            """Calculate Kelly Criterion from trades data"""
            if not trades_data:
                return 0.0
            wins = losses = 0
            total_win_return = total_loss_return = 0.0
            for trade in trades_data:
                if trade.get('type') == 'BUY':
                    purchase_price = trade.get('price_per_share') or trade.get('pricePerStockAtPurchase', 0)
                    if purchase_price and purchase_price > 0:
                        ret = (current_price - purchase_price) / purchase_price
                        if ret > 0:
                            wins += 1; total_win_return += ret
                        else:
                            losses += 1; total_loss_return += abs(ret)
            total_trades = wins + losses
            if total_trades == 0 or wins == 0:
                return 0.0
            win_p = wins / total_trades
            avg_win = total_win_return / wins if wins else 0
            if avg_win == 0:
                return 0.0
            kelly = (avg_win * win_p - (1 - win_p)) / avg_win
            return max(0.0, min(0.25, kelly))

        all_trades = []
        ticker_trades = []
        for sym, info in portfolio_data.items():
            trades = info.get('trades', [])
            all_trades.extend(trades)
            if sym.upper() == ticker.upper():
                ticker_trades.extend(trades)
        all_trades = all_trades[-50:]
        ticker_trades = ticker_trades[-50:]
        return {
            "ticker_trades_count": len(ticker_trades),
            "all_trades_kelly": round(calculate_kelly(all_trades, current_price), 4),
            "ticker_kelly": round(calculate_kelly(ticker_trades, current_price), 4),
        }
    
    
    @staticmethod
    @tool
    def get_portfolio_risk_parity(
        lookback_days: Annotated[int, "Number of days to look back for volatility calculation"] = 252,
    ) -> dict:
        """
        Calculate Risk Parity portfolio weights based on inverse volatility weighting.
        Reads tickers from portfolio.json file.
        Args:
            lookback_days (int): Number of days to look back for volatility calculation
        Returns:
            dict: Risk parity weights and analysis
        """
        
        try:
            # Read portfolio data to get tickers
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "weights": {}}
            
            # Extract tickers from portfolio
            tickers = list(portfolio_data.get('portfolio', {}).keys())
            
            if not tickers:
                return {"error": "No tickers found in portfolio", "weights": {}}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)  # Extra buffer
            
            returns_data = {}
            volatilities = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > 1:
                        returns = hist['Close'].pct_change().dropna()
                        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
                        returns_data[ticker] = returns
                        volatilities[ticker] = volatility
                except:
                    continue
            
            if not volatilities:
                return {"error": "Could not fetch data for any tickers", "weights": {}}
            
            # Calculate inverse volatility weights
            inv_vol = {ticker: 1/vol for ticker, vol in volatilities.items()}
            total_inv_vol = sum(inv_vol.values())
            
            # Normalize to get weights
            weights = {ticker: weight/total_inv_vol for ticker, weight in inv_vol.items()}
            
            # Calculate portfolio metrics
            portfolio_vol = np.sqrt(sum(weights[t1] * weights[t2] * 
                                       np.corrcoef(returns_data[t1], returns_data[t2])[0,1] *
                                       volatilities[t1] * volatilities[t2]
                                       for t1 in weights for t2 in weights
                                       if t1 in returns_data and t2 in returns_data))
            
            return {
                "strategy": "Risk Parity",
                "weights": {ticker: round(weight, 4) for ticker, weight in weights.items()},
                "individual_volatilities": {ticker: round(vol, 4) for ticker, vol in volatilities.items()},
                "portfolio_volatility": round(portfolio_vol, 4),
                "diversification_ratio": round(sum(weights[t] * volatilities[t] for t in weights) / portfolio_vol, 2),
                "methodology": "Inverse volatility weighting to equalize risk contribution"
            }
            
        except Exception as e:
            return {"error": f"Risk parity calculation failed: {str(e)}", "weights": {}}

    @staticmethod
    @tool
    def get_portfolio_black_litterman(
        views: Annotated[dict, "Expected return views for each ticker"],
        confidence: Annotated[float, "Confidence in views (0-1)"] = 0.5,
        lookback_days: Annotated[int, "Number of days for covariance estimation"] = 252,
    ) -> dict:
        """
        Calculate Black-Litterman portfolio weights incorporating market views.
        Reads tickers and market cap weights from portfolio.json file.
        Args:
            views (dict): Expected return views for each ticker
            confidence (float): Confidence in views (0-1)
            lookback_days (int): Number of days for covariance estimation
        Returns:
            dict: Black-Litterman optimized weights and analysis
        """
        
        try:
            # Read portfolio data to get tickers and weights
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "weights": {}}
            
            # Extract tickers and calculate market cap weights from portfolio
            portfolio_holdings = portfolio_data.get('portfolio', {})
            if not portfolio_holdings:
                return {"error": "No holdings found in portfolio", "weights": {}}
            
            tickers = list(portfolio_holdings.keys())
            
            # Calculate market cap weights based on total amounts in portfolio
            total_portfolio_value = sum(holding.get('totalAmount', 0) for holding in portfolio_holdings.values())
            market_cap_weights = {}
            
            for ticker, holding in portfolio_holdings.items():
                weight = holding.get('totalAmount', 0) / total_portfolio_value if total_portfolio_value > 0 else 1/len(tickers)
                market_cap_weights[ticker] = weight
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)
            
            returns_data = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > 1:
                        returns = hist['Close'].pct_change().dropna()
                        returns_data[ticker] = returns
                except:
                    continue
            
            if len(returns_data) < 2:
                return {"error": "Insufficient data for Black-Litterman", "weights": {}}
            
            # Create returns matrix
            returns_df = pd.DataFrame(returns_data)
            returns_matrix = returns_df.values
            
            # Calculate covariance matrix
            cov_matrix = np.cov(returns_matrix.T) * 252  # Annualized
            
            # Market equilibrium returns (reverse optimization)
            risk_aversion = 3.0  # Typical assumption
            market_weights = np.array([market_cap_weights.get(t, 1/len(tickers)) for t in returns_df.columns])
            market_weights = market_weights / market_weights.sum()  # Normalize
            
            pi = risk_aversion * np.dot(cov_matrix, market_weights)  # Implied returns
            
            # Black-Litterman calculation
            tau = 0.025  # Scaling factor
            
            # Views matrix P and views vector Q
            P = np.eye(len(returns_df.columns))  # Identity matrix for absolute views
            Q = np.array([views.get(ticker, 0) for ticker in returns_df.columns])
            
            # Uncertainty matrix Omega
            omega = confidence * np.diag(np.diag(np.dot(P, np.dot(tau * cov_matrix, P.T))))
            
            # Black-Litterman formula
            M1 = np.linalg.inv(tau * cov_matrix)
            M2 = np.dot(P.T, np.dot(np.linalg.inv(omega), P))
            M3 = np.dot(np.linalg.inv(tau * cov_matrix), pi)
            M4 = np.dot(P.T, np.dot(np.linalg.inv(omega), Q))
            
            mu_bl = np.dot(np.linalg.inv(M1 + M2), M3 + M4)  # BL expected returns
            cov_bl = np.linalg.inv(M1 + M2)  # BL covariance
            
            # Optimize portfolio
            inv_cov = np.linalg.inv(cov_bl)
            ones = np.ones((len(mu_bl), 1))
            
            # Mean-variance optimization
            weights_bl = np.dot(inv_cov, mu_bl) / (risk_aversion)
            weights_bl = weights_bl / weights_bl.sum()  # Normalize
            
            weights_dict = {ticker: round(float(weight), 4) 
                           for ticker, weight in zip(returns_df.columns, weights_bl)}
            
            # Calculate portfolio metrics
            portfolio_return = np.dot(weights_bl, mu_bl)
            portfolio_risk = np.sqrt(np.dot(weights_bl, np.dot(cov_bl, weights_bl)))
            
            return {
                "strategy": "Black-Litterman",
                "weights": weights_dict,
                "market_weights": {ticker: round(market_cap_weights.get(ticker, 0), 4) for ticker in returns_df.columns},
                "expected_returns": {ticker: round(float(ret), 4) for ticker, ret in zip(returns_df.columns, mu_bl)},
                "implied_returns": {ticker: round(float(ret), 4) for ticker, ret in zip(returns_df.columns, pi)},
                "portfolio_return": round(float(portfolio_return), 4),
                "portfolio_risk": round(float(portfolio_risk), 4),
                "confidence_level": confidence,
                "methodology": "Bayesian approach combining market equilibrium with investor views"
            }
            
        except Exception as e:
            return {"error": f"Black-Litterman calculation failed: {str(e)}", "weights": {}}

    @staticmethod
    @tool
    def get_portfolio_mean_reversion(
        lookback_days: Annotated[int, "Number of days for mean reversion analysis"] = 60,
        z_score_threshold: Annotated[float, "Z-score threshold for mean reversion signals"] = 2.0,
    ) -> dict:
        """
        Calculate mean reversion portfolio weights based on z-score analysis.
        Reads tickers from portfolio.json file.
        Args:
            lookback_days (int): Number of days for mean reversion analysis
            z_score_threshold (float): Z-score threshold for mean reversion signals
        Returns:
            dict: Mean reversion strategy weights and signals
        """
        
        try:
            # Read portfolio data to get tickers
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "signals": {}}
            
            # Extract tickers from portfolio
            tickers = list(portfolio_data.get('portfolio', {}).keys())
            
            if not tickers:
                return {"error": "No tickers found in portfolio", "signals": {}}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)
            
            mean_reversion_signals = {}
            z_scores = {}
            current_prices = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > lookback_days:
                        prices = hist['Close']
                        current_price = prices.iloc[-1]
                        
                        # Calculate rolling statistics
                        rolling_mean = prices.rolling(window=lookback_days).mean().iloc[-1]
                        rolling_std = prices.rolling(window=lookback_days).std().iloc[-1]
                        
                        # Calculate z-score
                        z_score = (current_price - rolling_mean) / rolling_std if rolling_std > 0 else 0
                        
                        # Mean reversion signal
                        if z_score > z_score_threshold:
                            signal = "SELL"  # Overvalued, expect reversion down
                            weight = max(0, (z_score - z_score_threshold) / 10)  # Scale weight
                        elif z_score < -z_score_threshold:
                            signal = "BUY"   # Undervalued, expect reversion up
                            weight = max(0, (abs(z_score) - z_score_threshold) / 10)  # Scale weight
                        else:
                            signal = "HOLD"
                            weight = 0
                        
                        mean_reversion_signals[ticker] = {
                            "signal": signal,
                            "z_score": round(z_score, 3),
                            "weight": round(weight, 4),
                            "current_price": round(current_price, 2),
                            "mean_price": round(rolling_mean, 2)
                        }
                        
                        z_scores[ticker] = z_score
                        current_prices[ticker] = current_price
                        
                except:
                    continue
            
            if not mean_reversion_signals:
                return {"error": "Could not calculate mean reversion for any tickers", "signals": {}}
            
            # Normalize weights for long positions (BUY signals)
            buy_weights = {ticker: data["weight"] for ticker, data in mean_reversion_signals.items() 
                          if data["signal"] == "BUY"}
            
            if buy_weights:
                total_buy_weight = sum(buy_weights.values())
                if total_buy_weight > 0:
                    normalized_weights = {ticker: weight/total_buy_weight 
                                        for ticker, weight in buy_weights.items()}
                else:
                    normalized_weights = {ticker: 1/len(buy_weights) for ticker in buy_weights}
            else:
                normalized_weights = {}
            
            # Calculate portfolio metrics
            avg_z_score = np.mean(list(z_scores.values())) if z_scores else 0
            reversion_opportunities = len([s for s in mean_reversion_signals.values() 
                                         if abs(s["z_score"]) > z_score_threshold])
            
            return {
                "strategy": "Mean Reversion",
                "signals": mean_reversion_signals,
                "portfolio_weights": normalized_weights,
                "average_z_score": round(avg_z_score, 3),
                "reversion_opportunities": reversion_opportunities,
                "threshold_used": z_score_threshold,
                "lookback_period": lookback_days,
                "methodology": f"Buy undervalued (z < -{z_score_threshold}), sell overvalued (z > {z_score_threshold})"
            }
            
        except Exception as e:
            return {"error": f"Mean reversion calculation failed: {str(e)}", "signals": {}}
    @staticmethod
    @tool
    def get_portfolio_momentum(
        short_period: Annotated[int, "Short period for momentum calculation"] = 20,
        long_period: Annotated[int, "Long period for momentum calculation"] = 60,
        momentum_threshold: Annotated[float, "Momentum threshold for signals"] = 0.02,
    ) -> dict:
        """
        Calculate momentum portfolio weights based on price momentum analysis.
        Reads tickers from portfolio.json file.
        Args:
            short_period (int): Short period for momentum calculation
            long_period (int): Long period for momentum calculation  
            momentum_threshold (float): Momentum threshold for signals
        Returns:
            dict: Momentum strategy weights and signals
        """
        
        try:
            # Read portfolio data to get tickers
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "signals": {}}
            
            # Extract tickers from portfolio
            tickers = list(portfolio_data.get('portfolio', {}).keys())
            
            if not tickers:
                return {"error": "No tickers found in portfolio", "signals": {}}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=long_period + 30)
            
            momentum_signals = {}
            momentum_scores = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > long_period:
                        prices = hist['Close']
                        
                        # Calculate momentum indicators
                        short_ma = prices.rolling(window=short_period).mean().iloc[-1]
                        long_ma = prices.rolling(window=long_period).mean().iloc[-1]
                        current_price = prices.iloc[-1]
                        
                        # Price momentum (rate of change)
                        price_momentum = (current_price - prices.iloc[-long_period]) / prices.iloc[-long_period]
                        
                        # Moving average momentum
                        ma_momentum = (short_ma - long_ma) / long_ma if long_ma > 0 else 0
                        
                        # Combined momentum score
                        momentum_score = (price_momentum + ma_momentum) / 2
                        
                        # RSI calculation for additional confirmation
                        try:
                            delta = prices.diff()
                            up = delta.clip(lower=0)
                            down = -1 * delta.clip(upper=0)
                            ma_up = up.rolling(window=14).mean()
                            ma_down = down.rolling(window=14).mean()
                            rs = ma_up / ma_down
                            rsi = 100 - (100 / (1 + rs))
                            current_rsi = float(rsi.iloc[-1]) if len(rsi) > 0 and not np.isnan(rsi.iloc[-1]) else 50.0
                        except:
                            current_rsi = 50.0  # Default neutral RSI
                        
                        # Generate signals
                        if momentum_score > momentum_threshold and current_rsi < 70:
                            signal = "BUY"  # Strong upward momentum, not overbought
                            weight = min(momentum_score * 5, 1.0)  # Scale momentum to weight
                        elif momentum_score < -momentum_threshold and current_rsi > 30:
                            signal = "SELL"  # Strong downward momentum, not oversold
                            weight = min(abs(momentum_score) * 5, 1.0)
                        else:
                            signal = "HOLD"
                            weight = 0
                        
                        momentum_signals[ticker] = {
                            "signal": signal,
                            "momentum_score": round(momentum_score, 4),
                            "price_momentum": round(price_momentum, 4),
                            "ma_momentum": round(ma_momentum, 4),
                            "rsi": round(current_rsi, 2),
                            "weight": round(weight, 4),
                            "current_price": round(current_price, 2),
                            "short_ma": round(short_ma, 2),
                            "long_ma": round(long_ma, 2)
                        }
                        
                        momentum_scores[ticker] = momentum_score
                        
                except:
                    continue
            
            if not momentum_signals:
                return {"error": "Could not calculate momentum for any tickers", "signals": {}}
            
            # Normalize weights for long positions (BUY signals)
            buy_weights = {ticker: data["weight"] for ticker, data in momentum_signals.items() 
                          if data["signal"] == "BUY"}
            
            if buy_weights:
                total_buy_weight = sum(buy_weights.values())
                if total_buy_weight > 0:
                    normalized_weights = {ticker: weight/total_buy_weight 
                                        for ticker, weight in buy_weights.items()}
                else:
                    normalized_weights = {ticker: 1/len(buy_weights) for ticker in buy_weights}
            else:
                normalized_weights = {}
            
            # Calculate portfolio metrics
            avg_momentum = np.mean(list(momentum_scores.values())) if momentum_scores else 0
            strong_momentum_count = len([s for s in momentum_signals.values() 
                                       if abs(s["momentum_score"]) > momentum_threshold])
            
            return {
                "strategy": "Momentum",
                "signals": momentum_signals,
                "portfolio_weights": normalized_weights,
                "average_momentum": round(avg_momentum, 4),
                "strong_momentum_count": strong_momentum_count,
                "momentum_threshold": momentum_threshold,
                "short_period": short_period,
                "long_period": long_period,
                "methodology": f"Buy strong upward momentum (>{momentum_threshold}), sell strong downward momentum (<-{momentum_threshold})"
            }
            
        except Exception as e:
            return {"error": f"Momentum calculation failed: {str(e)}", "signals": {}}

    @staticmethod
    @tool
    def perform_stress_test(
        portfolio_weights: Annotated[dict, "Portfolio weights for each ticker"] = {},
        scenarios: Annotated[list, "List of stress test scenarios to run"] = [],
        confidence_level: Annotated[float, "Confidence level for VaR calculation"] = 0.05,
        lookback_days: Annotated[int, "Number of days for historical data"] = 252,
    ) -> dict:
        """
        Perform comprehensive stress testing on portfolio positions.
        Reads tickers from portfolio.json if weights not provided.
        Args:
            portfolio_weights (dict): Portfolio weights for each ticker (optional)
            scenarios (list): Custom stress test scenarios (optional)
            confidence_level (float): Confidence level for VaR (default 5%)
            lookback_days (int): Historical data lookback period
        Returns:
            dict: Comprehensive stress test results including VaR, scenario analysis
        """
        
        try:
            # Read portfolio data to get tickers and weights if not provided
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "stress_tests": {}}
            
            # Extract tickers and weights
            if not portfolio_weights:
                portfolio_holdings = portfolio_data.get('portfolio', {})
                if not portfolio_holdings:
                    return {"error": "No holdings found in portfolio", "stress_tests": {}}
                
                # Calculate weights based on total amounts
                total_portfolio_value = sum(holding.get('totalAmount', 0) for holding in portfolio_holdings.values())
                portfolio_weights = {}
                
                for ticker, holding in portfolio_holdings.items():
                    weight = holding.get('totalAmount', 0) / total_portfolio_value if total_portfolio_value > 0 else 1/len(portfolio_holdings)
                    portfolio_weights[ticker] = weight
            
            tickers = list(portfolio_weights.keys())
            
            if not tickers:
                return {"error": "No tickers found for stress testing", "stress_tests": {}}
            
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)
            
            returns_data = {}
            price_data = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > 1:
                        returns = hist['Close'].pct_change().dropna()
                        returns_data[ticker] = returns
                        price_data[ticker] = hist['Close']
                except:
                    continue
            
            if not returns_data:
                return {"error": "Could not fetch data for any tickers", "stress_tests": {}}
            
            # Create returns DataFrame
            returns_df = pd.DataFrame(returns_data)
            
            # Default stress test scenarios if not provided
            if not scenarios:
                scenarios = [
                    {"name": "Market Crash 2008", "market_shock": -0.20, "volatility_spike": 2.5, "correlation_increase": 0.3},
                    {"name": "Black Monday 1987", "market_shock": -0.22, "volatility_spike": 3.0, "correlation_increase": 0.5},
                    {"name": "COVID-19 Crash", "market_shock": -0.34, "volatility_spike": 4.0, "correlation_increase": 0.4},
                    {"name": "Flash Crash", "market_shock": -0.10, "volatility_spike": 5.0, "correlation_increase": 0.2},
                    {"name": "Dot-com Crash", "market_shock": -0.49, "volatility_spike": 2.0, "correlation_increase": 0.3},
                    {"name": "Inflation Spike", "market_shock": -0.15, "volatility_spike": 1.8, "correlation_increase": 0.25},
                    {"name": "Currency Crisis", "market_shock": -0.25, "volatility_spike": 3.5, "correlation_increase": 0.6},
                    {"name": "Interest Rate Shock", "market_shock": -0.12, "volatility_spike": 2.2, "correlation_increase": 0.35}
                ]
            
            stress_test_results = {}
            
            # Calculate baseline portfolio metrics
            portfolio_returns = np.dot(returns_df.values, list(portfolio_weights.values()))
            baseline_volatility = np.std(portfolio_returns) * np.sqrt(252)  # Annualized
            baseline_var = np.percentile(portfolio_returns, confidence_level * 100)
            baseline_cvar = np.mean(portfolio_returns[portfolio_returns <= baseline_var])
            
            # Run stress tests for each scenario
            for scenario in scenarios:
                scenario_name = scenario["name"]
                market_shock = scenario.get("market_shock", -0.20)
                volatility_spike = scenario.get("volatility_spike", 2.0)
                correlation_increase = scenario.get("correlation_increase", 0.3)
                
                # Simulate stressed returns
                stressed_returns = returns_df.copy()
                
                # Apply market shock (systematic risk)
                for ticker in tickers:
                    if ticker in stressed_returns.columns:
                        # Apply market shock with some idiosyncratic variation
                        idiosyncratic_factor = np.random.normal(1.0, 0.1, len(stressed_returns))
                        shock = market_shock * idiosyncratic_factor
                        stressed_returns[ticker] = stressed_returns[ticker] + shock
                
                # Increase volatility
                for ticker in tickers:
                    if ticker in stressed_returns.columns:
                        mean_return = stressed_returns[ticker].mean()
                        stressed_returns[ticker] = mean_return + (stressed_returns[ticker] - mean_return) * volatility_spike
                
                # Calculate stressed portfolio metrics
                stressed_portfolio_returns = np.dot(stressed_returns.values, list(portfolio_weights.values()))
                stressed_volatility = np.std(stressed_portfolio_returns) * np.sqrt(252)
                stressed_var = np.percentile(stressed_portfolio_returns, confidence_level * 100)
                stressed_cvar = np.mean(stressed_portfolio_returns[stressed_portfolio_returns <= stressed_var])
                
                # Calculate maximum drawdown
                cumulative_returns = (1 + stressed_portfolio_returns).cumprod()
                rolling_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = drawdown.min()
                
                # Portfolio value impact (assuming $1M portfolio)
                portfolio_value = 1000000
                var_loss = abs(stressed_var) * portfolio_value
                cvar_loss = abs(stressed_cvar) * portfolio_value
                max_loss = abs(max_drawdown) * portfolio_value
                
                # Individual ticker stress impact
                ticker_impacts = {}
                for ticker in tickers:
                    if ticker in stressed_returns.columns:
                        ticker_return_impact = stressed_returns[ticker].mean() * 252  # Annualized
                        ticker_vol_impact = stressed_returns[ticker].std() * np.sqrt(252)
                        position_value = portfolio_weights.get(ticker, 0) * portfolio_value
                        
                        ticker_impacts[ticker] = {
                            "weight": round(portfolio_weights.get(ticker, 0), 4),
                            "return_impact": round(ticker_return_impact, 4),
                            "volatility_impact": round(ticker_vol_impact, 4),
                            "position_value": round(position_value, 2),
                            "estimated_loss": round(abs(ticker_return_impact) * position_value, 2)
                        }
                
                stress_test_results[scenario_name] = {
                    "scenario_parameters": scenario,
                    "portfolio_impact": {
                        "baseline_volatility": round(baseline_volatility, 4),
                        "stressed_volatility": round(stressed_volatility, 4),
                        "volatility_increase": round((stressed_volatility - baseline_volatility) / baseline_volatility, 4),
                        "var_1d": round(stressed_var, 6),
                        "cvar_1d": round(stressed_cvar, 6),
                        "max_drawdown": round(max_drawdown, 4),
                        "var_loss_usd": round(var_loss, 2),
                        "cvar_loss_usd": round(cvar_loss, 2),
                        "max_loss_usd": round(max_loss, 2)
                    },
                    "ticker_impacts": ticker_impacts,
                    "risk_metrics": {
                        "sharpe_degradation": round((stressed_volatility - baseline_volatility) / baseline_volatility, 4),
                        "tail_risk_ratio": round(abs(stressed_cvar) / abs(baseline_cvar) if baseline_cvar != 0 else 0, 2),
                        "correlation_stress": correlation_increase
                    }
                }
            
            # Calculate aggregate stress test summary
            worst_case_var = min([result["portfolio_impact"]["var_1d"] for result in stress_test_results.values()])
            worst_case_scenario = [name for name, result in stress_test_results.items() 
                                 if result["portfolio_impact"]["var_1d"] == worst_case_var][0]
            
            avg_volatility_increase = np.mean([result["portfolio_impact"]["volatility_increase"] 
                                             for result in stress_test_results.values()])
            
            # Portfolio resilience score (0-100, higher is better)
            max_vol_increase = max([result["portfolio_impact"]["volatility_increase"] 
                                  for result in stress_test_results.values()])
            resilience_score = max(0, 100 - (max_vol_increase * 100))
            
            return {
                "stress_test_summary": {
                    "total_scenarios": len(scenarios),
                    "worst_case_scenario": worst_case_scenario,
                    "worst_case_var": round(worst_case_var, 6),
                    "average_volatility_increase": round(avg_volatility_increase, 4),
                    "portfolio_resilience_score": round(resilience_score, 2),
                    "confidence_level": confidence_level,
                    "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "baseline_metrics": {
                    "portfolio_volatility": round(baseline_volatility, 4),
                    "baseline_var": round(baseline_var, 6),
                    "baseline_cvar": round(baseline_cvar, 6),
                    "portfolio_weights": {ticker: round(weight, 4) for ticker, weight in portfolio_weights.items()}
                },
                "stress_test_results": stress_test_results,
                "recommendations": {
                    "high_risk_positions": [ticker for ticker, weight in portfolio_weights.items() if weight > 0.2],
                    "diversification_needed": resilience_score < 70,
                    "hedge_recommended": worst_case_var < -0.05,
                    "risk_management": "Consider position sizing limits and correlation-based hedging" if max_vol_increase > 1.0 else "Portfolio shows good stress resilience"
                },
                "methodology": f"Monte Carlo stress testing with {len(scenarios)} scenarios, {confidence_level:.1%} VaR confidence level"
            }
            
        except Exception as e:
            return {"error": f"Stress test calculation failed: {str(e)}", "stress_tests": {}}

    @staticmethod
    @tool
    def calculate_beta(
        portfolio_weights: Annotated[dict, "Portfolio weights for each ticker"] = {},
        benchmark_ticker: Annotated[str, "Benchmark ticker symbol"] = "SPY",
        lookback_days: Annotated[int, "Number of days for beta calculation"] = 252,
    ) -> dict:
        """
        Calculate portfolio beta relative to a benchmark index.
        Reads tickers from portfolio.json if weights not provided.
        Args:
            portfolio_weights (dict): Portfolio weights for each ticker (optional)
            benchmark_ticker (str): Benchmark ticker symbol (default: SPY)
            lookback_days (int): Historical data lookback period
        Returns:
            dict: Beta analysis including individual and portfolio betas
        """
        
        try:
            # Read portfolio data to get tickers and weights if not provided
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "beta_analysis": {}}
            
            # Extract tickers and weights
            if not portfolio_weights:
                portfolio_holdings = portfolio_data.get('portfolio', {})
                if not portfolio_holdings:
                    return {"error": "No holdings found in portfolio", "beta_analysis": {}}
                
                # Calculate weights based on total amounts
                total_portfolio_value = sum(holding.get('totalAmount', 0) for holding in portfolio_holdings.values())
                portfolio_weights = {}
                
                for ticker, holding in portfolio_holdings.items():
                    weight = holding.get('totalAmount', 0) / total_portfolio_value if total_portfolio_value > 0 else 1/len(portfolio_holdings)
                    portfolio_weights[ticker] = weight
            
            tickers = list(portfolio_weights.keys())
            
            if not tickers:
                return {"error": "No tickers found for beta calculation", "beta_analysis": {}}
            
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days + 30)
            
            # Get benchmark data
            try:
                benchmark = yf.Ticker(benchmark_ticker)
                benchmark_hist = benchmark.history(start=start_date, end=end_date)
                benchmark_returns = benchmark_hist['Close'].pct_change().dropna()
            except:
                return {"error": f"Could not fetch benchmark data for {benchmark_ticker}", "beta_analysis": {}}
            
            # Get individual stock data and calculate betas
            individual_betas = {}
            returns_data = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > 1:
                        stock_returns = hist['Close'].pct_change().dropna()
                        
                        # Align dates with benchmark
                        aligned_data = pd.DataFrame({
                            'stock': stock_returns,
                            'benchmark': benchmark_returns
                        }).dropna()
                        
                        if len(aligned_data) > 20:  # Need sufficient data points
                            # Calculate beta using covariance method
                            covariance = np.cov(aligned_data['stock'], aligned_data['benchmark'])[0, 1]
                            benchmark_variance = np.var(aligned_data['benchmark'])
                            
                            if benchmark_variance > 0:
                                beta = covariance / benchmark_variance
                                
                                # Calculate correlation and R-squared
                                correlation = np.corrcoef(aligned_data['stock'], aligned_data['benchmark'])[0, 1]
                                r_squared = correlation ** 2
                                
                                # Calculate alpha (Jensen's alpha)
                                stock_mean_return = aligned_data['stock'].mean() * 252  # Annualized
                                benchmark_mean_return = aligned_data['benchmark'].mean() * 252  # Annualized
                                alpha = stock_mean_return - (benchmark_mean_return * beta)
                                
                                # Calculate tracking error
                                excess_returns = aligned_data['stock'] - beta * aligned_data['benchmark']
                                tracking_error = excess_returns.std() * np.sqrt(252)  # Annualized
                                
                                individual_betas[ticker] = {
                                    "beta": round(beta, 4),
                                    "alpha": round(alpha, 4),
                                    "correlation": round(correlation, 4),
                                    "r_squared": round(r_squared, 4),
                                    "tracking_error": round(tracking_error, 4),
                                    "weight": round(portfolio_weights.get(ticker, 0), 4),
                                    "data_points": len(aligned_data)
                                }
                                
                                returns_data[ticker] = aligned_data['stock']
                                
                except Exception as e:
                    continue
            
            if not individual_betas:
                return {"error": "Could not calculate beta for any tickers", "beta_analysis": {}}
            
            # Calculate portfolio beta (weighted average of individual betas)
            portfolio_beta = sum(individual_betas[ticker]["beta"] * portfolio_weights.get(ticker, 0) 
                               for ticker in individual_betas)
            
            # Calculate portfolio alpha (weighted average of individual alphas)
            portfolio_alpha = sum(individual_betas[ticker]["alpha"] * portfolio_weights.get(ticker, 0) 
                                for ticker in individual_betas)
            
            # Calculate portfolio tracking error
            portfolio_returns_series = pd.Series(dtype=float)
            
            # Create aligned portfolio returns
            for ticker in returns_data:
                weight = portfolio_weights.get(ticker, 0)
                ticker_returns = returns_data[ticker]
                
                if portfolio_returns_series.empty:
                    portfolio_returns_series = weight * ticker_returns
                else:
                    # Align indices and add
                    aligned_ticker = ticker_returns.reindex(portfolio_returns_series.index, fill_value=0)
                    portfolio_returns_series += weight * aligned_ticker
            
            # Align portfolio returns with benchmark
            aligned_benchmark = benchmark_returns.reindex(portfolio_returns_series.index)
            portfolio_excess_returns = portfolio_returns_series - portfolio_beta * aligned_benchmark
            portfolio_tracking_error = portfolio_excess_returns.std() * np.sqrt(252)
            
            # Beta risk categories
            def categorize_beta(beta_value):
                if beta_value < 0.7:
                    return "Low Beta (Defensive)"
                elif beta_value < 0.85:
                    return "Below Market"
                elif beta_value < 1.15:
                    return "Market Neutral"
                elif beta_value < 1.3:
                    return "Above Market"
                else:
                    return "High Beta (Aggressive)"
            
            # Hedging recommendations based on beta
            hedging_needs = {}
            if portfolio_beta > 1.2:
                hedging_needs["high_beta"] = "Consider short index futures to reduce market exposure"
            elif portfolio_beta < 0.8:
                hedging_needs["low_beta"] = "Consider long index futures to increase market exposure"
            
            if portfolio_tracking_error > 0.15:
                hedging_needs["high_tracking_error"] = "High tracking error - consider sector hedging"
            
            # Calculate sector exposure if possible
            sector_betas = {}
            high_beta_positions = [ticker for ticker, data in individual_betas.items() 
                                 if data["beta"] > 1.3 and data["weight"] > 0.05]
            low_beta_positions = [ticker for ticker, data in individual_betas.items() 
                                if data["beta"] < 0.7 and data["weight"] > 0.05]
            
            return {
                "portfolio_beta_analysis": {
                    "portfolio_beta": round(portfolio_beta, 4),
                    "portfolio_alpha": round(portfolio_alpha, 4),
                    "portfolio_tracking_error": round(portfolio_tracking_error, 4),
                    "beta_category": categorize_beta(portfolio_beta),
                    "benchmark": benchmark_ticker,
                    "analysis_period": f"{lookback_days} days",
                    "calculation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "individual_betas": individual_betas,
                "risk_assessment": {
                    "market_sensitivity": "High" if portfolio_beta > 1.2 else "Low" if portfolio_beta < 0.8 else "Moderate",
                    "diversification_benefit": "Good" if portfolio_tracking_error < 0.1 else "Poor" if portfolio_tracking_error > 0.2 else "Moderate",
                    "alpha_generation": "Positive" if portfolio_alpha > 0.02 else "Negative" if portfolio_alpha < -0.02 else "Neutral"
                },
                "position_analysis": {
                    "high_beta_positions": high_beta_positions,
                    "low_beta_positions": low_beta_positions,
                    "concentrated_risk": [ticker for ticker, weight in portfolio_weights.items() if weight > 0.2]
                },
                "hedging_recommendations": hedging_needs if hedging_needs else {"status": "No immediate hedging needed"},
                "beta_statistics": {
                    "max_individual_beta": round(max([data["beta"] for data in individual_betas.values()]), 4),
                    "min_individual_beta": round(min([data["beta"] for data in individual_betas.values()]), 4),
                    "avg_individual_beta": round(np.mean([data["beta"] for data in individual_betas.values()]), 4),
                    "beta_dispersion": round(np.std([data["beta"] for data in individual_betas.values()]), 4)
                },
                "methodology": f"Beta calculated using {lookback_days}-day regression vs {benchmark_ticker}"
            }
            
        except Exception as e:
            return {"error": f"Beta calculation failed: {str(e)}", "beta_analysis": {}}

    @staticmethod
    @tool
    def design_hedging_strategy(
        portfolio_weights: Annotated[dict, "Portfolio weights for each ticker"] = {},
        hedge_types: Annotated[list, "Types of hedges to analyze"] = [],
        risk_tolerance: Annotated[float, "Risk tolerance level (0-1)"] = 0.5,
        hedge_ratio: Annotated[float, "Target hedge ratio (0-1)"] = 0.8,
    ) -> dict:
        """
        Design comprehensive multi-asset hedging strategy for portfolio protection.
        Reads tickers from portfolio.json if weights not provided.
        Args:
            portfolio_weights (dict): Portfolio weights for each ticker (optional)
            hedge_types (list): Types of hedges to analyze (optional)
            risk_tolerance (float): Risk tolerance level (0-1)
            hedge_ratio (float): Target hedge ratio (0-1)
        Returns:
            dict: Comprehensive hedging strategy across multiple asset classes
        """
        
        try:
            # Read portfolio data to get tickers and weights if not provided
            portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
            
            try:
                with open(portfolio_path, 'r') as f:
                    portfolio_data = json.load(f)
            except FileNotFoundError:
                return {"error": "Portfolio file not found", "hedging_strategy": {}}
            
            # Extract tickers and weights
            if not portfolio_weights:
                portfolio_holdings = portfolio_data.get('portfolio', {})
                if not portfolio_holdings:
                    return {"error": "No holdings found in portfolio", "hedging_strategy": {}}
                
                # Calculate weights based on total amounts
                total_portfolio_value = sum(holding.get('totalAmount', 0) for holding in portfolio_holdings.values())
                portfolio_weights = {}
                
                for ticker, holding in portfolio_holdings.items():
                    weight = holding.get('totalAmount', 0) / total_portfolio_value if total_portfolio_value > 0 else 1/len(portfolio_holdings)
                    portfolio_weights[ticker] = weight
            
            tickers = list(portfolio_weights.keys())
            
            if not tickers:
                return {"error": "No tickers found for hedging analysis", "hedging_strategy": {}}
            
            # Default hedge types if not provided
            if not hedge_types:
                hedge_types = ["equity_index", "options", "crypto", "commodities", "forex", "volatility"]
            
            # Calculate portfolio value (assuming $1M for demonstration)
            portfolio_value = 1000000
            
            # Fetch current market data for analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # 3 months for correlation analysis
            
            returns_data = {}
            current_prices = {}
            volatilities = {}
            
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(start=start_date, end=end_date)
                    
                    if len(hist) > 1:
                        returns = hist['Close'].pct_change().dropna()
                        returns_data[ticker] = returns
                        current_prices[ticker] = hist['Close'].iloc[-1]
                        volatilities[ticker] = returns.std() * np.sqrt(252)  # Annualized
                except:
                    continue
            
            if not returns_data:
                return {"error": "Could not fetch data for hedging analysis", "hedging_strategy": {}}
            
            # Portfolio metrics
            portfolio_returns = np.zeros(len(next(iter(returns_data.values()))))
            for ticker, returns in returns_data.items():
                weight = portfolio_weights.get(ticker, 0)
                portfolio_returns += weight * returns.values
            
            portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)
            portfolio_var_95 = np.percentile(portfolio_returns, 5) * portfolio_value
            
            hedging_strategies = {}
            
            # 1. Equity Index Hedging
            if "equity_index" in hedge_types:
                # Calculate beta vs major indices for hedging
                indices = {"SPY": "S&P 500", "QQQ": "NASDAQ", "IWM": "Russell 2000", "EFA": "International"}
                index_hedges = {}
                
                for index_ticker, index_name in indices.items():
                    try:
                        index = yf.Ticker(index_ticker)
                        index_hist = index.history(start=start_date, end=end_date)
                        index_returns = index_hist['Close'].pct_change().dropna()
                        
                        # Calculate correlation and beta
                        if len(index_returns) > 20:
                            aligned_data = pd.DataFrame({
                                'portfolio': portfolio_returns[:len(index_returns)],
                                'index': index_returns
                            }).dropna()
                            
                            if len(aligned_data) > 10:
                                correlation = np.corrcoef(aligned_data['portfolio'], aligned_data['index'])[0, 1]
                                beta = np.cov(aligned_data['portfolio'], aligned_data['index'])[0, 1] / np.var(aligned_data['index'])
                                
                                hedge_notional = portfolio_value * hedge_ratio * abs(beta)
                                
                                index_hedges[index_ticker] = {
                                    "index_name": index_name,
                                    "correlation": round(correlation, 4),
                                    "beta": round(beta, 4),
                                    "hedge_notional": round(hedge_notional, 2),
                                    "hedge_direction": "Short" if beta > 0 else "Long",
                                    "effectiveness": "High" if abs(correlation) > 0.7 else "Medium" if abs(correlation) > 0.4 else "Low"
                                }
                    except:
                        continue
                
                hedging_strategies["equity_index_hedging"] = {
                    "strategy_type": "Index Futures/ETF Hedging",
                    "recommended_hedges": index_hedges,
                    "implementation": "Use futures contracts or inverse ETFs for cost-effective hedging",
                    "cost_estimate": "0.1-0.3% of notional per month"
                }
            
            # 2. Options Hedging Strategy
            if "options" in hedge_types:
                # Protective put strategy
                put_protection_levels = [0.9, 0.95, 1.0]  # % of current portfolio value
                options_strategies = {}
                
                for protection_level in put_protection_levels:
                    protection_value = portfolio_value * protection_level
                    estimated_premium = portfolio_value * 0.02 * protection_level  # Rough estimate
                    
                    options_strategies[f"{int(protection_level*100)}%_protection"] = {
                        "strategy": "Protective Put",
                        "protection_level": f"{protection_level:.0%}",
                        "notional_protected": round(protection_value, 2),
                        "estimated_premium": round(estimated_premium, 2),
                        "premium_percentage": round((estimated_premium / portfolio_value) * 100, 2),
                        "recommendation": "High" if risk_tolerance < 0.3 else "Medium" if risk_tolerance < 0.7 else "Low"
                    }
                
                # Collar strategy
                collar_strategy = {
                    "strategy": "Collar (Buy Put, Sell Call)",
                    "put_strike": "95% of portfolio value",
                    "call_strike": "105% of portfolio value",
                    "net_premium": "Near zero (premium neutral)",
                    "max_upside": "5% above current value",
                    "max_downside": "5% below current value"
                }
                
                hedging_strategies["options_hedging"] = {
                    "strategy_type": "Options Protection",
                    "protective_puts": options_strategies,
                    "collar_strategy": collar_strategy,
                    "implementation": "Use index options (SPX, QQQ) or individual stock options",
                    "timing_consideration": "Buy protection during low volatility periods"
                }
            
            # 3. Cryptocurrency Hedging
            if "crypto" in hedge_types:
                crypto_hedges = {
                    "BTC": {
                        "asset_name": "Bitcoin",
                        "hedge_rationale": "Inflation hedge and currency debasement protection",
                        "recommended_allocation": "2-5% of portfolio",
                        "correlation_with_stocks": "Medium (0.3-0.6)",
                        "volatility_profile": "Very High"
                    },
                    "ETH": {
                        "asset_name": "Ethereum",
                        "hedge_rationale": "Technology disruption and digital asset exposure",
                        "recommended_allocation": "1-3% of portfolio",
                        "correlation_with_stocks": "Medium-High (0.4-0.7)",
                        "volatility_profile": "Very High"
                    }
                }
                
                hedging_strategies["crypto_hedging"] = {
                    "strategy_type": "Cryptocurrency Diversification",
                    "crypto_allocations": crypto_hedges,
                    "implementation": "ETFs (BITO, ETHE) or direct holdings via exchanges",
                    "risk_warning": "High volatility - limit exposure to small percentage",
                    "regulatory_risk": "Monitor regulatory developments"
                }
            
            # 4. Commodities Hedging
            if "commodities" in hedge_types:
                commodity_hedges = {
                    "GLD": {
                        "commodity": "Gold",
                        "hedge_purpose": "Inflation and currency hedge",
                        "recommended_allocation": "5-10% of portfolio",
                        "implementation": "GLD ETF or futures"
                    },
                    "USO": {
                        "commodity": "Oil",
                        "hedge_purpose": "Energy inflation hedge",
                        "recommended_allocation": "2-5% of portfolio",
                        "implementation": "USO ETF or oil futures"
                    },
                    "DBA": {
                        "commodity": "Agricultural",
                        "hedge_purpose": "Food inflation hedge",
                        "recommended_allocation": "2-3% of portfolio",
                        "implementation": "DBA ETF or agricultural futures"
                    }
                }
                
                hedging_strategies["commodities_hedging"] = {
                    "strategy_type": "Commodity Inflation Protection",
                    "commodity_allocations": commodity_hedges,
                    "total_recommended_allocation": "9-18% of portfolio",
                    "rebalancing_frequency": "Quarterly"
                }
            
            # 5. Forex Hedging
            if "forex" in hedge_types:
                forex_hedges = {
                    "USD_strength": {
                        "scenario": "USD Strengthening",
                        "impact_on_portfolio": "Negative for international stocks",
                        "hedge": "Long USD index (DXY) or short foreign currency ETFs"
                    },
                    "USD_weakness": {
                        "scenario": "USD Weakening",
                        "impact_on_portfolio": "Positive for international stocks",
                        "hedge": "Foreign currency ETFs (FXE, FXY) or international bonds"
                    }
                }
                
                hedging_strategies["forex_hedging"] = {
                    "strategy_type": "Currency Risk Management",
                    "currency_scenarios": forex_hedges,
                    "implementation": "Currency ETFs or forex futures",
                    "monitoring": "Watch DXY and major currency pairs"
                }
            
            # 6. Volatility Hedging
            if "volatility" in hedge_types:
                vol_hedges = {
                    "VIX_protection": {
                        "instrument": "VIX ETFs (VXX, UVXY)",
                        "purpose": "Profit from volatility spikes",
                        "allocation": "1-2% of portfolio",
                        "timing": "Buy during low volatility periods"
                    },
                    "long_vol_strategies": {
                        "instrument": "Long volatility options strategies",
                        "purpose": "Tail risk protection",
                        "cost": "1-3% annually",
                        "effectiveness": "High during market crashes"
                    }
                }
                
                hedging_strategies["volatility_hedging"] = {
                    "strategy_type": "Volatility Protection",
                    "volatility_instruments": vol_hedges,
                    "current_vix_level": "Monitor VIX levels for entry timing",
                    "warning": "VIX products have contango decay - use sparingly"
                }
            
            # Calculate total hedging cost
            estimated_annual_cost = portfolio_value * 0.015  # Rough estimate: 1.5% annually
            
            # Risk-adjusted recommendations
            if risk_tolerance < 0.3:
                urgency = "High - Implement comprehensive hedging immediately"
                hedge_coverage = "80-100% of portfolio value"
            elif risk_tolerance < 0.7:
                urgency = "Medium - Gradual hedging implementation"
                hedge_coverage = "50-80% of portfolio value"
            else:
                urgency = "Low - Selective hedging for tail risks only"
                hedge_coverage = "20-50% of portfolio value"
            
            return {
                "portfolio_analysis": {
                    "portfolio_value": portfolio_value,
                    "portfolio_volatility": round(portfolio_volatility, 4),
                    "daily_var_95": round(abs(portfolio_var_95), 2),
                    "risk_tolerance": risk_tolerance,
                    "hedge_ratio_target": hedge_ratio
                },
                "hedging_strategies": hedging_strategies,
                "implementation_plan": {
                    "urgency": urgency,
                    "recommended_hedge_coverage": hedge_coverage,
                    "estimated_annual_cost": round(estimated_annual_cost, 2),
                    "cost_percentage": round((estimated_annual_cost / portfolio_value) * 100, 2),
                    "implementation_phases": [
                        "Phase 1: Implement core index hedging (1-2 weeks)",
                        "Phase 2: Add options protection (2-4 weeks)",
                        "Phase 3: Diversify with alternative assets (1-3 months)"
                    ]
                },
                "monitoring_metrics": {
                    "hedge_effectiveness": "Track correlation between hedges and portfolio",
                    "cost_monitoring": "Monitor premium decay and roll costs",
                    "rebalancing_triggers": "VIX > 25, portfolio drawdown > 10%",
                    "review_frequency": "Monthly hedge effectiveness review"
                },
                "risk_warnings": [
                    "Hedging reduces both downside and upside potential",
                    "Hedge ratios should be adjusted based on market conditions",
                    "Over-hedging can significantly impact returns",
                    "Regular monitoring and rebalancing required"
                ],
                "methodology": f"Multi-asset hedging analysis with {hedge_ratio:.0%} target hedge ratio"
            }
            
        except Exception as e:
            return {"error": f"Hedging strategy design failed: {str(e)}", "hedging_strategy": {}}

