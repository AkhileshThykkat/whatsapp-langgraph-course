# Understanding tasks — YOU do these, the teaching agent guides

**The requirement is understanding, not having the assistant complete this checklist.**
Only lesson 1 tasks are active; later lessons unlock one at a time. Do them in order, one small experiment at a time.
Predict before running. Ask for a hint if stuck; no full solution is required upfront.

## How to demonstrate understanding

For each task, keep a short note or bring the output to the teaching agent:

```text
My prediction:
What I changed:
What actually happened:
Why it happened (plain English):
The technical concept:
What I am still unsure about:
```

Do not mark a task done just because code runs. Explain one specific state transition
or control-flow decision, then have the teaching agent review that explanation.

## Active: lesson 1 — node, edge, state, compile, invoke

### Task 1 — draw and predict (before running)

- [ ] Draw the existing route on paper or in a text note.
- [ ] Identify the node function, node ID, and each edge's source/destination.
- [ ] Write the dictionary you expect the node to receive.
- [ ] Write the dictionary you expect the node to return.
- [ ] Write the final state you expect invoke to return.

**Simple why:** Predicting forces you to follow the mechanism rather than recognize an answer.

**Technical explanation:** Node input, partial output, and merged state are separate
values. Fixed edges select the execution path; they do not themselves generate text.

**Review evidence:** Explain why a returned update can omit the original message while
the final state still retains it. Explain why `make_reply` and `"make_reply"` appear as
separate arguments in add_node.

### Task 2 — change the data, not the route

- [ ] Change the incoming message and predict which print statements change.
- [ ] Run it and compare the prediction.
- [ ] Change only the node's reply text and repeat.
- [ ] Explain whether either change alters which nodes execute.

**Simple why:** Changing the traveler is different from changing the roads.

**Technical explanation:** Runtime state values and graph topology are different.
This graph has no conditional router; different text does not automatically reroute it.
Its reply is Python formatting, not model inference.

**Review evidence:** Explain what would be missing if someone called this example an AI agent.

### Task 3 — add your own second node

- [ ] Write a second small function that prints received state and returns a new reply.
- [ ] Register it with a distinct node ID.
- [ ] Rewire the route to START → make_reply → your_node → END.
- [ ] Remove the old direct make_reply → END edge; do not leave an unintended extra road.
- [ ] Predict whether the second node sees the first reply and which reply wins at the end.
- [ ] Run it and explain each state transition.

**Simple why:** Two stops make the handoff of information visible.

**Technical explanation:** LangGraph applies the first node's update before scheduling
the next sequential node. Without a custom reducer, a later update to the same key
replaces the earlier value; a partial update preserves omitted keys.

**Review evidence:** Point to the exact returned update that determines the final reply.
The agent should offer hints, not supply the full second-node implementation for you.

### Task 4 — deliberately break one thing

Use a copy of your small script or restore your change afterward.

- [ ] Change an edge destination to a node name you never registered.
- [ ] Predict whether failure happens while building, compiling, or invoking.
- [ ] Run it, read the actual error, and explain what was invalid.
- [ ] Restore the route.
- [ ] Add a print before compile and another before invoke. Explain when the node's own
      print runs relative to those prints.

**Simple why:** A broken example shows what the framework checks and when work starts.

**Technical explanation:** Graph construction, structural compilation, and runtime
execution are separate phases. Node registration passes a callable; it does not invoke
that function. Compile does not perform the reply computation.

**Review evidence:** State your prediction, the observed failure phase, and why they
matched or differed. Do not "fix" it by adding arbitrary edges without understanding.

### Task 5 — rebuild the tiny graph from a blank file

- [ ] Write a new small example using a different node name and message.
- [ ] Define the state, register your function, wire entry/exit, compile, and invoke.
- [ ] Print input, node update, and final state.
- [ ] Use docs or hints if needed, but do not ask the coding agent to write the file for you.
- [ ] Explain each part without reading the original script aloud.

**Simple why:** Rebuilding tells you whether you understand the idea or only the example.

**Technical explanation:** Reproducing the minimal workflow independently demonstrates
the relationship between state schema, node callable, registered ID, edges, builder,
compiled runtime, and invocation input.

**Review evidence:** Your new script and an explanation of why compile alone produces no reply.

## Gate before lesson 2

Do not advance until you can answer:

1. What does a node do that an edge does not?
2. Why is a node's returned dictionary not necessarily the whole state?
3. What is the difference between registering a function and calling it?
4. What changes when you edit message text vs when you edit graph edges?
5. Why is this a graph demonstration but not yet an AI agent?

The teaching agent should check one tricky concrete case, not ask for definitions only.
Record learner-reviewed completion in PROGRESS.md; runtime verification is not enough.

## Locked: lessons 2–12

These unlock **one at a time**, only after the previous lesson's gate is reviewed. Each
lesson guide (`lessons/NN_name.md`) has the full predictions and experiments; the tasks
below are the evidence to bring. Use the same note template as above. The scripts exist
already, but do not open the next lesson early: each one shows a version of the previous
lesson's main experiment.

| Lesson | Tasks (predict → modify → observe → explain) | Gate question the agent will ask |
|---|---|---|
| 2 Path | Predict all node inputs; reorder the nodes and explain the failure; add a `word_count` node | What breaks if `clean_message → guess_intent` is removed, and when? |
| 3 Branch | Prove unchosen routes do not run; add a `shipping` branch; leave it out of `path_map` | Which return values are merged, which pick a road, which come back to you? |
| 4 Tool | Try to read Ben's order as Ana in several ways; add a fact; make a tool raise | Which exact line prevents the leak, and why can't message text change it? |
| 5 Loop | Move `MAX_DECISIONS`; break the stop rule; meet `GraphRecursionError` | Why are an app hop limit and `recursion_limit` different? |
| 6 Reducer | Reproduce the doubled trace and predict its exact length; remove the reducer | Why is "return a delta" right only for append fields? |
| 7 Model | Identify everything the model receives; add an intent and find all places to change | Where exactly does model output stop being data and become a decision? |
| 8 Dispatch | Send malicious tool inputs; add a tool and forget its allowlist branch | Why is removing `customer_id` from the schema stronger than a prompt rule? |
| 9 Memory | Reproduce stale per-turn data; mix up threads and customers | How are `history` and `tool_result` merged, reset, and lost on restart? |
| 10 Webhook | Send invalid requests with curl; call `run_bot` without HTTP; design a dedupe | Where does `phone` become `thread_id` and `customer_id`? Why is that not auth? |
| 11 Interrupt | Fix the double notification; resume from a fresh checkpointer | What re-executes on resume, and why is checkpointing not exactly-once? |
| 12 Testing | Break ownership and read the failing test; write one AAA test yourself | Explain one test's arrange/act/assert and the bug it would catch |

The agent checks one tricky concrete case per gate, not definitions. Record reviewed
completion in PROGRESS.md; runtime verification is not enough.

## Final independent task

After the guided course, request a new assignment under CAPSTONE.md. Each request
must receive a different domain/workflow/scenarios, checked against CAPSTONE_HISTORY.md.
The agent gives only a brief/rubric. Build from a blank folder with NO AI development
help: no design, implementation, debugging, test writing, or AI code review.
This remains inactive until the prerequisite lessons are completed and reviewed.
