"""
Storage functions for the blackboard communication system.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


# Default blackboard log file
BLACKBOARD_LOG_FILE = "blackboard_logs.jsonl"


def write_message(message: Dict[str, Any]) -> None:
    """
    Append a message to the blackboard log file.
    
    Args:
        message: Dictionary representation of a BlackboardMessage
    """
    # Ensure the message has a timestamp if not provided
    if "timestamp" not in message:
        message["timestamp"] = datetime.utcnow().isoformat()
    
    # Convert datetime objects to ISO format for JSON serialization
    if isinstance(message["timestamp"], datetime):
        message["timestamp"] = message["timestamp"].isoformat()
    
    # Write to JSONL file (one JSON object per line)
    with open(BLACKBOARD_LOG_FILE, "a", encoding="utf-8") as f:
        json.dump(message, f, ensure_ascii=False)
        f.write("\n")


def read_messages(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Read messages from the blackboard log file with optional filtering.
    
    Args:
        filters: Optional dictionary of filters to apply. Keys can be:
                - 'type': Filter by message type
                - 'sender.role': Filter by sender role
                - 'sender.id': Filter by sender ID
                - 'intent': Filter by intent
                - 'target.role': Filter by target role
                - 'target.id': Filter by target ID
                - 'reply_to': Filter by reply_to message ID
                - 'timestamp_after': Filter messages after this timestamp (ISO format)
                - 'timestamp_before': Filter messages before this timestamp (ISO format)
    
    Returns:
        List of message dictionaries that match the filters
    """
    if not os.path.exists(BLACKBOARD_LOG_FILE):
        return []
    
    messages = []
    
    with open(BLACKBOARD_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                message = json.loads(line)
                if _matches_filters(message, filters):
                    messages.append(message)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    
    return messages


def _matches_filters(message: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    """
    Check if a message matches the given filters.
    
    Args:
        message: The message to check
        filters: The filters to apply
    
    Returns:
        True if the message matches all filters, False otherwise
    """
    if not filters:
        return True
    
    for filter_key, filter_value in filters.items():
        if filter_key == "timestamp_after":
            if "timestamp" not in message:
                return False
            message_time = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
            filter_time = datetime.fromisoformat(filter_value.replace("Z", "+00:00"))
            if message_time <= filter_time:
                return False
        elif filter_key == "timestamp_before":
            if "timestamp" not in message:
                return False
            message_time = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
            filter_time = datetime.fromisoformat(filter_value.replace("Z", "+00:00"))
            if message_time >= filter_time:
                return False
        elif "." in filter_key:
            # Handle nested keys like "sender.role"
            keys = filter_key.split(".")
            value = message
            for key in keys:
                if value is None or key not in value:
                    return False
                value = value[key]
            if value != filter_value:
                return False
        else:
            # Handle top-level keys
            if filter_key not in message or message[filter_key] != filter_value:
                return False
    
    return True


def clear_blackboard() -> None:
    """
    Clear all messages from the blackboard log file.
    """
    if os.path.exists(BLACKBOARD_LOG_FILE):
        os.remove(BLACKBOARD_LOG_FILE)


def get_blackboard_stats() -> Dict[str, Any]:
    """
    Get statistics about the blackboard.
    
    Returns:
        Dictionary with statistics about message counts, types, etc.
    """
    if not os.path.exists(BLACKBOARD_LOG_FILE):
        return {
            "total_messages": 0,
            "message_types": {},
            "sender_roles": {},
            "intents": {}
        }
    
    stats = {
        "total_messages": 0,
        "message_types": {},
        "sender_roles": {},
        "intents": {}
    }
    
    with open(BLACKBOARD_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                message = json.loads(line)
                stats["total_messages"] += 1
                
                # Count message types
                msg_type = message.get("type", "Unknown")
                stats["message_types"][msg_type] = stats["message_types"].get(msg_type, 0) + 1
                
                # Count sender roles
                sender_role = message.get("sender", {}).get("role", "Unknown")
                stats["sender_roles"][sender_role] = stats["sender_roles"].get(sender_role, 0) + 1
                
                # Count intents
                intent = message.get("intent", "Unknown")
                stats["intents"][intent] = stats["intents"].get(intent, 0) + 1
                
            except json.JSONDecodeError:
                continue
    
    return stats 