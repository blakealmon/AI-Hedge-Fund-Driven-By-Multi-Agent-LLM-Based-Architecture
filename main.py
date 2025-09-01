from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
import os
import dotenv

# Load environment variables from a .env file
dotenv.load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["max_debate_rounds"] = 1  # Increase debate rounds
config["online_tools"] = False
config["abmrOffline"] = True
config["deep_think_llm"] = "gpt-4.1-nano"
config["quick_think_llm"] = "gpt-4o-mini" 

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("AAPL", "2025-07-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
