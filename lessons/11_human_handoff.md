# Lesson 11: waiting for a human

```text
START → triage ─"auto_reply"→ auto_reply → END                    (finished)
           └────"handoff"───→ handoff ⏸ interrupt()               (PAUSED, saved)
                                  ⋮  later: invoke(Command(resume="..."), same thread)
                              handoff ▶ (runs again from line 1) → END   (finished)
```

**New idea:** reaching `END` **finishes** a run. `interrupt()` **pauses** it. The paused run
is saved, and it can be **resumed** later with a human's answer.

## END vs pause

| | Thread A (`"Hello"`) | Thread B (`"refund"`), first invoke |
|---|---|---|
| `invoke` returns | full final state with `reply` | state so far + `__interrupt__`, **no** `reply` |
| `get_state(config).next` | `()`: nothing left to run | `('handoff',)`: waiting there |
| Can it continue? | Only as a *new* turn | Yes: `invoke(Command(resume=...), config)` |

**Simple why:** Finishing a phone call is not the same as putting the caller on hold.

**Technical explanation:** `interrupt(payload)` saves a checkpoint for the thread and makes
`invoke` return early with the payload under `__interrupt__`. That requires a checkpointer
and a `thread_id`. `Command(resume=value)` on the same thread continues from that
checkpoint. A node that simply *returns* `"handing off"` and reaches `END` has terminated.
Nothing is waiting, and there is nothing to resume.

## The surprise: the node runs again from the top

On resume, LangGraph does **not** continue from the middle of `handoff`. It runs `handoff`
again **from its first line**. The second time, `interrupt()` returns the resume value
instead of pausing. `triage` does not run again, because its result was saved.

So everything *before* `interrupt()` in that node runs twice. The script prints
`Notifications sent for ONE handoff: 2`. That is the bug you will fix.

**Simple why:** If you rewind a video to replay one scene, everything in that scene
happens again, including the doorbell ringing.

**Technical explanation:** Python can't freeze a function halfway and restore it later in
another process. LangGraph resumes at **node granularity**. Side effects before an
interrupt in the same node are replayed. Fixes: move side effects into a separate,
earlier node (whose completion is checkpointed), put them after the interrupt, or make
them **idempotent** (e.g. keyed by a handoff ID so a second send is ignored). Checkpointing
is not exactly-once delivery.

## Predict before running

1. For thread B's first `invoke`, which prints appear, and is `reply` in the result?
2. On resume, which nodes run? Does `triage` print again?
3. What value does `interrupt()` return the second time, and where does it come from?
4. **Tricky case:** what would happen if you resumed thread **A** with `Command(resume=...)`?

```bash
uv run --locked python lessons/11_human_handoff.py
```

## Your experiments

### Experiment A: fix the double notification

Change the graph so the support team is notified exactly **once** per handoff, while the
handoff still pauses for the human. Predict the new node order and the final count, then
verify. Explain why your fix works in terms of checkpoints.

### Experiment B: pause without resuming

Comment out the resume `invoke`. Then, *in a new `graph`* (new `InMemorySaver`), try to resume
thread B. What happens, and what does that tell you about where the paused run lived?

### Experiment C: a second interrupt

Add a second question in the same node after the first (e.g. "Add a note for the
customer?"). How many `invoke` calls does the full conversation now need? How many
times does the code before the first interrupt run in total?

## Review checkpoint

> Using your Experiment A output, explain: (1) the difference between reaching `END` and
> pausing, (2) exactly which code re-executes on resume and why, and (3) why
> "checkpointing" does not mean "each side effect happens exactly once."

Official reference: [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).
