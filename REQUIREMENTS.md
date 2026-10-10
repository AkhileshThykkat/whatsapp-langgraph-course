# Requirements — read before implementing anything

## PRIMARY REQUIREMENT: build understanding, not a finished generated app

The learner wants to independently build an AI agent and intuitively understand a
**graph, node, edge, state, tool, loop, and model decision**. They have never built
an AI agent without a coding assistant. This repository is a guided learning course.

**Do not interpret the eventual bot specification as permission to implement every
feature now. Only prepare the next small lesson after reviewing the current one.**

## Mandatory teaching requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| T1 | Small complete runnable scripts, not a large app or upfront TODO/test scaffold | Learner can follow an example from input to output in one small file |
| T2 | Ordinary functions, explicit inputs, printed intermediate state | Node input, returned update, and final state are visibly different |
| T3 | Two-part reasoning: **Simple why** first, **Technical explanation** second | Important code/design decisions include both parts; plain English comes first |
| T4 | One principal new concept per lesson | New complexity is introduced for a visible reason, not architectural fashion |
| T5 | Use real LangGraph for graph lessons | No requirement to first build a homemade graph runtime or generic merge framework |
| T6 | Predict → run → modify → explain → review | Learner performs an experiment and answers a concrete reasoning question |
| T7 | No advance on a bare "okay"; no full solutions to learner experiments by default | Agent checks understanding and offers hints before taking over |
| T8 | Use **uv** throughout | uv manages dependencies/environment; uv.lock is committed; scripts run via uv |
| T9 | Thorough explanation without huge code | Companion notes explain mechanisms while each script stays focused |
| T10 | Honest progress and clear boundaries | PROGRESS.md separates scaffold availability, runtime verification, and learner mastery |
| T11 | Explicit understanding tasks, not just feature implementation | TASKS.md asks the learner to predict, experiment, explain, and rebuild; agent reviews evidence |
| T12 | Final independent capstone with NO AI development help | Learner builds from a blank folder, writes tests/docs, and records independent evidence; see CAPSTONE.md |
| T13 | A DIFFERENT capstone project on every explicit request | Agent checks CAPSTONE_HISTORY.md, varies domain/workflow/scenarios, and supplies only a brief/rubric |

The teaching analogy is a scalar neural-network example where inputs, predictions,
errors, and updates are visible—not a high-level library call hiding the mechanism.
For this course the visible cycle is **message → decision → action → observation →
next decision → reply**. Using a pretrained LLM is not training its weights.

## Eventual functional target — NOT an immediate build checklist

A standalone learning adaptation of a WhatsApp AI support bot. Original platform code
is not required in this public repo; use invented facts and records.

| ID | Eventually required behavior | Acceptance evidence when its lesson is reached |
|---|---|---|
| F1 | Explicit graph nodes, directed edges, state updates, START/END | Learner can draw and explain the executed path |
| F2 | Fixed paths, conditional routing, and a bounded action loop | A branch executes its intended path; a deliberate loop cannot run forever |
| F3 | Dummy knowledge-base search for policy questions | Answer is grounded in invented retrieved facts; missing facts have an explicit outcome |
| F4 | Dummy order-status tool scoped to a customer | One customer cannot retrieve another customer's order by guessing its ID |
| F5 | Deterministic decision examples before a real model | Fake policy exercises control flow without pretending to be AI |
| F6 | Real model call, then validated model-guided tool decisions | Learner understands messages, output, parsing, approved actions, and failures |
| F7 | Conversation memory and separate thread identities | Conversations stay isolated; per-turn results/hop counters do not remain stale |
| F8 | Local dummy WhatsApp-like webhook | Thin HTTP layer validates input and invokes the same bot usable from CLI/tests |
| F9 | Dummy human handoff; later pause/resume exercise | Learner distinguishes END from interrupt/resume and explains node replay |
| F10 | Scenario tests and failure handling when foundations are understood | Unknown tools, missing facts, tool errors, loops, and ownership are exercised |

## Final independent assessment

After the guided lessons, every explicit capstone request gets a fresh project brief
following CAPSTONE.md and CAPSTONE_HISTORY.md. It must differ in domain, workflow, and
scenarios from prior briefs, not repeat the course support bot with renamed entities.
The learner implements it independently in a new blank folder with NO AI help for
design, implementation, debugging, tests, or review. Runtime LLM usage is allowed.
The agent may generate/log the assignment brief and self-check criteria ONLY—not a
starter, solution, node/edge blueprint, or tailored implementation plan. Official docs
and the learner's notes are allowed.

## Safety / non-goals

- No production WhatsApp sends, real customer data, secrets, credentials, billing,
  production Django dependencies, Redis, Celery, or automatic deployment.
- Initial webhook is a local demo, not full Meta payload/signature verification.
- Demo customer identity is not authentication. Real authorization is a separate concern.
- No eval of model output or arbitrary model-controlled code execution.
- Checkpointing is not exactly-once sending, concurrency control, or an authorization boundary.
- No automatic external tracing, paid calls, or hosted rendering. Ask before adding them.
- Never publish ignored local drafts or source provenance with forced git staging.

## Current requirement priority

**Now:** help the learner trace lesson 1, make their own changes, and explain a second
node's input. **Not now:** build the webhook, install a model adapter, add memory, or
complete remaining lessons. See PROGRESS.md for actual completion status.
