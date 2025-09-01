from tradingagents.dataflows.stockstats_utils import StockstatsUtils


print(StockstatsUtils.get_stock_stats(
    symbol="AAPL",
    indicator="close",
    curr_date="2025-07-10",
    data_dir="data/market_data/price_data",
    online=False
))