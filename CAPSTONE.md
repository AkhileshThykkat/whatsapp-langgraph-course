# Independent capstones — a different project on every request

## Primary requirements

1. **Every request for a capstone gets a fresh assignment**, not the same support bot
   with renamed entities. Vary the domain, primary workflow, data, and acceptance scenarios.
2. The learner builds from a blank folder with **NO AI development assistance**.
3. An agent may generate the **assignment brief and behavioral acceptance criteria only**.
   It must not provide an architecture blueprint, node/edge solution, starter, code,
   debugging hints, tests, refactor, or AI code review for the independent attempt.

Runtime use of an LLM inside the learner's product is allowed; using an AI assistant
to develop that product is not. Official docs, non-AI tools, and the learner's notes
are allowed. Turn off AI coding completions during the attempt.

**Simple why:** Repeating the course bot can test copying rather than understanding.

**Technical explanation:** Applying the same concepts to a new domain checks transfer:
independent state contracts, control flow, tool boundaries, identity, persistence, and
failure handling. Novelty must change observable behavior, not merely names or prompts.

## When to begin

Finish and review the prerequisite guided lessons first. No capstone is currently
assigned or started. Lesson 1 itself has not been learner-reviewed.

When ready, the learner can ask:

> Give me a new independent capstone. Read the assignment history, choose a genuinely
> different project, and give only the brief and self-check criteria—not a solution.

Generating a brief is the sole permitted AI contribution to the capstone. Do not
interpret a request for a fresh brief as permission to set up or implement its project.

## Rules for the agent generating a brief

1. Read REQUIREMENTS.md, PROGRESS.md, and CAPSTONE_HISTORY.md. Use skills the learner
   has demonstrated; do not require unfamiliar infrastructure or paid integrations.
2. Read earlier `capstones/*-brief.md` files if present. Do not repeat an issued
   assignment. The original static support-bot draft was replaced; do not use it as
   the default first capstone.
3. Choose a new domain and materially different primary workflow. Possible areas
   include resource reservations, document triage, travel planning, learning support,
   or inventory operations. These are areas to choose from, not preset solutions.
   If areas have been used, expand the set rather than recycle an assignment.
4. Change at least the domain, main workflow, and multiple acceptance scenarios relative
   to earlier assignments. Do not reskin order lookup as another ID lookup and call it new.
5. Keep it small: a few capabilities, invented local data, no mandatory deployment,
   real-world sending, production credentials, or unlearned infrastructure.
6. Supply ONLY the problem, invented-data requirements, user-visible behaviors,
   failure/isolation scenarios, permitted resources, deliverables, and assessment criteria.
   The learner chooses modules, state fields, node names, edge topology, tool interface,
   model adapter, storage approach, and implementation.
7. Save the issued brief as `capstones/NNN-brief.md` and log it in CAPSTONE_HISTORY.md.
   Do not overwrite old briefs. Include why it differs from previous assignments.
   Create these files only when a new assignment is actually requested.
8. Keep assignment issuance distinct from an attempt starting or being completed.
   Do not create a solution directory, project scaffold, or generated test code.

Novelty is checked against this repository's recorded history, not imagined history
from other sessions or repositories. If prior assignments are mentioned but missing,
ask for their titles/briefs rather than claiming you checked them.

## Skills each assignment must assess, with domain-specific scenarios

| Requirement | Required evidence in the learner's independent project |
|---|---|
| Actual LangGraph | Learner can explain the nodes, directed edges, state, and termination |
| Branching and tool use | Different inputs take deliberate paths; tools return observable facts |
| Model-guided decisions | A pretrained model requests only validated, approved capabilities |
| Observe-and-decide loop | New tool observations reach the next decision before an answer/action |
| Bounded execution | Repeated actions cannot run indefinitely; stop policy is visible |
| Scoped access | One invented user's private records/context are not visible to another |
| Conversation continuity | Follow-up context works; separate threads remain isolated |
| Per-turn correctness | Old observations/counters do not silently control a new turn |
| CLI and local HTTP | Equivalent input reaches the same underlying behavior through both |
| Honest failure outcome | Missing facts, invalid model output, and tool/model errors are deliberate |
| Reproducibility and tests | uv.lock, runnable instructions, and deterministic non-paid scenario tests |

A pause/resume workflow is optional unless the learner specifically wants that concept
assessed. If included, they must explain replay and side effects. A terminal outcome
is not automatically an interrupt.

## What every issued brief must contain

- A unique title and a short domain/problem statement.
- A note explaining how it differs from earlier assignments.
- Invented input/data expectations without prescribing an implementation schema.
- Concrete success, missing-data, invalid-action, tool-failure, loop-limit, isolation,
  follow-up, and interface scenarios appropriate to that domain.
- A list of deliverables: independently authored source, uv files, run instructions,
  diagram/explanation, tests, scenario outcomes, debugging log, and limitations.
- The no-AI-development-assistance rule and the permitted-resource boundary.
- A self-check rubric based on behavior and explanation, not the existence of files.

No answers, code snippets, recommended graph route, node list, or tailored build plan.

## Safety and independent-work rules

- Use invented local data. No real user data, billing, notifications, production
  service calls, or automatic deployment is needed.
- Keep credentials out of git. Never eval model output or grant arbitrary capabilities.
- Do not claim demo caller identity is authentication. Document production limitations.
- Do not copy an abandoned draft or a finished generated course solution wholesale.
- The learner personally creates their blank project and authors its source/tests/docs.
- If stuck, use their observations and official docs. If they deliberately pause the
  independent attempt to receive AI help, record that honestly; it is no longer an
  uninterrupted independent completion.
- Agents must not debug or review code during an active independent attempt. A human
  reviewer or the learner's recorded self-checks may assess it.

## Completion rule

An issued assignment is complete only when its observable acceptance scenarios work,
the learner can trace and explain their own graph, clean setup is reproducible, and
independent development is honestly documented. Guided lesson progress, assignment
issuance, runtime verification, and independent mastery are different statuses.
