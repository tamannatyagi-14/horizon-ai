from langgraph.graph import StateGraph, END
from state.pipeline_state import PipelineState
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.editor import editor_node
from agents.fact_checker import fact_checker_node
from agents.platform_adapter import platform_adapter_node


def should_retry(state: PipelineState) -> str:
    """
    Editor ke baad decide karta hai kahan jaana hai.
    """
    if state["is_approved"]:
        return "fact_checker"
    elif state["human_review_needed"]:
        return "human_review"
    else:
        return "writer"


def build_graph():
    graph = StateGraph(PipelineState)

    # Nodes add karo
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("editor", editor_node)
    graph.add_node("fact_checker", fact_checker_node)
    graph.add_node("platform_adapter", platform_adapter_node)

    # Entry point
    graph.set_entry_point("researcher")

    # Simple edges
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "editor")
    graph.add_edge("fact_checker", "platform_adapter")
    graph.add_edge("platform_adapter", END)

    # Conditional edge
    graph.add_conditional_edges(
        "editor",
        should_retry,
        {
            "writer": "writer",
            "fact_checker": "fact_checker",
            "human_review": END
        }
    )

    return graph.compile()


horizon_graph = build_graph()
