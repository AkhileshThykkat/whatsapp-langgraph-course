"""Lesson 1: one node, two edges. No LLM, tools, HTTP, or saved memory."""

from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph


# Simple why: Write down what can be in our shared notebook.
# Technical explanation: TypedDict defines state keys for type tooling and LangGraph
# channels. It does NOT validate values at runtime. 'reply' is absent until our node runs.
class BotState(TypedDict):
    message: str
    reply: NotRequired[str]


def make_reply(state: BotState) -> dict:
    print("2. NODE RECEIVED:", state)

    # Simple why: This step adds an answer without rewriting the customer's message.
    # Technical explanation: A node returns a partial state update. LangGraph keeps
    # omitted keys and replaces updated keys by default; this function generates no AI text.
    update = {"reply": f"Demo reply to: {state['message']}"}
    print("3. NODE RETURNS: ", update)
    return update


def main():
    # Simple why: First draw the route; drawing it does not send anyone down it.
    # Technical explanation: StateGraph is a builder for nodes, edges, and state channels.
    builder = StateGraph(BotState)

    # Simple why: Give this stop a name and say which function does its work.
    # Technical explanation: 'make_reply' is the registered node ID; make_reply without
    # parentheses is a callable. LangGraph calls it later with the current state.
    builder.add_node("make_reply", make_reply)

    # Simple why: Enter at our stop, then finish after it has done its work.
    # Technical explanation: Fixed directed edges schedule the next destination.
    # START and END are special graph markers, not Python functions or model calls.
    builder.add_edge(START, "make_reply")
    builder.add_edge("make_reply", END)

    # Simple why: Turn the route drawing into a machine we can run.
    # Technical explanation: compile() checks wiring and creates an executable graph.
    # It does not execute the node, train a model, or save conversation history.
    graph = builder.compile()

    initial_state = {"message": "Hello"}
    print("1. INPUT:        ", initial_state)

    # Simple why: Now send one message through the route and inspect the result.
    # Technical explanation: invoke() starts an execution, applies the node's update
    # to state, follows the edge to END, and returns the final accumulated state.
    final_state = graph.invoke(initial_state)
    print("4. FINAL STATE:  ", final_state)


if __name__ == "__main__":
    main()
