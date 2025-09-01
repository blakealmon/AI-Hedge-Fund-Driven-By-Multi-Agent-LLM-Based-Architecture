"""
Example usage of the blackboard communication system.

This file demonstrates how agents can use the blackboard system
to communicate with each other in the TradingAgents framework.
"""

import uuid
from datetime import datetime, timezone
from tradingagents.blackboard import (
    BlackboardMessage, 
    write_message, 
    read_messages,
    BlackboardAgent,
    create_agent_blackboard
)


def example_basic_usage():
    """Example of basic blackboard usage."""
    print("=== Basic Blackboard Usage Example ===")
    
    # Create a message manually
    msg = BlackboardMessage(
        message_id=str(uuid.uuid4()),
        sender={"id": "Agent_01", "role": "FundamentalAnalyst"},
        intent="Inform",
        type="AnalysisReport",
        timestamp=datetime.now(timezone.utc),
        content={
            "ticker": "AAPL",
            "recommendation": "Bullish",
            "confidence": "High",
            "analysis": {
                "revenue_growth": "15% YoY",
                "profit_margins": "Expanding",
                "market_position": "Strong"
            }
        }
    )
    
    # Write the message to the blackboard
    write_message(msg.model_dump())
    print(f"Posted message: {msg.message_id}")
    
    # Read all analysis reports
    analysis_reports = read_messages({"type": "AnalysisReport"})
    print(f"Found {len(analysis_reports)} analysis reports")
    
    for report in analysis_reports:
        content = report.get('content', {})
        print(f"- {report['sender'].get('role', 'Unknown')}: {content.get('ticker', 'N/A')} - {content.get('recommendation', 'N/A')}")


def example_agent_integration():
    """Example of how agents can integrate with the blackboard."""
    print("\n=== Agent Integration Example ===")
    
    # Create blackboard agents for different roles
    fundamental_analyst = create_agent_blackboard("FA_001", "FundamentalAnalyst")
    technical_analyst = create_agent_blackboard("TA_001", "TechnicalAnalyst")
    trader = create_agent_blackboard("TR_001", "Trader")
    risk_manager = create_agent_blackboard("RM_001", "RiskManager")
    
    # Fundamental analyst posts an analysis
    analysis_msg_id = fundamental_analyst.post_analysis_report(
        ticker="TSLA",
        analysis={
            "revenue_growth": "25% YoY",
            "profit_margins": "Improving",
            "market_position": "Leading in EV market",
            "risks": ["Supply chain issues", "Competition"]
        },
        confidence="High"
    )
    print(f"Fundamental Analyst posted analysis: {analysis_msg_id}")
    
    # Technical analyst posts a trade proposal
    trade_msg_id = technical_analyst.post_trade_proposal(
        ticker="TSLA",
        action="Buy",
        quantity=100,
        price=250.0,
        reasoning="Strong technical breakout above resistance level"
    )
    print(f"Technical Analyst posted trade proposal: {trade_msg_id}")
    
    # Risk manager posts a risk alert
    risk_msg_id = risk_manager.post_risk_alert(
        ticker="TSLA",
        risk_level="Medium",
        risk_factors=["High volatility", "Market sentiment shift"],
        recommendation="Reduce position size, set stop-loss at $240"
    )
    print(f"Risk Manager posted risk alert: {risk_msg_id}")
    
    # Trader reads all relevant information
    print("\n--- Trader's Information Gathering ---")
    
    # Get analysis reports for TSLA
    tsla_analyses = trader.get_analysis_reports(ticker="TSLA")
    print(f"Found {len(tsla_analyses)} analysis reports for TSLA")
    
    # Get trade proposals for TSLA
    tsla_trades = trader.get_trade_proposals(ticker="TSLA")
    print(f"Found {len(tsla_trades)} trade proposals for TSLA")
    
    # Get risk alerts for TSLA
    tsla_risks = trader.get_risk_alerts(ticker="TSLA")
    print(f"Found {len(tsla_risks)} risk alerts for TSLA")
    
    # Get recent messages from the last hour
    recent_messages = trader.get_recent_messages(hours=1)
    print(f"Found {len(recent_messages)} recent messages")
    
    # Trader posts a debate comment
    debate_msg_id = trader.post_debate_comment(
        topic="TSLA Trading Decision",
        position="Bullish",
        argument="Combining fundamental strength with technical breakout, TSLA looks attractive despite medium risk level. Recommend proceeding with reduced position size as suggested by risk management."
    )
    print(f"Trader posted debate comment: {debate_msg_id}")
    
    # Get the debate thread
    debate_comments = trader.get_debate_comments(topic="TSLA Trading Decision")
    print(f"Found {len(debate_comments)} debate comments")


def example_debate_thread():
    """Example of a threaded debate using reply_to."""
    print("\n=== Debate Thread Example ===")
    
    # Create agents for a debate
    bull_researcher = create_agent_blackboard("BR_001", "BullResearcher")
    bear_researcher = create_agent_blackboard("BR_002", "BearResearcher")
    
    # Initial debate comment
    initial_comment = bull_researcher.post_debate_comment(
        topic="Market Outlook Q4 2024",
        position="Bullish",
        argument="Strong earnings growth, Fed easing cycle, and AI revolution will drive markets higher."
    )
    print(f"Bull Researcher posted initial comment: {initial_comment}")
    
    # Bear researcher replies
    reply_1 = bear_researcher.post_debate_comment(
        topic="Market Outlook Q4 2024",
        position="Bearish",
        argument="Valuation concerns, geopolitical risks, and potential recession indicators suggest caution.",
        reply_to=initial_comment
    )
    print(f"Bear Researcher replied: {reply_1}")
    
    # Bull researcher counters
    counter_reply = bull_researcher.post_debate_comment(
        topic="Market Outlook Q4 2024",
        position="Bullish",
        argument="Valuations are reasonable given growth prospects, and geopolitical risks are already priced in.",
        reply_to=reply_1
    )
    print(f"Bull Researcher countered: {counter_reply}")
    
    # Get the full debate thread
    debate_thread = bull_researcher.get_debate_comments(topic="Market Outlook Q4 2024")
    print(f"Debate thread has {len(debate_thread)} comments")


def example_targeted_communication():
    """Example of targeted communication between agents."""
    print("\n=== Targeted Communication Example ===")
    
    # Create agents
    research_manager = create_agent_blackboard("RM_001", "ResearchManager")
    analyst = create_agent_blackboard("AN_001", "Analyst")
    
    # Research manager requests analysis from specific analyst
    request_msg_id = research_manager.post_request(
        request_type="AnalysisRequest",
        content={
            "ticker": "NVDA",
            "analysis_type": "Comprehensive",
            "deadline": "2024-01-15T18:00:00Z",
            "priority": "High"
        },
        target={"id": "AN_001", "role": "Analyst"}
    )
    print(f"Research Manager sent request to Analyst: {request_msg_id}")
    
    # Analyst checks for messages targeted to them
    my_messages = analyst.get_messages_for_me()
    print(f"Analyst found {len(my_messages)} messages targeted to them")
    
    for msg in my_messages:
        print(f"- {msg['type']}: {msg['content']}")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_agent_integration()
    example_debate_thread()
    example_targeted_communication()
    
    print("\n=== Example Complete ===")
    print("Check blackboard_logs.jsonl to see all posted messages!") 