import time
from datetime import datetime
from tradingagents.blackboard.utils import create_agent_blackboard

def create_options_trading_agent(llm, memory, toolkit):
    def options_trading_node(state) -> dict:
        company_name = state["company_of_interest"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=3)

        past_memory_str = "\n\n".join([rec["recommendation"] for rec in past_memories])

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("OP_001", "OptionsTradingAgent")
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=company_name)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Options Analyses on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        json_format = """{
    "strategy_name": "...", // e.g. 'Protective Put', 'Covered Call', 'Iron Condor'
    "trade_direction": "...", // 'Bullish', 'Bearish', 'Neutral', 'Volatility'
    "option_legs": [{
        "type": "...", // 'Call' or 'Put'
        "action": "...", // 'Buy' or 'Sell'
        "strike": "...", // strike price
        "expiry": "...", // expiry date
        "contracts": "...", // number of contracts
        "premium": "...", // premium per contract
        "greeks": { "delta": "...", "gamma": "...", "theta": "...", "vega": "..." }
    }],
    "rationale": "...", // why this trade is recommended
    "risk_management": "...", // stop loss, adjustment rules
    "confidence": "..." // 1-100
}"""

        prompt = f"""As the Senior Options Strategist, design an institutional-grade options trading plan for {company_name}.

**REQUIREMENTS:**
1. Base your decision on market conditions, sentiment, news, and fundamentals.
2. Recommend an options structure (single leg, spread, condor, straddle, etc.) optimized for current volatility and directional bias.
3. Include detailed strikes, expiries, and rationale.
4. Include Greek exposures and risk management rules.
5. Consider both hedging and alpha generation opportunities.

**Context:**
- Market Intelligence: {market_research_report}
- Sentiment Analysis: {sentiment_report}
- News Report: {news_report}
- Fundamentals: {fundamentals_report}
- Past Strategy Lessons: {past_memory_str}
- Blackboard Context: {blackboard_context}

Respond ONLY with valid JSON in this format:
{json_format}
"""

        response = llm.invoke(prompt)

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"options_strategy_{company_name}_{timestamp}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.content)
            print(f" Options strategy saved: {filename}")
        except Exception as e:
            print(f" Error saving options strategy: {e}")

        # Post to blackboard
        blackboard_agent.post_investment_decision(
            ticker=company_name,
            decision="Options Strategy",
            reasoning=response.content,
            confidence="N/A"
        )

        # Save to memory
        memory.add_situations([(curr_situation, f"Options strategy for {company_name}: {response.content[:300]}...")])

        return {
            "options_trading_state": {
                "analysis": response.content,
                "company": company_name,
                "report_file": filename,
                "timestamp": timestamp,
                "options_strategy_completed": True
            }
        }

    return options_trading_node
