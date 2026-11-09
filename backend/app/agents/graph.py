from langgraph.graph import StateGraph, START, END

from backend.app.agents.state import AgentState
from backend.app.agents.nodes import (
    routing_node,
    retrieval_node,
    analysis_node,
    response_node,
    verification_node,
)


def route_after_routing(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "end"

    if state.get("requires_analysis"):
        return "analysis"

    if state.get("requires_rag"):
        return "retrieval"

    return "response"


def route_after_execution(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "end"

    return "response"


def build_agent_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("router", routing_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("response", response_node)
    workflow.add_node("verification", verification_node)

    workflow.add_edge(START, "router")

    workflow.add_conditional_edges(
        "router",
        route_after_routing,
        {
            "retrieval": "retrieval",
            "analysis": "analysis",
            "response": "response",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "retrieval",
        route_after_execution,
        {
            "response": "response",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "analysis",
        route_after_execution,
        {
            "response": "response",
            "end": END,
        },
    )

    workflow.add_edge("response", "verification")
    workflow.add_edge("verification", END)

    return workflow.compile()


agent_graph = build_agent_graph()


async def run_agent(
    user_query: str,
    csv_bytes: bytes | None = None,
    csv_filename: str | None = None,
) -> dict:
    """
    Executes the LangGraph workflow.
    """
    initial_state: AgentState = {
        "user_query": user_query,
        "csv_bytes": csv_bytes,
        "csv_filename": csv_filename,
        "status": "started",
        "execution_steps": [],
        "citations": [],
        "retrieved_documents": [],
        "error": None,
    }

    return await agent_graph.ainvoke(initial_state)