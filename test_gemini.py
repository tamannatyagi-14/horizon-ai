from orchestrator.graph import horizon_graph

# Initial state
state = {
    "topic": "My DRDO internship where I built a computer vision system",
    "research_notes": "",
    "draft": "",
    "editor_feedback": "",
    "retry_count": 0,
    "is_approved": False,
    "human_review_needed": False,
    "fact_check_passed": False,
    "fact_check_notes": "",
    "platform_outputs": {}
}

# Graph chalao — sab automatic hoga
print("Pipeline starting...")
result = horizon_graph.invoke(state)

print("\n=== FINAL RESULT ===")
print("Draft:", result["draft"])
print("Approved:", result["is_approved"])
print("Retry count:", result["retry_count"])

print("\n=== PLATFORM OUTPUTS ===")
print("LinkedIn:", result["platform_outputs"].get("linkedin", ""))
print("\nInstagram:", result["platform_outputs"].get("instagram", ""))
print("\nTwitter:", result["platform_outputs"].get("twitter", ""))