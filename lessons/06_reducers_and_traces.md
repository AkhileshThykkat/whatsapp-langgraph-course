# Lesson 6: reducers and traces

```text
START → start → tick ─"again"→ tick (loop)
                  └──"done"──→ END
```

**New idea:** a **reducer** decides how a node's update combines with the value already
in state. Some fields are *replaced*; others *accumulate*.

The graph is deliberately tiny, with no tools and no shop, so the merge rule is the
only thing to watch.

## The rule, per key

For every key a node returns:

```text
new_state[key] = reducer(old_state[key], update[key])
```

| Field | Annotation | Reducer | Effect |
|---|---|---|---|
| `count` | `int` | default (replace) | `new = update` |
| `last_node` | `str` | default (replace) | `new = update` |
| `trace` | `Annotated[list[str], operator.add]` | `operator.add` | `new = old + update` |

Keys a node does **not** return are untouched. That rule is the same as in lesson 1.

**Simple why:** You want one current count, but a growing diary of what happened.

**Technical explanation:** `Annotated[type, reducer]` attaches a binary function to the
channel. LangGraph calls it for every update to that key, in sequential steps as well
as parallel ones. Even the **input** goes through the reducer: `["input received"]` is
added to an empty list.

## Updates vs values: two views of the same run

- `stream_mode="updates"` shows what each node **returned**: the small deltas.
- `stream_mode="values"` shows the whole state **after** each step: the accumulated result.

**Simple why:** One shows the change; the other shows the result of the change.

**Technical explanation:** Consuming the stream iterator is what runs the graph.
Neither mode is token streaming from a model. The script runs the graph three times
(two streams and one `invoke`) only so that you can compare the views. Each run starts
fresh from the same input.

## The classic bug: returning the whole list into an append field

If `tick` returned `state["trace"] + [new_line]` instead of `[new_line]`, the reducer would
compute `old + (old + [new_line])`, so every old entry appears again. The rule:

> **Replace field:** return the full new value. **Append field:** return only the delta.

Lesson 5's `act` returned `old_list + [item]`. That was correct *because* `observations`
had no reducer.

## A consequence for later (lesson 9)

With `operator.add`, returning `[]` adds nothing, so **you cannot clear an append
field by returning an empty list**. Keep this in mind when per-turn data must be reset.

## Predict before running

1. Write the `updates` chunk for step 3, and the full `values` dictionary after step 3.
2. How many entries does the final `trace` have? Where does each one come from?
3. Why does `count` still read `0` after step 1 in the `values` view?
4. **Tricky case:** if `initial_state` had `"trace": []`, how many entries would the final trace have?

Run it:

```bash
uv run --locked python lessons/06_reducers_and_traces.py
```

## Your experiments

### Experiment A: reproduce the duplication bug

Change `tick` to return the **whole** trace plus its new line. Before running, predict
the exact length of the final trace. (Work it out step by step. It is not 5.) Run it,
compare, and explain the growth. Restore it.

### Experiment B: remove the reducer

Change `trace` back to a plain `list[str]`. Predict the final trace. Which single entry
survives, and why?

### Experiment C: upgrade lesson 5

In *your copy* of `05_loop.py`, give `observations` an `operator.add` reducer. Which line
in `act` must change, and why? Predict what happens if you forget to change it, then check.

## Review checkpoint

> Using your Experiment A output, explain the difference between an update and the
> accumulated state, and why "return a delta" is correct only for fields with an
> append reducer.

Official reference: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) (see "reducers")
and [streaming](https://docs.langchain.com/oss/python/langgraph/streaming).
