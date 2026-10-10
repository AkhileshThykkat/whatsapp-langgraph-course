# Lesson 5: a loop

```text
START → decide ──"act"──────────→ act ─┐
          ↑                            │   (edge back = the loop)
          └────────────────────────────┘
        decide ──"respond"───────→ respond ───────→ END
        decide ──"stop_at_limit"─→ stop_at_limit ─→ END
```

**New idea:** decide → act → **observe** → decide again. The second decision can see the
first tool's result, so later choices depend on earlier observations.

This is the agent cycle from `REQUIREMENTS.md`:
**message → decision → action → observation → next decision → reply**. The decision
maker is still fake: plain deterministic Python. Lesson 8 swaps in a model.

## Why a loop instead of a longer path?

**Simple why:** You do not know in advance how many lookups a message needs.

**Technical explanation:** A fixed path has a fixed number of steps. A cycle lets one
`decide` node run as many times as needed, with each trip choosing based on the
observations gathered so far. A loop needs an exit (the router) and a guaranteed end.

## Two different limits

| Limit | Where | What happens when hit |
|---|---|---|
| `MAX_DECISIONS` (yours) | `route_after_decide` | Planned outcome: `stop_at_limit` writes a polite reply |
| `recursion_limit` (LangGraph) | `invoke(..., {"recursion_limit": 25})` | `GraphRecursionError` is raised. A crash, not a reply |

**Simple why:** Your rule stops a bot that is thinking too much. LangGraph's rule catches
a bot whose stop rule is broken.

**Technical explanation:** `recursion_limit` counts graph super-steps. Here each node
run is one step, so tool nodes use up budget too. It has nothing to do with Python stack
recursion or a model's output length. Your own counter is what gives users a defined
answer, so the framework limit should only be a backstop.

## Where the loop's memory lives

`observations` is a list in state. Each `act` returns the **old list plus one item**,
because without a reducer the returned value *replaces* the old one. Lesson 6 changes
exactly this line.

## Predict before running

For `"Where is A100, and what is your returns policy?"`:

1. How many times does `decide` run? How many times does `act` run?
2. What does `decide #2` see in `observations`? Why does it choose differently from `decide #1`?
3. What does the router return after each `decide`?

For the last scenario (two orders + shipping + warranty):

4. Which step hits the limit? Did the warranty search run? Does the reply include the
   facts that *were* found? Is that a good user experience?

Run it:

```bash
uv run --locked python lessons/05_loop.py
```

## Your experiments

### Experiment A: move the limit

Set `MAX_DECISIONS = 5`, then `= 1`. Before each run, write down the reply you expect
for every scenario. Explain any difference between your prediction and the output.

### Experiment B: break the stop rule, then meet the backstop

1. Make `decide` "forget" what it already did. For example, make `already_done` always
   `[]`. Predict what happens with `MAX_DECISIONS = 4`.
2. Now *also* disable your own limit (make `route_after_decide` never return
   `"stop_at_limit"`). Predict: which error, after roughly how many node runs?
3. Restore both. Write down why the two limits are different.

### Experiment C: a better outcome at the limit

Change `stop_at_limit` so it includes whatever was already found, and *then* says a
colleague will follow up. Which state fields does it need to read?

## Review checkpoint

> Trace `"Where is A100, and what is your returns policy?"` as a numbered list of node
> runs. After each one, write the value of `decisions`, `next_action` and the *length*
> of `observations`. Explain what makes the third `decide` choose `finish`.

Official reference: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) (see "recursion limit").
