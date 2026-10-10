"""Lesson 9: memory. A checkpointer saves state per thread_id between invoke() calls.

Deterministic bot (no LLM) so that memory is the only new thing. Data is invented.
"""

import operator
import re
from typing import Annotated, NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

ORDERS = {
    "A100": {"customer_id": "cust_ana", "status": "shipped", "eta": "14 October"},
    "A200": {"customer_id": "cust_ben", "status": "processing", "eta": "20 October"},
}


def lookup_order(customer_id: str, order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, "status": order["status"], "eta": order["eta"]}


# Simple why: Some pages are about the whole conversation; others are only about this message.
# Technical explanation: With a checkpointer, EVERY key is saved after each step and
# loaded again on the next invoke for the same thread_id. "Per-turn" is not a LangGraph
# concept: you must reset those keys yourself, or old values leak into the next turn.
class ChatState(TypedDict):
    customer_id: str                              # supplied by the caller every turn
    message: str                                  # this turn's input (replaced each turn)
    history: Annotated[list[str], operator.add]   # conversation-long: grows every turn
    last_order_id: NotRequired[str]               # conversation-long: what "it" refers to
    tool_result: NotRequired[dict | None]         # PER-TURN: must not leak into the next turn
    reply: NotRequired[str]                       # per-turn output


def start_turn(state: ChatState) -> dict:
    print("   start_turn LOADED:", {k: v for k, v in state.items() if k != "history"},
          f"(history has {len(state.get('history', []))} lines)")

    # Simple why: Wipe this-message-only notes before handling a new message.
    # Technical explanation: Setting tool_result to None replaces the saved value from the
    # previous turn. (An append field could NOT be cleared this way; see lesson 6.)
    return {"tool_result": None, "history": [f"customer: {state['message']}"]}


def maybe_lookup(state: ChatState) -> dict:
    match = re.search(r"\b[A-Z]\d{3}\b", state["message"].upper())

    # Simple why: "When will it arrive?" means the order we talked about before.
    # Technical explanation: last_order_id survives between turns because the checkpointer
    # restored it. Without a checkpointer it would be gone after every invoke().
    if match:
        order_id = match.group()
    elif "it" in state["message"].lower().split() and state.get("last_order_id"):
        order_id = state["last_order_id"]
    else:
        return {}

    result = lookup_order(state["customer_id"], order_id)
    print(f"   maybe_lookup: lookup_order({state['customer_id']!r}, {order_id!r}) -> {result}")
    return {"tool_result": result, "last_order_id": order_id}


def write_reply(state: ChatState) -> dict:
    result = state.get("tool_result")
    if result and result["found"]:
        reply = f"Order {result['order_id']} is {result['status']}, ETA {result['eta']}."
    elif result:
        reply = f"I couldn't find order {result['order_id']} on your account."
    elif "thank" in state["message"].lower():
        reply = "You're welcome!"
    else:
        reply = "Which order do you mean? Please include its ID, like A100."
    return {"reply": reply, "history": [f"bot: {reply}"]}


def build_graph(checkpointer):
    builder = StateGraph(ChatState)
    builder.add_node("start_turn", start_turn)
    builder.add_node("maybe_lookup", maybe_lookup)
    builder.add_node("write_reply", write_reply)
    builder.add_edge(START, "start_turn")
    builder.add_edge("start_turn", "maybe_lookup")
    builder.add_edge("maybe_lookup", "write_reply")
    builder.add_edge("write_reply", END)

    # Simple why: Give the graph a filing cabinet for saved conversations.
    # Technical explanation: compile(checkpointer=...) makes LangGraph save a state snapshot
    # (a checkpoint) after every step, filed under config["configurable"]["thread_id"].
    return builder.compile(checkpointer=checkpointer)


def send(graph, thread_id: str, customer_id: str, message: str) -> None:
    # Simple why: The thread_id says which saved conversation to reopen.
    # Technical explanation: The same thread_id loads the latest checkpoint and continues
    # it; a new thread_id starts from empty state. thread_id, customer_id and (later) the
    # inbound message ID are three DIFFERENT identities, and none of them is authentication.
    config = {"configurable": {"thread_id": thread_id}}
    print(f"\n>>> thread={thread_id!r} customer={customer_id!r}: {message!r}")
    final_state = graph.invoke({"customer_id": customer_id, "message": message}, config)
    print("   REPLY:", final_state["reply"])


def main():
    checkpointer = InMemorySaver()
    graph = build_graph(checkpointer)

    send(graph, "chat-ana", "cust_ana", "Where is order A100?")
    send(graph, "chat-ana", "cust_ana", "When will it arrive?")   # 'it' = A100, from memory
    send(graph, "chat-ben", "cust_ben", "When will it arrive?")   # Ben's thread knows nothing
    send(graph, "chat-ana", "cust_ana", "Thanks!")                # no lookup this turn

    print("\n=== Saved state for chat-ana ===")
    saved = graph.get_state({"configurable": {"thread_id": "chat-ana"}})
    for line in saved.values["history"]:
        print("  ", line)

    # Simple why: InMemorySaver lives in RAM; a restart forgets everything.
    # Technical explanation: A new InMemorySaver is empty, exactly like a restarted
    # process. Durable savers (SQLite, Postgres) are separate packages, not used here.
    print("\n=== Simulated restart: new process, new InMemorySaver ===")
    restarted_graph = build_graph(InMemorySaver())
    send(restarted_graph, "chat-ana", "cust_ana", "When will it arrive?")


if __name__ == "__main__":
    main()
