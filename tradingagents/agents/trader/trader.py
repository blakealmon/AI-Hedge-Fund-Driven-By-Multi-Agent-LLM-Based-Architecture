import functools
import time
import json
from datetime import datetime
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.agents.utils.agent_utils import Toolkit


def create_trader(llm, memory):

    def trader_node(state, name):
        ticker = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("TR_001", "Trader")
        
        # Get comprehensive trade context from all agents
        trade_context = blackboard_agent.get_comprehensive_trade_context(ticker)
        
        # Build context strings for the prompt
        analyst_context = ""
        if trade_context["analyst_reports"]:
            analyst_context += "\n\nAnalyst Reports on Blackboard:\n"
            for report in trade_context["analyst_reports"][-4:]:  # Last 4 reports
                content = report.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    analyst_context += f"- {report['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        risk_context = ""
        if trade_context["risk_assessments"]:
            risk_context += "\n\nRisk Assessments on Blackboard:\n"
            for assessment in trade_context["risk_assessments"][-3:]:  # Last 3 assessments
                content = assessment.get('content', {})
                risk_context += f"- {assessment['sender'].get('role', 'Unknown')}: Risk Level {content.get('risk_level', 'N/A')} - {content.get('recommendation', 'N/A')[:100]}...\n"

        manager_context = ""
        if trade_context["investment_decisions"]:
            manager_context += "\n\nManager Decisions on Blackboard:\n"
            for decision in trade_context["investment_decisions"][-2:]:  # Last 2 decisions
                content = decision.get('content', {})
                manager_context += f"- {decision['sender'].get('role', 'Unknown')}: {content.get('decision', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        research_context = ""
        if trade_context["research_debates"]:
            research_context += "\n\nResearch Debates on Blackboard:\n"
            for debate in trade_context["research_debates"][-3:]:  # Last 3 debate comments
                content = debate.get('content', {})
                research_context += f"- {debate['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:80]}...\n"

        risk_debate_context = ""
        if trade_context["risk_debates"]:
            risk_debate_context += "\n\nRisk Debates on Blackboard:\n"
            for debate in trade_context["risk_debates"][-3:]:  # Last 3 risk debate comments
                content = debate.get('content', {})
                risk_debate_context += f"- {debate['sender'].get('role', 'Unknown')}: {content.get('stance', 'N/A')} - {content.get('argument', 'N/A')[:80]}...\n"

        portfolio_context = ""
        if trade_context["portfolio_updates"]:
            portfolio_context += "\n\nCurrent Portfolio Status:\n"
            for update in trade_context["portfolio_updates"][-1:]:  # Latest portfolio update
                content = update.get('content', {})
                portfolio_context += f"- Position: {content.get('position_type', 'N/A')} ({content.get('position_size', 'N/A')} shares)\n"
                portfolio_context += f"- Value: ${content.get('current_value', 'N/A'):,.2f}\n"
                portfolio_context += f"- P&L: ${content.get('unrealized_pnl', 'N/A'):,.2f}\n"

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {ticker}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }
        
        json_format = """{  
  "content": "...",
    "recommendation": "...",
    "confidence": "...",
    "reasoning": "...",
    "suffix": "FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**"
}"""

        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold. End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}

Blackboard Context:{analyst_context}
{risk_context}
{manager_context}
{research_context}
{risk_debate_context}
{portfolio_context}

Consider all the insights from analysts, risk managers, research managers, and current portfolio status when making your decision. Provide a comprehensive analysis that incorporates all available perspectives.""",
            },
            context,
        ]

        result = llm.invoke(messages)

        # Extract trade decision from response
        response_text = result.content.upper()
        trade_action = "HOLD"
        if "FINAL TRANSACTION PROPOSAL: **BUY**" in response_text:
            trade_action = "BUY"
        elif "FINAL TRANSACTION PROPOSAL: **SELL**" in response_text:
            trade_action = "SELL"

        # Extract confidence from response
        confidence = "Medium"
        if "HIGH" in response_text and "CONFIDENCE" in response_text:
            confidence = "High"
        elif "LOW" in response_text and "CONFIDENCE" in response_text:
            confidence = "Low"

        # Post trade decision to blackboard
        blackboard_agent.post_trade_decision(
            ticker=ticker,
            action=trade_action,
            confidence=confidence,
            reasoning=f"Trade decision for {ticker} based on comprehensive multi-agent analysis."
        )

        # Execution must be performed by the LLM via the provided tools.
        # Capture any tool responses returned in the LLM response object if present.
        exec_result = getattr(result, 'tool_responses', None) or getattr(result, 'tools_called', None) or result.content
        print(f"Trade execution result (from LLM/tools): {exec_result}")

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
