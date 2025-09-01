# TradingAgents/graph/conditional_logic.py

from tradingagents.agents.utils.agent_states import AgentState


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(self, max_debate_rounds=1, max_risk_discuss_rounds=1):
        """Initialize with configuration parameters."""
        self.max_debate_rounds = max_debate_rounds
        self.max_risk_discuss_rounds = max_risk_discuss_rounds

    def should_continue_market(self, state: AgentState):
        """Determine if market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        # Avoid repeated tool loops during testing/one-shot runs
        if state.get("market_tools_used"):
            return "Msg Clear Market"
        if last_message.tool_calls:
            print(f"[ {state.get('trade_date','')} ] Routing: tools_market")
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_quant_market(self, state: AgentState):
        """Determine if quant market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_quant_market"
        return "Msg Clear Quant_market"

    def should_continue_macroeconomic(self, state: AgentState):
        """Determine if macroeconomic analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if state.get("macroeconomic_tools_used"):
            return "Msg Clear Macroeconomic"
        if last_message.tool_calls:
            return "tools_macroeconomic"
        return "Msg Clear Macroeconomic"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if state.get("social_tools_used"):
            return "Msg Clear Social"
        if last_message.tool_calls:
            print(f"[ {state.get('trade_date','')} ] Routing: tools_social")
            return "tools_social"
        return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if state.get("news_tools_used"):
            return "Msg Clear News"
        if last_message.tool_calls:
            print(f"[ {state.get('trade_date','')} ] Routing: tools_news")
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if state.get("fundamentals_tools_used"):
            return "Msg Clear Fundamentals"
        if last_message.tool_calls:
            print(f"[ {state.get('trade_date','')} ] Routing: tools_fundamentals")
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"
    
    def should_continue_macroeconomic(self, state: AgentState):
        """Determine if macroeconomic analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_macroeconomic"
        return "Msg Clear Macroeconomic"
    
    def should_continue_risk_judgment(self, state: AgentState):
        """Determine if risk judgment should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if state.get("riskjudge_tools_used"):
            return "Msg Clear Risk Judge"
        if last_message.tool_calls:
            print(f"[ {state.get('trade_date','')} ] Routing: tools_Risk Judge")
            return "tools_Risk Judge"
        return "Msg Clear Risk Judge"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue."""
        # 1 => Bull Researcher
        # 2 => Bear Researcher
        # 3 => Bull Researcher Ask
        # 4 => Bear Researcher Ans
        # 5 => Bear Researcher Ask
        # 6 => Bull Researcher Ans
        # 7 => Bull Researcher
        # 8 => Bear Researcher
        # 9 => Research Manager
        # Repeat 3 to 9 as needed

        count = state["investment_debate_state"]["count"]

        # 1 => Bullish Researcher
        # 2 => Bearish Researcher
        # 3 => Bullish Researcher Ask
        # 4 => Bullish Researcher Ans
        # 5 => Bearish Researcher Ask
        # 6 => Bullish Researcher Ans
        # 7 => Bullish Researcher
        # 8 => Bearish Researcher
        # 9 => Research Manager
        # Repeat 3 to 9 as needed

        if count == 0:
            return "Bull Researcher"
        elif count == 1:
            return "Bear Researcher"
        elif count == 2:
            return "Bull Researcher Ask"
        elif count == 3:
            return "Bull Researcher Ans"
        elif count == 4:
            return "Bear Researcher Ask"
        elif count == 5:
            return "Bull Researcher Ans"
        elif count == 6:
            return "Bull Researcher"
        elif count == 7:
            return "Bear Researcher"
        elif count == 8:
            return "Research Manager"
        else:
            # For counts >= 9, repeat 3-9 as needed
            repeat_sequence = [
                "Bull Researcher Ask",
                "Bull Researcher Ans",
                "Bear Researcher Ask",
                "Bull Researcher Ans",
                "Bull Researcher",
                "Bear Researcher",
                "Research Manager",
            ]
            idx = (count - 2) % len(repeat_sequence)
            return repeat_sequence[idx]

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        print(f"[DEBUG] should_continue_risk_analysis: count={state['risk_debate_state']['count']}, max_risk_discuss_rounds={self.max_risk_discuss_rounds}")
        # Check if we've reached the maximum number of rounds
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            print("[DEBUG] Risk debate complete. Handing off to Risk Judge.")
            return "Risk Judge"
        
        
        # 1 => Risky Analyst
        # 2 => Safe Analyst
        # 3 => Neutral Analyst
        # 4 => Risky Analyst Ask
        # 5 => Risky Analyst Ans
        # 6 => Safe Analyst Ask
        # 7 => Risky Analyst Ans
        # 8 => Risky Analyst
        # 9 => Safe Analyst
        # Repeat 4 to 9 as needed
        
        count = state["risk_debate_state"]["count"]

        # 1 => Risky Analyst
        # 2 => Safe Analyst
        # 3 => Neutral Analyst
        # 4 => Risky Analyst Ask
        # 5 => Risky Analyst Ans
        # 6 => Safe Analyst Ask
        # 7 => Risky Analyst Ans
        # 8 => Risky Analyst
        # 9 => Safe Analyst
        # Repeat 4 to 9 as needed

        if count == 0:
            print("[DEBUG] Next: Risky Analyst")
            return "Risky Analyst"
        elif count == 1:
            print("[DEBUG] Next: Safe Analyst")
            return "Safe Analyst"
        elif count == 2:
            print("[DEBUG] Next: Neutral Analyst")
            return "Neutral Analyst"
        elif count == 3:
            print("[DEBUG] Next: Risky Analyst Ask")
            return "Risky Analyst Ask"
        elif count == 4:
            print("[DEBUG] Next: Risky Analyst Ans")
            return "Risky Analyst Ans"
        elif count == 5:
            print("[DEBUG] Next: Safe Analyst Ask")
            return "Safe Analyst Ask"
        elif count == 6:
            print("[DEBUG] Next: Risky Analyst Ans")
            return "Risky Analyst Ans"
        elif count == 7:
            print("[DEBUG] Next: Risky Analyst")
            return "Risky Analyst"
        elif count == 8:
            print("[DEBUG] Next: Safe Analyst")
            return "Safe Analyst"
        else:
            # For counts >= 9, repeat sequence 4-9 pattern (mapped via repeat_sequence) dynamically
            repeat_sequence = [
                "Risky Analyst Ask",  # analogous to original position 4
                "Risky Analyst Ans",  # 5
                "Safe Analyst Ask",   # 6
                "Risky Analyst Ans",  # 7
                "Risky Analyst",      # 8
                "Safe Analyst",       # 9
            ]
            idx = (count - 3) % len(repeat_sequence)
            next_role = repeat_sequence[idx]
            print(f"[DEBUG] Next (loop): {next_role}")
            return next_role

    def should_continue_portfolio_flow(self, state: AgentState) -> str:
        """Determine if portfolio optimization flow should continue."""
        # Check if portfolio optimization has been completed
        if "portfolio_optimization_state" not in state or not state["portfolio_optimization_state"]:
            # First go to Quant Options Manager in the enterprise flow
            return "Quant Options Manager"
        else:
            return "END"