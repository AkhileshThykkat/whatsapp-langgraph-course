# Direction of the course

## The teaching style

Scalar neural-network learning scripts make every calculation visible. Here we make each state change,
function call, and choice of next step visible. One small runnable file per lesson,
ordinary functions, invented inputs, and print traces. You make the experiments.

**Simple why:** You need to understand the moving parts before assembling a large bot.

**Technical explanation:** We minimize abstraction and dependency count per lesson.
We do not introduce architecture patterns, schema validators, or test scaffolding
before their purpose is visible. We use actual LangGraph from the first graph lesson,
not a homemade graph runtime you must implement first.

## Planned progression — only the first lesson is ready

| Step | New thing to see | Small experiment |
|---|---|---|
| **1: node and edge** | One function registered as a node; START/END and invoke | Add a second node and predict the state it receives |
| 2: a path of nodes | Different functions contribute different state fields | Change execution order and explain what breaks |
| 3: a branch | A conditional edge chooses one road | Route a greeting differently from an order question |
| 4: a tool | A node calls an ordinary fact-finding function | Look up an invented order without inventing its status |
| 5: a loop | Decide → tool → observe → decide again | Add a stop rule and deliberately trigger it |
| 6: reducers and traces | Some fields replace; others accumulate | Return a full trace by mistake and observe duplication |
| 7: one model call | Messages enter an LLM; text comes back | Separate prompt, request, response, and parse failure |
| 8: a model-guided graph | Replace the fake decision with validated model output | Prove the model cannot execute an unknown tool |
| 9: memory | State saved and loaded for a thread | Keep two conversations separate and reset per-turn fields |
| 10: the dummy webhook | HTTP hands a message to the graph | Invoke the same bot from a terminal and local HTTP |
| 11: waiting for a human | Pause/resume instead of simply reaching END | Inspect node replay; avoid duplicated effects |
| 12: reliability | Tests and failure scenarios for behavior you now understand | Catch wrong order ownership, loops, and bad model output |

The target is a small learning version of your existing AI bot: policy questions,
order lookup, conversation memory, and dummy handoff. No production extraction claims.

## Final independent capstone

After these guided lessons, request a fresh assignment following CAPSTONE.md. Every
request must differ in domain, workflow, and scenarios from the recorded history.
Only a brief/rubric is generated. Build it in a blank project with NO AI help for
design, coding, debugging, tests, or review. Official docs, your own notes, and runtime
LLM usage are allowed. No capstone solution, starter, or tailored plan is generated.

## Our checkpoints

After each example:

1. Predict a state transition without running the code.
2. Modify the example yourself.
3. Explain the result in plain English.
4. Connect that explanation to the technical term.

We stop at that point and review. Later scripts are not generated ahead of you.
You can ask for a hint or a smaller example. A course is not complete merely because
all its scripts exist: you should be able to rebuild their ideas without a coding agent.

## Keep these boundaries clear

**Simple why:** A demo should not send messages to real customers or reveal their data.

**Technical explanation:** The initial tools and payloads use invented data; real
identity, authorization, signature verification, idempotency, and external sending
remain separate production concerns. LangGraph supplies orchestration, not those
security guarantees. A model-guided loop also uses a pretrained model; we are not
training its weights as you did in the NeuralN exercises.
