from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard


def create_macroeconomic_analyst(llm, toolkit):

    def macroeconomic_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("MEA_001", "MacroeconomicAnalyst")
        # Read recent macroeconomic analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Macroeconomic Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        if toolkit.config["online_tools"]:
            tools = [
                toolkit.get_YFin_data_online,
                toolkit.get_stockstats_indicators_report_online,
            ]
        else:
            tools = [
                toolkit.get_YFin_data,
                toolkit.get_stockstats_indicators_report,
            ]

        system_message = (
            """You are a Macroeconomic Analyst specializing in analyzing how economic factors, monetary policy, and global economic conditions impact financial markets and individual securities. Your role is to provide comprehensive macroeconomic analysis that helps traders understand the broader economic context affecting their trading decisions.

## Your Analysis Focus Areas:

### 1. Economic Indicators & Data
- **GDP Growth (Gt)**: Economic expansion/contraction trends and their impact on market sentiment
- **Inflation Rate (It)**: CPI, PPI, PCE inflation rates and trends affecting bond yields and equity valuations
- **Unemployment Rate (Ut)**: Employment data, job creation, wage growth, and labor market health
- **Consumer Confidence Index (Ct)**: Spending patterns, economic sentiment, and consumer behavior trends
- **Manufacturing Data**: PMI, industrial production, capacity utilization, and sector health
- **Housing Market**: Housing starts, building permits, home sales, and real estate trends

### 2. Monetary Policy & Central Banking
- **Fed Funds Rate (Ft)**: Current interest rate levels, rate hike/cut expectations, and monetary policy stance
- **Federal Reserve Policy**: FOMC decisions, forward guidance, balance sheet management, and policy outlook
- **Global Central Banks**: ECB, BoJ, BoE, PBOC policy coordination and divergence
- **Money Supply (Mt)**: Liquidity conditions, credit availability, and financial market conditions

### 3. Global Economic Factors
- **Trade Relations**: Tariffs, trade agreements, supply chain disruptions, and international commerce
- **Geopolitical Events**: Political stability, international conflicts, sanctions, and global risk factors
- **Currency Markets**: US Dollar Index (Dt), INR/USD Exchange Rate (Et), and currency correlations
- **Commodity Prices**: Crude Oil Prices (Ot), Gold Prices (Gdt), industrial metals, and agricultural products
- **Emerging Markets**: Growth prospects, debt levels, political risks, and investment opportunities

### 4. Market Sentiment & Risk Factors
- **Volatility Index (VIX, Vt)**: Market fear, risk appetite, and volatility expectations
- **S&P 500 Index (St)**: Equity market performance, sector rotation, and risk-on/risk-off sentiment
- **Risk Appetite**: Credit spreads, safe-haven flows, and investor behavior patterns
- **Sector Rotation**: Defensive vs. cyclical sector performance and economic cycle positioning
- **Market Breadth**: Advance/decline ratios, new highs/lows, and market participation
- **Institutional Flows**: Fund flows, positioning, allocation changes, and smart money movements

## Analysis Approach:

1. **Start with Macro Context**: Assess current economic environment and identify key trends
2. **Variable-Specific Analysis**: Analyze each macroeconomic variable individually with current values and trends
3. **Market Impact Assessment**: Determine how macro factors affect the specific security being analyzed
4. **Risk Evaluation**: Identify macroeconomic risks, their probability, and potential impact
5. **Trading Implications**: Provide actionable insights and recommendations for trading decisions

## Technical Indicators for Macro Context:

When analyzing market data, focus on indicators that reflect macroeconomic trends:

**Trend Indicators:**
- close_50_sma: Medium-term economic trend confirmation
- close_200_sma: Long-term economic cycle positioning
- close_10_ema: Short-term economic momentum shifts

**Volatility & Risk Indicators:**
- atr: Economic uncertainty and market volatility
- boll: Economic cycle positioning and mean reversion
- boll_ub/lb: Economic extreme conditions and reversals

**Momentum Indicators:**
- rsi: Economic momentum and overbought/oversold conditions
- macd: Economic cycle momentum and trend changes
- vwma: Economic trend confirmation with volume validation

## Response Requirements:

- Provide comprehensive macroeconomic analysis with specific economic data points for each variable
- Explain how each macro factor impacts the specific security being analyzed
- Identify key economic risks and opportunities with probability assessments
- Give actionable trading recommendations based on macro analysis
- Use technical indicators to validate macro trends
- Include economic calendar events and their potential impact
- Structure the response to clearly show the relationship between macro variables and market outcomes

## CRITICAL: You MUST respond with ONLY a valid JSON object in the following format:

{   
    "prefix": "...", // The prefix of the response. If previous messages contain FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**, make sure to include it in your response too. Else, leave it empty.
    "content": "...", // Comprehensive macroeconomic analysis with economic data, policy implications, and market impact
    "economic_variables": [{
        "variable": "...", // Variable name (e.g., "Inflation Rate (It)", "Fed Funds Rate (Ft)", "GDP Growth (Gt)")
        "current_value": "...", // Current value or status
        "trend": "...", // Trend direction (increasing, decreasing, stable, mixed)
        "impact_on_markets": "...", // How this variable affects financial markets
        "impact_on_security": "...", // How this variable specifically affects the analyzed security
        "confidence": 0 // Confidence in the analysis (1-100)
    }], // List of all key macroeconomic variables with detailed analysis
    "macro_risks": [{
        "risk": "...", // Description of macroeconomic risk
        "probability": "...", // High/Medium/Low probability
        "affected_variables": ["...", "..."], // List of variables affected by this risk
        "potential_impact": "...", // Potential impact on trading position
        "timeframe": "..." // Short-term/Medium-term/Long-term impact
    }], // List of macroeconomic risks to consider
    "policy_implications": [{
        "policy_area": "...", // Monetary policy, fiscal policy, trade policy, etc.
        "current_stance": "...", // Current policy position
        "expected_changes": "...", // Expected policy changes
        "market_impact": "..." // How policy changes affect markets
    }], // Analysis of policy implications
    "confidence": 0, // Overall confidence in the analysis (1-100)
    "decision": 0, // Trading decision based on macro analysis (1-100, where 1 is avoid trading, 100 is aggressive trading)
    "table": "..." // Markdown table summarizing key macroeconomic insights and trading implications
}

Make sure to append a Markdown table at the end of the report to organize key macroeconomic insights and their trading implications."""
            + f"\n\nBlackboard Context:{blackboard_context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}"
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        # Execute the analysis
        messages = state["messages"]
        response = llm.invoke(prompt.format_messages(messages=messages))
        
        # Parse the response
        try:
            # Extract the content from the response
            content = response.content
            
            # Try to parse as JSON
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                
                # Parse the JSON response
                parsed_response = json.loads(json_str)
                
                # Post analysis report to blackboard
                blackboard_agent.post_analysis_report(
                    ticker=ticker,
                    analysis=parsed_response,
                    confidence=str(parsed_response.get("confidence", 50))
                )
                
                # Return the parsed response
                return {
                    "messages": [response],
                    "macroeconomic_analysis": parsed_response
                }
            else:
                # Fallback if JSON parsing fails
                fallback_response = {
                    "prefix": "",
                    "content": content,
                    "economic_variables": [],
                    "macro_risks": [],
                    "policy_implications": [],
                    "confidence": 50,
                    "decision": 50,
                    "table": "| Factor | Status | Impact |\n|--------|--------|--------|\n| Analysis | Complete | See content above |"
                }
                
                # Post to blackboard
                blackboard_agent.post_analysis_report(
                    ticker=ticker,
                    analysis=fallback_response,
                    confidence="50"
                )
                
                return {
                    "messages": [response],
                    "macroeconomic_analysis": fallback_response
                }
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in macroeconomic analyst: {e}")
            # Return the raw response if JSON parsing fails
            return {"messages": [response]}

    return macroeconomic_analyst_node 