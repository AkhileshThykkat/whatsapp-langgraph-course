# First mental model: what you are actually building

This is an orientation, not a demand to memorize everything before lesson 1.
Later lessons develop each idea through code that you write yourself.

## 1. An LLM is not the entire agent

### Simple explanation

Think of a language model as a function that reads some text and produces an answer.
It can suggest an action, but a suggestion does not execute Python, look up an order,
or send a WhatsApp message. Your program must do those things.

A chatbot that only produces text is different from a program that can repeatedly
choose actions, execute tools, inspect their results, and decide what to do next.

### Technical explanation

A typical chat-model request sends a sequence of messages to an inference endpoint.
Those messages are encoded as tokens. The model generates output tokens; depending
on the API, the response may contain text, structured JSON, or tool-call metadata.
A hosted inference service is separate from your Python application.

An agent application wraps this inference step with state, tool dispatch, control
flow, validation, failure handling, and explicit stopping conditions. "Agent" is a
broad term, not a guarantee of independent reasoning or reliability. In this course,
our target is a **model-guided decision/action loop**.

### Why start with a fake decision maker?

**Simple why:** First learn the machinery; then swap in the unpredictable brain.

**Technical why:** A deterministic policy isolates orchestration bugs from model
behavior. It exercises state transitions and tools without network calls, token
costs, credentials, or hallucinations. Until we install a model, this is a workflow
simulator—not a functioning AI agent.

## 2. A tool is an ordinary capability your program exposes

### Simple explanation

A tool is a function the bot is allowed to ask for: "search the knowledge base" or
"look up this order." The program checks the request and calls that function.

The model saying "I checked your order" is not proof that a lookup happened.

### Technical explanation

Separate four events:

1. **Declaration:** describe a tool's name, arguments, and intended use.
2. **Selection:** a model or policy emits a request with that name and arguments.
3. **Execution:** application code validates and dispatches to an allowed function.
4. **Observation:** return the result to the next decision step.

Some model APIs provide native tool calling. Others require validated structured
JSON. Neither approach executes your local function automatically. Framework helpers
can perform dispatch, but you still control approval, scope, and side effects.

### Why not let the model run arbitrary code?

**Simple why:** Asking for one approved lookup is very different from controlling
anything on your computer.

**Technical why:** An allowlist, argument validation, authenticated caller identity,
and scoped data access form the execution boundary. Never `eval()` model output.
User messages and retrieved text are untrusted data, not new tool permissions.

## 3. State is the working notebook

### Simple explanation

State records what this run knows: the incoming question, the latest decision,
tool results, and the answer. Each step reads it and contributes a small change.

It is not a magic memory that automatically survives the program stopping.

### Technical explanation

In a LangGraph `StateGraph`, state is represented as named channels defined by a
schema. A node receives current state and returns a partial update. LangGraph applies
a reducer independently to each updated key. Without a custom reducer, that key's
new value replaces its old value. An omitted key retains its previous value.

A `TypedDict` communicates key/type expectations to tooling; it is not itself a
runtime validation mechanism. Pydantic validation at input and model-output boundaries
is a separate concern we will cover later.

### Why distinguish state from prompt?

**Simple why:** The program may know things the model has not been told.

**Technical why:** Graph state is application data. The model sees only the messages
or other input your model adapter constructs. LangGraph does not automatically send
all state fields to an LLM or turn trace entries into conversation history.

## 4. A node does work; an edge chooses what runs next

### Simple explanation

A node is a stop on the journey: think, search, answer, or hand over. An edge is a
road between stops. A conditional edge is a junction with a rule for choosing a road.

### Technical explanation

A node is usually a Python callable returning a state update. A fixed edge schedules
a particular destination after a node. A conditional-edge router inspects state and
returns a routing key or destination(s). The router is not a state update.

`START` and `END` are special graph sentinels, not model calls. Building a `StateGraph`
defines the topology. `compile()` creates its executable runtime; it does not run the
bot, train a model, or persist conversations by itself.

Our target loop will look like:

```text
START → decide
          ├── search_kb → decide
          ├── order_lookup → decide
          ├── reply → END
          └── handoff → END
```

The second `decide` sees the tool result produced since the first `decide`.

### Why not use a straight chain for everything?

**Simple why:** Sometimes the bot needs to fetch information and think again instead
of always doing the same three steps.

**Technical why:** A graph represents cycles, branches, terminal outcomes, and later
persistence/interruption features explicitly. For a single call with no branching,
a normal Python function or simple chain may be easier. LangGraph is not required
for every LLM application.

## 5. Reducers determine how changes combine

### Simple explanation

Some pages in the notebook should be replaced: the latest decision. Other pages
should grow: the list of steps already taken.

### Technical explanation

For an updated key `k`, the conceptual operation is:

```text
next_value[k] = reducer(current_value[k], node_update[k])
```

With default replacement, a new decision becomes the current decision. With an
append reducer, a new trace item is appended to the old trace. Reducers apply to
updates across sequential steps too—not only parallel execution.

A subtle error: returning the whole accumulated trace from a node when the reducer
already appends. Old entries get appended again. Nodes should return deltas for
append-based fields. Lesson 1 simulates these mechanics in plain Python.

### Why not append every field?

**Simple why:** You usually want one current answer, not a growing list of old answers.

**Technical why:** Merge behavior follows the semantics of each channel. Later,
LangChain message histories use `add_messages`, which can replace a message with the
same ID; it is not identical to ordinary list concatenation.

## 6. LangGraph runs the workflow; it does not decide everything

### Simple explanation

LangGraph is the traffic system. You still provide the roads, the work at each stop,
and the decision-making rules.

### Technical explanation

LangGraph schedules active nodes using message-passing/super-step semantics, merges
updates into channels, and follows configured edges. Sequential nodes use distinct
super-steps; parallel nodes may share a super-step. A workflow can contain no LLM at
all, one model call, or multiple calls.

`invoke()` returns the completed run's output. `stream(..., stream_mode="updates")`
yields node deltas as execution advances; `"values"` exposes accumulated state at step
boundaries. Neither is automatically token streaming from the model.

When using streams, consuming the iterator drives execution. In an HTTP integration,
you must deliberately choose final-response or streaming-response behavior.

### Why two loop limits?

**Simple why:** One stops too much thinking; another catches a broken route.

**Technical why:** An application hop counter can limit decision/model calls.
LangGraph's top-level `config["recursion_limit"]` bounds graph super-steps. Tool nodes
also consume execution steps. A recursion limit is not Python stack recursion and
not a model's maximum output tokens. A cap needs a defined failure/fallback outcome.

## 7. Memory, checkpointing, and pausing are separate concepts

### Simple explanation

A notebook used for one question is not a saved conversation. To continue later,
you need to save it and know whose conversation to reopen.

### Technical explanation

A checkpointer persists graph state snapshots for a `thread_id`. Reusing that thread
allows conversation continuity when you supply new input, or resumption when execution
is paused. A store supports application-defined data outside an individual thread.
The meanings of thread identity, customer identity, and inbound-message identity are
different; none is automatically an authorization proof.

`InMemorySaver` holds checkpoints in RAM and loses them on process restart. Durable
checkpoint implementations use storage such as SQLite or PostgreSQL. Persisting
history does not automatically manage prompt size, remove stale tool results, or
serialize simultaneous requests from the same customer.

`interrupt()` can pause for external input when used with checkpointing. Resuming
with `Command(resume=...)` re-executes the interrupted node from its beginning.
Side effects before the interrupt therefore require careful handling/idempotency.
A node that simply returns "handoff" and reaches `END` has terminated, not paused.

### Why postpone this until after the single-turn graph?

**Simple why:** First understand one journey before managing many saved journeys.

**Technical why:** Multi-turn state adds stale per-turn fields, identity/isolation,
retention, serialization, replay, and concurrency concerns. We will introduce those
with tests rather than add a checkpointer and assume memory is now solved.

## 8. The webhook is a door, not the agent

### Simple explanation

The webhook accepts a message and gives it to the bot. The bot should also work
without that door—for example from a terminal or a test.

### Technical explanation

Transport validation belongs in the HTTP layer. Orchestration belongs in a service
and graph. Keeping those boundaries separate lets us test state transitions without
HTTP and test ingress without a real model or WhatsApp network call.

A dummy webhook does not implement Meta verification/signatures, delivery retries,
authentication, or the full WhatsApp payload schema. Production inbound deliveries
must be treated as possibly duplicated and untrusted until verified.

### Why keep live WhatsApp sending out of the course initially?

**Simple why:** A mistake should fail a local exercise, not send a confusing message
to a real customer.

**Technical why:** External sends are side effects that need validated recipients,
approved payloads, idempotency, error handling, and operational observability. Graph
retries/checkpoint replay do not automatically make those effects exactly-once.

## Where these concepts enter the course

- Now: state, partial updates, and overwrite vs append.
- Next: tools, scope, and deterministic control flow.
- Then: graph nodes/edges/reducers/streaming.
- After that: model input/output, safe dispatch, memory, webhook, interrupts, evaluation.

You do not have to understand checkpoint replay yet. Start by predicting the result
of the three small state functions in lesson 1.

## References

- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

These are official sources for runtime semantics, not a substitute for experimenting
with the examples. Check the online docs against the package version in uv.lock.
