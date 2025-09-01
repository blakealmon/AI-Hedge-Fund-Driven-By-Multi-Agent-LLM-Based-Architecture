# Done
from langchain_core.messages import AIMessage
import json

def create_bear_researcher_ask(llm, memory):
    def bear_researcher_ask_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        bull_response = investment_debate_state.get("current_response", "")
        bear_history = investment_debate_state.get("bear_history", "[]")

        curr_situation = f"Bull Response: {bull_response}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        json_format = """{
  "questions": [{
      "question": "...", // Question for the bull researcher
      "source": "..." // Source of the question (e.g., "Bull Response")
  }, ...]
}"""

        prompt = f"""You are a Bear Analyst conducting a cross-examination of the Bull Analyst's arguments. Your goal is to critically analyze the bull's response and generate insightful questions to their claims.

Key points to focus on:

- Questions: Formulate questions that challenge the bull's assumptions, data, or reasoning.

Resources available:
Bull's latest response: {bull_response}
Reflections from similar situations and lessons learned: {past_memory_str}

Respond ONLY with a valid JSON object in the following format:
{json_format}
The content of the questions should be detailed and evidence-based. Source indicates where the information was obtained from, such as the bull's response or past reflections.
"""
        response = llm.invoke(prompt)

        # Parse the JSON from the LLM response
        crossex_json = {}
        try:
            crossex_json = json.loads(response.content)
        except Exception:
            pass

        # Parse Bear History and append the new cross-examination
        try:
            bear_history_list = json.loads(bear_history)
        except Exception:
            bear_history_list = []
        bear_history_list.append(crossex_json)
        new_bear_history = json.dumps(bear_history_list)

        new_investment_debate_state = {
            "bear_history": new_bear_history,
            "bull_history": investment_debate_state.get("bull_history", "[]"),
            "current_response": crossex_json,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_researcher_ask_node
