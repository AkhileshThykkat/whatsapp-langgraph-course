"""Lesson 2: a path of three nodes. Each node contributes a DIFFERENT state field.

Still no LLM, tools, branches, HTTP, or saved memory.
"""

from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph


# Simple why: The notebook now has one page per step, so we can see who wrote what.
# Technical explanation: Each NotRequired key is written by exactly one node. Before that
# node runs, the key is absent from state, so reading it too early raises KeyError.
class BotState(TypedDict):
    message: str
    cleaned: NotRequired[str]
    intent: NotRequired[str]
    reply: NotRequired[str]


def clean_message(state: BotState) -> dict:
    print("   clean_message RECEIVED:", state)

    # Simple why: Tidy the text once so later steps do not each have to.
    # Technical explanation: We write a NEW key instead of overwriting 'message', so the
    # customer's original words stay available for later steps and for debugging.
    update = {"cleaned": state["message"].strip().lower()}
    print("   clean_message RETURNS: ", update)
    return update


def guess_intent(state: BotState) -> dict:
    print("   guess_intent RECEIVED: ", state)
    text = state["cleaned"]

    # Simple why: A few keyword rules stand in for "understanding" for now.
    # Technical explanation: Deterministic substring checks, not language understanding or
    # a model. They are easy to predict, which is the point. The first matching rule wins.
    if "order" in text:
        intent = "order_status"
    elif "return" in text or "refund" in text:
        intent = "returns_policy"
    elif text.startswith(("hi", "hello", "hey")):
        intent = "greeting"
    else:
        intent = "unknown"

    update = {"intent": intent}
    print("   guess_intent RETURNS:  ", update)
    return update


def write_reply(state: BotState) -> dict:
    print("   write_reply RECEIVED:  ", state)

    # Simple why: The last step uses what the earlier steps wrote down.
    # Technical explanation: Every intent gets the same formatting. Choosing a different
    # node per intent is lesson 3 (a conditional edge); here the route never changes.
    update = {"reply": f"(intent={state['intent']}) I received: {state['message']}"}
    print("   write_reply RETURNS:   ", update)
    return update


def build_graph():
    builder = StateGraph(BotState)
    builder.add_node("clean_message", clean_message)
    builder.add_node("guess_intent", guess_intent)
    builder.add_node("write_reply", write_reply)

    # Simple why: The roads fix the order of the stops.
    # Technical explanation: Each fixed edge schedules exactly one next node. Because each
    # node runs in its own step, the next node receives state that already includes the
    # previous node's update. The order of these add_edge calls in the file does not matter;
    # the source/destination pairs do.
    builder.add_edge(START, "clean_message")
    builder.add_edge("clean_message", "guess_intent")
    builder.add_edge("guess_intent", "write_reply")
    builder.add_edge("write_reply", END)
    return builder.compile()


def main():
    graph = build_graph()

    for message in ["  Where is my ORDER?  ", "Hello there"]:
        print(f"\n=== Running with message {message!r} ===")
        initial_state = {"message": message}
        print("1. INPUT:      ", initial_state)
        final_state = graph.invoke(initial_state)
        print("2. FINAL STATE:", final_state)


if __name__ == "__main__":
    main()
