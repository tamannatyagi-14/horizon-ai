from state.pipeline_state import PipelineState
from utils.gemini_client import call_gemini
from prompts.platform_prompts import PLATFORM_PROMPTS

def platform_adapter_node(state: PipelineState) -> dict:
    """
    Approved draft ko 3 platforms ke liye adapt karta hai.
    LinkedIn, Instagram, Twitter — teeno ke liye alag format.
    """
    draft = state["draft"]
    platform_outputs = {}

    # Teeno platforms ke liye loop chalao
    for platform in ["linkedin", "instagram", "twitter"]:
        
        # Platform ka prompt lo aur draft inject karo
        prompt = PLATFORM_PROMPTS[platform].format(draft=draft)
        
        # Gemini ko call karo
        result = call_gemini(prompt)

        # Error handle karo
        if "error" in result:
            platform_outputs[platform] = {
                "content": f"Generation failed for {platform}",
                "error": True
            }
        else:
            platform_outputs[platform] = result

    # State update karo
    return {
        "platform_outputs": platform_outputs
    }