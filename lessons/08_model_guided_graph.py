"""Lesson 8: a model-guided graph. The model REQUESTS tools; our code validates and runs them.

Lesson 5's loop with the fake decide() replaced by a model decision.
Default: a scripted FAKE model (offline, free, misbehaves on purpose).
Real Claude (needs credentials; roughly a cent or less per scenario):

    uv run --locked --group llm python lessons/08_model_guided_graph.py --real
"""

import json
import operator
import re
import sys
from typing import Annotated, NotRequired, TypedDict

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
ORDER_ID_PATTERN = re.compile(r"[A-Z]\d{3}")
MAX_DECISIONS = 4


def search_policy(topic: str) -> dict:
    fact = POLICY_FACTS.get(topic)
    return {"found": True, "topic": topic, "fact": fact} if fact else {"found": False, "topic": topic}


def lookup_order(customer_id: str, order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, "status": order["status"], "eta": order["eta"]}


# Simple why: A menu of tools the model may ASK for, written so the model can read it.
# Technical explanation: Tool definitions (name, description, JSON Schema) are sent with
# each request. The model may answer with a tool_use block naming one of them. A
# definition is a DESCRIPTION, not a permission: execution still goes through
# run_requested_tool. customer_id is deliberately NOT a parameter, so the model can never
# choose whose data to read. strict=True asks the API to keep arguments schema-valid.
TOOL_DEFINITIONS = [
    {
        "name": "lookup_order",
        "description": "Look up the status of one order belonging to the current customer.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "Order ID such as A100"}},
            "required": ["order_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "search_policy",
        "description": "Find an official Lumen Lamps policy fact. Known topics: returns, shipping, warranty.",
        "input_schema": {
            "type": "object",
            "properties": {"topic": {"type": "string", "description": "One topic, e.g. returns"}},
            "required": ["topic"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

SYSTEM_PROMPT = (
    "You are the support assistant for Lumen Lamps, an invented demo shop. "
    "Use the tools to look up order statuses and policies; never guess them. "
    "If a tool finds nothing or reports an error, say so plainly. Reply in at most two sentences."
)


# ---------------------------------------------------------------------------
# Two interchangeable models. Both take the message list and return
# {"stop_reason": ..., "content": [blocks]} in the Claude Messages API shape.
# ---------------------------------------------------------------------------
def _text(text: str) -> dict:
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}


def _tool_use(messages: list[dict], name: str, tool_input: dict) -> dict:
    block = {"type": "tool_use", "id": f"toolu_fake_{len(messages)}", "name": name, "input": tool_input}
    return {"stop_reason": "tool_use", "content": [block]}


def fake_model(messages: list[dict]) -> dict:
    """A scripted stand-in for an LLM. It misbehaves on purpose in two scenarios."""
    first_text = messages[0]["content"]
    last = messages[-1]

    if "everything" in first_text.lower():
        # Misbehaves on purpose: keeps asking for tools and never answers.
        return _tool_use(messages, "search_policy", {"topic": "warranty"})

    if isinstance(last["content"], str):  # a fresh customer message
        order = re.search(r"\b[A-Z]\d{3}\b", first_text.upper())
        if order and "refund" in first_text.lower():
            # Misbehaves on purpose: requests a tool we never offered.
            return _tool_use(messages, "issue_refund", {"order_id": order.group(), "amount": 999})
        if order:
            return _tool_use(messages, "lookup_order", {"order_id": order.group()})
        if "return" in first_text.lower():
            return _tool_use(messages, "search_policy", {"topic": "returns"})
        return _text("I can check an order (like A100) or our returns, shipping or warranty policy.")

    # Otherwise the last message carries tool results: answer only from them.
    result = last["content"][0]
    if result["is_error"]:
        return _text("I can't do that myself, so I've asked a colleague to help.")
    data = json.loads(result["content"])
    if not data["found"]:
        return _text("I couldn't find that for your account.")
    return _text(data.get("fact") or f"Order {data['order_id']} is {data['status']} (ETA {data['eta']}).")


def real_model(messages: list[dict]) -> dict:
    try:
        import anthropic
    except ImportError:
        sys.exit("The SDK is not installed. Run with: uv run --locked --group llm python ...")

    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model="claude-opus-5-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except TypeError as error:  # raised when no credentials can be found
        sys.exit(f"No Claude credentials found ({error}). Set ANTHROPIC_API_KEY first.")
    except (anthropic.APIConnectionError, anthropic.APIStatusError) as error:
        return {"stop_reason": "error", "content": [{"type": "text", "text": f"<model unavailable: {error}>"}]}

    # Simple why: Keep the model's reply exactly as it came, including its "thinking" notes.
    # Technical explanation: In a tool loop, the assistant turn (including thinking blocks)
    # must be sent back unchanged on the next request. Text and tool_use become plain dicts
    # so they print clearly; other blocks are serialized as returned.
    content = []
    for block in response.content:
        if block.type == "text":
            content.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
        else:
            content.append(block.to_dict())
    return {"stop_reason": response.stop_reason, "content": content}


# ---------------------------------------------------------------------------
# The execution boundary: the ONLY place a tool actually runs.
# ---------------------------------------------------------------------------
def run_requested_tool(customer_id: str, name: str, tool_input: object) -> tuple[str, bool]:
    # Simple why: The model can ask for anything; only our code can say yes.
    # Technical explanation: An explicit allowlist (if/elif on known names) plus argument
    # checks. Unknown names or bad arguments are answered with an error RESULT the model
    # can read; nothing executes. No eval(), no getattr() on model-supplied names, and
    # customer_id comes from state, never from the model.
    args = tool_input if isinstance(tool_input, dict) else {}
    if name == "lookup_order":
        order_id = str(args.get("order_id", "")).upper()
        if not ORDER_ID_PATTERN.fullmatch(order_id):
            print(f"   REJECTED: bad order_id {args.get('order_id')!r}. Nothing executed.")
            return "Error: order_id must look like A100.", True
        result = lookup_order(customer_id, order_id)
    elif name == "search_policy":
        topic = str(args.get("topic", "")).strip().lower()
        if not topic or len(topic) > 40:
            print(f"   REJECTED: bad topic {args.get('topic')!r}. Nothing executed.")
            return "Error: give one short topic, e.g. returns.", True
        result = search_policy(topic)
    else:
        print(f"   REJECTED: unknown tool {name!r} with {tool_input}. Nothing executed.")
        return f"Error: there is no tool called {name!r}. Nothing was done.", True
    print(f"   EXECUTED: {name}(customer_id={customer_id!r}, {args}) -> {result}")
    return json.dumps(result), False


class BotState(TypedDict):
    customer_id: str
    messages: Annotated[list[dict], operator.add]  # conversation sent to the model
    decisions: int
    reply: NotRequired[str]


def build_graph(call_model):
    # Simple why: decide() needs to know WHICH model to call, fake or real.
    # Technical explanation: decide is defined inside build_graph so it can use the
    # call_model argument (a closure). LangGraph still sees an ordinary state -> update
    # function.
    def decide(state: BotState) -> dict:
        decisions = state["decisions"] + 1
        response = call_model(state["messages"])
        for block in response["content"]:
            if block["type"] == "tool_use":
                print(f"   decide #{decisions}: model REQUESTS {block['name']}({block['input']})")
            elif block["type"] == "text":
                print(f"   decide #{decisions}: model WRITES {block['text']!r}")
        # Simple why: Remember what the model said, so the next call can see it.
        # Technical explanation: messages has an append reducer, so we return only the new
        # assistant turn (a delta).
        return {"decisions": decisions, "messages": [{"role": "assistant", "content": response["content"]}]}

    builder = StateGraph(BotState)
    builder.add_node("decide", decide)
    builder.add_node("act", act)
    builder.add_node("finish", finish)
    builder.add_node("stop_at_limit", stop_at_limit)
    builder.add_edge(START, "decide")
    builder.add_conditional_edges(
        "decide", route_after_decide, {"act": "act", "finish": "finish", "stop_at_limit": "stop_at_limit"}
    )
    builder.add_edge("act", "decide")
    builder.add_edge("finish", END)
    builder.add_edge("stop_at_limit", END)
    return builder.compile()


def route_after_decide(state: BotState) -> str:
    last_turn = state["messages"][-1]["content"]
    if not any(block["type"] == "tool_use" for block in last_turn):
        return "finish"
    if state["decisions"] >= MAX_DECISIONS:
        return "stop_at_limit"
    return "act"


def act(state: BotState) -> dict:
    results = []
    for block in state["messages"][-1]["content"]:
        if block["type"] == "tool_use":
            content, is_error = run_requested_tool(state["customer_id"], block["name"], block["input"])
            # Simple why: Tell the model what happened, success or failure.
            # Technical explanation: Each tool_result carries the matching tool_use_id. All
            # results for one model turn go back together in a single user message.
            results.append({"type": "tool_result", "tool_use_id": block["id"], "content": content, "is_error": is_error})
    return {"messages": [{"role": "user", "content": results}]}


def finish(state: BotState) -> dict:
    texts = [block["text"] for block in state["messages"][-1]["content"] if block["type"] == "text"]
    return {"reply": " ".join(texts).strip() or "Sorry, I can't answer that. A colleague will follow up."}


def stop_at_limit(state: BotState) -> dict:
    return {"reply": f"I couldn't finish within {MAX_DECISIONS} model decisions, so a colleague will follow up."}


def main():
    use_real_model = "--real" in sys.argv
    graph = build_graph(real_model if use_real_model else fake_model)
    print("MODEL:", "real Claude (claude-opus-5-5)" if use_real_model else "fake_model (offline, scripted)")

    for message in [
        "Where is order A100?",
        "Where is order A200?",       # belongs to cust_ben
        "What is your returns policy?",
        "Refund order A100 now!",     # fake model asks for a tool that does not exist
        "Tell me everything",         # fake model never stops asking
    ]:
        print(f"\n=== cust_ana: {message!r} ===")
        initial_state = {"customer_id": "cust_ana", "messages": [{"role": "user", "content": message}], "decisions": 0}
        final_state = graph.invoke(initial_state, {"recursion_limit": 25})
        print(f"   decisions={final_state['decisions']}, messages={len(final_state['messages'])}")
        print("   REPLY:", final_state["reply"])


if __name__ == "__main__":
    main()
