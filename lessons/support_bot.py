"""Lesson 12: the support bot, assembled from lessons 4-9 and written so it can be TESTED.

    uv run --locked python lessons/support_bot.py    # short demo
    uv run --locked pytest lessons -q                # the tests in test_support_bot.py

The "model" is any function: view -> decision. Decisions use a simplified version of
lesson 8's tool requests, so tests stay readable:

    {"action": "lookup_order", "args": {"order_id": "A100"}}
    {"action": "search_policy", "args": {"topic": "returns"}}
    {"action": "reply", "text": "..."}
    {"action": "handoff", "reason": "..."}

All shop data is invented.
"""

import operator
import re
from typing import Annotated, NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

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
ORDER_ID_PATTERN = re.compile(r"[A-Z]\d{3}")


# --- Tools (lesson 4) --------------------------------------------------------
def search_policy(topic: str) -> dict:
    fact = POLICY_FACTS.get(topic)
    return {"found": True, "topic": topic, "fact": fact} if fact else {"found": False, "topic": topic}


def lookup_order(customer_id: str, order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, "status": order["status"], "eta": order["eta"]}


# --- The execution boundary (lesson 8) ---------------------------------------
def execute_action(customer_id: str, decision: object) -> dict:
    """Validate one decision and run the tool it names. ALWAYS returns an observation."""
    action = decision.get("action") if isinstance(decision, dict) else None
    args = decision.get("args") if isinstance(decision, dict) and isinstance(decision.get("args"), dict) else {}

    # Simple why: A broken tool should lead to a polite answer, not a crashed bot.
    # Technical explanation: Exceptions from tools are caught HERE, at the boundary, and
    # turned into an observation with status "error". The error type is recorded, not the
    # message or a traceback, which could leak internals to the model or the customer.
    try:
        if action == "lookup_order":
            order_id = str(args.get("order_id", "")).upper()
            if not ORDER_ID_PATTERN.fullmatch(order_id):
                return {"action": action, "status": "rejected", "detail": "order_id must look like A100"}
            result = lookup_order(customer_id, order_id)
        elif action == "search_policy":
            topic = str(args.get("topic", "")).strip().lower()
            if not topic or len(topic) > 40:
                return {"action": action, "status": "rejected", "detail": "topic must be one short word"}
            result = search_policy(topic)
        else:
            return {"action": action, "status": "rejected", "detail": "not an allowed action"}
    except Exception as error:
        return {"action": action, "status": "error", "detail": type(error).__name__}
    return {"action": action, "status": "ok", "result": result}


# --- State (lessons 6 and 9) ------------------------------------------------------
class BotState(TypedDict):
    customer_id: str
    message: str
    history: Annotated[list[str], operator.add]  # conversation-long (append)
    decisions: int                               # per-turn
    observations: list[dict]                     # per-turn (replace, so it can be reset)
    pending: NotRequired[dict | None]            # per-turn: latest decision
    reply: NotRequired[str]
    outcome: NotRequired[str | None]             # per-turn: answered | handoff | step_limit


def build_graph(model, checkpointer=None, max_decisions: int = 4):
    # Simple why: Pass the "brain" in, so tests can swap in a predictable one.
    # Technical explanation: The model is an ordinary function argument (not a framework
    # feature). Tests pass scripted fakes; the demo passes keyword_model; lesson 8 shows
    # how a real Claude adapter would produce the same kind of decision.
    def start_turn(state: BotState) -> dict:
        return {"decisions": 0, "observations": [], "pending": None, "outcome": None,
                "history": [f"customer: {state['message']}"]}

    def decide(state: BotState) -> dict:
        view = {"message": state["message"], "history": state["history"], "observations": state["observations"]}
        return {"decisions": state["decisions"] + 1, "pending": model(view)}

    def route_after_decide(state: BotState) -> str:
        decision = state["pending"] if isinstance(state["pending"], dict) else {}
        text = decision.get("text")
        if decision.get("action") == "reply" and isinstance(text, str) and text.strip():
            return "reply"
        if decision.get("action") == "handoff":
            return "handoff"
        if state["decisions"] >= max_decisions:
            return "step_limit"
        return "act"  # tools AND malformed decisions go through the boundary

    def act(state: BotState) -> dict:
        observation = execute_action(state["customer_id"], state["pending"])
        return {"observations": state["observations"] + [observation]}

    def reply(state: BotState) -> dict:
        text = state["pending"]["text"].strip()
        return {"reply": text, "outcome": "answered", "history": [f"bot: {text}"]}

    def handoff(state: BotState) -> dict:
        text = "I've passed this to a colleague, who will follow up."
        return {"reply": text, "outcome": "handoff", "history": [f"bot: {text}"]}

    def step_limit(state: BotState) -> dict:
        text = "I couldn't finish this safely, so a colleague will follow up."
        return {"reply": text, "outcome": "step_limit", "history": [f"bot: {text}"]}

    builder = StateGraph(BotState)
    for name, function in [("start_turn", start_turn), ("decide", decide), ("act", act),
                           ("reply", reply), ("handoff", handoff), ("step_limit", step_limit)]:
        builder.add_node(name, function)
    builder.add_edge(START, "start_turn")
    builder.add_edge("start_turn", "decide")
    builder.add_conditional_edges("decide", route_after_decide,
                                  {"act": "act", "reply": "reply", "handoff": "handoff", "step_limit": "step_limit"})
    builder.add_edge("act", "decide")
    for terminal in ["reply", "handoff", "step_limit"]:
        builder.add_edge(terminal, END)
    return builder.compile(checkpointer=checkpointer)


def run_turn(graph, customer_id: str, message: str, thread_id: str = "default") -> dict:
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}
    return graph.invoke({"customer_id": customer_id, "message": message}, config)


# --- A deterministic stand-in model for the demo -----------------------------
def keyword_model(view: dict) -> dict:
    observations = view["observations"]
    if observations:
        last = observations[-1]
        if last["status"] != "ok":
            return {"action": "handoff", "reason": last["detail"]}
        result = last["result"]
        if not result["found"]:
            return {"action": "reply", "text": "I couldn't find that for your account."}
        return {"action": "reply", "text": result.get("fact") or f"Order {result['order_id']} is {result['status']}."}

    match = re.search(r"\b[A-Z]\d{3}\b", view["message"].upper())
    if match:
        return {"action": "lookup_order", "args": {"order_id": match.group()}}
    if "return" in view["message"].lower():
        return {"action": "search_policy", "args": {"topic": "returns"}}
    if "thank" in view["message"].lower():
        return {"action": "reply", "text": "You're welcome!"}
    return {"action": "reply", "text": "I can check an order (like A100) or our returns policy."}


def main():
    graph = build_graph(keyword_model, checkpointer=InMemorySaver())
    for customer_id, message in [("cust_ana", "Where is A100?"), ("cust_ana", "And A200?"),
                                 ("cust_ana", "Can I return it?"), ("cust_ana", "Thanks")]:
        state = run_turn(graph, customer_id, message, thread_id="demo-ana")
        print(f"{message!r:22} -> outcome={state['outcome']:9} observations={len(state['observations'])} "
              f"reply={state['reply']!r}")


if __name__ == "__main__":
    main()
