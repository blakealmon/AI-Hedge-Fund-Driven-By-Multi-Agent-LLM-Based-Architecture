"""
FastAPI endpoints for the blackboard communication system.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .schema import BlackboardMessage
from .storage import write_message, read_messages, get_blackboard_stats, clear_blackboard


app = FastAPI(
    title="TradingAgents Blackboard API",
    description="API for the blackboard communication system",
    version="1.0.0"
)


class MessageCreateRequest(BaseModel):
    """Request model for creating a new message."""
    sender: Dict[str, str]
    intent: str
    type: str
    target: Optional[Dict[str, str]] = None
    content: Dict[str, Any]
    reply_to: Optional[str] = None


class MessageResponse(BaseModel):
    """Response model for messages."""
    message_id: str
    sender: Dict[str, str]
    intent: str
    type: str
    target: Optional[Dict[str, str]] = None
    timestamp: str
    content: Dict[str, Any]
    reply_to: Optional[str] = None


@app.get("/blackboard", response_model=List[MessageResponse])
async def get_messages(
    type: Optional[str] = Query(None, description="Filter by message type"),
    sender_role: Optional[str] = Query(None, description="Filter by sender role"),
    sender_id: Optional[str] = Query(None, description="Filter by sender ID"),
    intent: Optional[str] = Query(None, description="Filter by intent"),
    target_role: Optional[str] = Query(None, description="Filter by target role"),
    target_id: Optional[str] = Query(None, description="Filter by target ID"),
    reply_to: Optional[str] = Query(None, description="Filter by reply_to message ID"),
    timestamp_after: Optional[str] = Query(None, description="Filter messages after this timestamp (ISO format)"),
    timestamp_before: Optional[str] = Query(None, description="Filter messages before this timestamp (ISO format)")
):
    """
    Get messages from the blackboard with optional filtering.
    
    Returns a list of messages that match the specified filters.
    """
    filters = {}
    
    if type:
        filters["type"] = type
    if sender_role:
        filters["sender.role"] = sender_role
    if sender_id:
        filters["sender.id"] = sender_id
    if intent:
        filters["intent"] = intent
    if target_role:
        filters["target.role"] = target_role
    if target_id:
        filters["target.id"] = target_id
    if reply_to:
        filters["reply_to"] = reply_to
    if timestamp_after:
        filters["timestamp_after"] = timestamp_after
    if timestamp_before:
        filters["timestamp_before"] = timestamp_before
    
    messages = read_messages(filters)
    return messages


@app.post("/blackboard", response_model=MessageResponse)
async def create_message(message_request: MessageCreateRequest):
    """
    Create a new message on the blackboard.
    
    Creates a new message with a unique ID and timestamp, then stores it.
    """
    import uuid
    
    # Create the message
    message = BlackboardMessage(
        message_id=str(uuid.uuid4()),
        sender=message_request.sender,
        intent=message_request.intent,
        type=message_request.type,
        target=message_request.target,
        timestamp=datetime.utcnow(),
        content=message_request.content,
        reply_to=message_request.reply_to
    )
    
    # Write to storage
    write_message(message.dict())
    
    return message


@app.get("/blackboard/stats")
async def get_stats():
    """
    Get statistics about the blackboard.
    
    Returns counts of messages by type, sender role, and intent.
    """
    return get_blackboard_stats()


@app.delete("/blackboard")
async def clear_messages():
    """
    Clear all messages from the blackboard.
    
    WARNING: This action cannot be undone.
    """
    clear_blackboard()
    return {"message": "Blackboard cleared successfully"}


@app.get("/blackboard/health")
async def health_check():
    """
    Health check endpoint for the blackboard API.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TradingAgents Blackboard API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 