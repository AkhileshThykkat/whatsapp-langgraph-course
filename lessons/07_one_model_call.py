"""Lesson 7: one model call. No graph in this file, on purpose.

Default: a FAKE model. Offline, free, deterministic, and sometimes wrong on purpose.
Real Claude call (needs credentials; a few hundredths of a cent per message):

    uv run --locked --group llm python lessons/07_one_model_call.py --real
"""

import json
import sys

ALLOWED_INTENTS = {"order_status", "returns_policy", "greeting", "unknown"}

# Simple why: The instructions the model reads before the customer's words.
# Technical explanation: A system prompt is plain text sent with every request. It
# guides the model but does not enforce anything. That is why we still parse and check
# the output below.
SYSTEM_PROMPT = (
    "You classify messages sent to Lumen Lamps customer support (an invented demo shop). "
    'Reply with ONLY a JSON object such as {"intent": "order_status"} and nothing else. '
    "Allowed intents: order_status, returns_policy, greeting, unknown."
)


def build_request(customer_message: str) -> dict:
    # Simple why: Write down exactly what the model will read.
    # Technical explanation: The model receives ONLY this: a system prompt plus a list of
    # role-tagged messages. It cannot see our Python variables, our tools, or graph state
    # unless we put them into this request ourselves.
    return {"system": SYSTEM_PROMPT, "messages": [{"role": "user", "content": customer_message}]}


def fake_model(request: dict) -> str:
    """Stands in for an LLM. Returns TEXT, and sometimes text that breaks our format."""
    text = request["messages"][-1]["content"].lower()
    if "order" in text:
        return '{"intent": "order_status"}'
    if "refund" in text or "return" in text:
        return '{"intent": "returns_policy"}'
    if "hello" in text:
        return 'Sure! Here you go: {"intent": "greeting"}'   # chatty: not pure JSON
    if "lamp" in text:
        return '{"intent": "buy_a_lamp"}'                    # valid JSON, unknown value
    return "I am not sure what this customer wants."         # not JSON at all


def real_model(request: dict) -> str:
    # Simple why: Only import the SDK when you ask for a real call.
    # Technical explanation: 'anthropic' lives in the optional 'llm' dependency group, so
    # the default offline install stays small and this lesson runs without it.
    try:
        import anthropic
    except ImportError:
        sys.exit("The SDK is not installed. Run with: uv run --locked --group llm python ...")

    # Simple why: The client finds your API key itself; never paste keys into code.
    # Technical explanation: Anthropic() reads ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN,
    # or an `ant auth login` profile). Keep keys in your shell environment, not in git.
    client = anthropic.Anthropic()
    try:
        # Simple why: Send the request over the network and wait for the reply.
        # Technical explanation: One HTTPS request to the Messages API. The model is
        # pretrained; we are running inference, not training it. effort="low" suits a
        # tiny classification. The 'fallbacks' beta asks the API to retry on another
        # model server-side if this model's safety classifier declines the request.
        response = client.beta.messages.create(
            model="claude-opus-5-5",
            max_tokens=1024,
            system=request["system"],
            messages=request["messages"],
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except TypeError as error:  # raised when no credentials can be found
        sys.exit(f"No Claude credentials found ({error}). Set ANTHROPIC_API_KEY first.")
    except anthropic.APIConnectionError:
        return "<network error>"
    except anthropic.APIStatusError as error:
        return f"<API error {error.status_code}>"

    print(f"   (stop_reason={response.stop_reason}, tokens in={response.usage.input_tokens}, "
          f"out={response.usage.output_tokens}, model={response.model})")

    # Simple why: Check WHY the model stopped before trusting what it wrote.
    # Technical explanation: 'refusal' means a safety decline; 'max_tokens' means the text
    # was cut off. Either way the content is not a complete answer.
    if response.stop_reason in ("refusal", "max_tokens"):
        return f"<no usable answer: {response.stop_reason}>"

    # Simple why: The reply can contain several pieces; we only want the text pieces.
    # Technical explanation: response.content is a list of typed blocks. This model thinks
    # before answering, so 'thinking' blocks may appear before the 'text' block.
    return "".join(block.text for block in response.content if block.type == "text")


def parse_intent(raw_text: str) -> dict:
    # Simple why: Never trust the model's text blindly; check it like user input.
    # Technical explanation: Strict json.loads plus an allowlist check. Anything else is a
    # parse failure with an explicit, safe fallback ('unknown'). We never eval() output,
    # and we do not quietly "repair" it, because that hides how often the format breaks.
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as error:
        return {"ok": False, "intent": "unknown", "problem": f"not JSON ({error.msg})"}
    intent = data.get("intent") if isinstance(data, dict) else None
    # Check the TYPE before the allowlist: a list or dict cannot be looked up in a set.
    if not isinstance(intent, str) or intent not in ALLOWED_INTENTS:
        return {"ok": False, "intent": "unknown", "problem": f"not an allowed intent: {data!r}"}
    return {"ok": True, "intent": intent, "problem": None}


def main():
    use_real_model = "--real" in sys.argv
    call_model = real_model if use_real_model else fake_model
    print("MODEL:", "real Claude (claude-opus-5-5)" if use_real_model else "fake_model (offline)")

    for message in ["Where is my order?", "Can I get a refund?", "Hello there", "Nice lamp!", "asdf"]:
        print(f"\n=== {message!r} ===")
        request = build_request(message)
        print("1. REQUEST (all the model sees):", request["messages"])
        raw_text = call_model(request)
        print("2. RAW RESPONSE TEXT:          ", repr(raw_text))
        parsed = parse_intent(raw_text)
        print("3. PARSED + VALIDATED:         ", parsed)
        print("4. OUR CODE DECIDES:           ", f"route to '{parsed['intent']}'")


if __name__ == "__main__":
    main()
