from langchain_core.messages import AIMessage
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_safe_debator(llm):
    def safe_node(state) -> dict:
        ticker = state.get("company_of_interest", "UNKNOWN")
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "[]")
        safe_history = risk_debate_state.get("safe_history", "[]")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        trader_decision = state["trader_investment_plan"]
        
        json_format = """{  
  "content": "...", // Overall writeup of the response
  "arguments": [{
      "title": "...", // Short title for the argument
      "content": "...", // Detailed content of the argument
      "source": "...", // Source of the information (e.g., "Market Research Report")
      "confidence": "..." // Confidence level in the argument (1-100)
  }, ...],
  "counterpoints": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "...",
      "target": "..." // The agent you are responding to, e.g. "Conservative", "Neutral"
    }, ...]
}"""

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("CRD_001", "ConservativeRiskManager")
        
        # Read trader decisions from blackboard
        trader_decisions = blackboard_agent.get_investment_decisions(ticker=ticker)
        trader_context = ""
        if trader_decisions:
            trader_context += "\n\nRecent Trader Decisions on Blackboard:\n"
            for decision in trader_decisions[-2:]:  # Last 2 decisions
                content = decision.get('content', {})
                trader_context += f"- Trader Decision: {content.get('decision', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        # Read analyst reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        analyst_context = ""
        if recent_analyses:
            analyst_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:  # Last 3 analyses
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    analyst_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        # Read recent risk debate comments
        risk_debate_round = risk_debate_state["count"] + 1
        recent_risk_debate = blackboard_agent.get_risk_debate_comments(topic=f"{ticker} Risk Debate")
        risk_debate_context = ""
        if recent_risk_debate:
            risk_debate_context += f"\n\nRISK DEBATE ROUND {risk_debate_round} - Previous Risk Debate Context:\n"
            for comment in recent_risk_debate[-6:]:  # Last 6 comments for context (3 agents x 2 rounds)
                content = comment.get('content', {})
                risk_debate_context += f"- {comment['sender'].get('role', 'Unknown')}: {content.get('stance', 'N/A')} - {content.get('argument', 'N/A')[:200]}...\n"

        prompt = f"""As the Conservative Risk Manager, your role is to advocate for cautious, risk-averse investment strategies. You should focus on capital preservation, risk mitigation, and stable, predictable returns while highlighting the dangers of aggressive approaches.

RISK DEBATE ROUND {risk_debate_round}: This is round {risk_debate_round} of the risk debate. If this is round 1, provide your initial conservative risk position. If this is a later round, build upon your previous arguments and directly address the aggressive and neutral analysts' counter-arguments from the previous round.

{trader_context}
{analyst_context}
{risk_debate_context}

Here is the trader's decision:
{trader_decision}

Current Market Situation:
Market Research: {market_research_report}
Social Media Sentiment: {sentiment_report}
News Analysis: {news_report}
Fundamentals: {fundamentals_report}

Your task is to:
1. Analyze the trader's decision and market conditions
2. Build a compelling case for conservative risk management
3. Address arguments raised by aggressive and neutral analysts in previous rounds
4. Provide specific evidence and reasoning for cautious approaches
5. Consider the debate context and previous arguments
6. Maintain a cautious and protective tone

Focus on:
- Risk identification and assessment
- Capital preservation strategies
- Diversification and hedging approaches
- Counter-arguments to aggressive positions
- Evidence supporting conservative stances

Respond in the following JSON format:
{json_format}"""

        response = llm.invoke(prompt)
        
        # Extract confidence from response
        confidence = "Medium"
        response_text = response.content.upper()
        if "HIGH" in response_text and "CONFIDENCE" in response_text:
            confidence = "High"
        elif "LOW" in response_text and "CONFIDENCE" in response_text:
            confidence = "Low"

        # Extract risk level from response
        risk_level = "Low"
        if "HIGH" in response_text and "RISK" in response_text:
            risk_level = "High"
        elif "MEDIUM" in response_text and "RISK" in response_text:
            risk_level = "Medium"

        # Determine reply_to for threading
        reply_to = None
        if recent_risk_debate:
            # Reply to the last aggressive or neutral comment if it exists
            other_comments = [c for c in recent_risk_debate if c.get('content', {}).get('stance') in ['Aggressive', 'Neutral']]
            if other_comments:
                reply_to = other_comments[-1].get('message_id')

        # Post risk debate comment to blackboard
        blackboard_agent.post_risk_debate_comment(
            topic=f"{ticker} Risk Debate",
            stance="Conservative",
            argument=response.content,
            confidence=confidence,
            reply_to=reply_to
        )

        # Post risk position to blackboard
        blackboard_agent.post_risk_position(
            ticker=ticker,
            stance="Conservative",
            confidence=confidence,
            reasoning=f"Conservative risk stance for {ticker} based on asset protection and stability.",
            risk_level=risk_level
        )

        # Post risk recommendation to blackboard
        actions = [
            "Reduce position size for risk mitigation",
            "Focus on defensive strategies",
            "Implement stop-loss orders",
            "Maintain conservative stance for stability"
        ]
        blackboard_agent.post_risk_recommendation(
            ticker=ticker,
            stance="Conservative",
            actions=actions,
            rationale=f"Conservative recommendations for {ticker} to protect assets and minimize volatility.",
            priority="Medium"
        )

        argument = f"Safe Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
