from state.pipeline_state import PipelineState
from utils.gemini_client import call_gemini
from prompts.researcher_prompt import RESEARCHER_PROMPT

def researcher_node(state: PipelineState) -> dict:
    """
    Topic lega, key points nikalega, research notes return karega.
    """
    topic = state["topic"]
    
    # Prompt mein topic daal do
    prompt = RESEARCHER_PROMPT.format(topic=topic)
    
    # Gemini ko call karo
    result = call_gemini(prompt)
    
    # Agar error aaya
    if "error" in result:
        return {
            "research_notes": f"Research failed: {result}"
        }
    
    # State update karo
    return {
        "research_notes": str(result)
    }