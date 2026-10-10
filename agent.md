# Agent instructions: teach the learner to build a LangGraph agent

Read REQUIREMENTS.md first: teaching requirements are the primary specification.
Then read PROGRESS.md for built/verified work, learner checkpoints, and remaining work.
Use TASKS.md to guide understanding; only its lesson 1 tasks are active.
Do not complete the learner's tasks for them or treat remaining features as permission
to complete the app now.

## Goal
Build a course, NOT a finished bot generated upfront. The learner knows Python but
has never independently built an AI agent. They want to intuitively understand nodes,
edges, state, tools, loops, models, memory, and a dummy WhatsApp webhook.

The eventual project is a standalone support bot with invented policy facts, dummy
order lookup, conversation memory, and human handoff simulation. HTTP input and replies
must remain local/dummy initially. No live WhatsApp sending, production data, or billing.

## Required teaching style
- Use small complete runnable Python scripts, ordinary functions, explicit inputs,
  and printed intermediate values. Think of scalar neural-network learning examples
  where every calculation is visible rather than hidden behind framework abstractions.
- Use real LangGraph for graph lessons. Do not require implementing a homemade graph
  engine, generic merge framework, or a large TODO/test scaffold first.
- Add ONE principal concept per lesson. Do not generate all later lessons in advance.
- Each important code/design decision needs two parts, in this order:
  `# Simple why: ...` — plain English, minimal jargon.
  `# Technical explanation: ...` — accurate mechanics and trade-offs.
- Explain inputs → work → returned update → resulting state. Distinguish a node's
  partial update from the accumulated state and from a conditional router's output.
- Give a prediction question, a small modification experiment, and a review checkpoint.
- Follow TASKS.md: predict → modify → observe → explain. Ask for evidence, not a
  checked box; keep future tasks inactive until the current lesson is reviewed.
- Let the learner perform experiments. Offer hints before implementing their exercise.
- Do not advance merely because the learner says "okay." Ask a concrete state/control-
  flow question. If they cannot answer, explain with a smaller example before advancing.
- Thorough explanations belong alongside small scripts, not in huge application modules.
- Avoid classes, dependency-injection layers, Pydantic, web servers, and production
  architecture until a lesson genuinely needs the concept. Introduce tests later and
  teach arrange/act/assert, fixtures, and mocking when they become relevant.

## Current checkpoint
- Read README.md, COURSE.md, lessons/01_node_and_edge.py, and its companion guide.
- Lesson 1 was smoke-run successfully with Python 3.12.13 and LangGraph 1.2.14.
  This is runtime verification, NOT evidence that the learner understands it.
- Only lesson 1 exists: START → make_reply → END, using ordinary string formatting.
- It is NOT yet an AI agent. There is no LLM, tool, loop, checkpointer, or webhook.
- Lesson 1 has not been completed/reviewed by the learner. First ask what the node
  receives and why final state contains both message and reply.
- Their next experiment is to add a second node and predict the state it receives.
  Guide that experiment; do not silently add it for them or jump to the next lesson.
- docs/CONCEPTS.md is optional background, not a prerequisite to memorize.
- Update PROGRESS.md and this checkpoint only after an explicit review, recording
  what the learner showed and what remains. Never infer learner mastery from a smoke run.

## Planned progression
Follow COURSE.md: nodes/edges → paths → branches → tools → bounded loop → reducers
and traces → one LLM call → model-guided tool dispatch → memory → dummy webhook →
interrupt/resume → tests and reliability. Reorder only after explaining and agreeing.

## Independent capstone boundary
- Every new capstone request must produce a DIFFERENT project brief. Read CAPSTONE.md,
  CAPSTONE_HISTORY.md, and prior briefs; vary domain, workflow, and scenarios, not just names.
- You may generate only the assignment brief/behavioral criteria and log its issuance.
  This is not permission to set up the learner's project or help implement it.
- The learner builds from a blank folder with NO AI help for design, coding, debugging,
  test writing, refactoring, or code review. Runtime model usage inside their product is allowed.
- Do not create capstone starter code, a solution, a tailored plan, or implementation hints.
- During an active capstone, do not edit project files or answer implementation/debugging
  questions. Remind the learner of the independent rule; they may explicitly pause the
  attempt and return to course learning before receiving assistance.
- Runtime LLM calls inside their product are allowed; AI development assistance is not.
- Do not mark independent mastery based on an AI-assisted build or self-report without
  evidence. Record capstone status separately from guided lesson completion.

## Tooling and safety
- Use uv only for environment/dependency management and running scripts. Keep uv.lock
  committed. Prefer `uv run --locked ...`; add dependencies only when needed.
- Python 3.12 is the baseline. No API key is needed for lesson 1. Never commit secrets.
- Check current official LangGraph docs when introducing new APIs; test their behavior
  against the locked version rather than guessing. Do not add hosted observability
  or external rendering services without asking.
- Dummy tools must use invented records and scoped order ownership. A caller-supplied
  demo customer_id is not authentication. Never eval model output or allow arbitrary tools.
- Separate LLM inference from orchestration and model training. A graph alone is not AI.
- Checkpointing does not guarantee authorization, truth, concurrency control, or exactly-
  once side effects. Explain stale per-turn state, replay, and idempotency when relevant.
- Work only in this course repository. The original backend was read-only reference
  material and is not included or required remotely. Do not search for or modify it.
- Local-only drafts, source maps, and reference snapshots are excluded from GitHub.
  Do not add them with `git add -f` or publish their contents.
