from state.pipeline_state import PipelineState
from utils.gemini_client import call_gemini
from prompts.editor_prompt import EDITOR_PROMPT

def editor_node(state: PipelineState) -> dict:
    """
    Draft review karta hai — approve ya reject karta hai.
    Reject hone pe specific feedback deta hai.
    """
    draft = state["draft"]
    retry_count = state["retry_count"]

    # Prompt taiyaar karo
    prompt = EDITOR_PROMPT.format(draft=draft)

    # Gemini ko call karo
    result = call_gemini(prompt)

    # Error handle karo
    if "error" in result:
        return {
            "is_approved": True,
            "editor_feedback": "Editor failed, force approving."
        }

    approved = result.get("approved", False)
    feedback = result.get("feedback", "")

    # Agar reject hua toh retry count badhao
    if not approved:
        new_retry_count = retry_count + 1

        # 3 retries ho gayi — human review chahiye
        if new_retry_count >= 3:
            return {
                "is_approved": False,
                "editor_feedback": feedback,
                "retry_count": new_retry_count,
                "human_review_needed": True
            }

        return {
            "is_approved": False,
            "editor_feedback": feedback,
            "retry_count": new_retry_count,
            "human_review_needed": False
        }

    # Approve hua
    return {
        "is_approved": True,
        "editor_feedback": "",
        "human_review_needed": False
    }
    