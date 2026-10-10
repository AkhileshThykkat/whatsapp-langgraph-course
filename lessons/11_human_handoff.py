"""Lesson 11: waiting for a human. interrupt() PAUSES a run; Command(resume=...) continues it.

Deterministic, local, invented data. The "support team notification" only prints.
"""

from typing import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

NOTIFICATIONS_SENT = []  # pretend outbox, so we can count side effects


def notify_support_team(customer_id: str, message: str) -> None:
    # Simple why: Stands in for "send an alert to the human team".
    # Technical explanation: A side effect: it changes something outside graph state. Here
    # it appends to a list and prints; a real one might send a Slack message or email.
    NOTIFICATIONS_SENT.append((customer_id, message))
    print(f"   SIDE EFFECT: notified support team (notification #{len(NOTIFICATIONS_SENT)})")


class HandoffState(TypedDict):
    customer_id: str
    message: str
    needs_human: NotRequired[bool]
    reply: NotRequired[str]


def triage(state: HandoffState) -> dict:
    text = state["message"].lower()
    needs_human = "refund" in text or "human" in text
    print("   triage RETURNS:", {"needs_human": needs_human})
    return {"needs_human": needs_human}


def route_after_triage(state: HandoffState) -> str:
    return "handoff" if state["needs_human"] else "auto_reply"


def auto_reply(state: HandoffState) -> dict:
    return {"reply": "Thanks! Ask about an order (like A100) or our policies."}


def handoff(state: HandoffState) -> dict:
    print("   handoff: node STARTED")

    # Deliberately placed BEFORE interrupt() so you can see the replay problem.
    notify_support_team(state["customer_id"], state["message"])

    # Simple why: Stop here and wait. The run is saved, not finished.
    # Technical explanation: interrupt(payload) raises a special signal that LangGraph
    # catches. It saves a checkpoint, and invoke() returns with '__interrupt__' in the
    # result. On resume, this node runs AGAIN FROM ITS FIRST LINE, and this time
    # interrupt() returns the resume value instead of pausing.
    human_decision = interrupt({"question": "How should we answer?", "customer_message": state["message"]})

    print("   handoff: RESUMED with human_decision =", repr(human_decision))
    return {"reply": f"A support colleague says: {human_decision}"}


def build_graph():
    builder = StateGraph(HandoffState)
    builder.add_node("triage", triage)
    builder.add_node("auto_reply", auto_reply)
    builder.add_node("handoff", handoff)
    builder.add_edge(START, "triage")
    builder.add_conditional_edges("triage", route_after_triage, {"handoff": "handoff", "auto_reply": "auto_reply"})
    builder.add_edge("auto_reply", END)
    builder.add_edge("handoff", END)

    # Simple why: Pausing only works if there is somewhere to save the paused run.
    # Technical explanation: interrupt() requires a checkpointer and a thread_id. The
    # paused state lives in the checkpointer until someone resumes that thread.
    return builder.compile(checkpointer=InMemorySaver())


def show_status(graph, config: dict, label: str) -> None:
    snapshot = graph.get_state(config)
    status = f"PAUSED, will resume at {snapshot.next}" if snapshot.next else "FINISHED (reached END)"
    print(f"   [{label}] status: {status}")


def main():
    graph = build_graph()

    print("=== A. Normal message: runs to END ===")
    config_a = {"configurable": {"thread_id": "thread-a"}}
    result = graph.invoke({"customer_id": "cust_ana", "message": "Hello"}, config_a)
    print("   invoke RETURNED:", result)
    show_status(graph, config_a, "thread-a")

    print("\n=== B. Refund request: pauses for a human ===")
    config_b = {"configurable": {"thread_id": "thread-b"}}
    result = graph.invoke({"customer_id": "cust_ben", "message": "I want a refund for A200"}, config_b)
    print("   invoke RETURNED:", result)
    print("   'reply' in result?", "reply" in result)
    show_status(graph, config_b, "thread-b")

    print("\n   ... time passes; a human reads the question and decides ...\n")

    # Simple why: Hand the human's answer back to the paused run.
    # Technical explanation: Command(resume=value) with the SAME thread_id loads the paused
    # checkpoint and re-runs the interrupted node; interrupt() now returns 'value'.
    result = graph.invoke(Command(resume="Approved: refund issued for A200."), config_b)
    print("   invoke RETURNED:", result)
    show_status(graph, config_b, "thread-b")

    print(f"\nNotifications sent for ONE handoff: {len(NOTIFICATIONS_SENT)}  <- why not 1?")


if __name__ == "__main__":
    main()
