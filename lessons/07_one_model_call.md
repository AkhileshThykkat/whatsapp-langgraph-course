# Lesson 7: one model call

```text
customer text → build_request → MODEL → raw text → parse_intent → our code decides
                 (prompt)       (inference)          (validate)     (control flow)
```

**New idea:** a language model is a function from **messages in** to **text out**. Your
code builds the input, sends it, and must check the output before acting on it.

There is **no graph** in this file, on purpose. Lesson 8 puts the model inside a graph.

**Simple why:** First see the model alone, so you know what it does and what it doesn't.

**Technical explanation:** Inference (calling a pretrained model) and orchestration
(deciding which step runs next) are different jobs. A graph alone is not AI, and a model
alone does not run tools or loops. Keeping them apart here makes each one's failures visible.

## Two models, same interface

| | `fake_model` (default) | `real_model` (`--real`) |
|---|---|---|
| Network / cost | none / free | HTTPS to Claude, a few hundredths of a cent per message |
| Output | scripted, **wrong on purpose** for 3 of 5 messages | real model output, usually well formatted |
| Purpose | see every failure path, every time | see the real request/response shape |

Both take the same `request` dict and return text. Because of that shared interface,
the rest of the code doesn't care which one runs.

## What the model actually receives

Look at print `1. REQUEST`. That is **everything** the model sees: the system prompt and
the message list. It does not see your Python variables, your order database, or any
graph state, unless you put them into the request.

## Prompt → request → response → parse

1. **Prompt:** `SYSTEM_PROMPT` asks for JSON only. That is a request, not a guarantee.
2. **Request:** `build_request` assembles the exact data that gets sent.
3. **Response:** text, possibly chatty, cut off, refused, or simply wrong.
4. **Parse + validate:** `parse_intent` uses strict `json.loads` plus an **allowlist**.
   Any failure becomes `intent="unknown"`, with the problem recorded.

**Simple why:** Treat model output like a stranger's form: check every box before using it.

**Technical explanation:** Never `eval()` model output, and don't silently "repair" it.
Silent repair hides how often the format breaks. In production you can make the format
much more reliable with *structured outputs* or *tool calling*. Lesson 8 uses tool
calling. Even then, your code still validates values against what it allows.

## Running the real model (optional)

The real call uses `claude-opus-5-5` (about $4 per million input tokens and $20 per million
output tokens). One classification here uses on the order of a hundred tokens. The script
prints the exact token usage, so you can check.

```bash
export ANTHROPIC_API_KEY=...        # your key; never commit it
uv run --locked --group llm python lessons/07_one_model_call.py --real
```

`--group llm` installs the optional `anthropic` SDK. Without credentials, the script
exits with a message instead of calling anything. The request also sets
`fallbacks="default"`: if a safety classifier declines, the API retries on another model
server-side. The code checks `stop_reason` before it trusts any text.

## Predict before running (fake model)

1. For `"Hello there"`, the raw text *contains* `{"intent": "greeting"}`. Will it parse? Why?
2. For `"Nice lamp!"`, the output is valid JSON. Why is it still rejected?
3. In every failure case, what does "our code" decide? Who made that decision: the model or you?
4. **Tricky case:** `"I want to return order A100"` mentions both. Which intent does the fake
   return, and why? Would a real model necessarily agree?

```bash
uv run --locked python lessons/07_one_model_call.py
```

## Your experiments

### Experiment A: change what the model sees

Add one sentence of invented context to `SYSTEM_PROMPT` (e.g. a new allowed intent
`"shipping"`). What else **must** change for a `"shipping"` answer to be accepted?
Explain why changing the prompt alone is not enough.

### Experiment B: make the parser stricter or looser (and argue about it)

Should `'Sure! {"intent": "greeting"}'` be accepted by extracting the `{...}` part? Write
down one benefit and one risk. Do not implement a regex "repair" until you can explain
what it might accept by mistake.

### Experiment C (optional, costs a fraction of a cent): compare with the real model

Run with `--real`. Which outputs differ from the fake ones? Find the `stop_reason` and
token counts in the output. Then ask the real model something off-topic and see what
the parser does.

## Review checkpoint

> Explain the difference between "the model returned text" and "our application decided
> to route somewhere." Name the exact line where a model's output stops being trusted
> data and becomes a decision.

Official reference: [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview) and [tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview).
