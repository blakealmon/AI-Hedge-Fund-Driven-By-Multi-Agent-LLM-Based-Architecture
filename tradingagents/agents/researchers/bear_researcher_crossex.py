from langchain_core.messages import AIMessage
import json
from tradingagents.agents.utils.debate_utils import increment_debate_count, get_debate_round_info

def create_bear_crossex_researcher(llm, memory):
    def bear_crossex_node(state) -> dict:
        print(f"[DEBUG] Bear Cross Examination Researcher executing...")
        investment_debate_state = state["investment_debate_state"]
        
        # Get the bull's response from bull_history
        bull_history = investment_debate_state.get("bull_history", "[]")
        try:
            bull_history_list = json.loads(bull_history) if bull_history else []
            bull_response = bull_history_list[-1] if bull_history_list else "No bull response available"
        except Exception:
            bull_response = "No bull response available"
        
        bear_history = investment_debate_state.get("bear_history", "[]")
        
        print(f"[DEBUG] Current count: {investment_debate_state.get('count', 0)}")
        print(f"[DEBUG] Bull response: {str(bull_response)[:100]}...")
        
        # Get current debate round information
        round_info = get_debate_round_info(state)
        current_round = round_info["round"]
        current_step = round_info["step_name"]
        
        print(f"[DEBUG] Round: {current_round}, Step: {current_step}")

        # Get past memory for context
        curr_situation = f"Bull Response: {bull_response}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)
        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        # Blackboard integration
        from tradingagents.blackboard.utils import create_agent_blackboard
        blackboard_agent = create_agent_blackboard("BECR_001", "BearCrossExaminer")
        
        ticker = state["company_of_interest"]
        
        json_format = """{
  "questions": [{
      "question": "...", // Question for the bull researcher
      "source": "..." // Source of the question (e.g., "Bull Response")
  }, ...],
  "rebuttals": [{
      "rebuttal": "...", // Rebuttal to the bull's argument
      "source": "..." // Source of the rebuttal (e.g., "Bull Response")
  }, ...]
}"""

        # Read full debate context for multi-round debates
        debate_round = investment_debate_state["count"] + 1
        recent_debate = blackboard_agent.get_debate_comments(topic=f"{ticker} Investment Debate")
        debate_context = ""
        if recent_debate:
            debate_context += f"\n\nDEBATE ROUND {debate_round} - Previous Debate Context:\n"
            for comment in recent_debate[-6:]:  # Last 6 comments for context (3 agents x 2 rounds)
                content = comment.get('content', {})
                debate_context += f"- {comment['sender'].get('role', 'Unknown')}: {content.get('position', 'N/A')} - {content.get('argument', 'N/A')[:200]}...\n"

        prompt = f"""As the Bear Cross-Examination Researcher, your role is to critically examine the bullish analyst's arguments, identify weaknesses, and provide compelling counter-arguments. You should focus on challenging assumptions, highlighting inconsistencies, and strengthening the bearish case.

DEBATE ROUND {debate_round}: This is round {debate_round} of the investment debate. You are cross-examining the bullish analyst's arguments from the previous round.

{debate_context}

Bullish Analyst's Response to Cross-Examine:
{bull_response}

Current Market Situation:
Market Research: {state.get('market_report', 'N/A')}
Social Media Sentiment: {state.get('sentiment_report', 'N/A')}
News Analysis: {state.get('news_report', 'N/A')}
Fundamentals: {state.get('fundamentals_report', 'N/A')}

Your task is to:
1. Critically analyze the bullish analyst's arguments
2. Identify logical fallacies, weak evidence, or flawed assumptions
3. Provide compelling counter-arguments with specific evidence
4. Strengthen the overall bearish case
5. Consider the broader debate context
6. Maintain a critical but constructive tone

Focus on:
- Questioning the validity of bullish claims
- Highlighting contradictory evidence
- Identifying overlooked negative factors
- Providing alternative interpretations
- Strengthening bearish arguments

Respond in the following JSON format:
{json_format}"""

        response = llm.invoke(prompt)

        # Parse the JSON from the LLM response
        crossex_json = {}
        try:
            crossex_json = json.loads(response.content)
        except Exception:
            pass

        # Post cross-examination to blackboard
        from tradingagents.blackboard.utils import create_agent_blackboard
        blackboard_agent = create_agent_blackboard("BECR_001", "BearCrossExaminer")
        
        ticker = state["company_of_interest"]
        
        # Format the cross-examination for posting
        crossex_text = f"Cross-Examination of Bull Arguments:\n\n"
        
        if "questions" in crossex_json:
            crossex_text += "**Questions:**\n"
            for i, q in enumerate(crossex_json["questions"], 1):
                crossex_text += f"{i}. {q.get('question', 'N/A')}\n"
            crossex_text += "\n"
        
        if "rebuttals" in crossex_json:
            crossex_text += "**Rebuttals:**\n"
            for i, r in enumerate(crossex_json["rebuttals"], 1):
                crossex_text += f"{i}. {r.get('rebuttal', 'N/A')}\n"
        
        # Post debate comment to blackboard
        blackboard_agent.post_debate_comment(
            topic=f"{ticker} Investment Debate - Cross Examination",
            position="Bearish Cross-Examination",
            argument=crossex_text,
            reply_to=None  # Could link to bull's last comment if needed
        )

        # Parse Bear History and append the new cross-examination
        try:
            bear_history_list = json.loads(bear_history)
        except Exception:
            bear_history_list = []
        bear_history_list.append(crossex_json)
        new_bear_history = json.dumps(bear_history_list)

        # Update the debate state
        new_investment_debate_state = {
            "history": investment_debate_state.get("history", "[]"),
            "bear_history": new_bear_history,
            "bull_history": investment_debate_state.get("bull_history", "[]"),
            "current_response": crossex_json,
            "judge_decision": investment_debate_state.get("judge_decision", ""),
            "count": investment_debate_state["count"],  # Keep current count
        }

        # Increment the count for the next step
        updated_state = {"investment_debate_state": new_investment_debate_state}
        updated_state = increment_debate_count(updated_state)
        
        # Return the complete state update
        return updated_state

    return bear_crossex_node
