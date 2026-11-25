"""
Local dev server: serves public/ and the same api/index.py that Vercel runs.

    python3 run_local.py        ->  http://localhost:8000

Reads BOLNA_API_KEY etc. from .env in this folder (never committed / zipped).
"""
import os
import sys
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
_env = os.path.join(HERE, ".env")
if os.path.exists(_env):
    for _line in open(_env):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

sys.path.insert(0, os.path.join(HERE, "api"))
import index  # noqa: E402  (api/index.py)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("SmileCare CRM on http://localhost:%d  (%s mode)" % (port, index.get_config()[1]["mode"].upper()), flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), index.handler).serve_forever()
