from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import sys
from datetime import datetime, timedelta

config = DEFAULT_CONFIG.copy()

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def run_tradingagents_for_dates(ticker, start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    for single_date in daterange(start_date, end_date):
        date_str = single_date.strftime("%Y-%m-%d")
        print(f"Running TradingAgentsGraph for {ticker} on {date_str}")
        graph = TradingAgentsGraph(debug=True, config=config)
        final_state, final_decision = graph.propagate(ticker, date_str)
        print(f"Final decision for {ticker} on {date_str}: {final_decision}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python eval_range.py <TICKER> <START_DATE> <END_DATE>")
        print("Example: python eval_range.py AAPL 2025-07-01 2025-07-10")
        sys.exit(1)
    ticker = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    run_tradingagents_for_dates(ticker, start_date, end_date)