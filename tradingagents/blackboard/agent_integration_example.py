"""
Example of how to integrate the blackboard system with existing agents.

This file shows how to modify existing agent implementations to use
the blackboard communication system instead of direct communication.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard import create_agent_blackboard


def create_fundamentals_analyst_with_blackboard(llm, toolkit):
    """
    Modified fundamentals analyst that uses the blackboard system.
    
    This agent will:
    1. Post its analysis reports to the blackboard
    2. Read relevant messages from other agents
    3. Include blackboard context in its analysis
    """
    
    # Create blackboard agent for this analyst
    blackboard_agent = create_agent_blackboard("FA_001", "FundamentalAnalyst")
    
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        # Get relevant messages from the blackboard
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        risk_alerts = blackboard_agent.get_risk_alerts(ticker=ticker)
        trade_proposals = blackboard_agent.get_trade_proposals(ticker=ticker)
        
        # Build context from blackboard messages
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analysis Reports:\n"
            for analysis in recent_analyses[-3:]:  # Last 3 analyses
                blackboard_context += f"- {analysis['sender']['role']}: {analysis['content'].get('recommendation', 'N/A')} confidence\n"
        
        if risk_alerts:
            blackboard_context += "\n\nRisk Alerts:\n"
            for alert in risk_alerts[-2:]:  # Last 2 alerts
                blackboard_context += f"- Risk Level: {alert['content'].get('risk_level', 'N/A')} - {alert['content'].get('recommendation', 'N/A')}\n"
        
        if trade_proposals:
            blackboard_context += "\n\nRecent Trade Proposals:\n"
            for proposal in trade_proposals[-2:]:  # Last 2 proposals
                blackboard_context += f"- {proposal['content'].get('action', 'N/A')} {proposal['content'].get('quantity', 'N/A')} @ ${proposal['content'].get('price', 'N/A')}\n"

        if toolkit.config["online_tools"]:
            tools = [toolkit.get_fundamentals_openai]
        else:
            tools = [
                toolkit.get_finnhub_company_insider_sentiment,
                toolkit.get_finnhub_company_insider_transactions,
                toolkit.get_simfin_balance_sheet,
                toolkit.get_simfin_cashflow,
                toolkit.get_simfin_income_stmt,
            ]

        system_message = (
            "You are a researcher tasked with analyzing fundamental information over the past week about a company. "
            "Please write a comprehensive report of the company's fundamental information such as financial documents, "
            "company profile, basic company financials, company financial history, insider sentiment and insider transactions "
            "to gain a full view of the company's fundamental information to inform traders. "
            "Make sure to include as much detail as possible. Do not simply state the trends are mixed, provide detailed "
            "and finegrained analysis and insights that may help traders make decisions."
            " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
            f"\n\nBlackboard Context:{blackboard_context}"
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
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        # Extract key insights from the report for blackboard posting
        try:
            # Simple extraction of recommendation and confidence
            recommendation = "Neutral"
            confidence = "Medium"
            
            if "BUY" in report.upper():
                recommendation = "Bullish"
            elif "SELL" in report.upper():
                recommendation = "Bearish"
            
            if "HIGH" in report.upper() and "CONFIDENCE" in report.upper():
                confidence = "High"
            elif "LOW" in report.upper() and "CONFIDENCE" in report.upper():
                confidence = "Low"
            
            # Post analysis to blackboard
            analysis_content = {
                "ticker": ticker,
                "recommendation": recommendation,
                "confidence": confidence,
                "analysis": {
                    "report": report,
                    "key_insights": "Fundamental analysis completed",
                    "data_sources": [tool.name for tool in tools]
                }
            }
            
            message_id = blackboard_agent.post_analysis_report(
                ticker=ticker,
                analysis=analysis_content,
                confidence=confidence
            )
            
            print(f"Fundamental Analyst posted analysis to blackboard: {message_id}")
            
        except Exception as e:
            print(f"Error posting to blackboard: {e}")

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node


def create_trader_with_blackboard(llm, toolkit):
    """
    Modified trader that uses the blackboard system.
    
    This agent will:
    1. Read analysis reports, trade proposals, and risk alerts from the blackboard
    2. Make trading decisions based on all available information
    3. Post its final trading decision to the blackboard
    """
    
    # Create blackboard agent for this trader
    blackboard_agent = create_agent_blackboard("TR_001", "Trader")
    
    def trader_node(state):
        ticker = state["company_of_interest"]
        
        # Gather all relevant information from the blackboard
        analysis_reports = blackboard_agent.get_analysis_reports(ticker=ticker)
        trade_proposals = blackboard_agent.get_trade_proposals(ticker=ticker)
        risk_alerts = blackboard_agent.get_risk_alerts(ticker=ticker)
        debate_comments = blackboard_agent.get_debate_comments(topic=f"{ticker} Trading Decision")
        
        # Build comprehensive context
        blackboard_summary = f"""
        BLACKBOARD SUMMARY FOR {ticker}:
        
        Analysis Reports ({len(analysis_reports)}):
        """
        
        for report in analysis_reports:
            blackboard_summary += f"- {report['sender']['role']}: {report['content'].get('recommendation', 'N/A')} (Confidence: {report['content'].get('confidence', 'N/A')})\n"
        
        blackboard_summary += f"\nTrade Proposals ({len(trade_proposals)}):\n"
        for proposal in trade_proposals:
            blackboard_summary += f"- {proposal['sender']['role']}: {proposal['content'].get('action', 'N/A')} {proposal['content'].get('quantity', 'N/A')} @ ${proposal['content'].get('price', 'N/A')}\n"
        
        blackboard_summary += f"\nRisk Alerts ({len(risk_alerts)}):\n"
        for alert in risk_alerts:
            blackboard_summary += f"- Risk Level: {alert['content'].get('risk_level', 'N/A')} - {alert['content'].get('recommendation', 'N/A')}\n"
        
        blackboard_summary += f"\nDebate Comments ({len(debate_comments)}):\n"
        for comment in debate_comments:
            blackboard_summary += f"- {comment['sender']['role']}: {comment['content'].get('position', 'N/A')} - {comment['content'].get('argument', 'N/A')[:100]}...\n"

        system_message = (
            "You are a trader who makes final trading decisions based on all available information. "
            "You have access to analysis reports, trade proposals, risk alerts, and debate comments "
            "from other agents in the system. "
            "Your job is to synthesize all this information and make a final trading decision. "
            "Consider the confidence levels, risk factors, and different perspectives before making your decision. "
            "Make sure to explain your reasoning clearly."
            f"\n\n{blackboard_summary}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | llm

        result = chain.invoke(state["messages"])
        
        # Extract trading decision
        decision = "HOLD"
        reasoning = result.content
        
        if "BUY" in result.content.upper():
            decision = "BUY"
        elif "SELL" in result.content.upper():
            decision = "SELL"
        
        # Post final trading decision to blackboard
        try:
            decision_content = {
                "ticker": ticker,
                "decision": decision,
                "reasoning": reasoning,
                "timestamp": state.get("trade_date", "N/A"),
                "confidence": "High" if len(analysis_reports) > 0 else "Medium"
            }
            
            message_id = blackboard_agent.post_trade_proposal(
                ticker=ticker,
                action=decision,
                quantity=0,  # Will be determined by position sizing
                price=0,     # Will be determined by market price
                reasoning=reasoning
            )
            
            print(f"Trader posted final decision to blackboard: {message_id}")
            
        except Exception as e:
            print(f"Error posting trading decision to blackboard: {e}")

        return {
            "messages": [result],
            "final_decision": decision,
            "reasoning": reasoning,
        }

    return trader_node


def create_risk_manager_with_blackboard(llm, toolkit):
    """
    Modified risk manager that uses the blackboard system.
    
    This agent will:
    1. Monitor all trading activities and analysis from the blackboard
    2. Post risk alerts when necessary
    3. Provide risk management recommendations
    """
    
    # Create blackboard agent for this risk manager
    blackboard_agent = create_agent_blackboard("RM_001", "RiskManager")
    
    def risk_manager_node(state):
        ticker = state["company_of_interest"]
        
        # Get recent trading activity and analysis
        recent_trades = blackboard_agent.get_trade_proposals(ticker=ticker)
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        recent_risks = blackboard_agent.get_risk_alerts(ticker=ticker)
        
        # Analyze risk factors
        risk_factors = []
        risk_level = "Low"
        
        # Check for conflicting signals
        if len(recent_analyses) > 1:
            recommendations = [a['content'].get('recommendation', 'Neutral') for a in recent_analyses]
            if len(set(recommendations)) > 1:
                risk_factors.append("Conflicting analyst recommendations")
                risk_level = "Medium"
        
        # Check for high volatility in trade proposals
        if len(recent_trades) > 2:
            actions = [t['content'].get('action', 'HOLD') for t in recent_trades]
            if actions.count('BUY') > 0 and actions.count('SELL') > 0:
                risk_factors.append("Mixed trading signals")
                risk_level = "Medium"
        
        # Check for existing risk alerts
        if recent_risks:
            risk_level = "High"  # Escalate if there are existing alerts
        
        system_message = (
            "You are a risk manager responsible for monitoring trading activities and identifying potential risks. "
            "Based on the current trading activity and analysis, provide a risk assessment and recommendations. "
            "Consider factors like conflicting signals, high volatility, and market conditions."
            f"\n\nCurrent Activity for {ticker}:\n"
            f"- Recent trades: {len(recent_trades)}\n"
            f"- Recent analyses: {len(recent_analyses)}\n"
            f"- Existing risk alerts: {len(recent_risks)}\n"
            f"- Identified risk factors: {risk_factors}\n"
            f"- Current risk level: {risk_level}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        chain = prompt | llm

        result = chain.invoke(state["messages"])
        
        # Post risk alert if necessary
        if risk_factors or risk_level != "Low":
            try:
                recommendation = result.content
                
                message_id = blackboard_agent.post_risk_alert(
                    ticker=ticker,
                    risk_level=risk_level,
                    risk_factors=risk_factors,
                    recommendation=recommendation
                )
                
                print(f"Risk Manager posted risk alert to blackboard: {message_id}")
                
            except Exception as e:
                print(f"Error posting risk alert to blackboard: {e}")

        return {
            "messages": [result],
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }

    return risk_manager_node


# Example of how to use these modified agents
def example_agent_workflow():
    """
    Example workflow showing how the modified agents work together.
    """
    print("=== Agent Workflow with Blackboard Integration ===")
    
    # This would be called in your main workflow
    # fundamentals_analyst = create_fundamentals_analyst_with_blackboard(llm, toolkit)
    # trader = create_trader_with_blackboard(llm, toolkit)
    # risk_manager = create_risk_manager_with_blackboard(llm, toolkit)
    
    print("Agents are now integrated with the blackboard system!")
    print("They will automatically post their outputs and read from the blackboard.")
    print("Check blackboard_logs.jsonl to see the communication flow.")


if __name__ == "__main__":
    example_agent_workflow() 