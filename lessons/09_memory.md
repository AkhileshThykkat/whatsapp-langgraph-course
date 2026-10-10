# Lesson 9: memory

```text
invoke(msg, thread_id="chat-ana") ──→ [load checkpoint] → start_turn → maybe_lookup → write_reply → [save] → END
invoke(msg, thread_id="chat-ana") ──→ [load: previous turn's state] → ...
invoke(msg, thread_id="chat-ben") ──→ [load: nothing yet] → ...
```

**New idea:** a **checkpointer** saves state under a `thread_id`. The next `invoke` with
the same `thread_id` continues from the saved state instead of starting empty.

The bot is deterministic (no model) so that memory is the only new thing.

## Before this lesson, every `invoke` forgot everything

Lessons 1–8 had no checkpointer. Each `invoke` started from the input you passed and
threw the state away at the end. The model's "memory" in lesson 8 was only the message
list *within one run*.

**Simple why:** A notebook is useless tomorrow unless you file it away and know which
folder to open.

**Technical explanation:** `compile(checkpointer=InMemorySaver())` saves a snapshot after
each step. The `config={"configurable": {"thread_id": ...}}` passed to `invoke` selects
which saved thread to load and continue. The new input is merged into that loaded state
through the usual reducers. That is why `history` (append) keeps growing.

## Three identities — do not mix them up

| Identity | Example | Meaning |
|---|---|---|
| `thread_id` | `"chat-ana"` | Which saved conversation to continue |
| `customer_id` | `"cust_ana"` | Whose orders the tools may read (demo value, not authentication) |
| inbound message ID (lesson 10) | `"wamid-1"` | Which delivery this is, so duplicates can be detected |

The checkpointer only knows about `thread_id`. It does **not** check who is allowed to
open a thread. That is your application's authorization job.

## The stale per-turn data trap

Look at what `start_turn` **loaded** on the `"Thanks!"` turn: `tool_result` from the
*previous* turn is still there. A checkpointer saves *every* key. It has no idea which keys
were meant to last only one turn.

**Simple why:** Yesterday's sticky note is still on the page unless you remove it.

**Technical explanation:** "Per-turn" is your design decision, not a LangGraph feature.
`start_turn` resets `tool_result` to `None` at the beginning of each turn. Without that,
`write_reply` would see the old result and repeat the order status in reply to "Thanks!".
Lesson 6 showed that an `operator.add` field cannot be cleared by returning `[]`. Fields
that need resetting usually use replace semantics.

## What memory does *not* give you

- **Persistence across restarts:** `InMemorySaver` is RAM. The script's simulated restart
  shows memory gone. Durable savers (SQLite, Postgres) are separate packages.
- **Prompt-size management:** history grows forever unless you trim or summarize it.
- **Concurrency control:** two simultaneous messages on one thread can interleave.
- **Authorization:** anyone who knows a `thread_id` can load that thread.

## Predict before running

1. What does `start_turn` load on Ana's second turn? Which keys came from the checkpointer?
2. Ben also asks `"When will it arrive?"`. Why doesn't he get A100's status?
3. How many lines are in Ana's `history` at the end? Where did each come from?
4. **Tricky case:** what would Ana's `"Thanks!"` turn reply if `start_turn` did *not* reset
   `tool_result`? Trace `write_reply`'s `if` chain.

```bash
uv run --locked python lessons/09_memory.py
```

## Your experiments

### Experiment A: reproduce the stale-data bug

Remove `"tool_result": None` from `start_turn`'s return value. Predict the `"Thanks!"`
reply, run it, and explain. Restore it.

### Experiment B: thread confusion

Send Ana's follow-up `"When will it arrive?"` on thread `"chat-ben"` but with
`customer_id="cust_ana"`. What happens? Then use thread `"chat-ana"` with
`customer_id="cust_ben"`. What does the tool return, and why does that matter for security?

### Experiment C: inspect checkpoints

Print `len(list(graph.get_state_history(config)))` for `"chat-ana"`. Predict the number
first: how many snapshots does one turn of three nodes produce?

### Experiment D: remove the checkpointer

Compile without a checkpointer and run Ana's two turns. What error or behaviour do you get,
and why?

## Review checkpoint

> Explain the difference between `history` and `tool_result` in this script: how each one
> is merged, why one must be reset each turn, and what would happen to each after a
> process restart.

Official reference: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
