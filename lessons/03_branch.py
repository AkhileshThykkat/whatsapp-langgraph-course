"""Lesson 3: a branch. A conditional edge chooses ONE road after guess_intent.

Still no LLM, tools, HTTP, or saved memory. Replies are fixed strings.
"""

from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph


class BotState(TypedDict):
    message: str
    intent: NotRequired[str]
    reply: NotRequired[str]


def guess_intent(state: BotState) -> dict:
    text = state["message"].strip().lower()
    if "order" in text:
        intent = "order_status"
    elif "return" in text or "refund" in text:
        intent = "returns_policy"
    elif text.startswith(("hi", "hello", "hey")):
        intent = "greeting"
    else:
        intent = "unknown"
    update = {"intent": intent}
    print("   NODE guess_intent RETURNS:", update)
    return update


# Simple why: The router looks at the notebook and points to a road. It writes nothing.
# Technical explanation: A conditional-edge function receives state and returns a routing
# key (here a string). LangGraph looks the key up in path_map to find the next node.
# The router's return value is NOT merged into state. That makes it different from a
# node, whose returned dictionary IS merged.
def route_by_intent(state: BotState) -> str:
    key = state["intent"]
    print("   ROUTER route_by_intent RECEIVED:", state)
    print("   ROUTER route_by_intent RETURNS: ", repr(key), "(a road name, not a state update)")
    return key


def greet(state: BotState) -> dict:
    print("   NODE greet RAN")
    return {"reply": "Hello! Ask me about an order or about returns."}


def order_help(state: BotState) -> dict:
    print("   NODE order_help RAN")
    # Simple why: Be honest; we cannot look anything up yet.
    # Technical explanation: No tool exists until lesson 4. Inventing a status here would
    # be exactly the ungrounded answer we later want the bot to avoid.
    return {"reply": "I can't look up orders yet. That arrives in lesson 4."}


def returns_help(state: BotState) -> dict:
    print("   NODE returns_help RAN")
    return {"reply": "Returns questions will be answered from invented policy facts in lesson 4."}


def fallback(state: BotState) -> dict:
    print("   NODE fallback RAN")
    return {"reply": "Sorry, I did not understand. A human colleague can help."}


def build_graph():
    builder = StateGraph(BotState)
    builder.add_node("guess_intent", guess_intent)
    builder.add_node("greet", greet)
    builder.add_node("order_help", order_help)
    builder.add_node("returns_help", returns_help)
    builder.add_node("fallback", fallback)

    builder.add_edge(START, "guess_intent")

    # Simple why: At this junction, follow the sign the router points to.
    # Technical explanation: add_conditional_edges(source, router, path_map). After
    # 'guess_intent' finishes, LangGraph calls the router with current state and schedules
    # path_map[router_result]. Only that one destination runs; the others are skipped.
    # path_map also tells LangGraph every possible destination when it compiles the graph.
    builder.add_conditional_edges(
        "guess_intent",
        route_by_intent,
        {
            "greeting": "greet",
            "order_status": "order_help",
            "returns_policy": "returns_help",
            "unknown": "fallback",
        },
    )

    # Simple why: Every road ends at the exit.
    # Technical explanation: Each branch needs its own path to END. Without one, a branch
    # node would have nowhere to go after it runs.
    for branch_node in ["greet", "order_help", "returns_help", "fallback"]:
        builder.add_edge(branch_node, END)

    return builder.compile()


def main():
    graph = build_graph()

    for message in ["Hello!", "Where is my order?", "Can I return a lamp?", "Do you sell bulbs?"]:
        print(f"\n=== {message!r} ===")
        final_state = graph.invoke({"message": message})
        print("   FINAL STATE:", final_state)


if __name__ == "__main__":
    main()
