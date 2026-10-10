# Lesson 3: a branch

```text
                      ┌─ "greeting"       → greet        ─┐
START → guess_intent ─┼─ "order_status"   → order_help   ─┼→ END
          (node)      ├─ "returns_policy" → returns_help ─┤
                      └─ "unknown"        → fallback     ─┘
                 route_by_intent (router; not a node)
```

**New idea:** a **conditional edge** picks one road based on the current state.

## Three different kinds of return value

This lesson is the first time three different things come back from your functions.
Keep them apart:

| Function | Returns | What LangGraph does with it |
|---|---|---|
| `guess_intent` (node) | `{"intent": "order_status"}` | **Merges** it into state |
| `route_by_intent` (router) | `"order_status"` | **Looks it up** in `path_map` to pick the next node; state is unchanged |
| `graph.invoke(...)` | the whole final state | Hands it back to *your* code |

**Simple why:** A node writes in the notebook. A router only points at a road.

**Technical explanation:** The node's dictionary is a partial state update. The router's
return value is a routing key that `add_conditional_edges` maps to a destination node.
It is never written to state. That is why the final state contains `intent` (written by
a node) but nothing that records the router's decision.

## Why is the decision in a node *and* a router?

**Simple why:** One step decides and writes down the decision. The junction only reads it.

**Technical explanation:** Keeping classification in a node means the decision is saved
in state, where prints, traces, and later tests can see it. The router stays a tiny pure
function. You *can* put the classification logic directly inside a router, but then the
decision is not recorded in state.

## Why not one `write_reply` node with `if/else` inside?

You could do that, and for tiny cases it is fine. **A branch inside a node** hides the
choice inside Python code. **A branch between nodes** makes the route part of the graph,
so you can see exactly which node ran. Later the branches will do different *work*
(look up an order, search policy, hand off to a human), not just print different text.

## Predict before running

1. For `"Can I return a lamp?"`, which nodes print `RAN`? Which nodes never run at all?
2. What does the router receive? What does it return? Is that return value in the final state?
3. **Tricky case:** what happens for `"Hi, where is my order?"`? Which rule wins, and why?
4. Does the final state record *which branch* ran? How could you tell from the outside?

Run it:

```bash
uv run --locked python lessons/03_branch.py
```

## Your experiments

### Experiment A: prove the other roads do not run

Add a print to every branch node (they already have one) and run all four messages.
For one message, explain *why* the three unchosen nodes did not run, using the words
"router", "routing key", and "path_map".

### Experiment B: add a new branch

Add a `"shipping"` intent for messages containing `"ship"` or `"deliver"`. You need to
change several places. List them **before** you start editing. Then do it, run it, and
check that `"When will it be delivered?"` takes your new road.

### Experiment C: break the mapping on purpose

Make `guess_intent` produce `"shipping"`, but leave `"shipping"` **out** of `path_map`.
Predict: does it fail when compiling or when invoking? What does the error say? Restore it.

### Experiment D (optional): let the router write state

Make the router return `{"intent": "greeting"}` instead of a string. Predict what happens.
Then explain why a router is the wrong place to change state.

## Review checkpoint

> For `"Where is my order?"`, name every function that runs, in order. For each one,
> say whether its return value was merged into state, used to pick a road, or returned
> to your code.

If you mix up "node update" and "router output", stay here and trace it again.

Official reference: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).
