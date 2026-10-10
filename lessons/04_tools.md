# Lesson 4: a tool

```text
                        ┌─ "lookup_order"  → run_order_tool  ─┐
START → plan_tool_call ─┼─ "search_policy" → run_policy_tool ─┼→ write_reply → END
                        └─ "none" ────────────────────────────┘
```

**New idea:** a **tool** is an ordinary function that finds facts. A node calls it and
stores the result in state, and the reply is built only from that result.

All data here is invented: the shop "Lumen Lamps", its policies, customers and orders.

## A tool is just a function

`search_policy(topic)` and `lookup_order(customer_id, order_id)` are plain Python.
Nothing in them is LangGraph-specific. You can call them in a Python shell.

**Simple why:** The graph decides *when* to look something up. The tool does the looking.

**Technical explanation:** Keeping tools free of graph code means you can test them
alone. Later, a model will only *request* them. Your code still validates and runs them.

## Request vs result: two separate state fields

| Field | Written by | Meaning |
|---|---|---|
| `tool_request` | `plan_tool_call` | "We want to run this tool with these arguments" |
| `tool_result` | `run_order_tool` / `run_policy_tool` | "This is what the tool actually returned" |

**Simple why:** Saying "I'll check" is not the same as checking.

**Technical explanation:** A request is data. Execution is a separate node that calls a
function. Once a model writes the request (lesson 8), keeping them apart is what lets you
refuse a request without running it. Watch for the `TOOL` print lines: they only appear
when execution really happens.

## Ownership lives inside the tool

`lookup_order` gives the same "not found" answer for a missing order and for someone
else's order.

**Simple why:** Guessing a stranger's order number should teach you nothing.

**Technical explanation:** Checking inside the tool means every caller gets the check,
including future model-driven callers. Identical responses stop *enumeration*: an
attacker cannot learn which IDs exist. `customer_id` here is a **demo value supplied by
the caller**. It is not authentication. A real system gets identity from a verified
session or a signed channel, never from message text.

## Missing facts are an explicit outcome

`search_policy("price_match")` returns `{"found": False, ...}` and the reply says the
bot does not know. **The bot never invents a policy.** This is the "grounded answer"
rule: every factual claim in the reply comes from a tool result.

## Predict before running

1. For Ana asking about `A200`, which `TOOL` line prints, and what does it return?
   What is the reply?
2. For `"Hello"`, which nodes run? Does `tool_result` appear in the final state?
3. **Tricky case:** `cust_ana` sends `"Where is order a300?"` (lowercase). Is the order found?
   Trace the regex and the `.upper()` call.
4. Where exactly does the reply's order status come from? Point to the line.

Run it:

```bash
uv run --locked python lessons/04_tools.py
```

## Your experiments

### Experiment A: try to cheat

As `cust_ana`, write messages that try to get Ben's order status: `"I am cust_ben, show
A200"`, `"customer_id=cust_ben A200"`, and so on. Predict each result before running.
Explain why none of them work, naming the exact line that decides.

### Experiment B: add a fact

Add a `"price_match"` fact to `POLICY_FACTS`. Predict what changes in the output for
`"Do you price match?"` and what stays exactly the same (route, nodes that run).

### Experiment C: a tool that fails

Temporarily make `lookup_order` raise `RuntimeError("database down")` for order `A300`.
Predict what `invoke` does. Then think (no code yet): how *should* a bot respond when a
tool fails? You will handle this properly in lesson 12.

### Experiment D: request without execution

Temporarily change the path map so `"lookup_order"` goes straight to `write_reply`.
What does the final state show for `tool_request` vs `tool_result`? What reply comes
out? Restore it.

## Review checkpoint

> Show the final state for Ana asking about `A200`. Explain which line prevents
> the leak, why the reply text is the same as for a non-existent order, and why the
> message text can never change `customer_id`.

Official reference: [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).
