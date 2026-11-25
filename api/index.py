"""
Single Vercel entrypoint for the SmileCare CRM API.

Routes:
    GET  /api/config              -> live/demo mode (never returns the key)
    POST /api/call                -> ask Bolna to place the confirmation call
    GET  /api/execution?id=...    -> call status, transcript, extracted outcome
    GET  /                        -> public/index.html (fallback if Vercel doesn't serve it statically)

The Bolna API key is read from the BOLNA_API_KEY environment variable and never leaves the server.
Standard library only.
"""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

BOLNA_BASE = "https://api.bolna.ai"
DEFAULT_AGENT = "106ac92f-41e1-4e2e-9c7f-dca769d5bcb6"
PHONE = re.compile(r"^\+[1-9]\d{7,14}$")
EXEC_ID = re.compile(r"^[A-Za-z0-9-]{6,64}$")
FIELDS = ("patient_name", "treatment", "doctor_name", "appointment_date", "appointment_time")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def env(k):
    return os.environ.get(k, "").strip()


def api_key():
    k = env("BOLNA_API_KEY")
    return "" if k.startswith("your-") else k


def access_ok(headers):
    code = env("ACCESS_CODE")
    return (not code) or (headers.get("X-Access-Code") or "").strip() == code


def bolna(method, path, payload=None):
    req = urllib.request.Request(
        BOLNA_BASE + path, method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Authorization": "Bearer " + api_key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read() or b"{}")


# ----------------------------------------------------------------- route handlers
def get_config():
    return 200, {"mode": "live" if api_key() else "demo",
                 "agent_id": env("BOLNA_AGENT_ID") or DEFAULT_AGENT,
                 "access_required": bool(env("ACCESS_CODE"))}


def post_call(body, headers):
    if not api_key():
        return 400, {"error": "BOLNA_API_KEY is not set on the server, so the app is in demo mode."}
    if not access_ok(headers):
        return 401, {"error": "Wrong or missing access code."}
    phone = str(body.get("phone", "")).replace(" ", "")
    if not PHONE.match(phone):
        return 400, {"error": "Phone must be in international format, e.g. +919812345678"}
    payload = {"agent_id": env("BOLNA_AGENT_ID") or DEFAULT_AGENT,
               "recipient_phone_number": phone,
               "user_data": {k: str(body.get(k, ""))[:100] for k in FIELDS}}
    if env("BOLNA_FROM_NUMBER"):
        payload["from_phone_number"] = env("BOLNA_FROM_NUMBER")
    try:
        res = bolna("POST", "/call", payload)
    except urllib.error.HTTPError as e:
        return 502, {"error": "Bolna rejected the call (%s): %s" % (e.code, e.read().decode()[:300])}
    except Exception as e:
        return 502, {"error": "Could not reach Bolna: %s" % e}
    eid = res.get("execution_id") or res.get("call_id") or res.get("id")
    if not eid:
        return 502, {"error": "Unexpected Bolna response: %s" % json.dumps(res)[:300]}
    return 200, {"execution_id": eid, "status": res.get("status", "queued")}


def get_execution(query, headers):
    if not api_key():
        return 400, {"error": "BOLNA_API_KEY is not set on the server."}
    if not access_ok(headers):
        return 401, {"error": "Wrong or missing access code."}
    eid = (query.get("id") or [""])[0]
    if not EXEC_ID.match(eid):
        return 400, {"error": "Invalid execution id."}
    try:
        ex = bolna("GET", "/executions/" + eid)
    except urllib.error.HTTPError as e:
        return 502, {"error": "Bolna error (%s): %s" % (e.code, e.read().decode()[:300])}
    except Exception as e:
        return 502, {"error": "Could not reach Bolna: %s" % e}
    tel = ex.get("telephony_data") or {}
    return 200, {"status": ex.get("status"), "transcript": ex.get("transcript"),
                 "summary": ex.get("summary"), "extracted_data": ex.get("extracted_data"),
                 "recording_url": tel.get("recording_url"),
                 "duration": tel.get("duration") or ex.get("conversation_duration")}


def route(method, raw_path, headers, body):
    """Returns (status, payload, content_type). payload is dict (JSON) or bytes."""
    path, _, qs = raw_path.partition("?")
    query = urllib.parse.parse_qs(qs)
    # Works with direct paths (/api/config) and with vercel.json rewrites (?route=config)
    name = (query.get("route") or [""])[0] or path.rstrip("/").rsplit("/", 1)[-1]
    if path.startswith("/api") or query.get("route"):
        if name == "config" and method == "GET":
            return get_config() + ("application/json",)
        if name == "call" and method == "POST":
            return post_call(body, headers) + ("application/json",)
        if name == "execution" and method == "GET":
            return get_execution(query, headers) + ("application/json",)
        return 404, {"error": "unknown API route"}, "application/json"
    if method == "GET" and path in ("", "/", "/index.html"):
        try:
            with open(os.path.join(ROOT, "public", "index.html"), "rb") as f:
                return 200, f.read(), "text/html; charset=utf-8"
        except OSError:
            pass
    return 404, {"error": "not found"}, "application/json"


class handler(BaseHTTPRequestHandler):
    def _send(self, code, payload, ctype):
        out = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(out)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(out)

    def do_GET(self):
        self._send(*route("GET", self.path, self.headers, {}))

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
        except ValueError:
            body = {}
        self._send(*route("POST", self.path, self.headers, body))

    def log_message(self, fmt, *args):
        pass
