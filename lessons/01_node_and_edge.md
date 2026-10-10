# Lesson 1: intuitively build a node and an edge

Read `01_node_and_edge.py`. The whole example is one route:

```text
START → make_reply → END
```

There is no AI yet. That is deliberate: first see what the graph runtime does.

## The working notebook: state

**Simple why:** The steps need somewhere to read the message and put their results.

**Technical explanation:** `BotState` declares named state channels with `TypedDict`.
Initially we provide only `message`. `reply` is `NotRequired` because the node has not
created it yet. These annotations describe the schema; they are not runtime input
validation. There is no checkpointer, so this state is not saved conversation memory.

## The stop where work happens: node

**Simple why:** A node is a function that does one piece of work on the notebook.

**Technical explanation:** `make_reply(state)` receives the current graph state and
returns `{"reply": ...}`. That is a **partial update**, not the entire state.
LangGraph retains keys absent from the update and replaces updated keys by default.
This function formats a string; it does not call a language model.

`add_node("make_reply", make_reply)` registers a name and a callable. Notice the
second argument has no parentheses. We give LangGraph the function to call later;
we do not call it while constructing the graph.

## The road: edge

**Simple why:** Naming the stops does not tell a message where to go. Roads do that.

**Technical explanation:** `add_edge(START, "make_reply")` establishes the entry path.
`add_edge("make_reply", END)` establishes termination after that node. These are
fixed directed edges. START and END are special markers, not functions. Node names
must match registered names. Branches and loops come later.

## Drawing vs running

**Simple why:** A route drawing and a journey along it are different things.

**Technical explanation:** `StateGraph(...)` is the builder. `compile()` checks wiring
and produces an executable graph, without running the node. `invoke(initial_state)`
executes it and returns accumulated state when the route finishes. Compilation alone
does not train anything, add intelligence, or persist the conversation.

## Predict before running

The input is `{"message": "Hello"}`. Write down your predictions:

1. What does `make_reply` receive?
2. What dictionary does it return?
3. Will the final dictionary still contain `message`? Why?
4. Is the node's returned dictionary identical to the final dictionary?

Then run:

```bash
uv run --locked python lessons/01_node_and_edge.py
```

Compare the four print statements. Their numbering exposes input → node input → node
update → final state. Do not treat the output as model-generated text.

## Your experiments — the assistant should guide, not do these for you

### Experiment A: change the input

Change `"Hello"` to a different message. Predict which printed values will change,
then run it. Does changing input change the graph's route?

### Experiment B: change one update

Change the reply text in the node. Predict whether the original message will disappear
from final state. Explain the difference between an omitted key and a key overwritten
with a new value.

### Experiment C: add a second stop

Write a small ordinary function that receives state, prints it, and returns another
update to `reply`. Register it under a new node name, then wire:

```text
START → make_reply → your_new_node → END
```

Replace the existing edge from `make_reply` to END; do not leave it as an unintended
additional road. Print what the second node receives. Can it see the first node's reply?
Which reply is in final state? Explain before introducing reducers or parallel paths.

## Review checkpoint

Bring your modified script or printed output to the teaching agent. Explain:

> How can a node return only `reply`, while the final state still contains `message`?

If that is unclear, stay here and trace the dictionaries together. Do not move to
conditional routing, a real LLM, or a webhook until this mechanism makes sense.

Official reference: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).
