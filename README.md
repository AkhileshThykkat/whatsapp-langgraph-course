# WhatsApp agent course — learn LangGraph one moving part at a time

**Small runnable scripts, not a finished application.** Predict what will happen,
run the example, change one thing, and explain the result. We add one concept at a time.

The goal is to independently build a small model-guided support bot: policy questions,
dummy order lookup, conversation memory, and a local dummy WhatsApp-like webhook.

## Start with lesson 1

From the repository root:

```bash
# Optional: keep uv's cache and any downloaded Python inside this checkout.
export UV_CACHE_DIR="$PWD/.uv-cache"
export UV_PYTHON_INSTALL_DIR="$PWD/.uv-python"

uv sync --locked --python 3.12
uv run --locked python lessons/01_node_and_edge.py
```

Install [uv](https://docs.astral.sh/uv/) first if needed. Package installation needs
internet; the lesson itself runs offline. No API key is needed.

Read **[the lesson guide](lessons/01_node_and_edge.md)** alongside the script.

```text
START → make_reply → END
```

Lesson 1 uses actual LangGraph but is **not yet an AI agent**. Its reply is ordinary
Python text formatting. Tools, loops, a model, memory, and a local webhook arrive one
lesson at a time (see [COURSE.md](COURSE.md)). Nothing in the course sends WhatsApp messages.

## Later lessons

Every lesson runs the same way: `uv run --locked python lessons/NN_name.py`, with its
guide `lessons/NN_name.md` next to it. Two lessons need something extra:

```bash
# Lessons 7-8: optional real Claude call (default is an offline fake model, no key needed)
export ANTHROPIC_API_KEY=...   # your own key; never commit it
uv run --locked --group llm python lessons/07_one_model_call.py --real

# Lesson 12: run the tests
uv run --locked pytest lessons -q
```

## Learn with Claude or another coding agent

Start a session in this repository and say:

> Read agent.md, REQUIREMENTS.md, PROGRESS.md, and TASKS.md, then the lesson 1 guide. Teach me
> at the current checkpoint. Help me predict the state and do the experiment myself;
> do not complete the agent for me.

`CLAUDE.md` contains only `@agent.md`. The lowercase `claude.md` is the same redirect;
`AGENTS.md` points other coding agents to the canonical instructions. `REQUIREMENTS.md`
emphasizes the teaching and eventual bot requirements. `PROGRESS.md` separates what
exists, what has been runtime-verified, what the learner has reviewed, and what remains.

## Teaching format

1. Read one small runnable example.
2. Predict its output before running it.
3. Run it with uv and compare your prediction.
4. Modify one thing yourself using the experiment instructions.
5. Review the behavior before the next lesson is created.

**Simple why:** Tracing and changing a mechanism builds understanding better than
reading a finished generated application.

**Technical explanation:** We introduce state transitions, graph topology, tool
execution, and model inference separately so their responsibilities and failure
modes remain visible instead of hiding behind application abstractions.

Every important decision is explained twice: **Simple why**, then **Technical
explanation**. We introduce automated tests and application structure later, when
they solve a problem the learner has already encountered.

## Files

- `lessons/NN_*.py` — one small runnable example per lesson (01–11).
- `lessons/NN_*.md` — each lesson's explanation, predictions, experiments, and review checkpoint.
- `lessons/support_bot.py` / `lessons/test_support_bot.py` — lesson 12's bot and its tests.
- `COURSE.md` — the progression and which files belong to each lesson.
- `REQUIREMENTS.md` — primary teaching requirements and eventual bot acceptance criteria.
- `PROGRESS.md` — implementation status, review checkpoint, and pending work.
- `TASKS.md` — prediction, modification, debugging, and rebuilding exercises to demonstrate understanding.
- `CAPSTONE.md` — rules for fresh independent assignments; no AI development help.
- `CAPSTONE_HISTORY.md` — history used to ensure a different project on each request.
- `agent.md` — canonical teaching-agent instructions.
- `AGENTS.md` / `CLAUDE.md` / `claude.md` — redirects to those instructions.
- `docs/CONCEPTS.md` — optional background, not a prerequisite to memorize.
- `pyproject.toml` / `uv.lock` — dependency configuration and exact resolved versions.

## Final independent capstone

After the guided lessons, ask for a new assignment following [CAPSTONE.md](CAPSTONE.md).
**Every request gets a different project**, checked against CAPSTONE_HISTORY.md: a new
domain, workflow, and scenarios—not just a renamed support bot. The agent may provide
only the brief/rubric. Build from a blank folder **without AI help for design, coding,
debugging, tests, or review**. Official docs and your notes are allowed. Runtime use
of an LLM inside your product is allowed; AI development assistance is not.

All twelve lessons are written, but the learner has not yet completed lesson 1's
review. Do them in order. There is no production bot or real webhook in this repository.
Use invented data; never commit credentials or production customer information.
