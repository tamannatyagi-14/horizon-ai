from state.pipeline_state import PipelineState
from utils.gemini_client import call_gemini
from prompts.writer_prompt import WRITER_PROMPT_FIRST, WRITER_PROMPT_RETRY

def writer_node(state: PipelineState) -> dict:
    """
    Research notes se draft banata hai.
    Agar retry hai toh editor feedback bhi use karta hai.
    """
    research_notes = state["research_notes"]
    editor_feedback = state["editor_feedback"]
    previous_draft = state["draft"]
    retry_count = state["retry_count"]

    # Decide karo — pehli baar hai ya retry
    if retry_count == 0:
        # Pehli baar — sirf research notes use karo
        prompt = WRITER_PROMPT_FIRST.format(
            research_notes=research_notes
        )
    else:
        # Retry — research + previous draft + feedback use karo
        prompt = WRITER_PROMPT_RETRY.format(
            research_notes=research_notes,
            previous_draft=previous_draft,
            editor_feedback=editor_feedback
        )

    # Gemini ko call karo — Writer ke liye Flash use karo
    result = call_gemini(prompt, use_flash=True)

    # Error handle karo
    if "error" in result:
        return {"draft": f"Writing failed: {result}"}

    # State update karo
    return {
        "draft": result.get("draft", ""),
    }