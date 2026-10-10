# Progress and handoff

## Most important requirement

**Teach the learner to build and understand the agent themselves. Do not complete the
bot or the learner's experiments for them.** Read REQUIREMENTS.md before coding.

All twelve lessons were written on 2026-10-10 at the learner's explicit request.
**Lesson material existing is not learner progress.** The learner is still at lesson 1.

## Built and verified (implementation status, not learner mastery)

| Item | Implementation status | Verification / limitation |
|---|---|---|
| Course roadmap | COURSE.md lists all 12 lessons and their files | Take in order; each lesson gives away the previous lesson's main experiment |
| Teaching requirements | REQUIREMENTS.md and agent.md | Two-part reasoning, tiny scripts, learner experiments, review gates |
| Understanding tasks | TASKS.md | Lesson 1 active; lessons 2–12 listed and locked behind each gate |
| Fresh independent capstone rules | CAPSTONE.md / CAPSTONE_HISTORY.md | Unchanged; no brief issued |
| Lesson 1: node and edge | `01_node_and_edge` (.py + .md) | Smoke run: `{'message': 'Hello', 'reply': 'Demo reply to: Hello'}` |
| Lesson 2: path of nodes | `02_path_of_nodes` | Smoke run passed; three nodes write three different keys |
| Lesson 3: branch | `03_branch` | Smoke run passed; each of 4 messages runs exactly one branch node |
| Lesson 4: tools + ownership | `04_tools` | Smoke run passed; cust_ana cannot see A200; missing fact → explicit reply |
| Lesson 5: bounded loop | `05_loop` | Smoke run passed; last scenario hits `MAX_DECISIONS` by design |
| Lesson 6: reducers + streams | `06_reducers_and_traces` | Smoke run passed; `updates` vs `values` output shown |
| Lesson 7: one model call | `07_one_model_call` | Fake model run passed (3 of 5 outputs fail parsing on purpose). `--real` path **not exercised**: no credentials in the build environment; missing-credential path verified to exit cleanly |
| Lesson 8: model-guided graph | `08_model_guided_graph` | Fake model run passed (unknown tool rejected, decision cap hit). `--real` (Claude tool use) **not exercised against the live API** for the same reason |
| Lesson 9: memory | `09_memory` | Smoke run passed; thread isolation, "it" resolved from memory, restart loses memory |
| Lesson 10: dummy webhook | `10_dummy_webhook` | Demo run passed (200/400 cases); `--serve` answered a curl request on 127.0.0.1 |
| Lesson 11: interrupt/resume | `11_human_handoff` | Smoke run passed; node replay visibly sends the notification twice (learner fixes it) |
| Lesson 12: tests | `support_bot.py`, `test_support_bot.py`, `12_tests_and_reliability.md` | 14 tests pass; deliberately breaking ownership or the allowlist fails 2 tests each |
| uv environment and lockfile | `uv.lock` committed | LangGraph 1.2.14; optional `llm` group (anthropic 1.13.0); `dev` group (pytest 9.1.1) |
| General concept orientation | docs/CONCEPTS.md | Optional background; not a prerequisite or proof of understanding |

Verification commands (run 2026-10-10, Python 3.12.3):

```bash
uv run --locked python lessons/NN_name.py   # every lesson script exits 0
uv run --locked pytest lessons -q           # 14 passed
```

**Runtime verification is not learner completion.** Passing scripts and tests that the
assistant wrote prove the material runs. They are not evidence that the learner understands it.

## Learner checkpoint — lesson 1, NOT completed yet

- [ ] Predict what make_reply receives.
- [ ] Explain the difference between its returned update and the final state.
- [ ] Change the input and reply text, predicting output before running.
- [ ] Add a second node personally, with guidance rather than a supplied full solution.
- [ ] Explain which reply wins and what the second node can see.
- [ ] Have the teaching agent review the explanation and modification.

**First question for the next Claude session:**

> Why does the final state contain both message and reply when make_reply returns
> only a dictionary containing reply?

Use TASKS.md in order: predict, vary data, add a node, break an edge, and rebuild.
Do not jump ahead if the current task is unclear or implement experiments for the learner.

## Learner review status per lesson

| Lesson | Requirement IDs | Material | Learner review |
|---|---|---|---|
| 1 Node and edge | F1 / T6 | available | **current**, not reviewed |
| 2 Path of nodes | F1 | available | locked |
| 3 Branch | F2 | available | locked |
| 4 Tools and ownership | F3–F4 | available | locked |
| 5 Bounded loop | F2 / F5 | available | locked |
| 6 Reducers and traces | F1 | available | locked |
| 7 One model call | F6 | available | locked |
| 8 Model-guided tool selection | F6 | available | locked |
| 9 Conversation memory | F7 | available | locked |
| 10 Dummy webhook | F8 | available | locked |
| 11 Human handoff / interrupt | F9 | available | locked |
| 12 Tests and reliability | F10 | available | locked |

## Independent capstone — NOT started

- [ ] Complete the prerequisite guided lessons and reviews.
- [ ] Request a fresh brief; agent checks history and records a distinct assignment.
- [ ] Start a new project from a blank folder personally.
- [ ] Meet that brief's behavioral criteria without AI development help.
- [ ] Author tests, documentation, diagram, and debugging log personally.
- [ ] Record scenario evidence and the no-AI-assistance declaration honestly.

No capstone assignment has been issued or started. Each explicit future request must
produce a different project following the recorded history. Assignment briefs/rubrics
are allowed; agents must not generate a starter, solution plan, implementation, test
suite, debugging fixes, or code review. Guided lesson 1 remains the current checkpoint.

## How to update progress

Only mark a learner checkpoint complete after they show the behavior and explain it.
Record the evidence, affected script, remaining question, and next small experiment.
Keep implementation status distinct from learner review. Do not infer mastery from
"okay," passing code generated by the assistant, or the presence of a file.

## Boundaries carried forward

This is a public, standalone learning repository. Private source maps, abandoned drafts,
reference snapshots, caches, and environments are excluded. The original application
is not included and is not required remotely. Never try to find it or modify it.

All data in the lessons is invented. Nothing sends WhatsApp messages; the webhook binds
to 127.0.0.1 only. Real model calls happen only with `--real` and the learner's own
credentials; no key is stored in the repository.
