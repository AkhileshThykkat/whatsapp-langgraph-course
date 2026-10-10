"""Lesson 10: a dummy WhatsApp-like webhook. HTTP is a thin door in front of the SAME bot.

Local only (127.0.0.1). Nothing is ever sent to WhatsApp. Payloads and phone numbers are
invented, and this is NOT Meta's real webhook format or signature verification.

    uv run --locked python lessons/10_dummy_webhook.py           # demo: starts, sends, stops
    uv run --locked python lessons/10_dummy_webhook.py --serve   # keep serving for curl
"""

import json
import operator
import re
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Annotated, NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

ORDERS = {
    "A100": {"customer_id": "cust_ana", "status": "shipped", "eta": "14 October"},
    "A200": {"customer_id": "cust_ben", "status": "processing", "eta": "20 October"},
}
# 555-01xx numbers are reserved for fiction. Knowing a number is NOT authentication.
DEMO_CUSTOMERS_BY_PHONE = {"+15550100001": "cust_ana", "+15550100002": "cust_ben"}
MAX_TEXT_LENGTH = 1000
MAX_BODY_BYTES = 10_000


# ---------------------------------------------------------------------------
# The bot: lesson 9's graph, condensed. It knows nothing about HTTP.
# ---------------------------------------------------------------------------
def lookup_order(customer_id: str, order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, "status": order["status"], "eta": order["eta"]}


class ChatState(TypedDict):
    customer_id: str
    message: str
    history: Annotated[list[str], operator.add]
    last_order_id: NotRequired[str]
    tool_result: NotRequired[dict | None]
    reply: NotRequired[str]


def start_turn(state: ChatState) -> dict:
    return {"tool_result": None, "history": [f"customer: {state['message']}"]}


def maybe_lookup(state: ChatState) -> dict:
    match = re.search(r"\b[A-Z]\d{3}\b", state["message"].upper())
    order_id = match.group() if match else None
    if order_id is None and "it" in state["message"].lower().split():
        order_id = state.get("last_order_id")
    if order_id is None:
        return {}
    return {"tool_result": lookup_order(state["customer_id"], order_id), "last_order_id": order_id}


def write_reply(state: ChatState) -> dict:
    result = state.get("tool_result")
    if result and result["found"]:
        reply = f"Order {result['order_id']} is {result['status']}, ETA {result['eta']}."
    elif result:
        reply = f"I couldn't find order {result['order_id']} on your account."
    else:
        reply = "Which order do you mean? Please include its ID, like A100."
    return {"reply": reply, "history": [f"bot: {reply}"]}


def build_bot():
    builder = StateGraph(ChatState)
    builder.add_node("start_turn", start_turn)
    builder.add_node("maybe_lookup", maybe_lookup)
    builder.add_node("write_reply", write_reply)
    builder.add_edge(START, "start_turn")
    builder.add_edge("start_turn", "maybe_lookup")
    builder.add_edge("maybe_lookup", "write_reply")
    builder.add_edge("write_reply", END)
    return builder.compile(checkpointer=InMemorySaver())


def run_bot(bot, phone: str, text: str) -> str:
    # Simple why: One function that terminal, tests, and HTTP all use the same way.
    # Technical explanation: The service boundary. It maps the transport identity (phone)
    # to a thread_id and a demo customer_id, then invokes the graph. Nothing here knows
    # about HTTP, so the bot can be tested without a server.
    config = {"configurable": {"thread_id": f"whatsapp:{phone}"}}
    final_state = bot.invoke({"customer_id": DEMO_CUSTOMERS_BY_PHONE[phone], "message": text}, config)
    return final_state["reply"]


# ---------------------------------------------------------------------------
# The door: HTTP. Only parsing, validation, and status codes live here.
# ---------------------------------------------------------------------------
def validate_payload(data: object) -> str | None:
    # Simple why: Check the envelope before opening it.
    # Technical explanation: Transport validation returns a reason string (-> HTTP 400) or
    # None. It checks shape, types, length and known senders. It is NOT authentication;
    # real WhatsApp webhooks also need signature verification and a verify-token handshake.
    if not isinstance(data, dict):
        return "body must be a JSON object"
    for field in ("message_id", "from", "text"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            return f"'{field}' must be a non-empty string"
    if len(data["text"]) > MAX_TEXT_LENGTH:
        return f"'text' is longer than {MAX_TEXT_LENGTH} characters"
    if data["from"] not in DEMO_CUSTOMERS_BY_PHONE:
        return "unknown sender"
    return None


# Simple why: Python's built-in web server asks us to fill in a template class.
# Technical explanation: http.server calls do_POST on a BaseHTTPRequestHandler subclass
# for each request. This is the first class in the course, and only because the standard
# library's API requires it. self.server.bot is the graph we attach in start_server().
class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            return self.send_json(404, {"error": "not found"})
        # Simple why: Check how big the envelope claims to be before opening it.
        # Technical explanation: Content-Length comes from the client. A non-number would
        # crash int(), a negative value makes read() wait for the client to hang up, and a
        # huge one would pull a huge body into memory. Reject all three before reading.
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return self.send_json(400, {"error": "invalid Content-Length"})
        if length < 0:
            return self.send_json(400, {"error": "invalid Content-Length"})
        if length > MAX_BODY_BYTES:
            return self.send_json(413, {"error": "body too large"})
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):  # bad JSON, or bytes that aren't UTF-8
            return self.send_json(400, {"error": "body is not valid JSON"})
        problem = validate_payload(data)
        if problem:
            return self.send_json(400, {"error": problem})

        reply = run_bot(self.server.bot, data["from"], data["text"])
        # Simple why: Show the reply instead of sending it anywhere.
        # Technical explanation: A real integration would call WhatsApp's send API here, a
        # side effect that needs idempotency and error handling. We return it in the
        # HTTP response instead, so nothing leaves this machine.
        self.send_json(200, {"message_id": data["message_id"], "reply": reply, "sent_to_whatsapp": False})

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # keep the demo output readable
        pass


def start_server(bot, port: int) -> HTTPServer:
    # Simple why: Listen only on this computer.
    # Technical explanation: 127.0.0.1 is unreachable from other machines. Port 0 asks the
    # OS for any free port.
    server = HTTPServer(("127.0.0.1", port), WebhookHandler)
    server.bot = bot
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def post(url: str, raw_body: bytes) -> tuple[int, dict]:
    request = urllib.request.Request(url, data=raw_body, headers={"Content-Type": "application/json"})
    no_proxy_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # local server: skip proxies
    try:
        with no_proxy_opener.open(request) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def main():
    bot = build_bot()

    if "--serve" in sys.argv:
        server = start_server(bot, 8000)
        print("Listening on http://127.0.0.1:8000/webhook (Ctrl+C to stop). Try:")
        print("""  curl -s -X POST http://127.0.0.1:8000/webhook -H 'Content-Type: application/json' \\
       -d '{"message_id": "m1", "from": "+15550100001", "text": "Where is A100?"}'""")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            server.shutdown()
        return

    print("=== 1. Same bot, called directly (terminal / test path) ===")
    print("   run_bot ->", run_bot(bot, "+15550100002", "Where is A200?"))

    server = start_server(bot, 0)
    url = f"http://127.0.0.1:{server.server_port}/webhook"
    print(f"\n=== 2. Same bot, through local HTTP at {url} ===")
    requests = [
        ("Ana asks about A100", {"message_id": "m1", "from": "+15550100001", "text": "Where is A100?"}),
        ("Ana follows up (memory via thread)", {"message_id": "m2", "from": "+15550100001", "text": "When will it arrive?"}),
        ("Ana tries Ben's order", {"message_id": "m3", "from": "+15550100001", "text": "Where is A200?"}),
        ("Missing 'text'", {"message_id": "m4", "from": "+15550100001"}),
        ("Unknown sender", {"message_id": "m5", "from": "+15550199999", "text": "Hi"}),
    ]
    for label, payload in requests:
        status, body = post(url, json.dumps(payload).encode())
        print(f"   {label:38} -> HTTP {status} {body}")
    status, body = post(url, b"{not json")
    print(f"   {'Broken JSON':38} -> HTTP {status} {body}")

    server.shutdown()
    print("\nServer stopped. Nothing was sent to WhatsApp.")


if __name__ == "__main__":
    main()
