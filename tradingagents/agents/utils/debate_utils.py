"""
Utility functions for managing debate state and count incrementing.
"""

def increment_debate_count(state: dict) -> dict:
    """
    Increment the debate count in the investment_debate_state.
    
    Args:
        state: The current agent state
        
    Returns:
        Updated state with incremented count
    """
    if "investment_debate_state" in state:
        current_count = state["investment_debate_state"].get("count", 0)
        new_count = current_count + 1
        state["investment_debate_state"]["count"] = new_count
        print(f"[DEBUG] Debate count incremented: {current_count} -> {new_count}")
    
    return state


def get_debate_round_info(state: dict) -> dict:
    """
    Get information about the current debate round.
    
    Args:
        state: The current agent state
        
    Returns:
        Dictionary with round information
    """
    if "investment_debate_state" not in state:
        return {"round": 0, "step": 0, "total_steps": 0}
    
    count = state["investment_debate_state"].get("count", 0)
    round_num = (count // 4) + 1
    step_in_round = count % 4
    
    return {
        "round": round_num,
        "step": step_in_round,
        "total_steps": count,
        "step_name": ["Bull", "Bear", "Bull Cross", "Bear Cross"][step_in_round]
    } 