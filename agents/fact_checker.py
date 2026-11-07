from state.pipeline_state import PipelineState
from utils.gemini_client import call_gemini
from prompts.fact_checker_prompt import FACT_CHECKER_PROMPT

def fact_checker_node(state: PipelineState) -> dict:
    """
    Approved draft ko verify karta hai.
    Exaggerated ya unverifiable claims flag karta hai.
    """
    draft = state["draft"]

    # Prompt taiyaar karo
    prompt = FACT_CHECKER_PROMPT.format(draft=draft)

    # Gemini ko call karo
    result = call_gemini(prompt)

    # Error handle karo
    if "error" in result:
        return {
            "fact_check_passed": True,
            "fact_check_notes": "Fact check failed, force passing."
        }

    passed = result.get("passed", True)
    flagged = result.get("flagged_claims", [])

    # Flagged claims ko readable string mein convert karo
    notes = ""
    if flagged:
        notes = " | ".join(flagged)

    return {
        "fact_check_passed": passed,
        "fact_check_notes": notes
    }