from datetime import date
from typing import TypedDict

from langgraph.graph import END, StateGraph

from .llm import extract_action_items
from .models import Priority


class ExtractionState(TypedDict):
    transcript: str
    raw_items: list[dict]
    items: list[dict]


def _extract(state: ExtractionState) -> ExtractionState:
    state["raw_items"] = extract_action_items(state["transcript"])
    return state


def _normalize(state: ExtractionState) -> ExtractionState:
    cleaned = []
    for item in state["raw_items"]:
        description = (item.get("description") or "").strip()
        if not description:
            continue

        priority = item.get("priority")
        if priority not in (p.value for p in Priority):
            priority = Priority.medium.value

        deadline = item.get("deadline") or None
        if deadline:
            try:
                date.fromisoformat(deadline)
            except ValueError:
                deadline = None

        cleaned.append(
            {
                "description": description,
                "owner": item.get("owner") or None,
                "deadline": deadline,
                "priority": priority,
            }
        )
    state["items"] = cleaned
    return state


def build_extraction_graph():
    graph = StateGraph(ExtractionState)
    graph.add_node("extract", _extract)
    graph.add_node("normalize", _normalize)
    graph.set_entry_point("extract")
    graph.add_edge("extract", "normalize")
    graph.add_edge("normalize", END)
    return graph.compile()


extraction_graph = build_extraction_graph()


def run_extraction(transcript: str) -> list[dict]:
    result = extraction_graph.invoke({"transcript": transcript, "raw_items": [], "items": []})
    return result["items"]
