from langchain_core.messages import AIMessage
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        ticker = state["company_of_interest"]
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("BR_001", "BullResearcher")
        
        # Read recent analyst reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:  # Last 3 analyses
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"

        # Read full debate context for multi-round debates
        debate_round = investment_debate_state["count"] + 1
        recent_debate = blackboard_agent.get_debate_comments(topic=f"{ticker} Investment Debate")
        debate_context = ""
        if recent_debate:
            debate_context += f"\n\nDEBATE ROUND {debate_round} - Previous Debate Context:\n"
            for comment in recent_debate[-6:]:  # Last 6 comments for context (3 agents x 2 rounds)
                content = comment.get('content', {})
                debate_context += f"- {comment['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:200]}...\n"

        # Read research arguments for context
        research_args = blackboard_agent.get_research_arguments(ticker=ticker)
        research_context = ""
        if research_args:
            research_context += f"\n\nPrevious Research Arguments:\n"
            for arg in research_args[-2:]:  # Last 2 arguments
                content = arg.get('content', {})
                research_context += f"- {arg['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:150]}...\n"

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        json_format = """{
  "arguments": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "..."
  }],
  "risks": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "..."
  }, ...],
  "counterpoints": [{
      "title": "...",
      "content": "...",
      "source": "...",
      "confidence": "..."
    }, ]
}"""

        prompt = f"""As the Bullish Research Analyst, your role is to build a compelling case for why the company represents a strong investment opportunity. You should focus on growth potential, market opportunities, competitive advantages, and positive catalysts.

DEBATE ROUND {debate_round}: This is round {debate_round} of the investment debate. If this is round 1, provide your initial bullish position. If this is a later round, build upon your previous arguments and directly address the bearish analyst's counter-arguments from the previous round.

{blackboard_context}
{debate_context}

Current Market Situation:
Market Research: {market_research_report}
Social Media Sentiment: {sentiment_report}
News Analysis: {news_report}
Fundamentals: {fundamentals_report}

Your task is to:
1. Analyze the market conditions and company fundamentals
2. Build a compelling bullish case with specific evidence
3. Address potential bearish concerns proactively
4. Provide concrete examples and data points
5. Consider the debate context and previous arguments
6. Maintain a confident but data-driven tone

Focus on:
- Growth potential and market opportunities
- Competitive advantages and innovation
- Positive market indicators and trends
- Counter-arguments to bearish concerns
- Evidence from provided data and research

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

        # Extract evidence sources from response
        evidence_sources = []
        if "FUNDAMENTAL" in response_text:
            evidence_sources.append("Fundamental Analysis")
        if "TECHNICAL" in response_text:
            evidence_sources.append("Technical Analysis")
        if "NEWS" in response_text:
            evidence_sources.append("News Analysis")
        if "SENTIMENT" in response_text:
            evidence_sources.append("Sentiment Analysis")
        if not evidence_sources:
            evidence_sources = ["Market Analysis"]

        # Determine reply_to for threading
        reply_to = None
        if recent_debate:
            # Reply to the last bear comment if it exists
            bear_comments = [c for c in recent_debate if c.get('content', {}).get('position') == 'Bearish']
            if bear_comments:
                reply_to = bear_comments[-1].get('message_id')

        # Post debate comment to blackboard
        blackboard_agent.post_debate_comment(
            topic=f"{ticker} Investment Debate",
            position="Bullish",
            argument=response.content,
            reply_to=reply_to
        )

        # Post research argument to blackboard
        blackboard_agent.post_research_argument(
            ticker=ticker,
            position="Bullish",
            argument=response.content,
            confidence=confidence,
            evidence_sources=evidence_sources,
            reply_to=reply_to
        )

        # Post research summary
        key_points = [
            "Growth potential and market opportunities",
            "Competitive advantages and positioning",
            "Positive financial indicators",
            "Counter-arguments to bearish concerns"
        ]
        blackboard_agent.post_research_summary(
            ticker=ticker,
            position="Bullish",
            key_points=key_points,
            conclusion=f"Bullish case for {ticker} based on growth potential and positive indicators.",
            confidence=confidence
        )

        argument = f"Bull Analyst: {response.content}"

        # Get current debate round information
        round_info = get_debate_round_info(state)
        current_round = round_info["round"]
        current_step = round_info["step_name"]
        
        # Parse history fields as JSON arrays
        try:
            history_list = json.loads(history) if history else []
        except Exception:
            history_list = []
        
        try:
            bull_history_list = json.loads(bull_history) if bull_history else []
        except Exception:
            bull_history_list = []
        
        # Append new argument
        history_list.append(argument)
        bull_history_list.append(argument)

        new_investment_debate_state = {
            "history": json.dumps(history_list),
            "bull_history": json.dumps(bull_history_list),
            "bear_history": investment_debate_state.get("bear_history", "[]"),
            "current_response": argument,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"],  # Keep current count
        }

        # Increment the count for the next step
        updated_state = {"investment_debate_state": new_investment_debate_state}
        updated_state = increment_debate_count(updated_state)
        
        # Return the complete state update
        return updated_state

    return bull_node
