"""Lesson 12 tests: behaviours you have already watched by hand in lessons 4-11.

Run:  uv run --locked pytest lessons -q
Each test follows Arrange (set up) -> Act (do one thing) -> Assert (check the result).
"""

import pytest
from langgraph.checkpoint.memory import InMemorySaver

import support_bot


def scripted_model(*decisions):
    """A test double: returns `decisions` in order and records every view it was shown."""
    remaining = list(decisions)
    seen_views = []

    def model(view):
        seen_views.append(view)
        return remaining.pop(0) if remaining else {"action": "reply", "text": "(script finished)"}

    return model, seen_views


# Simple why: Every test gets its own empty filing cabinet, so tests cannot affect each other.
# Technical explanation: A pytest fixture is a function pytest calls for each test that names
# it as a parameter. Function scope (the default) means a fresh InMemorySaver per test.
@pytest.fixture
def checkpointer():
    return InMemorySaver()


# --- Tools on their own: plain unit tests ------------------------------------
@pytest.mark.parametrize(
    ("customer_id", "order_id", "expected_found"),
    [("cust_ana", "A100", True), ("cust_ana", "A200", False), ("cust_ben", "A200", True), ("cust_ana", "Z999", False)],
)
def test_lookup_order_only_finds_the_callers_own_orders(customer_id, order_id, expected_found):
    result = support_bot.lookup_order(customer_id, order_id)
    assert result["found"] is expected_found


def test_missing_policy_fact_is_an_explicit_outcome():
    assert support_bot.search_policy("price_match") == {"found": False, "topic": "price_match"}


# --- The whole graph, with a scripted model -----------------------------------
def test_own_order_status_comes_from_the_tool():
    # Arrange
    model, _ = scripted_model(
        {"action": "lookup_order", "args": {"order_id": "A100"}},
        {"action": "reply", "text": "Your order has shipped."},
    )
    graph = support_bot.build_graph(model)

    # Act
    state = support_bot.run_turn(graph, "cust_ana", "Where is A100?")

    # Assert
    assert state["outcome"] == "answered"
    assert state["observations"][0]["result"] == {"found": True, "order_id": "A100", "status": "shipped", "eta": "14 October"}


def test_customer_cannot_read_another_customers_order():
    model, _ = scripted_model({"action": "lookup_order", "args": {"order_id": "A200"}})
    graph = support_bot.build_graph(model)

    state = support_bot.run_turn(graph, "cust_ana", "Where is A200?")

    assert state["observations"][0]["result"] == {"found": False, "order_id": "A200"}
    assert "processing" not in str(state["observations"])


def test_unknown_action_is_rejected_and_no_tool_runs(monkeypatch):
    # Arrange: replace both tools with spies that record any call.
    calls = []
    monkeypatch.setattr(support_bot, "lookup_order", lambda *args: calls.append(("lookup_order", args)))
    monkeypatch.setattr(support_bot, "search_policy", lambda *args: calls.append(("search_policy", args)))
    model, _ = scripted_model({"action": "delete_all_orders", "args": {}}, {"action": "reply", "text": "Sorry."})
    graph = support_bot.build_graph(model)

    # Act
    state = support_bot.run_turn(graph, "cust_ana", "Delete everything")

    # Assert
    assert state["observations"][0]["status"] == "rejected"
    assert calls == []


def test_tool_crash_becomes_an_observation_not_an_exception(monkeypatch):
    def broken_lookup(customer_id, order_id):
        raise RuntimeError("database down")

    monkeypatch.setattr(support_bot, "lookup_order", broken_lookup)
    graph = support_bot.build_graph(support_bot.keyword_model)

    state = support_bot.run_turn(graph, "cust_ana", "Where is A100?")

    assert state["observations"][0] == {"action": "lookup_order", "status": "error", "detail": "RuntimeError"}
    assert state["outcome"] == "handoff"
    assert "database" not in state["reply"]


def test_malformed_reply_is_not_sent_to_the_customer():
    model, _ = scripted_model({"action": "reply"}, {"action": "reply", "text": "Fixed reply."})
    graph = support_bot.build_graph(model)

    state = support_bot.run_turn(graph, "cust_ana", "Hi")

    assert state["observations"][0]["status"] == "rejected"
    assert state["reply"] == "Fixed reply."


def test_loop_stops_at_the_decision_limit():
    def model_that_never_stops(view):
        return {"action": "lookup_order", "args": {"order_id": "A100"}}

    graph = support_bot.build_graph(model_that_never_stops, max_decisions=3)

    state = support_bot.run_turn(graph, "cust_ana", "Where is A100?")

    assert state["outcome"] == "step_limit"
    assert state["decisions"] == 3
    assert len(state["observations"]) == 2  # the 3rd request was refused by the limit


def test_model_sees_observations_from_earlier_steps():
    model, seen_views = scripted_model(
        {"action": "search_policy", "args": {"topic": "returns"}},
        {"action": "reply", "text": "30 days."},
    )
    graph = support_bot.build_graph(model)

    support_bot.run_turn(graph, "cust_ana", "Can I return it?")

    assert seen_views[0]["observations"] == []
    assert seen_views[1]["observations"][0]["result"]["found"] is True


# --- Memory (lesson 9) -----------------------------------------------------------
def test_threads_are_isolated(checkpointer):
    graph = support_bot.build_graph(support_bot.keyword_model, checkpointer=checkpointer)

    support_bot.run_turn(graph, "cust_ana", "Where is A100?", thread_id="ana")
    ben_state = support_bot.run_turn(graph, "cust_ben", "Thanks", thread_id="ben")

    assert ben_state["history"] == ["customer: Thanks", "bot: You're welcome!"]


def test_per_turn_fields_reset_but_history_persists(checkpointer):
    graph = support_bot.build_graph(support_bot.keyword_model, checkpointer=checkpointer)

    support_bot.run_turn(graph, "cust_ana", "Where is A100?", thread_id="ana")
    second = support_bot.run_turn(graph, "cust_ana", "Thanks", thread_id="ana")

    assert second["observations"] == []
    assert second["decisions"] == 1
    assert len(second["history"]) == 4
