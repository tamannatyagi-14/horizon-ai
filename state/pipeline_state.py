from typing import TypedDict, Optional 

class PipelineState(TypedDict):
    # User input 
    topic: str
    
    #Researcher output 
    research_notes :str
    
    #writer output
    draft: str
    
    #editor feedback (if rejected)
    editor_feedback:str
    
    #retry count for editor feedback
    retry_count: int
    
    #editor decision (approved/rejected)
    is_approved: bool
 
    #3 retries ke baad human review chahiye
    human_review_needed: bool

    # Fact checker ka result
    fact_check_passed: bool
    fact_check_notes: str

    # Final platform outputs
    platform_outputs: dict