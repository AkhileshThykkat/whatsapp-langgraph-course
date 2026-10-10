"""Lesson 4: tools. A node calls an ordinary fact-finding function and stores the result.

All shop facts, customers, and orders below are INVENTED for this course.
Still no LLM, loop, HTTP, or saved memory.
"""

import re
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

# ---------------------------------------------------------------------------
# Invented data for "Lumen Lamps", a shop that does not exist.
# ---------------------------------------------------------------------------
POLICY_FACTS = {
    "returns": "Unused lamps can be returned within 30 days of delivery for a full refund.",
    "shipping": "Standard shipping takes 3-5 business days; express takes 1-2 business days.",
    "warranty": "Every lamp has a 2-year warranty for electrical faults. Broken glass is not covered.",
}

ORDERS = {
    "A100": {"customer_id": "cust_ana", "status": "shipped", "eta": "14 October"},
    "A200": {"customer_id": "cust_ben", "status": "processing", "eta": "20 October"},
    "A300": {"customer_id": "cust_ana", "status": "delivered", "eta": None},
}


# ---------------------------------------------------------------------------
# Tools: ordinary Python functions. Nothing about them is LangGraph-specific.
# ---------------------------------------------------------------------------
def search_policy(topic: str) -> dict:
    # Simple why: Say clearly when we do not know, instead of guessing.
    # Technical explanation: The result always has 'found'. A missing fact is a normal,
    # explicit outcome (found=False), not an exception and not an invented answer.
    fact = POLICY_FACTS.get(topic)
    if fact is None:
        return {"found": False, "topic": topic}
    return {"found": True, "topic": topic, "fact": fact}


def lookup_order(customer_id: str, order_id: str) -> dict:
    order = ORDERS.get(order_id)

    # Simple why: You only get answers about your own orders.
    # Technical explanation: Ownership is checked INSIDE the tool, so no caller can skip it.
    # Missing and not-yours orders get the SAME answer, so guessing IDs does not reveal
    # which orders exist. The caller-supplied demo customer_id is NOT authentication; a
    # real system takes it from a verified identity, never from the message text.
    if order is None or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, "status": order["status"], "eta": order["eta"]}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class BotState(TypedDict):
    customer_id: str
    message: str
    tool_request: NotRequired[dict]  # what we WANT to run
    tool_result: NotRequired[dict]   # what actually came back
    reply: NotRequired[str]


TOPIC_KEYWORDS = {
    "return": "returns",
    "refund": "returns",
    "ship": "shipping",
    "deliver": "shipping",
    "warranty": "warranty",
    "price match": "price_match",  # a topic we recognise but have NO fact for
}


def plan_tool_call(state: BotState) -> dict:
    text = state["message"]

    # Simple why: Decide WHICH lookup we need, but do not do it yet.
    # Technical explanation: The request is plain data saved in state. Making a request and
    # executing it are separate steps; lesson 8 depends on keeping them apart.
    order_match = re.search(r"\b[A-Z]\d{3}\b", text.upper())
    if order_match:
        request = {"tool": "lookup_order", "order_id": order_match.group()}
    else:
        topic = next((t for word, t in TOPIC_KEYWORDS.items() if word in text.lower()), None)
        request = {"tool": "search_policy", "topic": topic} if topic else {"tool": "none"}

    print("   NODE plan_tool_call RETURNS:", {"tool_request": request})
    return {"tool_request": request}


def route_to_tool(state: BotState) -> str:
    return state["tool_request"]["tool"]


def run_order_tool(state: BotState) -> dict:
    request = state["tool_request"]

    # Simple why: The customer ID comes from who is asking, not from what they typed.
    # Technical explanation: customer_id is read from state, which the caller supplied.
    # The message can choose WHICH order to ask about, never WHOSE orders to search.
    result = lookup_order(state["customer_id"], request["order_id"])
    print(f"   TOOL lookup_order({state['customer_id']!r}, {request['order_id']!r}) ->", result)
    return {"tool_result": result}


def run_policy_tool(state: BotState) -> dict:
    result = search_policy(state["tool_request"]["topic"])
    print(f"   TOOL search_policy({state['tool_request']['topic']!r}) ->", result)
    return {"tool_result": result}


def write_reply(state: BotState) -> dict:
    result = state.get("tool_result")

    # Simple why: Only repeat what the tool actually said.
    # Technical explanation: The reply is built ONLY from tool_result fields. If no tool ran,
    # or the tool found nothing, the reply says so instead of inventing a status or policy.
    if result is None:
        reply = "I can help with an order (e.g. 'Where is A100?') or our returns/shipping/warranty policy."
    elif "order_id" in result and result["found"]:
        eta = f", expected {result['eta']}" if result["eta"] else ""
        reply = f"Order {result['order_id']} is {result['status']}{eta}."
    elif "order_id" in result:
        reply = f"I couldn't find order {result['order_id']} on your account."
    elif result["found"]:
        reply = result["fact"]
    else:
        reply = f"I don't have a policy about '{result['topic']}'. A colleague will follow up."

    print("   NODE write_reply RETURNS:", {"reply": reply})
    return {"reply": reply}


def build_graph():
    builder = StateGraph(BotState)
    builder.add_node("plan_tool_call", plan_tool_call)
    builder.add_node("run_order_tool", run_order_tool)
    builder.add_node("run_policy_tool", run_policy_tool)
    builder.add_node("write_reply", write_reply)

    builder.add_edge(START, "plan_tool_call")

    # Simple why: Go to the right lookup, or skip straight to replying.
    # Technical explanation: A branch can skip work. "none" routes directly to write_reply,
    # so no tool node runs and tool_result stays absent from state.
    builder.add_conditional_edges(
        "plan_tool_call",
        route_to_tool,
        {"lookup_order": "run_order_tool", "search_policy": "run_policy_tool", "none": "write_reply"},
    )
    builder.add_edge("run_order_tool", "write_reply")
    builder.add_edge("run_policy_tool", "write_reply")
    builder.add_edge("write_reply", END)
    return builder.compile()


def main():
    graph = build_graph()

    scenarios = [
        ("cust_ana", "Where is order A100?"),        # Ana's own order
        ("cust_ana", "Where is order A200?"),        # Ben's order: must be refused
        ("cust_ben", "Where is order A200?"),        # Ben's own order
        ("cust_ana", "Can I return my lamp?"),       # policy fact exists
        ("cust_ana", "Do you price match?"),         # recognised topic, NO fact
        ("cust_ana", "Hello"),                       # no tool at all
    ]
    for customer_id, message in scenarios:
        print(f"\n=== {customer_id}: {message!r} ===")
        final_state = graph.invoke({"customer_id": customer_id, "message": message})
        print("   FINAL STATE:", final_state)


if __name__ == "__main__":
    main()
