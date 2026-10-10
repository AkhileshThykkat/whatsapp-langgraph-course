"""Lesson 6: reducers. Some state fields are replaced; others accumulate.

A tiny loop with no tools, so the merge behaviour is the only thing to watch.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


# Simple why: Some notebook pages hold "the latest value"; others are a growing diary.
# Technical explanation: A plain annotation (int, str) uses the default reducer: the
# newest value replaces the old one. Annotated[list[str], operator.add] attaches a
# reducer, so LangGraph computes new = operator.add(old, update), i.e. old + update.
class LoopState(TypedDict):
    count: int                                  # replaced on every update
    last_node: str                              # replaced on every update
    trace: Annotated[list[str], operator.add]   # appended on every update


def start(state: LoopState) -> dict:
    # Simple why: Return only the NEW diary line, not the whole diary.
    # Technical explanation: For an operator.add field, a node returns a DELTA. LangGraph
    # appends it. Returning the whole list here would append old entries a second time.
    return {"last_node": "start", "trace": ["start: count is 0"]}


def tick(state: LoopState) -> dict:
    new_count = state["count"] + 1
    return {"count": new_count, "last_node": "tick", "trace": [f"tick: count {state['count']} -> {new_count}"]}


def route_after_tick(state: LoopState) -> str:
    return "again" if state["count"] < 3 else "done"


def build_graph():
    builder = StateGraph(LoopState)
    builder.add_node("start", start)
    builder.add_node("tick", tick)
    builder.add_edge(START, "start")
    builder.add_edge("start", "tick")
    builder.add_conditional_edges("tick", route_after_tick, {"again": "tick", "done": END})
    return builder.compile()


def main():
    graph = build_graph()
    initial_state = {"count": 0, "last_node": "none", "trace": ["input received"]}
    print("INPUT:", initial_state)

    # Simple why: Watch each node's own small change as it happens.
    # Technical explanation: stream_mode="updates" yields {node_name: returned_update}
    # after each step: the raw partial updates, BEFORE merging. Iterating the stream is
    # what drives execution; nothing runs until we loop over it.
    print("\n--- stream_mode='updates': what each node RETURNED ---")
    for step, chunk in enumerate(graph.stream(initial_state, stream_mode="updates"), start=1):
        print(f"step {step}:", chunk)

    # Simple why: Now watch the whole notebook after each step.
    # Technical explanation: stream_mode="values" yields the FULL accumulated state after
    # each step, i.e. after reducers ran. Compare 'trace' here with the deltas above.
    print("\n--- stream_mode='values': the whole state AFTER merging ---")
    for step, values in enumerate(graph.stream(initial_state, stream_mode="values")):
        print(f"after step {step}:", values)

    final_state = graph.invoke(initial_state)
    print("\nFINAL STATE:", final_state)
    print("trace has", len(final_state["trace"]), "entries; count was replaced, trace was appended.")


if __name__ == "__main__":
    main()
