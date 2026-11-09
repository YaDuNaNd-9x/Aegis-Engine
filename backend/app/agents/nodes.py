from backend.app.agents.state import AgentState
from backend.app.agents.router import agent_router
from backend.app.agents.tools import retrieve_documents, analyze_csv

from backend.app.llm.ollama_client import ollama_client


def _add_step(state: AgentState, message: str) -> list[str]:
    steps = list(state.get("execution_steps", []))
    steps.append(message)
    return steps


def _extract_citations(documents: list[dict]) -> list[dict]:
    citations = []

    for document in documents:
        citation = document.get("citation")

        if citation:
            citations.append(citation)

    return citations


async def routing_node(state: AgentState) -> dict:
    """
    Classifies the user request and selects the appropriate workflow.
    """
    query = (state.get("user_query") or "").strip()

    if not query:
        return {
            "status": "failed",
            "error": "The user query cannot be empty.",
            "execution_steps": _add_step(
                state,
                "Routing failed: empty user query.",
            ),
        }

    try:
        classification = agent_router.classify(
            query,
            has_csv=bool(state.get("csv_bytes")),
        )

        return {
            **classification,
            "status": "processing",
            "error": None,
            "execution_steps": _add_step(
                state,
                f"Request classified as: {classification['task_type']}.",
            ),
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "execution_steps": _add_step(
                state,
                f"Routing failed: {exc}",
            ),
        }


async def retrieval_node(state: AgentState) -> dict:
    """
    Retrieves relevant SOPs and documents for document-based questions.
    """
    try:
        documents = await retrieve_documents(
            query=state["user_query"],
            top_k=5,
        )

        citations = _extract_citations(documents)

        return {
            "retrieved_documents": documents,
            "citations": citations,
            "status": "processing",
            "execution_steps": _add_step(
                state,
                f"Retrieved {len(documents)} relevant document chunks.",
            ),
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": f"Document retrieval failed: {exc}",
            "execution_steps": _add_step(
                state,
                f"Document retrieval failed: {exc}",
            ),
        }


async def analysis_node(state: AgentState) -> dict:
    """
    Performs CSV analysis using the existing Docker execution sandbox.
    """
    try:
        csv_bytes = state.get("csv_bytes")

        if not csv_bytes:
            raise ValueError(
                "This request requires a CSV file. Please upload one."
            )

        result = await analyze_csv(
            instruction=state["user_query"],
            csv_bytes=csv_bytes,
        )

        return {
            "analysis_result": result.get("result"),
            "analysis_explanation": result.get("explanation"),
            "response": str(result.get("result")),
            "status": "processing",
            "execution_steps": _add_step(
                state,
                "CSV analysis completed successfully in the Docker sandbox.",
            ),
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "execution_steps": _add_step(
                state,
                f"CSV analysis failed: {exc}",
            ),
        }


async def response_node(state: AgentState) -> dict:
    """
    Generates the final answer using local Ollama inference.
    """
    if state.get("status") == "failed":
        return {}

    try:
        query = state["user_query"]
        task_type = state.get("task_type", "general")
        selected_model = state.get("selected_model")

        # CSV analysis already has a structured result.
        if task_type == "analysis":
            return {
                "status": "success",
                "execution_steps": _add_step(
                    state,
                    "Analysis result prepared for the user.",
                ),
            }

        # Document questions must be grounded in retrieved evidence.
        if task_type == "document_question":
            documents = state.get("retrieved_documents", [])

            if not documents:
                return {
                    "response": (
                        "I could not find relevant supporting information "
                        "in the uploaded knowledge base. I cannot provide "
                        "a plant-specific answer without document evidence."
                    ),
                    "status": "success",
                    "execution_steps": _add_step(
                        state,
                        "No supporting documents found; returned a grounded refusal.",
                    ),
                }

            context_parts = []

            for index, document in enumerate(documents, start=1):
                content = document.get("content", "")
                citation = document.get("citation", {})

                context_parts.append(
                    f"[Evidence {index}]\n"
                    f"Source: {citation}\n"
                    f"Content: {content}"
                )

            context = "\n\n".join(context_parts)

            system_prompt = """
You are Aegis Engine, an industrial operations assistant.

Answer document-based questions using ONLY the supplied evidence.

Rules:
1. Never invent industrial procedures, limits, measurements, or safety rules.
2. If the evidence does not answer the question, explicitly say so.
3. Distinguish documented facts from reasonable interpretations.
4. Preserve important numerical values and units.
5. Mention the relevant source when possible.
6. Never instruct users to bypass safety procedures.
"""

            user_prompt = f"""
DOCUMENT EVIDENCE:

{context}

USER QUESTION:

{query}

Provide a clear answer grounded in the evidence.
"""

        else:
            system_prompt = """
You are Aegis Engine, a private industrial operations assistant.

You run locally and help users understand industrial concepts,
maintenance principles, operational workflows, and technical topics.

Rules:
1. Do not invent plant-specific measurements or procedures.
2. Clearly distinguish general knowledge from site-specific facts.
3. For site-specific information, request supporting documentation.
4. Be concise, technically accurate, and practical.
"""

            user_prompt = query

        result = await ollama_client.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=selected_model,
            temperature=0.2,
        )

        answer = (
            result.get("message", {}).get("content")
            if isinstance(result, dict)
            else str(result)
        )

        if not answer:
            raise RuntimeError("The local model returned an empty response.")

        return {
            "response": answer,
            "status": "success",
            "execution_steps": _add_step(
                state,
                "Final response generated using the local LLM.",
            ),
        }

    except Exception as exc:
        return {
            "status": "failed",
            "error": f"Response generation failed: {exc}",
            "execution_steps": _add_step(
                state,
                f"Response generation failed: {exc}",
            ),
        }


async def verification_node(state: AgentState) -> dict:
    """
    Performs a final workflow-level verification before returning results.
    """
    if state.get("status") == "failed":
        return {}

    task_type = state.get("task_type")

    if task_type == "analysis" and state.get("analysis_result") is None:
        return {
            "status": "failed",
            "error": "Analysis completed without producing a result.",
            "execution_steps": _add_step(
                state,
                "Verification failed: missing analysis result.",
            ),
        }

    if task_type == "document_question":
        if not state.get("citations") and state.get("retrieved_documents"):
            return {
                "status": "failed",
                "error": "Retrieved evidence has no usable citations.",
                "execution_steps": _add_step(
                    state,
                    "Verification failed: citations missing.",
                ),
            }

    return {
        "status": "success",
        "execution_steps": _add_step(
            state,
            "Workflow verification completed.",
        ),
    }