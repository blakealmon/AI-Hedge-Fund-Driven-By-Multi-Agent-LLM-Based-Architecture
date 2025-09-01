# TradingAgents/graph/setup.py

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.utils.agent_utils import Toolkit

from .conditional_logic import ConditionalLogic


class GraphSetup:
    """Handles the setup and configuration of the agent graph."""

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        toolkit: Toolkit,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        risk_manager_memory,
        portfolio_optimizer_memory,
        conditional_logic: ConditionalLogic,
    ):
        """Initialize with required components."""
        self.quick_thinking_llm = quick_thinking_llm
        self.deep_thinking_llm = deep_thinking_llm
        self.toolkit = toolkit
        self.tool_nodes = tool_nodes
        self.bull_memory = bull_memory
        self.bear_memory = bear_memory
        self.trader_memory = trader_memory
        self.invest_judge_memory = invest_judge_memory
        self.risk_manager_memory = risk_manager_memory
        self.conditional_logic = conditional_logic
        self.portfolio_optimizer_memory = portfolio_optimizer_memory

    def setup_graph(
        self, selected_analysts=["market", "social", "news", "fundamentals", "macroeconomic"]
    ):
        """Set up and compile the agent workflow graph.

        Args:
            selected_analysts (list): List of analyst types to include. Options are:
                - "market": Market analyst
                - "social": Social media analyst
                - "news": News analyst
                - "fundamentals": Fundamentals analyst
        """
        if len(selected_analysts) == 0:
            raise ValueError("Trading Agents Graph Setup Error: no analysts selected!")

        # Helper to print progress for each node execution
        def wrap(node, label: str):
            def wrapped(state):
                try:
                    td = state.get("trade_date", "")
                except Exception:
                    td = ""
                print(f"[ {td} ] Running: {label}")
                return node(state)
            return wrapped

        # Create analyst nodes
        analyst_nodes = {}
        delete_nodes = {}
        tool_nodes = {}

        if "market" in selected_analysts:
            analyst_nodes["market"] = create_market_analyst(
                self.quick_thinking_llm, self.toolkit
            )
            delete_nodes["market"] = create_msg_delete()
            tool_nodes["market"] = self.tool_nodes["market"]

        if "macroeconomic" in selected_analysts:
            analyst_nodes["macroeconomic"] = create_macroeconomic_analyst(
                self.quick_thinking_llm, self.toolkit
            )
            delete_nodes["macroeconomic"] = create_msg_delete()
            tool_nodes["macroeconomic"] = self.tool_nodes["market"]  # Use same tools as market analyst

        if "social" in selected_analysts:
            analyst_nodes["social"] = create_social_media_analyst(
                self.quick_thinking_llm, self.toolkit
            )
            delete_nodes["social"] = create_msg_delete()
            tool_nodes["social"] = self.tool_nodes["social"]

        if "news" in selected_analysts:
            analyst_nodes["news"] = create_news_analyst(
                self.quick_thinking_llm, self.toolkit
            )
            delete_nodes["news"] = create_msg_delete()
            tool_nodes["news"] = self.tool_nodes["news"]

        if "fundamentals" in selected_analysts:
            analyst_nodes["fundamentals"] = create_fundamentals_analyst(
                self.quick_thinking_llm, self.toolkit
            )
            delete_nodes["fundamentals"] = create_msg_delete()
            tool_nodes["fundamentals"] = self.tool_nodes["fundamentals"]
        
        tool_nodes["riskJudge"] = self.tool_nodes["riskJudge"]
        delete_nodes["riskJudge"] = create_msg_delete()

        # Create researcher and manager nodes
        # Changed the models from quick thinking to deep thinking
        bull_researcher_node = create_bull_researcher(
            self.deep_thinking_llm, self.bull_memory
        )
        bear_researcher_node = create_bear_researcher(
            self.deep_thinking_llm, self.bear_memory
        )
        research_manager_node = create_research_manager(
            self.deep_thinking_llm, self.invest_judge_memory
        )
        
        # Cross Ex Nodes
        
        bull_researcher_ask_node = create_bull_researcher_ask(
            self.deep_thinking_llm, self.bull_memory
        )
        bull_researcher_ans_node = create_bull_researcher_ans(
            self.deep_thinking_llm, self.bull_memory
        )
        
        bear_researcher_ask_node = create_bear_researcher_ask(
            self.deep_thinking_llm, self.bear_memory
        )
        bear_researcher_ans_node = create_bear_researcher_ans(
            self.deep_thinking_llm, self.bear_memory
        )
        
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)

        # Create risk analysis nodes
        risky_analyst = create_risky_debator(self.quick_thinking_llm)

        risky_analyst_ask = create_risky_debator_ask(self.quick_thinking_llm)
        risky_analyst_ans = create_risky_debator_ans(self.quick_thinking_llm)
        
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        safe_analyst = create_safe_debator(self.quick_thinking_llm)
        
        safe_analyst_ask = create_safe_debator_ask(self.quick_thinking_llm)
        safe_analyst_ans = create_safe_debator_ans(self.quick_thinking_llm)

        risk_manager_node = create_risk_manager(
            self.deep_thinking_llm, self.risk_manager_memory, toolkit=self.toolkit
        )

        # Portfolio optimizer node (final decision maker)
        portfolio_optimizer_node = create_portfolio_optimizer(
            self.deep_thinking_llm, self.portfolio_optimizer_memory, self.toolkit
        )

        # Create workflow
        workflow = StateGraph(AgentState)

        # Add analyst nodes to the graph
        for analyst_type, node in analyst_nodes.items():
            workflow.add_node(f"{analyst_type.capitalize()} Analyst", wrap(node, f"{analyst_type.capitalize()} Analyst"))
            workflow.add_node(
                f"Msg Clear {analyst_type.capitalize()}", wrap(delete_nodes[analyst_type], f"Msg Clear {analyst_type.capitalize()}")
            )
            # ToolNode is not callable; add directly and log via conditional logic
            workflow.add_node(f"tools_{analyst_type}", tool_nodes[analyst_type])

        # Add other nodes
        workflow.add_node("Bull Researcher", wrap(bull_researcher_node, "Bull Researcher"))
        workflow.add_node("Bear Researcher", wrap(bear_researcher_node, "Bear Researcher"))
        workflow.add_node("Bull Researcher Ask", wrap(bull_researcher_ask_node, "Bull Researcher Ask"))
        workflow.add_node("Bull Researcher Ans", wrap(bull_researcher_ans_node, "Bull Researcher Ans"))
        workflow.add_node("Bear Researcher Ask", wrap(bear_researcher_ask_node, "Bear Researcher Ask"))
        workflow.add_node("Bear Researcher Ans", wrap(bear_researcher_ans_node, "Bear Researcher Ans"))
        workflow.add_node("Research Manager", wrap(research_manager_node, "Research Manager"))
        workflow.add_node("Trader", wrap(trader_node, "Trader"))
        workflow.add_node("Risky Analyst", wrap(risky_analyst, "Risky Analyst"))
        workflow.add_node("Risky Analyst Ask", wrap(risky_analyst_ask, "Risky Analyst Ask"))
        workflow.add_node("Risky Analyst Ans", wrap(risky_analyst_ans, "Risky Analyst Ans"))
        workflow.add_node("Neutral Analyst", wrap(neutral_analyst, "Neutral Analyst"))
        workflow.add_node("Safe Analyst", wrap(safe_analyst, "Safe Analyst"))
        workflow.add_node("Safe Analyst Ask", wrap(safe_analyst_ask, "Safe Analyst Ask"))
        workflow.add_node("Safe Analyst Ans", wrap(safe_analyst_ans, "Safe Analyst Ans"))
        workflow.add_node("Risk Judge", wrap(risk_manager_node, "Risk Judge"))
        # ToolNode is not callable; add directly and log via conditional logic
        workflow.add_node("tools_Risk Judge", tool_nodes["riskJudge"]) 
        workflow.add_node("Portfolio Optimizer", wrap(portfolio_optimizer_node, "Portfolio Optimizer"))

        # Define edges
        # Start with the first analyst
        first_analyst = selected_analysts[0]
        workflow.add_edge(START, f"{first_analyst.capitalize()} Analyst")

        # Connect analysts in sequence
        for i, analyst_type in enumerate(selected_analysts):
            current_analyst = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            # Add conditional edges for current analyst
            workflow.add_conditional_edges(
                current_analyst,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current_analyst)

            # Connect to next analyst or to Bull Researcher if this is the last analyst
            if i < len(selected_analysts) - 1:
                next_analyst = f"{selected_analysts[i+1].capitalize()} Analyst"
                workflow.add_edge(current_clear, next_analyst)
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # Add remaining edges
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher": "Bear Researcher",
                "Bull Researcher Ask": "Bull Researcher Ask",
                "Bear Researcher Ask": "Bear Researcher Ask",
                "Bull Researcher Ans": "Bull Researcher Ans",
                "Bear Researcher Ans": "Bear Researcher Ans",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher": "Bull Researcher",
                "Bull Researcher Ask": "Bull Researcher Ask",
                "Bear Researcher Ask": "Bear Researcher Ask",
                "Bull Researcher Ans": "Bull Researcher Ans",
                "Bear Researcher Ans": "Bear Researcher Ans",
                "Research Manager": "Research Manager",
            },
        )
        
        # Replace former Cross Examination conditional edges with Ask/Ans node edges
        workflow.add_conditional_edges(
            "Bull Researcher Ask",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher Ans": "Bull Researcher Ans",
                "Bear Researcher Ask": "Bear Researcher Ask",
                "Bear Researcher Ans": "Bear Researcher Ans",
                "Bull Researcher": "Bull Researcher",
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bull Researcher Ans",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher Ask": "Bear Researcher Ask",
                "Bear Researcher Ans": "Bear Researcher Ans",
                "Bull Researcher": "Bull Researcher",
                "Bear Researcher": "Bear Researcher",
                "Bull Researcher Ask": "Bull Researcher Ask",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher Ask",
            self.conditional_logic.should_continue_debate,
            {
                "Bear Researcher Ans": "Bear Researcher Ans",
                "Bull Researcher Ask": "Bull Researcher Ask",
                "Bull Researcher Ans": "Bull Researcher Ans",
                "Bull Researcher": "Bull Researcher",
                "Bear Researcher": "Bear Researcher",
                "Research Manager": "Research Manager",
            },
        )
        workflow.add_conditional_edges(
            "Bear Researcher Ans",
            self.conditional_logic.should_continue_debate,
            {
                "Bull Researcher Ask": "Bull Researcher Ask",
                "Bull Researcher Ans": "Bull Researcher Ans",
                "Bull Researcher": "Bull Researcher",
                "Bear Researcher": "Bear Researcher",
                "Bear Researcher Ask": "Bear Researcher Ask",
                "Research Manager": "Research Manager",
            },
        )
        
        workflow.add_edge("Research Manager", "Trader")
        
        workflow.add_edge("Trader", "Risky Analyst")
        workflow.add_conditional_edges(
            "Risky Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Safe Analyst": "Safe Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        workflow.add_conditional_edges(
            "Safe Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Neutral Analyst": "Neutral Analyst",
                "Risk Judge": "Risk Judge",
            },
        )
        
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {
                "Risky Analyst": "Risky Analyst",
                "Risk Judge": "Risk Judge",
            },
        )

        workflow.add_edge("Risk Judge", "Portfolio Optimizer")
        workflow.add_edge("Portfolio Optimizer", END)

        # Compile and return
        return workflow.compile()
