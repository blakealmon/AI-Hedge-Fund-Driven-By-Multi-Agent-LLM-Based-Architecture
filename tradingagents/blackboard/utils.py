"""
Utility functions for agents to easily interact with the blackboard system.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from .schema import BlackboardMessage
from .storage import write_message, read_messages


class BlackboardAgent:
    """
    A helper class that agents can use to interact with the blackboard.
    
    This class provides convenient methods for agents to post messages
    and read messages from other agents.
    """
    
    def __init__(self, agent_id: str, agent_role: str):
        """
        Initialize the blackboard agent.
        
        Args:
            agent_id: Unique identifier for this agent
            agent_role: Role of this agent (e.g., "FundamentalAnalyst", "Trader")
        """
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.sender = {"id": agent_id, "role": agent_role}
    
    def post_analysis_report(self, ticker: str, analysis: Dict[str, Any], 
                           confidence: str = "Medium", target: Optional[Dict[str, str]] = None) -> str:
        """
        Post an analysis report to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            analysis: Analysis content
            confidence: Confidence level (Low, Medium, High)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "analysis": analysis,
            "confidence": confidence
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="AnalysisReport",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_trade_proposal(self, ticker: str, action: str, quantity: int, 
                           price: float, reasoning: str, target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a trade proposal to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            action: Buy or Sell
            quantity: Number of shares
            price: Price per share
            reasoning: Reasoning for the trade
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": price,
            "reasoning": reasoning
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Propose",
            type="TradeProposal",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_debate_comment(self, topic: str, position: str, argument: str, 
                           reply_to: Optional[str] = None, target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a debate comment to the blackboard.
        
        Args:
            topic: Debate topic
            position: Position (Bullish, Bearish, Neutral)
            argument: Argument content
            reply_to: Optional message ID to reply to
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "topic": topic,
            "position": position,
            "argument": argument
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Critique" if reply_to else "Inform",
            type="DebateComment",
            target=target,
            timestamp=datetime.utcnow(),
            content=content,
            reply_to=reply_to
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_risk_alert(self, ticker: str, risk_level: str, risk_factors: List[str], 
                       recommendation: str, target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a risk alert to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            risk_level: Risk level (Low, Medium, High, Critical)
            risk_factors: List of risk factors
            recommendation: Risk management recommendation
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": recommendation
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="RiskAlert",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_investment_decision(self, ticker: str, decision: str, reasoning: str, 
                               confidence: str = "Medium", target: Optional[Dict[str, str]] = None) -> str:
        """
        Post an investment decision to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            decision: Investment decision (Buy, Sell, Hold)
            reasoning: Detailed reasoning for the decision
            confidence: Confidence level (Low, Medium, High)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="InvestmentDecision",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_risk_assessment(self, ticker: str, risk_level: str, risk_factors: List[str], 
                           recommendation: str, confidence: str = "Medium", 
                           target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a risk assessment to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            risk_level: Risk level (Low, Medium, High, Critical)
            risk_factors: List of risk factors
            recommendation: Risk management recommendation
            confidence: Confidence level (Low, Medium, High)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "confidence": confidence
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="RiskAssessment",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_debate_summary(self, ticker: str, debate_type: str, summary: str, 
                           decision: str, confidence: str = "Medium", 
                           target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a debate summary to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            debate_type: Type of debate (Investment, Risk, etc.)
            summary: Summary of the debate
            decision: Final decision from the debate
            confidence: Confidence level (Low, Medium, High)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "debate_type": debate_type,
            "summary": summary,
            "decision": decision,
            "confidence": confidence
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="DebateSummary",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_research_argument(self, ticker: str, position: str, argument: str, 
                             confidence: str = "Medium", evidence_sources: Optional[List[str]] = None,
                             reply_to: Optional[str] = None, target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a research argument to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            position: Position (Bullish, Bearish, Neutral)
            argument: The research argument content
            confidence: Confidence level (Low, Medium, High)
            evidence_sources: List of evidence sources used
            reply_to: Optional message ID to reply to
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "position": position,
            "argument": argument,
            "confidence": confidence,
            "evidence_sources": evidence_sources or []
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Critique" if reply_to else "Inform",
            type="ResearchArgument",
            target=target,
            timestamp=datetime.utcnow(),
            content=content,
            reply_to=reply_to
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_risk_debate_comment(self, topic: str, stance: str, argument: str, 
                                confidence: str = "Medium", reply_to: Optional[str] = None,
                                target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a risk debate comment to the blackboard.
        
        Args:
            topic: Risk debate topic
            stance: Risk stance (Aggressive, Conservative, Neutral)
            argument: The risk argument content
            confidence: Confidence level (Low, Medium, High)
            reply_to: Optional message ID to reply to
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "topic": topic,
            "stance": stance,
            "argument": argument,
            "confidence": confidence
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Critique" if reply_to else "Inform",
            type="RiskDebateComment",
            target=target,
            timestamp=datetime.utcnow(),
            content=content,
            reply_to=reply_to
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_risk_position(self, ticker: str, stance: str, confidence: str, 
                          reasoning: str, risk_level: str = "Medium",
                          target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a risk position to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            stance: Risk stance (Aggressive, Conservative, Neutral)
            confidence: Confidence level (Low, Medium, High)
            reasoning: Reasoning for the risk position
            risk_level: Risk level (Low, Medium, High, Critical)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "stance": stance,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_level": risk_level
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="RiskPosition",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_risk_recommendation(self, ticker: str, stance: str, actions: List[str], 
                                rationale: str, priority: str = "Medium",
                                target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a risk recommendation to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            stance: Risk stance (Aggressive, Conservative, Neutral)
            actions: List of recommended actions
            rationale: Rationale for the recommendations
            priority: Priority level (Low, Medium, High, Critical)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "stance": stance,
            "actions": actions,
            "rationale": rationale,
            "priority": priority
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Propose",
            type="RiskRecommendation",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_trade_decision(self, ticker: str, action: str, confidence: str, 
                           reasoning: str, target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a trade decision to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            action: Trade action (BUY, SELL, HOLD)
            confidence: Confidence level (Low, Medium, High)
            reasoning: Reasoning for the trade decision
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Propose",
            type="TradeDecision",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_trade_execution(self, ticker: str, action: str, quantity: int, 
                            price: float, execution_time: Optional[datetime] = None,
                            target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a trade execution to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            action: Trade action (BUY, SELL)
            quantity: Number of shares traded
            price: Execution price per share
            execution_time: Time of execution (defaults to current time)
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        if execution_time is None:
            execution_time = datetime.utcnow()
            
        content = {
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": price,
            "execution_time": execution_time.isoformat(),
            "total_value": quantity * price
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="TradeExecution",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_portfolio_update(self, ticker: str, position_size: int, 
                             current_value: float, unrealized_pnl: float = 0.0,
                             target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a portfolio update to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            position_size: Current position size (positive for long, negative for short)
            current_value: Current market value of the position
            unrealized_pnl: Unrealized profit/loss
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "position_size": position_size,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "position_type": "LONG" if position_size > 0 else "SHORT" if position_size < 0 else "FLAT"
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="PortfolioUpdate",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_trade_analysis(self, ticker: str, market_conditions: str, 
                           technical_analysis: str, fundamental_analysis: str,
                           risk_assessment: str, target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a trade analysis to the blackboard.
        
        Args:
            ticker: Stock ticker symbol
            market_conditions: Current market conditions analysis
            technical_analysis: Technical analysis summary
            fundamental_analysis: Fundamental analysis summary
            risk_assessment: Risk assessment summary
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        content = {
            "ticker": ticker,
            "market_conditions": market_conditions,
            "technical_analysis": technical_analysis,
            "fundamental_analysis": fundamental_analysis,
            "risk_assessment": risk_assessment
        }
        
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="TradeAnalysis",
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_request(self, request_type: str, content: Dict[str, Any], 
                    target: Optional[Dict[str, str]] = None) -> str:
        """
        Post a request to the blackboard.
        
        Args:
            request_type: Type of request
            content: Request content
            target: Optional target recipient
            
        Returns:
            Message ID of the posted message
        """
        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Request",
            type=request_type,
            target=target,
            timestamp=datetime.utcnow(),
            content=content
        )
        
        write_message(message.model_dump())
        return message.message_id
    
    def post_research_summary(
        self,
        ticker: str,
        position: str,
        key_points: Optional[list] = None,
        conclusion: Optional[str] = None,
        confidence: str = "Medium",
        evidence_sources: Optional[list] = None,
        summary: Optional[str] = None,
        reply_to: Optional[str] = None,
        target: Optional[dict] = None
    ) -> str:
        """
        Post a research summary to the blackboard.

        Args:
            ticker: Stock ticker symbol
            position: Bullish, Bearish, or Neutral
            key_points: List of key points in the summary
            conclusion: Main conclusion text
            confidence: Confidence level (Low, Medium, High)
            evidence_sources: List of evidence sources used
            summary: (Optional) If provided, used as conclusion if conclusion is not given
            reply_to: Optional message ID to reply to
            target: Optional target recipient

        Returns:
            Message ID of the posted message
        """
        import uuid
        from datetime import datetime, timezone

        if not conclusion and summary:
            conclusion = summary

        content = {
            "ticker": ticker,
            "key_points": key_points or [],
            "conclusion": conclusion or "",
            "position": position,
            "confidence": confidence,
            "evidence_sources": evidence_sources or []
        }

        message = BlackboardMessage(
            message_id=str(uuid.uuid4()),
            sender=self.sender,
            intent="Inform",
            type="ResearchSummary",
            target=target,
            timestamp=datetime.now(timezone.utc),
            content=content,
            reply_to=reply_to
        )

        write_message(message.model_dump())
        return message.message_id
    
    def get_analysis_reports(self, ticker: Optional[str] = None, 
                           sender_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get analysis reports from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            sender_role: Optional sender role to filter by
            
        Returns:
            List of analysis report messages
        """
        filters = {"type": "AnalysisReport"}
        
        if ticker:
            # We'll need to filter by content after reading
            pass
        if sender_role:
            filters["sender.role"] = sender_role
        
        messages = read_messages(filters)
        
        # Filter by ticker if specified
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_trade_proposals(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade proposals from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            
        Returns:
            List of trade proposal messages
        """
        filters = {"type": "TradeProposal"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_debate_comments(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get debate comments from the blackboard.
        
        Args:
            topic: Optional topic to filter by
            
        Returns:
            List of debate comment messages
        """
        filters = {"type": "DebateComment"}
        messages = read_messages(filters)
        
        if topic:
            messages = [msg for msg in messages if msg.get("content", {}).get("topic") == topic]
        
        return messages
    
    def get_risk_alerts(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get risk alerts from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            
        Returns:
            List of risk alert messages
        """
        filters = {"type": "RiskAlert"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_investment_decisions(self, ticker: Optional[str] = None, 
                               sender_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get investment decisions from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            sender_role: Optional sender role to filter by
            
        Returns:
            List of investment decision messages
        """
        filters = {"type": "InvestmentDecision"}
        
        if sender_role:
            filters["sender.role"] = sender_role
        
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_risk_assessments(self, ticker: Optional[str] = None, 
                           sender_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get risk assessments from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            sender_role: Optional sender role to filter by
            
        Returns:
            List of risk assessment messages
        """
        filters = {"type": "RiskAssessment"}
        
        if sender_role:
            filters["sender.role"] = sender_role
        
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_debate_summaries(self, ticker: Optional[str] = None, 
                           debate_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get debate summaries from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            debate_type: Optional debate type to filter by
            
        Returns:
            List of debate summary messages
        """
        filters = {"type": "DebateSummary"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        if debate_type:
            messages = [msg for msg in messages if msg.get("content", {}).get("debate_type") == debate_type]
        
        return messages
    
    def get_research_arguments(self, ticker: Optional[str] = None, 
                             position: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get research arguments from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            position: Optional position to filter by (Bullish, Bearish, Neutral)
            
        Returns:
            List of research argument messages
        """
        filters = {"type": "ResearchArgument"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        if position:
            messages = [msg for msg in messages if msg.get("content", {}).get("position") == position]
        
        return messages
    
    def get_research_summaries(
        self,
        ticker: Optional[str] = None,
        position: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get research summaries from the blackboard.

        Args:
            ticker: Optional ticker to filter by
            position: Optional position (Bullish, Bearish, Neutral) to filter by

        Returns:
            List of research summary messages
        """
        filters = {"type": "ResearchSummary"}
        messages = read_messages(filters)
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        if position:
            messages = [msg for msg in messages if msg.get("content", {}).get("position") == position]
        return messages
    
    def get_research_debate_thread(self, ticker: str, position: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a complete research debate thread for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            position: Optional position to filter by (Bullish, Bearish, Neutral)
            
        Returns:
            List of debate messages in chronological order
        """
        # Get both debate comments and research arguments
        debate_comments = self.get_debate_comments(topic=f"{ticker} Investment Debate")
        research_arguments = self.get_research_arguments(ticker=ticker)
        
        # Combine and sort by timestamp
        all_messages = debate_comments + research_arguments
        all_messages.sort(key=lambda x: x.get('timestamp', ''))
        
        # Filter by position if specified
        if position:
            all_messages = [msg for msg in all_messages if msg.get('content', {}).get('position') == position]
        
        return all_messages
    
    def get_risk_debate_comments(self, topic: Optional[str] = None, 
                                stance: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get risk debate comments from the blackboard.
        
        Args:
            topic: Optional topic to filter by
            stance: Optional stance to filter by (Aggressive, Conservative, Neutral)
            
        Returns:
            List of risk debate comment messages
        """
        filters = {"type": "RiskDebateComment"}
        messages = read_messages(filters)
        
        if topic:
            messages = [msg for msg in messages if msg.get("content", {}).get("topic") == topic]
        
        if stance:
            messages = [msg for msg in messages if msg.get("content", {}).get("stance") == stance]
        
        return messages
    
    def get_risk_positions(self, ticker: Optional[str] = None, 
                          stance: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get risk positions from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            stance: Optional stance to filter by (Aggressive, Conservative, Neutral)
            
        Returns:
            List of risk position messages
        """
        filters = {"type": "RiskPosition"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        if stance:
            messages = [msg for msg in messages if msg.get("content", {}).get("stance") == stance]
        
        return messages
    
    def get_risk_recommendations(self, ticker: Optional[str] = None, 
                                stance: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get risk recommendations from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            stance: Optional stance to filter by (Aggressive, Conservative, Neutral)
            
        Returns:
            List of risk recommendation messages
        """
        filters = {"type": "RiskRecommendation"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        if stance:
            messages = [msg for msg in messages if msg.get("content", {}).get("stance") == stance]
        
        return messages
    
    def get_risk_debate_thread(self, ticker: str, stance: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a complete risk debate thread for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            stance: Optional stance to filter by (Aggressive, Conservative, Neutral)
            
        Returns:
            List of risk debate messages in chronological order
        """
        # Get risk debate comments for the ticker
        risk_debate_comments = self.get_risk_debate_comments(topic=f"{ticker} Risk Debate")
        
        # Sort by timestamp
        risk_debate_comments.sort(key=lambda x: x.get('timestamp', ''))
        
        # Filter by stance if specified
        if stance:
            risk_debate_comments = [msg for msg in risk_debate_comments if msg.get('content', {}).get('stance') == stance]
        
        return risk_debate_comments
    
    def get_trade_decisions(self, ticker: Optional[str] = None, 
                           action: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade decisions from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            action: Optional action to filter by (BUY, SELL, HOLD)
            
        Returns:
            List of trade decision messages
        """
        filters = {"type": "TradeDecision"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        if action:
            messages = [msg for msg in messages if msg.get("content", {}).get("action") == action]
        
        return messages
    
    def get_trade_executions(self, ticker: Optional[str] = None, 
                            action: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade executions from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            action: Optional action to filter by (BUY, SELL)
            
        Returns:
            List of trade execution messages
        """
        filters = {"type": "TradeExecution"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        if action:
            messages = [msg for msg in messages if msg.get("content", {}).get("action") == action]
        
        return messages
    
    def get_portfolio_updates(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get portfolio updates from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            
        Returns:
            List of portfolio update messages
        """
        filters = {"type": "PortfolioUpdate"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_trade_analyses(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade analyses from the blackboard.
        
        Args:
            ticker: Optional ticker to filter by
            
        Returns:
            List of trade analysis messages
        """
        filters = {"type": "TradeAnalysis"}
        messages = read_messages(filters)
        
        if ticker:
            messages = [msg for msg in messages if msg.get("content", {}).get("ticker") == ticker]
        
        return messages
    
    def get_comprehensive_trade_context(self, ticker: str) -> Dict[str, Any]:
        """
        Get comprehensive trade context for a ticker from all agents.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary containing all relevant context for trading decisions
        """
        context = {
            "analyst_reports": self.get_analysis_reports(ticker=ticker),
            "risk_assessments": self.get_risk_assessments(ticker=ticker),
            "investment_decisions": self.get_investment_decisions(ticker=ticker),
            "research_debates": self.get_debate_comments(topic=f"{ticker} Investment Debate"),
            "risk_debates": self.get_risk_debate_comments(topic=f"{ticker} Risk Debate"),
            "trade_decisions": self.get_trade_decisions(ticker=ticker),
            "trade_executions": self.get_trade_executions(ticker=ticker),
            "portfolio_updates": self.get_portfolio_updates(ticker=ticker)
        }
        
        return context
    
    def get_messages_for_me(self, message_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages specifically targeted to this agent.
        
        Args:
            message_type: Optional message type to filter by
            
        Returns:
            List of messages targeted to this agent
        """
        filters = {"target.id": self.agent_id}
        
        if message_type:
            filters["type"] = message_type
        
        return read_messages(filters)
    
    def get_recent_messages(self, hours: int = 24, message_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent messages from the last N hours.
        
        Args:
            hours: Number of hours to look back
            message_type: Optional message type to filter by
            
        Returns:
            List of recent messages
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filters = {"timestamp_after": cutoff_time.isoformat()}
        
        if message_type:
            filters["type"] = message_type
        
        return read_messages(filters)


def create_agent_blackboard(agent_id: str, agent_role: str) -> BlackboardAgent:
    """
    Create a BlackboardAgent instance for easy integration.
    
    Args:
        agent_id: Unique identifier for the agent
        agent_role: Role of the agent
        
    Returns:
        BlackboardAgent instance
    """
    return BlackboardAgent(agent_id, agent_role) 