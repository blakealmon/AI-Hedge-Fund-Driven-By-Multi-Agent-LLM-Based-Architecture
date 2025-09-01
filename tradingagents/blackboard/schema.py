"""
Schema definitions for the blackboard communication system.
"""

from typing import Dict, Optional, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

# Message type constants for better organization
ANALYSIS_REPORT = "AnalysisReport"
TRADE_PROPOSAL = "TradeProposal"
DEBATE_COMMENT = "DebateComment"
RISK_ALERT = "RiskAlert"

# Manager-specific message types
INVESTMENT_DECISION = "InvestmentDecision"
RISK_ASSESSMENT = "RiskAssessment"
DEBATE_SUMMARY = "DebateSummary"
PORTFOLIO_RECOMMENDATION = "PortfolioRecommendation"

# Risk manager-specific message types
RISK_DEBATE_COMMENT = "RiskDebateComment"
RISK_POSITION = "RiskPosition"
RISK_RECOMMENDATION = "RiskRecommendation"

# Risk stance constants
RISK_STANCE_AGGRESSIVE = "Aggressive"
RISK_STANCE_CONSERVATIVE = "Conservative"
RISK_STANCE_NEUTRAL = "Neutral"

# Trader-specific message types
TRADE_DECISION = "TradeDecision"
TRADE_EXECUTION = "TradeExecution"
PORTFOLIO_UPDATE = "PortfolioUpdate"
TRADE_ANALYSIS = "TradeAnalysis"

# Trade action constants
TRADE_ACTION_BUY = "BUY"
TRADE_ACTION_SELL = "SELL"
TRADE_ACTION_HOLD = "HOLD"


class BlackboardMessage(BaseModel):
    """
    A message posted to the blackboard by an agent.
    
    This model defines the structure for all inter-agent communication
    in the TradingAgents framework.
    """
    
    message_id: str = Field(..., description="Unique identifier for the message")
    sender: Dict[str, str] = Field(..., description="Sender information with 'id' and 'role' keys")
    intent: str = Field(..., description="Communication intent: Inform, Request, Propose, Critique, etc.")
    type: str = Field(..., description="Message type: AnalysisReport, DebateComment, TradeProposal, etc.")
    target: Optional[Dict[str, str]] = Field(None, description="Target recipient information")
    timestamp: datetime = Field(..., description="When the message was created")
    content: Dict[str, Any] = Field(..., description="The message payload with structured content")
    reply_to: Optional[str] = Field(None, description="ID of the message this is replying to")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 