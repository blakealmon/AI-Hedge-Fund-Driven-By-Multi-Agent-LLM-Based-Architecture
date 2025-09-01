# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.blackboard.utils import create_agent_blackboard

def create_fundamentals_analyst(llm, toolkit):
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("FA_001", "FundamentalAnalyst")
        # Read recent analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

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
            "You are a researcher tasked with analyzing fundamental information over the past week about a company. Please write a comprehensive report of the company's fundamental information such as financial documents, company profile, basic company financials, company financial history, insider sentiment and insider transactions to gain a full view of the company's fundamental information to inform traders. Make sure to include as much detail as possible. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
            + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
            + f"\n\nBlackboard Context:{blackboard_context}"
        )

        json_format = """
                    {   
                        "prefix": "...", // The prefix of the response. If previous messages contain FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**, make sure to include it in your response too. Else, leave it empty.
                        "content": "...", // The writeup of the content
                        "confidence": "", // The confidence of the response, a number between 1 and 100
                        "decision": "", // the decision of the response as a scale from 1 to 100, where 1 is do not trade and 100 is trade
                        "table": "" // A Markdown table with key points in the report, organized and easy to read
                    }
                    """

        system_prompt = (
            "You are a helpful AI assistant, collaborating with other assistants."
            " Use the provided tools to progress towards answering the question."
            " If you are unable to fully answer, that's OK; another assistant with different tools"
            " will help where you left off. Execute what you can to make progress."
            " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
            " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
            " You have access to the following tools: {tool_names}.\n\n{system_message}\n\n"
            " For your reference, the current date is {current_date}. The company we want to look at is {ticker}."
            " Respond ONLY with a valid JSON object in the following format: {json_format}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(json_format=json_format)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content.encode('utf-8', errors='replace').decode('utf-8') if result.content else ""
        else:
            state["fundamentals_tools_used"] = True

        # Escape the result content to handle Unicode characters
        if hasattr(result, 'content') and result.content:
            result.content = result.content.encode('utf-8', errors='replace').decode('utf-8')

        # Post the generated report to the blackboard
        # Extract recommendation and confidence heuristically
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
        analysis_content = {
            "ticker": ticker,
            "recommendation": recommendation,
            "confidence": confidence,
            "analysis": report
        }
        blackboard_agent.post_analysis_report(
            ticker=ticker,
            analysis=analysis_content,
            confidence=confidence
        )

        return {
            "messages": [result],
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
