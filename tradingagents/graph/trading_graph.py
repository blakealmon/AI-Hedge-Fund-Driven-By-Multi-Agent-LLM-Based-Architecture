# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date, datetime
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.interface import set_config

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor

# Import blackboard utilities
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.blackboard.storage import clear_blackboard


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework with blackboard integration."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config: Dict[str, Any] = None, # type: ignore
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        self.toolkit = Toolkit(config=self.config)

        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)
        self.portfolio_optimizer_memory = FinancialSituationMemory("portfolio_optimizer_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config.get("max_debate_rounds", 1),
            max_risk_discuss_rounds=self.config.get("max_risk_discuss_rounds", 1)
        )
        print(f"[DEBUG] TradingAgentsGraph: max_debate_rounds={self.config.get('max_debate_rounds')}, max_risk_discuss_rounds={self.config.get('max_risk_discuss_rounds')}")
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm, # type: ignore
            self.deep_thinking_llm, # type: ignore
            self.toolkit,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.portfolio_optimizer_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm) # type: ignore
        self.signal_processor = SignalProcessor(self.quick_thinking_llm) # type: ignore

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)
        
        # Initialize blackboard for the trading session
        self._initialize_blackboard()

    def _initialize_blackboard(self):
        """Initialize the blackboard system for this trading session."""
        if self.debug:
            print("🔄 Initializing blackboard system...")
        
        # Clear any existing messages for a fresh start
        clear_blackboard()
        
        # Create blackboard agents for all agent types
        self.blackboard_agents = {
            "analysts": {
                "market": create_agent_blackboard("MA_001", "MarketAnalyst"),
                "social": create_agent_blackboard("SMA_001", "SocialMediaAnalyst"),
                "news": create_agent_blackboard("NA_001", "NewsAnalyst"),
                "fundamentals": create_agent_blackboard("FA_001", "FundamentalAnalyst"),
            },
            "managers": {
                "research": create_agent_blackboard("RM_001", "ResearchManager"),
                "risk": create_agent_blackboard("RKM_001", "RiskManager"),
            },
            "researchers": {
                "bull": create_agent_blackboard("BR_001", "BullResearcher"),
                "bear": create_agent_blackboard("BER_001", "BearResearcher"),
            },
            "risk_managers": {
                "aggressive": create_agent_blackboard("ARD_001", "AggressiveRiskManager"),
                "conservative": create_agent_blackboard("CRD_001", "ConservativeRiskManager"),
                "neutral": create_agent_blackboard("NRD_001", "NeutralRiskManager"),
            },
            "trader": create_agent_blackboard("TR_001", "Trader"),
        }
        
        if self.debug:
            print("✅ Blackboard system initialized")

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources."""
        return {
            "market": ToolNode(
                [
                    # online tools
                    self.toolkit.get_YFin_data_online,
                    self.toolkit.get_stockstats_indicators_report_online,
                    # offline tools
                    self.toolkit.get_YFin_data,
                    self.toolkit.get_stockstats_indicators_report,
                ]
            ),
            "social": ToolNode(
                [
                    # online tools
                    self.toolkit.get_stock_news_openai,
                    # offline tools
                    self.toolkit.get_reddit_stock_info,
                ]
            ),
            "news": ToolNode(
                [
                    # online tools
                    self.toolkit.get_global_news_openai,
                    self.toolkit.get_google_news,
                    # offline tools
                    self.toolkit.get_finnhub_news,
                    self.toolkit.get_reddit_news,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # online tools
                    self.toolkit.get_fundamentals_openai,
                    # offline tools
                    self.toolkit.get_finnhub_company_insider_sentiment,
                    self.toolkit.get_finnhub_company_insider_transactions,
                    self.toolkit.get_simfin_balance_sheet,
                    self.toolkit.get_simfin_cashflow,
                    self.toolkit.get_simfin_income_stmt,
                ]
            ),
            # Trader-specific tools (execution and portfolio helpers)
            "riskJudge": ToolNode(
                [
                    # Execution tools
                    self.toolkit.buy,
                    self.toolkit.hold,
                    self.toolkit.sell,
                    self.toolkit.get_portfolio,
                    self.toolkit.get_price,
                ]
            ),
        }

    def propagate(self, ticker: str, date: str) -> Tuple[Dict[str, Any], str]:
        """
        Propagate through the trading agents graph with blackboard integration.
        
        Args:
            ticker: Stock ticker symbol
            date: Analysis date
            
        Returns:
            Tuple of (final_state, final_decision)
        """
        if self.debug:
            print(f"🚀 Starting propagation for {ticker} on {date}")
            print(f"📊 Using blackboard system for multi-agent coordination")
        
        # Store ticker for blackboard context
        self.ticker = ticker
        
        # Initialize state
        init_agent_state = self.propagator.create_initial_state(ticker, date)
        args = self.propagator.get_graph_args()
        
        # Stream the analysis with blackboard integration
        trace = []
        for chunk in self.graph.stream(init_agent_state, **args):
            if len(chunk["messages"]) > 0:
                # Process messages and update blackboard as needed
                self._process_chunk_for_blackboard(chunk, ticker)
                if self.debug:
                    chunk["messages"][-1].pretty_print()
            
            trace.append(chunk)
        
        # Get final state and decision
        final_state = trace[-1] if trace else init_agent_state
        final_decision = self._extract_final_decision(final_state)
        
        if self.debug:
            print(f"✅ Propagation completed for {ticker}")
            print(f"📋 Final decision: {final_decision}")
        
        return final_state, final_decision

    def _process_chunk_for_blackboard(self, chunk: Dict[str, Any], ticker: str):
        """Process a chunk of the graph execution and update blackboard accordingly."""
        # This method would process the chunk and ensure relevant information
        # is posted to the blackboard for other agents to access
        # Implementation depends on your specific chunk structure
        
        # Example: If chunk contains analyst reports, post them to blackboard
        if "market_report" in chunk and chunk["market_report"]:
            self.blackboard_agents["analysts"]["market"].post_analysis_report(
                ticker=ticker,
                analysis={"report": chunk["market_report"]},
                confidence="Medium"
            )
        
        # Add more chunk processing logic as needed

    def _extract_final_decision(self, final_state: Dict[str, Any]) -> str:
        """Extract the final trading decision from the state.

        Policy: decisions come from the analysis pipeline (trader/risk), not the MVO-BLM executor.
        The portfolio optimizer may execute sizing but should not override the decision verb (BUY/SELL/HOLD).
        """
        # Prefer explicit pipeline decision fields
        decision = final_state.get("final_trade_decision")
        if decision:
            return str(decision)
        # Fallback to trader plan text if present
        plan = final_state.get("trader_investment_plan")
        if plan:
            return str(plan)
        # Last resort: if nothing else exists, look at optimizer execution action
        try:
            po_state = final_state.get("portfolio_optimization_state")
            if isinstance(po_state, dict):
                exec_info = po_state.get("execution") or {}
                action = exec_info.get("action")
                if action:
                    return str(action)
        except Exception:
            pass
        return "No decision made"

    def get_blackboard_context(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive blackboard context for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary containing all relevant context from the blackboard
        """
        return self.blackboard_agents["trader"].get_comprehensive_trade_context(ticker)

    def get_blackboard_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the blackboard usage.
        
        Returns:
            Dictionary with blackboard statistics
        """
        from tradingagents.blackboard.storage import get_blackboard_stats
        return get_blackboard_stats()

    def clear_blackboard(self):
        """Clear the blackboard for a fresh start."""
        clear_blackboard()
        if self.debug:
            print("🧹 Blackboard cleared")

    def process_signal(self, full_signal: str) -> str:
        """
        Process a full trading signal to extract the core decision.
        
        Args:
            full_signal: Complete trading signal text
            
        Returns:
            Extracted decision (BUY, SELL, or HOLD)
        """
        return self.signal_processor.process_signal(full_signal)

    def export_blackboard_data(self, filename: str = None):
        """
        Export blackboard data to a file.
        
        Args:
            filename: Optional filename for export
        """
        if filename is None:
            filename = f"blackboard_export_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        from tradingagents.blackboard.storage import read_messages
        import json
        
        messages = read_messages()
        with open(filename, 'w') as f:
            json.dump(messages, f, indent=2)
        
        if self.debug:
            print(f"📤 Blackboard data exported to {filename}")
