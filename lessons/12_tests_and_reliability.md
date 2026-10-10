# Lesson 12: tests and reliability

Files: `support_bot.py` (the bot) and `test_support_bot.py` (its tests). The file names
have no number because Python can only `import` names that start with a letter.

```text
START → start_turn → decide ─"act"────────→ act ─→ decide (loop)
                        ├────"reply"───────→ reply ──────→ END
                        ├────"handoff"─────→ handoff ────→ END
                        └────"step_limit"──→ step_limit ─→ END
```

**New idea:** turn behaviours you have already **watched by hand** into **automated
tests** that fail loudly when something breaks.

`support_bot.py` brings the earlier lessons together: tools with ownership checks (4), a
bounded loop (5), reducers (6), a model-shaped decision function (7–8), and per-turn
reset with memory (9). It adds one thing: tool **crashes** become observations at the
boundary, as lesson 4's Experiment C hinted.

```bash
uv run --locked python lessons/support_bot.py   # demo
uv run --locked pytest lessons -q               # tests
```

## Why tests now, and not in lesson 1?

**Simple why:** A test is a written-down prediction. You can only write good predictions
for behaviour you understand.

**Technical explanation:** Each test here encodes a scenario from an earlier lesson:
ownership (4), missing facts (4), unknown tools (8), loop limits (5), thread isolation and
stale per-turn data (9). Writing the tests *after* observing the behaviour means each
assertion has a reason you can explain.

## Arrange → Act → Assert

```python
def test_own_order_status_comes_from_the_tool():
    # Arrange: build the world for this one test
    model, _ = scripted_model({"action": "lookup_order", "args": {"order_id": "A100"}},
                              {"action": "reply", "text": "Your order has shipped."})
    graph = support_bot.build_graph(model)
    # Act: do exactly one thing
    state = support_bot.run_turn(graph, "cust_ana", "Where is A100?")
    # Assert: check observable results
    assert state["observations"][0]["result"]["status"] == "shipped"
```

**Simple why:** Set up, do it, check it. One behaviour per test.

**Technical explanation:** When each test has one Act step, a failure points to one
behaviour. Most assertions check *state and observations*, such as `outcome`, tool results,
and what the model was shown. They avoid reply wording that a scripted model made up,
because asserting on that would only test the script.

## Test doubles: fakes, spies and `monkeypatch`

| Tool | In this file | Purpose |
|---|---|---|
| **Fake** (scripted model) | `scripted_model(...)` | Predictable decisions, no network, no cost |
| **Spy** | `calls = []` lambdas in the unknown-action test | Prove that something did *not* happen |
| **`monkeypatch`** | `monkeypatch.setattr(support_bot, "lookup_order", ...)` | Temporarily replace a function; pytest restores it after the test |

**Simple why:** To test the bot's rules, replace the unpredictable or slow parts with
predictable stand-ins.

**Technical explanation:** `build_graph(model)` accepts the model as a plain argument, so
tests inject fakes without any framework. `monkeypatch` swaps a module attribute.
That works because `execute_action` looks up `lookup_order` at call time. A real model is
*not* tested here: a model's behaviour is checked with evaluations, not unit tests.

## Fixtures

`checkpointer()` is a **fixture**: pytest calls it for each test that has a parameter with
that name. Every test gets a fresh `InMemorySaver`. Shared state between tests causes
failures that depend on test order, which are very hard to debug.

## Reliability scenarios covered

| Failure | Test | Defence |
|---|---|---|
| Reading another customer's order | `test_customer_cannot_read_another_customers_order` | Ownership check inside the tool |
| Model requests a non-existent tool | `test_unknown_action_is_rejected_and_no_tool_runs` | Allowlist in `execute_action` |
| Malformed model output | `test_malformed_reply_is_not_sent_to_the_customer` | Validation in `route_after_decide` |
| Tool crashes | `test_tool_crash_becomes_an_observation_not_an_exception` | `try/except` at the boundary; no internals in the reply |
| Endless loop | `test_loop_stops_at_the_decision_limit` | `max_decisions` → `step_limit` outcome |
| Missing fact | `test_missing_policy_fact_is_an_explicit_outcome` | `found: False`, never invented |
| Conversation leaks | `test_threads_are_isolated`, `test_per_turn_fields_reset_...` | `thread_id` + `start_turn` reset |

## Predict before running

1. In `test_loop_stops_at_the_decision_limit`, why are there 2 observations, not 3?
2. In the unknown-action test, why is `calls == []` stronger evidence than checking the reply?
3. **Tricky case:** delete `"observations": []` from `start_turn`. Which tests fail, and why?
   Which tests *still pass*, even though the bot is now wrong?

## Your experiments

### Experiment A: watch a test catch a bug

Break the ownership check in `lookup_order` (remove the `customer_id` comparison). Run the
tests. Read the failure output: which tests fail, and does the message tell you *why*?
Restore it.

### Experiment B: write your own test (arrange/act/assert)

Write a test for a validation rule in `execute_action`: a `search_policy` request with an
empty topic is rejected and no tool runs. Write the three AAA comments
first, then fill them in. Make it fail once on purpose to prove it can.

### Experiment C: test the handoff path

Write a test where the scripted model returns `{"action": "handoff"}` right away. What
should `outcome`, `decisions`, and `observations` be? Predict first.

### Experiment D: an idea from lesson 10 or 11

Pick one: duplicate `message_id` delivery (lesson 10) or double notification on resume
(lesson 11). Write a test that **fails** on the current lesson code, then fix that code
so the test passes.

## Review checkpoint

> Pick one test. Explain its arrange/act/assert parts, which earlier lesson's behaviour it
> protects, which test double it uses and why, and show the failure it produces when the
> protected code is broken.

## After this lesson

The guided course is complete when **you** can explain these behaviours and have done
the experiments, not when these files exist. Then you are ready for the independent
capstone in `CAPSTONE.md`: a different project, from a blank folder, with no AI help.

Official reference: [pytest: how to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
and [monkeypatch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html).
