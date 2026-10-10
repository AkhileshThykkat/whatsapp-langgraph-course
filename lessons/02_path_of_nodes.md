# Lesson 2: a path of nodes

Finish lesson 1, including Experiment C and its review, before opening this lesson.
Lesson 2 is a longer version of what you built there, so reading it first gives that
exercise away.

```text
START → clean_message → guess_intent → write_reply → END
```

**New idea:** different nodes contribute **different fields** to one shared state, and
the order of the nodes decides what each node can see.

## Who writes which page?

| Node | Reads | Writes |
|---|---|---|
| `clean_message` | `message` | `cleaned` |
| `guess_intent` | `cleaned` | `intent` |
| `write_reply` | `intent`, `message` | `reply` |

**Simple why:** Each step has one job and leaves its result for the next step.

**Technical explanation:** Each node returns a partial update with one new key.
LangGraph merges it into the state before the next node runs. No node returns the
whole state, yet the final state contains every key, because omitted keys are kept.

## Why not overwrite `message` with the cleaned text?

**Simple why:** You may still want the customer's exact words later.

**Technical explanation:** Overwriting would *replace* the `message` channel's value.
Every later node would see only the cleaned version. Writing a new key keeps the raw
input next to the derived value. That makes debugging easier and keeps derived data
apart from the customer's raw input.

## Order matters: a node can only read what earlier nodes wrote

`guess_intent` reads `state["cleaned"]`. That key exists only because `clean_message`
ran first. The edges decide the order; the order of the `add_node` calls does not.

## Predict before running

1. What exactly does `guess_intent` receive for `"  Where is my ORDER?  "`?
   Write the whole dictionary.
2. How many keys does the final state have? Which node created each one?
3. Is `write_reply`'s returned dictionary the same as the final state?
4. **Tricky case:** what intent will `"Hiking lamp for sale?"` get, and why? Is the
   result *correct*? What does that tell you about keyword rules?

Then run:

```bash
uv run --locked python lessons/02_path_of_nodes.py
```

## Your experiments

### Experiment A: change the order of the stops

Rewire the edges so that `guess_intent` runs **before** `clean_message`. First predict:
does it fail while building, while compiling, or while invoking? Which line fails, and
what is the error? Run it, read the error, and explain it. Then restore the route.

### Experiment B: add a fourth contributor

Add a node that counts the words in `cleaned` and writes a new key, `word_count`.
Decide where it can sit in the path, and where it cannot. Update the state schema too.
Can `write_reply` include the count in its reply? What has to be true about the edges?

### Experiment C: overwrite on purpose

Make `write_reply` also return `"message": "CHANGED"`. Predict the final state. Then
explain the difference between "a node omitted a key" and "a node overwrote a key."

## Review checkpoint

Explain, with a concrete dictionary from your run:

> `write_reply` returns only `reply`. Which earlier updates does it depend on, and
> what would go wrong if the edge from `clean_message` to `guess_intent` were removed?

Do not continue until you can trace all four dictionaries for one message by hand.

Official reference: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).
