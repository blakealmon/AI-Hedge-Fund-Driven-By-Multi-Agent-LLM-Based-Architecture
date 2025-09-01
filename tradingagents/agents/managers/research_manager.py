import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.agents.utils.debate_utils import get_debate_round_info


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        print(f"[DEBUG] Research Manager executing...")
        ticker = state["company_of_interest"]
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "[]")
        bull_history = investment_debate_state.get("bull_history", "[]")
        bear_history = investment_debate_state.get("bear_history", "[]")
        
        print(f"[DEBUG] Research Manager: Count = {investment_debate_state.get('count', 0)}")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("RM_001", "ResearchManager")
        
        # Read recent analyst reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-4:]:  # Last 4 analyses
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
        
        json_format = """{
    "recommendation": "...", // Your final recommendation (Buy, Sell, or Hold)
    "investment_plan": "...", // Detailed investment plan for the trader
    "arguments": [{
        "title": "...", // Short title for the argument
        "analysis": "...", // Detailed analysis of a specific argument
    }, ...],
    "rationale": "...", // Overall explanation of your recommendation
    "confidence": "..." // Confidence level in your recommendation (1-100)
}"""

        prompt = f"""As the portfolio manager and debate facilitator, your role is to critically evaluate this round of debate and make a definitive decision: align with the bear analyst, the bull analyst, or choose Hold only if it is strongly justified based on the arguments presented.

Summarize the key points from both sides concisely, focusing on the most compelling evidence or reasoning. Your recommendation—Buy, Sell, or Hold—must be clear and actionable. Avoid defaulting to Hold simply because both sides have valid points; commit to a stance grounded in the debate's strongest arguments.

Additionally, develop a detailed investment plan for the trader. This should include:

Your Recommendation: A decisive stance supported by the most convincing arguments.
Rationale: An explanation of why these arguments lead to your conclusion.
Strategic Actions: Concrete steps for implementing the recommendation.
Take into account your past mistakes on similar situations. Use these insights to refine your decision-making and ensure you are learning and improving. Present your analysis conversationally, as if speaking naturally, without special formatting. 

Here are your past reflections on mistakes:
\"{past_memory_str}\"

Blackboard Context:{blackboard_context}

Here is the debate:
Debate History:
{history}

Respond ONLY with a valid JSON object in the following format:
{json_format}
"""
        response = llm.invoke(prompt)

        # Extract decision and confidence from response
        decision = "Hold"
        confidence = "Medium"
        response_text = response.content.upper()
        
        if "BUY" in response_text:
            decision = "Buy"
        elif "SELL" in response_text:
            decision = "Sell"
        
        if "HIGH" in response_text and "CONFIDENCE" in response_text:
            confidence = "High"
        elif "LOW" in response_text and "CONFIDENCE" in response_text:
            confidence = "Low"

        # Post investment decision to blackboard
        blackboard_agent.post_investment_decision(
            ticker=ticker,
            decision=decision,
            reasoning=response.content,
            confidence=confidence
        )

        # Post debate summary to blackboard
        debate_summary = f"Investment debate for {ticker} concluded with {decision} decision. {response.content[:200]}..."
        blackboard_agent.post_debate_summary(
            ticker=ticker,
            debate_type="Investment",
            summary=debate_summary,
            decision=decision,
            confidence=confidence
        )

        new_investment_debate_state = {
            "history": history,
            "bull_history": bull_history,
            "bear_history": bear_history,
            "current_response": response.content,
            "judge_decision": decision,
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response.content,
        }

    return research_manager_node
