# Lesson 10: the dummy webhook

```text
terminal / test ──────────────────────────────┐
                                              ▼
HTTP POST /webhook → parse JSON → validate → run_bot(phone, text) → graph (lesson 9) → reply
   (the door)          (transport layer)       (service boundary)    (orchestration)
                                              ▲
                        reply returned in the HTTP response, never sent to WhatsApp
```

**New idea:** the webhook is a **door**, not the agent. A thin HTTP layer validates the
input and calls the *same* `run_bot` function that the terminal and tests use.

Everything is local (`127.0.0.1`). The phone numbers are fictional `555-01xx` numbers. The
payload is a simplified invention, **not** Meta's real WhatsApp webhook format.

## Three layers, three jobs

| Layer | Function | Knows about |
|---|---|---|
| Transport | `WebhookHandler.do_POST`, `validate_payload` | HTTP, JSON, status codes |
| Service boundary | `run_bot(bot, phone, text)` | Mapping phone → `thread_id` + demo `customer_id` |
| Orchestration | the graph | State, nodes, tools. **Nothing about HTTP** |

**Simple why:** If the bot only works through the door, you can't test it without
building a house around it.

**Technical explanation:** Keeping HTTP out of the graph lets you test orchestration
without a server, and test HTTP validation without a model or network. Part 1 of the demo
calls `run_bot` directly, and part 2 goes through HTTP. Both run the same graph, with the
same memory, because they share one compiled `bot` and its checkpointer.

## Why the first class appears here

`http.server` requires a subclass of `BaseHTTPRequestHandler` whose `do_POST` method it
calls for each request. We use a class because the standard library's API requires one,
not as an architecture pattern. A framework like FastAPI would hide this, and it would
also be a new dependency. We'll add one only when a lesson needs it.

## What validation is, and what it is not

`validate_payload` checks shape, types, length, and that the sender is a known demo
number. **That is not authentication.** Anyone can type any phone number into a JSON
body. Real WhatsApp webhooks need a verify-token handshake, **signature verification**
of each request, and Meta's actual nested payload schema. None of that is implemented here.

## Duplicate deliveries

Real webhook providers **retry** when they don't get a fast success response, so the
same message can arrive twice. Each payload carries a `message_id` for exactly this
reason. Right now the bot would process a duplicate twice. That is harmless for a
lookup, but not for a refund or an outgoing message. Experiment C is about this.

## Predict before running

1. Ana's second HTTP request says `"When will it arrive?"`. How does the bot know which
   order she means? Which piece of data connects the two HTTP requests?
2. Which requests reach the graph at all? Which are rejected by the transport layer?
3. **Tricky case:** the direct call (part 1) used Ben's number. Did that affect Ana's
   HTTP conversation? Why not?

```bash
uv run --locked python lessons/10_dummy_webhook.py
```

To experiment with `curl`, run `--serve` in one terminal and use the printed command in
another. If your shell has an HTTP proxy configured, add `--noproxy 127.0.0.1` to curl.

## Your experiments

### Experiment A: send your own requests

Run with `--serve` and use curl to send: an empty `text`, a 2000-character `text`, a body
that is a JSON *list*, and a valid follow-up. Predict each status code first.

### Experiment B: prove the bot is HTTP-free

Without starting a server, write three lines of Python that build the bot and call
`run_bot` twice for Ben (an order question, then a follow-up). What did you *not* need?

### Experiment C: make duplicate deliveries safe

Send the same `message_id` twice. Notice that `history` now contains the message twice.
Design (then implement) a small dedupe: where should the "seen message IDs" live, what
should a duplicate return, and what goes wrong if the store is only in memory?

## Review checkpoint

> Trace one HTTP request from bytes to reply: name every function it passes through,
> which layer each belongs to, and the exact point where `phone` becomes a `thread_id`
> and a `customer_id`. Then explain why knowing a phone number is not authentication.

Official reference: Python's [`http.server`](https://docs.python.org/3/library/http.server.html)
and [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).
