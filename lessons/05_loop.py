"""Lesson 5: a loop. decide -> act -> decide again, until done or a limit is reached.

The decision maker is a FAKE, deterministic policy (no LLM yet). Data is invented.
"""

import re
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

POLICY_FACTS = {
    "returns": "Unused lamps can be returned within 30 days of delivery for a full refund.",
    "shipping": "Standard shipping takes 3-5 business days; express takes 1-2 business days.",
    "warranty": "Every lamp has a 2-year warranty for electrical faults. Broken glass is not covered.",
}
ORDERS = {
    "A100": {"customer_id": "cust_ana", "status": "shipped", "eta": "14 October"},
    "A200": {"customer_id": "cust_ben", "status": "processing", "eta": "20 October"},
}
TOPIC_KEYWORDS = {"return": "returns", "refund": "returns", "ship": "shipping", "warranty": "warranty"}

# Simple why: A safety stop, so a confused bot cannot think forever.
# Technical explanation: Application-level hop counter. It bounds how many decisions
# (later: paid model calls) one message may trigger, and it gives a DEFINED outcome
# (stop_at_limit) instead of a crash.
MAX_DECISIONS = 4


def search_policy(topic: str) -> dict:
    fact = POLICY_FACTS.get(topic)
    return {"found": True, "topic": topic, "fact": fact} if fact else {"found": False, "topic": topic}


def lookup_order(customer_id: str, order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, "status": order["status"], "eta": order["eta"]}


class BotState(TypedDict):
    customer_id: str
    message: str
    decisions: int              # how many times decide has run
    observations: list[dict]    # every tool request + result seen so far
    next_action: NotRequired[dict]
    reply: NotRequired[str]


def actions_needed(message: str) -> list[dict]:
    """The fake policy's 'understanding': every lookup this message needs."""
    needed = [{"tool": "lookup_order", "order_id": m} for m in re.findall(r"\b[A-Z]\d{3}\b", message.upper())]
    for word, topic in TOPIC_KEYWORDS.items():
        action = {"tool": "search_policy", "topic": topic}
        if word in message.lower() and action not in needed:
            needed.append(action)
    return needed


def decide(state: BotState) -> dict:
    decisions = state["decisions"] + 1
    already_done = [obs["request"] for obs in state["observations"]]

    # Simple why: Look at what we've learned so far, then pick the next missing piece.
    # Technical explanation: The decision is a function of state, INCLUDING the
    # observations from previous trips around the loop. That feedback (observe -> decide
    # again) is what makes this a loop rather than a fixed path. It is deterministic
    # Python standing in for a model, so you can predict every step.
    next_action = {"tool": "finish"}
    for action in actions_needed(state["message"]):
        if action not in already_done:
            next_action = action
            break

    print(f"   decide #{decisions}: sees {len(already_done)} observation(s) -> next_action={next_action}")
    return {"decisions": decisions, "next_action": next_action}


def route_after_decide(state: BotState) -> str:
    # Simple why: Finished? Answer. Out of steps? Stop safely. Otherwise, go do the work.
    # Technical explanation: This router is where the loop either continues ("act" leads
    # back to decide) or exits. Checking the limit HERE means a tool never runs once the
    # budget is spent.
    if state["next_action"]["tool"] == "finish":
        return "respond"
    if state["decisions"] >= MAX_DECISIONS:
        return "stop_at_limit"
    return "act"


def act(state: BotState) -> dict:
    action = state["next_action"]
    if action["tool"] == "lookup_order":
        result = lookup_order(state["customer_id"], action["order_id"])
    else:
        result = search_policy(action["topic"])
    print(f"   act: ran {action['tool']} -> {result}")

    # Simple why: Add the new result to the list of things we've learned.
    # Technical explanation: 'observations' has no reducer, so a returned value REPLACES
    # the old list. That is why we return the old list plus the new item. Lesson 6 shows
    # an append reducer, where you return only the new item.
    return {"observations": state["observations"] + [{"request": action, "result": result}]}


def respond(state: BotState) -> dict:
    parts = []
    for obs in state["observations"]:
        result = obs["result"]
        if "order_id" in result:
            parts.append(f"Order {result['order_id']} is {result['status']}." if result["found"]
                         else f"I couldn't find order {result['order_id']} on your account.")
        else:
            parts.append(result["fact"] if result["found"] else f"No policy found for {result['topic']}.")
    reply = " ".join(parts) or "Ask me about an order (like A100) or our returns, shipping or warranty."
    return {"reply": reply}


def stop_at_limit(state: BotState) -> dict:
    return {"reply": f"I couldn't finish within {MAX_DECISIONS} steps, so a colleague will follow up."}


def build_graph():
    builder = StateGraph(BotState)
    for name, function in [("decide", decide), ("act", act), ("respond", respond), ("stop_at_limit", stop_at_limit)]:
        builder.add_node(name, function)

    builder.add_edge(START, "decide")
    builder.add_conditional_edges(
        "decide", route_after_decide, {"act": "act", "respond": "respond", "stop_at_limit": "stop_at_limit"}
    )

    # Simple why: After doing the work, go back and think again.
    # Technical explanation: This edge points BACKWARDS to an earlier node, which creates
    # a cycle. Only the router above can leave the cycle.
    builder.add_edge("act", "decide")

    builder.add_edge("respond", END)
    builder.add_edge("stop_at_limit", END)
    return builder.compile()


def main():
    graph = build_graph()

    for customer_id, message in [
        ("cust_ana", "Hi!"),
        ("cust_ana", "Where is A100?"),
        ("cust_ana", "Where is A100, and what is your returns policy?"),
        ("cust_ana", "Status of A100 and A200? Also shipping and warranty info please."),
    ]:
        print(f"\n=== {customer_id}: {message!r} ===")
        initial_state = {"customer_id": customer_id, "message": message, "decisions": 0, "observations": []}

        # Simple why: A second, framework-level safety net in case our own stop rule is broken.
        # Technical explanation: recursion_limit caps graph super-steps (each node run is
        # one step here). If it is hit, LangGraph raises GraphRecursionError. Unlike our
        # stop_at_limit, that is a crash, not a planned outcome.
        final_state = graph.invoke(initial_state, {"recursion_limit": 25})
        print("   decisions:", final_state["decisions"], "| observations:", len(final_state["observations"]))
        print("   REPLY:", final_state["reply"])


if __name__ == "__main__":
    main()
