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

## Progression — all twelve lessons are written; take them in order

Each lesson is one runnable script plus a guide (`.md`) with predictions, experiments
and a review checkpoint. **Do the review gate of one lesson before opening the next:**
each lesson contains a fuller version of the previous lesson's main experiment.

| Step | Files in `lessons/` | New thing to see | Small experiment |
|---|---|---|---|
| **1: node and edge** | `01_node_and_edge` | One function registered as a node; START/END and invoke | Add a second node and predict the state it receives |
| 2: a path of nodes | `02_path_of_nodes` | Different functions contribute different state fields | Change execution order and explain what breaks |
| 3: a branch | `03_branch` | A conditional edge chooses one road | Add a new intent; break the path map on purpose |
| 4: a tool | `04_tools` | A node calls an ordinary fact-finding function | Try to read another customer's order |
| 5: a loop | `05_loop` | Decide → tool → observe → decide again | Break the stop rule and meet the recursion limit |
| 6: reducers and traces | `06_reducers_and_traces` | Some fields replace; others accumulate | Return a full trace by mistake and observe duplication |
| 7: one model call | `07_one_model_call` | Messages enter an LLM; text comes back | Separate prompt, request, response, and parse failure |
| 8: a model-guided graph | `08_model_guided_graph` | Replace the fake decision with validated model tool requests | Prove the model cannot execute an unknown tool |
| 9: memory | `09_memory` | State saved and loaded per thread | Reproduce stale per-turn data; keep threads separate |
| 10: the dummy webhook | `10_dummy_webhook` | HTTP hands a message to the same bot | Invoke from terminal and local HTTP; dedupe deliveries |
| 11: waiting for a human | `11_human_handoff` | Pause/resume instead of simply reaching END | Fix the side effect duplicated by node replay |
| 12: reliability | `12_tests_and_reliability.md`, `support_bot.py`, `test_support_bot.py` | Tests and failure scenarios for behaviour you now understand | Break ownership and watch a test catch it |

Lessons 1–6 and 9–12 run offline. Lessons 7–8 use a scripted fake model by default; an
optional `--real` flag calls Claude with your own credentials (see their guides).

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

We stop at that point and review. Later scripts exist, but do not open the next one
until this review is done.
You can ask for a hint or a smaller example. A course is not complete merely because
all its scripts exist: you should be able to rebuild their ideas without a coding agent.

## Keep these boundaries clear

**Simple why:** A demo should not send messages to real customers or reveal their data.

**Technical explanation:** The initial tools and payloads use invented data; real
identity, authorization, signature verification, idempotency, and external sending
remain separate production concerns. LangGraph supplies orchestration, not those
security guarantees. A model-guided loop also uses a pretrained model; we are not
training its weights as you did in the NeuralN exercises.
